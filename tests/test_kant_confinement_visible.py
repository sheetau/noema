"""Keep the compound warning sentence and its distinct nonliteral presentations."""
from copy import deepcopy
import json
import pytest
from noema.constructed_semantics import evaluate_document
from scripts import check_kant_confinement_visible as check
from scripts.shared_modality import call,renamed
import test_kant_guardians_visible as parent

# This statement actually uses the earlier group as a viewpoint, beyond quoting it.
DOMAIN=parent.DOMAIN+('confinement','livestock-span','guardians-span','guardians')


def evaluate(doc,values,domain=DOMAIN,memo=True):
    return [r['value'] for r in evaluate_document(doc,individuals=domain,situations=('body','closing','other'),
        primitives=values,max_steps=1000000,memoize_definitions=memo,memoize_expressions=memo)]


def model(doc,variant='baseline'):
    values=parent.model(doc);voc=check.vocabulary();inverse={v:k for k,v in check.mapping().items()}
    syntax=lambda code:renamed(json.loads(code.syntax),inverse)
    name=lambda code:syntax(code)['symbol']
    oldsentence=values[voc._symbols['sentencereference']]
    oldspan=values[voc._symbols['sentencetokenspanreference']]
    oldreferent=values[voc._symbols['discoursereferent']]
    oldclaim=values[voc._symbols['assertsdescribedcontent']]
    oldbefore=values[voc._symbols['textbefore']]
    olddepiction=values[voc._symbols['nonliteralpropertypresentation']]
    def sentence(context,paragraph,index):
        if (context,paragraph,index)==('closing',2,6):return 'confinement'
        return oldsentence(context,paragraph,index)
    anchors=check.read(check.ANCHORS)
    def span(document,first,a,last,b,context):
        if (document,first,last,context)==('document','confinement','confinement','closing'):
            for key,target in [('qp','livestock-span'),('permission_span','permission-span')]:
                row=anchors['source_spans'][key]
                if (a,b)==(row['first_token'],row['last_token']):return target
            raise ValueError('Unknown confinement span')
        return oldspan(document,first,a,last,b,context)
    def referent(document,node,ordinal,context):
        if node=='permission-span':
            if (document,ordinal,context)==('document',1,'closing'):return 'supervised'
            raise ValueError('Unknown permission-role referent')
        return oldreferent(document,node,ordinal,context)
    def claim(node,author,code,context):
        if node=='confinement':return variant!='no_claim' and (author,syntax(code),context)==(
            'author',call('r2am',call('mv' if variant=='wrong_claim_group' else 'db')),'body')
        return oldclaim(node,author,code,context)
    def before(first,second,context):
        if (first,second)==('guardian','confinement'):return context=='body' and variant!='no_order'
        return oldbefore(first,second,context)
    def depiction(node,author,target,depicted,context):
        if node=='livestock-span':
            return variant!='no_livestock' and (author,name(target),name(depicted),context)==(
                'author','qk' if variant=='reverse_livestock' else 'qj','qj' if variant=='reverse_livestock' else 'qk','body')
        if node=='confinement':
            return variant!='no_danger_depiction' and (author,name(target),name(depicted),context)==('author','eu','rqy4','body')
        return olddepiction(node,author,target,depicted,context)
    def phase(node,author,claimed,target,depicted,context):
        expected_claim=call('r2am',call('mv' if variant=='wrong_phase_claim' else 'db'))
        if (node,author,syntax(claimed),name(target),context)!=('confinement','author',expected_claim,
                'rqzx' if variant=='wrong_phase_target' else 'r2an','closing' if variant=='wrong_phase_context' else 'body'):return False
        return name(depicted) in {'r2af','rqzx','rqz7'} and variant!='no_'+name(depicted)
    def insistence(node,author,claimed,viewpoint,focus,context):
        return variant!='no_insistence' and (node,author,syntax(claimed),viewpoint,name(focus),context)==(
            'confinement','author',call('r2am',call('mv' if variant=='wrong_insistence_claim' else 'db')),
            'author' if variant=='wrong_viewpoint' else 'guardians',
            'r2an' if variant=='wrong_insistence_focus' else 'rqzx','body')
    handlers=dict(sentencereference=sentence,sentencetokenspanreference=span,discoursereferent=referent,
        assertsdescribedcontent=claim,textbefore=before,nonliteralpropertypresentation=depiction,
        nonliteralphaserelationpresentation=phase,insistentviewpointpresentation=insistence)
    values.update({voc._symbols[n]:f for n,f in handlers.items()})
    return values


