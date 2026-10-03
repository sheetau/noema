import pytest

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_origin_clock import (
    alignment, answer_checks, attribution_checks, frame_checks,
    placement_checks, polynomial_checks,
)
from scripts.compose_origin_clock import ROOT, generic_composed, source_composed


def test_origin_time_and_rate_require_calibration_and_nonzero_duration():
    result=polynomial_checks();rows=result['claims']
    assert len(rows)==12
    assert {n for n,r in rows.items() if r['status']=='invalid'}=={
        'one_zero_event_identifies_rate','different_dial_offsets_cancel',
        'changing_dial_scale_preserves_rate','origin_rate_is_beta_instead_of_its_inverse'}
    assert result['signed_coordinate_time_not_elapsed_duration']


def test_capability_actual_placement_and_equations_are_distinct():
    result=placement_checks();rows=result['cases']
    assert len(rows)==23
    for name in ('baseline','stationary','negative_velocity','negative_times'):
        assert rows[name]==[True]*5
    for name in ('rest_setup_unavailable','moving_setup_unavailable'):
        assert rows[name]==[False,True,False,True,True]
    for name in ('not_stationary','incomplete_records','missing_observer_chart',
                 'wrong_origin','wrong_clock_place','missing_reading','replaced_clock','wrong_unit','dial_offset'):
        assert rows[name]==[True,False,False,True,True]
    assert rows['off_origin']==rows['wrong_candidate_record']==[True,False,False,False,False]
    assert rows['wrong_position']==[True,True,True,False,True]
    assert rows['nonlinear_clock']==rows['different_linear_rate']==[True,True,True,False,False]
    assert result['complete_reading_scope_and_physical_charts_are_oracles']


def test_typed_question_accepts_rate_from_readings_without_inserting_formula():
    result=answer_checks();rows=result['cases']
    assert len(rows)==13
    assert {n for n,r in rows.items() if r['accepted']==[True,True]}=={
        'baseline','stationary','negative_velocity','negative_times',
        'rest_setup_unavailable','different_linear_rate'}
    assert rows['different_linear_rate']['rate']=='1/2'
    assert result['positive_time_width_required']


def test_alternative_calibration_does_not_make_actual_clock_rest_in_both_frames():
    assert frame_checks()=={'baseline':[True,True,False],'collapsed_frames':[False,False,True]}


def test_question_setup_equations_and_derivation_are_separate_attributions():
    rows=attribution_checks()
    assert len(rows)==9 and rows['baseline']==[True]*5
    assert rows['wrong_author']==rows['wrong_scope']==rows['wrong_context']==[False]*5
    assert rows['wrong_question']==[True,False,True,True,True]
    assert rows['wrong_equations']==[True,True,False,True,True]
    assert rows['wrong_derived']==[True]*4+[False]


def test_alignment_keeps_later_delay_and_approximation_unfinished():
    result=alignment();rows=result['segments']
    assert {r['unit'] for r in rows}=={f'einstein-1905:u{i:04}' for i in range(118,125)}
    assert {r['math_id'] for r in rows if 'math_id' in r}=={f'M{i:04}' for i in range(207,217)}
    assert result['per_unit_delay_and_approximation_not_yet_connected']
    assert result['verified_full_units']==0 and not result['facsimile_checked']


def test_rate_question_has_no_dependency_on_transform_or_light_speed():
    text,basis=source_composed();audit=audit_basis(parse(text),basis)
    deps=audit['definition_dependencies']['definition_primitive_dependencies']['svd']
    assert 'tc' not in deps and 'zb7' not in deps and 'ce' in deps


@pytest.mark.parametrize('compose,counts',[(generic_composed,(4,51)),(source_composed,(410,572))])
def test_basis_roundtrip_and_frozen_parent(compose,counts):
    text,basis=compose();doc=parse(text);audit=audit_basis(doc,basis)
    assert (audit['primitive_count'],audit['definition_count'])==counts
    assert (ROOT/basis['document']).read_text(encoding='utf-8')==text
    for notation in ('compact','full'):
        form=format_graph(doc,notation)
        assert parse(form)==parse(decode(encode(form,'v2')))==doc
    if compose==source_composed:
        parent=parse((ROOT/'examples/v014/einstein-shape-contraction.noema').read_text(encoding='utf-8'))
        assert doc['declarations'][:len(parent['declarations'])]==parent['declarations']
        assert doc['statements'][:-5]==parent['statements'] and len(doc['statements'])==112
