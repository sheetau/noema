"""Keep the payment condition, prospective continuation and nur attribution."""
from copy import deepcopy
import json
import pytest
from noema.constructed_semantics import evaluate_document
from scripts import check_kant_payment_visible as check
from scripts.shared_modality import renamed
import test_kant_three_examples_visible as parent

DOMAIN=parent.parent.DOMAIN+('payment',)


def evaluate(doc,values):
    return [r['value'] for r in evaluate_document(doc,individuals=DOMAIN,situations=('body','closing','other'),
        primitives=values,max_steps=1000000,memoize_definitions=False,memoize_expressions=False)]


def model(doc,variant='baseline'):
    values=parent.model(doc);voc=check.vocabulary();inverse={value:key for key,value in check.mapping().items()}
    def name(description):return renamed(json.loads(description.syntax),inverse)['symbol']
    prior_sentence=values[voc._symbols['sentencereference']]
    def sentence(context,paragraph,index):
        if (context,paragraph,index)==('closing',2,4):return 'payment'
        return prior_sentence(context,paragraph,index)
    prior_presentation=values[voc._symbols['hypotheticalfirstpersonpresentation']]
    def presented(node,author,description,context):
        if node=='payment':return variant!='no_presentation' and (author,name(description),context)==(
            'author','t2' if variant=='wrong_conditional' else 't3','body')
        return prior_presentation(node,author,description,context)
    def sufficient(node,author,premise,conclusion,context):
        return variant!='no_marker' and (node,author,name(premise),name(conclusion),context)==(
            'illustration' if variant=='wrong_node' else 'payment',
            'other' if variant=='wrong_author' else 'author',
            'tq' if variant=='reversed_scope' else 'to' if variant=='wrong_premise' else 'tp',
            'tp' if variant=='reversed_scope' else 't2' if variant=='wrong_conclusion' else 'tq',
            'closing' if variant=='wrong_context' else 'body')
    prior_before=values[voc._symbols['textbefore']]
    def before(first,second,context):
        if (first,second)==('illustration','payment'):return context=='body' and variant!='reverse_order'
        return prior_before(first,second,context)
    values.update({voc._symbols[n]:fn for n,fn in dict(sentencereference=sentence,hypotheticalfirstpersonpresentation=presented,
        soleconditionpresentation=sufficient,textbefore=before).items()})
    return values


def test_whole_source_and_inherited_specialization_are_preserved():
    doc=check.restored()['document']
    assert check.backprojection(doc)==check.source_excerpt()
    assert check.specialized_backprojection(doc)==check.specialized_source()
    assert doc['statements'][:9]==check.previous.document()['statements']
    assert len(doc['declarations'])==302 and len(doc['statements'])==11
    assert len(check.source_excerpt()['declarations'])==284


def test_whole_document_preserves_payment_presentation_scope_and_order():
    doc=check.restored()['document']
    for variant in ('baseline','no_presentation','wrong_conditional','no_marker','wrong_node','wrong_author',
        'wrong_premise','wrong_conclusion','reversed_scope','wrong_context','reverse_order'):
        old=variant not in ('no_presentation','wrong_conditional','reverse_order')
        new=variant in ('baseline','reverse_order')
        assert evaluate(doc,model(doc,variant))==[True]*9+[old,new],variant


def test_unknown_new_presentation_inputs_are_rejected():
    doc=check.restored()['document'];voc=check.vocabulary()
    def unknown(*args):raise ValueError('Unspecified payment input')
    with pytest.raises(ValueError,match='Unspecified'):
        evaluate(doc,model(doc)|{voc._symbols['soleconditionpresentation']:unknown})
    values=model(doc);presented=values[voc._symbols['hypotheticalfirstpersonpresentation']]
    def scoped(node,*args):return unknown() if node=='payment' else presented(node,*args)
    with pytest.raises(ValueError,match='Unspecified'):
        evaluate(doc,values|{voc._symbols['hypotheticalfirstpersonpresentation']:scoped})


def test_payment_reference_is_derived_from_the_same_sentence_position():
    doc=deepcopy(check.restored()['document']);d=next(d for d in doc['declarations'] if d['name']==check.names()['t4'])
    assert d['body']['symbol']==check.vocabulary()._symbols['sentencereference']
    d['body']['arguments'][2]=check.num(3)
    values=evaluate(doc,model(doc))
    assert values[:9]==[True]*9 and values[-2:]==[False,False]
