"""Check signed geometry, shared-event records and all eight printed equalities."""
from functools import lru_cache
from fractions import Fraction as Q
from itertools import product
import json,re
from xml.etree import ElementTree as ET
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
from scripts.check_four_coordinate_claim import model as previous_model,RS
from scripts.compose_third_frame_geometry import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,MEANINGS,build

DOC='docs/third-frame-geometry-v1.md';SOURCE='data/einstein-third-frame-geometry-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';PRIOR='data/einstein-phi-determination-intent-u0092-review-v1.json'
DEPENDENCIES=('reports/first-principle-v1.json','reports/origin-light-ray-v1.json','reports/event-coordinate-task-v1.json','reports/reverse-transform-v1.json','reports/four-coordinate-claim-v1.json')
CONSTANTS={'ra':'K','zbm':'k','zgi':'third','yn':'x','yo':'y','yp':'z','zc7':'time','ta':'length','rb':'duration','zgk':'zero','zb6':'context'}
DOMAIN=('K','k','third','x','y','z','time','length','duration','zero','event','origin','moment','later','other')
POINTS=('context','discourse','other')

@lru_cache(None)
def fixture(name):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    bounds=NUM|{'sje','sjd','sky','eioj','sfc','ei46','eiyx','shh'}
    if name in ('eja6','eja7'):bounds|={'eja4','srf','srg','srh'}
    if name=='ejba':bounds|={'eja5','eja6','eja7'}
    if name=='ejbb':bounds|={'eja2','eja3'}
    if name=='ejbc':bounds|={'ei7c','ejbb','eja5','eja6'}
    abstract(doc,bounds);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jtfg'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    body=dict(kind='call',symbol=name,arguments=args)
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jtfgpoint',parameters=[],result='situation'));body=dict(kind='evaluate',content=body,situation=dict(kind='call',symbol='jtfgpoint',arguments=[]))
    doc['statements']=[dict(kind='ask',body=body)];return doc,slots


def run(name,args,m,domain=DOMAIN):
    doc,slots=fixture(name);assert len(args)==len(slots)
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|m|{n:lambda x=x:x for n,x in zip(slots,args)}|{'jtfgpoint':lambda:'discourse'}
    return evaluate_document(doc,individuals=domain,situations=POINTS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=1200000,memoize_definitions=True,memoize_expressions=True)[0]['value']


@lru_cache(None)
def numeric_checks():
    count=0
    # phi(+v) and phi(-v) may differ, vanish or have opposite signs.
    for plus,minus in ((2,3),(2,Q(1,2)),(-2,3),(0,3),(2,0)):
        cuts,m,coords,*_=previous_model();c=cuts.make;r=cuts.read;beta=Q(5,4);seen=[]
        def coefficient(speed):
            speed=r(speed);assert speed in (3,-3);seen.append(speed)
            return c(Q(plus if speed==3 else minus)/beta)
        m['zeq']=lambda:FunctionValue((RS,),RS,coefficient)
        x,y,z,t=coords['x'];coords['y']=[Q(plus)*beta*(x-3*t),Q(plus)*y,Q(plus)*z,Q(plus)*beta*(t-Q(3,25)*x)]
        coords['z']=[Q(plus)*Q(minus)*n for n in coords['x']]
        assert run('srf',['x','y','z'],m) and run('srg',['x','z',c(Q(plus)*Q(minus))],m);count+=2
        for record in ('y','z'):
            for slot in range(4):
                coords[record][slot]+=1
                assert not run('srf',['x','y','z'],m);count+=1
                if record=='z':assert not run('srg',['x','z',c(Q(plus)*Q(minus))],m);count+=1
                coords[record][slot]-=1
        for speed in (3,-3):
            assert run('srd',[c(Q(5)),c(Q(speed)),c(beta)],m);count+=1
            for wrong in (-beta,Q(4,5)):
                assert not run('srd',[c(Q(5)),c(Q(speed)),c(wrong)],m);count+=1
        assert set(seen)=={3,-3}
        if plus!=minus and plus!=0:
            wrong=m|{'zeq':lambda:FunctionValue((RS,),RS,lambda speed:c(Q(plus)/beta))}
            assert not run('srf',['x','y','z'],wrong);count+=1
        unknowns(lambda mm:run('srf',['x','y','z'],mm),m,('tc','zb7','zeq','sky','zc5','zc6'))
    # The native linear-motion body also accepts negative velocity.
    cuts,m,*_=previous_model();c=cuts.make
    assert run('eioh',[c(Q(x)) for x in (-3,0,2,7,1)],m);count+=1
    assert not run('eioh',[c(Q(x)) for x in (3,0,2,7,1)],m);count+=1
    return dict(cases=count,eight_equalities_and_both_signed_phi_values_checked=True,negative_zero_and_nonunit_product_not_forbidden=True,native_signed_linear_motion_checked=True)


