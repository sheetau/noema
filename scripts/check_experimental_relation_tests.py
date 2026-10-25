"""Check measured quantities, independent channels, predictions and comparisons."""
from scripts.compose_experimental_relation_tests import *
from fractions import Fraction as Q
import json,re
from noema.finite_semantics import evaluate_document,Content
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts import check_local_magnetic_radius as rad
from scripts import check_traversed_potential as pot
from scripts import check_direct_speed_experiment as direct
from scripts.check_ninth_section_opening import lifted
from scripts.check_problem_series_reduction import collapse

DOC='docs/experimental-relation-tests-v1.md';REPORT='reports/experimental-relation-tests-v1.json'
INVENTORY=pot.INVENTORY;FACSIMILE=pot.FACSIMILE
DEPENDENCIES=('reports/local-magnetic-radius-v1.json','reports/traversed-potential-v1.json','reports/direct-speed-experiment-v1.json','reports/closing-acknowledgment-v1.json')
CONSTANTS=direct.CONSTANTS|{'eis3k':'view','eirf':'paper','ri':'case'}
PEOPLE=tuple(dict.fromkeys([*rad.PEOPLE,*pot.PEOPLE,*CONSTANTS.values(),'observer','view','speedunit',*[pre+'read'+n for pre in RCHANNELS+('drop',) for n,t in DEVICE if t=='a']]))
SCENES=('case','other','assessment')
NUM=pot.prior.physical.NUM
BOUNDS={'et7':{'er7','eoy'},'eua':{'ek3q','ejwb'},'eub':{'ek3o'},'euc':{'ek3u'},'eud':{'er7','eoy','eoz','eo2'},'eue':{'esp','ern'},'euf':{'eud','et7','erm','eub','euc'},'eug':{'eue','eua','erm','eub','euc','equ'},'euh':{'euf'},'eui':{'eug'},'euj':{'euh'},'euk':{'eui'},'eul':{'erw','euj','euk'}}
forbidden=pot.forbidden;reject=pot.reject;walk=pot.walk;fn=pot.fn;sort=pot.sort;key=direct.key;scalarize=direct.scalarize
@lru_cache(None)
def core():return parse(read(CORE))
@lru_cache(None)
def boundary(root,mode='native'):
    doc=extract_document(core(),roots=[root],statement_indices=[]).document
    for i,d in enumerate(doc['declarations']):
        if d['kind']=='definition' and d['name'] in NUM|BOUNDS.get(root,set()):doc['declarations'][i]=dict(kind='primitive',name=d['name'],parameters=[p['sort'] for p in d['parameters']],result=d['result'])
    doc=extract_document(doc,roots=[root],statement_indices=[]).document
    if mode=='instance':
        d=next(d for d in doc['declarations'] if d['name']==root)
        def expose(x):
            if isinstance(x,list):return [expose(y) for y in x]
            if not isinstance(x,dict):return x
            if x.get('kind') in ('forall','exists'):
                d['parameters'].append(dict(name=x['variable'],sort=x['sort']));return expose(x['body'])
            return {k:expose(y) for k,y in x.items()}
        d['body']=expose(d['body'])
    return doc
@lru_cache(None)
def fixture(root,mode='native'):
    doc=deepcopy(boundary(root,mode));d=next(d for d in doc['declarations'] if d['name']==root);slots=[]
    for i,p in enumerate(d['parameters']):
        n='jertslot'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=root,arguments=[dict(kind='call',symbol=n,arguments=[]) for n in slots])
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jertpoint',parameters=[],result='situation'));expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='jertpoint',arguments=[]))
    doc['declarations'].sort(key=lambda d:d['kind']!='primitive');doc['statements']=[dict(kind='ask',body=expr)];return doc,slots
