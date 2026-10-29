"""Preserve guardian attribution, evaluation distance and ordered addition."""
from copy import deepcopy
import json
import pytest
from noema.constructed_semantics import evaluate_document
from scripts import check_kant_guardians_visible as check
from scripts.shared_modality import call,renamed
import test_kant_payment_visible as parent

DOMAIN=parent.DOMAIN+('guardian',)


def evaluate(doc,values,domain=DOMAIN):
    return [r['value'] for r in evaluate_document(doc,individuals=domain,situations=('body','closing','other'),
        primitives=values,max_steps=1000000,memoize_definitions=False,memoize_expressions=False)]


def model(doc,variant='baseline'):
    values=parent.model(doc);voc=check.vocabulary();inverse={v:k for k,v in check.mapping().items()}
    syntax=lambda code:renamed(json.loads(code.syntax),inverse)
    name=lambda code:syntax(code)['symbol']
    oldsentence=values[voc._symbols['sentencereference']]
    oldspan=values[voc._symbols['sentencetokenspanreference']]
    oldreferent=values[voc._symbols['discoursereferent']]
    oldclaim=values[voc._symbols['assertsdescribedcontent']]
    oldbefore=values[voc._symbols['textbefore']]
    def sentence(context,paragraph,index):
        if (context,paragraph,index)==('closing',2,5):return 'guardian'
        return oldsentence(context,paragraph,index)
    anchors=check.read(check.ANCHORS);bounds=anchors['source_spans']['guardians_span']
    def span(document,first,a,last,b,context):
        if (document,first,last,context)==('document','guardian','guardian','closing'):
            if (a,b)==(bounds['first_token'],bounds['last_token']):return 'guardians-span'
            raise ValueError('Unknown guardian span')
        return oldspan(document,first,a,last,b,context)
    def referent(document,node,ordinal,context):
        if node=='guardians-span':
            if (document,ordinal,context)==('document',1,'closing'):return 'guardians'
            raise ValueError('Unknown guardian referent')
        return oldreferent(document,node,ordinal,context)
    def claim(node,author,code,context):
        if node=='guardian':return variant!='no_claim' and (author,name(code),context)==('author','dp','body')
        return oldclaim(node,author,code,context)
    def before(first,second,context):
        if (first,second)==('payment','guardian'):return context=='body' and variant!='no_order'
        return oldbefore(first,second,context)
    def label(node,author,p,q,context):
        return variant!='no_label' and (node,author,name(p),name(q),context)==('guardian','author','dr','ds','body')
    def framed(node,author,p,q,r,context):
        return variant!='no_frame' and (node,author,name(p),name(q),name(r),context)==('guardian','author','dp','rqyl','rqyp','body')
    def distance(node,author,p,q,r,context):
        return variant!='no_distance' and (node,author,name(p),name(q),name(r),context)==('guardian','author','dp','rqyl','rqyp','body')
    def assurance(node,author,p,q,context):
        return variant!='no_assurance' and (node,author,name(p),syntax(q),context)==(
            'guardian','author','un' if variant=='other_claim' else 'dp',
            call('do' if variant=='other_focus' else 'rqyx',call('mv' if variant=='other_group' else 'db')),
            'closing' if variant=='other_context' else 'body')
    def addition(node,author,p,q,r,context):
        return variant!='no_addition' and (node,author,name(p),name(q),name(r),context)==(
            'guardian','author','un' if variant=='other_additive_claim' else 'dp',
            'ux' if variant=='reversed_addition' else 'uy',
            'uy' if variant=='reversed_addition' else 'uw' if variant=='actual_risk' else 'ux',
            'closing' if variant=='other_additive_context' else 'body')
    handlers=dict(sentencereference=sentence,sentencetokenspanreference=span,discoursereferent=referent,
        assertsdescribedcontent=claim,textbefore=before,propertylabelpresentation=label,
        favorableeventpresentation=framed,criticalevaluationdistance=distance,
        focusedclaimassurance=assurance,additivepropertypresentation=addition)
    values.update({voc._symbols[n]:f for n,f in handlers.items()})
    return values


def test_whole_source_and_inherited_specialization_are_preserved():
    doc=check.restored()['document']
    assert check.backprojection(doc)==check.source_excerpt()
    assert check.specialized_backprojection(doc)==check.specialized_source()
    assert doc['statements'][:11]==check.previous.document()['statements']
    assert len(doc['declarations'])==369 and len(doc['statements'])==15
    assert len(check.source_excerpt()['declarations'])==350


def test_whole_sentence_keeps_claim_focus_distance_and_addition_separate():
    doc=check.restored()['document']
    for variant in ('baseline','no_claim','no_order','no_label','no_frame','no_distance',
        'no_assurance','other_claim','other_focus','other_group','other_context','no_addition',
        'other_additive_claim','reversed_addition','actual_risk','other_additive_context'):
        expected=[variant not in ('no_claim','no_order'),variant!='no_label',
            variant not in ('no_claim','no_frame','no_distance'),
            variant in ('baseline','no_order','no_label','no_frame','no_distance')]
        assert evaluate(doc,model(doc,variant))==[True]*11+expected,variant


def test_unknown_presentations_are_rejected_without_executing_world_content():
    doc=check.restored()['document'];voc=check.vocabulary()
    def unknown(*args):raise ValueError('Unspecified guardian input')
    for name in ('propertylabelpresentation','favorableeventpresentation','criticalevaluationdistance',
            'focusedclaimassurance','additivepropertypresentation'):
        with pytest.raises(ValueError,match='Unspecified'):
            evaluate(doc,model(doc)|{voc._symbols[name]:unknown})
    assert evaluate(doc,model(doc)|{voc._symbols['discoursereferent']:unknown})==[True]*15


def test_reference_definitions_keep_sentence_span_and_ordinal():
    doc=check.restored()['document'];voc=check.vocabulary()
    changed=deepcopy(doc);d=next(d for d in changed['declarations'] if d['name']==check.names()['dq'])
    assert d['body']['symbol']==voc._symbols['sentencereference'];d['body']['arguments'][2]=check.num(4)
    assert evaluate(changed,model(changed))==[True]*11+[False]*4
    query=deepcopy(doc);query['statements']=[dict(kind='ask',body=dict(kind='equal',
        arguments=[call(check.names()['db']),call(check.names()['wa'])]))]
    domain=DOMAIN+('guardians-span','guardians')
    assert evaluate(query,model(query),domain)==[False]
    unknown=deepcopy(query);d=next(d for d in unknown['declarations'] if d['name']==check.names()['db'])
    d['body']['arguments'][2]=check.num(2)
    with pytest.raises(ValueError,match='Unknown guardian referent'):evaluate(unknown,model(unknown),domain)
    unknown=deepcopy(query);d=next(d for d in unknown['declarations'] if d['name']==check.names()['guardians_span'])
    d['body']['arguments'][2]=check.num(1)
    with pytest.raises(ValueError,match='Unknown guardian span'):evaluate(unknown,model(unknown),domain)
