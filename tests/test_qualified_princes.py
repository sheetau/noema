import hashlib
import json
import pytest
from noema.grammar import parse,format_graph
from scripts.check_qualified_princes import ROOT,REPORT,PARENT,setup,generic_model,source_setup,source_model,values
from scripts.check_rod_setup import guarded


def generic():return setup((ROOT/'examples/v014/qualified-princes.noema').read_text(encoding='utf-8'))
def source():return source_setup((ROOT/'examples/v014/qualified-princes-core.noema').read_text(encoding='utf-8'))
def only(data,indices):
    data['document']['statements']=[data['document']['statements'][i] for i in indices]
    return data


def test_a_vacuously_true_general_claim_has_no_witness():
    data=generic()
    assert values(data,generic_model(data,(False,True,True,False),(True,False,True,False)))==[False,False,True,False,False]


def test_qualifying_conditions_cannot_be_pooled_across_people():
    data=generic()
    assert values(data,generic_model(data,(True,False,False,False),(False,True,True,False)))==[False,False,True,False,False]


def test_one_counterexample_defeats_the_generalization_despite_another_success():
    data=generic()
    assert values(data,generic_model(data,(True,True,True,True),(True,True,True,False)))==[True,True,False,True,True]


def test_an_unqualified_person_is_not_a_counterexample():
    data=generic()
    assert values(data,generic_model(data,(True,True,True,True),(False,True,True,False)))==[True,False,True,True,False]


def test_the_claim_does_not_quantify_over_other_contexts():
    data=generic();first=(True,True,True,False)
    assert values(data,generic_model(data,first))[2] is False
    assert values(data,generic_model(data,first,context='belief'))==[False,False,True,False,False]


def test_inner_duty_belief_and_actual_policy_are_not_required_by_outer_appraisal():
    data=only(source(),(0,))
    assert values(data,source_model(data,inner_truth=False))==[True]
    assert values(data,source_model(data,inner_truth=True))==[True]


def test_the_appraised_report_need_not_be_enacted():
    data=source();model=source_model(data)
    assert model['dg']('speech','now') is False
    assert model['dg']('refusal','now') is True
    assert values(only(data,(0,)),model)==[True]


def test_refusal_by_another_person_does_not_complete_the_subject_description():
    data=only(source(),(0,))
    assert values(data,source_model(data,'other_refuser'))==[False]
    assert values(data,source_model(data,'other_subject'))==[False]


def test_empty_judgment_candidates_do_not_establish_the_appraisal():
    data=only(source(),(0,))
    assert values(data,source_model(data,'empty_appraisal'))==[False]


def test_an_attributed_general_claim_can_have_a_counterexample():
    data=source()
    assert values(data,source_model(data))==[True,False,True,True,True,False]


def test_attribution_does_not_evaluate_the_closed_claim():
    data=only(source(),(4,));model=source_model(data);limited=guarded(data['document'])
    for name in ('jmnode','jmauthor','jtcontext','uc'):limited[name]=model[name]
    assert values(data,limited)==[True]


def test_quoted_claim_and_utterance_do_not_evaluate_their_contents():
    data=source();base=data['document'];base['statements']=[]
    assert data['disquotations_removed']==1
    qs=''.join('q[e[r['+expr+']][r['+expr+']]].' for expr in (data['utterance'],data['claim']))
    data['document']=parse(format_graph(base,'compact')+qs)
    assert values(data,guarded(data['document']))==[True,True]


def test_a_constructed_assertion_can_have_false_content():
    data=source();model=source_model(data);base=data['document'];base['statements']=[]
    qs='q[e['+data['utterance']+'][j s['+data['claim']+']]].q[t['+data['claim']+'][k jtcontext[]]].'
    data['document']=parse(format_graph(base,'compact')+qs)
    assert values(data,model)==[True,False]


def test_capability_uses_own_understanding_and_rejects_external_guidance():
    data=only(source(),(5,));model=source_model(data,capable=True)
    assert values(data,model)==[True]
    model['ad']=lambda guide,person,act,point:(guide,person,act)==('coholder','leader','act')
    assert values(data,model)==[False]


def test_unknown_capability_is_not_filled_from_the_authors_claim():
    data=only(source(),(1,));model=source_model(data)
    def unknown(*args):raise ValueError('Unknown ability assessment')
    model['ap']=unknown
    with pytest.raises(ValueError,match='Unknown ability assessment'):values(data,model)


def test_saved_evidence_preserves_history_and_does_not_claim_semantic_completion():
    report=json.loads(REPORT.read_text(encoding='utf-8'))
    for name,digest in report['source_sha256'].items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    child=parse((ROOT/'examples/v014/kant-qualified-princes.noema').read_text(encoding='utf-8'))
    assert child['declarations'][:len(parent['declarations'])]==parent['declarations']
    assert len(child['declarations'])==len(parent['declarations'])+6
    assert child['statements']==parent['statements']
    assert report['new_definitions']==6 and report['new_primitives']==report['new_author_statements']==0
    assert not report['alignment']['semantic_completion']
    assert report['verified_full_units']=={'kant-1784':0,'einstein-1905':0}
