import pytest

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_four_coordinates import (
    alignment, attribution_checks, beta_checks, calibration_checks,
    component_binding_checks, equation_checks, finite_refusals,
    graph_checks, polynomial_checks,
)
from scripts.compose_four_coordinates import ROOT, generic_composed, source_composed


def test_coefficient_change_and_affine_calibration_have_rational_proofs():
    result=polynomial_checks();rows=result['claims']
    assert len(rows)==9
    rejected={'unchanged_phi_is_valid_after_reparameterization','three_light_samples_force_the_moving_origin_value'}
    assert {name for name,row in rows.items() if row['status']=='invalid'}==rejected
    assert all(row['status']=='valid' for name,row in rows.items() if name not in rejected)
    assert not result['full_real_affine_extension_proved']


def test_beta_has_the_historical_positive_inverse_root_meaning():
    result=beta_checks();rows=result['cases']
    assert len(rows)==8
    assert {name for name,value in rows.items() if value}=={'baseline','other_speed','stationary'}
    assert not rows['modern_speed_ratio'] and not rows['negative_root_branch']
    assert result['beta_not_speed_ratio']


def test_old_and_new_four_equations_match_away_from_light_rays():
    result=equation_checks();rows=result['cases']
    assert len(rows)==11
    assert rows['baseline']['second']==['25/8','15/2','10','29/8']
    assert {name for name,row in rows.items() if row['accepted']==[True,True]}=={'baseline','zero_origin','stationary','other_old_scale'}
    assert rows['old_phi_reused']['accepted']==[False,False]
    assert result['same_speed_for_all_four_components']


def test_five_calibration_values_need_affinity_and_the_moving_origin():
    result=calibration_checks();rows=result['cases']
    assert len(rows)==11
    assert {name for name,value in rows.items() if value}=={'x_row','y_row','z_row','nonlinear_same_five_values'}
    assert not rows['missing_origin_constraint']
    assert result['affine_membership_is_separate_from_five_values']


def test_spatial_functions_bind_to_the_correct_same_event_components():
    result=component_binding_checks();rows=result['cases']
    assert len(rows)==6 and rows['baseline']==[True]*3
    assert rows['swapped_transverse_functions']==[True,False,False]
    assert rows['wrong_x_time_argument']==[False,True,True]
    assert result['separate_spatial_rows_bound_to_corresponding_components']


def test_equation_graph_checks_missing_extra_and_equal_value_records():
    result=graph_checks();rows=result['cases']
    assert len(rows)==7
    assert rows['baseline']==rows['duplicate_value_records']==rows['different_value_alias']==[True,True]
    assert rows['excluded_alias_relation']==[False,False]
    assert rows['spurious_relation']==rows['omitted_relation']==rows['empty_graph']==[False,True]
    assert result['both_directions_and_equal_value_aliases_checked']


def test_full_affine_membership_is_not_replaced_by_five_samples():
    rows=finite_refusals()
    assert rows['all_real_affine_membership']['refused']


def test_added_interpretation_rewrite_and_beta_definition_remain_distinct():
    rows=attribution_checks()
    assert len(rows)==10 and rows['baseline']==[True]*3
    assert rows['wrong_added_premise']==[False,True,True]
    assert rows['wrong_new_form']==[True,False,True]
    assert rows['wrong_beta_content']==[True,True,False]


def test_alignment_does_not_claim_added_calibration_is_verbatim_source():
    result=alignment();rows=result['segments']
    assert {row['unit'] for row in rows}=={f'einstein-1905:u{i:04}' for i in range(81,85)}
    assert {row['math_id'] for row in rows if 'math_id' in row}=={f'M{i:04}' for i in range(134,137)}
    assert result['coefficient_reparameterization_explicit'] and result['affine_calibration_is_additional_interpretation']
    assert not result['facsimile_checked'] and result['verified_full_units']==0


@pytest.mark.parametrize('compose,counts',[(generic_composed,(4,33)),(source_composed,(329,422))])
def test_basis_roundtrip_and_frozen_predecessor(compose,counts):
    text,basis=compose();doc=parse(text);audit=audit_basis(doc,basis)
    assert (audit['primitive_count'],audit['definition_count'])==counts
    assert (ROOT/basis['document']).read_text(encoding='utf-8')==text
    for notation in ('compact','full'):
        form=format_graph(doc,notation)
        assert parse(form)==parse(decode(encode(form,'v2')))==doc
    if compose==source_composed:
        previous=parse((ROOT/'examples/v014/einstein-transverse-space.noema').read_text(encoding='utf-8'))
        assert doc['declarations'][:len(previous['declarations'])]==previous['declarations']
        assert doc['statements'][:-3]==previous['statements'] and len(doc['statements'])==66
