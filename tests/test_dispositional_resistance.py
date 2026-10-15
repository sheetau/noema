from fractions import Fraction as F
from itertools import product
import json
import pytest
from noema.extraction import _references
from scripts.check_dispositional_resistance import values,source_values,attribution,review_report,document,CANDIDATES
from scripts.compose_dispositional_resistance import ROOT,PARENT,SOURCE,BASIS,REVIEW,build,basis,review,manuscript


def test_untested_object_can_have_disposition_without_actual_loading():
    assert values()==[False,True]
    assert values(actual_loaded=True)==[True,True]
    calls=[]
    assert values(indices=(1,),calls=calls)==[True]
    assert calls and {r[-1] for r in calls}=={'nowresponseone','nowresponsetwo'}


@pytest.mark.parametrize('variant',('no_candidates','missing_test_candidates','bad_candidate'))
def test_actual_success_does_not_supply_missing_or_bad_counterfactual_responses(variant):
    assert values(variant=variant,actual_loaded=True)==[True,False]


@pytest.mark.parametrize('load,deformation',list(product((0,9,10,11),(F(-1,10),0,F(1,10),F(1,5)))))
def test_all_candidate_responses_must_meet_the_existing_protocol(load,deformation):
    assert values(loads=(load,load),deformations=(deformation,deformation))==[False,load>=10 and 0<=deformation<=F(1,10)]


@pytest.mark.parametrize('variant',('empty','omitted','duplicate','unassessed','wrong_object','wrong_test',
    'wrong_protocol','wrong_loadunit','wrong_deformationunit','wrong_anchor'))
def test_candidate_relation_keeps_exact_test_identity_and_metadata(variant):
    assert values(variant=variant)==[False,False]


@pytest.mark.parametrize('minimum,maximum',[(0,F(1,10)),(-1,F(1,10)),(10,F(-1,10))])
def test_bounds_remain_valid_inside_hypothetical_situations(minimum,maximum):
    assert values(minimum=minimum,maximum=maximum)==[False,False]


def test_each_unit_can_be_rescaled_with_its_corresponding_bound():
    assert values(force_scale=1000,deformation_scale=F(1,100))==[False,True]
    assert values(deformations=(0,0),maximum=0)==[False,True]
    assert values(loads=(0,0),deformations=(0,0),maximum=0)==[False,False]


@pytest.mark.parametrize('variant',('unknown_prospects','unknown_assessment','unknown_load','unknown_deformation'))
def test_unknown_response_inputs_are_not_guessed(variant):
    with pytest.raises(ValueError,match='Unknown'):values(variant=variant,indices=(1,))


def test_memoization_does_not_change_the_disposition_result():
    assert values(memoize=False)==values()==[False,True]
    assert values(variant='bad_candidate',memoize=False)==values(variant='bad_candidate')==[False,False]


def test_actual_source_depiction_accepts_untested_cover_at_every_stage():
    assert source_values()==[False,True,True]
    calls=[];assert source_values(indices=(1,),calls=calls)==[True]
    assert {r[-1] for r in calls}==set(CANDIDATES)-{'nowresponseone','nowresponsetwo'}
    assert all(r[0]=='cover' and r[2:5]==('protocol','forceunit','lengthunit') for r in calls)


def test_interior_candidate_failure_is_not_hidden_by_good_endpoints():
    assert source_values('middle_failure')==[False,False,True]
    assert source_values('bad_candidate',actual_loaded=True)==[True,False,True]


@pytest.mark.parametrize('variant',('no_candidates','missing_test_candidates','wrong_object','wrong_test',
    'wrong_protocol','wrong_loadunit','wrong_deformationunit','wrong_anchor','unassessed'))
def test_current_source_uses_candidate_conditions_for_the_same_cover(variant):
    assert source_values(variant)==[False,False,True]


def test_cover_identity_and_apposition_survive_the_relocation():
    assert source_values('split_cover')==[False,False,True]
    assert source_values('switched_cover')==[False,False,True]
    assert source_values('legacy_false')==[False,True,True]
    assert source_values('no_apposition')==[False,True,False]


def test_quoted_family_and_attribution_do_not_execute_response_conditions():
    for variant in ('unknown_prospects','unknown_assessment','unknown_load','unknown_deformation'):
        assert source_values(variant,indices=(2,))==[True]
    assert source_values('old_depiction',indices=(2,))==[False]
    assert attribution()==[True] and attribution(True)==[False]


def test_updated_manuscript_preserves_old_definitions_and_open_obligations():
    old,new=document(PARENT),document(SOURCE);_,mapping=manuscript()
    assert new['declarations'][:len(old['declarations'])]==old['declarations']
    assert new['statements'][:-1]==old['statements'][:-1]
    assert len(new['statements'])==22
    assert _references(new['statements'][-1])=={mapping[old['statements'][-1]['body']['symbol']]}
    packet=review_report()
    assert all(not row['unconnected_candidate_roots'] for row in packet['obligations'])
    assert len(packet['templates'][0]['parameters'])==8
    assert not packet['semantic_completion'] and not packet['counts_as_translated_coverage']


def test_text_basis_and_review_are_reproducible():
    files=build()
    assert all((ROOT/path).read_text(encoding='utf-8')==text for path,text in files.items())
    for path,value in ((BASIS,basis()),(REVIEW,review(files))):
        assert json.loads((ROOT/path).read_text(encoding='utf-8'))==value
