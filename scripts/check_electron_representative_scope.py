"""Check coordinate representatives without reducing the physical law question."""
from copy import deepcopy
from functools import lru_cache
from fractions import Fraction as Q
from itertools import product
import json
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts import check_electron_coordinate_normalization as base
from scripts.check_ninth_section_opening import lifted
from scripts.check_problem_series_reduction import collapse
from scripts.compose_electron_representative_scope import *

DOC='docs/electron-representative-scope-v1.md'
DEPENDENCIES=('reports/electron-comoving-history-v1.json','reports/electron-coordinate-normalization-v1.json','reports/electron-moving-law-task-v1.json')
AXES=('x','y','z','t');CONSTANTS=dict(zip(ROLES,AXES))|{'eisxh':'matter'}
PEOPLE=tuple(dict.fromkeys([*base.old.PEOPLE,*AXES,'newframe','newrecord','before','event','after','law','otherlaw','representation','duplicate']))
FIELDS={'ek5z':NORMAL+[('field',FIELD)],'ek52':NORMAL+[('region',REGION)],'ek53':NORMAL+PROFILES+[('axis','a')],'ek54':SETTING,'ek55':SETTING+[('law','a')],'ek56':SETTING,'ek57':EVENT,'ek6a':PAIR,'ek6b':PAIR,'ek6c':PAIR,'ek6d':SETTING,'ek6e':[]}
BOUNDS={'ek54':{'ek3v','ek4m','ek4o'},'ek55':{'ek54','ek32'},'ek56':{'ek54'},'ek57':{'seoa'},'ek6a':{'ek54','ek56','ek5h','ek57'},'ek6b':{'ek55'},'ek6c':{'ek6a','ek6b'},'ek6d':{'ek6c'},'ek6e':{'ek54','ek6d'}}
fn=base.old.fn;sort=base.old.sort;forbidden=base.forbidden

@lru_cache(None)
def core():return parse(read(CORE))

@lru_cache(None)
def boundary(root):
    doc=extract_document(core(),roots=[root],statement_indices=[]).document
    for i,d in enumerate(doc['declarations']):
        if d['kind']=='definition' and d['name'] in base.BOUNDS|BOUNDS.get(root,set()):doc['declarations'][i]=dict(kind='primitive',name=d['name'],parameters=[p['sort'] for p in d['parameters']],result=d['result'])
    return extract_document(doc,roots=[root],statement_indices=[]).document

