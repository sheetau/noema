"""Check free activity kind, acquired familiarity, and causal reason in one conditional."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json

from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest, canonical_digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_unfamiliar_judgment import ROOT, FULL, CORE, LIBRARY, BASIS, ANNOTATIONS, PARENT, PARENT_BASIS, MEANINGS, LIMITS, parent, build, closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol

INDEX = 'data/semantic-review-index-v108.json'
REPORT = 'reports/unfamiliar-judgment-v1.json'
AUDIT = 'data/unfamiliar-judgment-reading-v1.json'
DOC = 'docs/unfamiliar-judgment-v1.md'
INVENTORY = 'artifacts/written-units-v1/kant-1784.json'
PRIOR = ['reports/uncertain-judgment-v1.json', 'reports/abandoned-reliance-v1.json', 'reports/depicted-referents-v1.json', 'reports/fetters-sentence-v1.json']
SENTENCES = [('data/nature-sentence-reading-v1.json', [51]), ('data/confirmed-incapacity-reading-v1.json', [11, 12]),
             ('data/fetters-sentence-reading-v1.json', [10, 52])]

from scripts.check_uncertain_judgment import source_values as judgment_values, PEOPLE as JUDGMENT_PEOPLE, SCENES as JUDGMENT_SCENES

PEOPLE = ('person', 'other', 'experience', 'second')
SCENES = ('before', 'anchor', 'future', 'outside')


def read(path): return json.loads((ROOT / path).read_text(encoding='utf-8'))
@lru_cache(None)
def document(): return parse((ROOT / FULL).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog(): return load_catalog(ROOT, BASIS)


def fixture(roots, extra):
    doc = deepcopy(document()); doc.update(declarations=closure(doc, roots), statements=[])
    return parse(format_graph(doc, 'compact') + extra)


def unknowns(doc): return {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}


def refuse(doc, values, names, people=PEOPLE, scenes=SCENES):
    for name in names:
        changed = dict(values); changed[name] = unknown
        try: evaluate(doc, changed, people, scenes, True)
        except ValueError as error: assert 'Unknown' in str(error), (name, str(error))
        else: raise AssertionError(name)


@lru_cache(None)
def kind_checks():
    doc = fixture(['r2ha', 'r2he', 'r2hf'], '''r zperson[] a.r zact[] a.r ztopic[] a.r zanchor[] d.
q[k r2ha[k zperson[] k zact[] k ztopic[] k zanchor[]]].
q[k r2he[k zperson[] k zact[] k zanchor[]]].q[t[k r2hf[k zperson[]]][k zanchor[]]].''')
    for actual, first, second in product((False, True), repeat=3):
        values = judgment_values(doc, actual_support=actual, responses=(first, second))
        assert evaluate(doc, values, JUDGMENT_PEOPLE, JUDGMENT_SCENES, True) == [not (first and second), True, True]
    rows = {}
    for name, expected in [('baseline', [True, True, True]), ('wrong_actual_topic', [False, True, True]),
        ('no_actual', [False, False, False]), ('guided_actual', [False, False, False]), ('wrong_actual_faculty', [False, False, False])]:
        actual = evaluate(doc, judgment_values(doc, name), JUDGMENT_PEOPLE, JUDGMENT_SCENES, True)
        assert actual == expected, (name, actual); rows[name] = actual
    return dict(combinations=8, cases=rows, kind_drops_topic_identity_and_uncertainty=True,
        same_actual_judgment_projects_to_kind=True)


def familiarity_values(doc, bits=(True, True, True), variant='baseline'):
    experience, contribution, settled = bits
    values = unknowns(doc); order = ('before', 'anchor', 'future')
    values.update(zperson=lambda: 'person', zanchor=lambda: 'anchor',
        hzzzs=lambda p, end, t: (p, end) == ('person', 'anchor') and t in order and not (variant == 'missing_anchor' and t == 'anchor'),
        ic=lambda a, b, sc: sc == 'anchor' and a in order and b in order and (order.index(a) < order.index(b) or variant == 'cycle' and (a, b) == ('anchor', 'before')),
        h3e=lambda p, ev, d, t: experience and (p, ev, symbol(d), t) == (
            'other' if variant == 'other_person' else 'person', 'experience',
            'r2hb' if variant == 'other_kind' else 'r2hf',
            'future' if variant == 'future_experience' else 'anchor' if variant == 'current_experience' else 'outside' if variant == 'outside_experience' else 'before'),
        h3g=lambda ev, p, d, t, now: contribution and (ev, p, symbol(d), t, now) == (
            'second' if variant == 'split_event' else 'experience', 'person',
            'r2hb' if variant == 'other_contribution_kind' else 'r2hf', 'before', 'anchor'),
        h3f=lambda p, d, t: settled and (p, symbol(d), t) == ('person', 'r2hb' if variant == 'other_settled_kind' else 'r2hf', 'anchor'))
    return values


@lru_cache(None)
def familiarity_checks():
    doc = fixture(['r2hg', 'r2hh', 'r2hi'], 'r zperson[] a.r zanchor[] d.' +
        ''.join('q[t[k '+n+'[k zperson[]]][k zanchor[]]].' for n in ('r2hg', 'r2hh', 'r2hi')))
    for bits in product((False, True), repeat=3):
        expected = [all(bits), not all(bits), bits[0]]
        assert evaluate(doc, familiarity_values(doc, bits), PEOPLE, SCENES, True) == expected, bits
    rows = {}
    for name in ('baseline', 'split_event', 'other_contribution_kind', 'other_settled_kind', 'other_kind', 'other_person',
                 'future_experience', 'current_experience', 'outside_experience', 'missing_anchor', 'cycle'):
        expected = [True, False, True] if name == 'baseline' else [False, False, False] if name in ('missing_anchor', 'cycle') else [False, True, name in ('split_event', 'other_contribution_kind', 'other_settled_kind')]
        actual = evaluate(doc, familiarity_values(doc, variant=name), PEOPLE, SCENES, True)
        assert actual == expected, (name, actual); rows[name] = actual
    refuse(doc, familiarity_values(doc), ('hzzzs', 'ic', 'h3e', 'h3g', 'h3f'))
    return dict(combinations=8, cases=rows, unknown_inputs_refused=5, activity_content_not_executed=True,
        experience_contribution_and_settling_distinguished=True)


def replace_contents(doc, pairs):
    lookup = {d['name']: d for d in doc['declarations']}
    for original, replacement in pairs:
        lookup[original]['parameters'] = deepcopy(lookup[replacement]['parameters'])
        lookup[original]['body'] = deepcopy(lookup[replacement]['body'])
    doc['declarations'] = closure(doc, [s['body']['content']['symbol'] for s in doc['statements']] + ['zperson', 'zanchor'])
    doc['declarations'].sort(key=lambda d: d['kind'] != 'primitive')
    return parse(format_graph(doc, 'compact'))


@lru_cache(None)
def cause_checks():
    doc = fixture(['r2hj', 'r2hk'], '''r zfactor[a d] c.r zeffect[a d] c.r zperson[] a.r zanchor[] d.
d zbefore[person a] e[b point[k zfactor[v person v point]]].d zafter[person a] e[b point[k zeffect[v person v point]]].
q[t[k r2hj[k zperson[]]][k zanchor[]]].q[t[k r2hk[k zperson[]]][k zanchor[]]].''')
    doc = replace_contents(doc, [('r2hh', 'zbefore'), ('r2hb', 'zafter')])
    def model(bits=(True, True, True, True), variant='baseline'):
        f, e, cause, adopted = bits
        def relation(p, fd, q, ed, s):
            return (p, symbol(fd), q, symbol(ed), s) == (
                'other' if variant == 'other_factor_person' else 'person',
                'r2hb' if variant == 'reversed_descriptions' else 'r2hh',
                'other' if variant == 'other_effect_person' else 'person',
                'r2hh' if variant == 'reversed_descriptions' else 'r2hb',
                'before' if variant == 'other_scene' else 'anchor')
        return dict(zperson=lambda: 'person', zanchor=lambda: 'anchor',
            zfactor=lambda p, s: f and (p, s) == ('person', 'anchor'), zeffect=lambda p, s: e and (p, s) == ('person', 'anchor'),
            hzie=lambda *args: cause and relation(*args), ea=lambda *args: adopted and relation(*args))
    for bits in product((False, True), repeat=4):
        assert evaluate(doc, model(bits), PEOPLE, SCENES, True) == [all(bits[:3]), bits[0] and bits[1] and bits[3]], bits
    rows = {}
    for name in ('baseline', 'other_factor_person', 'other_effect_person', 'reversed_descriptions', 'other_scene'):
        actual = evaluate(doc, model(variant=name), PEOPLE, SCENES, True)
        assert actual == [name == 'baseline']*2; rows[name] = actual
    refuse(doc, model(), ('zfactor', 'zeffect', 'hzie', 'ea'))
    return dict(combinations=16, cases=rows, unknown_inputs_refused=4, content_boundary_test=True,
        adopted_explanation_is_not_causal_contribution=True, same_subjects_descriptions_and_scene=True)


@lru_cache(None)
def conditional_checks():
    doc = fixture(['r2hm'], '''r zante[a d] c.r zcons[a d] c.r zperson[] a.r zanchor[] d.
d zbefore[person a] e[b point[k zante[v person v point]]].d zafter[person a] e[b point[k zcons[v person v point]]].
q[t[k r2hm[k zperson[]]][k zanchor[]]].''')
    doc = replace_contents(doc, [('r2gt', 'zbefore'), ('r2hj', 'zafter')])
    scenes = ('scope', 'one', 'two'); people = ('person', 'other')
    def model(bits=(True, False, True, False)):
        return dict(wh=lambda: 'scope', zanchor=lambda: 'scope', zperson=lambda: 'person',
            hzzzy=lambda p, sc, s: (p, sc) == ('person', 'scope') and s in ('one', 'two'),
            zante=lambda p, s: p == 'person' and s in ('one', 'two') and bits[('one', 'two').index(s)],
            zcons=lambda p, s: p == 'person' and s in ('one', 'two') and bits[2+('one', 'two').index(s)])
    for bits in product((False, True), repeat=4):
        wanted = any(bits[:2]) and all(not bits[i] or bits[i+2] for i in range(2))
        assert evaluate(doc, model(bits), people, scenes, True) == [wanted]
    rows = {}
    for name in ('baseline', 'empty', 'other_person_reason', 'wrong_anchor'):
        v = model()
        if name == 'empty': v['hzzzy'] = lambda *args: False
        if name == 'other_person_reason': v['zcons'] = lambda p, s: p == 'other'
        if name == 'wrong_anchor': v['zanchor'] = lambda: 'one'
        actual = evaluate(doc, v, people, scenes, True); assert actual == [name == 'baseline']; rows[name] = actual
    refuse(doc, model(), ('hzzzy', 'zante', 'zcons', 'wh'), people, scenes)
    return dict(combinations=16, cases=rows, unknown_inputs_refused=4, content_boundary_test=True,
        same_person_and_nonvacuous_conditional=True)


@lru_cache(None)
def native_checks():
    doc = fixture(['r2hm'], '''r zperson[] a.r zanchor[] d.r zpast[] d.r zcopy[] a.
q[t[k r2hm[k zperson[]]][k zanchor[]]].q[k r2he[k zperson[] k zcopy[] k zpast[]]].''')
    people = JUDGMENT_PEOPLE + ('process', 'source', 'author'); scenes = ('before', 'anchor', 'one', 'two')
    rows = {}
    for variant in ('baseline', 'familiar', 'no_cause', 'adoption_absent', 'wrong_description', 'no_actual', 'no_departure', 'reliable', 'missing_history'):
        values = judgment_values(doc, variant, responses=(True, variant == 'reliable'))
        old_fa, old_dg = values['fa'], values['dg']
        values.update(h2d=lambda: 'source', wa=lambda: 'author', zpast=lambda: 'before', zcopy=lambda: 'copy',
            fa=lambda p, j, s: old_fa(p, j, s) or (p, j, s) == ('person', 'copy', 'before'),
            hzzzm=lambda n, a, d, p, o, s: (n, a, symbol(d), p, o, s) == ('source', 'author', 'r2fh', 'person', 'topic', 'anchor'),
            hzzzo=lambda sc, o, p, a, s: (sc, o, p) == ('anchor', 'topic', 'person') and (a, s) in (('before', 'one'), ('anchor', 'two')),
            hzzzp=lambda *args: True, hzzzq=lambda *args: True, hzzzr=lambda *args: False,
            hx2=lambda p, o, act, s: (p, o, act, s) == ('person', 'topic', 'act', 'one'), hz2=lambda *args: False,
            dg=lambda act, s: old_dg(act, s) or (act, s) in (('act', 'one'), ('copy', 'before')) or variant != 'no_departure' and (act, s) == ('process', 'anchor'),
            hzzzs=lambda p, end, t: (p, end) == ('person', 'anchor') and t in ('before', 'anchor') and not (variant == 'missing_history' and t == 'anchor'),
            ic=lambda a, b, s: (a, b, s) == ('before', 'anchor', 'anchor'),
            ag=lambda proc, a, b: (proc, a, b) == ('process', 'before', 'anchor'),
            la=lambda p, proc, a, b: (p, proc, a, b) == ('person', 'process', 'before', 'anchor'),
            df=lambda p, proc, s: (p, proc, s) == ('person', 'process', 'anchor'),
            hzid=lambda p, proc, old, new, a, b: (p, proc, symbol(old), symbol(new), a, b) == ('person', 'process', 'r2gp', 'r2gq', 'before', 'anchor'),
            g3=lambda proc, p, d, s: (proc, p, symbol(d), s) == ('process', 'person', 'r2gq', 'anchor'),
            hzzzy=lambda p, sc, s: (p, sc, s) == ('person', 'anchor', 'anchor'),
            h3e=lambda p, event, d, s: (p, event, symbol(d), s) == ('person', 'copy', 'r2hf', 'before'),
            h3g=lambda event, p, d, a, b: (event, p, symbol(d), a, b) == ('copy', 'person', 'r2hf', 'before', 'anchor'),
            h3f=lambda p, d, s: variant == 'familiar' and (p, symbol(d), s) == ('person', 'r2hf', 'anchor'),
            hzie=lambda p, f, q, e, s: variant != 'no_cause' and (p, symbol(f), q, symbol(e), s) == (
                'person', 'r2hf' if variant == 'wrong_description' else 'r2hh', 'person', 'r2hb', 'anchor'),
            ea=lambda *args: variant != 'adoption_absent')
        actual = evaluate(doc, values, people, scenes, True)
        assert actual == [variant in ('baseline', 'adoption_absent'), True], (variant, actual); rows[variant] = actual
    return dict(cases=rows, native_departure_familiarity_judgment_and_cause_executed=True,
        same_world=True, past_experience_activity_witness_executed=True,
        explanation_adoption_not_required=True, prior_experience_can_coexist_with_unfamiliarity=True)


@lru_cache(None)
def quotation_checks():
    doc = fixture(['r2hm'], 'q[e[r[p r2hm]][r[p r2hm]]].')
    assert evaluate(doc, unknowns(doc), PEOPLE, SCENES, True) == [True]
    return dict(closed_reasoned_conditional_quotable_without_world_evaluation=True)

def reading():
    unit = next(u for u in read(INVENTORY)['units'] if u['id'] == 'kant-1784:u0010')
    phrase = 'weil er zu dergleichen freier Bewegung nicht gewöhnt ist'
    start = unit['text'].index(phrase, 474); end = start + len(phrase)
    current = catalog(); dependencies = [d['name'] for d in closure(current.document, ['r2hm'])]
    paths = {INDEX, INVENTORY, FULL, BASIS, PARENT, PARENT_BASIS, *PRIOR, *(p for p, _ in SENTENCES)}
    return dict(status='unasserted_unfamiliarity_and_causal_conditional_candidate', reviewer='assistant_review', document=FULL, meaning_basis=BASIS,
        source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'], range=[start, end], text=unit['text'][start:end]),
        candidate_definitions=list(MEANINGS), candidate_dependency_sha256=canonical_digest([current.entries[n] for n in dependencies]),
        candidate_dependencies=dependencies, preserved_authored_selection=selection_binding(current, [13, 53]),
        decision='自分の理解力による指導なしの判断という活動種類へ経験・寄与・定着を結び、その不慣れが不確かな判断へ寄与する理由付き条件骨格を構成する。種類の読解は候補であり、尺度・限定・譲歩と本文への採用は未完。',
        interpretation_limits=LIMITS, revised_statement_indices=[],
        references=[dict(url='https://korpora.org/Kant/aa08/036.html', title='Kant AA VIII036', accessed='2026-10-20',
            use='自由な運動の種類への不慣れを理由とする部分を照合。対象側を指導なしの判断活動の種類へ結ぶ読みは候補であり、原文の唯一の解釈ではない。')],
        whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
        new_verified_sentence_characters=0, preserved_reviewed_sentence_characters=408,
        semantic_equivalence_automatically_proved=False,
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})


@lru_cache(None)
def structure_checks():
    old, new = parent(), catalog()
    assert new.document['declarations'][:-9] == old.document['declarations']
    assert all(new.entries[n] == entry for n, entry in old.entries.items())
    assert len(new.document['statements']) == 54 and old.document['statements'] == new.document['statements']
    for path in read(INDEX)['works']['kant-1784']['reviews']:
        record = read(path); validate_hashes(ROOT, record['source_sha256'])
        indices = [s['index'] for s in record['selection']['statements']]
        assert record['selection'] == selection_binding(old, indices) == selection_binding(new, indices)
    for path, indices in SENTENCES:
        record = read(path); validate_hashes(ROOT, record['source_sha256'])
        assert record['selection'] == selection_binding(new, indices)
    for path in PRIOR: validate_hashes(ROOT, read(path)['source_sha256'])
    assert not set(MEANINGS) & set(selection_binding(new, list(range(54)))['dependencies'])
    for path, body in build().items(): assert (ROOT / path).read_text(encoding='utf-8') == body, path
    for path in (FULL, CORE, LIBRARY):
        doc = parse((ROOT / path).read_text(encoding='utf-8'))
        for style in ('compact', 'full'):
            text = format_graph(doc, style); assert parse(text) == parse(transcribe(text, alphabet='v2')) == doc
    assert read(AUDIT) == reading()
    return dict(added_definitions=9, added_primitives=0, authored_statements=54, preserved_statements=54,
        revised_statement_indices=[], preserved_review_selections=12, reviewed_nonblank_characters=2212,
        preserved_reviewed_sentence_characters=408, candidate_not_asserted=True, roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    for path, body in build().items(): write_exact(ROOT / path, body)
    write_exact(ROOT / AUDIT, encoded(reading()))


def build_report():
    results = {}
    for name, fn in [('kind', kind_checks), ('familiarity', familiarity_checks), ('cause', cause_checks),
                     ('conditional', conditional_checks), ('native', native_checks), ('quotation', quotation_checks), ('structure', structure_checks)]:
        results[name] = fn(); print(name + ' checked', flush=True)
    record = reading()
    paths = set(build()) | set(catalog().source_sha256) | set(record['source_sha256']) | {
        AUDIT, DOC, 'scripts/compose_unfamiliar_judgment.py', 'scripts/check_unfamiliar_judgment.py',
        'scripts/register_unfamiliar_judgment.py', 'tests/test_unfamiliar_judgment.py',
        'scripts/check_uncertain_judgment.py', 'scripts/check_abandoned_reliance.py', 'scripts/check_pastoral_roles.py', 'scripts/check_motive_causes.py'}
    for path in PRIOR: paths.update(read(path)['source_sha256'])
    paths.update(read(INDEX)['works']['kant-1784']['reviews'])
    return dict(status='unfamiliarity_and_causal_conditional_candidate_checked', document=FULL, **results,
        alignment=dict(**record['source'], definitions=list(MEANINGS), status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
        new_covered_characters=0, new_verified_sentence_characters=0, preserved_reviewed_sentence_characters=408,
        verified_full_units={'kant-1784': 0, 'einstein-1905': 0}, semantic_equivalence_automatically_proved=False,
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})


if __name__ == '__main__':
    from scripts.audit_opening_scope import write_exact, encoded
    prepare(); write_exact(ROOT / REPORT, encoded(build_report()))
