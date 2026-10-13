import pytest
from noema.grammar import parse
from noema.first_order_proofs import verify


def test_domain_is_not_a_single_finite_example():
    result=verify(parse('n:s[f x a[f y a[e[v x][v y]]]].'))[0]
    assert result['status']=='invalid' and result['countermodel'] is not None


def test_nonempty_domain_has_a_reflexive_witness():
    assert verify(parse('n:s[g x a[e[v x][v x]]].'))[0]['status']=='valid'


def test_definitions_expand_with_lexically_captured_parameters():
    text='n:r a[a] a.d b[x a] h[a] c[i[y a][e[v x][k a[v y]]]].s[f x a[c[k b[k a[v x]]][v x]]].'
    assert verify(parse(text))[0]['status']=='valid'


def test_boolean_quantification_keeps_both_truth_values():
    result=verify(parse('n:s[g x c[v x]].s[f x c[v x]].'))
    assert [r['status'] for r in result]==['valid','invalid']


def test_individual_predicates_are_uninterpreted_not_assumed_true():
    result=verify(parse('n:r a[a] c.s[f x a[k a[v x]]].'))[0]
    assert result['status']=='invalid'


def test_situations_have_an_independent_nonempty_unbounded_sort():
    result=verify(parse('n:s[g x d[e[v x][v x]]].s[f x d[f y d[e[v x][v y]]]].'))
    assert [row['status'] for row in result]==['valid','invalid']
    assert 'NoemaSituation' in result[0]['formula']
    assert 'NoemaIndividual' not in result[0]['formula']
    assert result[1]['countermodel'] is not None


def test_contextual_predicates_and_situation_valued_functions_keep_types():
    doc=parse('n:r a[a] d.r b[a d] c.s[f person a[y[k b[v person k a[v person]]][g context d[k b[v person v context]]]]].')
    row=verify(doc)[0]
    assert row['status']=='valid'
    assert 'NoemaIndividual' in row['formula'] and 'NoemaSituation' in row['formula']
    # A contextual predicate need not have the same value in every situation.
    row=verify(parse('n:r a[a d] c.s[f person a[f x d[f y d[z[k a[v person v x]][k a[v person v y]]]]]].'))[0]
    assert row['status']=='invalid'


@pytest.mark.parametrize('text',[
    'n:s[f x b[e[v x][v x]]].',
    'n:r a[] b.s[e[k a[]][k a[]]].',
    'n:s[f x h[a] a[e[v x][v x]]].',
    'n:s[e[i[x a][v x]][i[y a][v y]]].',
    'n:r a[] e.s[e[k a[]][k a[]]].',
    'n:r a[] a.q[e[k a[]][k a[]]].',
])
def test_unsupported_domains_and_speech_acts_are_rejected(text):
    with pytest.raises(ValueError):verify(parse(text))


def test_limits_are_explicit_and_the_formula_is_reproducible():
    doc=parse('n:s[f x a[e[v x][v x]]].')
    assert verify(doc)==verify(doc)
    for kwargs in ({'timeout_ms':0},{'max_expansion':0},{'timeout_ms':True},{'max_expansion':1}):
        with pytest.raises(ValueError):verify(doc,**kwargs)


def test_solver_unknown_is_never_reported_as_valid_or_invalid(monkeypatch):
    import z3
    class Inconclusive:
        def set(self,**kwargs):pass
        def add(self,*args):pass
        def check(self):return z3.unknown
        def reason_unknown(self):return 'test resource limit'
        def model(self):raise AssertionError('An inconclusive solver has no certified countermodel')
    monkeypatch.setattr(z3,'Solver',Inconclusive)
    result=verify(parse('n:s[f x a[e[v x][v x]]].'))[0]
    assert result['status']=='unknown' and result['countermodel'] is None
    assert result['reason']=='test resource limit'
