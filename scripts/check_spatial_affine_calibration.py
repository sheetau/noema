"""Check same affine rows, actual calibration times and moving-origin bindings."""
from functools import lru_cache
from fractions import Fraction as Q
import json
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import FunctionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.polynomial_proofs import verify_universal
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_clock_site_time import perturb,unknowns,forbidden
from scripts.check_translated_light_trial import expose
from scripts.check_transverse_ray_claim import model as transverse_model,RS,CONSTANTS as BASE_CONSTANTS
from scripts.check_moving_trip_geometry import NUM
from scripts.check_real_products import MEANINGS as POLY,call as pk,op as po,assertion
from scripts.compose_spatial_affine_calibration import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,INDEX,MEANINGS,build

DOC='docs/spatial-affine-calibration-v1.md';PRIOR='data/einstein-transverse-ray-u0073-review-v1.json'
DEPENDENCIES=('reports/transverse-ray-claim-v1.json','reports/longitudinal-elimination-v1.json','reports/time-origin-affinity-v1.json','reports/homogeneity-claim-v1.json','reports/event-coordinate-task-v1.json','reports/four-coordinates-v1.json')
CONSTANTS=BASE_CONSTANTS|{'zez':'rx','zey':'mx'}
ROLES=('x','y','z','time');PROBES=((0,0,0,0),(1,0,0,0),(0,1,0,0),(0,0,1,0),(0,0,0,1),(7,2,-3,5))
DOMAIN=tuple(dict.fromkeys((*CONSTANTS.values(),'a','b','origin','x0','x1','o1','y0','y1','z0','z1','rayx','rayy','rayz','my','mz','axisy','axisz',*(f+'_'+e for f in ('K','k') for e in ('x0','x1','o1','y0','y1','z0','z1')),'other')))

