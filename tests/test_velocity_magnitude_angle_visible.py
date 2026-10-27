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
from scripts import check_einstein_velocity_magnitude_angle_visible as check
from scripts import velocity_magnitude_angle_visible_profile as profile
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
    raise ValueError('Unknown clock-site-time input (velocity-magnitude-angle-visible fixture)')

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
from scripts import check_point_motion_records as records
from scripts import check_point_motion_transform as transform
from scripts import check_velocity_first_order as first
from scripts import check_velocity_magnitude_claim as magnitude
from scripts import check_velocity_angle_measure as angle
from scripts import check_velocity_angle_claim as claim
from scripts import check_velocity_composition_claim as composition
from scripts import check_calculation_discourse as calculation

MODULES=dict(first=first,magnitude=magnitude,angle=angle,claim=claim,composition=composition)
CHECKS=dict(first=('numeric_checks','derivative_checks','bridge_checks','quantifier_checks'),
    magnitude=('magnitude_checks','trajectory_checks','scope_checks','presentation_checks'),
    angle=('integral_checks','branch_checks','geometry_checks','physical_checks'),
    claim=('reference_checks','presentation_checks','attribution_checks'),
    composition=('numeric_checks','physical_checks','chain_checks','presentation_checks'))


@lru_cache(None)
def fixture(group,name,mode='boundary'):
    source=MODULES[group]
    blueprint,slots=source.fixture(name) if group=='claim' else source.fixture(name,mode)
    doc=normalize_document(renamed(deepcopy(blueprint),mapping()))
    decoded={d['name']:d for d in check.restored()['document']['declarations']}
    for i,d in enumerate(doc['declarations']):
        if d['kind']!='definition':continue
        # This is the preserved finite calculation-program boundary. The
        # decoded ejpd/chain definitions still execute against its varied pairs.
        if group=='composition' and name=='ejpd' and d['name']==mapping()['zlx']:
            assert _references(d['body'])-set(mapping().values())<= {'jvccprogram','jvccmid'}
            continue
        # Unsigned s2h is an explicitly retained legacy comparator, not a
        # migrated assertion. The directed geometry s2g/ejou is decoded below.
        if group=='angle' and name=='s2h' and d['name']=='s2h':continue
        assert d['name'] in decoded,(group,name,d['name'])
        actual=deepcopy(decoded[d['name']])
        if mode=='instance' and d['name']==mapping()[name]:
            expected=len(d['parameters'])-len(actual['parameters']);assert expected>0
            assert len(expose(actual,{'forall','exists'},only_sort=RS))==expected
        assert [p['sort'] for p in actual['parameters']]==[p['sort'] for p in d['parameters']]
        assert actual['result']==d['result'];doc['declarations'][i]=actual
    return normalize_document(doc),slots


def run(group,name,*args,**kwargs):
    source=MODULES[group];bound=signature(source.run).bind(name,*args,**kwargs);bound.apply_defaults()
    options=bound.arguments;doc,slots=fixture(group,name,options.get('mode','boundary'));arguments=options['args']
    assert len(arguments)==len(slots),(group,name,len(arguments),len(slots))
    prefix={'first':'jvfo','magnitude':'jvmc','angle':'jvam','claim':'jvac','composition':'jvcc'}[group]
    values=[]
    def capture(x):values.append(x);return True
    mm={n:lambda x=x:x for n,x in source.CONSTANTS.items()}|{prefix+'point':lambda:'discourse',prefix+'result':capture}|options['m']|{n:lambda x=x:x for n,x in zip(slots,arguments)}
    if group=='composition':mm.setdefault('jvccprogram',lambda method,stage,seq:seq if (method,stage)==('method','discourse') else SequenceValue((),seq.element_type))
    mapped={mapping().get(n,n):fn for n,fn in mm.items()}
    result=evaluate_document(doc,individuals=options.get('domain',source.DOMAIN),situations=source.POINTS,
        primitives={d['name']:mapped.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},
        max_steps=3000000,memoize_definitions=True,memoize_expressions=True)[0]['value']
    return values[0] if values else result


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
    norm=clone(trip,('norm_factory',))['norm_factory']
    base=clone(equations,('model',),dict(norm_factory=norm))['model']
    runner=lambda group:lambda *args,**kwargs:run(group,*args,**kwargs)
    t=clone(transfer,('relations','physical','phase_model'),dict(norm_factory=norm,model=base))
    r=clone(records,('relations','moving_model'),dict(physical=t['physical'],phase_model=t['phase_model'],norm_factory=norm))
    tf=clone(transform,('model',),dict(clock_model=base,moving_model=r['moving_model']))
    core=lambda:renamed(check.restored()['document'],{v:k for k,v in mapping().items()})
    f=clone(first,('relations',*CHECKS['first']),dict(model=tf['model'],run=runner('first'),core=core))
    m=clone(magnitude,('norm_with_domains','relations',*CHECKS['magnitude']),dict(model=tf['model'],moving_model=r['moving_model'],run=runner('magnitude')))
    a=clone(angle,('arithmetic','relations','branch_model',*CHECKS['angle']),dict(norm_factory=norm,run=runner('angle')))
    c=clone(claim,('introduction_rows',*CHECKS['claim']),dict(norm_factory=norm,run=runner('claim')))
    pair=clone(calculation,('pair',),dict(symbol=value))['pair']
    cp=clone(composition,('arithmetic',*CHECKS['composition']),dict(norm_factory=norm,pair=pair,symbol=value,run=runner('composition')))
    return dict(first=f,magnitude=m,angle=a,claim=c,composition=cp)


