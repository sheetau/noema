"""Check vacuum-law references, native local driving and both heading subjects."""
from functools import lru_cache
from fractions import Fraction as Q
import json,re
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import FunctionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_moving_trip_geometry import NUM
from scripts.check_material_relative_frame import RS,NUM as MAG_NUM
from scripts.check_clock_site_time import relation,perturb,unknowns,forbidden
from scripts.check_magnetic_action import setup as magnetic_setup,cross,vector,DOMAIN as MAG_DOMAIN,mutate
from scripts.check_vacuum_field_domain import setup as field_setup,DOMAIN as FIELD_DOMAIN
from scripts.compose_sixth_section_heading import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,INDEX,PRIMITIVES,MEANINGS,MAGNETIC,DRIVING,build

DOC='docs/sixth-section-heading-v1.md';SOURCE='data/einstein-sixth-section-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json'
FACSIMILES=('artifacts/written-facsimiles-v1/einstein-1905-unlp.pdf','artifacts/written-facsimiles-v1/einstein-1905-unlp-p907-0.jpg')
PRIOR='data/einstein-electrodynamic-part-u0151-review-v1.json'
DEPENDENCIES=('reports/vacuum-field-domain-v1.json','reports/magnetic-action-v1.json','reports/moving-conductor-case-v1.json','reports/transformation-heading-v1.json')
CONSTANTS={'yn':'x','yo':'y','yp':'z','zc7':'t','eispf':'designation','eispg':'section','eisph':'heading','eispb':'part','eirf':'paper','eispc':'partheading','zno':'assumption','ri':'case','tb':'speedunit'}
DOMAIN=tuple(dict.fromkeys((*MAG_DOMAIN,*FIELD_DOMAIN,*CONSTANTS.values(),'inquiry','driveunit')))
TAU=dict(kind='function',parameters=[RS]*4,result=RS)
POINT_SORT=dict(kind='function',parameters=['individual'],result=RS)


