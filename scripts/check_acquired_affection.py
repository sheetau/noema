"""Check directed affection, acquisition and retained disposition independently."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_acquired_affection import ROOT, FULL, CORE, BASIS, ANNOTATIONS, PARENT, PARENT_BASIS, PRIMITIVES, MEANINGS, LIMITS, parent, build, closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol
from scripts import check_exercise_capacity as capacity

INDEX = 'data/semantic-review-index-v88.json'
AUDIT = 'data/acquired-affection-reading-v1.json'
REPORT = 'reports/acquired-affection-v1.json'
DOC = 'docs/acquired-affection-v1.md'
INVENTORY = 'artifacts/written-units-v1/kant-1784.json'
PEOPLE = ('person', 'method', 'faculty', 'act', 'other')
SCENES = ('anchor', 'past', 'acquired', 'middle', 'first', 'second')


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog():
    return load_catalog(ROOT, BASIS)


@lru_cache(None)
def fixture(roots, suffix):
    d = deepcopy(catalog().document)
    d.update(declarations=closure(d, roots.split()), statements=[])
    return parse(format_graph(d, 'compact') + suffix)


@lru_cache(None)
def structure_checks():
    old, new = parent(), catalog()
    assert new.document['declarations'][:-6] == old.document['declarations']
    assert new.document['statements'] == old.document['statements'] and len(new.document['statements']) == 51
    assert all(new.entries[n] == entry for n, entry in old.entries.items())
    assert set(new.entries) - set(old.entries) == set(MEANINGS) | set(PRIMITIVES)
    for name in read(INDEX)['works']['kant-1784']['reviews']:
        r = read(name); validate_hashes(ROOT, r['source_sha256'])
        ids = [s['index'] for s in r['selection']['statements']]
        assert r['selection'] == selection_binding(old, ids) == selection_binding(new, ids)
    assert len(read(INDEX)['works']['kant-1784']['reviews']) == 12
    for path, body in build().items():
        assert (ROOT / path).read_text(encoding='utf-8') == body, path
    for path in (FULL, CORE):
        d = parse((ROOT / path).read_text(encoding='utf-8'))
        for style in ('compact', 'full'):
            text = format_graph(d, style)
            assert parse(text) == parse(transcribe(text, alphabet='v2')) == d
    core = parse((ROOT / CORE).read_text(encoding='utf-8'))
    assert core['statements'] == []
    assert core['declarations'] == closure(new.document, list(MEANINGS))
    assert reading() == read(AUDIT); validate_hashes(ROOT, read(AUDIT)['source_sha256'])
    return dict(new_definitions=3, new_primitives=3, preserved_statements=51, new_authored_assertions=0,
        preserved_review_selections=12, reviewed_nonblank_characters=2212, roundtrips=True,
        affection_candidate_not_unconditionally_asserted=True)


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    write_exact(ROOT / AUDIT, encoded(reading()))


@lru_cache(None)
def disposition_document():
    return fixture('r2ci r2cj id', '''r zperson[] a.r ztarget[] a.r zanchor[] d.
q[k r2ci[k zperson[] k ztarget[] r[p bf] k zanchor[] p hzyw p hzyx p hzyy]].
q[t[k r2cj[k zperson[]]][k zanchor[]]].
q[k hzyw[k zperson[] k ztarget[] r[p bf] k zanchor[]]].
q[k id[k zperson[] r[p bf] k zanchor[]]].''')


def disposition_values(d, bits=(True, True, True, False, False), variant='baseline'):
    first, second, ordered, now, accepted = bits
    v = {e['name']: unknown for e in d['declarations'] if e['kind'] == 'primitive'}
    def same(actor, target, description):
        return (actor, target, symbol(description)) == (
            'other' if variant == 'wrong_actor' else 'person',
            'other' if variant in ('wrong_target', 'distinct_target') else 'person',
            'bm' if variant == 'wrong_property' else 'bf')
    def cases(actor, target, description, anchor, candidate):
        return same(actor, target, description) and anchor == ('past' if variant == 'wrong_anchor' else 'anchor') and candidate in (
            () if variant == 'empty' else ('first', 'second'))
    def preferred(actor, target, description, anchor, a, b):
        return same(actor, target, description) and anchor == 'anchor' and (
            ordered and (a, b) == ('first', 'second') or variant == 'cyclic' and (a, b) == ('second', 'first') or
            variant == 'reflexive' and (a, b) == ('first', 'first'))
    v.update(zperson=lambda: 'person', ztarget=lambda: 'other' if variant == 'distinct_target' else 'person', zanchor=lambda: 'anchor',
        hzyx=cases, hzyy=preferred,
        hzyw=lambda a, t, desc, s: same(a, t, desc) and dict(first=first, second=second, anchor=now).get(s, False),
        id=lambda p, desc, s: accepted and (p, symbol(desc), s) == ('person', 'bf', 'anchor'))
    return v


@lru_cache(None)
def disposition_checks():
    d = disposition_document(); rows = []
    run = lambda v: evaluate(d, v, ('person', 'other'), ('anchor', 'first', 'second', 'past'), True)
    for bits in product((False, True), repeat=5):
        first, second, preferred, now, accepted = bits
        wanted = first and (preferred or second)
        actual = run(disposition_values(d, bits))
        assert actual == [wanted, wanted, now, accepted], (bits, actual)
        rows.append(dict(first=first, second=second, preferred=preferred, current_feeling=now,
                         acceptance=accepted, values=actual))
    contrasts = {}
    for name in ('wrong_actor', 'wrong_target', 'wrong_property', 'wrong_anchor', 'empty', 'cyclic', 'reflexive', 'distinct_target'):
        actual = run(disposition_values(d, variant=name))
        assert actual == ([True, False, False, False] if name == 'distinct_target' else [False, False, False, False]), (name, actual)
        contrasts[name] = actual
    for n in ('hzyw', 'hzyx', 'hzyy'):
        v = disposition_values(d); v[n] = unknown
        try:
            run(v)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(n)
    return dict(combinations=rows, contrasts=contrasts, unknown_inputs_refused=3,
                property_truth_not_evaluated=True, actual_feeling_and_acceptance_independent=True)


@lru_cache(None)
def acquisition_document():
    return fixture('r2cj r2ck ha2', '''r zperson[] a.r zanchor[] d.
q[t[k r2cj[k zperson[]]][k zanchor[]]].
q[t[k r2ck[k zperson[]]][k zanchor[]]].
q[t[k ha2[k zperson[]]][k zanchor[]]].''')


def acquisition_values(d, variant='baseline'):
    # Reuse the real capacity definitions on a smaller complete finite model.
    # The successful outcome is 'middle', the failed outcome is 'past'.
    rename = lambda a: {'middle': 'success', 'past': 'failure'}.get(a, a) if isinstance(a, str) else a
    v = {n: (lambda *args, fn=fn: fn(*(rename(a) for a in args)))
         for n, fn in capacity.source_values(d, passes=(variant == 'currently_capable',) * 2).items()}
    history = ['past', 'acquired', 'middle', 'anchor']
    states = {'acquired', 'middle', 'anchor'}
    if variant == 'already_attached':
        states.add('past')
    if variant == 'lost_middle':
        states.remove('middle')
    if variant == 'lost_now':
        states.remove('anchor')
    if variant == 'only_future':
        states = {'outside'}
    def cases(actor, target, desc, anchor, candidate):
        return (actor, target, symbol(desc)) == ('person', 'person', 'bf') and anchor in history and candidate == anchor and not (
            variant in ('unknown_prior_profile', 'empty_prior_profile') and anchor == 'past')
    def affection(actor, target, desc, scene):
        return (actor, target, symbol(desc)) == (
            'other' if variant == 'wrong_actor' else 'person',
            'other' if variant == 'wrong_target' else 'person',
            'bm' if variant == 'wrong_property' else 'bf') and scene in states
    v.update(zperson=lambda: 'person', zanchor=lambda: 'anchor',
        hzyw=affection, hzyx=cases, hzyy=lambda a, t, desc, anchor, first, last:
            variant == 'invalid_prior_order' and anchor == first == last == 'past',
        id=lambda p, desc, s: variant == 'acceptance_only' and (p, symbol(desc)) == ('person', 'bf') and s in ('acquired', 'middle', 'anchor'),
        ia=lambda p, anchor, s: (p, anchor) == ('person', 'anchor') and s in history and not (
            variant == 'missing_anchor' and s == 'anchor' or variant == 'missing_past' and s == 'past'),
        ic=lambda a, b, anchor: anchor == 'anchor' and a in history and b in history and (
            history.index(a) < history.index(b) or variant == 'cyclic_history' and (a, b) == ('anchor', 'past')),
        ag=lambda process, a, b: variant != 'no_change' and (process, a, b) == (
            'act', 'second' if variant == 'outside_change' else 'past', 'acquired'),
        la=lambda p, process, a, b: (p, process, a, b) == (
            'other' if variant == 'other_person_change' else 'person',
            'method' if variant == 'other_process' else 'act', 'past', 'acquired'))
    if variant == 'acceptance_only':
        v['hzyw'] = lambda *args: False
    # Lack of a valid profile is not evidence that a real disposition was absent.
    if variant == 'unknown_prior_profile':
        v['hzyx'] = lambda *args: unknown() if args[-2] == 'past' else cases(*args)
    return v


@lru_cache(None)
def acquisition_checks():
    d = acquisition_document(); run = lambda v: evaluate(d, v, PEOPLE, SCENES, True)
    rows = {}
    for name in ('baseline', 'already_attached', 'lost_middle', 'lost_now', 'only_future', 'no_change',
                 'other_person_change', 'other_process', 'outside_change', 'missing_anchor', 'missing_past',
                 'cyclic_history', 'wrong_actor', 'wrong_target', 'wrong_property', 'currently_capable', 'acceptance_only',
                 'empty_prior_profile', 'invalid_prior_order'):
        actual = run(acquisition_values(d, name))
        current = name not in ('lost_now', 'only_future', 'wrong_actor', 'wrong_target', 'wrong_property', 'acceptance_only')
        assert actual == [current, name == 'baseline', name == 'acceptance_only'], (name, actual)
        rows[name] = actual
    for name in ('hzyw', 'hzyx', 'hzyy', 'ia', 'ic', 'ag', 'la', 'hzsh'):
        v = acquisition_values(d); v[name] = unknown
        try:
            run(v)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(name)
    try:
        run(acquisition_values(d, 'unknown_prior_profile'))
    except ValueError as error:
        assert 'Unknown' in str(error)
    else:
        raise AssertionError('Unknown past disposition became a known absence')
    return dict(contrasts=rows, unknown_inputs_refused=9, native_history_and_capacity_executed=True,
                current_affection_does_not_prove_acquisition=True)


@lru_cache(None)
def quotation_checks():
    d = fixture('r2ck uc', 'r zperson[] a.r znode[] a.r zscene[] d.q[k uc[k znode[] k zperson[] r[k r2ck[k zperson[]]] k zscene[]]].')
    rows = {}
    for variant in ('baseline', 'false_attribution', 'wrong_person', 'wrong_context', 'obsolete_content'):
        v = {e['name']: unknown for e in d['declarations'] if e['kind'] == 'primitive'}
        def reported(node, author, content, scene):
            wanted = dict(kind='call', symbol='ha2' if variant == 'obsolete_content' else 'r2ck',
                          arguments=[dict(kind='call', symbol='zperson', arguments=[])])
            return variant != 'false_attribution' and (node, author, scene) == (
                'act', 'other' if variant == 'wrong_person' else 'person', 'past' if variant == 'wrong_context' else 'anchor') and json.loads(content.syntax) == wanted
        v.update(zperson=lambda: 'person', znode=lambda: 'act', zscene=lambda: 'anchor', uc=reported)
        actual = evaluate(d, v, PEOPLE, SCENES)
        assert actual == [variant == 'baseline'], (variant, actual)
        rows[variant] = actual
    return dict(contrasts=rows, world_contents_unknown=True, rank_zero_quote_accepted=True,
                diagnostic_quotation_not_added_to_manuscript=True)


def reading():
    u = next(u for u in read(INVENTORY)['units'] if u['id'] == 'kant-1784:u0010')
    paths = {INDEX, INVENTORY, FULL, BASIS, PARENT, PARENT_BASIS,
             'reports/retained-attitudes-v1.json', 'reports/fear-proneness-v1.json'}
    return dict(status='acquired_affective_disposition_not_whole_sentence', reviewer='assistant_review',
        document=FULL, meaning_basis=BASIS, source=dict(unit=u['id'], unit_sha256=u['text_sha256'],
            range=[126, 156], text=u['text'][126:156]), definitions=list(MEANINGS),
        decision='対象へ向かう親しみの感情の応答傾向と、その取得・持続を合成する。旧来のidによる受容と分ける。sogar、人称の量化範囲と著者への帰属はまだ接続しない。',
        references=[dict(url='https://lexika.digitale-sammlungen.de/adelung/lemma/bsb00009132_7_1_1390',
            title='Adelung, Lieb, active sense', accessed='2026-10-20',
            use='lieb gewinnenを人や物へのLiebe・Neigungの獲得として説明する。応答傾向による形式化と持続範囲はこの実装の採用読解であり、辞書からの自動的な帰結ではない。')],
        interpretation_limits=LIMITS, whole_sentence_semantically_verified=False,
        whole_unit_semantically_verified=False, new_verified_sentence_characters=0,
        semantic_equivalence_automatically_proved=False,
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})


def build_report():
    results = {}
    for name, fn in [('disposition', disposition_checks), ('acquisition', acquisition_checks),
                     ('quotation', quotation_checks), ('structure', structure_checks)]:
        results[name] = fn(); print(name + ' checked', flush=True)
    r = reading()
    paths = set(build()) | set(catalog().source_sha256) | set(r['source_sha256']) | {
        AUDIT, DOC, 'scripts/compose_acquired_affection.py', 'scripts/check_acquired_affection.py',
        'scripts/register_acquired_affection.py', 'tests/test_acquired_affection.py',
        'scripts/check_exercise_capacity.py', 'scripts/check_standing_ability.py', 'scripts/compose_exercise_capacity.py',
        'scripts/check_pastoral_roles.py', 'scripts/check_motive_causes.py', 'scripts/compose_courageous_undertaking.py',
        'scripts/compose_grounded_step.py', 'noema/constructed.py', 'noema/constructed_semantics.py',
        'noema/meaning_catalog.py', 'noema/semantic_reviews.py', 'noema/script.py'}
    return dict(status='acquired_affective_disposition_checked', document=FULL, **results,
        alignment=dict(**r['source'], definitions=list(MEANINGS), status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=False, new_verified_sentence_characters=0, new_covered_characters=0,
        verified_full_units={'kant-1784': 0, 'einstein-1905': 0}, semantic_equivalence_automatically_proved=False,
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})


if __name__ == '__main__':
    from scripts.audit_opening_scope import write_exact, encoded
    prepare()
    write_exact(ROOT / REPORT, encoded(build_report()))
