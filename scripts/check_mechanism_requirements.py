"""Check practical requirements, task-scoped passivity and partial attribution."""
from copy import deepcopy
from functools import lru_cache
from itertools import permutations, product
import json
from noema.constructed import parse, format_graph
from noema.constructed_semantics import FunctionValue
from noema.meaning_catalog import load_catalog
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_mechanism_requirements import (
    ROOT, FULL, CORE, BASIS, ANNOTATIONS, MEANINGS, LIMITS, parent, library, build, closure)
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol

INDEX = 'data/semantic-review-index-v162.json'
REPORT = 'reports/mechanism-requirements-v1.json'
AUDIT = 'data/mechanism-requirements-reading-v1.json'
DOC = 'docs/mechanism-requirements-v1.md'
INVENTORY = 'artifacts/written-units-v1/kant-1784.json'
PRIOR = ('reports/use-definitions-v1.json', 'reports/institutional-coordination-v1.json')
DOMAIN = ('one', 'two', 'roleone', 'roletwo', 'work', 'otherwork', 'community',
          'mechanism', 'source', 'other')
SCENES = ('reference', 'future', 'other')


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog():
    return load_catalog(ROOT, BASIS)


@lru_cache(None)
def fixture(kind, sequence=('one', 'roleone', 'work')):
    doc = deepcopy(catalog().document)
    roots = {'passive': ['r2zu'], 'adapter': ['r2zv'], 'requirements': ['r2zx', 'r2zy'],
             'attribution': ['r2zz']}[kind]
    doc.update(declarations=closure(doc, roots), statements=[])
    extra = ''
    if kind in ('passive', 'adapter'):
        extra = 'r zone[] a.r zroleone[] a.r zwork[] a.r zother[] a.r zpoint[] d.'
        if kind == 'passive':
            query = 'q[t[k r2zu[k zone[] k zroleone[] k zwork[]]][k zpoint[]]].'
        else:
            items = ' '.join('k z' + x + '[]' for x in sequence)
            query = 'q[t[k r2zv[l[a][' + items + ']]][k zpoint[]]].'
    elif kind == 'requirements':
        text = format_graph(doc, 'compact')
        start = text.index('r h232f[')
        end = text.index('.', start) + 1
        text = text[:start] + text[end:]
        adapter = '''
r zrequiredcode[a d i b[h[a d] e] i b[h[a d] e]] i b[h[a d] e].
d h232f[mechanism a reference d] i b[h[a d] e][
 k zrequiredcode[v mechanism v reference r b[p r2zw] r b[p r2zt]]
].
'''
        # Insert after the quoted families and before their consuming definition.
        start = text.index('d r2zx[')
        doc = parse(text[:start] + adapter + text[start:])
        extra = 'r zwork[] a.r zreference[] d.'
        query = 'q[k r2zx[k zwork[] k zreference[]]].q[t[k r2zy[]][k zreference[]]].'
    else:
        query = 'q[k r2zz[]].'
    return parse(format_graph(doc, 'compact') + extra + query)


def passive_model(doc, executing=True, independent=False):
    v = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
    v.update(zone=lambda: 'one', zroleone=lambda: 'roleone', zwork=lambda: 'work',
             zother=lambda: 'other', zpoint=lambda: 'future',
             h237a=lambda p, r, w, s: executing and (p, r, w, s) == (
                 'one', 'roleone', 'work', 'future'),
             h237b=lambda p, r, w, s: independent and (p, r, w, s) == (
                 'one', 'roleone', 'work', 'future'))
    return v