@lru_cache(None)
def fixture(root,mode='sample'):
    doc=deepcopy(boundary(root));d=next(d for d in doc['declarations'] if d['name']==root)
    if root=='ek6a' and mode=='sample':
        def sample(node):
            if isinstance(node,list):return [sample(x) for x in node]
            if not isinstance(node,dict):return node
            if node.get('kind')=='forall' and node['sort']==sort(R):
                terms=[sample(base.old.old.replace(node['body'],node['variable'],dict(kind='call',symbol=n,arguments=[]))) for n in ('jrstzero','jrstone')]
                return dict(kind='and',arguments=terms)
            return {k:sample(x) for k,x in node.items()}
        d['body']=sample(d['body'])
    slots=[]
    for i,p in enumerate(d['parameters']):
        n='jrsarg'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    doc['declarations'] += [dict(kind='primitive',name=n,parameters=[],result=sort(R)) for n in ('jrstzero','jrstone')]
    expr=dict(kind='call',symbol=root,arguments=[dict(kind='call',symbol=n,arguments=[]) for n in slots])
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jrssituation',parameters=[],result='situation'));expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='jrssituation',arguments=[]))
    elif d['result']!='truth':
        doc['declarations'].append(dict(kind='primitive',name='jrscapture',parameters=[d['result']],result='truth'));expr=dict(kind='call',symbol='jrscapture',arguments=[expr])
    doc['declarations'].sort(key=lambda d:d['kind']!='primitive');doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(root,by,m,mode='sample'):
    doc,slots=fixture(root,mode);captured=[]
    def capture(x):captured.append(x);return True
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|m|{slot:lambda x=by[n]:x for slot,(n,t) in zip(slots,FIELDS[root])}|{'jrscapture':capture,'jrssituation':lambda:'case'}
    value=evaluate_document(doc,individuals=PEOPLE,situations=('case','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=2000000,memoize_definitions=True,memoize_expressions=True)[0]['value']
    return captured[0] if captured else value

class Model:
    def __init__(self,matrix=base.ROTATIONS[3],epoch=2,speed=3):
        by,m,self.c,self.r,self.key=base.old.setup();self.by=by.copy();self.m=m.copy();c,r=self.c,self.r
        self.matrix=matrix;self.origin=(Q(1),Q(2),Q(3),Q(epoch));self.point=lambda xs:base.old.old.point(c,xs)
        self.pv=lambda p:tuple(r(p(a)) for a in AXES)
        self.u=tuple(Q(speed)*Q(x) for x in matrix[0]);self.acc=(Q(2),Q(-4),Q(6))
        self.by.update({n:c(x) for (n,t),x in zip(MATRIX,base.flatten(matrix))})
        self.by.update(newframe='newframe',newrecord='newrecord',point=self.point(self.origin),origin=self.point(self.origin),time=c(epoch),observed='event',axis='x',law='law',lengthscale=Q(3),timescale=Q(2),massscale=Q(5),forcescale=Q(15,4),chargescale=Q(7))
        self.by['domain']=fn(sort(DOMAIN),lambda t:abs(r(t)-epoch)<2)
        def curve(t):
            d=r(t)-epoch;return self.point(tuple(self.origin[i]+self.u[i]*d+self.acc[i]*d*d/2 for i in range(3))+(r(t),))
        self.by['curve']=fn(sort(CURVE),curve)
        for i,(n,t) in enumerate(PROFILES):self.by[n]=fn(sort(t),lambda time,i=i:c(self.u[i]+self.acc[i]*(r(time)-epoch)))
        for i,(n,t) in enumerate(ACCEL):self.by[n]=c(self.acc[i])
        def field(offset):return fn(sort(FIELD),lambda axis:fn(sort('h['+' '.join([R]*4)+'] '+R),lambda x,y,z,t:c(offset+{'x':r(x)+2*r(y)-r(t),'y':-r(x)+3*r(z)+r(t),'z':r(y)-2*r(z)+4*r(t)}.get(axis,0))))
        self.by['electricfield']=field(1);self.by['magneticfield']=field(7)
        self.by['region']=fn(sort(REGION),lambda x,y,z,t:-3<r(x)+2*r(y)-r(z)+r(t)<8)
        self.m|={'eisxt':lambda:c(speed),'jrstzero':lambda:c(0),'jrstone':lambda:c(1)}
        self.target=self.transformed()
    def inverse(self,point):
        spatial=tuple(base.dot(column,point[:3])+self.origin[i] for i,column in enumerate(zip(*self.matrix)))
        return spatial+(Q(point[3])+self.origin[3],)
    def transformed(self):
        c,r=self.c,self.r;by=self.by;matrix=self.matrix;origin=self.origin
        target=by.copy();target.update(frame='newframe',chargerecord='newrecord',point=self.point((0,0,0,0)))
        target['domain']=fn(sort(DOMAIN),lambda t:by['domain'](c(r(t)+origin[3])))
        target['curve']=fn(sort(CURVE),lambda t:self.point(base.norm(matrix,origin,self.pv(by['curve'](c(r(t)+origin[3]))))))
        for i,(n,t) in enumerate(PROFILES):target[n]=fn(sort(t),lambda time,i=i:c(base.dot(matrix[i],[r(by[name](c(r(time)+origin[3]))) for name,typ in PROFILES])))
        for i,(n,t) in enumerate(ACCEL):target[n]=c(base.dot(matrix[i],self.acc))
        def converted(field):
            def component(axis):
                def value(*coords):
                    old=self.inverse(tuple(map(r,coords)));values=[r(field(a)(*map(c,old))) for a in AXES[:3]]
                    return c(base.dot(matrix[AXES.index(axis)],values) if axis in AXES[:3] else 0)
                return fn(sort('h['+' '.join([R]*4)+'] '+R),value)
            return fn(sort(FIELD),component)
        target['electricfield']=converted(by['electricfield']);target['magneticfield']=converted(by['magneticfield'])
        target['region']=fn(sort(REGION),lambda *xs:by['region'](*map(c,self.inverse(tuple(map(r,xs))))))
        return target
    def values(self,fields,by=None):return [ (by or self.by)[n] for n,t in fields]

@lru_cache(None)
def field_checks():
    cases=0
    for matrix in base.ROTATIONS:
        for epoch in (0,2):
            a=Model(matrix,epoch);c,r=a.c,a.r;by,m=a.by,a.m
            for name in ('electricfield','magneticfield'):
                field=run('ek5z',by|{'field':by[name]},m)
                for point in base.POINTS:
                    for axis in AXES[:3]:
                        assert r(field(axis)(*map(c,point)))==r(a.target[name](axis)(*map(c,point)));cases+=1
            region=run('ek52',by,m)
            for point in base.POINTS:
                assert region(*map(c,point))==a.target['region'](*map(c,point));cases+=1
            for axis,(n,t) in zip(AXES[:3],PROFILES):
                profile=run('ek53',by|{'axis':axis},m)
                for moment in (-2,0,Q(1,2),1,3):
                    assert r(profile(c(moment)))==r(a.target[n](c(moment)));cases+=1
            for name in ('electricfield','magneticfield'):
                base.old.old.reject(lambda:run('ek5z',by|{'field':fn(sort(FIELD),forbidden)},m)('x')(*map(c,(0,0,0,0))),unknown=True);cases+=1
    return dict(cases=cases,two_distinct_nonuniform_fields_pulled_back_before_rotation=True,space_and_time_offsets_and_inverse_matrix_distinguished=True,region_and_all_velocity_profiles_use_same_map=True)

@lru_cache(None)
def setting_checks():
    a=Model();by,m,key=a.by,a.m,a.key;cases=0;sk=key(a.values(SETTING))
    mk=key([by['domain'],by['curve']]);speedkey=key([by[n] for n,t in REST]+[a.c(3)])
    for physical,moving,speed in product((False,True),repeat=3):
        mm=m|{'ek3v':lambda *xs:physical and key(xs)==sk,'ek4m':lambda *xs:moving and key(xs)==mk,'ek4o':lambda *xs:speed and key(xs)==speedkey}
        assert run('ek54',by,mm)==(physical and moving and speed);cases+=1
    mm=m|{'ek3v':lambda *xs:True,'ek4m':lambda *xs:True,'ek4o':lambda *xs:True}
    assert run('ek54',by|{'frame':'newframe'},mm);cases+=1
    assert not run('ek54',by|{'matter':'other'},mm);cases+=1
    for name in ('ek3v','ek4m','ek4o'):
        base.old.old.reject(lambda:run('ek54',by,mm|{name:forbidden}),unknown=True);cases+=1
    target=a.target;tm=m|{'ek54':lambda *xs:True}
    assert run('ek56',target,tm);cases+=1
    for axis in range(4):
        assert not run('ek56',target|{'point':a.point(tuple(1 if i==axis else 0 for i in range(4)))},tm);cases+=1
    for i,(name,typ) in enumerate(PROFILES):
        changed=fn(sort(typ),lambda time,i=i:a.c((3 if i==0 else 0)+1))
        assert not run('ek56',target|{name:changed},tm);cases+=1
    # A physical law is not one matching record: all corresponding records matter.
    records={'representation','duplicate'}
    cm=m|{'ek54':lambda *xs:key(xs)==sk,'ek32':lambda *xs:key(xs)==key(a.values(FUTURE)),'vd':lambda law,ctx:(law,ctx)==('law','case'),'eisxn':lambda law,matter,frame,ctx:(law,matter,frame,ctx)==('law','matter','frame','case'),'eisbi':lambda law,frame,ctx:(law,frame,ctx)==('law','frame','case'),'eisxo':lambda rep,*xs:rep in records and key(xs)==sk,'vi':lambda law,rep,ctx:(law,ctx)==('law','case') and rep in records}
    assert run('ek55',by,cm);cases+=1
    for name in ('ek54','ek32','vd','eisxn','eisbi','eisxo'):
        assert not run('ek55',by,cm|{name:lambda *xs:False});cases+=1
        base.old.old.reject(lambda:run('ek55',by,cm|{name:forbidden}),unknown=True);cases+=1
    for record in records:
        assert not run('ek55',by,cm|{'vi':lambda law,rep,ctx,record=record:rep!=record});cases+=1
    return dict(cases=cases,only_fixed_K_removed_from_setting=True,same_particle_and_all_prior_physical_conditions_retained=True,law_candidates_keep_nonempty_all_record_fit=True)

@lru_cache(None)
def transport_checks():
    a=Model();by,m,key=a.by,a.m,a.key;cases=0
    oldkey=key(a.values(SETTING));newkey=key(a.values(SETTING,a.target));pairkey=key(a.values(PAIR))
    chartkey=key([by['frame'],by['newframe'],by['lengthunit'],by['timeunit'],by['context'],*[by[n] for n,t in MATRIX],by['point']])
    mm=m|{'ek54':lambda *xs:key(xs)==oldkey,'ek56':lambda *xs:key(xs)==newkey,'ek5h':lambda *xs:key(xs)==chartkey,'ek57':lambda *xs:key(xs[:-2])==pairkey}
    assert run('ek6a',by,mm);cases+=1
    for symbol,expected in [('ek54',oldkey),('ek56',newkey),('ek5h',chartkey)]:
        for i in range(len(expected)):
            wrong=list(expected);wrong[i]=('different',i)
            assert not run('ek6a',by,mm|{symbol:lambda *xs,wrong=tuple(wrong):key(xs)==wrong});cases+=1
        base.old.old.reject(lambda:run('ek6a',by,mm|{symbol:forbidden}),unknown=True);cases+=1
    for event in ('event','before'):
        for time in (0,1):
            assert not run('ek6a',by,mm|{'ek57':lambda *xs,event=event,time=time:not(xs[-2]==event and a.r(xs[-1])==time)});cases+=1
    base.old.old.reject(lambda:run('ek6a',by,mm,'native'));cases+=1
    # Same event/time tuples from the actual forward/reverse native body.
    observed=[]
    def record(*xs):observed.append(key(xs));return True
    for t in (0,1,2,3):
        observed.clear();assert run('ek57',by|{'time':a.c(t)},m|{'seoa':record});cases+=1
        oldtrack=[by['matter'],by['frame'],by['context'],by['domain'],by['curve']]
        newtrack=[by['matter'],by['newframe'],by['context'],a.target['domain'],a.target['curve']]
        want=[key([*oldtrack,'event',a.c(t)]),key([*newtrack,'event',a.c(t-2)]),key([*newtrack,'event',a.c(t)]),key([*oldtrack,'event',a.c(t+2)])]
        assert set(observed)==set(want);cases+=1
        for missing in (want[1],want[3]):
            assert not run('ek57',by|{'time':a.c(t)},m|{'seoa':lambda *xs,missing=missing:key(xs)!=missing});cases+=1
    return dict(cases=cases,all_transformed_setting_roles_and_physical_chart_bound=True,same_event_in_both_directions_at_shifted_times=True,full_real_time_quantification_not_finitely_certified=True)

@lru_cache(None)
def candidate_preservation_checks():
    a=Model();by,m,key=a.by,a.m,a.key;oldkey=key(a.values(SETTING));newkey=key(a.values(SETTING,a.target));pairkey=key(a.values(PAIR));cases=0
    for oldset,newset in [(set(),set()),({'law'},{'law'}),({'law','otherlaw'},{'law','otherlaw'}),({'law'},set()),(set(),{'law'}),({'law'},{'otherlaw'})]:
        def candidate(*xs):
            if xs[-1] not in oldset|newset:return False
            setting=key(xs[:-1])
            return xs[-1] in (oldset if setting==oldkey else newset if setting==newkey else set())
        assert run('ek6b',by,m|{'ek55':candidate})==(oldset==newset);cases+=1
    base.old.old.reject(lambda:run('ek6b',by,m|{'ek55':forbidden}),unknown=True);cases+=1
    for physical,answers in product((False,True),repeat=2):
        assert run('ek6c',by,m|{'ek6a':lambda *xs:physical and key(xs)==pairkey,'ek6b':lambda *xs:answers and key(xs)==pairkey})==(physical and answers);cases+=1
    for part in ('ek6a','ek6b'):
        for i in range(len(PAIR)):
            wrong=list(pairkey);wrong[i]=('different',i)
            assert not run('ek6c',by,m|{'ek6a':lambda *xs:True,'ek6b':lambda *xs:True,part:lambda *xs,wrong=tuple(wrong):key(xs)==wrong});cases+=1
    return dict(cases=cases,empty_single_and_multiple_law_answer_sets_preserved_bidirectionally=True,same_physical_laws_not_identical_printed_formulae=True,one_shared_representative_for_physics_and_question=True)

@lru_cache(None)
def binder_checks():
    def scalarize(node):
        if node=='number':return 'individual'
        if isinstance(node,list):return [scalarize(x) for x in node]
        if not isinstance(node,dict):return node
        return {k:scalarize(x) for k,x in node.items()}
    cases=0
    for root,count,kind in [('ek6d',len(CHOICE),'exists'),('ek6e',len(SETTING)-1,'forall')]:
        doc=collapse(scalarize(boundary(root)))
        declaration=next(d for d in doc['declarations'] if d['name']==root)
        chain=declaration['body'];context=None
        if root=='ek6e':context=chain['variable'];chain=chain['body']
        names=[]
        for _ in range(count):
            assert chain['kind']==kind;names.append(chain['variable']);chain=chain['body']
        if root=='ek6d':
            expected=[p['name'] for p in declaration['parameters']]+names
            assert [x['name'] for x in chain['arguments']]==expected
        else:
            sequence=iter(names);expected=[context if n=='context' else next(sequence) for n,t in SETTING]
            assert all([x['name'] for x in call['arguments']]==expected for call in chain['arguments'])
        for pivot in range(count):
            f,d,slots,var,body=lifted(doc,root,pivot,count,kind)
            env={p['name']:'case' if p['sort']=='situation' else 'a' for p in d['parameters']}
            if kind=='exists':
                assert body['kind']=='call' and body['symbol']=='ek6c';arguments=body['arguments']
                scenarios=[((),(),False),(('a',),(),True),(('b',),(),True)]
            else:
                left,right=body['arguments'];assert left['symbol']=='ek54' and right['symbol']=='ek6d' and left['arguments']==right['arguments'];arguments=left['arguments']
                scenarios=[(('a','b'),('a','b'),True),(('a','b'),('a',),False),(('b',),('a',),False),((),(),True)]
            def rows(picks):return {tuple((env|{var:p})[x['name']] for x in arguments) for p in picks}
            for selected,allowed,want in scenarios:
                mm={n:lambda x=env[p['name']]:x for n,p in zip(slots,d['parameters'])}
                mm|={'ek6c':lambda *xs:xs in rows(selected)} if kind=='exists' else {'ek54':lambda *xs:xs in rows(selected),'ek6d':lambda *xs:xs in rows(allowed)}
                assert evaluate_document(f,individuals=('a','b'),situations=('case','other'),primitives=mm,max_steps=20000)[0]['value']==want;cases+=1
    a=Model()
    for root in ('ek6d','ek6e'):
        base.old.old.reject(lambda:run(root,a.by,a.m,'native'));cases+=1
    return dict(cases=cases,all_representative_witness_and_general_setting_slots_checked=True,one_actual_binder_at_a_time_two_value_diagnostics=True,native_full_function_domains_refused=True)

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    before=load_catalog(ROOT,PARENT_BASIS);after=load_catalog(ROOT,BASIS)
    assert after.document['statements']==before.document['statements'] and len(after.document['statements'])==417
    assert after.document['declarations'][:len(before.document['declarations'])]==before.document['declarations']
    assert all(after.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in before.entries.items())
    ds={d['name']:d for d in after.document['declarations']}
    def rename(node):
        if isinstance(node,list):return [rename(x) for x in node]
        if not isinstance(node,dict):return node
        return {k:('ek54' if k=='symbol' and x=='ek4p' else rename(x)) for k,x in node.items()}
    assert ds['ek55']['parameters']==ds['ek4w']['parameters'] and ds['ek55']['body']==rename(ds['ek4w']['body'])
    assert selection_binding(after,[415,416])==selection_binding(before,[415,416]);load_annotations(ROOT,BASIS,ANNOTATIONS)
    assert json.loads(read(ANNOTATIONS))['entries']==json.loads(read('data/electron-comoving-history-identifiers-v1.json'))['entries']
    assert len(MEANINGS)==12
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    for style in ('compact','full'):
        body=format_graph(core(),style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core()
    return dict(new_definitions=12,new_primitives=0,new_statements=0,all_417_prior_statements_and_meanings_preserved=True,general_law_candidate_changes_only_setting_frame_restriction=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('fields',field_checks),('setting',setting_checks),('transport',transport_checks),('answers',candidate_preservation_checks),('binders',binder_checks),('structure',structure_checks)]}
    helpers=('compose_limits','compose_material_relative_frame','compose_point_particle_dynamics','compose_electron_rest_law_claim','compose_electron_coordinate_normalization','compose_field_transform','compose_doppler_infinity','compose_relativity_conjecture','check_electron_coordinate_normalization','check_point_particle_dynamics','check_attached_material_charge','check_ninth_section_opening','check_problem_series_reduction','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|{DOC,*DEPENDENCIES,'data/einstein-electron-coordinate-obligations-v1.json','scripts/compose_electron_representative_scope.py','scripts/check_electron_representative_scope.py','tests/test_electron_representative_scope.py',*(f'scripts/{n}.py' for n in helpers)}
    return dict(status='complete_representative_settings_and_law_answer_preservation_checked',document=FULL,**results,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
