"""Check relative positions, native intersections and complete-path bindings."""
from copy import deepcopy
from fractions import Fraction as Q
from functools import lru_cache
import json,re
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import FunctionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_material_relative_frame import arithmetic,RS,FS
from scripts.check_rod_geometry import instantiate
from scripts.check_rod_methods import value
from scripts.compose_moving_trip_geometry import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,MEANINGS,PRIMITIVES,build

DOC='docs/moving-trip-geometry-v1.md';SOURCE='data/einstein-moving-trip-geometry-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json'
PRIOR='data/einstein-carried-clock-synchrony-review-v1.json'
NUM={'ba','bb','bc','bd','bf','bg','shv','sah','sca','zzba','zzbc','zzbg'}
DOMAIN=('firstend','lastend','ray','depart','reflection','arrival','frame','lengthunit','timeunit','carrieda','carriedb','observera','observerb','rod','recorda','recordb','recordc','placea','placeb','placec','locala','localb','localc','trial','x','y','z','other')
POINTS=('context','other')

def forbidden(*xs):raise ValueError('Unknown moving-trip-geometry input')

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=extract_document(parse(read(FULL if name=='sdb' else CORE)),roots=[name],statement_indices=[]).document
    boundaries=NUM|{'se','eiq2','eiq4','eiqz','eipk'}
    if name!='eite':boundaries.add('eite')
    if mode!='native':abstract(doc,boundaries)
    if name=='eite' and mode=='instance':instantiate(next(d for d in doc['declarations'] if d['name']==name))
    doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jmtg'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    doc['statements']=[dict(kind='ask',body=dict(kind='call',symbol=name,arguments=args))]
    return doc,slots

