"""Run distinguishing models against definitions recovered from visible pages.

The preserved reviewers supply models and abstraction boundaries. Every source
definition under test is replaced by the decoded Native definition. References
and closed roles are checked separately. Native individual quantifiers remain in the distinguishing two-value models. Numerical cut examples and reference binding checks are diagnostics, not proofs over all real inputs.
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
from scripts import check_einstein_clock_transport_visible as check
from scripts import clock_transport_visible_profile as profile
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
    raise ValueError('Unknown clock-site-time input (clock-transport-visible fixture)')

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


from inspect import signature
from scripts import check_moving_trip_geometry as trip
from scripts import check_origin_clock_equations as equations
from scripts import check_clock_seconds_claim as seconds
from scripts import check_clock_transfer_records as records
from scripts import check_clock_transfer_claim as transfer
from scripts import check_polygon_clock_claim as polygon
from scripts import check_curved_clock_records as curve
from scripts import check_curve_earth_claim as earth

MODULES=dict(records=records,transfer=transfer,polygon=polygon,curve=curve,earth=earth)
CHECKS=dict(records=('local_checks','binding_checks','rate_checks','path_checks','rest_checks','setup_checks'),
    transfer=('seconds_checks','arrival_checks','approximation_checks','conditional_checks','presentation_checks'),
    polygon=('path_checks','setup_checks','total_checks','scope_checks','presentation_checks'),
    curve=('point_checks','coverage_checks','kinematic_checks','adapter_checks','scope_checks'),
    earth=('mechanism_checks','profile_checks','rate_checks','binding_checks','necessity_checks','presentation_checks'))
ALL_SORT_EXPOSE={'ejlc','ejld','ejle','ejlv','ejlw','ejmf','ejmh'}


@lru_cache(None)
def fixture(group,name,mode='boundary'):
    blueprint,slots=MODULES[group].fixture(name,mode)
    doc=normalize_document(renamed(deepcopy(blueprint),mapping()))
    decoded={d['name']:d for d in check.restored()['document']['declarations']}
    for i,d in enumerate(doc['declarations']):
        if d['kind']!='definition':continue
        actual=deepcopy(decoded[d['name']])
        if mode=='instance' and d['name']==mapping()[name]:
            expected=len(d['parameters'])-len(actual['parameters']);assert expected>0
            assert len(expose(actual,{'forall','exists'},only_sort=None if name in ALL_SORT_EXPOSE else RS))==expected
        assert [p['sort'] for p in actual['parameters']]==[p['sort'] for p in d['parameters']]
        assert actual['result']==d['result'];doc['declarations'][i]=actual
    return normalize_document(doc),slots


def run(group,name,args,m,*rest,**kwargs):
    source=MODULES[group];bound=signature(source.run).bind(name,args,m,*rest,**kwargs);bound.apply_defaults()
    options=bound.arguments;doc,slots=fixture(group,name,options.get('mode','boundary'))
    assert len(args)==len(slots),(group,name,len(args),len(slots))
    point={'records':'jctrpoint','transfer':'jctcpoint','polygon':'jpccpoint','curve':'jccrpoint','earth':'jcecpoint'}[group]
    mm={n:lambda x=x:x for n,x in source.CONSTANTS.items()}|{point:lambda:'discourse'}|m|{n:lambda x=x:x for n,x in zip(slots,args)}
    mapped={mapping().get(n,n):fn for n,fn in mm.items()}
    return evaluate_document(doc,individuals=options.get('domain',source.DOMAIN),situations=source.POINTS,
        primitives={d['name']:mapped.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},
        max_steps=3000000,memoize_definitions=True,memoize_expressions=True)[0]['value']


def clone(module,names,extra=None):
    ns=dict(vars(module))|dict(FunctionValue=FunctionValue,QuestionValue=QuestionValue,Content=Content,
        SequenceValue=SequenceValue,numbers=numbers,forbidden=forbidden,unknowns=unknowns,
        perturb=perturb,relation=relation,value=value)|(extra or {})
    for name in names:
        original=getattr(module,name);original=getattr(original,'__wrapped__',original)
        ns[name]=FunctionType(original.__code__,ns,name,original.__defaults__,original.__closure__)
    return ns


@lru_cache(None)
def models():
    norm=clone(trip,('norm_factory',))['norm_factory'];base=clone(equations,('model',))['model']
    runner=lambda group:lambda *args,**kwargs:run(group,*args,**kwargs)
    r=clone(records,('relations','physical','phase_model','setup_model',*CHECKS['records']),
        dict(norm_factory=norm,model=base,run=runner('records')))
    t=clone(transfer,('model','relations','content_value',*CHECKS['transfer']),
        dict(setup_model=r['setup_model'],function_norm=clone(seconds,('function_norm',))['function_norm'],run=runner('transfer')))
    p=clone(polygon,('relations','model','setup_rows',*CHECKS['polygon']),
        dict(physical=r['physical'],phase_model=r['phase_model'],run=runner('polygon')))
    c=clone(curve,('norm_factory','relations','model','adapted','small_model',*CHECKS['curve']),
        dict(polygon_model=p['model'],phase_model=r['phase_model'],run=runner('curve')))
    e=clone(earth,CHECKS['earth'],dict(physical=r['physical'],phase_model=r['phase_model'],
        curve_model=c['model'],norm_factory=c['norm_factory'],relations=c['relations'],run=runner('earth')))
    return dict(records=r,transfer=t,polygon=p,curve=c,earth=e)


@pytest.mark.parametrize('group,name',[(g,n) for g,ns in CHECKS.items() for n in ns])
def test_decoded_transport_distinguishing_models(group,name):assert models()[group][name]()


def test_source_backprojection_parent_and_public_contracts():
    doc=check.restored()['document'];assert check.backprojection(doc)==check.source_excerpt()
    b=check.bridge();assert b['source_statement_indices']==list(range(179,186))
    assert list(b['source_units'])==[f'einstein-1905:u{i:04d}' for i in range(126,129)]
    assert (len(doc['declarations']),len(doc['statements']))==(2521,161)
    parent=check.previous.document();assert doc['statements'][:154]==parent['statements']
    ds={d['name']:d for d in doc['declarations']};assert all(ds[d['name']]==d for d in parent['declarations'])
    current=check.vocabulary().document();prior=check.previous.vocabulary().document()
    for field in ('entries','compounds','definitions','primitives'):
        assert all(current[field][n]==row for n,row in prior[field].items())
    catalog=check.catalogs()['einstein-1905'];old={d['name']:d for d in check.source_excerpt()['declarations']}
    for name,public in check.PUBLIC_RELATIONS.items():
        contract=profile.CONTRACTS[public]
        assert (contract['parameters'],contract['result'])==(old[name]['parameters'],old[name]['result'])
        assert contract['meaning_ja']==re.sub(r'^\[[^]]+ の記号名\] ','',catalog.entries[name]['meaning_ja'])
    assert len(check.vocabulary()._words)==851 and len(check.NEW_DEFINITIONS)==100
    assert b['new_public_relations']==15 and b['new_core_words']==b['new_reference_primitives']==0
    assert (b['new_source_assertions'],b['total_source_assertions'],b['total_annotations'])==(7,129,32)


def test_native_quantified_roles_and_dependency_graph():
    ds={d['name']:d for d in check.restored()['document']['declarations']}
    assert all(ds[d['name']]==d for d in check.role_definitions())
    for old in check.ROLE_ASSIGNMENTS:
        role=ds[check.reference_roles()[old]];seen=set();active=set()
        def visit(name):
            assert name not in active,'Cyclic role dependency'
            if name in seen:return
            seen.add(name);active.add(name)
            for ref in _references(ds[name].get('body')):visit(ref)
            active.remove(name)
        visit(role['name']);assert check.names()[old] not in seen
        exposed=deepcopy(role);added=expose(exposed,{'exists'},only_sort=None)
        if old in check.TRANSFER_ORDER:
            later=check.TRANSFER_ORDER[check.TRANSFER_ORDER.index(old)+1:]
            assert len(added)==len(later)
            assert [p['sort'] for p in exposed['parameters'][2:]]==[check.REFERENCE_SORTS[n] for n in later]
        else:assert len(added)=={'zjr':2,'zjs':1}.get(old,0)
    for old in check.NEW_DEFINITIONS:
        assert ds[mapping()[old]]==renamed(next(d for d in check.source_excerpt()['declarations'] if d['name']==old),mapping())


def reference_values():
    cuts,_=numbers();b=dict(check.BASE)
    for i,(old,sort) in enumerate(check.REFERENCE_SORTS.items()):
        if sort==RS:b[old]=cuts.make(Q(i+1))
    return b,cuts


def test_source_positions_typed_references_and_unknown_inputs():
    b,cuts=reference_values();h=check.context_handlers(b)
    cases=[]
    for old,pos in check.SENTENCES.items():cases.append(('sentencereference',[b['ri'],*map(Q,pos)],b[old]))
    for old,(node,start,end) in check.SPANS.items():cases.append(('sentencetokenspanreference',[b['eirf'],b[node],Q(start),b[node],Q(end),b['ri']],b[old]))
    for old,(first,last) in check.MULTI_SPANS.items():cases.append(('sentencespanreference',[b['eirf'],b[first],b[last],b['ri']],b[old]))
    for old,(node,index) in check.DESIGNATIONS.items():cases.append(('designationreference',[b['eirf'],b[node],Q(index),b['ri']],b[old]))
    for old in check.ROLE_ASSIGNMENTS:
        role=DescriptionValue(check.canonical(dict(kind='function_ref',symbol=check.reference_roles()[old])),
            check.canonical(dict(kind='function',parameters=[check.REFERENCE_SORTS[old],'situation'],result='truth')))
        kind=check.reference_kind(old);args=[b['eirf'],b[check.reference_anchor(old)],role,b['ri']]
        cases.append((kind,args,b[old]))
        for bad in (DescriptionValue('{}',role.result_type),DescriptionValue(role.syntax,'"individual"'),DescriptionValue(role.syntax,role.result_type,1)):
            with pytest.raises(ValueError):h[kind](*args[:2],bad,args[3])
    for kind,args,expected in cases:
        assert h[kind](*args)==expected
        for slot in range(len(args)):
            bad=args[:];bad[slot]=Q(999) if isinstance(args[slot],Q) else 'unknown'
            with pytest.raises(ValueError):h[kind](*bad)
    assert [len(row['tokens']) for row in check.text_boundaries()['sentences'].values()]==[6,89,35,73,31]


def test_native_reference_lookup_does_not_execute_role_or_claim():
    b,cuts=reference_values()
    for old in (*check.SENTENCES,*check.SPANS,*check.ROLE_ASSIGNMENTS,*check.DESIGNATIONS,*check.MULTI_SPANS):
        doc=deepcopy(check.restored()['document']);sort=check.REFERENCE_SORTS.get(old,'individual')
        doc['declarations'].append(dict(kind='primitive',name='transportcapture',parameters=[sort],result='truth'))
        doc['statements']=[dict(kind='ask',body=call('transportcapture',call(check.names()[old])))]
        handlers={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
        handlers.update({check.vocabulary()._symbols[n]:fn for n,fn in check.context_handlers(b).items()})
        handlers['transportcapture']=(lambda x:cuts.read(x)==cuts.read(b[old])) if sort==RS else lambda x:x==b[old]
        domain=tuple({x for x in b.values() if isinstance(x,str)}|{'other'})
        assert evaluate_document(doc,individuals=domain,situations=check.SITUATIONS,primitives=handlers)[0]['value']


def role_fixture(old,retain=None):
    ds={d['name']:d for d in check.restored()['document']['declarations']}
    role=deepcopy(ds[check.reference_roles()[old]]);expose(role,{'exists'},only_sort=None)
    if retain is not None:
        parameter=role['parameters'].pop(retain)
        role['body']=dict(kind='exists',variable=parameter['name'],sort=parameter['sort'],body=role['body'])
    decls=[]
    for symbol in sorted(_references(role['body'])):
        d=ds[symbol];sorts=d['parameters'] if d['kind']=='primitive' else [p['sort'] for p in d['parameters']]
        decls.append(dict(kind='primitive',name=symbol,parameters=sorts,result=d['result']))
    slots=[]
    for i,p in enumerate(role['parameters']):
        symbol='transportslot'+chr(97+i);slots.append(symbol)
        decls.append(dict(kind='primitive',name=symbol,parameters=[],result=p['sort']))
    doc=normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=decls+[role],
        statements=[dict(kind='ask',body=call(role['name'],*(call(s) for s in slots)))]))
    return doc,slots,role


@pytest.mark.parametrize('old',list(check.ROLE_ASSIGNMENTS))
def test_each_role_binding_and_each_relation_slot(old):
    doc,slots,role=role_fixture(old);cuts,_=numbers();c=cuts.make
    def norm(xs):return tuple(cuts.read(x) if isinstance(x,FunctionValue) else value(x) for x in xs)
    def sample(sort,index):return c(Q(index+1)) if sort==RS else ('s' if index%2==0 else 't') if sort=='situation' else ('a' if index%2==0 else 'b')
    args=[sample(p['sort'],i) for i,p in enumerate(role['parameters'])]
    constants={}
    inverse={value:key for key,value in mapping().items()}
    for d in doc['declarations']:
        if d['kind']=='primitive' and not d['parameters'] and d['name'] not in slots:
            constants[inverse[d['name']]]=sample(d['result'],len(constants))
    x,context=args[:2];k=lambda n:constants[n]
    if old in check.TRANSFER_ORDER:
        later=check.TRANSFER_ORDER[check.TRANSFER_ORDER.index(old)+1:]
        witnesses=dict(zip(later,args[2:],strict=True))
        row=[x if n==old else witnesses[n] if n in witnesses else k(n) for n in check.TRANSFER_TUPLE]
        rows={'ejkf':{norm(row)}}
    elif old=='zjr':rows={'eisd3':{norm([k('earthnamespan'),x,k('eirf'),context])},'zjn':{norm([x,args[2],k('ra'),args[3]])}}
    elif old=='zjs':rows={'zjn':{norm([k('zjr'),x,k('ra'),args[2]])}}
    elif old=='zjt':rows={'zjn':{norm([k('zjr'),k('zjs'),k('ra'),x])}}
    elif old=='zjw':rows={'zjl':{norm([x,k('zjt')])}}
    elif old=='zja':rows={'zfl':{norm([x,k('rd'),'ejkn','ejkl',k('eisn5'),context])}}
    else:
        assert old=='zjd'
        rows={'ug':{norm([k('zje'),k('rd'),'ejlx',x,context])},
              'uh':{norm([k('zjf'),k('rd'),'ejlw',x,context]),norm([k('zjy'),k('rd'),'ejmg',x,context])}}
    model={n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}
    def evaluate(model,document=doc,slot_names=slots,arguments=args):
        handlers={d['name']:forbidden for d in document['declarations'] if d['kind']=='primitive'}
        handlers.update({mapping()[n]:lambda x=x:x for n,x in constants.items()})
        handlers.update({mapping()[n]:fn for n,fn in model.items()})
        handlers.update({n:lambda x=x:x for n,x in zip(slot_names,arguments,strict=True)})
        return evaluate_document(document,individuals=('a','b'),situations=('s','t'),primitives=handlers)[0]['value']
    assert perturb(evaluate,model,rows,norm)
    # Restore one actual existential at a time. Other witnesses remain fixed;
    # this distinguishes binder wiring without an exponential tuple-domain test.
    for index,p in enumerate(role['parameters'][2:],2):
        if p['sort'] not in ('individual','situation'):continue
        native,nslots,_=role_fixture(old,index);nargs=args[:index]+args[index+1:]
        assert evaluate(model,native,nslots,nargs)
        if old in check.TRANSFER_ORDER:
            bound_old=check.TRANSFER_ORDER[check.TRANSFER_ORDER.index(old)+1:][index-2]
            relation_name='ejkf';position=check.TRANSFER_TUPLE.index(bound_old)
        else:
            assert old in ('zjr','zjs')
            relation_name='zjn';position=1 if old=='zjr' and index==2 else 3
        original_row=next(iter(rows[relation_name]))
        for witness in ('a','b') if p['sort']=='individual' else ('s','t'):
            changed=tuple(witness if j==position else entry for j,entry in enumerate(original_row))
            assert evaluate(model|{relation_name:lambda *xs,row=changed:norm(xs)==row},native,nslots,nargs)
        outside=tuple('outside-domain' if j==position else entry for j,entry in enumerate(original_row))
        assert not evaluate(model|{relation_name:lambda *xs:norm(xs)==outside},native,nslots,nargs)
        for name in rows:
            assert not evaluate(model|{name:lambda *xs:False},native,nslots,nargs)