def test_complete_source_and_prior_statements_are_preserved():
    doc=check.restored()['document']
    assert check.backprojection(doc)==check.source_excerpt()
    assert check.specialized_backprojection(doc)==check.specialized_source()
    assert doc['statements'][:15]==check.previous.document()['statements']
    assert len(doc['declarations'])==497 and len(doc['statements'])==22
    assert len(check.source_excerpt()['declarations'])==477


def test_full_document_keeps_phase_claim_viewpoint_and_depiction_distinct():
    doc=check.restored()['document']
    variants=('baseline','no_claim','wrong_claim_group','no_order','no_livestock','reverse_livestock',
        'no_danger_depiction','no_r2af','no_rqzx','no_rqz7','wrong_phase_claim','wrong_phase_target',
        'wrong_phase_context','no_insistence','wrong_viewpoint','wrong_insistence_claim','wrong_insistence_focus')
    for variant in variants:
        claims=variant not in ('no_claim','wrong_claim_group')
        phase=variant not in ('wrong_phase_claim','wrong_phase_target','wrong_phase_context')
        expected=[variant not in ('no_livestock','reverse_livestock'),claims and variant!='no_order',
            phase and variant!='no_r2af',variant!='no_danger_depiction',phase and variant!='no_rqzx',
            phase and variant!='no_rqz7',claims and phase and variant not in ('no_rqzx','no_insistence',
                'wrong_viewpoint','wrong_insistence_claim','wrong_insistence_focus')]
        assert evaluate(doc,model(doc,variant))==[True]*15+expected,variant
    # The new assertions also run without memoization; the extra referents need
    # not multiply the unrelated earlier paragraph's finite attribution search.
    new=deepcopy(doc);new['statements']=new['statements'][15:]
    assert evaluate(new,model(new),memo=False)==[True]*7


def test_unknown_presentation_and_viewpoint_inputs_are_rejected():
    doc=check.restored()['document'];voc=check.vocabulary()
    def unknown(*args):raise ValueError('Unspecified confinement input')
    for name in ('nonliteralphaserelationpresentation','insistentviewpointpresentation'):
        with pytest.raises(ValueError,match='Unspecified'):
            evaluate(doc,model(doc)|{voc._symbols[name]:unknown})
    values=model(doc);old=values[voc._symbols['discoursereferent']]
    def scoped(document,node,*args):return unknown() if node=='guardians-span' else old(document,node,*args)
    with pytest.raises(ValueError,match='Unspecified'):
        evaluate(doc,values|{voc._symbols['discoursereferent']:scoped})


def test_sentence_span_and_permission_role_are_explicit_references():
    doc=check.restored()['document'];ds={d['name']:d for d in doc['declarations']};voc=check.vocabulary()
    assert ds[check.names()['hzsq']]['body']['symbol']==voc._symbols['sentencereference']
    assert ds[check.names()['qp']]['body']['symbol']==voc._symbols['sentencetokenspanreference']
    assert ds[check.names()['hztd']]['body']['symbol']==voc._symbols['discoursereferent']
    bad=deepcopy(doc);d=next(d for d in bad['declarations'] if d['name']==check.names()['qp'])
    d['body']['arguments'][2]=check.num(1)
    with pytest.raises(ValueError,match='Unknown confinement span'):evaluate(bad,model(bad))
    query=deepcopy(doc);query['statements']=[dict(kind='ask',body=dict(kind='equal',
        arguments=[call(check.names()['hztd']),call(check.names()['wa'])]))]
    domain=DOMAIN+('permission-span','supervised')
    assert evaluate(query,model(query),domain,memo=False)==[False]
    bad=deepcopy(query);d=next(d for d in bad['declarations'] if d['name']==check.names()['hztd'])
    d['body']['arguments'][2]=check.num(2)
    with pytest.raises(ValueError,match='Unknown permission-role referent'):evaluate(bad,model(bad),domain,memo=False)
