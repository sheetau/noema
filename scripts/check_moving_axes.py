"""Check moving material axes without replacing all time by endpoints."""
from functools import lru_cache
from fractions import Fraction as Q
import json,re
from xml.etree import ElementTree as ET
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import FunctionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_moving_trip_geometry import NUM,numbers
from scripts.check_material_relative_frame import RS,FS
from scripts.check_material_axes import setup as static_setup,DOMAIN
from scripts.check_rod_geometry import instantiate
from scripts.check_rod_methods import value,relation
from scripts.compose_moving_axes import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,MEANINGS,build

DOC='docs/moving-axes-v1.md';SOURCE='data/einstein-moving-axes-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';PRIOR='data/einstein-frame-instruments-review-v1.json'
DEPENDENCIES=('reports/frame-motion-v1.json','reports/material-axes-v1.json','reports/moving-trip-geometry-v1.json')
POINTS=('context','other')

def forbidden(*xs):raise ValueError('Unknown moving-axes input')
def constants():return {n:lambda x=x:x for n,x in {'ra':'frame','ta':'lengthunit','rb':'timeunit','yn':'x','yo':'y','yp':'z'}.items()}

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    boundaries=NUM|{'eigy','se'}
    if name=='eiv2':boundaries.add('eiu7')
    if name=='eiv6':boundaries|={'eiu7','eiv5'}
    if name=='eiv7':boundaries|={'eiv2','eiv6'}
    if name=='eiwa':boundaries|={'eiv6','eiv4'}
    if name=='eiwb':boundaries|={'eiv7','eiwa'}
    abstract(doc,boundaries);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name)
    if mode=='instance':assert instantiate(d)==[RS]
    slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jma2'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    doc['statements']=[dict(kind='ask',body=dict(kind='call',symbol=name,arguments=args))];return doc,slots

