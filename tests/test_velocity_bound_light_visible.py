"""Distinguishing diagnostics for decoded deficit and light-invariance definitions.

All selected definitions come from the recovered Native document. Finite
arithmetic models, abstraction boundaries and exposed binders are diagnostics,
not a proof over all real cuts or an independent reading of the source.
"""
from copy import deepcopy
from fractions import Fraction as Q
from functools import lru_cache
from types import FunctionType
import json,re
import pytest
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import Content,FunctionValue,SequenceValue,DescriptionValue,QuestionValue,evaluate_document
from scripts import check_einstein_velocity_bound_light_visible as check
from scripts import velocity_axial_visible_profile as profile
from itertools import product
from scripts.check_translated_light_trial import expose
from scripts.shared_modality import call,renamed
from noema.meaning_catalog import _references

RS=profile.CUT

@lru_cache(None)
def mapping():
    return check.names()|{old:check.vocabulary()._symbols[new] for old,new in check.RELATIONS.items()}|check.mapping()

def forbidden(*xs):
    # Preserve the diagnostic expected by the reused frame model.
    raise ValueError('Unknown clock-site-time input (velocity-bound-light-visible fixture)')

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



from scripts import check_velocity_deficit_claim as deficit
from scripts import check_velocity_light_claim as light
from scripts import check_velocity_composition_claim as composition
from scripts import check_moving_trip_geometry as trip

MODULES=dict(deficit=deficit,light=light)
CHECKS=('numeric_checks','universal_checks','physical_checks','presentation_checks')


@lru_cache(None)
def fixture(group,name,mode='boundary'):
    source=MODULES[group];blueprint,slots=source.fixture(name,mode)
    doc=normalize_document(renamed(deepcopy(blueprint),mapping()))
    decoded={d['name']:d for d in check.restored()['document']['declarations']}
    for i,d in enumerate(doc['declarations']):
        if d['kind']!='definition':continue
        assert d['name'] in decoded,(group,name,d['name'])
        actual=deepcopy(decoded[d['name']])
        if d['name']==mapping()[name] and mode in ('instance','binding'):
            expected=len(d['parameters'])-len(actual['parameters'])
            if expected:assert len(expose(actual,{'forall'},only_sort=RS))==expected
        assert [p['sort'] for p in actual['parameters']]==[p['sort'] for p in d['parameters']]
        assert actual['result']==d['result'];doc['declarations'][i]=actual
    return normalize_document(doc),slots


def run(group,name,args,m,mode='boundary'):
    source=MODULES[group];doc,slots=fixture(group,name,mode);assert len(args)==len(slots)
    prefix='jvdc' if group=='deficit' else 'jvlc';values=[]
    def capture(x):values.append(x);return True
    mm={n:lambda x=x:x for n,x in source.CONSTANTS.items()}|{prefix+'point':lambda:'discourse',prefix+'result':capture}|m|{n:lambda x=x:x for n,x in zip(slots,args,strict=True)}
    mapped={mapping().get(n,n):fn for n,fn in mm.items()}
    result=evaluate_document(doc,individuals=source.DOMAIN,situations=source.POINTS,
        primitives={d['name']:mapped.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},
        max_steps=3000000,memoize_definitions=True,memoize_expressions=True)[0]['value']
    return values[0] if values else result


def clone(module,names,extra=None):
    ns=dict(vars(module))|dict(FunctionValue=FunctionValue,Content=Content,SequenceValue=SequenceValue,
        numbers=numbers,forbidden=forbidden,unknowns=unknowns,perturb=perturb,relation=relation,
        symbol=value,value=value,SemanticError=ValueError)|(extra or {})
    for name in names:
        original=getattr(module,name);original=getattr(original,'__wrapped__',original)
        ns[name]=FunctionType(original.__code__,ns,name,original.__defaults__,original.__closure__)
    return ns


@lru_cache(None)
def models():
    arithmetic=clone(composition,('arithmetic',))['arithmetic']
    norm=clone(trip,('norm_factory',))['norm_factory']
    return {group:clone(module,CHECKS,dict(arithmetic=arithmetic,norm_factory=norm,
        run=lambda *a,g=group,**kw:run(g,*a,**kw))) for group,module in MODULES.items()}


@pytest.mark.parametrize('group,name',[(g,n) for g in MODULES for n in CHECKS])
def test_decoded_bound_and_light_distinguishing_models(group,name):assert models()[group][name]()


def test_whole_source_parent_and_unchanged_vocabulary():
    doc=check.restored()['document'];assert check.backprojection(doc)==check.source_excerpt()
    b=check.bridge();assert b['source_statement_indices']==list(range(8,14))
    assert list(b['source_units'])==[f'einstein-1905:u{i:04d}' for i in range(143,147)]
    parent=check.previous.document();assert len(doc['statements'])==181 and doc['statements'][:175]==parent['statements']
    ds={d['name']:d for d in doc['declarations']};assert all(ds[d['name']]==d for d in parent['declarations'])
    assert check.vocabulary().document()==check.previous.vocabulary().document()
    assert len(check.vocabulary()._words)==861 and len(check.NEW_DEFINITIONS)==49
    assert (b['new_public_relations'],b['new_core_words'],b['new_reference_primitives'])==(0,0,0)
    assert (b['new_source_assertions'],b['total_source_assertions'],b['total_annotations'])==(6,149,32)
    old={d['name']:d for d in check.source_excerpt()['declarations']}
    assert all(ds[mapping()[n]]==renamed(old[n],mapping()) for n in check.NEW_DEFINITIONS)
    assert all(ds[check.reference_roles()[n]]==renamed(d,mapping()) for n,d in check.ROLE_DEFINITIONS.items())


