"""Check actual 3-D slow acceleration and a nonassertive dynamics heading."""
from scripts.compose_tenth_section_heading import *
from fractions import Fraction as Q
import json,re
from noema.finite_semantics import evaluate_document,FunctionValue,Content
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts import check_experimental_relation_tests as prior
from scripts import check_point_particle_dynamics as old
from scripts.check_clock_site_time import relation,perturb
from scripts.check_ninth_section_opening import lifted
from scripts.check_problem_series_reduction import collapse

DOC='docs/tenth-section-heading-v1.md';SOURCE='data/einstein-tenth-section-heading-reading-v1.json'
INVENTORY=prior.INVENTORY;FACSIMILE=prior.FACSIMILE
DEPENDENCIES=('reports/point-particle-dynamics-v1.json','reports/electron-kinetic-work-v1.json','reports/electron-transformed-dynamics-v1.json','reports/complete-motion-expression-v1.json','reports/seventh-section-heading-v1.json')
CONSTANTS=prior.CONSTANTS|{'eisxg':'section','eisxm':'heading','eiswv':'previous','eisxa':'following','eispb':'part','eirf':'paper','ri':'case','ra':'frame','eisxh':'matter'}
PEOPLE=tuple(dict.fromkeys([*prior.PEOPLE,*old.PEOPLE,*CONSTANTS.values(),'inquiry','scope']));SCENES=('case','other','assessment')
BOUNDS={'evg':{'senz','sepn','sjs'},'evh':{'ek3p','evg'},'evi':{'ek34','evh'},'evj':{'evi'},'evk':{'evj','elm'},'evl':{'evk'}}
forbidden=prior.forbidden;reject=prior.reject;walk=prior.walk
@lru_cache(None)
def core():return parse(read(CORE))
@lru_cache(None)
def boundary(root,mode='native'):
    doc=extract_document(core(),roots=[root],statement_indices=[]).document
    cuts=prior.NUM|BOUNDS.get(root,set())|({'evf'} if mode=='finite' else set())
    for i,d in enumerate(doc['declarations']):
        if d['kind']=='definition' and d['name'] in cuts:doc['declarations'][i]=dict(kind='primitive',name=d['name'],parameters=[p['sort'] for p in d['parameters']],result=d['result'])
    doc=extract_document(doc,roots=[root],statement_indices=[]).document
    if mode=='instance':
        d=next(d for d in doc['declarations'] if d['name']==root)
        if d['result']=='content':b=d['body'];d['parameters']=[dict(name=b['variable'],sort='situation')];d['body']=b['body'];d['result']='truth'
        def expose(x):
            if isinstance(x,list):return [expose(y) for y in x]
            if not isinstance(x,dict):return x
            if x.get('kind') in ('exists','forall'):d['parameters'].append(dict(name=x['variable'],sort=x['sort']));return expose(x['body'])
            return {k:expose(v) for k,v in x.items()}
        d['body']=expose(d['body'])
    return doc
@lru_cache(None)
def fixture(root,mode='native'):
    doc=deepcopy(boundary(root,mode));d=next(d for d in doc['declarations'] if d['name']==root);slots=[]
    for i,p in enumerate(d['parameters']):
        n='jthslot'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=root,arguments=[dict(kind='call',symbol=n,arguments=[]) for n in slots])
    if d['result']=='content':
        if not any(d['name']=='ri' for d in doc['declarations']):doc['declarations'].append(dict(kind='primitive',name='ri',parameters=[],result='situation'))
        expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='ri',arguments=[]))
    doc['declarations'].sort(key=lambda d:d['kind']!='primitive');doc['statements']=[dict(kind='ask',body=expr)];return doc,slots
def run(root,vs,m,mode='native'):
    doc,slots=fixture(root,mode);assert len(vs)==len(slots),(root,len(vs),len(slots))
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|m|{n:lambda x=x:x for n,x in zip(slots,vs)}
    return evaluate_document(doc,individuals=PEOPLE,situations=SCENES,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=300000,memoize_definitions=True,memoize_expressions=True)[0]['value']

