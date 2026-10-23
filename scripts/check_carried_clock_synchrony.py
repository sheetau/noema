"""Check carried-clock locality, complete time coverage and quoted naming."""
from copy import deepcopy
from functools import lru_cache
from fractions import Fraction as Q
import json
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import FunctionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_material_relative_frame import RS
from scripts.check_rod_methods import setup as old_setup,constants as old_constants,value,relation,DOMAIN as OLD_DOMAIN,NUM
from scripts.check_rod_length_claims import replace_real_sort
from scripts.compose_carried_clock_synchrony import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,INDICES,MEANINGS,PRIMITIVES,build
from scripts.review_carried_clock_synchrony import SOURCE,DOC,INVENTORY,PRIORS,DEPENDENCIES,source_record

RECORDS=('recorda7','recorda8','recordb7','recordb8')
DOMAIN=OLD_DOMAIN+('carrieda','carriedb','namea','nameb','syncname','addition','naming','initial','kinematicsnode','timeconvention')+RECORDS+tuple(prefix+str(i) for prefix in ('event','place','localclock','owndisplay','localdisplay') for i in range(4))
SITUATIONS=('methodactx','methodbctx','context','other')
def forbidden(*xs):raise ValueError('Unknown carried-clock-synchrony input')
def constants():return old_constants()|{n:lambda x=x:x for n,x in {'yd':'methodbctx','zaj':'carrieda','zak':'carriedb','zal':'addition','zam':'naming','y2':'initial','zv':'kinematicsnode','eisjd':'timeconvention','eismd':'syncname','eismf':'namea','eismg':'nameb'}.items()}


@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    boundaries=NUM|{'qo','se','eipk'}
    if mode=='coverage':boundaries|={'eiqz','eiq2','lg'}
    if mode=='pair':boundaries|={'eiq4'}
    if mode!='full':abstract(doc,boundaries)
    doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jccs'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    body=dict(kind='call',symbol=name,arguments=args)
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jccscontext',parameters=[],result='situation'));body=dict(kind='evaluate',content=body,situation=dict(kind='call',symbol='jccscontext',arguments=[]))
    doc['statements']=[dict(kind='ask',body=body)]
    return doc,slots