def run(root,values,m,mode='native'):
    doc,slots=fixture(root,mode);assert len(values)==len(slots),(root,len(values),len(slots))
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|{'jertpoint':lambda:'case'}|m|{n:lambda x=x:x for n,x in zip(slots,values)}
    return evaluate_document(doc,individuals=PEOPLE,situations=SCENES,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=3000000,memoize_definitions=True,memoize_expressions=True)[0]['value']
def table(a,rows):return {n:lambda *xs,rs=rs:key(a,xs) in {key(a,row) for row in rs} for n,rs in rows.items()}
def model(kind,observed=None,agrees=True):
    a=pot.model() if kind=='potential' else rad.model();c=a.c
    a.by.update(view='view',observer='observer',context='other',scene='case',assessment='assessment',predicted=c(Q(25,4) if kind=='potential' else Q(15,4)),agrees=agrees,speedunit='speedunit',speedscale=Q(1))
    if kind=='potential':a.by.update(light=c(5),finalspeed=c(3),speed=c(3),mass=c(2),charge=c(2),drop=c(Q(25,4) if observed is None else observed))
    else:a.by.update(radius=c(Q(15,4) if observed is None else observed))
    for pre,quantity,target,event,unit,value in channel_specs(kind):
        a.by.update({pre+'readmethod':pre+'readmethod',pre+'readinstrument':pre+'readinstrument',pre+'readrecord':pre+'readrecord',pre+'readrange':fn(sort(DOMAIN),lambda x:abs(a.r(x))<100),pre+'readcalibration':fn(sort(F),lambda x:x),pre+'readsignal':a.by[value]})
    return a
def comparison_rows(a,kind):
    by=a.by;base=PBASE if kind=='potential' else RBASE;physical='eud' if kind=='potential' else 'eue';claim='esd' if kind=='potential' else 'es2';observed='drop' if kind=='potential' else 'radius'
    rows={physical:[[by[n] if n!='context' else by['scene'] for n,t in base]],'eisoe':[[by['view'],by['context'],by[n]] for n in ('scene','assessment')]}
    for pre,quantity,target,event,unit,value in channel_specs(kind):
        vals={n:by[pre+'read'+n] for n,t in DEVICE}|dict(observer=by['observer'],target=by[target],quantity=quantity,frame=by['frame'],event=by[event],unit=by[unit],context=by['scene'],value=by[value])
        for name,row in [(quantity,[vals[n] for n,t in QUANTITY]),('eis3r',[vals[n] for n,t in measurement.CAL]),('eis3s',[vals[n] for n,t in measurement.ACQUIRE]),('eis36',[by[pre+'readmethod'],claim,by['scene']]),('eis3u',[by['observer'],by[pre+'readrecord'],by['scene'],by['assessment']])]:rows.setdefault(name,[]).append(row)
    rows['eis37']=[[by['observer'],claim,by[observed],by['predicted'],by['agrees'],by['assessment']]]
    return rows

@lru_cache(None)
def comparison_checks():
    cases=0
    for kind,root,fields,correct in [('potential','euf',PTEST,Q(25,4)),('radius','eug',RTEST,Q(15,4))]:
        for observed,agrees,wanted in [(correct,True,True),(correct,False,False),(correct+1,False,True),(correct+1,True,False)]:
            a=model(kind,observed,agrees);rows=comparison_rows(a,kind);m=a.m|table(a,rows);vs=a.values(fields)
            assert run(root,vs,m)==wanted,(kind,observed,agrees);cases+=1
            if not wanted:continue
            for name,rs in rows.items():
                for i in range(len(rs)):
                    assert not run(root,vs,a.m|table(a,rows|{name:rs[:i]+rs[i+1:]})),(kind,name,i);cases+=1
                reject(lambda:run(root,vs,m|{name:forbidden}));cases+=1
            for name in ('predicted',):
                bad=vs.copy();bad[[n for n,t in fields].index(name)]=a.c(a.r(a.by[name])+1);assert not run(root,bad,m|{'eis37':lambda *xs:True});cases+=1
        a=model(kind);m=a.m|table(a,comparison_rows(a,kind));vs=a.values(fields)
        for pre,quantity,target,event,unit,value in channel_specs(kind):
            for name in (pre+'readmethod',pre+'readinstrument',pre+'readrecord',target,event,unit):
                bad=vs.copy();bad[[n for n,t in fields].index(name)]='a';assert not run(root,bad,m),(kind,name);cases+=1
            bad=vs.copy();bad[[n for n,t in fields].index(pre+'readsignal')]=a.c(7);assert not run(root,bad,m|{'eis3s':lambda *xs:True});cases+=1
            bad=vs.copy();bad[[n for n,t in fields].index(pre+'readcalibration')]=fn(sort(F),lambda x:a.c(a.r(x)+1));assert not run(root,bad,m|{'eis3r':lambda *xs:True});cases+=1
        for name in ('observer','scene','assessment','view'):
            bad=vs.copy();bad[[n for n,t in fields].index(name)]='other' if name in ('scene','assessment') else 'a';assert not run(root,bad,m),(kind,name);cases+=1
    return dict(cases=cases,all_nine_channels_calibrated_acquired_and_independent=True,shared_process_records_and_same_target_event_units=True,observed_disagreement_is_testable=True,prediction_not_fitted_to_observation=True)