@lru_cache(None)
def fixture(name,mode='native'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    bounds=(MAG_NUM if name in ('ejsr','ejss') else NUM)|{'szi'}
    if name=='ejsq' and mode!='unbounded':bounds.add('ejsp')
    if name in ('ejsr','ejss'):
        if mode=='binding':bounds.add('eico')
        elif mode!='unbounded':bounds|={'seob','senz','sjs','sepw'}
    abstract(doc,bounds);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[]
    for i,p in enumerate(d['parameters']):
        n='jssh'+number_word(i);slots.append((n,p['sort']));doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    doc['statements']=[dict(kind='ask',body=dict(kind='call',symbol=name,arguments=[dict(kind='call',symbol=n,arguments=[]) for n,_ in slots]))]
    return doc,slots


def run(name,args,m,mode='native'):
    doc,slots=fixture(name,mode);assert len(args)==len(slots)
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|{'szi':lambda c,a,b:a if c else b}|m
    for (n,s),x in zip(slots,args):
        if isinstance(s,dict) and callable(x) and not isinstance(x,FunctionValue):x=FunctionValue(tuple(s['parameters']),s['result'],x)
        mm[n]=lambda x=x:x
    def missing(symbol):
        def reject(*xs):raise ValueError('Unknown sixth-section input: '+symbol)
        return reject
    return evaluate_document(doc,individuals=DOMAIN,situations=('case','context','other'),primitives={d['name']:mm.get(d['name'],missing(d['name'])) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=700000,memoize_definitions=True,memoize_expressions=True)[0]['value']


@lru_cache(None)
def equation_checks():
    s=field_setup();light=s['c'](4);args=s['fields'];norm=s['norm'];rel=s['relation']
    rows={'ejsp':{norm((*args,light))},'eiscc':{('frame','length','duration','speedunit','context')}}
    m=s['m']|{n:rel(rs) for n,rs in rows.items()}|{'tc':lambda:light}
    count=perturb(lambda mm:run('ejsq',args,mm),m,rows,norm)
    assert not run('ejsq',args,m|{'tc':lambda:s['c'](5)});count+=1
    unknowns(lambda mm:run('ejsq',args,mm),m,('tc',))
    try:run('ejsq',args,m,'unbounded')
    except ValueError as e:assert 'rational number domain' in str(e) or 'Finite function domain' in str(e),str(e)
    else:raise AssertionError('Whole vacuum region silently sampled')
    return dict(cases=count,same_existing_light_and_speed_unit=True,all_field_regime_arguments_retained=True,native_full_region_refused=True)


def driving_fixture(charge=1,velocity=(1,2,-1)):
    cuts,m,f=magnetic_setup(charge,velocity);r=cuts.read
    drive=tuple(Q(3,2)*x for x in cross(velocity,(6,2,2)))
    f|={'driveunit':'driveunit','driving':vector(cuts,drive)}
    m['eisar']=relation({('driveunit','forceunit','chargeunit','case')})
    return cuts,m,f,[f[n] for n,_ in DRIVING],drive


def norm_factory(cuts):
    c=cuts.make;r=cuts.read
    def norm_one(value,sort):
        if not isinstance(sort,dict):return value
        if sort==RS:return r(value)
        parameters=sort['parameters'];result=sort['result']
        if parameters==['individual']:inputs=[(a,) for a in ('x','y','z','t')]
        elif parameters==[RS]*4:inputs=[tuple(c(Q(x)) for x in p) for p in ((1,2,3,4),(2,3,4,5))]
        elif parameters==[RS]:inputs=[(c(Q(t)),) for t in (3,4,5)]
        else:raise AssertionError(sort)
        return tuple(norm_one(value(*xs),result) for xs in inputs)
    return norm_one


@lru_cache(None)
def driving_checks():
    count=0
    for velocity in ((0,0,0),(6,2,2),(1,2,-1),(0,1,0),(0,0,1),(-1,2,0)):
        cuts,m,f,args,drive=driving_fixture(velocity=velocity)
        assert run('ejsr',args,m);assert run('ejss',args,m)==any(drive);count+=2
        for slot in range(3):
            changed=list(drive);changed[slot]+=1;bad=args.copy();bad[-1]=vector(cuts,changed)
            assert not run('ejsr',bad,m);count+=1
    for charge in (0,-1,2):
        _,m,_,args,_=driving_fixture(charge=charge);assert not run('ejsr',args,m);count+=1
    cuts,m,f,args,_=driving_fixture();norm_one=norm_factory(cuts)
    doc,slots=fixture('ejsr','binding');sorts=[s for _,s in slots[:len(MAGNETIC)]]
    expected=tuple(norm_one(x,s) for x,s in zip(args,sorts))
    same=lambda *xs:tuple(norm_one(x,s) for x,s in zip(xs,sorts))==expected
    assert run('ejsr',args,m|{'eico':same},'binding');count+=1
    for i,s in enumerate(sorts):
        changed=list(expected);changed[i]='wrong'
        assert not run('ejsr',args,m|{'eico':lambda *xs,changed=tuple(changed):tuple(norm_one(x,s) for x,s in zip(xs,sorts))==changed},'binding');count+=1
    rows={'eisar':{('driveunit','forceunit','chargeunit','case')}}
    count+=perturb(lambda mm:run('ejsr',args,mm),m,rows)
    unknowns(lambda mm:run('ejsr',args,mm,'binding'),m|{'eico':same},('eico',))
    try:run('ejsr',args,m,'unbounded')
    except ValueError as e:assert 'rational number domain' in str(e) or 'Finite function domain' in str(e),str(e)
    else:raise AssertionError('Whole material history silently sampled')
    return dict(cases=count,native_magnetic_force_and_local_driving_connected=True,all_magnetic_arguments_bound=True,positive_unit_probe_and_force_per_charge_unit=True,stationary_and_parallel_zero_cases_kept=True,native_full_history_refused=True)


@lru_cache(None)
def heading_checks():
    topic={'eispd':{('inquiry','designation','ejsq','eiu2','case')},'eispe':{('inquiry','ejss','case')}}
    count=perturb(lambda mm:run('ejsv',['inquiry','case'],mm),{n:relation(rs) for n,rs in topic.items()},topic)
    rows={'eisdv':{('heading','section','part','paper',Q(2),Q(6),'case')},'eisdw':{('heading','section','ejsv','case')},'ue':{('partheading','heading','case')}}
    m={n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda mm:run('ejsw',[],mm),m,rows)
    for name,value in (('eisph','section'),('eispg','part'),('eisph','partheading'),('eispg','assumption')):
        assert not run('ejsw',[],{n:lambda *xs:True for n in rows}|{name:lambda value=value:value});count+=1
    return dict(cases=count,two_subjects_share_inquiry_and_context=True,quoted_rules_not_executed=True,section_six_in_part_two=True,heading_and_full_section_distinct_from_opening_assumption=True)


@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));u=inv['units'][151]
    assert u['id']=='einstein-1905:u0152' and u['kind']=='heading' and not u['math_ids']
    assert digest(u['text'].encode())==u['text_sha256'] and inv['units'][177]['text'].startswith('§ 7.')
    context=inv['units'][172:176]
    s=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],text=u['text'],math=[],source_nonblank_characters=len(re.sub(r'\s','',u['text'])))
    return dict(version='einstein-sixth-section-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['907'],segments=[s],context_only=[dict(unit=x['id'],unit_sha256=x['text_sha256'],text=x['text']) for x in context],division=dict(level=2,ordinal=6,parent='eispb',first=u['id'],last='einstein-1905:u0177',next_boundary='einstein-1905:u0178'),observations=['原刊907頁の第二部の直後、本文仮定の前にある二文の第六節見出しを照合した。§6、Maxwell-Hertzschen、leeren Raum、Über die Natur、Bewegung in einem Magnetfeld、elektromotorischen Kräfteを保持する。','u0173–u0176の固定転記を解釈の文脈として読み、単位電荷の力・旧表現の一次近似・新表現・補助概念という後続の説明と見出しを区別した。この文脈の四単位を今回の全体確認へ加算しない。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in (INVENTORY,DOC,*FACSIMILES)})