@lru_cache(None)
def passive_checks():
    doc = fixture('passive')
    rows = []
    for executing, independent in product((False, True), repeat=2):
        value = evaluate(doc, passive_model(doc, executing, independent), DOMAIN, SCENES, True)
        assert value == [executing and not independent]
        rows.append(dict(executing=executing, independently_sets_policy=independent, value=value[0]))
    adapter = {}
    for sequence in [(), ('one',), ('one', 'roleone'),
                     *permutations(('one', 'roleone', 'work')),
                     ('one', 'roleone', 'work', 'other')]:
        doc = fixture('adapter', sequence)
        actual = evaluate(doc, passive_model(doc), DOMAIN[:6] + ('other',), SCENES, True)
        assert actual == [sequence == ('one', 'roleone', 'work')], (sequence, actual)
        adapter[','.join(sequence)] = actual[0]
    # Independent policy-making in another role/work or by another person is not excluded.
    doc = fixture('passive')
    for other in [('one', 'other', 'work'), ('one', 'roleone', 'otherwork'), ('two', 'roleone', 'work')]:
        values = passive_model(doc)
        values['h237b'] = lambda p, r, w, s: (p, r, w) == other and s == 'future'
        assert evaluate(doc, values, DOMAIN, SCENES, True) == [True]
    for name in ('h237a', 'h237b'):
        values = passive_model(doc); values[name] = unknown
        try:
            evaluate(doc, values, DOMAIN, SCENES, True)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(name)
    return dict(conditions=rows, adapters=adapter, other_roles_works_people_not_excluded=True,
                unknown_inputs_refused=2, full_obedience_definition_not_replaced=True)


def requirements_model(variant='baseline'):
    doc = fixture('requirements')
    values = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
    people = ('one', 'two') if variant != 'empty_members' else ()
    roles = {'one': 'roleone', 'two': 'roletwo'}
    validworks = {'work', 'otherwork'} if variant == 'multiple_works' else {'work'}
    if variant == 'only_other_work':
        validworks = {'otherwork'}
    if variant == 'no_qualifying_work':
        validworks = set()

    def publicwork(work, community, reference):
        return work in validworks and (community, reference) == ('community', 'reference')

    def required(mechanism, code, work, reference):
        return variant != 'no_necessity' and (mechanism, symbol(code), code.rank, work, reference) == (
            'other' if variant == 'other_required_mechanism' else 'mechanism',
            'r2zw' if variant == 'necessity_for_wrong_goal' else 'r2zt', 1,
            'other' if variant == 'necessity_for_other_work' else work, 'reference')

    def norm(source, person, role, code, bindings, polarity, reference):
        return variant != 'no_role_requirement' and person in roles and bindings.items[2] in validworks and (
            source, role, symbol(code), code.rank, tuple(bindings.items), polarity, reference) == (
            'mechanism' if variant == 'norm_source_conflated' else (
                'source' if bindings.items[2] == 'work' else 'other'),
            roles[person], 'r2zt' if variant == 'wrong_role_target' else 'r2zv', 0,
            (person, roles[person], 'other') if variant == 'norm_for_other_work' else (
                person, roles[person], bindings.items[2]),
            False if variant == 'negative_role_requirement' else True,
            'future' if variant == 'norm_at_wrong_reference' else 'reference')

    values.update(zwork=lambda: 'work', zreference=lambda: 'reference', h232v=lambda: 'reference',
        aa=lambda p: p in roles and not (variant == 'nonhuman_member' and p == 'two'),
        h236w=publicwork,
        h236y=lambda m, c, w, r: variant != 'no_organized_configuration' and (m, c, r) == (
            'mechanism', 'other' if variant == 'configuration_other_community' else 'community', 'reference')
            and (variant != 'configuration_other_work' or w == 'otherwork'),
        h237c=lambda p, c, r: p in roles and (c, r) == ('community', 'reference')
            and not (variant == 'one_nonmember' and p == 'two'),
        h237d=lambda m, w, r: FunctionValue(('individual',), 'truth',
            lambda p: p in people and m == 'mechanism' and r == 'reference'),
        h237e=lambda p, m, w, r: roles.get(p, 'other'),
        h237f=lambda p, role, m, w, r: p in roles and (role, m, r) == (
            'other' if variant == 'assignment_other_role' else roles.get(p),
            'other' if variant == 'assignment_other_mechanism' else 'mechanism', 'reference')
            and (variant != 'assignment_other_work' or w == 'otherwork'),
        h237g=lambda m, w, r: 'source' if w == 'work' else 'other',
        h237h=lambda w, r: 'mechanism', h237i=lambda w, r: 'community',
        h232e=required,
        zrequiredcode=lambda m, r, right, wrong: wrong if variant == 'wrong_requirement_state' else right,
        h7k=norm)
    return values


