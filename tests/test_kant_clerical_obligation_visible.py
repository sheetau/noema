"""Keep the current obligation, appointment reason and two different prior references distinct."""
from copy import deepcopy
import json
import pytest
from noema.constructed_semantics import evaluate_document
from scripts import check_kant_clerical_obligation_visible as check
from scripts.shared_modality import call,renamed
from scripts.sentence_text_span_references import SentenceTextSpanReferences
import test_kant_public_civic_opinion_visible as parent

REFERENCES={n:'clerical-obligation-'+n for n in ('h246q','h246r','h246s')}
DOMAIN=parent.DOMAIN+tuple(REFERENCES.values())
SCENES=parent.SCENES
CONTEXT=parent.CONTEXT
ROOTS=('r36l',)

def evaluate(doc,values,memo=True):
    return [r['value'] for r in evaluate_document(doc,individuals=DOMAIN,situations=SCENES,
        primitives=values,max_steps=25000000,memoize_definitions=memo,memoize_expressions=memo)]

def expectations():
    q=lambda name:('quote',3,'call',name)
    return [('r36l','h236i',(node,'wa',q(content),'h232o')) for node,content in
        [('h246q','r36k'),('h246r','r36i'),('h246s','r36j')]]+[
        ('r36l','ud',('wa',('h246s',),'h246r','h232o')),
        ('r36l','h245m',('h246q','wa','h245f',q('r34x'),q('r36k'),'h232o')),
        ('r36l','ue',('h245u','h246q','h232o')),
        ('r36l','ue',('h246r','h246s','h232o'))]


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
        if sentence==REFERENCES['h246q']:return refs.span(document,sentence,first,last,context)
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
            if name=='h245m':
                raise ValueError('Unspecified clerical obligation presentation')
            return previous(*args)
        return relation
    for name in {n for _,n,_ in rows}:values[m[name]]=handler(name,values.get(m[name],lambda *args:False))
    return values

def selection(start=65):
    doc=deepcopy(check.restored()['document']);doc['statements']=doc['statements'][start:]
    return doc

def test_source_and_every_prior_declaration_are_preserved():
    doc=check.restored()['document'];old=check.previous.document()
    assert check.backprojection(doc)==check.source_excerpt()
    assert check.specialized_backprojection(doc)==check.specialized_source()
    assert doc['statements'][:65]==old['statements']
    ds={d['name']:d for d in doc['declarations']}
    assert all(ds[d['name']]==d for d in old['declarations'])
    assert (len(doc['declarations']),len(doc['statements']))==(1988,66)
    assert len(check.source_excerpt()['declarations'])==1957
    assert check.SOURCE_ORDER[-1:]==[82]
    current=selection(64);assert evaluate(current,model(current))==[True]*2

def test_whole_clause_attribution_reason_parallel_example_and_order_are_required():
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
            if name=='h245m' and slot==0:
                # Changing the only current source node leaves this model's
                # specified presentation scope. Reject it rather than inventing
                # a false value for an unspecified parallel-example relation.
                with pytest.raises(ValueError,match='Unspecified clerical obligation presentation'):
                    evaluate(changed,model(changed))
            else:
                assert evaluate(changed,model(changed))[ROOTS.index(root)] is False,(root,name,occurrence,slot)

def test_unknown_presentations_refused_and_quoted_policy_contents_not_executed():
    doc=selection();m=check.mapping()
    def unknown(*args):raise ValueError('Unspecified clerical obligation input')
    for name in {n for _,n,_ in expectations()}:
        with pytest.raises(ValueError,match='Unspecified clerical obligation'):evaluate(doc,model(doc)|{m[name]:unknown})
    values=model(doc)
    for name in set(check.profile.SOURCE_RELATIONS)-{n for _,n,_ in expectations()}:values[m[name]]=unknown
    assert evaluate(doc,values)==[True]

def test_whole_sentence_reference_is_exact_and_refuses_unknown_addresses():
    m=check.mapping();voc=check.vocabulary()
    assert check.names()['h245u']==check.previous.names()['h245u']
    doc=selection();doc['declarations'].append(dict(kind='primitive',name='jexpected',parameters=[],result='individual'))
    doc['statements']=[dict(kind='ask',body=dict(kind='equal',arguments=[call(m['h246q']),call('jexpected')]))]
    assert evaluate(doc,model(doc)|{'jexpected':lambda:REFERENCES['h246q']})==[True]
    assert evaluate(doc,model(doc)|{'jexpected':lambda:parent.REFERENCES['h245u']})==[False]
    for slot in (1,2):
        changed=deepcopy(doc);body=next(d for d in changed['declarations'] if d['name']==m['h246q'])['body']
        body['arguments'][slot]['numerator']=999
        with pytest.raises(ValueError):evaluate(changed,model(changed)|{'jexpected':lambda:REFERENCES['h246q']})
    changed=deepcopy(doc);body=next(d for d in changed['declarations'] if d['name']==m['h246q'])['body']
    body['arguments'][0]=call(m['wh'])
    with pytest.raises(ValueError):evaluate(changed,model(changed)|{'jexpected':lambda:REFERENCES['h246q']})
    def unknown(*args):raise ValueError('Unspecified clerical obligation reference')
    with pytest.raises(ValueError,match='Unspecified clerical obligation reference'):
        evaluate(doc,model(doc)|{'jexpected':lambda:REFERENCES['h246q'],voc._symbols['sentencereference']:unknown})


def test_inherited_description_wrapper_mutations_are_refused():
    doc=deepcopy(check.restored()['document']);m=check.mapping()
    next(d for d in doc['declarations'] if d['name']==m['h227c'])['body']['arguments'][0]=call(m['wh'])
    with pytest.raises(ValueError,match='Reused description wrapper differs'):check.backprojection(doc)


def test_main_and_reason_clause_references_preserve_exact_character_ranges():
    m=check.mapping();anchors=check.read(check.ANCHORS)
    for name,row in anchors['source_character_spans'].items():
        assert row['text']==anchors['text'][row['first_character']:row['past_last_character']]
        assert row['source_range']==[2984+row['first_character'],2984+row['past_last_character']]
        doc=selection();doc['declarations'].append(dict(kind='primitive',name='jexpected',parameters=[],result='individual'))
        doc['statements']=[dict(kind='ask',body=dict(kind='equal',arguments=[call(m[name]),call('jexpected')]))]
        assert evaluate(doc,model(doc)|{'jexpected':lambda name=name:REFERENCES[name]})==[True]
        assert evaluate(doc,model(doc)|{'jexpected':lambda:REFERENCES['h246q']})==[False]
        for slot in (2,3):
            changed=deepcopy(doc);body=next(d for d in changed['declarations'] if d['name']==m[name])['body']
            body['arguments'][slot]['numerator']+=1
            with pytest.raises(ValueError):evaluate(changed,model(changed)|{'jexpected':lambda name=name:REFERENCES[name]})
        for slot,replacement in ((0,'wa'),(1,'h245u'),(4,'wh')):
            changed=deepcopy(doc);body=next(d for d in changed['declarations'] if d['name']==m[name])['body']
            body['arguments'][slot]=call(m[replacement])
            with pytest.raises(ValueError):evaluate(changed,model(changed)|{'jexpected':lambda name=name:REFERENCES[name]})
    assert anchors['source_character_spans']['h246r']['text'].endswith('thun;')
    assert anchors['source_character_spans']['h246s']['text']=='denn er ist auf diese Bedingung angenommen worden.'
