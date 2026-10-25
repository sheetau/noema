"""Diagnose shared physical roles, actual acceleration and the printed chain."""
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
from scripts import check_electron_alternative_conventions as physical
from scripts.check_electron_transformed_dynamics import Model,Rational,fn,sort
from scripts.check_clock_site_time import relation,perturb
from scripts.check_ninth_section_opening import lifted
from scripts.check_problem_series_reduction import collapse
from scripts.compose_electron_kinetic_work import *

DOC='docs/electron-kinetic-work-v1.md';SOURCE='data/einstein-electron-kinetic-work-reading-v1.json'
INVENTORY=physical.INVENTORY;FACSIMILE=physical.FACSIMILE
DEPENDENCIES=('reports/material-mass-claim-v1.json','reports/electron-axis-motion-v1.json','reports/electron-power-law-v1.json','reports/electron-energy-balance-v1.json','reports/kinetic-energy-chain-v1.json','reports/electric-action-v1.json','reports/point-particle-dynamics-v1.json')
CONSTANTS=physical.CONSTANTS|{n:n for n in REFERENCES}|{'eiszq':'eiszq','zpn':'force','eis3j':'W'}
PEOPLE=tuple(dict.fromkeys([*physical.PEOPLE,*CONSTANTS.values(),*[n for n,t in ALL if t=='a'],'a','b']))
PEOPLE=tuple(dict.fromkeys([*PEOPLE,'event','chargerecord','forcerecord']))
forbidden=physical.forbidden;reject=physical.reject;walk=physical.walk
BOUNDS={'eor':{'serw','ek3p','ejsn','ek3n','ejwb'},'eot':{'eibs','ek3u','ek3o'},'eou':{'eor','eos','eot'},'eow':{'eov'},'eoy':{'sero'},'eo2':{'eox'},'eo3':{'eox'},'eo4':{'sesf'},'eo5':{'sero','serg'},'epi':{'eo6','epa','epb','epc','epd','epe','epf','epg','eph','elk','epo'},'epk':{'epj'},'epl':{'eph'},'epn':{'epm'}}
BOUNDS['eov']={'senz','sjs'}
BOUNDS['epi'].add('epp')

@lru_cache(None)
def core():return parse(read(CORE))
@lru_cache(None)
def boundary(root,mode='native'):
    doc=extract_document(core(),roots=[root],statement_indices=[]).document
    for i,d in enumerate(doc['declarations']):
        if d['kind']=='definition' and d['name'] in physical.NUM|BOUNDS.get(root,set()):doc['declarations'][i]=dict(kind='primitive',name=d['name'],parameters=[p['sort'] for p in d['parameters']],result=d['result'])
    doc=extract_document(doc,roots=[root],statement_indices=[]).document
    if mode=='instance':
        d=next(x for x in doc['declarations'] if x['name']==root)
        if root in ('eos','eot'):
            node=d['body']
            for _ in range(4):d['parameters'].append(dict(name=node['variable'],sort=node['sort']));node=node['body']
            d['body']=node
        else:
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
        n='jkwslot'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=root,arguments=[dict(kind='call',symbol=n,arguments=[]) for n in slots])
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jkwpoint',parameters=[],result='situation'));expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='jkwpoint',arguments=[]))
    doc['declarations'].sort(key=lambda x:x['kind']!='primitive');doc['statements']=[dict(kind='ask',body=expr)];return doc,slots
