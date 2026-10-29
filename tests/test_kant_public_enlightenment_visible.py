"""Keep public possibility, contrasting claims and paragraph contexts distinct."""
from copy import deepcopy
from fractions import Fraction
import json
import pytest
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import evaluate_document
from scripts import check_kant_public_enlightenment_visible as check
from scripts.shared_modality import call,renamed
import test_kant_self_development_visible as parent

REFERENCES={'hzp4':'public-sentence','h222t':'public-first','h222u':'public-second'}
DOMAIN=parent.DOMAIN+tuple(REFERENCES.values())
SMALL_DOMAIN=parent.SMALL_DOMAIN+tuple(REFERENCES.values())


def evaluate(doc,values,memo=True,domain=SMALL_DOMAIN):
    return [r['value'] for r in evaluate_document(doc,individuals=domain,
        situations=('body','closing','public-context','other'),primitives=values,max_steps=20000000,
        memoize_definitions=memo,memoize_expressions=memo)]


def model(doc,bits=(True,)*8):
    values=parent.model(doc);voc=check.vocabulary();m=check.mapping();inverse={v:k for k,v in m.items()}
    oldsentence=values[voc._symbols['sentencereference']]
    oldspan=values[voc._symbols['sentencetokenspanreference']];oldorder=values[m['ue']]
    def sentence(context,paragraph,index):
        if (context,paragraph,index)==('closing',4,1):return 'public-sentence'
        return oldsentence(context,paragraph,index)
    def span(document,first,a,last,b,context):
        if first=='public-sentence':
            if (document,last,context)==('document','public-sentence','closing'):
                if (a,b)==(1,10):return 'public-first'
                if (a,b)==(11,21):return 'public-second'
            raise ValueError('Unknown public sentence span')
        return oldspan(document,first,a,last,b,context)
    def paragraph(body,index):
        if (body,index)!=('body',4):raise ValueError('Unknown paragraph presentation')
        return 'public-context'
    def syntax(description,name,rank,kind='call'):
        return description.rank==rank and renamed(json.loads(description.syntax),inverse)==(
            call(name) if kind=='call' else dict(kind='function_ref',symbol=name))
    def claim(node,author,content,point):
        targets={'public-sentence':('r2lf',0),'public-first':('r2lj',2),'public-second':('r2ll',3)}
        if node not in targets:raise ValueError('Unknown ranked claim node')
        target,slot=targets[node]
        return bits[slot] and (author,point)==('author','public-context') and syntax(content,target,1)
    def contrast(node,author,first,left,last,right,aspect,point):
        return bits[4] and (node,author,first,last,point)==('public-sentence','author','emancipation','public-first','public-context') and syntax(left,'r2ec',1) and syntax(right,'r2lj',1) and syntax(aspect,'h4l',0,'function_ref')
    def strengthen(node,author,first,left,last,right,aspect,point):
        return bits[5] and (node,author,first,last,point)==('public-sentence','author','public-first','public-second','public-context') and syntax(left,'r2lj',1) and syntax(right,'r2ll',1) and syntax(aspect,'h4l',0,'function_ref')
    def sufficient(node,author,scope,condition,goal,qualification,point):
        return bits[6] and (node,author,point)==('public-second','author','public-context') and all(
            syntax(value,name,rank,'function_ref') for value,name,rank in (
                (scope,'h222e',0),(condition,'r2lm',1),(goal,'r2ln',1),(qualification,'r2lk',1)))
    def order(first,last,point):
        if last=='public-sentence':return bits[1] and (first,point)==('self-development','public-context')
        if last=='public-second':return bits[7] and (first,point)==('public-first','public-context')
        return oldorder(first,last,point)
    for name,fn in dict(sentencereference=sentence,sentencetokenspanreference=span,paragraphpresentationcontext=paragraph).items():
        values[voc._symbols[name]]=fn
    values.update({m[n]:fn for n,fn in dict(hzon=claim,h222q=contrast,h222r=strengthen,h222s=sufficient,ue=order).items()})
    return values


def new_statements():
    doc=deepcopy(check.restored()['document']);doc['statements']=doc['statements'][36:]
    return doc


def test_complete_source_and_prior_group_are_preserved():
    doc=check.restored()['document']
    assert check.backprojection(doc)==check.source_excerpt()
    assert check.specialized_backprojection(doc)==check.specialized_source()
    assert doc['statements'][:36]==check.previous.document()['statements']
    assert (len(doc['declarations']),len(doc['statements']))==(970,38)
    assert len(check.source_excerpt()['declarations'])==946
    assert evaluate(doc,model(doc),domain=DOMAIN)==[True]*38


