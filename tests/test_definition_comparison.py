from copy import deepcopy
import pytest
from noema.constructed import parse
from noema.constructed_semantics import evaluate_document
from noema.definition_comparison import DefinitionComparator, ExpansionLimitError


PREFIX = '''p:
r atom[a a d] c.r other[a a d] c.r one[] a.r two[] a.
d relation[left a right a ctx d] c[k atom[v left v right v ctx]].
d named[] f[j s[b ctx[k relation[k one[] k two[] v ctx]]]].
d preserve[person a] e[b ctx[f person a[k atom[k one[] v person v ctx]]]].
d capture[person a] e[b ctx[f someone a[k atom[v person v someone v ctx]]]].
d higher[fun h[a a d] c left a right a ctx d] c[c[v fun][v left v right v ctx]].
'''
DIRECT = 'j s[b at[k atom[k one[] k two[] v at]]]'


def pair(left, right, prefix=PREFIX):
    document = parse(prefix + 'q[e[r[' + left + ']][r[' + right + ']]].')
    return document, document['statements'][0]['body']['arguments']


def compare(left, right, prefix=PREFIX, **options):
    document, quotes = pair(left, right, prefix)
    return DefinitionComparator(document, **options).compare(*quotes)


@pytest.mark.parametrize('left,right', [
    ('k named[]', DIRECT),
    ('j s[b at[k relation[k one[] k two[] v at]]]', DIRECT),
    ('j s[b renamed[k atom[k one[] k two[] v renamed]]]', DIRECT),
    ('j s[b at[k higher[p relation k one[] k two[] v at]]]', DIRECT),
    ('j s[b at[c[i[x a][k relation[v x k two[] v at]]][k one[]]]]', DIRECT),
    ('j s[k capture[k two[]]]', 'j s[b at[f x a[k atom[k two[] v x v at]]]]'),
    ('j s[k preserve[k two[]]]', 'j s[b at[f x a[k atom[k one[] v x v at]]]]'),
    ('j s[b at[f x a[t[k capture[v x]][v at]]]]',
     'j s[b at[f x a[t[b inside[f y a[k atom[v x v y v inside]]]][v at]]]]'),
])
def test_aliases_higher_order_calls_and_capture_avoidance(left, right):
    result = compare(left, right)
    assert result['status'] == 'same_definition_expansion'
    assert not result['contents_evaluated']


@pytest.mark.parametrize('other', [
    'j s[b at[u[k atom[k one[] k two[] v at]]]]',
    DIRECT.replace('j s[', 'j q['), DIRECT.replace('j s[', 'j m['),
    DIRECT.replace('k one[] k two[]', 'k two[] k one[]'),
    DIRECT.replace('k atom', 'k other'),
])
def test_force_polarity_roles_and_predicates_remain_distinct(other):
    result = compare('k named[]', other)
    assert result['status'] == 'not_established'
    assert not result['universal_semantic_equivalence_decided']


@pytest.mark.parametrize('left,right', [
    ('j s[b at[f x a[k atom[v x k one[] v at]]]]', 'j s[b at[g x a[k atom[v x k one[] v at]]]]'),
    ('j s[b at[u[f x a[k atom[v x k one[] v at]]]]]', 'j s[b at[f x a[u[k atom[v x k one[] v at]]]]]'),
    ('j s[b at[y[k atom[k one[] k two[] v at]][k other[k one[] k two[] v at]]]]',
     'j s[b at[y[k other[k one[] k two[] v at]][k atom[k one[] k two[] v at]]]]'),
    ('r[k named[]]', 'r[' + DIRECT + ']'),
])
def test_quantification_scope_direction_and_nested_spelling_are_not_erased(left, right):
    assert compare(left, right)['status'] == 'not_established'


def test_nested_literal_equality_is_not_changed_by_expansion():
    left = 'e[r[k named[]]][r[' + DIRECT + ']]'
    right = 'e[r[' + DIRECT + ']][r[' + DIRECT + ']]'
    assert compare(left, right)['status'] == 'not_established'