@lru_cache(None)
def magnitude_checks():
    a=prior.rad.model();c=a.c;cases=0
    for xs,b,want in [((0,0,0),1,True),((3,4,0),6,True),((3,4,0),5,False),((-3,-4,0),6,True),((4,4,0),5,False),((0,0,6),5,False),((0,0,0),0,False),((0,0,0),-1,False),((1,2,2),Q(31,10),True),((1,2,2),3,False)]:
        assert run('evf',[c(x) for x in (*xs,b)],a.m)==want;cases+=1
    return dict(cases=cases,euclidean_three_component_bound_not_componentwise=True,strict_positive_bound_and_sign_invariance=True)
@lru_cache(None)
def derivative_checks():
    cases=0
    for speed,accs in [(0,(1,2,3)),(4,(Q(1,10),Q(-1,10),0)),(3,(-2,0,2))]:
        a=prior.rad.model();c=a.c;polys=[prior.rad.physical.Rational((0,speed,Q(accs[0],2))),prior.rad.physical.Rational((0,0,Q(accs[1],2))),prior.rad.physical.Rational((0,0,Q(accs[2],2))),prior.rad.physical.Rational((0,1))]
        a.by.update(curve=a.register_curve(polys),time=c(0),**{n:c(x) for (n,t),x in zip(particle.ACCEL,accs)})
        a.by.update({n:a.register_function(p.derivative()) for (n,t),p in zip(particle.PROFILES,polys)})
        vs=a.values(LOCAL);assert run('evg',vs,a.m);cases+=1
        for n,t in particle.ACCEL:
            bad=vs.copy();bad[[n for n,t in LOCAL].index(n)]=c(a.r(a.by[n])+1);assert not run('evg',bad,a.m);cases+=1
        bad=vs.copy();bad[[n for n,t in LOCAL].index('velocityy')]=a.register_function(prior.rad.physical.Rational((1,)));assert not run('evg',bad,a.m);cases+=1
    return dict(cases=cases,actual_polynomial_first_and_second_derivatives=True,three_axes_and_same_velocity_profiles_required=True,large_speed_does_not_mean_large_acceleration=True)
@lru_cache(None)
def physical_checks():
    a=prior.rad.model();c=a.c;by=a.by;by.update(bound=c(5),scope='scope',time=c(0),point=by['location'],ax=c(3),ay=c(3),az=c(0));cases=0
    rows={'ek3p':[a.values(particle.HISTORY)],'eiszx':[[by[n] for n in ('frame','lengthunit','timeunit','bound','scope','context')]],'evg':[a.values(LOCAL)]}
    m=a.m|prior.table(a,rows);vs=a.values(SLOW)+[by[n] for n,t in [('time',R)]+particle.ACCEL]
    assert run('evh',vs,m,'instance');cases+=1
    for name in rows:
        assert not run('evh',vs,m|{name:lambda *xs:False},'instance');reject(lambda:run('evh',vs,m|{name:forbidden},'instance'));cases+=2
    bad=vs.copy();bad[[n for n,t in SLOW].index('bound')]=c(4);assert not run('evh',bad,m|{'eiszx':lambda *xs:True},'instance');cases+=1
    reject(lambda:run('evh',a.values(SLOW),m));cases+=1
    by,m,c,r,key=old.setup();by=by|{'bound':c(10)};vs=[by[n] for n,t in SETTING]
    row1=key([by[n] for n,t in particle.SETTING]);row2=key([by.get(n,'section') for n,t in SLOW]);m|={'ek34':lambda *xs:key(xs)==row1,'evh':lambda *xs:key(xs)==row2}
    assert run('evi',vs,m);cases+=1
    for n in ('ek34','evh'):assert not run('evi',vs,m|{n:lambda *xs:False});cases+=1
    return dict(cases=cases,complete_history_calibration_and_degree_criterion_required=True,same_particle_and_motion_in_modifier=True,unknown_real_domain_refused=True,no_radiation_condition_added=True)

