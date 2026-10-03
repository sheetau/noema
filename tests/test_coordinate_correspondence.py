import pytest

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_coordinate_correspondence import (
    alignment, attribution_checks, chart_checks, equation_checks, tuple_binding_checks,
)
from scripts.compose_coordinate_correspondence import ROOT, generic_composed, source_composed


@pytest.mark.parametrize('source',[False,True])
def test_coordinate_mapping_preserves_events_but_does_not_identify_coincident_events(source):
    rows=chart_checks(source)
    assert len(rows)==12
    if source:
        assert rows['baseline']==rows['coincident_events']==rows['equivalent_source_same_output']==[True]
        assert rows['same_input_different_output']==rows['equivalent_source_different_output']==[False]
    else:
        assert rows['baseline']==[True,True,True,False]
        assert rows['swapped_event_targets']==[True,True,False,True]
        assert rows['equivalent_target_alias'][:2]==[True,True]
        assert rows['equivalent_source_different_output'][:2]==[True,False]


def test_tuple_components_bind_to_the_same_event_frame_place_and_units():
    result=tuple_binding_checks();rows=result['cases']
    assert len(rows)==23
    assert {name for name,value in rows.items() if value}=={'baseline','moving_frame','tuple_alias'}
    assert not result['full_measurement_model_evaluated']


@pytest.mark.parametrize('source',[False,True])
def test_equations_must_capture_all_and_only_the_coordinate_correspondence(source):
    result=equation_checks(source);rows=result['cases']
    assert len(rows)==11
    assert rows['exact']==rows['reordered']==rows['duplicate_equation']==[True,True]
    assert rows['missing_x']==rows['missing_y']==rows['too_restrictive']==[False,False]
    assert rows['empty']==rows['missing_correspondence']==[False,False]
    assert not result['general_transformation_derived']


def test_finding_equations_is_attributed_as_an_open_task_without_executing_content():
    rows=attribution_checks()
    assert rows['baseline']==[True,True]
    assert rows['wrong_claim']==rows['wrong_prior_setting']==[False,True]
    assert rows['wrong_question']==[True,False]


def test_source_association_remains_partial():
    result=alignment();row=result['segments'][0]
    assert row['unit']=='einstein-1905:u0046' and row['start']==0
    assert result['coordinate_chart_completeness_not_proved']
    assert result['verified_full_units']==0 and not result['facsimile_checked']
    assert not row['full_semantic_equivalence']


@pytest.mark.parametrize('compose,counts',[(generic_composed,(0,8)),(source_composed,(255,216))])
def test_basis_roundtrip_and_frozen_predecessor(compose,counts):
    text,basis=compose();doc=parse(text);audit=audit_basis(doc,basis)
    assert (audit['primitive_count'],audit['definition_count'])==counts
    assert (ROOT/basis['document']).read_text(encoding='utf-8')==text
    for notation in ('compact','full'):
        form=format_graph(doc,notation)
        assert parse(form)==parse(decode(encode(form,'v2')))==doc
    if compose==source_composed:
        old=parse((ROOT/'examples/v014/einstein-frame-measurements.noema').read_text(encoding='utf-8'))
        assert doc['declarations'][:len(old['declarations'])]==old['declarations']
        assert doc['statements'][:-2]==old['statements'] and len(doc['statements'])==34
