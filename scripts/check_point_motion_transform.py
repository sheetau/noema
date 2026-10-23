"""Check same-point substitution, full current scopes and a genuine motion query."""
from functools import lru_cache
from fractions import Fraction as Q
from itertools import product
from xml.etree import ElementTree as ET
import json,re
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import Content,FunctionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_moving_trip_geometry import NUM
from scripts.check_clock_site_time import relation,perturb,unknowns,forbidden
from scripts.check_origin_clock_equations import model as clock_model
from scripts.check_point_motion_records import moving_model
from scripts.check_material_relative_frame import RS
from scripts.check_translated_light_trial import expose
from scripts.check_transverse_segment import refused
from scripts.compose_point_motion_transform import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,MEANINGS,build

DOC='docs/point-motion-transform-v1.md';SOURCE='data/einstein-point-motion-transform-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json'
PRIORS=tuple(f'data/einstein-velocity-opening-u{n:04d}-review-v1.json' for n in range(129,133))
DEPENDENCIES=('reports/point-motion-records-v1.json','reports/velocity-opening-claim-v1.json','reports/final-transform-claim-v1.json','reports/event-coordinate-task-v1.json')
CONSTANTS={'ra':'K','zbm':'k','ta':'length','rb':'duration','yn':'x','yo':'y','yp':'z','zc7':'time','zb6':'context','zkb':'clock'}
DOMAIN=tuple(dict.fromkeys((*CONSTANTS.values(),'a','b','event','arrival','other')));POINTS=('context','discourse','other');RECORDS=('x','y','z','time')
BOUNDS={'ejne':{'ejms'},'ejnf':{'ejne'},'ejng':{'ejmu','ejm3','ejnf','eiyz','eiy2','eiyy'},'ejnk':{'ejng','ejnf'},'ejnl':{'ejng','ejmz'},'ejnm':{'ejmu'},'ejnn':{'ejmx','ejnm'},'ejno':{'ejmy','ejeh','ejnk'},'ejnp':{'ejnl'}}

@lru_cache(None)
def core():return parse(read(CORE))

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=extract_document(core(),roots=[name],statement_indices=[]).document
    abstract(doc,NUM|{'sje','sjd','sky','zzbb','zzbd'}|BOUNDS.get(name,set()));doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name)
    if mode=='instance':assert len(expose(d,{'forall'},only_sort=RS))==1
    slots=[]
    for i,p in enumerate(d['parameters']):
        n='jpmta'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=name,arguments=[dict(kind='call',symbol=n,arguments=[]) for n in slots])
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jpmtpoint',parameters=[],result='situation'));expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='jpmtpoint',arguments=[]))
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots


