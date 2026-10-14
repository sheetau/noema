import hashlib
import json
import pytest
from noema.grammar import parse,format_graph
from scripts.check_label_refusals import ROOT,REPORT,PARENT,setup,model_for,values
from scripts.check_rod_setup import guarded


def data(source=False,**kwargs):
    stem='label-refusals-core' if source else 'label-refusals'
    return setup((ROOT/('examples/v014/'+stem+'.noema')).read_text(encoding='utf-8'),source,**kwargs)


def only(item,indices):
    item['document']['statements']=[item['document']['statements'][i] for i in indices]
    return item


def test_a_refusal_can_be_communicated_while_people_keep_using_the_name():
    item=data(True)
    assert values(item,model_for(item))==[True,False,True,True,False]


def test_not_using_a_name_is_not_a_refusal_event():
    item=data()
    assert values(item,model_for(item,(False,False,False,False,True)))==[False,True,False,True,False]


def test_refusal_does_not_determine_whether_the_description_is_true():
    item=data()
    for truth in (False,True):
        assert values(item,model_for(item,(True,True,True,True,truth)))==[True,False,True,truth,False]


def test_two_coextensive_designations_can_be_refused_separately():
    item=data();model=model_for(item)
    model['jwlabel']=lambda:'alternate'
    assert values(item,model)==[True,True,False,True,False]
    original=data();assert values(original,model_for(original))==[True,False,True,True,False]


def test_an_empty_target_scope_does_not_make_the_request_fulfilled():
    item=data();model=model_for(item,(True,True,True,False,True),'empty_users')
    assert values(item,model)==[False,False,False,True,False]


def test_all_recipients_need_the_same_refusal_presentation():
    item=data(True);model=model_for(item);old=model['f2']
    model['jwusers']=lambda person:person in ('caller','other')
    assert values(item,model)[0] is False
    model['f2']=lambda act,recipient,subject,desc,point:old(act,'caller' if recipient=='other' else recipient,subject,desc,point)
    assert values(item,model)[0] is True


def test_name_use_outside_the_requested_scope_does_not_break_its_content():
    item=only(data(),(1,2));model=model_for(item)
    model['jwusers']=lambda person:person=='other'
    assert values(item,model)==[True,True]


def test_the_name_and_the_presentation_must_belong_to_the_same_act():
    item=data(True)
    assert values(item,model_for(item,variant='wrong_naming_act'))==[True,True,False,True,False]


def test_delivery_does_not_evaluate_the_requested_content_or_label_quality():
    item=only(data(True),(0,));model=model_for(item);limited=guarded(item['document'])
    for name in ('jwperson','jwactivity','jwcontext','jwusers','dg','f3','f2'):limited[name]=model[name]
    assert values(item,limited)==[True]


def test_quoting_a_refusal_does_not_execute_its_message():
    item=data(True);base=item['document'];base['statements']=[];quoted='r['+item['message']+']'
    item['document']=parse(format_graph(base,'compact')+'q[e['+quoted+']['+quoted+']].')
    assert values(item,guarded(item['document']))==[True]


def test_unknown_naming_records_are_not_assumed_to_be_absence():
    item=only(data(),(1,));model=model_for(item)
    def unknown(*args):raise ValueError('Unknown naming record')
    model['jwassigns']=unknown
    with pytest.raises(ValueError,match='Unknown naming record'):values(item,model)


@pytest.mark.parametrize('force',['s','q'])
def test_a_directive_is_distinct_from_asserting_or_asking_the_same_content(force):
    item=data();base=item['document'];base['statements']=[]
    content='c['+item['content']+'][k jwperson[]]';message='c['+item['message']+'][k jwperson[]]'
    item['document']=parse(format_graph(base,'compact')+'q[e['+message+'][j '+force+'['+content+']]].q[e[o['+message+']]['+content+']].')
    assert values(item,model_for(item))==[False,True]


def test_present_nonuse_is_not_a_claim_about_all_times():
    item=data();model=model_for(item);model['jwcontext']=lambda:'later'
    assert values(item,model)==[False,True,False,True,False]


def test_saved_evidence_keeps_name_refusal_partial_and_preserves_history():
    report=json.loads(REPORT.read_text(encoding='utf-8'))
    for name,digest in report['source_sha256'].items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    child=parse((ROOT/'examples/v014/kant-label-refusals.noema').read_text(encoding='utf-8'))
    assert child['declarations'][:len(parent['declarations'])]==parent['declarations']
    assert len(child['declarations'])==len(parent['declarations'])+5
    assert child['statements']==parent['statements']
    assert report['new_primitives']==report['new_author_statements']==0
    assert not report['alignment']['semantic_completion']
    assert report['verified_full_units']=={'kant-1784':0,'einstein-1905':0}
