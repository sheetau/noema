"""Preserve the causal assertion, figurative attribution and reference boundary."""
from copy import deepcopy
import json
import pytest
from noema.constructed_semantics import evaluate_document
from scripts import check_kant_first_cause_visible as check
from scripts.shared_modality import call,renamed
import test_kant_first_paragraph_visible as parent

DOMAIN=parent.DOMAIN+('causal','population-span','nature-span','population','nature')


def evaluate(doc,values):
    return [r['value'] for r in evaluate_document(doc,individuals=DOMAIN,situations=('body','closing','other'),
        primitives=values,max_steps=1000000,memoize_definitions=False,memoize_expressions=False)]


def model(doc,variant='baseline'):
    values=parent.model(doc);voc=check.vocabulary();inverse={v:k for k,v in check.mapping().items()}
    syntax=lambda code:renamed(json.loads(code.syntax),inverse)
    oldsentence=values[voc._symbols['sentencereference']]
    oldspan=values[voc._symbols['sentencetokenspanreference']]
    oldclaim=values[voc._symbols['assertsdescribedcontent']]
    oldbefore=values[voc._symbols['textbefore']]
    def sentence(context,paragraph,index):
        if (context,paragraph,index)==('closing',2,1):return 'causal'
        return oldsentence(context,paragraph,index)
    def span(document,first,a,last,b,context):
        if (document,first,last,context)==('document','causal','causal','closing'):
            if (a,b)==(12,13):return 'population-span'
            if (a,b)==(16,17):return 'nature-span'
            raise ValueError('Unknown cause span')
        return oldspan(document,first,a,last,b,context)
    def referent(document,node,ordinal,context):
        if (document,ordinal,context)!=('document',1,'closing'):raise ValueError('Unknown cause referent')
        known={'population-span':'population','nature-span':'nature'}
        if node not in known:raise ValueError('Unknown cause referent')
        return known[node]
    def claim(node,author,code,context):
        if node=='causal':
            return (author,context)==('other' if variant=='wrong_author' else 'author',
                'other' if variant=='wrong_context' else 'body') and syntax(code)==call('mx') and variant!='missing_cause'
        return oldclaim(node,author,code,context)
    def before(a,b,context):
        if (a,b)==('conclusion','causal'):return context=='body' and variant!='reverse_order'
        return oldbefore(a,b,context)
    def figurative(node,author,target,depiction,context):
        expected=('other' if variant=='wrong_node' else 'causal',
            'other' if variant=='wrong_author' else 'author',
            dict(kind='function_ref',symbol='qg' if variant=='reversed_depiction' else 'kf'),
            dict(kind='function_ref',symbol='kf' if variant=='reversed_depiction' else 'qg'),
            'other' if variant=='wrong_context' else 'body')
        return (node,author,syntax(target),syntax(depiction),context)==expected and variant!='missing_depiction'
    handlers=dict(sentencereference=sentence,sentencetokenspanreference=span,discoursereferent=referent,
        assertsdescribedcontent=claim,textbefore=before,nonliteralpropertypresentation=figurative)
    values.update({voc._symbols[n]:f for n,f in handlers.items()})
    return values


def test_all_source_bodies_and_prior_statements_are_preserved():
    doc=check.restored()['document']
    assert check.backprojection(doc)==check.source_excerpt()
    assert len(check.source_excerpt()['declarations'])==180 and len(doc['statements'])==6
    assert doc['statements'][:4]==check.previous.document()['statements']
    ds={d['name']:d for d in doc['declarations']}
    for name in ('mw','mv','qb','population_span','nature_span'):assert ds[check.names()[name]]['kind']=='definition'


def test_whole_sentence_preserves_attribution_and_nonliteral_direction():
    doc=check.restored()['document']
    variants={'baseline':(True,True),'wrong_author':(False,False),'wrong_context':(False,False),
        'missing_cause':(False,True),'reverse_order':(False,True),'wrong_node':(True,False),
        'reversed_depiction':(True,False),'missing_depiction':(True,False)}
    for variant,expected in variants.items():assert evaluate(doc,model(doc,variant))==[True]*4+list(expected),variant


def test_referents_are_resolved_only_when_used_and_do_not_execute_description():
    doc=deepcopy(check.restored()['document']);voc=check.vocabulary();values=model(doc)
    values[voc._symbols['discoursereferent']]=parent.parent.forbidden
    assert evaluate(doc,values)==[True]*6
    for old,expected in [('mv','population'),('qb','nature')]:
        query=deepcopy(doc);query['statements'].append(dict(kind='ask',body=dict(kind='equal',
            arguments=[call(check.names()[old]),call(check.names()['wa'])])))
        assert evaluate(query,model(query))==[True]*6+[False]
        with pytest.raises(ValueError,match='Unspecified'):evaluate(query,values)
    reference=model(doc)[voc._symbols['discoursereferent']]
    for node,expected in [('population-span','population'),('nature-span','nature')]:
        args=['document',node,1,'closing'];assert reference(*args)==expected
        for slot in range(4):
            bad=list(args);bad[slot]=2 if slot==2 else 'other'
            with pytest.raises(ValueError,match='Unknown cause referent'):reference(*bad)


def test_unknown_attribution_inputs_are_rejected():
    doc=check.restored()['document'];voc=check.vocabulary()
    for name in ('sentencereference','assertsdescribedcontent','textbefore','nonliteralpropertypresentation'):
        values=model(doc);values[voc._symbols[name]]=parent.parent.forbidden
        with pytest.raises(ValueError,match='Unspecified'):evaluate(doc,values)
