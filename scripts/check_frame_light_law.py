"""Check frame-specific clocks, complete light scopes and paired measurements."""
from functools import lru_cache
from fractions import Fraction as Q
from itertools import product
import json
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import FunctionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_moving_trip_geometry import NUM,numbers
from scripts.check_clock_site_time import perturb,unknowns,forbidden
from scripts.compose_frame_light_law import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,INDEX,MEANINGS,build

DOC='docs/frame-light-law-v1.md';PRIOR='data/einstein-affine-time-u0064-review-v1.json'
DEPENDENCIES=('reports/affine-time-claim-v1.json','reports/clock-site-time-v1.json','reports/second-principle-v1.json','reports/vacuum-light-postulate-v1.json')
RS=dict(kind='function',parameters=['number'],result='truth')
CONSTANTS={'ra':'frame','zbm':'moving','ta':'lengthunit','rb':'timeunit','tb':'speedunit','zc7':'time'}
DOMAIN=('s','t','u','ray','emitter','emission','start','end','frame','moving','reference','movingreference','clockstart','clockend','movingclockstart','movingclockend','placestart','placeend','movingplacestart','movingplaceend','firsttuple','lasttuple','movingfirsttuple','movinglasttuple','lengthunit','timeunit','speedunit','time','other')

@lru_cache(None)
def fixture(name):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document;boundaries=NUM|{'qo'}
    if name=='ei42':boundaries|={'eiyg','eiyi','eiyj'}
    if name=='ei43':boundaries|={'ei42','eiyf','eifw'}
    if name=='ei44':boundaries|={'ei42','eiyx','eifw'}
    if name=='ei45':boundaries|={'ei43','ei44','ei3c'}
    abstract(doc,boundaries);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jfll'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    doc['statements']=[dict(kind='ask',body=dict(kind='call',symbol=name,arguments=args))];return doc,slots

