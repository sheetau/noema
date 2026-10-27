"""Run distinguishing models against definitions recovered from visible pages.

The preserved reviewers supply models and abstraction boundaries. Every source
definition under test is replaced by the decoded Native definition. The synthetic
finite program supplies inputs to the decoded calculation definitions. Old verdicts and
caches are not reused.
"""
from copy import deepcopy
from fractions import Fraction as Q
from math import isqrt
from functools import lru_cache
from types import FunctionType
import json
import pytest
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import Content,FunctionValue,SequenceValue,DescriptionValue,evaluate_document
from scripts import check_einstein_spherical_equation_rewrite_visible as check
from scripts import rest_spherical_wave_visible_profile as profile
from scripts import check_spherical_equation_rewrite as source
from scripts.shared_modality import call,renamed
from noema.meaning_catalog import _references

RS=profile.CUT

@lru_cache(None)
def mapping():
    return check.names()|{old:check.vocabulary()._symbols[new] for old,new in check.RELATIONS.items()}|check.mapping()

def forbidden(*xs):
    # Preserve the diagnostic expected by the reused frame model.
    raise ValueError('Unknown clock-site-time input (spherical-equation-rewrite-visible fixture)')

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

def pair(step):
    desc=dict(kind='description',result='content')
    return tuple(value(step(FunctionValue((desc,desc),desc,lambda left,right,i=i:(left,right)[i]))) for i in (0,1))

CHECKS=('binding_checks','numeric_checks','target_checks','premise_checks','chain_checks','presentation_checks')


@lru_cache(None)
def fixture(name,mode='boundary'):
    old,slots=source.fixture(name,mode)
    doc=normalize_document(renamed(deepcopy(old),mapping()))
    decoded={d['name']:d for d in check.restored()['document']['declarations']}
    for i,d in enumerate(doc['declarations']):
        if d['kind']!='definition':continue
        actual=deepcopy(decoded[d['name']])
        if d['name']==mapping()['zlx']:
            # A synthetic finite program is input to the Native definitions.
            # zlx itself is a public primitive, not a source definition.
            assert actual['kind']=='primitive'
            assert [p['sort'] for p in d['parameters']]==actual['parameters'] and d['result']==actual['result']
            continue
        assert actual['kind']=='definition'
        assert [p['sort'] for p in actual['parameters']]==[p['sort'] for p in d['parameters']] and actual['result']==d['result']
        doc['declarations'][i]=actual
    return normalize_document(doc),slots


def run(name,args,model,domain=source.DOMAIN,point='discourse',mode='boundary'):
    doc,slots=fixture(name,mode);assert len(args)==len(slots)
    mm={n:lambda x=x:x for n,x in source.CONSTANTS.items()}|model|{n:lambda x=x:x for n,x in zip(slots,args)}|{'jserpoint':lambda:point}
    mm.setdefault('jserprogram',lambda method,stage,seq:seq if (method,stage)==('method','discourse') else SequenceValue((),seq.element_type))
    mapped={mapping().get(n,n):fn for n,fn in mm.items()}
    handlers={d['name']:mapped.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'}
    return evaluate_document(doc,individuals=domain,situations=source.POINTS,primitives=handlers,
        max_steps=700000,memoize_definitions=True,memoize_expressions=True)[0]['value']


@lru_cache(None)
def models():
    ns=dict(vars(source))|dict(FunctionValue=FunctionValue,Content=Content,SequenceValue=SequenceValue,
        numbers=numbers,forbidden=forbidden,unknowns=unknowns,perturb=perturb,relation=relation,run=run,pair=pair,symbol=value,RS=RS,isqrt=isqrt)
    for name in ('coordinate_model','target_model',*CHECKS):
        original=getattr(source,name);original=getattr(original,'__wrapped__',original)
        ns[name]=FunctionType(original.__code__,ns,name,original.__defaults__,original.__closure__)
    return ns


@pytest.mark.parametrize('name',CHECKS)
def test_decoded_native_distinguishing_models(name):assert models()[name]()


def test_source_backprojection_same_profile_and_unchanged_parent():
    doc=check.restored()['document'];assert check.backprojection(doc)==check.source_excerpt()
    b=check.bridge();assert b['source_statement_indices']==[142]
    assert list(b['source_units'])==['einstein-1905:u0089','einstein-1905:u0090']
    assert [r['id'] for r in b['math']]==['M0146']
    sentence=b['text_boundaries']['sentences']['sphericalequationrewritesentence']
    assert sentence['position']==[46,1] and len(sentence['tokens'])==14 and sentence['tokens'][-1]=='[M0146].'
    assert b['text_boundaries']['spans']=={'zge':['sphericalequationrewritesentence',1,14]}
    assert len(check.NEW_DEFINITIONS)==7 and len(check.vocabulary()._words)==787
    parent=check.previous.document()
    assert doc['statements'][:112]==parent['statements']
    old={d['name']:d for d in parent['declarations']};new={d['name']:d for d in doc['declarations']}
    assert all(new[n]==d for n,d in old.items())
    assert check.vocabulary().document()==check.previous.vocabulary().document()
    assert len(new)-len(old)==9 and b['reference_roles']=={} and b['forwarded_reference_signatures']=={}


def test_exact_rewrite_span_and_all_scope_arguments():
    b=check.BASE;h=check.context_handlers(b);node=b['sphericalequationrewritesentence']
    args=[b['eirf'],node,Q(1),node,Q(14),b['ri']]
    assert h['sentencetokenspanreference'](*args)==b['zge']
    for slot in range(len(args)):
        bad=args.copy();bad[slot]=Q(2 if slot==2 else 13) if slot in (2,4) else 'unknown'
        with pytest.raises(ValueError):h['sentencetokenspanreference'](*bad)
    assert h['sentencereference'](b['ri'],Q(46),Q(1))==node
    for bad in ((b['ri'],Q(46),Q(2)),('unknown',Q(46),Q(1))):
        with pytest.raises(ValueError):h['sentencereference'](*bad)


def test_native_rewrite_reference_is_the_whole_sentence_without_execution():
    doc=deepcopy(check.restored()['document']);b=check.BASE
    doc['declarations'].append(dict(kind='primitive',name='rewritecapture',parameters=['individual'],result='truth'))
    doc['statements']=[dict(kind='ask',body=call('rewritecapture',call(check.names()['zge'])))]
    h={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
    h|={check.vocabulary()._symbols[n]:fn for n,fn in check.context_handlers(b).items()}
    h['rewritecapture']=lambda node:node==b['zge']
    assert [r['value'] for r in evaluate_document(doc,individuals=tuple(set(b.values())|{'other','setting','frame'}),situations=check.SITUATIONS,primitives=h)]==[True]
