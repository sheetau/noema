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
from scripts import check_einstein_velocity_addition_setting_visible as check
from scripts import velocity_addition_setting_visible_profile as profile
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
    raise ValueError('Unknown clock-site-time input (velocity-addition-setting-visible fixture)')

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
from scripts import check_clock_transfer_records as transfer
from scripts import check_velocity_opening_claim as opening
from scripts import check_point_motion_records as records
from scripts import check_point_motion_transform as transform
from scripts import check_point_motion_claim as claim

MODULES=dict(opening=opening,records=records,transform=transform,claim=claim)
CHECKS=dict(opening=('relative_checks','event_binding_checks','composition_checks','designation_checks','presentation_checks'),
    records=('local_checks','binding_checks','coverage_checks','velocity_checks','planar_checks','setup_checks'),
    transform=('numeric_checks','binding_checks','bridge_checks','full_scope_checks','candidate_checks','content_checks'),
    claim=('presentation_checks','attribution_checks'))


@lru_cache(None)
def fixture(group,name,mode='boundary'):
    source=MODULES[group]
    if group=='claim':blueprint,slots=source.fixture(name),[]
    elif group=='opening':blueprint,slots=source.fixture(name)
    else:blueprint,slots=source.fixture(name,mode)
    doc=normalize_document(renamed(deepcopy(blueprint),mapping()))
    decoded={d['name']:d for d in check.restored()['document']['declarations']}
    for i,d in enumerate(doc['declarations']):
        if d['kind']!='definition':continue
        actual=deepcopy(decoded[d['name']])
        if mode=='instance' and d['name']==mapping()[name]:
            expected=len(d['parameters'])-len(actual['parameters']);assert expected>0
            assert len(expose(actual,{'forall','exists'},only_sort=RS))==expected
        assert [p['sort'] for p in actual['parameters']]==[p['sort'] for p in d['parameters']]
        assert actual['result']==d['result'];doc['declarations'][i]=actual
    return normalize_document(doc),slots


def run(group,name,*args,**kwargs):
    source=MODULES[group];bound=signature(source.run).bind(name,*args,**kwargs);bound.apply_defaults()
    options=bound.arguments;doc,slots=fixture(group,name,options.get('mode','boundary'))
    arguments=options.get('args',[]);assert len(arguments)==len(slots),(group,name,len(arguments),len(slots))
    point={'opening':'jvocpoint','records':'jpmrpoint','transform':'jpmtpoint','claim':'jpmcpoint'}[group]
    mm={n:lambda x=x:x for n,x in source.CONSTANTS.items()}|{point:lambda:'discourse'}|options['m']|{n:lambda x=x:x for n,x in zip(slots,arguments)}
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
    t=clone(transfer,('relations','physical','phase_model'),dict(norm_factory=norm,model=base))
    r=clone(records,('relations','moving_model',*CHECKS['records']),
        dict(physical=t['physical'],phase_model=t['phase_model'],norm_factory=norm,run=runner('records')))
    o=clone(opening,('relations',*CHECKS['opening']),dict(physical=t['physical'],run=runner('opening')))
    tf=clone(transform,('model',*CHECKS['transform']),dict(clock_model=base,moving_model=r['moving_model'],run=runner('transform')))
    c=clone(claim,CHECKS['claim'],dict(run=runner('claim')))
    return dict(opening=o,records=r,transform=tf,claim=c)


@pytest.mark.parametrize('group,name',[(g,n) for g,ns in CHECKS.items() for n in ns])
def test_decoded_velocity_addition_distinguishing_models(group,name):assert models()[group][name]()


