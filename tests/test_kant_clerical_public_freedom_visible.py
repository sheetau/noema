"""Preserve scholarly freedom, calling, shared infinitive and prior-duty contrast."""
from copy import deepcopy
import json
import pytest
from noema.constructed_semantics import evaluate_document
from scripts import check_kant_clerical_public_freedom_visible as check
from scripts.shared_modality import call,renamed
from scripts.sentence_text_span_references import SentenceTextSpanReferences
import test_kant_clerical_obligation_visible as parent

REFERENCES={n:'clerical-public-freedom-'+n for n in ('h247e','h247f','h247g')}
DOMAIN=parent.DOMAIN+tuple(REFERENCES.values())
SCENES=parent.SCENES
CONTEXT=parent.CONTEXT
ROOTS=('r37q',)

def evaluate(doc,values,memo=True):
    return [r['value'] for r in evaluate_document(doc,individuals=DOMAIN,situations=SCENES,
        primitives=values,max_steps=25000000,memoize_definitions=memo,memoize_expressions=memo)]

def expectations():
    q=lambda name:('quote',3,'call',name)
    return [('r37q','h236i',(node,'wa',q(content),'h232o')) for node,content in
        [('h247e','r37o'),('h247f','r37m'),('h247g','r37n')]]+[
        ('r37q','h245k',('h247e','wa','h247f',q('r37m'),'h247g',q('r37n'),q('r37p'),'h232o')),
        ('r37q','h236k',('h247e','wa','h246q',q('r36k'),'h247e',q('r37o'),('quote',0,'function_ref','r2zg'),'h232o')),
        ('r37q','ue',('h246q','h247e','h232o')),
        ('r37q','ue',('h247f','h247g','h232o'))]


def calls(node,symbol):
    if isinstance(node,list):return [row for child in node for row in calls(child,symbol)]
    if not isinstance(node,dict):return []
    return ([node] if node.get('kind')=='call' and node.get('symbol')==symbol else [])+[row for child in node.values() for row in calls(child,symbol)]


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
        if sentence==REFERENCES['h247e']:return refs.span(document,sentence,first,last,context)
        return oldspan(document,sentence,first,last,context)
    values[voc._symbols['sentencetextspanreference']]=span
    values[voc._symbols['sentencereference']]=sentence
    labels={v:k for k,v in (parent.parent.REFERENCES|parent.REFERENCES|REFERENCES).items()}|{'author':'wa',CONTEXT:'h232o'}
    rows=expectations();expected=[(n,args) for _,n,args in rows]
    def normalized(value):
        if isinstance(value,str):return labels.get(value,value)
        if isinstance(value,tuple):return tuple(normalized(v) for v in value)
        if hasattr(value,'syntax'):
            code=renamed(json.loads(value.syntax),inverse)
            return ('quote',value.rank,code['kind'],code['symbol'])
        raise AssertionError(type(value))
    def handler(name,previous):
        def relation(*args):
            converted=(args[0],tuple(p for p in DOMAIN if args[1](p)),*args[2:]) if name=='ud' else args
            row=(name,tuple(normalized(a) for a in converted))
            if row in expected:
                if seen is not None:seen.update(i for i,r in enumerate(expected) if r==row)
                return omitted is None or expected[omitted]!=row
            if any(isinstance(a,str) and a in REFERENCES.values() for a in args):return False
            if name=='ud' and any(p in REFERENCES.values() for p in converted[1]):return False
            if name in {'h245k','h236k'}:
                raise ValueError('Unspecified clerical public freedom presentation')
            return previous(*args)
        return relation
    for name in {n for _,n,_ in rows}:values[m[name]]=handler(name,values.get(m[name],lambda *args:False))
    return values

def selection(start=66):
    doc=deepcopy(check.restored()['document']);doc['statements']=doc['statements'][start:]
    return doc

def test_source_and_every_prior_declaration_are_preserved():
    doc=check.restored()['document'];old=check.previous.document()
    assert check.backprojection(doc)==check.source_excerpt()
    assert check.specialized_backprojection(doc)==check.specialized_source()
    assert doc['statements'][:66]==old['statements']
    ds={d['name']:d for d in doc['declarations']}
    assert all(ds[d['name']]==d for d in old['declarations'])
    assert (len(doc['declarations']),len(doc['statements']))==(2041,67)
    assert len(check.source_excerpt()['declarations'])==2010
    assert check.SOURCE_ORDER[-1:]==[83]
    current=selection(65);assert evaluate(current,model(current))==[True]*2

def test_whole_clause_attribution_focus_contrast_and_order_are_required():
    doc=selection();seen=set();assert evaluate(doc,model(doc,seen=seen),memo=False)==[True]
    rows=expectations();assert seen==set(range(len(rows)))
    for index,(_,name,args) in enumerate(rows):
        expected=[not any(root==r and (n,a)==(name,args) for r,n,a in rows) for root in ROOTS]
        assert evaluate(doc,model(doc,omitted=index))==expected,(index,name)

