"""Check kind-wise generalization against the misleading pooled alternative."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_conjoined_kinds import ROOT, SOURCE, SOURCE_BASIS, LIBRARY, BASIS, MEANINGS, LIMITS, catalog, build, closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown
from scripts import check_conditioned_persistence as previous

REPORT = 'reports/conjoined-kinds-v1.json'
AUDIT = 'data/conjoined-kinds-reading-v1.json'
DOC = 'docs/conjoined-kinds-v1.md'
INDEX = 'data/semantic-review-index-v100.json'
INVENTORY = 'artifacts/written-units-v1/kant-1784.json'
EXTRA = '''r zitems[a] c.r zobjects[a] a.r zpersons[a] a.r zanchors[a] d.r zpreferred[a a] c.
r zbranches[a a d d] c.r zfutures[a a d d d] c.r zfirst[] a.r zsecond[] a.'''
BODY_ARGS = 'p zobjects p zpersons p zanchors p zbranches p zfutures'
ALL_ARGS = 'p zitems p zobjects p zpersons p zanchors p zpreferred p zbranches p zfutures'


def read(path): return json.loads((ROOT / path).read_text(encoding='utf-8'))


@lru_cache(None)
def local_catalog(): return load_catalog(ROOT, BASIS)


def fixture(roots, suffix):
    doc = deepcopy(local_catalog().document)
    doc.update(declarations=closure(doc, roots), statements=[])
    return parse(format_graph(doc, 'compact') + suffix)


def normal(scope, relation, response):
    if any((x, x) in relation for x in scope): return False
    if any((x, y) in relation and (y, z) in relation and (x, z) not in relation for x in scope for y in scope for z in scope): return False
    minima = {x for x in scope if not any((y, x) in relation for y in scope)}
    return bool(minima) and all(x in minima or any((y, x) in relation for y in minima) for x in scope) and minima <= response


@lru_cache(None)
def generic_checks():
    doc = fixture(['r2fa'], '''r zleft[a] c.r zright[a] c.r zorder[a a] c.r zresponse[a] c.
q[k r2fa[p zleft p zright p zorder p zresponse]].
q[k r2bg[i[item a][x[k zleft[v item]][k zright[v item]]] p zorder p zresponse]].''')
    def run(items, left, right, relation, response):
        values = dict(zleft=lambda x: x in left, zright=lambda x: x in right,
            zorder=lambda x, y: (x, y) in relation, zresponse=lambda x: x in response)
        actual = evaluate(doc, values, items, ('scene',), True)
        assert actual == [normal(left, relation, response) and normal(right, relation, response), normal(left | right, relation, response)]
        return actual
    items = ('one', 'two'); subsets = [set(x for x, b in zip(items, bits) if b) for bits in product((False, True), repeat=2)]
    count = 0
    for bits in product((False, True), repeat=4):
        relation = set(pair for pair, b in zip(product(items, repeat=2), bits) if b)
        for left, right, response in product(subsets, repeat=3):
            run(items, left, right, relation, response); count += 1
    cases = {
        'one_kind_erased_by_pooling': ({'one'}, {'two'}, {('one', 'two')}, {'one'}),
        'reverse_kind_erased': ({'one'}, {'two'}, {('two', 'one')}, {'two'}),
        'both_kinds_respond': ({'one'}, {'two'}, {('one', 'two')}, {'one', 'two'}),
        'overlap_allowed': ({'one', 'two'}, {'two'}, {('two', 'one')}, {'two'}),
        'within_kind_exception': ({'one', 'three'}, {'two'}, {('one', 'three')}, {'one', 'two'}),
        'incomparable_counterexample': ({'one', 'three'}, {'two'}, set(), {'one', 'two'}),
        'within_kind_cycle': ({'one', 'three'}, {'two'}, {('one', 'three'), ('three', 'one')}, {'one', 'two', 'three'}),
        'cross_kind_cycle_not_a_within_kind_order': ({'one'}, {'two'}, {('one', 'two'), ('two', 'one')}, {'one', 'two'}),
        'empty_second_kind': ({'one'}, set(), set(), {'one'}),
    }
    rows = {name: run(('one', 'two', 'three'), *args) for name, args in cases.items()}
    assert rows['one_kind_erased_by_pooling'] == rows['reverse_kind_erased'] == [False, True]
    assert rows['cross_kind_cycle_not_a_within_kind_order'] == [True, False]
    for name in ('zleft', 'zright', 'zorder', 'zresponse'):
        values = dict(zleft=lambda x: x == 'one', zright=lambda x: x == 'two', zorder=lambda *args: False, zresponse=lambda x: True)
        values[name] = unknown
        try: evaluate(doc, values, items, ('scene',), True)
        except ValueError as error: assert 'Unknown' in str(error)
        else: raise AssertionError(name)
    return dict(combinations=count, contrasts=rows, unknown_inputs_refused=4,
        pooling_counterexample_verified=True, neither_frequency_nor_collective_action=True)


@lru_cache(None)
def source_document(boundary):
    text = EXTRA + 'q[k r2fb[k zfirst[] ' + BODY_ARGS + ']].q[k r2fb[k zsecond[] ' + BODY_ARGS + ']].'
    text += 'q[k r2fc[' + ALL_ARGS + ']].'
    text += '''q[k r2bg[i[item a][w[k zitems[v item]][x[t[k hd2[k zobjects[v item]]][k zanchors[v item]]][t[k h22[k zobjects[v item]]][k zanchors[v item]]]]]
p zpreferred i[item a][k r2fb[v item ''' + BODY_ARGS + ']]]].'
    doc = fixture(['r2fc'], text)
    if boundary:
        replacements = parse('''p:r zkindfirst[a d] c.r zkindsecond[a d] c.r zstate[a d] c.
d hd2[object a] e[b point[k zkindfirst[v object v point]]].
d h22[object a] e[b point[k zkindsecond[v object v point]]].
d bf[person a] e[b point[k zstate[v person v point]]].''')['declarations']
        by_name = {d['name']: d for d in replacements[3:]}
        doc['declarations'] = replacements[:3] + [deepcopy(by_name.get(d['name'], d)) for d in doc['declarations']]
        roots = ['r2fc'] + [d['name'] for d in parse('p:' + EXTRA)['declarations']]
        doc['declarations'] = closure(doc, roots)
    return parse(format_graph(doc, 'compact'))


def source_values(doc, variant='baseline', boundary=True):
    values = previous.source_values(doc, variant, boundary)
    def identity(o, p, anchor):
        return (o, p, anchor) in (('object', 'person', 'anchor'), ('other', 'person', 'anchor2'))
    values.update(zfirst=lambda: 'object', zsecond=lambda: 'other',
        zitems=lambda item: item in ('object', 'other'),
        zobjects=lambda item: 'object' if variant == 'second_object' and item == 'other' else item,
        zpersons=lambda item: 'other' if variant == 'second_person' and item == 'other' else 'person',
        zanchors=lambda item: 'anchor' if item == 'object' or variant == 'second_anchor' else 'anchor2',
        zpreferred=lambda a, b: (a, b) == ('object', 'other'),
        zkindfirst=lambda o, anchor: (o, anchor) == ('object', 'anchor'),
        zkindsecond=lambda o, anchor: (o, anchor) == ('other', 'anchor2'),
        hx2=lambda p, o, a, s: p == 'person' and o in ('object', 'other') and a == 'act' and s in ('first', 'last'),
        zbranches=lambda o, p, anchor, branch: identity(o, p, anchor) and branch in ('keep', 'stop') and not (variant == 'second_branches' and o == 'other'),
        zfutures=lambda o, p, anchor, branch, point: identity(o, p, anchor) and not (variant == 'second_futures' and o == 'other') and
            (branch == 'keep' and point in ('first', 'last') or branch == 'stop' and point == 'released'))
    if variant == 'category_anchor': values['zkindsecond'] = lambda o, anchor: (o, anchor) == ('other', 'anchor')
    if variant == 'category_object': values['zkindsecond'] = lambda o, anchor: (o, anchor) == ('object', 'anchor2')
    if variant == 'exclude_second_case': values['zitems'] = lambda item: item == 'object'
    return values


@lru_cache(None)
def binding_checks():
    doc = source_document(True); scenes = previous.SCENES + ('anchor2',); rows = {}
    for name in ('baseline', 'second_object', 'second_person', 'second_anchor', 'second_branches', 'second_futures',
                 'category_anchor', 'category_object', 'exclude_second_case', 'cause_act', 'mature_last'):
        actual = evaluate(doc, source_values(doc, name), previous.PEOPLE, scenes, True)
        both_fail = name in ('cause_act', 'mature_last')
        body_second = name not in ('second_object', 'second_person', 'second_anchor', 'second_branches', 'second_futures') and not both_fail
        want = [not both_fail, body_second, name == 'baseline', not both_fail]
        assert actual == want, (name, actual, want)
        rows[name] = actual
    for name in ('zitems', 'zobjects', 'zpersons', 'zanchors', 'zpreferred', 'zbranches', 'zfutures', 'zkindfirst', 'zkindsecond', 'g3', 'zstate'):
        values = source_values(doc); values[name] = unknown
        try: evaluate(doc, values, previous.PEOPLE, scenes, True)
        except ValueError as error: assert 'Unknown' in str(error)
        else: raise AssertionError(name)
    return dict(cases=rows, unknown_inputs_refused=11, classification_and_capacity_boundaries_isolated=True,
        original_conditional_profile_executed=True, each_case_identity_preserved=True,
        second_kind_failure_hidden_by_pooling=True)


@lru_cache(None)
def native_checks():
    doc = deepcopy(source_document(False)); doc['statements'] = doc['statements'][:2]
    rows = {}
    for name in ('baseline', 'mature_last', 'cause_act'):
        actual = evaluate(doc, source_values(doc, name, False), previous.PEOPLE, previous.SCENES + ('anchor2',), True)
        assert actual == [name == 'baseline'] * 2, (name, actual)
        rows[name] = actual
    refused = deepcopy(source_document(False)); refused['statements'] = refused['statements'][2:3]
    try: evaluate(refused, source_values(refused, boundary=False), previous.PEOPLE, previous.SCENES + ('anchor2',), True)
    except ValueError as error: assert 'Cannot finitely quantify' in str(error) and 'description' in str(error), str(error)
    else: raise AssertionError('Description domain replaced by finite samples')
    return dict(cases=rows, native_capacity_and_conditional_profile_executed=True, classification_domain_explicitly_refused=True)


def reading():
    unit = next(u for u in read(INVENTORY)['units'] if u['id'] == 'kant-1784:u0010')
    return dict(status='kindwise_generalization_comparison_not_adopted', document=LIBRARY,
        source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'], range=[293, 473], text=unit['text'][293:473]),
        alignment=[], definitions=list(MEANINGS), source_manuscript=SOURCE, active_registry=INDEX,
        retained_selection=selection_binding(catalog(), [10, 52, 53]),
        references=[dict(url='https://korpora.org/Kant/aa08/036.html', title='Kant AA VIII036', accessed='2026-10-20', use='二種類の名詞と同格・比喩の接続を照合。'),
            dict(url='https://tzin.bgu.ac.il/~arikc/gen.pdf', title='Cohen, Genericity (2002), section 2', accessed='2026-10-20', use='一般文を全称や現在の多数と同一視しないための比較資料。今回の合成や原文の唯一の読みを同論文の結論とはしない。')],
        interpretation_limits=LIMITS, whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
        new_covered_characters=0, new_verified_sentence_characters=0)


@lru_cache(None)
def structure_checks():
    old, new = catalog(), local_catalog()
    assert not new.document['statements']
    assert set(new.entries) - set(old.entries) == set(MEANINGS)
    inherited = set(new.entries) & set(old.entries)
    for n in inherited:
        assert new.entries[n]['declaration'] == old.entries[n]['declaration']
        assert new.entries[n]['meaning_ja'] == old.entries[n]['meaning_ja']
        assert new.entries[n].get('arguments') == old.entries[n].get('arguments')
    assert all(e['kind'] == 'definition' for n, e in new.entries.items() if n in MEANINGS)
    prior = read(previous.REPORT); validate_hashes(ROOT, prior['source_sha256'])
    assert closure(new.document, ['r2ey']) == closure(old.document, ['r2ey'])
    assert read(INDEX)['works']['kant-1784']['document'] == SOURCE
    assert len(old.document['statements']) == 54
    for path in read(INDEX)['works']['kant-1784']['reviews']:
        review = read(path); validate_hashes(ROOT, review['source_sha256'])
        assert review['selection'] == selection_binding(old, [r['index'] for r in review['selection']['statements']])
    for path, ids in ((previous.FIRST, [51]), (previous.SECOND, [11, 12])):
        r = read(path); validate_hashes(ROOT, r['source_sha256']); assert r['selection'] == selection_binding(old, ids)
    for path, body in build().items(): assert (ROOT / path).read_text(encoding='utf-8') == body
    for style in ('compact', 'full'):
        text = format_graph(new.document, style)
        assert parse(text) == parse(transcribe(text, alphabet='v2')) == new.document
    assert read(AUDIT) == reading()
    return dict(new_definitions=3, new_primitives=0, inherited_declarations_and_meanings=len(inherited),
        manuscript_statements_preserved=54, registered_reviews_preserved=12, reviewed_sentence_characters_preserved=247,
        source_profile_evidence_reused_without_claiming_rerun=True, active_registry_unchanged=True, roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    for path, body in build().items(): write_exact(ROOT / path, body)
    write_exact(ROOT / AUDIT, encoded(reading()))


def build_report():
    results = {}
    for name, fn in [('generic', generic_checks), ('binding', binding_checks), ('native', native_checks), ('structure', structure_checks)]:
        results[name] = fn(); print(name + ' checked', flush=True)
    paths = set(catalog().source_sha256) | set(read(previous.REPORT)['source_sha256']) | set(build()) | {
        REPORT.replace('reports/', 'docs/').replace('.json', '.md'), AUDIT, INDEX, INVENTORY, previous.REPORT,
        previous.FIRST, previous.SECOND, 'scripts/compose_conjoined_kinds.py', 'scripts/check_conjoined_kinds.py',
        'tests/test_conjoined_kinds.py'}
    paths.update(read(INDEX)['works']['kant-1784']['reviews'])
    return dict(status='conjoined_kind_generalizations_checked_not_source_replacement', document=LIBRARY, **results,
        alignment=[], whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
        new_covered_characters=0, new_verified_sentence_characters=0, verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})


if __name__ == '__main__':
    from scripts.audit_opening_scope import write_exact, encoded
    prepare(); write_exact(ROOT / REPORT, encoded(build_report()))
