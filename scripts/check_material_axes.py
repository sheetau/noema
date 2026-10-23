"""Check material support geometry, complete-history bindings and axis coverage."""
from functools import lru_cache
from fractions import Fraction as Q
from itertools import product
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
from scripts.check_rod_methods import value,relation
from scripts.compose_material_axes import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,MEANINGS,PRIMITIVES,build

DOC='docs/material-axes-v1.md';SOURCE='data/einstein-material-axes-source-reading-v1.json';INVENTORY='artifacts/written-units-v1/einstein-1905.json'
PRIORS=('data/einstein-transformation-heading-review-v1.json',)
DEPENDENCIES=('reports/material-body-motion-v1.json','reports/rod-methods-v1.json','reports/observer-contrast-v1.json','reports/rod-geometry-v1.json')
DOMAIN=('body','second','origin','otherorigin','guide','otherguide','point','hidden','frame','moving','lengthunit','timeunit','x','y','z','other')
POINTS=('context','other')
def forbidden(*xs):raise ValueError('Unknown material-axes input')
def constants():return {n:lambda x=x:x for n,x in {'ra':'frame','ta':'lengthunit','rb':'timeunit','yn':'x','yo':'y','yp':'z'}.items()}

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    boundaries=NUM|{'eigy','eit2'}
    if mode=='native_history':boundaries.add('eiad')
    else:boundaries.add('eipw')
    if name in ('eivc','eivd','eive','eivf'):boundaries.add('eiva')
    if name=='eivf':boundaries.add('eivc')
    if name=='eivg':boundaries|={'eivf','eive','eivd'}
    abstract(doc,boundaries);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jma'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    doc['statements']=[dict(kind='ask',body=dict(kind='call',symbol=name,arguments=args))];return doc,slots

