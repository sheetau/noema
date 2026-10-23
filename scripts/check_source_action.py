"""Check native source-force records, occupancy, cancellation and kind binding."""
from functools import lru_cache
from itertools import product
from fractions import Fraction as Q
import json
from noema.grammar import parse,format_graph,number_word
from noema.finite_semantics import FunctionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.extraction import extract_document
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_material_relative_frame import arithmetic,NUM,RS
from scripts.check_magnetic_action import setup as magnetic_setup,mutate,vector,DOMAIN as MAGNETIC_DOMAIN
from scripts.check_conductor_cases import sentinel as base_sentinel,same_value
from scripts.compose_source_action import ROOT,read,PARENT,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,FIELDS,CLASSIFIED,SOURCE,source_args,capacity_args,build

DOC='docs/source-action-v1.md';PRIOR='data/einstein-author-credit-review-v1.json';OBLIGATIONS='data/einstein-opening-obligations-v1.json'
DOMAIN=MAGNETIC_DOMAIN+('sourcebody','hostbody','condition','body','standard')
CONTEXTS=('case','first','other');AXES=('x','y','z');ROLES=AXES+('t',)

def forbidden(*xs):raise ValueError('Unknown source-action input')

def sentinel(sort,tag,cuts):
    return Q(tag) if sort=='number' else base_sentinel(sort,tag,cuts)

@lru_cache(None)
def fixture(symbol,mode='native'):
    doc=parse(read(CORE));doc['statements']=[]
    boundaries=NUM|{'szi','eicr','eici'}
    if mode!='history':boundaries|={'seob','senz','sjs','sepw'}
    if mode=='binding':boundaries|={'eicw'}
    abstract(doc,boundaries)
    d=next(d for d in doc['declarations'] if d['name']==symbol);slots=[];arguments=[]
    for i,p in enumerate(d['parameters']):
        n='jsac'+number_word(i);slots.append((n,p['sort']))
        doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
        arguments.append(dict(kind='call',symbol=n,arguments=[]))
    doc['statements']=[dict(kind='ask',body=dict(kind='call',symbol=symbol,arguments=arguments))]
    return doc,slots

def run(symbol,values,model,mode='native'):
    doc,slots=fixture(symbol,mode);assert len(slots)==len(values);model=dict(model,szi=lambda condition,left,right:left if condition else right)
    for (n,s),value in zip(slots,values,strict=True):
        if isinstance(s,dict) and not isinstance(value,FunctionValue):value=FunctionValue(tuple(s['parameters']),s['result'],value)
        model[n]=lambda value=value:value
    names={d['name'] for d in doc['declarations'] if d['kind']=='primitive'}
    return evaluate_document(doc,individuals=DOMAIN,situations=CONTEXTS,primitives={n:model.get(n,forbidden) for n in names},
        max_steps=1000000,memoize_definitions=False,memoize_expressions=False)[0]['value']

def values(f,fields):return [f[n] for n,_ in fields]