def run(name,args,m,mode='boundary'):
    doc,slots=fixture(name,mode);assert len(args)==len(slots),(name,len(args),len(slots))
    mm=m|{n:(lambda x=x:x) for n,x in zip(slots,args)}
    return evaluate_document(doc,individuals=DOMAIN,situations=POINTS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=300000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def numbers():
    cuts,m=arithmetic();c=cuts.make;r=cuts.read
    m|={'bg':lambda a,b:r(a)<r(b),'sah':lambda a,b:c(r(a)*r(b))}
    return cuts,m

def unknowns(check,m,names):
    for n in names:
        try:check(m|{n:forbidden})
        except ValueError as e:assert 'Unknown moving-trip-geometry' in str(e),str(e)
        else:raise AssertionError(('Unknown input accepted',n))

def norm_factory(cuts,times):
    def norm(xs):
        def one(x):
            if not isinstance(x,FunctionValue):return value(x)
            if x.parameters==('number',):return cuts.read(x)
            if x.result==RS:return tuple(cuts.read(x(cuts.make(Q(t)))) for t in times)
            forbidden()
        return tuple(one(x) for x in xs)
    return norm

def perturb(check,m,rows,norm):
    count=1;assert check(m)
    for n,rs in rows.items():
        for row in rs:
            assert not check(m|{n:lambda *xs,rs=rs-{row}:norm(xs) in rs}),(n,row);count+=1
            for i in range(len(row)):
                bad=tuple('other' if j==i else x for j,x in enumerate(row))
                assert not check(m|{n:lambda *xs,rs=(rs-{row})|{bad}:norm(xs) in rs}),(n,i);count+=1
    unknowns(check,m,rows);return count

@lru_cache(None)
def numeric_checks():
    cuts,m=numbers();c=cuts.make;count=0
    # Compare independently expressed intersections and elapsed-time equations.
    for origin in (-9,0,Q(5,2)):
        for length,light,speed,start in ((6,3,1,7),(4,5,0,-2),(Q(3,2),Q(7,2),Q(1,2),Q(1,3))):
            middle=Q(start)+Q(length)/(Q(light)-speed);last=middle+Q(length)/(Q(light)+speed)
            base=list(map(Q,(origin,length,light,speed,start,middle,last)))
            for slot in range(7):
                for delta in (0,Q(1,4)):
                    xs=list(base);xs[slot]+=delta
                    expected=(xs[1]>0 and 0<=xs[3]<xs[2] and xs[4]<xs[5]<xs[6] and (xs[2]-xs[3])*(xs[5]-xs[4])==xs[1] and (xs[2]+xs[3])*(xs[6]-xs[5])==xs[1])
                    assert run('eith',list(map(c,xs)),m)==expected;count+=1
                    assert run('sdb',list(map(c,xs[1:])),m)==expected;count+=1
    for xs in ((5,0,3,1,7,7,7),(5,6,3,3,7,10,12),(5,6,3,-1,7,10,12),(5,6,-3,1,7,10,12),(5,6,3,1,10,7,12),(5,6,3,1,7,10,9)):
        assert not run('eith',list(map(c,map(Q,xs))),m);count+=1
    good=list(map(c,map(Q,(5,6,3,1,7,10,Q(23,2)))))
    unknowns(lambda mm:run('eith',good,mm),m,('ba','bg','bc','bf','bd','shv','sca'))
    bad=list(good);bad[0]=FunctionValue(('number',),'truth',lambda x:x<5)
    try:run('eith',bad,m)
    except ValueError:pass
    else:raise AssertionError('Unknown cut decoded by sampling')
    return dict(cases=count,arbitrary_origin_and_initial_time=True,zero_speed_comparison_allowed_but_not_superluminal=True,two_intersections_match_existing_elapsed_equations_on_exact_rationals=True,unknown_cut_refused=True)

@lru_cache(None)
def comotion_checks():
    cuts,m=numbers();c=cuts.make;r=cuts.read;count=0
    def traces(profile):
        def xyz(side,a,t):
            base=(t*t,2*t,-t)[a]
            if side=='reference':return base
            offset=(2,3,4)[a]
            if profile=='drift':offset+=t if a==2 else 0
            if profile=='excursion':offset+=t*(2-t) if a==0 else 0
            if profile=='orbit':offset=((1-t*t)/(1+t*t),2*t/(1+t*t),0)[a]
            return base+offset
        return [FunctionValue((RS,),RS,lambda t,s=s,a=a:c(xyz(s,a,r(t)))) for s in ('target','reference') for a in range(3)]
    for profile in ('fixed','drift','excursion','orbit'):
        fs=traces(profile)
        for t,u in ((0,1),(0,2),(1,2),(1,1)):
            expected=profile=='fixed' or t==u or profile=='excursion' and (t,u)==(0,2)
            assert run('eitd',[c(Q(t)),c(Q(u)),*fs],m)==expected;count+=1
    # The excursion returns to the initial offset but fails at an interior time.
    fs=traces('fixed');times=(0,1,2);norm=norm_factory(cuts,times)
    args=['observera','carrieda','frame','context','lengthunit','timeunit',c(Q(0)),c(Q(2)),*fs]
    rows={'se':{norm([obj,*args[2:8],*fs[offset:offset+3]]) for obj,offset in (('observera',0),('carrieda',3))},'eisdd':{('frame','lengthunit','timeunit','context')}}
    mm=m|{n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}
    check=lambda model:run('eite',args+[c(Q(0)),c(Q(1))],model,'instance')
    count+=perturb(check,mm,rows,norm)
    for lo,hi in ((2,0),(0,0)):
        bad=list(args);bad[6:8]=[c(Q(lo)),c(Q(hi))]
        assert not run('eite',bad+[c(Q(0)),c(Q(1))],mm|{'se':lambda *xs:True},'instance');count+=1
    same=list(args);same[0]=same[1];assert not run('eite',same+[c(Q(0)),c(Q(1))],mm|{'se':lambda *xs:True},'instance');count+=1
    try:run('eite',args,mm)
    except ValueError as e:assert 'rational number domain' in str(e) or 'Finite function domain' in str(e),str(e)
    else:raise AssertionError('Whole time domain replaced by samples')
    return dict(cases=count,constant_relative_vector_not_only_distance=True,common_curved_motion_allowed=True,interior_excursion_detected=True,both_complete_history_bindings_required=True,local_quantifier_instantiation_only=True,full_real_time_domain_refused=True)

def trip_model():
    cuts,m=numbers();c=cuts.make;r=cuts.read;times=(Q(7),Q(8),Q(10),Q(23,2));norm=norm_factory(cuts,times)
    scalar=list(map(Q,(5,6,3,1,7,10,Q(23,2))))
    args=['firstend','lastend','ray','depart','reflection','arrival','frame','context','lengthunit','timeunit',*map(c,scalar)]
    fn=lambda lo,x,v:FunctionValue((RS,),RS,lambda t:c(Q(x)+Q(v)*(r(t)-Q(lo))))
    zero=fn(0,0,0)
    histories=[['firstend','frame','context','lengthunit','timeunit',c(Q(7)),c(Q(23,2)),fn(7,5,1),zero,zero],['lastend','frame','context','lengthunit','timeunit',c(Q(7)),c(Q(23,2)),fn(7,11,1),zero,zero],['ray','frame','context','lengthunit','timeunit',c(Q(7)),c(Q(10)),fn(7,5,3),zero,zero],['ray','frame','context','lengthunit','timeunit',c(Q(10)),c(Q(23,2)),fn(10,14,-3),zero,zero]]
    rows={'se':{norm(xs) for xs in histories},'eisb5':{('ray','frame','context')},'cf':{('ray',)},'cg':{('ray','depart','reflection','frame'),('ray','reflection','arrival','frame')},'ch':{('ray','reflection','frame')},'eisca':{('ray','depart','reflection','frame','context'),('ray','reflection','arrival','frame','context')},'zzbu':set(),'zzbv':set()}
    for end,event,t,x in (('firstend','depart',Q(7),Q(5)),('lastend','reflection',Q(10),Q(14)),('firstend','arrival',Q(23,2),Q(19,2))):
        rows['zzbu'].add((event,'frame','context','lengthunit','timeunit',t,x,Q(0),Q(0)))
        for obj in (end,'ray'):rows['zzbv'].add((obj,event,'context'))
    m|={n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}
    return cuts,m,args,rows,norm,histories,fn

@lru_cache(None)
def path_checks():
    cuts,m,args,rows,norm,histories,fn=trip_model();c=cuts.make;count=0
    count+=perturb(lambda mm:run('eiti',args,mm),m,rows,norm)
    for slot in range(len(args)):
        bad=list(args);bad[slot]=c(cuts.read(bad[slot])+1) if isinstance(bad[slot],FunctionValue) else 'other'
        assert not run('eiti',bad,m),(slot,);count+=1
    # Native linear construction in all three axes, independent of the X-axis trip.
    linear=['observera','frame','context','lengthunit','timeunit',c(Q(2)),c(Q(5)),*map(c,map(Q,(4,-3,2,-2,3,1)))]
    expected=norm(linear[:7]+[fn(2,x,v) for x,v in ((4,-2),(-3,3),(2,1))])
    model=m|{'se':lambda *xs:norm(xs)==expected}
    assert run('eitf',linear,model);count+=1
    for slot in range(len(linear)):
        bad=list(linear);bad[slot]=c(cuts.read(bad[slot])+1) if isinstance(bad[slot],FunctionValue) else 'other'
        assert not run('eitf',bad,model),slot;count+=1
    unknowns(lambda mm:run('eitf',linear,mm),model,('se','ba','bf','bd','shv'))
    return dict(cases=count,native_linear_coordinates_in_all_axes=True,both_endpoint_histories_and_both_light_histories_bound=True,native_sde_and_sb_same_three_events=True,vacuum_reflection_and_physical_light_separate=True,finite_boundary_function_fingerprints_not_full_history_proof=True)

def joined_model():
    cuts,m,args,rows,norm,histories,fn=trip_model();c=cuts.make
    constants={'xn':'firstend','xo':'lastend','xi':'rod','zaj':'carrieda','zak':'carriedb','zax':'ray','ra':'frame','ta':'lengthunit','rb':'timeunit','zas':'recorda','zat':'recordb','zau':'recordc','zay':'observera','zaz':'observerb','zaw':'trial','yn':'x','yo':'y','yp':'z'}
    m|={n:lambda x=x:x for n,x in constants.items()};m|={'zav':lambda:c(Q(6)),'tc':lambda:c(Q(3)),'yb':lambda:c(Q(1)),'eisls':lambda *xs:c(Q(7)),'eislt':lambda *xs:c(Q(23,2))}
    data={'recorda':('carrieda','firstend','depart','placea','locala',Q(7)),'recordb':('carriedb','lastend','reflection','placeb','localb',Q(10)),'recordc':('carrieda','firstend','arrival','placec','localc',Q(23,2))}
    def selected(rec,slot):
        if rec not in data:forbidden()
        return data[rec][slot]
    m|={'zad':lambda rec:selected(rec,2),'zae':lambda rec:selected(rec,3),'zaf':lambda rec:selected(rec,4),'zag':lambda rec:c(selected(rec,5)),'zah':lambda rec:c(selected(rec,5))}
    rows|={'eipk':{('context',)},'eiq4':{('carrieda','firstend','context'),('carriedb','lastend','context')},'zac':set(),'eiq2':set(),'eiqz':{('carrieda','firstend','context'),('carriedb','lastend','context')},'xb':{('observera',),('observerb',)},'zap':{('observera','carrieda','context'),('observerb','carriedb','context')},'zaq':{('observera','carrieda','frame','context'),('observerb','carriedb','frame','context')},'eite':set(),'za4':{('trial','ray','depart','reflection','arrival','frame','context')},'zar':{(o,'carrieda','carriedb','trial','bi','context') for o in ('observera','observerb')}}
    for rec,(ck,end,event,place,local,t) in data.items():
        rows['zac'].add((rec,ck,'context'));rows['eiq2'].add((ck,end,event,place,local,t,t,'context'))
    tracks={}
    for end,x in (('firstend',5),('lastend',11)):
        tracks[end]=[fn(7,x,1),fn(0,0,0),fn(0,0,0)]
    def family(body,frame,lu,tu,axis,ctx):
        if (body,frame,lu,tu,ctx)!=('rod','frame','lengthunit','timeunit','context') or axis not in ('x','y','z'):forbidden()
        def get(end):
            if end not in tracks:forbidden()
            return tracks[end][('x','y','z').index(axis)]
        return FunctionValue(('individual',),FS,get)
    observers={o:[fn(7,x,1),fn(0,1,0),fn(0,0,0)] for o,x in (('observera',5),('observerb',11))}
    def observer(obj,frame,lu,tu,axis,ctx):
        if obj not in observers or (frame,lu,tu,ctx)!=('frame','lengthunit','timeunit','context') or axis not in ('x','y','z'):forbidden()
        return observers[obj][('x','y','z').index(axis)]
    for o,ck,end in (('observera','carrieda','firstend'),('observerb','carriedb','lastend')):
        rows['eite'].add(norm([o,ck,'frame','context','lengthunit','timeunit',c(Q(7)),c(Q(23,2)),*observers[o],*tracks[end]]))
    m|={'eislu':family,'eismh':observer}
    m|={n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}
    return cuts,m,rows,norm

@lru_cache(None)
def connection_checks():
    cuts,m,rows,norm=joined_model();count=0
    selected={n:rows[n] for n in ('eipk','eiq4','zac','eiq2')}
    count+=perturb(lambda mm:run('eitk',['context'],mm),m,selected,norm)
    selected={n:rows[n] for n in ('zac','eiq2','eiqz','xb','zap','zaq','eite','za4','zar')}
    count+=perturb(lambda mm:run('eitm',['context'],mm),m,selected,norm)
    # Applying the quoted test never runs its midpoint or a stationary-clock rule.
    assert run('eitm',['context'],m|{'bi':forbidden,'qo':forbidden});count+=1
    for n in ('zas','zat','zau'):
        replacement={'zas':'recordb','zat':'recordc','zau':'recorda'}[n]
        assert not run('eitk',['context'],m|{n:lambda x=replacement:x});count+=1
    assert not run('eitm',['context'],m|{'zaz':lambda:'observera'});count+=1
    unknowns(lambda mm:run('eitk',['context'],mm),m,('eislu','zad','zah','zag','se','eiq2'))
    unknowns(lambda mm:run('eitm',['context'],mm),m,('eismh','eislu','eisls','eislt','zar'))
    return dict(cases=count,three_records_same_current_local_comparisons=True,rod_and_carried_clock_whole_interval_conditions_preserved=True,observer_representatives_bound_to_same_clock_endpoints=True,criterion_application_does_not_execute_midpoint_or_qo=True)

def source_record():
    inv=json.loads(read(INVENTORY));ids={f'einstein-1905:u{n:04}' for n in (36,37,38,39,280)}
    units=[u for u in inv['units'] if u['id'] in ids];assert len(units)==5
    paths={INVENTORY,DOC,'scripts/check_moving_trip_geometry.py'}
    for receipt in ('artifacts/einstein-rod-methods-v1/retrieval.json','artifacts/einstein-moving-trip-v1/retrieval.json'):
        paths.add(receipt)
        for row in json.loads(read(receipt))['sources']:
            assert digest((ROOT/row['path']).read_bytes())==row['sha256'];paths.add(row['path'])
    return dict(version='einstein-moving-trip-geometry-source-reading-v1',pages=['896','897'],segments=[dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],text=u['text']) for u in units],source_nonblank_characters=sum(sum(not c.isspace() for c in re.sub(r'\[M\d+\]','',u['text'])) for u in units),observations=['原刊896頁の追加の観測者設定と光往復、897頁冒頭のundと復路式を照合した。','897頁の直後の文はr_ABを静止系で測った動く棒の長さと説明する。u0040全体の判断は今回行わない。','注u0280は原刊896頁のZur Zeitに付く時間の説明である。本文の付着と提示は次の統合で接続する。'],semantic_completion=False,remaining=['u0036〜u0039の追加の想定と二式の著者帰属','r_ABと現行の静止系測定、現行の第二原理との接続','u0280の説明内容と本文への付着','全文単位の意味判断'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements']==old.document['statements'] and len(new.document['statements'])==261
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read(PRIOR));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[260])==prior['selection']
    load_annotations(ROOT,BASIS,ANNOTATIONS);assert json.loads(read(ANNOTATIONS))['entries']==json.loads(read('data/carried-clock-synchrony-identifiers-v1.json'))['entries']
    doc=parse(read(CORE));assert not doc['statements']
    for style in ('compact','full'):
        body=format_graph(doc,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    source=json.loads(read(SOURCE));assert source==source_record();validate_hashes(ROOT,source['source_sha256']);assert source['source_nonblank_characters']==476
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),preserved_statements=261,prior_meanings_and_review_preserved=True,no_new_whole_unit_claim=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:fn() for n,fn in [('numeric',numeric_checks),('comotion',comotion_checks),('paths',path_checks),('connections',connection_checks),('structure',structure_checks)]}
    source=source_record();paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source['source_sha256'])|{SOURCE,DOC,INVENTORY,PRIOR,'scripts/compose_moving_trip_geometry.py','scripts/check_moving_trip_geometry.py','tests/test_moving_trip_geometry.py','scripts/check_coordinate_correspondence.py','scripts/check_material_relative_frame.py','scripts/check_tau_differential.py','scripts/check_rod_geometry.py','scripts/check_rod_methods.py','scripts/compose_rod_methods.py','scripts/compose_carried_clock_synchrony.py','scripts/compose_material_relative_frame.py','scripts/compose_limits.py'}
    return dict(status='moving_trip_geometry_dependency_checked_source_integration_pending',document=FULL,**results,alignment=dict(segments=[dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],definitions=list(MEANINGS),status='explicit_interpretive_annotation') for s in source['segments']]),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=source['remaining'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
