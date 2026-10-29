"""Keep explicit definitions and their term mentions bound to the same prior answer."""
from copy import deepcopy
import json
import pytest
from noema.constructed_semantics import evaluate_document
from scripts import check_kant_use_definitions_visible as check
from scripts.shared_modality import call,renamed
from scripts.sentence_text_span_references import SentenceTextSpanReferences
import test_kant_answer_discourse_visible as parent

REFERENCES={n:'use-definitions-'+n for n in ('h236p','h236q','h236r','h236s')}
DOMAIN=parent.DOMAIN+tuple(REFERENCES.values())
SCENES=parent.SCENES
CONTEXT=parent.CONTEXT
ROOTS=('r2zk','r2zl')

def evaluate(doc,values,memo=True):
    return [r['value'] for r in evaluate_document(doc,individuals=DOMAIN,situations=SCENES,
        primitives=values,max_steps=25000000,memoize_definitions=memo,memoize_expressions=memo)]

def expectations():
    q=lambda rank,name,kind='function_ref':('quote',rank,kind,name)
    return [('r2zk','h236o',('h236r','wa','h236p',q(0,'r2zi'),'h232o')),
        ('r2zk','h236u',('h236r','wa','h235p',q(3,'r2zf','call'),'h236p',q(0,'r2zi'),'h232o')),
        ('r2zk','h236v',('h236r','wa',q(0,'r2zi'),q(0,'r2zm'),'h232o')),
        ('r2zk','ue',('h235p','h236r','h232o')),
        ('r2zl','h236o',('h236s','wa','h236q',q(0,'r2zj'),'h232o')),
        ('r2zl','h236t',('h236s','wa',q(0,'r2zj'),q(0,'cf'),'h232o')),
        ('r2zl','ue',('h236r','h236s','h232o'))]


def model(doc,omitted=None,seen=None):
    values=parent.model(doc);voc=check.vocabulary();m=check.mapping();inverse={v:k for k,v in m.items()}
    anchors=check.read(check.ANCHORS)
    oldspan=values[voc._symbols['sentencetextspanreference']];oldsentence=values[voc._symbols['sentencereference']]
    def sentence(context,paragraph,index):
        for n,where in anchors['source_nodes'].items():
            if (context,paragraph,index)==('closing',*where):return REFERENCES[n]
        return oldsentence(context,paragraph,index)
    refs=SentenceTextSpanReferences({('document',REFERENCES[n],'closing'):r['text'] for n,r in anchors['texts'].items()},
        {('document',REFERENCES[row['sentence_reference']],row['first_character'],row['past_last_character'],'closing'):REFERENCES[n]
         for n,row in anchors['source_character_spans'].items()})
    def span(document,sentence,first,last,context):
        if sentence in (REFERENCES['h236r'],REFERENCES['h236s']):return refs.span(document,sentence,first,last,context)
        return oldspan(document,sentence,first,last,context)
    values[voc._symbols['sentencereference']]=sentence
    values[voc._symbols['sentencetextspanreference']]=span
    labels={v:k for k,v in (parent.parent.REFERENCES|REFERENCES).items()}|{'author':'wa',CONTEXT:'h232o'}
    rows=expectations();expected=[(n,args) for _,n,args in rows]
    def normalized(value):
        if isinstance(value,str):return labels.get(value,value)
        if hasattr(value,'syntax'):
            code=renamed(json.loads(value.syntax),inverse)
            return ('quote',value.rank,code['kind'],code['symbol'])
        raise AssertionError(type(value))
    def handler(name,previous):
        def relation(*args):
            row=(name,tuple(normalized(a) for a in args))
            if row in expected:
                if seen is not None:seen.update(i for i,r in enumerate(expected) if r==row)
                return omitted is None or expected[omitted]!=row
            if name in {'h236o','h236t','h236u','h236v'} or any(isinstance(a,str) and a in REFERENCES.values() for a in args):return False
            return previous(*args)
        return relation
    for name in {n for _,n,_ in rows}:values[m[name]]=handler(name,values.get(m[name],lambda *args:False))
    return values

def selection(start=56):
    doc=deepcopy(check.restored()['document']);doc['statements']=doc['statements'][start:]
    return doc

def test_source_and_every_prior_declaration_are_preserved():
    doc=check.restored()['document'];old=check.previous.document()
    assert check.backprojection(doc)==check.source_excerpt()
    assert check.specialized_backprojection(doc)==check.specialized_source()
    assert doc['statements'][:56]==old['statements']
    ds={d['name']:d for d in doc['declarations']}
    assert all(ds[d['name']]==d for d in old['declarations'])
    assert (len(doc['declarations']),len(doc['statements']))==(1660,58)
    assert len(check.source_excerpt()['declarations'])==1629
    assert check.SOURCE_ORDER[-2:]==[73,74]
    current=selection(52);assert evaluate(current,model(current))==[True]*6

