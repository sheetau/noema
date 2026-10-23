"""Check generalized contexts, translated full paths and current trial bindings."""
from copy import deepcopy
from functools import lru_cache
from fractions import Fraction as Q
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
from scripts.check_light_time_expansion import model as prior_model,segments,CONSTANTS as PRIOR_CONSTANTS,DOMAIN as PRIOR_DOMAIN
from scripts.compose_translated_light_trial import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,INDEX,MEANINGS,build

DOC='docs/translated-light-trial-v1.md'
PRIORS=tuple(f'data/einstein-differential-step-u{n:04d}-review-v1.json' for n in (54,55,56,57))
DEPENDENCIES=('reports/differential-step-v1.json','reports/light-time-expansion-v1.json','reports/axial-time-condition-v1.json','reports/comoving-time-task-v1.json','reports/event-coordinate-task-v1.json','reports/measured-space-sentence-v1.json')
RS=dict(kind='function',parameters=['number'],result='truth')
CONSTANTS=PRIOR_CONSTANTS
DOMAIN=tuple(dict.fromkeys([*PRIOR_DOMAIN,'firstclock','secondclock','history','moment','a','b']))

def expose(d,kinds,only_sort=None):
    added=[]
    def walk(node):
        if isinstance(node,list):return [walk(x) for x in node]
        if not isinstance(node,dict):return node
        if node.get('kind') in kinds and (only_sort is None or node['sort']==only_sort):
            added.append(dict(name=node['variable'],sort=node['sort']));return walk(node['body'])
        return {k:walk(v) for k,v in node.items()}
    d['body']=walk(d['body']);d['parameters']+=added
    return added

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    boundaries=NUM|{'bj'}
    if name in ('ei26','ei27','ei3a'):boundaries|={'eiyx','shh'}
    if name=='ei3b':boundaries|={'ei3a','ei26','ei27'}
    if name=='ei3c':boundaries|={'ei3b','eiyf','eiyx','eiyg'}
    if name=='ei3d':boundaries|={'eivf','eivg','eivl','eiwn','eixs','eipw','eigy','eivv'}
    if name=='ei3e':boundaries|={'eifw','eior','eiyg','eiyi','eiyj'}
    if name=='ei3f':boundaries|={'eiz7','qo'}
    if name=='ei3g':boundaries|={'se'}
    if name in ('ei3h','ei3i'):boundaries.add('eiyx')
    if name=='ei3j':boundaries|={'ei3f','eizm','ei3i','ei3h','ei3g','ei3e'}
    if name=='ei3k':boundaries|={'ei3d','ei3c','eiyf','eios','ei3j'}
    if name=='ei3l':boundaries.add('eizm')
    abstract(doc,boundaries);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name)
    if name=='ei3b' and mode=='instance':assert len(expose(d,{'forall'}))==2
    if name=='ei3c' and mode=='instance':assert len(expose(d,{'forall'}))==5
    if name=='ei3k' and mode=='instance':assert len(expose(d,{'exists'}))==4
    if name=='ei3l' and mode=='instance':assert len(expose(d,{'exists'}))==1
    slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jtlta'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    doc['statements']=[dict(kind='ask',body=dict(kind='call',symbol=name,arguments=args))];return doc,slots