@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert len(new.document['statements'])==358 and new.document['statements'][:INDEX]==old.document['statements']
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read(PRIOR));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[356])==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS)
    names=set(selection_binding(new,[INDEX])['dependencies'])
    assert set(MEANINGS)|{'eihq','ejsm','ejsn','s5y','s5u','s5t','eiro','eico','seoc','sepw','eidz','eisar','eiu2'}<=names
    assert not names&{'eisas','eiea','eieb','zhr','s6o','scj2','eir3'}
    core=parse(read(CORE))
    for style in ('compact','full'):
        body=format_graph(core,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core
    assert source_record()==json.loads(read(SOURCE))
    return dict(new_definitions=len(MEANINGS),new_topic_relations=2,new_reference_individuals=3,previous_357_statements_and_judgments_preserved=True,conductor_case_and_later_conclusions_not_imported=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')


@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('equations',equation_checks),('driving',driving_checks),('heading',heading_checks),('structure',structure_checks)]}
    helpers=('compose_vacuum_field_domain','compose_magnetic_action','compose_field_equations','compose_material_relative_frame','compose_limits','check_coordinate_correspondence','check_moving_trip_geometry','check_material_relative_frame','check_clock_site_time','check_magnetic_action','check_vacuum_field_domain','check_electric_action','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,PRIOR,*DEPENDENCIES,'scripts/compose_sixth_section_heading.py','scripts/check_sixth_section_heading.py','tests/test_sixth_section_heading.py',*(f'scripts/{n}.py' for n in helpers)}
    s=source_record()['segments'][0]
    alignment=dict(segments=[dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],statements=[INDEX],definitions=list(MEANINGS),status='explicit_interpretive_annotation')])
    return dict(status='sixth_section_both_subjects_and_heading_connected',document=FULL,**results,alignment=alignment,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['u0152の全単位意味判断'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
