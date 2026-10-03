import pytest

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_comoving_labels import (
    alignment, attribution_checks, polynomial_checks, time_question_checks, trajectory_checks,
)
from scripts.compose_comoving_labels import ROOT, generic_composed, source_composed


def test_auxiliary_coordinate_tracks_uniform_translation_without_identifying_xi():
    result=polynomial_checks();rows=result['claims']
    assert len(rows)==5
    assert rows['constant_auxiliary_coordinate_iff_uniform_displacement']['status']=='valid'
    assert rows['translated_trajectory_keeps_its_initial_label']['status']=='valid'
    assert rows['auxiliary_label_automatically_equals_rescaled_coordinate']['status']=='invalid'
    assert not result['physical_stationarity_equivalence_proved']


@pytest.mark.parametrize('source',[False,True])
def test_all_times_of_each_stationary_point_are_checked_in_the_reference_frame(source):
    result=trajectory_checks(source);rows=result['cases']
    assert len(rows)==(17 if source else 12)
    assert {name for name,value in rows.items() if value}=={'baseline','moving_point_ignored'}
    assert not rows['middle_x_changes'] and not rows['no_time_width']
    if source:assert result['only_stationary_frame_coordinates_read']
    assert not result['continuous_time_interval_proved']


def test_tau_question_keeps_all_four_arguments_and_the_same_event_correspondence():
    result=time_question_checks();rows=result['cases']
    assert len(rows)==14 and rows['baseline']==[True,True]
    assert all(value==[False,False] for name,value in rows.items() if name!='baseline')
    assert not result['tau_formula_derived']


def test_definition_priority_and_equation_purpose_are_separate_attributions():
    rows=attribution_checks()
    assert len(rows)==11 and rows['baseline']==[True]*4
    assert rows['wrong_definition']==[False,True,True,True]
    assert rows['wrong_parent_task']==[True,True,False,True]
    assert rows['wrong_clock_rule']==rows['wrong_subtask']==[True,True,True,False]


def test_source_math_and_text_are_pinned_without_claiming_complete_translation():
    result=alignment();row=result['segments'][0]
    assert row['unit']=='einstein-1905:u0048' and row['start']==0
    assert {r['math_id'] for r in result['segments'][1:]}=={f'M{i:04}' for i in range(84,92)}
    assert result['auxiliary_xprime_not_identified_with_xi']
    assert not result['facsimile_checked'] and not row['full_semantic_equivalence']
    assert result['verified_full_units']==0


@pytest.mark.parametrize('compose,counts',[(generic_composed,(4,4)),(source_composed,(268,245))])
def test_basis_roundtrip_and_frozen_predecessor(compose,counts):
    text,basis=compose();doc=parse(text);audit=audit_basis(doc,basis)
    assert (audit['primitive_count'],audit['definition_count'])==counts
    assert (ROOT/basis['document']).read_text(encoding='utf-8')==text
    for notation in ('compact','full'):
        form=format_graph(doc,notation)
        assert parse(form)==parse(decode(encode(form,'v2')))==doc
    if compose==source_composed:
        old=parse((ROOT/'examples/v014/einstein-homogeneous-coordinates.noema').read_text(encoding='utf-8'))
        assert doc['declarations'][:len(old['declarations'])]==old['declarations']
        assert doc['statements'][:-4]==old['statements'] and len(doc['statements'])==40
