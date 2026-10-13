from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_field_constraints import (
    polynomial_checks, constraints_checks, full_jet_checks, chain_checks,
    counterexample_checks, connection_checks, finite_refusals, alignment,
)
from scripts.compose_field_constraints import ROOT, PARENT, composed, generic_composed


def test_eight_transformed_residual_identities_hold_for_arbitrary_rational_jets():
    result=polynomial_checks();rows=result['identities'];assert len(rows)==8
    assert all(row['status']=='valid' for row in rows.values())
    assert result['time_coordinate']=='u=V*t'
    assert result['rational_coefficient_algebra_only_not_actual_real_derivative_chain_rule']


def test_divergence_adds_constraints_and_validates_previously_unused_diagonals():
    result=constraints_checks();rows=result['cases'];assert len(rows)==8
    assert rows['baseline']==rows['zero_fields']==[True,True]
    assert rows['electric_divergence']==rows['magnetic_divergence']==rows['invalid_diagonal']==[True,False]
    assert rows['missing_curl']==rows['zero_light']==rows['negative_light']==[False,False]


def test_all_six_new_diagonal_values_belong_to_the_same_fields_and_point():
    result=full_jet_checks();rows=result['cases'];assert len(rows)==9
    for name,row in rows.items():assert row==[name=='baseline']
    assert result['actual_derivative_relation_is_fixture_oracle']


def test_every_transformed_derivative_is_checked_and_preserves_all_eight_conditions():
    result=chain_checks();rows=result['cases'];assert len(rows)==27
    for name,row in rows.items():assert row==[not name.startswith('changed_')]*2
    assert result['coefficient_transform_not_a_differentiability_proof']


def test_previous_counterexamples_fail_divergence_even_when_transport_is_correct():
    result=counterexample_checks();rows=result['cases'];assert len(rows)==3
    assert all(row==[True,False,True,False] for row in rows.values())
    assert result['counterexamples_excluded_by_old_divergence_not_by_breaking_transform']


def test_old_and_new_jets_bind_to_inverse_related_points_and_same_fields():
    result=connection_checks();rows=result['cases'];assert len(rows)==6
    for name,row in rows.items():assert row==[name=='baseline']
    assert result['old_point_is_inverse_image_of_same_new_point']
    assert result['derivative_and_chain_relations_are_explicit_fixture_oracles']


def test_finite_fixtures_do_not_establish_full_real_differentiability():
    rows=finite_refusals();assert len(rows)==3
    assert all(row['refused'] and 'Cannot finitely quantify' in row['reason'] for row in rows.values())


def test_annotation_does_not_claim_new_source_words_or_complete_semantics():
    result=alignment();assert len(result['segments'])==2
    assert all(row['status']=='explicit_interpretive_annotation' and not row['full_semantic_equivalence'] for row in result['segments'])
    assert result['new_source_text_ranges']==result['verified_full_units']==0
    assert result['additional_mathematical_conditions_not_explicit_source_words']


def test_all_parent_statements_preserved_and_constraint_notations_roundtrip():
    for builder,counts in ((generic_composed,(3,16,0)),(composed,(533,841,154))):
        text,basis=builder();doc=parse(text);audit=audit_basis(doc,basis)
        assert (audit['primitive_count'],audit['definition_count'],len(doc['statements']))==counts
        assert (ROOT/basis['document']).read_text(encoding='utf-8')==text
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            assert parse(form)==parse(decode(encode(form,'v2')))==doc
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    assert doc['declarations'][:len(parent['declarations'])]==parent['declarations']
    assert doc['statements']==parent['statements']
