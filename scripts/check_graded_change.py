"""Check qualitative actual progress without replacing it by binary acquisition."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_graded_change import ROOT, FULL, CORE, BASIS, ANNOTATIONS, PARENT, PARENT_BASIS, MEANINGS, LIMITS, parent, build, closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol

INDEX = 'data/semantic-review-index-v89.json'
AUDIT = 'data/graded-change-reading-v1.json'
REPORT = 'reports/graded-change-v1.json'
DOC = 'docs/graded-change-v1.md'
INVENTORY = 'artifacts/written-units-v1/kant-1784.json'
VALUES = ('low', 'nearA', 'nearB', 'top')
PEOPLE = VALUES + ('person', 'process', 'other')
SCENES = ('before', 'after', 'middle', 'now', 'outside')


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
    assert new.document['declarations'][:-5] == old.document['declarations']
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
    return dict(new_definitions=5, new_primitives=0, preserved_statements=51, new_authored_assertions=0,
        preserved_review_selections=12, reviewed_nonblank_characters=2212, roundtrips=True,
        reference_schema_not_grounded_as_nature=True)


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    write_exact(ROOT / AUDIT, encoded(reading()))


SCALE_DECLS = 'r zscale[a] c.r zless[a a] c.r znear[a] c.r zlow[] a.r zhigh[] a.'
SCALE_ARGS = 'p zscale p zless p znear k zlow[] k zhigh[] p zassessed'
CHANGE_ARGS = 'p zhistory p zbefore k zperson[] k zprocess[] k zearlier[] k zlater[] p zchanges p zaffected ' + SCALE_ARGS


@lru_cache(None)
def generic_document():
    return fixture('r2co th', SCALE_DECLS + '''
r zassessed[d a] c.r zhistory[d] c.r zbefore[d d] c.r zperson[] a.r zprocess[] a.
r zearlier[] d.r zlater[] d.r zanchor[] d.r zchanges[a d d] c.r zaffected[a a d d] c.
q[k r2cm[''' + SCALE_ARGS + ''' k zanchor[]]].
q[k r2cn[''' + CHANGE_ARGS + ''']].
q[k r2co[''' + CHANGE_ARGS + ''' k zanchor[]]].
q[w[k th[p zhistory p zbefore k zprocess[] k zearlier[] k zlater[] p zchanges
 b point[k r2cm[''' + SCALE_ARGS + ''' v point]]]]
 [k zaffected[k zperson[] k zprocess[] k zearlier[] k zlater[]]]].''')


def data(initial='low', final='nearB', current='nearB', variant='baseline'):
    order = [(a, b) for i, a in enumerate(VALUES) for b in VALUES[i + 1:]]
    points = SCENES[:4]
    d = dict(scale=set(VALUES), edges=set(order), near={'nearA', 'nearB'}, low='low', high='top',
        assigned={'before': {initial}, 'after': {final}, 'middle': {final}, 'now': {current}},
        history=set(points), time={(a, b) for i, a in enumerate(points) for b in points[i + 1:]},
        change=True, affected=True, anchor='now')
    if variant == 'no_change': d['change'] = False
    if variant in ('no_affected_person', 'other_person', 'other_process'): d['affected'] = False
    if variant.startswith('missing_'):
        d['history'].remove(dict(missing_before='before', missing_after='after', missing_anchor='now')[variant])
    if variant == 'cyclic_history': d['time'].add(('now', 'before'))
    if variant == 'anchor_before_change': d['anchor'] = 'before'
    if variant == 'same_endpoint': d['later'] = 'before'
    if variant == 'reversed_endpoints': d.update(earlier='after', later='before')
    if variant == 'empty_prior': d['assigned']['before'] = set()
    if variant == 'ambiguous_prior': d['assigned']['before'] = {'low', 'nearA'}
    if variant == 'outside_prior': d['assigned']['before'] = {'other'}
    if variant == 'empty_later': d['assigned']['after'] = set()
    if variant == 'ambiguous_later': d['assigned']['after'] = {'nearA', 'nearB'}
    if variant == 'empty_middle': d['assigned']['middle'] = set()
    if variant == 'middle_lost': d['assigned']['middle'] = {'low'}
    if variant == 'middle_reached_target': d['assigned']['middle'] = {'top'}
    if variant == 'middle_near_lower': d['assigned']['middle'] = {'nearA'}
    if variant == 'empty_current': d['assigned']['now'] = set()
    if variant == 'ambiguous_current': d['assigned']['now'] = {'nearA', 'nearB'}
    if variant == 'empty_near': d['near'] = set()
    if variant == 'near_hole': d['near'] = {'nearA'}
    if variant == 'near_top': d['near'].add('top')
    if variant == 'near_low': d['near'].add('low')
    if variant == 'near_outside': d['near'].add('other')
    if variant == 'reflexive_scale': d['edges'].add(('nearA', 'nearA'))
    if variant == 'cyclic_scale': d['edges'].add(('nearB', 'nearA'))
    if variant == 'incomparable_scale': d['edges'].remove(('nearA', 'nearB'))
    if variant == 'nontransitive_scale': d['edges'].remove(('low', 'nearB'))
    if variant == 'outside_high': d['high'] = 'other'
    if variant == 'same_bounds': d['high'] = 'low'
    return d


def model(d, variant='baseline'):
    v = dict(zscale=lambda x: x in d['scale'], zless=lambda a, b: (a, b) in d['edges'], znear=lambda x: x in d['near'],
        zlow=lambda: d['low'], zhigh=lambda: d['high'], zassessed=lambda s, x: x in d['assigned'].get(s, set()),
        zhistory=lambda s: s in d['history'], zbefore=lambda a, b: (a, b) in d['time'],
        zperson=lambda: 'person', zprocess=lambda: 'process', zearlier=lambda: d.get('earlier', 'before'),
        zlater=lambda: d.get('later', 'after'), zanchor=lambda: d['anchor'],
        zchanges=lambda p, a, b: d['change'] and (p, a, b) == ('process', 'before', 'after'),
        zaffected=lambda person, process, a, b: d['affected'] and (person, process, a, b) == ('person', 'process', 'before', 'after'))
    if variant == 'other_person': v['zaffected'] = lambda p, c, a, b: (p, c, a, b) == ('other', 'process', 'before', 'after')
    if variant == 'other_process': v['zaffected'] = lambda p, c, a, b: (p, c, a, b) == ('person', 'other', 'before', 'after')
    return v


def oracle(d):
    # Set and order oracle independent of the Noema construction machinery.
    def total(elements, edges):
        return all((a, a) not in edges for a in elements) and all(
            a == b or ((a, b) in edges) != ((b, a) in edges) for a in elements for b in elements) and all(
            (a, c) in edges for a in elements for b in elements for c in elements if (a, b) in edges and (b, c) in edges)
    scale, edges, low, high, near = (d[n] for n in ('scale', 'edges', 'low', 'high', 'near'))
    valid = low in scale and high in scale and low != high and total(scale, edges) and all(
        (x == low or (low, x) in edges) and (x == high or (x, high) in edges) for x in scale)
    valid = valid and bool(near) and near <= scale - {low, high} and all(
        y in near for x in near for y in scale - {high} if (x, y) in edges)
    def value(s):
        values = d['assigned'].get(s, set())
        return next(iter(values)) if len(values) == 1 and values <= scale else None
    def near_at(s): return valid and value(s) in near
    a, b, now = d.get('earlier', 'before'), d.get('later', 'after'), d['anchor']
    history = d['history']; temporal = total(history, d['time']) and a in history and b in history and (a, b) in d['time']
    event = temporal and d['change'] and (a, b) == ('before', 'after') and d['affected']
    change = event and valid and value(a) is not None and value(b) is not None and (value(a), value(b)) in edges and near_at(b)
    retained = change and now in history and (b == now or (b, now) in d['time']) and all(
        near_at(p) for p in history if (b == p or (b, p) in d['time']) and (p == now or (p, now) in d['time']))
    binary = event and not near_at(a) and near_at(b)
    return [bool(x) for x in (near_at(now), change, retained, binary)]


@lru_cache(None)
def generic_checks():
    doc = generic_document(); run = lambda values: evaluate(doc, values, PEOPLE, SCENES, True)
    rows = []
    for initial, final, current in product(VALUES, repeat=3):
        d = data(initial, final, current); actual = run(model(d)); expected = oracle(d)
        assert actual == expected, (initial, final, current, actual, expected)
        rows.append(dict(initial=initial, final=final, current=current, values=actual))
    contrasts = {}
    variants = ('no_change', 'no_affected_person', 'other_person', 'other_process', 'missing_before', 'missing_after', 'missing_anchor',
        'cyclic_history', 'anchor_before_change', 'same_endpoint', 'reversed_endpoints', 'empty_prior', 'ambiguous_prior', 'outside_prior',
        'empty_later', 'ambiguous_later', 'empty_middle', 'middle_lost', 'middle_reached_target', 'middle_near_lower',
        'empty_current', 'ambiguous_current', 'empty_near', 'near_hole', 'near_top', 'near_low', 'near_outside',
        'reflexive_scale', 'cyclic_scale', 'incomparable_scale', 'nontransitive_scale', 'outside_high', 'same_bounds')
    for name in variants:
        d = data(variant=name); actual = run(model(d, name)); expected = oracle(d)
        assert actual == expected, (name, actual, expected)
        contrasts[name] = actual
    for n in ('zscale', 'zless', 'znear', 'zassessed', 'zhistory', 'zbefore', 'zchanges', 'zaffected'):
        v = model(data()); v[n] = unknown
        try: run(v)
        except ValueError as error: assert 'Unknown' in str(error)
        else: raise AssertionError(n)
    witness = next(r for r in rows if (r['initial'], r['final'], r['current']) == ('nearA', 'nearB', 'nearB'))
    assert witness['values'] == [True, True, True, False]
    return dict(combinations=rows, contrasts=contrasts, unknown_inputs_refused=8,
                progress_within_near_region_differs_from_binary_acquisition=True, fixed_numeric_threshold_not_supplied=True)


SOURCE_PEOPLE = VALUES + ('person', 'process', 'method', 'faculty', 'reference')
SOURCE_SCENES = ('before', 'after', 'now')
SOURCE_DECLS = SCALE_DECLS + 'r zperson[] a.r zreference[] a.r zanchor[] d.r zmeasured[a i[h[a] e] a d d a] c.'
SOURCE_ARGS = 'k zperson[] k zreference[] p zscale p zless p znear k zlow[] k zhigh[] p zmeasured'


@lru_cache(None)
def source_document():
    return fixture('r2cp', SOURCE_DECLS + 'q[t[k r2cp[' + SOURCE_ARGS + ']][k zanchor[]]].')


def source_values(doc, variant='baseline'):
    v = {e['name']: unknown for e in doc['declarations'] if e['kind'] == 'primitive'}
    degrees = dict(before='nearA', after='nearB', now='nearB')
    v.update({n:fn for n,fn in model(data()).items() if n in ('zscale', 'zless', 'znear', 'zlow', 'zhigh')})
    def measured(person, desc, reference, anchor, point, degree):
        return (person, symbol(desc), reference, anchor) == (
            'method' if variant == 'wrong_person' else 'person', 'bm' if variant == 'wrong_property' else 'bf',
            'method' if variant == 'wrong_reference' else 'reference', 'after' if variant == 'wrong_anchor' else 'now') and degree == degrees.get(point)
    def opportunity(person, point): return person == 'person' and point in ('before', 'after')
    def available(person, method, point): return method == 'method' and opportunity(person, point)
    def results(person, method, point, result): return available(person, method, point) and result == 'now'
    v.update(zperson=lambda: 'person', zreference=lambda: 'reference', zanchor=lambda: 'now', zmeasured=measured,
        aa=lambda p: p == 'person', ab=lambda faculty, p, s: (faculty, p) == ('faculty', 'person'),
        ac=lambda p, faculty, act, s: variant == 'currently_capable' and (p, faculty, act, s) == ('person', 'faculty', 'process', 'now'),
        ad=lambda *args: False, ae=available, af=results, ap=results,
        hzsc=lambda p, anchor, point: anchor == 'now' and opportunity(p, point),
        hzsd=lambda p, anchor, point: (p, anchor) == ('person', 'now'), hzse=opportunity,
        hzsf=lambda *args: False, hzsg=lambda p, m, anchor, point: (p, m, anchor) == ('person', 'method', 'now'),
        hzsh=lambda p, m, anchor, point: (p, anchor) == ('person', 'now'),
        ia=lambda p, anchor, point: (p, anchor) == ('person', 'now') and point in SOURCE_SCENES,
        ic=lambda a, b, anchor: anchor == 'now' and SOURCE_SCENES.index(a) < SOURCE_SCENES.index(b),
        ag=lambda process, a, b: variant != 'no_process' and (process, a, b) == ('process', 'before', 'after'),
        la=lambda p, process, a, b: (p, process, a, b) == ('person', 'process', 'before', 'after'))
    return v


@lru_cache(None)
def source_checks():
    doc = source_document(); rows = {}
    for name in ('baseline', 'wrong_person', 'wrong_property', 'wrong_reference', 'wrong_anchor', 'currently_capable', 'no_process'):
        actual = evaluate(doc, source_values(doc, name), SOURCE_PEOPLE, SOURCE_SCENES, True)
        assert actual == [name == 'baseline'], (name, actual)
        rows[name] = actual
    for n in ('zmeasured', 'hzsh'):
        values = source_values(doc); values[n] = unknown
        try: evaluate(doc, values, SOURCE_PEOPLE, SOURCE_SCENES, True)
        except ValueError as error: assert 'Unknown' in str(error)
        else: raise AssertionError(n)
    return dict(contrasts=rows, unknown_inputs_refused=2, native_current_immaturity_executed=True,
                reference_and_assessment_are_diagnostic_parameters_not_a_completed_nature_definition=True)


@lru_cache(None)
def quotation_checks():
    doc = fixture('r2cp uc', SOURCE_DECLS + 'r znode[] a.q[k uc[k znode[] k zperson[] r[k r2cp[' + SOURCE_ARGS + ']] k zanchor[]]].')
    expected = doc['statements'][0]['body']['arguments'][2]['body']
    rows = {}
    for variant in ('baseline', 'false_attribution', 'wrong_person', 'wrong_context', 'obsolete_content'):
        values = {e['name']: unknown for e in doc['declarations'] if e['kind'] == 'primitive'}
        wanted = deepcopy(expected)
        if variant == 'obsolete_content': wanted['symbol'] = 'hb2'
        values.update(zperson=lambda: 'person', znode=lambda: 'process', zanchor=lambda: 'now',
            uc=lambda node, author, content, scene: variant != 'false_attribution' and (node, author, scene) == (
                'process', 'method' if variant == 'wrong_person' else 'person', 'after' if variant == 'wrong_context' else 'now') and json.loads(content.syntax) == wanted)
        actual = evaluate(doc, values, SOURCE_PEOPLE, SOURCE_SCENES)
        assert actual == [variant == 'baseline'], (variant, actual)
        rows[variant] = actual
    return dict(contrasts=rows, world_contents_unknown=True, rank_zero_quote_accepted=True,
                diagnostic_quotation_not_added_to_manuscript=True)


def reading():
    u = next(u for u in read(INVENTORY)['units'] if u['id'] == 'kant-1784:u0010')
    paths = {INDEX, INVENTORY, FULL, BASIS, PARENT, PARENT_BASIS,
             'reports/graded-modality-v1.json', 'reports/retained-attitudes-v1.json'}
    return dict(status='graded_change_schema_with_nature_reference_unfilled', reviewer='assistant_review',
        document=FULL, meaning_basis=BASIS, source=dict(unit=u['id'], unit_sha256=u['text_sha256'],
            range=[62, 107], text=u['text'][62:107]), definitions=list(MEANINGS),
        decision='近さの状態と、実際に程度が進み近い状態を保つことを区別する。前端が既に近接域内でも進行を認める。本性の比較特性と評価の根拠は未充足の引数として残し、句全体の完成とはしない。',
        references=[
            dict(url='https://lexika.digitale-sammlungen.de/adelung//lemma/bsb00009133_2_0_600', title='Adelung, Die Natur', accessed='2026-10-20',
                 use='習慣が別の本性となる用法と、起源としての自然の語義がある。現在の定着と生来の起源を同一視しない。具体的な比較特性は未確定。'),
            dict(url='https://www.duden.de/rechtschreibung/beinahe', title='Duden, beinahe', accessed='2026-10-20',
                 use='近似の意味と異なる使用例を確認した。程度の尺度、上端の排除、取得との作用範囲は今回の形式化の明示的な選択であり、辞書から一意に決まるとはしない。')],
        interpretation_limits=LIMITS, nature_reference_fully_composed=False, whole_sentence_semantically_verified=False,
        whole_unit_semantically_verified=False, new_verified_sentence_characters=0,
        semantic_equivalence_automatically_proved=False,
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})


def build_report():
    results = {}
    for name, fn in [('generic', generic_checks), ('source', source_checks), ('quotation', quotation_checks), ('structure', structure_checks)]:
        results[name] = fn(); print(name + ' checked', flush=True)
    r = reading()
    paths = set(build()) | set(catalog().source_sha256) | set(r['source_sha256']) | {
        AUDIT, DOC, 'scripts/compose_graded_change.py', 'scripts/check_graded_change.py', 'scripts/register_graded_change.py',
        'tests/test_graded_change.py', 'scripts/compose_limits.py', 'scripts/check_pastoral_roles.py', 'scripts/check_motive_causes.py',
        'scripts/compose_grounded_step.py', 'noema/constructed.py', 'noema/constructed_semantics.py',
        'noema/meaning_catalog.py', 'noema/semantic_reviews.py', 'noema/script.py'}
    return dict(status='graded_actual_change_and_near_retention_checked', document=FULL, **results,
        alignment=dict(**r['source'], definitions=list(MEANINGS), status='explicit_interpretive_annotation'),
        nature_reference_fully_composed=False, whole_sentence_semantically_verified=False,
        new_verified_sentence_characters=0, new_covered_characters=0,
        verified_full_units={'kant-1784': 0, 'einstein-1905': 0}, semantic_equivalence_automatically_proved=False,
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})


if __name__ == '__main__':
    from scripts.audit_opening_scope import write_exact, encoded
    prepare()
    write_exact(ROOT / REPORT, encoded(build_report()))