def run(name,args,m,mode='boundary',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(args)==len(slots),(name,len(args),len(slots))
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|m|{n:lambda x=x:x for n,x in zip(slots,args)}
    return evaluate_document(doc,individuals=domain,situations=('context','discourse','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=700000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def relations(m,rows,norm):return m|{n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}

@lru_cache(None)
def correspondence_checks():
    # Two individuals distinguish every quantifier slot without a large product.
    domain=('a','b');ctx='other';base={'zc4':lambda e:e=='a','eiyx':lambda e,t,f,c:(e,t,f,c) in {('a','a','a',ctx),('a','b','b',ctx)},'shh':lambda a,b:a==b,'ra':lambda:'a','zbm':lambda:'b'}
    assert run('ei3a',[ctx],base,domain=domain);count=1
    for missing in (('a','a','a',ctx),('a','b','b',ctx)):
        good={('a','a','a',ctx),('a','b','b',ctx)}-{missing}
        assert not run('ei3a',[ctx],base|{'eiyx':lambda *xs:xs in good},domain=domain);count+=1
    assert not run('ei3a',['context'],base,domain=domain);count+=1
    assert not run('ei3a',[ctx],base|{'zc4':lambda e:False},domain=domain);count+=1
    assert not run('ei3a',[ctx],base|{'eiyx':lambda e,t,f,c:c==ctx},domain=domain);count+=1
    for first in domain:
        for second in domain:
            assert run('ei26',[first,second,ctx],base,domain=domain)==((first,second)==('a','b'));count+=1
    for frame in domain:
        for tup in domain:
            assert run('ei27',[tup,frame,ctx],base,domain=domain)==(tup==frame);count+=1
    return dict(cases=count,native_same_event_graph_and_both_complete_coordinate_ranges=True,alternative_context_not_fixed_to_baseline=True,missing_and_nonunique_coordinates_rejected=True)

def global_model():
    cuts,m=numbers();c=cuts.make;r=cuts.read;norm=norm_factory(cuts,());ctx='other'
    # Eager Boolean evaluation also visits explicitly known non-coordinate
    # fixture individuals before reaching the real-domain refusal. Only a/b
    # belong to eiyx; these extra cells do not assert coordinate validity.
    coords={t:(3,4,5,6) for t in DOMAIN};coords.update(a=(5,0,0,5),b=(8,1,2,10));roles=('x','y','z','time')
    def coordinate(t,a):
        if t not in coords or a not in roles:forbidden()
        return c(Q(coords[t][roles.index(a)]))
    fn=FunctionValue((RS,)*4,RS,lambda x,y,z,t:c(2*r(t)-r(x)/4))
    m|={'zb7':lambda:c(Q(1)),'zc6':coordinate,'zbi':lambda f,g,lu,tu,ct:c(Q(1)) if (f,g,lu,tu,ct)==('frame','moving','lengthunit','unit',ctx) else forbidden()}
    rows={'ei3a':{(ctx,)},'ei27':{('a','frame',ctx),('b','moving',ctx)},'ei26':{('a','b',ctx)}}
    return cuts,relations(m,rows,norm),fn,norm,rows

@lru_cache(None)
def global_clock_checks():
    cuts,m,fn,norm,rows=global_model();c=cuts.make;r=cuts.read;ctx='other';count=0
    # Expose the native quantified body; constants retain distinct typed values.
    # Correspondence scope itself is tested natively on two individuals above.
    for first in ('a','b'):
        for second in ('a','b'):
            assert run('ei3b',[fn,ctx,first,second],m,'instance');count+=1
    args=[fn,ctx,'a','b'];check=lambda mm:run('ei3b',args,mm,'instance')
    assert not check(m|{'zb7':lambda:c(Q(2))});count+=1
    assert not check(m|{'ei3a':lambda *xs:False});count+=1
    old=m['zc6'];assert not check(m|{'zc6':lambda tup,role:c(r(old(tup,role))+(1 if (tup,role)==('b','time') else 0))});count+=1
    unknowns(check,m,('zc6','zbi','zb7','ba','sca','bf','shv'))
    rows={'eiyf':{('moving',ctx)},'zc4':{('a',)},'eiyx':{('a','a','frame',ctx)},'zcz':{('a','moving',ctx)},'zbz':{('moving','b',ctx)},'cb':{('b','a','moving'),('a','a','moving')},'eiyg':{('a','b','a','moving',Q(10),ctx)}}
    mm=relations(m,rows,norm)|{'ei3b':lambda f,ct:ct==ctx and r(f(c(Q(1)),c(Q(0)),c(Q(0)),c(Q(5))))==Q(39,4)}
    local=lambda reading:[fn,ctx,'a','b','a','a',c(Q(reading))]
    for reading in (10,11):assert run('ei3c',local(reading),mm,'instance');count+=1
    assert not run('ei3c',local(11),mm|{'eiyg':lambda e,cl,p,f,val,ct:(e,cl,p,f,ct)==('a','b','a','moving',ctx) and r(val) in (10,11)},'instance');count+=1
    assert not run('ei3c',local(10),mm|{'eiyg':lambda *xs:False},'instance');count+=1
    assert not run('ei3c',local(10),mm|{'eiyf':lambda *xs:False},'instance');count+=1
    assert not run('ei3c',local(10),mm|{'ei3b':lambda *xs:False},'instance');count+=1
    for name,args in (('ei3c',[fn,ctx]),('ei3k',['a','b',*map(c,map(Q,(7,2,-3,5))),ctx])):
        try:run(name,args,mm)
        except ValueError as e:assert 'Cannot finitely quantify' in str(e)
        else:raise AssertionError('Full real-valued quantifier accepted by finite evaluator')
    return dict(cases=count,all_candidate_clock_values_required_and_spurious_readings_rejected=True,full_real_clock_and_trial_quantification_refused=True,instances_are_binding_checks_only=True)

@lru_cache(None)
def adaptation_checks():
    old={d['name']:d for d in parse(read('examples/v014/einstein-differential-step.noema'))['declarations']};new={d['name']:d for d in parse(read(FULL))['declarations']}
    # Undo just the documented adaptations and compare modulo variable names.
    def alpha(d):
        counter=[0]
        def fresh():counter[0]+=1;return 'v'+str(counter[0])
        env={p['name']:fresh() for p in d['parameters']}
        def walk(n,scope):
            if isinstance(n,list):return [walk(x,scope) for x in n]
            if not isinstance(n,dict):return n
            if n.get('kind')=='variable':return {'kind':'variable','name':scope[n['name']]}
            if n.get('kind') in ('forall','exists','content'):
                sc=scope|{n['variable']:fresh()};return {**n,'variable':sc[n['variable']],'body':walk(n['body'],sc)}
            if n.get('kind')=='lambda':
                sc=scope|{p['name']:fresh() for p in n['parameters']};return {**n,'parameters':[dict(p,name=sc[p['name']]) for p in n['parameters']],'body':walk(n['body'],sc)}
            return {k:walk(v,scope) for k,v in n.items()}
        return ([p['sort'] for p in d['parameters']],d['result'],walk(d['body'],env))
    for source,target in (('eixt','ei3d'),('ei2m','ei3e')):
        d=deepcopy(new[target]);hist=d['parameters'][-1]['name'] if target=='ei3d' else None
        if hist:d['parameters'].pop()
        def undo(n):
            if isinstance(n,list):return [undo(x) for x in n]
            if not isinstance(n,dict):return n
            if hist and n.get('kind')=='variable' and n['name']==hist:return dict(kind='call',symbol='zcj',arguments=[])
            n={k:undo(v) for k,v in n.items()}
            if target=='ei3e' and n.get('symbol')=='zef':n['symbol']='zdw'
            return n
        d['body']=undo(d['body']);assert alpha(d)==alpha(old[source])
    return dict(physical_history_adaptation_preserves_all_other_conditions=True,parallel_segment_adaptation_preserves_all_current_clock_and_light_conditions=True)

@lru_cache(None)
def trial_checks():
    cuts,m,rows,norm=trial_model();rows.pop('zbv');rows['zef']=rows.pop('zdw');m=relations(m,rows,norm)
    check=lambda mm:run('ei3f',['trial','firstclock','secondclock','context'],mm)
    count=perturb(check,m,rows,norm)
    assert check(m|{'zbn':forbidden,'zbv':forbidden,'zdw':forbidden,'sgp':forbidden});count+=1
    for patch in ({'qg':lambda tr:'depart'},{'qd':lambda tr:'origin'},{'qj':lambda tr:cuts.make(Q(2))}):assert not check(m|patch);count+=1
    unknowns(check,m,('qc','qd','qe','qf','qg','qh','qi','qj','qk','zbo','bg'))
    return dict(cases=count,native_roundtrip_clock_roles_sync_scope_and_current_local_times_preserved=True,departure_not_required_to_be_frame_origin=True,both_full_parallel_paths_required=True)

def translated_model():
    cuts,m,coords,_=prior_model();c=cuts.make;r=cuts.read
    coords.update(tuplea=(12,2,-3,5),tupleb=(30,2,-3,11),tuplec=(21,2,-3,14))
    fn=FunctionValue((RS,)*4,RS,lambda x,y,z,t:c(2*r(t)-r(x)/4+3*r(y)+7*r(z)))
    m['zd4']=lambda:fn
    for n,val in zip(('qi','qj','qk'),(Q(-27,4),Q(9,4),Q(45,4))):m[n]=lambda tr,val=val:c(val) if tr=='trial' else forbidden()
    m['te']=lambda tr:'firstclock' if tr=='trial' else forbidden();m['tf']=lambda tr:'secondclock' if tr=='trial' else forbidden()
    return cuts,m,coords,fn

@lru_cache(None)
def selected_coordinate_checks():
    cuts,m,coords,fn=translated_model();c=cuts.make;r=cuts.read;norm=norm_factory(cuts,())
    events=('depart','reflection','arrival');tuples=('tuplea','tupleb','tuplec');labels=(7,19,7)
    rows={'eiyx':{(e,t,'frame','context') for e,t in zip(events,tuples)}};m=relations(m,rows,norm)
    checks=lambda mm:all(run('ei3h',[e,t,*map(c,map(Q,(x,2,-3))),'context'],mm) for e,t,x in zip(events,tuples,labels)) and run('ei3i',['trial','context'],mm)
    count=perturb(checks,m,rows,norm)
    for t in tuples:
        for axis in ('x','y','z','time'):
            old=m['zc6'];assert not checks(m|{'zc6':lambda rec,a,t=t,axis=axis:c(r(old(rec,a))+(1 if (rec,a)==(t,axis) else 0))});count+=1
    unknowns(checks,m,('zdz','zc6','qe','qf','qg','qi','qj','qk','zd4','zb7','bf','shv','sca','ba'))
    return dict(cases=count,three_current_K_tuples_and_actual_tau_readings_bound=True,nonzero_transverse_coordinates_and_auxiliary_origin_preserved=True)

@lru_cache(None)
def segment_checks():
    cuts,m,coords,fn=translated_model();c=cuts.make;m,rows,norm=segments(cuts,m);rows['zef']=rows.pop('zdw');m=relations(m,rows,norm)
    args=[['outward','ray','depart','reflection',c(Q(18)),'context'],['returning','ray','reflection','arrival',c(Q(9)),'context']]
    check=lambda mm:all(run('ei3e',xs,mm) for xs in args);count=perturb(check,m,rows,norm)
    assert check(m|{'zdw':forbidden,'sba':forbidden,'sbc':forbidden,'shd':forbidden});count+=1
    unknowns(check,m,('wf','wi','wj','wk','wl','wm','wn','wo','wp','wq','zbe','zbo','zdz','zc6'))
    return dict(cases=count,both_segments_current_K_clocks_geometric_length_and_principle_scope=True,parallel_support_line_not_original_axis_required=True)

@lru_cache(None)
def geometry_checks():
    cuts,m,coords,fn=translated_model();c=cuts.make;norm=norm_factory(cuts,(5,8,11,14))
    def linear(start,x,speed):return FunctionValue((RS,),RS,lambda t:c(Q(x)+Q(speed)*(cuts.read(t)-start)))
    y=linear(0,2,0);z=linear(0,-3,0)
    histories=[['origin','frame','context','lengthunit','unit',c(Q(5)),c(Q(14)),linear(5,12,1),y,z],['mirror','frame','context','lengthunit','unit',c(Q(5)),c(Q(14)),linear(5,24,1),y,z],['ray','frame','context','lengthunit','unit',c(Q(5)),c(Q(11)),linear(5,12,3),y,z],['ray','frame','context','lengthunit','unit',c(Q(11)),c(Q(14)),linear(11,30,-3),y,z]]
    rows={'se':{norm(h) for h in histories},'eisb5':{('ray','frame','context')},'cf':{('ray',)},'cg':{('ray','depart','reflection','frame'),('ray','reflection','arrival','frame')},'ch':{('ray','reflection','frame')},'eisca':{('ray','depart','reflection','frame','context'),('ray','reflection','arrival','frame','context')},'zzbu':set(),'zzbv':set()}
    for point,event,t,x in (('origin','depart',5,12),('mirror','reflection',11,30),('origin','arrival',14,21)):
        rows['zzbu'].add((event,'frame','context','lengthunit','unit',Q(t),Q(x),Q(2),Q(-3)))
        for obj in (point,'ray'):rows['zzbv'].add((obj,event,'context'))
    m=relations(m,rows,norm);args=['origin','mirror','ray','depart','reflection','arrival','frame','context','lengthunit','unit',*map(c,map(Q,(12,12,3,1,5,11,14,2,-3)))]
    count=perturb(lambda mm:run('ei3g',args,mm),m,rows,norm)
    for slot in range(10,19):
        bad=args.copy();bad[slot]=c(cuts.read(bad[slot])+1);assert not run('ei3g',bad,m);count+=1
    return dict(cases=count,native_four_complete_histories_and_six_same_event_meetings=True,arbitrary_constant_y_z_preserved_and_transverse_velocities_zero=True,history_fingerprints_not_full_real_trajectory_proofs=True)

@lru_cache(None)
def connection_checks():
    cuts,m,coords,fn=translated_model();c=cuts.make;norm=norm_factory(cuts,())
    rows={'ei3f':{('trial','firstclock','secondclock','context')},'eizm':{('origin','context'),('mirror','context')},'ei3i':{('trial','context')},'ei3h':{(e,t,Q(x),Q(2),Q(-3),'context') for e,t,x in zip(('depart','reflection','arrival'),('tuplea','tupleb','tuplec'),(7,19,7))},'ei3g':{('origin','mirror','ray','depart','reflection','arrival','frame','context','lengthunit','unit',*map(Q,(12,12,3,1,5,11,14,2,-3)))},'ei3e':{('outward','ray','depart','reflection',Q(18),'context'),('returning','ray','reflection','arrival',Q(9),'context')}}
    m=relations(m,rows,norm);args=['trial','origin','outward','returning',*map(c,map(Q,(12,7,2,-3,5))),'context']
    count=perturb(lambda mm:run('ei3j',args,mm),m,rows,norm)
    for slot in range(4,9):
        bad=args.copy();bad[slot]=c(cuts.read(bad[slot])+1);assert not run('ei3j',bad,m);count+=1
    unknowns(lambda mm:run('ei3j',args,mm),m,('te','tf','qc','qd','qh','qe','qf','qg','zdz','zc6','tc','zb7','bd','bf','sca'))
    # Exposed witnesses test every binding, without replacing existential real scope.
    def normfn(xs):return tuple((cuts.read(x(c(Q(0)),c(Q(0)),c(Q(0)),c(Q(5)))),) if isinstance(x,FunctionValue) and len(x.parameters)==4 else norm((x,))[0] for x in xs)
    outer={'ei3d':{('context','history')},'ei3c':{((Q(10),),'context')},'eiyf':{('frame','context')},'eios':{(Q(3),'context')},'ei3j':{norm(args)}}
    mm=relations(m,outer,normfn);outerargs=['trial','origin',*map(c,map(Q,(7,2,-3,5))),'context','history','outward','returning',c(Q(12))]
    count+=perturb(lambda mm:run('ei3k',outerargs,mm,'instance'),mm,outer,normfn)
    return dict(cases=count,all_trial_geometry_coordinates_two_segments_and_global_conditions_bound=True,all_witness_slots_checked_without_claiming_finite_real_existence=True)

@lru_cache(None)
def point_checks():
    cuts,m=numbers();c=cuts.make;r=cuts.read;norm=norm_factory(cuts,());ctx='other';domain=('a','b')
    rows={'zdi':{('a',ctx)},'zcu':{('a','moving',ctx)},'x4':{('a','moving',ctx)},'eizm':{('a',ctx)},'ys':{('b',ctx)},'zce':{('a','b','frame','lengthunit',ctx)},'zcf':{('b','frame','unit',ctx)}}
    def moment(mo,f,u,ct):
        if mo not in domain or (f,u,ct)!=('frame','unit',ctx):forbidden()
        return c(Q(5 if mo=='b' else 8))
    def track(p,f,lu,tu,a,ct):
        if (p,f,lu,tu,ct)!=('a','frame','lengthunit','unit',ctx) or a not in ('x','y','z'):forbidden()
        return FunctionValue((RS,),RS,lambda t:c(7+r(t) if a=='x' else 2 if a=='y' else -3))
    def position(p,mo,f,lu,a,ct):return track(p,f,lu,'unit',a,ct)(moment(mo,f,'unit',ct))
    m=relations(m,rows,norm)|{'yl':moment,'ym':position,'eismh':track,'zb7':lambda:c(Q(1))}
    args=['a',*map(c,map(Q,(7,2,-3,5))),ctx,'b'];check=lambda mm:run('ei3l',args,mm,'instance')
    count=perturb(check,m,rows,norm)
    for slot in range(1,5):
        bad=args.copy();bad[slot]=c(r(bad[slot])+1);assert not run('ei3l',bad,m,'instance');count+=1
    assert not run('ei3l',args[:-1]+['a'],m,'instance');count+=1
    assert check(m|{'eiyg':forbidden,'zbe':forbidden,'eiyx':forbidden});count+=1
    unknowns(check,m,('yl','ym','eismh','zb7','ba','sca','bf','shv'))
    return dict(cases=count,same_measured_point_time_and_representative_trajectory_bound=True,baseline_point_not_required_to_already_have_local_clock_reading=True)

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements']==old.document['statements'] and len(new.document['statements'])==INDEX
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    for i,path in enumerate(PRIORS):
        prior=json.loads(read(path));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[280+i//2])==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);assert json.loads(read(ANNOTATIONS))['entries']==json.loads(read('data/differential-step-identifiers-v1.json'))['entries']
    doc=parse(read(CORE))
    for style in ('compact','full'):
        body=format_graph(doc,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    return dict(new_definitions=len(MEANINGS),new_primitives=0,preserved_statements=INDEX,all_prior_judgments_unchanged=True,whole_unit_review_not_yet_claimed=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('correspondence',correspondence_checks),('global_clocks',global_clock_checks),('adaptations',adaptation_checks),('trial',trial_checks),('coordinates',selected_coordinate_checks),('segments',segment_checks),('geometry',geometry_checks),('connection',connection_checks),('point',point_checks),('structure',structure_checks)]}
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|{DOC,*PRIORS,*DEPENDENCIES,'scripts/compose_translated_light_trial.py','scripts/check_translated_light_trial.py','tests/test_translated_light_trial.py','scripts/check_coordinate_correspondence.py','scripts/check_moving_trip_geometry.py','scripts/check_material_relative_frame.py','scripts/check_clock_site_time.py','scripts/check_rod_methods.py','scripts/check_axial_time_condition.py','scripts/check_light_time_expansion.py','scripts/compose_moving_trip_geometry.py','scripts/compose_comoving_time_task.py','scripts/compose_limits.py','scripts/compose_material_relative_frame.py'}
    return dict(status='current_clock_and_full_translated_trial_dependency_checked',document=FULL,**results,verified_full_units={'kant-1784':0,'einstein-1905':0},all_spatial_trial_choices_exist_proved=False,general_real_physical_derivation_proved=False,remaining=['u0058の元と候補の地点・時刻を共有した可能選択','平行移動した近傍と局所偏微分、全空間への帰結','注意喚起・著者主張・原刊と一文全体の判断'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
