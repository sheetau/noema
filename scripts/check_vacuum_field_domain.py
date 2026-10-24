"""Check material-free regions, field calibration and the six-equation boundary."""
from functools import lru_cache
from itertools import product
from copy import deepcopy
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
from scripts.check_material_relative_frame import arithmetic,RS
from scripts.check_moving_trip_geometry import NUM
from scripts.check_clock_site_time import perturb,unknowns,forbidden
from scripts.compose_vacuum_field_domain import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,MEANINGS,build

DOC='docs/vacuum-field-domain-v1.md'
SOURCE='data/einstein-vacuum-field-obligations-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json'
PRIOR='data/einstein-electrodynamic-part-u0151-review-v1.json'
DEPENDENCIES=('reports/field-equations-v1.json','reports/electric-action-v1.json','reports/magnetic-action-v1.json','reports/carrier-relative-motion-v1.json')
AXES=('x','y','z','time')
DOMAIN=AXES+('frame','length','duration','charge','electricunit','magneticunit','force','body','other')
PS=dict(kind='function',parameters=['individual'],result=RS)
TAU=dict(kind='function',parameters=[RS]*4,result=RS)
POINTS=((Q(1),Q(2),Q(3),Q(4)),(Q(5),Q(6),Q(7),Q(8)),(Q(9),Q(10),Q(11),Q(12)))


def sample_points(node):
    if isinstance(node,list):return [sample_points(x) for x in node]
    if not isinstance(node,dict):return node
    if node.get('kind') in ('exists','forall') and node.get('sort')==PS:
        def replace(x,term):
            if isinstance(x,list):return [replace(y,term) for y in x]
            if not isinstance(x,dict):return x
            if x.get('kind')=='variable' and x['name']==node['variable']:return deepcopy(term)
            return {k:replace(y,term) for k,y in x.items()}
        return dict(kind='or' if node['kind']=='exists' else 'and',arguments=[sample_points(replace(node['body'],dict(kind='call',symbol=n,arguments=[]))) for n in ('jvfdone','jvfdtwo')])
    return {k:sample_points(x) for k,x in node.items()}


