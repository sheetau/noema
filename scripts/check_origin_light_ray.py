"""Check same-origin emission, native full-path construction and time substitution."""
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
from scripts.check_moving_trip_geometry import NUM
from scripts.check_clock_site_time import perturb,unknowns,forbidden
from scripts.check_frame_light_law import model as base_model,RS,DOMAIN as BASE_DOMAIN,CONSTANTS as BASE_CONSTANTS
from scripts.compose_origin_light_ray import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,INDEX,MEANINGS,build

DOC='docs/origin-light-ray-v1.md';PRIOR='data/einstein-affine-time-u0064-review-v1.json'
DEPENDENCIES=('reports/frame-light-law-v1.json','reports/time-origin-affinity-v1.json','reports/affine-time-claim-v1.json','reports/moving-trip-geometry-v1.json','reports/longitudinal-light-v1.json')
CONSTANTS=BASE_CONSTANTS|{'yn':'x','yo':'y','yp':'z'}
DOMAIN=(*BASE_DOMAIN,'x','y','z','axis','movingaxis')

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document;boundaries=NUM|{'sje'}
    if name=='ei46':boundaries.add('ei4k')
    if name=='ei47':boundaries|={'ei44','se'}
    if name=='ei5a':boundaries|={'ei45','ei4l','ei46','ei47','smj'}
    if name=='eitf' and mode!='full':boundaries.add('se')
    abstract(doc,boundaries);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jolr'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    doc['statements']=[dict(kind='ask',body=dict(kind='call',symbol=name,arguments=args))];return doc,slots