def setup(charge=-2,cancel=False):
    cuts,model,old=magnetic_setup(charge);c=cuts.make;r=cuts.read
    f=dict(old,sourcebody='sourcebody',hostbody='hostbody',sourcecondition='condition',sourcerecord=old['totalrecord'],sourceforce=old['totalforce'])
    if cancel:
        assert charge!=0
        e=tuple(-r(f['force'](a))/(charge*r(f['electricconversion'])) for a in AXES)
        f['electric']=vector(cuts,e)
        f['electricfield']=lambda a:FunctionValue(tuple([RS]*4),RS,lambda *xs:c(dict(zip(AXES,e)).get(a,0)))
        f['electricforce']=lambda a:c(-r(f['force'](a)))
        f['sourceforce']=vector(cuts,(0,0,0))
    def field_equal(a,b):
        return all(r(a(axis)(*[c(n) for n in row]))==r(b(axis)(*[c(n) for n in row])) for axis in AXES for row in ((1,2,3,4),(2,3,4,5)))
    def region_equal(a,b):return all(a(*[c(n) for n in row])==b(*[c(n) for n in row]) for row in ((1,2,3,4),(-1,2,3,4)))
    def source(*xs):
        expected=[f['sourcebody' if n=='body' else n] for n,_ in SOURCE]
        return tuple(xs[:8])==tuple(expected[:8]) and field_equal(xs[8],expected[8]) and field_equal(xs[9],expected[9]) and region_equal(xs[10],expected[10])
    def record(rec,b,kind,frame,event,unit,vec,ctx):
        expected={f['electricrecord']:f['electricforce'],f['forcerecord']:f['force'],f['sourcerecord']:f['sourceforce']}.get(rec)
        return expected is not None and (b,kind,frame,event,unit,ctx)==('carrier','forcekind','frame','event','forceunit','case') and all(r(vec(a))==r(expected(a)) for a in AXES)
    model.update(zm=lambda b:b in ('sourcebody','hostbody'),eirw=source,
        eiry=lambda rec,source,carrier,frame,event,condition,ctx:rec in (f['electricrecord'],f['forcerecord'],f['sourcerecord']) and (source,carrier,frame,event,condition,ctx)==('sourcebody','carrier','frame','event','condition','case'),
        eiro=lambda b,frame,ctx,lu,tu,x,y,z,t:(b,frame,ctx,lu,tu)==('hostbody','frame','case','lengthunit','timeunit') and tuple(map(r,(x,y,z,t)))==(1,2,3,4),
        zzbv=lambda b,event,ctx:(b,event,ctx)==('carrier','event','case'),
        zzbu=lambda event,frame,ctx,lu,tu,t,x,y,z:(event,frame,ctx,lu,tu)==('event','frame','case','lengthunit','timeunit') and tuple(map(r,(t,x,y,z)))==(4,1,2,3),
        znn=lambda frame,e,b,reg,ctx:(frame,ctx)==('frame','case') and field_equal(e,f['electricfield']) and field_equal(b,f['magneticfield']) and region_equal(reg,f['region']),
        eirn=lambda frame,field,unit,ctx:(frame,ctx)==('frame','case') and ((unit=='fieldunit' and field_equal(field,f['electricfield'])) or (unit=='magneticunit' and field_equal(field,f['magneticfield']))),
        zpc=record,eirv=forbidden)
    return cuts,model,f

@lru_cache(None)
def action_checks():
    cuts,model,f=setup();assert run('eicw',values(f,FIELDS),model) and run('eicx',values(f,FIELDS),model)
    for (name,_),(_,sort) in zip(FIELDS,fixture('eicw')[1]):
        changed=dict(f);changed[name]=mutate(f[name],sort,cuts)
        assert not run('eicw',values(changed,FIELDS),model),name
    for name in ('eirw','eiro','zm','zzbu','zzbv'):
        assert not run('eicw',values(f,FIELDS),dict(model,**{name:lambda *xs:False})),name
    for missing in ('electricrecord','forcerecord','sourcerecord'):
        prior=model['eiry']
        assert not run('eicw',values(f,FIELDS),dict(model,eiry=lambda rec,*xs:rec!=f[missing] and prior(rec,*xs))),missing
    for axis in AXES:
        wrong=lambda a:cuts.make(cuts.read(f['sourceforce'](a))+(a==axis))
        prior=model['zpc']
        permissive=dict(model,zpc=lambda rec,*xs:True if rec==f['sourcerecord'] else prior(rec,*xs))
        assert not run('eicw',values(dict(f,sourceforce=wrong),FIELDS),permissive),axis
    for charge in (-2,0,2):
        c,m,fields=setup(charge)
        assert run('eicw',values(fields,FIELDS),m)
        assert run('eicx',values(fields,FIELDS),m)==(charge!=0)
    c,m,fields=setup(cancel=True)
    assert any(c.read(fields['electricforce'](a))!=0 for a in AXES) and any(c.read(fields['force'](a))!=0 for a in AXES)
    assert run('eicw',values(fields,FIELDS),m) and not run('eicx',values(fields,FIELDS),m)
    try:run('eicw',values(f,FIELDS),dict(model,eiry=forbidden))
    except ValueError as e:assert 'Unknown source-action' in str(e)
    else:raise AssertionError('Unknown force source accepted')
    try:run('eicw',values(f,FIELDS),model,'history')
    except ValueError as e:assert 'rational number domain' in str(e)
    else:raise AssertionError('Full real trajectory sampled')
    return dict(argument_mutations=len(FIELDS),missing_connections=8,sum_component_mutations=3,signed_charge_cases=3,
        nonzero_contributions_can_cancel=True,native_electric_and_magnetic_action=True,native_sb_and_vector_sum=True,
        whole_electromagnetic_force_not_used=True,unknown_source_rejected=True,full_history_refused=True,
        boundaries=['scalar arithmetic and szi','seob','senz','sjs','sepw'])

