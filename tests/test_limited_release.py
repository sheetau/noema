import hashlib
import json
import pytest
from noema.grammar import parse
from scripts.check_limited_release import ROOT,REPORT,PARENT,setup,generic_model,source_model,values
from scripts.check_rod_setup import guarded


def data(source=False):
    stem='limited-release-core' if source else 'limited-release'
    return setup((ROOT/('examples/v014/'+stem+'.noema')).read_text(encoding='utf-8'),source)


def only(item,indices):
    item['document']['statements']=[item['document']['statements'][i] for i in indices]
    return item


def test_at_least_the_selected_source_does_not_mean_only_that_source():
    item=data()
    assert values(item,generic_model(item,(True,False,True,True,True,True)))==[True,True,True]


def test_other_sources_may_still_fail_when_the_minimum_holds():
    item=data()
    assert values(item,generic_model(item,(True,False,True,True,True,False)))==[True,True,False]


def test_success_at_another_source_does_not_replace_the_selected_one():
    item=data()
    assert values(item,generic_model(item,(True,False,True,True,False,True)))==[True,False,False]


def test_empty_minimum_is_not_an_asserted_lower_bound():
    item=data()
    assert values(item,generic_model(item,(False,False,True,True,True,True)))==[False,False,True]


def test_the_minimum_must_belong_to_the_stated_comparison_range():
    item=data()
    assert values(item,generic_model(item,(True,False,False,True,True,True)))==[False,False,True]


def test_all_selected_sources_must_satisfy_the_condition():
    item=data()
    assert values(item,generic_model(item,(True,True,True,True,True,False)))==[True,False,False]


def test_changing_the_selected_source_changes_the_limited_claim():
    item=data()
    assert values(item,generic_model(item,(True,False,True,True,True,False)))[1] is True
    assert values(item,generic_model(item,(False,True,True,True,True,False)))[1] is False


def test_scoped_release_is_not_total_release_in_the_source_example():
    item=data(True)
    assert values(item,source_model(item))==[True,False,False,True,True,True]


def test_permission_to_act_alone_is_not_both_directions_of_choice():
    item=only(data(True),(0,1,2))
    assert values(item,source_model(item,(True,False,True,True)))==[False,False,True]


def test_the_same_people_and_activities_remain_bound_across_sources():
    item=only(data(True),(0,1,2))
    assert values(item,source_model(item,(True,)*4,'private_wrong_activity'))==[True,False,False]


def test_limited_state_does_not_invent_a_release_action_or_first_achiever():
    item=data(True)
    assert values(item,source_model(item,(True,)*4,'no_cause'))==[True,True,True,False,False,True]


def test_release_does_not_establish_first_priority_without_history_assessment():
    item=data(True)
    assert values(item,source_model(item,(True,)*4,'unassessed'))==[True,True,True,True,False,True]


def test_the_limited_goal_is_quotable_without_executing_the_norms():
    item=only(data(True),(5,))
    assert item['disquotations_removed']==1
    assert values(item,guarded(item['document']))==[True]


def test_scope_semantics_does_not_hide_the_eager_evaluators_input_requirement():
    item=only(data(),(1,));model=generic_model(item);original=model['jpcondition']
    def unknown(source,subject):
        if source=='private':raise ValueError('Unknown other-source condition')
        return original(source,subject)
    model['jpcondition']=unknown
    with pytest.raises(ValueError,match='Unknown other-source condition'):values(item,model)


def test_normative_scope_does_not_require_capability_or_causal_primitives():
    item=only(data(True),(0,));model=source_model(item);limited=guarded(item['document'])
    for name in ('jogovernor','jpbroader','jomembers','joroles','jotopic','joview','joactivities','joevaluated','aa','h7a','h7b','jpsubject','jpcontext'):
        limited[name]=model[name]
    assert values(item,limited)==[True]


def test_saved_evidence_preserves_history_and_limits_source_alignment():
    report=json.loads(REPORT.read_text(encoding='utf-8'))
    for name,digest in report['source_sha256'].items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    child=parse((ROOT/'examples/v014/kant-limited-release.noema').read_text(encoding='utf-8'))
    assert child['declarations'][:len(parent['declarations'])]==parent['declarations']
    assert len(child['declarations'])==len(parent['declarations'])+4
    assert child['statements']==parent['statements']
    assert report['new_definitions']==4 and report['new_primitives']==report['new_author_statements']==0
    assert not report['alignment']['semantic_completion']
    assert report['verified_full_units']=={'kant-1784':0,'einstein-1905':0}
    segment=report['alignment']['segments'][0]
    unit=next(u for u in json.loads((ROOT/'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id']==segment['unit'])
    start,end=segment['range']
    assert 0<=start<end<=len(unit['text'])
    assert unit['text'][start:end]==segment['text']


def test_another_sources_explicit_requirement_does_not_change_government_freedom():
    item=data(True)
    assert values(item,source_model(item,(True,)*4,'private_requirement'))==[True,False,False,True,True,True]
