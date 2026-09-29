from pathlib import Path

import pytest

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.render import render
from noema.script import encode, decode
from scripts.compose_phi_normalization import composed
from scripts.check_phi_normalization import numerical_checks, proof_checks, source_alignment


def test_each_missing_premise_has_a_concrete_countermodel():
    cases = numerical_checks()
    assert len(cases) == 16
    assert cases['reciprocal_but_unequal']['actual']
    assert cases['negative_reciprocal']['actual'] and cases['negative_even']['actual']
    assert not cases['negative_branch_rejected']['actual']
    assert cases['positive_rod_complete_conditions']['actual']
    assert not cases['zero_length_cannot_fix_phi']['actual']
    assert not cases['absolute_length_alone_does_not_satisfy_signed_equations']['actual']
    assert 'refused' in cases['all_admissible_velocities_not_replaced_by_samples']


def test_composition_and_rod_derivation_are_universal_polynomial_checks():
    pytest.importorskip('z3')
    results = proof_checks()
    assert len(results) == 14
    assert sum(r['status'] == 'valid' for r in results.values()) == 10
    assert sum(r['status'] == 'invalid' for r in results.values()) == 4
    assert results['opposite_transform_composition_is_common_scaling']['status'] == 'valid'
    assert results['transverse_endpoint_coordinates_follow_from_transform']['status'] == 'valid'
    for row in results.values():
        if row['status'] == 'invalid':
            assert row['counterexample'] is not None


def test_original_equations_remain_distinct_from_physical_premises():
    if not Path('artifacts/written-units-v1/einstein-1905.json').exists():
        pytest.skip('Source artifact is prepared separately')
    alignment = source_alignment()
    assert len(alignment['selections']) == 8
    assert all(s['status'] == 'partial' for s in alignment['selections'])
    assert not alignment['physical_identity_and_isotropy_derived_from_algebra']
    assert alignment['positive_length_sign_convention_explicit']


def test_rational_and_real_cut_conditions_roundtrip_without_new_primitives():
    text, basis = composed()
    doc = parse(text)
    audit = audit_basis(doc, basis)
    assert audit['primitive_count'] == 10
    assert audit['definition_count'] == 64
    assert not audit['semantic_equivalence_to_source_proven']
    for notation in ('full', 'compact'):
        canonical = format_graph(doc, notation)
        assert parse(canonical) == parse(decode(encode(canonical, 'v2'))) == doc
    assert '<svg' in render(text, alphabet='v2')
