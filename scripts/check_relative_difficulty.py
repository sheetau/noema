"""Check deliberated choice, unselected responses, and a counterfactual comparison."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_relative_difficulty import ROOT, FULL, CORE, BASIS, ANNOTATIONS, PARENT, PARENT_BASIS, MEANINGS, PRIMITIVES, LIMITS, parent, build, closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol
from scripts.compose_relative_difficulty import TASK

INDEX = 'data/semantic-review-index-v92.json'
AUDIT = 'data/relative-difficulty-reading-v1.json'
REPORT = 'reports/relative-difficulty-v1.json'
DOC = 'docs/relative-difficulty-v1.md'
INVENTORY = 'artifacts/written-units-v1/kant-1784.json'


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
    assert new.document['declarations'][:-10] == old.document['declarations']
    assert new.document['statements'] == old.document['statements'] and len(new.document['statements']) == 51
    assert all(new.entries[n] == entry for n, entry in old.entries.items())
    assert set(new.entries) - set(old.entries) == set(MEANINGS) | set(PRIMITIVES)
    for path in read(INDEX)['works']['kant-1784']['reviews']:
        r = read(path); validate_hashes(ROOT, r['source_sha256'])
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
    assert core['statements'] == [] and core['declarations'] == closure(new.document, list(MEANINGS))
    assert reading() == read(AUDIT); validate_hashes(ROOT, read(AUDIT)['source_sha256'])
    return dict(new_definitions=8, new_primitives=2, preserved_statements=51, new_authored_assertions=0,
        preserved_review_selections=12, reviewed_nonblank_characters=2212, roundtrips=True,
        same_method_relative_difficulty_composed=True, lexical_equivalence_not_claimed=True)


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    write_exact(ROOT / AUDIT, encoded(reading()))


VALUES = ('none', 'light', 'heavy', 'full')
PEOPLE = VALUES + ('person', 'first', 'second', 'other')
SCENES = ('start', 'one', 'two')
DECLS = '''r zactor[] a.r zstart[] d.r zscale[a] c.r zless[a a] c.r zlow[] a.r zhigh[] a.r zband[a] c.
r zcapacity[a d a] c.r zrequired[a a d d a] c.r zavailable[a a d] c.
r zoutcomes[a a d d] c.r zselected[a a d d] c.r zsuccess[a a d d] c.'''
ARGS = ' '.join(('k z' + n + '[]') if n in ('actor', 'start', 'low', 'high') else ('p z' + n) for n, _ in TASK)


@lru_cache(None)
def generic_document():
    return fixture('r2dg r2dh r2dd', DECLS + 'q[k r2dg[' + ARGS + ']].q[k r2dh[' + ARGS + ''']].
q[k r2dd[k zactor[] k zstart[] p zscale p zrequired p zavailable p zoutcomes p zselected p zsuccess]].''')


def data(first='heavy', second='full', first_success=True, second_success=True, variant='baseline'):
    d = dict(scale=set(VALUES), less={(a, b) for i, a in enumerate(VALUES) for b in VALUES[i + 1:]}, low='none', high='full',
        capacity={'full'}, band={'heavy', 'full'}, available={'first', 'second'},
        outcomes={p: {'one', 'two'} for p in ('first', 'second')}, selected={p: {'one', 'two'} for p in ('first', 'second')},
        success={'first': {'one', 'two'} if first_success else set(), 'second': {'one', 'two'} if second_success else set()},
        required={'first': {'one': {first}, 'two': {first}}, 'second': {'one': {second}, 'two': {second}}})
    if variant == 'missing_success_cost': d['required']['first']['one'] = set()
    if variant == 'ambiguous_success_cost': d['required']['first']['one'] = {'light', 'heavy'}
    if variant == 'outside_success_cost': d['required']['first']['one'] = {'other'}
    if variant == 'missing_failed_cost':
        d['success']['first'] = set(); d['required']['first']['one'] = set()
    if variant == 'cheap_failed_route':
        d['success']['second'] = set(); d['required']['second'] = {'one': {'none'}, 'two': {'none'}}
    if variant == 'cheap_success_route': d['required']['second'] = {'one': {'light'}, 'two': {'light'}}
    if variant == 'easy_witness_unassessed_alternative':
        d['required']['first']['one'] = set(); d['required']['second'] = {'one': {'light'}, 'two': {'light'}}
    if variant == 'one_easy_path': d['required']['first']['one'] = {'light'}
    if variant == 'partial_success_only':
        d['success']['first'] = {'one'}; d['required']['first'] = {'one': {'none'}, 'two': {'none'}}
    if variant == 'only_failed_routes': d['success'] = {'first': set(), 'second': set()}
    if variant == 'no_methods': d['available'] = set()
    if variant == 'empty_selection': d['selected']['first'] = set()
    if variant == 'outside_selection': d['selected']['first'].add('start')
    if variant == 'missing_capacity': d['capacity'] = set()
    if variant == 'ambiguous_capacity': d['capacity'] = {'light', 'full'}
    if variant == 'outside_capacity': d['capacity'] = {'other'}
    if variant == 'unaffordable': d.update(capacity={'light'}, band={'light'})
    if variant == 'same_effort_smaller_capacity':
        d.update(capacity={'heavy'}, band={'heavy'}); d['required']['second'] = {'one': {'heavy'}, 'two': {'heavy'}}
    if variant == 'same_effort_more_reserve':
        d['band'] = {'full'}; d['required']['second'] = {'one': {'heavy'}, 'two': {'heavy'}}
    if variant == 'no_additional_resource':
        d.update(capacity={'none'}, band=set()); d['required'] = {p: {s: {'none'} for s in ('one', 'two')} for p in ('first', 'second')}
    if variant == 'empty_band': d['band'] = set()
    if variant == 'band_hole': d['band'] = {'light', 'full'}
    if variant == 'band_includes_low': d['band'].add('none')
    if variant == 'band_above_capacity': d.update(capacity={'heavy'}, band={'full'})
    if variant == 'cyclic_scale': d['less'].add(('full', 'none'))
    if variant in ('wrong_cost_actor', 'wrong_cost_start'): d['required'] = {p: {s: set() for s in ('one', 'two')} for p in ('first', 'second')}
    return d


def model(d, variant='baseline'):
    actual_costs = data()['required'] if variant in ('wrong_cost_actor', 'wrong_cost_start') else d['required']
    return dict(zactor=lambda: 'person', zstart=lambda: 'start', zscale=lambda v: v in d['scale'],
        zless=lambda a, b: (a, b) in d['less'], zlow=lambda: d['low'], zhigh=lambda: d['high'], zband=lambda v: v in d['band'],
        zcapacity=lambda p, s, amount: (p, s) == ('person', 'start') and amount in d['capacity'],
        zrequired=lambda p, method, start, end, amount: (p, start) == (
            'other' if variant == 'wrong_cost_actor' else 'person', 'one' if variant == 'wrong_cost_start' else 'start') and amount in actual_costs.get(method, {}).get(end, set()),
        zavailable=lambda p, method, start: (p, start) == ('person', 'start') and method in d['available'],
        zoutcomes=lambda p, method, start, end: (p, start) == ('person', 'start') and end in d['outcomes'].get(method, set()),
        zselected=lambda p, method, start, end: (p, start) == ('person', 'start') and end in d['selected'].get(method, set()),
        zsuccess=lambda p, method, start, end: (p, start) == ('person', 'start') and end in d['success'].get(method, set()))


def oracle(d):
    scale, order, low, high = (d[k] for k in ('scale', 'less', 'low', 'high'))
    ordered = low in scale and high in scale and low != high and all((v, v) not in order for v in scale) and all(
        a == b or ((a, b) in order) != ((b, a) in order) for a in scale for b in scale) and all(
        (a, c) in order for a in scale for b in scale for c in scale if (a, b) in order and (b, c) in order) and all(
        (x == low or (low, x) in order) and (x == high or (x, high) in order) for x in scale)
    def unique(values): return next(iter(values)) if len(values) == 1 and values <= scale else None
    limit = unique(d['capacity']); band = d['band']
    setting = ordered and limit is not None and bool(band) == (limit != low) and all(
        x in scale and (low, x) in order and (x == limit or (x, limit) in order) for x in band) and all(
        y in band for x in band for y in scale if (x, y) in order and (y == limit or (y, limit) in order))
    evaluated = True; feasible = []; easy = []
    for plan in d['available']:
        selected = d['selected'][plan]; valid = bool(selected) and selected <= d['outcomes'][plan]
        achieved = selected <= d['success'][plan]
        amounts = [unique(d['required'][plan].get(end, set())) for end in selected]
        evaluated &= valid and (not achieved or all(amount is not None for amount in amounts))
        possible = valid and achieved and limit is not None and all(amount is not None and (
            amount == limit or (amount, limit) in order) for amount in amounts)
        feasible.append(possible); easy.append(possible and all(amount not in band for amount in amounts))
    return [bool(setting and any(easy)), bool(setting and evaluated and any(feasible) and not any(easy)), bool(evaluated)]


@lru_cache(None)
def generic_checks():
    doc = generic_document(); rows = []
    for first, second, first_success, second_success in product(VALUES, VALUES, (False, True), (False, True)):
        d = data(first, second, first_success, second_success)
        actual = evaluate(doc, model(d), PEOPLE, SCENES, True); expected = oracle(d)
        assert actual == expected, (first, second, first_success, second_success, actual, expected)
        rows.append(dict(first=first, second=second, first_success=first_success, second_success=second_success, values=actual))
    names = ('missing_success_cost', 'ambiguous_success_cost', 'outside_success_cost', 'missing_failed_cost', 'cheap_failed_route',
        'cheap_success_route', 'easy_witness_unassessed_alternative', 'one_easy_path', 'partial_success_only', 'only_failed_routes', 'no_methods', 'empty_selection',
        'outside_selection', 'missing_capacity', 'ambiguous_capacity', 'outside_capacity', 'unaffordable',
        'same_effort_smaller_capacity', 'same_effort_more_reserve', 'no_additional_resource', 'empty_band', 'band_hole',
        'band_includes_low', 'band_above_capacity', 'cyclic_scale', 'wrong_cost_actor', 'wrong_cost_start')
    contrasts = {}
    for name in names:
        d = data(variant=name); actual = evaluate(doc, model(d, name), PEOPLE, SCENES, True)
        assert actual == oracle(d), (name, actual, oracle(d))
        contrasts[name] = actual
    assert contrasts['same_effort_smaller_capacity'] == [False, True, True]
    assert contrasts['same_effort_more_reserve'] == [True, False, True]
    assert contrasts['no_additional_resource'] == [True, False, True]
    assert contrasts['missing_failed_cost'] == [False, True, True]
    assert contrasts['easy_witness_unassessed_alternative'] == [True, False, False]
    for name in ('zscale', 'zless', 'zband', 'zcapacity', 'zrequired', 'zavailable', 'zoutcomes', 'zselected', 'zsuccess'):
        values = model(data()); values[name] = unknown
        try: evaluate(doc, values, PEOPLE, SCENES, True)
        except ValueError as error: assert 'Unknown' in str(error)
        else: raise AssertionError(name)
    return dict(combinations=rows, contrasts=contrasts, unknown_inputs_refused=9,
                same_absolute_requirement_can_have_different_actor_relative_difficulty=True,
                inability_and_missing_assessments_not_counted_as_difficulty=True)


SOURCE_PEOPLE = VALUES + ('person', 'process', 'method', 'faculty', 'other', 'dimension')
SOURCE_SCENES = ('start', 'end')
SOURCE_DECLS = '''r zperson[] a.r zdimension[] a.r zprocess[] a.r zstart[] d.r zend[] d.
r zscale[a] c.r zless[a a] c.r zlow[] a.r zhigh[] a.r zband[a] c.'''
SOURCE_ARGS = 'k zperson[] k zdimension[] p zscale p zless k zlow[] k zhigh[] p zband'


def source_values(doc, variant='baseline'):
    values = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
    base = model(data())
    values.update({k: base[k] for k in ('zscale', 'zless', 'zlow', 'zhigh', 'zband')})
    plans = {'process', 'other'} if variant in ('cheap_failed_route', 'cheap_success_route') else {'process'}
    def available(p, method, start):
        return p == 'person' and ((method in plans and start == 'start') or (method == 'method' and start == 'end'))
    def outcomes(p, method, start, end): return available(p, method, start) and end == 'end'
    values.update(zperson=lambda: 'person', zdimension=lambda: 'dimension', zprocess=lambda: 'process', zstart=lambda: 'start', zend=lambda: 'end',
        aa=lambda p: p == 'person', ab=lambda faculty, p, point: (faculty, p) == ('faculty', 'person'),
        ac=lambda p, faculty, act, point: variant != 'no_future_capacity' and (p, faculty, act, point) == ('person', 'faculty', 'method', 'end'),
        ad=lambda *args: False, ae=available, af=outcomes, ap=outcomes,
        hzsc=lambda p, anchor, point: p == 'person' and anchor == point,
        hzsd=lambda p, anchor, point: p == 'person' and anchor == point,
        hzse=lambda p, point: p == 'person', hzsf=lambda *args: False,
        hzsg=lambda p, method, anchor, point: (p, method) == ('person', 'method'),
        hzsh=lambda p, method, anchor, point: p == 'person',
        ia=lambda p, anchor, point: (p, anchor) == ('person', 'end'),
        ic=lambda first, last, anchor: (first, last, anchor) == ('start', 'end', 'end'),
        ag=lambda method, first, last: variant != 'no_change' and method in plans and (first, last) == ('start', 'end'),
        la=lambda p, method, first, last: p == 'person' and method in plans and (first, last) == ('start', 'end'),
        dg=lambda method, point: method in plans and point == 'end',
        df=lambda p, method, point: variant != 'no_participation' and p == 'person' and method in plans and point == 'end',
        h4m=lambda part, p, point: (part, p, point) == ('faculty', 'person', 'end'),
        h4n=lambda p, part, method, point: variant != 'no_self_work' and (
            p, part, point) == ('other' if variant == 'other_worker' else 'person', 'faculty', 'end') and method in plans,
        g3=lambda method, p, description, point: variant != 'no_producing_cause' and method in plans and (
            method != 'other' or variant != 'cheap_failed_route') and (p, symbol(description), point) == (
            'person', 'up' if variant == 'other_goal_description' else 'h4l', 'end'),
        hzzi=lambda p, dimension, point, amount: (p, dimension, point, amount) == ('person', 'dimension', 'start', 'full'),
        hzzh=lambda agent, beneficiary, dimension, method, start, end, amount: method in plans and (
            agent, beneficiary, dimension, start, end, amount) == (
            'other' if variant == 'other_effort_agent' else 'person',
            'other' if variant == 'other_beneficiary' else 'person',
            'method' if variant == 'other_dimension' else 'dimension', 'start', 'end',
            'light' if method == 'other' else 'heavy'))
    if variant == 'more_reserve': values['zband'] = lambda amount: amount == 'full'
    return values


@lru_cache(None)
def source_checks():
    doc = fixture('r2di bf up h4p', SOURCE_DECLS + '''
q[t[k bf[k zperson[]]][k zstart[]]].q[t[k up[k zperson[]]][k zend[]]].
q[k h4p[k zperson[] k zprocess[] k zstart[] k zend[] k zend[]]].
q[t[k r2di[''' + SOURCE_ARGS + ']][k zstart[]]].')
    rows = {}
    names = ('baseline', 'no_self_work', 'other_worker', 'no_participation', 'no_producing_cause', 'other_goal_description',
             'no_change', 'no_future_capacity', 'other_effort_agent', 'other_beneficiary', 'other_dimension', 'more_reserve',
             'cheap_failed_route', 'cheap_success_route')
    for name in names:
        actual = evaluate(doc, source_values(doc, name), SOURCE_PEOPLE, SOURCE_SCENES, True)
        achieved = name not in ('no_self_work', 'other_worker', 'no_participation', 'no_producing_cause', 'other_goal_description', 'no_change', 'no_future_capacity')
        expected = [True, name != 'no_future_capacity', achieved, name in ('baseline', 'cheap_failed_route')]
        assert actual == expected, (name, actual, expected)
        rows[name] = actual
    for name in ('hzzh', 'hzzi', 'h4n', 'g3'):
        values = source_values(doc); values[name] = unknown
        try: evaluate(doc, values, SOURCE_PEOPLE, SOURCE_SCENES, True)
        except ValueError as error: assert 'Unknown' in str(error)
        else: raise AssertionError(name)
    return dict(contrasts=rows, unknown_inputs_refused=4, native_current_incapacity_future_capacity_and_self_work_executed=True,
                successful_route_and_cheap_failed_route_not_mixed=True)


@lru_cache(None)
def quotation_checks():
    doc = fixture('r2di uc', SOURCE_DECLS + 'r znode[] a.q[k uc[k znode[] k zperson[] r[k r2di[' + SOURCE_ARGS + ']] k zstart[]]].')
    expected = doc['statements'][0]['body']['arguments'][2]['body']; rows = {}
    for variant in ('baseline', 'false_attribution', 'wrong_person', 'wrong_context', 'obsolete_content'):
        values = {e['name']: unknown for e in doc['declarations'] if e['kind'] == 'primitive'}
        wanted = deepcopy(expected)
        if variant == 'obsolete_content': wanted['symbol'] = 'hb2'
        values.update(zperson=lambda: 'person', znode=lambda: 'process', zstart=lambda: 'start',
            uc=lambda node, author, content, scene: variant != 'false_attribution' and (node, author, scene) == (
                'process', 'other' if variant == 'wrong_person' else 'person', 'end' if variant == 'wrong_context' else 'start') and json.loads(content.syntax) == wanted)
        actual = evaluate(doc, values, SOURCE_PEOPLE, SOURCE_SCENES)
        assert actual == [variant == 'baseline'], (variant, actual)
        rows[variant] = actual
    return dict(contrasts=rows, world_contents_unknown=True, rank_zero_quote_accepted=True,
                diagnostic_quotation_not_added_to_manuscript=True)


def reading():
    u = next(u for u in read(INVENTORY)['units'] if u['id'] == 'kant-1784:u0010')
    paths = {INDEX, INVENTORY, FULL, BASIS, PARENT, PARENT_BASIS, 'reports/unselected-continuation-v1.json'}
    return dict(status='actor_relative_difficulty_of_self_development_interpretation_candidate', reviewer='assistant_review',
        document=FULL, meaning_basis=BASIS, source=dict(unit=u['id'], unit_sha256=u['text_sha256'],
            range=[41, 124], text=u['text'][41:124]), definitions=list(MEANINGS),
        decision='同じ本人による自己作業で達成する同じ方法と経路を評価し、本人の上限に対する必要量と余力を結ぶ。達成方法はあるが余裕を確保できる方法がないという困難さの候補であり、到達不能、未評価、単なる煩わしさとは区別する。句全体や全個人への主張は未確認。',
        references=[
            dict(url='https://korpora.org/Kant/aa07/147.html', title='Kant, Anthropologie AA VII147', accessed='2026-10-20',
                 use='容易さと煩わしさを区別し、本人の力と必要な投入に対する余裕を参照する。今回の質的尺度、方法の結果選択、到達可能な困難さの範囲は形式化上の選択であり、1784年の語義を一意に導くものではない。'),
            dict(url='https://korpora.org/Kant/aa08/036.html', title='Kant, Aufklärung AA VIII036', accessed='2026-10-20',
                 use='個人の離脱の困難と、自己の精神への働きかけで成功した少数者を述べる文脈を確認する。AA転記であり原版画像の検証ではない。')],
        interpretation_limits=LIMITS, actor_relative_difficulty_composed=True, whole_sentence_semantically_verified=False,
        whole_unit_semantically_verified=False, new_verified_sentence_characters=0, semantic_equivalence_automatically_proved=False,
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})


def build_report():
    results = {}
    for name, fn in [('generic', generic_checks), ('source', source_checks), ('quotation', quotation_checks), ('structure', structure_checks)]:
        results[name] = fn(); print(name + ' checked', flush=True)
    r = reading()
    paths = set(build()) | set(catalog().source_sha256) | set(r['source_sha256']) | {
        AUDIT, DOC, 'scripts/compose_relative_difficulty.py', 'scripts/check_relative_difficulty.py', 'scripts/register_relative_difficulty.py',
        'tests/test_relative_difficulty.py', 'scripts/compose_graded_change.py', 'scripts/compose_limits.py',
        'scripts/check_pastoral_roles.py', 'scripts/check_motive_causes.py', 'scripts/compose_grounded_step.py',
        'noema/constructed.py', 'noema/constructed_semantics.py', 'noema/meaning_catalog.py', 'noema/semantic_reviews.py', 'noema/script.py'}
    return dict(status='actor_relative_difficulty_and_native_self_development_checked', document=FULL, **results,
        alignment=dict(**r['source'], definitions=list(MEANINGS), status='explicit_interpretive_annotation'),
        actor_relative_difficulty_composed=True, whole_sentence_semantically_verified=False,
        new_verified_sentence_characters=0, new_covered_characters=0,
        verified_full_units={'kant-1784': 0, 'einstein-1905': 0}, semantic_equivalence_automatically_proved=False,
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})


if __name__ == '__main__':
    from scripts.audit_opening_scope import write_exact, encoded
    prepare()
    write_exact(ROOT / REPORT, encoded(build_report()))
