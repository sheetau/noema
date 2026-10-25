from copy import deepcopy
import json
import pytest
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from scripts.shared_reference import ROOT,LIBRARY,BASIS,composed,raw,basis,call,op,content,truth,I,S,T
from scripts.check_shared_reference import (EXAMPLE,reference_document,reference_values,reference_checks,
    projection_document,projection_checks,anaphora_checks,binding_diagnostics,context_checks,contexts,
    again_checks,again_values,again_document,AGAIN_EXAMPLE,document,values,diagnostic,ref)


def test_public_contracts_native_bodies_and_example_are_complete():
    doc=composed()
    assert len(doc['declarations'])==22 and all(d['kind']=='definition' for d in doc['declarations'])
    assert parse((ROOT/LIBRARY).read_text(encoding='utf-8'))==doc==parse(format_graph(doc))
    assert parse((ROOT/EXAMPLE).read_text(encoding='utf-8'))==reference_document()
    assert json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis()
    assert set(basis()['definitions'])==set(basis()['public_contracts'])=={d['name'] for d in doc['declarations']}
    for d in doc['declarations']:
        contract=basis()['public_contracts'][d['name']]
        assert [p['sort'] for p in d['parameters']]==[p['sort'] for p in contract['arguments']]
        assert d['result']==contract['result']
        assert all(p['interpretation'] for p in contract['arguments'])


def test_reference_models_distinguish_failure_from_false_content():
    assert reference_checks()['models']==64
    missing=reference_values((),())
    ambiguous=reference_values(('first','second'),('first',))
    false_content=reference_values(('first',),())
    assert missing[5:8]==ambiguous[5:8]==[False,False,True]
    assert false_content[5:8]==[False,True,False]
    assert missing[1] and not missing[3]
    assert ambiguous[3] and not ambiguous[1]


def test_negation_does_not_turn_missing_reference_into_negative_assertion():
    missing=reference_values((),())
    assert not missing[5] and not missing[8] and missing[10]
    assert (not missing[5])!=missing[8]
    positive=reference_values(('first',),('first',))
    negative=reference_values(('first',),())
    assert positive[5:8]==negative[8:11]
    assert negative[5:8]==positive[8:11]


def test_conditioned_and_global_projection_have_distinct_readings():
    rows=projection_checks()
    assert len(rows)==16
    case=next(r for r in rows if r['input']==(True,False,False,False))
    assert case['values']==[True,True,False,True,True,False]


def test_conditional_background_tracks_its_own_world():
    doc=projection_document()
    flags={'leftbackground':True,'leftissue':False,'rightbackground':False,'rightissue':False}
    model={n:(lambda w,b=b:b if w=='now' else not b) for n,b in flags.items()}
    model['inputworld']=lambda:'other'
    assert values(doc,model)==[False,True,False,True,False,True]


def test_ordered_conjunction_does_not_silently_swap_background_requirements():
    doc=deepcopy(projection_document())
    # Keep only the conjunction background, then exchange its operands.
    original=doc['statements'][4]['body'];swapped=deepcopy(original)
    pair=swapped['content']['arguments'][0]
    pair['arguments'].reverse()
    doc['statements']=[dict(kind='ask',body=original),dict(kind='ask',body=swapped)]
    model={'leftbackground':lambda w:True,'leftissue':lambda w:False,
           'rightbackground':lambda w:False,'rightissue':lambda w:True,'inputworld':lambda:'now'}
    assert values(normalize_document(doc),model)==[True,False]


def test_two_topics_use_the_same_failure_and_negation_rules():
    rows=contexts()
    assert len(rows)==8 and {r['topic'] for r in rows}=={'王の来訪','文書の受領'}
    for row in rows:
        if row['case'] in ('no_referent','two_candidates'):
            assert row['unsupported'] and not row['negative'] and not row['question_valid']
        if row['case']=='unique_negative':
            assert row['negative'] and row['negated_positive'] and row['question_valid']


