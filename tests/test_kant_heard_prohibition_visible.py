"""Keep the reported command, narrated scene and presentation context separate."""
from copy import deepcopy
import json
import pytest
from noema.constructed_semantics import evaluate_document
from scripts import check_kant_heard_prohibition_visible as check
from scripts.shared_modality import call,renamed
import test_kant_enlightenment_requirement_visible as parent

WHOLE='heard-prohibition-sentence'
SCENE='heard-prohibition-now'
DOMAIN=parent.SMALL_DOMAIN+(WHOLE,)
SCENES=('body','closing','public-context',parent.CONTEXT,SCENE,'other')


def evaluate(doc,values,memo=True):
    return [r['value'] for r in evaluate_document(doc,individuals=DOMAIN,situations=SCENES,
        primitives=values,max_steps=25000000,memoize_definitions=memo,memoize_expressions=memo)]


def model(doc,bits=(True,True,True),variant='baseline'):
    values=parent.model(doc);voc=check.vocabulary();m=check.mapping();inverse={v:k for k,v in m.items()}
    oldsentence=values[voc._symbols['sentencereference']]
    oldclaim,oldcontrast,oldorder=[values[m[n]] for n in ('hzon','h222q','ue')]
    first=parent.REFERENCES['h232h']
    def sentence(context,paragraph,index):
        if (context,paragraph,index)==('closing',5,2):return WHOLE
        return oldsentence(context,paragraph,index)
    def scene(context,address):
        if (context,address)!=(WHOLE,0):raise ValueError('Unknown narrated scene reference')
        return SCENE
    def syntax(description,name,rank=1,kind='call'):
        return description.rank==rank and renamed(json.loads(description.syntax),inverse)==(
            call(name) if kind=='call' else dict(kind='function_ref',symbol=name))
    def claim(node,author,content,context):
        if node!=WHOLE:return oldclaim(node,author,content,context)
        return bits[0] and (author,context)==('author',parent.CONTEXT) and syntax(content,'r2ss' if variant=='wrong_claim' else 'r2te')
    def contrast(node,author,left,c1,right,c2,axis,context):
        if node!=WHOLE:return oldcontrast(node,author,left,c1,right,c2,axis,context)
        pair=(WHOLE,first) if variant=='reverse_contrast' else (first,WHOLE)
        return bits[1] and (author,left,right,context)==('author',*pair,parent.CONTEXT) and syntax(c1,'r2ss') and syntax(c2,'r2te') and syntax(axis,'h4l',0,'function_ref')
    def order(left,right,context):
        if WHOLE not in (left,right):return oldorder(left,right,context)
        pair=(WHOLE,first) if variant=='reverse_order' else (first,WHOLE)
        return bits[2] and (left,right)==pair and context==parent.CONTEXT
    values[voc._symbols['sentencereference']]=sentence;values[voc._symbols['situationslot']]=scene
    values.update({m[n]:fn for n,fn in dict(hzon=claim,h222q=contrast,ue=order).items()})
    return values


def selection(start=44):
    doc=deepcopy(check.restored()['document']);doc['statements']=doc['statements'][start:]
    return doc


def test_source_and_unchanged_prior_selection_are_preserved():
    doc=check.restored()['document'];old=check.previous.document()
    assert check.backprojection(doc)==check.source_excerpt()
    assert check.specialized_backprojection(doc)==check.specialized_source()
    assert doc['statements'][:44]==old['statements']
    declarations={d['name']:d for d in doc['declarations']}
    assert all(declarations[d['name']]==d for d in old['declarations'])
    assert len(doc['statements'])==45 and len(check.source_excerpt()['declarations'])==1361
    # Recheck the cross-sentence connection without expanding unrelated older
    # tuple domains; their exact statements and dependencies are unchanged.
    current=selection(43)
    assert evaluate(current,model(current))==[True,True]


def test_each_claim_contrast_and_order_is_required():
    doc=selection()
    assert evaluate(doc,model(doc),memo=False)==[True]
    for slot in range(3):
        bits=[True]*3;bits[slot]=False
        assert evaluate(doc,model(doc,bits=bits))==[False]
    for variant in ('wrong_claim','reverse_contrast','reverse_order'):
        assert evaluate(doc,model(doc,variant=variant))==[False]


def test_unknown_presentations_refused_and_quoted_commands_unexecuted():
    doc=selection();m=check.mapping();voc=check.vocabulary()
    def unknown(*args):raise ValueError('Unspecified heard prohibition input')
    for name in ('hzon','h222q','ue'):
        with pytest.raises(ValueError,match='Unspecified heard prohibition'):evaluate(doc,model(doc)|{m[name]:unknown})
    values=model(doc)
    for name in check.profile.SOURCE_RELATIONS:values[m[name]]=unknown
    values[voc._symbols['situationslot']]=unknown
    assert evaluate(doc,values)==[True]


def test_narrated_scene_reference_has_exact_sentence_and_address():
    doc=selection();m=check.mapping();voc=check.vocabulary()
    doc['declarations'].append(dict(kind='primitive',name='jexpected',parameters=[],result='situation'))
    doc['statements']=[dict(kind='ask',body=dict(kind='equal',arguments=[call(m['h232v']),call('jexpected')]))]
    for point in SCENES:
        assert evaluate(doc,model(doc)|{'jexpected':lambda point=point:point})==[point==SCENE]
    for slot,value in ((0,call(m['h232h'])),(1,check.num(1))):
        changed=deepcopy(doc)
        next(d for d in changed['declarations'] if d['name']==m['h232v'])['body']['arguments'][slot]=value
        with pytest.raises(ValueError,match='Unknown narrated scene'):evaluate(changed,model(changed)|{'jexpected':lambda:SCENE})
    def unknown(*args):raise ValueError('Unknown narrated scene reference')
    with pytest.raises(ValueError,match='Unknown narrated scene'):
        evaluate(doc,model(doc)|{voc._symbols['situationslot']:unknown,'jexpected':lambda:SCENE})


def test_sentence_and_paragraph_context_cannot_be_replaced():
    doc=selection();m=check.mapping()
    for owner,other in (('h232w','h232h'),('h232o','hzp3')):
        changed=deepcopy(doc)
        next(d for d in changed['declarations'] if d['name']==m[owner])['body']=call(m[other])
        assert evaluate(changed,model(changed))==[False]
    changed=deepcopy(doc)
    d=next(d for d in changed['declarations'] if d['name']==m['r2tf'])
    d['body']=renamed(d['body'],{m['h232o']:m['h232v']})
    assert evaluate(changed,model(changed))==[False]
    def unknown(*args):raise ValueError('Unknown heard reference')
    for name in ('sentencereference','paragraphpresentationcontext'):
        with pytest.raises(ValueError,match='Unknown heard reference'):
            evaluate(doc,model(doc)|{check.vocabulary()._symbols[name]:unknown})


def test_inherited_wrapper_mutation_is_rejected():
    doc=deepcopy(check.restored()['document']);m=check.mapping()
    next(d for d in doc['declarations'] if d['name']==m['h227c'])['body']['arguments'][0]=call(m['wh'])
    with pytest.raises(ValueError,match='Reused description wrapper differs'):check.backprojection(doc)