@lru_cache(None)
def requirements_checks():
    doc, rows = fixture('requirements'), {}
    false_cases = ('no_necessity', 'other_required_mechanism', 'necessity_for_wrong_goal',
                   'necessity_for_other_work', 'wrong_requirement_state', 'empty_members',
                   'no_role_requirement', 'norm_source_conflated', 'wrong_role_target',
                   'norm_for_other_work', 'negative_role_requirement', 'norm_at_wrong_reference',
                   'nonhuman_member', 'no_organized_configuration', 'configuration_other_community',
                   'one_nonmember', 'assignment_other_role', 'assignment_other_mechanism',
                   'no_qualifying_work')
    for variant in ('baseline', 'multiple_works', 'only_other_work', *false_cases,
                    'configuration_other_work', 'assignment_other_work'):
        actual = evaluate(doc, requirements_model(variant), DOMAIN, SCENES, True)
        expected = [True, True] if variant in ('baseline', 'multiple_works') else (
            [False, True] if variant == 'only_other_work' else [False, False])
        assert actual == expected, (variant, actual)
        rows[variant] = actual
    # An invalid second business does not turn the existential into a universal.
    assert rows['baseline'] == [True, True]
    values = requirements_model()
    values['zreference'] = lambda: 'future'
    assert evaluate(doc, values, DOMAIN, SCENES, True) == [False, True]
    values = requirements_model()
    values['h232v'] = lambda: 'future'
    assert evaluate(doc, values, DOMAIN, SCENES, True) == [True, False]
    for name in ('h232e', 'zrequiredcode', 'h237d', 'h237f', 'h7k'):
        values = requirements_model(); values[name] = unknown
        try:
            evaluate(doc, values, DOMAIN, SCENES, True)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(name)
    assert all(requirements_model()[n] is unknown for n in ('h236x', 'h236z', 'h237a', 'h237b'))
    return dict(contrasts=rows, unknown_inputs_refused=5,
                work_performance_means_supply_and_passive_fulfilment_not_executed=True,
                native_target_codes_and_same_requirement_state=True,
                existential_not_all_businesses=True, distinct_work_norm_sources_preserved=True,
                source_reference_fixed_independently_of_evaluation=True,
                semantic_boundaries=[
                    'h232f is a model-supplied native description selected by a fixture adapter.',
                    'Membership, assignment, institutional configuration and requirement relations remain primitive inputs.',
                    'Finite cases do not prove source equivalence or full-obedience conditions.'])


@lru_cache(None)
def attribution_checks():
    doc, rows = fixture('attribution'), {}
    for variant in ('baseline', 'wrong_author', 'wrong_content', 'wrong_context', 'wrong_order'):
        v = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
        v.update(h237j=lambda: 'clause', wa=lambda: 'author', h232o=lambda: 'presentation',
                 h236s=lambda: 'definition',
                 h236i=lambda n, a, code, ctx: (n, a, symbol(code), code.rank, ctx) == (
                     'clause', 'other' if variant == 'wrong_author' else 'author',
                     'r2zw' if variant == 'wrong_content' else 'r2zy', 3,
                     'reference' if variant == 'wrong_context' else 'presentation'),
                 ue=lambda first, last, ctx: (first, last, ctx) == (
                     'clause' if variant == 'wrong_order' else 'definition', 'clause', 'presentation'))
        actual = evaluate(doc, v, DOMAIN + ('clause', 'author', 'definition'),
                          SCENES + ('presentation',), True)
        assert actual == [variant == 'baseline'], (variant, actual)
        rows[variant] = actual[0]
    return dict(contrasts=rows, rank_three_quote_preserved=True,
                attributed_content_inputs_not_executed=True)


