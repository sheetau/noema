import pytest

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_transverse_time import (
    alignment, attribution_checks, finite_refusals, geometry_checks, polynomial_checks,
    protocol_checks, reuse_checks, scope_checks, speed_checks, tau_checks,
)
from scripts.compose_transverse_time import ROOT, generic_composed, source_composed


def test_equal_transverse_legs_and_derivative_cancellation_preserve_total_speed():
    result=polynomial_checks();rows=result['claims']
    assert len(rows)==8
    assert rows['total_light_speed_can_replace_transverse_component']['status']=='invalid'
    assert all(row['status']=='valid' for name,row in rows.items() if name!='total_light_speed_can_replace_transverse_component')
    assert not result['general_chain_rule_or_physical_geometry_proved']


def test_square_root_and_generalized_trial_keep_their_preserved_definitions():
    assert all(reuse_checks().values())


def test_positive_transverse_root_is_not_the_total_light_speed():
    result=speed_checks();rows=result['cases']
    assert len(rows)==9
    assert {name for name,value in rows.items() if value}=={'three_four_five','stationary_limit','other_triangle'}
    assert result['total_speed_distinct_from_component']


def test_y_and_z_permutations_vary_only_the_selected_axis():
    rows=tau_checks()['cases']
    assert len(rows)==6 and rows['baseline']==rows['shifted_clock_origin']==[True]*4
    assert rows['y_dependence']==[False,True,False,True]
    assert rows['z_dependence']==[True,False,True,False]
    assert rows['both_dependences']==[False]*4
    assert rows['nonlinear_time']==[False,False,True,True]


def test_trial_accepts_both_transverse_axes_and_rejects_the_longitudinal_one():
    result=protocol_checks();rows=result['cases']
    assert len(rows)==8 and {name for name,value in rows.items() if value}=={'y_axis','z_axis'}
    assert result['both_transverse_roles_tested']


def test_event_coordinates_keep_xprime_other_axis_and_both_travel_times():
    result=geometry_checks();rows=result['cases']
    assert len(rows)==13 and {name for name,value in rows.items() if value}=={'y_axis','z_axis'}
    assert not rows['wrong_x_motion'] and not rows['total_speed_as_component']
    assert result['fixed_xprime_and_other_transverse_coordinate']


def test_both_axis_scopes_are_nonempty_complete_and_use_the_same_law():
    result=scope_checks();rows=result['cases']
    assert len(rows)==12 and rows['baseline']
    assert not any(value for name,value in rows.items() if name!='baseline')
    assert result['both_axes_nonempty_and_all_trials_checked']


def test_real_neighborhood_and_all_space_claims_are_not_finitely_sampled():
    result=finite_refusals()
    assert len(result)==3 and all(row['refused'] for row in result.values())


def test_analogous_argument_refers_to_the_prior_limit_step_without_asserting_proof():
    rows=attribution_checks()
    assert len(rows)==9 and rows['baseline']==[True,True]
    assert rows['wrong_speed_content']==[False,True]
    assert rows['wrong_earlier_argument']==rows['wrong_conclusion']==[True,False]


def test_source_alignment_preserves_both_zero_partial_equations_and_component_speed():
    result=alignment();rows=result['segments']
    assert {row['unit'] for row in rows}=={f'einstein-1905:u{i:04}' for i in range(59,62)}
    assert {row['math_id'] for row in rows if 'math_id' in row}=={f'M{i:04}' for i in range(106,111)}
    assert result['transverse_component_not_total_speed'] and not result['facsimile_checked']
    assert result['verified_full_units']==0


@pytest.mark.parametrize('compose,counts',[(generic_composed,(4,13)),(source_composed,(300,326))])
def test_basis_roundtrip_and_frozen_predecessor(compose,counts):
    text,basis=compose();doc=parse(text);audit=audit_basis(doc,basis)
    assert (audit['primitive_count'],audit['definition_count'])==counts
    assert (ROOT/basis['document']).read_text(encoding='utf-8')==text
    for notation in ('compact','full'):
        form=format_graph(doc,notation)
        assert parse(form)==parse(decode(encode(form,'v2')))==doc
    if compose==source_composed:
        old=parse((ROOT/'examples/v014/einstein-arbitrary-origins.noema').read_text(encoding='utf-8'))
        assert doc['declarations'][:len(old['declarations'])]==old['declarations']
        assert doc['statements'][:-2]==old['statements'] and len(doc['statements'])==49
