"""Diagnose the charge-free mass setting and the same-body possible addition."""
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
from scripts.check_clock_site_time import relation,perturb
from scripts.check_ninth_section_opening import lifted
from scripts.check_problem_series_reduction import collapse
from scripts.compose_material_mass_claim import *

DOC='docs/material-mass-claim-v1.md';SOURCE='data/einstein-material-mass-claim-reading-v1.json'
INVENTORY=physical.INVENTORY;FACSIMILE=physical.FACSIMILE
DEPENDENCIES=('reports/electron-convention-caution-v1.json','reports/arbitrary-small-charge-v1.json','reports/electron-directional-masses-v1.json')
CONSTANTS=physical.CONSTANTS|{n:n for n in REFERENCES}|{'eiszm':'eiszm','eisxb':'eisxb','eisxi':'eisxi','zpn':'force'}
PEOPLE=tuple(dict.fromkeys([*physical.PEOPLE,*CONSTANTS.values(),'a','b','unit']))
forbidden=physical.forbidden;reject=physical.reject;walk=physical.walk
BOUNDS={'eoc':{'ek3o','ejwb'},'eod':{'sbw2'},'eoe':{'eod'},'eof':{'eod','eoe'},'eog':{'eof'},'eoh':{'eog'},'eoi':{'eoc','eoh'},'eoj':{'ek3n','ek3o','ejwb'},'eok':{'ek5s','sepp','seoc'},'eol':{'eoj','eok'},'eom':{'eol'},'eon':{'eol','eom'},'eoo':{'eon','eoi','enb','eoe'},'eoq':{'eop'}}

@lru_cache(None)
def core():return parse(read(CORE))
@lru_cache(None)
def boundary(root,mode='native'):
    doc=extract_document(core(),roots=[root],statement_indices=[]).document
    for i,d in enumerate(doc['declarations']):
        if d['kind']=='definition' and d['name'] in physical.NUM|BOUNDS.get(root,set()):doc['declarations'][i]=dict(kind='primitive',name=d['name'],parameters=[p['sort'] for p in d['parameters']],result=d['result'])
    doc=extract_document(doc,roots=[root],statement_indices=[]).document
    if mode=='instance':
        d=next(x for x in doc['declarations'] if x['name']==root);start=d['body']['arguments'][1];body=start
        for _ in range(5 if root=='eoc' else 4):
            assert body['kind']=='exists';d['parameters'].append(dict(name=body['variable'],sort=body['sort']));body=body['body']
        d['body']['arguments'][1]=body
    return doc
