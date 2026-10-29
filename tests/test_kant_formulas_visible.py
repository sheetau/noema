"""Keep apposition, reformulation, nonliteral depiction and text order distinct."""
from copy import deepcopy
import json
import pytest
from noema.constructed_semantics import evaluate_document
from scripts import check_kant_formulas_visible as check
from scripts.shared_modality import call,renamed
import test_kant_affection_visible as parent

REFERENCES={'h2d':'formulas','conditional_sentence':'conditional-sentence','h3a':'conditional',
    'hk2':'reformulation','hzzzj':'subject','hzzzk':'apposition'}
DOMAIN=parent.DOMAIN+tuple(REFERENCES.values())


def evaluate(doc,values,memo=True):
    return [r['value'] for r in evaluate_document(doc,individuals=DOMAIN,situations=('body','closing','other'),
        primitives=values,max_steps=1000000,memoize_definitions=memo,memoize_expressions=memo)]


def model(doc,variant='baseline',bits=(True,)*9):
    values=parent.model(doc);voc=check.vocabulary();m=check.mapping();inverse={v:k for k,v in m.items()}
    oldsentence=values[voc._symbols['sentencereference']];oldspan=values[voc._symbols['sentencetokenspanreference']]
    oldclaim,olddepiction,oldorder=[values[m[n]] for n in ('uc','rbt','ue')]
    author='other' if variant=='other_author' else 'author';point='closing' if variant=='other_context' else 'body'
    def code(description,rank=0):
        assert description.rank==rank
        return renamed(json.loads(description.syntax),inverse)
    def function(name):return dict(kind='function_ref',symbol=name)
    def sentence(context,paragraph,index):
        if context=='closing' and paragraph==3 and index in (3,4):
            return 'formulas' if index==3 else 'conditional-sentence'
        return oldsentence(context,paragraph,index)
    def span(document,first,a,last,b,context):
        if first in ('formulas','conditional-sentence'):
            for name,row in check.read(check.ANCHORS)['source_spans'].items():
                node=REFERENCES[row['sentence_reference']]
                if (document,first,a,last,b,context)==('document',node,row['first_token'],node,row['last_token'],'closing'):
                    return REFERENCES[name]
            raise ValueError('Unknown formulas text span')
        return oldspan(document,first,a,last,b,context)
    def reformulation(node,a,earlier,replacement,p):
        first,last=('hn2','hm2') if variant=='reversed_reformulation' else ('hm2','hn2')
        if variant=='repeated_description':last=first
        return bits[0] and (node,a,p)==('subject' if variant=='wrong_reformulation_node' else 'reformulation',author,point) and code(earlier)==function(first) and code(replacement)==function(last)
    def claim(node,a,description,p):
        if node=='formulas':return bits[1] and (node,a,p)==('other' if variant=='wrong_claim_node' else 'formulas',author,point) and code(description)==call('r2fu' if variant=='obsolete_claim' else 'r2gc')
        return oldclaim(node,a,description,p)
    def depiction(node,a,target,depicted,p):
        if node=='formulas':
            target_name,depicted_name=('h2b','r2gd') if variant=='reversed_depiction' else ('r2gd','h2b')
            if variant=='obsolete_depiction_target':target_name='r2g3'
            return bits[2] and (node,a,p)==('subject' if variant=='wrong_depiction_node' else 'formulas',author,point) and code(target)==function(target_name) and code(depicted)==function(depicted_name)
        return olddepiction(node,a,target,depicted,p)
    def denotes(node,a,description,scope,p):
        if node not in ('subject','apposition'):return False
        expected='r2fg' if variant=='different_apposition_property' and node=='apposition' else 'r2fh'
        return bits[3 if node=='subject' else 4] and (a,scope,p)==(author,'subject' if variant=='wrong_apposition_scope' else 'formulas',point) and code(description,1)==function(expected)
    def clarifies(first,second,a,scope,p):
        expected=('apposition','subject') if variant=='reversed_clarification' else ('subject','apposition')
        return bits[6] and (first,second,a,scope,p)==(*expected,author,'formulas',point)
    def order(first,last,p):
        if (first,last)==('subject','apposition'):return bits[5] and p==point
        if (first,last)==('apposition','subject'):return variant=='both_apposition_directions' and p==point
        if (first,last)==('affection','formulas'):return bits[7] and p==point and variant!='reversed_previous_order'
        if (first,last)==('formulas','conditional'):return bits[8] and p==point and variant!='reversed_next_order'
        return oldorder(first,last,p)
    values[voc._symbols['sentencereference']]=sentence;values[voc._symbols['sentencetokenspanreference']]=span
    values.update({m[n]:fn for n,fn in dict(rbf=reformulation,uc=claim,rbt=depiction,ibbdenotes=denotes,ibbclarifies=clarifies,ue=order).items()})
    return values


