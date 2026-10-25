"""Check independent readouts, possible disagreement, and the physical field example."""
from functools import lru_cache
from copy import deepcopy
from fractions import Fraction as Q
import json,re
from noema.grammar import parse,format_graph,number_word
from noema.finite_semantics import evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
# Load the schema before the historical checker chain to keep its import stack bounded.
from scripts.compose_direct_speed_experiment import *
from scripts import check_deflection_speed_determination as prior
from scripts.check_clock_site_time import relation,perturb
from scripts.check_ninth_section_opening import lifted
from scripts.check_problem_series_reduction import collapse

DOC='docs/direct-speed-experiment-v1.md';SOURCE='data/einstein-direct-speed-experiment-reading-v1.json'
INVENTORY=prior.INVENTORY;FACSIMILE=prior.FACSIMILE
DEPENDENCIES=('reports/deflection-speed-determination-v1.json','reports/kinetic-energy-consequences-v1.json','reports/wave-cycle-frequency-v1.json')
CONSTANTS=prior.CONSTANTS|{n:n for n in REFERENCES}
PEOPLE=tuple(dict.fromkeys([*prior.PEOPLE,*CONSTANTS.values(),*[n for n,t in DIRECT if t=='a'],'speedunit','directmethod','directinstrument','directrecord']))
SCENES=prior.SCENES+('directcase',)
forbidden=prior.forbidden;reject=prior.reject;walk=prior.walk;fn=prior.fn;sort=prior.sort;scalarize=prior.scalarize;key=prior.key;keyed=prior.keyed
BOUNDS={'erm':{'epr','ejwb'},'ern':{'ejwb'},'ero':{'erm','ern'},'erp':{'eq4','ero'},'erq':{'erp'},'err':{'ero'},'ers':{'ekc2','lf'},'ert':{'ejsj'},'eru':{'ero','ejsn','ers','ert'},'erv':{'eru'},'erw':{'eq6','erq'},'erx':{'eq6','err'},'ery':{'eq6','erv'},'erz':{'erc','eq7','erw','erx','ery'},'er3':{'er2'}}

@lru_cache(None)
def core():return parse(read(CORE))
@lru_cache(None)
def boundary(root,mode='native'):
    doc=extract_document(core(),roots=[root],statement_indices=[]).document
    for i,d in enumerate(doc['declarations']):
        if d['kind']=='definition' and d['name'] in prior.prior.prior.prior.physical.NUM|BOUNDS.get(root,set()):doc['declarations'][i]=dict(kind='primitive',name=d['name'],parameters=[p['sort'] for p in d['parameters']],result=d['result'])
    doc=extract_document(doc,roots=[root],statement_indices=[]).document
    if mode=='instance':
        d=next(d for d in doc['declarations'] if d['name']==root)
        def expose(x):
            if isinstance(x,list):return [expose(y) for y in x]
            if not isinstance(x,dict):return x
            if x.get('kind') in ('forall','exists'):
                d['parameters'].append(dict(name=x['variable'],sort=x['sort']));return expose(x['body'])
            return {k:expose(v) for k,v in x.items()}
        d['body']=expose(d['body'])
    return doc
@lru_cache(None)
def fixture(root,mode='native'):
    doc=deepcopy(boundary(root,mode));d=next(x for x in doc['declarations'] if x['name']==root);slots=[]
    for i,p in enumerate(d['parameters']):
        n='jdexarg'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=root,arguments=[dict(kind='call',symbol=n,arguments=[]) for n in slots])
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jdexpoint',parameters=[],result='situation'));expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='jdexpoint',arguments=[]))
    doc['declarations'].sort(key=lambda x:x['kind']!='primitive');doc['statements']=[dict(kind='ask',body=expr)];return doc,slots
