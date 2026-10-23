"""Check simultaneous measured length, signed branches and full vector motion."""
from functools import lru_cache
from fractions import Fraction as Q
from itertools import product
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
from scripts.check_clock_site_time import relation,perturb,unknowns,forbidden
from scripts.check_material_relative_frame import RS,FS
from scripts.check_translated_light_trial import expose
from scripts.check_transverse_segment import model as segment_model,DOMAIN,refused,relations
from scripts.check_four_coordinate_claim import model as numeric_model
from scripts.compose_transverse_measured_length import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,MEANINGS,build

DOC='docs/transverse-measured-length-v1.md';SOURCE='data/einstein-transverse-measured-length-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';PRIOR='data/einstein-transverse-endpoint-u0097-review-v1.json'
DEPENDENCIES=('reports/transverse-endpoint-claim-v1.json','reports/transverse-segment-v1.json','reports/rod-geometry-v1.json','reports/rod-methods-v1.json','reports/first-principle-v1.json')
CONSTANTS={'ra':'K','zbm':'k','yn':'x','yo':'y','yp':'z','zc7':'time','ta':'length','rb':'duration','zgu':'body','zgv':'low','zgw':'high'}

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    bounds=NUM|{'sje','sjd','sky'}
    bounds|={'ejcx':{'eipc','ejce'},'ejcy':{'ejcx'},'ejcz':{'ejcy'},'ejc2':{'ejcf','ejcj','ejcz'},'ejc3':{'eiad'},'ejc4':{'eipc','ejc3','ejcz'},'ejc5':{'eipe','ejc4'}}[name]
    abstract(doc,bounds);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name)
    if mode=='instance':assert len(expose(d,{'forall'},only_sort=RS))==(2 if name=='ejc3' else 1)
    slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jtml'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    doc['statements']=[dict(kind='ask',body=dict(kind='call',symbol=name,arguments=args))];return doc,slots

