"""Check current transfer display witnesses, complete phases and shared endpoints."""
from functools import lru_cache
from fractions import Fraction as Q
from itertools import product
from xml.etree import ElementTree as ET
import json,re
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import FunctionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_moving_trip_geometry import NUM,norm_factory
from scripts.check_clock_site_time import relation,perturb,unknowns,forbidden
from scripts.check_origin_clock_equations import model
from scripts.check_material_relative_frame import RS
from scripts.check_translated_light_trial import expose
from scripts.check_transverse_segment import refused
from scripts.compose_clock_transfer_records import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,MEANINGS,COMMON,build

DOC='docs/clock-transfer-records-v1.md';SOURCE='data/einstein-clock-transfer-records-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';PRIOR='data/einstein-clock-seconds-u0125-review-v1.json'
DEPENDENCIES=('reports/clock-seconds-claim-v1.json','reports/clock-transfer-v1.json','reports/origin-clock-question-v1.json','reports/observer-contrast-v1.json')
CONSTANTS={'ra':'K','ta':'length','rb':'duration','yn':'x','yo':'y','yp':'z','zc7':'time'}
DOMAIN=('clock','reference','event','display','record','first','initialrecord','last','middle','A','B','K','length','duration','x','y','z','time','a','b','departure','initialreference','arrival')
POINTS=('initial','motion','context','discourse','other')
BOUNDS={'ejj5':{'ejik','sb'},'ejj6':{'ejj5'},'ejj7':{'ejj6'},'ejka':{'ejj5'},'ejkc':{'ejj6'},'ejkb':{'se','ejj5','ejj6','ejkc'},'ejkd':{'se','swo','swp','ejj5','ejka'},'ejke':{'eit2','eiyv'},'ejkf':{'ejj7','ejke','ejkb','ejkd'},'ejkg':{'ejkf','ejkb'},'ejkh':{'ejkg'},'eit2':{'se','eitf'}}

@lru_cache(None)
def core():return parse(read(CORE))

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=extract_document(core(),roots=[name],statement_indices=[]).document
    abstract(doc,NUM|{'sje','sjd','sky','zzbb','zzbd'}|BOUNDS.get(name,set()));doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name)
    if mode=='instance':assert len(expose(d,{'forall','exists'},only_sort=RS))==1
    slots=[]
    for i,p in enumerate(d['parameters']):
        n='jctr'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    doc['statements']=[dict(kind='ask',body=dict(kind='call',symbol=name,arguments=[dict(kind='call',symbol=n,arguments=[]) for n in slots]))]
    return doc,slots

