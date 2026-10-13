from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_total_differential import (
    polynomial_checks, remainder_checks, counterexample_checks, field_binding_checks, finite_refusals, alignment,
)
from scripts.compose_total_differential import ROOT, PARENT, composed, generic_composed


def test_uniform_error_bounds_and_arbitrary_scale_counterexample_algebra():
    result=polynomial_checks();rows=result['claims'];assert len(rows)==5
    assert all(row['status']=='valid' for row in rows.values())
    assert result['rational_error_identities_and_bounds_only']
    assert not result['arbitrary_real_chain_rule_proved']


def test_remainder_distinguishes_linear_quadratic_and_invalid_bounds():
    result=remainder_checks();rows=result['cases'];assert len(rows)==12
    accepted={'affine_mixed_step','quadratic_small_mixed_step','two_axes_only','reordered_axes'}
    for name,row in rows.items():assert row==[name in accepted]
    assert result['finite_remainder_checks_not_a_full_epsilon_delta_verification']


def test_generic_axis_selection_does_not_leak_unlisted_components():
    result=remainder_checks();rows=result['cases']
    assert rows['two_axes_only']==rows['reordered_axes']==[True]
    assert rows['duplicate_axes']==rows['empty_axes']==[False]
    assert result['unlisted_coordinates_projected_to_zero_before_function_evaluation']


def test_axis_partials_alone_do_not_establish_a_uniform_linear_approximation():
    result=counterexample_checks();rows=result['cases'];assert len(rows)==15
    for name,row in rows.items():assert row==[not name.endswith(':xt')]
    assert result['all_coordinate_axis_remainders_zero_but_mixed_direction_fails']
    assert result['all_positive_diagonal_scales_also_checked_by_rational_inequality']


def test_same_six_gradients_bind_total_and_partial_conditions_separately():
    result=field_binding_checks();rows=result['cases'];assert len(rows)==6
    assert rows['baseline']==[True,True,True]
    assert rows['partials_only']==[False,True,False]
    assert rows['total_only']==[True,False,False]
    assert rows['wrong_gradient']==rows['wrong_point']==rows['outside_region']==[False,True,False]
    assert result['total_and_partial_derivative_relations_are_fixture_oracles']


def test_full_neighborhood_and_epsilon_delta_are_not_finitely_sampled():
    rows=finite_refusals();assert len(rows)==2
    assert all(row['refused'] and 'Cannot finitely quantify' in row['reason'] for row in rows.values())


def test_local_regularity_annotation_adds_no_source_text_coverage():
    result=alignment();assert len(result['segments'])==2
    assert all(row['status']=='explicit_interpretive_annotation' and not row['full_semantic_equivalence'] for row in result['segments'])
    assert result['new_source_text_ranges']==result['verified_full_units']==0


def test_dependency_library_and_full_document_preserve_definitions_and_roundtrip():
    for builder,counts in ((generic_composed,(4,21,0)),(composed,(533,854,154))):
        text,basis=builder();doc=parse(text);audit=audit_basis(doc,basis)
        assert (audit['primitive_count'],audit['definition_count'],len(doc['statements']))==counts
        assert (ROOT/basis['document']).read_text(encoding='utf-8')==text
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            assert parse(form)==parse(decode(encode(form,'v2')))==doc
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    assert doc['declarations'][:len(parent['declarations'])]==parent['declarations']
    assert doc['statements']==parent['statements']
    generic=parse(generic_composed()[0]);definitions={d['name']:d for d in doc['declarations']}
    assert all(d==definitions[d['name']] for d in generic['declarations'])
    assert {d['name'] for d in generic['declarations'] if d['kind']=='primitive'}=={'aa','ab','ac','ad'}
