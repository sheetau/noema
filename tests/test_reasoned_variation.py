from itertools import product
import json
import pytest
from scripts.check_reasoned_variation import values,source_values,wrapper_values,attribution,review_report,document
from scripts.compose_reasoned_variation import ROOT,PARENT,SOURCE,BASIS,READING,REVIEW,build,basis,reading,review
from noema.extraction import _references


@pytest.mark.parametrize('command,choice,reasons',list(product((False,True),repeat=3)))
def test_response_patterns_are_not_a_numeric_ranking(command,choice,reasons):
    assert values(same_command=command,same_choice=choice,same_reasons=reasons)==[True,not command or choice,command and not choice and not reasons]


@pytest.mark.parametrize('left,right',list(product((False,True),repeat=2)))
def test_both_responses_must_be_independently_reasoned(left,right):
    assert values(independent=(left,right))==[True,False,left and right]


@pytest.mark.parametrize('variant',('empty','unassessed'))
def test_missing_comparison_evidence_is_not_a_directive_only_profile(variant):
    assert values(variant=variant)==[False,False,False]


def test_unknown_comparison_refused_and_uncached_interpretation_agrees():
    with pytest.raises(ValueError,match='Unknown'):values(variant='unknown')
    assert values(memoize=False)==values()==[True,False,True]


def test_two_profiles_are_not_exhaustive_opposites():
    # Variation without a change in used reasons is neither of these profiles.
    assert values(same_reasons=True)==[True,False,False]
    # A reasoned person may show a fixed choice across these particular cases.
    assert values(same_choice=True)==[True,True,False]


@pytest.mark.parametrize('variant',('other_faculty_owner','other_judge','other_topic','unsupported','guided','unlinked_choice','same_reasons','nonhuman'))
def test_source_requires_same_person_topic_reason_support_and_choice_link(variant):
    assert source_values(variant=variant)==[False,False,False,False,False]


@pytest.mark.parametrize('variant',('same_choice','different_command'))
def test_source_does_not_count_instruction_changes_or_fixed_choices_as_beyond_profile(variant):
    assert source_values(variant=variant)==[True,False,False,False,False]


@pytest.mark.parametrize('variant',('early','unassessed'))
def test_source_keeps_current_evaluation_anchor_and_assessment(variant):
    assert source_values(variant=variant)==[False,False,False,False,False]


@pytest.mark.parametrize('variant',('other_policy','other_government','duplicate'))
def test_beneficiaries_are_bound_to_this_policy_and_government(variant):
    assert source_values(variant=variant)==[False,True,True,False,False]


def test_counterfactual_reasoned_choices_do_not_require_judging_at_actual_evaluation_point():
    assert source_values()==[False,True,True,True,False]


def test_new_consequent_is_composed_through_parent_interface_and_preserves_remaining():
    assert wrapper_values()==[True]
    assert wrapper_values(remaining=False)==[False]
    for variant in ('guided','other_policy','other_government'):
        assert wrapper_values(variant=variant)==[False]


@pytest.mark.parametrize('variant,expected',[('baseline',True),('old',False),('author',False)])
def test_attribution_keeps_identity_and_does_not_execute_reasoning(variant,expected):
    assert attribution(variant)==[expected]


def test_actual_manuscript_and_open_review_include_the_contrast():
    old,new=document(PARENT),document(SOURCE)
    assert new['declarations'][:len(old['declarations'])]==old['declarations']
    assert new['statements'][:-1]==old['statements'][:-1]
    assert len(new['statements'])==len(old['statements'])==22
    assert _references(new['statements'][-1])=={'iaxattribution'}
    packet=review_report();rows={r['id']:r for r in packet['obligations']}
    assert rows['more_than_machine']['unconnected_candidate_roots']==[]
    assert rows['tender_care']['unconnected_candidate_roots']==[]
    assert rows['dignified_treatment']['unconnected_candidate_roots']==['iaustanding','iautreatment','iavclaim','iavtreatment']
    assert packet['templates'][0]['symbol']=='iaxschema'
    assert len(packet['templates'][0]['parameters'])==8
    assert not packet['semantic_completion'] and not packet['counts_as_translated_coverage']


def test_reproducible_definitions_conventions_and_review():
    files=build()
    assert all((ROOT/path).read_text(encoding='utf-8')==text for path,text in files.items())
    assert json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis()
    assert json.loads((ROOT/READING).read_text(encoding='utf-8'))==reading()
    assert json.loads((ROOT/REVIEW).read_text(encoding='utf-8'))==review(files)
