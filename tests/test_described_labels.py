import hashlib
import json
import pytest
from noema.grammar import parse,format_graph
from scripts.check_described_labels import ROOT,REPORT,PARENT,setup,model_for,values
from scripts.check_rod_setup import guarded


def data(source=False,**kwargs):
    stem='described-labels-core' if source else 'described-labels'
    return setup((ROOT/('examples/v014/'+stem+'.noema')).read_text(encoding='utf-8'),source,**kwargs)


def only(item,indices):
    item['document']['statements']=[item['document']['statements'][i] for i in indices]
    return item


def test_self_adoption_is_possible_even_when_the_described_qualification_is_false():
    item=data(True)
    assert values(item,model_for(item))==[True,True,True,True,True,False,True]


def test_a_true_description_does_not_invent_a_label_use():
    item=data()
    assert values(item,model_for(item,(False,True,True,True,True,True)))==[False,False,False,False,False,True,False]


def test_a_reported_or_quoted_label_does_not_imply_adoption():
    item=data(True)
    assert values(item,model_for(item,(True,True,True,False,False,True)))==[True,True,False,False,False,False,False]


def test_naming_someone_else_is_not_self_positioning():
    item=data(True,argument='k jtassessor[]');model=model_for(item)
    model['jysubject']=lambda:'assessor'
    model['jyassigns']=lambda act,label,subject,point:(act,label,subject,point)==('act','label','assessor','now')
    assert values(item,model)==[True,True,True,False,False,False,False]


def test_a_correct_template_instance_must_still_refer_to_the_actual_named_person():
    item=data(argument='k jtassessor[]')
    assert values(item,model_for(item))==[True,False,False,False,False,False,False]


def test_a_different_instance_argument_is_not_accepted_by_the_structural_matcher():
    item=data(instance_argument='k jtassessor[]')
    assert values(item,model_for(item))==[True,False,False,False,False,False,False]


def test_co_referring_argument_expressions_are_not_the_same_template_instance():
    item=data(argument='k jtassessor[]',instance_argument='k jtperson[]');model=model_for(item)
    model['jtassessor']=lambda:'leader'
    item=only(item,(0,1,2,3,4))
    assert values(item,model)==[True,False,False,False,False]


def test_using_the_name_does_not_execute_its_unknown_policy_description():
    item=only(data(True),(0,1,2,3,4));model=model_for(item);limited=guarded(item['document'])
    for name in ('jtperson','jtcontext','jxactivity','jxstanding','jylabel','jysubject','jyassigns','dg','f3','hw2','hx2','hy2','rbo'):limited[name]=model[name]
    assert values(item,limited)==[True]*5


def test_evaluating_the_qualification_does_not_require_actual_policy_execution():
    item=only(data(True),(6,));model=model_for(item)
    def unknown(*args):raise ValueError('Unknown actual permission')
    model['h7b']=unknown
    assert values(item,model)==[True]


def test_truth_of_the_label_description_requires_actual_policy_inputs():
    item=only(data(True),(5,));model=model_for(item,(True,True,True,True,True,True))
    def unknown(*args):raise ValueError('Unknown actual permission')
    model['h7b']=unknown
    with pytest.raises(ValueError,match='Unknown actual permission'):values(item,model)


def test_unknown_definition_record_is_not_replaced_with_a_guessed_meaning():
    item=only(data(True),(1,));model=model_for(item)
    def unknown(*args):raise ValueError('Unknown definition record')
    model['hw2']=unknown
    with pytest.raises(ValueError,match='Unknown definition record'):values(item,model)


def test_closed_explanatory_property_can_be_quoted_without_evaluating_any_primitive():
    item=data(True);base=item['document'];base['statements']=[];quoted='r['+item['pattern']+']'
    assert item['disquotations_removed']==1
    item['document']=parse(format_graph(base,'compact')+'q[e['+quoted+']['+quoted+']].')
    assert values(item,guarded(item['document']))==[True]


def test_the_stance_factory_does_not_claim_another_standing():
    item=data(True);base=item['document'];base['statements']=[]
    query='c['+item['assumed']+'][k jtperson[] k jxactivity[] k jtoffice[] k jtcontext[]]'
    item['document']=parse(format_graph(base,'compact')+'q['+query+'].')
    assert values(item,model_for(item))==[False]


def test_definition_records_from_another_context_do_not_supply_current_meaning():
    item=data(True)
    assert values(item,model_for(item,variant='other_stored_context'))==[True,False,False,False,False,False,False]


def test_missing_adoption_does_not_become_arrogance_from_actual_duty_alone():
    item=data()
    assert values(item,model_for(item,(True,True,False,True,False,True)))[4:]==[False,False,False]


def test_saved_evidence_preserves_history_without_promoting_the_candidate_to_full_translation():
    report=json.loads(REPORT.read_text(encoding='utf-8'))
    for name,digest in report['source_sha256'].items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    child=parse((ROOT/'examples/v014/kant-described-labels.noema').read_text(encoding='utf-8'))
    assert child['declarations'][:len(parent['declarations'])]==parent['declarations']
    assert len(child['declarations'])==len(parent['declarations'])+7
    assert child['statements']==parent['statements']
    assert report['new_primitives']==report['new_author_statements']==0
    assert not report['alignment']['semantic_completion']
    assert report['verified_full_units']=={'kant-1784':0,'einstein-1905':0}
