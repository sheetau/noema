from copy import deepcopy
from fractions import Fraction

import pytest

from noema.constructed import parse
from noema.constructed_semantics import evaluate_document
from noema.existential_witnesses import instantiate_witnesses, verify_witnesses


def term(text):
    return parse('p:q[e['+text+']['+text+']].')['statements'][0]['body']['arguments'][0]


def test_finite_sequence_witnesses_have_no_search_length_cutoff():
    doc = parse('p:r zn[] b.q[g xs j[a][e[d[v xs]][k zn[]]]].')
    for size in (0,1,257):
        # A literal sequence of truth values needs no named individuals.
        trial = parse('p:r zn[] b.q[g xs j[c][e[d[v xs]][k zn[]]]].')
        # Use the parser's sequence AST schema rather than p a b Python sequence.
        witness = term('l[c]['+' '.join('e[n p a b][n p a b]' for _ in range(size))+']')
        result = verify_witnesses(trial,[witness],individuals=('p',),situations=('now',),
                                  primitives={'zn':lambda:Fraction(size)},max_steps=100000)
        assert result['status']=='valid' and not result['unrestricted_domain_enumerated']
    with pytest.raises(ValueError,match='unbounded sequence'):
        evaluate_document(doc,individuals=('p',),situations=('now',),primitives={'zn':lambda:Fraction(0)})


def test_a_failed_witness_does_not_disprove_an_existence_claim():
    doc = parse('p:q[g number b[e[v number][n p b b]]].')
    failed = verify_witnesses(doc,[term('n p a b')],individuals=('p',),situations=('now',),primitives={})
    valid = verify_witnesses(doc,[term('n p b b')],individuals=('p',),situations=('now',),primitives={})
    assert failed['status']=='uncertified' and failed['instance_value'] is False
    assert not failed['theorem_disproved'] and valid['status']=='valid'


def test_typed_closed_witnesses_and_order_are_required():
    doc = parse('p:q[g x b[g xs j[b][e[d[v xs]][v x]]]].')
    options=dict(individuals=('p',),situations=('now',),primitives={})
    assert verify_witnesses(doc,[term('n p b b'),term('l[b][n p a b]')],**options)['status']=='valid'
    for bad in ([],[term('n p b b')],[term('l[b][]'),term('n p a b')],
                [dict(kind='variable',name='x'),term('l[b][]')]):
        with pytest.raises(ValueError): instantiate_witnesses(doc,bad)


def test_named_definition_keeps_parameters_and_local_binders_separate():
    doc = parse('p:d claim[expected b] c[g actual b[e[v expected][v actual]]].q[k claim[n p b b]].')
    original=deepcopy(doc)
    options=dict(individuals=('p',),situations=('now',),primitives={})
    assert verify_witnesses(doc,[term('n p b b')],**options)['status']=='valid'
    assert verify_witnesses(doc,[term('n p a b')],**options)['status']=='uncertified'
    parameter=doc['declarations'][0]['parameters'][0]['name']
    with pytest.raises(ValueError): instantiate_witnesses(doc,[dict(kind='variable',name=parameter)])
    assert doc==original


def test_no_discharge_under_negation_or_a_conditional_or_universal():
    for body in ('u[g x b[e[v x][n p a b]]]', 'y[e[n p a b][n p a b]][g x b[e[v x][n p a b]]]',
                 'f x b[g y b[e[v x][v y]]]'):
        with pytest.raises(ValueError,match='leading existential'):
            instantiate_witnesses(parse('p:q['+body+'].'),[term('n p a b')])


def test_unknowns_and_budget_failures_are_not_boolean_answers():
    doc=parse('p:r holds[b] c.q[g x b[k holds[v x]]].')
    def unknown(*args): raise ValueError('Unknown interpretation')
    with pytest.raises(ValueError,match='Unknown'):
        verify_witnesses(doc,[term('n p a b')],individuals=('p',),situations=('now',),primitives={'holds':unknown})
    with pytest.raises(ValueError,match='budget|Budget'):
        verify_witnesses(doc,[term('n p a b')],individuals=('p',),situations=('now',),
                         primitives={'holds':lambda x:True},max_steps=1)


def test_closed_function_witness_preserves_its_inner_binding():
    doc=parse('p:q[g fn h[b] b[e[c[v fn][n p b b]][n p b b]]].')
    identity=term('i[x b][v x]')
    assert verify_witnesses(doc,[identity],individuals=('p',),situations=('now',),primitives={})['status']=='valid'


def test_positive_witness_agrees_with_exhaustive_finite_domain():
    doc=parse('p:r chosen[] a.r holds[a] c.q[g x a[k holds[v x]]].')
    witness=parse('p:r chosen[] a.q[e[k chosen[]][k chosen[]]].')['statements'][0]['body']['arguments'][0]
    for selected in ('p','q'):
        for true_at in ((),('p',),('q',),('p','q')):
            options=dict(individuals=('p','q'),situations=('now',),
                         primitives={'chosen':lambda:selected,'holds':lambda x:x in true_at})
            result=verify_witnesses(doc,[witness],**options)
            exhaustive=evaluate_document(doc,**options)[0]['value']
            assert result['instance_value']==(selected in true_at)
            assert result['status']!='valid' or exhaustive