@lru_cache(None)
def geometry_checks():
    cuts,m,*_=previous_model();c=cuts.make;r=cuts.read;count=0
    rows={'eioj':{('k','third','length','duration','context')},'sfc':{('k','third','context')},'eisk7':{('third','origin','context')},'eisla':{('k','third','moment','context'),('k','third','later','context')}}
    m|={n:relation(rs) for n,rs in rows.items()}
    velocities={('k','third','length','duration',axis,'context'):Q(-3 if axis=='x' else 0) for axis in ('x','y','z')}
    positions={('origin',moment,'k','length',axis,'context'):Q(0) for moment in DOMAIN for axis in ('y','z')}
    m|={'zbn':lambda f,s:'origin' if (f,s)==('third','context') else forbidden(),'eislc':lambda *xs:c(velocities[xs]) if xs in velocities else forbidden(),'ym':lambda *xs:c(positions[xs]) if xs in positions else forbidden()}
    check=lambda mm:run('eja2',['k','third',c(Q(-3)),'context'],mm)
    # The moment scope is owned by eioj/eislb; here test each selected moment's axis constraint.
    count+=perturb(check,m,{n:rs for n,rs in rows.items() if n!='eisla'})
    for key in velocities:
        velocities[key]+=1;assert not check(m);velocities[key]-=1;count+=1
    for moment,axis in product(('moment','later'),('y','z')):
        key=('origin',moment,'k','length',axis,'context');positions[key]=Q(1);assert not check(m);positions[key]=Q(0);count+=1
    assert not run('eja2',['k','third',c(Q(3)),'context'],m);count+=1
    unknowns(check,m,('zbn','eislc','ym','eisla'))
    rows={'zc4':{('zero',)},'ei46':{('zero','x','y','context')},'zbv':{('third','origin','context')},'cb':{('zero','origin','third')},'eiyx':{('zero','z','third','context')}}
    m|={n:relation(rs) for n,rs in rows.items()};values={axis:Q(0) for axis in ('x','y','z','time')}
    m['zdz']=lambda event,frame,ctx:{'K':'x','k':'y','third':'z'}[frame] if event=='zero' and ctx=='context' else forbidden()
    m['zc6']=lambda record,role:c(values[role]) if record=='z' and role in values else forbidden()
    check=lambda mm:run('eja3',['zero','context'],mm)
    count+=perturb(check,m,rows)
    for role in values:
        values[role]=Q(1);assert not check(m);values[role]=Q(0);count+=1
    unknowns(check,m,('zbn','zdz','zc6'))
    return dict(cases=count,whole_frame_signed_vector_and_every_selected_origin_position=True,all_three_origin_records_and_four_third_coordinates_required=True)


@lru_cache(None)
def record_checks():
    count=0
    rows={'zc4':{('event',)},'eiyx':{('event','x','K','context'),('event','y','k','context'),('event','z','third','context')}}
    m={n:relation(rs) for n,rs in rows.items()}
    count+=perturb(lambda mm:run('eja4',['event','x','y','z','context'],mm),m,rows)
    for const in ('ra','zbm'):
        assert not run('eja4',['event','x','y','z','context'],m|{'zgi':lambda n=const:CONSTANTS[n]});count+=1
    # Native sgv, with two events and a distinct alias of the third-frame values.
    tuples={('event','x','K','context'),('event','y','k','context'),('event','z','third','context'),('zero','x','K','context'),('zero','y','k','context'),('zero','z','third','context'),('event','time','third','context')}
    m={'zc4':lambda e:e in ('event','zero'),'eiyx':lambda *xs:xs in tuples,'shh':lambda a,b:a==b or {a,b}<={'z','time'}}
    assert run('eja5',['context'],m);count+=1
    for event,frame in product(('event','zero'),('K','k','third')):
        assert not run('eja5',['context'],m|{'eiyx':lambda e,t,f,s,e0=event,f0=frame:(e,t,f,s) in tuples and (e,f)!=(e0,f0)});count+=1
    assert not run('eja5',['context'],m|{'zc4':lambda e:False});count+=1
    assert not run('eja5',['context'],m|{'shh':lambda a,b:a==b});count+=1
    unknowns(lambda mm:run('eja5',['context'],mm),m,('zc4','eiyx','shh'))
    return dict(cases=count,same_event_and_distinct_three_frames=True,nonempty_every_event_three_records_and_value_uniqueness=True,aliases_not_rejected=True)


