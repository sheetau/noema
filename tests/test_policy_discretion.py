import hashlib
import json
import pytest
from noema.grammar import parse,format_graph
from noema.specialization import specialize_definition
from scripts.check_policy_discretion import ROOT,REPORT,PARENT,setup,model_for,values,DUTY,SOURCE_DUTY
from scripts.check_assessed_payments import description
from scripts.check_rod_setup import guarded
from scripts.compose_limits import call as k


def data(source=False):
    stem='policy-discretion-core' if source else 'policy-discretion'
    return setup((ROOT/('examples/v014/'+stem+'.noema')).read_text(encoding='utf-8'),source)


def only(item,indices):
    item['document']['statements']=[item['document']['statements'][i] for i in indices]
    return item


def test_actual_freedom_can_fulfil_a_duty_without_being_a_discretionary_grant():
    item=data(True)
    assert values(item,model_for(item))==[True,False,False,True,True,False]


def test_discretion_can_exist_without_realizing_the_policy():
    item=data()
    assert values(item,model_for(item,(False,True,True,False,False,True)))==[False,True,False,False,False,True]


def test_just_having_no_requirement_is_not_positive_latitude():
    item=data()
    assert values(item,model_for(item,(True,False,False,False,False,False)))==[True,False,False,False,False,False]


def test_permission_to_grant_alone_does_not_allow_withholding():
    item=data()
    assert values(item,model_for(item,(True,True,False,False,False,True)))==[True,False,False,False,True,False]


def test_conflicting_requirements_do_not_become_discretion():
    item=data(True)
    assert values(item,model_for(item,(True,True,True,True,True,True)))==[True,False,False,True,True,False]


def test_lack_of_qualification_does_not_invent_a_claimed_standing():
    item=data()
    assert values(item,model_for(item,(True,False,False,True,False,False)))[4] is False


def test_latitude_and_claim_evaluation_do_not_execute_the_policy():
    item=only(data(True),(1,4,5));model=model_for(item,(False,True,True,False,False,True));limited=guarded(item['document'])
    for name in ('jtperson','jtcontext','jtassessor','jtoffice','jxactivity','jxstanding','jxassumes','h7k','h7l'):limited[name]=model[name]
    assert values(item,limited)==[True,False,True]


def test_fulfilment_needs_the_actual_policy_conditions():
    item=only(data(True),(3,));model=model_for(item)
    def unknown(*args):raise ValueError('Unknown inner permission')
    model['h7b']=unknown
    with pytest.raises(ValueError,match='Unknown inner permission'):values(item,model)


def test_unknown_outer_norms_are_not_interpreted_as_free_choice():
    item=only(data(),(1,));model=model_for(item)
    def unknown(*args):raise ValueError('Unknown outer norm')
    model['jtouterrequired']=unknown
    with pytest.raises(ValueError,match='Unknown outer norm'):values(item,model)


@pytest.mark.parametrize('bindings',['l[a][]','l[a][k jtperson[] k jtperson[]]'])
def test_latitude_requires_exactly_one_person_binding(bindings):
    item=data();base=item['document'];base['statements']=[]
    item['document']=parse(format_graph(base,'compact')+'q[t[c['+item['policies'][0]+']['+bindings+']][k jtcontext[]]].')
    assert values(item,model_for(item,(True,True,True,False,False,True)))==[False]


def test_a_different_standing_does_not_inherit_this_qualification():
    item=data();base=item['document'];base['statements']=[]
    item['document']=parse(format_graph(base,'compact')+'q[t[c['+item['criterion']+'][k jtperson[] k jtoffice[]]][k jtcontext[]]].')
    assert values(item,model_for(item,(True,True,True,False,False,True)))==[False]


def test_a_policy_alias_does_not_inherit_another_description_permission():
    item=data(True);base=item['document'];base['statements']=[]
    alias='d jxpolicyalias[] h[j[a]] e['+item['old']['policy']+'].'
    refs={**item['refs'],'policy':'r[k jxpolicyalias[]]'}
    choice=k('hzfx',*(refs[n] for n,_ in SOURCE_DUTY))
    queries='q[t[c['+choice+']['+item['bindings']+']][k jtcontext[]]].q[t[c[k jxpolicyalias[]]['+item['bindings']+']][k jtcontext[]]].'
    item['document']=parse(format_graph(base,'compact')+alias+queries)
    assert values(item,model_for(item,(True,True,True,False,False,True)))==[False,True]


@pytest.mark.parametrize('symbol,index',[('hzfy',1),('hzfz',2)])
def test_actual_policy_checks_can_be_quoted_after_closed_specialization(symbol,index):
    item=data(True);base=item['document'];base['statements']=[]
    expr=item['policies'][index]
    with pytest.raises(ValueError):parse(format_graph(base,'compact')+'q[e[r['+expr+']][r['+expr+']]].')
    specialized=specialize_definition(base,symbol,'jxknown',{2:description(base,item['old']['policy'])})
    assert specialized.disquotations_removed==1
    expr=k('jxknown',item['refs']['assessor'],item['refs']['office'])
    item['document']=parse(format_graph(specialized.document,'compact')+'q[e[r['+expr+']][r['+expr+']]].')
    assert values(item,guarded(item['document']))==[True]


def test_saved_evidence_preserves_history_and_keeps_the_interpretation_explicit():
    report=json.loads(REPORT.read_text(encoding='utf-8'))
    for name,digest in report['source_sha256'].items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    child=parse((ROOT/'examples/v014/kant-policy-discretion.noema').read_text(encoding='utf-8'))
    assert child['declarations'][:len(parent['declarations'])]==parent['declarations']
    assert len(child['declarations'])==len(parent['declarations'])+9
    assert child['statements']==parent['statements']
    assert report['new_primitives']==report['new_author_statements']==0
    assert report['source_context']['interpretation_not_explicit_in_source']
    assert not report['alignment']['semantic_completion']
    assert report['verified_full_units']=={'kant-1784':0,'einstein-1905':0}
