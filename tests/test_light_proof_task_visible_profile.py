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
from scripts import check_einstein_light_proof_task_visible as check
from scripts import light_proof_task_visible_profile as profile
from scripts import check_light_proof_task as source
from scripts import check_frame_light_law as light
from scripts.shared_modality import call,renamed
from noema.meaning_catalog import _references

RS=profile.CUT

@lru_cache(None)
def mapping():
    return check.names()|{old:check.vocabulary()._symbols[new] for old,new in check.RELATIONS.items()}|check.mapping()

def forbidden(*xs):
    # Preserve the diagnostic expected by the reused frame model.
    raise ValueError('Unknown clock-site-time input (light-proof-task-visible fixture)')

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

CHECKS=('target_checks','proof_gap_checks','compatibility_checks','presentation_checks')

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=normalize_document(renamed(deepcopy(source.fixture(name,mode)),mapping()))
    decoded={d['name']:d for d in check.restored()['document']['declarations']}
    for i,d in enumerate(doc['declarations']):
        if d['kind']!='definition':continue
        actual=deepcopy(decoded[d['name']])
        assert actual['parameters']==d['parameters'] and actual['result']==d['result']
        doc['declarations'][i]=actual
    return normalize_document(doc)

def run(name,model,mode='boundary',point='discourse',domain=source.DOMAIN,points=source.POINTS):
    doc=fixture(name,mode)
    mm={n:lambda x=x:x for n,x in source.CONSTANTS.items()}|model|{'jlptpoint':lambda:point}
    mapped={mapping().get(n,n):fn for n,fn in mm.items()}
    handlers={d['name']:mapped.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'}
    return evaluate_document(doc,individuals=domain,situations=points,primitives=handlers,
        max_steps=700000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def clone_models(module,names,extra=None):
    ns=dict(vars(module))|dict(FunctionValue=FunctionValue,Content=Content,SequenceValue=SequenceValue,
        numbers=numbers,forbidden=forbidden,unknowns=unknowns,perturb=perturb,relation=relation,
        symbol=value)|(extra or {})
    for name in names:
        original=getattr(module,name);original=getattr(original,'__wrapped__',original)
        ns[name]=FunctionType(original.__code__,ns,name,original.__defaults__,original.__closure__)
    return ns

@lru_cache(None)
def models():
    physical=clone_models(light,('model',))
    return clone_models(source,CHECKS,dict(run=run,light_model=physical['model']))

@pytest.mark.parametrize('name',CHECKS)
def test_decoded_native_distinguishing_models(name):assert models()[name]()

def test_source_backprojection_complete_sentence_and_unchanged_parent():
    doc=check.restored()['document'];assert check.backprojection(doc)==check.source_excerpt()
    b=check.bridge();assert b['source_statement_indices']==[140]
    assert list(b['source_units'])==['einstein-1905:u0086']
    assert [r['id'] for r in b['math']]==['M0140']
    sentence=b['text_boundaries']['sentences']['lightprooftasksentence']
    assert sentence['position']==[44,1] and len(sentence['tokens'])==51
    assert sentence['tokens'][29:32]==['ist;','denn','wir']
    assert b['text_boundaries']['spans']=={'zfz':['lightprooftasksentence',1,30],'zfy':['lightprooftasksentence',31,51]}
    assert len(check.NEW_DEFINITIONS)==9 and len(check.vocabulary()._words)==786
    assert doc['statements'][:110]==check.previous.document()['statements']
    prior=check.previous.vocabulary().document();current=check.vocabulary().document()
    for field in ('entries','compounds','definitions','primitives'):
        assert all(current[field][n]==d for n,d in prior[field].items())
    assert len(profile.CONTRACTS)==4 and b['forwarded_reference_signatures']=={}

def context(doc):
    h={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
    return h|{check.vocabulary()._symbols[n]:f for n,f in check.context_handlers(check.BASE).items()}

def evaluate(doc,handlers):
    return [r['value'] for r in evaluate_document(doc,individuals=tuple(set(check.BASE.values())|{'other','setting','frame'}),
        situations=check.SITUATIONS,primitives=handlers)]

def test_stage_reference_is_distinct_scoped_and_does_not_execute_role():
    b=check.BASE;h=check.context_handlers(b)
    role=DescriptionValue(check.canonical(dict(kind='function_ref',symbol=check.reference_roles()['zfx'])),
        check.canonical(dict(kind='function',parameters=['situation','situation'],result='truth')))
    args=[b['eirf'],b['zfz'],role,b['ri']]
    assert h['describedsettingreference'](*args)==b['zfx']!=b['zfm']
    for slot in range(4):
        bad=args.copy();bad[slot]='unknown'
        with pytest.raises(ValueError):h['describedsettingreference'](*bad)
    for bad in (DescriptionValue('{}',role.result_type),DescriptionValue(role.syntax,'"individual"'),DescriptionValue(role.syntax,role.result_type,1)):
        with pytest.raises(ValueError):h['describedsettingreference'](*args[:2],bad,args[3])
    doc=deepcopy(check.restored()['document'])
    doc['declarations'].append(dict(kind='primitive',name='proofcapture',parameters=['situation'],result='truth'))
    doc['statements']=[dict(kind='ask',body=call('proofcapture',call(check.names()['zfx'])))]
    assert evaluate(doc,context(doc)|dict(proofcapture=lambda x:x==b['zfx']))==[True]

def test_native_stage_role_passes_the_candidate_and_presentation_context():
    b=check.BASE;doc=deepcopy(check.restored()['document'])
    for name in ('proofstageprobe','proofcontextprobe'):
        doc['declarations'].append(dict(kind='primitive',name=name,parameters=[],result='situation'))
    doc['statements']=[dict(kind='ask',body=call(check.names()['lightproofstagerole'],call('proofstageprobe'),call('proofcontextprobe')))]
    expected=(b['zfz'],b['rd'],'ei7v',b['zfx'],b['eisms'],b['ri'])
    h=context(doc)|{check.vocabulary()._symbols['presentsprooftask']:lambda *xs:tuple(value(x) for x in xs)==expected,
        'proofstageprobe':lambda:b['zfx'],'proofcontextprobe':lambda:b['ri']}
    assert evaluate(doc,h)==[True]
    assert evaluate(doc,h|{'proofstageprobe':lambda:b['zfm']})==[False]
    assert evaluate(doc,h|{'proofcontextprobe':lambda:b['zfm']})==[False]

def test_exact_task_and_reason_spans_and_unknown_boundaries():
    b=check.BASE;h=check.context_handlers(b)
    for old,(node,start,end) in check.SPANS.items():
        assert h['sentencetokenspanreference'](b['eirf'],b[node],Q(start),b[node],Q(end),b['ri'])==b[old]
    for start,end in ((1,29),(30,51),(1,52)):
        with pytest.raises(ValueError):
            h['sentencetokenspanreference'](b['eirf'],b['lightprooftasksentence'],Q(start),b['lightprooftasksentence'],Q(end),b['ri'])