def test_complete_source_and_prior_statements_are_preserved():
    doc=check.restored()['document']
    assert check.backprojection(doc)==check.source_excerpt()
    assert check.specialized_backprojection(doc)==check.specialized_source()
    assert doc['statements'][:29]==check.previous.document()['statements']
    assert len(doc['declarations'])==746 and len(doc['statements'])==31
    assert len(check.source_excerpt()['declarations'])==723


def test_reformulation_apposition_depiction_and_each_order_edge_are_independent():
    doc=check.restored()['document']
    both=('other_author','other_context','reversed_reformulation','repeated_description','wrong_reformulation_node')
    variants=('baseline',*both,'wrong_claim_node','obsolete_claim','reversed_depiction','obsolete_depiction_target',
        'wrong_depiction_node','different_apposition_property','wrong_apposition_scope','reversed_clarification',
        'both_apposition_directions','reversed_previous_order','reversed_next_order')
    for variant in variants:
        assert evaluate(doc,model(doc,variant))==[True]*29+[variant not in both,variant=='baseline'],variant
    new=deepcopy(doc);new['statements']=new['statements'][29:]
    assert evaluate(new,model(new),memo=False)==[True,True]
    for slot in range(9):
        bits=[True]*9;bits[slot]=False
        assert evaluate(new,model(new,bits=tuple(bits)),memo=False)==[slot!=0,False],slot


def test_unknown_required_reports_and_references_are_not_false_claims():
    doc=deepcopy(check.restored()['document']);doc['statements']=doc['statements'][29:]
    def unknown(*args):raise ValueError('Unspecified formulas relation')
    for name in ('rbf','uc','rbt','ibbdenotes','ibbclarifies','ue'):
        with pytest.raises(ValueError,match='Unspecified formulas relation'):
            evaluate(doc,model(doc)|{check.mapping()[name]:unknown})
    with pytest.raises(ValueError,match='Unspecified formulas relation'):
        evaluate(doc,model(doc,bits=(True,False,*((True,)*7)))|{check.mapping()['ibbdenotes']:unknown})


def test_actual_spans_distinguish_following_clause_from_its_reason():
    doc=deepcopy(check.restored()['document']);m=check.mapping()
    doc['declarations'].append(dict(kind='primitive',name='jexpected',parameters=[],result='individual'))
    doc['statements']=[dict(kind='ask',body=dict(kind='equal',arguments=[call(m[n]),call('jexpected')])) for n in REFERENCES]
    for i,target in enumerate(REFERENCES.values()):
        expected=[False]*len(REFERENCES);expected[i]=True
        assert evaluate(doc,model(doc)|{'jexpected':lambda target=target:target})==expected
    values=model(doc);name=check.vocabulary()._symbols['sentencetokenspanreference'];old=values[name]
    def wrong_end(document,first,a,last,b,context):
        return old(document,first,a,last,b+1 if first=='conditional-sentence' else b,context)
    with pytest.raises(ValueError,match='Unknown formulas text span'):
        evaluate(doc,values|{name:wrong_end,'jexpected':lambda:'conditional'})
    def wrong_sentence(document,first,a,last,b,context):
        node='formulas' if first=='conditional-sentence' else first
        return old(document,node,a,node,b,context)
    with pytest.raises(ValueError,match='Unknown formulas text span'):
        evaluate(doc,values|{name:wrong_sentence,'jexpected':lambda:'conditional'})