@lru_cache(None)
def fixture(name,mode='sample'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    abstract(doc,NUM|({'s5y'} if name=='ejsp' else set()))
    doc=extract_document(doc,roots=[name],statement_indices=[]).document
    if mode=='sample':doc=sample_points(doc)
    doc['declarations'][:0]=[dict(kind='primitive',name=n,parameters=[],result=PS) for n in ('jvfdone','jvfdtwo')]
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[]
    for i,p in enumerate(d['parameters']):
        n='jvfd'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    doc['statements']=[dict(kind='ask',body=dict(kind='call',symbol=name,arguments=[dict(kind='call',symbol=n,arguments=[]) for n in slots]))]
    return doc,slots


def run(name,args,m,mode='sample'):
    doc,slots=fixture(name,mode);assert len(args)==len(slots)
    mm={n:lambda x=x:x for n,x in zip(('yn','yo','yp','zc7'),AXES)}|m|{n:lambda x=x:x for n,x in zip(slots,args)}
    return evaluate_document(doc,individuals=DOMAIN,situations=('context','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=500000,memoize_definitions=True,memoize_expressions=True)[0]['value']


def setup():
    cuts,m=arithmetic();c=lambda x:cuts.make(Q(x));r=cuts.read
    m['bg']=lambda a,b:r(a)<r(b)
    point=lambda xs:FunctionValue(('individual',),RS,lambda role:c(dict(zip(AXES,xs)).get(role,0)))
    region=lambda selected:FunctionValue(tuple([RS]*4),'truth',lambda *xs:tuple(map(r,xs)) in selected)
    def field(values):
        return FunctionValue(('individual',),TAU,lambda role:FunctionValue(tuple([RS]*4),RS,lambda *xs:c(dict(zip(AXES[:3],values)).get(role,0))))
    pts=[point(p) for p in POINTS];reg=region(set(POINTS[:2]));electric=field((1,2,3));magnetic=field((4,5,6))
    def one(x):
        if not isinstance(x,FunctionValue):return x
        if x.parameters==('number',):return r(x)
        if x.parameters==('individual',) and x.result==RS:return ('point',tuple(r(x(a)) for a in AXES))
        if x.parameters==('individual',) and x.result==TAU:return ('field',tuple(r(x(a)(*[c(y) for y in p])) for p in POINTS for a in AXES[:3]))
        if x.parameters==tuple([RS]*4) and x.result=='truth':return ('region',tuple(x(*[c(y) for y in p]) for p in POINTS))
        raise ValueError('Unknown field-domain function fingerprint')
    norm=lambda xs:tuple(one(x) for x in xs)
    relation=lambda rows:lambda *xs:norm(xs) in rows
    chart=['frame','length','duration','context']
    rows={'va':{('frame',)},'ti':{('length',)},'ci':{('duration',)},'eisdd':{tuple(chart)}}
    m|={n:relation(rs) for n,rs in rows.items()}|{'eiro':lambda *xs:False,'jvfdone':lambda:pts[0],'jvfdtwo':lambda:pts[1]}
    fs=chart+[reg,'charge','electricunit','magneticunit','force',c(2),c(Q(1,2)),electric,magnetic]
    fieldrows={'znn':{norm(('frame',electric,magnetic,reg,'context'))},'eirn':{norm(('frame',electric,'electricunit','context')),norm(('frame',magnetic,'magneticunit','context'))},'eirm':{('charge','electricunit','force',Q(2),'context')},'eiru':{('frame','charge','length','duration','magneticunit','force',Q(1,2),'context')}}
    m|={n:relation(rs) for n,rs in fieldrows.items()}
    return dict(c=c,r=r,m=m,points=pts,region=region,norm=norm,relation=relation,chart=chart,rows=rows,fields=fs,fieldrows=fieldrows)


@lru_cache(None)
def point_checks():
    s=setup();m=s['m'];p=s['points'][0];args=s['chart']+[p];norm=s['norm'];rel=s['relation']
    assert run('ejsk',args,m);count=1
    occupied=('body','frame','context','length','duration',*POINTS[0])
    assert not run('ejsk',args,m|{'eiro':rel({occupied})});count+=1
    # Change each reference/coordinate slot: occupation then belongs elsewhere.
    for slot in range(1,len(occupied)):
        changed=list(occupied);changed[slot]='other' if slot<5 else changed[slot]+1
        assert run('ejsk',args,m|{'eiro':rel({tuple(changed)})});count+=1
    another=('other',*occupied[1:]);assert not run('ejsk',args,m|{'eiro':rel({another})});count+=1
    unknowns(lambda mm:run('ejsk',args,mm),m,('eiro',))
    assert not run('ejsk',args,m|{'ba':lambda x:False});count+=1
    for role in ('yo','yp','zc7'):
        assert not run('ejsk',args,m|{role:lambda:'x'});count+=1
    reg=s['fields'][4]
    assert run('ejsj',[p,reg],m);assert not run('ejsj',[s['points'][2],reg],m);count+=2
    count+=perturb(lambda mm:run('ejsl',s['chart'],mm),m,s['rows'],norm)
    bad=s['chart'].copy();bad[2]='length'
    assert not run('ejsl',bad,m|{n:lambda *xs:True for n in s['rows']});count+=1
    return dict(cases=count,same_body_frame_units_coordinates_and_time=True,all_material_objects_not_only_charged_ones=True,unknown_occupancy_rejected=True)


@lru_cache(None)
def region_checks():
    s=setup();m=s['m'];rel=s['relation'];count=0
    for active,occupied in product(product((False,True),repeat=2),repeat=2):
        reg=s['region']({p for p,on in zip(POINTS,active) if on})
        rows={('body','frame','context','length','duration',*p) for p,on in zip(POINTS,occupied) if on}
        expected=any(active) and not any(a and b for a,b in zip(active,occupied))
        assert run('ejsm',s['chart']+[reg],m|{'eiro':rel(rows)})==expected;count+=1
    outside={('body','frame','context','length','duration',*POINTS[2])}
    assert run('ejsm',s['chart']+[s['fields'][4]],m|{'eiro':rel(outside)});count+=1
    unknowns(lambda mm:run('ejsm',s['chart']+[s['fields'][4]],mm),m,('eiro','eisdd'))
    try:run('ejsm',s['chart']+[s['fields'][4]],m,'native')
    except ValueError as e:assert 'rational number domain' in str(e) or 'Finite function domain' in str(e),str(e)
    else:raise AssertionError('Full coordinate-function domain silently sampled')
    return dict(cases=count,nonempty_region_and_all_selected_points=True,outside_matter_allowed=True,native_full_coordinate_domain_refused=True,two_points_are_explicit_diagnostic_substitution=True)


@lru_cache(None)
def field_checks():
    s=setup();m=s['m'];args=s['fields'];norm=s['norm'];rel=s['relation']
    count=perturb(lambda mm:run('ejsn',args,mm),m,s['fieldrows'],norm)
    for slot in (9,10):
        for value in (0,-1):
            bad=args.copy();bad[slot]=s['c'](value)
            assert not run('ejsn',bad,m|{'eirm':lambda *xs:True,'eiru':lambda *xs:True});count+=1
    assert run('ejso',args,m);count+=1
    assert not run('ejso',args,m|{'eiro':rel({('body','frame','context','length','duration',*POINTS[1])})});count+=1
    # Both physical fields are nonzero at both diagnostic points; vacuum does
    # not force them to vanish or require a real test charge to occupy space.
    assert all(s['r'](f(a)(*[s['c'](x) for x in p]))!=0 for f in args[-2:] for a in AXES[:3] for p in POINTS[:2])
    return dict(cases=count,same_field_assignment_units_and_force_conventions=True,positive_conversions_required=True,nonzero_electric_and_magnetic_fields_allowed_in_vacuum=True)


@lru_cache(None)
def equation_checks():
    s=setup();m=s['m'];args=s['fields'];norm=s['norm'];rel=s['relation'];light=s['c'](4)
    rows={'s5y':{norm((args[-2],args[-1],args[4],light))}}
    m|={n:rel(rs) for n,rs in rows.items()}
    count=perturb(lambda mm:run('ejsp',args+[light],mm),m,rows,norm)
    assert not run('ejsp',args+[light],m|{'eiro':rel({('body','frame','context','length','duration',*POINTS[0])})});count+=1
    # Native six algebraic curl balances, independent of physical tagging.
    for speed in (1,4):
        e={(a,b):Q(i-j) for i,a in enumerate(AXES[:3]) for j,b in enumerate(AXES)}
        h={(a,b):Q(i+2*j) for i,a in enumerate(AXES[:3]) for j,b in enumerate(AXES)}
        for i,a in enumerate(AXES[:3]):
            b=AXES[(i+1)%3];c=AXES[(i+2)%3]
            e[a,'time']=speed*(h[c,b]-h[b,c]);h[a,'time']=speed*(e[b,c]-e[c,b])
        jet=lambda table:FunctionValue(('individual','individual'),RS,lambda a,b:s['c'](table.get((a,b),0)))
        assert run('s5w',[s['c'](speed),jet(e),jet(h)],m);count+=1
        for which,a in product((0,1),AXES[:3]):
            ee=e.copy();hh=h.copy();(ee if which==0 else hh)[a,'time']+=1
            assert not run('s5w',[s['c'](speed),jet(ee),jet(hh)],m);count+=1
    return dict(cases=count,six_equations_use_same_fields_region_and_light=True,native_six_curl_balances_checked=True,divergence_and_transformation_not_inferred=True)


@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));units=inv['units'][151:155]
    assert units[0]['id']=='einstein-1905:u0152'
    for u in units:assert digest(u['text'].encode())==u['text_sha256']
    return dict(version='einstein-vacuum-field-obligations-v1',kind='dependency_scope_not_semantic_review',units=[dict(unit=u['id'],unit_sha256=u['text_sha256'],text=u['text']) for u in units],requirements=['見出しの方程式変換と起電力の性質という二主題を保持する。','真空領域と物理的な二場・同じ単位・六式を接続する。','本文適用時に光速度Vの指示と、Maxwell-Hertzの式の同定・見出しの役割を結ぶ。'],resolved_dependencies=list(MEANINGS),unresolved=['u0152の二主題と見出し構造への接続','Maxwell-Hertzという式の同定と変換の研究対象','光速度の物理的指示と現在の場・領域への適用','一般の磁場中の運動に伴う起電力と性質・説明という主題','u0153以降の仮定・式・場の成分の全体の意味判断'],whole_unit_reviewed=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in (INVENTORY,DOC)})