@lru_cache(None)
def quantity_checks():
    cases=0;a=pot.model();by=a.by;by.update(target=by['episode'],event=by['end'],unit=by['potentialunit'],value=by['drop'])
    rows={'er7':[a.values(PBASE)],'eoy':[a.values(energy.ALL)]};m=a.m|table(a,rows);vs=[by[n] for n,t in QUANTITY+PWS]
    assert run('et7',vs,m,'instance');cases+=1
    for name in ('target','frame','event','unit','value','context'):
        bad=vs.copy();j=[n for n,t in QUANTITY+PWS].index(name);bad[j]='other' if name=='context' else a.c(7) if name=='value' else 'a';assert not run('et7',bad,m,'instance');cases+=1
    for name in rows:assert not run('et7',vs,m|{name:lambda *xs:False},'instance');cases+=1
    reject(lambda:run('et7',vs[:6],m));cases+=1
    a=rad.model();by=a.by;by.update(target=by['matter'],unit=by['massunit'],value=by['mass']);row=[[by[n] for n,t in dynamics.MASS]]
    assert run('eub',[by[n] for n,t in QUANTITY],a.m|table(a,{'ek3o':row}));cases+=1
    by.update(unit=by['chargeunit'],value=by['charge']);m=a.m|table(a,{'ek3u':[[by[n] for n,t in dynamics.CHARGE]]});vs=[by[n] for n,t in QUANTITY+QWS]
    assert run('euc',vs,m,'instance');cases+=1
    for i in range(len(vs)):
        bad=vs.copy();typ=(QUANTITY+QWS)[i][1];bad[i]=a.c(-a.r(vs[i])) if typ==R else Q(2) if typ=='b' else 'other' if typ=='d' else 'a';assert not run('euc',bad,m,'instance');cases+=1
    reject(lambda:run('euc',vs[:6],m));cases+=1
    return dict(cases=cases,potential_bound_to_same_episode_not_only_endpoint_particle=True,mass_and_signed_charge_quantity_roles=True,unknown_physical_and_number_domains_not_filled=True)