@pytest.mark.parametrize('group,name',[(g,n) for g,ns in CHECKS.items() for n in ns])
def test_decoded_velocity_magnitude_angle_distinguishing_models(group,name):assert models()[group][name]()


def test_source_order_parent_and_public_contracts():
    doc=check.restored()['document'];assert check.backprojection(doc)==check.source_excerpt()
    b=check.bridge();assert b['source_statement_indices']==[190,191,0,1,2,3,4]
    assert list(b['source_units'])==[f'einstein-1905:u{i:04d}' for i in range(135,141)]
    assert len(doc['statements'])==172
    parent=check.previous.document();assert doc['statements'][:165]==parent['statements']
    ds={d['name']:d for d in doc['declarations']};assert all(ds[d['name']]==d for d in parent['declarations'])
    current=check.vocabulary().document();prior=check.previous.vocabulary().document()
    for field in ('entries','compounds','definitions','primitives'):
        assert all(current[field][n]==row for n,row in prior[field].items())
    catalog=check.catalogs()['einstein-1905'];old={d['name']:d for d in check.source_excerpt()['declarations']}
    for name,public in check.PUBLIC_RELATIONS.items():
        contract=profile.CONTRACTS[public]
        assert (contract['parameters'],contract['result'])==(old[name]['parameters'],old[name]['result'])
        assert contract['meaning_ja']==re.sub(r'^\[[^]]+ の記号名\] ','',catalog.entries[name]['meaning_ja'])
    assert len(check.vocabulary()._words)==859 and len(check.NEW_DEFINITIONS)==61
    assert (b['new_public_relations'],b['new_core_words'],b['new_reference_primitives'])==(3,0,1)
    assert (b['new_source_assertions'],b['total_source_assertions'],b['total_annotations'])==(7,140,32)


def test_native_role_dependency_graph_and_preserved_definitions():
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
    for old in check.NEW_DEFINITIONS:
        assert ds[mapping()[old]]==renamed(next(d for d in check.source_excerpt()['declarations'] if d['name']==old),mapping())


def reference_values():
    cuts,_=numbers();b=dict(check.BASE)
    for i,(old,sort) in enumerate(check.REFERENCE_SORTS.items()):
        if sort==RS:b[old]=cuts.make(Q(i+1))
        elif sort==profile.PAIR:b[old]=FunctionValue(('truth',),RS,lambda flag:cuts.make(Q(3,5) if flag else Q(-4,5)))
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
    assert [len(row['tokens']) for row in check.text_boundaries()['sentences'].values()]==[15,18,6]

