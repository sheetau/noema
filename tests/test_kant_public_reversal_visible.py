"""Keep all scoped presentations, role directions and exact third-sentence anchors."""
from copy import deepcopy
import json
import pytest
from noema.constructed_semantics import evaluate_document
from scripts import check_kant_public_reversal_visible as check
from scripts import check_public_third_sentence as retained
from scripts.shared_modality import call,renamed
from scripts.sentence_text_span_references import SentenceTextSpanReferences
import test_kant_public_dissemination_visible as parent

REFERENCES={n:'reversal-'+n for n in ('thirdsentencereference','h224m','h224o','h224q','h224t','h224u','h224v','h225o','h225p','h225s','h225y','h226d')}
DOMAIN=parent.DOMAIN+tuple(REFERENCES.values())
SMALL_DOMAIN=parent.SMALL_DOMAIN+tuple(REFERENCES.values())


def evaluate(doc,values,memo=True,domain=SMALL_DOMAIN):
    return [r['value'] for r in evaluate_document(doc,individuals=domain,
        situations=('body','closing','public-context','other'),primitives=values,max_steps=25000000,
        memoize_definitions=memo,memoize_expressions=memo)]


def model(doc,omitted=None,seen=None):
    values=parent.model(doc);voc=check.vocabulary();m=check.mapping();inverse={v:k for k,v in m.items()}
    anchors=check.read(check.ANCHORS);whole=REFERENCES['thirdsentencereference']
    oldsentence=values[voc._symbols['sentencereference']];oldspan=values[voc._symbols['sentencetextspanreference']]
    def sentence(context,paragraph,index):
        if (context,paragraph,index)==('closing',4,3):return whole
        return oldsentence(context,paragraph,index)
    refs=SentenceTextSpanReferences({('document',whole,'closing'):anchors['text']},
        {('document',whole,r['first_character'],r['past_last_character'],'closing'):REFERENCES[n]
         for n,r in anchors['source_character_spans'].items()})
    def span(document,sentence,first,last,context):
        if sentence==whole:return refs.span(document,sentence,first,last,context)
        return oldspan(document,sentence,first,last,context)
    values[voc._symbols['sentencereference']]=sentence
    values[voc._symbols['sentencetextspanreference']]=span
    labels={v:k for k,v in REFERENCES.items()}|{'author':'wa','public-context':'hzp3',
        'public-sentence':'hzp4','dissemination-sentence':'hzp5','yoke-clause':'hzpo'}
    expected=retained.expectations()
    def normalized(value):
        if isinstance(value,str):return labels.get(value,value)
        if isinstance(value,tuple):return tuple(normalized(x) for x in value)
        if hasattr(value,'syntax'):
            code=renamed(json.loads(value.syntax),inverse)
            return ('quote',value.rank,code['kind'],code['symbol'])
        if hasattr(value,'items'):return tuple(normalized(x) for x in value.items)
        raise AssertionError(type(value))
    def handler(name,previous):
        def relation(*args):
            # Existing sentence handlers own their richer quotation syntax.
            if name in ('hznreport','ud','ue') and not any(isinstance(a,str) and a in REFERENCES.values() for a in args):
                return previous(*args)
            converted=(args[0],tuple(p for p in SMALL_DOMAIN if args[1](p)),*args[2:]) if name=='ud' else args
            row=(name,tuple(normalized(a) for a in converted))
            if row in expected:
                index=expected.index(row)
                if seen is not None:seen.add(index)
                return index!=omitted
            if name not in ('hznreport','ud','ue') or any(isinstance(a,str) and a in REFERENCES.values() for a in args):return False
            return previous(*args)
        return relation
    for name in {n for n,_ in expected}:values[m[name]]=handler(name,values[m[name]])
    return values


def new_statement():
    doc=deepcopy(check.restored()['document']);doc['statements']=doc['statements'][39:]
    return doc


def test_complete_source_and_previous_group_are_preserved():
    doc=check.restored()['document']
    assert check.backprojection(doc)==check.source_excerpt()
    assert check.specialized_backprojection(doc)==check.specialized_source()
    assert doc['statements'][:39]==check.previous.document()['statements']
    assert (len(doc['declarations']),len(doc['statements']))==(1230,40)
    assert len(check.source_excerpt()['declarations'])==1204
    assert evaluate(doc,model(doc),domain=DOMAIN)==[True]*40


def test_every_presentation_and_direction_is_required():
    doc=new_statement();seen=set()
    assert evaluate(doc,model(doc,seen=seen),memo=False)==[True]
    assert seen==set(range(len(retained.expectations())))
    for index in range(len(retained.expectations())):
        assert evaluate(doc,model(doc,omitted=index))==[False],index
    # Swap the actual same-typed target/depiction references inside each presentation.
    for owner in ('r2no','r2ph','r2pm'):
        changed=deepcopy(doc);d=next(d for d in changed['declarations'] if d['name']==check.mapping()[owner])
        assert d['body']['symbol']==check.mapping()['h224n']
        args=d['body']['arguments'];args[4],args[5]=args[5],args[4]
        assert evaluate(changed,model(changed))==[False]


def test_unknown_presentations_are_refused_without_executing_world_claims():
    doc=new_statement()
    def unknown(*args):raise ValueError('Unspecified reversal relation')
    names={n for n,_ in retained.expectations()}
    for name in names:
        with pytest.raises(ValueError,match='Unspecified reversal'):
            evaluate(doc,model(doc)|{check.mapping()[name]:unknown})
    values=model(doc)
    for name in set(check.profile.SOURCE_RELATIONS)-names:values[check.mapping()[name]]=unknown
    assert evaluate(doc,values)==[True]
    with pytest.raises(ValueError,match='Unspecified reversal'):
        evaluate(doc,model(doc,omitted=0)|{check.mapping()['h224n']:unknown})


def test_exact_source_spans_preserve_distinct_mentions():
    doc=new_statement();m=check.mapping()
    doc['declarations'].append(dict(kind='primitive',name='jexpected',parameters=[],result='individual'))
    doc['statements']=[dict(kind='ask',body=dict(kind='equal',arguments=[call(m[n]),call('jexpected')])) for n in REFERENCES]
    for index,target in enumerate(REFERENCES.values()):
        assert evaluate(doc,model(doc)|{'jexpected':lambda target=target:target})==[i==index for i in range(len(REFERENCES))]
    for name,row in check.read(check.ANCHORS)['source_character_spans'].items():
        changed=new_statement();d=next(d for d in changed['declarations'] if d['name']==m[name])
        d['body']['arguments'][3]['numerator']+=1
        with pytest.raises(ValueError):evaluate(changed,model(changed))


def test_reference_context_and_order_inputs_cannot_be_silently_replaced():
    doc=new_statement();m=check.mapping();voc=check.vocabulary()
    for slot,other in ((0,'wa'),(1,'hzp4'),(4,'wh')):
        changed=deepcopy(doc)
        next(d for d in changed['declarations'] if d['name']==m['h224o'])['body']['arguments'][slot]=call(m[other])
        with pytest.raises(ValueError):evaluate(changed,model(changed))
    def unknown(*args):raise ValueError('Unspecified reversal reference')
    for name in ('sentencereference','sentencetextspanreference','paragraphpresentationcontext'):
        with pytest.raises(ValueError,match='Unspecified reversal reference'):
            evaluate(doc,model(doc)|{voc._symbols[name]:unknown})
