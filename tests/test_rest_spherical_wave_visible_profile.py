"""Run distinguishing models against definitions recovered from visible pages.

The preserved reviewers supply models and abstraction boundaries. Every source
definition under test is replaced by the decoded Native definition. Reference
forwarding and the actual map pair are checked separately. Old verdicts and
caches are not reused.
"""
from copy import deepcopy
from fractions import Fraction as Q
from functools import lru_cache
from types import FunctionType
import json
import pytest
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import Content,FunctionValue,SequenceValue,DescriptionValue,evaluate_document
from scripts import check_einstein_rest_spherical_wave_visible as check
from scripts import rest_spherical_wave_visible_profile as profile
from scripts import check_rest_spherical_wave as source
from scripts.shared_modality import call,renamed
from noema.meaning_catalog import _references

RS=profile.CUT

@lru_cache(None)
def mapping():
    return check.names()|{old:check.vocabulary()._symbols[new] for old,new in check.RELATIONS.items()}|check.mapping()

def forbidden(*xs):
    # Preserve the diagnostic expected by the reused frame model.
    raise ValueError('Unknown clock-site-time input (rest-spherical-wave-visible fixture)')

def value(x):
    if isinstance(x,DescriptionValue):
        node=renamed(json.loads(x.syntax),{v:k for k,v in mapping().items()})
        if node.get('kind') in ('call','function_ref'):return node['symbol']
        raise ValueError('Unexpected quoted form')
    if isinstance(x,SequenceValue):return tuple(value(v) for v in x.items)
    return x

def relation(rows):return lambda *xs:tuple(value(x) for x in xs) in rows

def unknowns(test,model,names):
    for name in names:
        with pytest.raises(ValueError,match='Unknown clock-site-time'):
            test(model|{name:forbidden})

def perturb(test,model,rows,norm=lambda xs:tuple(value(x) for x in xs)):
    count=1;assert test(model)
    for name,rs in rows.items():
        for row in rs:
            assert not test(model|{name:lambda *xs,rs=rs-{row}:norm(xs) in rs});count+=1
            for slot in range(len(row)):
                bad=tuple('wrong' if i==slot else x for i,x in enumerate(row))
                assert not test(model|{name:lambda *xs,rs=(rs-{row})|{bad}:norm(xs) in rs});count+=1
    unknowns(test,model,rows)
    return count

class Cuts:
    def __init__(self):self.table={}
    def make(self,n):
        n=Q(n);f=FunctionValue(('number',),'truth',lambda q:q<n)
        self.table[f.implementation]=n;return f
    def read(self,f):
        while isinstance(f,FunctionValue):
            impl=f.implementation
            if impl in self.table:return self.table[impl]
            if isinstance(impl,FunctionValue):f=impl;continue
            code=getattr(impl,'__code__',None)
            if code is None:break
            free=dict(zip(code.co_freevars,(c.cell_contents for c in (getattr(impl,'__closure__',None) or ()))))
            f=free.get('raw')
        raise ValueError('Unregistered finite cut')

def numbers():
    cuts=Cuts();c=cuts.make;r=cuts.read
    return cuts,dict(ba=lambda x:isinstance(r(x),Q),bb=c,bc=lambda a,b:r(a)<=r(b),
        bd=lambda a,b:c(r(a)+r(b)),bf=lambda a,b:c(r(a)-r(b)),
        bg=lambda a,b:r(a)<r(b),shv=lambda a,b:c(r(a)*r(b)),sah=lambda a,b:c(r(a)*r(b)),
        sca=lambda a,b:r(a)==r(b),zzba=lambda x:isinstance(r(x),Q),zzbc=lambda a,b:r(a)<=r(b),zzbg=lambda a,b:r(a)<r(b))

CHECKS=('numeric_checks','arrival_checks','emission_checks','front_checks','presentation_checks')


@lru_cache(None)
def fixture(name):
    old,slots=source.fixture(name)
    doc=normalize_document(renamed(deepcopy(old),mapping()))
    decoded={d['name']:d for d in check.restored()['document']['declarations']}
    for i,d in enumerate(doc['declarations']):
        if d['kind']!='definition':continue
        actual=deepcopy(decoded[d['name']])
        assert actual['parameters']==d['parameters'] and actual['result']==d['result']
        doc['declarations'][i]=actual
    return normalize_document(doc),slots


