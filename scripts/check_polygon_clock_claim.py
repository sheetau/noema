"""Check current polygon paths, shared corners, total lag and source attribution."""
from functools import lru_cache
from fractions import Fraction as Q
from itertools import product
from xml.etree import ElementTree as ET
import json,re
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import FunctionValue,SequenceValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_moving_trip_geometry import NUM
from scripts.check_clock_site_time import relation,perturb,unknowns,forbidden
from scripts.check_clock_transfer_records import physical,phase_model
from scripts.check_material_relative_frame import RS
from scripts.check_translated_light_trial import expose
from scripts.check_transverse_segment import refused
from scripts.check_rod_methods import value
from scripts.compose_polygon_clock_claim import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,INDICES,MEANINGS,PATH,COMPARE,OLD_PATH,REUSED_SOURCE,REUSED_BASIS,build

DOC='docs/polygon-clock-claim-v1.md';SOURCE='data/einstein-polygon-clock-claim-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';PRIOR='data/einstein-clock-transfer-u0126-review-v1.json'
DEPENDENCIES=('reports/clock-transfer-claim-v1.json','reports/clock-transfer-records-v1.json')
CONSTANTS={'ra':'K','ta':'length','rb':'duration','zik':'second','yn':'x','yo':'y','yp':'z','zc7':'time','rd':'author','eirf':'paper','eisn5':'section','ri':'discourse','zi7':'previous','zjb':'polygon','zjc':'return'}
DOMAIN=tuple(dict.fromkeys((*CONSTANTS.values(),'clock','reference','A','B','C','e0','e1','e2','alias','s0','s1','r0','r1','r2','initialreference','initialrecord','a','b')))
POINTS=('initial','motion','context','discourse','other')
BOUNDS={'ejkx':{'se','swo','swp','ejj5','ejka'},'ejky':{'ejj7','ejkx'},'ejkz':{'ejky'},'ejk2':{'ejj7','ejke','ejkb'},'ejk3':{'ejkz','ejk2'},'ejk4':{'ejkb'},'ejk5':{'ejk3','ejk4','ejkb'},'ejk7':{'svp'},'ejla':{'ejj7','svp','swy'},'ejlc':{'ejk3','ejla'},'ejld':{'ejk3','ejlb','ejla'},'ejle':{'ejk3','ejk5'}}

