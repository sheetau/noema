"""Preserve each role, command example, textual span and associated social quarter."""
from copy import deepcopy
import json
import pytest
from noema.constructed_semantics import evaluate_document
from scripts import check_kant_role_commands_visible as check
from scripts.shared_modality import call,renamed
from scripts.sentence_text_span_references import SentenceTextSpanReferences
import test_kant_heard_prohibition_visible as parent

NODES=('h233m','h233n','h233o')
QUARTERS=('h233i','h233j','h233k')
SPANS=('officerrolespan','financerolespan','clericrolespan')
REFERENCES={n:'role-commands-'+n for n in NODES+QUARTERS+SPANS}
DOMAIN=parent.DOMAIN+tuple(REFERENCES.values())


def evaluate(doc,values,memo=True):
    return [r['value'] for r in evaluate_document(doc,individuals=DOMAIN,situations=parent.SCENES,
        primitives=values,max_steps=25000000,memoize_definitions=memo,memoize_expressions=memo)]


def expectations():
    q=lambda name:('quote',1,'call',name)
    rows=[]
    for node,content,prior in zip(NODES,('r2ts','r2tt','r2tu'),('h232w','h233m','h233n'),strict=True):
        rows += [('hzon',(node,'wa',q(content),'h232o')),
            ('h233l',(node,'wa','h232w',q('r2te'),q(content),'h232o')),
            ('ue',(prior,node,'h232o'))]
    return rows


def model(doc,omitted=None,seen=None):
    values=parent.model(doc);voc=check.vocabulary();m=check.mapping();inverse={v:k for k,v in m.items()}
    anchors=check.read(check.ANCHORS)
    oldsentence=values[voc._symbols['sentencereference']];oldspan=values[voc._symbols['sentencetextspanreference']]
    oldreferent=values[voc._symbols['discoursereferent']]
    def sentence(context,paragraph,index):
        for node,where in anchors['source_nodes'].items():
            if (context,paragraph,index)==('closing',*where):return REFERENCES[node]
        return oldsentence(context,paragraph,index)
    texts={('document',REFERENCES[n],'closing'):r['text'] for n,r in anchors['texts'].items()}
    refs=SentenceTextSpanReferences(texts,{('document',REFERENCES[r['sentence_reference']],r['first_character'],r['past_last_character'],'closing'):REFERENCES[n] for n,r in anchors['source_character_spans'].items()})
    def span(document,sentence,first,last,context):
        if sentence in {REFERENCES[n] for n in NODES}:return refs.span(document,sentence,first,last,context)
        return oldspan(document,sentence,first,last,context)
    def referent(document,node,ordinal,context):
        if node in {REFERENCES[n] for n in SPANS}:
            for n,r in anchors['referents'].items():
                if (document,node,ordinal,context)==('document',REFERENCES[r['span']],r['ordinal'],'closing'):return REFERENCES[n]
            raise ValueError('Unknown role-command quarter reference')
        return oldreferent(document,node,ordinal,context)
    values[voc._symbols['sentencereference']]=sentence;values[voc._symbols['sentencetextspanreference']]=span
    values[voc._symbols['discoursereferent']]=referent
    labels={v:k for k,v in REFERENCES.items()}|{'author':'wa',parent.WHOLE:'h232w',parent.parent.CONTEXT:'h232o'}
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
            return False
        return relation
    for name in {n for n,_ in expected}:values[m[name]]=handler(name,values.get(m[name],lambda *args:False))
    return values


def selection(start=45):
    doc=deepcopy(check.restored()['document']);doc['statements']=doc['statements'][start:]
    return doc


def test_source_and_every_prior_declaration_are_preserved():
    doc=check.restored()['document'];old=check.previous.document()
    assert check.backprojection(doc)==check.source_excerpt()
    assert check.specialized_backprojection(doc)==check.specialized_source()
    assert doc['statements'][:45]==old['statements']
    ds={d['name']:d for d in doc['declarations']}
    assert all(ds[d['name']]==d for d in old['declarations'])
    assert (len(doc['declarations']),len(doc['statements']))==(1429,48)
    assert len(check.source_excerpt()['declarations'])==1399
    current=selection(43)
    assert evaluate(current,model(current))==[True]*5


