import pytest
from noema.grammar import parse
from noema.rational_witnesses import verify_witnesses
from noema.semantics import SemanticError


def inverse_doc(premise='u[e[v input][n p a b]]', matrix='e[k ad[v input v output]][n p b b]'):
    return parse('n:r ad[b b] b.s[f input b[y['+premise+'][g output b['+matrix+']]]].')


def names(doc):
    root = doc['statements'][0]['body']
    return root['variable'], root['body']['arguments'][1]['variable']


def inverse(doc):
    x, y = names(doc)
    return {y: ['divide', ['number', 1, 1], ['variable', x]]}


def test_nonzero_rational_input_has_a_constructed_rational_inverse():
    doc = inverse_doc(); result = verify_witnesses(doc, {'ad': 'multiply'}, inverse(doc))
    assert result['status'] == 'valid' and result['rational_closure_checked']
    assert result['denominator_obligations'] == 1


def test_unconditional_inverse_is_not_certified_at_zero():
    doc = inverse_doc('e[n p a b][n p a b]')
    result = verify_witnesses(doc, {'ad': 'multiply'}, inverse(doc))
    assert result['status'] == 'uncertified' and not result['theorem_disproved']


def test_totalized_smt_division_cannot_hide_an_undefined_witness():
    doc = inverse_doc('e[n p a b][n p a b]', 'e[v output][v output]')
    _, y = names(doc)
    result = verify_witnesses(doc, {'ad': 'multiply'}, {y: ['divide', ['number', 1, 1], ['number', 0, 1]]})
    assert result['status'] == 'uncertified'


def test_real_square_root_existence_is_not_imported_into_rationals():
    doc = inverse_doc('e[n p a b][n p a b]', 'e[k ad[v output v output]][n p c b]')
    _, y = names(doc)
    result = verify_witnesses(doc, {'ad': 'multiply'}, {y: ['number', 141421, 100000]})
    assert result['status'] == 'uncertified' and not result['theorem_disproved']
    with pytest.raises(SemanticError, match='Unsupported rational witness operation'):
        verify_witnesses(doc, {'ad': 'multiply'}, {y: ['sqrt', ['number', 2, 1]]})


def test_failed_guess_does_not_disprove_an_existing_solution():
    doc = inverse_doc(); _, y = names(doc)
    result = verify_witnesses(doc, {'ad': 'multiply'}, {y: ['number', 0, 1]})
    assert result['status'] == 'uncertified' and not result['theorem_disproved']


def test_conditional_certificate_does_not_claim_nonempty_premises():
    doc = inverse_doc('u[e[n p a b][n p a b]]'); _, y = names(doc)
    result = verify_witnesses(doc, {'ad': 'multiply'}, {y: ['number', 0, 1]})
    assert result['status'] == 'valid' and not result['premise_satisfiability_proved']


@pytest.mark.parametrize('term', [
    ['number', 1.0, 1], ['number', True, 1], ['number', 1, 0],
    ['variable', 'missing'], ['variable', 'vb'], ['divide', ['number', 1, 1]],
])
def test_inexact_unbound_circular_or_malformed_terms_are_refused(term):
    doc = inverse_doc(); _, y = names(doc)
    with pytest.raises(SemanticError): verify_witnesses(doc, {'ad': 'multiply'}, {y: term})


def test_missing_witness_meaning_and_signature_mismatch_are_refused():
    doc = inverse_doc()
    with pytest.raises(SemanticError): verify_witnesses(doc, {'ad': 'multiply'}, {})
    with pytest.raises(SemanticError): verify_witnesses(doc, {}, inverse(doc))
    with pytest.raises(SemanticError): verify_witnesses(doc, {'ad': 'less'}, inverse(doc))


def test_nested_quantifiers_are_not_silently_relaxed_to_reals():
    doc = inverse_doc(matrix='f nested b[e[v nested][v output]]')
    with pytest.raises(SemanticError, match='quantifier-free'):
        verify_witnesses(doc, {'ad': 'multiply'}, inverse(doc))


def test_all_nested_denominators_and_expansion_budget_are_checked():
    doc = inverse_doc(matrix='e[v output][v input]'); x, y = names(doc)
    terms = {y: ['divide', ['number', 1, 1], ['divide', ['number', 1, 1], ['variable', x]]]}
    result = verify_witnesses(doc, {'ad': 'multiply'}, terms)
    assert result['status'] == 'valid' and result['denominator_obligations'] == 2
    with pytest.raises(SemanticError, match='budget'):
        verify_witnesses(doc, {'ad': 'multiply'}, terms, max_expansion=1)


def test_solver_unknown_is_not_reported_as_a_proof(monkeypatch):
    import z3
    class UnfinishedSolver:
        def set(self, **kwargs): pass
        def add(self, *args): pass
        def check(self): return z3.unknown
        def reason_unknown(self): return 'simulated timeout'
    monkeypatch.setattr(z3, 'SolverFor', lambda logic: UnfinishedSolver())
    doc = inverse_doc(); result = verify_witnesses(doc, {'ad': 'multiply'}, inverse(doc))
    assert result['status'] == 'unknown' and result['reason'] == 'simulated timeout'
    assert not result['theorem_disproved']
