"""Check projection, sign, actual histories and every positive-direction record."""
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
from scripts.check_rod_geometry import instantiate
from scripts.check_rod_methods import value
from scripts.compose_axis_projection import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,MEANINGS,build

DOC='docs/axis-projection-v1.md';SOURCE='data/einstein-axis-projection-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';PRIOR='data/einstein-parallel-choice-review-v1.json'
DEPENDENCIES=('reports/moving-axes-v1.json','reports/material-axes-v1.json','reports/parallel-choice-v1.json')
DOMAIN=('axis','origin','guide','place','projection','frame','lengthunit','timeunit','x','y','z','recorda','recordb','other')
POINTS=('context','other')

def forbidden(*xs):raise ValueError('Unknown axis-projection input')
def constants():return {n:lambda x=x:x for n,x in {'ta':'lengthunit','rb':'timeunit','yn':'x','yo':'y','yp':'z'}.items()}

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    abstract(doc,NUM|{'eiv2','eipw','eit2'}|({'eixa'} if name=='eixb' else set()))
    doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name)
    if mode=='instance':assert instantiate(d)==[RS]
    slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jap'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    doc['statements']=[dict(kind='ask',body=dict(kind='call',symbol=name,arguments=args))];return doc,slots

def run(name,args,m,mode='boundary'):
    doc,slots=fixture(name,mode);assert len(args)==len(slots),(name,len(args),len(slots))
    mm=constants()|m|{n:lambda x=x:x for n,x in zip(slots,args)}
    return evaluate_document(doc,individuals=DOMAIN,situations=POINTS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=500000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def unknowns(check,m,names):
    for n in names:
        try:check(m|{n:forbidden})
        except ValueError as e:assert 'Unknown axis-projection' in str(e),str(e)
        else:raise AssertionError(('Unknown input accepted',n))

@lru_cache(None)
def geometry_checks():
    cuts,m=numbers();c=cuts.make;count=0
    def check(name,args,expected):
        nonlocal count
        actual=run(name,[c(Q(x)) for x in args],m);assert actual==expected,(name,args,actual);count+=1
    # Each component, both signs, zero residual, zero foot and arbitrary direction scale.
    for axis in range(3):
        for signed in (-3,0,2):
            foot=[0,0,0];foot[axis]=signed
            point=foot.copy();point[(axis+1)%3]=4
            for scale in (-5,2):
                direction=[0,0,0];direction[axis]=scale
                for p in (point,foot):
                    check('eiw4',p+foot+direction,True)
                    expected=signed*(1 if scale>0 else -1)
                    check('eiw6',p+foot+direction+[expected],True)
                    check('eiw6',p+foot+direction+[expected+1],False)
                broken=foot.copy();broken[(axis+1)%3]=1
                check('eiw4',point+broken+direction,False)
                broken=foot.copy();broken[axis]+=1
                check('eiw4',point+broken+direction,False)
    # Rational non-axis-aligned example: displacement length is 5, not dot product 50.
    for scale in (Q(1,2),2,-3):
        d=[3*scale,4*scale,0];s=5 if scale>0 else -5
        check('eiw6',[7,1,2,3,4,0]+d+[s],True)
        check('eiw6',[7,1,2,3,4,0]+d+[50],False)
    for name,args in (('eiw4',[1,2,3,0,0,0,0,0,0]),('eiw5',[0,0,0,0,0,0,0]),('eiw6',[0]*10)):
        check(name,args,False)
    args=[c(Q(x)) for x in [2,1,3,2,0,0,4,0,0,2]]
    assert not run('eiw6',args,m|{'ba':lambda x:False});count+=1
    unknowns(lambda mm:run('eiw6',args,mm),m,('ba','bf','bd','shv','bg','sca'))
    return dict(cases=count,zero_and_negative_coordinates_and_each_axis=True,oblique_direction_scale_and_sign_distinguished=True,zero_direction_and_nonorthogonal_foot_rejected=True)

def setup(positions=None,directions=None):
    cuts,m=numbers();c=cuts.make;r=cuts.read
    pos={'origin':(10,20,30),'guide':(8,20,30),'place':(12,21,33),'projection':(12,20,30)}|(positions or {})
    fs={(p,a):FunctionValue((RS,),RS,lambda t,p=p,a=a:c(Q(pos[p][a]))) for p in pos for a in range(3)}
    def representative(p,f,lu,tu,a,ctx):
        if p not in pos or (f,lu,tu,ctx)!=('frame','lengthunit','timeunit','context') or a not in ('x','y','z'):forbidden()
        return fs[p,('x','y','z').index(a)]
    def family(body,f,lu,tu,a,ctx):
        if body!='axis' or (f,lu,tu,ctx)!=('frame','lengthunit','timeunit','context') or a not in ('x','y','z'):forbidden()
        return FunctionValue(('individual',),FS,lambda p:representative(p,f,lu,tu,a,ctx))
    def norm(xs):
        def one(x):
            if not isinstance(x,FunctionValue):return value(x)
            if x.parameters==('number',):return r(x)
            if x.parameters==(RS,) and x.result==RS:return tuple(r(x(c(Q(t)))) for t in (0,1,2))
            forbidden()
        return tuple(one(x) for x in xs)
    rows={'va':{('frame',)},'ti':{('lengthunit',)},'ci':{('timeunit',)},'zbv':{('frame','origin','context')},'zbw':{('frame','axis','x','context')},'zcu':{(p,'frame','context') for p in ('place','projection')},'eisdd':{('frame','lengthunit','timeunit','context')},'eiv2':{('axis','origin','guide','frame','context')},'eipw':{('axis','frame','context')}}
    rows['eit2']={norm([p,'frame','context','lengthunit','timeunit',c(Q(0)),c(Q(2)),*(fs[p,a] for a in range(3))]) for p in ('origin','place','projection')}
    rows['zsa']={(p,'axis','frame','lengthunit','context') for p in ('recorda','recordb')}
    vectors={'recorda':(4,0,0),'recordb':(7,0,0)}|(directions or {})
    def component(rec,a):
        if rec not in DOMAIN or a not in ('x','y','z'):forbidden()
        # Defined non-record values in this finite fixture; membership is independently tested.
        return c(Q(vectors.get(rec,(1,0,0))[('x','y','z').index(a)]))
    m|={n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}
    m|={'eismh':representative,'eislu':family,'eisls':lambda *xs:c(Q(0)),'eislt':lambda *xs:c(Q(2)),'zsb':component}
    args=['axis','origin','guide','place','projection','frame','x','context',c(Q(1)),c(Q(2))]
    return cuts,m,rows,norm,args

@lru_cache(None)
def physical_checks():
    cuts,m,rows,norm,args=setup();count=1
    check=lambda mm:run('eixa',args,mm)
    assert check(m)
    for n,rs in rows.items():
        if n=='zsa':continue
        for row in rs:
            assert not check(m|{n:lambda *xs,rs=rs-{row}:norm(xs) in rs}),(n,row);count+=1
            for i in range(len(row)):
                changed=tuple('wrong' if j==i else x for j,x in enumerate(row))
                assert not check(m|{n:lambda *xs,rs=(rs-{row})|{changed}:norm(xs) in rs}),(n,i);count+=1
    # Native arithmetic compares actual positions, including translated origins.
    for positions,expected in (({'projection':(12,21,30)},False),({'projection':(13,20,30)},False),({'guide':(10,20,30)},False),({'guide':(10,18,30)},False),({'guide':(17,20,30)},True),({'origin':(0,0,0),'guide':(-2,0,0),'place':(2,1,3),'projection':(2,0,0)},True)):
        _,mm,_,_,aa=setup(positions);assert run('eixa',aa,mm)==expected,(positions,expected);count+=1
    for a in ('eismh','eislu'):
        original=m[a]
        def changed(*xs,original=original,a=a):
            fn=original(*xs)
            if xs[4]!='y':return fn
            if a=='eismh':return FunctionValue((RS,),RS,lambda t:cuts.make(cuts.read(fn(t))+1))
            return FunctionValue(('individual',),FS,lambda p:FunctionValue((RS,),RS,lambda t:cuts.make(cuts.read(fn(p)(t))+(1 if p=='guide' else 0))))
        assert not check(m|{a:changed});count+=1
    unknowns(check,m,tuple(rows)+('eismh','eislu','eisls','eislt','zsb'))
    return dict(cases=count,native_coordinates_and_material_direction_connected=True,origin_and_both_places_share_complete_static_histories=True,every_physical_boundary_argument_checked=True)

@lru_cache(None)
def orientation_checks():
    cuts,m,rows,norm,args=setup();count=0
    for directions,expected in (({'recordb':(-7,0,0)},False),({'recordb':(0,0,0)},False),({'recordb':(7,1,0)},False),({'recorda':(Q(1,7),0,0)},True)):
        _,mm,_,_,aa=setup(directions=directions);assert run('eixa',aa,mm)==expected;count+=1
    # Record identity is immaterial; its axis/chart/unit/context is not.
    renamed={('other',)+row[1:] for row in rows['zsa']}
    assert run('eixa',args,m|{'zsa':lambda *xs:tuple(xs) in renamed});count+=1
    for i in range(1,5):
        changed={tuple('other' if j==i else x for j,x in enumerate(row)) for row in rows['zsa']}
        assert not run('eixa',args,m|{'zsa':lambda *xs:tuple(xs) in changed});count+=1
    assert not run('eixa',args,m|{'zsa':lambda *xs:False});count+=1
    assert not run('eixa',args[:-1]+[cuts.make(Q(-2))],m);count+=1
    for positive in (-1,1):
        localcuts,mm,_,_,aa=setup({'place':(10,21,33),'projection':(10,20,30)},dict(recorda=(positive,0,0),recordb=(positive*2,0,0)))
        aa[-1]=localcuts.make(Q(0));assert run('eixa',aa,mm);count+=1
    return dict(cases=count,arbitrary_material_guide_not_assumed_positive=True,all_positive_direction_records_checked=True,zero_coordinate_valid_with_either_consistent_orientation=True)

@lru_cache(None)
def interval_checks():
    cuts,m,_,norm,args=setup();c=cuts.make;count=0
    base=args[:8]+args[-1:];row=norm(args)
    mm=m|{'eixa':lambda *xs:norm(xs)==row}
    assert run('eixb',base+[c(Q(1))],mm,'instance');count+=1
    for i in range(len(row)):
        altered=tuple('wrong' if j==i else x for j,x in enumerate(row))
        assert not run('eixb',base+[c(Q(1))],m|{'eixa':lambda *xs:norm(xs)==altered},'instance');count+=1
    for t in (-1,0,1,2,3):
        assert run('eixb',base+[c(Q(t))],m|{'eixa':lambda *xs:False},'instance')==(t not in (0,1,2));count+=1
    try:run('eixb',base,mm)
    except ValueError as e:assert 'rational number domain' in str(e) or 'Finite function domain' in str(e),str(e)
    else:raise AssertionError('Whole real interval silently sampled')
    unknowns(lambda model:run('eixb',base+[c(Q(1))],model,'instance'),mm,('eixa','eisls','eislt'))
    return dict(cases=count,same_points_role_and_value_bound_at_every_time=True,native_all_real_time_evaluation_rejected=True)

def source_record():
    inv=json.loads(read(INVENTORY));u=inv['units'][44];assert u['id']=='einstein-1905:u0045' and len(u['text'])==761
    end=u['text'].index(' Es werde');text=u['text'][:end]
    math={m['id']:m for m in inv['math'] if m['id'] in u['math_ids']};forms=dict(zip(('M0075','M0076','M0077','M0078','M0079','M0080'),('K','k','x,y,z','ξ,η,ζ','t','τ')))
    for n,s in forms.items():assert ''.join(ET.fromstring(math[n]['mathml']).itertext())==s
    receipts=('artifacts/einstein-moving-trip-v1/retrieval.json','artifacts/einstein-frame-coordinates-v1/retrieval.json');paths={INVENTORY,DOC,*receipts}
    for receipt in receipts:
        for row in json.loads(read(receipt))['sources']:
            assert digest((ROOT/row['path']).read_bytes())==row['sha256'];paths.add(row['path'])
    return dict(version='einstein-axis-projection-source-reading-v1',reviewer='assistant_visual_and_text_review',unit=u['id'],unit_sha256=u['text_sha256'],range=[0,end],text=text,source_nonblank_characters=sum(not c.isspace() for c in re.sub(r'\[M\d+\]','',text)),pages=['897','898'],math=[dict(id=n,sha256=math[n]['sha256'],printed=s) for n,s in forms.items()],observations=['897頁末のWir denken unsから898頁冒頭ermitteltまでが空間測定の一文。','静止系Kには静止物差し、運動系kには共に動く物差しを用い、三成分をそれぞれx,y,zとξ,η,ζで示す。','第二文は両系とも時計が存在する全地点に限定し、§1の光信号による手順を二度参照する。','正射影と符号付き距離は明示的な操作的読解で、本文にその手順が逐語的に書かれているとは扱わない。'],semantic_completion=False,remaining=['同じ校正済み物差しによる実際の測定操作と符号付き距離の接続','全空間の三成分の存在・値の一意性、初期の両系と計器の同一性','時計配置点の局所時刻と§1の全信号試行による同期','二つの設定指示、表記と参照を含むu0045の全体統合・意味判断'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements']==old.document['statements'] and len(new.document['statements'])==270
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read(PRIOR));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[268,269])==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);assert json.loads(read(ANNOTATIONS))['entries']==json.loads(read('data/parallel-choice-identifiers-v1.json'))['entries']
    doc=parse(read(CORE));assert not doc['statements']
    for style in ('compact','full'):
        body=format_graph(doc,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=len(MEANINGS),new_primitives=0,preserved_statements=270,prior_meanings_and_reviews_preserved=True,whole_unit_completion=False)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:fn() for n,fn in [('geometry',geometry_checks),('physical',physical_checks),('orientation',orientation_checks),('interval',interval_checks),('structure',structure_checks)]}
    source=source_record();paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source['source_sha256'])|{SOURCE,DOC,INVENTORY,PRIOR,*DEPENDENCIES,'scripts/compose_axis_projection.py','scripts/check_axis_projection.py','tests/test_axis_projection.py','scripts/check_moving_trip_geometry.py','scripts/check_coordinate_correspondence.py','scripts/check_material_relative_frame.py','scripts/check_rod_geometry.py','scripts/check_rod_methods.py','scripts/check_tau_differential.py','scripts/compose_parallel_choice.py','scripts/compose_material_axes.py','scripts/compose_moving_axes.py','scripts/compose_rod_methods.py','scripts/compose_material_relative_frame.py','scripts/compose_limits.py'}
    return dict(status='signed_physical_axis_projection_checked',document=FULL,**results,alignment=dict(segments=[dict(unit=source['unit'],unit_sha256=source['unit_sha256'],range=source['range'],source=source['text'],definitions=list(MEANINGS),status='explicit_interpretive_annotation')]),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=source['remaining'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
