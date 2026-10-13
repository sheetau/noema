from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_charge_calibration import conversion_checks, source_checks, distinct_target_check, attribution_checks, alignment
from scripts.compose_charge_calibration import ROOT, PARENT, composed, generic_composed


def test_quantity_comparison_preserves_kind_and_positive_unit_scale():
    rows=conversion_checks()['cases'];assert len(rows)==8
    assert rows['same_unit']==rows['different_unit_same_quantity']==rows['signed_quantity']==[True]
    assert all(rows[n]==[False] for n in ('same_numbers_different_units','different_kind','zero_scale','negative_scale','opposite_values'))


def test_calibration_keeps_objects_trial_frame_event_unit_and_value_together():
    result=source_checks();rows=result['cases'];assert len(rows)==26
    assert rows['baseline']==[True,True,True]
    assert all(value[2] is False for name,value in rows.items() if name!='baseline')
    assert rows['charge_wrong_body']==[True,False,False]
    assert rows['force_wrong_target']==rows['equal_amount_wrong_frame']==[False,True,False]
    assert result['no_second_body_rest_requirement_added']
    assert result['force_charge_and_pointlike_physical_meanings_not_verified']


def test_equal_amount_does_not_collapse_two_objects_into_one():
    assert distinct_target_check()['self_pair_rejected']


def test_hypothetical_calibration_is_attributed_without_executing_its_content():
    result=attribution_checks();assert len(result['cases'])==6
    assert all(value==[name=='-1'] for name,value in result['cases'].items())
    assert result['assumption_not_actual_observation']
    assert result['quoted_measurement_contents_not_executed']


def test_source_range_is_partial_and_retains_unexplained_physical_concepts():
    result=alignment();assert len(result['segments'])==2
    assert result['segments'][0]['unit']=='einstein-1905:u0173'
    assert result['segments'][0]['source'].startswith('welche im ruhenden System')
    assert result['segments'][1]['math_id']=='M0315'
    assert result['physical_concept_gaps_remain_within_partial_range']
    assert result['verified_full_units']==0


def test_library_parent_and_notation_roundtrips_are_preserved():
    for builder,counts in ((generic_composed,(2,8,0)),(composed,(572,908,164))):
        text,basis=builder();doc=parse(text);audit=audit_basis(doc,basis)
        assert (audit['primitive_count'],audit['definition_count'],len(doc['statements']))==counts
        assert (ROOT/basis['document']).read_text(encoding='utf-8')==text
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            assert parse(form)==parse(decode(encode(form,'v2')))==doc
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    assert doc['declarations'][:len(parent['declarations'])]==parent['declarations']
    assert doc['statements'][:-1]==parent['statements']
    byname={d['name']:d for d in doc['declarations']}
    assert all(d==byname[d['name']] for d in parse(generic_composed()[0])['declarations'])
