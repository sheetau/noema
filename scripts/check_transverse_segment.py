"""Check complete-segment bodies, same histories and current endpoint records."""
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
from scripts.compose_transverse_segment import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,MEANINGS,build

DOC='docs/transverse-segment-v1.md';SOURCE='data/einstein-transverse-segment-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';PRIOR='data/einstein-reciprocal-claim-u0095-review-v1.json'
DEPENDENCIES=('reports/rod-geometry-v1.json','reports/material-axes-v1.json','reports/event-coordinate-task-v1.json','reports/reciprocal-claim-v1.json')
CONSTANTS={'ra':'K','zbm':'k','yn':'x','yo':'y','yp':'z','zc7':'time','ta':'length','rb':'duration','zgu':'body','zgv':'low','zgw':'high'}
DOMAIN=tuple(dict.fromkeys((*CONSTANTS.values(),'p','q','r','event','record','place','other')))
POINTS=('context','other')

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    bounds=NUM.copy()
    if name=='ejcb':bounds|={'eipe','ejca'}
    if name=='ejcc':bounds|={'sfb','ejcb'}
    if name=='ejcd':bounds|={'eipc','eipf'}
    if name=='ejce':bounds|={'eiyx','sb'}
    if name=='ejcf':bounds|={'ejcc','ejcd'}
    abstract(doc,bounds);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name)
    if mode=='instance':assert len(expose(d,{'forall'},only_sort=RS))==1
    slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jtsg'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    doc['statements']=[dict(kind='ask',body=dict(kind='call',symbol=name,arguments=args))];return doc,slots