def test_source_backprojection_parent_and_public_contracts():
    doc=check.restored()['document'];assert check.backprojection(doc)==check.source_excerpt()
    b=check.bridge();assert b['source_statement_indices']==list(range(186,190))
    assert list(b['source_units'])==[f'einstein-1905:u{i:04d}' for i in range(129,135)]
    assert (len(doc['declarations']),len(doc['statements']))==(2579,165)
    parent=check.previous.document();assert doc['statements'][:161]==parent['statements']
    ds={d['name']:d for d in doc['declarations']};assert all(ds[d['name']]==d for d in parent['declarations'])
    current=check.vocabulary().document();prior=check.previous.vocabulary().document()
    for field in ('entries','compounds','definitions','primitives'):
        assert all(current[field][n]==row for n,row in prior[field].items())
    catalog=check.catalogs()['einstein-1905'];old={d['name']:d for d in check.source_excerpt()['declarations']}
    for name,public in check.PUBLIC_RELATIONS.items():
        contract=profile.CONTRACTS[public]
        assert (contract['parameters'],contract['result'])==(old[name]['parameters'],old[name]['result'])
        assert contract['meaning_ja']==re.sub(r'^\[[^]]+ の記号名\] ','',catalog.entries[name]['meaning_ja'])
    assert len(check.vocabulary()._words)==855 and len(check.NEW_DEFINITIONS)==39
    assert b['new_public_relations']==4 and b['new_core_words']==b['new_reference_primitives']==0
    assert (b['new_source_assertions'],b['total_source_assertions'],b['total_annotations'])==(4,133,32)


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
        assert len(added)=={'zkb':2,'zkc':1}.get(old,0)
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
    for old,ordinal in check.HEADINGS.items():cases.append(('headingreference',[b['ri'],Q(ordinal)],b[old]))
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
    assert [len(row['tokens']) for row in check.text_boundaries()['sentences'].values()]==[29,10,23]


def test_native_reference_lookup_does_not_execute_role_or_claim():
    b,cuts=reference_values()
    for old in (*check.HEADINGS,*check.SENTENCES,*check.SPANS,*check.ROLE_ASSIGNMENTS,*check.DESIGNATIONS,*check.MULTI_SPANS):
        doc=deepcopy(check.restored()['document']);sort=check.REFERENCE_SORTS.get(old,'individual')
        doc['declarations'].append(dict(kind='primitive',name='velocitycapture',parameters=[sort],result='truth'))
        doc['statements']=[dict(kind='ask',body=call('velocitycapture',call(check.names()[old])))]
        handlers={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
        handlers.update({check.vocabulary()._symbols[n]:fn for n,fn in check.context_handlers(b).items()})
        handlers['velocitycapture']=(lambda x:cuts.read(x)==cuts.read(b[old])) if sort==RS else lambda x:x==b[old]
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
        symbol='velocityslot'+chr(97+i);slots.append(symbol)
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
    if old=='eisoq':rows={'eisdv':{norm([k('eisor'),x,k('eisdx'),k('eirf'),Q(2),Q(5),context])}}
    elif old=='zkb':rows={'ejmw':{norm([x,k('zbm'),args[2],args[3],k('zb6')])}}
    elif old=='zkc':rows={'ejmw':{norm([k('zkb'),k('zbm'),x,args[2],k('zb6')])}}
    else:
        assert old=='zkd'
        rows={'ejmw':{norm([k('zkb'),k('zbm'),k('zkc'),x,k('zb6')])}}
    model={n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}
    def evaluate(model,document=doc,slot_names=slots,arguments=args):
        handlers={d['name']:forbidden for d in document['declarations'] if d['kind']=='primitive'}
        handlers.update({mapping()[n]:lambda x=x:x for n,x in constants.items()})
        handlers.update({mapping()[n]:fn for n,fn in model.items()})
        handlers.update({n:lambda x=x:x for n,x in zip(slot_names,arguments,strict=True)})
        return evaluate_document(document,individuals=('a','b'),situations=('s','t'),primitives=handlers)[0]['value']
    assert perturb(evaluate,model,rows,norm)
    # Function-valued witnesses cannot be finitely enumerated. Check every exposed
    # binding and the unchanged Native body, and require refusal to sample it.
    for index,p in enumerate(role['parameters'][2:],2):
        assert p['sort']==RS
        native,nslots,_=role_fixture(old,index);nargs=args[:index]+args[index+1:]
        with pytest.raises(ValueError,match='Cannot finitely quantify|Finite function domain'):
            evaluate(model,native,nslots,nargs)
        for witness in (Q(-2),Q(3)):
            varied=args[:];varied[index]=c(witness)
            position=index if old=='zkb' else 3
            row=next(iter(rows['ejmw']))
            changed=tuple(witness if j==position else entry for j,entry in enumerate(row))
            assert evaluate(model|{'ejmw':lambda *xs,row=changed:norm(xs)==row},arguments=varied)
            assert not evaluate(model|{'ejmw':lambda *xs:False},arguments=varied)
