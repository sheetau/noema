import json

import pytest

from noema.grammar import parse
from scripts.check_density_referents import REPORT,build_report
from scripts.compose_density_referents import ROOT,PARENT,source_composed


@pytest.fixture(scope='module')
def result():
    return build_report()


def test_shared_referents_allow_signed_density_and_all_defined_formula_cases(result):
    cases=result['finite']['cases']
    assert len(cases)==27
    assert all(row['results']==[True]*4 for row in cases)
    assert {row['density'] for row in cases}=={-4,0,4}
    assert any(row['speed']==3 and row['velocity']==[10,0,0] for row in cases)


def test_equal_numbers_do_not_replace_same_matter_event_frame_and_context(result):
    rows=result['finite']['binding_contrasts']
    assert len(rows)==40
    for prefix in ('old','new'):
        for name in ('matter','frame','event','density','ux','uy','uz','context'):
            assert rows[prefix+'_assignment_'+name]==[False,False,True,True]
        for name in ('matter','frame','event','point','context'):
            assert rows[prefix+'_location_'+name]==[False,False,True,True]


def test_coordinate_correspondence_is_required_even_with_accepted_location_assignments(result):
    rows=result['finite']['binding_contrasts']
    for axis in ('x','y','z','t'):
        assert rows['coordinate_'+axis]==[False,False,True,True]
    for name in ('old','new','speed','context'):
        assert rows['frames_'+name]==[False,False,True,True]


def test_electric_assignment_is_bound_without_adding_magnetic_field_conditions(result):
    rows=result['finite']['binding_contrasts']
    for name in ('frame','field','region','context'):
        assert rows['electric_'+name]==[False,False,True,True]
    assert result['finite']['no_old_field_or_magnetic_conditions_executed']
    assert result['finite']['exactly_three_new_partials']


def test_reference_assignment_does_not_prove_derivatives_or_invent_unknown_interpretations(result):
    assert result['finite']['derivative_contrasts']=={
        name:[True,False,True,False] for name in ('compensated_diagonals','missing_x','missing_y','missing_z')}
    assert result['finite']['unknown_interpretations_refused']
    assert not result['finite']['actual_physical_assignments_validated']


def test_historical_parent_and_source_association_are_retained(result):
    doc=parse(source_composed()[0]);parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    assert doc['declarations'][:len(parent['declarations'])]==parent['declarations']
    assert len(doc['declarations'])==len(parent['declarations'])+2
    assert doc['statements']==parent['statements']
    assert len(doc['statements'])==174
    assert result['new_primitives']==result['new_author_statements']==0
    segment=result['alignment']['segments'][0]
    assert (segment['unit'],segment['math_id'])==('einstein-1905:u0236','M0390')
    assert not result['alignment']['semantic_completion']
    assert result['verified_full_units']=={'kant-1784':0,'einstein-1905':0}


def test_standalone_roundtrips_and_saved_evidence_agree(result):
    assert result['roundtrips'] and result['finite']['standalone_agrees']
    assert result==json.loads(REPORT.read_text(encoding='utf-8'))
