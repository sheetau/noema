import hashlib
import json
import pytest
from noema.grammar import parse,format_graph
from scripts.check_first_achievers import ROOT,REPORT,PARENT,setup,generic_model,source_model,values
from scripts.check_rod_setup import guarded


def data(source=False):
    stem='first-achievers-core' if source else 'first-achievers'
    return setup((ROOT/('examples/v014/'+stem+'.noema')).read_text(encoding='utf-8'),source)


def only(item,indices):
    item['document']['statements']=[item['document']['statements'][i] for i in indices]
    return item


def test_same_time_achievers_are_first_without_being_uniquely_first():
    item=data()
    assert values(item,generic_model(item,(False,False,True,False,False,True)))==[True,False,True,False,True]


def test_a_later_person_is_not_first_even_if_it_is_their_first_success():
    item=data()
    assert values(item,generic_model(item,(False,False,True,False,True,False)))==[False,False,False,False,True]


def test_a_later_success_does_not_remove_an_earlier_achievement():
    item=data()
    assert values(item,generic_model(item,(False,True,True,False,False,True)))==[False,False,True,True,False]


def test_an_empty_achievement_history_has_no_first_actor():
    item=data()
    assert values(item,generic_model(item,(False,)*6))==[False]*5


def test_unassessed_prior_history_does_not_count_as_no_earlier_success():
    item=data()
    assert values(item,generic_model(item,variant='unassessed'))==[False]*5


def test_restricting_the_comparison_population_changes_relative_priority():
    item=data();model=generic_model(item,(False,False,True,False,True,False))
    model['jopeople']=lambda person:person=='leader'
    assert values(item,model)==[True,True,True,True,False]


def test_a_future_achievement_is_not_completed_at_the_anchor():
    item=data();model=generic_model(item);model['joanchor']=lambda:'early'
    assert values(item,model)==[False]*5


def test_unknown_prior_achievement_is_not_replaced_by_false():
    item=data();model=generic_model(item);original=model['joachieves']
    def unknown(person,activity,target,goal,point):
        if (person,activity,point)==('other','otheract','start'):raise ValueError('Unknown prior achievement')
        return original(person,activity,target,goal,point)
    model['joachieves']=unknown
    with pytest.raises(ValueError,match='Unknown prior achievement'):values(item,model)


def test_cyclic_and_incomparable_times_cannot_certify_priority():
    item=data()
    for variant in ('cyclic','unordered'):
        assert values(item,generic_model(item,variant=variant))==[False]*5


def test_later_truth_without_the_same_action_causal_link_is_not_achievement():
    item=only(data(True),(0,1,3))
    for variant in ('no_agent','no_affected','no_occurrence','no_production','wrong_goal','wrong_target'):
        assert values(item,source_model(item,variant))==[False]*3


def test_an_already_true_goal_is_not_a_transition_into_success():
    item=only(data(True),(0,3))
    assert values(item,source_model(item,'already_true'))==[False,False]


def test_a_different_requested_goal_does_not_inherit_the_achievement():
    item=data(True);base=item['document'];base['statements']=[]
    alternate='i[target a][c['+item['goal']+'][v target]]'
    query='c['+item['facts']+'][k joperson[] k joactivity[] k jotarget[] r['+alternate+'] k jopoint[]]'
    item['document']=parse(format_graph(base,'compact')+'q['+query+'].')
    assert values(item,source_model(item))==[False]


def test_first_achievement_does_not_by_itself_establish_response_worthiness():
    item=only(data(True),(0,3,6))
    assert values(item,source_model(item,'unworthy'))==[True,True,False]


def test_the_first_achiever_property_is_quotable_without_execution():
    item=only(data(True),(7,))
    assert item['disquotations_removed']==2
    assert values(item,guarded(item['document']))==[True]


def test_result_generation_can_involve_more_than_one_agent():
    item=only(data(True),(0,1,2));model=source_model(item);original=model['df']
    model['df']=lambda person,activity,point:original(person,activity,point) or (person,activity,point)==('other','act','late')
    assert values(item,model)==[True,True,False]


def test_saved_evidence_preserves_history_and_limits_the_source_range():
    report=json.loads(REPORT.read_text(encoding='utf-8'))
    for name,digest in report['source_sha256'].items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    child=parse((ROOT/'examples/v014/kant-first-achievers.noema').read_text(encoding='utf-8'))
    assert child['declarations'][:len(parent['declarations'])]==parent['declarations']
    assert len(child['declarations'])==len(parent['declarations'])+8
    assert child['statements']==parent['statements']
    assert report['new_definitions']==8 and report['new_primitives']==report['new_author_statements']==0
    assert not report['alignment']['semantic_completion']
    assert report['verified_full_units']=={'kant-1784':0,'einstein-1905':0}
    segment=report['alignment']['segments'][0]
    unit=next(u for u in json.loads((ROOT/'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id']==segment['unit'])
    start,end=segment['range']
    assert 0<=start<end<=len(unit['text'])
    assert unit['text'][start:end]==segment['text']=='der zuerst'