def run(name,args,m,mode='boundary'):
    doc,slots=fixture(name,mode);assert len(args)==len(slots)
    mm=constants()|m|{n:lambda x=x:x for n,x in zip(slots,args)}
    return evaluate_document(doc,individuals=DOMAIN,situations=POINTS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=300000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def unknowns(check,m,names):
    for n in names:
        try:check(m|{n:forbidden})
        except ValueError as e:assert 'Unknown material-axes' in str(e),str(e)
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

def setup(positions=None,members=('guide','point','hidden')):
    cuts,m=numbers();c=cuts.make;r=cuts.read
    # Every member of this explicit finite carrier has a specified coordinate.
    # Inputs outside it are rejected, never assigned a default zero trajectory.
    pos={p:(Q(i+11),Q(5),Q(6)) for i,p in enumerate(DOMAIN)}
    pos.update(origin=(0,0,0),guide=(2,0,0),point=(0,0,0),hidden=(-3,0,0),otherorigin=(0,0,0),otherguide=(0,3,0))
    pos.update(positions or {})
    tracks={(a,p):FunctionValue((RS,),RS,lambda t,a=a,p=p:c(Q(pos[p][a]))) for a in range(3) for p in DOMAIN}
    families=[FunctionValue(('individual',),FS,lambda p,a=a:tracks[a,p] if (a,p) in tracks else forbidden()) for a in range(3)]
    def selector(body,frame,lu,tu,axis,ctx):
        if body not in DOMAIN or (frame,lu,tu,ctx)!=('frame','lengthunit','timeunit','context') or axis not in ('x','y','z'):forbidden()
        return families[('x','y','z').index(axis)]
    m|={'eislu':selector,'eisls':lambda *xs:c(Q(0)),'eislt':lambda *xs:c(Q(2)),'eirh':lambda b,p,ctx:b=='body' and p in members and ctx=='context'}
    def one(x):
        if not isinstance(x,FunctionValue):return value(x)
        if x.parameters==('number',):return r(x)
        if x.parameters==(RS,):return tuple(r(x(c(Q(t)))) for t in (0,1,2))
        if x.parameters==('individual',) and x.result=='truth':return tuple(x(p) for p in DOMAIN)
        if x.parameters==('individual',) and x.result==FS:return tuple(one(x(p)) for p in DOMAIN)
        forbidden()
    return cuts,m,families,lambda xs:tuple(one(x) for x in xs)

@lru_cache(None)
def numeric_checks():
    cuts,m=numbers();c=cuts.make;count=0
    vectors=((0,0,0),(1,0,0),(-2,0,0),(0,3,0),(1,2,3))
    for u,w in product(vectors,repeat=2):
        cross=(u[1]*w[2]-u[2]*w[1],u[2]*w[0]-u[0]*w[2],u[0]*w[1]-u[1]*w[0])
        args=[c(Q(x)) for x in u+w]
        assert run('eiu5',args,m)==(cross==(0,0,0));count+=1
        assert run('eiu6',args,m)==(any(u) and any(w) and sum(a*b for a,b in zip(u,w))==0);count+=1
    for root in ('eiu5','eiu6'):
        args=[c(Q(x)) for x in (1,0,0,0,1,0)]
        assert not run(root,args,m|{'ba':lambda x:False});count+=1
        unknowns(lambda mm:run(root,args,mm),m,('ba','bb','shv','sca'))
    return dict(cases=count,zero_displacement_allowed_but_zero_direction_not_perpendicular=True,opposite_directions_and_nonunit_vectors_supported=True)

@lru_cache(None)
def line_checks():
    count=0
    cases=(('straight',{},('guide','point','hidden'),True),('hidden_bend',{'hidden':(-3,1,0)},('guide','point','hidden'),False),('zero_direction',{'guide':(0,0,0)},('guide','point','hidden'),False),('origin_unoccupied',{'point':(1,0,0)},('guide','point','hidden'),False),('guide_not_material',{},('point','hidden'),False),('empty',{},(),False),('opposite_side',{'guide':(-2,0,0)},('guide','point','hidden'),True))
    for label,pos,members,expected in cases:
        cuts,m,_,_=setup(pos,members);args=['body','origin','guide','frame','context',cuts.make(Q(0))]
        assert run('eiu7',args,m)==expected,label;count+=1
    cuts,m,_,_=setup();args=['body','origin','guide','frame','context',cuts.make(Q(0))]
    unknowns(lambda mm:run('eiu7',args,mm),m,('eislu','eirh','ba','sca'))
    assert not run('eiu7',args,m|{'eirh':lambda b,p,ctx:b=='body' and p in ('guide','point','hidden','other') and ctx=='context'});count+=1
    return dict(cases=count,all_members_not_only_two_markers_checked=True,origin_occupied_without_marker_identity=True,nondegenerate_material_direction_required=True)

@lru_cache(None)
def history_checks():
    cuts,m,families,norm=setup();c=cuts.make
    members=FunctionValue(('individual',),'truth',lambda p:p in ('guide','point','hidden'))
    fields=['body','frame','context','lengthunit','timeunit',c(Q(0)),c(Q(2)),members,*families]
    origin=['origin','frame','context','lengthunit','timeunit',c(Q(0)),c(Q(2)),*(f('origin') for f in families)]
    rows={'eismv':{('body','context')},'eipw':{('body','frame','context')},'eigy':{norm(fields)},'eit2':{norm(origin)},'eisdd':{('frame','lengthunit','timeunit','context')}}
    m|={n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}
    check=lambda mm:run('eiva',['body','origin','guide','frame','context'],mm)
    count=perturb(check,m,rows,norm)
    unknowns(check,m,('eislu','eisls','eislt'))
    try:run('eiva',['body','origin','guide','frame','context'],m|{'eiad':lambda *xs:True},'native_history')
    except ValueError as e:assert 'rational number domain' in str(e) or 'Finite function domain' in str(e),str(e)
    else:raise AssertionError('Complete static history silently sampled')
    return dict(cases=count,same_complete_material_history_and_geometric_origin=True,all_real_history_refused=True,finite_boundary_function_samples_not_extensional_or_history_proof=True)

@lru_cache(None)
def support_checks():
    count=0;args=['body','origin','guide','second','otherorigin','otherguide','frame','context']
    cases=(('perpendicular',(0,0,0),(0,3,0),(True,False,False)),('same_line_shift',(4,0,0),(1,0,0),(False,True,True)),('parallel_offset',(0,1,0),(2,1,0),(False,True,False)),('same_origin_opposite',(0,0,0),(-4,0,0),(False,True,True)),('oblique',(0,0,0),(1,1,0),(False,False,False)))
    rows={'eiva':{tuple(args[:3]+args[-2:]),tuple(args[3:6]+args[-2:])}}
    for label,o,g,expected in cases:
        _,m,_,_=setup({'otherorigin':o,'otherguide':g});m|={'eiva':relation(rows['eiva'])}
        actual=tuple(run(n,args,m) for n in ('eivc','eivd','eive'));assert actual==expected,(label,actual);count+=3
    _,m,_,_=setup({'otherorigin':(4,0,0),'otherguide':(1,0,0)});m|={'eiva':relation(rows['eiva'])}
    count+=perturb(lambda mm:run('eive',args,mm),m,rows)
    unknowns(lambda mm:run('eive',args,mm),m,('eislu','eisls'))
    return dict(cases=count,support_coincidence_distinct_from_parallelism_and_object_identity=True,shifted_origins_and_reversed_directions_allowed=True,actual_coordinate_directions_used=True)

@lru_cache(None)
def triad_checks():
    cuts,m,_,_=setup();count=0
    lines={'x':'body','y':'second','z':'hidden'}
    rows={'va':{('moving',)},'zbv':{('moving','origin','context')}}
    rows['zbw']={('moving',line,role,'context') for role,line in lines.items()}
    rows['zbr']={(line,'origin','context') for line in lines.values()}
    rows['eiva']={(line,'origin','guide','frame','context') for line in lines.values()}
    rows['eivc']={(lines[a],'origin','guide',lines[b],'origin','guide','frame','context') for a,b in (('x','y'),('x','z'),('y','z'))}
    m|={n:relation(rs) for n,rs in rows.items()}
    m|={'zbn':lambda f,c:'origin','zbo':lambda f,r,c:lines[r] if (f,c)==('moving','context') and r in lines else forbidden(),'eismu':lambda *xs:'guide','eigy':lambda *xs:xs[0] in lines.values() and xs[1:5]==('frame','context','lengthunit','timeunit')}
    count+=perturb(lambda mm:run('eivf',['moving','context'],mm),m,rows)
    for extra in (('moving','other','x','context'),('moving','body','other','context')):
        assert not run('eivf',['moving','context'],m|{'zbw':relation(rows['zbw']|{extra})});count+=1
    assert not run('eivf',['moving','context'],m|{'zbv':relation(rows['zbv']|{('moving','other','context')})});count+=1
    assert not run('eivf',['moving','context'],m|{'eigy':lambda *xs:False});count+=1
    unknowns(lambda mm:run('eivf',['moving','context'],mm),m,('eismu','zbn','zbo','eigy'))
    # Connect native sey with two different origins and three directed pairings.
    linepairs={('frame','x'):'body',('frame','y'):'second',('frame','z'):'hidden',('moving','x'):'point',('moving','y'):'other',('moving','z'):'otherguide'}
    expected=lambda a,b: (a,'origin','guide',b,'otherorigin','guide','frame','context')
    rows={'eivf':{('frame','context'),('moving','context')},'eive':{expected('body','point')},'eivd':{expected('second','other'),expected('hidden','otherguide')}}
    m={n:relation(rs) for n,rs in rows.items()}|{'zbn':lambda f,c:'origin' if f=='frame' else 'otherorigin','zbo':lambda f,r,c:linepairs[f,r],'eismu':lambda *xs:'guide'}
    count+=perturb(lambda mm:run('eivg',['frame','moving','context'],mm),m,rows)
    assert not run('eivg',['frame','frame','context'],{n:lambda *xs:True for n in rows}|{k:v for k,v in m.items() if k not in rows});count+=1
    return dict(cases=count,native_sex_and_sey_connected_to_material_geometry=True,exact_three_axis_roles_and_unique_origin=True,all_three_pairs_and_frame_identity_checked=True)

def source_record():
    inv=json.loads(read(INVENTORY));u=inv['units'][42];assert u['id']=='einstein-1905:u0043' and len(u['text'])==441
    math={m['id']:m for m in inv['math'] if m['id'] in u['math_ids']};forms=dict(zip(('M0063','M0064','M0065'),('X','Y','Z')))
    for n,s in forms.items():assert ''.join(ET.fromstring(math[n]['mathml']).itertext())==s
    receipt='artifacts/einstein-moving-trip-v1/retrieval.json';paths={INVENTORY,DOC,'scripts/check_material_axes.py',receipt}
    for row in json.loads(read(receipt))['sources']:
        assert digest((ROOT/row['path']).read_bytes())==row['sha256'];paths.add(row['path'])
    return dict(version='einstein-material-axes-source-reading-v1',reviewer='assistant_visual_and_text_review',unit=u['id'],unit_sha256=u['text_sha256'],range=[0,441],text=u['text'],source_nonblank_characters=sum(not c.isspace() for c in re.sub(r'\[M\d+\]','',u['text'])),pages=['897'],math=[dict(id=n,sha256=math[n]['sha256'],printed=s) for n,s in forms.items()],observations=['各系は同じ一点から出る三本の互いに直交する剛な物質線として説明される。','対応するX軸はzusammenfallen、Y/Z軸はbezüglich parallelであり、同じ物体と原点の一致を要求する文面ではない。','後半は各系の物差しと時計群、それらのgenau gleichを設定する。今回の依存群だけで全文を記述済みとしない。'],semantic_completion=False,remaining=['同じ二系の物差しと全時計の仕様の厳密な一致','静止空間という呼称・d. h.の説明・設定指示と著者帰属','u0043全体の意味判断'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements']==old.document['statements'] and len(new.document['statements'])==267
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read(PRIORS[0]));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[266])==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);assert json.loads(read(ANNOTATIONS))['entries']==json.loads(read('data/transformation-heading-identifiers-v1.json'))['entries']
    doc=parse(read(CORE));assert not doc['statements']
    for style in ('compact','full'):
        body=format_graph(doc,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),preserved_statements=267,prior_meanings_and_reviews_preserved=True,no_new_author_assertion=True,whole_unit_completion=False)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:fn() for n,fn in [('numeric',numeric_checks),('line',line_checks),('history',history_checks),('supports',support_checks),('triads',triad_checks),('structure',structure_checks)]}
    source=source_record();text=source['text'];phrases=('je drei von einem Punkte ausgehenden, aufeinander senkrechten starren materiellen Linien','Die [M0063]-Achsen beider Systeme mögen zusammenfallen, ihre [M0064]- und [M0065]-Achsen bezüglich parallel sein.')
    segments=[dict(unit=source['unit'],unit_sha256=source['unit_sha256'],range=[text.index(p),text.index(p)+len(p)],source=p,definitions=list(MEANINGS),status='explicit_interpretive_annotation') for p in phrases]
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source['source_sha256'])|{SOURCE,DOC,INVENTORY,*PRIORS,*DEPENDENCIES,'scripts/compose_material_axes.py','scripts/check_material_axes.py','tests/test_material_axes.py','scripts/check_moving_trip_geometry.py','scripts/check_coordinate_correspondence.py','scripts/check_rod_methods.py','scripts/check_material_relative_frame.py','scripts/check_tau_differential.py','scripts/compose_rod_methods.py','scripts/compose_transformation_heading.py','scripts/compose_material_relative_frame.py','scripts/compose_limits.py'}
    return dict(status='material_axes_dependency_checked_source_integration_pending',document=FULL,**results,alignment=dict(segments=segments),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=source['remaining'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
