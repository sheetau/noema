import pytest

from noema.finite_semantics import evaluate_document
from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_described_appraisals import candidate
from scripts.check_rod_setup import (
    ARITHMETIC, alignment, attribution_checks, guarded, initial_checks,
    motion_checks, numeric_checks, polynomial_checks, question_checks, stage_checks,
)
from scripts.compose_rod_setup import ROOT, generic_composed, source_composed


def test_positive_translation_preserves_transverse_coordinates_and_equal_time_positions():
    rows=numeric_checks()
    assert len(rows)==9
    assert {name for name,value in rows.items() if value}=={'positive_motion','same_time_same_place'}


def test_uniform_pair_laws_do_not_infer_unobserved_intermediate_positions():
    rows=polynomial_checks()
    assert len(rows)==6
    assert rows['endpoint_pair_determines_intermediate_position']['status']=='invalid'
    assert sum(row['status']=='valid' for row in rows.values())==5


def test_initial_measurement_does_not_identify_its_observer_with_the_later_one():
    rows=initial_checks()
    assert len(rows)==10 and [name for name,value in rows.items() if value]==['distinct_initial_observer']


def test_all_points_all_times_and_duplicate_time_records_are_checked():
    result=motion_checks()
    rows=result['cases']
    assert len(rows)==20 and [name for name,value in rows.items() if value]==['baseline']
    assert not rows['middle_time_x_deviation'] and not rows['interior_point_deviation']
    assert not rows['duplicate_time_different_position']
    assert not result['continuous_time_physics_evaluated']
    assert result['scope_completeness_is_an_explicit_assumption_not_inferred_from_samples']


def test_ordered_stages_preserve_rod_axis_and_distinct_measurement_settings():
    rows=stage_checks()
    assert len(rows)==10 and [name for name,value in rows.items() if value]==['baseline']


def test_question_preserves_method_context_empty_and_multiple_answer_possibilities():
    rows=question_checks()
    assert len(rows)==10
    assert {name for name,value in rows.items() if value}=={
        'direct_five','slice_four','equal_values_allowed','multiple_candidates_allowed'}
    assert not rows['same_method_identity'] and not rows['contexts_swapped']


def test_attributing_setup_and_question_does_not_execute_their_physical_contents():
    rows=attribution_checks()
    assert rows['baseline']==[True,True]
    assert rows['wrong_setup']==[False,True] and rows['wrong_question']==[True,False]
    assert rows['wrong_scope']==rows['wrong_author']==[False,False]


def test_real_trajectory_and_full_question_answers_are_not_finitely_sampled():
    cut='k bb[n p b b]'
    doc=parse(generic_composed()[0]+'q[k sbm['+' '.join([cut]*9)+']].')
    with pytest.raises(ValueError,match='rational number domain'):
        evaluate_document(doc,individuals=('point',),situations=('text',),primitives=ARITHMETIC)
    doc=candidate(source_composed()[0],'q[k sbv[]].')
    model=guarded(doc)
    model.update(xw=lambda:'directmethod',xx=lambda:'slicemethod')
    with pytest.raises(ValueError,match='rational number domain'):
        evaluate_document(doc,individuals=('directmethod','slicemethod'),situations=('text',),primitives=model)


def test_initial_setting_alignment_remains_partial():
    report=alignment()
    assert report['verified_full_units']==0
    assert report['segments'][0]['unit']=='einstein-1905:u0029'
    assert len(report['segments'])==6
    assert {row['math_id'] for row in report['segments'][1:]}=={'M0043','M0044','M0045','M0046','M0047'}
    assert all(not row['full_semantic_equivalence'] for row in report['segments'])


@pytest.mark.parametrize('compose,counts',[(generic_composed,(4,26)),(source_composed,(137,72))])
def test_frozen_documents_basis_notations_and_previous_source_are_preserved(compose,counts):
    text,basis=compose()
    doc=parse(text)
    audit=audit_basis(doc,basis)
    assert (audit['primitive_count'],audit['definition_count'])==counts
    assert (ROOT/basis['document']).read_text(encoding='utf-8')==text
    for notation in ('compact','full'):
        form=format_graph(doc,notation)
        assert parse(form)==parse(decode(encode(form,'v2')))==doc
    if compose==source_composed:
        old=parse((ROOT/'examples/v014/einstein-rod-measurements.noema').read_text(encoding='utf-8'))
        assert doc['declarations'][:len(old['declarations'])]==old['declarations']
        assert doc['statements'][:-2]==old['statements']
        assert len(doc['statements'])==10
