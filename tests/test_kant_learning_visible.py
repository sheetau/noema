"""Preserve the whole learning/reaction sentence and its ranked attributions."""
from copy import deepcopy
from dataclasses import replace
import json
import pytest
from noema.constructed_semantics import DescriptionValue,FunctionValue,evaluate_document
from scripts import check_kant_learning_visible as check
from scripts import check_deterrence_sentence as retained
from scripts.shared_modality import call,renamed
import test_kant_confinement_visible as parent

DOMAIN=parent.DOMAIN+('contrast','low','learn','outcome')


def evaluate(doc,values,memo=True):
    return [r['value'] for r in evaluate_document(doc,individuals=DOMAIN,situations=('body','closing','other'),
        primitives=values,max_steps=1000000,memoize_definitions=memo,memoize_expressions=memo)]


def model(doc,variant='baseline',bits=(True,)*6,depictions=(True,)*3):
    values=parent.model(doc);voc=check.vocabulary();m=check.mapping();inverse={v:k for k,v in m.items()}
    prior_sentence=values[voc._symbols['sentencereference']]
    prior_span=values[voc._symbols['sentencetokenspanreference']]
    def sentence(context,paragraph,index):
        if (context,paragraph,index)==('closing',2,7):return 'contrast'
        return prior_sentence(context,paragraph,index)
    def span(document,first,a,last,b,context):
        if (document,first,last,context)==('document','contrast','contrast','closing'):
            for key,target in [('fu','low'),('fv','learn'),('g2','outcome')]:
                row=check.read(check.ANCHORS)['source_spans'][key]
                if (a,b)==(row['first_token'],row['last_token']):return target
            raise ValueError('Unknown learning clause span')
        return prior_span(document,first,a,last,b,context)
    values[voc._symbols['sentencereference']]=sentence
    values[voc._symbols['sentencetokenspanreference']]=span
    original=retained.model(bits,depictions,variant)
    def adapt(value):
        if isinstance(value,DescriptionValue):
            return replace(value,syntax=json.dumps(renamed(json.loads(value.syntax),inverse),ensure_ascii=False,sort_keys=True))
        if isinstance(value,str):return {'confinement':'previous','body':'anchor'}.get(value,value)
        if isinstance(value,FunctionValue):
            # The old model enumerates its 'previous' node when inspecting
            # premises. Map it back to the actual preceding sentence before
            # calling the original guarded function in the new document.
            def invoke(*args):
                actual=[{'previous':'confinement','anchor':'body'}.get(a,a) if isinstance(a,str) else a for a in args]
                return value(*actual)
            return replace(value,implementation=invoke)
        return value
    nodes={'low','learn','outcome','contrast'}
    def handler(name,previous):
        def invoke(*args):
            selected=(name in ('hznreport','hzrbgreport','rbt') or
                name in ('uc','qa') and args[0] in nodes or
                name=='ud' and args[2] in nodes or
                name=='ue' and (args[0] in nodes or args[1] in nodes))
            return original[name](*(adapt(a) for a in args)) if selected else previous(*args)
        return invoke
    for name in ('uc','ud','ue','qa','hznreport','hzrbgreport','rbt'):
        values[m[name]]=handler(name,values[m[name]])
    return values


def test_complete_source_and_prior_statements_are_preserved():
    doc=check.restored()['document']
    assert check.backprojection(doc)==check.source_excerpt()
    assert check.specialized_backprojection(doc)==check.specialized_source()
    assert doc['statements'][:22]==check.previous.document()['statements']
    assert len(doc['declarations'])==600 and len(doc['statements'])==26
    assert len(check.source_excerpt()['declarations'])==580


def test_full_document_keeps_reason_background_order_and_depictions_distinct():
    doc=check.restored()['document']
    ordinary=('swapped_claims','reversed_reason','extra_premise','missing_prior_link',
        'reversed_learning','both_directions','other_foreground_scope','other_background_scope',
        'other_node','swapped_background')
    expected={n:[False,True,True,True] for n in ordinary}
    expected.update(baseline=[True]*4,other_author=[False]*4,other_context=[False]*4,
        fall_in_wrong_clause=[True,False,True,True],swapped_depiction_clauses=[True,True,False,False],
        reversed_depiction=[True,True,False,False],obsolete_prospect=[True,True,False,True])
    for variant,wanted in expected.items():
        assert evaluate(doc,model(doc,variant))==[True]*22+wanted,variant
    new=deepcopy(doc);new['statements']=new['statements'][22:]
    assert evaluate(new,model(new),memo=False)==[True]*4
    # Vary each independent premise/report/background and depiction slot.
    for slot in range(6):
        bits=[True]*6;bits[slot]=False
        assert evaluate(new,model(new,bits=tuple(bits)),memo=False)==[False,True,True,True]
    for slot in range(3):
        bits=[True]*3;bits[slot]=False
        assert evaluate(new,model(new,depictions=tuple(bits)),memo=False)==[True,*bits]


def test_unknown_attributions_are_not_hidden_by_false_claims():
    doc=deepcopy(check.restored()['document']);doc['statements']=doc['statements'][22:]
    def unknown(*args):raise ValueError('Unspecified learning attribution')
    for name in ('uc','ud','ue','qa','hznreport','hzrbgreport','rbt'):
        with pytest.raises(ValueError,match='Unspecified learning attribution'):
            evaluate(doc,model(doc)|{check.mapping()[name]:unknown})
    with pytest.raises(ValueError,match='Unspecified learning attribution'):
        evaluate(doc,model(doc,bits=(False,True,True,True,True,True))|{check.mapping()['hzrbgreport']:unknown})


def test_whole_sentence_and_clause_references_use_actual_token_spans():
    doc=deepcopy(check.restored()['document']);m=check.mapping()
    doc['statements']=[dict(kind='ask',body=dict(kind='equal',arguments=[call(m[n]),call('jexpected')]))
        for n in ('hztz','fu','fv','g2')]
    doc['declarations'].append(dict(kind='primitive',name='jexpected',parameters=[],result='individual'))
    for index,target in enumerate(('contrast','low','learn','outcome')):
        expected=[False]*4;expected[index]=True
        assert evaluate(doc,model(doc)|{'jexpected':lambda target=target:target})==expected
    values=model(doc);name=check.vocabulary()._symbols['sentencetokenspanreference'];old=values[name]
    def wrong_span(document,first,a,last,b,context):
        return old(document,first,a+1 if first=='contrast' else a,last,b,context)
    with pytest.raises(ValueError,match='Unknown learning clause span'):
        evaluate(doc,values|{name:wrong_span,'jexpected':lambda:'low'})
