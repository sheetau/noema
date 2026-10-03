import pytest

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_frame_measurements import (
    actual_cut_checks, alignment, attribution_checks, clock_scope_checks,
    coverage_checks, spatial_checks, temporal_checks, wrapper_checks,
)
from scripts.compose_frame_measurements import ROOT, generic_composed, source_composed


def test_every_place_needs_every_coordinate_component():
    rows=coverage_checks()
    assert len(rows)==64
    assert sum(r['result'] for r in rows)==1


def test_clock_network_does_not_extend_time_to_unclocked_places():
    rows=clock_scope_checks()
    assert rows['baseline']==rows['event_at_empty_place']==[True,True]
    assert rows['second_clock_at_empty_place']==rows['second_event_at_clock_place']==[True,False]
    assert rows['clock_outside_space']==rows['clock_unsynchronized']==[False,True]


def test_coordinates_keep_the_same_frame_axes_origin_ruler_and_value():
    result=spatial_checks();rows=result['cases']
    assert len(rows)==20
    assert rows['baseline']==rows['same_value_alias']==[True,True]
    assert rows['conflicting_value']==rows['ruler_replaced']==rows['axis_replaced']==[False,True]
    assert rows['wrong_unit']==[False,False]
    assert result['real_cut_carrier_substitution'] and not result['full_real_uniqueness_proved']


def test_each_frame_uses_its_own_static_clocks_and_reference():
    result=temporal_checks();rows=result['cases'];local=result['local_readings']
    assert len(rows)==20
    assert rows['baseline']==rows['same_value_alias']==[True,True]
    assert rows['reference_from_other_frame']==rows['clock_not_stationary']==[False,True]
    assert rows['event_at_unclocked_place']==[True,True]
    assert local['event_at_unclocked_place']==local['conflicting_local_reading']==[False,True]
    assert result['outer_scope_uses_tabulated_local_fixtures'] and not result['full_real_uniqueness_proved']


def test_actual_integer_cuts_keep_signed_coordinate_values():
    rows=actual_cut_checks()['cases']
    assert len(rows)==6 and {name for name,value in rows.items() if value}=={'-2','0','3'}


def test_both_frames_are_required_and_space_and_time_are_distinct_conditions():
    rows=wrapper_checks()['cases']
    assert rows['baseline']==[True,True]
    assert rows['rest_space_invalid']==rows['moving_space_invalid']==[False,True]
    assert rows['rest_time_invalid']==rows['moving_time_invalid']==[True,False]


def test_measurement_assumptions_keep_attribution_and_previous_setting():
    rows=attribution_checks()
    assert rows['baseline']==[True,True]
    assert all(row==[False,False] for name,row in rows.items() if name!='baseline')


def test_full_range_association_stays_partial_and_discloses_interpretation():
    result=alignment();row=result['segments'][0]
    assert row['unit']=='einstein-1905:u0045' and row['start']==0
    assert result['projection_procedure_is_explicit_interpretation']
    assert not result['facsimile_checked'] and not row['full_semantic_equivalence']
    assert result['verified_full_units']==0


@pytest.mark.parametrize('compose,counts',[(generic_composed,(0,4)),(source_composed,(248,197))])
def test_basis_roundtrip_and_frozen_predecessor(compose,counts):
    text,basis=compose();doc=parse(text);audit=audit_basis(doc,basis)
    assert (audit['primitive_count'],audit['definition_count'])==counts
    assert (ROOT/basis['document']).read_text(encoding='utf-8')==text
    for notation in ('compact','full'):
        form=format_graph(doc,notation)
        assert parse(form)==parse(decode(encode(form,'v2')))==doc
    if compose==source_composed:
        old=parse((ROOT/'examples/v014/einstein-parallel-histories.noema').read_text(encoding='utf-8'))
        assert doc['declarations'][:len(old['declarations'])]==old['declarations']
        assert doc['statements'][:-2]==old['statements'] and len(doc['statements'])==32
