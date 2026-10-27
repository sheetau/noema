"""Run distinguishing models against definitions recovered from visible pages.

The preserved reviewers supply models and abstraction boundaries. Every source
definition under test is replaced by the decoded Native definition. References
and closed roles are checked separately. Native individual quantifiers remain in the distinguishing two-value models. Numerical cut examples and reference binding checks are diagnostics, not proofs over all real inputs.
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
from scripts import check_einstein_sphere_zero_slice_visible as check
from scripts import physical_meaning_heading_visible_profile as profile
from scripts import check_four_coordinate_claim as four
from scripts import check_sphere_zero_slice as source
from scripts import check_final_transform_claim as final
from scripts.shared_modality import call,renamed
from noema.meaning_catalog import _references

RS=profile.CUT

@lru_cache(None)
def mapping():
    return check.names()|{old:check.vocabulary()._symbols[new] for old,new in check.RELATIONS.items()}|check.mapping()

def forbidden(*xs):
    # Preserve the diagnostic expected by the reused frame model.
    raise ValueError('Unknown clock-site-time input (four-coordinate-visible fixture)')

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

CHECKS=('numeric_checks','scope_checks','binding_checks','presentation_checks')

@lru_cache(None)
def fixture(name):
    blueprint,slots=source.fixture(name)
    doc=normalize_document(renamed(deepcopy(blueprint),mapping()))
    decoded={d['name']:d for d in check.restored()['document']['declarations']}
    for i,d in enumerate(doc['declarations']):
        if d['kind']!='definition':continue
        actual=deepcopy(decoded[d['name']])
        assert [p['sort'] for p in actual['parameters']]==[p['sort'] for p in d['parameters']]
        assert actual['result']==d['result'];doc['declarations'][i]=actual
    return normalize_document(doc),slots


def run(name,args,model,domain=source.DOMAIN):
    doc,slots=fixture(name);assert len(args)==len(slots)
    mm={n:lambda x=x:x for n,x in source.CONSTANTS.items()}|{'jszspoint':lambda:'discourse'}|model|{n:lambda x=x:x for n,x in zip(slots,args)}
    mapped={mapping().get(n,n):fn for n,fn in mm.items()}
    return evaluate_document(doc,individuals=domain,situations=source.POINTS,
        primitives={d['name']:mapped.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},
        max_steps=3000000,memoize_definitions=True,memoize_expressions=True)[0]['value']


def clone(module,names,extra=None):
    ns=dict(vars(module))|dict(FunctionValue=FunctionValue,Content=Content,SequenceValue=SequenceValue,
        numbers=numbers,arithmetic=numbers,forbidden=forbidden,unknowns=unknowns,perturb=perturb,relation=relation)|(extra or {})
    for name in names:
        original=getattr(module,name);original=getattr(original,'__wrapped__',original)
        ns[name]=FunctionType(original.__code__,ns,name,original.__defaults__,original.__closure__)
    return ns


@lru_cache(None)
def models():
    numeric=clone(four,('model',))
    final_model=clone(final,('final_model',),dict(numeric_model=numeric['model']))['final_model']
    return clone(source,CHECKS,dict(final_model=final_model,run=run))


@pytest.mark.parametrize('name',CHECKS)
def test_decoded_zero_slice_distinguishing_models(name):assert models()[name]()


def test_source_backprojection_parent_and_unchanged_vocabulary():
    doc=check.restored()['document'];assert check.backprojection(doc)==check.source_excerpt()
    b=check.bridge();assert b['source_statement_indices']==[166]
    assert list(b['source_units'])==['einstein-1905:u0112','einstein-1905:u0113']
    assert [r['id'] for r in b['math']]==['M0197','M0198','M0199']
    assert len(doc['declarations'])==2097 and len(doc['statements'])==142
    parent=check.previous.document();assert doc['statements'][:141]==parent['statements']
    ds={d['name']:d for d in doc['declarations']};assert all(ds[d['name']]==d for d in parent['declarations'])
    assert check.vocabulary().document()==check.previous.vocabulary().document()
    assert len(check.vocabulary()._words)==802 and len(check.NEW_DEFINITIONS)==12
    assert b['new_public_relations']==b['new_reference_primitives']==0
    assert b['new_source_assertions']==1 and b['total_source_assertions']==111


def test_native_scope_same_event_and_all_three_rewrite_prerequisites():
    ds={d['name']:d for d in check.restored()['document']['declarations']}
    for name in ('stf','ssn','ssz','ejfr','ejfs','ejft','ejfu','ejfv','ejfy','ejf2'):
        actual={d['name']:d for d in fixture(name)[0]['declarations']}
        assert actual[mapping()[name]]==ds[mapping()[name]]
    def refs(name):return set(_references(ds[mapping()[name]]['body']))
    assert {mapping()[n] for n in ('ejfr','ejfa')}<=refs('ejfs')
    assert {mapping()[n] for n in ('ejfs','eiyx','ejfa','ssz')}<=refs('ejft')
    assert {mapping()[n] for n in ('ejfs','stf')}<=refs('ejfu')
    assert {mapping()[n] for n in ('ejff','ejfh','ejeh')}==refs('ejfv')
    assert not set(check.mapping())&{'shd','zhu','zhv','stl','stm'}


def test_whole_sentence_coordinates_and_unknown_inputs():
    b=check.BASE;h=check.context_handlers(b)
    assert h['sentencereference'](b['ri'],Q(54),Q(3))==b['zh2']
    for args in (('unknown',Q(54),Q(3)),(b['ri'],Q(0),Q(3)),(b['ri'],Q(54),Q(4))):
        with pytest.raises(ValueError):h['sentencereference'](*args)
    row=check.text_boundaries()['sentences']['zh2']
    assert row['position']==[54,3] and len(row['tokens'])==12
    assert row['tokens'][6]=='[M0197]' and row['tokens'][-2:]==['[M0198]:','[M0199]']
    assert b['zh2']!=b['eisn6']


def test_native_sentence_reference_does_not_execute_equations():
    doc=deepcopy(check.restored()['document']);b=check.BASE
    doc['declarations'].append(dict(kind='primitive',name='zeroslicecapture',parameters=['individual'],result='truth'))
    doc['statements']=[dict(kind='ask',body=call('zeroslicecapture',call(check.names()['zh2'])))]
    handlers={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
    handlers.update({check.vocabulary()._symbols[n]:f for n,f in check.context_handlers(b).items()})
    handlers['zeroslicecapture']=lambda x:x==b['zh2']
    result=evaluate_document(doc,individuals=tuple(set(b.values())|{'other'}),situations=check.SITUATIONS,primitives=handlers)
    assert [r['value'] for r in result]==[True]
