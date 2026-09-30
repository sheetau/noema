import pytest

from noema.finite_semantics import evaluate_document
from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_emitted_light import (
    ARITHMETIC, alignment, attribution_checks, motion_checks, numeric_checks,
    polynomial_checks, source_checks,
)
from scripts.compose_emitted_light import ROOT, generic_composed, source_composed


def test_emission_requires_the_same_body_event_frame_and_one_motion_class():
    rows=motion_checks()
    assert len(rows)==16 and sum(row['accepted'] for row in rows)==2
    assert all(not row['accepted'] for row in rows if row['resting']==row['moving'])


def test_one_way_path_is_not_doubled_or_given_the_source_speed():
    rows=numeric_checks()
    assert len(rows)==12 and sum(rows.values())==5
    assert not rows['unnecessary_roundtrip_factor']
    assert not rows['source_speed_added']


def test_unit_changes_and_the_relation_to_roundtrip_distance():
    rows=polynomial_checks()
    assert len(rows)==7
    assert rows['source_speed_can_be_added']['status']=='invalid'
    assert all(row['status']=='valid' for name,row in rows.items() if name!='source_speed_can_be_added')


def test_moving_emitter_and_moving_local_clock_have_different_roles():
    report=source_checks()
    rows=report['cases']
    assert len(rows)==28
    assert [name for name,accepted in rows.items() if accepted]==[
        'both_emitter_states_and_subsegment','only_emitter_motion_class_changes','no_claim_that_both_emitter_states_exist']
    assert not rows['moving_measurement_clock']
    assert not rows['whole_path_agrees_but_subsegment_disagrees']
    assert not rows['unknown_motion']
    assert not report['full_real_cut_physics_evaluated']


def test_both_principles_are_adopted_in_the_same_following_reasoning_scope():
    rows=attribution_checks()
    assert len(rows)==7 and rows['baseline']==[True,True]
    assert rows['wrong_definition']==[False,True]
    assert rows['missing_first_principle']==rows['missing_second_principle']==[True,False]
    assert rows['wrong_following_scope']==[True,False]


def test_source_alignment_remains_partial_and_separates_prose_from_math():
    result=alignment()
    assert result['verified_full_units']==0
    assert len(result['segments'])==6
    assert {row['unit'] for row in result['segments']}=={f'einstein-1905:u{i:04d}' for i in (24,26,27,28)}
    assert {row['math_id'] for row in result['segments'] if 'math_id' in row}=={'M0041','M0042'}
    assert all(not row['full_semantic_equivalence'] for row in result['segments'])


def test_real_cut_rate_is_not_replaced_with_finite_rational_samples():
    doc=parse(generic_composed()[0]+'q[k sax[k bb[n p g b] k bb[n p a b] k bb[n p c b] k bb[n p d b]]].')
    with pytest.raises(ValueError,match='rational number domain'):
        evaluate_document(doc,individuals=('object',),situations=('text',),primitives=ARITHMETIC,memoize_expressions=True)


@pytest.mark.parametrize('compose,counts',[(generic_composed,(4,19)),(source_composed,(87,53))])
def test_basis_roundtrips_and_both_prior_principles_are_preserved(compose,counts):
    text,basis=compose()
    doc=parse(text)
    audit=audit_basis(doc,basis)
    assert (audit['primitive_count'],audit['definition_count'])==counts
    assert (ROOT/basis['document']).read_text(encoding='utf-8')==text
    for notation in ('compact','full'):
        form=format_graph(doc,notation)
        assert parse(form)==parse(decode(encode(form,'v2')))==doc
    if compose==source_composed:
        old=parse((ROOT/'examples/v014/einstein-law-invariance.noema').read_text(encoding='utf-8'))
        assert doc['declarations'][:len(old['declarations'])]==old['declarations']
        assert doc['statements'][:-2]==old['statements']
        assert len(doc['statements'])==6
