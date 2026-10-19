"""Execute current ability, permission history and actual cause independently."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_current_deprivation import ROOT, FULL, CORE, BASIS, ANNOTATIONS, PARENT, PARENT_BASIS, MEANINGS, LIMITS, parent, build, closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol
from scripts import check_exercise_capacity as capacity

INDEX = 'data/semantic-review-index-v87.json'
AUDIT = 'data/current-deprivation-reading-v1.json'
REPORT = 'reports/current-deprivation-v1.json'
DOC = 'docs/current-deprivation-v1.md'
INVENTORY = 'artifacts/written-units-v1/kant-1784.json'
PEOPLE = capacity.DOMAIN
SCENES = capacity.SCENES + ('past', 'later', 'outside')


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
def capacity_document():
    return fixture('r2cf r2ch h4 bc', '''r zperson[] a.r zanchor[] d.
q[t[k r2cf[k zperson[]]][k zanchor[]]].q[t[k r2ch[k zperson[]]][k zanchor[]]].
q[t[k h4[k zperson[]]][k zanchor[]]].q[k bc[k zperson[] k zanchor[]]].''')


def capacity_values(d, variant='baseline', **options):
    v = capacity.source_values(d, variant, **options)
    if variant == 'guided':
        v['ad'] = lambda other, person, act, scene: (other, person, act, scene) == ('guide', 'person', 'act', 'success')
    return v


@lru_cache(None)
def capacity_checks():
    d = capacity_document(); rows = []
    for now, first, second, preferred in product((False, True), repeat=4):
        expected = first and (preferred or second)
        v = capacity_values(d, now=now, passes=(first, second), prefer_first=preferred)
        actual = evaluate(d, v, PEOPLE, SCENES, True)
        assert actual == [not expected, expected, not now, not expected], (now, first, second, preferred, actual)
        rows.append(dict(current_opportunity=now, first=first, second=second, first_preferred=preferred, values=actual))
    contrasts = {}
    for name, opts, wanted in [
        ('guided', {}, [False, True, True, True]),
        ('training_only', {'now': True, 'passes': (False, False)}, [True, False, False, True]),
        ('unclassified_training', {'passes': (False, False)}, [False, False, True, False]),
        ('known_success_unknown_other', {}, [False, True, True, False]),
        ('empty_profile', {}, [False, False, True, False]),
        ('changed_person_state', {}, [False, False, True, False]),
        ('missing_external_opportunity', {}, [False, False, True, False]),
        ('cyclic_order', {}, [False, False, True, False]),
        ('missing_assessment', {}, [False, False, True, False]),
    ]:
        actual = evaluate(d, capacity_values(d, name, **opts), PEOPLE, SCENES, True)
        assert actual == wanted, (name, actual, wanted)
        contrasts[name] = actual
    for n in ('hzsc', 'hzsd', 'hzse', 'hzsf', 'hzsg', 'hzsh', 'ap'):
        v = capacity_values(d); v[n] = unknown
        try:
            evaluate(d, v, PEOPLE, SCENES, True)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(n)
    return dict(combinations=rows, contrasts=contrasts, unknown_inputs_refused=7,
                current_bm_and_independent_bb_distinguished=True, native_capacity_definitions_executed=True)


@lru_cache(None)
def causal_document():
    return fixture('r2cg h3 h6 r2cf ea', '''r zperson[] a.r zanchor[] d.
q[t[k h3[k zperson[]]][k zanchor[]]].q[t[k r2cf[k zperson[]]][k zanchor[]]].
q[t[k r2cg[k zperson[]]][k zanchor[]]].q[t[k h6[k zperson[]]][k zanchor[]]].
q[k ea[k zperson[] r[p h3] k zperson[] r[p r2cf] k zanchor[]]].''')


def causal_values(bits=(True, True, True, True, False), variant='baseline'):
    absent, unable, caused, adopted, attempted = bits
    d = causal_document(); v = capacity_values(d, passes=(not unable, not unable))
    history = ['past', 'anchor', 'later']
    if variant == 'empty_past':
        history.remove('past')
    def permitted(agent, person, content, scene):
        point = 'anchor' if variant == 'present_permission' else 'later' if variant == 'future_permission' else 'outside' if variant == 'outside_history_permission' else 'past'
        owner = 'other' if variant == 'other_person_permission' else 'person'
        task = 'bb' if variant == 'other_activity_permission' else 'bm'
        return not absent and (agent, person, symbol(content), scene) == ('other', owner, task, point)
    def cause(person, factor, target, result, scene):
        expected = ('other' if variant == 'other_factor_person' else 'person',
                    'other' if variant == 'other_effect_person' else 'person',
                    'later' if variant == 'other_causal_context' else 'anchor')
        names = ('r2cf', 'h3') if variant == 'reversed_cause' else ('h6', 'r2cf') if variant == 'nonattempt_as_cause' else ('h3', 'h4') if variant == 'obsolete_effect' else ('h3', 'r2cf')
        return caused and (person, target, scene) == expected and (symbol(factor), symbol(result)) == names
    v.update(ia=lambda p, a, s: (p, a) == ('person', 'anchor') and s in history and not(variant == 'missing_anchor' and s == 'anchor'),
        ic=lambda a, b, context: context == 'anchor' and a in history and b in history and (
            history.index(a) < history.index(b) or variant == 'cyclic_history' and (a, b) == ('anchor', 'past')),
        g7=permitted, ei=lambda p, activity, s: attempted and (p, symbol(activity), s) == ('person', 'bm', 'past'),
        hzie=cause, ea=lambda p, factor, q, result, s: adopted and (p, q, s) == ('person', 'person', 'anchor') and (symbol(factor), symbol(result)) == ('h3', 'r2cf'))
    return v


@lru_cache(None)
def causal_checks():
    d = causal_document(); rows = []
    run = lambda v: evaluate(d, v, PEOPLE, SCENES, True)
    for bits in product((False, True), repeat=5):
        absent, unable, cause, adopted, attempted = bits
        actual = run(causal_values(bits))
        assert actual == [absent, unable, absent and unable and cause, not attempted, adopted], (bits, actual)
        rows.append(dict(permission_absent=absent, currently_unable=unable, actual_cause=cause,
                         explanatory_adoption=adopted, actual_attempt=attempted, values=actual))
    contrasts = {}
    for name in ('present_permission', 'future_permission', 'outside_history_permission', 'other_person_permission', 'other_activity_permission'):
        actual = run(causal_values((False, True, True, True, False), name))
        assert actual == [True, True, True, True, True], (name, actual)
        contrasts[name] = actual
    for name in ('other_factor_person', 'other_effect_person', 'other_causal_context', 'reversed_cause', 'nonattempt_as_cause', 'obsolete_effect'):
        actual = run(causal_values(variant=name))
        assert actual == [True, True, False, True, True], (name, actual)
        contrasts[name] = actual
    for name in ('missing_anchor', 'cyclic_history'):
        actual = run(causal_values(variant=name))
        assert actual == [False, True, False, False, True], (name, actual)
        contrasts[name] = actual
    # Empty past makes the negative history vacuous, but does not supply a cause.
    actual = run(causal_values((True, True, False, True, False), 'empty_past'))
    assert actual == [True, True, False, True, True]
    contrasts['empty_past_without_cause'] = actual
    for n in ('ia', 'ic', 'g7', 'hzie', 'hzsh'):
        v = causal_values(); v[n] = unknown
        try:
            run(v)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(n)
    return dict(independent_conditions=rows, contrasts=contrasts, unknown_inputs_refused=5,
        native_permission_history_and_capacity_executed=True, cause_not_inferred_from_history=True)


@lru_cache(None)
def quotation_checks():
    from noema.semantics import SemanticError
    # A rank-zero quotation cannot hide the generic described evaluator.
    try:
        fixture('rqqu h3 r2cf uc', '''r zperson[] a.r znode[] a.r zscene[] d.
d zold[person a] e[b scene[k rqqu[v person r[p h3] v person r[p r2cf] v scene]]].
q[k uc[k znode[] k zperson[] r[k zold[k zperson[]]] k zscene[]]].''')
    except SemanticError as error:
        assert 'Quoted evaluation must target strictly lower ranks' in str(error)
    else:
        raise AssertionError('Rank-zero quotation hid described evaluation')
    d = fixture('r2cg uc', 'r zperson[] a.r znode[] a.r zscene[] d.q[k uc[k znode[] k zperson[] r[k r2cg[k zperson[]]] k zscene[]]].')
    rows = {}
    for variant in ('baseline', 'false_attribution', 'wrong_person', 'wrong_context', 'obsolete_content'):
        v = {e['name']: unknown for e in d['declarations'] if e['kind'] == 'primitive'}
        def reported(node, author, content, scene):
            wanted = dict(kind='call', symbol='h5' if variant == 'obsolete_content' else 'r2cg',
                          arguments=[dict(kind='call', symbol='zperson', arguments=[])])
            return variant != 'false_attribution' and (node, author, scene) == (
                'act', 'other' if variant == 'wrong_person' else 'person', 'later' if variant == 'wrong_context' else 'anchor') and json.loads(content.syntax) == wanted
        v.update(zperson=lambda: 'person', znode=lambda: 'act', zscene=lambda: 'anchor', uc=reported)
        actual = evaluate(d, v, PEOPLE, SCENES)
        assert actual == [variant == 'baseline'], (variant, actual)
        rows[variant] = actual
    v['uc'] = unknown
    try:
        evaluate(d, v, PEOPLE, SCENES)
    except ValueError as error:
        assert 'Unknown' in str(error)
    else:
        raise AssertionError('Unknown report was guessed')
    return dict(contrasts=rows, world_contents_unknown=True, unknown_attribution_refused=True, rank_regression_checked=True,
                diagnostic_quotation_not_added_to_manuscript=True)


def reading():
    u = next(u for u in read(INVENTORY)['units'] if u['id'] == 'kant-1784:u0010')
    paths = {INDEX, INVENTORY, FULL, BASIS, PARENT, PARENT_BASIS,
             'reports/attempt-history-v1.json', 'reports/exercise-capacity-v1.json'}
    return dict(status='current_deprivation_content_composed_not_whole_sentence', reviewer='assistant_review',
        document=FULL, meaning_basis=BASIS, source=dict(unit=u['id'], unit_sha256=u['text_sha256'],
            range=[162, 291], text=u['text'][162:291]), definitions=list(MEANINGS),
        decision='自分の理解力の使用bmの現在の行使能力と、過去の試行の許容不在からの因果的寄与を、既存の一般構成で表す。人称の量化範囲と著者への帰属はまだ接続しない。',
        references=[
            dict(url='https://grammis.ids-mannheim.de/systematische-grammatik/2425', title='IDS, Kausalspezifikation', accessed='2026-10-20',
                 use='事態間の因果では両事態と関係を分ける。因果を単純な必要条件の反実仮想へ還元できない。今回の因果的寄与モデルは実装上の採用読解。'),
            dict(url='https://grammis.ids-mannheim.de/fragen/133', title='IDS, Verbstellung nach weil', accessed='2026-10-20',
                 use='weilには事態そのもの以外を根拠付ける読みもあり、動詞末尾だけで客観的因果とは決められない。今回の文脈で事態間の因果を選ぶ。'),
        ], interpretation_limits=LIMITS, whole_sentence_semantically_verified=False,
        whole_unit_semantically_verified=False, new_verified_sentence_characters=0,
        semantic_equivalence_automatically_proved=False,
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})


@lru_cache(None)
def structure_checks():
    old, new = parent(), catalog()
    assert new.document['declarations'][:-3] == old.document['declarations']
    assert new.document['statements'] == old.document['statements'] and len(new.document['statements']) == 51
    assert all(new.entries[n] == entry for n, entry in old.entries.items())
    assert set(new.entries) - set(old.entries) == set(MEANINGS)
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
    return dict(new_definitions=3, new_primitives=0, preserved_statements=51, new_authored_assertions=0,
        preserved_review_selections=12, reviewed_nonblank_characters=2212, roundtrips=True,
        source_cause_candidate_not_unconditionally_asserted=True)


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    write_exact(ROOT / AUDIT, encoded(reading()))


def build_report():
    results = {}
    for name, fn in [('capacity', capacity_checks), ('causal', causal_checks),
                     ('quotation', quotation_checks), ('structure', structure_checks)]:
        results[name] = fn(); print(name + ' checked', flush=True)
    r = reading()
    paths = set(build()) | set(catalog().source_sha256) | set(r['source_sha256']) | {
        AUDIT, DOC, 'scripts/compose_current_deprivation.py', 'scripts/check_current_deprivation.py',
        'scripts/register_current_deprivation.py', 'tests/test_current_deprivation.py',
        'scripts/check_exercise_capacity.py', 'scripts/check_standing_ability.py', 'scripts/compose_exercise_capacity.py',
        'scripts/check_pastoral_roles.py', 'scripts/check_motive_causes.py', 'scripts/compose_courageous_undertaking.py',
        'scripts/compose_grounded_step.py', 'noema/constructed.py', 'noema/constructed_semantics.py',
        'noema/meaning_catalog.py', 'noema/semantic_reviews.py', 'noema/script.py'}
    return dict(status='current_capacity_and_causal_deprivation_content_checked', document=FULL, **results,
        alignment=dict(**r['source'], definitions=list(MEANINGS), status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=False, new_verified_sentence_characters=0, new_covered_characters=0,
        verified_full_units={'kant-1784': 0, 'einstein-1905': 0}, semantic_equivalence_automatically_proved=False,
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})


if __name__ == '__main__':
    from scripts.audit_opening_scope import write_exact, encoded
    prepare()
    write_exact(ROOT / REPORT, encoded(build_report()))
