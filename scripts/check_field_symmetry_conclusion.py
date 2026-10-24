"""Check the conditional magnetic probe, symmetry discourse and final fields."""
from functools import lru_cache
from itertools import product
from fractions import Fraction as Q
import json,re,xml.etree.ElementTree as ET
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.finite_semantics import Content,FunctionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_clock_site_time import relation,perturb,unknowns,forbidden
from scripts.check_total_differential import OPERATIONS,setup as numeric_setup
from scripts.check_material_relative_frame import RS
from scripts.check_field_comparison_claim import setup as final_setup
from scripts.check_vacuum_field_domain import sample_points,PS,TAU,POINTS
from scripts.compose_field_symmetry_conclusion import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,PARENT_BASIS,INDICES,MEANINGS,build

DOC='docs/field-symmetry-conclusion-v1.md';SOURCE='data/einstein-field-symmetry-conclusion-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';CORRECTION='data/field-scale-inverse-facsimile-v1.json'
FACSIMILES=('artifacts/written-facsimiles-v1/einstein-1905-unlp.pdf','artifacts/written-facsimiles-v1/einstein-1905-unlp-p909-0.jpg')
PRIORS=tuple(f'data/einstein-inverse-field-claim-u{n:04d}-review-v1.json' for n in (165,166))
DEPENDENCIES=('reports/inverse-field-claim-v1.json','reports/field-parity-v1.json','reports/field-scale-inverse-v1.json','reports/field-transform-v1.json','reports/field-comparison-claim-v1.json')
UNITS=(167,168,169,170,171,172,282)
AXES=('x','y','z','t')
CONSTANTS={'ri':'context','rd':'author','eirf':'paper','zno':'scope','ra':'frame','zbm':'moving','zn4':'even','zn5':'unit','zn6':'final','zoa':'note','eisp5':'prior','eisp6':'evendisplay','eisp7':'unitdisplay','eisqa':'finaldisplay',**dict(zip(('yn','yo','yp','zc7'),AXES))}
DOMAIN=tuple(dict.fromkeys((*CONSTANTS.values(),'other','time')));SITUATIONS=('context','other')

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    bounds=OPERATIONS|{'ejvf':{'ejuh','ejuz','sbe2'},'ejvh':{'ejvf','ejvg'},'ejvi':{'ejub'},'ejvj':{'ejuz','ejvi'},'ejvk':{'ejub'},'ejvl':{'ejuh','ejvk'},'ejvm':{'ejub','s6k','s6l','s6m','s45'}}.get(name,set())
    if mode=='probe':bounds-= {'sbe2'}
    abstract(doc,bounds);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    if mode=='sample':
        doc=sample_points(doc);doc['declarations'][:0]=[dict(kind='primitive',name=n,parameters=[],result=PS) for n in ('jvfdone','jvfdtwo')]
    if not any(d['name']=='ri' for d in doc['declarations']):doc['declarations'].append(dict(kind='primitive',name='ri',parameters=[],result='situation'))
    d=next(d for d in doc['declarations'] if d['name']==name);expr=dict(kind='call',symbol=name,arguments=[])
    if d['result']=='content':expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='ri',arguments=[]))
    doc['statements']=[dict(kind='ask',body=expr)];return doc