def test_every_attribution_contrast_concession_and_answer_link_is_required():
    doc=selection();seen=set();assert evaluate(doc,model(doc,seen=seen),memo=False)==[True]*2
    rows=expectations();assert seen==set(range(len(rows)))
    for index,(_,name,args) in enumerate(rows):
        expected=[not any(root==r and (n,a)==(name,args) for r,n,a in rows) for root in ROOTS]
        assert evaluate(doc,model(doc,omitted=index))==expected,(index,name)

def test_each_relation_argument_is_bound():
    doc=selection();m=check.mapping();occurrences={}
    substitutions={n:'h234o' for n in REFERENCES|parent.parent.REFERENCES}
    substitutions.update(wa='h234o',h232o='hzp3')
    for root,name,_ in expectations():
        occurrence=occurrences.get((root,name),0);occurrences[root,name]=occurrence+1
        original=parent.parent.calls(next(d for d in doc['declarations'] if d['name']==m[root])['body'],m[name])[occurrence]
        for slot,arg in enumerate(original['arguments']):
            changed=deepcopy(doc);body=next(d for d in changed['declarations'] if d['name']==m[root])['body']
            if arg['kind']=='quote':
                target=arg['body']['symbol']
                declaration=next(d for d in doc['declarations'] if d['name']==target)
                changed['declarations'].insert(0,dict(kind='primitive',name='jmutation',
                    parameters=[deepcopy(p['sort']) if declaration['kind']=='definition' else deepcopy(p) for p in declaration['parameters']],result=deepcopy(declaration['result'])))
                replacement=renamed(arg,{target:'jmutation'})
            else:replacement=renamed(arg,{m[a]:m[b] for a,b in substitutions.items()})
            assert replacement!=arg,(root,name,slot)
            parent.parent.calls(body,m[name])[occurrence]['arguments'][slot]=replacement
            assert evaluate(changed,model(changed))[ROOTS.index(root)] is False,(root,name,occurrence,slot)

def test_unknown_presentations_refused_and_quoted_policy_contents_not_executed():
    doc=selection();m=check.mapping()
    def unknown(*args):raise ValueError('Unspecified use definitions input')
    for name in {n for _,n,_ in expectations()}:
        with pytest.raises(ValueError,match='Unspecified use definitions'):evaluate(doc,model(doc)|{m[name]:unknown})
    values=model(doc)
    for name in set(check.profile.SOURCE_RELATIONS)-{n for _,n,_ in expectations()}:values[m[name]]=unknown
    assert evaluate(doc,values)==[True]*2

def test_two_sentences_and_two_term_mentions_are_exact_and_refuse_unknown_addresses():
    m=check.mapping();voc=check.vocabulary();anchors=check.read(check.ANCHORS)
    assert check.names()['h235p']==check.previous.names()['h235p']
    for name,expected in REFERENCES.items():
        doc=selection();doc['declarations'].append(dict(kind='primitive',name='jexpected',parameters=[],result='individual'))
        doc['statements']=[dict(kind='ask',body=dict(kind='equal',arguments=[call(m[name]),call('jexpected')]))]
        assert evaluate(doc,model(doc)|{'jexpected':lambda:expected})==[True]
        assert evaluate(doc,model(doc)|{'jexpected':lambda:parent.parent.REFERENCES['h235p']})==[False]
        changed=deepcopy(doc);body=next(d for d in changed['declarations'] if d['name']==m[name])['body']
        body['arguments'][2]['numerator']=999
        with pytest.raises(ValueError):evaluate(changed,model(changed)|{'jexpected':lambda:expected})
        if name in anchors['source_character_spans']:
            for slot,other in ((0,'wh'),(1,'h235p'),(4,'h232o')):
                changed=deepcopy(doc);body=next(d for d in changed['declarations'] if d['name']==m[name])['body']
                body['arguments'][slot]=call(m[other])
                with pytest.raises(ValueError):evaluate(changed,model(changed)|{'jexpected':lambda:expected})
    for operation in ('sentencereference','sentencetextspanreference'):
        def unknown(*args):raise ValueError('Unspecified definition reference')
        target='h236p';doc=selection();doc['statements']=[dict(kind='ask',body=dict(kind='equal',arguments=[call(m[target]),call(m[target])]))]
        with pytest.raises(ValueError,match='Unspecified definition reference'):
            evaluate(doc,model(doc)|{voc._symbols[operation]:unknown})


def test_inherited_description_wrapper_mutations_are_refused():
    doc=deepcopy(check.restored()['document']);m=check.mapping()
    next(d for d in doc['declarations'] if d['name']==m['h227c'])['body']['arguments'][0]=call(m['wh'])
    with pytest.raises(ValueError,match='Reused description wrapper differs'):check.backprojection(doc)
