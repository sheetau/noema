"""Check shared material events, all-point application and ten local witness slots."""
from functools import lru_cache
from copy import deepcopy
import json
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import FunctionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts import check_carrier_charge_composition as prior
from scripts.check_problem_series_reduction import collapse
from scripts.compose_carrier_field_correspondence import *

old=prior.old
DOC='docs/carrier-field-correspondence-v1.md';SOURCE='data/einstein-carrier-field-correspondence-obligations-v1.json'
DEPENDENCIES=('reports/carrier-charge-composition-v1.json','reports/convective-charge-setting-v1.json')
BOUNDS={'ekyh':{'ejsl'},'ekyi':{'ekyh'},'ekyj':{'ekyb','ejsj','ekyi'},'ekyk':{'ekyf'},'ekyl':{'ekyc','ekyj','ejsn','ejsj','ekyk','ekxk','ekxl'}}
PEOPLE=tuple(dict.fromkeys([*prior.PEOPLE,*(n for n,t in BRIDGE if t=='a')]))

@lru_cache(None)
def core():return parse(read(CORE))

@lru_cache(None)
def fixture(root,mode='sample'):
    doc=extract_document(core(),roots=[root],statement_indices=[]).document
    for i,d in enumerate(doc['declarations']):
        if d['kind']=='definition' and d['name'] in old.NUM|{'bg','bj','szi'}|BOUNDS.get(root,set()):
            doc['declarations'][i]=dict(kind='primitive',name=d['name'],parameters=[p['sort'] for p in d['parameters']],result=d['result'])
    doc=extract_document(doc,roots=[root],statement_indices=[]).document
    if mode.startswith('slot:'):
        assert root=='ekyk';doc=collapse(doc)
    d=next(d for d in doc['declarations'] if d['name']==root)
    if mode.startswith('slot:'):
        pivot=int(mode.split(':')[1]);node=d['body'];kept=None
        for i,(name,t) in enumerate(LOCAL_WITNESSES):
            assert node['kind']=='exists'
            if i==pivot:kept={k:node[k] for k in ('kind','variable','sort')}
            else:d['parameters'].append(dict(name=node['variable'],sort=node['sort']))
            node=node['body']
        assert node['symbol']=='ekyf';d['body']=kept|dict(body=node)
    elif mode=='sample':
        groups=[('individual',('jafbodya','jafbodyb')),(old.RS,('jaftimea','jaftimeb')),(old.PS,('jafpointa','jafpointb'))]
        def sample(node):
            if isinstance(node,list):return [sample(x) for x in node]
            if not isinstance(node,dict):return node
            if node.get('kind') in ('exists','forall'):
                names=next((ns for s,ns in groups if s==node['sort']),None)
                if names:return dict(kind='and' if node['kind']=='forall' else 'or',arguments=[sample(old.replace(node['body'],node['variable'],dict(kind='call',symbol=n,arguments=[]))) for n in names])
            return {k:sample(v) for k,v in node.items()}
        d['body']=sample(d['body'])
    extras={'jafbodya':'individual','jafbodyb':'individual','jaftimea':old.RS,'jaftimeb':old.RS,'jafpointa':old.PS,'jafpointb':old.PS}
    if not mode.startswith('slot:'):doc['declarations'] += [dict(kind='primitive',name=n,parameters=[],result=s) for n,s in extras.items()]
    slots=[]
    for i,p in enumerate(d['parameters']):
        n='jafarg'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    body=dict(kind='call',symbol=root,arguments=[dict(kind='call',symbol=n,arguments=[]) for n in slots])
    if d['result']!='truth':
        doc['declarations'].append(dict(kind='primitive',name='jafcapture',parameters=[d['result']],result='truth'));body=dict(kind='call',symbol='jafcapture',arguments=[body])
    doc['declarations'].sort(key=lambda d:d['kind']!='primitive');doc['statements']=[dict(kind='ask',body=body)]
    return doc,slots