@lru_cache(None)
def geometric_checks():
    cases=0
    for ax,ay,az in [(0,-Q(12,5),0),(4,-Q(12,5),0),(4,-Q(36,19),0),(100,3,4)]:
        a=rad.model(ax=ax);c=a.c;norm=abs(ay) if not az else Q(5);by=a.by
        polys=[rad.physical.Rational((0,3,Q(ax,2))),rad.physical.Rational((0,0,ay/2)),rad.physical.Rational((0,0,az/2)),rad.physical.Rational((0,1))]
        by.update(curve=a.register_curve(polys),ax=c(ax),ay=c(ay),az=c(az),radius=c(9/norm),point=by['location'],target=by['matter'],unit=by['lengthunit'],value=c(9/norm))
        by.update({n:a.register_function(p.derivative()) for (n,t),p in zip(dynamics.PROFILES,polys)})
        from scripts.compose_material_acceleration import AT
        assert rad.run('sepp',[by[n] for n,t in AT],a.m);cases+=1
        rows={'ek3q':[[by[n] for n,t in dynamics.KINEMATIC]],'ejwb':[[by['unit'],Q(1),Q(0),Q(0),by['lengthscale'],by['context']],[by['timeunit'],Q(0),Q(0),Q(1),by['timescale'],by['context']]]}
        m=a.m|table(a,rows);vs=[by[n] for n,t in QUANTITY+RWS]
        assert run('eua',vs,m,'instance'),(ax,ay,az);cases+=1
        bad=vs.copy();bad[4]=c(9/norm+1);assert not run('eua',bad,m,'instance');cases+=1
        for name in ('target','event','unit','context'):
            bad=vs.copy();bad[[n for n,t in QUANTITY+RWS].index(name)]='other' if name=='context' else 'a';assert not run('eua',bad,m,'instance');cases+=1
        reject(lambda:run('eua',vs[:6],m));cases+=1
    return dict(cases=cases,actual_second_derivatives_checked_separately=True,general_three_dimensional_geometric_radius=True,tangential_acceleration_allowed=True,radius_different_from_magnetic_prediction_has_consistent_curve=True)

def executable_refs(node):
    if isinstance(node,list):return set().union(*(executable_refs(x) for x in node))
    if not isinstance(node,dict) or node.get('kind')=='quote':return set()
    found={node['symbol']} if node.get('kind') in ('call','function_ref') else set()
    return found|set().union(*(executable_refs(x) for x in node.values()))
@lru_cache(None)
def premise_checks():
    cases=0
    for kind,root,fields,parts in [('potential','eud',PBASE,('er7','eoy','eoz','eo2')),('radius','eue',RBASE,('esp','ern'))]:
        a=model(kind);by=a.by
        rows={n:[a.values(PBASE if n=='er7' else energy.ALL)] for n in parts} if kind=='potential' else {'esp':[a.values(radius.SETTING)],'ern':[[by[n] for n,t in potential.SPEED_UNITS]]}
        m=a.m|table(a,rows);vs=a.values(fields);assert run(root,vs,m);cases+=1
        for n in rows:assert not run(root,vs,m|{n:lambda *xs:False});reject(lambda:run(root,vs,m|{n:forbidden}));cases+=2
        lookup={d['name']:d for d in extract_document(core(),roots=[root],statement_indices=[]).document['declarations']};pending={root};used=set()
        while pending:
            name=pending.pop();used.add(name);pending.update(executable_refs(lookup[name].get('body'))-used)
        assert not {'esa','esr','ess','eo4','sesf','setk','serc','ep7','esd','es2'}&used,(root,used);cases+=1
    return dict(cases=cases,physical_applicability_retains_radiation_balance_and_exclusion=True,tested_equations_absent_from_executable_premises=True)

