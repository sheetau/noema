"""Preserve fourth-sentence attribution, exact grounds and inherited scope."""
from copy import deepcopy
import json
import pytest
from noema.constructed_semantics import evaluate_document
from scripts import check_kant_public_slow_attainment_visible as check
from scripts.shared_modality import call,renamed
import test_kant_public_reversal_visible as parent

WHOLE='slow-attainment-sentence'
DOMAIN=parent.DOMAIN+(WHOLE,)
SMALL_DOMAIN=parent.SMALL_DOMAIN+(WHOLE,)

def evaluate(doc,values,memo=True,domain=SMALL_DOMAIN):
    return [r['value'] for r in evaluate_document(doc,individuals=domain,
        situations=('body','closing','public-context','other'),primitives=values,max_steps=25000000,
        memoize_definitions=memo,memoize_expressions=memo)]

def model(doc,variant='baseline',bits=(True,)*5):
    values=parent.model(doc);voc=check.vocabulary();m=check.mapping();inverse={v:k for k,v in m.items()}
    oldsentence=values[voc._symbols['sentencereference']]
    oldreport,oldreason,oldorder=[values[m[n]] for n in ('hznreport','ud','ue')]
    grounds=tuple(parent.REFERENCES[n] for n in ('h224m','h225s','h225o'))
    def sentence(context,paragraph,index):
        if (context,paragraph,index)==('closing',4,4):return WHOLE
        return oldsentence(context,paragraph,index)
    def report(node,author,description,scope,point):
        if node==WHOLE:
            return bits[0] and (author,scope,point)==('author',WHOLE,'public-context') and description.rank==3 and renamed(json.loads(description.syntax),inverse)==call('r2pt')
        return oldreport(node,author,description,scope,point)
    def reason(author,premises,node,point):
        if node==WHOLE:
            expected=set(grounds)
            if variant=='missing_ground':expected.remove(grounds[0])
            if variant=='extra_ground':expected.add('public-sentence')
            return bits[1] and (author,point)==('author','public-context') and {n for n in SMALL_DOMAIN if premises(n)}==expected
        return oldreason(author,premises,node,point)
    def order(first,last,point):
        if last==WHOLE:
            return first in grounds and point=='public-context' and bits[2+grounds.index(first)] and variant!='reversed_order'
        return oldorder(first,last,point)
    values[voc._symbols['sentencereference']]=sentence
    values.update({m[n]:fn for n,fn in dict(hznreport=report,ud=reason,ue=order).items()})
    return values

def new_statement():
    doc=deepcopy(check.restored()['document']);doc['statements']=doc['statements'][40:]
    return doc

def test_complete_source_and_previous_group_are_preserved():
    doc=check.restored()['document']
    assert check.backprojection(doc)==check.source_excerpt()
    assert check.specialized_backprojection(doc)==check.specialized_source()
    assert doc['statements'][:40]==check.previous.document()['statements']
    assert (len(doc['declarations']),len(doc['statements']))==(1243,41)
    assert len(check.source_excerpt()['declarations'])==1217
    assert evaluate(doc,model(doc),domain=DOMAIN)==[True]*41

def test_attribution_each_ground_and_each_order_are_required():
    doc=new_statement()
    assert evaluate(doc,model(doc),memo=False)==[True]
    for slot in range(5):
        bits=[True]*5;bits[slot]=False
        assert evaluate(doc,model(doc,bits=bits))==[False],slot
    for variant in ('missing_ground','extra_ground','reversed_order'):
        assert evaluate(doc,model(doc,variant))==[False],variant
    for other in ('h226h','hzp4'):
        changed=deepcopy(doc)
        body=next(d for d in changed['declarations'] if d['name']==check.mapping()['r2pv'])['body']
        body['arguments'][0]['items'][0]=call(check.mapping()[other])
        assert evaluate(changed,model(changed))==[False]

def test_unknown_presentations_are_refused_without_executing_world_claims():
    doc=new_statement()
    def unknown(*args):raise ValueError('Unspecified slow-attainment relation')
    for name in ('hznreport','ud','ue'):
        with pytest.raises(ValueError,match='Unspecified slow-attainment'):
            evaluate(doc,model(doc)|{check.mapping()[name]:unknown})
    values=model(doc)
    for name in check.profile.SOURCE_RELATIONS:values[check.mapping()[name]]=unknown
    assert evaluate(doc,values)==[True]
    with pytest.raises(ValueError,match='Unspecified slow-attainment'):
        evaluate(doc,model(doc,bits=(False,True,True,True,True))|{check.mapping()['ud']:unknown})

def test_exact_sentence_reference_and_inherited_context_are_required():
    doc=new_statement();m=check.mapping()
    for owner,other in (('h226h','hzp5'),('hzp3','wh')):
        changed=deepcopy(doc)
        next(d for d in changed['declarations'] if d['name']==m[owner])['body']=call(m[other])
        assert evaluate(changed,model(changed))==[False]
    changed=deepcopy(doc)
    args=next(d for d in changed['declarations'] if d['name']==m['r2pu'])['body']['arguments']
    args[3]=call(m['hzp4'])
    assert evaluate(changed,model(changed))==[False]

def test_unknown_sentence_and_context_inputs_are_refused():
    doc=new_statement();voc=check.vocabulary()
    def unknown(*args):raise ValueError('Unspecified slow-attainment reference')
    for name in ('sentencereference','paragraphpresentationcontext'):
        with pytest.raises(ValueError,match='Unspecified slow-attainment reference'):
            evaluate(doc,model(doc)|{voc._symbols[name]:unknown})