def reading():
    unit = next(u for u in read(INVENTORY)['units'] if u['id'] == 'kant-1784:u0012')
    text = unit['text'][1298:1496]
    assert text.startswith('ist zu manchen Geschäften,') and text.endswith('passiv verhalten müssen')
    return dict(status='required_institutional_means_partial_sentence',
                document=FULL, meaning_basis=BASIS,
                source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'],
                            range=[1298, 1496], text=text),
                selection=selection_binding(catalog(), [78]),
                interpretation=LIMITS, whole_sentence_semantically_verified=False,
                whole_unit_semantically_verified=False, newly_reviewed_sentence_characters=0,
                preserved_reviewed_sentence_characters=1106,
                unresolved=['公共目的の具体的内容と目的としての引用',
                            '人為的協調による政府の方向付け、または目的破壊の抑止',
                            'wenigstensの最低限の提示', 'Nunの論述接続',
                            'manchenの量化を含む文全体の原刊照合・通読'],
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in (
                    FULL, BASIS, ANNOTATIONS, DOC, INVENTORY, *PRIOR)})


@lru_cache(None)
def structure_checks():
    old, new = parent(), catalog()
    assert new.document['statements'][:78] == old.document['statements']
    assert len(new.document['statements']) == 79
    assert all(new.entries[n] == entry for n, entry in old.entries.items())
    for n in ('r2zn', 'r2zs'):
        assert new.entries[n]['declaration'] == library().entries[n]['declaration']
        assert new.entries[n]['meaning_ja'] == library().entries[n]['meaning_ja']
    reviews = load_reviews(ROOT, INDEX)['works']['kant-1784']
    for row in reviews:
        assert row['selection'] == selection_binding(new, [s['index'] for s in row['selection']['statements']])
    for path in PRIOR:
        validate_hashes(ROOT, read(path)['source_sha256'])
    prior = read('data/use-definitions-reading-v1.json')
    assert prior['selection'] == selection_binding(new, [76, 77])
    validate_hashes(ROOT, prior['source_sha256'])
    assert read(AUDIT) == reading()
    for path, body in build().items():
        assert (ROOT / path).read_text(encoding='utf-8') == body
    for path in (FULL, CORE):
        doc = parse((ROOT / path).read_text(encoding='utf-8'))
        for notation in ('compact', 'full'):
            text = format_graph(doc, notation)
            assert parse(text) == parse(transcribe(text, alphabet='v2')) == doc
    return dict(preserved_statements=78, added_statements=1,
                preserved_whole_unit_reviews=len(reviews),
                new_reviewed_sentence_characters=0, preserved_reviewed_sentence_characters=1106,
                old_meanings_unchanged=True, roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    for path, body in build().items():
        write_exact(ROOT / path, body)
    write_exact(ROOT / AUDIT, encoded(reading()))


def build_report():
    results = {}
    for name, fn in [('passive', passive_checks), ('requirements', requirements_checks),
                     ('attribution', attribution_checks), ('structure', structure_checks)]:
        results[name] = fn()
        print(name + ' checked', flush=True)
    paths = set(build()) | set(catalog().source_sha256) | {
        INDEX, AUDIT, DOC, INVENTORY, *PRIOR, 'data/use-definitions-reading-v1.json',
        'scripts/compose_mechanism_requirements.py', 'scripts/check_mechanism_requirements.py',
        'tests/test_mechanism_requirements.py', 'scripts/compose_institutional_coordination.py',
        'scripts/compose_grounded_step.py', 'scripts/compose_qualitative_influence.py',
        'scripts/check_pastoral_roles.py', 'scripts/check_motive_causes.py'}
    return dict(status='required_institutional_means_and_passive_roles_partial_sentence',
                document=FULL, **results,
                alignment=dict(**read(AUDIT)['source'], statements=[78], definitions=list(MEANINGS),
                               status='partial_required_mechanism_and_passive_roles'),
                whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
                verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})