def test_every_claim_example_and_order_remains_bound_to_its_sentence():
    doc=selection();seen=set()
    assert evaluate(doc,model(doc,seen=seen),memo=False)==[True]*3
    assert seen==set(range(9))
    for index in range(9):assert evaluate(doc,model(doc,omitted=index))==[i!=index//3 for i in range(3)]
    m=check.mapping()
    for owner in ('r2tw','r2tx','r2ty'):
        changed=deepcopy(doc);d=next(d for d in changed['declarations'] if d['name']==m[owner])
        d['body']['arguments'][1]=dict(kind='quote',rank=1,body=call(m['r2te']))
        assert evaluate(changed,model(changed))==[n!=owner for n in ('r2tw','r2tx','r2ty')]


def test_unknown_presentations_refused_while_quoted_world_inputs_stay_unknown():
    doc=selection();m=check.mapping()
    def unknown(*args):raise ValueError('Unspecified role-command relation')
    for name in ('hzon','h233l','ue'):
        with pytest.raises(ValueError,match='Unspecified role-command'):evaluate(doc,model(doc)|{m[name]:unknown})
    values=model(doc)
    for name in set(check.profile.SOURCE_RELATIONS)-{'h233l'}:values[m[name]]=unknown
    values[check.vocabulary()._symbols['discoursereferent']]=unknown
    assert evaluate(doc,values)==[True]*3


def reference_questions():
    doc=selection();m=check.mapping()
    doc['declarations'].append(dict(kind='primitive',name='jexpected',parameters=[],result='individual'))
    doc['statements']=[dict(kind='ask',body=dict(kind='equal',arguments=[call(m[n]),call('jexpected')])) for n in REFERENCES]
    return doc


def test_sentences_spans_and_quarters_are_distinct_references():
    doc=reference_questions()
    for index,target in enumerate(REFERENCES.values()):
        assert evaluate(doc,model(doc)|{'jexpected':lambda target=target:target})==[i==index for i in range(len(REFERENCES))]
    for name in SPANS:
        changed=deepcopy(doc)
        next(d for d in changed['declarations'] if d['name']==check.mapping()[name])['body']['arguments'][3]['numerator']+=1
        with pytest.raises(ValueError):evaluate(changed,model(changed)|{'jexpected':lambda:'other'})
    for name in QUARTERS:
        changed=deepcopy(doc)
        next(d for d in changed['declarations'] if d['name']==check.mapping()[name])['body']['arguments'][2]['numerator']=2
        with pytest.raises(ValueError,match='Unknown role-command quarter'):evaluate(changed,model(changed)|{'jexpected':lambda:'other'})


def test_reference_and_context_inputs_cannot_be_silently_replaced():
    doc=reference_questions();voc=check.vocabulary();m=check.mapping()
    def unknown(*args):raise ValueError('Unspecified role-command reference')
    for name in ('sentencereference','sentencetextspanreference','discoursereferent'):
        with pytest.raises(ValueError,match='Unspecified role-command reference'):
            evaluate(doc,model(doc)|{voc._symbols[name]:unknown,'jexpected':lambda:'other'})
    current=selection()
    for other in ('hzp3','h232v'):
        changed=deepcopy(current);d=next(d for d in changed['declarations'] if d['name']==m['r2tv'])
        d['body']=renamed(d['body'],{m['h232o']:m[other]})
        assert evaluate(changed,model(changed))==[False]*3


def test_inherited_description_wrapper_mutations_are_refused():
    doc=deepcopy(check.restored()['document']);m=check.mapping()
    next(d for d in doc['declarations'] if d['name']==m['h227c'])['body']['arguments'][0]=call(m['wh'])
    with pytest.raises(ValueError,match='Reused description wrapper differs'):check.backprojection(doc)
