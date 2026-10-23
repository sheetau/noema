"""Check trial, measured results and the same local twofold time reading."""
from functools import lru_cache
from fractions import Fraction as Q
import json
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_moving_trip_geometry import joined_model,NUM,DOMAIN
from scripts.check_rod_methods import value,relation
from scripts.compose_moving_trip_reading import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,INDICES,MEANINGS,PRIMITIVES,build
from scripts.review_moving_trip_reading import DOC,SOURCE,INVENTORY,PRIOR,DEPENDENCIES,source_record

def forbidden(*xs):raise ValueError('Unknown moving-trip-reading input')

def constants():
    return {n:lambda x=x:x for n,x in {'yd':'context','yf':'measurement','tb':'speedunit','rd':'author','eirf':'paper','ri':'discourse','xy':'scope','zal':'clocks','za2':'trialnode','za3':'resultnode','eisdy':'sectionone','eisjd':'timeconvention','eismk':'note','eisml':'anchor','eismm':'timename','ra':'frame','rb':'timeunit'}.items()}

@lru_cache(None)
def fixture(name):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    boundaries=NUM|{'eiq2','eiq4','eipk','eitm','eitk','eip6'}
    if name!='eito':boundaries.add('eito')
    abstract(doc,boundaries);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jmtr'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    expr=dict(kind='call',symbol=name,arguments=args)
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jmtrcontext',parameters=[],result='situation'));expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='jmtrcontext',arguments=[]))
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,args,m):
    doc,slots=fixture(name);assert len(args)==len(slots)
    mm=constants()|m|{'jmtrcontext':lambda:'discourse'}|{n:lambda x=x:x for n,x in zip(slots,args)}
    return evaluate_document(doc,individuals=DOMAIN+('speedunit','author','paper','scope','clocks','trialnode','resultnode','sectionone','timeconvention','note','anchor','timename'),situations=('context','measurement','discourse','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=300000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def unknowns(check,m,names):
    for n in names:
        try:check(m|{n:forbidden})
        except ValueError as e:assert 'Unknown moving-trip-reading' in str(e),str(e)
        else:raise AssertionError(('Unknown input accepted',n))

def perturb(check,m,rows,norm=lambda xs:tuple(value(x) for x in xs)):
    count=1;assert check(m)
    for n,rs in rows.items():
        for row in rs:
            assert not check(m|{n:lambda *xs,rs=rs-{row}:norm(xs) in rs}),(n,row);count+=1
            for i in range(len(row)):
                bad=tuple('other' if j==i else x for j,x in enumerate(row))
                assert not check(m|{n:lambda *xs,rs=(rs-{row})|{bad}:norm(xs) in rs}),(n,i);count+=1
    unknowns(check,m,rows);return count

@lru_cache(None)
def trial_checks():
    cuts,m,rows,norm=joined_model();rows['eitm']={('context',)};m['eitm']=relation(rows['eitm'])
    used={n:rows[n] for n in ('eitm','eipk','eiq4','eisb5','cf','cg','ch','eisca','zzbu')}
    used['zzbv']={x for x in rows['zzbv'] if x[0]=='ray'}
    # Endpoint/clock positions are already required through eiq2 in eitm;
    # this native body adds the light's membership of the same three events.
    mm=m|{'zzbv':lambda *xs:norm(xs) in used['zzbv']}
    count=perturb(lambda model:run('eito',['context'],model),mm,used,norm)
    assert run('eito',['context'],mm|{n:forbidden for n in ('tc','sdb','eith','eitk')});count+=1
    unknowns(lambda model:run('eito',['context'],model),mm,('eislu','zad','zah'))
    return dict(cases=count,native_light_membership_at_same_endpoint_events=True,no_elapsed_equations_or_constant_speed_in_initial_setting=True)

@lru_cache(None)
def result_checks():
    cuts,m,rows,norm=joined_model();c=cuts.make
    rows={'eito':{('context',)},'eitk':{('context',)},'eiscc':{('frame','lengthunit','timeunit','speedunit','context')},'ti':{('lengthunit',)},'tj':{('lengthunit','timeunit','speedunit')},'yx':{('context','measurement')},'eip6':{(Q(6),'measurement')}}
    m|=constants();m|={n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}
    count=perturb(lambda mm:run('eitp',[],mm),m,rows,norm)
    for n in ('zav','tc','yb'):
        original=cuts.read(m[n]())
        assert not run('eitp',[],m|{n:lambda x=original:c(x+1)});count+=1
    for rec in ('recorda','recordb','recordc'):
        original=m['zag']
        assert not run('eitp',[],m|{'zag':lambda r,rec=rec:c(cuts.read(original(r))+(1 if r==rec else 0))});count+=1
    assert run('eitp',[],m|{n:forbidden for n in ('ya','sbd','sbk','eip2')});count+=1
    unknowns(lambda mm:run('eitp',[],mm),m,('zag','zav','tc','yb','sah','bc','bf'))
    return dict(cases=count,native_sdi_sdb_bind_both_elapsed_times=True,current_rest_frame_measurement_and_calibrated_units=True,initial_length_and_old_principle_not_substituted=True)

@lru_cache(None)
def note_checks():
    cuts,m,rows,norm=joined_model();c=cuts.make;count=0
    for rec,t in (('recorda',Q(7)),('recordb',Q(10)),('recordc',Q(23,2))):
        assert run('eitq',[rec,c(t),'context'],m);count+=1
        assert not run('eitq',[rec,c(t+1),'context'],m);count+=1
    selected={n:{row for row in rows[n] if (n=='zac' and row[0]=='recorda') or (n=='eiq2' and row[2]=='depart')} for n in ('zac','eiq2')}
    count+=perturb(lambda mm:run('eitq',['recorda',c(Q(7)),'context'],mm),m,selected,norm)
    for n in ('zag','zah'):
        assert not run('eitq',['recorda',c(Q(7)),'context'],m|{n:lambda rec:c(Q(8))});count+=1
    # A fourth eligible record is permitted; the gloss is not an enumeration
    # restricted to departure/reflection/arrival.
    extra=m|{'zad':lambda rec:'depart','zae':lambda rec:'placea','zaf':lambda rec:'locala','zag':lambda rec:c(Q(8)),'zah':lambda rec:c(Q(8)),
      'zac':lambda rec,clock,ctx:(rec,clock,ctx)==('other','carrieda','context'),
      'eiq2':lambda *xs:norm(xs)==('carrieda','firstend','depart','placea','locala',Q(8),Q(8),'context')}
    assert run('eitq',['other',c(Q(8)),'context'],extra);count+=1
    unknowns(lambda mm:run('eitq',['recorda',c(Q(7)),'context'],mm),m,('zac','eiq2','zad','zae','zaf','zag','zah'))
    return dict(cases=count,same_value_local_time_and_moving_clock_reading=True,same_current_place_event_and_local_comparison_required=True,arbitrary_eligible_record_not_only_three_trial_records=True)

@lru_cache(None)
def presentation_checks():
    count=0
    scenarios={
      'eits':{'ug':{('trialnode','author','eitn','scope','discourse')},'zao':{('clocks','trialnode','scope','discourse')},'eismi':{('trialnode','author','sectionone','bi','paper','discourse')}},
      'eitt':{'eismj':{('resultnode','author','eitn','eiot','eitp','scope','paper','discourse')}},
      'eitr':{'eislo':{('timename','eitq','paper','discourse')},'eisku':{('timeconvention','eing','frame','timeunit','paper','discourse')}},
      'eitx':{'eir3':{('trialnode','author','paper','eitu','discourse')},'ue':{('clocks','trialnode','discourse')}},
      'eity':{'eir3':{('resultnode','author','paper','eitv','discourse')},'ue':{('trialnode','resultnode','discourse')}},
      'eitz':{'eir3':{('note','author','paper','eitw','discourse')},'eisfo':{('anchor','note','paper',Q(1),'discourse')},'eisa5':{('note','author','eitn','eitr','discourse')}}}
    for name,rows in scenarios.items():
        m=constants()|{n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda mm:run(name,[],mm),m,rows)
        assert run(name,[],m|{n:forbidden for n in ('eito','eitk','eip6','bi','eitq','eing','se','eios')});count+=1
    assert not run('eitz',[],constants()|{n:lambda *xs:True for n in ('eir3','eisfo','eisa5')}|{'eisml':lambda:'note'});count+=1
    return dict(cases=count,additional_setting_section_one_criterion_and_present_results=True,current_principle_not_necessity_or_future_prediction=True,note_number_and_exact_anchor_supplement_connected=True,quotes_do_not_execute_physics_or_clock_readings=True)

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-3]==old.document['statements'] and len(new.document['statements'])==264
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read(PRIOR));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[260])==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);assert json.loads(read(ANNOTATIONS))['entries'][:-1]==json.loads(read('data/moving-trip-geometry-identifiers-v1.json'))['entries']
    doc=parse(read(CORE));ds={d['name']:d for d in doc['declarations']}
    assert len(doc['statements'])==3
    for msg,cont in (('eitu','eits'),('eitv','eitt'),('eitw','eitr')):assert ds[msg]['body']['force']=='assert' and ds[msg]['body']['content']['symbol']==cont
    for style in ('compact','full'):
        body=format_graph(doc,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),preserved_statements=261,prior_meanings_and_review_preserved=True,source_and_math_collated=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:fn() for n,fn in [('trial',trial_checks),('result',result_checks),('note',note_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    source=source_record();paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source['source_sha256'])|{SOURCE,DOC,INVENTORY,PRIOR,*DEPENDENCIES,'scripts/compose_moving_trip_reading.py','scripts/check_moving_trip_reading.py','scripts/review_moving_trip_reading.py','tests/test_moving_trip_reading.py','scripts/check_moving_trip_geometry.py','scripts/check_rod_methods.py','scripts/check_material_relative_frame.py','scripts/check_tau_differential.py','scripts/check_coordinate_correspondence.py','scripts/compose_carried_clock_synchrony.py','scripts/compose_rod_methods.py','scripts/compose_material_relative_frame.py','scripts/compose_limits.py','scripts/compose_two_postulates.py','scripts/compose_relativity_conjecture.py'}
    return dict(status='moving_trial_results_and_time_note_connected_and_checked',document=FULL,**results,alignment=dict(segments=[dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],definitions=list(MEANINGS),status='explicit_interpretive_annotation') for s in source['segments']]),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['u0036〜u0039と注u0280の全単位判断登録','u0040以降と二作品全体の目標'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