def run(root,values,m,mode='native'):
    doc,slots=fixture(root,mode);assert len(values)==len(slots)
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|{'jkwpoint':lambda:'case'}|m|{n:lambda x=x:x for n,x in zip(slots,values)}
    return evaluate_document(doc,individuals=PEOPLE,situations=('case','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=3000000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def model():
    a=Model(0,1,0,0);c=a.c
    for n,t in ALL:
        if n not in a.by:a.by[n]=n if t=='a' else Q(1) if t=='b' else c(0)
    a.by.update(light=c(5),start='start',end='end',context='case',episode='episode',field='field',energyunit='energyunit',energyscale=Q(1),slowbound=c(3),startpoint=a.point((0,0,0,0)),endpoint=a.point((Q(1,16),0,0,Q(1,4))),finalposition=c(Q(1,16)),finalspeed=c(Q(1,2)),velocity=a.register_function(Rational((0,2))),acceleration=a.register_function(Rational((2,))),profile=a.register_function(Rational((2,))),electricfield=a.field(lambda axis,p:2 if axis=='x' else 0))
    a.m['sxs']=lambda lo,hi,t:a.r(lo)<=a.r(t)<=a.r(hi)
    a.by['region']=fn(sort(REGION),lambda *xs:True)
    a.m['ad']=lambda x,y:x*y
    return a

def keyed(a,rows):return {n:lambda *xs,row=row:a.key(xs)==a.key(row) for n,row in rows.items()}

@lru_cache(None)
def physical_checks():
    a=model();c,r=a.c,a.r;by=a.by;values=a.values(SETTING);cases=0
    fs=by|dict(electricconversion=c(1),magneticconversion=c(Q(1,5)))
    rows={'serw':a.values(MOTION),'ek3p':a.values(HISTORY),'ejsn':[fs[n] for n,t in FIELDS],'ek3n':a.values(UNITS),'ejwb':[by['energyunit'],Q(2),Q(1),Q(-2),by['energyscale'],'case'],'eiszw':[by[n] for n in ('frame','lengthunit','forceunit','energyunit','context')],'eiszz':[by[n] for n in ('field','frame','electricfield','region','context')]}
    mm=a.m|keyed(a,rows)
    assert run('eor',values,mm);cases+=1
    for n in rows:assert not run('eor',values,mm|{n:lambda *xs:False});reject(lambda:run('eor',values,mm|{n:forbidden}));cases+=2
    for n in ('energyscale','forcescale','lengthscale'):
        vs=values.copy();vs[[x for x,t in SETTING].index(n)]=Q(2)
        assert not run('eor',vs,mm|{'ek3n':lambda *xs:True,'ejwb':lambda *xs:True});cases+=1
    # The native static field condition at several nonzero times and positions.
    for position,time in ((0,0),(2,3),(-2,-3)):
        vs=values+list(map(c,(position,1,-1,time)))
        assert run('eos',vs,a.m,'instance');cases+=1
        for axis in ('x','y','z'):
            bad=vs.copy();bad[[n for n,t in SETTING].index('electricfield')]=a.field(lambda ax,p: (2 if ax=='x' else 0)+(ax==axis))
            assert not run('eos',bad,a.m,'instance');cases+=1
    reject(lambda:run('eos',values,a.m));cases+=1
    for time in (0,Q(1,8)):
        loc=by['curve'](c(time));charge=r(by['charge'])
        action=by|dict(event='event',chargerecord='chargerecord',forcerecord='forcerecord',chargescale=Q(1),carrier=by['matter'],fieldunit=by['electricunit'],point=loc,electric=a.point((2,0,0,0)),force=a.point((2*charge,0,0,0)),conversion=c(1))
        rows={'eibs':[action[n] for n,t in ACTION],'ek3u':[action[n] for n,t in CHARGE],'ek3o':[action[n] for n,t in MASS]}
        mm=a.m|keyed(a,rows);vs=values+[c(time),'event','chargerecord','forcerecord',Q(1)]
        assert run('eot',vs,mm,'instance');cases+=1
        for n in rows:assert not run('eot',vs,mm|{n:lambda *xs:False},'instance');cases+=1
    # Native derivatives on a known rational curve; wrong velocity/acceleration rejected.
    for time in (0,Q(1,8),Q(1,4)):
        vs=values+[c(time)];assert run('eov',vs,a.m);cases+=1
        for name in ('velocity','acceleration'):
            bad=vs.copy();bad[[n for n,t in SETTING].index(name)]=a.register_function(Rational((7,)))
            assert not run('eov',bad,a.m);cases+=1
    rows={'eiszt':{('matter','frame','start','energyunit',Q(0),'case'),('matter','frame','end','energyunit',Q(5),'case')},'eiszu':{('episode','matter','field','frame','start','end','energyunit',Q(5),'case')},'eiszv':{('episode','matter','frame','start','end','energyunit',Q(0),'case')}}
    # Use role-distinguishing individuals rather than inherited fixture identities.
    for n in ('matter','frame','start','end','episode','field','energyunit'):by[n]=n
    by.update(withdrawn=c(5),initial=c(0),final=c(5),radiated=c(0));vs=a.values(ALL)
    mm=a.m|{n:lambda *xs,rs=rs:a.key(xs) in rs for n,rs in rows.items()}
    assert run('eox',vs,mm);cases+=1
    for n in rows:assert not run('eox',vs,mm|{n:lambda *xs:False});cases+=1
    for n in ('matter','frame','start','end','episode','field','energyunit','withdrawn','initial','final','radiated'):
        bad=vs.copy();i=[x for x,t in ALL].index(n);bad[i]='a' if isinstance(bad[i],str) else c(r(bad[i])+1)
        assert not run('eox',bad,mm);cases+=1
    return dict(cases=cases,physical_units_field_and_same_energy_owners=True,native_rational_derivatives_not_free_speed_assignments=True,static_field_all_three_components_and_time_independence_probed=True,full_field_domain_refused=True)

@lru_cache(None)
def energy_checks():
    a=model();c,r=a.c,a.r;cases=0
    for values,want in [((5,0,5,0),True),((5,1,5,0),False),((5,0,4,1),False),((5,0,6,0),False),((-1,0,-1,0),False)]:
        a.by.update(zip((n for n,t in VALUES),map(c,values)))
        mm=a.m|{'eox':lambda *xs:True,'zrgclosed':lambda:fn(sort('h[a a a a a a a d] c'),lambda *xs:xs==tuple(a.by[n] for n in ('episode','matter','field','frame','start','end','energyunit','context')))}
        assert run('eo2',a.values(ALL),mm)==want;cases+=1
    a.by.update(withdrawn=c(5),initial=c(0),final=c(5),radiated=c(0));vs=a.values(ALL)
    assert run('eo3',vs,a.m|{'eox':lambda *xs:True});cases+=1
    changed=vs.copy();changed[-2]=c(6);assert not run('eo3',changed,a.m|{'eox':lambda *xs:True});cases+=1
    wd=[a.by[n] for n in ('episode','matter','field','frame','start','end','energyunit','withdrawn','context')]
    work=[c(0),a.by['finalposition'],a.by['charge'],a.by['withdrawn'],a.by['profile']]
    mm=a.m|keyed(a,{'eiszu':wd,'sero':work})
    assert run('eoy',vs,mm);cases+=1
    for n in ('eiszu','sero'):assert not run('eoy',vs,mm|{n:lambda *xs:False});reject(lambda:run('eoy',vs,mm|{n:forbidden}));cases+=2
    rows={'eiszt':[a.by[n] for n in ('matter','frame','end','energyunit','final','context')],'sero':[c(0),a.by['finalposition'],a.by['charge'],a.by['final'],a.by['profile']],'serg':[a.by[n] for n in ('light','mass','finalspeed','final')]}
    mm=a.m|keyed(a,rows);assert run('eo5',vs,mm);cases+=1
    for n in rows:assert not run('eo5',vs,mm|{n:lambda *xs:False});cases+=1
    calls={x['symbol'] for x in walk(next(d for d in core()['declarations'] if d['name']=='eo5')['body']) if x.get('kind')=='call'}
    assert 'serg' in calls and 'serh' not in calls;cases+=1
    # Slow is bounded actual acceleration, not small speed or a radiation theorem.
    rows={'eiszy':[]};vs=a.values(SETTING)+[c(Q(1,8))]
    mm=a.m|{'eov':lambda *xs:True,'eiszx':lambda *xs:True}
    for acceleration,want in ((2,True),(-2,True),(3,False),(-3,False),(4,False)):
        bad=vs.copy();bad[[n for n,t in SETTING].index('acceleration')]=a.register_function(Rational((acceleration,)))
        assert run('eow',bad,mm,'instance')==want;cases+=1
    assert not run('eow',vs,mm|{'eiszx':lambda *xs:False},'instance');cases+=1
    reject(lambda:run('eow',a.values(SETTING),mm));cases+=1
    return dict(cases=cases,initial_rest_zero_and_radiation_zero_both_required=True,energy_equalities_retain_owners_units_and_work_bounds=True,printed_serg_not_corrected_serh=True,contextual_slow_bound_not_a_no_radiation_theorem=True)

@lru_cache(None)
def presentation_checks():
    rows={'eiszy':{('eis3a','author','eo6','tenth','case')},'zdg':{('eis3b','author','epa','tenth','case')},'eisox':{('eis3f','epp','case')},'ug':{('eis3c','author','epb','tenth','case'),('eis3i','author','epc','tenth','case')},'zc':{('eis3i','author','epb','epc','tenth','case'),('eis3d','author','epd','epe','tenth','case'),('eis3h','author','epg','eph','tenth','case')},'uh':{('eis3d','author','epe','tenth','case'),('eis3e','author','epf','tenth','case')},'eisnw':{('eis3g','author','W','epo','paper','case')},'eiswm':{('eis3e','author','Adisplay','elk','paper','case')},'ue':set(zip(('eis3a','eis3b','eis3c','eis3d','eis3e'),('eis3b','eis3c','eis3d','eis3e','eis3h'),['case']*5))}
    cases=perturb(lambda m:run('epi',[],m),{n:relation(rs) for n,rs in rows.items()}|{n:forbidden for n in BOUNDS['epi']},rows)
    for root,msg,node,previous in [('epk','epj','eis3a','eiszq'),('epn','epm','eis3h','eis3e')]:
        rows={'eir3':{(node,'author','paper',msg,'case')},'ue':{(previous,node,'case')}}
        cases+=perturb(lambda m:run(root,[],m),{n:relation(rs) for n,rs in rows.items()}|{msg:forbidden},rows)
    rows={'eisox':{('eis3h','eph','case')},'uh':{('eis3h','author','eph','tenth','case')}}
    cases+=perturb(lambda m:run('epl',[],m),{n:relation(rs) for n,rs in rows.items()}|{'eph':forbidden},rows)
    return dict(cases=cases,determination_task_obviousness_assumptions_and_inferences_distinguished=True,first_A_backward_reference_and_following_printed_display=True,quoted_physics_not_executed=True)

def scalarize(x):
    if x=='number':return 'individual'
    if isinstance(x,list):return [scalarize(y) for y in x]
    if not isinstance(x,dict):return x
    if x.get('kind') in ('number','apply','function_ref'):return dict(kind='call',symbol='jkwzero',arguments=[])
    return {k:scalarize(v) for k,v in x.items()}

@lru_cache(None)
def binding_checks():
    cases=0;decl={d['name']:d for d in core()['declarations']}
    # Check the public 36-role contracts independently before diagnostic lifting.
    for root,fields,target,wanted in [('eo4',SETTING,'sesf',POWER),('eou',SETTING,'eor',SETTING),('eou',SETTING,'eos',SETTING),('eor',SETTING,'serw',MOTION),('eor',SETTING,'ek3p',HISTORY),('eo2',ALL,'serm',VALUES),('eo3',ALL,'sern',VALUES)]:
        d=decl[root];names={n:dict(kind='variable',name=p['name']) for (n,t),p in zip(fields,d['parameters'])}
        call=next(x for x in walk(d['body']) if x.get('kind')=='call' and x.get('symbol')==target)
        assert call['arguments']==[names[n] for n,t in wanted];cases+=1
    # Every time, not just endpoints, and all four field coordinates stay native.
    for root,count in [('eou',1),('eow',1),('eos',4)]:
        qs=[x for x in walk(decl[root]['body']) if x.get('kind')=='forall'];assert len(qs)==count and all(x['sort']==sort(R) for x in qs);cases+=1
    d=decl['eot'];names={n:dict(kind='variable',name=p['name']) for (n,t),p in zip(SETTING+[('moment',R)],d['parameters'])};node=d['body'];bs=[]
    for _ in range(4):assert node['kind']=='exists';bs.append(dict(kind='variable',name=node['variable']));node=node['body']
    event,charge,force,scale=bs;calls={x['symbol']:x for x in walk(node) if x.get('kind')=='call' and x.get('symbol') in ('eibs','ek3u','ek3o')}
    assert calls['eibs']['arguments'][:6]==[charge,force,names['matter'],names['frame'],event,names['context']]
    assert calls['eibs']['arguments'][9]==scale
    assert calls['ek3u']['arguments']==[names['matter'],names['frame'],event,charge,names['chargeunit'],scale,names['charge'],names['context']]
    assert calls['ek3o']['arguments']==[names['matter'],names['frame'],event,names['massunit'],names['mass'],names['context']];cases+=1
    # Each actual witness is exposed while the other three become parameters.
    doc=deepcopy(boundary('eot'))
    for i,d in enumerate(doc['declarations']):
        if d['kind']=='definition' and d['name']=='ekbe':doc['declarations'][i]=dict(kind='primitive',name=d['name'],parameters=[p['sort'] for p in d['parameters']],result=d['result'])
    doc=collapse(scalarize(extract_document(doc,roots=['eot'],statement_indices=[]).document));doc['declarations'].append(dict(kind='primitive',name='jkwzero',parameters=[],result='individual'))
    for pivot,slot in enumerate((4,0,1,9)):
        f,dd,slots,name,b=lifted(doc,'eot',pivot,4,'exists');env={p['name']:'case' if p['sort']=='situation' else 'a' for p in dd['parameters']}
        for allowed in (False,True):
            mm={d['name']:(lambda *xs:True) if d['result']=='truth' else (lambda *xs:'a') for d in f['declarations'] if d['kind']=='primitive'}
            mm|={n:lambda x=env[p['name']]:x for n,p in zip(slots,dd['parameters'])};mm['eibs']=lambda *xs:allowed and xs[slot]=='b'
            assert evaluate_document(f,individuals=('a','b'),situations=('case','other'),primitives=mm,max_steps=30000)[0]['value']==allowed;cases+=1
    # Fixed current body/end and all shared settings must not drift to the old drafts.
    for root,target,fields in [('eo7','eou',SETTING),('epd','eo2',ALL),('eph','eo5',ALL),('epf','eo4',SETTING)]:
        d=decl[root];point=dict(kind='variable',name=d['body']['variable']);call=next(x for x in walk(d['body']) if x.get('kind')=='call' and x.get('symbol')==target)
        assert call['arguments']==[point if n=='context' else dict(kind='call',symbol=FIXED[n],arguments=[]) for n,t in fields];cases+=1
    assert FIXED['matter']=='eisxh' and FIXED['end']=='eisxv' and FIXED['finalspeed']=='eisxt';cases+=1
    return dict(cases=cases,public_shared_role_contracts=True,all_four_action_witness_slots_two_value_domain=True,native_universal_time_and_field_domains=True,current_electron_not_old_draft_reference=True)

@lru_cache(None)
def source_record():
    inventory=json.loads(read(INVENTORY));units=inventory['units'][260:262];math=[x for x in inventory['math'] if x['id'] in [f'M042{i}' for i in range(2,8)]]
    for u in units:assert digest(u['text'].encode())==u['text_sha256']
    assert len(math)==6
    return dict(version='einstein-electron-kinetic-work-reading-v1',units=[dict(unit=u['id'],text=u['text'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],math=[m for m in math if m['id'] in u['math_ids']],source_nonblank_characters=len(re.sub(r'\s|\[M\d+\]','',u['text']))) for u in units],facsimile_pages=[919,920],printed_middle_integral_has_no_mu=True,observations=LIMITS,source_sha256={p:digest((ROOT/p).read_bytes()) for p in (INVENTORY,FACSIMILE,DOC)})
@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    before=load_catalog(ROOT,PARENT_BASIS);after=load_catalog(ROOT,BASIS)
    assert len(after.document['statements'])==430 and after.document['statements'][:428]==before.document['statements']
    assert after.document['declarations'][:len(before.document['declarations'])]==before.document['declarations']
    assert all(after.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in before.entries.items())
    formula=extract_document(after.document,roots=[],statement_indices=[429]).document
    assert {'eou','eot','eox','eoz','eo2','eo4','epg','eiszt','eiszu','eiszv','eiszw'}<={d['name'] for d in formula['declarations']}
    assert selection_binding(after,[427])==selection_binding(before,[427]);load_annotations(ROOT,BASIS,ANNOTATIONS)
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    for style in ('compact','full'):
        body=format_graph(core(),style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core()
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=len(MEANINGS),new_general_relations=len(PRIMITIVES),new_reference_constants=len(REFERENCES)+len(NEW_VALUES),new_statements=2,all_428_prior_statements_and_meanings_preserved=True)
def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')
@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('physical',physical_checks),('energy',energy_checks),('presentation',presentation_checks),('bindings',binding_checks),('structure',structure_checks)]}
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,*DEPENDENCIES,'scripts/compose_electron_kinetic_work.py','scripts/check_electron_kinetic_work.py','tests/test_electron_kinetic_work.py'}
    for path in DEPENDENCIES:paths.update(json.loads(read(path))['source_sha256'])
    return dict(status='axial_work_energy_balance_and_printed_integral_connected',document=FULL,**results,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
