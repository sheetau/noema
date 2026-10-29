"""Keep self-emancipation, its premises and comparison references distinct."""
from copy import deepcopy
import json
import pytest
from noema.constructed_semantics import evaluate_document
from scripts import check_kant_emancipation_visible as check
from scripts.shared_modality import call,renamed
import test_kant_learning_visible as parent

DOMAIN=parent.DOMAIN+('emancipation',)
PREMISES=('causal','convenience','illustration','payment','confinement','outcome')
REFERENCES={'naturecomparison_span':'constitution-span','effortcomparison_span':'effort-span',
    'hzzo':'constitution-kind','hzzp':'effort-kind','hzzq':'emancipation'}


def evaluate(doc,values,memo=True,domain=DOMAIN):
    return [r['value'] for r in evaluate_document(doc,individuals=domain,situations=('body','closing','other'),
        primitives=values,max_steps=1000000,memoize_definitions=memo,memoize_expressions=memo)]


def model(doc,variant='baseline',bits=(True,)*8):
    values=parent.model(doc);voc=check.vocabulary();m=check.mapping();inverse={v:k for k,v in m.items()}
    oldsentence=values[voc._symbols['sentencereference']]
    oldspan=values[voc._symbols['sentencetokenspanreference']]
    oldreferent=values[voc._symbols['discoursereferent']]
    oldclaim,oldreason,oldorder=[values[m[n]] for n in ('uc','ud','ue')]
    def sentence(context,paragraph,index):
        if (context,paragraph,index)==('closing',3,1):return 'emancipation'
        return oldsentence(context,paragraph,index)
    def span(document,first,a,last,b,context):
        if (document,first,last,context)==('document','emancipation','emancipation','closing'):
            for key,row in check.read(check.ANCHORS)['source_spans'].items():
                if (a,b)==(row['first_token'],row['last_token']):return REFERENCES[key]
            raise ValueError('Unknown emancipation comparison span')
        return oldspan(document,first,a,last,b,context)
    def referent(document,node,ordinal,context):
        if node in ('constitution-span','effort-span'):
            if (document,ordinal,context)==('document',1,'closing'):
                return 'constitution-kind' if node=='constitution-span' else 'effort-kind'
            raise ValueError('Unknown emancipation comparison referent')
        return oldreferent(document,node,ordinal,context)
    def claim(node,author,content,point):
        if node=='emancipation':
            return bits[0] and (node,author,point)==(
                'other' if variant=='other_node' else 'emancipation',
                'other' if variant=='other_author' else 'author',
                'closing' if variant=='other_context' else 'body') and renamed(json.loads(content.syntax),inverse)==call(
                    'r2dy' if variant=='old_content' else 'r2ec')
        return oldclaim(node,author,content,point)
    def reason(author,premises,node,point):
        if node=='emancipation':
            return bits[1] and (author,node,point)==('author','emancipation','body') and {
                p for p in DOMAIN if premises(p)}==set(PREMISES[:-1] if variant=='wrong_premises' else PREMISES)
        return oldreason(author,premises,node,point)
    def order(first,last,point):
        if last=='emancipation':
            return first in PREMISES and bits[2+PREMISES.index(first)] and point=='body' and variant!='reversed_order'
        return oldorder(first,last,point)
    for name,fn in dict(sentencereference=sentence,sentencetokenspanreference=span,discoursereferent=referent).items():
        values[voc._symbols[name]]=fn
    values.update({m[n]:fn for n,fn in dict(uc=claim,ud=reason,ue=order).items()})
    return values


def test_complete_source_and_prior_statements_are_preserved():
    doc=check.restored()['document']
    assert check.backprojection(doc)==check.source_excerpt()
    assert check.specialized_backprojection(doc)==check.specialized_source()
    assert doc['statements'][:26]==check.previous.document()['statements']
    assert len(doc['declarations'])==654 and len(doc['statements'])==27
    assert len(check.source_excerpt()['declarations'])==632


def test_claim_reason_and_each_of_six_order_edges_remain_independent():
    doc=check.restored()['document']
    for variant in ('baseline','old_content','other_author','other_node','other_context','wrong_premises','reversed_order'):
        assert evaluate(doc,model(doc,variant))==[True]*26+[variant=='baseline'],variant
    new=deepcopy(doc);new['statements']=new['statements'][26:]
    assert evaluate(new,model(new),memo=False)==[True]
    for slot in range(8):
        bits=[True]*8;bits[slot]=False
        assert evaluate(new,model(new,bits=tuple(bits)),memo=False)==[False],slot


def test_required_attributions_refuse_unknown_inputs():
    doc=deepcopy(check.restored()['document']);doc['statements']=doc['statements'][26:]
    def unknown(*args):raise ValueError('Unspecified emancipation attribution')
    for name in ('uc','ud','ue'):
        with pytest.raises(ValueError,match='Unspecified emancipation attribution'):
            evaluate(doc,model(doc)|{check.mapping()[name]:unknown})


def test_sentence_spans_and_comparison_kinds_use_actual_references():
    doc=deepcopy(check.restored()['document']);m=check.mapping();voc=check.vocabulary()
    doc['declarations'].append(dict(kind='primitive',name='jexpected',parameters=[],result='individual'))
    doc['statements']=[dict(kind='ask',body=dict(kind='equal',arguments=[call(m[n]),call('jexpected')])) for n in REFERENCES]
    domain=DOMAIN+tuple(v for v in REFERENCES.values() if v not in DOMAIN)
    for i,target in enumerate(REFERENCES.values()):
        expected=[False]*len(REFERENCES);expected[i]=True
        assert evaluate(doc,model(doc)|{'jexpected':lambda target=target:target},domain=domain)==expected
    values=model(doc);name=voc._symbols['sentencetokenspanreference'];old=values[name]
    def wrong_span(document,first,a,last,b,context):
        return old(document,first,a+1 if first=='emancipation' else a,last,b,context)
    with pytest.raises(ValueError,match='Unknown emancipation comparison span'):
        evaluate(doc,values|{name:wrong_span,'jexpected':lambda:'emancipation'},domain=domain)
    name=voc._symbols['discoursereferent'];oldref=values[name]
    def wrong_ordinal(document,node,ordinal,context):
        return oldref(document,node,ordinal+1 if node in ('constitution-span','effort-span') else ordinal,context)
    with pytest.raises(ValueError,match='Unknown emancipation comparison referent'):
        evaluate(doc,values|{name:wrong_ordinal,'jexpected':lambda:'emancipation'},domain=domain)
