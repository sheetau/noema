"""Check signed cross products and native event/velocity/force connections."""
from functools import lru_cache
from itertools import product
from fractions import Fraction as Q
import json
from noema.grammar import parse,format_graph,number_word
from noema.finite_semantics import FunctionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_material_relative_frame import arithmetic,NUM,RS
from scripts.check_electric_action import setup as electric_setup
from scripts.compose_magnetic_action import ROOT,read,PARENT,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,VECTOR,FIELDS,COMBINED,build

DOC='docs/magnetic-action-v1.md';PRIOR='data/einstein-author-credit-review-v1.json';SOURCE='data/einstein-opening-obligations-v1.json'
AXES=('x','y','z');ALLAXES=AXES+('t',)
DOMAIN=('carrier','frame','event','chargerecord','forcerecord','electricrecord','totalrecord','chargeunit','fieldunit','magneticunit','forceunit','lengthunit','timeunit','chargekind','forcekind',*ALLAXES,'other')
POINT_SORT=dict(kind='function',parameters=['individual'],result=RS)

def forbidden(*xs):raise ValueError('Unknown magnetic-action input')

@lru_cache(None)
def fixture(symbol,native_history=False):
    doc=parse(read(CORE));doc['statements']=[]
    abstract(doc,NUM|{'szi'}|(set() if native_history else {'seob','senz','sjs','sepw'}))
    d=next(d for d in doc['declarations'] if d['name']==symbol);slots=[];arguments=[]
    for i,p in enumerate(d['parameters']):
        n='jmag'+number_word(i);slots.append((n,p['sort']))
        doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
        arguments.append(dict(kind='call',symbol=n,arguments=[]))
    doc['statements']=[dict(kind='ask',body=dict(kind='call',symbol=symbol,arguments=arguments))]
    return doc,slots

def run(symbol,values,model,native_history=False):
    doc,slots=fixture(symbol,native_history);assert len(slots)==len(values);model=dict(model)
    model['szi']=lambda condition,left,right:left if condition else right
    for (n,s),value in zip(slots,values,strict=True):
        if isinstance(s,dict) and not isinstance(value,FunctionValue):value=FunctionValue(tuple(s['parameters']),s['result'],value)
        model[n]=lambda value=value:value
    names={d['name'] for d in doc['declarations'] if d['kind']=='primitive'}
    return evaluate_document(doc,individuals=DOMAIN,situations=('case','other'),primitives={n:model.get(n,forbidden) for n in names},
        max_steps=600000,memoize_definitions=False,memoize_expressions=False)[0]['value']

def values(f,fields):return [f[n] for n,_ in fields]
def cross(v,b):return (v[1]*b[2]-v[2]*b[1],v[2]*b[0]-v[0]*b[2],v[0]*b[1]-v[1]*b[0])
def vector(cuts,values):return lambda a:cuts.make(dict(zip(AXES,values)).get(a,0))

