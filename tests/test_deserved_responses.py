import hashlib
import json
import pytest
from noema.grammar import parse,format_graph
from scripts.check_deserved_responses import ROOT,REPORT,PARENT,setup,model_for,values
from scripts.check_rod_setup import guarded


def data(source=False,empty=False):
    stem='deserved-responses-core' if source else 'deserved-responses'
    return setup((ROOT/('examples/v014/'+stem+'.noema')).read_text(encoding='utf-8'),source,empty)


def only(item,indices):
    item['document']['statements']=[item['document']['statements'][i] for i in indices]
    return item


def query(item,text):
    doc=item['document'];doc['statements']=[]
    item['document']=parse(format_graph(doc,'compact')+'q['+text+'].')
    return item


def test_deserving_praise_does_not_require_actual_praise():
    item=data()
    assert values(item,model_for(item,(True,True,True,False,True,True)))==[True,True,False,True]


def test_actual_praise_does_not_certify_desert_or_its_ground():
    item=data()
    assert values(item,model_for(item,(False,True,True,True,True,True)))==[False,False,True,True]


def test_a_true_ground_does_not_remove_the_need_for_response_standards():
    item=data()
    assert values(item,model_for(item,(True,True,False,True,True,True)))==[True,False,True,True]


def test_empty_standards_do_not_establish_desert():
    item=data(empty=True)
    assert values(item,model_for(item))==[True,False,True,True]


def test_desert_does_not_execute_the_response_description():
    item=only(data(),(1,));model=model_for(item)
    def forbidden(*args):raise ValueError('Response execution forbidden')
    for name in ('jnoccurs','jnpresents','jnconveys','jnusers'):model[name]=forbidden
    assert values(item,model)==[True]


def test_the_recipient_is_not_replaced_by_the_speaker():
    item=data();model=model_for(item);model['jnsubject']=lambda:'caller'
    assert values(item,model)==[False,False,False,True]


def test_the_response_must_be_about_the_same_recipient():
    item=data()
    assert values(item,model_for(item,variant='other_subject'))==[True,True,False,True]


def test_an_equivalent_ground_description_does_not_inherit_the_standard():
    item=data();basis='i[person a][c[p jnbasis][v person]]'
    expr='t[k ro5[k jnsubject[] r['+item['response']+'] r['+basis+'] '+item['standards']+']][k jncontext[]]'
    query(item,expr)
    assert values(item,model_for(item))==[False]


def test_a_different_response_description_does_not_inherit_the_standard():
    item=data();response=item['response'].replace('p jnusers','i[person a][k jnusers[v person]]')
    assert response!=item['response']
    expr='t[k ro5[k jnsubject[] r['+response+'] r['+item['basis']+'] '+item['standards']+']][k jncontext[]]'
    query(item,expr)
    assert values(item,model_for(item))==[False]


def test_unknown_response_standards_are_not_treated_as_satisfied():
    item=only(data(),(1,));model=model_for(item)
    def unknown(*args):raise ValueError('Unknown response standard')
    model['jnfirst']=unknown
    with pytest.raises(ValueError,match='Unknown response standard'):values(item,model)


def test_quoted_desert_content_does_not_evaluate_grounds_or_standards():
    item=only(data(),(3,))
    assert item['disquotations_removed']==1
    assert values(item,guarded(item['document']))==[True]


def test_source_desert_and_general_conclusion_can_hold_without_actual_praise():
    item=data(True)
    assert values(item,model_for(item,(True,True,True,False,True,True)))==[True,True,False,True,True,True]


def test_enlightenment_and_response_worthiness_are_independent_conjuncts():
    item=only(data(True),(1,4))
    assert values(item,model_for(item,variant='incapable'))==[True,False]
    assert values(item,model_for(item,(True,True,False,True,True,True)))==[False,False]


def test_author_attribution_does_not_execute_the_general_claim():
    item=only(data(True),(5,));model=model_for(item);limited=guarded(item['document'])
    assert item['disquotations_removed']==2
    for name in ('jmnode','jmauthor','jncontext','uc'):limited[name]=model[name]
    assert values(item,limited)==[True]


def test_saved_evidence_preserves_history_and_does_not_complete_the_source_unit():
    report=json.loads(REPORT.read_text(encoding='utf-8'))
    for name,digest in report['source_sha256'].items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    child=parse((ROOT/'examples/v014/kant-deserved-responses.noema').read_text(encoding='utf-8'))
    assert child['declarations'][:len(parent['declarations'])]==parent['declarations']
    assert len(child['declarations'])==len(parent['declarations'])+6
    assert child['statements']==parent['statements']
    assert report['new_definitions']==6 and report['new_primitives']==report['new_author_statements']==0
    assert not report['alignment']['semantic_completion']
    assert report['verified_full_units']=={'kant-1784':0,'einstein-1905':0}


def test_source_alignment_does_not_count_unwritten_collectives_or_achievements():
    report=json.loads(REPORT.read_text(encoding='utf-8'))
    units=json.loads((ROOT/'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units']
    unit=next(u for u in units if u['id']=='kant-1784:u0015')
    assert [s['text'] for s in report['alignment']['segments']]==['und verdient','gepriesen zu werden']
    for segment in report['alignment']['segments']:
        start,end=segment['range']
        assert 0<=start<end<=len(unit['text'])
        assert unit['text'][start:end]==segment['text']
