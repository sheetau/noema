"""Keep affection foreground, expectation focus and incapacity assurance separate."""
from copy import deepcopy
import json
import pytest
from noema.constructed_semantics import evaluate_document
from scripts import check_kant_affection_visible as check
from scripts.check_affection_sentence import expected_background
from scripts.check_attributed_focus import unwrap
from scripts.shared_modality import call,renamed
import test_kant_emancipation_visible as parent

DOMAIN=parent.DOMAIN+('affection','affection-whole','affection-focus')


def evaluate(doc,values,memo=True):
    return [r['value'] for r in evaluate_document(doc,individuals=DOMAIN,situations=('body','closing','other'),
        primitives=values,max_steps=1000000,memoize_definitions=memo,memoize_expressions=memo)]


def model(doc,variant='baseline',bits=(True,)*4):
    values=parent.model(doc);voc=check.vocabulary();m=check.mapping();inverse={v:k for k,v in m.items()}
    oldsentence=values[voc._symbols['sentencereference']];oldspan=values[voc._symbols['sentencetokenspanreference']]
    prior={n:values[m[n]] for n in ('hznreport','hzrbgreport','hzxu','ue')}
    foreground=call('r2eg' if variant=='only_attachment_foreground' else 'r2ei');background=deepcopy(expected_background())
    if variant=='whole_sentence_expectation_focus':background['arguments'][0]['body']['symbol']='r2ei'
    if variant=='wrong_expectation_comparison':background['arguments'][1]['items'][0]['body']['symbol']='r2ei'
    node='other' if variant=='other_node' else 'affection'
    author='other' if variant=='other_author' else 'author';point='closing' if variant=='other_context' else 'body'
    whole='affection-focus' if variant=='wrong_foreground_scope' else 'affection-whole'
    focus='affection-whole' if variant=='wrong_background_scope' else 'affection-focus'
    assurance=[node,author,call('r2ei'),call('r2en'),point]
    changes={'assurance_other_node':(0,'other'),'assurance_other_author':(1,'other'),
        'assurance_other_context':(4,'closing'),'assurance_attachment_claim':(2,call('r2eg')),
        'assurance_whole_claim_focus':(3,call('r2ei')),'assurance_attachment_focus':(3,call('r2eg')),
        'assurance_nature_focus':(3,call('r2eh'))}
    if variant in changes:
        slot,value=changes[variant];assurance[slot]=value
    def sentence(context,paragraph,index):
        if (context,paragraph,index)==('closing',3,2):return 'affection'
        return oldsentence(context,paragraph,index)
    def span(document,first,a,last,b,context):
        if (document,first,last,context)==('document','affection','affection','closing'):
            for key,target in [('hzzs','affection-whole'),('hzzt','affection-focus')]:
                row=check.read(check.ANCHORS)['source_spans'][key]
                if (a,b)==(row['first_token'],row['last_token']):return target
            raise ValueError('Unknown affection text span')
        return oldspan(document,first,a,last,b,context)
    def fg(n,a,code,scope,p):
        if n=='affection':return bits[0] and (n,a,scope,p)==(node,author,whole,point) and renamed(unwrap(code),inverse)==foreground
        return prior['hznreport'](n,a,code,scope,p)
    def bg(n,a,code,bgcode,fs,bs,p):
        if n=='affection':return bits[1] and (n,a,fs,bs,p)==(node,author,whole,focus,point) and renamed(unwrap(code),inverse)==foreground and renamed(unwrap(bgcode),inverse)==background
        return prior['hzrbgreport'](n,a,code,bgcode,fs,bs,p)
    def assured(n,a,claim,part,p):
        if n=='affection':return bits[2] and [n,a,renamed(json.loads(claim.syntax),inverse),renamed(json.loads(part.syntax),inverse),p]==assurance
        return prior['hzxu'](n,a,claim,part,p)
    def order(first,last,p):
        if last=='affection':return bits[3] and (first,last,p)==(('affection','emancipation',point) if variant=='reversed_order' else ('emancipation',node,point))
        return prior['ue'](first,last,p)
    values[voc._symbols['sentencereference']]=sentence;values[voc._symbols['sentencetokenspanreference']]=span
    values.update({m[n]:fn for n,fn in dict(hznreport=fg,hzrbgreport=bg,hzxu=assured,ue=order).items()})
    return values


def test_complete_source_and_prior_statements_are_preserved():
    doc=check.restored()['document']
    assert check.backprojection(doc)==check.source_excerpt()
    assert check.specialized_backprojection(doc)==check.specialized_source()
    assert doc['statements'][:27]==check.previous.document()['statements']
    assert len(doc['declarations'])==683 and len(doc['statements'])==29
    assert len(check.source_excerpt()['declarations'])==661


def test_foreground_background_assurance_and_order_remain_distinct():
    doc=check.restored()['document']
    variants=('baseline','other_author','other_node','other_context','wrong_foreground_scope','wrong_background_scope',
        'only_attachment_foreground','whole_sentence_expectation_focus','wrong_expectation_comparison','reversed_order',
        'assurance_other_node','assurance_other_author','assurance_other_context','assurance_attachment_claim',
        'assurance_whole_claim_focus','assurance_attachment_focus','assurance_nature_focus')
    for variant in variants:
        wanted=[variant in ('baseline','reversed_order'),variant not in ('other_node','other_context','reversed_order')]
        assert evaluate(doc,model(doc,variant))==[True]*27+wanted,variant
    new=deepcopy(doc);new['statements']=new['statements'][27:]
    assert evaluate(new,model(new),memo=False)==[True,True]
    for slot in range(4):
        bits=[True]*4;bits[slot]=False
        assert evaluate(new,model(new,bits=tuple(bits)),memo=False)==[slot==3,slot!=3]


def test_unknown_required_attributions_are_not_false_claims():
    doc=deepcopy(check.restored()['document']);doc['statements']=doc['statements'][27:]
    def unknown(*args):raise ValueError('Unspecified affection attribution')
    for name in ('hznreport','hzrbgreport','hzxu','ue'):
        with pytest.raises(ValueError,match='Unspecified affection attribution'):
            evaluate(doc,model(doc)|{check.mapping()[name]:unknown})
    with pytest.raises(ValueError,match='Unspecified affection attribution'):
        evaluate(doc,model(doc,bits=(False,True,True,True))|{check.mapping()['hzrbgreport']:unknown})


def test_whole_sentence_and_focus_use_the_actual_token_ranges():
    doc=deepcopy(check.restored()['document']);m=check.mapping()
    doc['declarations'].append(dict(kind='primitive',name='jexpected',parameters=[],result='individual'))
    doc['statements']=[dict(kind='ask',body=dict(kind='equal',arguments=[call(m[n]),call('jexpected')])) for n in ('hzzr','hzzs','hzzt')]
    for i,target in enumerate(('affection','affection-whole','affection-focus')):
        expected=[False]*3;expected[i]=True
        assert evaluate(doc,model(doc)|{'jexpected':lambda target=target:target})==expected
    values=model(doc);name=check.vocabulary()._symbols['sentencetokenspanreference'];old=values[name]
    def wrong_span(document,first,a,last,b,context):
        return old(document,first,a+1 if first=='affection' else a,last,b,context)
    with pytest.raises(ValueError,match='Unknown affection text span'):
        evaluate(doc,values|{name:wrong_span,'jexpected':lambda:'affection'})