def setup(charge=-2,velocity=(1,2,-1),conversion=Q(3,2)):
    cuts,model,old=electric_setup(charge,Q(1,2));c=cuts.make;r=cuts.read
    electricforce=old['force'];electricfield=old['electricfield']
    magneticfield=lambda a:FunctionValue(tuple([RS]*4),RS,lambda x,y,z,t:c({'x':r(y)+r(t),'y':r(z)-r(x),'z':2*r(x)}.get(a,0)))
    magnetic=vector(cuts,(6,2,2));force=vector(cuts,tuple(charge*conversion*x for x in cross(velocity,(6,2,2))))
    total=lambda a:c(r(electricforce(a))+r(force(a)))
    domain=lambda t:0<r(t)<8
    def curve(t):
        coords=dict(zip(AXES,[base+speed*(r(t)-4) for base,speed in zip((1,2,3),velocity)]));coords['t']=r(t)
        return FunctionValue(('individual',),RS,lambda a:c(coords.get(a,0)))
    f=dict(old,magneticunit='magneticunit',lengthunit='lengthunit',timeunit='timeunit',magneticfield=magneticfield,magnetic=magnetic,
        force=force,conversion=c(conversion),domain=domain,curve=curve,velocity=vector(cuts,velocity),electricrecord='electricrecord',
        electricunit='fieldunit',electricforce=electricforce,electricconversion=c(Q(1,2)),totalrecord='totalrecord',totalforce=total)
    def vector_equal(x,y,axes=ALLAXES):return all(r(x(a))==r(y(a)) for a in axes)
    def field_equal(x,y):return all(r(x(a)(*[c(n) for n in row]))==r(y(a)(*[c(n) for n in row])) for a in AXES for row in ((1,2,3,4),(2,3,4,5)))
    def valid_domain(d):return [d(c(t)) for t in (-1,0,1,4,8,9)]==[False,False,True,True,False,False]
    def track(body,frame,ctx,d,curve_arg):
        return (body,frame,ctx)==('carrier','frame','case') and valid_domain(d) and all(vector_equal(curve_arg(c(t)),curve(c(t))) for t in (3,4,5))
    def force_record(rec,b,k,fr,event,unit,vec,ctx):
        expected={'forcerecord':force,'electricrecord':electricforce,'totalrecord':total}.get(rec)
        return expected is not None and (b,k,fr,event,unit,ctx)==('carrier','forcekind','frame','event','forceunit','case') and vector_equal(vec,expected,AXES)
    model.update(znn=lambda fr,e,b,reg,ctx:(fr,ctx)==('frame','case') and field_equal(e,electricfield) and field_equal(b,magneticfield)
        and reg(*[c(n) for n in (1,2,3,4)]) and not reg(*[c(n) for n in (-1,2,3,4)]),
        eirn=lambda fr,field,unit,ctx:(fr,ctx)==('frame','case') and ((unit=='magneticunit' and field_equal(field,magneticfield)) or (unit=='fieldunit' and field_equal(field,electricfield))),
        eirt=lambda rec,b,fr,event,ctx:(rec,b,fr,event,ctx)==('forcerecord','carrier','frame','event','case'),
        eirl=lambda rec,b,fr,event,ctx:(rec,b,fr,event,ctx)==('electricrecord','carrier','frame','event','case'),
        eirv=lambda rec,b,fr,event,ctx:(rec,b,fr,event,ctx)==('totalrecord','carrier','frame','event','case'),
        eiru=lambda fr,qu,lu,tu,bu,fu,conversion_arg,ctx:(fr,qu,lu,tu,bu,fu,ctx)==('frame','chargeunit','lengthunit','timeunit','magneticunit','forceunit','case') and r(conversion_arg)==conversion,
        zpc=force_record,seob=track,senz=lambda d,t:valid_domain(d) and r(t)==4,
        sjs=lambda d,fn,t,speed:valid_domain(d) and r(t)==4 and r(speed)==(r(fn(c(5)))-r(fn(c(3))))/2,
        sepw=lambda *xs:track(*xs[:5]) and tuple(xs[5:])==('lengthunit','timeunit'))
    return cuts,model,f

@lru_cache(None)
def vector_checks():
    cuts,model=arithmetic();model.update({n:lambda a=a:a for n,a in zip(('yn','yo','yp'),AXES)})
    vectors=((0,0,0),(1,0,0),(0,1,0),(0,0,1),(1,2,-1),(-2,1,3));count=0
    for charge,velocity,magnetic,conversion in product((-2,0,3),vectors,vectors,(Q(1,2),2)):
        result=tuple(charge*conversion*x for x in cross(velocity,magnetic))
        assert run('eicn',[cuts.make(charge),vector(cuts,velocity),vector(cuts,magnetic),cuts.make(conversion),vector(cuts,result)],model)
        assert sum(v*f for v,f in zip(velocity,result))==0
        bad=(result[0]+1,*result[1:])
        assert not run('eicn',[cuts.make(charge),vector(cuts,velocity),vector(cuts,magnetic),cuts.make(conversion),vector(cuts,bad)],model);count+=2
    for conversion in (0,-1):assert not run('eicn',[cuts.make(1),vector(cuts,(1,0,0)),vector(cuts,(0,1,0)),cuts.make(conversion),vector(cuts,(0,0,conversion))],model)
    assert not run('eicn',[cuts.make(1),vector(cuts,(1,0,0)),vector(cuts,(0,1,0)),cuts.make(1),vector(cuts,(0,0,1))],dict(model,yo=lambda:'x'))
    return dict(signed_vector_cases=count,zero_stationary_parallel_cases_included=True,perpendicular_force_in_fixtures=True,
        positive_conversion_required=True,duplicate_axes_rejected=True,native_cross_product=True,
        scalar_boundaries=sorted(NUM|{'szi'}))

