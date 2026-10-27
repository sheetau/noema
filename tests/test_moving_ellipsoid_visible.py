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
from scripts import check_einstein_moving_ellipsoid_visible as check
from scripts import physical_meaning_heading_visible_profile as profile
from scripts import check_four_coordinate_claim as four
from scripts import check_moving_ellipsoid as source
from scripts import check_final_transform_claim as final
from scripts import check_transverse_segment as segment
from scripts.check_translated_light_trial import expose
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

CHECKS=('geometry_checks','setting_checks','shape_checks','general_checks')

@lru_cache(None)
def fixture(name,mode='boundary'):
    blueprint,slots=source.fixture(name,mode)
    doc=normalize_document(renamed(deepcopy(blueprint),mapping()))
    decoded={d['name']:d for d in check.restored()['document']['declarations']}
    for i,d in enumerate(doc['declarations']):
        if d['kind']!='definition':continue
        actual=deepcopy(decoded[d['name']])
        if mode=='instance' and d['name']==mapping()[name]:
            assert len(expose(actual,{'forall'},only_sort=RS))=={'ejf6':3,'ejga':1,'ejgb':4}[name]
        assert [p['sort'] for p in actual['parameters']]==[p['sort'] for p in d['parameters']]
        assert actual['result']==d['result'];doc['declarations'][i]=actual
    return normalize_document(doc),slots


def run(name,args,model,mode='boundary',domain=source.DOMAIN):
    doc,slots=fixture(name,mode);assert len(args)==len(slots)
    mm={n:lambda x=x:x for n,x in source.CONSTANTS.items()}|{'jmepoint':lambda:'discourse'}|model|{n:lambda x=x:x for n,x in zip(slots,args)}
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
    body_model=clone(segment,('model',))['model']
    return clone(source,('shape_model',*CHECKS),dict(final_model=final_model,body_model=body_model,run=run))


@pytest.mark.parametrize('name',CHECKS)
def test_decoded_ellipsoid_distinguishing_models(name):assert models()[name]()


def test_source_backprojection_parent_and_unchanged_vocabulary():
    doc=check.restored()['document'];assert check.backprojection(doc)==check.source_excerpt()
    b=check.bridge();assert b['source_statement_indices']==[167]
    assert list(b['source_units'])==['einstein-1905:u0114','einstein-1905:u0115']
    assert [r['id'] for r in b['math']]==['M0200']
    assert len(doc['declarations'])==2111 and len(doc['statements'])==143
    parent=check.previous.document();assert doc['statements'][:142]==parent['statements']
    ds={d['name']:d for d in doc['declarations']};assert all(ds[d['name']]==d for d in parent['declarations'])
    assert check.vocabulary().document()==check.previous.vocabulary().document()
    assert len(check.vocabulary()._words)==802 and len(check.NEW_DEFINITIONS)==13
    assert b['new_public_relations']==b['new_reference_primitives']==0
    assert b['new_source_assertions']==1 and b['total_source_assertions']==112


def test_native_quantifiers_full_region_and_generic_scope():
    ds={d['name']:d for d in check.restored()['document']['declarations']}
    for name in ('ejf6','ejga','ejgb'):
        actual={d['name']:d for d in fixture(name)[0]['declarations']}
        assert actual[mapping()[name]]==ds[mapping()[name]]
    def refs(name):return set(_references(ds[mapping()[name]]['body']))
    assert {mapping()[n] for n in ('ejf5','eje2')}<=refs('ejf6')
    assert {mapping()[n] for n in ('stg','ejf6','ejfa','ejf4','eiyx')}<=refs('ejga')
    assert {mapping()[n] for n in ('ejf7','ejga')}<=refs('ejgb')
    assert {mapping()[n] for n in ('ejfv','ejfx')}==refs('ejgc')
    seen=set()
    def visit(name):
        if name in seen:return
        seen.add(name)
        for ref in _references(ds[name].get('body')):visit(ref)
    visit(mapping()['ejgb'])
    assert not {check.names()[n] for n in ('zhw','zhx','zh2')}&seen
    assert not set(check.mapping())&{'shd','zhu','zhv','stl','stm','eipc','eipe'}


def test_each_radius_and_center_binder_in_two_body_diagnostics():
    # Other real binders are instantiated; this checks binding, not a full domain.
    cuts,_=numbers();c=cuts.make;r=cuts.read;domain=('a','b')
    baseline=[Q(5),Q(2),Q(-1),Q(3)]
    for slot in range(4):
        for candidate in (baseline[slot],baseline[slot]+7):
            values=baseline[:];values[slot]=candidate
            expected={(body,*values,'context') for body in domain}
            captured={'ejf7':set(),'ejga':set()}
            def handler(name):
                def invoke(*args):
                    row=tuple(r(x) if isinstance(x,FunctionValue) else x for x in args)
                    captured[name].add(row)
                    return row in expected
                return invoke
            model={name:handler(name) for name in captured}
            args=list(map(c,values))
            assert run('ejgb',args,model,'instance',domain)
            assert captured=={'ejf7':expected,'ejga':expected}
            assert not run('ejgb',args,model|{'ejga':lambda *xs:False},'instance',domain)


def test_whole_sentence_coordinates_and_unknown_inputs():
    b=check.BASE;h=check.context_handlers(b)
    assert h['sentencereference'](b['ri'],Q(54),Q(4))==b['zh3']
    for args in (('unknown',Q(54),Q(4)),(b['ri'],Q(0),Q(4)),(b['ri'],Q(54),Q(5))):
        with pytest.raises(ValueError):h['sentencereference'](*args)
    row=check.text_boundaries()['sentences']['zh3']
    assert row['position']==[54,4] and len(row['tokens'])==33
    assert row['tokens'][-4:]==['mit','den','Achsen','[M0200]']
    assert b['zh3']!=b['zh2']


def test_native_sentence_reference_does_not_execute_generic_conclusion():
    doc=deepcopy(check.restored()['document']);b=check.BASE
    doc['declarations'].append(dict(kind='primitive',name='ellipsoidcapture',parameters=['individual'],result='truth'))
    doc['statements']=[dict(kind='ask',body=call('ellipsoidcapture',call(check.names()['zh3'])))]
    handlers={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
    handlers.update({check.vocabulary()._symbols[n]:f for n,f in check.context_handlers(b).items()})
    handlers['ellipsoidcapture']=lambda x:x==b['zh3']
    result=evaluate_document(doc,individuals=tuple(set(b.values())|{'other'}),situations=check.SITUATIONS,primitives=handlers)
    assert [r['value'] for r in result]==[True]
