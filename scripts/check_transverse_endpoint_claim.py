"""Check endpoint formulas, nonvacuous time scope and ordered author presentation."""
from functools import lru_cache
from fractions import Fraction as Q
from itertools import product
import json
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import Content,FunctionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_moving_trip_geometry import NUM,numbers
from scripts.check_clock_site_time import relation,perturb,unknowns,forbidden
from scripts.check_four_coordinate_claim import model as previous_model,RS
from scripts.check_translated_light_trial import expose
from scripts.check_transverse_segment import source_record as prior_source,refused
from scripts.compose_transverse_endpoint_claim import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,INDICES,MEANINGS,PRIMITIVES,GROUPS,build

DOC='docs/transverse-endpoint-claim-v1.md';SOURCE='data/einstein-transverse-endpoint-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';PRIOR='data/einstein-reciprocal-claim-u0095-review-v1.json'
DEPENDENCIES=('reports/transverse-segment-v1.json','reports/reciprocal-claim-v1.json','reports/event-coordinate-task-v1.json','reports/transverse-rod-scale-v1.json')
CONSTANTS={'rd':'author','eirf':'paper','eisms':'section','ri':'discourse','ra':'K','zbm':'k','yn':'x','yo':'y','yp':'z','zc7':'time','zb6':'context','rb':'duration','zgu':'rod','zgv':'low','zgw':'high','zgs':'previous','zhh':'question','zhi':'selection','zhj':'intro','eisny':'first','eisnz':'second'}
DOMAIN=tuple(dict.fromkeys((*[x for n,x in CONSTANTS.items() if n not in ('ri','zb6')],'event','record','other')));POINTS=('context','discourse','other')

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    bounds=NUM|{'sje','sjd','sky'}
    bounds|={'ejcg':{'ejce'},'ejch':{'ejcg'},'ejci':{'ejch'},'ejcj':{'ejci','ejcg','srw','sry'},'ejck':{'ejcc'},'ejcl':{'ejcf'},'ejcm':{'ejcj'},'ejcn':{'ejcj'}}.get(name,set())
    abstract(doc,bounds);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name)
    if mode=='instance':assert len(expose(d,{'forall'},only_sort=RS))==1
    slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jtec'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    expr=dict(kind='call',symbol=name,arguments=args)
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jtecpoint',parameters=[],result='situation'));expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='jtecpoint',arguments=[]))
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,args,m,mode='boundary',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(args)==len(slots),(name,len(args),len(slots))
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|m|{n:lambda x=x:x for n,x in zip(slots,args)};mm.setdefault('jtecpoint',lambda:'discourse')
    return evaluate_document(doc,individuals=domain,situations=POINTS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=600000,memoize_definitions=True,memoize_expressions=True)[0]['value']

@lru_cache(None)
def numeric_checks():
    count=0
    # Signed nonzero phi remains signed; neither symmetry nor phi=1 is assumed.
    for phi,proper,t in product((Q(2),Q(-2),Q(1,2)),(Q(0),Q(2)),(Q(0),Q(1),Q(3,2))):
        cuts,m,coords,*_=previous_model(scale=phi/Q(5,4));c=cuts.make
        coords['x']=[3*t,proper/phi,Q(0),t];coords['y']=[Q(0),proper,Q(0),phi*t/Q(5,4)]
        assert run('srw',['x','y',c(Q(3)),c(proper)],m,domain=('x','y','z','time'));count+=1
        assert run('sry',['x',c(Q(3)),c(proper),c(phi)],m,domain=('x','y','z','time'));count+=1
        for slot in range(4):
            coords['x'][slot]+=1
            assert not run('sry',['x',c(Q(3)),c(proper),c(phi)],m,domain=('x','y','z','time'));count+=1
            assert not run('srw',['x','y',c(Q(3)),c(proper)],m,domain=('x','y','z','time'));count+=1
            coords['x'][slot]-=1
        for slot in range(4):
            coords['y'][slot]+=1;assert not run('srw',['x','y',c(Q(3)),c(proper)],m,domain=('x','y','z','time'));count+=1;coords['y'][slot]-=1
    unknowns(lambda mm:run('sry',['x',c(Q(3)),c(proper),c(phi)],mm,domain=('x','y','z','time')),m,('zc5','zc6','sje','sca'))
    return dict(cases=count,both_endpoints_all_printed_components_and_time_checked=True,negative_phi_not_replaced_by_absolute_value=True,same_signed_current_four_transform=True)

