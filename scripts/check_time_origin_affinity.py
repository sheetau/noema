"""Check same-event zero clocks, full conditional scope and affine pullback."""
from functools import lru_cache
from copy import deepcopy
from fractions import Fraction as Q
from itertools import product
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
from scripts.check_translated_light_trial import expose
from scripts.compose_time_origin_affinity import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,INDEX,MEANINGS,build

DOC='docs/time-origin-affinity-v1.md';PRIOR='data/einstein-transverse-derivative-u0059-review-v1.json'
DEPENDENCIES=('reports/transverse-derivative-claim-v1.json','reports/affine-time-form-v1.json','reports/homogeneity-claim-v1.json','reports/translated-light-trial-v1.json')
RS=dict(kind='function',parameters=['number'],result='truth')
ROLES=('x','y','z','time')
CONSTANTS={'ra':'frame','zbm':'moving','yn':'x','yo':'y','yp':'z','zc7':'time','zb6':'context'}
DOMAIN=(*ROLES,'frame','moving','event','other_event','origin','other_origin','first','second','other_tuple','a','b','other')

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=deepcopy(extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document);boundaries=set(NUM)
    if name in ('ei4g','ei4h','ei4i','ei4k'):boundaries.add('eiyx')
    if name=='ei4j':boundaries.add('ei4g')
    if name=='ei4l':boundaries|={'ei3c','ei4j','ei4k'}
    if name=='ei4n':boundaries|={'eizf','ei3c','smd'}
    abstract(doc,boundaries);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name)
    if mode=='instance':assert len(expose(d,{'forall','exists'}))=={'smd':4}[name]
    slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jtoa'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    expr=dict(kind='call',symbol=name,arguments=args)
    if d['result']!='truth':
        doc['declarations'].append(dict(kind='primitive',name='jtoacapture',parameters=[d['result']],result='truth'));expr=dict(kind='call',symbol='jtoacapture',arguments=[expr])
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,args,m,mode='boundary',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(args)==len(slots),(name,len(args),len(slots))
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|m|{n:lambda x=x:x for n,x in zip(slots,args)}
    return evaluate_document(doc,individuals=domain,situations=('context','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=400000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def relations(m,rows,norm):return m|{n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}

def origin_model():
    cuts,m=numbers();c=cuts.make;coords={'first':[Q(7),Q(2),Q(-3),Q(0)],'second':[Q(0)]*4}
    def coordinate(tup,role):
        if tup not in coords or role not in ROLES:forbidden()
        return c(coords[tup][ROLES.index(role)])
    m|={'zc6':coordinate,'zb7':lambda:c(Q(3)),'zbn':lambda f,ctx:'origin' if (f,ctx)==('moving','context') else forbidden()}
    rows={'zc4':{('event',)},'zbv':{('moving','origin','context')},'cb':{('event','origin','moving')},'eiyx':{('event','first','frame','context'),('event','second','moving','context')}}
    norm=norm_factory(cuts,());return cuts,relations(m,rows,norm),coords,rows,norm

@lru_cache(None)
def binding_checks():
    cuts,m,coords,rows,norm=origin_model();c=cuts.make;args=['event','first','second','context'];count=perturb(lambda mm:run('ei4g',args,mm),m,rows,norm)
    for kt,tau in ((0,0),(3,0),(0,3),(3,7),(-2,-5)):
        coords['first'][3]=Q(kt);coords['second'][3]=Q(tau)
        assert run('ei4g',args,m);assert run('ei4h',args,m)==(tau==0);assert run('ei4i',args,m)==(kt==0 and tau==0);count+=3
    coords['first'][3]=coords['second'][3]=Q(0)
    assert not run('ei4k',args,m);count+=1  # Clock zeros alone do not choose spatial labels.
    coords['first'][:3]=[Q(0)]*3;assert run('ei4k',args,m);count+=1
    for axis in range(3):
        coords['first'][axis]=Q(1);assert not run('ei4k',args,m);coords['first'][axis]=Q(0);count+=1
    assert run('ei4i',args,m|{'shd':forbidden,'sio':forbidden,'smk':forbidden});count+=1
    unknowns(lambda mm:run('ei4k',args,mm),m,('zbn','zc6','zb7','sca','bf','shv'))
    return dict(cases=count,same_origin_event_and_both_current_coordinate_tuples_required=True,zero_tau_and_zero_t_cannot_be_taken_from_different_events=True,clock_condition_does_not_force_all_spatial_values_zero=True,spatial_gauge_separately_bound_to_current_auxiliary_coordinates=True)

@lru_cache(None)
def conditional_scope_checks():
    cuts,m=numbers();c=cuts.make;domain=('a','b');count=0
    sets=[set(),{('a','a','a')},{('a','a','b')},{('b','b','a')},{('a','a','a'),('b','b','a')},{('a','a','a'),('b','a','b')},set(product(domain,repeat=3))]
    for ta,tb in ((0,7),(3,0),(0,0),(3,7)):
        times={'a':Q(ta),'b':Q(tb)}
        for selected in sets:
            def coord(t,role):
                if t not in times or role!='a':forbidden()
                return c(times[t])
            mm=m|{'zc7':lambda:'a','zc6':coord,'ei4g':lambda e,a,b,ctx:(e,a,b) in selected and ctx=='context'}
            expected=any(times[a]==times[b]==0 for e,a,b in selected) and all(times[b]!=0 or times[a]==0 for e,a,b in selected)
            assert run('ei4j',['context'],mm,domain=domain)==expected;count+=1
    mm=m|{'zc7':lambda:'a','zc6':lambda t,role:c(Q(0)) if t in domain and role=='a' else forbidden(),'ei4g':lambda e,a,b,ctx:(e,a,b,ctx)==('a','b','a','context')}
    unknowns(lambda mm:run('ei4j',['context'],mm,domain=domain),mm,('ei4g','zc6','sca'))
    return dict(cases=count,native_three_slot_exists_and_forall_checked_on_two_individuals=True,one_good_zero_event_does_not_hide_another_bad_zero_event=True,nonzero_tau_events_do_not_require_equal_times=True,nonempty_zero_anchor_required=True)

def affine_model(constant=7):
    cuts,m=numbers();c=cuts.make;r=cuts.read
    matrix_values={(a,b):Q((i+1)*(j+2)) for i,a in enumerate(ROLES) for j,b in enumerate(ROLES)}
    matrix_values.update({('time',a):Q(x) for a,x in zip(ROLES,(Q(-3,8),4,-2,Q(25,8)))})
    offsets=dict(zip(ROLES,map(Q,(11,13,17,constant))))
    def entry(a,b):
        if (a,b) not in matrix_values:forbidden()
        return c(matrix_values[a,b])
    def offset(a):
        if a not in offsets:forbidden()
        return c(offsets[a])
    matrix=FunctionValue(('individual','individual'),RS,entry);vec=FunctionValue(('individual',),RS,offset)
    coeff=list(map(Q,(Q(-3,8),4,-2,2,constant)))
    fn=FunctionValue((RS,)*4,RS,lambda x,y,z,t:c(coeff[0]*r(x)+coeff[1]*r(y)+coeff[2]*r(z)+coeff[3]*r(t)+coeff[4]))
    m|={'zb7':lambda:c(Q(3)),'zd4':lambda:fn}
    def norm(xs):
        def one(x):
            if not isinstance(x,FunctionValue):return x
            if x.parameters==('individual','individual'):return tuple(r(x(a,b)) for a in ROLES for b in ROLES)
            if x.parameters==('individual',):return tuple(r(x(a)) for a in ROLES)
            if len(x.parameters)==4:return tuple(r(x(*(c(Q(a)) for a in p))) for p in ((0,0,0,0),(7,2,-3,5)))
            return r(x)
        return tuple(one(x) for x in xs)
    return cuts,m,matrix_values,offsets,matrix,vec,coeff,fn,norm

@lru_cache(None)
def origin_premise_checks():
    cuts,m,mat,off,matrix,vec,coeff,fn,norm=affine_model(0);c=cuts.make;finger=norm((fn,))[0];domain=('a','b')
    rows={'ei3c':{(finger,'context')},'ei4j':{('context',)},'ei4k':{('a','b','a','context')}};m=relations(m,rows,norm)
    count=perturb(lambda mm:run('ei4l',['context'],mm,domain=domain),m,rows,norm)
    shifted=FunctionValue((RS,)*4,RS,lambda *xs:c(cuts.read(fn(*xs))+7))
    mm=m|{'zd4':lambda:shifted,'ei3c':lambda f,ctx:ctx=='context'}
    assert not run('ei4l',['context'],mm,domain=domain);count+=1
    assert run('smg',[fn],m);assert not run('smg',[shifted],m);count+=2
    unknowns(lambda mm:run('ei4l',['context'],mm,domain=domain),m,('zd4','ba','sca'))
    return dict(cases=count,current_global_tau_binding_conditional_clock_rule_and_same_spatial_anchor_required=True,nonzero_additive_constant_rejected_only_by_separate_zero_condition=True)

@lru_cache(None)
def coefficient_checks():
    cuts,m,mat,off,matrix,vec,coeff,fn,norm=affine_model();c=cuts.make;r=cuts.read;args=[matrix,vec,*map(c,coeff)];count=0
    assert run('ei4m',args,m);count+=1
    for i in range(5):
        bad=args.copy();bad[i+2]=c(coeff[i]+1);assert not run('ei4m',bad,m);count+=1
    for role in ROLES:
        old=mat['time',role];mat['time',role]=old+1;assert not run('ei4m',args,m);mat['time',role]=old;count+=1
    off['time']+=1;assert not run('ei4m',args,m);off['time']-=1;count+=1
    mat['x','y']+=1;assert run('ei4m',args,m);mat['x','y']-=1;count+=1
    off['x']+=1;assert run('ei4m',args,m);off['x']-=1;count+=1
    assert not run('ei4m',args,m|{'zb7':lambda:c(Q(2))});count+=1
    unknowns(lambda mm:run('ei4m',args,mm),m,('zb7','ba','bd','shv','sca'))
    # Independently substitute x=xprime+v*t in the source matrix row.
    for x,y,z,t in ((0,0,0,0),(7,2,-3,5),(-4,3,9,-2),(Q(1,2),Q(-2,3),Q(3,4),Q(5,6))):
        values=list(map(Q,(x,y,z,t)));xx,yy,zz,tt=values
        expected=mat['time','x']*(xx+3*tt)+mat['time','y']*yy+mat['time','z']*zz+mat['time','time']*tt+off['time']
        assert run('smc',[*map(c,coeff),*map(c,values)],m|{'jtoacapture':lambda got,expected=expected:r(got)==expected});count+=1
        assert r(fn(*map(c,values)))==expected;count+=1
    return dict(cases=count,same_time_row_and_offset_bound=True,auxiliary_time_coefficient_is_D_plus_vA=True,all_five_coefficients_distinguished=True,nonzero_transverse_coefficients_and_offset_allowed_before_later_constraints=True,exact_rational_pullback_agrees_with_native_affine_expression=True)

@lru_cache(None)
def extension_checks():
    cuts,m,mat,off,matrix,vec,coeff,fn,norm=affine_model();c=cuts.make;args=[fn,matrix,vec,*map(c,coeff)]
    rows={'eizf':{norm((matrix,vec))},'ei3c':{(*norm((fn,)),'context')},'smd':{norm((fn,*map(c,coeff)))}}
    mm=relations(m,rows,norm);count=perturb(lambda mm:run('ei4n',args,mm),mm,rows,norm)
    assert run('ei4n',args,mm|{'sio':forbidden,'shd':forbidden,'sid':forbidden});count+=1
    # The extension is a separately required all-input condition. Test the
    # native body at distinct points, then retain the real-domain refusal.
    for point in ((0,0,0,0),(7,2,-3,5),(-4,3,9,-2)):
        inputs=[fn,*map(c,coeff),*map(c,map(Q,point))]
        assert run('smd',inputs,m,'instance');count+=1
        bad=inputs.copy();bad[5]=c(coeff[4]+1);assert not run('smd',bad,m,'instance');count+=1
    try:run('smd',[fn,*map(c,coeff)],m)
    except ValueError as e:assert 'Cannot finitely quantify' in str(e),str(e)
    else:raise AssertionError('All real inputs replaced with measured samples')
    return dict(cases=count,current_measured_affinity_and_current_tau_binding_both_required=True,same_coefficients_explicitly_extend_to_all_real_inputs=True,all_real_extension_refused=True,finite_fingerprints_not_equality_of_functions=True)

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements']==old.document['statements'] and len(new.document['statements'])==INDEX
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read(PRIOR));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[284,285])==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);assert json.loads(read(ANNOTATIONS))['entries']==json.loads(read('data/transverse-derivative-claim-identifiers-v1.json'))['entries']
    doc=parse(read(CORE))
    for style in ('compact','full'):
        body=format_graph(doc,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    return dict(new_definitions=len(MEANINGS),new_primitives=0,preserved_statements=INDEX,prior_whole_unit_judgment_preserved=True,whole_unit_review_not_yet_claimed=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('binding',binding_checks),('conditional_scope',conditional_scope_checks),('origin_premise',origin_premise_checks),('coefficients',coefficient_checks),('extension',extension_checks),('structure',structure_checks)]}
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|{DOC,PRIOR,*DEPENDENCIES,'scripts/compose_time_origin_affinity.py','scripts/check_time_origin_affinity.py','tests/test_time_origin_affinity.py','scripts/check_coordinate_correspondence.py','scripts/check_moving_trip_geometry.py','scripts/check_material_relative_frame.py','scripts/check_clock_site_time.py','scripts/check_rod_methods.py','scripts/check_translated_light_trial.py','scripts/compose_homogeneous_coordinates.py','scripts/compose_comoving_labels.py','scripts/compose_limits.py','scripts/compose_material_relative_frame.py'}
    return dict(status='current_clock_origin_rule_and_same_affine_extension_checked',document=FULL,**results,verified_full_units={'kant-1784':0,'einstein-1905':0},general_real_affine_derivative_theorem_proved=False,remaining=['同じτの縦横偏微分と未定係数への接続','時刻原点の仮定・簡潔さ・式の帰結・未決定性の帰属','u0062–u0064の原刊と全文の判断'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
