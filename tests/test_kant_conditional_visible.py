"""Preserve the reasoned conditional and its six paired metaphor descriptions."""
from copy import deepcopy
import json
import pytest
from noema.constructed_semantics import evaluate_document
from scripts import check_kant_conditional_visible as check
from scripts.check_attributed_focus import unwrap
from scripts.shared_modality import call,renamed
import test_kant_formulas_visible as parent

DOMAIN=parent.DOMAIN
SMALL_DOMAIN=('use','designation','author','document','reader','other','first','second',
 'emancipation','affection','formulas','conditional-sentence','conditional','reformulation','subject','apposition')
PAIRS=(('conditional','r2gt','h3n'),('conditional','r2ie','r2iu'),
 ('conditional-sentence','r2hf','r2ir'),('conditional-sentence','r2hh','r2is'),
 ('conditional-sentence','r2if','r2iw'),('conditional-sentence','r2ii','r2ix'))


def evaluate(doc,values,memo=True,domain=SMALL_DOMAIN):
    return [r['value'] for r in evaluate_document(doc,individuals=domain,situations=('body','closing','other'),
        primitives=values,max_steps=20000000,memoize_definitions=memo,memoize_expressions=memo)]


def model(doc,variant='baseline',bits=(True,)*12):
    values=parent.model(doc);voc=check.vocabulary();m=check.mapping();inverse={v:k for k,v in m.items()}
    oldfg,oldbg,oldorder,oldpair=[values[m[n]] for n in ('hznreport','hzrbgreport','ue','qa')]
    def code(description,rank=0):
        assert description.rank==rank
        return renamed(json.loads(description.syntax),inverse)
    def function(n):return dict(kind='function_ref',symbol=n)
    def fg(node,author,description,scope,point):
        if node=='conditional-sentence':
            return bits[0] and (author,scope,point)==('author',
                'conditional' if variant=='wrong_foreground_scope' else 'conditional-sentence','body') and renamed(unwrap(description),inverse)==call('r2ii' if variant=='obsolete_foreground' else 'r2ik')
        return oldfg(node,author,description,scope,point)
    def bg(node,author,foreground,background,fs,bs,point):
        if node=='conditional-sentence':
            return bits[1] and (author,fs,bs,point)==('author','conditional-sentence',
                'conditional-sentence' if variant=='wrong_background_scope' else 'conditional','body') and renamed(unwrap(foreground),inverse)==call('r2ik') and renamed(unwrap(background),inverse)==call('r2ii' if variant=='obsolete_background' else 'r2il')
        return oldbg(node,author,foreground,background,fs,bs,point)
    def before(first,last,point):
        if (first,last)==('conditional','conditional-sentence'):return bits[2] and point=='body' and variant!='missing_reason_order'
        if (first,last)==('conditional','formulas'):return variant=='reversed_antecedent_order' and point=='body'
        return oldorder(first,last,point)
    def target(antecedent,author,kind,person,obj,scope):
        return bits[10] and (antecedent,author,person,obj,scope)==(
            'affection' if variant=='wrong_antecedent' else 'formulas',
            'other' if variant=='other_author' else 'author','reader','second',
            'closing' if variant=='other_context' else 'body') and code(kind,1)==function('r2fg' if variant=='wrong_kind' else 'r2fh')
    def correspondence(node,antecedent,author,person,depicted,obj,scope):
        wanted=('conditional','formulas','author','reader','first','second','body')
        actual=(node,antecedent,author,person,depicted,obj,scope)
        if variant=='reversed_correspondence':wanted=('conditional','formulas','author','reader','second','first','body')
        if variant=='outsider_correspondence' and actual==('conditional','formulas','author','other','first','second','body'):return True
        return bits[11] and actual==wanted
    def paired(node,author,target_description,depicted_description,point):
        if node not in ('conditional','conditional-sentence'):return oldpair(node,author,target_description,depicted_description,point)
        if (author,point)!=('author','body'):return False
        target_code,depicted_code=code(target_description),code(depicted_description)
        for i,(scope,left,right) in enumerate(PAIRS):
            if variant=='reversed_pair_'+str(i):left,right=right,left
            if variant=='wrong_pair_scope_'+str(i):scope='conditional-sentence' if scope=='conditional' else 'conditional'
            if node==scope and target_code==function(left) and depicted_code==function(right):return bits[3+i]
        return False
    values.update({m[n]:fn for n,fn in dict(
        aa=lambda person:person=='reader' and variant!='nonhuman_person',
        hzzn=lambda node,person,scope:(node,person,scope)==('emancipation','reader','body'),
        h2s=lambda obj,person,scope:bits[9] and (obj,person,scope)==('first','reader','body'),
        hzzzm=target,hzzzn=correspondence,hznreport=fg,hzrbgreport=bg,ue=before,qa=paired).items()})
    return values