def test_native_reference_lookup_does_not_execute_role_or_claim():
    b,cuts=reference_values()
    for old in (*check.HEADINGS,*check.SENTENCES,*check.SPANS,*check.ROLE_ASSIGNMENTS,*check.DESIGNATIONS,*check.MULTI_SPANS):
        doc=deepcopy(check.restored()['document']);sort=check.REFERENCE_SORTS.get(old,'individual')
        doc['declarations'].append(dict(kind='primitive',name='velocitycapture',parameters=[sort],result='truth'))
        doc['statements']=[dict(kind='ask',body=call('velocitycapture',call(check.names()[old])))]
        handlers={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
        handlers.update({check.vocabulary()._symbols[n]:fn for n,fn in check.context_handlers(b).items()})
        handlers['velocitycapture']=(lambda x:cuts.read(x)==cuts.read(b[old])) if sort==RS else (lambda x:all(cuts.read(x(flag))==cuts.read(b[old](flag)) for flag in (False,True))) if sort==profile.PAIR else lambda x:x==b[old]
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
    doc,slots,role=role_fixture(old);cuts,_=numbers();c=lambda x:cuts.make(Q(x))
    def norm(xs):return tuple(cuts.read(x) if isinstance(x,FunctionValue) else value(x) for x in xs)
    constants={'zb6':'physical','rd':'author','eisoq':'section'}
    if old in ('zkp','zkq','eiso4'):
        args=[c(5),'reference'];relation_name={'zkp':'ejoi','zkq':'ejoj','eiso4':'ejow'}[old]
        rows={relation_name:{(Q(5),'physical')}}
    elif old in ('zkr','zks'):
        args=['equation','reference'];methods=('ejoi','ejok') if old=='zkr' else ('ejoj','ejol')
        rows={'zb':{('equation','author',*methods,'section','reference')}}
    else:
        assert old=='zkt'
        constants|={'ra':'K','zbm':'k','zb7':c(3),'zkc':c(3),'zkd':c(-4),'zkq':c(5)}
        pair=FunctionValue(('truth',),RS,lambda flag:c(Q(3,5) if flag else Q(-4,5)))
        # Abstract role-boundary witnesses only: these are not pi/atan values.
        args=[pair,'reference',c(-1),c(Q(-4,3)),c(-1),c(4)]
        rows={'sbg':{(Q(3),)},'ejm2':{('K','k','physical',Q(3),Q(0),Q(0))},
            'ejoj':{(Q(5),'physical')},
            'ejou':{tuple(map(Q,(3,0,3,3,-4,5,Q(3,5),Q(-4,5),Q(-4,3),-1,4,-1)))},
            'ejos':{tuple(map(Q,(3,-4,Q(-4,3),-1,4,-1)))}}
    assert len(args)==len(slots)
    model={n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}
    def evaluate(model,document=doc,slot_names=slots,arguments=args):
        handlers={d['name']:forbidden for d in document['declarations'] if d['kind']=='primitive'}
        handlers.update({mapping()[n]:lambda x=x:x for n,x in constants.items()})
        handlers[mapping()['bb']]=lambda x:c(x)
        handlers.update({mapping()[n]:fn for n,fn in model.items()})
        handlers.update({n:lambda x=x:x for n,x in zip(slot_names,arguments,strict=True)})
        declared={d['name'] for d in document['declarations'] if d['kind']=='primitive'}
        return evaluate_document(document,individuals=('K','k','author','section','equation','other'),situations=('physical','reference','other'),primitives={n:handlers[n] for n in declared})[0]['value']
    assert perturb(evaluate,model,rows,norm)
    # Reference context is separate from the fixed physical situation. The
    # equation-presentation roles deliberately use the former, all others the latter.
    changed=args[:];changed[1]='other'
    assert evaluate(model,arguments=changed)==(old not in ('zkr','zks'))
    if old!='zkt':
        changed=args[:];changed[0]=c(6) if old in ('zkp','zkq','eiso4') else 'other'
        assert not evaluate(model,arguments=changed)
        return
    for flag in (False,True):
        changed=args[:]
        changed[0]=FunctionValue(('truth',),RS,lambda b,flag=flag:c((Q(3,5) if b else Q(-4,5))+(1 if b==flag else 0)))
        assert not evaluate(model,arguments=changed)
    # All four real witnesses are exposed independently, with the others held
    # fixed. Retaining any one binder must refuse finite enumeration.
    for index in range(2,6):
        changed=args[:];changed[index]=c(cuts.read(args[index])+1)
        assert not evaluate(model,arguments=changed)
        updated={n:set(rs) for n,rs in rows.items()}
        for name,positions in (('ejou',{2:11,3:8,4:9,5:10}),('ejos',{2:5,3:2,4:3,5:4})):
            row=list(next(iter(updated[name])));row[positions[index]]=cuts.read(changed[index]);updated[name]={tuple(row)}
        assert evaluate({n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in updated.items()},arguments=changed)
        native,nslots,_=role_fixture(old,index);nargs=args[:index]+args[index+1:]
        with pytest.raises(ValueError,match='Cannot finitely quantify|Finite function domain'):
            evaluate(model,native,nslots,nargs)