@lru_cache(None)
def core_document():return parse(read(CORE))

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=extract_document(core_document(),roots=[name],statement_indices=[]).document;boundaries=NUM|{'sje','sky'}
    if name in ('ei6y','ei6z'):boundaries|={'smd','eizf','eiyy'}
    if name=='ei62':boundaries.add('eiyx')
    if name=='ei63':boundaries|={'eivx','eizm','ei46','eiyx','se'}
    if name=='ei65':boundaries|={'eizf','ei5y','ei6e','ei63','ei6z','eiyx'}|(set() if mode=='integrated' else {'ei62','ei64'})
    if name=='ei66':boundaries.add('ei65')
    abstract(doc,boundaries);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name)
    if mode=='instance':assert len(expose(d,{'forall','exists'}))=={'smd':4,'ei6z':2,'ei66':3}[name]
    slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jsac'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    expr=dict(kind='call',symbol=name,arguments=args)
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jsacpoint',parameters=[],result='situation'));expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='jsacpoint',arguments=[]))
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,args,m,mode='boundary',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(args)==len(slots),(name,len(args),len(slots))
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|m|{n:lambda x=x:x for n,x in zip(slots,args)};mm.setdefault('jsacpoint',lambda:'context')
    return evaluate_document(doc,individuals=domain,situations=('context','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=700000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def model():
    cuts,m,oldrows,oldnorm,records,coords=transverse_model();c=cuts.make;r=cuts.read
    mat={(a,b):Q(0) for a in ROLES for b in ROLES};mat.update({('x','x'):Q(25,8),('x','time'):Q(-75,8),('y','y'):Q(5,2),('z','z'):Q(5,2),('time','x'):Q(-3,8),('time','time'):Q(25,8)})
    off={a:Q(0) for a in ROLES}
    matrix=FunctionValue(('individual','individual'),RS,lambda a,b:c(mat[a,b]) if (a,b) in mat else forbidden())
    offset=FunctionValue(('individual',),RS,lambda a:c(off[a]) if a in off else forbidden())
    def affine(coeff):
        coeff=tuple(map(Q,coeff));return FunctionValue((RS,)*4,RS,lambda *xs:c(sum(a*r(x) for a,x in zip(coeff,xs))+coeff[4]))
    functions={a:affine([mat[a,b] for b in ROLES]+[off[a]]) for a in ROLES}
    def norm(xs):
        def one(x):
            if not isinstance(x,FunctionValue):return x
            if x.parameters==('individual','individual'):return tuple(r(x(a,b)) for a in ROLES for b in ROLES)
            if x.parameters==('individual',):return tuple(r(x(a)) for a in ROLES)
            if x.parameters==(RS,)*4:return tuple(r(x(*(c(Q(a)) for a in p))) for p in PROBES)
            return oldnorm((x,))[0]
        return tuple(one(x) for x in xs)
    rows={}
    def add(n,*xs):rows.setdefault(n,set()).add(norm(xs))
    coords.update({'K_x0':[Q(0)]*4,'k_x0':[Q(0)]*4,'K_x1':list(map(Q,(20,0,0,4))),'k_x1':list(map(Q,(25,0,0,5))),'K_o1':[Q(9,2),Q(0),Q(0),Q(3,2)],'k_o1':[Q(0),Q(0),Q(0),Q(3)]})
    records['rx']=dict(wf='rayx',wi='x0',wj='x1',wh='x0',wq=Q(20));records['mx']=dict(wf='rayx',wi='x0',wj='x1',wh='x0',wq=Q(25))
    # The inherited coordinate accessors close over these same mutable mappings.
    events=('x0','o1','x1','y1','z1')
    for e in events:
        add('zc4',e)
        for f in ('K','k'):add('eiyx',e,f+'_'+e,f,'context')
        add('eiyy','K_'+e,'k_'+e)
    add('eizf',matrix,offset)
    for a in ('x','y','z'):
        coeff=[c(mat[a,b]) for b in ROLES]+[c(off[a])]
        add('smd',functions[a],*coeff);add('ei6z',functions[a],a,matrix,offset)
        for e in events:add('ei62',functions[a],a,e,'context')
        add('ei64',functions[a],a,c(Q(5)),c(Q(3)),c(Q(2)),c(Q(3,2)),c(Q(4)),c(Q(2)),c(Q(3)))
    add('ei5y','rx','mx','context');add('ei6e','y','context');add('ei6e','z','context');add('ei63','x0','o1','context');add('ei65',matrix,offset,'o1')
    add('eivx','context');add('zbv','k','origin','context');add('eizm','origin','context');add('ei46','x0','K_x0','k_x0','context');add('cb','o1','origin','k')
    linear=lambda speed:FunctionValue((RS,),RS,lambda t:c(Q(speed)*r(t)))
    tracks={'x':linear(3),'y':linear(0),'z':linear(0)}
    add('se','origin','K','context','length','timeunit',c(Q(0)),c(Q(3,2)),tracks['x'],tracks['y'],tracks['z'])
    for e,t,x in (('x0',Q(0),Q(0)),('o1',Q(3,2),Q(9,2))):
        add('zzbu',e,'K','context','length','timeunit',c(t),c(x),c(Q(0)),c(Q(0)));add('zzbv','origin',e,'context')
    m|={'zfh':lambda a:functions[a] if a in functions else forbidden(),'zbn':lambda f,ctx:'origin' if (f,ctx)==('k','context') else forbidden(),'eismh':lambda obj,f,lu,tu,a,ctx:tracks[a] if (obj,f,lu,tu,ctx)==('origin','K','length','timeunit','context') and a in tracks else forbidden(),'eisls':lambda f,tu,ctx:c(Q(-1)) if (f,tu,ctx)==('K','timeunit','context') else forbidden(),'eislt':lambda f,tu,ctx:c(Q(8)) if (f,tu,ctx)==('K','timeunit','context') else forbidden()}
    m|={n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}
    return cuts,m,rows,norm,records,coords,mat,off,matrix,offset,functions,affine,tracks

@lru_cache(None)
def row_checks():
    cuts,m,rows,norm,records,coords,mat,off,matrix,offset,functions,affine,tracks=model();c=cuts.make;count=0
    for role in ('x','y','z'):
        fn=functions[role];args=[fn,role,matrix,offset];coeff=[mat[role,b] for b in ROLES]+[off[role]]
        count+=perturb(lambda mm:run('ei6y',args,mm),m,{'smd':{norm((fn,*map(c,coeff)))}},norm)
        for b in ROLES:
            mat[role,b]+=1;assert not run('ei6y',args,m);mat[role,b]-=1;count+=1
        off[role]+=1;assert not run('ei6y',args,m);off[role]-=1;count+=1
        other='z' if role!='z' else 'x';mat[other,'x']+=1;assert run('ei6y',args,m);mat[other,'x']-=1;count+=1
        for point in PROBES:
            inputs=[fn,*map(c,coeff),*map(c,map(Q,point))]
            assert run('smd',inputs,m,'instance');count+=1
            bad=inputs.copy();bad[5]=c(Q(1));assert not run('smd',bad,m,'instance');count+=1
        try:run('smd',[fn,*map(c,coeff)],m)
        except ValueError as e:assert 'Cannot finitely quantify' in str(e),str(e)
        else:raise AssertionError('All real affine domain replaced by samples')
        unknowns(lambda mm:run('ei6y',args,mm),m,('smd','ba'))
    assert not run('ei6y',[functions['time'],'time',matrix,offset],m);count+=1
    return dict(cases=count,same_spatial_matrix_row_and_offset_checked=True,native_smd_at_distinguishing_points_checked=True,full_real_affine_extension_refused=True)

@lru_cache(None)
def correspondence_checks():
    cuts,m,rows,norm,records,coords,mat,off,matrix,offset,functions,affine,tracks=model();c=cuts.make;count=0
    # Expose both native universal slots: the eager finite interpreter would
    # otherwise evaluate coordinate accessors even for non-record individuals.
    # Every pair of the ten explicitly supplied records is checked below.
    domain=tuple(f+'_'+e for f in ('K','k') for e in ('x0','o1','x1','y1','z1'))
    for role in ('x','y','z'):
        fn=functions[role];args=[fn,role,matrix,offset]
        selected={'eizf':rows['eizf'],'smd':{norm((fn,*(c(mat[role,b]) for b in ROLES),c(off[role])))}}
        check=lambda mm,a='K_x1',b='k_x1':run('ei6z',args+[a,b],mm,'instance')
        count+=perturb(check,m,selected,norm)
        for a in domain:
            for b in domain:assert check(m,a,b);count+=1
        for badpair in (('K_x1','k_y1'),('K_y1','k_x1')):
            mm=m|{'eiyy':lambda a,b:(a,b) in rows['eiyy']|{badpair}}
            a,b=badpair;expected=cuts.read(fn(*(c(x) for x in coords[a])))==coords[b][ROLES.index(role)]
            assert check(mm,a,b)==expected;count+=1
        for e in ('x0','o1','x1','y1','z1'):
            pointargs=[fn,role,e,'context'];selected={'zc4':{(e,)},'eiyx':{(e,f+'_'+e,f,'context') for f in ('K','k')}}
            count+=perturb(lambda mm:run('ei62',pointargs,mm),m,selected,norm)
            slot=ROLES.index(role);coords['k_'+e][slot]+=1;assert not run('ei62',pointargs,m);coords['k_'+e][slot]-=1;count+=1
        unknowns(lambda mm:run('ei62',[fn,role,'x1','context'],mm),m,('zdz','zc6','eiyx'))
    # An additional current pair cannot be silently ignored in the whole scope.
    coords['k_y1'][2]+=1
    assert not run('ei6z',[functions['z'],'z',matrix,offset,'K_y1','k_y1'],m,'instance');count+=1
    coords['k_y1'][2]-=1
    return dict(cases=count,all_current_record_pairs_bound_to_same_row=True,actual_ray_and_origin_events_bound_to_both_current_tuples=True,extra_bad_correspondence_rejected=True)

@lru_cache(None)
def origin_checks():
    cuts,m,rows,norm,records,coords,mat,off,matrix,offset,functions,affine,tracks=model();c=cuts.make;r=cuts.read;args=['x0','o1','context']
    selected={n:rows[n] for n in ('eivx','zbv','eizm','ei46','cb','se','zzbu','zzbv')}
    selected|={'zc4':{('o1',)},'eiyx':{('o1','K_o1','K','context'),('o1','k_o1','k','context')}}
    count=perturb(lambda mm:run('ei63',args,mm),m,selected,norm)
    for tup in ('K_o1','k_o1'):
        for slot in range(4 if tup=='K_o1' else 3):
            coords[tup][slot]+=1;assert not run('ei63',args,m);coords[tup][slot]-=1;count+=1
    # k time is not equated to K time; its current measurement remains a boundary.
    coords['k_o1'][3]+=1;assert run('ei63',args,m);coords['k_o1'][3]-=1;count+=1
    for name,time in (('eisls',1),('eislt',1)):
        assert not run('ei63',args,m|{name:lambda *xs,time=time:c(Q(time))});count+=1
    for a in ('x','y','z'):
        old=tracks[a];tracks[a]=FunctionValue((RS,),RS,lambda t,old=old:c(r(old(t))+1))
        assert not run('ei63',args,m);tracks[a]=old;count+=1
    unknowns(lambda mm:run('ei63',args,mm),m,('zbn','eismh','eisls','eislt','eiyx','se','zzbu','zzbv'))
    return dict(cases=count,same_origin_full_motion_current_measurements_and_actual_positive_time_required=True,origin_not_a_light_arrival_or_fixed_unit_time=True,moving_clock_time_not_equal_to_rest_time_by_fiat=True)

@lru_cache(None)
def calibration_checks():
    cuts,m,rows,norm,records,coords,mat,off,matrix,offset,functions,affine,tracks=model();c=cuts.make;r=cuts.read;count=0
    timesets=((Q(3,2),Q(4),Q(2),Q(3)),(Q(1,3),Q(7,2),Q(5),Q(2,3)),(Q(2),Q(2),Q(2),Q(2)))
    for ts in timesets:
        for role in ('x','y','z'):
            args=[functions[role],role,*map(c,map(Q,(5,3,2,*ts)))]
            assert run('ei64',args,m);count+=1
            for i in range(5,9):
                for value in (0,-1):
                    bad=args.copy();bad[i]=c(Q(value));assert not run('ei64',bad,m);count+=1
            for value in (Q(1),Q(3)):
                bad=args.copy();bad[4]=c(value);assert not run('ei64',bad,m);count+=1
            assert not run('ei64',[functions['time'],'time',*args[2:]],m);count+=1
    args=[functions['x'],'x',*map(c,map(Q,(5,3,2,*timesets[0])))]
    # An affine perturbation vanishes on all three complete light lines and at
    # zero, but not on the moving origin. It must fail the origin constraint.
    ambiguous=affine((Q(25,8)+4,2,2,Q(-75,8)-20,0))
    assert not run('ei64',[ambiguous,*args[1:]],m);count+=1
    for p in ((20,0,0,4),(6,8,0,2),(9,0,12,3),(0,0,0,0)):
        assert r(ambiguous(*map(c,map(Q,p))))==r(functions['x'](*map(c,map(Q,p))));count+=1
    # A nonlinear perturbation can agree at all five chosen points. The
    # separate native all-input affine condition detects it at another point.
    times=timesets[0];fn=functions['x'];roots=(Q(0),3*times[0],5*times[1],3*times[2],3*times[3])
    def curved(x,y,z,t):
        extra=Q(1)
        for root in roots:extra*=r(x)-root
        return c(r(fn(x,y,z,t))+extra)
    curve=FunctionValue((RS,)*4,RS,curved)
    assert run('ei64',[curve,*args[1:]],m);count+=1
    coeff=[c(mat['x',b]) for b in ROLES]+[c(off['x'])]
    assert not run('smd',[curve,*coeff,*map(c,map(Q,(1,2,3,4)))],m,'instance');count+=1
    unknowns(lambda mm:run('ei64',args,mm),m,('sky','sje','ba','sca'))
    return dict(cases=count,independent_positive_times_not_fixed_to_one=True,same_coefficient_on_all_three_rays=True,moving_origin_constraint_excludes_affine_ambiguity=True,five_points_alone_do_not_imply_affinity=True)

@lru_cache(None)
def polynomial_checks():
    # Universal rational calibration with independent actual durations. It does
    # not quantify over real-cut functions or prove the physical premises.
    names='light speed component cx cy cz ct offset lx ly lz invlong invtrans originspan xspan yspan zspan x y z time'
    V,vv,w,cx,cy,cz,ct,o,lx,ly,lz,il,it,to,tx,ty,tz,x,y,z,t=['v '+n for n in names.split()]
    zero='n p a b';one='n p b b';mul=lambda a,b:pk('ad',a,b);add=lambda a,b:pk('ab',a,b);sub=lambda a,b:add(a,pk('ac',b))
    row=lambda xx,yy,zz,tt:pk('sld',cx,cy,cz,ct,o,xx,yy,zz,tt)
    conditions=[pk('sla',V,vv,w),*(pk('aa',zero,a) for a in (to,tx,ty,tz)),pk('sja',one,sub(V,vv),il),pk('sja',one,w,it),po('e',row(zero,zero,zero,zero),zero),po('e',row(mul(vv,to),zero,zero,to),zero),po('e',row(mul(V,tx),zero,zero,tx),mul(lx,tx)),po('e',row(mul(vv,ty),mul(w,ty),zero,ty),mul(ly,ty)),po('e',row(mul(vv,tz),zero,mul(w,tz),tz),mul(lz,tz))]
    conjunction=lambda xs:xs[0] if len(xs)==1 else po('w',xs[0],conjunction(xs[1:]))
    expected=pk('sox',vv,lx,ly,lz,il,it,x,y,z,t)
    claim=assertion(names,po('y',conjunction(conditions),po('e',row(x,y,z,t),expected)))
    base=parse(read('examples/v014/four-coordinates.noema'));base['statements']=[]
    result=verify_universal(parse(format_graph(base,'compact')+claim),POLY,timeout_ms=15000)[0]
    assert result['status']=='valid',result
    return dict(actual_positive_durations_affine_row_uniqueness=result,rational_polynomial_lemma_only=True,general_real_cut_theorem_proved=False)

@lru_cache(None)
def connection_checks():
    cuts,m,rows,norm,records,coords,mat,off,matrix,offset,functions,affine,tracks=model();c=cuts.make;args=[matrix,offset,'o1']
    selected={n:rows[n] for n in ('eizf','ei5y','ei6e','ei63','ei6z','ei62','ei64')}
    count=perturb(lambda mm:run('ei65',args,mm),m,selected,norm)
    assert run('ei65',args,m,'integrated');count+=1
    for e in ('o1','x1','y1','z1'):
        coords['K_'+e][3]+=1;assert not run('ei65',args,m);coords['K_'+e][3]-=1;count+=1
    for role in ('x','y','z'):
        wrong='y' if role=='x' else 'x';assert not run('ei65',args,m|{'zfh':lambda a,role=role,wrong=wrong:functions[wrong if a==role else a]});count+=1
    m2=m|{'zfb':lambda a:'my','zfa':lambda a:'ry'}
    assert not run('ei65',args,m2);count+=1
    unknowns(lambda mm:run('ei65',args,mm),m,('zfh','zdz','zc6','zeq','tc','zb7','ei63','ei6z','ei62','ei64'))
    # All three existence witnesses have to be bound to the same detailed body.
    assert run('ei66',args,m,'instance');count+=1
    for i in range(3):
        bad=args.copy()
        if i==0:bad[i]=FunctionValue(('individual','individual'),RS,lambda a,b:c(mat[a,b]+1))
        elif i==1:bad[i]=FunctionValue(('individual',),RS,lambda a:c(off[a]+1))
        else:bad[i]='x1'
        assert not run('ei66',bad,m,'instance');count+=1
    try:run('ei66',[],m)
    except ValueError as e:assert 'Cannot finitely quantify' in str(e),str(e)
    else:raise AssertionError('Full affine function witnesses silently sampled')
    return dict(cases=count,same_matrix_offset_origin_and_all_three_rays_bound=True,native_five_event_measurements_and_calibration_join_passed=True,full_function_existence_refused=True)

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements']==old.document['statements'] and len(new.document['statements'])==INDEX
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read(PRIOR));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[295,296,297,298,299])==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=core_document()
    for n in MEANINGS:
        selected=extract_document(doc,roots=[n],statement_indices=[])
        assert not set(selected.retained_symbols)&{'spo','spi','spn','shi','sio','shf','shg','she','shd'},n
    for style in ('compact','full'):
        body=format_graph(doc,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    return dict(new_definitions=len(MEANINGS),new_primitives=0,preserved_statements=INDEX,prior_whole_unit_judgment_preserved=True,whole_unit_review_not_yet_claimed=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('rows',row_checks),('correspondence',correspondence_checks),('origin',origin_checks),('calibration',calibration_checks),('polynomial',polynomial_checks),('connections',connection_checks),('structure',structure_checks)]}
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|{DOC,PRIOR,*DEPENDENCIES,'scripts/compose_spatial_affine_calibration.py','scripts/check_spatial_affine_calibration.py','tests/test_spatial_affine_calibration.py','scripts/check_transverse_ray_claim.py','scripts/check_coordinate_correspondence.py','scripts/check_moving_trip_geometry.py','scripts/check_material_relative_frame.py','scripts/check_clock_site_time.py','scripts/check_rod_methods.py','scripts/check_translated_light_trial.py','scripts/check_real_products.py','examples/v014/four-coordinates.noema','noema/polynomial_proofs.py','scripts/compose_homogeneous_coordinates.py','scripts/compose_comoving_labels.py','scripts/compose_material_axes.py','scripts/compose_limits.py','scripts/compose_material_relative_frame.py'}
    return dict(status='same_current_affine_rows_calibrated_by_actual_origin_and_ray_times',document=FULL,**results,verified_full_units={'kant-1784':0,'einstein-1905':0},general_real_physical_derivation_proved=False,remaining=['現在の全座標範囲で先行四式と正規化後四式を結ぶ','x′置換・φ=aβ再表示・βの著者提示とu0081–u0084全文判断','u0085以降と二作品全体の目標'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
