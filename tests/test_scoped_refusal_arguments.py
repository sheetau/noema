import hashlib
import json
import pytest
from noema.grammar import parse,format_graph
from scripts.check_scoped_refusal_arguments import ROOT,REPORT,PARENT,setup,model_for,values
from scripts.check_rod_setup import guarded
from scripts.compose_curve_discourse import conditional_basis


def data(source=False):
    stem='scoped-refusal-arguments-core' if source else 'scoped-refusal-arguments'
    return setup((ROOT/('examples/v014/'+stem+'.noema')).read_text(encoding='utf-8'),source)


def only(item,indices):
    item['document']['statements']=[item['document']['statements'][i] for i in indices]
    return item


def test_holding_a_duty_belief_does_not_imply_actual_duty_or_actual_refusal():
    item=data(True)
    assert values(item,model_for(item,norms=(False,False,True,True)))==[False,True,True,True,False,True]


def test_a_scoped_argument_does_not_assert_its_premise_is_actually_true():
    item=data()
    assert values(item,model_for(item,(False,False,True,True,True)))==[True,False,True,False,False,True]


def test_actual_refusal_does_not_invent_the_discourse_relation():
    item=data(True)
    assert values(item,model_for(item,(True,True,True,True,False)))==[True,False,True,True,True,False]


def test_a_reported_conclusion_can_be_false_in_the_actual_context():
    item=data(True)
    assert values(item,model_for(item))==[True,False,True,True,False,True]


def test_scoped_discourse_does_not_execute_either_quoted_content():
    item=only(data(True),(5,));model=model_for(item);limited=guarded(item['document'])
    for name in ('jkauthor','jkscope','jkpremise','jkconclusion','jtcontext','ug','uh','ud','ue'):limited[name]=model[name]
    assert values(item,limited)==[True]


def test_the_duty_choice_law_does_not_execute_the_policy():
    item=only(data(True),(2,));model=model_for(item);limited=guarded(item['document'])
    for name in ('jtperson','jtcontext','jtassessor','jtoffice','h7k','h7l'):limited[name]=model[name]
    assert values(item,limited)==[True]


def test_unknown_scoped_claim_is_not_inferred_from_refusal():
    item=only(data(True),(5,));model=model_for(item,(True,True,True,True,True))
    def unknown(*args):raise ValueError('Unknown scoped claim')
    model['uh']=unknown
    with pytest.raises(ValueError,match='Unknown scoped claim'):values(item,model)


def test_unknown_norm_is_not_replaced_by_a_proved_law_constant():
    item=only(data(True),(2,));model=model_for(item)
    def unknown(*args):raise ValueError('Unknown norm')
    model['h7k']=unknown
    with pytest.raises(ValueError,match='Unknown norm'):values(item,model)


def test_the_premise_and_result_are_quotable_without_recognizing_their_truth():
    item=data(True);base=item['document'];base['statements']=[]
    assert item['disquotations_removed']==1
    queries=''.join('q[e[r['+expr+']][r['+expr+']]].' for expr in (item['premise'],item['result']))
    item['document']=parse(format_graph(base,'compact')+queries)
    assert values(item,guarded(item['document']))==[True,True]


def test_changing_only_the_conclusion_person_does_not_inherit_the_source_claim():
    item=data(True);base=item['document'];base['statements']=[]
    result=item['result'].replace('k jtperson[]','k jtassessor[]')
    assert result!=item['result']
    query='k hzf5[k jkauthor[] k jtcontext[] k jkscope[] k jkpremise[] k jkconclusion[] r['+item['premise']+'] r['+result+']]'
    item['document']=parse(format_graph(base,'compact')+'q['+query+'].')
    assert values(item,model_for(item))==[False]


def test_scopes_cannot_be_combined_even_with_the_same_author():
    item=data(True)
    assert values(item,model_for(item,variant='other_conclusion_scope'))[5] is False
    assert values(item,model_for(item,variant='other_assumption_scope'))[5] is False


def test_source_and_conclusion_cannot_be_the_same_textual_node():
    item=data(True)
    assert values(item,model_for(item,variant='merged_nodes'))[5] is False


def test_textual_order_is_required_even_if_both_contents_are_true():
    item=data()
    assert values(item,model_for(item,(True,True,True,True,True),variant='reversed_order'))[3:]==[True,True,False]


def test_imported_scoped_relations_keep_the_existing_cross_document_meanings():
    basis=json.loads((ROOT/'data/kant-scoped-refusal-arguments-basis-v1.json').read_text(encoding='utf-8'))
    wanted={r['symbol']:r for r in conditional_basis()['primitives'] if r['symbol'] in ('ug','uh')}
    actual={r['symbol']:r for r in basis['primitives'] if r['symbol'] in wanted}
    assert actual==wanted


def test_saved_evidence_preserves_history_and_counts_shared_imports():
    report=json.loads(REPORT.read_text(encoding='utf-8'))
    for name,digest in report['source_sha256'].items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    child=parse((ROOT/'examples/v014/kant-scoped-refusal-arguments.noema').read_text(encoding='utf-8'))
    assert child['declarations'][:len(parent['declarations'])]==parent['declarations']
    assert len(child['declarations'])==len(parent['declarations'])+6
    assert child['statements']==parent['statements']
    assert report['new_primitives']==2 and report['new_definitions']==4 and report['new_author_statements']==0
    assert report['shared_imports']==['ug','uh']
    assert not report['alignment']['semantic_completion']
    assert report['verified_full_units']=={'kant-1784':0,'einstein-1905':0}
