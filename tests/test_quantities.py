import pytest

from noema.finite_semantics import evaluate_document
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.render import render
from noema.script import encode, decode
from scripts.compose_quantities import composed
from scripts.check_quantities import finite_checks, proof_checks, ARITHMETIC, DOMAIN, dimension


def test_kind_dimension_scale_and_value_countermodels():
    cases = finite_checks()
    assert len(cases) == 22
    assert cases['beta_mixed_velocity_scales']['actual']
    assert not cases['same_dimension_different_kind_rejected']['actual']
    assert not cases['beta_bad_base_vector_rejected']['actual']
    assert not cases['zero_duration_is_not_a_quotient']['actual']


def test_dimension_cancellation_and_fractional_exponents():
    text, _ = composed()
    text += '''
r za[] h[a] b.r zb[] h[a] b.
s[k dg[k dd[k za[] k za[]]]].
s[k df[k db[k dd[k za[] k zb[]] k zb[]] k za[]]].
s[k df[k de[k db[k za[] k za[]] n p b c] k za[]]].
s[u[k df[k dd[k za[] k zb[]] k za[]]]].
'''
    result = evaluate_document(parse(text), individuals=DOMAIN, situations=('now',), primitives={
        **ARITHMETIC, 'za': lambda: dimension(length=1), 'zb': lambda: dimension(time=1)})
    assert [r['value'] for r in result] == [True] * 4


def test_scale_invariance_is_universal_not_only_checked_on_sample_values():
    pytest.importorskip('z3')
    results = proof_checks()
    assert [r['status'] for r in results.values()].count('valid') == 4
    assert results['adding_common_offset_is_unit_conversion']['status'] == 'invalid'


def test_no_new_primitive_units_or_dimensions_are_hardcoded():
    text, basis = composed()
    doc = parse(text)
    audit = audit_basis(doc, basis)
    assert audit['primitive_count'] == 4
    assert audit['definition_count'] == 42
    assert set(audit['definition_dependencies']['primitive_symbols']) == {'aa', 'ab', 'ac', 'ad'}
    for notation in ('compact', 'full'):
        canonical = format_graph(doc, notation)
        assert parse(canonical) == parse(decode(encode(canonical, 'v2'))) == doc
    assert '<svg' in render(text, alphabet='v2')
