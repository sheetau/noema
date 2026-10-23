"""Check preserved space, all direction records and every place/component pair."""
from functools import lru_cache
from fractions import Fraction as Q
from copy import deepcopy
import json
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
from scripts.check_rod_methods import value
from scripts.compose_spatial_coverage import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,MEANINGS,build

DOC='docs/spatial-coverage-v1.md';SOURCE='data/einstein-spatial-coverage-source-reading-v1.json'
SOURCE_PARENT='data/einstein-coordinate-measurement-source-reading-v1.json';PRIOR='data/einstein-parallel-choice-review-v1.json'
DEPENDENCIES=('reports/coordinate-measurement-v1.json','reports/axis-projection-v1.json','reports/moving-axes-v1.json')
DOMAIN=('a','b','origin','guide','point','hidden','linea','lineb','linec','ruler','frame','moving','x','y','z')
POINTS=('reference','setting','initial')
def forbidden(*xs):raise ValueError('Unknown spatial-coverage input')
def constants():return {n:lambda x=x:x for n,x in {'ta':'a','rb':'b','yn':'x','yo':'y','yp':'z','zb4':'initial','ra':'frame','zbm':'moving'}.items()}

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    boundaries=NUM|{'eit2','eiv2','eipw','eigy'}
    boundaries|={'eixl':{'eixj','eixk'},'eixm':{'eixl','eiv5'},'eixn':{'eixm','eixj','eixk'},'eixo':{'eixn','eixj','eixh'},'eixp':{'eixo'},'eixq':{'eixp'},'eixr':{'eixm','eixq'},'eixs':{'eixr'}}.get(name,set())
    abstract(doc,boundaries);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name)
    if mode=='instance':
        from scripts.check_rod_geometry import instantiate
        assert instantiate(d)==[RS]
    slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jsc'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    doc['statements']=[dict(kind='ask',body=dict(kind='call',symbol=name,arguments=args))];return doc,slots

