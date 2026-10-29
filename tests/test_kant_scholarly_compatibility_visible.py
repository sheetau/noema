"""Keep every presentation attached to the same conditional scholarly content."""
from copy import deepcopy
import json
import pytest
from noema.constructed_semantics import evaluate_document
from scripts import check_kant_scholarly_compatibility_visible as check
from scripts.shared_modality import call,renamed
from scripts.sentence_text_span_references import SentenceTextSpanReferences
import test_kant_office_obedience_visible as parent

REFERENCES={n:'scholarly-compatibility-'+n for n in ('h242i',)}
DOMAIN=parent.DOMAIN+tuple(REFERENCES.values())
SCENES=parent.SCENES
CONTEXT=parent.CONTEXT
ROOTS=('r32g',)

def evaluate(doc,values,memo=True):
    return [r['value'] for r in evaluate_document(doc,individuals=DOMAIN,situations=SCENES,
        primitives=values,max_steps=25000000,memoize_definitions=memo,memoize_expressions=memo)]

def expectations():
    q=lambda rank,name,kind='function_ref':('quote',rank,kind,name)
    return [('r32g','h236i',('h242i','wa',q(3,'r32f','call'),'h232o')),
        ('r32g','h236k',('h242i','wa','h242c',q(3,'r3n','call'),'h242i',q(3,'r32f','call'),q(0,'r2zg'),'h232o')),
        ('r32g','h242b',('h242i','wa',q(3,'r32f','call'),'h232o')),
        ('r32g','h242s',('h242i','wa',q(3,'r32f','call'),q(0,'r3r'),q(0,'r32h'),q(0,'r32i'),'h232o')),
        ('r32g','h242t',('h242i','wa',q(3,'r32f','call'),q(0,'r32b'),q(0,'r32c'),q(0,'r32d'),'h232o')),
        ('r32g','h242u',('h242i','wa',q(3,'r32f','call'),q(0,'r32b'),q(0,'r32e'),'h232o')),
        ('r32g','ue',('h242c','h242i','h232o'))]


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
            if name in {'h242s','h242t','h242u'} or any(isinstance(a,str) and a in REFERENCES.values() for a in args):return False
            return previous(*args)
        return relation
    for name in {n for _,n,_ in rows}:values[m[name]]=handler(name,values.get(m[name],lambda *args:False))
    return values

def selection(start=60):
    doc=deepcopy(check.restored()['document']);doc['statements']=doc['statements'][start:]
    return doc

def test_source_and_every_prior_declaration_are_preserved():
    doc=check.restored()['document'];old=check.previous.document()
    assert check.backprojection(doc)==check.source_excerpt()
    assert check.specialized_backprojection(doc)==check.specialized_source()
    assert doc['statements'][:60]==old['statements']
    ds={d['name']:d for d in doc['declarations']}
    assert all(ds[d['name']]==d for d in old['declarations'])
    assert (len(doc['declarations']),len(doc['statements']))==(1755,61)
    assert len(check.source_excerpt()['declarations'])==1724
    assert check.SOURCE_ORDER[-1:]==[77]
    current=selection(59);assert evaluate(current,model(current))==[True]*2

def test_attribution_role_contrast_emphasis_explanation_and_aspect_links_are_required():
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
        original=parent.parent.parent.parent.parent.calls(next(d for d in doc['declarations'] if d['name']==m[root])['body'],m[name])[occurrence]
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
            parent.parent.parent.parent.parent.calls(body,m[name])[occurrence]['arguments'][slot]=replacement
            assert evaluate(changed,model(changed))[ROOTS.index(root)] is False,(root,name,occurrence,slot)

def test_unknown_presentations_refused_and_quoted_policy_contents_not_executed():
    doc=selection();m=check.mapping()
    def unknown(*args):raise ValueError('Unspecified scholarly compatibility input')
    for name in {n for _,n,_ in expectations()}:
        with pytest.raises(ValueError,match='Unspecified scholarly compatibility'):evaluate(doc,model(doc)|{m[name]:unknown})
    values=model(doc)
    for name in set(check.profile.SOURCE_RELATIONS)-{n for _,n,_ in expectations()}:values[m[name]]=unknown
    assert evaluate(doc,values)==[True]

def test_whole_sentence_reference_is_exact_and_refuses_unknown_addresses():
    m=check.mapping();voc=check.vocabulary()
    assert check.names()['h242c']==check.previous.names()['h242c']
    doc=selection();doc['declarations'].append(dict(kind='primitive',name='jexpected',parameters=[],result='individual'))
    doc['statements']=[dict(kind='ask',body=dict(kind='equal',arguments=[call(m['h242i']),call('jexpected')]))]
    assert evaluate(doc,model(doc)|{'jexpected':lambda:REFERENCES['h242i']})==[True]
    assert evaluate(doc,model(doc)|{'jexpected':lambda:parent.REFERENCES['h242c']})==[False]
    for slot in (1,2):
        changed=deepcopy(doc);body=next(d for d in changed['declarations'] if d['name']==m['h242i'])['body']
        body['arguments'][slot]['numerator']=999
        with pytest.raises(ValueError):evaluate(changed,model(changed)|{'jexpected':lambda:REFERENCES['h242i']})
    changed=deepcopy(doc);body=next(d for d in changed['declarations'] if d['name']==m['h242i'])['body']
    body['arguments'][0]=call(m['wh'])
    with pytest.raises(ValueError):evaluate(changed,model(changed)|{'jexpected':lambda:REFERENCES['h242i']})
    def unknown(*args):raise ValueError('Unspecified scholarly reference')
    with pytest.raises(ValueError,match='Unspecified scholarly reference'):
        evaluate(doc,model(doc)|{'jexpected':lambda:REFERENCES['h242i'],voc._symbols['sentencereference']:unknown})


def test_inherited_description_wrapper_mutations_are_refused():
    doc=deepcopy(check.restored()['document']);m=check.mapping()
    next(d for d in doc['declarations'] if d['name']==m['h227c'])['body']['arguments'][0]=call(m['wh'])
    with pytest.raises(ValueError,match='Reused description wrapper differs'):check.backprojection(doc)
