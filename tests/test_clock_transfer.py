import pytest

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_clock_transfer import (
    alignment, attribution_checks, gap_checks, infinite_conditions_refused,
    physical_checks, polynomial_checks,
)
from scripts.compose_clock_transfer import ROOT, generic_composed, source_composed


def test_initial_offset_and_interval_laws_determine_arrival_difference():
    result=polynomial_checks();rows=result['claims']
    assert len(rows)==8
    assert {n for n,r in rows.items() if r['status']=='invalid'}=={
        'unequal_start_readings_can_be_ignored',
        'matching_endpoints_proves_linear_midpoint','zero_duration_shows_positive_lag'}
    assert result['interval_clock_laws_are_explicit_premises']


def test_three_events_physical_motion_and_dial_laws_remain_distinct():
    result=physical_checks();rows=result['cases']
    assert len(rows)==26
    for name in ('baseline','negative_times','common_dial_offset','diagonal','backward'):
        assert rows[name]==[True]*5
    for name in ('no_initial_sync','not_simultaneous','same_clock','same_place',
                 'collapsed_contexts','reference_wrong_place','departure_not_preserved'):
        assert not rows[name][0] and not rows[name][3]
    for name in ('detour','nonuniform_progress'):
        assert rows[name]==[True,True,False,True,True]
    for name in ('reset_during_trip','reference_wrong_rate'):
        assert rows[name]==[True,True,True,False,False]
    assert rows['missing_middle']==[True]*5
    assert result['full_time_coverage_not_certified_by_samples']


def test_arrival_gap_seconds_approximation_and_error_are_not_interchanged():
    result=gap_checks();rows=result['cases']
    assert len(rows)==8 and rows['baseline']==[True]*3
    assert result['baseline_seconds']=={
        'duration':'10','exact_gap':'2','approximation':'9/5','error':'1/5'}
    for name in ('wrong_gap','exact_as_approximation','wrong_duration'):
        assert rows[name]==[False,True,True]
    assert rows['wrong_conversion']==[False,True,False]
    assert rows['unsynchronized_start']==[False]*3


def test_full_trajectory_and_asymptotic_condition_refuse_finite_sampling():
    rows=infinite_conditions_refused()
    assert set(rows)=={'trajectory','asymptotic_duration'}
    assert all('rational number domain' in message for message in rows.values())


def test_added_clock_law_is_not_attributed_as_original_setup():
    rows=attribution_checks()
    assert len(rows)==7 and rows['baseline']==[True]*3
    assert rows['wrong_author']==rows['wrong_scope']==rows['wrong_context']==[False]*3
    assert rows['wrong_setup']==[False,True,True]
    assert rows['wrong_idealization']==[True,False,True]
    assert rows['wrong_conclusion']==[True,True,False]


def test_source_alignment_retains_unfinished_meaning_review():
    result=alignment();rows=result['segments']
    assert {r['unit'] for r in rows}=={'einstein-1905:u0126'}
    assert {r['math_id'] for r in rows if 'math_id' in r}=={
        'M'+str(n).zfill(4) for n in range(219,233)}
    assert result['acceleration_response_not_derived']
    assert result['distinctive_consequence_appraisal_unwritten']
    assert result['verified_full_units']==0 and not result['facsimile_checked']


@pytest.mark.parametrize('compose,counts',[(generic_composed,(4,54)),(source_composed,(433,610))])
def test_basis_roundtrip_and_frozen_parent(compose,counts):
    text,basis=compose();doc=parse(text);audit=audit_basis(doc,basis)
    assert (audit['primitive_count'],audit['definition_count'])==counts
    assert (ROOT/basis['document']).read_text(encoding='utf-8')==text
    for notation in ('compact','full'):
        form=format_graph(doc,notation)
        assert parse(form)==parse(decode(encode(form,'v2')))==doc
    if compose==source_composed:
        parent=parse((ROOT/'examples/v014/einstein-clock-delay.noema').read_text(encoding='utf-8'))
        assert doc['declarations'][:len(parent['declarations'])]==parent['declarations']
        assert doc['statements'][:-3]==parent['statements'] and len(doc['statements'])==118
