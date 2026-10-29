"""Preserve whole mechanism sentence, ranked purposes and same prior definition."""
from copy import deepcopy
import json
import pytest
from noema.constructed_semantics import evaluate_document
from scripts import check_kant_public_purpose_mechanism_visible as check
from scripts.shared_modality import call,renamed
from scripts.sentence_text_span_references import SentenceTextSpanReferences
import test_kant_use_definitions_visible as parent

REFERENCES={n:'public-purpose-mechanism-'+n for n in ('h237w',)}
DOMAIN=parent.DOMAIN+tuple(REFERENCES.values())
SCENES=parent.SCENES
CONTEXT=parent.CONTEXT
ROOTS=('r3g',)

def evaluate(doc,values,memo=True):
    return [r['value'] for r in evaluate_document(doc,individuals=DOMAIN,situations=SCENES,
        primitives=values,max_steps=25000000,memoize_definitions=memo,memoize_expressions=memo)]

def expectations():
    q=lambda rank,name,kind='function_ref':('quote',rank,kind,name)
    return [('r3g','h236i',('h237w','wa',q(3,'r3d','call'),'h232o')),
        ('r3g','h237v',('h237w','wa',q(1,'r3a'),q(1,'r3e'),q(1,'r3f'),'h232o')),
        ('r3g','uf',('wa','h236s','h237w','h232o')),
        ('r3g','ue',('h236s','h237w','h232o'))]


def model(doc,omitted=None,seen=None):
    values=parent.model(doc);voc=check.vocabulary();m=check.mapping();inverse={v:k for k,v in m.items()}
    anchors=check.read(check.ANCHORS)
    oldsentence=values[voc._symbols['sentencereference']]
    def sentence(context,paragraph,index):
        for n,where in anchors['source_nodes'].items():
            if (context,paragraph,index)==('closing',*where):return REFERENCES[n]
        return oldsentence(context,paragraph,index)
    values[voc._symbols['sentencereference']]=sentence
    labels={v:k for k,v in (parent.REFERENCES|REFERENCES).items()}|{'author':'wa',CONTEXT:'h232o'}
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
            if name in {'h237v'} or any(isinstance(a,str) and a in REFERENCES.values() for a in args):return False
            return previous(*args)
        return relation
    for name in {n for _,n,_ in rows}:values[m[name]]=handler(name,values.get(m[name],lambda *args:False))
    return values

def selection(start=58):
    doc=deepcopy(check.restored()['document']);doc['statements']=doc['statements'][start:]
    return doc

def test_source_and_every_prior_declaration_are_preserved():
    doc=check.restored()['document'];old=check.previous.document()
    assert check.backprojection(doc)==check.source_excerpt()
    assert check.specialized_backprojection(doc)==check.specialized_source()
    assert doc['statements'][:58]==old['statements']
    ds={d['name']:d for d in doc['declarations']}
    assert all(ds[d['name']]==d for d in old['declarations'])
    assert (len(doc['declarations']),len(doc['statements']))==(1704,59)
    assert len(check.source_excerpt()['declarations'])==1673
    assert check.SOURCE_ORDER[-1:]==[75]
    current=selection(56);assert evaluate(current,model(current))==[True]*3

def test_attribution_per_person_fallback_and_prior_definition_links_are_required():
    doc=selection();seen=set();assert evaluate(doc,model(doc,seen=seen),memo=False)==[True]
    rows=expectations();assert seen==set(range(len(rows)))
    for index,(_,name,args) in enumerate(rows):
        expected=[not any(root==r and (n,a)==(name,args) for r,n,a in rows) for root in ROOTS]
        assert evaluate(doc,model(doc,omitted=index))==expected,(index,name)

def test_each_relation_argument_is_bound():
    doc=selection();m=check.mapping();occurrences={}
    substitutions={n:'h234o' for n in REFERENCES|parent.REFERENCES}
    substitutions.update(wa='h234o',h232o='hzp3')
    for root,name,_ in expectations():
        occurrence=occurrences.get((root,name),0);occurrences[root,name]=occurrence+1
        original=parent.parent.parent.calls(next(d for d in doc['declarations'] if d['name']==m[root])['body'],m[name])[occurrence]
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
            parent.parent.parent.calls(body,m[name])[occurrence]['arguments'][slot]=replacement
            assert evaluate(changed,model(changed))[ROOTS.index(root)] is False,(root,name,occurrence,slot)

def test_unknown_presentations_refused_and_quoted_policy_contents_not_executed():
    doc=selection();m=check.mapping()
    def unknown(*args):raise ValueError('Unspecified public purpose mechanism input')
    for name in {n for _,n,_ in expectations()}:
        with pytest.raises(ValueError,match='Unspecified public purpose mechanism'):evaluate(doc,model(doc)|{m[name]:unknown})
    values=model(doc)
    for name in set(check.profile.SOURCE_RELATIONS)-{n for _,n,_ in expectations()}:values[m[name]]=unknown
    assert evaluate(doc,values)==[True]

def test_whole_sentence_reference_is_exact_and_refuses_unknown_addresses():
    m=check.mapping();voc=check.vocabulary()
    assert check.names()['h236s']==check.previous.names()['h236s']
    doc=selection();doc['declarations'].append(dict(kind='primitive',name='jexpected',parameters=[],result='individual'))
    doc['statements']=[dict(kind='ask',body=dict(kind='equal',arguments=[call(m['h237w']),call('jexpected')]))]
    assert evaluate(doc,model(doc)|{'jexpected':lambda:REFERENCES['h237w']})==[True]
    assert evaluate(doc,model(doc)|{'jexpected':lambda:parent.REFERENCES['h236s']})==[False]
    for slot in (1,2):
        changed=deepcopy(doc);body=next(d for d in changed['declarations'] if d['name']==m['h237w'])['body']
        body['arguments'][slot]['numerator']=999
        with pytest.raises(ValueError):evaluate(changed,model(changed)|{'jexpected':lambda:REFERENCES['h237w']})
    changed=deepcopy(doc);body=next(d for d in changed['declarations'] if d['name']==m['h237w'])['body']
    body['arguments'][0]=call(m['wh'])
    with pytest.raises(ValueError):evaluate(changed,model(changed)|{'jexpected':lambda:REFERENCES['h237w']})
    def unknown(*args):raise ValueError('Unspecified mechanism reference')
    with pytest.raises(ValueError,match='Unspecified mechanism reference'):
        evaluate(doc,model(doc)|{'jexpected':lambda:REFERENCES['h237w'],voc._symbols['sentencereference']:unknown})


def test_inherited_description_wrapper_mutations_are_refused():
    doc=deepcopy(check.restored()['document']);m=check.mapping()
    next(d for d in doc['declarations'] if d['name']==m['h227c'])['body']['arguments'][0]=call(m['wh'])
    with pytest.raises(ValueError,match='Reused description wrapper differs'):check.backprojection(doc)
