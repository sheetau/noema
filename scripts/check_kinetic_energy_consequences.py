"""Check physical boundary scopes and charge-free energy formula application."""
from functools import lru_cache
from copy import deepcopy
from fractions import Fraction as Q
import json,re
from noema.grammar import parse,format_graph,number_word
from noema.finite_semantics import evaluate_document,FunctionValue
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts import check_electron_kinetic_work as prior
from scripts.check_clock_site_time import relation,perturb
from scripts.check_ninth_section_opening import lifted
from scripts.check_problem_series_reduction import collapse
from scripts.compose_kinetic_energy_consequences import *

DOC='docs/kinetic-energy-consequences-v1.md';SOURCE='data/einstein-kinetic-energy-consequences-reading-v1.json'
INVENTORY=prior.INVENTORY;FACSIMILE=prior.FACSIMILE
DEPENDENCIES=('reports/electron-kinetic-work-v1.json','reports/energy-boundary-v1.json','reports/radiative-intensity-v1.json','reports/material-energy-extension-v1.json','reports/speed-boundary-forecast-v1.json','reports/material-mass-claim-v1.json')
CONSTANTS=prior.CONSTANTS|{n:n for n in REFERENCES}|{'eis3k':'view','zia':'kinematic_results','eis3h':'energy_display','eiszr':'charge_reason'}
PEOPLE=tuple(dict.fromkeys([*prior.PEOPLE,*CONSTANTS.values(),'view','event']))
forbidden=prior.forbidden;reject=prior.reject;walk=prior.walk;sort=prior.sort;fn=prior.fn
BOUNDS={'epr':{'ek3p','seoc'},'eps':{'epr','ek3o','ek3n','ejwb'},'ept':{'eps'},'epu':{'ept'},'epv':{'epu'},'epw':{'epu'},'epx':{'epw','epu','ekjt'},'epy':{'epr','ek3o'},'epz':{'epy'},'ep5':{'eps'},'ep6':{'eoc','eps','ep5'},'eqa':{'ep3','ep4','ep7','eph','ejht','ep2','eqg'},'eqc':{'eqb'},'eqd':{'ep6','eon','ep7','eoi'},'eqf':{'eqe'}}

@lru_cache(None)
def core():return parse(read(CORE))
@lru_cache(None)
def boundary(root,mode='native'):
    doc=extract_document(core(),roots=[root],statement_indices=[]).document
    for i,d in enumerate(doc['declarations']):
        if d['kind']=='definition' and d['name'] in prior.physical.NUM|BOUNDS.get(root,set()):doc['declarations'][i]=dict(kind='primitive',name=d['name'],parameters=[p['sort'] for p in d['parameters']],result=d['result'])
    doc=extract_document(doc,roots=[root],statement_indices=[]).document
    if mode=='instance':
        d=next(x for x in doc['declarations'] if x['name']==root)
        if root in ('epu','epy'):
            node=d['body']
            for _ in WITNESSES:d['parameters'].append(dict(name=node['variable'],sort=node['sort']));node=node['body']
            d['body']=node
        elif root=='ep6':
            node=d['body']['body']
            while node['kind']=='forall':d['parameters'].append(dict(name=node['variable'],sort=node['sort']));node=node['body']
            d['body']['body']=node
        elif root=='epz':
            target=next(x for x in walk(d['body']) if x.get('kind')=='forall');d['parameters'].append(dict(name=target['variable'],sort=target['sort']))
            def replace(x):
                if x==target:return target['body']
                if isinstance(x,dict):return {k:replace(v) for k,v in x.items()}
                if isinstance(x,list):return [replace(v) for v in x]
                return x
            d['body']=replace(d['body'])
    return doc
@lru_cache(None)
def fixture(root,mode='native'):
    doc=deepcopy(boundary(root,mode));d=next(x for x in doc['declarations'] if x['name']==root);slots=[]
    for i,p in enumerate(d['parameters']):
        n='jkecslot'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=root,arguments=[dict(kind='call',symbol=n,arguments=[]) for n in slots])
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jkecpoint',parameters=[],result='situation'));expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='jkecpoint',arguments=[]))
    elif isinstance(d['result'],dict) and d['result'].get('kind')=='function':
        doc['declarations'].append(dict(kind='primitive',name='jkecprobe',parameters=[d['result']],result='truth'));expr=dict(kind='call',symbol='jkecprobe',arguments=[expr])
    doc['declarations'].sort(key=lambda x:x['kind']!='primitive');doc['statements']=[dict(kind='ask',body=expr)];return doc,slots