def run(name,args,m,mode='boundary',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(args)==len(slots),(name,len(args),len(slots))
    mm=constants()|m|{n:lambda x=x:x for n,x in zip(slots,args)}
    return evaluate_document(doc,individuals=domain,situations=POINTS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=800000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def unknowns(check,m,names):
    for n in names:
        try:check(m|{n:forbidden})
        except ValueError as e:assert 'Unknown spatial-coverage' in str(e),str(e)
        else:raise AssertionError(('Unknown input accepted',n))
def perturb(check,m,rows,norm=lambda xs:tuple(value(x) for x in xs)):
    count=1;assert check(m)
    for n,rs in rows.items():
        for row in rs:
            assert not check(m|{n:lambda *xs,rs=rs-{row}:norm(xs) in rs}),(n,row);count+=1
            for i in range(len(row)):
                wrong=tuple('wrong' if j==i else x for j,x in enumerate(row))
                assert not check(m|{n:lambda *xs,rs=(rs-{row})|{wrong}:norm(xs) in rs}),(n,i);count+=1
    unknowns(check,m,rows);return count

def numeric():
    cuts,m=numbers();c=cuts.make;r=cuts.read
    def norm(xs):
        def one(x):
            if not isinstance(x,FunctionValue):return value(x)
            if x.parameters==('number',):return r(x)
            if x.parameters==(RS,) and x.result==RS:return tuple(r(x(c(Q(t)))) for t in (0,1,2,3,5))
            forbidden()
        return tuple(one(x) for x in xs)
    return cuts,m,norm

@lru_cache(None)
def point_checks():
    cuts,m,norm=numeric();c=cuts.make;count=0
    def setup(offset=(0,0,0)):
        fs={(ctx,a):FunctionValue((RS,),RS,lambda t,ctx=ctx,i=i:c(Q(i+1+(offset[i] if ctx=='setting' else 0)))) for ctx in ('reference','setting') for i,a in enumerate(('x','y','z'))}
        def raw(p,f,lu,tu,a,ctx):
            if (p,f,lu,tu)!=('point','frame','a','b') or (ctx,a) not in fs:forbidden()
            return fs[ctx,a]
        spans={'reference':(0,2),'setting':(3,5)}
        rows={'eit2':{norm(['point','frame',ctx,'a','b',*(c(Q(x)) for x in spans[ctx]),*(fs[ctx,a] for a in ('x','y','z'))]) for ctx in spans},'eisdd':{('frame','a','b',ctx) for ctx in spans}}
        mm=m|{n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}
        mm|={'eismh':raw,'eisls':lambda f,tu,ctx:c(Q(spans[ctx][0])),'eislt':lambda f,tu,ctx:c(Q(spans[ctx][1]))}
        return mm,rows
    args=['point','frame','reference','setting'];mm,rows=setup();check=lambda model:run('eixj',args,model)
    count+=perturb(check,mm,rows,norm)
    for i in range(3):
        offset=tuple(1 if a==i else 0 for a in range(3));bad,_=setup(offset);assert not check(bad);count+=1
    unknowns(check,mm,('eismh','eisls','eislt','sca','ba'))
    return dict(cases=count,every_position_component_and_complete_static_history_bound=True,different_measurement_periods_allowed=True)

def direction_model(vectors=None):
    cuts,m,norm=numeric();c=cuts.make
    vec={'a':(2,0,0),'b':(7,0,0)}|(vectors or {})
    def component(rec,role):
        if rec not in ('a','b','x','y','z') or role not in ('x','y','z'):forbidden()
        return c(Q(vec.get(rec,(1,0,0))[('x','y','z').index(role)]))
    rows={('a','a','a','a','reference'),('b','a','a','a','setting')}
    m|={'zsa':lambda *xs:xs in rows,'zsb':component}
    return cuts,m,norm,rows

@lru_cache(None)
def orientation_checks():
    count=0;args=['a','a','reference','setting'];domain=('a','b','x','y','z')
    for vec,expected in (({'b':(Q(1,3),0,0)},True),({'b':(-7,0,0)},False),({'b':(0,0,0)},False),({'b':(7,1,0)},False)):
        _,m,_,_=direction_model(vec);assert run('eixk',args,m,domain=domain)==expected;count+=1
    _,m,_,rows=direction_model();check=lambda mm:run('eixk',args,mm,domain=domain)
    for row in rows:
        assert not check(m|{'zsa':lambda *xs,rs=rows-{row}:xs in rs});count+=1
        for i in range(1,5):
            wrong=tuple('wrong' if j==i else x for j,x in enumerate(row))
            assert not check(m|{'zsa':lambda *xs,rs=(rows-{row})|{wrong}:xs in rs});count+=1
    # A hidden opposite record on either side is rejected, even without a coordinate value.
    for ctx in ('reference','setting'):
        _,mm,_,rs=direction_model({'b':(-7,0,0)});rs={(p,'a','a','a',cc) for p,cc in (('a','reference'),('a','setting'),('b',ctx))}
        assert not check(mm|{'zsa':lambda *xs:xs in rs});count+=1
    unknowns(check,m,('zsa','zsb','ba','shv','sca'))
    return dict(cases=count,all_cross_setting_positive_directions_checked=True,opposite_record_rejected_independently_of_zero_coordinate=True)

@lru_cache(None)
def axis_checks():
    cuts,m,norm=numeric();c=cuts.make;count=0
    args=['linea','origin','frame','reference']
    rows={'eiv2':{('linea','origin','guide','frame','reference')},'eipw':{('linea','frame','reference')},'eixj':{('origin','frame','reference','reference')},'eixk':{('linea','frame','reference','reference')}}
    m|={n:lambda *xs,rs=rs:tuple(xs) in rs for n,rs in rows.items()}
    def family(body,f,lu,tu,role,ctx):
        if (body,f,lu,tu,ctx)!=('linea','frame','a','b','reference') or role not in ('x','y','z'):forbidden()
        return FunctionValue(('individual',),FS,lambda p:FunctionValue((RS,),RS,lambda t:c(Q(-2 if p=='guide' and role=='x' else 0))))
    def component(rec,role):
        if rec not in DOMAIN or role not in ('x','y','z'):forbidden()
        return c(Q(3 if role=='x' else 0))
    m|={'eismu':lambda *xs:'guide','eisls':lambda *xs:c(Q(0)),'eislu':family,'zsa':lambda *xs:xs==('a','linea','frame','a','reference'),'zsb':component}
    check=lambda mm:run('eixl',args,mm);count+=perturb(check,m,rows)
    assert not check(m|{'zsb':lambda rec,role:c(Q(1 if role=='y' else 0))});count+=1
    unknowns(check,m,('eismu','eislu','eisls','zsb'))
    return dict(cases=count,own_frame_static_axis_and_actual_material_direction_connected=True,negative_material_guide_allowed=True)

def triad_setup():
    cuts,m,norm=numeric();c=cuts.make
    lines={'x':'linea','y':'lineb','z':'linec'}
    m|={'zbn':lambda f,ctx:'origin','zbo':lambda f,role,ctx:lines[role] if role in lines else forbidden(),'zby':lambda f,ctx:'ruler','eismu':lambda *xs:'guide','eisls':lambda *xs:c(Q(0))}
    rows={'va':{('frame',)},'xc':{('ruler',)},'zbx':{('frame','ruler','reference')},'zbv':{('frame','origin','reference')},'zbw':{('frame',line,a,'reference') for a,line in lines.items()},'zbr':{(line,'origin','reference') for line in lines.values()},'eixl':{(line,'origin','frame','reference') for line in lines.values()},'eiv5':{(lines[a],'origin','guide',lines[b],'origin','guide','frame','reference',Q(0)) for a,b in (('x','y'),('x','z'),('y','z'))}}
    m|={n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}
    # History arguments are already covered in the preceding physical-axis checkpoints.
    m['eigy']=lambda *xs:xs[0] in lines.values() and xs[1:5]==('frame','reference','a','b')
    m['eislt']=lambda *xs:c(Q(2));m['eirh']=lambda *xs:False
    m['eislu']=lambda *xs:FunctionValue(('individual',),FS,lambda p:FunctionValue((RS,),RS,lambda t:c(Q(0))))
    return cuts,m,norm,rows

@lru_cache(None)
def triad_checks():
    cuts,m,norm,rows=triad_setup();check=lambda mm:run('eixm',['frame','reference'],mm)
    count=perturb(check,m,rows,norm)
    for n,row in (('zbw',('frame','hidden','x','reference')),('zbw',('frame','linea','a','reference')),('zbv',('frame','hidden','reference'))):
        assert not check(m|{n:lambda *xs,rs=rows[n]|{row}:xs in rs});count+=1
    for n in ('zbn','zbo','zby'):
        old=m[n];assert not check(m|{n:lambda *xs,old=old:'hidden' if xs[-1]=='initial' else old(*xs)});count+=1
    unknowns(check,m,('zbn','zbo','zby','eigy'))
    return dict(cases=count,all_three_own_frame_axes_exact_roles_and_unique_origin=True,initial_objects_preserved_without_freezing_ruler_position=True)

def transfer_setup():
    cuts,m,norm=numeric();lines={'x':'linea','y':'lineb','z':'linec'};members={'linea':{'a','hidden'},'lineb':{'b'},'linec':{'point'}}
    m|={'zbn':lambda f,ctx:'origin','zbo':lambda f,role,ctx:lines[role],'zby':lambda f,ctx:'ruler','eirh':lambda body,p,ctx:body in members and p in members[body] and ctx in ('reference','setting'),'zcu':lambda p,f,ctx:p in ('point','a') and f=='frame' and ctx in ('reference','setting')}
    rows={'eisnd':{('frame','reference','setting')},'eixm':{('frame',ctx) for ctx in ('reference','setting')},'eixj':{(p,'frame','reference','setting') for p in ('origin','a','hidden','b','point')},'eixk':{(line,'frame','reference','setting') for line in lines.values()}}
    m|={n:lambda *xs,rs=rs:xs in rs for n,rs in rows.items()}
    return cuts,m,norm,rows

@lru_cache(None)
def transfer_checks():
    _,m,_,rows=transfer_setup();check=lambda mm:run('eixn',['frame','reference','setting'],mm)
    count=perturb(check,m,rows)
    original=m['eirh']
    for ctx in ('reference','setting'):
        assert not check(m|{'eirh':lambda body,p,cc,ctx=ctx:False if (body,p,cc)==('linea','hidden',ctx) else original(body,p,cc)});count+=1
    originalspace=m['zcu']
    assert not check(m|{'zcu':lambda p,f,ctx:False if (p,ctx)==('a','setting') else originalspace(p,f,ctx)});count+=1
    for n in ('zbn','zby','zbo'):
        original=m[n];assert not check(m|{n:lambda *xs,original=original:'hidden' if xs[-1]=='setting' else original(*xs)});count+=1
    # Instruments are not in the axis-member coordinate preservation range.
    base=m['eixj'];assert check(m|{'eixj':lambda p,*xs:False if p=='ruler' else base(p,*xs)});count+=1
    unknowns(check,m,('eirh','zcu','zbn','zbo','zby'))
    return dict(cases=count,all_axis_members_positions_and_space_domain_preserved=True,measurement_affiliation_required=True,ruler_relocation_not_forbidden_by_axis_preservation=True)

@lru_cache(None)
def candidate_checks():
    cuts,m,norm=numeric();c=cuts.make
    rows={'eixn':{('frame','reference','setting')},'zcu':{('point','frame',ctx) for ctx in ('reference','setting')},'eixj':{('point','frame','reference','setting')},'eixh':{('point','frame','x',Q(-3),'setting')}}
    m|={n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}
    args=['point','frame','x',c(Q(-3)),'reference','setting'];check=lambda mm:run('eixo',args,mm)
    count=perturb(check,m,rows,norm)
    expected=norm(args);mm=m|{'eixo':lambda *xs:norm(xs)==expected}
    assert run('eixp',args[:-1],mm);count+=1
    assert not run('eixp',args[:-1],m|{'eixo':lambda *xs:False});count+=1
    for i in range(len(expected)):
        wrong=tuple('wrong' if j==i else x for j,x in enumerate(expected))
        assert not run('eixp',args[:-1],m|{'eixo':lambda *xs:norm(xs)==wrong});count+=1
    selected=('point','frame','x',Q(-3),'reference');base=args[:3]+['reference']
    mm=m|{'zcy':lambda *xs:c(Q(-3)),'eixp':lambda *xs:norm(xs)==selected}
    assert run('eixq',base+[c(Q(2))],mm,'instance');count+=1
    assert not run('eixq',base+[c(Q(2))],mm|{'eixp':lambda *xs:norm(xs) in {selected,('point','frame','x',Q(2),'reference')}},'instance');count+=1
    assert not run('eixq',base+[c(Q(-3))],mm|{'eixp':lambda *xs:False},'instance');count+=1
    try:run('eixq',base,mm)
    except ValueError as e:assert 'Finite function domain' in str(e) or 'rational number domain' in str(e),str(e)
    else:raise AssertionError('Global real uniqueness silently sampled')
    unknowns(lambda model:run('eixq',base+[c(Q(-3))],model,'instance'),mm,('zcy','eixp','sca'))
    return dict(cases=count,same_point_and_geometry_before_actual_measurement=True,global_uniqueness_covers_all_measurement_settings=True,full_real_value_domain_not_sampled=True)

@lru_cache(None)
def coverage_checks():
    count=0;space={'a','point'};roles={'x','y','z'}
    rows={'eixm':{('frame','reference')},'eixq':{(p,'frame',a,'reference') for p in space for a in roles}}
    m={n:lambda *xs,rs=rs:xs in rs for n,rs in rows.items()};m['zcu']=lambda p,f,ctx:p in space and (f,ctx)==('frame','reference')
    check=lambda mm:run('eixr',['frame','reference'],mm);count+=perturb(check,m,rows)
    assert not check(m|{'zcu':lambda *xs:False});count+=1
    assert not check(m|{'zcu':lambda p,f,ctx:p in space|{'hidden'} and (f,ctx)==('frame','reference')});count+=1
    rows={'eixr':{('frame','reference'),('moving','reference')}};m={n:lambda *xs,rs=rs:xs in rs for n,rs in rows.items()}
    check=lambda mm:run('eixs',['reference'],mm);count+=perturb(check,m,rows)
    assert not check(m|{'zbm':lambda:'frame'});count+=1
    return dict(cases=count,every_place_and_all_three_components_required=True,empty_or_extended_unmeasured_space_rejected=True,both_distinct_frames_required_without_value_equality=True)

def source_record():
    old=json.loads(read(SOURCE_PARENT));validate_hashes(ROOT,old['source_sha256'])
    result=deepcopy(old);result.update(version='einstein-spatial-coverage-source-reading-v1',reviewer='assistant_text_review_using_preserved_visual_collation')
    result['observations']+=['同じ空間構成の測定配置を、全軸成員と対象地点の位置・正方向・全地点範囲を保持して結ぶ。','各系で全地点と三成分の全組合せを被覆し、配置をまたぐ全有効値候補の一致を要求する。']
    result['remaining']=['u0044からの平行運動の仮定採用と、第一文の思考上の測定済み設定・座標表記の本文統合','時計配置点の局所時刻と§1の全信号試行による同期','追加設定指示、時刻表記と参照を含むu0045の全体意味判断']
    paths=set(old['source_sha256'])|{SOURCE_PARENT,DOC};result['source_sha256']={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};return result

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements']==old.document['statements'] and len(new.document['statements'])==270
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read(PRIOR));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[268,269])==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);assert json.loads(read(ANNOTATIONS))['entries']==json.loads(read('data/coordinate-measurement-identifiers-v1.json'))['entries']
    doc=parse(read(CORE));assert not doc['statements']
    for style in ('compact','full'):
        body=format_graph(doc,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=len(MEANINGS),new_primitives=1,preserved_statements=270,prior_meanings_and_reviews_preserved=True,whole_unit_completion=False)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:fn() for n,fn in [('points',point_checks),('orientation',orientation_checks),('axis',axis_checks),('triad',triad_checks),('transfer',transfer_checks),('candidate',candidate_checks),('coverage',coverage_checks),('structure',structure_checks)]}
    source=source_record();paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source['source_sha256'])|{SOURCE,DOC,PRIOR,*DEPENDENCIES,'scripts/compose_spatial_coverage.py','scripts/check_spatial_coverage.py','tests/test_spatial_coverage.py','scripts/check_moving_trip_geometry.py','scripts/check_coordinate_correspondence.py','scripts/check_material_relative_frame.py','scripts/check_rod_geometry.py','scripts/check_rod_methods.py','scripts/check_tau_differential.py','scripts/compose_coordinate_measurement.py','scripts/compose_axis_projection.py','scripts/compose_material_axes.py','scripts/compose_moving_axes.py','scripts/compose_rod_methods.py','scripts/compose_material_relative_frame.py','scripts/compose_limits.py'}
    return dict(status='all_spatial_components_across_preserved_settings_checked',document=FULL,**results,alignment=dict(segments=[dict(unit=source['unit'],unit_sha256=source['unit_sha256'],range=source['range'],source=source['text'],definitions=list(MEANINGS),status='explicit_interpretive_annotation')]),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=source['remaining'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