def test_same_sampled_truth_is_not_same_thought():
    other = DIRECT.replace('k atom', 'k other')
    doc = parse(PREFIX + 'q[e[' + DIRECT + '][' + other + ']].')
    values = dict(atom=lambda *a: True, other=lambda *a: True, one=lambda: 'one', two=lambda: 'two')
    assert evaluate_document(doc, individuals=('one', 'two'), situations=('now',), primitives=values)[0]['value']
    assert compare(DIRECT, other)['status'] == 'not_established'


def test_bound_namespace_and_inputs_are_immutable():
    doc, quotes = pair('k named[]', DIRECT)
    before = deepcopy(doc)
    comparator = DefinitionComparator(doc)
    result = comparator.compare(*quotes)
    assert doc == before
    result['left']['body'] = None
    assert comparator.compare(*quotes)['status'] == 'same_definition_expansion'
    revised = PREFIX.replace('k atom[v left v right v ctx]', 'k other[v left v right v ctx]')
    assert compare('k named[]', DIRECT, revised)['status'] == 'not_established'


def test_ill_typed_free_foreign_recursive_and_ranked_inputs_are_rejected():
    doc, quotes = pair('k named[]', DIRECT)
    comparator = DefinitionComparator(doc)
    bad = [dict(kind='quote', body=dict(kind='variable', name='free')),
           dict(kind='quote', body=dict(kind='call', symbol='absent', arguments=[])),
           dict(kind='quote', body=dict(kind='call', symbol='one', arguments=[])),
           dict(quotes[0], rank=1)]
    for node in bad:
        with pytest.raises(ValueError):
            comparator.compare(node, quotes[1])
    with pytest.raises(ValueError):
        parse('p:d loop[] c[k loop[]].')


def test_growth_limits_fail_instead_of_returning_a_semantic_judgment():
    with pytest.raises(ExpansionLimitError):
        compare('k named[]', DIRECT, max_nodes=10)
    doc, quotes = pair('k named[]', DIRECT)
    with pytest.raises(ExpansionLimitError):
        DefinitionComparator(doc, max_document_nodes=5)
    prefix = 'p:r atom[] c.d da[] c[w[k atom[]][k atom[]]].'
    prior = 'da'
    for name in ('db', 'dc', 'dd', 'de', 'df', 'dg', 'dh', 'di', 'dj'):
        prefix += 'd ' + name + '[] c[w[k ' + prior + '[]][k ' + prior + '[]]].'
        prior = name
    with pytest.raises(ExpansionLimitError):
        compare('k dj[]', 'k dj[]', prefix, max_nodes=500)


def test_no_runtime_optimization_claim_for_unused_partial_arguments():
    prefix = PREFIX + 'd ignore[value c] c[e[k one[]][k one[]]].'
    result = compare(
        'j s[b at[k ignore[k atom[k one[] k two[] v at]]]]', 'j s[b at[e[k one[]][k one[]]]]', prefix)
    assert result['status'] == 'same_definition_expansion'
    assert not result['operational_rewrite_authorized']
    def unknown(*args):
        raise ValueError('Unknown atom')
    values = dict(atom=unknown, other=unknown, one=lambda: 'one', two=lambda: 'two', now=lambda: 'now')
    doc = parse(prefix + 'r now[] d.q[k ignore[k atom[k one[] k two[] k now[]]]].')
    with pytest.raises(ValueError, match='Unknown atom'):
        evaluate_document(doc, individuals=('one', 'two'), situations=('now',), primitives=values)
    doc = parse(prefix + 'r now[] d.q[e[k one[]][k one[]]].')
    assert evaluate_document(doc, individuals=('one', 'two'), situations=('now',), primitives=values)[0]['value']


def test_typed_questions_and_sequence_definitions_also_preserve_structure():
    prefix = PREFIX + 'd query[] g[a][j v[i[item a][e[v item][k one[]]]]].d items[] j[a][l[a][k one[] k two[]]].'
    assert compare('k query[]', 'j v[i[x a][e[v x][k one[]]]]', prefix)['status'] == 'same_definition_expansion'
    assert compare('k items[]', 'l[a][k one[] k two[]]', prefix)['status'] == 'same_definition_expansion'
    assert compare('k items[]', 'l[a][k two[] k one[]]', prefix)['status'] == 'not_established'