def run(name,m,mode='boundary'):
    doc=fixture(name,mode);mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|m
    return evaluate_document(doc,individuals=DOMAIN,situations=SITUATIONS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=700000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def contents(names,bits):return {n:lambda b=b:Content(SITUATIONS,(b,not b)) for n,b in zip(names,bits)}

@lru_cache(None)
def premise_checks():
    cases=0
    for name,names in [('ejvf',('ejuh','ejuz','sbe2')),('ejvj',('ejuz','ejvi')),('ejvl',('ejuh','ejvk'))]:
        for bits in product((False,True),repeat=len(names)):
            assert run(name,contents(names,bits))==all(bits);cases+=1
        unknowns(lambda mm:run(name,mm),contents(names,[True]*len(names)),names)
    for selected,truth in product(product((False,True),repeat=2),repeat=2):
        m={'ejvf':lambda:Content(SITUATIONS,selected),'ejvg':lambda:Content(SITUATIONS,truth)}
        assert run('ejvh',m)==(any(selected) and all(not a or b for a,b in zip(selected,truth)));cases+=1
    unknowns(lambda mm:run('ejvh',mm),contents(('ejvf','ejvg'),(True,True)),('ejvf','ejvg'))
    return dict(cases=cases,nonempty_necessity_and_all_premises=True,no_response_or_evenness_in_candidate_selection=True)

def probe_setup(name,label):
    mode='probe' if name=='ejvf' else 'boundary';cuts,m=numeric_setup(fixture(name,mode));c,r=cuts.make,cuts.read
    speed=-3 if label=='negative_speed' else 0 if label=='zero_speed' else 3
    a,b={'negative_factor':(-1,-1),'unequal_reciprocal':(2,Q(1,2)),'opposite_factors':(1,-1),'zero_factors':(0,0)}.get(label,(1,1))
    electric=[[1,0,0,0,-1],[0]*5,[0]*5];magnetic=[[0]*5,[0]*5,[0,2,0,0,1]]
    if label.startswith('nonzero_component_'):(electric+magnetic)[int(label[-1])][4]+=1
    if label=='zero_magnetic':magnetic[2]=[0]*5
    if label=='negative_magnetic':magnetic[2][4]=-1
    def field(rows):
        return FunctionValue(('individual',),TAU,lambda role:FunctionValue(tuple([RS]*4),RS,lambda *xs:c(rows[AXES.index(role)][4]+sum(a*r(x) for a,x in zip(rows[AXES.index(role)],xs))) if role in AXES[:3] else c(0)))
    point=(2 if label=='wrong_point' else 1,0,0,0)
    m|={n:lambda x=x:x for n,x in CONSTANTS.items()}
    m|={'tc':lambda:c(5),'zb7':lambda:c(speed),'znl':lambda:field(electric),'znm':lambda:field(magnetic),'znk':lambda:FunctionValue(tuple([RS]*4),'truth',lambda *xs:label!='outside_region'),'zn7':lambda:FunctionValue(('individual',),RS,lambda role:c(point[AXES.index(role)] if role in AXES else 0)),'znz':lambda:FunctionValue((RS,),RS,lambda x:c(a if r(x)==speed else b)),'znn':lambda frame,e,h,region,ctx:frame=='frame' and ctx==('other' if label=='wrong_context' else 'context')}
    m|=contents(('ejuh','ejuz'),(True,True));return m

@lru_cache(None)
def probe_checks():
    cases=0
    for label in ('baseline','negative_factor','negative_magnetic','negative_speed','zero_speed','zero_magnetic','wrong_point','outside_region','wrong_context',*(f'nonzero_component_{i}' for i in range(5))):
        want=label in ('baseline','negative_factor','negative_magnetic','negative_speed')
        assert run('ejvf',probe_setup('ejvf',label),'probe')==want,label;cases+=1
    for label in ('baseline','negative_factor','negative_magnetic','negative_speed','zero_speed','zero_magnetic','unequal_reciprocal','opposite_factors','zero_factors'):
        want=label in ('baseline','negative_factor','negative_magnetic','negative_speed')
        assert run('ejvg',probe_setup('ejvg',label))==want,label;cases+=1
    return dict(cases=cases,native_same_point_five_zeros_nonzero_N_and_signed_response=True,fields_not_constant_away_from_probe=True,opposite_sign_and_same_magnitude_both_required=True,zero_speed_not_nontrivial_sign_flip=True,physical_binding_relation_is_fixture_boundary=True)

@lru_cache(None)
def coefficient_checks():
    cases=0;rows={}
    for label,speed,a,b in [('unit',3,1,1),('negative',3,-1,-1),('unequal_reciprocal',3,2,Q(1,2)),('equal_two',3,2,2),('zero_speed',0,2,2),('light_speed',5,1,1)]:
        results=[]
        for name,want in [('ejvi',abs(speed)<5 and a==b),('ejvk',abs(speed)<5 and a==1)]:
            cuts,m=numeric_setup(fixture(name));c,r=cuts.make,cuts.read
            m|={n:lambda x=x:x for n,x in CONSTANTS.items()};m|={'tc':lambda:c(5),'zb7':lambda:c(speed),'znz':lambda:FunctionValue((RS,),RS,lambda x:c(a if r(x)==speed else b))}|contents(('ejub',),(True,))
            value=run(name,m);assert value==want;results.append(value);cases+=1
            assert not run(name,m|contents(('ejub',),(False,)));cases+=1
        premise=run('ejvj',contents(('ejuz','ejvi'),(abs(speed)<5 and a*b==1,results[0])));cases+=1
        rows[label]=dict(even=results[0],unit=results[1],premise=premise)
    assert rows['negative']==dict(even=True,unit=False,premise=True)
    assert rows['zero_speed']['even']
    return dict(cases=cases,branches=rows,negative_branch_not_removed=True,zero_speed_evenness_is_identity=True)

@lru_cache(None)
def final_field_checks():
    s=final_setup(1);m=s['m']|contents(('ejub',),(True,))|{'znn':lambda *xs:True,'zc7':lambda:'time'};cases=0
    assert run('ejvm',m,'sample');cases+=1
    for which,axis,pos in product(('znr','zns'),AXES[:3],POINTS[:2]):
        f=s['e'] if which=='znr' else s['h'];changed=s['scaled'](f,1,axis,pos)
        assert not run('ejvm',m|{which:lambda changed=changed:changed},'sample');cases+=1
    assert not run('ejvm',m|contents(('ejub',),(False,)),'sample');cases+=1
    other=s['region']({POINTS[0]});assert not run('ejvm',m|{'znt':lambda:other},'sample');cases+=1
    s2=final_setup(2);assert not run('ejvm',s2['m']|contents(('ejub',),(True,))|{'znn':lambda *xs:True,'zc7':lambda:'time'},'sample');cases+=1
    try:run('ejvm',m)
    except ValueError as e:assert 'rational number domain' in str(e) or 'Finite function domain' in str(e),str(e)
    else:raise AssertionError('Full field-function domain silently sampled')
    return dict(cases=cases,native_all_six_components_and_full_domain_binding=True,mixed_fields_are_boundary_fixtures=True,full_function_domain_refused=True)

@lru_cache(None)
def presentation_checks():
    cases=0
    for name,node,pre,post,display in [('ejvn','even','ejvh','ejvi','evendisplay'),('ejvo','unit','ejvj','ejvk','unitdisplay'),('ejvp','final','ejvl','ejvm','finaldisplay')]:
        rows={'zc':{(node,'author',pre,post,'scope','context')},'eisox':{(display,post,'context')},'uf':{('author',node,display,'context')},'ue':{(node,display,'context')}}
        if name=='ejvn':rows['eisn2']={(node,'author',post,'scope','context')}
        m={n:relation(rs) for n,rs in rows.items()};cases+=perturb(lambda mm:run(name,mm),m,rows)
        assert run(name,m|{pre:forbidden,post:forbidden});cases+=1
    rows={n:{('note','author','ejvh','scope','context')} for n in ('uh','eisn2','zdg')}
    cases+=perturb(lambda mm:run('ejvq',mm),{n:relation(rs) for n,rs in rows.items()},rows)
    rows={'eisfo':{('even','note','paper',Q(1),'context')},'eir5':{('note','author','even','ejvh','context')},'uf':{('author','even','note','context')}}
    for name in ('ejvr','ejwa'):cases+=perturb(lambda mm:run(name,mm),{n:relation(rs) for n,rs in rows.items()},rows)
    for name,node,message,prior in [('ejvt','even','ejvs','prior'),('ejvv','unit','ejvu','evendisplay'),('ejvx','final','ejvw','unitdisplay'),('ejvz','note','ejvy',None)]:
        rows={'eir3':{(node,'author','paper',message,'context')}}
        if prior:rows['ue']={(prior,node,'context')}
        cases+=perturb(lambda mm:run(name,mm),{n:relation(rs) for n,rs in rows.items()},rows)
    return dict(cases=cases,symmetry_clarity_necessity_and_example_distinct=True,footnote_number_target_direction_and_author=True,three_conclusions_displays_and_source_order=True,quoted_claims_not_executed=True)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));table={m['id']:m for m in inv['math']};segments=[]
    for number in UNITS:
        u=inv['units'][number-1];assert digest(u['text'].encode())==u['text_sha256'];ms=[table[n] for n in u['math_ids']]
        for m in ms:assert digest(m['mathml'].encode())==m['sha256']
        segments.append(dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],text=u['text'],math=ms,source_nonblank_characters=len(re.sub(r'\s|\[M\d+\]','',u['text']))))
    raw={m['id']:''.join(ET.fromstring(m['mathml']).itertext()) for s in segments for m in s['math']}
    assert raw=={'M0312':'φ(v)=φ(−v)','M0313':'φ(v)=1','M0314':'X′=X,L′=L,Y′=β(Y−vVN),M′=β(M+vVZ),Z′=β(Z+vVM),N′=β(N−vVY).','M0443':'X=Y=Z=L=M=0','M0444':'N≠0','M0445':'v','M0446':'Y′'},raw
    ref=next(a for a in inv['annotations'] if a['id']=='A0023');assert ref['targets']==['#cite_note-4'] and 'cite_note-4' in inv['units'][281]['source_ids']
    correction=json.loads(read(CORRECTION));assert digest((ROOT/correction['image']).read_bytes())==correction['image_sha256']
    return dict(version='einstein-field-symmetry-conclusion-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['909'],segments=segments,raw_math=raw,footnote_reference=ref,observations=['原刊909頁のFernerから最終六式までと脚注1)を通読した。対称性・偶性・alsoの値1・われわれの式の最終形を連続した帰結として接続する。','脚注はz. B.の仮定例、五つの零成分と非零N、vの大きさを保つ符号反転、Y′の大きさを保つ符号反転の必要性を、対称性による明白さとして提示する。','原刊のφ/ψの同一参照を旧記録と共有する。脚注の在庫末尾の配置と原刊909頁の掲載位置を区別する。','係数積1と偶性から値1を結論する著者の提示は保持するが、負の枝を除く前提は本文に書かれていないため追加しない。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in (INVENTORY,DOC,CORRECTION,*FACSIMILES)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert len(new.document['statements'])==358
    assert [i for i,(a,b) in enumerate(zip(old.document['statements'],new.document['statements'])) if a!=b]==INDICES
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    for p in PRIORS:
        prior=json.loads(read(p));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[156,162])==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);names=set(selection_binding(new,INDICES)['dependencies'])
    assert set(MEANINGS)|{'ejuh','ejuz','sbe2','sbf2','sar2','sat2','sau2','sai2','saj2','s6k','s6l','ejrj','eisn2','zdg','eir5','eisfo'}<=names
    assert 'sap2' not in names
    prior=json.loads(read('reports/field-scale-inverse-v1.json'));assert prior['polynomial_lemmas']['claims']['negative_branch_is_a_counterexample_to_unit_conclusion']['status']=='valid'
    parity=json.loads(read('reports/field-parity-v1.json'));assert parity['components']['same_old_event_compared_at_both_speeds'] and parity['components']['no_equal_numeric_new_coordinates_assumed']
    core=parse(read(CORE))
    for style in ('compact','full'):
        body=format_graph(core,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core
    assert json.loads(json.dumps(source_record(),ensure_ascii=False))==json.loads(read(SOURCE))
    return dict(new_definitions=len(MEANINGS),new_general_relations=0,new_reference_individuals=3,replaced_statements=INDICES,other_353_statements_and_prior_judgments_preserved=True,negative_branch_and_same_old_event_checks_preserved=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('premises',premise_checks),('probe',probe_checks),('coefficient',coefficient_checks),('final_fields',final_field_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    helpers=('compose_vacuum_field_domain','compose_material_relative_frame','compose_relativity_conjecture','compose_two_postulates','compose_limits','check_coordinate_correspondence','check_clock_site_time','check_material_relative_frame','check_total_differential','check_field_transform','check_angle_composition','check_field_comparison_claim','check_vacuum_field_domain','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,*PRIORS,*DEPENDENCIES,'scripts/compose_field_symmetry_conclusion.py','scripts/check_field_symmetry_conclusion.py','tests/test_field_symmetry_conclusion.py',*(f'scripts/{n}.py' for n in helpers)}
    segments=[]
    for s in source_record()['segments']:
        row=dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],statements=INDICES,definitions=list(MEANINGS),status='explicit_interpretive_annotation');segments.append(row)
        for m in s['math']:segments.append(dict(row,math_id=m['id'],math_sha256=m['sha256']))
    return dict(status='symmetry_note_evenness_claimed_unit_and_final_fields_connected',document=FULL,**results,alignment=dict(segments=segments),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['u0167–u0172・u0282の全単位意味判断'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