def evaluate(doc,m,domain=DOMAIN):return evaluate_document(doc,individuals=domain,situations=SITUATIONS,primitives={d['name']:m.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=1000000,memoize_definitions=True,memoize_expressions=True)[0]['value']
def run(name,args,m,mode='boundary'):
    doc,slots=fixture(name,mode);assert len(args)==len(slots)
    return evaluate(doc,m|{'jccscontext':lambda:'context'}|{n:(lambda x=x:x) for n,x in zip(slots,args)})
def unknowns(check,m,names):
    for n in names:
        try:check(m|{n:forbidden})
        except ValueError as e:assert 'Unknown carried-clock-synchrony' in str(e)
        else:raise AssertionError(('Unknown input accepted',n))


def setup():
    cuts,m,_,_,_=old_setup();c=cuts.make;r=cuts.read;m|=constants()
    def norm(xs):
        def one(x):
            if not isinstance(x,FunctionValue):return value(x)
            if x.parameters==('number',):return r(x)
            if x.result==RS:return tuple(r(x(c(Q(t)))) for t in (7,8))
            forbidden()
        return tuple(one(x) for x in xs)
    rows={n:set() for n in ('zaa','xf','xm','xg','zab','ce','cb','cc','qo','eisgm','zzbv','zzbu','se')}
    events=set();clocks={'reference','carrieda','carriedb'};record_data={}
    for i,record in enumerate(RECORDS):
        clock,end=('carrieda','firstend') if i<2 else ('carriedb','lastend');time=Q(7+i%2)
        event,place,local,own_display,local_display=(prefix+str(i) for prefix in ('event','place','localclock','owndisplay','localdisplay'))
        clocks.add(local);events.update((event,own_display,local_display));ctx='methodbctx'
        record_data[record]=(clock,end,event,place,local,time,time,ctx)
        rows['zaa'].add((clock,end,'rod',ctx));rows['xf'].add((end,'rod','frame',ctx));rows['xm'].add((clock,'frame',ctx))
        rows['xg'].add((end,event,place,'frame',ctx));rows['zab'].add((clock,event,place,'frame',ctx))
        for ck,display in ((clock,own_display),(local,local_display)):
            for ev in (event,display):rows['ce'].add((ck,ev,'frame','timeunit',time))
            rows['eisgm'].add((event,display,ck,'frame',ctx));rows['cb'].add((display,place,'frame'))
        rows['cb'].update(((local,place,'frame'),(event,place,'frame')));rows['cc'].add((local,'frame'));rows['qo'].add((local,'reference','frame','timeunit',ctx))
        x=2*(time-7)+(0 if end=='firstend' else 4)
        rows['zzbu'].add((event,'frame',ctx,'lengthunit','timeunit',time,x,Q(0),Q(0)))
        for obj in (clock,end):rows['zzbv'].add((obj,event,ctx))
    rows['cc'].add(('reference','frame'))
    for clock,end in (('carrieda','firstend'),('carriedb','lastend')):
        for obj in (clock,end):rows['se'].add((obj,'frame','methodbctx','lengthunit','timeunit',Q(6),Q(8),(Q(0 if end=='firstend' else 4),Q(2 if end=='firstend' else 6)),(Q(0),Q(0)),(Q(0),Q(0))))
    m|={n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}
    m|={'ca':lambda ck:ck in clocks,'zbd':lambda e:e in events,'ci':lambda u:u=='timeunit'}
    return cuts,m,rows,norm,record_data


@lru_cache(None)
def local_checks():
    cuts,m,rows,norm,data=setup();c=cuts.make;count=0
    def args(record):
        ck,end,event,place,local,own,t,ctx=data[record];return [ck,end,event,place,local,c(own),c(t),ctx]
    for rec in RECORDS:assert run('eiq2',args(rec),m);count+=1
    selected='recorda7';check=lambda mm:run('eiq2',args(selected),mm)
    # Only remove rows actually consumed by this comparison; later records must
    # remain usable with their own distinct places and stationary local clocks.
    relevant={
      'zaa':{('carrieda','firstend','rod','methodbctx')},'xf':{('firstend','rod','frame','methodbctx')},'xm':{('carrieda','frame','methodbctx')},
      'xg':{('firstend','event0','place0','frame','methodbctx')},'zab':{('carrieda','event0','place0','frame','methodbctx')},
      'eisgm':{row for row in rows['eisgm'] if row[0]=='event0'},'ce':{row for row in rows['ce'] if row[1] in ('event0','owndisplay0','localdisplay0')},
      'cb':{row for row in rows['cb'] if row[1]=='place0'},'cc':{('localclock0','frame'),('reference','frame')},'qo':{('localclock0','reference','frame','timeunit','methodbctx')},
      'zzbv':{row for row in rows['zzbv'] if row[1]=='event0'},'zzbu':{row for row in rows['zzbu'] if row[0]=='event0'}}
    for n,rs in relevant.items():
        for row in rs:
            assert not check(m|{n:lambda *xs,rs=rows[n]-{row}:norm(xs) in rs}),n;count+=1
            for i in range(len(row)):
                changed=tuple('other' if j==i else x for j,x in enumerate(row))
                assert not check(m|{n:lambda *xs,rs=(rows[n]-{row})|{changed}:norm(xs) in rs}),(n,i);count+=1
    wrong=args(selected);wrong[5]=c(Q(8));assert not run('eiq2',wrong,m);count+=1
    wrong=args(selected);wrong[4]='carrieda';assert not run('eiq2',wrong,m);count+=1
    assert not check(m|{'rc':lambda:'carriedb'});count+=1
    # The successful model has no carried-clock cc row and no carried-clock qo row.
    assert all(row[0] not in ('carrieda','carriedb') for row in rows['cc']|rows['qo'])
    assert check(m|{'xv':forbidden,'ya':forbidden});count+=1
    unknowns(check,m,('ce','eisgm','qo','cc','zab','eislu','zzbv','zzbu'))
    unknown=FunctionValue(('number',),'truth',lambda x:x<7);wrong=args(selected);wrong[5]=unknown
    try:run('eiq2',wrong,m)
    except ValueError:pass
    else:raise AssertionError('Unknown displayed value decoded by sampling')
    return dict(cases=count,native_scv_sct_scu_eing_saf_and_sb_connected=True,same_event_position_and_both_local_displays=True,local_stationary_clock_can_change_with_position=True,no_carried_clock_stationarity_or_direct_reference_synchrony=True)


@lru_cache(None)
def attachment_checks():
    cuts,m,rows,norm,data=setup();count=0
    for clock,end in (('carrieda','firstend'),('carriedb','lastend')):
        check=lambda mm:run('eiqz',[clock,end,'methodbctx'],mm);assert check(m);count+=1
        for obj in (clock,end):
            row=next(row for row in rows['se'] if row[0]==obj)
            assert not check(m|{'se':lambda *xs,rs=rows['se']-{row}:norm(xs) in rs});count+=1
            for i in range(len(row)):
                changed=tuple('other' if j==i else x for j,x in enumerate(row))
                assert not check(m|{'se':lambda *xs,rs=(rows['se']-{row})|{changed}:norm(xs) in rs});count+=1
        assert not check(m|{'zaa':lambda *xs:False});count+=1
        unknowns(check,m,('se','zaa','eislu','eisls','eislt'))
    return dict(cases=count,clock_position_and_endpoint_share_complete_worldline=True,physical_attachment_not_coordinate_coincidence_alone=True,clock_internal_motion_not_frozen=True)


@lru_cache(None)
def coverage_checks():
    doc,slots=fixture('eiq4','coverage');projected=replace_real_sort(deepcopy(doc));count=0
    first,second='event0','event1';rec0,rec1='recorda7','recorda8'
    # Every individual in this declared finite carrier has an explicit selector
    # entry; non-records are known inactive inputs, never unknown-data defaults.
    def model(selected=(rec0,rec1),times=None,bad=None,complete=True):
        assigned={x:first for x in DOMAIN};assigned[rec1]=second
        if times:assigned.update(times)
        m=constants()|{'jccscontext':lambda:'context','eiqz':lambda *xs:True,'zai':lambda *xs:complete,
          'zac':lambda rec,ck,ctx:rec in selected and ck=='carrieda' and ctx=='methodbctx',
          'eisls':lambda *xs:first,'eislt':lambda *xs:second,'lg':lambda lo,hi,t:(lo,hi)==(first,second) and t in (first,second),
          'sca':lambda a,b:a==b,'zah':lambda rec:assigned[rec],
          'zad':lambda rec:rec,'zae':lambda rec:'place0','zaf':lambda rec:'localclock0','zag':lambda rec:assigned[rec],
          'eiq2':lambda ck,end,event,place,local,own,t,ctx:ck=='carrieda' and end=='firstend' and event!=bad and own==t and ctx=='methodbctx'}
        m|={n:lambda x=x:x for n,x in zip(slots,('carrieda','firstend','methodbctx'))}
        return m
    for selected,times,bad,complete,expected in (
       ((rec0,rec1),None,None,True,True),((rec0,),None,None,True,False),((rec1,),None,None,True,False),((),None,None,True,False),
       ((rec0,rec1),{rec1:first},None,True,False),((rec0,rec1),None,rec1,True,False),((rec0,rec1),None,None,False,False),
       ((rec0,rec1,'recordb7'),None,'recordb7',True,False)):
        assert evaluate(projected,model(selected,times,bad,complete))==expected;count+=1
    unknowns(lambda m:evaluate(projected,m),model(),('zac','zai','zah','eiq2','eiqz'))
    # Bind the actual projected body of the time witness, including the local
    # comparison. The two-time experiment above is not used in production Noema.
    assert all(d['result']!='individual' for d in doc['declarations'] if d['name'] in ('eisls','eislt','zah'))
    # Real-cut quantification is refused after explicitly abstracting histories
    # and local comparisons, so refusal cannot be attributed only to se.
    cuts,m,_,_,_=setup();c=cuts.make
    assignments={x:Q(7) for x in DOMAIN};assignments[rec1]=Q(8)
    mm=constants()|{'eiqz':lambda *xs:True,'eiq2':lambda *xs:True,'zai':lambda *xs:True,'zac':lambda rec,ck,ctx:rec in (rec0,rec1),
       'eisls':lambda *xs:c(Q(6)),'eislt':lambda *xs:c(Q(8)),'lg':lambda lo,hi,t:cuts.read(lo)<=cuts.read(t)<=cuts.read(hi),'sca':lambda a,b:cuts.read(a)==cuts.read(b),
       'zad':lambda rec:rec,'zae':lambda rec:'place0','zaf':lambda rec:'localclock0','zag':lambda rec:c(assignments[rec]),'zah':lambda rec:c(assignments[rec])}
    try:run('eiq4',['carrieda','firstend','methodbctx'],mm,mode='coverage')
    except ValueError as e:assert 'Cannot finitely quantify the rational number domain' in str(e),str(e)
    else:raise AssertionError('Real time silently replaced by selected records')
    return dict(cases=count,every_time_requires_its_own_matching_record=True,all_selected_records_valid_and_nonempty=True,complete_record_metadata_not_sufficient_by_itself=True,finite_time_projection_only_and_full_real_domain_refused=True)


def perturb(check,m,rows):
    count=1;assert check(m)
    for n,rs in rows.items():
        for row in rs:
            assert not check(m|{n:relation(rs-{row})});count+=1
            for i in range(len(row)):
                bad=tuple('other' if j==i else x for j,x in enumerate(row))
                assert not check(m|{n:relation((rs-{row})|{bad})});count+=1
    unknowns(check,m,rows);return count


@lru_cache(None)
def pair_presentation_checks():
    rows={'eipk':{('methodbctx',)},'eiq4':{('carrieda','firstend','methodbctx'),('carriedb','lastend','methodbctx')}}
    base=constants()|{'eislv':lambda *xs:'firstend','eislw':lambda *xs:'lastend'}
    m=base|{n:relation(rs) for n,rs in rows.items()};count=perturb(lambda mm:run('eiq6',[],mm,'pair'),m,rows)
    for n in ('eislv','eislw'):
        assert not run('eiq6',[],m|{n:lambda *xs:'other'},'pair');count+=1
    assert not run('eiq6',[],m|{'zak':lambda:'carrieda','eiq4':lambda *xs:True},'pair');count+=1
    rows={
      'ug':{('addition','author','eiq6','scope','context')},'zao':{('initial','addition','scope','context')},
      'zan':{('naming','author','eiq5','frame','scope','context')},
      'eismc':{('naming','author','syncname','eiq5',('carrieda','carriedb'),'frame','scope','paper','context')},
      'eisku':{('timeconvention','eing','frame','timeunit','paper','context')},
      'eisme':{('addition','author','eiq7','eiq6','paper','context')},'eisdk':{('paper','eiq6','eiq7','context')},
      'eisd4':{('addition','author','namea','firstend','paper','context'),('addition','author','nameb','lastend','paper','context')}}
    m=base|{n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda mm:run('eita',[],mm),m,rows)
    assert run('eita',[],m|{n:forbidden for n in ('se','ce','qo','eisgm','eislu','zac','zai','eipk')});count+=1
    for path in (FULL,CORE):
        doc=parse(read(path));doc['statements']=doc['statements'][-1:]
        rows={'eir3':{('addition','author','paper','eitb','context')},'ue':{('kinematicsnode','addition','context')}}
        m=base|{n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda mm:evaluate(doc,mm),m,rows)
        assert evaluate(doc,m|{n:forbidden for n in ('ug','zao','eismc','eisme','eisdk','eisd4','ce','se')});count+=1
    return dict(cases=count,distinct_clocks_bound_to_same_axis_endpoints=True,additive_thought_setting_gloss_and_therefore_naming=True,first_section_time_rule_and_a_b_names_kept=True,quotes_do_not_execute_moving_or_stationary_clocks=True)


@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-1]==old.document['statements'] and len(new.document['statements'])==261
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    for path,index in zip(PRIORS,(259,256)):
        prior=json.loads(read(path));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[index])==prior['selection']
    for path in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(path))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);ann=json.loads(read(ANNOTATIONS))['entries'];assert ann[:-3]==json.loads(read('data/kinematic-replacement-identifiers-v1.json'))['entries']
    assert [(a['symbol'],a['forms'][0]['text']) for a in ann[-3:]]==[('eismd','synchron im ruhenden System'),('eismf','A'),('eismg','B')]
    doc=parse(read(CORE));ds={d['name']:d for d in doc['declarations']}
    assert {'scv','sct','scu','eing','saf','sae','sb','se','eipk'}<=set(ds)
    assert ds['eitb']['body']['force']=='assert' and ds['eitb']['body']['content']['symbol']=='eita'
    for style in ('compact','full'):
        text=format_graph(doc,style);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    source=json.loads(read(SOURCE));assert source==source_record();validate_hashes(ROOT,source['source_sha256'])
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),preserved_statements=260,prior_methods_and_meanings_preserved=True,original_a_b_and_qualified_synchrony_name_checked=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')


@lru_cache(None)
def build_report():
    results={n:fn() for n,fn in [('local',local_checks),('attachment',attachment_checks),('coverage',coverage_checks),('presentation',pair_presentation_checks),('structure',structure_checks)]}
    source=source_record();paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source['source_sha256'])|{SOURCE,DOC,INVENTORY,*PRIORS,*DEPENDENCIES,'scripts/compose_carried_clock_synchrony.py','scripts/check_carried_clock_synchrony.py','scripts/review_carried_clock_synchrony.py','tests/test_carried_clock_synchrony.py','scripts/check_rod_length_claims.py','scripts/check_rod_methods.py','scripts/check_coordinate_correspondence.py','scripts/check_material_relative_frame.py','scripts/check_tau_differential.py','scripts/compose_rod_methods.py','scripts/compose_material_relative_frame.py','scripts/compose_two_postulates.py','scripts/compose_relativity_conjecture.py','scripts/compose_limits.py'}
    return dict(status='carried_endpoint_clocks_and_local_rest_time_connected_and_checked',document=FULL,**results,alignment=dict(segments=[dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],definitions=list(MEANINGS),status='explicit_interpretive_annotation') for s in source['segments']]),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['u0035の全単位判断登録','u0036以降と二作品全体の目標'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