def test_ranked_attributions_discourse_actions_and_order_are_independent():
    doc=new_statements()
    assert evaluate(doc,model(doc),memo=False)==[True,True]
    for slot in range(8):
        bits=[True]*8;bits[slot]=False
        assert evaluate(doc,model(doc,bits=bits))==[slot not in (0,1),slot not in range(2,8)],slot
    # The shared perspective is an opaque activity description, and all three
    # families in the sufficiency claim are retained, not executed as facts.
    for symbol,slots in [('h222q',[(2,4),(3,5)]),('h222r',[(2,4),(3,5)]),('h222s',[(3,4)])]:
        for left,right in slots:
            changed=deepcopy(doc);found=[]
            def visit(value):
                if isinstance(value,dict):
                    if value.get('kind')=='call' and value.get('symbol')==check.mapping()[symbol]:
                        args=value['arguments'];args[left],args[right]=args[right],args[left];found.append(True)
                    for child in value.values():visit(child)
                elif isinstance(value,list):
                    for child in value:visit(child)
            visit(next(d for d in changed['declarations'] if d['name']==check.mapping()['r2lo'])['body'])
            assert len(found)==1
            assert evaluate(normalize_document(changed),model(changed))==[True,False]


def test_unknown_discourse_inputs_are_not_false_and_content_is_opaque():
    doc=new_statements()
    def unknown(*args):raise ValueError('Unspecified public discourse relation')
    for name in ('hzon','h222q','h222r','h222s','ue'):
        with pytest.raises(ValueError,match='Unspecified public discourse'):
            evaluate(doc,model(doc)|{check.mapping()[name]:unknown})
    # All remaining new primitives keep the parent's throwing default. If a
    # quoted content is run during attribution, this positive case must fail.
    values=model(doc)
    for name in set(check.profile.SOURCE_RELATIONS)-{'hzon','h222q','h222r','h222s'}:
        values[check.mapping()[name]]=unknown
    assert evaluate(doc,values)==[True,True]


def test_sentence_clauses_and_paragraph_context_are_distinct():
    doc=new_statements();m=check.mapping()
    doc['declarations'].append(dict(kind='primitive',name='jexpected',parameters=[],result='individual'))
    doc['statements']=[dict(kind='ask',body=dict(kind='equal',arguments=[call(m[n]),call('jexpected')])) for n in REFERENCES]
    for index,target in enumerate(REFERENCES.values()):
        assert evaluate(doc,model(doc)|{'jexpected':lambda target=target:target})==[i==index for i in range(3)]
    context=new_statements()
    context['statements']=[dict(kind='ask',body=dict(kind='equal',arguments=[call(m['hzp3']),call(m[n])] )) for n in ('hzp3','wh','hzim')]
    assert evaluate(context,model(context))==[True,False,False]
    changed=new_statements()
    next(d for d in changed['declarations'] if d['name']==m['hzp3'])['body']=call(m['wh'])
    assert evaluate(changed,model(changed))==[False,False]
    changed=new_statements()
    next(d for d in changed['declarations'] if d['name']==m['h222u'])['body']=call(m['h222t'])
    assert evaluate(changed,model(changed))==[True,False]


def test_unknown_paragraph_and_span_references_are_rejected():
    doc=new_statements();m=check.mapping();voc=check.vocabulary()
    for index in (Fraction(0),Fraction(-1),Fraction(3,2),Fraction(3),Fraction(5)):
        changed=deepcopy(doc)
        next(d for d in changed['declarations'] if d['name']==m['hzp3'])['body']['arguments'][1]=dict(
            kind='number',numerator=index.numerator,denominator=index.denominator)
        with pytest.raises(ValueError,match='Unknown paragraph presentation'):evaluate(changed,model(changed))
    changed=deepcopy(doc)
    next(d for d in changed['declarations'] if d['name']==m['hzp3'])['body']['arguments'][0]=call(m['hzim'])
    with pytest.raises(ValueError,match='Unknown paragraph presentation'):evaluate(changed,model(changed))
    changed=deepcopy(doc)
    next(d for d in changed['declarations'] if d['name']==m['h222u'])['body']['arguments'][2]=check.num(10)
    with pytest.raises(ValueError,match='Unknown public sentence span'):evaluate(changed,model(changed))
    def unknown(*args):raise ValueError('Unspecified public reference')
    for name in ('paragraphpresentationcontext','sentencereference','sentencetokenspanreference'):
        with pytest.raises(ValueError,match='Unspecified public reference'):
            evaluate(doc,model(doc)|{voc._symbols[name]:unknown})
