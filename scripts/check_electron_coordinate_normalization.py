"""Check coordinate representatives, transported jets and free-origin boosts."""
from copy import deepcopy
from functools import lru_cache
from fractions import Fraction as Q
from math import isqrt
import json
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts import check_point_particle_dynamics as old
from scripts.compose_electron_coordinate_normalization import *

DOC='docs/electron-coordinate-normalization-v1.md';SOURCE='data/einstein-electron-coordinate-obligations-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json'
FACSIMILES=('artifacts/written-facsimiles-v1/einstein-1905-unlp.pdf','artifacts/written-facsimiles-v1/einstein-p917-0.jpg','artifacts/written-facsimiles-v1/einstein-p918-0.jpg')
DEPENDENCIES=('reports/electron-moving-law-task-v1.json','reports/comoving-wording-v1.json','reports/material-acceleration-v1.json')
AXES=('x','y','z','t');CONSTANTS=dict(zip(ROLES,AXES));PEOPLE=(*AXES,'first','second','length','duration','other')
BOUNDS=old.old.NUM|{'bg','be','sjd','sje','soy','szi','ejsl'}
ROTATIONS=(
 ((1,0,0),(0,1,0),(0,0,1)),
 ((0,1,0),(0,0,1),(1,0,0)),
 ((Q(3,5),Q(4,5),0),(Q(-4,5),Q(3,5),0),(0,0,1)),
 ((Q(1,3),Q(2,3),Q(2,3)),(Q(2,3),Q(1,3),Q(-2,3)),(Q(-2,3),Q(2,3),Q(-1,3))),
)
POINTS=((0,0,0,0),(1,0,0,0),(0,1,0,0),(0,0,1,0),(0,0,0,1),(1,2,-3,4),(Q(1,3),-2,5,Q(-2,3)))
dot=lambda a,b:sum(Q(x)*Q(y) for x,y in zip(a,b))
rot=lambda matrix,point:tuple(dot(row,point[:3]) for row in matrix)+(Q(point[3]),)
norm=lambda matrix,origin,point:rot(matrix,tuple(Q(a)-Q(b) for a,b in zip(point,origin)))
flatten=lambda matrix:[x for row in matrix for x in row]
forbidden=old.forbidden

@lru_cache(None)
def core():return parse(read(CORE))

