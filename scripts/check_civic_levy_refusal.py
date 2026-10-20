"""Check civic levy bindings and refusal distinct from nonpayment."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import Content
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_civic_levy_refusal import ROOT,LIBRARY,BASIS,NAMES,PRIMITIVES,MEANINGS,parent,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown,symbol

REPORT='reports/civic-levy-refusal-v1.json'
DOC='docs/civic-levy-refusal-v1.md'
PRIOR='reports/protected-remarks-v1.json'
DOMAIN=(*NAMES,'community','levy','response','other')
SCENES=('reference','outcome','other')
EXTRA=''.join('r z'+n+'[] a.' for n in DOMAIN)+'r zref[] d.r zpoint[] d.'


def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)


@lru_cache(None)
def fixture(kind,bindings=()):
    target=dict(citizen='r33s',payment='r33t',payment_adapter='r33u',demand='r33v',case='r33w',
                refusal='r33x',bindings='r33y',norm='r33z')[kind]
    doc=deepcopy(catalog().document)
    if kind=='bindings':
        d=next(d for d in doc['declarations'] if d['name']=='r33x')
        d.update(kind='primitive',parameters=[p['sort'] for p in d['parameters']]);d.pop('body')
    doc.update(declarations=closure(doc,[target]),statements=[])
    if kind in ('payment_adapter','bindings'):
        args='l[a]['+' '.join('k z'+n+'[]' for n in bindings)+']'+(' k zref[]' if kind=='bindings' else '')
    else:
        names=dict(citizen=('person','role','community'),payment=('person','transfer','receiver','medium'),
            demand=NAMES,case=('levy','community',*NAMES),refusal=(*NAMES,'response'),norm=(*NAMES,'response'))[kind]
        args=' '.join('k z'+n+'[]' for n in names)+(' k zref[]' if kind!='payment' else '')
    call='k '+target+'['+args+']'
    if kind in ('payment','payment_adapter','refusal','bindings','norm'):call='t['+call+'][k zpoint[]]'
    return parse(format_graph(doc,'compact')+EXTRA+'q['+call+'].')


def base(doc):
    v={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
    for n in DOMAIN:v['z'+n]=lambda n=n:n
    v.update(zref=lambda:'reference',zpoint=lambda:'outcome')
    return v


def payment_model(doc,variant='baseline'):
    v=base(doc)
    if variant=='same_receiver':v['zreceiver']=lambda:'person'
    v.update(ti=lambda transfer,payer,receiver,medium,point:(transfer,payer,receiver,medium,point)==(
            'other' if variant=='other_transfer' else 'transfer','person',
            'person' if variant=='same_receiver' else 'receiver','medium','outcome') and variant!='not_transferred',
        tj=lambda medium,point:(medium,point)==('medium','outcome') and variant!='unaccepted_medium')
    return v


@lru_cache(None)
def payment_checks():
    doc,rows=fixture('payment'),{}
    for variant in ('baseline','not_transferred','same_receiver','other_transfer','unaccepted_medium'):
        actual=evaluate(doc,payment_model(doc,variant),DOMAIN,SCENES,True)
        assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
    small=('person','transfer','receiver','medium')
    for bindings in ((),small,('person','transfer','medium','receiver'),small+('person',)):
        doc=fixture('payment_adapter',bindings)
        actual=evaluate(doc,payment_model(doc),small,('outcome',),True)
        assert actual==[bindings==small],(bindings,actual);rows[str(bindings)]=actual[0]
    return dict(contrasts=rows,native_value_transfer_and_exact_four_bindings=True)


def civic_model(doc,variant='baseline'):
    v=base(doc)
    v.update(aa=lambda p:p=='person',
        h237c=lambda p,community,ref:(p,community,ref)==('person','other' if variant=='other_community' else 'community','reference'),
        hzwn=lambda p,role,ref:(p,role,ref)==('person','other' if variant=='other_role' else 'role','reference'),
        h244g=lambda role,community,ref:variant!='not_civic_standing' and (role,community,ref)==('role','community','reference'))
    return v


@lru_cache(None)
def civic_checks():
    doc,rows=fixture('citizen'),{}
    for variant in ('baseline','other_community','other_role','not_civic_standing'):
        actual=evaluate(doc,civic_model(doc,variant),DOMAIN,SCENES,True)
        assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
    assert all(d['name'] not in ('cf','hzxf') for d in doc['declarations'])
    return dict(contrasts=rows,no_delegated_office_or_appointment_required=True)


def case_model(doc,variant='baseline'):
    v=civic_model(doc,variant)
    expected=('issuer','person','role','transfer','receiver','medium')
    v.update(h244h=lambda levy,community,ref:variant!='private_gift' and (levy,community,ref)==('levy','community','reference'),
        h244i=lambda levy,*args:(levy,*args)==('other' if variant=='other_levy' else 'levy',
            *(('other' if variant=='other_assessment_'+n else n) for n in expected),'reference'))
    def demand(issuer,person,role,code,bindings,sign,ref):
        return variant!='missing_requirement' and (issuer,person,role,symbol(code),code.rank,tuple(bindings.items),sign,ref)==(
            'other' if variant=='other_issuer' else 'issuer','person','role','r33u',0,
            ('person','other' if variant=='other_required_transfer' else 'transfer','receiver','medium'),
            variant!='negative_requirement','reference')
    v['h7k']=demand
    return v


@lru_cache(None)
def case_checks():
    doc,rows=fixture('case'),{}
    variants=('baseline','other_community','other_role','private_gift','other_levy','missing_requirement',
              'other_issuer','other_required_transfer','negative_requirement')+tuple('other_assessment_'+n for n in NAMES)
    for variant in variants:
        v=case_model(doc,variant)
        assert v['ti'] is unknown and v['tj'] is unknown
        actual=evaluate(doc,v,DOMAIN,SCENES,True)
        assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
    return dict(contrasts=rows,native_same_citizen_levy_and_requirement=True,payment_not_executed=True)


def refusal_model(doc,variant='baseline',calls=None):
    v=case_model(doc,variant)
    target=('person','transfer','receiver','medium')
    def response(act,issuer,person,role,code,bindings,sign,ref):
        return (act,issuer,person,role,symbol(code),code.rank,tuple(bindings.items),sign,ref)==(
            'response','other' if variant=='other_addressed_issuer' else 'issuer','person','role','r33u',0,
            ('person','other' if variant=='other_addressed_transfer' else 'transfer','receiver','medium'),
            variant!='opposite_addressed_sign','reference')
    def stance(person,act,code,bindings,sign,point):
        return variant!='no_practical_stance' and (person,act,symbol(code),code.rank,tuple(bindings.items),sign,point)==(
            'person','other' if variant=='other_stance_activity' else 'response','r33u',0,
            ('person','transfer','other' if variant=='other_stance_receiver' else 'receiver','medium'),
            variant=='accepts_payment','other' if variant=='other_stance_point' else 'outcome')
    def transfer(*args):
        if calls is not None:calls.append(args)
        return variant=='pays_anyway'
    v.update(h244k=response,h244j=stance,
        cg=lambda person,act,point:variant!='no_response_execution' and (person,act,point)==('person','response','outcome'),
        ti=transfer,tj=lambda medium,point:True)
    return v


@lru_cache(None)
def refusal_checks():
    doc,rows,calls=fixture('refusal'),{},[]
    for variant in ('baseline','pays_anyway','missing_requirement','other_addressed_issuer','other_addressed_transfer',
                    'opposite_addressed_sign','no_response_execution','no_practical_stance','other_stance_activity',
                    'other_stance_receiver','accepts_payment','other_stance_point'):
        actual=evaluate(doc,refusal_model(doc,variant,calls),DOMAIN,SCENES,True)
        assert actual==[variant in ('baseline','pays_anyway')],(variant,actual);rows[variant]=actual[0]
    assert not calls
    return dict(contrasts=rows,native_same_requirement_response_and_negative_stance=True,
                payment_or_nonpayment_not_inferred_from_refusal=True,no_payment_execution_during_refusal_evaluation=True)


@lru_cache(None)
def binding_checks():
    for special in range(7):
        names=tuple('person' if i==special else 'other' for i in range(7))
        expected=tuple('x' if i==special else 'y' for i in range(7))+('reference',)
        doc=fixture('bindings',names);v=base(doc);v.update(zperson=lambda:'x',zother=lambda:'y')
        v['r33x']=lambda *args:Content(SCENES,tuple(args==expected for _ in SCENES))
        assert evaluate(doc,v,('x','y'),SCENES,True)==[True],special
    for size in (0,6,8):
        doc=fixture('bindings',('person',)*size);v=base(doc);v['zperson']=lambda:'x'
        v['r33x']=lambda *args:Content(SCENES,(True,True,True))
        assert evaluate(doc,v,('x','y'),SCENES,True)==[False],size
    return dict(independently_checked_positions=7,invalid_lengths_refused=[0,6,8],
        boundaries=['r33x is a typed boundary in list binding checks; refusal checks evaluate its native definition.'])


@lru_cache(None)
def norm_checks():
    doc,rows=fixture('norm'),{}
    for variant in ('baseline','absent','positive_sign','wrong_source','wrong_person','wrong_role','wrong_response','wrong_reference','wrong_evaluation'):
        v=base(doc)
        def norm(issuer,person,role,code,bindings,ref,sign,point):
            return variant!='absent' and (issuer,person,role,symbol(code),code.rank,tuple(bindings.items),ref,sign,point)==(
                'other' if variant=='wrong_source' else 'issuer','other' if variant=='wrong_person' else 'person',
                'other' if variant=='wrong_role' else 'role','r33y',1,
                (*NAMES,'other' if variant=='wrong_response' else 'response'),
                'other' if variant=='wrong_reference' else 'reference',variant=='positive_sign',
                'reference' if variant=='wrong_evaluation' else 'outcome')
        v['h237z']=norm
        assert all(v[n] is unknown for n in ('h7k','h244j','h244k','cg','ti'))
        actual=evaluate(doc,v,DOMAIN,SCENES,True)
        assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
    return dict(contrasts=rows,refusal_prohibition_separate_from_actual_absence=True,quoted_refusal_not_executed=True)


@lru_cache(None)
def unknown_checks():
    rows=[]
    for kind,names,model in (('case',('h244g','h244h','h244i','h7k'),case_model),
                             ('refusal',('h244j','h244k','cg'),refusal_model)):
        doc=fixture(kind)
        for name in names:
            v=model(doc);v[name]=unknown
            try:evaluate(doc,v,DOMAIN,SCENES,True)
            except ValueError as error:assert 'Unknown' in str(error)
            else:raise AssertionError(name)
            rows.append(name)
    return dict(unknown_inputs_refused=rows)


@lru_cache(None)
def structure_checks():
    old,new=parent(),catalog();assert not new.document['statements']
    for n,e in new.entries.items():
        if n not in PRIMITIVES and n not in MEANINGS:
            assert e['declaration']==old.entries[n]['declaration'] and e['meaning_ja']==old.entries[n]['meaning_ja'],n
    validate_hashes(ROOT,read(PRIOR)['source_sha256'])
    for p,s in build().items():assert (ROOT/p).read_text(encoding='utf-8')==s,p
    for notation in ('compact','full'):
        text=format_graph(new.document,notation)
        assert parse(text)==parse(transcribe(text,alphabet='v2'))==new.document
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),new_semantic_reviews=0,
                active_manuscript_unchanged=True,roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,s in build().items():write_exact(ROOT/p,s)


def build_report():
    results={}
    for name,fn in [('payment',payment_checks),('civic',civic_checks),('case',case_checks),('refusal',refusal_checks),
                    ('bindings',binding_checks),('norm',norm_checks),('unknown',unknown_checks),('structure',structure_checks)]:
        results[name]=fn();print(name+' checked',flush=True)
    paths=set(build())|set(parent().source_sha256)|{
        DOC,PRIOR,'scripts/compose_civic_levy_refusal.py','scripts/check_civic_levy_refusal.py','tests/test_civic_levy_refusal.py',
        'scripts/compose_protected_remarks.py','scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py',
        'scripts/check_pastoral_roles.py','scripts/check_motive_causes.py'}
    return dict(status='civic_levy_payment_requirement_and_distinct_refusal_response',document=LIBRARY,**results,
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