@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert len(new.document['statements'])==357 and new.document['statements']==old.document['statements']
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    assert not any(d['kind']=='primitive' for d in new.document['declarations'][len(old.document['declarations']):])
    prior=json.loads(read(PRIOR));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[356])==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS)
    core=parse(read(CORE));names={d['name'] for d in core['declarations']}
    assert set(MEANINGS)|{'eiro','znn','eirn','eirm','eiru','s5y','s5u','s5t','s5w'}<=names
    assert not names&{'znk','znl','znm','eisca','s6r','s6o'}
    for style in ('compact','full'):
        body=format_graph(core,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core
    assert source_record()==json.loads(read(SOURCE))
    return dict(new_definitions=len(MEANINGS),new_primitives=0,all_357_statements_and_prior_judgments_preserved=True,physical_input_and_math_conditions_separate=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')


@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('point',point_checks),('region',region_checks),('field',field_checks),('equations',equation_checks),('structure',structure_checks)]}
    helpers=('compose_electrodynamic_part_heading','compose_material_relative_frame','compose_field_equations','compose_limits','check_clock_site_time','check_coordinate_correspondence','check_material_relative_frame','check_moving_trip_geometry','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|{SOURCE,DOC,INVENTORY,PRIOR,*DEPENDENCIES,'scripts/compose_vacuum_field_domain.py','scripts/check_vacuum_field_domain.py','tests/test_vacuum_field_domain.py',*(f'scripts/{n}.py' for n in helpers)}
    return dict(status='material_free_region_and_physical_field_dependencies_connected',document=FULL,**results,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=source_record()['unresolved'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