def run(name,args,m,mode='boundary',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(args)==len(slots),(name,len(args),len(slots))
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|m|{n:lambda x=x:x for n,x in zip(slots,args)}
    return evaluate_document(doc,individuals=domain,situations=('context','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=600000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def model(velocity=(3,0,0)):
    cuts,m,pos,members,_,pop,fields,norm=segment_model(True);c=cuts.make;r=cuts.read;vel=list(map(Q,velocity));drift={}
    def point(p,t,a,moving):
        if p not in pos:forbidden()
        return pos[p][a]+(vel[a]*t+drift.get((p,a),Q(0))*t*(2-t) if moving else 0)
    def families(moving):return [FunctionValue(('individual',),FS,lambda p,a=a:FunctionValue((RS,),RS,lambda t:c(point(p,r(t),a,moving)))) for a in range(3)]
    fs=families(True);restfs=families(False);fields=fields[:8]+fs
    def family(b,f,lu,tu,role,s):
        if (b,lu,tu,s)!=('body','length','duration','context') or f not in ('K','k') or role not in ('x','y','z'):forbidden()
        return (fs if f=='K' else restfs)[('x','y','z').index(role)]
    m|={'eislu':family,'eisls':lambda f,u,s:c(Q(0)) if f in ('K','k') and (u,s)==('duration','context') else forbidden(),'eislt':lambda f,u,s:c(Q(2)) if f in ('K','k') and (u,s)==('duration','context') else forbidden()}
    return cuts,m,pos,members,fs,restfs,pop,fields,norm,vel,drift

@lru_cache(None)
def length_checks():
    cuts,m,pos,members,fs,restfs,pop,fields,norm,vel,drift=model();c=cuts.make;r=cuts.read;count=0
    times={'p':Q(1),'q':Q(1)}
    m['zc6']=lambda rec,role:c(times[rec]) if rec in times and role=='time' else forbidden()
    args=['body','low','high','low','high','p','q','K','context',c(Q(2))]
    rows={'eipc':{norm(fields+['low','high'])},'ejce':{('body','low','low','p','K','context'),('body','high','high','q','K','context')}}
    m=relations(m,rows,norm);check=lambda mm:run('ejcx',args,mm)
    count+=perturb(check,m,rows,norm)
    for length in (-2,0,1,3):assert not run('ejcx',args[:-1]+[c(Q(length))],m);count+=1
    times['q']=Q(2);assert not check(m);count+=1;times['q']=Q(1)
    sameevent=args.copy();sameevent[4]=sameevent[3]
    assert not run('ejcx',sameevent,m|{'ejce':lambda *xs:True});count+=1
    # Native eipa measures a positive distance, independent of axis orientation.
    for endpoint in ((0,-2,0),(2,0,0),(0,0,-2)):
        pos['high']=list(map(Q,endpoint))
        mm=relations(m,{'eipc':{norm(fields+['low','high'])}},norm)
        assert check(mm);count+=1
        assert not run('ejcx',args[:-1]+[c(Q(-2))],mm);count+=1
    pos['high']=[Q(0),Q(2),Q(0)]
    unknowns(check,m,('zc6','eislu','eirh','eisls','eislt'))
    return dict(cases=count,current_two_end_records_same_time_and_positive_native_axis_distance=True,opposite_orientation_does_not_make_negative_length=True)

@lru_cache(None)
def time_checks():
    cuts,m=numbers();c=cuts.make;r=cuts.read;small=('a','b');count=0
    for row in product(small,repeat=4):
        target=('a','a','b',*row,'a','context',Q(2))
        norm=lambda xs:tuple(r(x) if isinstance(x,FunctionValue) else x for x in xs)
        base=m|{'zc7':lambda:'a','ejcx':lambda *xs,target=target:norm(xs)==target,'zc6':lambda rec,role:c(Q(1 if rec==row[2] else 0)) if rec in small and role=='a' else forbidden()}
        args=['a','a','b','a','context',c(Q(1)),c(Q(2))]
        assert run('ejcy',args,base,domain=small);count+=1
        assert not run('ejcy',args,base|{'ejcx':lambda *xs:False},domain=small);count+=1
        assert not run('ejcy',args[:-2]+[c(Q(2)),c(Q(2))],base,domain=small);count+=1
        assert not run('ejcy',args[:-1]+[c(Q(3))],base,domain=small);count+=1
    m|={'eisls':lambda *xs:c(Q(0)) if xs==('K','duration','context') else forbidden(),'eislt':lambda *xs:c(Q(2)) if xs==('K','duration','context') else forbidden()}
    args=['body','low','high','K','context',c(Q(2))]
    for t in (Q(0),Q(1,3),Q(2)):
        base=m|{'ejcy':lambda b,lo,hi,f,s,time,length:(b,lo,hi,f,s,r(time),r(length))==('body','low','high','K','context',t,Q(2))}
        assert run('ejcz',args+[c(t)],base,'instance');count+=1
        assert not run('ejcz',args+[c(t)],base|{'ejcy':lambda *xs:False},'instance');count+=1
    assert not run('ejcz',args+[c(Q(0))],base|{'ejcy':lambda *xs:True,'eislt':lambda *xs:c(Q(0))},'instance');count+=1
    assert run('ejcz',args+[c(Q(3))],base|{'ejcy':lambda *xs:False},'instance');count+=1
    refused(lambda:run('ejcz',args,base))
    return dict(cases=count,native_four_record_slots_and_exact_measurement_time=True,all_real_times_require_same_positive_length=True,native_unbounded_time_refused=True)

@lru_cache(None)
def vector_checks():
    count=0
    for velocity in ((3,0,0),(-3,0,0),(0,0,-3),(3,0,4),(0,-2,0),(0,0,0)):
        cuts,m,pos,members,fs,restfs,pop,fields,norm,vel,drift=model(velocity);c=cuts.make
        args=fields+[c(n) for n in vel]
        rows={'eiad':{norm(fields)},'eisdd':{('K','length','duration','context')}};m=relations(m,rows,norm)
        check=lambda mm:run('ejc3',args+[c(Q(0)),c(Q(1))],mm,'instance')
        count+=perturb(check,m,rows,norm)
        for axis in range(3):
            wrong=args.copy();wrong[len(fields)+axis]=c(vel[axis]+1)
            assert not run('ejc3',wrong+[c(Q(0)),c(Q(1))],m,'instance');count+=1
        # Internal member motion must fail even when both end markers agree.
        for point,axis in product(('p','q','r'),range(3)):
            drift[point,axis]=Q(1)
            mm=relations(m,{'eiad':{norm(fields)}},norm)
            assert not check(mm);count+=1;drift.clear()
        assert run('ejc3',args+[c(Q(1,3)),c(Q(5,3))],m,'instance');count+=1
        refused(lambda:run('ejc3',args,m))
    return dict(cases=count,native_all_members_all_three_signed_components=True,negative_oblique_and_zero_translation_distinguished=True,internal_member_drift_not_hidden_by_correct_endpoints=True)

@lru_cache(None)
def transverse_checks():
    count=0
    for velocity in ((3,0,0),(-3,0,0),(0,0,-3),(3,0,4)):
        cuts,m,pos,members,fs,restfs,pop,fields,norm,vel,drift=model(velocity);c=cuts.make
        base=['body','low','high','K','context'];args=base+[c(n) for n in vel]+[c(Q(2))]
        rows={'eipc':{norm(fields+['low','high'])},'ejc3':{norm(fields+[c(n) for n in vel])},'ejcz':{norm(base+[c(Q(2))])}}
        m=relations(m,rows,norm);check=lambda mm:run('ejc4',args+[c(Q(1))],mm,'instance')
        count+=perturb(check,m,rows,norm)
        for t in (0,Q(1,3),2):assert run('ejc4',args+[c(Q(t))],m,'instance');count+=1
        pos['high']=list(vel)
        assert not check(relations(m,{'eipc':{norm(fields+['low','high'])},'ejc3':{norm(fields+[c(n) for n in vel])}},norm));count+=1
        pos['high']=[Q(0)]*3
        assert not check(relations(m,{'eipc':{norm(fields+['low','high'])},'ejc3':{norm(fields+[c(n) for n in vel])}},norm));count+=1
        pos['high']=[Q(0),Q(2),Q(0)]
        refused(lambda:run('ejc4',args,m))
    cuts,m,pos,members,fs,restfs,pop,fields,norm,vel,drift=model();c=cuts.make
    restfields=fields.copy();restfields[1]='k';restfields[8:]=restfs
    args=['body','low','high','K','context','k',c(Q(2)),c(Q(3)),c(Q(0)),c(Q(0)),c(Q(2))]
    rows={'eipe':{norm(restfields+['low','high',c(Q(2))])},'ejc4':{norm(args[:5]+args[7:])}}
    m=relations(m,rows,norm);check=lambda mm:run('ejc5',args,mm);count+=perturb(check,m,rows,norm)
    sameframe=args.copy();sameframe[5]='K';assert not run('ejc5',sameframe,m|{'eipe':lambda *xs:True});count+=1
    assert not check(m|{'eislt':lambda f,u,s:c(Q(0 if f=='k' else 2))});count+=1
    unknowns(check,m,('eirh','eislu','eisls','eislt'))
    return dict(cases=count,actual_nonzero_axis_perpendicularity_in_multiple_directions=True,same_body_rest_geometry_and_current_measured_length=True)

@lru_cache(None)
def branch_checks():
    count=0
    for phi in (Q(2),Q(-2)):
        cuts,m,*_=numeric_model(scale=phi/Q(5,4));c=cuts.make;r=cuts.read
        norm=lambda xs:tuple(r(x) if isinstance(x,FunctionValue) else x for x in xs)
        rows={'ejcf':{('context',)},'ejcj':{('body','low',Q(0),'context'),('body','high',Q(2),'context')},'ejcz':{('body','low','high','K','context',Q(1))}}
        m=relations(m,rows,norm)|{'zgz':lambda:c(Q(2))}
        if phi>0:count+=perturb(lambda mm:run('ejc2',['context',c(Q(1))],mm),m,rows,norm)
        else:assert not run('ejc2',['context',c(Q(1))],m);count+=1
        assert not run('ejc2',['context',c(Q(-1))],m);count+=1
    return dict(cases=count,positive_geometric_length_not_signed_coordinate_difference=True,positive_branch_is_explicit_extra_condition_not_endpoint_theorem=True)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));math={m['id']:m for m in inv['math']};segments=[]
    hashes=('aee58b879e5440e740155c9acac7eff469407eea6ca6bf7ac21c6baa16993e28','cf4bd07c91dde070e387dfc8eea125213ae121a6741eec71b00fe989f238c551','b81d9593a3f6c4f7d125fd1da37c9b1fb180574cfb728f3db3c70eda3053e079','186b98e7b1075182c63c463ac88e784bd75033613df06f831f5756e186a55e9e')
    for u,sha in zip(inv['units'][100:104],hashes):
        assert u['text_sha256']==sha
        segments.append(dict(unit=u['id'],unit_sha256=sha,text=u['text'],range=[0,len(u['text'])],math=[dict(id=n,sha256=math[n]['sha256'],mathml_flat_text=''.join(ET.fromstring(math[n]['mathml']).itertext())) for n in u['math_ids']],source_nonblank_characters=len(re.sub(r'\s|\[M\d+\]','',u['text']))))
    assert '<mfrac' in math['M0186']['mathml']
    retrieval='artifacts/einstein-reciprocal-claim-v1/retrieval.json';saved=json.loads(read(retrieval));validate_hashes(ROOT,{r['path']:r['sha256'] for r in saved['sources']})
    paths={DOC,INVENTORY,retrieval,*(r['path'] for r in saved['sources'])}
    return dict(version='einstein-transverse-measured-length-source-reading-v1',status='dependency_reading_not_whole_unit_judgment',pages=['902'],segments=segments,observations=['同じ棒のKで測った長さがl/φ(v)であり、これで同じφの意味を与えるという第一文。','続く対称性は方向Richtungと向きSinnの両方を含み、正負速度交換だけへ縮めない。','二つの分数l/φ(v)=l/φ(−v)からoderでφの正負値の一致へ書き換える。','一般測定長は正の距離であり、符号付き商との一致には向きの読みが必要。','本依存群は同時刻測定長と一般三成分の横運動まで。設定間の比較・対称性・著者帰属・全文判断は未追加。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements']==old.document['statements'] and len(new.document['statements'])==318
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read(PRIOR));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[315,316,317])==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=parse(read(CORE));names={d['name'] for d in doc['declarations']}
    assert {'eipa','ejce','eiyx','eipc','eiad','eioh','eiu6'}<=names
    assert not names&{'za','shd','zgj','ssb','ssd','eiqg'}
    for style in ('compact','full'):
        body=format_graph(doc,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    assert source_record()==json.loads(read(SOURCE))
    return dict(new_definitions=len(MEANINGS),new_primitives=0,preserved_statements=318,prior_whole_unit_judgment_preserved=True,whole_unit_review_not_claimed=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('length',length_checks),('time',time_checks),('vector',vector_checks),('transverse',transverse_checks),('branch',branch_checks),('structure',structure_checks)]}
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,PRIOR,*DEPENDENCIES,'scripts/compose_transverse_measured_length.py','scripts/check_transverse_measured_length.py','tests/test_transverse_measured_length.py','scripts/check_transverse_segment.py','scripts/check_coordinate_correspondence.py','scripts/check_moving_trip_geometry.py','scripts/check_clock_site_time.py','scripts/check_material_relative_frame.py','scripts/check_translated_light_trial.py','scripts/check_four_coordinate_claim.py','scripts/compose_limits.py','scripts/compose_rod_methods.py','scripts/compose_material_relative_frame.py'}
    return dict(status='simultaneous_measured_length_and_general_transverse_motion_checked',document=FULL,**results,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['同じ棒・固有形状・尺度を保つ方向一般の比較設定の全範囲','同速の場合の測定長の不変性と対称性の理由の著者帰属','同じ正負速度の測定長・φの二値の一致とoderの書換え','u0101–u0104の本文接続・通読判断・登録'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