def test_question_package_preserves_force_even_when_reference_fails():
    for candidates in ((),('first',),('first','second')):
        row=reference_values(candidates,())
        assert row[12:]==[True,False]
        assert row[11]==(len(candidates)==1)
    # Questionhood supplies neither a referent nor a positive answer.
    assert not reference_values((),())[2]
    assert not reference_values(('first',),())[5]


@pytest.mark.parametrize('force',['assert','ask','direct'])
def test_speech_package_keeps_each_existing_force(force):
    background=content(truth(False));issue=content(truth(True))
    act=dict(kind='message',force=force,content=issue)
    package=call('speechpackage',background,act)
    other=dict(kind='message',force='ask' if force!='ask' else 'assert',content=issue)
    doc=document({'inputworld':([],S)},[call('speechvalid',package,call('inputworld')),
        call('speechmatches',package,act),call('speechmatches',package,other)])
    assert values(doc,{'inputworld':lambda:'now'})==[False,True,False]


def test_anaphoric_mentions_and_their_referents_are_counted_separately():
    rows={r['name']:r['values'] for r in anaphora_checks()}
    assert rows['two_mentions_one_referent'][2:]==[True,False]
    assert rows['two_mentions_two_referents'][2:]==[False,True]
    assert not any(rows['no_accessible_mention'])
    assert not any(rows['incompatible_referents'])


def test_anaphora_cannot_mix_antecedents_contexts_or_current_mentions():
    rows=binding_diagnostics()
    assert len(rows)==12 and sum(r['value'] for r in rows)==3


def test_outer_and_reported_speaker_place_and_now_remain_separate():
    data=context_checks()
    assert data['distinct_contexts']==[True,True,False,True,True,False,True,True,False]
    assert data['ambiguous_roles']==[True,False,False,True,True,False,True,False,False]


def test_repetitive_again_keeps_same_actors_prior_occurrence_under_negation():
    assert parse((ROOT/AGAIN_EXAMPLE).read_text(encoding='utf-8'))==again_document()
    rows=again_checks()
    assert len(rows)==4
    assert rows[0]['values']==[False,False,True,False,False,True]
    assert again_values(True,False)==[False,True,False,True,False,False]
    assert again_values(True,True,other_actor=True)==[False,False,True,False,False,True]


def test_quoted_context_selection_remains_visible_without_executing_the_reference():
    primitives={'outer':([],I),'inner':([],I),'speaker':([],I),'person':([],I),'assigned':([I,I,I],T)}
    def selection(ctx):return call('individualrole',call(ctx),call('speaker'),call('person'),ref('assigned'))
    left=dict(kind='quote',body=selection('outer'));right=dict(kind='quote',body=selection('inner'))
    doc=document(primitives,[op('not',op('equal',left,right))])
    def unknown(*args):raise AssertionError('Quoted context was executed')
    assert values(doc,{name:unknown for name in primitives})==[True]


def test_unknown_relation_is_not_converted_to_absent_candidate_or_false_presupposition():
    with pytest.raises(ValueError,match='Missing'):reference_values(None,())
    def unknown(*args):raise ValueError('Unknown property interpretation')
    model={'inputcandidates':lambda *args:False,'inputproperty':unknown,
           'inputworld':lambda:'now','inputreferent':lambda:'first'}
    with pytest.raises(ValueError,match='Unknown property'):values(reference_document(),model)


def test_nested_presupposition_negation_preserves_worldwise_content():
    doc=deepcopy(reference_document());pair=call('definitestatement',ref('inputcandidates'),ref('inputproperty'))
    double=call('presuppnegate',call('presuppnegate',pair))
    doc['statements']=[dict(kind='ask',body=b) for b in diagnostic(pair)+diagnostic(double)]
    model={'inputcandidates':lambda x,w:x=='first','inputproperty':lambda x,w:w=='other',
           'inputworld':lambda:'now','inputreferent':lambda:'first'}
    assert values(normalize_document(doc),model)==[False,True,False,False,True,False]
