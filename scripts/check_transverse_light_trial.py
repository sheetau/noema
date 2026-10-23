"""Check two transverse axes, full diagonal paths and current clock bindings."""
from copy import deepcopy
from fractions import Fraction as Q
from functools import lru_cache
from math import isqrt
import json
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import FunctionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_moving_trip_geometry import NUM,numbers,norm_factory
from scripts.check_clock_site_time import perturb,unknowns,forbidden
from scripts.check_axial_time_condition import trial_model
from scripts.check_light_time_expansion import model as prior_model,segments,EVENTS,TUPLES,CLOCKS,PLACES
from scripts.check_translated_light_trial import expose,CONSTANTS,DOMAIN
from scripts.compose_transverse_light_trial import ROOT,read,PARENT,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,INDEX,MEANINGS,conjuncts,build

DOC='docs/transverse-light-trial-v1.md';PRIOR='data/einstein-arbitrary-start-claim-review-v1.json'
DEPENDENCIES=('reports/arbitrary-start-claim-v1.json','reports/translated-light-trial-v1.json','reports/transverse-time-v1.json','reports/light-time-expansion-v1.json','reports/moving-trip-geometry-v1.json')
RS=dict(kind='function',parameters=['number'],result='truth')

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document;boundaries=NUM|{'bj','sle'}
    if name=='ei3w':boundaries|={'eiz7','qo'}
    if name=='ei3x':boundaries|={'eifw','eior','eiyg','eiyi','eiyj'}
    if name=='ei3z' and mode!='native_history':boundaries.add('se')
    if name=='ei32':boundaries|={'ei3w','eizm','ei3i','ei3h','ei3z','ei3x'}
    if name=='ei33':boundaries|={'ei3d','ei3c','eiyf','eios','ei32'}
    abstract(doc,boundaries);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name)
    if name=='ei33' and mode=='instance':assert len(expose(d,{'exists'}))==5
    slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jtt'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    doc['statements']=[dict(kind='ask',body=dict(kind='call',symbol=name,arguments=args))];return doc,slots