@lru_cache(None)
def core():return parse(read(CORE))

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=extract_document(core(),roots=[name],statement_indices=[]).document
    abstract(doc,NUM|{'sje','sjd','sky','zzbb','zzbd'}|BOUNDS.get(name,set()));doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name)
    if mode=='instance':
        added=expose(d,{'forall','exists'},only_sort=None if name in ('ejlc','ejld','ejle') else RS)
        assert len(added)==(len(COMPARE) if name in ('ejlc','ejld','ejle') else 1)
    slots=[]
    for i,p in enumerate(d['parameters']):
        n='jpcc'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=name,arguments=[dict(kind='call',symbol=n,arguments=[]) for n in slots])
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jpccpoint',parameters=[],result='situation'));expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='jpccpoint',arguments=[]))
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,args,m,mode='boundary',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(args)==len(slots),(name,len(args),len(slots))
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|{'jpccpoint':lambda:'discourse'}|m|{n:lambda x=x:x for n,x in zip(slots,args)}
    return evaluate_document(doc,individuals=domain,situations=POINTS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=700000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def relations(m,rows,norm):return m|{n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}

def model(closed=False):
    cuts,m,coords,fs,_=physical();c=cuts.make;r=cuts.read
    m['aa']=lambda x,y:x<y if isinstance(x,Q) and isinstance(y,Q) else forbidden()
    coords.update(r0=[0,0,0,10],r1=[15,0,0,15],r2=[0,0,0,20] if closed else [15,15,0,20])
    coords['initialrecord']=coords['r2'][:3]+[10]
    records={n:'r0' for n in DOMAIN}|{'e1':'r1','e2':'r2','alias':'r1','initialreference':'initialrecord'}
    readings={n:Q(7) for n in DOMAIN}|{'e1':Q(11),'e2':Q(15),'alias':Q(11)}
    places={n:'A' for n in DOMAIN}|{'e1':'C','alias':'C','e2':'A' if closed else 'B'}
    starts={n:'e0' for n in DOMAIN}|{'s1':'e1'};ends={n:'e1' for n in DOMAIN}|{'s1':'e2'}
    fn=lambda table,result='individual':FunctionValue(('individual',),result,lambda x:table[x] if x in table else forbidden())
    rf=fn(records);vf=FunctionValue(('individual',),RS,lambda x:c(readings[x]) if x in readings else forbidden());pf=fn(places)
    seq=lambda xs:SequenceValue(tuple(xs),'"individual"')
    a=[seq(['s0','s1']),fn(starts),fn(ends),rf,vf,pf,'clock','e0','e2',c(Q(3)),'motion','reference','e0' if closed else 'initialreference','r0' if closed else 'initialrecord',c(Q(7)),c(Q(17)),'initial']
    def normone(x):
        if isinstance(x,FunctionValue):
            if x.parameters==('number',):return r(x)
            if x.parameters==('individual',):return tuple(normone(x(n)) for n in ('e0','e1','e2','alias','s0','s1','initialreference'))
            if x.parameters==(RS,):return tuple(normone(x(c(Q(n)))) for n in (0,1,2))
            forbidden()
        return value(x)
    norm=lambda xs:tuple(normone(x) for x in xs)
    return cuts,m,coords,a,norm,dict(readings=readings,places=places,records=records,starts=starts,ends=ends,seq=seq)

@lru_cache(None)
def path_checks():
    cuts,m,coords,fs,norm,domain,base=phase_model();c=cuts.make;count=0;local=('a','b','a','b','b','context')
    rows={n:rs for n,rs in base.items() if n!='ci'}|{'swo':{norm(['a','b',c(Q(4))])},'ejj5':{local},'swp':{('b','a','b')},'ejka':{norm(['a',c(Q(1)),'context'])}}
    mm=relations(m,rows,norm);a=['a','a','b',c(Q(4)),'context',c(Q(1))];check=lambda mm:run('ejkx',a,mm,'instance',domain)
    count+=perturb(check,mm,{n:rs for n,rs in rows.items() if n!='ejj5'},norm)
    assert not check(mm|{'ejj5':relation({local,('a','a','b','a','a','context')})});count+=1
    refused(lambda:run('ejkx',a[:-1],mm,domain=domain))
    # Supplied speed, not the preceding particular transfer's global speed.
    assert check(mm|{'zb7':lambda:c(Q(3))});bad=a[:];bad[3]=c(Q(3));assert not run('ejkx',bad,mm,'instance',domain);count+=2
    cuts,m,coords,a,norm,t=model();c=cuts.make
    leg=['clock','e0','e1',a[3],a[4],a[5],a[9],'motion']
    rows={'ejj7':{norm(['clock',e,a[3](e),a[5](e),a[4](e),'motion']) for e in ('e0','e1')},'ejkx':{norm(['clock','r0','r1',a[9],'motion'])}}
    count+=perturb(lambda mm:run('ejky',leg,mm),relations(m,rows,norm),rows,norm)
    rows={'ejky':{norm(['clock',a[1](s),a[2](s),*a[3:6],a[9],'motion']) for s in ('s0','s1')}};mm=relations(m,rows,norm)
    count+=perturb(lambda mm:run('ejkz',a[:len(PATH)],mm),mm,rows,norm)
    for selected in ([],['s1','s0'],['s0','s0','s1']):
        bad=a[:len(PATH)];bad[0]=t['seq'](selected);assert not run('ejkz',bad,mm);count+=1
    # Equal numerical record and reading cannot replace identity of the corner event.
    t['ends']['s0']='alias';assert not run('ejkz',a[:len(PATH)],m|{'ejky':lambda *xs:True});count+=1
    t['ends']['s0']='e1';assert run('ejkz',a[:len(PATH)],mm);count+=1
    # Current validator executes inherited folds directly; archived reports stay historical.
    for size in (1,2,5,16):
        events=tuple('event'+str(i) for i in range(size+1));legs=tuple('leg'+str(i) for i in range(size))
        records={e:'record'+str(i) for i,e in enumerate(events)}
        domain=DOMAIN+events+legs+tuple(records.values())
        for i,e in enumerate(events):coords[records[e]]=[0,0,0,Q(i*i+3)]
        starts=dict(zip(legs,events));ends=dict(zip(legs,events[1:]));dur=Q(size*size)
        f=lambda table,result='individual':FunctionValue(('individual',),result,lambda x:table[x] if x in table else forbidden())
        p=[t['seq'](legs),f(starts),f(ends),f(records),f({e:c(Q(7)+Q(4,5)*(i*i)) for i,e in enumerate(events)},RS),f({e:'A' for e in events}),'clock',events[0],events[-1],c(Q(3)),'motion']
        assert run('ejkz',p,m|{'ejky':lambda *xs:True},domain=domain)
        assert run('ejk6',p,m,domain=domain);count+=2
        duplicate=p[:];duplicate[0]=t['seq']([legs[0],*legs])
        assert not run('ejkz',duplicate,m|{'ejky':lambda *xs:True},domain=domain)
        assert not run('ejk6',duplicate,m,domain=domain);count+=2
    return dict(cases=count,shared_current_corner_bindings=True,all_candidate_and_real_time_conditions_preserved=True,nonempty_ordered_path_not_just_matching_coordinates=True)

def setup_rows(cuts,a,norm):
    c=cuts.make;rf,vf,pf=a[3:6];ie,ir=a[12:14]
    reads=[['clock','e0','r0',pf('e0'),vf('e0'),s] for s in ('initial','motion')]+[['clock','e2','r2',pf('e2'),vf('e2'),'motion'],['reference','e2','r2',pf('e2'),a[15],'motion']]+[['reference',ie,ir,pf('e2'),a[14],s] for s in ('initial','motion')]
    return {'ejj7':set(map(norm,reads)),'ejke':{norm(['clock',pf('e0'),'r0',c(Q(0)),c(Q(10)),'initial']),norm(['reference',pf('e2'),ir,c(Q(0)),c(Q(10)),'initial']),norm(['reference',pf('e2'),ir,c(Q(10)),c(Q(20)),'motion'])},'ejkb':{norm([cl,c(Q(0)),c(Q(10)),c(Q(-3)),c(Q(1)),'initial']) for cl in ('clock','reference')}}

@lru_cache(None)
def setup_checks():
    count=0
    for closed in (False,True):
        cuts,m,coords,a,norm,t=model(closed);c=cuts.make;rows=setup_rows(cuts,a,norm);mm=relations(m,rows,norm)
        count+=perturb(lambda mm:run('ejk2',a,mm),mm,rows,norm)
        for i,j in ((6,11),(7,8),(10,16)):
            bad=a[:];bad[i]=bad[j];assert not run('ejk2',bad,mm);count+=1
        for record in ('r0',a[13]):
            coords[record][3]+=1;assert not run('ejk2',a,mm);coords[record][3]-=1;count+=1
        assert run('ejk2',a,mm|{'ejk4':forbidden,'ejk5':forbidden});count+=1
        assert run('ejlb',a[:len(PATH)],m)==closed;count+=1
        if closed:
            t['places']['e2']='B';assert not run('ejlb',a[:len(PATH)],m);t['places']['e2']='A';count+=1
            coords['r2'][0]+=1;assert not run('ejlb',a[:len(PATH)],m);coords['r2'][0]-=1;count+=1
            coords['r2'][3]=10;assert not run('ejlb',a[:len(PATH)],m);coords['r2'][3]=20;count+=1
        rows={'ejkz':{norm(a[:len(PATH)])},'ejk2':{norm(a)}}
        count+=perturb(lambda mm:run('ejk3',a,mm),relations(m,rows,norm),rows,norm)
    return dict(cases=count,return_allows_same_initial_event_and_place=True,initial_sync_reference_rest_and_arrival_bound=True)

@lru_cache(None)
def total_checks():
    count=0
    for closed in (False,True):
        cuts,m,coords,a,norm,t=model(closed);c=cuts.make;r=cuts.read;p=a[:len(PATH)]
        rows={'ejkb':{norm(['clock',c(Q(10+5*i)),c(Q(15+5*i)),c(Q(7+4*i)),c(Q(4,5)),'motion']) for i in (0,1)}}
        count+=perturb(lambda mm:run('ejk4',p,mm),relations(m,rows,norm),rows,norm)
        assert run('ejk6',p,m);count+=1
        t['readings']['e1']+=1
        assert run('ejk6',p,m) and not run('ejk4',p,m|{'ejkb':lambda *xs:True});count+=2
        t['readings']['e1']-=1
        bad=p[:];bad[0]=t['seq'](['s0','s0','s1']);assert not run('ejk6',bad,m);count+=1
        rows={'ejk3':{norm(a)},'ejk4':{norm(p)},'ejkb':{norm(['reference',c(Q(10)),c(Q(20)),c(Q(7)),c(Q(1)),'motion'])}}
        count+=perturb(lambda mm:run('ejk5',a,mm),relations(m,rows,norm),rows,norm)
        for scale in (Q(1,5),Q(1),Q(2)):
            nums=[c(scale),c(10*scale),c(2*scale),c(Q(9,5)*scale),c(Q(1,5)*scale)]
            rows={'svp':{norm([c(scale),'motion'])}};mm=relations(m,rows,norm)
            count+=perturb(lambda mm:run('ejk7',a+nums,mm),mm,rows,norm)
            for i in range(1,5):
                bad=nums[:];bad[i]=c(r(bad[i])+Q(1,7));assert not run('ejk7',a+bad,mm);count+=1
            rows|={'ejj7':{norm([cl,'e2','r2',a[5]('e2'),c(Q(val)),'motion']) for cl,val in (('clock',15),('reference',17))},'swy':{norm([c(10*scale)])}}
            mm=relations(m,rows,norm);count+=perturb(lambda mm:run('ejla',a+[c(scale)],mm,'instance'),mm,rows,norm)
            for readend in (Q(17),Q(18),Q(76,5)):
                t['readings']['e2']=readend;assert not run('ejla',a+[c(scale)],mm|{'ejj7':lambda *xs:True},'instance');count+=1
            t['readings']['e2']=Q(15)
            refused(lambda:run('ejla',a,mm))
        # Total elapsed time and exact gap are invariant under a common time/dial origin shift.
        for offset in (-100,100):
            for key in ('r0','r1','r2','initialrecord'):coords[key][3]+=offset
            for e in t['readings']:t['readings'][e]+=offset
            shifted=a[:];shifted[14:16]=[c(r(x)+offset) for x in a[14:16]]
            assert run('ejk6',shifted[:len(PATH)],m)
            assert run('ejla',shifted+[c(Q(1))],m|{'ejj7':lambda *xs:True,'svp':lambda *xs:True,'swy':lambda x:r(x)==10},'instance');count+=2
            for key in ('r0','r1','r2','initialrecord'):coords[key][3]-=offset
            for e in t['readings']:t['readings'][e]-=offset
    return dict(cases=count,shared_corner_sum_not_sufficient_for_rate_law=True,actual_total_seconds_exact_gap_estimate_and_residual_connected=True,fixed_total_duration_error_bound_and_real_scale_retained=True)

@lru_cache(None)
def scope_checks():
    cuts,m,coords,a,norm,t=model();count=0
    for name in ('ejlc','ejld','ejle'):
        target='ejk5' if name=='ejle' else 'ejla'
        for setting,closed,result in product((False,True),repeat=3):
            mm=m|{'ejk3':lambda *xs:setting,'ejlb':lambda *xs:closed,target:lambda *xs:result}
            assert run(name,a,mm,'instance')==(not(setting and (closed if name=='ejld' else True)) or result);count+=1
        # Every parameter is passed unchanged to setup and conclusion; functions compared by behavior.
        rows={'ejk3':{norm(a)},target:{norm(a)}}
        if name=='ejld':rows['ejlb']={norm(a[:len(PATH)])}
        mm=relations(m,rows,norm);count+=perturb(lambda mm:run(name,a,mm,'instance'),mm,{target:rows[target]},norm)
        for key in ('ejk3',)+(('ejlb',) if name=='ejld' else ()):
            row=next(iter(rows[key]))
            for i in range(len(row)):
                bad=tuple('wrong' if j==i else x for j,x in enumerate(row))
                assert run(name,a,mm|{key:lambda *xs,bad=bad:norm(xs)==bad,target:lambda *xs:False},'instance');count+=1
        refused(lambda:run(name,[],mm))
    return dict(cases=count,all_finite_sequences_functions_and_real_parameters_retained=True,return_case_does_not_restrict_general_antecedent=True,extra_rate_law_only_in_interpretive_content=True)

@lru_cache(None)
def presentation_checks():
    count=0
    table=(('ejlf',{'zfl':{('polygon','author','ejle','ejlc','section','discourse')}}),('ejlg',{'zc':{('polygon','author','ejkm','ejlc','section','discourse')},'uh':{('polygon','author','ejlc','section','discourse')},'zdg':{('polygon','author','ejlc','section','discourse')}}),('ejlh',{'zc':{('return','author','ejlc','ejld','section','discourse')},'uh':{('return','author','ejld','section','discourse')}}),('ejlj',{'zfl':{('polygon','author','ejle','ejlc','section','discourse')},'eir3':{('polygon','author','paper','ejli','discourse')},'ue':{('previous','polygon','discourse')}}),('ejll',{'eir3':{('return','author','paper','ejlk','discourse')},'ue':{('polygon','return','discourse')}}))
    for name,rows in table:
        mm={n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda mm:run(name,[],mm),mm,rows)
        assert run(name,[],mm|{n:forbidden for n in ('ejlc','ejld','ejle','ejkm')});count+=1
    return dict(cases=count,previous_result_extension_evident_presentation_and_return_order=True,quoted_claims_not_finitely_executed=True)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));u=inv['units'][126];assert u['id']=='einstein-1905:u0127';assert digest(u['text'].encode())==u['text_sha256'];table={m['id']:m for m in inv['math']};math=[]
    for mid,flat in zip(u['math_ids'],('A','B','A','B')):
        e=table[mid];assert re.sub(r'\s','',''.join(ET.fromstring(e['mathml']).itertext()))==flat;assert digest(e['mathml'].encode())==e['sha256'];math.append(dict(id=mid,sha256=e['sha256'],mathml_flat=flat))
    assert len(math)==len(u['math_ids'])==4
    retrieval='artifacts/einstein-origin-clock-setting-v1/retrieval.json';rr=json.loads(read(retrieval));validate_hashes(ROOT,{x['path']:x['sha256'] for x in rr['sources']})
    paths={INVENTORY,DOC,retrieval,*(x['path'] for x in rr['sources'])}
    return dict(version='einstein-polygon-clock-claim-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['904'],segments=[dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],text=u['text'],source_nonblank_characters=len(re.sub(r'\s|\[M\d+\]','',u['text'])),math=math)],observations=['原刊904頁で一文全体を再読した。Man sieht sofortの明白さ、dies Resultatの前段参照、auch dann nochの任意折れ線への拡張と、und zwar auch dann以下のA=Bでも成立する明示を確認した。','共通速さ、初期同期と到着比較、全所要時間の秒換算・近似と留保を前段から継承する。有限折れ線の折れ点では同じ出来事と指示を共有し、帰還は同じ場所への異なる時刻の到着と読む。','発進・方向転換・停止での追加指示変化を無視する読みは発話外の解釈注記へ置く。全体の意味判断は検査結果とは別に記録する。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-2]==old.document['statements'] and len(new.document['statements'])==347
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations'];assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read(PRIOR));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[343,344])==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=core();names=lambda root:{d['name'] for d in extract_document(doc,roots=[root],statement_indices=[]).document['declarations']}
    claim=names('ejlc');assert {'sxb','sxc','ejkx','ejj5','ejj7','ejkb','ejke','sxn','swy','svy'}<=claim
    assert not {'ejk4','ejk5','ejk6','ejle','ejlf','swl','swq','x4','sxl','sxm','sxp','sxq','sxr'}&claim
    assert 'ejlf' not in names('ejli') and 'ejle' in names('ejlj')
    assert not [d for d in new.document['declarations'][len(old.document['declarations']):] if d['kind']=='primitive']
    reused=parse(read(REUSED_SOURCE));prior_definitions={d['name']:d for d in reused['declarations']}
    for d in new.document['declarations']:
        if d['name'] in ('sxd','sxj','sxk'):assert d==prior_definitions[d['name']] and new.entries[d['name']]['meaning_ja']==json.loads(read(REUSED_BASIS))['definitions'][d['name']]
    for style in ('compact','full'):
        body=format_graph(doc,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    assert source_record()==json.loads(read(SOURCE))
    return dict(new_definitions=len(MEANINGS),new_primitives=0,preserved_statements=345,prior_judgments_preserved=True,additional_interval_laws_outside_author_message=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('path',path_checks),('setup',setup_checks),('total',total_checks),('scope',scope_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    helpers=('compose_clock_transfer_claim','compose_clock_transfer_records','compose_polygon_clock','compose_rod_methods','compose_solid_sphere_geometry','compose_material_relative_frame','compose_relativity_conjecture','compose_two_postulates','compose_limits','check_clock_transfer_records','check_clock_site_time','check_coordinate_correspondence','check_moving_trip_geometry','check_material_relative_frame','check_translated_light_trial','check_transverse_segment','check_rod_methods','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,PRIOR,REUSED_SOURCE,REUSED_BASIS,*DEPENDENCIES,'scripts/compose_polygon_clock_claim.py','scripts/check_polygon_clock_claim.py','tests/test_polygon_clock_claim.py',*(f'scripts/{n}.py' for n in helpers)}
    alignment=dict(segments=[dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],statements=list(INDICES),definitions=list(MEANINGS),status='explicit_interpretive_annotation') for s in source_record()['segments']])
    return dict(status='current_arbitrary_polygon_and_return_total_lag_connected',document=FULL,**results,alignment=alignment,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['u0127一文全体の通読判断と登録'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