@lru_cache(None)
def fixture(root,mode='native'):
    doc=deepcopy(boundary(root,mode));d=next(x for x in doc['declarations'] if x['name']==root);slots=[]
    for i,p in enumerate(d['parameters']):
        n='jmmcslot'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=root,arguments=[dict(kind='call',symbol=n,arguments=[]) for n in slots])
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jmmcpoint',parameters=[],result='situation'));expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='jmmcpoint',arguments=[]))
    doc['declarations'].sort(key=lambda x:x['kind']!='primitive');doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(root,values,m,mode='native'):
    doc,slots=fixture(root,mode);assert len(values)==len(slots)
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|{'jmmcpoint':lambda:'case'}|m|{n:lambda x=x:x for n,x in zip(slots,values)}
    return evaluate_document(doc,individuals=PEOPLE,situations=('case','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=3000000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def callbacks(root,functions):
    lookup={d['name']:d for d in boundary(root)['declarations']};result={}
    for n,fn in functions.items():
        typ=lookup[n]['result'];result[n]=lambda typ=typ,fn=fn:FunctionValue(tuple(typ['parameters']),typ['result'],fn)
    return result

def model(speed=3):
    a=physical.model(speed);a.by.update(forceframe='comoving',light=a.c(5),speed=a.c(speed),offset=a.point(a.offset),newdomain=a.newdomain,newcurve=a.newcurve)
    return a

@lru_cache(None)
def mass_checks():
    cases=0
    for speed in (0,3):
        a=model(speed);c,r,key=a.c,a.r,a.key;values=a.values(MATERIAL);mu=r(a.by['mass']);L=mu*a.beta**3;T=mu*a.beta**2
        mm=a.m|{'eol':lambda *xs:key(xs)==key(values)}
        assert run('eom',values+[c(L),c(T)],mm);cases+=1
        for pair in ((L+1,T),(L,T+1),(T,L)):
            if pair==(L,T):continue
            assert not run('eom',values+list(map(c,pair)),mm);cases+=1
        for axis in range(3):
            force=list(a.pv(a.by['force']));force[axis]+=1;changed=values.copy();changed[-1]=a.point(force)
            assert not run('eom',changed+[c(L),c(T)],mm|{'eol':lambda *xs:True});cases+=1
        # The generalized physics contains no charge requirement.
        used={d['name'] for d in boundary('eom')['declarations']}
        assert not used&{'ek3u','eibs','eisqc','zrdcharge'};cases+=1
        mm=a.m|{'ek3o':lambda *xs:key(xs)==key(a.values(INERTIA)),'ek3n':lambda *xs:True,'ejwb':lambda *xs:True,'eiszn':lambda *xs:xs==(a.by['matter'],'case'),'ad':lambda x,y:x*y}
        a.by.update(lengthscale=Q(18),timescale=Q(3),massscale=Q(5),forcescale=Q(10),accelerationscale=Q(2))
        assert run('eoj',a.values(MATERIAL),mm);cases+=1
        for name in ('lengthscale','timescale','massscale','forcescale','accelerationscale'):
            changed=a.values(MATERIAL);i=[n for n,t in MATERIAL].index(name);changed[i]+=1
            assert not run('eoj',changed,mm);cases+=1
        for symbol in ('ek3o','ek3n','ejwb','eiszn'):assert not run('eoj',a.values(MATERIAL),mm|{symbol:lambda *xs:False});cases+=1
    a=model();values=a.values(MATERIAL);key=a.key
    wanted={'eoj':key(values),'eok':key(values),'eiszo':(a.by['forcerecord'],a.by['matter'],'comoving',a.by['event'],'case'),'zpc':key([a.by['forcerecord'],a.by['matter'],CONSTANTS.get('zpn','force'), 'comoving',a.by['event'],a.by['forceunit'],a.by['force'],'case']),'zraconvention':(a.by['matter'],'comoving','frame',a.by['event'],a.by['forceunit'],'acceleration_unit','case')}
    mm={n:lambda *xs,row=row:key(xs)==row for n,row in wanted.items()}
    assert run('eol',values,mm);cases+=1
    for name in wanted:assert not run('eol',values,mm|{name:lambda *xs:False});cases+=1
    for name in wanted:reject(lambda:run('eol',values,mm|{name:forbidden}));cases+=1
    return dict(cases=cases,same_mass_units_force_and_actual_accelerations=True,neutral_materials_not_excluded=True,both_directional_coefficients_and_zero_speed=True)

@lru_cache(None)
def history_checks():
    a=model();key=a.key;by=a.by;values=a.values(MATERIAL);hist=by|{'first':'frame','second':'comoving','olddomain':by['domain'],'oldcurve':by['curve']}
    old=key([by[n] for n,t in AT]);newpoint=a.point(a.offset)
    new=key([by['matter'],'comoving','case',a.newdomain,a.newcurve,by['event'],newpoint,a.c(0),a.c(0),a.c(0)])
    rows={'ek5s':key([hist[n] for n,t in TWOHISTORY]),'sepp':old,'seoc':new}
    mm=a.m|{n:lambda *xs,row=row:key(xs)==row for n,row in rows.items()}
    assert run('eok',values,mm);cases=1
    for name in rows:assert not run('eok',values,mm|{name:lambda *xs:False});cases+=1
    for name in ('matter','frame','forceframe','event','lengthunit','timeunit'):
        changed=values.copy();changed[[n for n,t in MATERIAL].index(name)]='a'
        assert not run('eok',changed,mm);cases+=1
    for name in ('velocityx','velocityy','velocityz'):
        typ=next(d for d in core()['declarations'] if d['name']=='eok')['parameters'][[n for n,t in MATERIAL].index(name)]['sort'];changed=values.copy();changed[[n for n,t in MATERIAL].index(name)]=FunctionValue(tuple(typ['parameters']),typ['result'],lambda x:a.c(11))
        assert not run('eok',changed,mm|{'sepp':lambda *xs:True});cases+=1
    reject(lambda:run('eok',values,mm|{'sepp':forbidden}));cases+=1
    return dict(cases=cases,same_two_complete_histories_and_event=True,actual_velocity_profiles_and_comoving_zero_roles=True)

def charge_model(before=0,amount=Q(1,2),after=None):
    a=model();c,r=a.c,a.r;after=Q(before)+Q(amount) if after is None else Q(after)
    fns={'zrdcharge':lambda body,unit,ctx:c(before if ctx=='case' else after),'zrdamount':lambda *xs:c(amount),'zrdpossible':lambda *xs:xs==('a','matter','case','other'),'zrdadded':lambda op,body,unit,qty,ctx,alt:(op,body,unit,ctx,alt)==('a','matter','unit','case','other') and r(qty)==amount}
    mm=a.m|callbacks('eof',fns)|{'eiszn':lambda body,ctx:body=='matter','eirk':lambda *xs:xs==('a','matter','case'),'eod':lambda *xs:xs==('matter','unit','case'),'eoe':lambda *xs:xs==('matter','unit','other')}
    return a,mm

@lru_cache(None)
def charge_checks():
    cases=0;values=['matter','unit','case',Q(1),'a','other']
    for before,amount,after,want in [(0,Q(1,2),None,True),(0,Q(-1,2),None,True),(2,Q(1,2),None,True),(0,0,None,False),(Q(-1,2),Q(1,2),None,False),(2,Q(1,2),Q(1,2),False),(0,1,None,False)]:
        a,mm=charge_model(before,amount,after);assert run('eof',values,mm)==want;cases+=1
    for bound in (Q(1,10),Q(1,1000),Q(1,10**12)):
        a,mm=charge_model(amount=bound/2);changed=values.copy();changed[3]=bound;assert run('eof',changed,mm);cases+=1
    a,mm=charge_model()
    for sym in ('eiszn','eirk','eod','eoe'):assert not run('eof',values,mm|{sym:lambda *xs:False});cases+=1
    for sym in ('zrdpossible','zrdadded'):
        assert not run('eof',values,mm|callbacks('eof',{sym:lambda *xs:False}));cases+=1
    for pos,replacement in [(0,'a'),(1,'a'),(2,'other'),(4,'b'),(5,'case')]:
        changed=values.copy();changed[pos]=replacement;assert not run('eof',changed,mm);cases+=1
    for sym in ('eirk','eod','eoe'):reject(lambda:run('eof',values,mm|{sym:forbidden}));cases+=1
    reject(lambda:run('eoh',values[:3],{'eog':lambda *xs:True,'aa':lambda a,b:a<b}));cases+=1
    # Actual classifier: nonzero signed physical charge, with both point interpretations and no particle-species identifier.
    for charge,want in [(0,False),(Q(1,3),True),(-2,True)]:
        cm=a.m|callbacks('eoe',{'zrdcharge':lambda *xs:a.c(charge)})|{'eod':lambda *xs:xs==('matter','unit','other'),'eisqc':lambda *xs:xs==('matter','other')}
        assert run('eoe',['matter','unit','other'],cm)==want;cases+=1
    return dict(cases=cases,arbitrarily_small_bound_instances_not_universal_proof=True,signed_addition_and_initial_charge_retained=True,zero_cancellation_replacement_wrong_identity_and_impossible_results_rejected=True,physical_classifier_not_modern_species=True)

@lru_cache(None)
def presentation_checks():
    rows={'uh':{('eiszq','author','eon','tenth','case'),('eiszr','author','eoi','tenth','case')},'eiswm':{('eiszq','author','eisy3','enb','paper','case')},'zc':{('eiszr','author','eoi','eon','tenth','case')},'eiszp':{('eiszs','author','eisxi','eoe','eisxb','paper','tenth','case')},'ue':{('eiszq','eiszr','case'),('eiszr','eiszs','case')}}
    mm={n:relation(rs) for n,rs in rows.items()}|{n:forbidden for n in ('eon','eoi','enb','eoe')}
    cases=perturb(lambda m:run('eoo',[],m),mm,rows)
    rows={'eir3':{('eiszq','author','paper','eop','case')},'ue':{('eiszm','eiszq','case')}}
    cases+=perturb(lambda m:run('eoq',[],m),{n:relation(rs) for n,rs in rows.items()}|{'eop':forbidden},rows)
    return dict(cases=cases,prior_result_and_same_electron_meaning=True,reason_points_from_charge_possibility_to_mass_result=True,quoted_claims_not_executed=True)

def scalarize(x):
    if x=='number':return 'individual'
    if isinstance(x,list):return [scalarize(y) for y in x]
    if not isinstance(x,dict):return x
    if x.get('kind') in ('number','apply','function_ref'):return dict(kind='call',symbol='jmmczero',arguments=[])
    return {k:scalarize(v) for k,v in x.items()}

@lru_cache(None)
def binding_checks():
    cases=0
    # Public field orders, checked before diagnostic use of actual ASTs.
    d=next(x for x in core()['declarations'] if x['name']=='eof');names={n:p['name'] for (n,t),p in zip(TRIAL,d['parameters'])};var=lambda n:dict(kind='variable',name=names[n])
    calls={x['symbol']:x for x in walk(d['body']) if x.get('kind')=='call' and x['symbol'] in ('seqt','eirk','eod','eoe')}
    assert calls['seqt']['arguments'][:6]==[var(n) for n,t in TRIAL]
    assert calls['eirk']['arguments']==[var(n) for n in ('operation','matter','context')]
    assert calls['eod']['arguments']==[var(n) for n,t in BASE]
    assert calls['eoe']['arguments']==[var(n) for n in ('matter','unit','alternative')];cases+=1
    groups=[]
    for root,count,target in [('eoc',5,'ek3o'),('eod',4,'sbw2'),('eog',2,'eof')]:
        doc=collapse(scalarize(boundary(root)));doc['declarations'].append(dict(kind='primitive',name='jmmczero',parameters=[],result='individual'));d=next(x for x in doc['declarations'] if x['name']==root)
        start=d['body'] if root=='eog' else d['body']['arguments'][1];node=start;bindings=[]
        for _ in range(count):assert node['kind']=='exists';bindings.append(node['variable']);node=node['body']
        if root=='eog':assert node['arguments']==[dict(kind='variable',name=p['name']) for p in d['parameters']]+[dict(kind='variable',name=n) for n in bindings]
        elif root=='eoc':
            m,ctx=[dict(kind='variable',name=p['name']) for p in d['parameters']];vs=[dict(kind='variable',name=n) for n in bindings]
            found=next(x for x in walk(node) if x.get('kind')=='call' and x.get('symbol')=='ek3o');assert found['arguments']==[m,vs[0],vs[1],vs[2],vs[4],ctx]
        else:
            m,unit,ctx=[dict(kind='variable',name=p['name']) for p in d['parameters']];vs=[dict(kind='variable',name=n) for n in bindings]
            assert node['symbol']=='sbw2';assert node['arguments'][:2]==[vs[2],m];assert node['arguments'][3:7]==[vs[0],vs[1],unit,vs[3]];assert node['arguments'][8]==ctx
        groups.append((root,doc,start,d['parameters'],count,target));cases+=1
    # Keep the unit/scale witnesses outside the all-bound capability.
    doc=collapse(scalarize(boundary('eoi')));doc['declarations'].append(dict(kind='primitive',name='jmmczero',parameters=[],result='individual'));d=next(x for x in doc['declarations'] if x['name']=='eoi')
    outer=d['body']['body'];assert outer['kind']=='forall';start=outer['body']['arguments'][1]
    params=[dict(name=d['body']['variable'],sort='situation'),dict(name=outer['variable'],sort='individual')]
    bs=[];node=start
    for _ in range(2):assert node['kind']=='exists';bs.append(node['variable']);node=node['body']
    calls={x['symbol']:x for x in walk(node) if x.get('kind')=='call' and x['symbol'] in ('zof','eoh')}
    var=lambda n:dict(kind='variable',name=n)
    assert calls['eoh']['arguments']==[var(outer['variable']),var(bs[0]),var(d['body']['variable'])]
    assert calls['zof']['arguments'][0]==var(bs[0]) and calls['zof']['arguments'][2]==var(bs[1]);cases+=1
    groups.append(('eoi',doc,start,params,2,'zof'))
    # Lift both actual coefficient witnesses under the fixed material setting.
    doc=collapse(scalarize(boundary('eon')));d=next(x for x in doc['declarations'] if x['name']=='eon');node=d['body']['body'];params=[dict(name=d['body']['variable'],sort='situation')];bound=[]
    fields=[n for n,t in MATERIAL if n not in ('frame','context','light')]
    for _ in fields:assert node['kind']=='forall';params.append(dict(name=node['variable'],sort=node['sort']));bound.append(node['variable']);node=node['body']
    mapping=dict(zip(fields,bound));var=lambda n:dict(kind='variable',name=n);con=lambda n:dict(kind='call',symbol=n,arguments=[])
    actual=[{'frame':con('ra'),'context':var(d['body']['variable']),'light':con('tc')}.get(n,var(mapping.get(n,''))) for n,t in MATERIAL]
    assert node['arguments'][0]==dict(kind='call',symbol='eol',arguments=actual)
    start=node['arguments'][1];bs=[];b=start
    for _ in COEFFICIENTS:assert b['kind']=='exists';bs.append(var(b['variable']));b=b['body']
    assert b==dict(kind='call',symbol='eom',arguments=actual+bs);cases+=1
    groups.append(('eon',doc,start,params,2,'eom'))
    for root,doc,start,parameters,count,target in groups:
        for pivot in range(count):
            f,dd,slots,name,b=lifted(doc,root,pivot,count,'exists',(start,parameters));env={p['name']:'case' if p['sort']=='situation' else 'a' for p in dd['parameters']};special='other' if root=='eog' and pivot==1 else 'b'
            def val(x,env):
                if x['kind']=='variable':return env[x['name']]
                if x['kind']=='apply':return 'a'
                return 'a'
            call=next(x for x in walk(b) if x.get('kind')=='call' and x.get('symbol')==target)
            row=tuple(val(x,env|{name:special}) for x in call['arguments'])
            for allowed in (False,True):
                mm={x['name']:(lambda *xs:True) if x['result']=='truth' else (lambda:'a') for x in f['declarations'] if x['kind']=='primitive'}
                mm|={n:lambda x=env[p['name']]:x for n,p in zip(slots,dd['parameters'])};mm[target]=lambda *xs:allowed and xs==row
                # In eoc the scale witness is checked by the calibration relation, not the mass assignment.
                if root=='eoc' and pivot==3:
                    mm[target]=lambda *xs:True;mm['ejwb']=lambda *xs:allowed and xs[-2]=='b'
                assert evaluate_document(f,individuals=('a','b'),situations=('case','other'),primitives=mm,max_steps=30000)[0]['value']==allowed;cases+=1
    # All-bound contract stays native; it is not a finite list of small examples.
    d=next(x for x in core()['declarations'] if x['name']=='eoh');node=d['body'];assert node['kind']=='forall' and node['sort']=='number'
    assert node['body']['kind']=='implies';call=node['body']['arguments'][1];assert call['symbol']=='eog' and call['arguments']==[dict(kind='variable',name=p['name']) for p in d['parameters']]+[dict(kind='variable',name=node['variable'])];cases+=1
    return dict(cases=cases,public_argument_contracts_for_same_body_units_scenes_and_force_setting=True,all_existential_mass_reading_operation_result_and_coefficient_slots=True,arbitrary_positive_rational_bounds_not_sampled=True)

@lru_cache(None)
def source_record():
    unit=json.loads(read(INVENTORY))['units'][259];assert unit['id']=='einstein-1905:u0260' and digest(unit['text'].encode())==unit['text_sha256']
    return dict(version='einstein-material-mass-claim-reading-v1',unit=unit['id'],text=unit['text'],unit_sha256=unit['text_sha256'],range=[0,len(unit['text'])],math=[],source_nonblank_characters=len(re.sub(r'\s','',unit['text'])),facsimile_pages=[919],observations=LIMITS,source_sha256={p:digest((ROOT/p).read_bytes()) for p in (INVENTORY,FACSIMILE,DOC)})
@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    before=load_catalog(ROOT,PARENT_BASIS);after=load_catalog(ROOT,BASIS)
    assert len(after.document['statements'])==428 and after.document['statements'][:427]==before.document['statements']
    assert after.document['declarations'][:len(before.document['declarations'])]==before.document['declarations']
    assert all(after.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in before.entries.items())
    assert selection_binding(after,[426])==selection_binding(before,[426]);load_annotations(ROOT,BASIS,ANNOTATIONS)
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    for style in ('compact','full'):
        body=format_graph(core(),style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core()
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=len(MEANINGS),new_general_relations=len(PRIMITIVES),new_reference_constants=len(REFERENCES),new_statements=1,all_427_prior_statements_and_meanings_preserved=True)
def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')
@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('mass',mass_checks),('history',history_checks),('charge',charge_checks),('presentation',presentation_checks),('bindings',binding_checks),('structure',structure_checks)]}
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,*DEPENDENCIES,'scripts/compose_material_mass_claim.py','scripts/check_material_mass_claim.py','tests/test_material_mass_claim.py'}
    for path in DEPENDENCIES:paths.update(json.loads(read(path))['source_sha256'])
    return dict(status='mass_result_for_ponderable_points_and_charge_addition_connected',document=FULL,**results,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
