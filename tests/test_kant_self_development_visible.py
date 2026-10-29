"""Keep the conclusion's two premises, concessive scope and depictions distinct."""
from copy import deepcopy
import json
import pytest
from noema.constructed_semantics import evaluate_document
from scripts import check_kant_self_development_visible as check
from scripts.check_attributed_focus import unwrap
from scripts.shared_modality import call,renamed
import test_kant_conditional_visible as parent

REFERENCES={'h5t':'self-development','h222d':'concession','h5f':'secure-walk'}
DOMAIN=parent.DOMAIN+tuple(REFERENCES.values())
SMALL_DOMAIN=parent.SMALL_DOMAIN+tuple(REFERENCES.values())


def evaluate(doc,values,memo=True,domain=SMALL_DOMAIN):
    return [r['value'] for r in evaluate_document(doc,individuals=domain,situations=('body','closing','other'),
        primitives=values,max_steps=20000000,memoize_definitions=memo,memoize_expressions=memo)]


def model(doc,variant='baseline',bits=(True,)*7):
    values=parent.model(doc);voc=check.vocabulary();m=check.mapping();inverse={v:k for k,v in m.items()}
    oldsentence=values[voc._symbols['sentencereference']];oldspan=values[voc._symbols['sentencetokenspanreference']]
    oldfg,oldbg,oldorder,oldpair,oldinference,oldreference=[values[m[n]] for n in ('hznreport','hzrbgreport','ue','qa','ud','hzzzn')]
    def sentence(context,paragraph,index):
        if (context,paragraph,index)==('closing',3,5):return 'self-development'
        return oldsentence(context,paragraph,index)
    def span(document,first,a,last,b,context):
        if first=='self-development':
            if (document,last,b,context)==('document','self-development',28,'closing'):
                if a==22:return 'concession'
                if a==24:return 'secure-walk'
            raise ValueError('Unknown fifth sentence span')
        return oldspan(document,first,a,last,b,context)
    def fg(node,author,description,scope,point):
        if node=='self-development':
            return bits[1] and (author,scope,point)==('author','concession' if variant=='wrong_foreground_scope' else node,'body') and renamed(unwrap(description),inverse)==call('r2kq')
        return oldfg(node,author,description,scope,point)
    def bg(node,author,foreground,background,fs,bs,point):
        if node=='self-development':
            return bits[2] and (author,fs,bs,point)==('author',node,node if variant=='wrong_background_scope' else 'concession','body') and renamed(unwrap(foreground),inverse)==call('r2kq') and renamed(unwrap(background),inverse)==call('r2kr')
        return oldbg(node,author,foreground,background,fs,bs,point)
    def inferred(author,premises,node,point):
        if node=='self-development':
            expected={'conditional','conditional-sentence'}
            if variant=='missing_reason_premise':expected.remove('conditional-sentence')
            if variant=='added_remote_premise':expected.add('formulas')
            return bits[3] and (author,point)==('author','body') and {n for n in SMALL_DOMAIN if premises(n)}==expected
        return oldinference(author,premises,node,point)
    def before(first,last,point):
        if (first,last)==('conditional-sentence','self-development'):return bits[4] and point=='body' and variant!='reversed_order'
        return oldorder(first,last,point)
    def paired(node,author,left,right,point):
        if node in ('secure-walk','self-development'):
            targets=('r2jj','h4z') if node=='secure-walk' else ('h4q','h3n')
            if variant==('reversed_walk' if node=='secure-walk' else 'reversed_release'):targets=targets[::-1]
            if variant=='obsolete_walk' and node=='secure-walk':targets=('h5e','h4z')
            actual=(renamed(json.loads(left.syntax),inverse),renamed(json.loads(right.syntax),inverse))
            return bits[0 if node=='secure-walk' else 5] and (author,point)==('author','body') and left.rank==right.rank==0 and actual==tuple(dict(kind='function_ref',symbol=n) for n in targets)
        return oldpair(node,author,left,right,point)
    values[voc._symbols['sentencereference']]=sentence;values[voc._symbols['sentencetokenspanreference']]=span
    values.update({m[n]:f for n,f in dict(hznreport=fg,hzrbgreport=bg,ud=inferred,ue=before,qa=paired,
        hzzzn=lambda *args:bits[6] and oldreference(*args)).items()})
    return values


def new_statements():
    doc=deepcopy(check.restored()['document']);doc['statements']=doc['statements'][33:]
    return doc


def test_complete_source_and_prior_group_are_preserved():
    doc=check.restored()['document']
    assert check.backprojection(doc)==check.source_excerpt()
    assert check.specialized_backprojection(doc)==check.specialized_source()
    assert doc['statements'][:33]==check.previous.document()['statements']
    assert (len(doc['declarations']),len(doc['statements']))==(901,36)
    assert len(check.source_excerpt()['declarations'])==878
    assert evaluate(doc,model(doc),domain=DOMAIN)==[True]*36


def test_both_depictions_and_the_conclusion_are_independent():
    doc=new_statements()
    cases={'baseline':[True,True,True],'reversed_walk':[False,True,True],'obsolete_walk':[False,True,True],
        'reversed_release':[True,True,False],'wrong_foreground_scope':[True,False,True],
        'wrong_background_scope':[True,False,True],'missing_reason_premise':[True,False,True],
        'added_remote_premise':[True,False,True],'reversed_order':[True,False,True]}
    for variant,expected in cases.items():assert evaluate(doc,model(doc,variant))==expected,variant
    assert evaluate(doc,model(doc),memo=False)==[True,True,True]
    for slot in range(7):
        bits=[True]*7;bits[slot]=False
        assert evaluate(doc,model(doc,bits=bits))==[slot!=0,slot not in (1,2,3,4),slot not in (5,6)],slot


def test_unknown_premises_reports_and_correspondences_are_not_negations():
    doc=new_statements()
    def unknown(*args):raise ValueError('Unspecified fifth sentence relation')
    for name in ('qa','hznreport','hzrbgreport','ud','ue','hzzzn'):
        with pytest.raises(ValueError,match='Unspecified fifth sentence'):
            evaluate(doc,model(doc)|{check.mapping()[name]:unknown})
    with pytest.raises(ValueError,match='Unspecified fifth sentence'):
        evaluate(doc,model(doc,bits=(True,False,True,True,True,True,True))|{check.mapping()['hzrbgreport']:unknown})


def test_conclusion_concession_and_walking_have_distinct_text_references():
    doc=new_statements();m=check.mapping()
    doc['declarations'].append(dict(kind='primitive',name='jexpected',parameters=[],result='individual'))
    doc['statements']=[dict(kind='ask',body=dict(kind='equal',arguments=[call(m[n]),call('jexpected')])) for n in REFERENCES]
    for index,target in enumerate(REFERENCES.values()):
        assert evaluate(doc,model(doc)|{'jexpected':lambda target=target:target})==[i==index for i in range(3)]
    changed=deepcopy(doc)
    next(d for d in changed['declarations'] if d['name']==m['h222d'])['body']=call(m['h5t'])
    assert evaluate(changed,model(changed)|{'jexpected':lambda:'concession'})==[False,False,False]