def run(root,values,m,mode='native'):
    doc,slots=fixture(root,mode);assert len(values)==len(slots),(root,len(values),len(slots))
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|{'jdexpoint':lambda:'case'}|m|{n:lambda x=x:x for n,x in zip(slots,values)}
    return evaluate_document(doc,individuals=PEOPLE,situations=SCENES,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=3000000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def model(speed=3):
    a=prior.model(speed);a.by.update(event='event',scene='directcase',speedunit='speedunit',speedscale=Q(1),method='directmethod',instrument='directinstrument',record='directrecord',range=fn(sort(DOMAIN),lambda x:abs(a.r(x))<100),calibration=fn(sort(F),lambda x:a.c(2*a.r(x))),signal=a.c(Q(speed,2)),agrees=True,ux=a.c(speed),uy=a.c(0),uz=a.c(0))
    a.by.update({'direct'+n:a.by[n] for n,t in DETAIL});a.m['eisxt']=lambda:a.by['speed']
    return a
def direct_rows(a):
    by=a.by;values=by|dict(target=by['matter'],quantity='erm',unit=by['speedunit'],context=by['scene'],value=by['speed'])
    return {'ern':[by[n] for n,t in SPEED_UNITS[:-1]]+[by['scene']],'erm':[values[n] for n,t in QUANTITY],'eis3r':[values[n] for n,t in CAL],'eis3s':[values[n] for n,t in ACQUIRE],'eis36':[by['method'],'erc',by['scene']],'eis3u':[by['observer'],by['record'],by['scene'],by['assessment']]}

@lru_cache(None)
def quantity_checks():
    a=model();by=a.by;cases=0
    for L,T,U in ((1,1,1),(3,2,Q(3,2)),(2,3,Q(2,3))):
        mm=a.m|{'ejwb':lambda unit,l,m,t,scale,ctx:(unit,l,m,t,scale,ctx)==('speedunit',1,0,-1,U,'case')}
        vs=[Q(L),Q(T),'speedunit',Q(U),'case'];assert run('ern',vs,mm);bad=vs.copy();bad[0]+=1;assert not run('ern',bad,mm);cases+=2
    ws=[(n,t) for n,t in MOTION if n not in ('matter','frame','event','speed','context')]+[(n,'b') for n in ('lengthscale','timescale','speedscale')]
    supply=by|dict(target=by['matter'],unit=by['speedunit'],value=by['speed'],context=by['scene'])
    rows={'epr':[supply[n] for n,t in MOTION]};mm=a.m|keyed(a,rows)|{'ejwb':lambda *xs:True}
    vs=[supply[n] for n,t in QUANTITY+ws];assert run('erm',vs,mm,'instance');cases+=1
    for n in ('target','frame','event','value','context'):
        bad=vs.copy();pos=[x for x,t in QUANTITY+ws].index(n);bad[pos]='case' if n=='context' else a.c(4) if n=='value' else 'a';assert not run('erm',bad,mm,'instance');cases+=1
    reject(lambda:run('erm',vs[:len(QUANTITY)],mm));reject(lambda:run('erm',vs,mm|{'epr':forbidden},'instance'));cases+=2
    return dict(cases=cases,three_velocity_norm_and_coherent_speed_unit=True,acceleration_and_ratio_not_quantity_premises=True,full_trajectory_domain_refused=True)

@lru_cache(None)
def direct_checks():
    cases=0
    for speed in (0,3):
        a=model(speed);rows=direct_rows(a);mm=a.m|keyed(a,rows)|{'eisoe':lambda view,source,target:(view,source,target) in {('view','other','directcase'),('view','other','assessment')}};vs=a.values(DIRECT)
        assert run('ero',vs,mm);cases+=1
        for n in rows:
            assert not run('ero',vs,mm|{n:lambda *xs:False});reject(lambda:run('ero',vs,mm|{n:forbidden}));cases+=2
        for n,t in DIRECT:
            if t in ('a','d','b'):
                bad=vs.copy();pos=[x for x,ty in DIRECT].index(n);bad[pos]='case' if t=='d' else 'a' if t=='a' else bad[pos]+1
                # Mass, charge and unrelated field units are background for the comparison, not direct speed acquisition.
                if n in ('observer','assessment','event','scene','speedunit','speedscale','method','instrument','record','matter','frame','view','context','lengthscale','timescale'):
                    assert not run('ero',bad,mm);cases+=1
        bad=vs.copy();bad[[n for n,t in DIRECT].index('signal')]=a.c(7);assert not run('ero',bad,mm|{'eis3s':lambda *xs:True});cases+=1
        bad=vs.copy();bad[[n for n,t in DIRECT].index('calibration')]=fn(sort(F),lambda x:a.c(2*a.r(x)+1));assert not run('ero',bad,mm|{'eis3r':lambda *xs:True});cases+=1
    # The tested formula remains a quoted target of independence, not an executed premise.
    declarations={d['name']:d for d in boundary('ero')['declarations']}
    def executable_refs(node):
        if isinstance(node,list):return set().union(*(executable_refs(x) for x in node))
        if not isinstance(node,dict) or node.get('kind')=='quote':return set()
        found={node['symbol']} if node.get('kind') in ('call','function_ref') else set()
        return found|set().union(*(executable_refs(x) for x in node.values()))
    pending={'ero'};used=set()
    while pending:
        name=pending.pop();used.add(name);pending.update(executable_refs(declarations[name].get('body'))-used)
    assert not {'sets','setk','eq4','eq5','erc'}&used;cases+=1
    return dict(cases=cases,calibrated_speed_signal_acquired=True,independence_includes_calibration=True,same_observer_and_causal_records=True)

@lru_cache(None)
def comparison_checks():
    a=model();cases=0
    for recovered,agrees,want in ((3,True,True),(3,False,False),(4,False,True),(4,True,False)):
        a.by.update(recovered=a.c(recovered),agrees=agrees);by=a.by
        rows={'eq4':a.values(MEASUREMENT),'ero':a.values(DIRECT),'eis37':[by['observer'],'erc',by['recovered'],by['speed'],agrees,by['assessment']]};mm=a.m|keyed(a,rows);vs=a.values(COMPARED)
        assert run('erp',vs,mm)==want;cases+=1
        if want:
            for n in rows:
                assert not run('erp',vs,mm|{n:lambda *xs:False});reject(lambda:run('erp',vs,mm|{n:forbidden}));cases+=2
            for n in ('directevent','directscene','directmethod','directrecord','observer','assessment'):
                bad=vs.copy();bad[[x for x,t in COMPARED].index(n)]='case' if n.endswith('scene') or n=='assessment' else 'a';assert not run('erp',bad,mm);cases+=1
    return dict(cases=cases,support_and_disagreement_both_testable=True,comparison_is_an_operation_not_assumed_equality=True,shared_motion_and_assessment_roles=True)

def oscillating_model():
    a=model();c=a.c
    a.by.update(x=c(0),y=c(0),z=c(0),lower=c(0),upper=c(4),threshold=c(3),electricconversion=c(1),magneticconversion=c(Q(1,5)))
    def triangle(t,period,amplitude):return amplitude*(1-4*abs((t/period)%1-Q(1,2)))
    for pre,period,amp,axis in [('electric',Q(2),Q(2),'y'),('magnetic',Q(1),Q(3),'z')]:
        a.by.update({pre+'period':c(period),pre+'center':c(0),pre+'positive':c(period/2),pre+'negative':c(0),pre+'profile':fn(sort(F),lambda x,p=period,h=amp:c(triangle(a.r(x),p,h))),pre+'field':a.field(lambda ax,p,period=period,amp=amp,axis=axis:triangle(p[3],period,amp) if ax==axis else 0)})
    return a

@lru_cache(None)
def oscillation_checks():
    a=oscillating_model();by=a.by;c=a.c;cases=0
    for pre in ('electric','magnetic'):
        supply={n:by[n] if n in ('lower','upper') else by[pre+n] for n,t in OSCILLATION};vs=[supply[n] for n,t in OSCILLATION]
        periodrow=[supply['profile'],supply['profile'],supply['period']];mm=a.m|keyed(a,{'ekc2':periodrow})|{'lf':lambda *xs:True}
        assert run('ers',vs,mm);cases+=1
        for name in ('positive','negative','upper'):
            bad=vs.copy();pos=[n for n,t in OSCILLATION].index(name);bad[pos]=c(0 if name!='negative' else a.r(supply['positive']));assert not run('ers',bad,mm);cases+=1
        for name in ('ekc2','lf'):
            assert not run('ers',vs,mm|{name:lambda *xs:False});reject(lambda:run('ers',vs,mm|{name:forbidden}));cases+=2
    for t in (0,Q(1,4),Q(1,2),1,Q(3,2),2,4):
        vs=a.values(EXAMPLE)+[c(t)];mm=a.m|{'ejsj':lambda *xs:True};assert run('ert',vs,mm);cases+=1
        for pre in ('electric','magnetic'):
            bad=vs.copy();pos=[n for n,t in EXAMPLE].index(pre+'profile');old=by[pre+'profile'];bad[pos]=fn(sort(F),lambda x: c(a.r(old(x))+1));assert not run('ert',bad,mm);cases+=1
    fields=by|dict(context=by['scene']);av=by|dict(target=by['matter'],quantity='erm',unit=by['speedunit'],context=by['scene'])
    rows={'ero':a.values(DIRECT),'ejsn':[fields[n] for n,t in FIELDS],'eis4b':[by['method'],by['frame'],by['timeunit'],by['threshold'],by['scene']],'eis4a':[(av|fields)[n] for n,t in COUPLING]}
    periods={key(a,[by[n] if n in ('lower','upper') else by[pre+n] for n,t in OSCILLATION]) for pre in ('electric','magnetic')}
    mm=a.m|keyed(a,rows)|{'ers':lambda *xs:key(a,xs) in periods,'ert':lambda *xs:key(a,xs[:-1])==key(a,a.values(EXAMPLE))}
    vs=a.values(EXAMPLE)+[c(1)];assert run('eru',vs,mm,'instance');cases+=1
    for n in (*rows,'ers','ert'):
        assert not run('eru',vs,mm|{n:lambda *xs:False},'instance');reject(lambda:run('eru',vs,mm|{n:forbidden},'instance'));cases+=2
    bad=vs.copy();bad[[n for n,t in EXAMPLE].index('threshold')]=c(2);assert not run('eru',bad,mm|{'eis4b':lambda *xs:True,'ert':lambda *xs:True},'instance');cases+=1
    for name in ('x','y','z'):
        bad=vs.copy();bad[[n for n,t in EXAMPLE].index(name)]=c(1)
        assert not run('eru',bad,mm|{'ert':lambda *xs:True},'instance');cases+=1
        assert run('eru',bad,mm|{'ert':lambda *xs:True,'eis4a':lambda *xs:True},'instance');cases+=1
    reject(lambda:run('eru',a.values(EXAMPLE),mm));cases+=1
    return dict(cases=cases,both_physical_field_components_and_full_usage_interval=True,nonconstant_continuous_least_period_profiles=True,contextual_rapidness_and_actual_signal_coupling=True,finite_triangle_diagnostics_are_not_physical_measurements=True)

@lru_cache(None)
def possibility_checks():
    cases=0
    for root,fields,target in [('erq',COMPARED,'erp'),('err',DIRECT,'ero'),('erv',EXAMPLE,'eru')]:
        a=oscillating_model();witnesses=[(n,t) for n,t in fields if n not in dict(BACKGROUND)]
        vs=a.values(BACKGROUND+witnesses);row=key(a,a.values(fields));mm=a.m|{target:lambda *xs:key(a,xs)==row}
        assert run(root,vs,mm,'instance');assert not run(root,vs,mm|{target:lambda *xs:False},'instance');reject(lambda:run(root,a.values(BACKGROUND),mm));cases+=3
        doc=boundary(root);d=next(d for d in doc['declarations'] if d['name']==root);names={n:dict(kind='variable',name=p['name']) for (n,t),p in zip(BACKGROUND,d['parameters'])};node=d['body']
        for n,t in witnesses:assert node['kind']=='exists';names[n]=dict(kind='variable',name=node['variable']);node=node['body']
        assert node['kind']=='call' and node['symbol']==target and node['arguments']==[names[n] for n,t in fields];cases+=1
        compact=collapse(scalarize(doc))
        for pivot,(field,typ) in enumerate(witnesses):
            f,dd,slots,name,body=lifted(compact,root,pivot,len(witnesses),'exists');env={p['name']:'case' if p['sort']=='situation' else False if p['sort']=='truth' else 'a' for p in dd['parameters']};special='other' if typ=='d' else True if typ=='c' else 'b';row=tuple((env|{name:special})[x['name']] for x in body['arguments'])
            for permitted in (False,True):
                mm={n:lambda x=env[p['name']]:x for n,p in zip(slots,dd['parameters'])}|{target:lambda *xs:permitted and xs==row}
                assert evaluate_document(f,individuals=('a','b'),situations=('case','other'),primitives=mm,max_steps=30000)[0]['value']==permitted;cases+=1
    for root,target in [('erw','erq'),('erx','err'),('ery','erv')]:
        a=model();expected=a.by|dict(context='case');row=key(a,[expected[n] for n,t in BACKGROUND]);mm=a.m|{'eq6':lambda scale,ctx:(scale,ctx)==(Q(1),'case'),'eiscv':lambda *xs:True,target:lambda *xs:key(a,xs)==row}
        assert run(root,[Q(1)],mm,'instance');assert not run(root,[Q(1)],mm|{target:lambda *xs:False},'instance');reject(lambda:run(root,[],mm));cases+=3
    return dict(cases=cases,all_124_existential_slots_two_value_binding_diagnostics=True,current_electron_units_and_speed_held_fixed=True,full_function_and_number_quantification_refused=True)

@lru_cache(None)
def presentation_checks():
    rows={'eiswm':{('eis4c','author','eis32','erc','paper','case')},'uh':{('eis4c','author','erw','tenth','case'),('eis4d','author','erx','tenth','case'),('eis4e','author','ery','tenth','case')},'zc':{('eis4c','author','erx','erw','tenth','case')},'eisij':{('eis4d','author','eq7','erx','paper','case')},'eir5':{('eis4e','author','eis4d','ery','case')},'eisa5':{('eis4e','author','erx','ery','case')},'ue':{('eis4c','eis4d','case')}}
    cases=perturb(lambda m:run('erz',[],m),{n:relation(rs) for n,rs in rows.items()}|{n:forbidden for n in BOUNDS['erz']},rows)
    rows={'eir3':{('eis4c','author','paper','er2','case')},'ue':{('eis32','eis4c','case')}};cases+=perturb(lambda m:run('er3',[],m),{n:relation(rs) for n,rs in rows.items()}|{'er2':forbidden},rows)
    return dict(cases=cases,back_reference_reason_addition_and_inserted_example=True,quoted_contents_not_executed=True)

@lru_cache(None)
def source_record():
    u=json.loads(read(INVENTORY))['units'][267];assert digest(u['text'].encode())==u['text_sha256'];assert not u['math_ids']
    return dict(version='einstein-direct-speed-experiment-reading-v1',units=[dict(unit=u['id'],text=u['text'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],math=[],source_nonblank_characters=len(re.sub(r'\s','',u['text'])))],facsimile_pages=[920],observations=LIMITS,source_sha256={p:digest((ROOT/p).read_bytes()) for p in (INVENTORY,FACSIMILE,DOC)})
@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    before=load_catalog(ROOT,PARENT_BASIS);after=load_catalog(ROOT,BASIS)
    assert len(after.document['statements'])==435 and after.document['statements'][:434]==before.document['statements']
    assert after.document['declarations'][:len(before.document['declarations'])]==before.document['declarations']
    assert all(after.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in before.entries.items())
    assert selection_binding(after,[432,433])==selection_binding(before,[432,433]);load_annotations(ROOT,BASIS,ANNOTATIONS)
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    for style in ('compact','full'):
        body=format_graph(core(),style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core()
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=len(MEANINGS),new_general_relations=len(PRIMITIVES),new_reference_constants=len(REFERENCES),new_statements=1,all_434_prior_statements_and_meanings_preserved=True)
def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')
@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('quantity',quantity_checks),('direct',direct_checks),('comparison',comparison_checks),('oscillation',oscillation_checks),('possibility',possibility_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,*DEPENDENCIES,'scripts/compose_direct_speed_experiment.py','scripts/check_direct_speed_experiment.py','tests/test_direct_speed_experiment.py'}
    for path in DEPENDENCIES:paths.update(json.loads(read(path))['source_sha256'])
    return dict(status='independent_speed_comparison_and_oscillating_field_example_connected',document=FULL,**results,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