@lru_cache(None)
def possibility_checks():
    cases=0;slots_checked=0
    for kind,root,target,base,fields in [('potential','euh','euf',PBASE,PTEST),('radius','eui','eug',RBASE,RTEST)]:
        a=model(kind);fixed=base+[('view','a')];ws=[(n,t) for n,t in fields if n not in dict(fixed)];row=key(a,a.values(fields));m=a.m|{target:lambda *xs:key(a,xs)==row}
        assert run(root,a.values(fixed+ws),m,'instance');assert not run(root,a.values(fixed+ws),m|{target:lambda *xs:False},'instance');reject(lambda:run(root,a.values(fixed),m));cases+=3
        doc=boundary(root);d=next(d for d in doc['declarations'] if d['name']==root);names={n:dict(kind='variable',name=p['name']) for (n,t),p in zip(fixed,d['parameters'])};node=d['body']
        for n,t in ws:assert node['kind']=='exists';names[n]=dict(kind='variable',name=node['variable']);node=node['body']
        assert node['kind']=='call' and node['symbol']==target and node['arguments']==[names[n] for n,t in fields];cases+=1
        compact=collapse(scalarize(doc))
        for pivot,(field,typ) in enumerate(ws):
            f,dd,slots,name,body=lifted(compact,root,pivot,len(ws),'exists');env={p['name']:'case' if p['sort']=='situation' else False if p['sort']=='truth' else 'a' for p in dd['parameters']};special='other' if typ=='d' else True if typ=='c' else 'b';expected=tuple((env|{name:special})[x['name']] for x in body['arguments'])
            for permitted in (False,True):
                mm={n:lambda x=env[p['name']]:x for n,p in zip(slots,dd['parameters'])}|{target:lambda *xs:permitted and xs==expected}
                assert evaluate_document(f,individuals=('a','b'),situations=('case','other'),primitives=mm,max_steps=30000)[0]['value']==permitted;cases+=1
            slots_checked+=1
    return dict(cases=cases,existential_slots_checked=slots_checked,two_value_binding_diagnostics_for_every_slot=True,native_unbounded_function_and_number_domains_refused=True)

@lru_cache(None)
def connection_checks():
    cases=0
    for kind,root,target,base in [('potential','euj','euh',PBASE),('radius','euk','eui',RBASE)]:
        a=model(kind);by=a.by;expected=[by[n] if n!='context' else 'case' for n,t in base]+['view'];m=a.m|table(a,{target:[expected]})|{'eiscv':lambda *xs:True}
        if kind=='radius':m|={'eis4o':lambda:by['speedunit'],'eis4p':lambda:by['speedscale']}
        assert run(root,[],m),kind;assert not run(root,[],m|{target:lambda *xs:False});cases+=2
    from itertools import product
    for vals in product((False,True),repeat=3):
        m={n:lambda x=x:Content(SCENES,(x,False,False)) for n,x in zip(('erw','euj','euk'),vals)};assert run('eul',[],m)==all(vals);cases+=1
    return dict(cases=cases,same_current_settings_and_theory_preserved=True,all_three_experimental_access_conditions_required=True)
@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    before=load_catalog(ROOT,PARENT_BASIS);after=load_catalog(ROOT,BASIS)
    assert len(after.document['statements'])==444 and after.document['statements']==before.document['statements']
    assert after.document['declarations'][:len(before.document['declarations'])]==before.document['declarations']
    assert all(after.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in before.entries.items())
    assert selection_binding(after,[441,442,443])==selection_binding(before,[441,442,443]);load_annotations(ROOT,BASIS,ANNOTATIONS)
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    for style in ('compact','full'):
        body=format_graph(core(),style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core()
    return dict(new_definitions=len(MEANINGS),new_primitives=0,new_statements=0,all_444_prior_statements_and_meanings_preserved=True)
def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('comparison',comparison_checks),('quantity',quantity_checks),('geometry',geometric_checks),('premise',premise_checks),('possibility',possibility_checks),('connection',connection_checks),('structure',structure_checks)]}
    unit=json.loads(read(INVENTORY))['units'][264];assert unit['id']=='einstein-1905:u0265';excerpt='dem Experimente zugänglichen Eigenschaften der Bewegung des Elektrons';start=unit['text'].index(excerpt)
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|{DOC,INVENTORY,FACSIMILE,*DEPENDENCIES,'scripts/compose_experimental_relation_tests.py','scripts/check_experimental_relation_tests.py','tests/test_experimental_relation_tests.py'}
    for path in DEPENDENCIES:paths.update(json.loads(read(path))['source_sha256'])
    return dict(status='independent_potential_and_curvature_comparisons_composed',document=FULL,**results,source_dependency=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[start,start+len(excerpt)],text=excerpt,status='dependency_group_not_whole_unit_review'),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
