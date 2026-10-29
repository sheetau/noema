"""Preserve current paragraph context, referents, explanations and exact prior-word spans."""
from copy import deepcopy
import json
import pytest
from noema.constructed_semantics import evaluate_document
from scripts import check_kant_enlightenment_requirement_visible as check
from scripts.shared_modality import call,renamed
from scripts.sentence_text_span_references import SentenceTextSpanReferences
import test_kant_public_revolution_visible as parent

REFERENCES={n:'requirement-'+n for n in ('h232h','h232i','h232j','h232k','h232l','h232m','h232n')}
DOMAIN=parent.DOMAIN+tuple(REFERENCES.values())
SMALL_DOMAIN=parent.SMALL_DOMAIN+tuple(REFERENCES.values())
CONTEXT='requirement-context'


def evaluate(doc,values,memo=True,domain=SMALL_DOMAIN):
    return [r['value'] for r in evaluate_document(doc,individuals=domain,
        situations=('body','closing','public-context',CONTEXT,'other'),primitives=values,max_steps=25000000,
        memoize_definitions=memo,memoize_expressions=memo)]


def expectations():
    q=lambda name,kind='call',rank=1:('quote',rank,kind,name)
    rows=[('hzon',(node,'wa',q(content),'h232o')) for node,content in
        (('h232h','r2ss'),('h232n','r2sr'),('h232j','r2so'))]
    rows += [('h232g',(node,'wa',q('r2ln' if node in ('h232l','h232m') else 'r2sl','function_ref'),'h232h','h232o'))
        for node in ('h232i','h232j','h232k','h232l','h232m')]
    rows += [('ue',(first,last,'h232o')) for first,last in
        (('h232i','h232j'),('h232j','h232k'),('h232l','h232m'),('h227w','h232h'))]
    rows += [('ibbclarifies',(first,last,'wa','h232h','h232o')) for first,last in (('h232i','h232j'),('h232j','h232k'))]
    rows += [('h222q',('h232h','wa','h226h',q('r2pt'),'h232n',q('r2sr'),q('h4l','function_ref',0),'h232o'))]
    return rows


def model(doc,omitted=None,seen=None,cycle=False):
    values=parent.model(doc);voc=check.vocabulary();m=check.mapping();inverse={v:k for k,v in m.items()}
    anchors=check.read(check.ANCHORS);whole=REFERENCES['h232h'];prior='slow-attainment-sentence'
    oldsentence=values[voc._symbols['sentencereference']];oldspan=values[voc._symbols['sentencetextspanreference']]
    oldcontext=values[voc._symbols['paragraphpresentationcontext']]
    def sentence(context,paragraph,index):
        if (context,paragraph,index)==('closing',5,1):return whole
        return oldsentence(context,paragraph,index)
    def paragraph(body,index):
        if (body,index)==('body',5):return CONTEXT
        return oldcontext(body,index)
    texts={('document',whole,'closing'):anchors['text'],
        ('document',prior,'closing'):check.read('data/kant-public-slow-attainment-text-anchors-v1.json')['text']}
    refs=SentenceTextSpanReferences(texts,
        {('document',prior if n=='h232l' else whole,r['first_character'],r['past_last_character'],'closing'):REFERENCES[n]
         for n,r in anchors['source_character_spans'].items()})
    def span(document,sentence,first,last,context):
        if sentence in (whole,prior):return refs.span(document,sentence,first,last,context)
        return oldspan(document,sentence,first,last,context)
    values[voc._symbols['sentencereference']]=sentence
    values[voc._symbols['sentencetextspanreference']]=span
    values[voc._symbols['paragraphpresentationcontext']]=paragraph
    labels={v:k for k,v in REFERENCES.items()}|{'author':'wa',CONTEXT:'h232o','public-context':'hzp3',
        prior:'h226h',parent.REFERENCES['h227w']:'h227w'}
    def normalized(value):
        if isinstance(value,str):return labels.get(value,value)
        if hasattr(value,'syntax'):
            code=renamed(json.loads(value.syntax),inverse)
            return ('quote',value.rank,code['kind'],code['symbol'])
        raise AssertionError(type(value))
    expected=expectations()
    def handler(name,previous):
        def relation(*args):
            if not any(isinstance(a,str) and a in REFERENCES.values() for a in args):return previous(*args)
            row=(name,tuple(normalized(a) for a in args))
            if row in expected:
                index=expected.index(row)
                if seen is not None:seen.add(index)
                return index!=omitted
            if cycle and row==('ue',('h232m','h232l','h232o')):return True
            return False
        return relation
    for name in {n for n,_ in expected}:
        values[m[name]]=handler(name,values.get(m[name],lambda *args:False))
    return values