def run(name,args,model,domain=source.DOMAIN,point='discourse'):
    doc,slots=fixture(name);assert len(args)==len(slots)
    mm={n:lambda x=x:x for n,x in source.CONSTANTS.items()}|model|{n:lambda x=x:x for n,x in zip(slots,args)}|{'jrswpoint':lambda:point}
    mapped={mapping().get(n,n):fn for n,fn in mm.items()}
    handlers={d['name']:mapped.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'}
    return evaluate_document(doc,individuals=domain,situations=source.POINTS,primitives=handlers,
        max_steps=700000,memoize_definitions=True,memoize_expressions=True)[0]['value']


@lru_cache(None)
def models():
    ns=dict(vars(source))|dict(FunctionValue=FunctionValue,Content=Content,SequenceValue=SequenceValue,
        numbers=numbers,forbidden=forbidden,unknowns=unknowns,perturb=perturb,relation=relation,run=run)
    for name in ('coordinate_model','front_model',*CHECKS):
        original=getattr(source,name);original=getattr(original,'__wrapped__',original)
        ns[name]=FunctionType(original.__code__,ns,name,original.__defaults__,original.__closure__)
    return ns


@pytest.mark.parametrize('name',CHECKS)
def test_decoded_native_distinguishing_models(name):assert models()[name]()


def test_source_backprojection_two_sentences_equation_and_unchanged_parent():
    doc=check.restored()['document'];assert check.backprojection(doc)==check.source_excerpt()
    b=check.bridge();assert b['source_statement_indices']==[141]
    assert list(b['source_units'])==['einstein-1905:u0087','einstein-1905:u0088']
    assert [r['id'] for r in b['math']]==['M0141','M0142','M0143','M0144','M0145']
    sentences=b['text_boundaries']['sentences']
    assert [(s['position'],len(s['tokens'])) for s in sentences.values()]==[([45,1],27),([45,2],13)]
    assert sentences['restsphericalassumptionsentence']['tokens'][-1]=='ausbreitet.'
    assert sentences['restsphericalequationsentence']['tokens'][-1]=='[M0145].'
    assert b['text_boundaries']['spans']=={'zgc':['restsphericalassumptionsentence',1,27],'zgd':['restsphericalequationsentence',1,13]}
    assert len(check.NEW_DEFINITIONS)==12 and len(check.vocabulary()._words)==787
    assert doc['statements'][:111]==check.previous.document()['statements']
    prior=check.previous.vocabulary().document();current=check.vocabulary().document()
    for field in ('entries','compounds','definitions','primitives'):
        assert all(current[field][n]==d for n,d in prior[field].items())
    assert len(profile.CONTRACTS)==1 and b['forwarded_reference_signatures']=={}


def context(doc):
    h={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
    return h|{check.vocabulary()._symbols[n]:f for n,f in check.context_handlers(check.BASE).items()}


def evaluate(doc,handlers):
    return [r['value'] for r in evaluate_document(doc,individuals=tuple(set(check.BASE.values())|{'other','setting','frame'}),
        situations=check.SITUATIONS,primitives=handlers)]


def test_wave_and_emission_references_are_scoped_distinct_and_opaque():
    b=check.BASE;h=check.context_handlers(b)
    for old in check.ROLE_ASSIGNMENTS:
        role=DescriptionValue(check.canonical(dict(kind='function_ref',symbol=check.reference_roles()[old])),
            check.canonical(dict(kind='function',parameters=['individual','situation'],result='truth')))
        args=[b['eirf'],b['zgc'],role,b['ri']]
        assert h['describedreference'](*args)==b[old]
        for slot in range(4):
            bad=args.copy();bad[slot]='unknown'
            with pytest.raises(ValueError):h['describedreference'](*bad)
        for bad in (DescriptionValue('{}',role.result_type),DescriptionValue(role.syntax,'"individual"'),DescriptionValue(role.syntax,role.result_type,1)):
            with pytest.raises(ValueError):h['describedreference'](*args[:2],bad,args[3])
    assert b['zfu']!=b['zfv']
    doc=deepcopy(check.restored()['document'])
    doc['declarations'].append(dict(kind='primitive',name='wavecapture',parameters=['individual','individual'],result='truth'))
    doc['statements']=[dict(kind='ask',body=call('wavecapture',call(check.names()['zfu']),call(check.names()['zfv'])))]
    assert evaluate(doc,context(doc)|dict(wavecapture=lambda w,e:(w,e)==(b['zfu'],b['zfv'])))==[True]


@pytest.mark.parametrize('old',('zfu','zfv'))
def test_native_closed_role_passes_candidate_context_and_same_wave(old):
    # Check the actual role with ei76 abstracted; emission_checks independently
    # evaluates the Native ei76 body using two values and every witness slot.
    b=check.BASE;doc=deepcopy(check.restored()['document']);target=check.mapping()['ei76']
    for i,d in enumerate(doc['declarations']):
        if d['name']==target:
            doc['declarations'][i]=dict(kind='primitive',name=target,parameters=[p['sort'] for p in d['parameters']],result=d['result'])
    doc['declarations'] += [dict(kind='primitive',name='wavecandidate',parameters=[],result='individual'),
                            dict(kind='primitive',name='wavecontext',parameters=[],result='situation')]
    doc['statements']=[dict(kind='ask',body=call(check.reference_roles()[old],call('wavecandidate'),call('wavecontext')))]
    expected=(b['zfu'],b['zfv'],b['ri'])
    h=context(doc)|{target:lambda *xs:xs==expected,'wavecandidate':lambda:b[old],'wavecontext':lambda:b['ri']}
    assert evaluate(doc,h)==[True]
    other='zfv' if old=='zfu' else 'zfu'
    assert evaluate(doc,h|{'wavecandidate':lambda:b[other]})==[False]
    assert evaluate(doc,h|{'wavecontext':lambda:b['zb6']})==[False]
    assert evaluate(doc,h|{target:lambda *xs:xs==(b['zfv'],b['zfu'],b['ri'])})==[False]


def test_exact_assumption_and_equation_spans_and_unknown_boundaries():
    b=check.BASE;h=check.context_handlers(b)
    for old,(node,start,end) in check.SPANS.items():
        assert h['sentencetokenspanreference'](b['eirf'],b[node],Q(start),b[node],Q(end),b['ri'])==b[old]
        for badstart,badend in ((2,end),(1,end-1),(1,end+1)):
            with pytest.raises(ValueError):
                h['sentencetokenspanreference'](b['eirf'],b[node],Q(badstart),b[node],Q(badend),b['ri'])
