import pytest

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.rational_proofs import verify
from noema.render import render
from noema.script import decode, encode
from scripts.check_limits import CLAIMS, MEANINGS, claim_document, finite_refusals, proof_checks, source_alignment
from scripts.compose_limits import ROOT, composed


def test_exact_quantifiers_distinguish_limits_continuity_and_empty_domains():
    pytest.importorskip('z3')
    rows = proof_checks()
    assert len(rows) == 19
    assert sum(row['status'] == 'valid' for row in rows.values()) == 9
    assert rows['right_hand_limit_does_not_need_value_at_point']['status'] == 'valid'
    assert rows['continuity_requires_point_in_domain']['status'] == 'invalid'
    assert rows['isolated_point_is_continuous']['status'] == 'valid'
    assert rows['isolated_point_has_no_limit_under_accumulation_convention']['status'] == 'invalid'
    assert rows['empty_domain_has_no_limit']['status'] == 'invalid'
    assert rows['affine_limit_at_every_rational_point']['status'] == 'valid'
    assert rows['continuous_open_line_is_not_closed']['status'] == 'invalid'
    assert CLAIMS.read_text(encoding='utf-8') == claim_document()


def test_finite_sampling_and_nonlinear_real_for_rational_shortcuts_are_refused():
    assert finite_refusals()['finite_sampling_refused']
    pytest.importorskip('z3')
    doc = parse(composed()[0])
    text = format_graph(doc, 'compact') + '\ns[k kd[i[x b][e[v x][v x]] i[x b][k ad[v x v x]] n p a b]].'
    with pytest.raises(ValueError, match='Nonlinear rational arithmetic'):
        verify(parse(text), MEANINGS)


def test_real_cut_functions_derivatives_and_curve_types_roundtrip():
    text, basis = composed()
    doc = parse(text)
    audit = audit_basis(doc, basis)
    assert (audit['primitive_count'], audit['definition_count']) == (4, 38)
    assert not audit['semantic_equivalence_to_source_proven']
    assert (ROOT / basis['document']).read_text(encoding='utf-8') == text
    for notation in ('compact', 'full'):
        canonical = format_graph(doc, notation)
        assert parse(canonical) == parse(decode(encode(canonical, 'v2'))) == doc
    assert '<svg' in render(text, alphabet='v2')


def test_source_scope_is_geometric_and_does_not_assert_clock_curve_law():
    row = source_alignment()
    assert row['unit'] == 'einstein-1905:u0128'
    assert row['status'] == 'partial' and row['definitions'] == ['lh']
    assert 'constant physical speed' in row['uncovered']
    assert 'clock integral and acceleration law' in row['uncovered']