def run(name,args,m):
    doc,slots=fixture(name);assert len(args)==len(slots)
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|m|{n:lambda x=x:x for n,x in zip(slots,args)}
    return evaluate_document(doc,individuals=DOMAIN,situations=('context','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=400000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def relations(m,rows,norm):return m|{n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}

def model():
    cuts,m=numbers();c=cuts.make;r=cuts.read;rows={}
    def add(n,*row):rows.setdefault(n,set()).add(tuple(row))
    def norm(xs):return tuple(tuple(r(x(*(c(Q(a)) for a in p))) for p in ((0,0,0,0),(1,2,3,4))) if isinstance(x,FunctionValue) and len(x.parameters)==4 else r(x) if isinstance(x,FunctionValue) else x for x in xs)
    records={};tuples={};values={};refs={'frame':'reference','moving':'movingreference'}
    for seg,frame,prefix,duration,path in (('s','frame','',4,20),('t','moving','moving',5,25)):
        record={'wf':'ray','wg':'emitter','wh':'emission','wi':'start','wj':'end','wk':prefix+'clockstart','wl':prefix+'clockend','wm':prefix+'placestart','wn':prefix+'placeend','wo':Q(0),'wp':Q(duration),'wq':Q(path)};records[seg]=record
        add('wb','emitter');add('wc','ray','emitter','emission',frame,'context');add('wd' if frame=='frame' else 'we','emitter',frame,'emission','context')
        add('eiscd',seg,frame,'lengthunit','timeunit','context');add('ei42',seg,frame,'context');add('eiyf',frame,'context')
        add('eifw',seg,frame,refs[frame],Q(5),'context');add('ei43',frame,Q(5),'context')
        add('eisb5','ray',frame,'context');add('eisb6',seg,'ray','emitter','emission','start','end',frame,'lengthunit','timeunit','context');add('eisca','ray','start','end',frame,'context');add('eiscb',seg,'ray','start','end',frame,'lengthunit',Q(path),'context')
        add('eisb7',frame,refs[frame],'timeunit','context');add('eiscc',frame,'lengthunit','timeunit','speedunit','context');add('eisce',frame,'lengthunit','timeunit','context');add('ci','timeunit');add('ca',refs[frame]);add('cc',refs[frame],frame)
        for event,cl,pl,val,tup in (('start',record['wk'],record['wm'],Q(0),prefix+'firsttuple'),('end',record['wl'],record['wn'],Q(duration),prefix+'lasttuple')):
            tuples[event,frame]=tup;values[tup]=val
            add('eiyg',event,cl,pl,frame,val,'context');add('eiyi',event,pl,frame,'context');add('eiyj',event,frame,'context');add('eiyx',event,tup,frame,'context')
            add('ca',cl);add('cc',cl,frame);add('cb',event,pl,frame);add('cb',cl,pl,frame);add('ce',cl,event,frame,'timeunit',val);add('qo',cl,refs[frame],frame,'timeunit','context')
        add('ei44',seg,'ray','start','end',Q(path),frame,Q(5),'context')
    for name in ('wf','wg','wh','wi','wj','wk','wl','wm','wn','wo','wp','wq'):
        def get(s,name=name):
            if s not in records:forbidden()
            value=records[s][name];return c(value) if isinstance(value,Q) else value
        m[name]=get
    m['zbh']=lambda f,ctx:refs[f] if f in refs and ctx=='context' else forbidden()
    m['zbe']=lambda e,f,unit,ctx:c(values[tuples[e,f]]) if (e,f) in tuples and unit=='timeunit' and ctx=='context' else forbidden()
    m['zdz']=lambda e,f,ctx:tuples[e,f] if (e,f) in tuples and ctx=='context' else forbidden()
    m['zc6']=lambda tup,role:c(values[tup]) if tup in values and role=='time' else forbidden()
    fn=FunctionValue((RS,)*4,RS,lambda x,y,z,t:c(2*r(t)-Q(3,8)*r(x)))
    m|={'zd4':lambda:fn,'tc':lambda:c(Q(5))};add('ei3c',norm((fn,))[0],'context')
    return cuts,relations(m,rows,norm),rows,norm,records,values

@lru_cache(None)
def local_checks():
    cuts,m,rows,norm,records,values=model();count=0
    for seg,frame in (('s','frame'),('t','moving')):
        selected={n:{row for row in rows[n] if frame in row or n=='wb'} for n in ('wb','wc','wd','we','eiyg','eiyi','eiyj') if n in rows}
        count+=perturb(lambda mm:run('ei42',[seg,frame,'context'],mm),m,selected,norm)
        for rest,moving in product((False,True),repeat=2):
            mm=m|{'wd':lambda *xs,rest=rest:rest,'we':lambda *xs,moving=moving:moving}
            assert run('ei42',[seg,frame,'context'],mm)==(rest!=moving);count+=1
        for e in ('start','end'):
            old=m['zbe'];assert not run('ei42',[seg,frame,'context'],m|{'zbe':lambda ev,f,u,ctx,old=old,e=e:cuts.make(cuts.read(old(ev,f,u,ctx))+(1 if ev==e else 0))});count+=1
        assert run('ei42',[seg,frame,'context'],m|{'rc':forbidden,'eing':forbidden,'sjh':forbidden});count+=1
        unknowns(lambda mm:run('ei42',[seg,frame,'context'],mm),m,('wf','wg','wh','wo','wp','zbe','sca'))
    return dict(cases=count,same_emitter_can_be_rest_in_K_and_moving_in_k=True,both_current_local_readings_unique_times_and_frame_moments_bound=True,no_K_reference_or_time_getter_used_for_k=True)

@lru_cache(None)
def scope_checks():
    cuts,m,rows,norm,records,values=model();c=cuts.make;count=0
    for frame,seg in (('frame','s'),('moving','t')):
        selected={n:{row for row in rows[n] if frame in row} for n in ('eisb7','eiscc','eisce','eiscd','eifw','ei42','eiyf')}
        count+=perturb(lambda mm:run('ei43',[frame,c(Q(5)),'context'],mm),m,selected,norm)
        extra=(('u',frame,'lengthunit','timeunit','context'));extras=rows['eiscd']|{extra}
        mm=m|{'eiscd':lambda *xs:xs in extras}
        assert not run('ei43',[frame,c(Q(5)),'context'],mm);count+=1
        valid=rows['eifw']|{('u',frame,m['zbh'](frame,'context'),Q(5),'context')}
        mm|={'eifw':lambda *xs:norm(xs) in valid}
        assert not run('ei43',[frame,c(Q(5)),'context'],mm);count+=1
        alltimes=rows['ei42']|{('u',frame,'context')};mm|={'ei42':lambda *xs:xs in alltimes}
        assert run('ei43',[frame,c(Q(5)),'context'],mm);count+=1
        assert not run('ei43',[frame,c(Q(4)),'context'],m);count+=1
        unknowns(lambda mm:run('ei43',[frame,c(Q(5)),'context'],mm),m,('eifw','ei42','eiyf','eiscd','eisce','zbh'))
    return dict(cases=count,native_complete_nonempty_scope_and_same_speed_checked=True,extra_bad_segment_and_extra_missing_current_time_rejected=True,both_frames_use_their_own_reference_clock=True)

@lru_cache(None)
def segment_checks():
    cuts,m,rows,norm,records,values=model();c=cuts.make;count=0
    for seg,frame,path in (('s','frame',20),('t','moving',25)):
        selected={n:{row for row in rows[n] if frame in row} for n in ('eiscd','eifw','ei42','eiyx')}
        args=[seg,'ray','start','end',c(Q(path)),frame,c(Q(5)),'context'];count+=perturb(lambda mm:run('ei44',args,mm),m,selected,norm)
        for i,value in ((1,'other'),(2,'end'),(3,'start')):
            bad=args.copy();bad[i]=value;assert not run('ei44',bad,m);count+=1
        bad=args.copy();bad[2]='other'
        try:run('ei44',bad,m)
        except ValueError as e:assert 'Unknown clock-site-time' in str(e)
        else:raise AssertionError('Unknown event received a default coordinate record')
        bad=args.copy();bad[4]=c(Q(path+1));assert not run('ei44',bad,m);count+=1
        for e in ('start','end'):
            old=m['zc6'];tup=m['zdz'](e,frame,'context');assert not run('ei44',args,m|{'zc6':lambda t,a,tup=tup,old=old:c(cuts.read(old(t,a))+(1 if t==tup else 0))});count+=1
        unknowns(lambda mm:run('ei44',args,mm),m,('zbh','wf','wi','wj','wq','zdz','zc6'))
    return dict(cases=count,same_selected_ray_endpoints_arc_length_and_current_coordinate_times=True,each_frame_uses_its_own_measurements=True)

@lru_cache(None)
def physical_checks():
    cuts,m,rows,norm,records,values=model();c=cuts.make;count=0
    for seg,frame,path,elapsed in (('s','frame',20,4),('t','moving',25,5)):
        args=[seg,frame,m['zbh'](frame,'context'),c(Q(5)),'context']
        selected={n:{row for row in rows[n] if frame in row or n in ('ca','ci')} for n in ('eisb5','eisb6','eisca','eiscb','cc','cb','ce','qo')}
        count+=perturb(lambda mm:run('eifw',args,mm),m,selected,norm)
        assert not run('eifw',args,m|{'wq':lambda s:c(Q(path+1))});count+=1
        assert not run('eifw',args,m|{'wp':lambda s:c(Q(elapsed+1))});count+=1
        bad=args.copy();bad[2]='reference' if frame=='moving' else 'movingreference';assert not run('eifw',bad,m);count+=1
    return dict(cases=count,native_geometric_path_source_emission_local_clocks_and_rate_checked=True,different_frame_lengths_and_elapsed_times_can_share_same_V=True)

@lru_cache(None)
def pair_checks():
    cuts,m,rows,norm,records,values=model();count=perturb(lambda mm:run('ei45',['s','t','context'],mm),m,{n:rows[n] for n in ('ei3c','ei43','ei44')},norm)
    for name in ('wf','wg','wh','wi','wj'):
        old=m[name];assert not run('ei45',['s','t','context'],m|{name:lambda s,old=old:'other' if s=='s' else old(s)});count+=1
    assert not run('ei45',['s','s','context'],m);assert not run('ei45',['s','t','context'],m|{'zbm':lambda:'frame'});count+=2
    unknowns(lambda mm:run('ei45',['s','t','context'],mm),m,('tc','zd4','wq'))
    return dict(cases=count,same_ray_source_emission_and_two_events_required=True,distinct_frame_records_share_same_V_and_current_tau=True,numerical_equality_of_times_and_lengths_not_required=True)

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements']==old.document['statements'] and len(new.document['statements'])==INDEX
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read(PRIOR));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[286,287,288])==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS)
    doc=parse(read(CORE))
    for style in ('compact','full'):
        body=format_graph(doc,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    return dict(new_definitions=len(MEANINGS),new_primitives=0,preserved_statements=INDEX,prior_whole_unit_judgment_preserved=True,whole_unit_review_not_yet_claimed=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('local',local_checks),('scope',scope_checks),('segment',segment_checks),('physical',physical_checks),('pair',pair_checks),('structure',structure_checks)]}
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|{DOC,PRIOR,*DEPENDENCIES,'scripts/compose_frame_light_law.py','scripts/check_frame_light_law.py','tests/test_frame_light_law.py','scripts/check_coordinate_correspondence.py','scripts/check_moving_trip_geometry.py','scripts/check_material_relative_frame.py','scripts/check_clock_site_time.py','scripts/check_rod_methods.py','scripts/compose_limits.py','scripts/compose_material_relative_frame.py'}
    return dict(status='same_light_law_bound_to_each_frames_current_clocks',document=FULL,**results,verified_full_units={'kant-1784':0,'einstein-1905':0},general_real_physical_derivation_proved=False,remaining=['正のξ方向の全軌道と同じ原点からの放出','二原理からの帰属と容易さの評価','u0065–u0068の二式の本文接続と全文判断'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
