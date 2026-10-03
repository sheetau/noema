import pytest

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_axial_clock_trip import (
    alignment, attribution_checks, midpoint_checks, polynomial_checks, source_checks, synchronization_checks,
)
from scripts.compose_axial_clock_trip import ROOT, generic_composed, source_composed


def test_midpoint_has_equal_differences_but_does_not_imply_time_order():
    result=polynomial_checks();claims=result['claims']
    assert len(claims)==5
    assert claims['mean_iff_equal_differences']['status']=='valid'
    assert claims['mean_iff_doubled_middle']['status']=='valid'
    assert claims['common_nonzero_affine_clock_change']['status']=='valid'
    assert claims['midpoint_alone_implies_order']['status']=='invalid'
    assert claims['changing_only_reflection_clock_preserves_midpoint']['status']=='invalid'
    assert not result['general_real_cut_equivalence_proved']


def test_cut_midpoint_keeps_clock_origin_and_distinguishes_rest_time():
    result=midpoint_checks();rows=result['cases']
    assert len(rows)==7 and rows['ordinary']==rows['shifted_origin']==[True,True]
    assert rows['rest_times_are_not_moving_readings']==[False,False]
    assert rows['invalid_middle']==[False,False]
    assert rows['reversed_still_satisfies_equation']==rows['coincident_still_satisfies_equation']==[True,True]
    assert result['integer_embedding_operations_are_oracles']


def test_trial_preserves_ray_events_clocks_axis_frame_units_and_auxiliary_labels():
    result=source_checks();rows=result['cases']
    assert len(rows)==36
    assert {name for name,value in rows.items() if value}=={'baseline','negative_axial_label'}
    assert not rows['different_return_ray'] and not rows['wrong_return_clock']
    assert not rows['rest_time_substituted'] and not rows['xi_substituted']
    assert result['clock_synchrony_local_time_and_rest_chart_are_oracles']
    assert not result['general_physical_derivation_proved']


def test_synchronization_checks_the_whole_stated_trial_scope():
    result=synchronization_checks();rows=result['cases']
    assert len(rows)==7 and rows['baseline']==[True]*3
    assert rows['other_midpoint_fails']==[False,True,True]
    assert rows['selected_trial_outside_scope']==[True,False,False]
    assert rows['scope_not_complete']==[False,True,True]
    assert rows['empty_scope']==[False,False,True]
    assert result['single_passing_trial_does_not_establish_synchrony']


def test_assumed_trial_and_author_inference_do_not_execute_their_content():
    rows=attribution_checks()
    assert len(rows)==7 and rows['baseline']==[True,True]
    assert rows['wrong_assumption']==[False,True]
    assert rows['wrong_premise']==rows['wrong_conclusion']==[True,False]


def test_text_and_equation_alignment_do_not_claim_full_equivalence():
    result=alignment();rows=result['segments']
    assert {row['unit'] for row in rows}=={'einstein-1905:u0049','einstein-1905:u0050'}
    assert {row['math_id'] for row in rows if 'math_id' in row}=={f'M{i:04}' for i in range(92,99)}
    assert not any(row['full_semantic_equivalence'] for row in rows)
    assert result['verified_full_units']==0 and not result['facsimile_checked']


@pytest.mark.parametrize('compose,counts',[(generic_composed,(4,2)),(source_composed,(275,255))])
def test_basis_roundtrip_and_frozen_predecessor(compose,counts):
    text,basis=compose();doc=parse(text);audit=audit_basis(doc,basis)
    assert (audit['primitive_count'],audit['definition_count'])==counts
    assert (ROOT/basis['document']).read_text(encoding='utf-8')==text
    for notation in ('compact','full'):
        form=format_graph(doc,notation)
        assert parse(form)==parse(decode(encode(form,'v2')))==doc
    if compose==source_composed:
        old=parse((ROOT/'examples/v014/einstein-comoving-labels.noema').read_text(encoding='utf-8'))
        assert doc['declarations'][:len(old['declarations'])]==old['declarations']
        assert doc['statements'][:-2]==old['statements'] and len(doc['statements'])==42