def run(root,vs,m,mode='sample'):
    doc,slots=fixture(root,mode);assert len(vs)==len(slots),(root,len(vs),len(slots));captured=[]
    def capture(x):captured.append(x);return True
    mm={n:lambda x=x:x for n,x in old.CONSTANTS.items()}|m|{n:lambda x=x:x for n,x in zip(slots,vs)}|{'jafcapture':capture}
    binding=mode.startswith('slot:')
    value=evaluate_document(doc,individuals=('a','b') if binding else PEOPLE,situations=('a','b') if binding else ('case','other'),primitives={d['name']:mm.get(d['name'],old.forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=600000,memoize_definitions=True,memoize_expressions=True)[0]['value']
    return captured[0] if captured else value

def setup():
    by,m,c,r,parts,spaces,oldkey,mask=prior.setup()
    by['portions']=old.fn(old.sort(dict(FAMILY)['portions']),lambda body:parts[2 if body=='a' else 1])
    for name,start in [('ownlower',0),('ownupper',2)]:by[name]=old.fn(old.sort(dict(PACKET)[name]),lambda body,start=start:c(start+(10 if body=='b' else 0)))
    for i,axis in enumerate(('x','y','z')):
        t=dict(PACKET)['own'+axis];family_sort=old.sort(t)['result'];curve_sort=family_sort['result']
        by['own'+axis]=old.fn(old.sort(t),lambda body,i=i:old.fn(family_sort,lambda matter:old.fn(curve_sort,lambda time:c((i+1)*(r(time)+(10 if body=='b' else 0)+(1 if matter=='b' else 0))))))
    points=[old.point(c,(10,20,30,7)),old.point(c,(40,50,60,9))]
    by|=dict(body='a',matter='b',worldevent='a',point=points[0],owntime=c(1))
    m|={'jafbodya':lambda:'a','jafbodyb':lambda:'b','jaftimea':lambda:c(1),'jaftimeb':lambda:c(11),'jafpointa':lambda:points[0],'jafpointb':lambda:points[1]}
    def key(x):
        if isinstance(x,(list,tuple)):return tuple(key(y) for y in x)
        if isinstance(x,FunctionValue) and x.parameters==('individual',) and x.result==old.RS:return tuple(r(x(a)) for a in ('a','b','x','y','z','t'))
        return oldkey(x)
    return by,m,c,r,parts,points,key,mask

def contrasts(root,vs,m,rows,key):
    mm=m|{n:old.rel(rs,key) for n,rs in rows.items()};assert run(root,vs,mm),root;cases=1
    for n,rs in rows.items():
        for row in rs:
            assert not run(root,vs,mm|{n:old.rel(rs-{row},key)}),(root,n,'missing');cases+=1
            for i in range(len(row)):
                wrong=list(row);wrong[i]='wrong'
                assert not run(root,vs,mm|{n:old.rel((rs-{row})|{tuple(wrong)},key)}),(root,n,i);cases+=1
        prior.reject(lambda:run(root,vs,mm|{n:old.forbidden}),True);cases+=1
    return cases

@lru_cache(None)
def location_checks():
    by,m,c,r,parts,points,key,mask=setup();cases=0
    for body in ('a','b'):
        for matter in ('a','b'):
            for time in (1,11):
                loc=by|dict(body=body,matter=matter,owntime=c(time));p=run('ekyg',[loc[n] for n,t in LOCATION],m)
                base=time+(10 if body=='b' else 0)+(1 if matter=='b' else 0)
                for axis,want in zip(('x','y','z','t','other'),(base,2*base,3*base,time,0)):
                    assert r(p(axis))==want;cases+=1
    ownpoint=run('ekyg',[by[n] for n,t in LOCATION],m)
    rows={'ejsl':{key([by[n] for n,t in CHART]),key([by['ownframe']('a'),by['lengthunit'],by['timeunit'],'case'])},'eirh':{('a','b','case')},'zpb':set(),'eisqd':set()}
    for frame,p in [(by['frame'],by['point']),(by['ownframe']('a'),ownpoint)]:
        rows['zpb'].add(key(['b',frame,'a',p,'case']))
        rows['eisqd'].add(key(['b',frame,'a',by['lengthunit'],by['timeunit'],p,'case']))
    memberships={('b','distribution'),('b','componenta')}
    member=lambda pairs:lambda:old.fn(old.sort('h[a a d] c'),lambda who,dist,ctx:ctx=='case' and (who,dist) in pairs)
    mm=m|{'zqn':member(memberships)};vs=[by[n] for n,t in BRIDGE]
    cases+=contrasts('ekyh',vs,mm,rows,key)
    good=mm|{n:old.rel(rs,key) for n,rs in rows.items()}
    for pair in memberships:assert not run('ekyh',vs,good|{'zqn':member(memberships-{pair})});cases+=1
    for name,value in [('body','b'),('matter','a'),('worldevent','b'),('owntime',c(7))]:
        loc=by|{name:value};assert not run('ekyh',[loc[n] for n,t in BRIDGE],good);cases+=1
    assert r(by['point']('t'))!=r(by['owntime']);cases+=1
    return dict(cases=cases,native_all_four_coordinates_share_body_matter_and_time=True,same_material_event_and_both_calibrated_units_required=True,different_coordinate_times_allowed_and_outside_history_rejected=True)

@lru_cache(None)
def event_checks():
    by,m,c,r,parts,points,key,mask=setup();cases=0
    correct=key([by[n] for n,t in BRIDGE]);good=m|{'ekyh':old.rel({correct},key)}
    assert run('ekyi',[by[n] for n,t in EVENT],good);cases+=1
    for i in range(len(correct)):
        wrong=list(correct);wrong[i]='wrong'
        assert not run('ekyi',[by[n] for n,t in EVENT],m|{'ekyh':old.rel({tuple(wrong)},key)});cases+=1
    # Neither (body a,time 11) nor (body b,time 1) is the required joined pair.
    wrongpairs=set()
    for body,time in [('a',11),('b',1)]:
        loc=by|dict(body=body,owntime=c(time));wrongpairs.add(key([loc[n] for n,t in BRIDGE]))
    # A conjunction requires the same pair, not independent body/time witnesses.
    def joined(*xs):return key(xs)==correct and key(xs) in wrongpairs
    assert not run('ekyi',[by[n] for n,t in EVENT],m|{'ekyh':joined});cases+=1
    prior.reject(lambda:run('ekyi',[by[n] for n,t in EVENT],m|{'ekyh':old.forbidden}),True);cases+=1
    prior.reject(lambda:run('ekyi',[by[n] for n,t in EVENT],good,'native'));cases+=1
    positions=set();proofs=set()
    for matter,event,p in [('b','a',points[0]),('a','b',points[1])]:
        loc=by|dict(matter=matter,worldevent=event,point=p)
        positions.add(key([matter,by['frame'],event,p,'case']));proofs.add(key([loc[n] for n,t in EVENT]))
    selected=m|{'zqn':lambda:old.fn(old.sort('h[a a d] c'),lambda who,dist,ctx:who in ('a','b') and (dist,ctx)==('distribution','case')),'zpb':old.rel(positions,key),'ejsj':lambda *xs:True}
    rows={'ekyb':{key([by[n] for n,t in PARTITION])},'ekyi':proofs}
    cases+=contrasts('ekyj',[by[n] for n,t in TRANSFER],selected,rows,key)
    # Positions remain selected when the consequence's explicit units are absent.
    assert not run('ekyj',[by[n] for n,t in TRANSFER],selected|{'ekyb':lambda *xs:True,'ekyi':lambda *xs:False});cases+=1
    prior.reject(lambda:run('ekyj',[by[n] for n,t in TRANSFER],selected|{'ekyb':lambda *xs:True,'ekyi':lambda *xs:True},'native'));cases+=1
    return dict(cases=cases,every_selected_material_event_requires_correspondence=True,body_and_time_witnesses_share_one_relation=True,missing_explicit_units_not_removed_from_selection=True)

@lru_cache(None)
def witness_checks():
    cases=0
    for pivot in range(len(LOCAL_WITNESSES)):
        lifted=[name for i,(name,t) in enumerate(LOCAL_WITNESSES) if i!=pivot]
        fields=[name for name,t in LOCAL]+lifted
        env={name:'a' for name in fields};env[LOCAL_WITNESSES[pivot][0]]='b'
        values=lambda e:[e[n] for n in fields]
        expected=lambda e:tuple(e[n] for n,t in COUPLED_FAMILY)
        def model(e):
            target=expected(e);return {'ekyf':lambda *xs:xs==target}
        mode='slot:'+str(pivot)
        assert run('ekyk',values(env),model(env),mode);cases+=1
        assert not run('ekyk',values(env),{'ekyf':lambda *xs:False},mode);cases+=1
        for name in fields:
            changed=env|{name:'b'}
            assert run('ekyk',values(changed),model(changed),mode),(pivot,name);cases+=1
            assert not run('ekyk',values(changed),model(env),mode),(pivot,name,'unshared');cases+=1
        prior.reject(lambda:run('ekyk',values(env),{'ekyf':old.forbidden},mode),True);cases+=1
    by,m,c,r,parts,points,key,mask=setup()
    prior.reject(lambda:run('ekyk',[by[n] for n,t in LOCAL],m|{'ekyf':lambda *xs:True},'native'));cases+=1
    return dict(cases=cases,all_ten_witness_positions_checked_with_two_values=True,every_fixed_and_lifted_argument_bound_to_same_local_tuple=True,actual_function_and_real_domains_not_enumerated=True)

@lru_cache(None)
def global_checks():
    by,m,c,r,parts,points,key,mask=setup();cases=0
    rows={name:{key([by[n] for n,t in fields])} for name,fields in [('ekyc',ATTACHED),('ekyj',TRANSFER),('ejsn',FIELD_SETTING),('ekxl',FLOW)]}
    rows['ekyk']=set();rows['ekxk']=set()
    for p in points:
        loc=by|dict(point=p,normalized=by['densityfield'](*(p(a) for a in ('x','y','z','t'))))
        rows['ekyk'].add(key([loc[n] for n,t in LOCAL]));rows['ekxk'].add(key([loc[n] for n,t in SUPPORT]))
    mm=m|{'ejsj':lambda *xs:True};vs=[by[n] for n,t in GLOBAL]
    cases+=contrasts('ekyl',vs,mm,rows,key)
    good=mm|{n:old.rel(rs,key) for n,rs in rows.items()}
    assert not run('ekyl',vs,good|{'ejsj':lambda *xs:False});cases+=1
    prior.reject(lambda:run('ekyl',vs,good|{'ejsj':old.forbidden}),True);cases+=1
    prior.reject(lambda:run('ekyl',vs,good,'native'));cases+=1
    return dict(cases=cases,nonempty_domain_and_both_points_required=True,support_velocity_attachment_correspondence_and_fields_share_setting=True,all_point_quantification_preserved=True)

@lru_cache(None)
def source_record():
    previous=json.loads(read('data/einstein-carrier-charge-composition-obligations-v1.json'))
    return dict(version='einstein-carrier-field-correspondence-obligations-v1',kind='dependency_scope_not_semantic_review',unit=previous['unit'],unit_sha256=previous['unit_sha256'],text=previous['text'],resolved_dependencies=list(MEANINGS),reading='担体別の評価系と履歴区間を保った同一物質点・世界線出来事の座標対応を、場の全領域へ電荷合成・密度・速度・六式と共に適用する。同時刻断面の参照eventと物質点のworldeventを別に束縛する。',unresolved=previous['unresolved'][1:],whole_unit_reviewed=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in (old.INVENTORY,old.FACSIMILE,DOC)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    before=load_catalog(ROOT,PARENT_BASIS);after=load_catalog(ROOT,BASIS)
    assert len(after.document['statements'])==408 and after.document['statements']==before.document['statements']
    assert after.document['declarations'][:len(before.document['declarations'])]==before.document['declarations']
    assert all(after.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in before.entries.items())
    assert selection_binding(after,[407])==selection_binding(before,[407]);load_annotations(ROOT,BASIS,ANNOTATIONS)
    assert json.loads(read(ANNOTATIONS))['entries']==json.loads(read('data/carrier-charge-composition-identifiers-v1.json'))['entries']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    names={d['name'] for d in core()['declarations']};assert set(MEANINGS)|{'ekyf','ekyc','ekxk','ekxl','eisqd','zpb','eirh'}<=names
    assert not names&{'eiah','semf','ekbw','ekbx','ekby','ekbz'}
    for style in ('compact','full'):
        body=format_graph(core(),style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core()
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=6,new_general_relations=0,all_408_statements_meanings_and_original_evidence_preserved=True,no_common_rest_frame_or_cross_frame_charge_equality_assumed=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('location',location_checks),('event',event_checks),('witness',witness_checks),('global',global_checks),('structure',structure_checks)]}
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,*DEPENDENCIES,'scripts/compose_carrier_field_correspondence.py','scripts/check_carrier_field_correspondence.py','tests/test_carrier_field_correspondence.py','scripts/check_carrier_charge_composition.py','scripts/check_attached_material_charge.py','scripts/check_problem_series_reduction.py'}
    return dict(status='all_material_events_and_full_field_domain_connected',document=FULL,**results,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