@lru_cache(None)
def time_binding_checks():
    doc=deepcopy(boundary('evh','finite'));real=prior.sort(R)
    def scalars(x):
        if x==real:return 'individual'
        if isinstance(x,list):return [scalars(y) for y in x]
        if isinstance(x,dict):return {k:scalars(v) for k,v in x.items()}
        return x
    doc=scalars(doc);d=next(d for d in doc['declarations'] if d['name']=='evh');slots=[]
    def fake(t):
        if isinstance(t,dict) and t.get('kind')=='function':return FunctionValue(tuple(t['parameters']),t['result'],lambda *xs:fake(t['result']))
        return 'case' if t=='situation' else True if t=='truth' else Q(1) if t=='number' else 'a'
    constants={}
    for i,p in enumerate(d['parameters']):
        n='jthfinite'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));constants[n]=fake(p['sort'])
    doc['declarations'].sort(key=lambda d:d['kind']!='primitive');doc['statements']=[dict(kind='ask',body=dict(kind='call',symbol='evh',arguments=[dict(kind='call',symbol=n,arguments=[]) for n in slots]))]
    cases=0;domain_slot=slots[[n for n,t in SLOW].index('domain')]
    def evaluate(pivot,omit=False,bad=False):
        m={x['name']:lambda *xs,t=x['result']:fake(t) for x in doc['declarations'] if x['kind']=='primitive'}|{n:lambda x=x:x for n,x in constants.items()}
        m[domain_slot]=lambda:FunctionValue(('individual',),'truth',lambda x:x=='a' or not omit)
        m.update(ek3p=lambda *xs:True,eiszx=lambda *xs:True,ba=lambda *xs:True,bg=lambda *xs:True)
        def actual(*xs):
            expected=['a']*3
            if xs[5]=='b':expected[pivot]='b'
            return list(xs[-3:])==expected
        m['evg']=actual;m['evf']=lambda ax,ay,az,bound:not bad or (ax,ay,az)[pivot]=='a'
        return evaluate_document(doc,individuals=('a','b'),situations=('case','other'),primitives=m,max_steps=30000)[0]['value']
    for pivot in range(3):
        assert evaluate(pivot);assert not evaluate(pivot,bad=True);assert evaluate(pivot,omit=True,bad=True);cases+=3
    return dict(cases=cases,second_time_failure_not_hidden_by_first_success=True,every_acceleration_slot_bound_to_actual_derivative=True,finite_binding_probe_separate_from_real_evaluation=True)

@lru_cache(None)
def setting_binding_checks():
    doc=boundary('evj');d=next(d for d in doc['declarations'] if d['name']=='evj');point=d['body']['variable'];body=d['body']['body'];names={}
    for n,t in VARIABLES:assert body['kind']=='exists';names[n]=body['variable'];body=body['body']
    fixed={'frame':dict(kind='call',symbol='ra',arguments=[]),'context':dict(kind='variable',name=point),'electricconversion':dict(kind='call',symbol='bb',arguments=[dict(kind='number',numerator=1,denominator=1)])}
    expected=[fixed[n] if n in fixed else dict(kind='variable',name=names['location' if n=='point' else n]) for n,t in SETTING]
    assert body['symbol']=='evi' and body['arguments']==expected
    def replace(x):
        if isinstance(x,list):return [replace(y) for y in x]
        if not isinstance(x,dict):return x
        if x.get('kind')=='call' and x.get('symbol')=='bb':return dict(kind='call',symbol='jthone',arguments=[])
        return {k:replace(v) for k,v in x.items()}
    doc=replace(doc);doc['declarations'].insert(0,dict(kind='primitive',name='jthone',parameters=[],result=prior.sort(R)));doc=extract_document(doc,roots=['evj'],statement_indices=[]).document
    compact=collapse(prior.scalarize(doc));cases=1
    for pivot in range(len(VARIABLES)):
        f,d,slots,var,body=lifted(compact,'evj',pivot,len(VARIABLES),'exists');env={p['name']:'case' if p['sort']=='situation' else 'a' for p in d['parameters']};row=tuple((env|{var:'b'})[x['name']] if x['kind']=='variable' else 'a' for x in body['arguments'])
        for permitted in (False,True):
            m={x['name']:lambda:'a' for x in f['declarations'] if x['kind']=='primitive'}|{n:lambda x=env[p['name']]:x for n,p in zip(slots,d['parameters'])}|{'evi':lambda *xs:permitted and xs==row}
            assert evaluate_document(f,individuals=('a','b'),situations=('case','other'),primitives=m,max_steps=30000)[0]['value']==permitted;cases+=1
    reject(lambda:run('evj',[],{'evi':lambda *xs:True}));cases+=1
    return dict(cases=cases,existential_slots_checked=len(VARIABLES),all_roles_shared_by_one_setting=True,unbounded_native_setting_not_finitely_invented=True)