def new_statements():
    doc=deepcopy(check.restored()['document']);doc['statements']=doc['statements'][31:]
    return doc


def test_complete_source_and_prior_statements_are_preserved():
    doc=check.restored()['document']
    assert check.backprojection(doc)==check.source_excerpt()
    assert check.specialized_backprojection(doc)==check.specialized_source()
    assert doc['statements'][:31]==check.previous.document()['statements']
    assert (len(doc['declarations']),len(doc['statements']))==(851,33)
    assert len(check.source_excerpt()['declarations'])==828
    assert evaluate(doc,model(doc),domain=DOMAIN)==[True]*33


def test_conditional_attribution_and_all_six_correspondences_are_independent():
    doc=new_statements()
    both=('wrong_antecedent','other_author','other_context','wrong_kind','reversed_correspondence',
        'outsider_correspondence','nonhuman_person','reversed_antecedent_order')
    first=('wrong_foreground_scope','wrong_background_scope','obsolete_foreground','obsolete_background','missing_reason_order')
    for variant in ('baseline',*both,*first):
        assert evaluate(doc,model(doc,variant))==[variant=='baseline',variant not in both],variant
    for i in range(6):
        for prefix in ('reversed_pair_','wrong_pair_scope_'):
            assert evaluate(doc,model(doc,prefix+str(i)))==[True,False],(prefix,i)
    # Evaluate one complete new group without memoization as a separate diagnostic.
    assert evaluate(doc,model(doc),memo=False)==[True,True]
    for slot in range(12):
        bits=[True]*12;bits[slot]=False
        assert evaluate(doc,model(doc,bits=tuple(bits)))==[3<=slot<=8,slot<=2],slot


def test_unknown_correspondences_and_reports_are_not_false_claims():
    doc=new_statements()
    def unknown(*args):raise ValueError('Unspecified conditional relation')
    for name in ('aa','hzzn','h2s','hzzzm','hzzzn','hznreport','hzrbgreport','qa','ue'):
        with pytest.raises(ValueError,match='Unspecified conditional relation'):
            evaluate(doc,model(doc)|{check.mapping()[name]:unknown})
    with pytest.raises(ValueError,match='Unspecified conditional relation'):
        evaluate(doc,model(doc,bits=(False,*((True,)*11)))|{check.mapping()['hzrbgreport']:unknown})


def test_reasoned_whole_reuses_sentence_but_preserves_the_shorter_condition_span():
    doc=new_statements();m=check.mapping()
    doc['declarations'].append(dict(kind='primitive',name='jexpected',parameters=[],result='individual'))
    refs=('h3s','conditional_sentence','h3a')
    doc['statements']=[dict(kind='ask',body=dict(kind='equal',arguments=[call(m[n]),call('jexpected')])) for n in refs]
    for target,expected in [('conditional-sentence',[True,True,False]),('conditional',[False,False,True])]:
        assert evaluate(doc,model(doc)|{'jexpected':lambda target=target:target})==expected
    changed=deepcopy(doc)
    next(d for d in changed['declarations'] if d['name']==m['h3s'])['body']=call(m['h3a'])
    assert evaluate(changed,model(changed)|{'jexpected':lambda:'conditional-sentence'})==[False,True,False]
