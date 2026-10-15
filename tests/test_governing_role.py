import json
import pytest
from noema.extraction import _references
from scripts.check_governing_role import values,source_values,integration_checks,integrated_fixture,attribution,review_report,document
from scripts.compose_governing_role import ROOT,PARENT,SOURCE,CORE,BASIS,READING,REVIEW,build,basis,reading,review,parent_schema


@pytest.mark.parametrize('actor',('monarch','council'))
def test_an_individual_or_collective_actor_can_hold_the_role(actor):
    assert values(actor=actor)==[True]


@pytest.mark.parametrize('variant',('empty_roles','incomparable','cycle','reflexive','wrong_actor','lower_office',
    'other_organization','no_occupant','wrong_context','wrong_community','no_jurisdiction'))
def test_role_occupancy_order_and_community_are_distinct_conditions(variant):
    assert values(variant)==[False]


def test_single_governing_role_does_not_require_multiple_rulers():
    assert values('single_role')==[True]
    assert values('single_role',actor='council')==[True]


@pytest.mark.parametrize('variant',('unknown_occupant','unknown_jurisdiction'))
def test_unknown_institutional_relations_are_not_guessed(variant):
    with pytest.raises(ValueError,match='Unknown'):values(variant)


def test_cached_and_uncached_interpretations_agree():
    assert values(memoize=False)==values()==[True]
    assert values('incomparable',memoize=False)==values('incomparable')==[False]


@pytest.mark.parametrize('variant',('late_vacancy','late_jurisdiction_loss'))
def test_source_qualification_can_expire_before_political_endpoint(variant):
    assert source_values(variant)==[True,False]


@pytest.mark.parametrize('variant',('wrong_actor','lower_office','other_organization','wrong_community','no_jurisdiction','no_occupant'))
def test_source_uses_exact_actor_office_organization_and_community(variant):
    assert source_values(variant)==[False,False]


def test_source_keeps_organization_selection_at_the_same_anchor():
    calls=[];assert source_values(calls=calls)==[True,True]
    assert all(row[1:]==('community','end') for row in calls if row[0]=='organization')
    occupancy=[row[1:] for row in calls if row[0]=='occupants']
    assert {row[-1] for row in occupancy}=={'end','political'}
    assert all(row[:3]==('monarch','office','state') for row in occupancy)


def test_current_whole_conditional_uses_qualification_and_all_previous_layers():
    result=integration_checks()
    assert result['baseline']==dict(schema=True,premise_witness=True,appraisal=True,actual_benefit=False,
        beneficiaries=True,policy_inclusion=True,political_cause=True,current_family=True,apposition=True)
    assert all(row==[False] for row in result['contrasts'].values())
    assert {'end','political'}<=set(result['qualification_points'])


def test_integrated_fixture_preserves_all_actual_source_definitions():
    source=document(CORE);actual={d['name']:d for d in integrated_fixture()['declarations']}
    assert all(actual[d['name']]==d for d in source['declarations'])
    assert {'ibdqualified',parent_schema()}<=_references(actual['ibdschema']['body'])
    # The generic office criterion does not silently import the republic's
    # multi-person decision rule or identify an organization with a person.
    assert not {'rwp','rwn','aa'}&_references(actual['ryv'])


def test_attribution_does_not_assert_government_qualification_as_fact():
    assert attribution()==[True] and attribution(True)==[False]


def test_history_and_open_manuscript_obligations_are_preserved():
    old,new=document(PARENT),document(SOURCE)
    assert new['declarations'][:len(old['declarations'])]==old['declarations']
    assert new['statements'][:-1]==old['statements'][:-1]
    assert len(new['statements'])==22 and _references(new['statements'][-1])=={'ibdattribution'}
    packet=review_report()
    assert all(not row['unconnected_candidate_roots'] for row in packet['obligations'])
    assert packet['templates'][0]['symbol']=='ibdschema' and len(packet['templates'][0]['parameters'])==8
    assert not packet['semantic_completion'] and not packet['counts_as_translated_coverage']


def test_builder_and_interpretation_records_are_reproducible():
    files=build()
    assert all((ROOT/path).read_text(encoding='utf-8')==text for path,text in files.items())
    for path,value in ((BASIS,basis()),(READING,reading()),(REVIEW,review(files))):
        assert json.loads((ROOT/path).read_text(encoding='utf-8'))==value
