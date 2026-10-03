from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_curved_clock import (
    alignment, attribution_checks, binding_checks, continuity_checks,
    infinite_checks, speed_checks, truth_checks,
)
from scripts.compose_curved_clock import ROOT, composed


def test_curve_samples_bind_same_records_and_do_not_prescribe_clock_law():
    result=binding_checks();rows=result['cases']
    assert len(rows)==14
    for name in ('baseline','negative_times','common_dial_offset','changed_reading','missing_midpoint','missing_corner_record'):
        assert rows[name]==[True]*3
    assert rows['open_straight']==[True,True,False]
    for name in ('wrong_curve_point','candidate_record_mismatch','extra_inconsistent_chart','wrong_clock_at_corner'):
        assert rows[name]==[False,True,True]
    assert rows['wrong_time_unit']==[False,False,True]
    assert rows['same_endpoint_event']==[False]*3
    assert result['closed_polynomial_samples_do_not_have_constant_speed']
    assert result['binding_checks_do_not_certify_kinematics_or_clock_law']


def test_common_speed_allows_turning_without_allowing_larger_norm():
    rows=speed_checks()
    assert len(rows)==8
    assert {name for name,row in rows.items() if row['accepted']}=={
        'x_direction','y_direction','reverse','diagonal'}


def test_continuity_keeps_domain_and_relative_endpoint_conditions():
    result=continuity_checks();rows=result['cases']
    assert len(rows)==7
    assert {name for name,row in rows.items() if row['status']=='invalid'}=={
        'point_outside_domain','empty_domain_has_no_continuity_point'}
    assert result['actual_definitions_specialized_to_rationals']


def test_full_kinematics_worldline_and_error_do_not_use_sampled_domains():
    rows=infinite_checks()
    assert set(rows)=={'kinematics','worldline','complete_setting','approximation'}
    assert all('rational number domain' in row for row in rows.values())


def test_assumption_can_be_attributed_while_its_content_is_false():
    result=truth_checks();rows=result['cases']
    assert len(rows)==4
    assert rows['(True, False)']==[False,False,True]
    assert rows['(True, True)']==[True,True,True]
    assert rows['(False, True)']==[True,False,True]
    assert result['polygon_result_alone_does_not_establish_curve_law']


def test_prior_proved_status_and_scoped_extension_are_separate():
    result=attribution_checks();rows=result['cases']
    assert len(rows)==11 and rows['baseline']==[True]*4
    assert rows['wrong_author']==rows['wrong_context']==[False]*4
    assert rows['wrong_proved_node']==rows['missing_proved_status']==[False,True,True,True]
    assert rows['wrong_assumption_scope']==[True,False,True,True]
    assert rows['wrong_claim_scope']==[True,True,False,True]
    assert rows['wrong_inference_premise']==[True,True,True,False]
    assert result['quoted_physics_never_evaluated']


def test_curve_unit_stops_before_earth_comparison():
    result=alignment();rows=result['segments']
    assert {r['unit'] for r in rows}=={'einstein-1905:u0128'}
    assert {r['math_id'] for r in rows if 'math_id' in r}=={'M0237','M0238','M0239','M0240','M0241'}
    assert 'Man schließt daraus' not in rows[0]['source']
    assert result['earth_clock_comparison_not_yet_connected']
    assert result['expression_and_physical_proof_are_distinct']
    assert result['verified_full_units']==0 and not result['facsimile_checked']


def test_basis_script_roundtrip_and_parent_preservation():
    text,basis=composed();doc=parse(text);audit=audit_basis(doc,basis)
    assert (audit['primitive_count'],audit['definition_count'])==(439,643)
    assert (ROOT/basis['document']).read_text(encoding='utf-8')==text
    for notation in ('compact','full'):
        form=format_graph(doc,notation)
        assert parse(form)==parse(decode(encode(form,'v2')))==doc
    parent=parse((ROOT/'examples/v014/einstein-polygon-clock.noema').read_text(encoding='utf-8'))
    assert doc['declarations'][:len(parent['declarations'])]==parent['declarations']
    assert doc['statements'][:-4]==parent['statements'] and len(doc['statements'])==125