def reference_values():
    cuts,_=numbers();b=dict(check.BASE)
    b.update(zlg=cuts.make(2),zlh=cuts.make(4));return b,cuts


def test_reference_positions_types_and_unknown_arguments():
    b,_=reference_values();h=check.context_handlers(b);cases=[]
    for old,pos in check.SENTENCES.items():cases.append(('sentencereference',[b['ri'],*map(Q,pos)],b[old]))
    for old,(node,start,end) in check.SPANS.items():cases.append(('sentencetokenspanreference',[b['eirf'],b[node],Q(start),b[node],Q(end),b['ri']],b[old]))
    for old in check.ROLE_ASSIGNMENTS:
        role=DescriptionValue(check.canonical(dict(kind='function_ref',symbol=check.reference_roles()[old])),
            check.canonical(dict(kind='function',parameters=[RS,'situation'],result='truth')))
        args=[b['eirf'],b[check.reference_anchor(old)],role,b['ri']]
        cases.append(('describedcutreference',args,b[old]))
        for bad in (DescriptionValue('{}',role.result_type),DescriptionValue(role.syntax,'"individual"'),DescriptionValue(role.syntax,role.result_type,1)):
            with pytest.raises(ValueError):h['describedcutreference'](*args[:2],bad,args[3])
    for kind,args,expected in cases:
        assert h[kind](*args)==expected
        for slot in range(len(args)):
            bad=args[:];bad[slot]=Q(999) if isinstance(args[slot],Q) else 'unknown'
            with pytest.raises(ValueError):h[kind](*bad)
    assert len({b[n] for n in ('zlj','zlk','zll')})==3
    assert [len(r['tokens']) for r in check.text_boundaries()['sentences'].values()]==[22,18,16,6]


def test_native_reference_lookup_does_not_evaluate_role_or_claim():
    b,cuts=reference_values()
    for old in (*check.SENTENCES,*check.SPANS,*check.ROLE_ASSIGNMENTS):
        doc=deepcopy(check.restored()['document']);sort=check.REFERENCE_SORTS.get(old,'individual')
        doc['declarations'].append(dict(kind='primitive',name='boundlightcapture',parameters=[sort],result='truth'))
        doc['statements']=[dict(kind='ask',body=call('boundlightcapture',call(check.names()[old])))]
        handlers={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
        handlers.update({check.vocabulary()._symbols[n]:fn for n,fn in check.context_handlers(b).items()})
        handlers['boundlightcapture']=(lambda x:cuts.read(x)==cuts.read(b[old])) if sort==RS else lambda x:x==b[old]
        declared={d['name'] for d in doc['declarations'] if d['kind']=='primitive'}
        assert evaluate_document(doc,individuals=tuple({x for x in b.values() if isinstance(x,str)}|{'other'}),
            situations=check.SITUATIONS,primitives={n:handlers[n] for n in declared})[0]['value']


@pytest.mark.parametrize('old,speed', [('zlg','zb7'),('zlh','zkq')])
def test_deficit_role_binds_each_operand_without_evaluating_other_reference(old,speed):
    ds={d['name']:d for d in check.restored()['document']['declarations']}
    role=deepcopy(ds[check.reference_roles()[old]])
    assert _references(role['body'])=={mapping()[n] for n in ('s3o','tc',speed)}
    decls=[]
    for name in sorted(_references(role['body'])):
        d=ds[name];parameters=d['parameters'] if d['kind']=='primitive' else [p['sort'] for p in d['parameters']]
        decls.append(dict(kind='primitive',name=name,parameters=parameters,result=d['result']))
    decls.extend([dict(kind='primitive',name='deficitcandidate',parameters=[],result=RS),
        dict(kind='primitive',name='deficitcontext',parameters=[],result='situation')])
    doc=normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=decls+[role],
        statements=[dict(kind='ask',body=call(role['name'],call('deficitcandidate'),call('deficitcontext')))]))
    cuts,_=numbers();c=cuts.make;norm=lambda xs:tuple(cuts.read(x) for x in xs)
    result=2 if old=='zlg' else 4;velocity=3 if old=='zlg' else 1
    rows={'s3o':{tuple(map(Q,(5,velocity,result)))}}
    model={'s3o':lambda *xs:norm(xs) in rows['s3o']}
    def evaluate(model,candidate=result,light=5,speed_value=velocity,context='reference'):
        handlers={mapping()['tc']:lambda:c(light),mapping()[speed]:lambda:c(speed_value),
            'deficitcandidate':lambda:c(candidate),'deficitcontext':lambda:context}
        handlers.update({mapping()[n]:fn for n,fn in model.items()})
        return evaluate_document(doc,individuals=('other',),situations=('reference','other'),primitives=handlers)[0]['value']
    assert perturb(evaluate,model,rows,norm)
    assert not evaluate(model,candidate=result+1)
    assert not evaluate(model,light=6)
    assert not evaluate(model,speed_value=velocity+1)
    assert evaluate(model,context='other')