@lru_cache(None)
def classification_checks():
    cuts,model=arithmetic();slots=fixture('eicz','binding')[1];fields=CLASSIFIED
    supplied=[sentinel(s,i+1,cuts) for i,(_,s) in enumerate(slots)];pos={n:i for i,(n,_) in enumerate(fields)}
    for symbol,axis in zip(('yn','yo','yp'),AXES):model[symbol]=lambda axis=axis:axis
    def gate(names,enabled,xs):
        return enabled and len(xs)==len(names) and all(same_value(x,supplied[pos[n]],slots[pos[n]][1],cuts) for x,n in zip(xs,names))
    def local(bits):
        return dict(model,eicw=lambda *xs:gate([n for n,_ in FIELDS],bits[0],xs),
            eicr=lambda *xs:gate([x.removeprefix('v ') for x in source_args()],bits[1],xs),
            eici=lambda *xs:gate([x.removeprefix('v ') for x in capacity_args()],bits[2],xs))
    count=0;original=supplied[pos['sourceforce']]
    for bits in product((False,True),repeat=4):
        supplied[pos['sourceforce']]=original if bits[3] else FunctionValue(('individual',),RS,lambda a:cuts.make(0))
        assert run('eicy',supplied,local(bits),'binding')==all(bits[:3])
        assert run('eicz',supplied,local(bits),'binding')==all(bits);count+=2
    supplied[pos['sourceforce']]=original
    for i,(_,sort) in enumerate(slots):
        changed=supplied.copy();changed[i]=sentinel(sort,100+i,cuts)
        assert not run('eicz',changed,local((True,)*4),'binding'),fields[i][0]
        old=supplied[i];supplied[i]=changed[i]
        assert run('eicz',changed,local((True,)*4),'binding'),fields[i][0]
        supplied[i]=old
    return dict(truth_combinations=count,shared_argument_mutations=len(slots),distinguishing_slot_variants=len(slots),
        capacity_threshold_not_a_force_threshold=True,boundaries=['eicw','eicr','eici'])

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements']==old.document['statements'] and len(new.document['statements'])==207
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read(PRIOR));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[206])==prior['selection']
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=parse(read(CORE))
    dependencies={d['name'] for d in extract_document(doc,roots=['eicw'],statement_indices=[]).document['declarations']}
    assert not dependencies&{'eicp','eirv','eici','eicr'}
    assert {'eibs','eico','eirw','eiry','sb','eiro'}<=dependencies
    for style in ('compact','full'):
        text=format_graph(doc,style);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    return dict(new_definitions=4,new_primitives=1,preserved_statements=207,author_review_preserved=True,
        source_contribution_distinct_from_whole_force=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)

def build_report():
    results=dict(action=action_checks(),classification=classification_checks(),structure=structure_checks())
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|{DOC,PRIOR,OBLIGATIONS,
        'scripts/compose_source_action.py','scripts/check_source_action.py','scripts/compose_magnetic_action.py','scripts/compose_electric_action.py',
        'scripts/compose_magnet_source.py','scripts/compose_conductor_reading.py','scripts/compose_material_relative_frame.py','scripts/compose_field_equations.py',
        'scripts/compose_rest_force.py','scripts/compose_limits.py','scripts/check_conductor_cases.py','scripts/check_magnetic_action.py','scripts/check_electric_action.py',
        'scripts/check_material_relative_frame.py','scripts/check_tau_differential.py','scripts/check_coordinate_correspondence.py','tests/test_source_action.py'}
    return dict(status='source_resolved_force_in_host_checked',document=FULL,**results,source_application_complete=False,
        whole_interaction_complete=False,physical_current_generation_proved=False,source_text_coverage_added=False,
        verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
