import json
import pytest
from noema.extraction import _references
from scripts.check_institutional_appraisal import values,source_values,source_fixture,integration_checks,attribution,review_report,document
from scripts.compose_institutional_appraisal import ROOT,PARENT,SOURCE,CORE,BASIS,REVIEW,build,basis,review,manuscript


@pytest.mark.parametrize('rule',('anyrule','allrule','lastrule'))
@pytest.mark.parametrize('bits',range(4))
def test_explicit_noema_procedures_can_make_different_institutional_choices(rule,bits):
    expected={'anyrule':bits!=0,'allrule':bits==3,'lastrule':bool(bits&2)}[rule]
    assert values(rule=rule,bits=bits)==[expected]


@pytest.mark.parametrize('variant',('empty','omitted','duplicate','nonperson','unassessed','no_constitution',
    'wrong_assessor','wrong_actor','wrong_beneficiary','wrong_policy','wrong_recipe','wrong_context','wrong_rule','reversed'))
def test_procedural_result_alone_does_not_constitute_organizational_acceptance(variant):
    assert values(variant,bits=3)==[False]


def test_an_institution_may_use_a_single_designated_person():
    assert values('single_person',bits=1,rule='allrule')==[True]
    assert values('single_person',bits=0,rule='anyrule')==[False]


def test_position_sensitive_rules_keep_the_ordered_roster():
    assert values(bits=1,rule='lastrule')==[False]
    assert values('reordered',bits=1,rule='lastrule')==[True]
    assert values(bits=1)==values('reordered',bits=1)==[True]


def test_memoization_preserves_procedural_acceptance():
    assert values(memoize=False)==values()==[True]
    assert values(bits=1,rule='allrule',memoize=False)==[False]


def test_institutional_appraisal_remains_nonfactive_without_private_awareness():
    # Private awareness is a forbidden callback in this interpretation.
    assert source_values()==[True,False]
    assert source_values(bits=0)==[False,False]
    assert source_values(bits=1,rule='allrule')==[False,False]
    assert source_values(bits=3,rule='allrule')==[True,False]


@pytest.mark.parametrize('variant',('empty','omitted','duplicate','unassessed','nonperson','no_constitution',
    'wrong_assessor','wrong_actor','wrong_beneficiary','wrong_policy','wrong_recipe','wrong_context','wrong_rule',
    'no_collective','ambiguous_kind'))
def test_actual_appraisal_requires_the_same_scoped_constitution_and_inputs(variant):
    assert source_values(variant,indices=(2,))==[False]


def test_individual_judgment_uses_the_personal_branch_without_institutional_inputs():
    assert source_values('individual')==[True,False]
    assert source_values('individual_unrecognized')==[False,False]


def test_all_inputs_are_assessed_before_any_decision_is_computed():
    calls=[];assert source_values('unassessed',indices=(2,),calls=calls)==[False]
    assert not any(row[0]=='decides' for row in calls)
    assert source_values('no_benefit',indices=(2,))==[False]


@pytest.mark.parametrize('variant',('unknown_input','unknown_constitution','unknown_rule'))
def test_unknown_procedural_relations_are_not_guessed(variant):
    with pytest.raises(ValueError,match='Unknown'):source_values(variant,indices=(2,))


def test_current_whole_conditional_uses_procedural_appraisal_and_governing_role():
    result=integration_checks()
    assert result['baseline']['schema'] and result['baseline']['appraisal']
    assert not result['baseline']['actual_benefit']
    assert all(result['contrasts'][name]==[False] for name in ('no_constitution','late_vacancy'))
    assert not result['private_awareness_executed']


def test_all_source_definitions_are_preserved_in_the_integrated_fixture():
    actual={d['name']:d for d in source_fixture()['declarations']}
    assert all(actual[d['name']]==d for d in document(CORE)['declarations'])
    assert {'rya','ibeawareness','iatbenefit'}<=_references(actual['ibeappraisal'])


def test_attribution_does_not_execute_institutional_adoption_or_its_content():
    assert attribution()==[True] and attribution(True)==[False]


def test_historical_statements_and_open_review_are_preserved():
    old,new=document(PARENT),document(SOURCE);_,mapping=manuscript()
    assert new['declarations'][:len(old['declarations'])]==old['declarations']
    assert new['statements'][:-1]==old['statements'][:-1]
    assert len(new['statements'])==22 and _references(new['statements'][-1])=={'ibeattribution'}
    assert mapping['ibdschema']=='ibeschema'
    packet=review_report()
    assert all(not row['unconnected_candidate_roots'] for row in packet['obligations'])
    assert len(packet['templates'][0]['parameters'])==8
    assert not packet['semantic_completion'] and not packet['counts_as_translated_coverage']


def test_reproducible_documents_and_meaning_basis():
    files=build()
    assert all((ROOT/path).read_text(encoding='utf-8')==text for path,text in files.items())
    for path,value in ((BASIS,basis()),(REVIEW,review(files))):
        assert json.loads((ROOT/path).read_text(encoding='utf-8'))==value