@lru_cache(None)
def scope_checks():
    cuts,m=numbers();c=cuts.make;r=cuts.read;count=0;small=('a','b')
    rows={'ejce':{('rod','high','event','first','K','context'),('rod','high','event','second','k','context')}}
    count+=perturb(lambda mm:run('ejcg',['rod','high','event','first','second','context'],mm),{n:relation(rs) for n,rs in rows.items()},rows)
    # Native three existential slots, each distinguished in a two-value domain.
    for row in product(small,repeat=3):
        base=m|{'zc7':lambda:'a','ejcg':lambda b,p,e,kr,mr,s,row=row:(b,p,e,kr,mr,s)==('a','b',*row,'context'),'zc6':lambda rec,role:c(Q(1 if rec==row[1] else 0)) if role=='a' and rec in small else forbidden()}
        assert run('ejch',['a','b','context',c(Q(1))],base,domain=small);count+=1
        assert not run('ejch',['a','b','context',c(Q(2))],base,domain=small);count+=1
        assert not run('ejch',['a','b','context',c(Q(1))],base|{'ejcg':lambda *xs:False},domain=small);count+=1
        for slot in (0,1,5):
            target=['a','b',*row,'context'];target[slot]='b' if slot==0 else 'a' if slot==1 else 'other'
            assert not run('ejch',['a','b','context',c(Q(1))],base|{'ejcg':lambda *xs,target=tuple(target):xs==target},domain=small);count+=1
    m|={'eisls':lambda *xs:c(Q(0)) if xs==('K','duration','context') else forbidden(),'eislt':lambda *xs:c(Q(2)) if xs==('K','duration','context') else forbidden()}
    for t in (Q(0),Q(1,3),Q(2)):
        base=m|{'ejch':lambda b,p,s,time:(b,p,s,r(time))==('rod','high','context',t)}
        assert run('ejci',['rod','high','context',c(t)],base,'instance');count+=1
        assert not run('ejci',['rod','high','context',c(t)],base|{'ejch':lambda *xs:False},'instance');count+=1
    assert run('ejci',['rod','high','context',c(Q(3))],base|{'ejch':lambda *xs:False},'instance');count+=1
    assert not run('ejci',['rod','high','context',c(Q(0))],base|{'eislt':lambda *xs:c(Q(0)),'ejch':lambda *xs:True},'instance');count+=1
    refused(lambda:run('ejci',['rod','high','context'],base))
    # Every event/rest/moving tuple must obey both native numeric predicates.
    cuts,m,*_=previous_model(scale=Q(8,5));c=cuts.make;r=cuts.read
    for row in product(small,repeat=3):
        base=m|{'ejci':lambda *xs:xs==('a','b','context'),'ejcg':lambda b,p,e,kr,mr,s,row=row:(b,p,e,kr,mr,s)==('a','b',*row,'context'),'srw':lambda kr,mr,speed,proper,row=row:(kr,mr,r(speed),r(proper))==(*row[1:],Q(3),Q(2)),'sry':lambda kr,speed,proper,phi,row=row:(kr,r(speed),r(proper),r(phi))==(row[1],Q(3),Q(2),Q(2))}
        assert run('ejcj',['a','b',c(Q(2)),'context'],base,domain=small);count+=1
        for missing in ('ejci','srw','sry'):
            assert not run('ejcj',['a','b',c(Q(2)),'context'],base|{missing:lambda *xs:False},domain=small);count+=1
        assert not run('ejcj',['a','b',c(Q(0)),'context'],base,domain=small);count+=1
    assert not run('ejcj',['a','b',c(Q(2)),'context'],base|{'ejci':lambda *xs:False,'ejcg':lambda *xs:False},domain=small);count+=1
    return dict(cases=count,native_same_event_two_frame_slots_and_all_record_tuples=True,each_real_time_requires_records_and_positive_interval=True,no_vacuous_empty_scope_or_single_sample_substitute=True)