def run(name,args,m,mode='boundary'):
    doc,slots=fixture(name,mode);assert len(args)==len(slots),(name,len(args),len(slots))
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|m|{n:lambda x=x:x for n,x in zip(slots,args)}
    return evaluate_document(doc,individuals=DOMAIN,situations=('context','discourse','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=600000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def relations(m,rows,norm):return m|{n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}

def square_root(cuts):
    def root(light,speed):
        n=cuts.read(light)**2-cuts.read(speed)**2
        if n<0:forbidden()
        a,b=isqrt(n.numerator),isqrt(n.denominator)
        if a*a!=n.numerator or b*b!=n.denominator:forbidden()
        return cuts.make(Q(a,b))
    return root

@lru_cache(None)
def numeric_checks():
    cuts,m=numbers();c=cuts.make;m['sle']=square_root(cuts);count=0
    for V,s,w in ((5,3,4),(13,5,12),(5,0,5)):
        for origin,length,start in ((12,12,5),(-7,Q(3,2),Q(-2,3))):
            middle=Q(start)+Q(length,w);last=middle+Q(length,w);base=list(map(Q,(origin,length,V,s,start,middle,last,w)))
            for slot in (0,1,4,5,6,7):
                for delta in (0,Q(1,4)):
                    xs=base.copy();xs[slot]+=delta
                    expected=(xs[1]>0 and xs[4]<xs[5]<xs[6] and xs[3]>=0 and xs[3]<xs[2] and xs[7]>0 and xs[3]**2+xs[7]**2==xs[2]**2 and xs[7]*(xs[5]-xs[4])==xs[1] and xs[7]*(xs[6]-xs[5])==xs[1])
                    assert run('ei3y',list(map(c,xs)),m)==expected;count+=1
    for xs in ((12,12,5,-3,5,8,11,4),(12,12,5,5,5,8,11,4),(12,12,-5,3,5,8,11,4),(12,0,5,3,5,5,5,4),(12,12,5,3,5,8,11,5),(12,12,5,3,5,8,11,-4),(12,12,5,3,5,8,10,4)):
        assert not run('ei3y',list(map(c,map(Q,xs))),m);count+=1
    args=list(map(c,map(Q,(12,12,5,3,5,8,11,4))));unknowns(lambda mm:run('ei3y',args,mm),m,('sle','ba','bc','bg','bf','shv','sca'))
    unknown=args.copy();unknown[0]=FunctionValue(('number',),'truth',lambda x:x<12)
    try:run('ei3y',unknown,m)
    except ValueError:pass
    else:raise AssertionError('Unknown cut decoded by sampling')
    return dict(cases=count,both_positive_equal_transverse_travel_times_and_Pythagorean_components_checked=True,total_speed_not_transverse_speed=True,zero_speed_allowed_only_in_generic_numeric_comparison=True,unknown_cuts_refused=True,root_oracle_limited_to_exact_retained_rational_roots=True)

@lru_cache(None)
def trial_checks():
    count=0
    for axis in ('y','z'):
        cuts,m,rows,norm=trial_model();rows.pop('zbv');rows['zef']=rows.pop('zdw');rows['zbw']={('moving','axis',axis,'context')}
        def selected(f,a,ctx):
            if (f,ctx)!=('moving','context') or a not in ('x','y','z'):forbidden()
            return 'axis'
        m=relations(m,rows,norm)|{'zbo':selected};args=['trial','firstclock','secondclock','context',axis]
        count+=perturb(lambda mm:run('ei3w',args,mm),m,rows,norm)
        for other in ('x','z' if axis=='y' else 'y'):assert not run('ei3w',args[:-1]+[other],m);count+=1
        for patch in ({'qd':lambda tr:'origin'},{'qg':lambda tr:'depart'},{'qj':lambda tr:cuts.make(Q(2))},{'yp':lambda:'y'}):assert not run('ei3w',args,m|patch);count+=1
        assert run('ei3w',args,m|{'zbn':forbidden,'zbv':forbidden,'zdw':forbidden,'sgp':forbidden});count+=1
        unknowns(lambda mm:run('ei3w',args,mm),m,('zbo','qc','qd','qe','qf','qg','qh','qi','qj','qk'))
    return dict(cases=count,both_transverse_axes_require_native_roundtrip_and_current_local_readings=True,both_full_parallel_k_paths_and_distinct_axes_required=True,old_origin_and_local_clock_rules_not_used=True)

def model(axis):
    cuts,m,coords,_=prior_model();c=cuts.make;r=cuts.read
    points=((12,2,-3,5),(21,14 if axis=='y' else 2,-3 if axis=='y' else 9,8),(30,2,-3,11));coords.update(zip(TUPLES,points))
    fn=FunctionValue((RS,)*4,RS,lambda x,y,z,t:c(2*r(t)-3*r(x)/8))
    m|={'tc':lambda:c(Q(5)),'zb7':lambda:c(Q(3)),'zd4':lambda:fn,'sle':square_root(cuts)}
    m['te']=lambda tr:'firstclock' if tr=='trial' else forbidden();m['tf']=lambda tr:'secondclock' if tr=='trial' else forbidden()
    for n,t in zip(('qi','qj','qk'),(5,8,11)):m[n]=lambda tr,t=t:c(2*Q(t)+Q(9,8)) if tr=='trial' else forbidden()
    return cuts,m,coords,fn

@lru_cache(None)
def segment_checks():
    cuts,m,coords,fn=model('y');c=cuts.make;r=cuts.read;m,rows,norm=segments(cuts,m);rows.pop('zbw');rows.pop('zdw')
    rows['eifw']={(s,'frame','reference',Q(5),'context') for s in ('outward','returning')}
    rows['eiyg']={(e,cl,p,'frame',Q(t),'context') for e,cl,p,t in zip(EVENTS,CLOCKS,PLACES,(5,8,11))}
    for n,vals in (('wo',{'outward':5,'returning':8}),('wp',{'outward':8,'returning':11}),('wq',{'outward':15,'returning':15})):
        m[n]=lambda seg,vals=vals:c(Q(vals[seg])) if seg in vals else forbidden()
    m['zbe']=lambda e,f,u,ctx:c(Q((5,8,11)[EVENTS.index(e)])) if e in EVENTS and (f,u,ctx)==('frame','unit','context') else forbidden()
    m=relations(m,rows,norm);args=[['outward','ray','depart','reflection',c(Q(15)),'context'],['returning','ray','reflection','arrival',c(Q(15)),'context']]
    check=lambda mm:all(run('ei3x',a,mm) for a in args);count=perturb(check,m,rows,norm)
    for slot in ('wo','wp','wq'):
        for seg in ('outward','returning'):
            old=m[slot];assert not check(m|{slot:lambda s,old=old,seg=seg:c(r(old(s))+(1 if s==seg else 0))});count+=1
    assert check(m|{'zbo':forbidden,'zdw':forbidden,'zef':forbidden,'sbc':forbidden,'shd':forbidden});count+=1
    unknowns(check,m,('wf','wi','wj','wk','wl','wm','wn','wo','wp','wq','zbe','zdz','zc6','tc'))
    return dict(cases=count,both_diagonal_K_segments_keep_geometric_lengths_and_current_local_times=True,K_paths_not_required_parallel_to_k_axes=True,full_path_length_differs_from_transverse_distance=True)

def geometry_model(axis):
    cuts,m,coords,fn=model(axis);c=cuts.make;r=cuts.read;norm=norm_factory(cuts,(5,6,8,11))
    linear=lambda start,x,s:FunctionValue((RS,),RS,lambda t:c(Q(x)+Q(s)*(r(t)-start)))
    y,z=2,-3;my,mz=(14,-3) if axis=='y' else (2,9);vy,vz=(4,0) if axis=='y' else (0,4)
    def history(obj,lo,hi,x,yy,zz,sy,sz):return [obj,'frame','context','lengthunit','unit',c(Q(lo)),c(Q(hi)),linear(lo,x,3),linear(lo,yy,sy),linear(lo,zz,sz)]
    histories=[history('origin',5,11,12,y,z,0,0),history('mirror',5,11,12,my,mz,0,0),history('ray',5,8,12,y,z,vy,vz),history('ray',8,11,21,my,mz,-vy,-vz)]
    rows={'se':{norm(h) for h in histories},'eisb5':{('ray','frame','context')},'cf':{('ray',)},'cg':{('ray','depart','reflection','frame'),('ray','reflection','arrival','frame')},'ch':{('ray','reflection','frame')},'eisca':{('ray','depart','reflection','frame','context'),('ray','reflection','arrival','frame','context')},'zzbu':set(),'zzbv':set()}
    for endpoint,event,t,x,yy,zz in (('origin','depart',5,12,y,z),('mirror','reflection',8,21,my,mz),('origin','arrival',11,30,y,z)):
        rows['zzbu'].add((event,'frame','context','lengthunit','unit',*map(Q,(t,x,yy,zz))))
        for obj in (endpoint,'ray'):rows['zzbv'].add((obj,event,'context'))
    args=['origin','mirror','ray',*EVENTS,'frame','context','lengthunit','unit',*map(c,map(Q,(12,12,5,3,5,8,11,2,-3,4))),axis]
    return cuts,relations(m,rows,norm),rows,norm,args

@lru_cache(None)
def geometry_checks():
    count=0
    for axis in ('y','z'):
        cuts,m,rows,norm,args=geometry_model(axis);c=cuts.make;r=cuts.read
        count+=perturb(lambda mm:run('ei3z',args,mm),m,rows,norm)
        for slot in (10,11,14,15,16,17,18,19):
            bad=args.copy();bad[slot]=c(r(bad[slot])+1);assert not run('ei3z',bad,m);count+=1
        for role in ('x','z' if axis=='y' else 'y'):assert not run('ei3z',args[:-1]+[role],m);count+=1
        for patch in ({'yp':lambda:'y'},{'yn':lambda:axis}):assert not run('ei3z',args,m|patch);count+=1
        try:run('ei3z',args,m|{'zzbg':lambda a,b:r(a)<r(b)},'native_history')
        except ValueError as e:assert 'Cannot finitely quantify' in str(e) or 'Finite function domain' in str(e),str(e)
        else:raise AssertionError('Full trajectories accepted by finite sampling')
    return dict(cases=count,both_axes_native_four_complete_histories_and_six_meetings_bound=True,outbound_and_returning_K_longitudinal_velocity_same_v=True,selected_transverse_velocity_reverses_and_other_component_zero=True,full_real_histories_refused=2,finite_fingerprints_are_only_binding_checks=True)

@lru_cache(None)
def connection_checks():
    count=0
    for axis in ('y','z'):
        cuts,m,coords,fn=model(axis);c=cuts.make;r=cuts.read;norm=norm_factory(cuts,())
        triples=((-3,2,-3),(-3,14 if axis=='y' else 2,-3 if axis=='y' else 9),(-3,2,-3))
        rows={'ei3w':{('trial','firstclock','secondclock','context',axis)},'eizm':{('origin','context'),('mirror','context')},'ei3i':{('trial','context')},'ei3h':{(e,t,*map(Q,xyz),'context') for e,t,xyz in zip(EVENTS,TUPLES,triples)},'ei3z':{('origin','mirror','ray',*EVENTS,'frame','context','lengthunit','unit',*map(Q,(12,12,5,3,5,8,11,2,-3,4)),axis)},'ei3x':{('outward','ray','depart','reflection',Q(15),'context'),('returning','ray','reflection','arrival',Q(15),'context')}}
        args=['trial',axis,'origin','outward','returning',*map(c,map(Q,(12,4,-3,2,-3,5))),'context'];m=relations(m,rows,norm)
        count+=perturb(lambda mm:run('ei32',args,mm),m,rows,norm)
        for slot in range(5,11):
            bad=args.copy();bad[slot]=c(r(bad[slot])+1);assert not run('ei32',bad,m);count+=1
        assert not run('ei32',args[:1]+['x']+args[2:],m);count+=1
        unknowns(lambda mm:run('ei32',args,mm),m,('te','tf','qc','qd','qh','qe','qf','qg','zdz','zc6','tc','zb7','shv','bf','sca'))
        def normfn(xs):return tuple((r(x(c(Q(0)),c(Q(0)),c(Q(0)),c(Q(5)))),) if isinstance(x,FunctionValue) and len(x.parameters)==4 else norm((x,))[0] for x in xs)
        outer={'ei3d':{('context','history')},'ei3c':{((Q(10),),'context')},'eiyf':{('frame','context')},'eios':{(Q(5),'context')},'ei32':{norm(args)}}
        mm=relations(m,outer,normfn);outerargs=['trial',axis,'origin',*map(c,map(Q,(-3,2,-3,5))),'context','history','outward','returning',c(Q(12)),c(Q(4))]
        count+=perturb(lambda mm:run('ei33',outerargs,mm,'instance'),mm,outer,normfn)
        try:run('ei33',outerargs[:8],mm)
        except ValueError as e:assert 'Cannot finitely quantify' in str(e),str(e)
        else:raise AssertionError('Finite real witnesses accepted')
    return dict(cases=count,same_trial_point_axis_K_coordinates_and_three_tau_readings_required=True,constant_auxiliary_x_and_other_transverse_coordinate_preserved=True,two_geometric_paths_use_V_times_same_elapsed_times=True,all_global_current_clock_and_history_conditions_required=True,native_real_witness_quantification_refused=2)

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements']==old.document['statements'] and len(new.document['statements'])==INDEX
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read(PRIOR));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[282,283])==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);assert json.loads(read(ANNOTATIONS))['entries']==json.loads(read('data/arbitrary-start-claim-identifiers-v1.json'))['entries']
    oldds={d['name']:d for d in old.document['declarations']};ds={d['name']:d for d in new.document['declarations']}
    d=deepcopy(ds['ei3w']);axis=d['parameters'].pop()['name'];body=d['body']['arguments'][1]
    def undo(n):
        if isinstance(n,list):return [undo(x) for x in n]
        if not isinstance(n,dict):return n
        if n.get('kind')=='variable' and n['name']==axis:return dict(kind='call',symbol='yn',arguments=[])
        return {k:undo(x) for k,x in n.items()}
    assert undo(body)==oldds['ei3f']['body'] and d['parameters']==oldds['ei3f']['parameters']
    expected=[r for r in conjuncts(oldds['ei2m']['body']) if r.get('symbol') not in ('zbw','zdw')]
    assert conjuncts(ds['ei3x']['body'])==expected and ds['ei3x']['parameters']==oldds['ei2m']['parameters']
    assert ds['skz']==oldds['skz']
    doc=parse(read(CORE))
    for style in ('compact','full'):
        body=format_graph(doc,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    return dict(new_definitions=len(MEANINGS),new_primitives=0,preserved_statements=INDEX,previous_whole_unit_judgment_preserved=True,exact_trial_axis_adaptation_and_only_two_K_axis_constraints_removed=True,root_and_component_definition_unchanged=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('numeric',numeric_checks),('trial',trial_checks),('segments',segment_checks),('geometry',geometry_checks),('connection',connection_checks),('structure',structure_checks)]}
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|{DOC,PRIOR,*DEPENDENCIES,'scripts/compose_transverse_light_trial.py','scripts/check_transverse_light_trial.py','tests/test_transverse_light_trial.py','scripts/check_coordinate_correspondence.py','scripts/check_moving_trip_geometry.py','scripts/check_material_relative_frame.py','scripts/check_clock_site_time.py','scripts/check_rod_methods.py','scripts/check_axial_time_condition.py','scripts/check_light_time_expansion.py','scripts/check_translated_light_trial.py','scripts/compose_moving_trip_geometry.py','scripts/compose_limits.py','scripts/compose_material_relative_frame.py'}
    return dict(status='both_transverse_current_trials_and_complete_diagonal_K_paths_checked',document=FULL,**results,verified_full_units={'kant-1784':0,'einstein-1905':0},general_real_physical_derivation_proved=False,remaining=['u0059–u0061の全候補範囲と同じτの局所微分への接続','類似議論・注意条件・二偏微分零の帰属','原刊H/Z表記と全文の意味判断'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