@lru_cache(None)
def scope_checks():
    cuts,m,*_=previous_model();c=cuts.make;r=cuts.read;count=0;small=('a','b')
    # All 2^4 argument combinations, not a large-domain tuple search.
    for row in product(small,repeat=4):
        selected=(*row,'context')
        base=m|{'eja4':lambda *xs,selected=selected:xs==selected,'srf':lambda *xs,row=row:xs==row[1:],'srg':lambda a,b,scale,row=row:(a,b)==(row[1],row[3]) and r(scale)==6,'srh':lambda:c(Q(6))}
        for name,relation_name in (('eja6','srf'),('eja7','srg')):
            assert run(name,['context'],base,small);count+=1
            assert not run(name,['context'],base|{relation_name:lambda *xs:False},small);count+=1
    for bits in product((False,True),repeat=3):
        m={n:lambda ctx,on=on:ctx=='context' and on for n,on in zip(('eja5','eja6','eja7'),bits)}
        assert run('ejba',['context'],m,small)==all(bits);count+=1
    for bits in product((False,True),repeat=4):
        m={n:lambda on=on:Content(POINTS,(False,on,False)) for n,on in zip(('ei7c','ejbb'),bits[:2])}
        m|={n:lambda ctx,on=on:ctx=='context' and on for n,on in zip(('eja5','eja6'),bits[2:])}
        assert run('ejbc',[],m,small)==all(bits);count+=1
    cuts,m,*_=previous_model();c=cuts.make;r=cuts.read
    rows={'eja2':{('k','third',Q(-3),'context')},'eja3':{('zero','context')}}
    norm=lambda xs:tuple(r(x) if isinstance(x,FunctionValue) else x for x in xs)
    m|={n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}
    count+=perturb(lambda mm:run('ejbb',[],mm),m,rows,norm)
    return dict(cases=count,all_triple_slots_and_whole_scope_checked=True,existence_intermediate_and_final_all_required=True,premise_keeps_same_equations_setup_and_double_application=True)


@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));math={m['id']:m for m in inv['math']};segments=[]
    expected={'M0150':'K′','M0151':'k','M0152':'Ξ','M0153':'−v','M0154':'Ξ','M0155':'t=0','M0156':'t=x=y=z=0','M0157':'t′','M0158':'K′','M0159':'x′,y′,z′','M0160':'K′'}
    for i,sha in ((92,'c14b3594b6f39201397b3f2cea09bc2cb74a53feac150e3615940afa723e9da5'),(93,'793fa21bede5b93b6058cac6ec5ceb2e8d2d76d813b5c0fa99942066e22d4857')):
        u=inv['units'][i];assert u['text_sha256']==sha
        elements=[]
        for n in u['math_ids']:
            flat=''.join(ET.fromstring(math[n]['mathml']).itertext())
            if n in expected:assert flat==expected[n],(n,flat)
            elements.append(dict(id=n,sha256=math[n]['sha256'],mathml_flat_text=flat))
        segments.append(dict(unit=u['id'],unit_sha256=sha,range=[0,len(u['text'])],text=u['text'],math=elements,source_nonblank_characters=len(re.sub(r'\s|\[M\d+\]','',u['text']))))
    retrieval='artifacts/einstein-light-proof-task-v1/retrieval.json';saved=json.loads(read(retrieval));validate_hashes(ROOT,{r['path']:r['sha256'] for r in saved['sources']})
    paths={DOC,INVENTORY,retrieval,*(r['path'] for r in saved['sources'])}
    return dict(version='einstein-third-frame-geometry-source-reading-v1',status='dependency_reading_not_whole_unit_judgment',pages=['901'],segments=segments,observations=['K′は第三系、Ξはkの縦軸。全三原点と零時刻は同じ基準出来事へ結ぶ。','x′,y′,z′はここでは第三系の測定座標。以前の補助x′=x−vtを代入しない。','M0161の四つの連鎖等式は、同じ中間記録の−v変換とφ(v)φ(−v)による最終値を両方示す。','目的・命名・著者の提示と全文判断は次の本文統合で扱う。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements']==old.document['statements'] and len(new.document['statements'])==310
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read(PRIOR));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[309])==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=parse(read(CORE));names={d['name'] for d in doc['declarations']}
    assert {'eiyx','ei46','eioj','sfc','srd','sre','srf','srg','srh'}<=names
    assert not names&{'shd','smk','sri','srj','srk','srl','sro','zgj','srs'}
    for style in ('compact','full'):
        body=format_graph(doc,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    assert source_record()==json.loads(read(SOURCE))
    return dict(new_definitions=len(MEANINGS),new_primitives=0,preserved_statements=310,prior_whole_unit_judgment_preserved=True,old_record_paths_excluded=True,whole_unit_review_not_claimed=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')


@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('numeric',numeric_checks),('geometry',geometry_checks),('records',record_checks),('scope',scope_checks),('structure',structure_checks)]}
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,PRIOR,*DEPENDENCIES,'scripts/compose_third_frame_geometry.py','scripts/check_third_frame_geometry.py','tests/test_third_frame_geometry.py','scripts/check_coordinate_correspondence.py','scripts/check_moving_trip_geometry.py','scripts/check_clock_site_time.py','scripts/check_four_coordinate_claim.py','scripts/compose_limits.py','scripts/compose_material_relative_frame.py','scripts/compose_relativity_conjecture.py'}
    return dict(status='third_frame_current_record_dependencies_checked',document=FULL,**results,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['第三系導入の同じ決定目的への接続','K′と三位置座標の命名・既出時刻表記との接続','著者による仮定・二回適用と結果の提示','u0093–u0094の全文判断と登録'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
