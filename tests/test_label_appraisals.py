import hashlib
import json
import pytest
from noema.grammar import parse,format_graph
from scripts.check_label_appraisals import ROOT,REPORT,PARENT,setup,model_for,values
from scripts.check_rod_setup import guarded


def data(source=False):
    stem='label-appraisals-core' if source else 'label-appraisals'
    return setup((ROOT/('examples/v014/'+stem+'.noema')).read_text(encoding='utf-8'),source)


def only(item,indices):
    item['document']['statements']=[item['document']['statements'][i] for i in indices]
    return item


def test_label_appraisal_does_not_assert_the_prince_used_the_label():
    item=data(True)
    assert values(item,model_for(item))==[False,True,True,True,False,False]


def test_no_hypothetical_use_can_make_the_conditional_vacuous_but_not_the_supported_appraisal():
    item=data()
    assert values(item,model_for(item,(False,False,False,False,False,True)))==[False,True,False,True,False,False]


def test_one_in_scope_counterexample_defeats_the_appraisal():
    item=data()
    assert values(item,model_for(item,(False,True,True,False,True,True)))==[False,False,False,True,False,False]


def test_an_excluded_case_is_not_silently_added_to_the_selected_scope():
    item=data();model=model_for(item,(False,True,True,False,True,True))
    model['jzcases']=lambda label,context,point:(label,context,point)==('label','now','belief')
    assert values(item,model)[1:3]==[True,True]


def test_a_qualified_current_use_is_distinct_from_the_hypothetical_evaluation():
    item=data(True)
    assert values(item,model_for(item,(True,True,True,False,False,True),actual_choice=True))==[True,True,True,True,True,False]


def test_attribution_can_hold_while_the_attributed_content_is_false():
    item=data(True)
    assert values(item,model_for(item,(False,True,True,True,True,True)))[1:4]==[False,False,True]


def test_correct_content_does_not_invent_an_author_attribution():
    item=data(True)
    assert values(item,model_for(item,(False,True,True,False,False,False)))[1:4]==[True,True,False]


def test_author_attribution_does_not_execute_the_hypothetical_uses():
    item=only(data(True),(3,));model=model_for(item);limited=guarded(item['document'])
    for name in ('jznode','jzauthor','jtcontext','uc'):limited[name]=model[name]
    assert values(item,limited)==[True]


def test_the_appraisal_can_be_quoted_without_any_primitive_evaluation():
    item=data(True);base=item['document'];base['statements']=[];quote='r['+item['content']+']'
    assert item['disquotations_removed']==1
    item['document']=parse(format_graph(base,'compact')+'q[e['+quote+']['+quote+']].')
    assert values(item,guarded(item['document']))==[True]


def test_unknown_hypothetical_qualifications_are_not_filled_as_deficiencies():
    item=only(data(True),(1,2));model=model_for(item)
    def unknown(*args):raise ValueError('Unknown qualification')
    model['h7l']=unknown
    with pytest.raises(ValueError,match='Unknown qualification'):values(item,model)


def test_unknown_attribution_is_not_false_or_true_by_default():
    item=only(data(True),(3,));model=model_for(item)
    def unknown(*args):raise ValueError('Unknown author attribution')
    model['uc']=unknown
    with pytest.raises(ValueError,match='Unknown author attribution'):values(item,model)


def test_unselected_content_cannot_be_smuggled_into_the_attribution_candidates():
    item=data(True);base=item['document'];base['statements']=[];quote='r['+item['content']+']'
    other='r[b point[u[e[n p a b][n p a b]]]]'
    item['document']=parse(format_graph(base,'compact')+'q[k hzd2[k jznode[] k jzauthor[] l[i[e]]['+other+'] k jtcontext[] '+quote+']].')
    assert values(item,model_for(item))==[False]


def test_assessment_scope_is_bound_to_the_outer_context():
    item=only(data(),(1,2));model=model_for(item);model['jtcontext']=lambda:'belief'
    assert values(item,model)==[False,False]


def test_use_and_deficiency_cannot_be_borrowed_from_different_activities():
    item=data();base=item['document'];base['statements']=[]
    # Pure conditions isolate the universal same-activity requirement.
    extra='r jzuse[a a a d] c.r jzdefect[a a a d] c.'
    query='k rnv[k jylabel[] k jtcontext[] p jzpeople p jzcases p jzuse p jzdefect]'
    item['document']=parse(format_graph(base,'compact')+extra+'q['+query+'].')
    model=model_for(item)
    model['jzuse']=lambda person,act,label,point:(person,act,label,point)==('leader','act','label','belief')
    model['jzdefect']=lambda person,act,label,point:(person,act,label,point)==('leader','otheract','label','belief')
    assert values(item,model)==[False]
    model['jzdefect']=model['jzuse']
    assert values(item,model)==[True]


def test_saved_evidence_keeps_the_hypothetical_reading_partial():
    report=json.loads(REPORT.read_text(encoding='utf-8'))
    for name,digest in report['source_sha256'].items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    child=parse((ROOT/'examples/v014/kant-label-appraisals.noema').read_text(encoding='utf-8'))
    assert child['declarations'][:len(parent['declarations'])]==parent['declarations']
    assert len(child['declarations'])==len(parent['declarations'])+3
    assert child['statements']==parent['statements']
    assert report['new_primitives']==report['new_author_statements']==0
    assert not report['alignment']['semantic_completion']
    assert report['verified_full_units']=={'kant-1784':0,'einstein-1905':0}