def run(name,args,m,mode='boundary'):
    doc,slots=fixture(name,mode);assert len(args)==len(slots),(name,len(args),len(slots))
    mm=constants()|m|{n:lambda x=x:x for n,x in zip(slots,args)}
    return evaluate_document(doc,individuals=DOMAIN,situations=POINTS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=400000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def unknowns(check,m,names):
    for n in names:
        try:check(m|{n:forbidden})
        except ValueError as e:assert 'Unknown moving-axes' in str(e),str(e)
        else:raise AssertionError(('Unknown input accepted',n))

def perturb(check,m,rows,norm=lambda xs:tuple(value(x) for x in xs)):
    count=1;assert check(m)
    for n,rs in rows.items():
        for row in rs:
            assert not check(m|{n:lambda *xs,rs=rs-{row}:norm(xs) in rs}),(n,row);count+=1
            for i in range(len(row)):
                changed=tuple('wrong' if j==i else x for j,x in enumerate(row))
                assert not check(m|{n:lambda *xs,rs=(rs-{row})|{changed}:norm(xs) in rs}),(n,i);count+=1
    unknowns(check,m,rows);return count

def setup(positions=None,rotate=False):
    cuts,m,base,norm=static_setup(positions);c=cuts.make;r=cuts.read
    def coordinate(a,p,t):
        if p not in DOMAIN:forbidden()
        val=r(base[a](p)(t));time=r(t)
        if rotate and p=='otherguide':
            delta=(2*(time-1)**2,2*(1-(time-1)**2),0)[a]
            val=r(base[a]('otherorigin')(t))+delta
        return c(val+(3*time if a==0 else -2*time if a==1 else 0))
    tracks={(a,p):FunctionValue((RS,),RS,lambda t,a=a,p=p:coordinate(a,p,t)) for a in range(3) for p in DOMAIN}
    families=[FunctionValue(('individual',),FS,lambda p,a=a:tracks[a,p] if (a,p) in tracks else forbidden()) for a in range(3)]
    def selector(body,frame,lu,tu,axis,ctx):
        if body not in DOMAIN or (frame,lu,tu,ctx)!=('frame','lengthunit','timeunit','context') or axis not in ('x','y','z'):forbidden()
        return families[('x','y','z').index(axis)]
    m['eislu']=selector
    m['eirh']=lambda b,p,ctx:ctx=='context' and ((b=='body' and p in ('guide','point','hidden')) or (b=='second' and p in ('otherorigin','otherguide')))
    return cuts,m,families,norm

@lru_cache(None)
def geometry_checks():
    count=0;args=['body','origin','guide','second','otherorigin','otherguide','frame','context']
    cases=(('same',(0,1,0),(3,1,0),(True,False)),('opposite',(0,1,0),(-2,1,0),(True,False)),('perpendicular',(4,3,0),(4,5,0),(False,True)),('oblique',(4,3,0),(5,4,0),(False,False)),('collapsed',(4,3,0),(4,3,0),(False,False)))
    for label,o,g,expected in cases:
        cuts,m,_,_=setup({'otherorigin':o,'otherguide':g})
        for time in (0,1,2):
            actual=tuple(run(n,args+[cuts.make(Q(time))],m) for n in ('eiv4','eiv5'))
            assert actual==expected,(label,time,actual);count+=2
    cuts,m,_,_=setup({'otherorigin':(0,1,0)},rotate=True)
    for time,expected in ((0,(True,False)),(1,(False,True)),(2,(True,False))):
        actual=tuple(run(n,args+[cuts.make(Q(time))],m) for n in ('eiv4','eiv5'))
        assert actual==expected,(time,actual);count+=2
    cuts,m,_,_=setup({'otherorigin':(0,1,0),'otherguide':(2,1,0),'hidden':(-3,1,0)})
    assert not run('eiv4',args+[cuts.make(Q(1))],m);count+=1
    cuts,m,_,_=setup({'otherorigin':(0,1,0),'otherguide':(2,1,0)})
    unknowns(lambda mm:run('eiv4',args+[cuts.make(Q(1))],mm),m,('eislu','eirh','ba','bf','sca'))
    return dict(cases=count,actual_time_dependent_directions_not_initial_directions=True,opposite_and_transversely_separated_parallel_axes_allowed=True,intermediate_rotation_and_bent_hidden_member_detected=True)

@lru_cache(None)
def history_checks():
    cuts,m,fs,norm=setup();c=cuts.make
    members=FunctionValue(('individual',),'truth',lambda p:p in ('guide','point','hidden'))
    fields=['body','frame','context','lengthunit','timeunit',c(Q(0)),c(Q(2)),members,*fs]
    origin=['origin','frame','context','lengthunit','timeunit',c(Q(0)),c(Q(2)),*(f('origin') for f in fs)]
    line=['body','origin','guide','frame','context']
    rows={'eismv':{('body','context')},'eigy':{norm(fields)},'se':{norm(origin)},'eiu7':{norm(line+[c(Q(1))])}}
    m|={n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}
    def representative(o,f,lu,tu,axis,ctx):
        if (o,f,lu,tu,ctx)!=('origin','frame','lengthunit','timeunit','context') or axis not in ('x','y','z'):forbidden()
        return fs[('x','y','z').index(axis)]('origin')
    m['eismh']=representative
    check=lambda mm:run('eiv2',line+[c(Q(1))],mm,'instance')
    count=perturb(check,m,rows,norm)
    for axis in ('x','y','z'):
        def bad(*xs,axis=axis):
            fn=representative(*xs)
            return FunctionValue((RS,),RS,lambda t:c(cuts.read(fn(t))+1)) if xs[4]==axis else fn
        assert not check(m|{'eismh':bad});count+=1
    # The same source geometry is required at every time inside the interval.
    for time in (-1,0,1,2,3):
        args=line+[c(Q(time))]
        expected=time not in (0,1,2)
        assert run('eiv2',args,m|{'eiu7':lambda *xs:False},'instance')==expected;count+=1
    unknowns(check,m,('eislu','eismh','eisls','eislt','eirh'))
    try:run('eiv2',line,m)
    except ValueError as e:assert 'rational number domain' in str(e) or 'Finite function domain' in str(e),str(e)
    else:raise AssertionError('All real times silently sampled')
    return dict(cases=count,material_and_representative_origins_share_complete_worldline=True,all_time_body_and_interval_guard_checked=True,complete_real_time_quantification_refused=True,finite_function_fingerprints_only_for_boundary_binding=True)

def triad_setup():
    cuts,m,_,norm=setup();lines={'x':'body','y':'second','z':'hidden'}
    rows={'va':{('moving',)},'zbv':{('moving','origin','context')},'zbw':{('moving',line,a,'context') for a,line in lines.items()},'zbr':{(line,'origin','context') for line in lines.values()}}
    rows['eiu7']={(line,'origin','guide','frame','context',Q(1)) for line in lines.values()}
    rows['eiv5']={(lines[a],'origin','guide',lines[b],'origin','guide','frame','context',Q(1)) for a,b in (('x','y'),('x','z'),('y','z'))}
    m|={n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}
    m|={'zbn':lambda f,c:'origin','zbo':lambda f,a,c:lines[a] if (f,c)==('moving','context') and a in lines else forbidden(),'eismu':lambda *xs:'guide','eigy':lambda *xs:xs[0] in lines.values() and xs[1:5]==('frame','context','lengthunit','timeunit')}
    return cuts,m,rows,lines,norm

@lru_cache(None)
def triad_checks():
    cuts,m,rows,lines,norm=triad_setup();c=cuts.make
    check=lambda mm:run('eiv6',['moving','context',c(Q(1))],mm)
    count=perturb(check,m,rows,norm)
    for n,extra in (('zbw',('moving','other','x','context')),('zbw',('moving','body','other','context')),('zbv',('moving','otherorigin','context'))):
        assert not check(m|{n:relation(rows[n]|{extra})});count+=1
    assert not check(m|{'eigy':lambda *xs:False});count+=1
    unknowns(check,m,('eismu','zbn','zbo','eigy'))
    rows={'eiv2':{(line,'origin','guide','frame','context') for line in lines.values()},'eiv6':{('moving','context',Q(1))}}
    m|={n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}
    check=lambda mm:run('eiv7',['moving','context',c(Q(1))],mm,'instance')
    count+=perturb(check,m,rows,norm)
    for time in (-1,0,1,2,3):
        assert run('eiv7',['moving','context',c(Q(time))],m|{'eiv6':lambda *xs:False},'instance')==(time not in (0,1,2));count+=1
    try:run('eiv7',['moving','context'],m)
    except ValueError as e:assert 'rational number domain' in str(e) or 'Finite function domain' in str(e),str(e)
    else:raise AssertionError('All-time triad silently sampled')
    return dict(cases=count,native_three_axes_and_exact_roles_connected=True,all_three_complete_lines_and_every_time_bound=True)

@lru_cache(None)
def parallel_checks():
    cuts,m=numbers();c=cuts.make;r=cuts.read
    norm=lambda xs:tuple(r(x) if isinstance(x,FunctionValue) else value(x) for x in xs)
    lines={('frame','x'):'body',('frame','y'):'second',('frame','z'):'hidden',('moving','x'):'point',('moving','y'):'other',('moving','z'):'otherguide'}
    expected=lambda a,b:(a,'origin','guide',b,'otherorigin','guide','frame','context',Q(1))
    rows={'eiv6':{('frame','context',Q(1)),('moving','context',Q(1))},'eiv4':{expected(lines['frame',a],lines['moving',a]) for a in ('x','y','z')}}
    m|={n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}
    m|={'zbn':lambda f,c:'origin' if f=='frame' else 'otherorigin','zbo':lambda f,a,c:lines[f,a],'eismu':lambda *xs:'guide','eisls':lambda *xs:c(Q(0)),'eislt':lambda *xs:c(Q(2))}
    check=lambda mm:run('eiwa',['frame','moving','context',c(Q(1))],mm)
    count=perturb(check,m,rows,norm)
    assert not run('eiwa',['frame','frame','context',c(Q(1))],m|{'eiv6':lambda *xs:True,'eiv4':lambda *xs:True});count+=1
    rows={'eiv7':{('frame','context'),('moving','context')},'eiwa':{('frame','moving','context',Q(1))}}
    m|={n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}
    check=lambda mm:run('eiwb',['frame','moving','context',c(Q(1))],mm,'instance')
    count+=perturb(check,m,rows,norm)
    for time in (-1,0,1,2,3):
        assert run('eiwb',['frame','moving','context',c(Q(time))],m|{'eiwa':lambda *xs:False},'instance')==(time not in (0,1,2));count+=1
    try:run('eiwb',['frame','moving','context'],m)
    except ValueError as e:assert 'rational number domain' in str(e) or 'Finite function domain' in str(e),str(e)
    else:raise AssertionError('Whole interval alignment silently sampled')
    return dict(cases=count,all_three_corresponding_pairs_and_distinct_frames=True,same_two_histories_across_all_times=True,no_origin_coincidence_or_positive_orientation_required=True)

def source_record():
    inv=json.loads(read(INVENTORY));u=inv['units'][43];assert u['id']=='einstein-1905:u0044' and len(u['text'])==687
    start=u['text'].index('Jeder Zeit');text=u['text'][start:]
    math={m['id']:m for m in inv['math'] if m['id'] in u['math_ids']};forms=dict(zip(('M0070','M0071','M0072','M0073','M0074'),('t','K','k','t','t')))
    for n,s in forms.items():assert ''.join(ET.fromstring(math[n]['mathml']).itertext())==s
    receipt='artifacts/einstein-moving-trip-v1/retrieval.json';paths={INVENTORY,DOC,receipt}
    for row in json.loads(read(receipt))['sources']:
        assert digest((ROOT/row['path']).read_bytes())==row['sha256'];paths.add(row['path'])
    return dict(version='einstein-moving-axes-source-reading-v1',reviewer='assistant_visual_and_text_review',unit=u['id'],unit_sha256=u['text_sha256'],range=[start,len(u['text'])],text=text,source_nonblank_characters=sum(not c.isspace() for c in re.sub(r'\[M\d+\]','',text)),pages=['897'],math=[dict(id=n,sha256=math[n]['sha256'],printed=s) for n,s in forms.items()],observations=['各静止系時刻に動く軸の一定の配置が対応する。','平行な一つの運動の可能性を仮定してよい理由として対称性が提示される。','括弧でtが常に静止系の時刻を指すことを明記している。'],semantic_completion=False,remaining=['配置状態の存在・一意性と全実座標に基づく同値性','並進と幾何を同じ候補履歴へ結び、一つの全時刻平行運動の可能性を保持する','対称性による仮定採用の許容、第一文の設定指示、時刻tの説明','u0044全体の意味判断'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements']==old.document['statements'] and len(new.document['statements'])==268
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read(PRIOR));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[267])==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);assert json.loads(read(ANNOTATIONS))['entries']==json.loads(read('data/frame-motion-identifiers-v1.json'))['entries']
    doc=parse(read(CORE));assert not doc['statements']
    names={d['name'] for d in doc['declarations']};assert not names&{'eiva','eivf','eivg','eit2','eipw'}
    for style in ('compact','full'):
        body=format_graph(doc,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=len(MEANINGS),new_primitives=0,preserved_statements=268,prior_meanings_and_reviews_preserved=True,no_rest_assumption_in_moving_geometry=True,whole_unit_completion=False)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:fn() for n,fn in [('geometry',geometry_checks),('history',history_checks),('triads',triad_checks),('parallel',parallel_checks),('structure',structure_checks)]}
    source=source_record();paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source['source_sha256'])|{SOURCE,DOC,INVENTORY,PRIOR,*DEPENDENCIES,'scripts/compose_moving_axes.py','scripts/check_moving_axes.py','tests/test_moving_axes.py','scripts/check_material_axes.py','scripts/check_moving_trip_geometry.py','scripts/check_coordinate_correspondence.py','scripts/check_rod_geometry.py','scripts/check_rod_methods.py','scripts/check_material_relative_frame.py','scripts/check_tau_differential.py','scripts/compose_frame_motion.py','scripts/compose_material_axes.py','scripts/compose_rod_methods.py','scripts/compose_material_relative_frame.py','scripts/compose_limits.py'}
    return dict(status='complete_time_dependent_axis_geometry_checked',document=FULL,**results,alignment=dict(segments=[dict(unit=source['unit'],unit_sha256=source['unit_sha256'],range=source['range'],source=source['text'],definitions=list(MEANINGS),status='explicit_interpretive_annotation')]),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=source['remaining'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