@lru_cache(None)
def presentation_checks():
    count=0;cuts,m=numbers();c=cuts.make;r=cuts.read
    norm=lambda xs:tuple(r(x) if isinstance(x,FunctionValue) else x for x in xs)
    for name,bound,rows in (('ejck','ejcc',{('rod','low','high','context',Q(2))}),('ejcl','ejcf',{('context',)}),('ejcm','ejcj',{('rod','high',Q(2),'context')}),('ejcn','ejcj',{('rod','low',Q(0),'context')})):
        mm=m|{'zgz':lambda:c(Q(2)),bound:lambda *xs,rows=rows:norm(xs) in rows}
        count+=perturb(lambda mm:run(name,[],mm),mm,{bound:rows},norm)
    cases=(('ejco',{'zhg':{('question','author','spc','section','discourse')},'ue':{('previous','question','discourse')}}),('ejcp',{'eisnx':{('selection','author','rod','ejck','section','discourse')},'ug':{('selection','author','ejck','section','discourse')}}),('ejcq',{'uh':{('intro','author','ejcl','section','discourse'),('first','author','ejcm','section','discourse'),('second','author','ejcn','section','discourse')},'eiskj':{('first','intro',Q(1),'paper','discourse'),('second','intro',Q(2),'paper','discourse')},'ue':{('intro','first','discourse'),('first','second','discourse')}}))
    for name,rows in cases:
        m={n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda mm:run(name,[],mm),m,rows)
        assert run(name,[],m|{n:forbidden for n in ('spc','ejck','ejcl','ejcm','ejcn','ejcf','ejcj')});count+=1
    for value,message,claim,node,previous in GROUPS:
        rows={'eir3':{(CONSTANTS[node],'author','paper',message,'discourse')},'ue':{(CONSTANTS[previous],CONSTANTS[node],'discourse')}}
        count+=perturb(lambda mm:run(claim,[],mm),{n:relation(rs) for n,rs in rows.items()},rows)
    return dict(cases=count,same_function_question_and_object_attention_separate_from_assumption=True,both_endpoints_and_ordered_numbered_displays_preserved=True,quoted_content_not_executed_as_truth=True)

@lru_cache(None)
def source_record():
    prior=prior_source();validate_hashes(ROOT,prior['source_sha256'])
    pins={p:h for p,h in prior['source_sha256'].items() if p!='docs/transverse-segment-v1.md'};pins[DOC]=digest((ROOT/DOC).read_bytes())
    return dict(version='einstein-transverse-endpoint-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['902'],segments=prior['segments'],observations=['原刊902頁でWir fragen nunから第一端表示、und、第二端表示の句点まで照合する。','印字Hは同じkのη軸。指定された閉区間全体を理想化した線状棒として読み、物質の切断を加えない。','第一端のyはl/φ(v)でありMathMLのmfracを保つ。第二端のyは0。添字1が高いη側、2が低いη側である。','nunは直前の相反積からの談話上の移行。問い、対象へ考察を向ける行為、同じ横棒の主張と二つの表示を区別する。','両端式は対象区間の任意K時刻tの現在記録について読む。全時刻の存在と全該当記録への式を共に保持する。'],source_sha256=pins)

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-3]==old.document['statements'] and len(new.document['statements'])==318
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read(PRIOR));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[312,313,314])==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=parse(read(CORE));ds={d['name']:d for d in doc['declarations']}
    assert {'ejcf','ejce','eiyx','eipf','ejca','srw','sry','spc'}<=set(ds)
    assert not set(ds)&{'shd','zgj','ssa','ssb','sse','ssf','ssl','ssk'}
    assert all(ds[g[1]]['body']['force']=='assert' for g in GROUPS)
    for style in ('compact','full'):
        body=format_graph(doc,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),preserved_statements=315,prior_whole_unit_judgment_preserved=True,current_full_histories_and_measured_records=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('numeric',numeric_checks),('scope',scope_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,PRIOR,*DEPENDENCIES,'scripts/compose_transverse_endpoint_claim.py','scripts/check_transverse_endpoint_claim.py','tests/test_transverse_endpoint_claim.py','scripts/check_transverse_segment.py','scripts/check_coordinate_correspondence.py','scripts/check_clock_site_time.py','scripts/check_four_coordinate_claim.py','scripts/check_moving_trip_geometry.py','scripts/check_translated_light_trial.py','scripts/compose_limits.py','scripts/compose_material_relative_frame.py','scripts/compose_relativity_conjecture.py','scripts/compose_two_postulates.py','scripts/compose_rod_methods.py'}
    alignment=dict(segments=[dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],statements=list(INDICES if i==0 else [INDICES[-1]]),definitions=list(MEANINGS),status='explicit_interpretive_annotation') for i,s in enumerate(source_record()['segments'])])
    return dict(status='transverse_meaning_question_selection_and_endpoint_displays_connected',document=FULL,**results,alignment=alignment,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['u0097–u0100の全文通読判断と登録','u0101以降と二作品全体の目標'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