@lru_cache(None)
def fixture(root):
    doc=extract_document(core(),roots=[root],statement_indices=[]).document
    for i,d in enumerate(doc['declarations']):
        if d['kind']=='definition' and d['name'] in BOUNDS:doc['declarations'][i]=dict(kind='primitive',name=d['name'],parameters=[p['sort'] for p in d['parameters']],result=d['result'])
    doc=extract_document(doc,roots=[root],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==root);slots=[]
    for i,p in enumerate(d['parameters']):
        name='jcnarg'+number_word(i);slots.append(name);doc['declarations'].append(dict(kind='primitive',name=name,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=root,arguments=[dict(kind='call',symbol=n,arguments=[]) for n in slots])
    if d['result']!='truth':
        doc['declarations'].append(dict(kind='primitive',name='jcncapture',parameters=[d['result']],result='truth'));expr=dict(kind='call',symbol='jcncapture',arguments=[expr])
    doc['declarations'].sort(key=lambda d:d['kind']!='primitive');doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(root,values,m):
    doc,slots=fixture(root);assert len(values)==len(slots),(root,len(values),len(slots));captured=[]
    def capture(x):captured.append(x);return True
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|m|{n:lambda x=x:x for n,x in zip(slots,values)}|{'jcncapture':capture}
    result=evaluate_document(doc,individuals=PEOPLE,situations=('case','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=700000,memoize_definitions=True,memoize_expressions=True)[0]['value']
    return captured[0] if captured else result

def setup():
    cuts,m=old.old.numbers();c,r=cuts.make,cuts.read
    def beta(V,s):
        V,s=r(V),r(s);square=V*V-s*s
        if V<=0 or square<=0:raise ValueError('Unknown or inadmissible boost root')
        a,b=isqrt(square.numerator),isqrt(square.denominator)
        if a*a!=square.numerator or b*b!=square.denominator:raise ValueError('Unknown irrational boost root')
        return c(V/Q(a,b))
    m|={'soy':beta,'sjd':lambda x:c(1/r(x))}
    point=lambda xs:old.old.point(c,tuple(map(Q,xs)))
    values=lambda p:tuple(r(p(a)) for a in AXES)
    return c,r,m,point,values

@lru_cache(None)
def rotation_checks():
    c,r,m,p,pv=setup();cases=0
    for matrix in ROTATIONS:
        vals=list(map(c,flatten(matrix)));assert run('ek43',vals,m);cases+=1
        for i in range(9):
            wrong=vals.copy();wrong[i]=c(r(wrong[i])+1);assert not run('ek43',wrong,m);cases+=1
        mirror=[*matrix[:2],tuple(-Q(x) for x in matrix[2])]
        assert not run('ek43',list(map(c,flatten(mirror))),m);cases+=1
        for speed in (0,3,7):
            velocity=tuple(Q(speed)*Q(x) for x in matrix[0])+(0,)
            assert run('ek5c',vals+[p((2,-1,5,3)),p(velocity),c(speed)],m);cases+=1
            assert not run('ek5c',vals+[p((2,-1,5,3)),p(velocity),c(speed+1)],m);cases+=1
            if speed:
                assert not run('ek5b',vals+[p(velocity),c(-speed)],m);cases+=1
    for symbol in ('ba','shv','bd','sca'):
        old.old.reject(lambda:run('ek43',list(map(c,flatten(ROTATIONS[2]))),m|{symbol:forbidden}),unknown=True);cases+=1
    return dict(cases=cases,proper_orthogonal_rotations_not_reflections_or_scalings=True,all_nine_entries_distinguished=True,zero_speed_has_no_selected_direction=True)

@lru_cache(None)
def map_checks():
    c,r,m,p,pv=setup();cases=0
    for matrix in ROTATIONS:
        vals=list(map(c,flatten(matrix)))
        for origin in ((0,0,0,0),(2,-1,5,3),(Q(1,2),3,0,-2)):
            assert pv(run('ek47',vals+[p(origin),p(origin)],m))==(0,0,0,0);cases+=1
            for point in POINTS:
                result=run('ek47',vals+[p(origin),p(point)],m)
                assert pv(result)==norm(matrix,origin,point);cases+=1
                assert pv(run('ek5a',vals+[p(origin),result],m))==point;cases+=1
                back=run('ek5a',vals+[p(origin),p(point)],m)
                assert pv(run('ek47',vals+[p(origin),back],m))==point;cases+=1
            a,b=POINTS[-2:];left=pv(run('ek47',vals+[p(origin),p(a)],m));right=pv(run('ek47',vals+[p(origin),p(b)],m))
            delta=tuple(Q(x)-Q(y) for x,y in zip(a,b));newdelta=tuple(x-y for x,y in zip(left,right))
            assert dot(delta[:3],delta[:3])==dot(newdelta[:3],newdelta[:3]) and delta[3]==newdelta[3];cases+=1
    return dict(cases=cases,origin_event_maps_to_four_zeroes=True,both_inverse_orders_and_spatial_distance_preserved=True,time_origin_shift_not_time_scaling=True)

@lru_cache(None)
def history_checks():
    c,r,m,p,pv=setup();cases=0
    # Registered quadratic coordinate histories. Derivatives are obtained from
    # coefficients, not inferred by finite differences through sample values.
    coefficients=((2,1,2),(-1,-3,1),(4,2,-1))
    position=lambda t:tuple(a+b*t+d*t*t for a,b,d in coefficients)+(t,)
    velocity=lambda t:tuple(b+2*d*t for a,b,d in coefficients)+(0,)
    acceleration=tuple(2*d for a,b,d in coefficients)+(0,)
    curve=old.fn(old.sort(CURVE),lambda t:p(position(r(t))))
    domain=old.fn(old.sort(DOMAIN),lambda t:-4<r(t)<4)
    profiles=[old.fn(old.sort(typ),lambda t,b=b,d=d:c(b+2*d*r(t))) for (name,typ),(a,b,d) in zip(PROFILES,coefficients)]
    for matrix in ROTATIONS:
        vals=list(map(c,flatten(matrix)))
        for epoch in (-1,0,2):
            origin=position(Q(epoch));normal=vals+[p(origin)]
            d=run('ek5d',[domain,p(origin)],m);track=run('ek5e',normal+[curve],m);speeds=run('ek5f',normal+profiles,m)
            assert pv(track(c(0)))==(0,0,0,0);cases+=1
            for t in (-6,-3,-1,0,1,3,6):
                assert d(c(t))==(-4<t+epoch<4);cases+=1
                assert pv(track(c(t)))==norm(matrix,origin,position(Q(t+epoch)));cases+=1
                assert pv(speeds(c(t)))==rot(matrix,velocity(Q(t+epoch)));cases+=1
            assert pv(run('ek5g',vals+list(map(c,acceleration[:3])),m))==rot(matrix,acceleration);cases+=1
    return dict(cases=cases,shifted_domain_and_full_curve_use_same_time_origin=True,velocity_functions_and_acceleration_use_same_rotation=True,analytical_polynomial_coefficients_not_sample_inferred_derivatives=True,general_chain_rule_proved=False)

@lru_cache(None)
def boost_checks():
    c,r,m,p,pv=setup();cases=0
    def transform(point,V,s):
        b=r(m['soy'](c(V),c(s)));x,y,z,t=map(Q,point)
        return (b*(x-s*t),y,z,b*(t-s*x/(V*V)))
    for V,s in ((5,0),(5,3),(5,4),(13,5)):
        beta=r(m['soy'](c(V),c(s)));bs=[c(V),c(s)]
        for offset in ((0,0,0,0),(2,-1,3,4),(-3,5,1,Q(1,2))):
            for point in POINTS:
                expected=tuple(a+Q(b) for a,b in zip(transform(point,Q(V),Q(s)),offset))
                result=run('ek5i',bs+[p(offset),p(point)],m);assert pv(result)==expected;cases+=1
                assert pv(run('ek5j',bs+[p(offset),result],m))==point;cases+=1
                inverse=run('ek5j',bs+[p(offset),p(point)],m);assert pv(run('ek5i',bs+[p(offset),inverse],m))==point;cases+=1
            assert pv(run('ek5i',bs+[p(offset),p((0,0,0,0))],m))==offset;cases+=1
        at=bs+[p((s,0,0,0))];assert run('ek5m',at,m);cases+=1
        assert pv(run('ek5l',at,m))==(0,0,0,0);cases+=1
        assert r(run('ek5k',at,m))==1/beta;cases+=1
    # For x=3t+t²,y=t²,z=-t², transform each polynomial coefficient exactly.
    V,s=Q(5),Q(3);source=((0,0,0,0),(3,0,0,1),(1,1,-1,0))
    target=tuple(transform(coefficient,V,s) for coefficient in source)
    for t in (-1,0,1):
        tangent=tuple(source[1][i]+2*t*source[2][i] for i in range(4))
        transformed=tuple(target[1][i]+2*t*target[2][i] for i in range(4))
        args=[c(V),c(s),p(tangent[:3]+(0,))]
        assert run('ek5m',args,m);cases+=1
        assert r(run('ek5k',args,m))==transformed[3];cases+=1
        answer=pv(run('ek5l',args,m));assert answer==tuple(x/transformed[3] for x in transformed[:3])+(0,);cases+=1
        assert (answer[:3]==(0,0,0))==(t==0);cases+=1
    assert not run('ek5m',[c(5),c(-3),p((0,0,0,0))],m);cases+=1
    assert not run('ek5m',[c(5),c(3),p((9,0,0,0))],m);cases+=1
    assert not run('s45',[c(5),c(5)],m);cases+=1
    # A returned function is lazy: force its coordinates before checking rejection.
    old.old.reject(lambda:pv(run('ek5l',[c(5),c(3),p((3,0,0,0))],m|{'soy':forbidden})),unknown=True);cases+=1
    return dict(cases=cases,all_four_comoving_origins_remain_free=True,exact_polynomial_tangent_divided_by_coordinate_time_rate=True,instant_rest_all_three_axes_not_neighborhood_rest=True,subluminal_nonnegative_boost_domain_explicit=True)

@lru_cache(None)
def physical_checks():
    c,r,m,p,pv=setup();cases=0;matrix=ROTATIONS[3];origin=(2,-1,5,3);vals=list(map(c,flatten(matrix)))
    rows={('first','length','duration','case'),('second','length','duration','case')}
    expected=tuple(norm(matrix,origin,point) for point in POINTS)
    def mapping(first,second,length,duration,fn,context):
        return (first,second,length,duration,context)==('first','second','length','duration','case') and tuple(pv(fn(p(point))) for point in POINTS)==expected
    mm=m|{'ejsl':lambda *xs:xs in rows,'eisqt':mapping};values=['first','second','length','duration','case',*vals,p(origin)]
    assert run('ek5h',values,mm);cases+=1
    for row in rows:
        assert not run('ek5h',values,mm|{'ejsl':lambda *xs:xs in rows-{row}});cases+=1
    for i in range(5):
        wrong=values.copy();wrong[i]='other';assert not run('ek5h',wrong,mm);cases+=1
    for matrix2 in ROTATIONS[:3]:
        assert not run('ek5h',values[:5]+list(map(c,flatten(matrix2)))+[p(origin)],mm);cases+=1
    for axis in range(4):
        changed=tuple(x+1 if i==axis else x for i,x in enumerate(origin));assert not run('ek5h',values[:-1]+[p(changed)],mm);cases+=1
    for name in ('ejsl','eisqt'):
        old.old.reject(lambda:run('ek5h',values,mm|{name:forbidden}),unknown=True);cases+=1
    return dict(cases=cases,both_calibrated_frames_and_same_physical_coordinate_map_required=True,all_four_origin_components_and_units_distinguished=True,numerical_map_alone_not_physical_correspondence=True)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));u=inv['units'][244];assert u['id']=='einstein-1905:u0245';assert digest(u['text'].encode())==u['text_sha256']
    ms=[m for m in inv['math'] if m['id'] in u['math_ids']]
    for m in ms:assert digest(m['mathml'].encode())==m['sha256']
    assert len(ms)==7
    return dict(version='einstein-electron-coordinate-obligations-v1',unit=u['id'],text=u['text'],unit_sha256=u['text_sha256'],math=ms,semantic_completion=False,observations=['原刊917頁末のKoordinaten-と918頁冒頭sprungを視認した。固定在庫の綴りを変更せず、後続のt=x=y=z=0の指定から座標原点と読む。','u0245の一般性を保つ仮定の選択と採用、指定した同じ瞬間の原点とX方向のv、t=0、同じvでの一定並進系kへの瞬間静止、明白さを照合した。','918頁では後続の文がKの零四座標に対するkの零四座標を追加で指定する。その指定をu0245の共動系へ先取りしない。','今回は回転と原点移動、時間領域・曲線・速度・加速度の共通変換、原点ずれを残すboostと局所速度の依存群。一般性の物理的範囲、同じ粒子の両系の完全な履歴と微分、著者提示と全文判断は未完。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in (INVENTORY,*FACSIMILES,DOC)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    before=load_catalog(ROOT,PARENT_BASIS);after=load_catalog(ROOT,BASIS)
    assert after.document['statements']==before.document['statements'] and len(after.document['statements'])==417
    assert after.document['declarations'][:len(before.document['declarations'])]==before.document['declarations']
    assert all(after.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in before.entries.items())
    assert selection_binding(after,[415,416])==selection_binding(before,[415,416]);load_annotations(ROOT,BASIS,ANNOTATIONS)
    assert json.loads(read(ANNOTATIONS))['entries']==json.loads(read('data/electron-moving-law-task-identifiers-v1.json'))['entries']
    assert len(MEANINGS)==18
    for path in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(path))['source_sha256'])
    for style in ('compact','full'):
        body=format_graph(core(),style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core()
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=18,new_primitives=0,new_statements=0,all_417_prior_statements_and_meanings_preserved=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('rotation',rotation_checks),('map',map_checks),('history',history_checks),('boost',boost_checks),('physical',physical_checks),('structure',structure_checks)]}
    helpers=('compose_limits','compose_material_relative_frame','compose_material_velocity','compose_material_acceleration','compose_field_transform','compose_point_particle_dynamics','check_point_particle_dynamics','check_attached_material_charge','check_body_rest_field_method','check_material_relative_frame','check_material_acceleration','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,*DEPENDENCIES,'scripts/compose_electron_coordinate_normalization.py','scripts/check_electron_coordinate_normalization.py','tests/test_electron_coordinate_normalization.py',*(f'scripts/{n}.py' for n in helpers)}
    return dict(status='electron_representative_and_free_origin_boost_dependencies_checked',document=FULL,**results,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