def run(name,args,m,mode='boundary',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(args)==len(slots),(name,len(args),len(slots))
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|{'jpmtpoint':lambda:'discourse'}|m|{n:lambda x=x:x for n,x in zip(slots,args)}
    return evaluate_document(doc,individuals=domain,situations=POINTS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=500000,memoize_definitions=True,memoize_expressions=True)[0]['value']


def model(speed=Q(3),u=Q(2),w=Q(-1),time=Q(2)):
    speed,u,w,time=map(Q,(speed,u,w,time));cuts,m,coords,norm=clock_model(speed,time);c=cuts.make
    beta=Q(5,3) if abs(speed)==4 else Q(5,4) if abs(speed)==3 else Q(1)
    den=1+speed*u/25
    assert den
    for lab,own,t in (('x','y',time),('z','time',time+3)):
        tau=t/(beta*den);coords[lab]=[(u+speed)*t/den,w*t/(beta*den),Q(0),t];coords[own]=[u*tau,w*tau,Q(0),tau]
    m|={'zkc':lambda:c(u),'zkd':lambda:c(w)}
    return cuts,m,coords,norm,beta,den


@lru_cache(None)
def numeric_checks():
    count=0;negative=0
    for speed,u,w,time in product((-3,0,3),(-10,-2,0,7),(-3,0,2),(-2,0,3)):
        cuts,m,coords,norm,beta,den=model(speed,u,w,time);c=cuts.make
        args=[c(Q(x)) for x in (5,speed,u,w,*coords['x'])]
        assert run('ejni',['x','y'],m) and run('ejnj',['x'],m) and run('ejnh',args,m);count+=3
        if den<0:negative+=1
        # All four output coordinates matter, except that t can vary freely for a stationary point.
        for slot in range(4):
            bad=args[:];bad[4+slot]=c(cuts.read(bad[4+slot])+1)
            expected=slot==3 and u+speed==0 and w==0
            assert run('ejnh',bad,m)==expected;count+=1
        # A transformed pair can obey ssn but fail the original planar law.
        coords['x'][2]=1;coords['y'][2]=1
        assert run('ssn',['x','y'],m) and not run('ejni',['x','y'],m) and not run('ejnj',['x'],m);count+=3
        coords['x'][2]=0;coords['y'][2]=0
    assert negative
    # A singular t parameterization is not an invalid Lorentz pair in itself.
    cuts,m,coords,norm,beta,den=model();c=cuts.make;u=Q(-25,3);w=Q(2);tau=Q(3)
    coords['x']=[u*tau/beta,w*tau,Q(0),Q(0)];coords['y']=[u*tau,w*tau,Q(0),tau]
    mm=m|{'zkc':lambda:c(u),'zkd':lambda:c(w)}
    assert run('ssn',['x','y'],mm) and run('ejni',['x','y'],mm) and not run('ejnj',['x'],mm);count+=3
    cuts,m,coords,norm,beta,den=model();c=cuts.make
    unknowns(lambda mm:run('ejnj',['x'],mm),m,('tc','zb7','zkc','zkd','zc6','sky','sje','sjd'))
    # Positive root, not its reciprocal, occurs in the printed transverse numerator.
    correct=coords['x'][1];coords['x'][1]=Q(-1)*Q(2)*beta/den
    assert not run('ejnj',['x'],m);coords['x'][1]=correct;count+=1
    for slot in range(4):
        coords['y'][slot]+=1;assert not run('ejni',['x','y'],m);coords['y'][slot]-=1;count+=1
    return dict(cases=count,negative_denominator_examples=negative,native_four_coordinate_substitution_and_three_result_equations=True,positive_root_and_shared_constants=True,zero_denominator_rejected_without_discarding_original_transform_pairs=True)


@lru_cache(None)
def binding_checks():
    count=0;domain=('a','b')
    for event,lab,own,lp,op in product(domain,repeat=5):
        rows={'ejms':{('a',event,lab,lp,'a','context'),('a',event,own,op,'b','context')}}
        mm={n:relation(rs) for n,rs in rows.items()}|{'ra':lambda:'a','zbm':lambda:'b'}
        count+=perturb(lambda mm:run('ejne',['a',event,lab,own,'context'],mm,domain=domain),mm,rows)
    for event,lab,own in product(domain,repeat=3):
        rows={'ejne':{('a',event,lab,own,'context')}};mm={n:relation(rs) for n,rs in rows.items()}
        count+=perturb(lambda mm:run('ejnf',['a',lab,own,'context'],mm,domain=domain),mm,rows)
    return dict(cases=count,same_point_event_and_each_current_record_place_bound=True,two_value_witness_domain_all_argument_slots_checked=True)


@lru_cache(None)
def bridge_checks():
    count=0;domain=('a','b')
    rows={'ejmu':{('a',f,'context') for f in domain},'ejm3':{('a',ev,f,'context') for ev in domain for f in domain},'ejnf':{('a','a','b','context')},'eiyz':{('a',)},'eiy2':{('b',)},'eiyy':{('a','b')}}
    constants={'ra':lambda:'a','zbm':lambda:'b'}
    mm={n:relation(rs) for n,rs in rows.items()}|constants;a=['a','context'];check=lambda mm:run('ejng',a,mm,domain=domain)
    count+=perturb(check,mm,{n:rs for n,rs in rows.items() if n!='ejnf'})
    assert not check(mm|{'ejnf':relation(rows['ejnf']|{('a','b','a','context')})});count+=1
    assert not check(mm|{'zb6':lambda:'other'});count+=1
    # Extra current pairs require complete scope and correspondence, not just one valid pair.
    expanded=rows|{'ejnf':rows['ejnf']|{('a','b','a','context')},'eiyz':{('a',),('b',)},'eiy2':{('a',),('b',)},'eiyy':{('a','b'),('b','a')}}
    assert check({n:relation(rs) for n,rs in expanded.items()}|constants);count+=1
    unknowns(check,mm,('ejnf','ejmu','ejm3','eiyz','eiy2','eiyy'))
    return dict(cases=count,both_full_histories_same_event_extent_and_current_section_three_scopes=True,unmatched_or_unbridged_extra_current_record_rejected=True)


@lru_cache(None)
def full_scope_checks():
    count=0;cuts,m,coords,norm,beta,den=model()
    pairs={('x','x','y','context'),('x','z','time','context')};labrecords={('x',r,'x','context') for r in ('x','z')}
    mm=m|{'ra':lambda:'x','ejng':relation({('x','context')}),'ejnf':relation(pairs),'ejmz':relation(labrecords)}
    for name in ('ejnk','ejnl'):
        assert run(name,['x','context'],mm,domain=RECORDS);count+=1
        assert not run(name,['x','context'],mm|{'ejng':lambda *xs:False},domain=RECORDS);count+=1
        for rec in ('x','z'):
            for slot in (0,1,2):
                coords[rec][slot]+=1;assert not run(name,['x','context'],mm,domain=RECORDS);coords[rec][slot]-=1;count+=1
    for rec in ('y','time'):
        coords[rec][0]+=1;assert not run('ejnk',['x','context'],mm,domain=RECORDS);assert run('ejnl',['x','context'],mm,domain=RECORDS);coords[rec][0]-=1;count+=2
    assert not run('ejnk',['x','context'],mm|{'ejnf':relation(pairs|{('x','x','time','context')})},domain=RECORDS);count+=1
    assert not run('ejnl',['x','context'],mm|{'ejmz':relation(labrecords|{('x','y','x','context')})},domain=RECORDS);count+=1
    unknowns(lambda m:run('ejnl',['x','context'],m,domain=RECORDS),mm,('ejmz','zc6'))
    return dict(cases=count,native_original_and_result_equations_for_every_current_record=True,cross_event_pairs_and_additional_wrong_lab_records_rejected=True)


@lru_cache(None)
def candidate_checks():
    count=0;cuts,m,fs,norm=moving_model((2,-3,4),(7,-2,0));c=cuts.make;r=cuts.read
    rows={'ejmu':{('clock','K','context')}};mm=m|{n:relation(rs) for n,rs in rows.items()}
    def candidate(offset_axis=None,at=None):
        def value(axis,time):
            if axis not in ('x','y','z'):forbidden()
            out=r(fs[('x','y','z').index(axis)](time))
            return c(out+(1 if axis==offset_axis and (at is None or r(time)==at) else 0))
        return FunctionValue(('individual',RS),RS,value)
    f=candidate()
    for time in (-3,0,2,7):
        a=['clock','K','context',f,c(Q(time))];check=lambda mm:run('ejnm',a,mm,'instance')
        count+=perturb(check,mm,rows)
        for axis in ('x','y','z'):
            bad=a[:];bad[3]=candidate(axis,Q(time));assert not run('ejnm',bad,mm,'instance');count+=1
        unknowns(check,mm,('eismh','eisls','eislt'))
    # A defect at an interior time is not excused by agreement at the two ends.
    f=candidate('x',Q(2))
    for time,expected in ((-3,True),(2,False),(7,True)):
        assert run('ejnm',['clock','K','context',f,c(Q(time))],mm,'instance')==expected;count+=1
    refused(lambda:run('ejnm',['clock','K','context',candidate()],mm))
    refused(lambda:run('ejnn',[],{'ejmx':lambda *xs:True,'ejnm':lambda *xs:True}))
    return dict(cases=count,all_three_axes_and_interior_times_of_same_actual_history=True,arbitrary_origin_and_nonconstant_candidate_type=True,unbounded_time_and_function_question_refuse_finite_enumeration=True)


@lru_cache(None)
def content_checks():
    cuts,m,coords,norm,beta,den=model();count=0
    for a,b,c in product((False,True),repeat=3):
        mm=m|{'ejmy':lambda:Content(POINTS,(not a,a,not a)),'ejeh':lambda:Content(POINTS,(not b,b,not b)),'ejnk':lambda obj,ctx:c and (obj,ctx)==('clock','context')}
        assert run('ejno',[],mm)==(a and b and c);count+=1
    mm=m|{'ejmy':lambda:Content(POINTS,(False,True,False)),'ejeh':lambda:Content(POINTS,(False,True,False)),'ejnk':relation({('clock','context')}),'zkc':lambda:cuts.make(Q(-25,3))}
    assert not run('ejno',[],mm);count+=1
    rows={'ejnl':{('clock','context')}};mm={n:relation(rs) for n,rs in rows.items()}
    count+=perturb(lambda mm:run('ejnp',[],mm),mm,rows)
    return dict(cases=count,prior_point_assumption_and_current_transform_share_same_context=True,nonzero_denominator_explicit_in_rewrite_premise=True)


@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));table={m['id']:m for m in inv['math']};segments=[]
    expected=(('K','x,y,z,t'),('x=wξ+v1+vwξV2t,y=1−(vV)21+vwξV2wηt,z=0.',))
    for index,flats in zip(range(132,134),expected):
        u=inv['units'][index];assert u['id']==f'einstein-1905:u{index+1:04d}' and digest(u['text'].encode())==u['text_sha256'];math=[]
        assert len(u['math_ids'])==len(flats)
        for mid,flat in zip(u['math_ids'],flats):
            e=table[mid];root=ET.fromstring(e['mathml']);assert re.sub(r'\s','',''.join(root.itertext()))==flat;assert digest(e['mathml'].encode())==e['sha256']
            if mid=='M0251':
                ns='{http://www.w3.org/1998/Math/MathML}'
                assert len(root.findall('.//'+ns+'mtr'))==3 and len(root.findall('.//'+ns+'msqrt'))==1 and len(root.findall('.//'+ns+'mfrac'))==5
            math.append(dict(id=mid,sha256=e['sha256'],mathml_flat=flat))
        segments.append(dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],text=u['text'],source_nonblank_characters=len(re.sub(r'\s|\[M\d+\]','',u['text'])),math=math))
    retrieval='artifacts/einstein-curved-clock-records-v1/retrieval.json';rr=json.loads(read(retrieval));validate_hashes(ROOT,{x['path']:x['sha256'] for x in rr['sources']});paths={INVENTORY,DOC,retrieval,*(x['path'] for x in rr['sources'])}
    return dict(version='einstein-point-motion-transform-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['905'],segments=segments,observations=['原刊905頁で先行三式からGesucht ist、§3の変換を使う導入、結果の三式、次の平行四辺形則までを再読した。固定本文のK、x/y/z/t、wの二添字、正の平方根、共通分母とz=0を照合した。','第一文は同じ点のKでの運動を求める課題、第二文は既出§3の変換で元の運動式へKの四数量を導入し三式を得る提示と読む。今回は問いの候補と全記録の代入前後の内容であり、発話の提示と全単位判断は後続。','商の非零分母を明示した定義域とし、原文に印字された条件とは区別する。零分母では元の変換に合う記録もあり得る。点の速度上限を追加せず、負の分母・符号付き成分を許す。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements']==old.document['statements'] and len(new.document['statements'])==352
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations'];assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    for i,p in enumerate(PRIORS):
        prior=json.loads(read(p));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[350 if i==0 else 351])==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=core();names=lambda root:{d['name'] for d in extract_document(doc,roots=[root],statement_indices=[]).document['declarations']}
    assert {'ejms','ejmu','eiyw','se','eiyz','eiy2','eiyy','ssn','syr'}<=names('ejnk')
    assert {'ejmz','ejnh','syt','stw','sjd'}<=names('ejnl')
    assert not {'zka','syu','syv','syx','shd','zke'}&names('ejnp')
    assert not {'ejnh','ejnj','syt','sys'}&names('ejnn')
    assert not [d for d in new.document['declarations'][len(old.document['declarations']):] if d['kind']=='primitive'] and not doc['statements']
    for style in ('compact','full'):
        body=format_graph(doc,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    assert source_record()==json.loads(read(SOURCE))
    return dict(new_definitions=len(MEANINGS),new_primitives=0,preserved_statements=352,prior_judgments_preserved=True,question_contains_no_result_formula=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('numeric',numeric_checks),('binding',binding_checks),('bridge',bridge_checks),('scope',full_scope_checks),('candidate',candidate_checks),('content',content_checks),('structure',structure_checks)]}
    helpers=('compose_point_motion_records','compose_origin_clock_question','compose_rod_methods','compose_solid_sphere_geometry','compose_material_relative_frame','compose_relativity_conjecture','compose_limits','check_origin_clock_equations','check_point_motion_records','check_clock_site_time','check_coordinate_correspondence','check_moving_trip_geometry','check_material_relative_frame','check_translated_light_trial','check_transverse_segment','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,*PRIORS,*DEPENDENCIES,'scripts/compose_point_motion_transform.py','scripts/check_point_motion_transform.py','tests/test_point_motion_transform.py',*(f'scripts/{n}.py' for n in helpers)}
    return dict(status='same_point_current_motion_query_and_substitution_dependency_checked',document=FULL,**results,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['u0133の課題と代入の発話・§3への参照の提示','u0133–u0134の全単位判断'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