def run(root,values,m,mode='native'):
    doc,slots=fixture(root,mode);assert len(values)==len(slots)
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|{'jkecpoint':lambda:'case'}|m|{n:lambda x=x:x for n,x in zip(slots,values)}
    return evaluate_document(doc,individuals=PEOPLE,situations=('case','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=3000000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def model():
    a=prior.model();c=a.c;a.by.update(view='view',event='event',location=a.point((0,0,0,0)),ux=c(1),uy=c(2),uz=c(2),speed=c(3),energy=c(a.r(a.by['mass'])*Q(25,4)),alternative='other')
    a.by['curve']=a.register_curve([prior.Rational((0,u)) for u in (1,2,2,1)])
    a.m['bc']=lambda x,y:a.r(x)<=a.r(y)
    return a
def keyed(a,rows):return {n:lambda *xs,row=row:a.key(xs)==a.key(row) for n,row in rows.items()}
def scalarize(x):
    if x=='number':return 'individual'
    if isinstance(x,list):return [scalarize(y) for y in x]
    if isinstance(x,dict):return {k:scalarize(v) for k,v in x.items()}
    return x

@lru_cache(None)
def numerical_checks():
    a=model();c,r=a.c,a.r;cases=0
    for values,want in [((0,0,0,0),True),((1,2,2,3),True),((-1,-2,-2,3),True),((1,2,2,-3),False),((3,4,0,5),True),((0,6,8,10),True),((1,2,2,2),False),((6,0,0,6),True)]:
        assert run('epq',list(map(c,values)),a.m)==want;cases+=1
    vs=a.values(SETTING);mm=a.m|{'eps':lambda *xs:True}
    assert run('ept',vs,mm) and run('ep5',vs,mm);cases+=2
    for target in ('ept','ep5'):
        bad=vs.copy();bad[-1]=c(r(vs[-1])+1);assert not run(target,bad,mm);cases+=1
        assert not run(target,vs,mm|{'eps':lambda *xs:False});cases+=1
        reject(lambda:run(target,vs,mm|{'eps':forbidden}));cases+=1
    # E=M(L/T)^2; different valid numerical scales preserve the formula.
    for L,T,M in ((3,2,5),(2,3,4)):
        a.by.update(lengthscale=Q(L),timescale=Q(T),massscale=Q(M),forcescale=Q(M*L,T*T),energyscale=Q(M*L*L,T*T))
        vs=a.values(SETTING);assert run('ep5',vs,mm);cases+=1
        for n in ('massscale','lengthscale','timescale','energyscale'):
            bad=vs.copy();pos=[x for x,t in SETTING].index(n);bad[pos]+=1
            assert not run('ep5',bad,mm);cases+=1
    return dict(cases=cases,three_dimensional_nonnegative_speed=True,same_rightmost_expression_and_compatible_rescalings=True,printed_integral_not_rewritten=True)

@lru_cache(None)
def physical_checks():
    a=model();c,r=a.c,a.r;by=a.by;cases=0
    rows={'eiszn':[by['matter'],'case'],'ejsl':[by[n] for n in ('frame','lengthunit','timeunit','context')],'eisqd':[by[n] for n in ('matter','frame','event','lengthunit','timeunit','location','context')],'seoc':[by[n] for n in ('matter','frame','context','domain','curve','event','location','ux','uy','uz')]}
    def history(*xs):
        return a.key(xs[:-1])==a.key([by[n] for n in ('matter','frame','context','domain','curve','lengthunit','timeunit')]) and all(xs[-1](*map(c,p)) for p in ((0,0,0,0),(1,2,3,4)))
    mm=a.m|keyed(a,rows)|{'ek3p':history}
    assert run('epr',a.values(MOTION),mm);cases+=1
    for n in rows.keys()|{'ek3p'}:assert not run('epr',a.values(MOTION),mm|{n:lambda *xs:False});cases+=1
    # A valid superluminal motion input is not excluded by a hidden beta/energy test.
    by.update(ux=c(6),uy=c(0),uz=c(0),speed=c(6),curve=a.register_curve([prior.Rational((0,u)) for u in (6,0,0,1)]));rows['seoc']=[by[n] for n in ('matter','frame','context','domain','curve','event','location','ux','uy','uz')]
    assert a.first(by['domain'],a.register_function(prior.Rational((0,6))),c(0),c(6));cases+=1
    assert run('epr',a.values(MOTION),a.m|keyed(a,rows)|{'ek3p':history});cases+=1
    assert not {'soy','srd','serc','eiszt','ek3o'}&{d['name'] for d in boundary('epr')['declarations']};cases+=1
    a=model();by=a.by
    rows={'epr':a.values(MOTION),'ek3o':a.values(MASS),'ek3n':a.values(UNITS),'ejwb':[by['energyunit'],Q(2),Q(1),Q(-2),by['energyscale'],'case'],'eiszw':[by[n] for n in ('frame','lengthunit','forceunit','energyunit','context')],'eiszt':[by[n] for n in ('matter','frame','event','energyunit','energy','context')]}
    mm=a.m|keyed(a,rows);vs=a.values(SETTING);assert run('eps',vs,mm);cases+=1
    for n in rows:assert not run('eps',vs,mm|{n:lambda *xs:False});reject(lambda:run('eps',vs,mm|{n:forbidden}));cases+=2
    for n in ('energyscale','forcescale','lengthscale'):
        bad=vs.copy();bad[[x for x,t in SETTING].index(n)]+=1
        assert not run('eps',bad,mm|{'ejwb':lambda *xs:True,'ek3n':lambda *xs:True});cases+=1
    assert not {'ek3u','eibs','eisqc','serg','serh'}&{d['name'] for d in boundary('eps')['declarations']};cases+=1
    return dict(cases=cases,actual_calibrated_motion_mass_and_kinetic_assignment_connected=True,superluminal_candidate_not_excluded_by_numeric_formula=True,neutral_or_charged_materials_not_preselected=True)

@lru_cache(None)
def possibility_checks():
    a=model();c=a.c;by=a.by;cases=0;alt=by|dict(context='other')
    allowed=lambda *xs:xs==('view','case','other')
    mm=a.m|{'eisoe':allowed}|keyed(a,{'ept':[alt[n] for n,t in SETTING],'epr':[alt[n] for n,t in MOTION],'ek3o':[alt[n] for n,t in MASS]})
    for root,fields in [('epu',BACKGROUND+NUM),('epy',BACKGROUND+[('speed',R)])]:
        vs=a.values(fields+WITNESSES);assert run(root,vs,mm,'instance');cases+=1
        for n in ('view','matter','frame','mass','massunit','lengthunit','timeunit','speed','event','alternative'):
            bad=vs.copy();pos=[x for x,t in fields+WITNESSES].index(n);value=bad[pos];bad[pos]='case' if n=='alternative' else 'a' if isinstance(value,str) else c(a.r(value)+1)
            assert not run(root,bad,mm,'instance');cases+=1
        assert not run(root,vs,mm|{'eisoe':lambda *xs:False},'instance');cases+=1
        reject(lambda:run(root,vs,mm|{'eisoe':forbidden},'instance'));cases+=1
        reject(lambda:run(root,a.values(fields),mm));cases+=1
    # The graph keeps both candidate slots outside its fixed background.
    row=a.key(a.values(BACKGROUND+NUM));m=a.m|{'epu':lambda *xs:a.key(xs)==row}
    for speed,energy,want in ((by['speed'],by['energy'],True),(c(4),by['energy'],False),(by['speed'],c(0),False)):
        assert run('epv',a.values(BACKGROUND),m|{'jkecprobe':lambda graph:graph(speed,energy)})==want;cases+=1
    def divergence(g,V):return a.r(V)==5 and g(by['speed'],by['energy']) and not g(c(4),by['energy'])
    mm=m|{'epw':lambda *xs:True,'ekjt':divergence}
    assert run('epx',a.values(BACKGROUND),mm);cases+=1
    for n in ('epw','ekjt'):assert not run('epx',a.values(BACKGROUND),mm|{n:lambda *xs:False});cases+=1
    for speed in (4,5,6):
        for attained in (False,True):
            vs=a.values(BACKGROUND)+[c(speed)];mm=a.m|{'eisoe':allowed,'epy':lambda *xs:attained}
            assert run('epz',vs,mm,'instance')==(speed<=5 or not attained);cases+=1
    assert not run('epz',a.values(BACKGROUND)+[c(6)],a.m|{'eisoe':lambda *xs:False,'epy':lambda *xs:False},'instance');cases+=1
    reject(lambda:run('epz',a.values(BACKGROUND),a.m|{'eisoe':allowed,'epy':lambda *xs:False}));cases+=1
    return dict(cases=cases,same_theory_full_allowed_contexts_and_shared_trace=True,nonempty_graph_and_all_output_boundary_are_separate=True,strictly_above_light_not_boundary_itself=True,full_real_and_function_quantification_refused=True)

@lru_cache(None)
def binding_checks():
    cases=0;decl={d['name']:d for d in core()['declarations']}
    for root,target,fields,called in [('ept','eps',SETTING,SETTING),('ep5','eps',SETTING,SETTING),('eps','epr',SETTING,MOTION)]:
        d=decl[root];names={n:dict(kind='variable',name=p['name']) for (n,t),p in zip(fields,d['parameters'])};call=next(x for x in walk(d['body']) if x.get('kind')=='call' and x.get('symbol')==target)
        assert call['arguments']==[names[n] for n,t in called];cases+=1
    for root,target,fields,called in [('epu','ept',BACKGROUND+NUM,SETTING),('epy','epr',BACKGROUND+[('speed',R)],MOTION)]:
        d=decl[root];names={n:dict(kind='variable',name=p['name']) for (n,t),p in zip(fields,d['parameters'])};node=d['body'];bound=[]
        for n,t in WITNESSES:assert node['kind']=='exists';bound.append(node['variable']);names[n]=dict(kind='variable',name=node['variable']);node=node['body']
        call=next(x for x in walk(node) if x.get('kind')=='call' and x.get('symbol')==target)
        assert call['arguments']==[names['alternative'] if n=='context' else names[n] for n,t in called];cases+=1
        access=next(x for x in walk(node) if x.get('kind')=='call' and x.get('symbol')=='eisoe');assert access['arguments']==[names[n] for n in ('view','context','alternative')];cases+=1
        doc=collapse(scalarize(boundary(root)))
        # No rational witnesses: functions/real cuts collapse to a two-value sort.
        for pivot in range(len(WITNESSES)):
            f,dd,slots,name,body=lifted(doc,root,pivot,len(WITNESSES),'exists');env={p['name']:'case' if p['sort']=='situation' else 'a' for p in dd['parameters']}
            probe=next(x for x in walk(body) if x.get('kind')=='call' and x.get('symbol')==target);special='other' if WITNESSES[pivot][0]=='alternative' else 'b'
            row=tuple((env|{name:special})[x['name']] for x in probe['arguments'])
            for permitted in (False,True):
                mm={d['name']:(lambda *xs:True) for d in f['declarations'] if d['kind']=='primitive'};mm|={n:lambda x=env[p['name']]:x for n,p in zip(slots,dd['parameters'])};mm[target]=lambda *xs:permitted and xs==row
                assert evaluate_document(f,individuals=('a','b'),situations=('case','other'),primitives=mm,max_steps=30000)[0]['value']==permitted;cases+=1
    # Material extension quantifies every physical setting outside the conclusion.
    fields=[(n,t) for n,t in SETTING if n not in ('frame','lengthunit','timeunit','light','context')]
    d=decl['ep6'];p=dict(kind='variable',name=d['body']['variable']);node=d['body']['body'];names={}
    for n,t in fields:assert node['kind']=='forall';names[n]=dict(kind='variable',name=node['variable']);node=node['body']
    fixed_values={'frame':dict(kind='call',symbol='ra',arguments=[]),'lengthunit':dict(kind='call',symbol='ta',arguments=[]),'timeunit':dict(kind='call',symbol='rb',arguments=[]),'light':dict(kind='call',symbol='tc',arguments=[]),'context':p}
    expected=[fixed_values.get(n,names.get(n)) for n,t in SETTING]
    for symbol in ('eps','ep5'):
        call=next(x for x in walk(node) if x.get('kind')=='call' and x.get('symbol')==symbol);assert call['arguments']==expected;cases+=1
    a=model();vs=a.values(fields);mm=a.m|{'eoc':lambda *xs:True,'eps':lambda *xs:True,'ep5':lambda *xs:True,'tc':lambda:a.by['light'],'ta':lambda:a.by['lengthunit'],'rb':lambda:a.by['timeunit']}
    assert run('ep6',vs,mm,'instance');assert not run('ep6',vs,mm|{'ep5':lambda *xs:False},'instance');cases+=2
    assert run('ep6',vs,mm|{'eps':lambda *xs:False,'ep5':lambda *xs:False},'instance');cases+=1
    reject(lambda:run('ep6',[],mm));cases+=1
    return dict(cases=cases,all_trace_and_alternative_witnesses_two_value_domain=True,background_and_same_units_outside_speed_and_energy=True,all_material_settings_and_same_conclusion_parameters=True)

@lru_cache(None)
def presentation_checks():
    rows={'uh':{('eis3m','author','ep3','tenth','case'),('eis3n','author','ep4','tenth','case')},'zc':{('eis3m','author','ep7','ep3','tenth','case')},'eiswm':{('eis3m','author','energy_display','eph','paper','case'),('eis3o','author','kinematic_results','ejht','paper','case')},'eis3l':{('eis3o','author','ejht','ep4','ep2','paper','case')},'eisa5':{('eis3o','author','ep4','eqg','case')},'ue':{('eis3m','eis3n','case')}}
    cases=perturb(lambda m:run('eqa',[],m),{n:relation(rs) for n,rs in rows.items()}|{n:forbidden for n in BOUNDS['eqa']},rows)
    rows={'uh':{('eis3p','author','ep6','tenth','case')},'eisij':{('eis3p','author','eon','ep6','paper','case')},'eiswm':{('eis3p','author','energy_display','ep7','paper','case'),('eis3q','author','charge_reason','eoi','paper','case')},'zc':{('eis3q','author','eoi','ep6','tenth','case')}}
    cases+=perturb(lambda m:run('eqd',[],m),{n:relation(rs) for n,rs in rows.items()}|{n:forbidden for n in BOUNDS['eqd']},rows)
    for root,node,msg,prev in [('eqc','eis3m','eqb','energy_display'),('eqf','eis3p','eqe','eis3n')]:
        rows={'eir3':{(node,'author','paper',msg,'case')},'ue':{(prev,node,'case')}}
        cases+=perturb(lambda m:run(root,[],m),{n:relation(rs) for n,rs in rows.items()}|{msg:forbidden},rows)
    return dict(cases=cases,also_from_expression_not_physical_impossibility_proof=True,earlier_results_comparison_retains_insertion_and_scope=True,charge_addition_reason_and_material_addition=True,quoted_physics_not_executed=True)

@lru_cache(None)
def source_record():
    d=json.loads(read(INVENTORY));units=d['units'][262:264];math=[m for m in d['math'] if m['id'] in ('M0428','M0429')]
    for u in units:assert digest(u['text'].encode())==u['text_sha256']
    return dict(version='einstein-kinetic-energy-consequences-reading-v1',units=[dict(unit=u['id'],text=u['text'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],math=[m for m in math if m['id'] in u['math_ids']],source_nonblank_characters=len(re.sub(r'\s|\[M\d+\]','',u['text']))) for u in units],facsimile_pages=[920],observations=LIMITS,source_sha256={p:digest((ROOT/p).read_bytes()) for p in (INVENTORY,FACSIMILE,DOC)})
@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    before=load_catalog(ROOT,PARENT_BASIS);after=load_catalog(ROOT,BASIS)
    assert len(after.document['statements'])==432 and after.document['statements'][:430]==before.document['statements']
    assert after.document['declarations'][:len(before.document['declarations'])]==before.document['declarations']
    assert all(after.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in before.entries.items())
    assert selection_binding(after,[428,429])==selection_binding(before,[428,429]);load_annotations(ROOT,BASIS,ANNOTATIONS)
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    for style in ('compact','full'):
        body=format_graph(core(),style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core()
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=len(MEANINGS),new_general_relations=len(PRIMITIVES),new_reference_constants=len(REFERENCES),new_statements=2,all_430_prior_statements_and_meanings_preserved=True)
def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')
@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('numerical',numerical_checks),('physical',physical_checks),('possibility',possibility_checks),('bindings',binding_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,*DEPENDENCIES,'scripts/compose_kinetic_energy_consequences.py','scripts/check_kinetic_energy_consequences.py','tests/test_kinetic_energy_consequences.py'}
    for path in DEPENDENCIES:paths.update(json.loads(read(path))['source_sha256'])
    return dict(status='physical_energy_boundary_and_material_extension_connected',document=FULL,**results,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
