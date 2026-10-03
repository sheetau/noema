import pytest

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_parallel_histories import (
    alignment, attribution_checks, configuration_checks, history_checks,
    snapshot_coordinate_checks, symmetry_checks, time_binding_checks, uniqueness_checks,
)
from scripts.compose_parallel_histories import ROOT, generic_composed, source_composed


@pytest.mark.parametrize('source',[False,True])
def test_one_global_history_is_stronger_than_different_witnesses_at_each_time(source):
    rows=history_checks(source)
    assert len(rows)==16
    switched=next(r for r in rows if r['parallel_at_history_times']==[True,False,False,True])
    assert switched['results']==[False,True,False]
    other=next(r for r in rows if r['parallel_at_history_times']==[False,False,True,True])
    assert other['results']==[True,True,False]


def test_missing_or_conflicting_states_fail_but_equivalent_representations_are_allowed():
    rows=uniqueness_checks()
    assert len(rows)==6 and rows['baseline']==rows['duplicate_same_pose']==[True]*3
    assert rows['missing_last']==rows['conflicting_pose']==rows['empty_times']==[False]*3
    assert rows['equivalent_pose_with_bad_property']==[False,True,False]


def test_invertible_condition_preservation_does_not_prove_a_parallel_history_exists():
    result=symmetry_checks();rows=result['cases']
    assert len(rows)==7 and {n for n,v in rows.items() if v}=={'swap_preserves','identity_preserves'}
    assert result['symmetry_without_parallel_history']=={'symmetry':True,'parallel_history_exists':False}


def test_history_and_common_time_use_the_same_stationary_frame_value():
    result=time_binding_checks();rows=result['cases']
    assert len(rows)==13 and {n for n,v in rows.items() if v}=={'baseline'}
    assert not result['full_real_equality_evaluated']


def test_pose_coordinates_cannot_be_substituted_without_matching_the_history():
    result=snapshot_coordinate_checks();rows=result['cases']
    assert len(rows)==12 and {n for n,v in rows.items() if v}=={'baseline','clock_only_difference'}
    assert not result['full_real_coordinate_equality_evaluated']


def test_all_three_parallel_axes_keep_their_original_objects_and_roles():
    rows=configuration_checks()
    assert len(rows)==12 and {n for n,v in rows.items() if v}=={'baseline'}


def test_definite_poses_adopted_choice_and_symmetry_reason_are_separate_attributions():
    rows=attribution_checks()
    assert len(rows)==10 and rows['baseline']==[True]*3
    assert rows['wrong_definite_content']==[False,True,True]
    assert rows['wrong_choice']==rows['wrong_prior_motion']==[True,False,True]
    assert rows['wrong_symmetry']==rows['wrong_assumption_target']==[True,True,False]


def test_partial_alignment_discloses_the_unspecified_symmetry_transformation():
    result=alignment();row=result['segments'][0]
    assert row['unit']=='einstein-1905:u0044' and row['start']>0
    assert row['source'].startswith('Jeder Zeit') and 'Symmetriegründen' in row['source']
    assert result['specific_source_symmetry_transformation_not_identified']
    assert not result['facsimile_checked'] and not row['full_semantic_equivalence']
    assert result['verified_full_units']==0


@pytest.mark.parametrize('compose,counts',[(generic_composed,(0,5)),(source_composed,(240,183))])
def test_basis_roundtrip_and_frozen_predecessor(compose,counts):
    text,basis=compose();doc=parse(text);audit=audit_basis(doc,basis)
    assert (audit['primitive_count'],audit['definition_count'])==counts
    assert (ROOT/basis['document']).read_text(encoding='utf-8')==text
    for notation in ('compact','full'):
        form=format_graph(doc,notation)
        assert parse(form)==parse(decode(encode(form,'v2')))==doc
    if compose==source_composed:
        old=parse((ROOT/'examples/v014/einstein-frame-translation.noema').read_text(encoding='utf-8'))
        assert doc['declarations'][:len(old['declarations'])]==old['declarations']
        assert doc['statements'][:-3]==old['statements'] and len(doc['statements'])==30