def mutate(value,sort,cuts):
    if sort in ('individual','situation'):return 'other'
    if sort=='number':return Q(2)
    if sort=='truth':return not value
    if sort==RS:return cuts.make(cuts.read(value)+1)
    return FunctionValue(tuple(sort['parameters']),sort['result'],lambda *xs:mutate(value(*xs),sort['result'],cuts))

@lru_cache(None)
def record_checks():
    cuts,model,f=setup();assert run('eico',values(f,FIELDS),model)
    for (name,_),(_,sort) in zip(FIELDS,fixture('eico')[1]):
        changed=dict(f);changed[name]=mutate(f[name],sort,cuts)
        assert not run('eico',values(changed,FIELDS),model),name
    for name in ('eirt','eiru','eirn','seob','senz','sjs','sepw','zpc','zpb','znn'):
        assert not run('eico',values(f,FIELDS),dict(model,**{name:lambda *xs:False})),name
    try:run('eico',values(f,FIELDS),dict(model,eirt=forbidden))
    except ValueError as e:assert 'Unknown magnetic-action' in str(e)
    else:raise AssertionError('Unknown magnetic contribution accepted')
    for charge,velocity in ((0,(1,2,-1)),(2,(0,0,0)),(-2,(6,2,2)),(2,(-1,-2,1))):
        c,m,fields=setup(charge,velocity);assert run('eico',values(fields,FIELDS),m)
    try:run('eico',values(f,FIELDS),model,native_history=True)
    except ValueError as e:assert 'rational number domain' in str(e)
    else:raise AssertionError('Full real trajectory sampled')
    return dict(argument_mutations=len(FIELDS),missing_physical_connections=10,degenerate_or_reversed_cases=4,
        native_seoc_charge_record_and_field_evaluation=True,full_history_and_derivative_boundaries=['seob','senz','sjs','sepw'],
        full_real_trajectory_refused=True,unknown_attribution_rejected=True)

@lru_cache(None)
def combined_checks():
    cuts,model,f=setup();assert run('eicp',values(f,COMBINED),model)
    for (name,_),(_,sort) in zip(COMBINED,fixture('eicp')[1]):
        changed=dict(f);changed[name]=mutate(f[name],sort,cuts)
        assert not run('eicp',values(changed,COMBINED),model),name
    assert not run('eicp',values(f,COMBINED),dict(model,eirv=lambda *xs:False))
    # Make the total record accept the altered vector to isolate the native sum.
    for axis in AXES:
        wrong=lambda a:cuts.make(cuts.read(f['totalforce'](a))+(a==axis))
        old=model['zpc']
        patched=dict(model,zpc=lambda rec,*xs:True if rec=='totalrecord' else old(rec,*xs))
        assert not run('eicp',values(dict(f,totalforce=wrong),COMBINED),patched),axis
    return dict(shared_argument_mutations=len(COMBINED),sum_component_mutations=3,magnetic_and_electric_records_native=True,
        mechanical_total_not_substituted=True)

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements']==old.document['statements'] and len(new.document['statements'])==207
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read(PRIOR));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[206])==prior['selection']
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=parse(read(CORE))
    for style in ('compact','full'):
        text=format_graph(doc,style);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    return dict(new_definitions=3,new_primitives=3,preserved_statements=207,author_review_preserved=True,old_approximation_meanings_preserved=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)

def build_report():
    results=dict(vectors=vector_checks(),records=record_checks(),combined=combined_checks(),structure=structure_checks())
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|{DOC,PRIOR,SOURCE,
        'scripts/compose_magnetic_action.py','scripts/check_magnetic_action.py','scripts/compose_electric_action.py','scripts/compose_material_velocity.py',
        'scripts/compose_material_relative_frame.py','scripts/compose_field_equations.py','scripts/compose_rest_force.py','scripts/compose_limits.py',
        'scripts/check_material_relative_frame.py','scripts/check_electric_action.py','scripts/check_tau_differential.py','scripts/check_coordinate_correspondence.py','tests/test_magnetic_action.py'}
    return dict(status='magnetic_and_electromagnetic_force_checked',document=FULL,**results,
        physical_law_empirically_proved=False,magnet_source_classification_complete=False,source_text_coverage_added=False,
        verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