def run(name,args,m,mode='boundary',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(args)==len(slots),(name,len(args),len(slots))
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|m|{n:lambda x=x:x for n,x in zip(slots,args)}
    return evaluate_document(doc,individuals=domain,situations=POINTS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=700000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def relations(m,rows,norm):return m|{n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}

def physical():
    cuts,m,coords,_=model();c=cuts.make;r=cuts.read;norm=norm_factory(cuts,(0,1,2));coords.clear();coords.update(record=[2,3,4,1],first=[2,3,4,10],initialrecord=[32,3,4,10],last=[32,3,4,20],middle=[17,3,4,15],a=[0,0,0,0],b=[0,0,0,1])
    fs={a:FunctionValue((RS,),RS,lambda t,i=i:c(Q(i))) for a,i in zip(('x','y','z'),(2,3,4))}
    def track(cl,fr,lu,tu,a,ctx):
        if cl not in DOMAIN or (fr,lu,tu)!=('K','length','duration') or a not in fs or ctx not in POINTS:forbidden()
        return fs[a]
    def coord(rec,axis):
        if rec not in coords or axis not in ('x','y','z','time'):forbidden()
        return c(Q(coords[rec][('x','y','z','time').index(axis)]))
    m|={'eismh':track,'zc6':coord,'zc5':lambda rec:rec in coords,'eisls':lambda *xs:c(Q(0)),'eislt':lambda *xs:c(Q(10 if xs[-1]=='initial' else 20))}
    return cuts,m,coords,fs,norm

@lru_cache(None)
def local_checks():
    cuts,m,coords,fs,norm=physical();c=cuts.make;count=0
    a=['clock','event','display','record','A','context']
    rows={'ejik':{('clock','event','display','record','A','K','context')},'sb':{norm(['clock','event','K','context','length','duration',c(Q(1)),c(Q(2)),c(Q(3)),c(Q(4))])}}
    mm=relations(m,rows,norm);check=lambda mm:run('ejj5',a,mm);count+=perturb(check,mm,rows,norm)
    for i in range(3):coords['record'][i]+=1;assert not check(mm);coords['record'][i]-=1;count+=1
    assert check(mm|{'ce':forbidden});count+=1;unknowns(check,mm,('zc6','eismh'))
    rows={'ejj5':{tuple(a)},'ce':{norm(['clock',ev,'K','duration',c(Q(7))]) for ev in ('event','display')}}
    mm=relations(m,rows,norm);check=lambda mm:run('ejj6',a[:-1]+[c(Q(7)),a[-1],c(Q(7))],mm,'instance')
    count+=perturb(check,mm,rows,norm)
    for ev in ('event','display'):
        bad=rows['ce']|{norm(['clock',ev,'K','duration',c(Q(8))])}
        assert not run('ejj6',a[:-1]+[c(Q(7)),a[-1],c(Q(8))],mm|{'ce':lambda *xs:norm(xs) in bad},'instance');count+=1
    assert run('ejj6',a[:-1]+[c(Q(7)),a[-1],c(Q(8))],mm,'instance');count+=1
    refused(lambda:run('ejj6',a[:-1]+[c(Q(7)),a[-1]],mm))
    return dict(cases=count,current_record_actual_track_and_both_local_readings=True,all_alternative_readings_unique=True,reading_value_does_not_select_candidates=True)

@lru_cache(None)
def binding_checks():
    cuts,m,coords,fs,norm=physical();c=cuts.make;domain=('a','b');m|={'zc7':lambda:'a','zc6':lambda rec,axis:c(Q(domain.index(rec))) if rec in domain and axis=='a' else forbidden()};count=0
    for di in domain:
        rows={'ejj6':{norm(['a','b',di,'a','b',c(Q(7)),'context'])}};mm=relations(m,rows,norm)
        count+=perturb(lambda mm:run('ejj7',['a','b','a','b',c(Q(7)),'context'],mm,domain=domain),mm,rows,norm)
    for ev,di,rec,pl in product(domain,repeat=4):
        t=c(Q(domain.index(rec)));local=['a',ev,di,rec,pl,'context'];rows={'ejj5':{tuple(local)}};mm=relations(m,rows,norm)
        count+=perturb(lambda mm:run('ejka',['a',t,'context'],mm,domain=domain),mm,rows,norm)
        wrong=c(Q(1-domain.index(rec)));assert not run('ejka',['a',wrong,'context'],mm,domain=domain);count+=1
        rows={'ejj6':{norm(local[:-1]+[c(Q(7)),local[-1]])}};mm=relations(m,rows,norm)
        count+=perturb(lambda mm:run('ejkc',['a',t,c(Q(7)),'context'],mm,domain=domain),mm,rows,norm)
        for at,val in ((wrong,c(Q(7))),(t,c(Q(8)))):assert not run('ejkc',['a',at,val,'context'],mm,domain=domain);count+=1
    return dict(cases=count,shared_four_witnesses_every_slot=True,time_and_reading_not_separate_witnesses=True)

def phase_model():
    cuts,m,coords,fs,norm=physical();c=cuts.make;domain=('a','b')
    # Only the individual binding uses two values. Functions and times retain their declared sorts.
    m|={'ra':lambda:'a','ta':lambda:'b','rb':lambda:'b','yn':lambda:'a','yo':lambda:'a','yp':lambda:'a','zc7':lambda:'a',
        'zc6':lambda rec,axis:c(Q(domain.index(rec))) if rec in domain and axis=='a' else forbidden(),
        'eismh':lambda *xs:fs['x'],'eisls':lambda *xs:c(Q(0)),'eislt':lambda *xs:c(Q(1))}
    hist=['a','a','context','b','b',c(Q(0)),c(Q(1)),fs['x'],fs['x'],fs['x']]
    rows={'ca':{('a',)},'ci':{('b',)},'eisdf':{('a','context')},'eisdd':{('a','b','b','context')},'se':{norm(hist)}}
    return cuts,m,coords,fs,norm,domain,rows

@lru_cache(None)
def rate_checks():
    cuts,m,coords,fs,norm,domain,base=phase_model();c=cuts.make;count=0
    for rate,origin,t in product((Q(1),Q(4,5)),(Q(-3),Q(7)),(Q(0),Q(1))):
        local=('a','b','a','b','b','context');value=origin+rate
        rows=base|{'ejj5':{local},'ejj6':{norm([*local[:-1],c(value),local[-1]])},'ejkc':{norm(['a',c(t),c(origin+rate*t),'context'])}}
        mm=relations(m,rows,norm);a=['a',c(Q(0)),c(Q(1)),c(origin),c(rate),'context',c(t)];check=lambda mm:run('ejkb',a,mm,'instance',domain)
        # Candidate membership is a restriction; remove its matching law, not the candidate, to test it.
        required={n:rs for n,rs in rows.items() if n!='ejj5'};count+=perturb(check,mm,required,norm)
        bad=('a','a','b','a','a','context');assert not check(mm|{'ejj5':relation({local,bad})});count+=1
        refused(lambda:run('ejkb',a[:-1],mm,domain=domain))
    # An out-of-interval point does not weaken either the nonempty phase or the every-record law.
    a=['a',c(Q(0)),c(Q(1)),c(Q(7)),c(Q(1)),'context',c(Q(2))]
    mm=relations(m,base|{'ejj5':set(),'ejj6':set(),'ejkc':set()},norm)
    assert run('ejkb',a,mm,'instance',domain);count+=1
    for badlo,badhi,badrate in ((0,0,1),(1,0,1),(0,1,0),(0,1,-1)):
        bad=a[:];bad[1:3]=[c(Q(badlo)),c(Q(badhi))];bad[4]=c(Q(badrate));assert not run('ejkb',bad,mm,'instance',domain);count+=1
    return dict(cases=count,complete_history_every_candidate_and_every_time=True,common_origin_and_rate_across_phase=True,real_time_quantifier_preserved=True)

@lru_cache(None)
def path_checks():
    cuts,m,coords,fs,norm,domain,base=phase_model();c=cuts.make;count=0;local=('a','b','a','b','b','context')
    rows={n:rs for n,rs in base.items() if n!='ci'}|{'swo':{norm(['a','b',c(Q(3))])},'ejj5':{local},'swp':{('b','a','b')},'ejka':{norm(['a',c(Q(1)),'context'])}}
    mm=relations(m,rows,norm);check=lambda mm:run('ejkd',['a','a','b','context',c(Q(1))],mm,'instance',domain)
    count+=perturb(check,mm,{n:rs for n,rs in rows.items() if n!='ejj5'},norm)
    bad=('a','a','b','a','a','context');assert not check(mm|{'ejj5':relation({local,bad})});count+=1
    refused(lambda:run('ejkd',['a','a','b','context'],mm,domain=domain))
    # Native reusable numerical path conditions, including non-axial directions and negative times.
    cuts,m,coords,fs,norm=physical();c=cuts.make
    for t0,displacement in product((-20,10),((30,0,0),(-30,0,0),(18,24,0),(0,0,-30))):
        start=[2,3,4,t0];end=[start[i]+displacement[i] for i in range(3)]+[t0+10]
        coords['first']=start;coords['last']=end;coords['middle']=[Q(a+b,2) for a,b in zip(start,end)]
        assert run('swo',['first','last',c(Q(3))],m);assert run('swp',['middle','first','last'],m);count+=2
        for axis in range(3):
            coords['middle'][axis]+=1;assert not run('swp',['middle','first','last'],m);coords['middle'][axis]-=1;count+=1
        coords['middle'][3]+=1;assert not run('swp',['middle','first','last'],m);coords['middle'][3]-=1;count+=1
        for speed in (0,-3,4):assert not run('swo',['first','last',c(Q(speed))],m);count+=1
        for at in (t0-1,t0+11):coords['middle'][3]=at;assert not run('swp',['middle','first','last'],m);count+=1
    return dict(cases=count,current_all_record_path_and_time_existence_bound=True,native_three_dimensional_uniform_path_checked=True,endpoint_only_detours_and_nonuniform_progress_rejected=True)

@lru_cache(None)
def rest_checks():
    cuts,m,coords,fs,norm=physical();c=cuts.make;count=0
    a=['clock','A','record',c(Q(0)),c(Q(2)),'context'];hist=['clock','K','context','length','duration',*a[3:5],*fs.values()]
    rows={'ca':{('clock',)},'eisdf':{('clock','context')},'eit2':{norm(hist)},'eiyv':{('record','A','K','context')}};mm=relations(m,rows,norm);check=lambda mm:run('ejke',a,mm)
    count+=perturb(check,mm,rows,norm)
    for axis in range(3):coords['record'][axis]+=1;assert not check(mm);coords['record'][axis]-=1;count+=1
    unknowns(check,mm,('eismh','zc6','eisls','eislt'))
    # The inherited rest body keeps actual and constant histories on the same phase.
    rows={'eisdd':{('K','length','duration','context')},'se':{norm(hist)},'eitf':{norm(hist[:7]+[c(Q(n)) for n in (2,3,4,0,0,0)])}}
    mm=relations(m,rows,norm);count+=perturb(lambda mm:run('eit2',hist,mm),mm,rows,norm)
    for hi in (0,-1):bad=hist[:];bad[6]=c(Q(hi));assert not run('eit2',bad,mm);count+=1
    return dict(cases=count,rest_is_complete_representative_history_at_same_place=True,initial_and_motion_phases_are_separate=True)

def setup_model():
    cuts,m,coords,fs,norm=physical();c=cuts.make
    a=['clock','reference','A','B','departure','initialreference','arrival','first','initialrecord','last',c(Q(7)),c(Q(7)),c(Q(15)),c(Q(17)),'initial','motion']
    reads=[('clock','departure','first','A',7,'initial'),('reference','initialreference','initialrecord','B',7,'initial'),('clock','departure','first','A',7,'motion'),('clock','arrival','last','B',15,'motion'),('reference','arrival','last','B',17,'motion')]
    rows={'ejj7':{norm([*r[:4],c(Q(r[4])),r[5]]) for r in reads},'ejke':{norm(['clock','A','first',c(Q(0)),c(Q(10)),'initial']),norm(['reference','B','initialrecord',c(Q(0)),c(Q(10)),'initial']),norm(['reference','B','initialrecord',c(Q(10)),c(Q(20)),'motion'])},'ejkb':{norm([cl,c(Q(0)),c(Q(10)),c(Q(-3)),c(Q(1)),'initial']) for cl in ('clock','reference')},'ejkd':{('clock','first','last','motion')}}
    return cuts,m,coords,fs,norm,a,rows

@lru_cache(None)
def setup_checks():
    cuts,m,coords,fs,norm,a,rows=setup_model();c=cuts.make;mm=relations(m,rows,norm);count=perturb(lambda mm:run('ejkf',a,mm),mm,rows,norm)
    for i,j in ((0,1),(2,3),(4,5),(4,6),(5,6),(14,15)):
        bad=a[:];bad[i]=bad[j];assert not run('ejkf',bad,mm);count+=1
    for name,axis in (('first',3),('initialrecord',3),('last',3)):
        previous=coords[name][axis];coords[name][axis]=previous+1 if name!='last' else 10
        assert not run('ejkf',a,mm);coords[name][axis]=previous;count+=1
    assert run('ejkf',a,mm|{'svm':forbidden,'ejkg':forbidden});count+=1
    rows={'ejkf':{norm(a)},'ejkb':{norm(['clock',c(Q(10)),c(Q(20)),c(Q(7)),c(Q(4,5)),'motion']),norm(['reference',c(Q(10)),c(Q(20)),c(Q(7)),c(Q(1)),'motion'])}}
    mm=relations(m,rows,norm);count+=perturb(lambda mm:run('ejkg',a,mm),mm,rows,norm)
    mm=m|{'ejkg':lambda *xs:norm(xs)==norm(a)};assert run('ejkh',a,mm);count+=1
    # Native endpoint laws distinguish reset, reference rate and nonpositive elapsed time.
    for i in range(10,14):bad=a[:];bad[i]=c(cuts.read(a[i])+1);assert not run('ejkh',bad,m|{'ejkg':lambda *xs:True});count+=1
    for offset in (-100,100):
        shifted=a[:];shifted[10:14]=[c(cuts.read(x)+offset) for x in a[10:14]];assert run('ejkh',shifted,m|{'ejkg':lambda *xs:True});count+=1
    for speed in (-4,-3,0,3,4):
        cuts2,mm,_,_=model(speed);cc=cuts2.make;f=Q(3,5) if abs(speed)==4 else Q(4,5) if abs(speed)==3 else Q(1)
        # Reuse one fixture's cuts for the exposed arithmetic; a new speed is sufficient.
        vals=a[:];vals[12]=c(7+10*f);assert run('ejkh',vals,m|{'zb7':lambda:c(Q(speed)),'ejkg':lambda *xs:True});count+=1
    return dict(cases=count,initial_sync_straight_motion_and_same_arrival_bound=True,whole_phase_laws_are_explicit_interpretive_premises=True,native_endpoint_differences_and_common_offsets=True)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));u=inv['units'][125];assert u['id']=='einstein-1905:u0126';assert digest(u['text'].encode())==u['text_sha256'];table={m['id']:m for m in inv['math']}
    expected=['A','B','K','A','v','B','B','A','B','B','12tv2/V2','t','A','B'];math=[]
    for mid,flat in zip(u['math_ids'],expected):
        e=table[mid];assert re.sub(r'\s','',''.join(ET.fromstring(e['mathml']).itertext()))==flat,(mid,e['mathml']);math.append(dict(id=mid,sha256=e['sha256'],mathml_flat=flat))
    retrieval='artifacts/einstein-origin-clock-setting-v1/retrieval.json';rr=json.loads(read(retrieval));validate_hashes(ROOT,{x['path']:x['sha256'] for x in rr['sources']});paths={INVENTORY,DOC,retrieval,*(x['path'] for x in rr['sources'])}
    return dict(version='einstein-clock-transfer-records-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['904'],segments=[dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],text=u['text'],source_nonblank_characters=len(re.sub(r'\s|\[M\d+\]','',u['text'])),math=math)],observations=['原刊904頁でHieraus ergibt sich以下の二文を通読した。前の単位秒の遅れからの帰結、eigentümliche、A/B/K、初期同期、速さvでの連結直線上の移送、到着時の非同期と初めからBにある時計との比較、½tv²/V²秒、四次以上の留保、所要時間tの説明を確認した。','今回は現在表示と全初期・移送区間の履歴・指示法則を構成した依存群。到着差の秒換算、近似と留保、評価と帰属は後続であり、一単位全体の意味判断は未実施。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements']==old.document['statements'] and len(new.document['statements'])==343
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations'];assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read(PRIOR));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[341,342])==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=core();names={d['name'] for d in extract_document(doc,roots=['ejkh'],statement_indices=[]).document['declarations']}
    assert {'ejik','eiyw','sb','se','eit2','ejj5','ejkb','swp','swo','ejis'}<=names
    assert not {'swm','swq','swl','x4','zac','zdz','svc'}&names
    assert not [d for d in new.document['declarations'][len(old.document['declarations']):] if d['kind']=='primitive']
    for style in ('compact','full'):
        body=format_graph(doc,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    assert source_record()==json.loads(read(SOURCE))
    return dict(new_definitions=len(MEANINGS),new_primitives=0,preserved_statements=343,prior_selections_and_meanings_preserved=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('local',local_checks),('binding',binding_checks),('rate',rate_checks),('path',path_checks),('rest',rest_checks),('setup',setup_checks),('structure',structure_checks)]}
    helpers=('compose_clock_transfer','compose_origin_clock_question','compose_rod_methods','compose_solid_sphere_geometry','compose_material_relative_frame','compose_limits','check_clock_site_time','check_origin_clock_equations','check_coordinate_correspondence','check_moving_trip_geometry','check_material_relative_frame','check_translated_light_trial','check_transverse_segment','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,PRIOR,*DEPENDENCIES,'scripts/compose_clock_transfer_records.py','scripts/check_clock_transfer_records.py','tests/test_clock_transfer_records.py',*(f'scripts/{n}.py' for n in helpers)}
    return dict(status='current_transfer_displays_complete_phase_histories_and_rate_laws_connected',document=FULL,**results,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['u0126の秒換算・二次近似・四次の留保・前段参照・評価・著者帰属・全体通読判断'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
