import pytest

from noema.finite_semantics import evaluate_document
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_moving_light_trip import (
    ARITHMETIC, alignment, attribution_checks, numeric_checks, polynomial_checks, source_checks,
)
from scripts.compose_moving_light_trip import ROOT, generic_composed, source_composed


def test_moving_roundtrip_times_and_zero_speed_limit_have_distinct_midpoint_results():
    rows=numeric_checks()
    assert len(rows)==12
    assert {k for k,v in rows.items() if v['travel_relation']}=={
        'moving','fractional_times','stationary_limit','shifted_time_origin'}
    assert rows['moving']=={'travel_relation':True,'midpoint':False}
    assert rows['stationary_limit']=={'travel_relation':True,'midpoint':True}
    assert rows['wrong_midpoint_assumption']=={'travel_relation':False,'midpoint':True}


def test_intersection_model_and_time_asymmetry_are_checked_as_polynomial_claims():
    rows=polynomial_checks()
    assert len(rows)==6 and sum(r['status']=='valid' for r in rows.values())==5
    assert rows['intersection_equations_equal_travel_equations']['status']=='valid'
    assert rows['midpoint_exactly_at_zero_speed']['status']=='valid'
    assert rows['moving_clocks_always_pass_midpoint']['status']=='invalid'


def test_same_ray_events_carried_clocks_observers_and_length_setting_are_bound():
    result=source_checks();rows=result['cases']
    assert len(rows)==26 and rows['baseline']==[True,True]
    assert rows['missing_outward_leg']==rows['different_trial']==rows['wrong_criterion']==[False,True]
    assert rows['wrong_length']==rows['wrong_speed_unit']==[True,False]
    assert rows['wrong_return_reading']==rows['wrong_context']==[False,False]
    assert result['carried_clock_rest_not_required']
    assert not result['full_real_conditions_evaluated']
    assert not result['physical_worldlines_derived_from_all_source_relations']


def test_prior_clock_setting_and_light_speed_principle_are_attributed_without_execution():
    rows=attribution_checks()
    assert len(rows)==7 and rows['baseline']==[True,True]
    assert rows['wrong_previous_setting']==rows['missing_extension']==[False,True]
    assert rows['wrong_principle']==rows['wrong_conclusion']==[True,False]


def test_real_cut_flight_times_are_not_approximated_by_finite_samples():
    cut='k bb[n p b b]'
    doc=parse(generic_composed()[0]+'q[k sdb['+' '.join([cut]*6)+']].')
    with pytest.raises(ValueError,match='rational number domain'):
        evaluate_document(doc,individuals=('object',),situations=('text',),primitives=ARITHMETIC)


def test_alignment_does_not_claim_the_later_observer_judgment_or_complete_units():
    result=alignment();rows=result['segments']
    assert len(rows)==6 and result['verified_full_units']==0
    assert {r['unit'] for r in rows}=={f'einstein-1905:u{n:04d}' for n in range(36,41)}
    assert {r['math_id'] for r in rows if 'math_id' in r}=={'M0060','M0061','M0062'}
    forty=next(r for r in rows if r['unit']=='einstein-1905:u0040' and 'source' in r)
    assert forty['source'].endswith('bedeutet.') and 'Beobachter' not in forty['source']
    assert all(not r['full_semantic_equivalence'] for r in rows)


@pytest.mark.parametrize('compose,counts',[(generic_composed,(4,41)),(source_composed,(190,110))])
def test_basis_notation_roundtrips_and_prior_source_are_preserved(compose,counts):
    text,basis=compose();doc=parse(text);audit=audit_basis(doc,basis)
    assert (audit['primitive_count'],audit['definition_count'])==counts
    assert (ROOT/basis['document']).read_text(encoding='utf-8')==text
    for notation in ('compact','full'):
        form=format_graph(doc,notation)
        assert parse(form)==parse(decode(encode(form,'v2')))==doc
    if compose==source_composed:
        old=parse((ROOT/'examples/v014/einstein-carried-clocks.noema').read_text(encoding='utf-8'))
        assert doc['declarations'][:len(old['declarations'])]==old['declarations']
        assert doc['statements'][:-2]==old['statements'] and len(doc['statements'])==21
