import pytest

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.render import render
from noema.script import decode, encode
from scripts.check_integrals import (CLAIMS, claim_document, example_checks, partition_checks,
                                     proof_checks, refusal_checks, source_alignment)
from scripts.compose_integrals import ROOT, composed


def test_partition_geometry_tags_and_representative_dependence():
    rows = partition_checks()
    assert len(rows) == 94
    assert rows['connected_partition']['actual']
    assert not rows['gap']['actual'] and not rows['overlap']['actual']
    assert not rows['duplicate_interval']['actual']
    assert not rows['empty_is_not_positive_partition']['actual']
    assert not rows['mesh_equal_bound_is_not_strictly_below']['actual']
    assert not rows['outside_left']['actual']
    assert rows['12_left_affine']['actual'] and rows['12_right_affine']['actual']
    assert rows['clock_rate_sum']['actual']
    assert example_checks() == 5


def test_scalar_error_bounds_and_noema_record_construction():
    pytest.importorskip('z3')
    rows = proof_checks()
    assert len(rows) == 11
    assert all(row['status'] == 'valid' for row in rows.values())
    assert rows['identity_cell_error_bounded_by_mesh']['status'] == 'valid'
    assert rows['record_constructor_tag_field']['status'] == 'valid'
    assert CLAIMS.read_text(encoding='utf-8') == claim_document()


def test_integral_quantification_is_not_replaced_with_finite_partitions():
    rows = refusal_checks()
    assert 'unbounded sequence domain' in rows['all_partitions']
    assert 'rational number domain' in rows['integral_is_not_a_finite_sum']


def test_real_integral_curve_model_preserves_types_basis_and_source_limits():
    text, basis = composed()
    doc = parse(text)
    audit = audit_basis(doc, basis)
    assert (audit['primitive_count'], audit['definition_count']) == (4, 54)
    assert not audit['semantic_equivalence_to_source_proven']
    assert (ROOT / basis['document']).read_text(encoding='utf-8') == text
    for notation in ('compact', 'full'):
        canonical = format_graph(doc, notation)
        assert parse(canonical) == parse(decode(encode(canonical, 'v2'))) == doc
    assert '<svg' in render(text, alphabet='v2')
    alignment = source_alignment()
    assert alignment['unit'] == 'einstein-1905:u0128' and alignment['status'] == 'partial'
    assert 'physical acceleration law' in alignment['uncovered']
