"""Check current-field bindings, extensional notation and attributed assumptions."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
from fractions import Fraction as Q
import json,re,xml.etree.ElementTree as ET
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import FunctionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_moving_trip_geometry import NUM
from scripts.check_material_relative_frame import RS
from scripts.check_clock_site_time import relation,perturb,unknowns,forbidden
from scripts.check_vacuum_field_domain import setup as field_setup,sample_points,PS,TAU,AXES,POINTS,DOMAIN as FIELD_DOMAIN
from scripts.compose_vacuum_equation_assumption import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,INDEX,PARAMS,MEANINGS,PRIMITIVES,build

DOC='docs/vacuum-equation-assumption-v1.md';SOURCE='data/einstein-vacuum-equation-assumption-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json'
FACSIMILES=('artifacts/written-facsimiles-v1/einstein-1905-unlp.pdf','artifacts/written-facsimiles-v1/einstein-1905-unlp-p907-0.jpg')
PRIOR='data/einstein-sixth-section-u0152-review-v1.json'
DEPENDENCIES=('reports/field-equations-v1.json','reports/vacuum-field-domain-v1.json','reports/sixth-section-heading-v1.json')
CONSTANTS={'ra':'frame','ta':'length','rb':'duration','tb':'speedunit','rd':'author','eirf':'paper','ri':'context','znp':'intro','zno':'scope','eisph':'heading','eispf':'designation','eispj':'electricname','eispk':'magneticname','eispl':'display','eispm':'explanation',**dict(zip(('yn','yo','yp','zc7'),AXES))}
DOMAIN=tuple(dict.fromkeys((*FIELD_DOMAIN,*CONSTANTS.values())))


def witness_sorts(x):
    if isinstance(x,list):return [witness_sorts(y) for y in x]
    if not isinstance(x,dict):return x
    out={k:witness_sorts(v) for k,v in x.items()}
    if x.get('kind') in ('exists','forall') and x.get('sort')==RS:out['sort']='individual'
    return out


@lru_cache(None)
def fixture(name,mode='sample'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    bounds=NUM|({'ejsx'} if name=='ejsy' and mode=='witness' else set())
    if name=='ejsz':bounds|={'ejsy','ejsm','s5y'}
    if name in ('ejs4','ejs5'):bounds.add('ejsy')
    if name=='ejs6':bounds.add('ejsz')
    abstract(doc,bounds);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    if mode=='sample':
        doc=sample_points(doc)
        doc['declarations'][:0]=[dict(kind='primitive',name=n,parameters=[],result=PS) for n in ('jvfdone','jvfdtwo')]
    if mode=='witness':
        doc=witness_sorts(doc)
        for d in doc['declarations']:
            if d['name']=='ejsx':d['parameters']=['individual']*6+['situation']
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[]
    for i,p in enumerate(d['parameters']):
        n='jvea'+number_word(i);slots.append((n,p['sort']));doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=name,arguments=[dict(kind='call',symbol=n,arguments=[]) for n,_ in slots])
    if d['result']=='content':expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='ri',arguments=[]))
    if not any(x['name']=='ri' for x in doc['declarations']):doc['declarations'].append(dict(kind='primitive',name='ri',parameters=[],result='situation'))
    doc['statements']=[dict(kind='ask',body=expr)]
    return doc,slots


def run(name,args,m,mode='sample',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(args)==len(slots)
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|m
    for (n,s),x in zip(slots,args):
        if isinstance(s,dict) and callable(x) and not isinstance(x,FunctionValue):x=FunctionValue(tuple(s['parameters']),s['result'],x)
        mm[n]=lambda x=x:x
    def missing(symbol):
        def reject(*xs):raise ValueError('Unknown vacuum-equation input: '+symbol)
        return reject
    return evaluate_document(doc,individuals=domain,situations=('context','other'),primitives={d['name']:mm.get(d['name'],missing(d['name'])) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=600000,memoize_definitions=True,memoize_expressions=True)[0]['value']


def setup():
    s=field_setup();f=s['fields'];m=s['m']|{'znk':lambda:f[4],'znl':lambda:f[-2],'znm':lambda:f[-1],'tc':lambda:s['c'](2),'eiscc':relation({('frame','length','duration','speedunit','context')})}
    s['m']=m;return s


@lru_cache(None)
def physical_checks():
    s=setup();m=s['m'];args=s['fields'][5:11]+['context'];norm=s['norm']
    rows=s['rows']|s['fieldrows']|{'eiscc':{('frame','length','duration','speedunit','context')}}
    count=perturb(lambda mm:run('ejsx',args,mm),m,rows,norm)
    for symbol in ('ra','ta','rb','tb'):
        assert not run('ejsx',args,m|{symbol:lambda:'other'});count+=1
    for symbol,other in (('znl',s['fields'][-1]),('znm',s['fields'][-2]),('znk',s['region'](set()))):
        assert not run('ejsx',args,m|{symbol:lambda other=other:other});count+=1
    for i in (4,5):
        for x in (0,-1):
            bad=args.copy();bad[i]=s['c'](x);assert not run('ejsx',bad,m);count+=1
    return dict(cases=count,native_current_field_units_and_positive_factors=True,rest_frame_scales_and_two_fields_retained=True)


@lru_cache(None)
def witness_checks():
    count=0
    for target in product(('a','b'),repeat=6):
        m={'ejsx':lambda *xs,target=target:xs==(*target,'context')}
        assert run('ejsy',['context'],m,'witness',('a','b'));count+=1
        assert not run('ejsy',['other'],m,'witness',('a','b'));count+=1
    assert not run('ejsy',['context'],{'ejsx':lambda *xs:False},'witness',('a','b'));count+=1
    unknowns(lambda mm:run('ejsy',['context'],mm,'witness',('a','b')),{'ejsx':lambda *xs:True},('ejsx',))
    try:run('ejsy',['context'],{},'unbounded',('a','b'))
    except ValueError as e:assert 'rational number domain' in str(e) or 'Finite function domain' in str(e),str(e)
    else:raise AssertionError('Real conversion witnesses silently sampled')
    return dict(cases=count,all_six_witness_slots_independent=True,two_value_binding_diagnostic_only=True,native_real_witnesses_refused=True)


@lru_cache(None)
def equation_binding_checks():
    s=setup();f=s['fields'];norm=s['norm'];rows={'ejsy':{('context',)},'ejsm':{norm(('frame','length','duration','context',f[4]))},'s5y':{norm((f[-2],f[-1],f[4],s['c'](2)))}}
    m=s['m']|{n:s['relation'](rs) for n,rs in rows.items()}
    count=perturb(lambda mm:run('ejsz',['context'],mm),m,rows,norm)
    rows2={'ejsz':{('context',)}}
    count+=perturb(lambda mm:run('ejs6',[],mm),{'ejsz':relation(rows2['ejsz'])},rows2)
    return dict(cases=count,same_region_fields_light_vacuum_and_physical_convention=True,content_keeps_current_situation=True)


def altered(field,s,axis=None,position=None,temporal=False):
    c,r=s['c'],s['r']
    def at(a):
        return FunctionValue(tuple([RS]*4),RS,lambda *xs:c(r(field(a)(*xs))+(a==('time' if temporal else axis) and (position is None or tuple(map(r,xs))==position))))
    return FunctionValue(('individual',),TAU,at)


@lru_cache(None)
def vector_checks():
    s=setup();m=s['m'];field=s['fields'][-2];region=s['fields'][4];count=0
    for p in s['points'][:2]:
        assert run('ejs2',[field,field,p],m);count+=1
        for axis in AXES[:3]:
            bad=altered(field,s,axis=axis);assert not run('ejs2',[bad,field,p],m);count+=1
    for position in POINTS[:2]:
        for axis in AXES[:3]:
            bad=altered(field,s,axis,position);assert not run('ejs3',[bad,field,region],m);count+=1
    assert run('ejs3',[altered(field,s,'x',POINTS[2]),field,region],m);count+=1
    assert run('ejs3',[altered(field,s,temporal=True),field,region],m);count+=1
    assert not run('ejs3',[field,field,s['region'](set())],m);count+=1
    assert not run('ejs2',[field,field,s['points'][0]],m|{'yo':lambda:'x'});count+=1
    for name,target in (('ejs4',s['fields'][-2]),('ejs5',s['fields'][-1])):
        mm=m|{'ejsy':relation({('context',)})}
        clone=altered(target,s,'x',POINTS[2])
        assert run(name,[clone,'context'],mm);count+=1
        assert not run(name,[clone,'other'],mm);count+=1
        swapped=s['fields'][-1 if name=='ejs4' else -2]
        assert not run(name,[swapped,'context'],mm);count+=1
        unknowns(lambda model:run(name,[clone,'context'],model),mm,('ejsy',))
    unknowns(lambda model:run('ejs2',[field,field,s['points'][0]],model),m,('sca',))
    try:run('ejs3',[field,field,region],m,'unbounded')
    except ValueError as e:assert 'rational number domain' in str(e) or 'Finite function domain' in str(e),str(e)
    else:raise AssertionError('All field coordinates silently sampled')
    return dict(cases=count,all_three_components_at_two_distinguishing_points=True,outside_region_and_time_component_not_forced=True,extensional_field_rules_and_distinct_axes=True,native_full_domain_refused=True)


@lru_cache(None)
def curl_checks():
    s=setup();c=s['c'];m=s['m'];e=[[1,2,3,12],[4,5,6,-12],[7,8,9,-4]];b=[[2,5,11,-4],[3,7,13,8],[17,19,23,-4]]
    jet=lambda values:FunctionValue(('individual','individual'),RS,lambda a,axis:c(values[AXES.index(a)][AXES.index(axis)] if a in AXES[:3] and axis in AXES else 0))
    assert run('s5w',[c(2),jet(e),jet(b)],m);count=1
    for field in (0,1):
        for component in range(3):
            for axis in range(4):
                if axis==component:continue
                matrices=deepcopy([e,b]);matrices[field][component][axis]+=1
                assert not run('s5w',[c(2),*(jet(x) for x in matrices)],m);count+=1
    for light in (0,-2,3):assert not run('s5w',[c(light),jet(e),jet(b)],m);count+=1
    diagonal=deepcopy(e);diagonal[0][0]+=1
    assert run('s5w',[c(2),jet(diagonal),jet(b)],m);count+=1
    return dict(cases=count,all_eighteen_derivative_slots_and_six_signs=True,positive_same_light=True,divergence_not_added=True,actual_derivative_connections_pinned_in_prior_report=True)


@lru_cache(None)
def presentation_checks():
    rows={'ug':{('intro','author','ejs6','scope','context')},'eisch':{('designation','ejs6','scope','context')},'eisox':{('display','ejs6','context')},'uf':{('author','intro','display','context'),('author','display','explanation','context')},'ue':{('intro','display','context'),('display','explanation','context')},'eispi':{('electricname','ejs4','paper','context'),('magneticname','ejs5','paper','context')}}
    m={n:relation(rs) for n,rs in rows.items()}
    count=perturb(lambda mm:run('ejtb',[],mm),m,rows)
    assert run('ejtb',[],m|{n:forbidden for n in ('ejsz','ejsy','ejsm','s5y','znl','znm','znk')});count+=1
    for n,val in (('eispl','intro'),('eispm','intro'),('eispm','display')):
        assert not run('ejtb',[],{x:lambda *xs:True for x in rows}|{n:lambda val=val:val});count+=1
    outer={'eir3':{('intro','author','paper','ejtc','context')},'ue':{('heading','intro','context')}}
    count+=perturb(lambda mm:run('ejtd',[],mm),{n:relation(rs) for n,rs in outer.items()},outer)
    assert not run('ejtd',[],{n:lambda *xs:True for n in outer}|{'eisph':lambda:'intro'});count+=1
    return dict(cases=count,assumption_display_and_explanation_share_content=True,naming_and_both_vector_rules_retained=True,assumed_physical_truth_not_executed=True,source_order_and_distinct_nodes=True)


@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));math={m['id']:m for m in inv['math']};segments=[]
    for u in inv['units'][152:155]:
        assert digest(u['text'].encode())==u['text_sha256']
        ms=[math[n] for n in u['math_ids']]
        for m in ms:assert digest(m['mathml'].encode())==m['sha256']
        segments.append(dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],text=u['text'],math=ms,source_nonblank_characters=len(re.sub(r'\s|\[M\d+\]','',u['text']))))
    ns='{http://www.w3.org/1998/Math/MathML}';tree=ET.fromstring(math['M0287']['mathml']);fractions=[tuple(''.join(n.itertext()) for n in f) for f in tree.iter(ns+'mfrac')]
    expected=[('∂X','∂t'),('∂N','∂y'),('∂M','∂z'),('∂L','∂t'),('∂Y','∂z'),('∂Z','∂y'),('∂Y','∂t'),('∂L','∂z'),('∂N','∂x'),('∂M','∂t'),('∂Z','∂x'),('∂X','∂z'),('∂Z','∂t'),('∂M','∂x'),('∂L','∂y'),('∂N','∂t'),('∂X','∂y'),('∂Y','∂x')]
    assert [f for f in fractions if f!=('1','V')]==expected and fractions.count(('1','V'))==6
    operators=[''.join(n.itertext()) for n in tree.iter(ns+'mo')];assert operators.count('−')==operators.count('=')==6
    for mid,flat in (('M0286','K'),('M0288','X,Y,Z'),('M0289','L,M,N')):assert ''.join(ET.fromstring(math[mid]['mathml']).itertext())==flat
    return dict(version='einstein-vacuum-equation-assumption-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['907'],segments=segments,source_derivative_order=expected,observations=['原刊907頁でmögen ... so daß gelten mögeの導入、三行二列の六式、コンマからwobeiに続く二ベクトルの意味説明を一文として照合した。','各式の1/V、時間微分と空間偏微分の成分・軸、差の符号と列順を固定MathMLと照合した。表示式はugの同じ仮定内容を具体化する。','elektrische/magnetische Kraftは既存の同じ系の場の強さとして解釈する。後続の変換の証明や磁気的質量の説明をこの範囲から認定しない。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in (INVENTORY,DOC,*FACSIMILES)})


@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert len(new.document['statements'])==358
    assert [i for i,(a,b) in enumerate(zip(old.document['statements'],new.document['statements'])) if a!=b]==[INDEX]
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read(PRIOR));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[357])==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS)
    names=set(selection_binding(new,[INDEX])['dependencies'])
    assert set(MEANINGS)|{'ejsn','ejsm','s5y','s5u','s5t','eirm','eiru','eiro','eiscc','ug','uf','eisox','eisch','eir3'}<=names
    assert not names&{'s5z','s6o','s6p','scj2','eisas'}
    core=parse(read(CORE))
    for style in ('compact','full'):
        body=format_graph(core,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core
    assert json.loads(json.dumps(source_record(),ensure_ascii=False))==json.loads(read(SOURCE))
    return dict(new_definitions=len(MEANINGS),new_notation_relation=1,new_reference_individuals=4,replaced_statement=INDEX,other_357_statements_and_prior_judgments_preserved=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')


@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('physical',physical_checks),('witnesses',witness_checks),('equation_binding',equation_binding_checks),('vectors',vector_checks),('curl',curl_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    helpers=('compose_vacuum_field_domain','compose_field_equations','compose_material_relative_frame','compose_solid_sphere_geometry','compose_relativity_conjecture','compose_two_postulates','compose_limits','check_coordinate_correspondence','check_moving_trip_geometry','check_material_relative_frame','check_clock_site_time','check_vacuum_field_domain','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,PRIOR,*DEPENDENCIES,'scripts/compose_vacuum_equation_assumption.py','scripts/check_vacuum_equation_assumption.py','tests/test_vacuum_equation_assumption.py',*(f'scripts/{n}.py' for n in helpers)}
    segments=[]
    for s in source_record()['segments']:
        row=dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],statements=[INDEX],definitions=list(MEANINGS),status='explicit_interpretive_annotation');segments.append(row)
        for m in s['math']:segments.append(dict(row,math_id=m['id'],math_sha256=m['sha256']))
    return dict(status='vacuum_equation_assumption_six_formulas_and_vector_meanings_connected',document=FULL,**results,alignment=dict(segments=segments),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['u0153–u0155の全単位意味判断'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