def run(name,args,m,mode='boundary',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(args)==len(slots),(name,len(args),len(slots))
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|m|{n:lambda x=x:x for n,x in zip(slots,args)}
    return evaluate_document(doc,individuals=domain,situations=POINTS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=400000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def refused(check):
    try:check()
    except ValueError as e:assert 'Cannot finitely quantify' in str(e) or 'Finite function domain' in str(e),str(e)
    else:raise AssertionError('Unbounded real domain silently sampled')

def model(moving=False):
    cuts,m=numbers();c=cuts.make;r=cuts.read
    # Every table cell is explicit, including nonmembers visited by eager logic.
    positions={p:[Q(0),Q(0),Q(0)] for p in DOMAIN}
    positions.update(p=[Q(0),Q(0),Q(0)],q=[Q(0),Q(1),Q(0)],r=[Q(0),Q(2),Q(0)],low=[Q(0),Q(0),Q(0)],high=[Q(0),Q(2),Q(0)])
    members={'p','q','r'}
    def position(p,t,i):
        if p not in positions:forbidden()
        return positions[p][i]+(3*t if moving and i==0 else 0)
    fs=[FunctionValue(('individual',),FS,lambda p,i=i:FunctionValue((RS,),RS,lambda t: c(position(p,r(t),i)))) for i in range(3)]
    population=FunctionValue(('individual',),'truth',lambda p:p in members)
    frame='K' if moving else 'k'
    fields=['body',frame,'context','length','duration',c(Q(0)),c(Q(2)),population,*fs]
    def norm(xs):
        def one(x):
            if not isinstance(x,FunctionValue):return x
            if x.parameters==('number',):return r(x)
            if x.result=='truth':return tuple(x(p) for p in DOMAIN)
            if x.result==FS:return tuple(r(x(p)(c(Q(t)))) for p in DOMAIN for t in (0,1,2))
            forbidden()
        return tuple(one(x) for x in xs)
    def family(b,f,lu,tu,a,ctx):
        if (b,f,lu,tu,ctx)!=('body',frame,'length','duration','context') or a not in ('x','y','z'):forbidden()
        return fs[('x','y','z').index(a)]
    m|={'eislu':family,'eisls':lambda f,u,s:c(Q(0)) if (f,u,s)==(frame,'duration','context') else forbidden(),'eislt':lambda f,u,s:c(Q(2)) if (f,u,s)==(frame,'duration','context') else forbidden(),'eirh':lambda b,p,s:(b,s)==('body','context') and p in members}
    return cuts,m,positions,members,fs,population,fields,norm

def relations(m,rows,norm):return m|{n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}

@lru_cache(None)
def segment_checks():
    cuts,m,pos,members,fs,pop,fields,norm=model();c=cuts.make;count=0
    for x,y,z,l in product((0,1),(-1,0,1,2,3),(0,1),(0,2)):
        assert run('ejb7',[c(Q(n)) for n in (x,y,z,l)],m)==(l>0 and x==z==0 and 0<=y<=l);count+=1
    args=[pop,*fs,c(Q(1)),c(Q(2))]
    for h in (-1,0,1,2,3):assert run('ejca',args+[c(Q(h))],m,'instance',('p','q','r'));count+=1
    # Both endpoints remain correct, but the missing interior is rejected.
    members.remove('q');assert not run('ejca',args+[c(Q(1))],m,'instance',('p','q','r'));count+=1
    assert run('ejca',args+[c(Q(0))],m,'instance',('p','q','r'));count+=1;members.add('q')
    for axis,wrong in ((0,1),(1,-1),(1,3),(2,1)):
        saved=pos['q'][axis];pos['q'][axis]=Q(wrong)
        assert not run('ejca',args+[c(Q(0))],m,'instance',('p','q','r'));count+=1;pos['q'][axis]=saved
    # A point outside this snapshot's member set does not alter the segment.
    pos['other']=[Q(9)]*3;assert run('ejca',args+[c(Q(1))],m,'instance');count+=1
    refused(lambda:run('ejca',args,m,domain=('p','q','r')))
    unknowns(lambda mm:run('ejca',args+[c(Q(1))],mm,'instance'),m,('ba','bc','sca'))
    return dict(cases=count,containment_and_every_height_witness_distinguished=True,endpoints_alone_insufficient=True,native_unbounded_height_refused=True)

@lru_cache(None)
def history_checks():
    cuts,m,pos,members,fs,pop,fields,norm=model();c=cuts.make;count=0
    args=fields+['low','high',c(Q(2))];snap=[pop,*fs,c(Q(1)),c(Q(2))]
    rows={'eipe':{norm(args)},'ejca':{norm(snap)}};m=relations(m,rows,norm)
    check=lambda mm:run('ejcb',args+[c(Q(1))],mm,'instance')
    count+=perturb(check,m,rows,norm)
    for endpoint,axis in product(('low','high'),range(3)):
        pos[endpoint][axis]+=1;assert not check(relations(m,{'eipe':{norm(args)},'ejca':{norm(snap)}},norm));pos[endpoint][axis]-=1;count+=1
    # Even a permissive lower boundary cannot admit a zero-width interval.
    collapsed=args.copy();collapsed[6]=collapsed[5]
    assert not run('ejcb',collapsed+[c(Q(0))],m|{'eipe':lambda *xs:True,'ejca':lambda *xs:True},'instance');count+=1
    refused(lambda:run('ejcb',args,m))
    rows={'xa':{('body',)},'sfb':{('k','context')},'zbw':{('k','q','y','context')},'ejcb':{norm(args)}}
    m=relations(m,rows,norm)|{'zbo':lambda *xs:'q' if xs==('k','y','context') else forbidden()}
    count+=perturb(lambda mm:run('ejcc',['body','low','high','context',c(Q(2))],mm),m,rows,norm)
    unknowns(lambda mm:run('ejcc',['body','low','high','context',c(Q(2))],mm),m,('eirh','eislu','eisls','eislt','zbo'))
    return dict(cases=count,same_body_members_families_units_endpoints_and_interval=True,full_history_and_all_time_snapshot_required=True)

@lru_cache(None)
def motion_checks():
    cuts,m,pos,members,fs,pop,fields,norm=model(True);c=cuts.make;count=0
    args=['body','low','high','context',c(Q(3))]
    rows={'eipc':{norm(fields+['low','high'])},'eipf':{norm(fields+[c(Q(3))])}}
    m=relations(m,rows,norm);check=lambda mm:run('ejcd',args+[c(Q(1))],mm,'instance')
    count+=perturb(check,m,rows,norm)
    for t in (0,Q(1,3),2):assert run('ejcd',args+[c(Q(t))],m,'instance');count+=1
    for delta in (-1,1):
        pos['high'][0]=Q(delta)
        assert not check(relations(m,{'eipc':{norm(fields+['low','high'])},'eipf':{norm(fields+[c(Q(3))])}},norm));count+=1
    pos['high'][0]=Q(0);pos['high'][1]=Q(0)
    assert not check(relations(m,{'eipc':{norm(fields+['low','high'])},'eipf':{norm(fields+[c(Q(3))])}},norm));count+=1;pos['high'][1]=Q(2)
    assert not run('ejcd',args[:-1]+[c(Q(0)),c(Q(1))],m|{'eipf':lambda *xs:True},'instance');count+=1
    refused(lambda:run('ejcd',args,m))
    unknowns(check,m,('eirh','eislu','eisls','eislt'))
    # The manuscript wrapper must use the same body/ends but different l and v.
    rows={'ejcc':{('body','low','high','context',Q(2))},'ejcd':{('body','low','high','context',Q(3))}}
    m=relations(m,rows,norm)|{'zgz':lambda:c(Q(2)),'zb7':lambda:c(Q(3))}
    count+=perturb(lambda mm:run('ejcf',['context'],mm),m,rows,norm)
    return dict(cases=count,full_material_translation_and_actual_axis_perpendicularity=True,same_time_actual_endpoint_difference_and_nondegeneracy=True,native_unbounded_time_refused=True)

@lru_cache(None)
def record_checks():
    cuts,m,pos,members,fs,pop,fields,norm=model(True);c=cuts.make;count=0
    values={'x':Q(3),'y':Q(2),'z':Q(0),'time':Q(1)}
    rows={'xf':{('high','body','K','context')},'eiyx':{('event','record','K','context')},'xg':{('high','event','place','K','context')},'cb':{('event','place','K')},'sb':{('high','event','K','context','length','duration',Q(1),Q(3),Q(2),Q(0))}}
    m=relations(m,rows,norm)|{'zc6':lambda rec,role:c(values[role]) if rec=='record' and role in values else forbidden()}
    args=['body','high','event','record','K','context'];check=lambda mm:run('ejce',args,mm)
    count+=perturb(check,m,rows,norm)
    for role in values:
        values[role]+=1;assert not check(m);count+=1
        # Isolate history matching from the sb boundary.
        if role!='time':assert not check(m|{'sb':lambda *xs:True});count+=1
        values[role]-=1
    for t in (-1,3):
        values['time']=Q(t);values['x']=3*Q(t)
        assert not check(m|{'sb':lambda *xs:True});count+=1
    values.update(time=Q(1),x=Q(3))
    old=m['eislu']
    def different_time(*xs):
        f=old(*xs)
        return FunctionValue(('individual',),FS,lambda p:FunctionValue((RS,),RS,lambda t:f(p)(c(cuts.read(t)+1))))
    assert not check(m|{'eislu':different_time});count+=1
    unknowns(check,m,('zc6','eislu','eisls','eislt'))
    return dict(cases=count,same_endpoint_event_place_frame_and_current_record=True,actual_history_at_same_record_time_and_inside_interval=True,unknown_coordinates_refused=True)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));math={m['id']:m for m in inv['math']};segments=[]
    hashes=('37af5c8cda27233e5e50e43840a400603d79a4a763ccd15788ac0f2f6756bb3b','5760fb03cb677071b4fcf674bb9b6fe64433cc025cc89a6651905c877334cb58','856cc99d87343400dc05fe7d03fa666602a1d92c4fb0ee1f5ae2f0a5fb218eb8','f791ef0887a5652d5c34058d207de8c64528f25fe615e0d278b180c1651c6ad2')
    for u,sha in zip(inv['units'][96:100],hashes):
        assert u['text_sha256']==sha
        elements=[dict(id=n,sha256=math[n]['sha256'],mathml_flat_text=''.join(ET.fromstring(math[n]['mathml']).itertext())) for n in u['math_ids']]
        segments.append(dict(unit=u['id'],unit_sha256=sha,range=[0,len(u['text'])],text=u['text'],math=elements,source_nonblank_characters=len(re.sub(r'\s|\[M\d+\]','',u['text']))))
    assert '<mfrac' in math['M0179']['mathml']
    retrieval='artifacts/einstein-reciprocal-claim-v1/retrieval.json';saved=json.loads(read(retrieval));validate_hashes(ROOT,{r['path']:r['sha256'] for r in saved['sources']})
    paths={DOC,INVENTORY,retrieval,*(r['path'] for r in saved['sources'])}
    return dict(version='einstein-transverse-segment-source-reading-v1',status='dependency_reading_not_whole_unit_judgment',pages=['902'],segments=segments,observations=['M0171/M0175の保存MathMLはH。印字をkの第二軸ηの役割として読む。','0≤η≤lの全区間を理想化した線状棒として読む。両端だけで区間全体を代用しない。','M0179の分数はl/φ(v)。平坦化文字列のlφ(v)を積として読まない。','表示1はη=l側、表示2はη=0側。u0099のundは両端の列挙の接続。','意味の問い・取り上げる行為・一般端点座標・著者帰属と全文判断は未追加。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements']==old.document['statements'] and len(new.document['statements'])==315
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read(PRIOR));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[s['index'] for s in prior['selection']['statements']])==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=parse(read(CORE));names={d['name'] for d in doc['declarations']}
    assert {'eiyx','eipe','eipf','eipc','eiu6','sb','eirh'}<=names
    assert not names&{'shd','zgj','ssa'}
    for style in ('compact','full'):
        body=format_graph(doc,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    assert source_record()==json.loads(read(SOURCE))
    return dict(new_definitions=len(MEANINGS),new_primitives=0,preserved_statements=315,prior_whole_unit_judgment_preserved=True,whole_unit_review_not_claimed=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('segment',segment_checks),('history',history_checks),('motion',motion_checks),('records',record_checks),('structure',structure_checks)]}
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,PRIOR,*DEPENDENCIES,'scripts/compose_transverse_segment.py','scripts/check_transverse_segment.py','tests/test_transverse_segment.py','scripts/check_coordinate_correspondence.py','scripts/check_moving_trip_geometry.py','scripts/check_clock_site_time.py','scripts/check_material_relative_frame.py','scripts/check_translated_light_trial.py','scripts/compose_limits.py','scripts/compose_rod_methods.py','scripts/compose_rod_geometry.py','scripts/compose_material_relative_frame.py'}
    return dict(status='complete_transverse_material_segment_dependencies_checked',document=FULL,**results,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['同じφ(v)の物理的意味への問いと今という位置づけ','軸区間を取り上げる行為と同じ横棒の説明','全対象時刻にわたる両端の現在記録・二つの表示とundの接続','u0097–u0100の著者帰属・通読判断・登録'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
