import pytest

from noema.finite_semantics import evaluate_document
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_described_appraisals import candidate
from scripts.check_frame_translation import alignment, attribution_checks, coverage_checks, source_checks
from scripts.check_rod_setup import guarded
from scripts.check_rod_measurements import ARITHMETIC, cut
from scripts.compose_frame_translation import ROOT, generic_composed, source_composed


@pytest.fixture(scope='module')
def source_result():
    return source_checks()


def test_each_object_needs_placement_and_all_selected_middle_times_are_checked():
    rows=coverage_checks()
    assert len(rows)==64
    for row in rows:
        if not any(row['selected_objects']) or not row['origin_available']:assert not row['result']
        if row['selected_objects'][1] and not row['placements'][1]:assert not row['result']
    accepted=next(r for r in rows if r['selected_objects']==[True,False] and r['placements']==[True,True]
        and r['origin_available'] and r['bad_middle_for_second_point'])
    assert accepted['result']  # Unselected object's trajectory is not constrained.


def test_one_shared_velocity_applies_to_origin_axes_ruler_and_every_clock(source_result):
    rows=source_result['cases']
    assert len(rows)==24 and rows['baseline']==[True,True]
    for name in ('origin_wrong_speed','axis_middle_deviation','ruler_transverse_motion','one_clock_wrong_speed'):
        assert rows[name]==[True,False]
    assert rows['moving_internal_clock_hand']==[True,True]
    assert source_result['placement_points_are_not_all_internal_material_points']
    assert not source_result['clock_reading_primitive_executed']


def test_the_same_initial_equipment_is_kept_without_dropping_or_adding_clocks(source_result):
    rows=source_result['cases']
    for name in ('replaced_origin','replaced_axis','replaced_ruler','dropped_clock','added_clock',
                 'missing_object_transfer','missing_frame_transfer','same_initial_context'):
        assert rows[name]==[False,False]


def test_missing_positions_empty_placements_and_time_or_unit_confusion_fail(source_result):
    rows=source_result['cases']
    for name in ('missing_origin_position','missing_clock_position','missing_time_assignment','empty_clock_placement',
                 'incomplete_domain','single_time','wrong_time_order','relative_speed_mismatch','wrong_length_unit','wrong_time_frame'):
        assert rows[name]==[True,False]
    assert not source_result['complete_continuous_time_motion_proved']
    assert not source_result['full_real_pair_condition_evaluated']


def test_actual_real_pair_condition_is_not_replaced_by_the_integer_fixture():
    doc=candidate(source_composed()[0],'''
r ja[] a.r jb[] a.r jc[] a.r jd[] d.
q[k sfk[k ja[] k jb[] k jc[] k jd[] p sbm]].''')
    model=guarded(doc);model.update(ARITHMETIC)
    constants={'ja':'point','jb':'first','jc':'last','jd':'motion','ra':'rest','rb':'timeunit','ta':'lengthunit',
        'yn':'xrole','yo':'yrole','yp':'zrole'}
    for key,val in constants.items():model[key]=lambda val=val:val
    model.update(zb7=lambda:cut(2),yl=lambda moment,*args:cut(0 if moment=='first' else 1),ym=lambda *args:cut(1))
    with pytest.raises(ValueError,match='rational number domain'):
        evaluate_document(doc,individuals=('point','first','last','rest','timeunit','lengthunit','xrole','yrole','zrole'),
            situations=('motion',),primitives=model)


def test_motion_assumption_extends_the_same_initial_setup_without_evaluating_it():
    rows=attribution_checks()
    assert len(rows)==7 and {name for name,value in rows.items() if value}=={'baseline'}


def test_alignment_excludes_the_later_symmetry_argument():
    result=alignment();row=result['segments'][0]
    assert row['unit']=='einstein-1905:u0044' and row['source'].endswith('möge.')
    assert 'Jeder Zeit' not in row['source'] and '[M0070]' not in row['source']
    assert result['later_symmetry_and_parallel_configuration_not_yet_composed']
    assert not row['full_semantic_equivalence'] and result['verified_full_units']==0


@pytest.mark.parametrize('compose,counts',[(generic_composed,(4,29)),(source_composed,(227,166))])
def test_basis_roundtrip_and_frozen_predecessor(compose,counts):
    text,basis=compose();doc=parse(text);audit=audit_basis(doc,basis)
    assert (audit['primitive_count'],audit['definition_count'])==counts
    assert (ROOT/basis['document']).read_text(encoding='utf-8')==text
    for notation in ('compact','full'):
        form=format_graph(doc,notation)
        assert parse(form)==parse(decode(encode(form,'v2')))==doc
    if compose==source_composed:
        old=parse((ROOT/'examples/v014/einstein-coordinate-frames.noema').read_text(encoding='utf-8'))
        assert doc['declarations'][:len(old['declarations'])]==old['declarations']
        assert doc['statements'][:-1]==old['statements'] and len(doc['statements'])==27