def new_statement():
    doc=deepcopy(check.restored()['document']);doc['statements']=doc['statements'][43:]
    return doc


def test_complete_source_and_previous_group_are_preserved():
    doc=check.restored()['document']
    assert check.backprojection(doc)==check.source_excerpt()
    assert check.specialized_backprojection(doc)==check.specialized_source()
    assert doc['statements'][:43]==check.previous.document()['statements']
    assert (len(doc['declarations']),len(doc['statements']))==(1373,44)
    assert len(check.source_excerpt()['declarations'])==1347
    # The unchanged prior statements retain their distinguishing domain. New
    # textual references do not justify enlarging every earlier tuple binder.
    prior=deepcopy(doc);prior['statements']=prior['statements'][:43]
    assert parent.evaluate(prior,model(prior),domain=parent.DOMAIN)==[True]*43
    current=new_statement()
    assert evaluate(current,model(current))==[True]


def test_every_attribution_referent_explanation_and_order_is_required():
    doc=new_statement();seen=set()
    assert evaluate(doc,model(doc,seen=seen),memo=False)==[True]
    assert seen==set(range(len(expectations())))
    for index in range(len(expectations())):assert evaluate(doc,model(doc,omitted=index))==[False],index
    assert evaluate(doc,model(doc,cycle=True))==[False]
    m=check.mapping()
    for owner,first,last in (('r2sx','h232i','h232k'),('r2sy','h232m','h232l')):
        changed=deepcopy(doc)
        d=next(d for d in changed['declarations'] if d['name']==m[owner])
        d['body']=renamed(d['body'],{m[first]:m[last]})
        assert evaluate(changed,model(changed))==[False]


def test_unknown_presentations_refused_without_executing_world_claims():
    doc=new_statement();m=check.mapping()
    def unknown(*args):raise ValueError('Unspecified requirement relation')
    for name in {n for n,_ in expectations()}:
        with pytest.raises(ValueError,match='Unspecified requirement'):evaluate(doc,model(doc)|{m[name]:unknown})
    values=model(doc)
    for name in set(check.profile.SOURCE_RELATIONS)-{'h232g'}:values[m[name]]=unknown
    assert evaluate(doc,values)==[True]


def test_exact_spans_include_the_prior_paragraph_word():
    doc=new_statement();m=check.mapping()
    doc['declarations'].append(dict(kind='primitive',name='jexpected',parameters=[],result='individual'))
    doc['statements']=[dict(kind='ask',body=dict(kind='equal',arguments=[call(m[n]),call('jexpected')])) for n in REFERENCES]
    for index,target in enumerate(REFERENCES.values()):
        assert evaluate(doc,model(doc)|{'jexpected':lambda target=target:target})==[i==index for i in range(len(REFERENCES))]
    for name in check.read(check.ANCHORS)['source_character_spans']:
        changed=new_statement();d=next(d for d in changed['declarations'] if d['name']==m[name])
        d['body']['arguments'][3]['numerator']+=1
        with pytest.raises(ValueError):evaluate(changed,model(changed))


def test_new_paragraph_context_is_distinct_and_reference_inputs_are_checked():
    doc=new_statement();m=check.mapping();voc=check.vocabulary()
    for other in ('hzp3','wh','hzim'):
        changed=deepcopy(doc)
        next(d for d in changed['declarations'] if d['name']==m['h232o'])['body']=call(m[other])
        assert evaluate(changed,model(changed))==[False]
    for slot,other in ((0,'wa'),(1,'h232h'),(4,'wh')):
        changed=deepcopy(doc)
        next(d for d in changed['declarations'] if d['name']==m['h232l'])['body']['arguments'][slot]=call(m[other])
        with pytest.raises(ValueError):evaluate(changed,model(changed))
    def unknown(*args):raise ValueError('Unspecified requirement reference')
    for name in ('sentencereference','sentencetextspanreference','paragraphpresentationcontext'):
        with pytest.raises(ValueError,match='Unspecified requirement reference'):
            evaluate(doc,model(doc)|{voc._symbols[name]:unknown})


def test_inherited_description_wrappers_are_checked_before_backprojection():
    doc=check.restored()['document'];m=check.mapping()
    for name in ('h227b','h227c'):
        changed=deepcopy(doc)
        next(d for d in changed['declarations'] if d['name']==m[name])['body']['arguments'][0]=call(m['wh' if name=='h227c' else 'wa'])
        with pytest.raises(ValueError,match='Reused description wrapper differs'):check.backprojection(changed)
