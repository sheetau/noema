import pytest

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_reverse_transform import (
    alignment, attribution_checks, composition_checks, graph_checks,
    polynomial_checks, setup_checks, signed_beta_checks,
)
from scripts.compose_reverse_transform import ROOT, generic_composed, source_composed


def test_two_applications_give_reciprocity_without_forcing_phi_one():
    result=polynomial_checks();rows=result['claims']
    assert len(rows)==7
    assert {name for name,row in rows.items() if row['status']=='invalid'}=={
        'reciprocity_forces_each_factor_one','zero_origin_identity_forces_product_one','stationary_rescaling_is_identity'}
    assert all(row['status'] in ('valid','invalid') for row in rows.values())
    assert not result['relative_rest_alone_proves_identity'] and not result['phi_normalized_to_one']


def test_signed_beta_accepts_opposite_velocity_with_same_positive_branch():
    result=signed_beta_checks();rows=result['cases']
    assert len(rows)==8
    assert {name for name,value in rows.items() if value}=={'positive','negative','stationary'}
    assert result['old_positive_speed_definition_unchanged']


def test_same_function_is_evaluated_at_opposite_signed_speeds():
    result=composition_checks();rows=result['cases']
    assert len(rows)==10 and rows['reciprocal']['accepted']==[True]*4
    assert rows['reciprocal']['first']==rows['reciprocal']['last']==['7','3','4','2']
    assert rows['nonreciprocal']['accepted']==[True,True,False,False]
    assert rows['nonreciprocal']['last']==['35','15','20','10']
    assert rows['zero_nonreciprocal']['accepted']==[True,True,True,False]
    assert rows['same_phi_value_reused']['accepted']==[False,False,False,True]
    assert rows['wrong_middle_record']['accepted']==[False,True,True,True]
    assert result['same_function_at_opposite_velocities']


def test_every_event_needs_all_three_records_and_a_nonzero_identity_probe():
    result=graph_checks();rows=result['cases']
    assert len(rows)==8 and rows['reciprocal']==rows['duplicate_alias']==[True]*4
    assert rows['nonreciprocal']==[True,True,False,False]
    assert rows['zero_only']==[True,True,True,False]
    assert rows['missing_third_record']==rows['wrong_event']==rows['empty_scope']==rows['conflicting_alias']==[False]*4
    assert result['all_record_choices_not_only_one_witness']


def test_third_frame_setup_retains_signed_motion_and_three_zero_times():
    result=setup_checks();rows=result['cases']
    assert len(rows)==9 and {name for name,value in rows.items() if value}=={'baseline'}
    assert result['signed_velocity_units_frame_axis_and_zero_time_checked']


def test_source_attribution_keeps_claimed_identity_separate_from_composition():
    rows=attribution_checks()
    assert len(rows)==12 and rows['baseline']==[True]*7
    assert rows['wrong_composition']==[True,True,True,False,True,True,True]
    assert rows['wrong_identity']==rows['lost_clarity_claim']==[True]*5+[False,True]
    assert rows['wrong_reciprocity']==[True]*6+[False]


def test_current_unknown_stage_does_not_mutate_its_predecessor():
    text,basis=source_composed();doc=parse(text);audit=audit_basis(doc,basis)
    dependencies=audit['definition_dependencies']['definition_primitive_dependencies']
    assert 'zgl' in dependencies['srp'] and 'zfm' not in dependencies['srp']
    assert 'zfm' in dependencies['sqd'] and 'zgl' not in dependencies['sqd']
    assert 'zeq' in dependencies['srh']


def test_source_alignment_does_not_certify_relative_rest_as_identity():
    result=alignment();rows=result['segments']
    assert {row['unit'] for row in rows}=={f'einstein-1905:u{i:04}' for i in range(92,97)}
    assert {row['math_id'] for row in rows if 'math_id' in row}=={f'M{i:04}' for i in range(148,170)}
    assert not result['facsimile_checked'] and result['verified_full_units']==0
    assert result['relative_rest_to_identity_is_attributed_not_proved']


@pytest.mark.parametrize('compose,counts',[(generic_composed,(4,40)),(source_composed,(363,474))])
def test_basis_roundtrips_and_frozen_parent(compose,counts):
    text,basis=compose();doc=parse(text);audit=audit_basis(doc,basis)
    assert (audit['primitive_count'],audit['definition_count'])==counts
    assert (ROOT/basis['document']).read_text(encoding='utf-8')==text
    for notation in ('compact','full'):
        form=format_graph(doc,notation)
        assert parse(form)==parse(decode(encode(form,'v2')))==doc
    if compose==source_composed:
        previous=parse((ROOT/'examples/v014/einstein-spherical-wave.noema').read_text(encoding='utf-8'))
        assert doc['declarations'][:len(previous['declarations'])]==previous['declarations']
        assert doc['statements'][:-7]==previous['statements'] and len(doc['statements'])==84
