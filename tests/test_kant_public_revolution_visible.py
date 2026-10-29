"""Keep fifth-sentence presentations, exact scopes and reused description bindings."""
from copy import deepcopy
import json
import pytest
from noema.constructed_semantics import evaluate_document
from scripts import check_kant_public_revolution_visible as check
from scripts import check_revolution_presentation as retained
from scripts.shared_modality import call,renamed
from scripts.sentence_text_span_references import SentenceTextSpanReferences
import test_kant_public_slow_attainment_visible as parent

REFERENCES={n:'revolution-'+n for n in ('h227w','h227h','h227n','h227o','h227x','h227y')}
DOMAIN=parent.DOMAIN+tuple(REFERENCES.values())
SMALL_DOMAIN=parent.SMALL_DOMAIN+tuple(REFERENCES.values())


def evaluate(doc,values,memo=True,domain=SMALL_DOMAIN):
    return [r['value'] for r in evaluate_document(doc,individuals=domain,
        situations=('body','closing','public-context','other'),primitives=values,max_steps=25000000,
        memoize_definitions=memo,memoize_expressions=memo)]


def model(doc,omitted=None,seen=None):
    values=parent.model(doc);voc=check.vocabulary();m=check.mapping();inverse={v:k for k,v in m.items()}
    anchors=check.read(check.ANCHORS);whole=REFERENCES['h227w']
    oldsentence=values[voc._symbols['sentencereference']];oldspan=values[voc._symbols['sentencetextspanreference']]
    def sentence(context,paragraph,index):
        if (context,paragraph,index)==('closing',4,5):return whole
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
        'public-sentence':'hzp4','dissemination-sentence':'hzp5','yoke-clause':'hzpo','slow-attainment-sentence':'h226h'}
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
            if not any(isinstance(a,str) and a in REFERENCES.values() for a in args):
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
    doc=deepcopy(check.restored()['document']);doc['statements']=doc['statements'][42:]
    return doc


def test_complete_source_and_previous_group_are_preserved():
    doc=check.restored()['document']
    assert check.backprojection(doc)==check.source_excerpt()
    assert check.specialized_backprojection(doc)==check.specialized_source()
    assert doc['statements'][:41]==check.previous.document()['statements']
    assert (len(doc['declarations']),len(doc['statements']))==(1344,43)
    assert len(check.source_excerpt()['declarations'])==1318
    assert evaluate(doc,model(doc),domain=DOMAIN)==[True]*43


def test_every_presentation_and_direction_is_required():
    doc=new_statement();seen=set()
    assert evaluate(doc,model(doc,seen=seen),memo=False)==[True]
    assert seen==set(range(len(retained.expectations())))
    for index in range(len(retained.expectations())):
        assert evaluate(doc,model(doc,omitted=index))==[False],index
    # Swap the actual same-typed target/depiction references inside each presentation.
    for owner in ('r2rx',):
        changed=deepcopy(doc);d=next(d for d in changed['declarations'] if d['name']==check.mapping()[owner])
        assert d['body']['symbol']==check.mapping()['h224n']
        args=d['body']['arguments'];args[4],args[5]=args[5],args[4]
        assert evaluate(changed,model(changed))==[False]


def test_unknown_presentations_are_refused_without_executing_world_claims():
    doc=new_statement()
    def unknown(*args):raise ValueError('Unspecified revolution relation')
    names={n for n,_ in retained.expectations()}
    for name in names:
        with pytest.raises(ValueError,match='Unspecified revolution'):
            evaluate(doc,model(doc)|{check.mapping()[name]:unknown})
    values=model(doc)
    for name in set(check.profile.SOURCE_RELATIONS)-names:values[check.mapping()[name]]=unknown
    assert evaluate(doc,values)==[True]
    with pytest.raises(ValueError,match='Unspecified revolution'):
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
        next(d for d in changed['declarations'] if d['name']==m['h227o'])['body']['arguments'][slot]=call(m[other])
        with pytest.raises(ValueError):evaluate(changed,model(changed))
    def unknown(*args):raise ValueError('Unspecified revolution reference')
    for name in ('sentencereference','sentencetextspanreference','paragraphpresentationcontext'):
        with pytest.raises(ValueError,match='Unspecified revolution reference'):
            evaluate(doc,model(doc)|{voc._symbols[name]:unknown})


def test_reused_description_wrappers_preserve_issuance_and_denotation():
    import test_public_dissemination_visible_profile as providers
    from noema.constructed_discourse import normalize_document
    from noema.constructed_semantics import DescriptionValue
    actual=check.restored()['document'];ds={d['name']:d for d in actual['declarations']}
    for old,target in check.profile.REUSED_RELATIONS.items():
        doc=providers.fixture(target)
        wrapper=renamed(ds[check.mapping()[old]],{
            check.mapping()[old]:old,check.vocabulary()._symbols[target]:target})
        doc['declarations'].append(wrapper)
        doc['statements']=renamed(doc['statements'],{target:old})
        doc=normalize_document(doc);values=providers.model(doc,target,'jreturned')
        # The local wrapper forwards the same argument and keeps the quotation opaque.
        assert providers.run(doc,values)==[True]
        with pytest.raises(ValueError,match='Unknown'):
            providers.run(doc,values|{'jarga':lambda:'other'})
        registration=deepcopy(doc['statements'][0]['body']['arguments'][0])
        doc['statements']=[dict(kind='ask',body=dict(kind='and',arguments=[registration,
            dict(kind='equal',arguments=[dict(kind='disquote',description=call(old,call('jarga'))),call('jarga')])]))]
        doc=normalize_document(doc)
        assert providers.run(doc,values|{'jreturned':lambda:'jarga'})==[True]
        assert providers.run(doc,values|{'jreturned':lambda:'other'})==[False]
        with pytest.raises(ValueError,match='must not execute'):providers.run(doc,values)
        sort=wrapper['result']['result']
        forged=DescriptionValue(json.dumps(call('jreturned'),sort_keys=True,separators=(',',':')),json.dumps(sort))
        with pytest.raises(ValueError):providers.run(doc,values|{target:lambda *args:forged})


def test_backprojection_rejects_changed_reused_description_bodies():
    actual=check.restored()['document'];m=check.mapping()
    changed=deepcopy(actual)
    next(d for d in changed['declarations'] if d['name']==m['h227b'])['body']['symbol']=m['h225h']
    with pytest.raises(ValueError,match='Reused description wrapper differs'):check.backprojection(changed)
    changed=deepcopy(actual)
    next(d for d in changed['declarations'] if d['name']==m['h227c'])['body']['arguments'][0]=call(m['wh'])
    with pytest.raises(ValueError,match='Reused description wrapper differs'):check.backprojection(changed)