@lru_cache(None)
def presentation_checks():
    rows={'eisth':{('inquiry','evj','elm','case')}};cases=perturb(lambda m:run('evk',['inquiry','case'],m),{'eisth':relation(rows['eisth']),'evj':forbidden,'elm':forbidden},rows)
    rows={'eisdv':{('heading','section','part','paper',Q(2),Q(10),'case')},'eisdw':{('heading','section','evk','case')},'ue':{('previous','heading','case'),('heading','following','case')}}
    m={n:relation(rs) for n,rs in rows.items()}|{'evk':forbidden};cases+=perturb(lambda mm:run('evl',[],mm),m,rows)
    for n in ('eiswv','eisxa'):assert not run('evl',[],{p:lambda *xs:True for p in rows}|{n:lambda:'heading'});cases+=1
    return dict(cases=cases,physical_setting_and_law_account_are_quoted=True,depth_two_and_printed_ten_in_same_part=True,previous_heading_and_following_distinct=True,no_claim_of_physical_truth=True)

@lru_cache(None)
def source_record():
    u=json.loads(read(INVENTORY))['units'][238];assert u['id']=='einstein-1905:u0239' and not u['math_ids'];assert digest(u['text'].encode())==u['text_sha256']
    return dict(version='einstein-tenth-section-heading-reading-v1',unit=u['id'],text=u['text'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],math=[],source_nonblank_characters=len(re.sub(r'\s','',u['text'])),facsimile_pages=[917],observations=LIMITS,source_sha256={p:digest((ROOT/p).read_bytes()) for p in (INVENTORY,FACSIMILE,DOC)})
@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    before=load_catalog(ROOT,PARENT_BASIS);after=load_catalog(ROOT,BASIS)
    assert len(after.document['statements'])==447 and after.document['statements'][:446]==before.document['statements']
    assert after.document['declarations'][:len(before.document['declarations'])]==before.document['declarations']
    assert all(after.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in before.entries.items());load_annotations(ROOT,BASIS,ANNOTATIONS)
    assert selection_binding(after,[413,414,445])==selection_binding(before,[413,414,445])
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    for style in ('compact','full'):
        body=format_graph(core(),style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core()
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=len(MEANINGS),new_primitives=0,new_statements=1,all_446_prior_statements_and_meanings_preserved=True)
def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')
@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('magnitude',magnitude_checks),('derivative',derivative_checks),('physical',physical_checks),('time_binding',time_binding_checks),('setting_binding',setting_binding_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,*DEPENDENCIES,'scripts/compose_tenth_section_heading.py','scripts/check_tenth_section_heading.py','tests/test_tenth_section_heading.py'}
    for p in DEPENDENCIES:paths.update(json.loads(read(p))['source_sha256'])
    return dict(status='slowly_accelerated_electron_dynamics_heading_connected',document=FULL,**results,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