def run(name,args,m,mode='boundary'):
    doc,slots=fixture(name,mode);assert len(args)==len(slots)
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|m|{n:lambda x=x:x for n,x in zip(slots,args)}
    return evaluate_document(doc,individuals=DOMAIN,situations=('context','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=400000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def relations(m,rows,norm):return m|{n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}

def model():
    cuts,m,oldrows,oldnorm,records,values=base_model();c=cuts.make;r=cuts.read
    coords={'firsttuple':[Q(0)]*4,'movingfirsttuple':[Q(0)]*4,'lasttuple':list(map(Q,(20,0,0,4))),'movinglasttuple':list(map(Q,(25,0,0,5)))}
    def norm(xs):return tuple(tuple(r(x(c(Q(t)))) for t in (0,1,2,4,5)) if isinstance(x,FunctionValue) and x.parameters==(RS,) else oldnorm((x,))[0] for x in xs)
    m['zc6']=lambda tup,axis:c(coords[tup][('x','y','z','time').index(axis)]) if tup in coords and axis in ('x','y','z','time') else forbidden()
    m['zb7']=lambda:c(Q(3));m['zeq']=lambda:FunctionValue((RS,),RS,lambda speed:c(Q(2)));m['zzbg']=m['bg']
    m['sje']=lambda a,b:c(r(a)/r(b)) if r(b)!=0 else forbidden()
    m['zbo']=lambda frame,axis,ctx:('axis' if frame=='frame' else 'movingaxis') if frame in ('frame','moving') and axis=='x' and ctx=='context' else forbidden()
    rows={'ei4k':{('start','firsttuple','movingfirsttuple','context')},'ei45':{('s','t','context')},'ei4l':{('context',)},'ei46':{('start','firsttuple','movingfirsttuple','context')},'ei47':{('s','frame','context'),('t','moving','context')},'ei44':oldrows['ei44']}
    rows['smj']={norm((m['zd4'](),m['zeq'](),c(Q(5)),c(Q(3))))}
    fn=lambda speed:FunctionValue((RS,),RS,lambda time:c(Q(speed)*r(time)))
    for seg,frame,duration,path,axis in (('s','frame',4,20,'axis'),('t','moving',5,25,'movingaxis')):
        records[seg]['wh']='start'
        rows.setdefault('zbw',set()).add((frame,axis,'x','context'));rows.setdefault('zdw',set()).add(('ray','start','end',axis,frame,'context'))
        history=['ray',frame,'context','lengthunit','timeunit',c(Q(0)),c(Q(duration)),fn(5),fn(0),fn(0)]
        rows.setdefault('se',set()).add(norm(history))
        for e,t,x in (('start',0,0),('end',duration,path)):
            rows.setdefault('zzbu',set()).add((e,frame,'context','lengthunit','timeunit',Q(t),Q(x),Q(0),Q(0)))
            rows.setdefault('zzbv',set()).add(('ray',e,'context'))
    return cuts,relations(m,rows,norm),rows,norm,records,coords

@lru_cache(None)
def origin_checks():
    cuts,m,rows,norm,records,coords=model();args=['start','firsttuple','movingfirsttuple','context'];count=perturb(lambda mm:run('ei46',args,mm),m,{'ei4k':rows['ei4k']},norm)
    for i in range(3):
        coords['movingfirsttuple'][i]=Q(1);assert not run('ei46',args,m);coords['movingfirsttuple'][i]=Q(0);count+=1
    unknowns(lambda mm:run('ei46',args,mm),m,('zc6','sca'))
    return dict(cases=count,same_previous_zero_time_event_and_two_current_tuples_required=True,moving_spatial_labels_zero_are_separate_from_clock_convention=True)

@lru_cache(None)
def path_checks():
    cuts,m,rows,norm,records,coords=model();c=cuts.make;count=0
    for seg,frame,tup in (('s','frame','lasttuple'),('t','moving','movinglasttuple')):
        selected={n:{row for row in rows[n] if frame in row or n=='zzbv'} for n in ('ei44','zbw','zdw','se','zzbu','zzbv')}
        count+=perturb(lambda mm:run('ei47',[seg,frame,'context'],mm),m,selected,norm)
        for i in range(4):
            coords[tup][i]+=1;assert not run('ei47',[seg,frame,'context'],m);coords[tup][i]-=1;count+=1
        first='firsttuple' if frame=='frame' else 'movingfirsttuple'
        for i in range(4):
            coords[first][i]=Q(1);assert not run('ei47',[seg,frame,'context'],m);coords[first][i]=Q(0);count+=1
        for field,value in (('wh','emission'),('wj','start')):
            old=records[seg][field];records[seg][field]=value;assert not run('ei47',[seg,frame,'context'],m);records[seg][field]=old;count+=1
        old=records[seg]['wq'];records[seg]['wq']=old+1;assert not run('ei47',[seg,frame,'context'],m);records[seg]['wq']=old;count+=1
        unknowns(lambda mm:run('ei47',[seg,frame,'context'],mm),m,('se','zzbu','zzbv','zdz','zc6','zbo','wh','tc'))
    return dict(cases=count,native_eitf_and_sb_bind_both_complete_paths_and_same_end_events=True,both_frame_origin_times_and_all_three_coordinates_checked=True,actual_emission_must_be_departure_not_an_earlier_event=True,positive_longitudinal_arc_length_not_arbitrary_endpoint_distance=True)

@lru_cache(None)
def trace_checks():
    cuts,m,rows,norm,records,coords=model();c=cuts.make;r=cuts.read;count=0
    for frame,upper in (('frame',4),('moving',5)):
        args=['ray',frame,'context','lengthunit','timeunit',c(Q(0)),c(Q(upper)),*map(c,map(Q,(0,0,0,5,0,0)))]
        assert run('eitf',args,m);count+=1
        for i in range(len(args)):
            bad=args.copy();bad[i]=c(r(bad[i])+1) if isinstance(bad[i],FunctionValue) else 'other'
            assert not run('eitf',bad,m);count+=1
        # A competing curve has the same endpoints but differs inside. The
        # finite fingerprint distinguishes this supplied curve, not all histories.
        curve=FunctionValue((RS,),RS,lambda t:c(5*r(t)+r(t)*(upper-r(t))))
        zero=FunctionValue((RS,),RS,lambda t:c(Q(0)));bad_history=norm(args[:7]+[curve,zero,zero])
        assert not run('eitf',args,m|{'se':lambda *xs:norm(xs)==bad_history});count+=1
        try:run('eitf',args,m,'full')
        except ValueError as e:assert 'Cannot finitely quantify' in str(e),str(e)
        else:raise AssertionError('Whole real time trajectory replaced by finite samples')
    return dict(cases=count,native_linear_functions_all_three_axes_and_intervals_checked=True,same_endpoint_curved_history_not_accepted_as_linear=True,full_real_history_refused=True,finite_function_fingerprints_not_full_function_equality=True)

@lru_cache(None)
def connection_checks():
    cuts,m,rows,norm,records,coords=model();c=cuts.make;count=perturb(lambda mm:run('ei5a',['s','t','context'],mm),m,{n:rows[n] for n in ('ei45','ei4l','ei46','ei47','smj')},norm)
    for tup,i in (('firsttuple',3),('movingfirsttuple',3),('lasttuple',0),('lasttuple',3),('movinglasttuple',3)):
        coords[tup][i]+=1;assert not run('ei5a',['s','t','context'],m);coords[tup][i]-=1;count+=1
    unknowns(lambda mm:run('ei5a',['s','t','context'],mm),m,('zd4','zeq','tc','zb7','zdz','zc6'))
    assert run('ei5a',['s','t','context'],m|{'smk':forbidden,'shd':forbidden,'sio':forbidden,'snk':forbidden});count+=1
    return dict(cases=count,current_global_pair_origin_both_paths_and_same_tau_phi_bound=True,native_tau_application_to_both_endpoints_checked=True,legacy_incomplete_coordinate_bindings_not_used=True)

@lru_cache(None)
def substitution_checks():
    cuts,m,rows,norm,records,coords=model();c=cuts.make;count=0
    for event in ('start','end'):
        assert run('snf',[event,'context'],m);assert run('sng',[event,'context'],m);assert run('snh',[event,'context'],m);count+=3
    # Same light ray: a=2, V=5, v=3, x'=20-3*4=8, tau=5, xi=25.
    for tup,slot,expected in (('movinglasttuple',0,(True,False,False)),('movinglasttuple',3,(False,False,True)),('lasttuple',0,(False,True,False)),('lasttuple',3,(False,True,False))):
        coords[tup][slot]+=1;actual=tuple(run(n,['end','context'],m) for n in ('snf','sng','snh'));assert actual==expected,(tup,slot,actual);coords[tup][slot]-=1;count+=3
    for scale in (Q(1),Q(3),Q(-2)):
        phi=FunctionValue((RS,),RS,lambda speed,scale=scale:c(scale));assert not run('snh',['end','context'],m|{'zeq':lambda:phi});count+=1
    assert not run('sng',['end','context'],m|{'tc':lambda:c(Q(2))});count+=1
    unknowns(lambda mm:run('snh',['end','context'],mm),m,('zeq','zb7','tc','sje','zdz','zc6'))
    return dict(cases=count,native_xi_Vtau_and_same_tau_substitution_checked=True,K_time_moving_time_xprime_and_xi_distinguished=True,changing_only_phi_breaks_the_selected_formula=True,no_general_off_ray_coordinate_transformation_claimed=True)

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements']==old.document['statements'] and len(new.document['statements'])==INDEX
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read(PRIOR));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[286,287,288])==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS)
    doc=parse(read(CORE))
    for style in ('compact','full'):
        body=format_graph(doc,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    return dict(new_definitions=len(MEANINGS),new_primitives=0,preserved_statements=INDEX,prior_whole_unit_judgment_preserved=True,whole_unit_review_not_yet_claimed=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('origin',origin_checks),('paths',path_checks),('traces',trace_checks),('connection',connection_checks),('substitution',substitution_checks),('structure',structure_checks)]}
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|{DOC,PRIOR,*DEPENDENCIES,'scripts/compose_origin_light_ray.py','scripts/check_origin_light_ray.py','tests/test_origin_light_ray.py','scripts/check_frame_light_law.py','scripts/check_coordinate_correspondence.py','scripts/check_moving_trip_geometry.py','scripts/check_material_relative_frame.py','scripts/check_clock_site_time.py','scripts/check_rod_methods.py','scripts/compose_limits.py','scripts/compose_material_relative_frame.py'}
    return dict(status='same_origin_and_full_positive_light_paths_connected',document=FULL,**results,verified_full_units={'kant-1784':0,'einstein-1905':0},general_real_physical_derivation_proved=False,remaining=['二原理からの帰属と空間座標を容易に求める評価','u0065–u0068の二式の帰結・書換えの本文接続と全文判断'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