def test_each_relation_argument_is_bound():
    doc=selection();m=check.mapping();occurrences={}
    substitutions={n:'h234o' for n in REFERENCES|parent.REFERENCES|parent.parent.REFERENCES}
    substitutions.update(wa='h234o',h232o='hzp3')
    for root,name,_ in expectations():
        occurrence=occurrences.get((root,name),0);occurrences[root,name]=occurrence+1
        original=calls(next(d for d in doc['declarations'] if d['name']==m[root])['body'],m[name])[occurrence]
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
            calls(body,m[name])[occurrence]['arguments'][slot]=replacement
            assert evaluate(changed,model(changed))[ROOTS.index(root)] is False,(root,name,occurrence,slot)


def test_unknown_presentations_refused_and_quoted_policy_contents_not_executed():
    doc=selection();m=check.mapping()
    def unknown(*args):raise ValueError('Unspecified clerical public freedom input')
    for name in {n for _,n,_ in expectations()}:
        with pytest.raises(ValueError,match='Unspecified clerical public freedom'):evaluate(doc,model(doc)|{m[name]:unknown})
    values=model(doc)
    for name in set(check.profile.SOURCE_RELATIONS)-{n for _,n,_ in expectations()}:values[m[name]]=unknown
    assert evaluate(doc,values)==[True]

def test_whole_sentence_reference_is_exact_and_refuses_unknown_addresses():
    m=check.mapping();voc=check.vocabulary()
    assert check.names()['h246q']==check.previous.names()['h246q']
    doc=selection();doc['declarations'].append(dict(kind='primitive',name='jexpected',parameters=[],result='individual'))
    doc['statements']=[dict(kind='ask',body=dict(kind='equal',arguments=[call(m['h247e']),call('jexpected')]))]
    assert evaluate(doc,model(doc)|{'jexpected':lambda:REFERENCES['h247e']})==[True]
    assert evaluate(doc,model(doc)|{'jexpected':lambda:parent.REFERENCES['h246q']})==[False]
    for slot in (1,2):
        changed=deepcopy(doc);body=next(d for d in changed['declarations'] if d['name']==m['h247e'])['body']
        body['arguments'][slot]['numerator']=999
        with pytest.raises(ValueError):evaluate(changed,model(changed)|{'jexpected':lambda:REFERENCES['h247e']})
    changed=deepcopy(doc);body=next(d for d in changed['declarations'] if d['name']==m['h247e'])['body']
    body['arguments'][0]=call(m['wh'])
    with pytest.raises(ValueError):evaluate(changed,model(changed)|{'jexpected':lambda:REFERENCES['h247e']})
    def unknown(*args):raise ValueError('Unspecified clerical public freedom reference')
    with pytest.raises(ValueError,match='Unspecified clerical public freedom reference'):
        evaluate(doc,model(doc)|{'jexpected':lambda:REFERENCES['h247e'],voc._symbols['sentencereference']:unknown})


def test_inherited_description_wrapper_mutations_are_refused():
    doc=deepcopy(check.restored()['document']);m=check.mapping()
    next(d for d in doc['declarations'] if d['name']==m['h227c'])['body']['arguments'][0]=call(m['wh'])
    with pytest.raises(ValueError,match='Reused description wrapper differs'):check.backprojection(doc)


def test_freedom_and_calling_clause_references_preserve_exact_character_ranges():
    m=check.mapping();anchors=check.read(check.ANCHORS)
    for name,row in anchors['source_character_spans'].items():
        assert row['text']==anchors['text'][row['first_character']:row['past_last_character']]
        assert row['source_range']==[3186+row['first_character'],3186+row['past_last_character']]
        doc=selection();doc['declarations'].append(dict(kind='primitive',name='jexpected',parameters=[],result='individual'))
        doc['statements']=[dict(kind='ask',body=dict(kind='equal',arguments=[call(m[name]),call('jexpected')]))]
        assert evaluate(doc,model(doc)|{'jexpected':lambda name=name:REFERENCES[name]})==[True]
        assert evaluate(doc,model(doc)|{'jexpected':lambda:REFERENCES['h247e']})==[False]
        for slot in (2,3):
            changed=deepcopy(doc);body=next(d for d in changed['declarations'] if d['name']==m[name])['body']
            body['arguments'][slot]['numerator']+=1
            with pytest.raises(ValueError):evaluate(changed,model(changed)|{'jexpected':lambda name=name:REFERENCES[name]})
        for slot,replacement in ((0,'wa'),(1,'h246q'),(4,'wh')):
            changed=deepcopy(doc);body=next(d for d in changed['declarations'] if d['name']==m[name])['body']
            body['arguments'][slot]=call(m[replacement])
            with pytest.raises(ValueError):evaluate(changed,model(changed)|{'jexpected':lambda name=name:REFERENCES[name]})
    assert anchors['source_character_spans']['h247f']['text']=='Aber als Gelehrter hat er volle Freiheit,'
    assert anchors['source_character_spans']['h247g']['text']=='ja sogar den Beruf dazu,'
    assert anchors['text'][67:].startswith('alle seine') and anchors['text'][67:].endswith('dem Publikum mitzutheilen.')
