"""Check generic frame/event identity, both physical fields and shared body histories."""
from copy import deepcopy
from functools import lru_cache
from fractions import Fraction as Q
from itertools import product
import json
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import FunctionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_material_relative_frame import NUM,RS
from scripts.check_tau_differential import ConstructedCuts
from scripts.compose_body_rest_field_method import *

DOC='docs/body-rest-field-method-v1.md'
DEPENDENCIES=('reports/problem-series-reduction-v1.json','reports/wave-transform-application-v1.json','reports/material-body-motion-v1.json','reports/vacuum-field-domain-v1.json')
CONSTANTS={'yn':'x','yo':'y','yp':'z','zc7':'t','ta':'lengthunit','rb':'timeunit'}
DOMAIN=tuple(dict.fromkeys([*CONSTANTS.values(),*[n for n,t in SETTING if t=='a'],'old','new','body','process','eventa','eventb','lab','own','lab2','own2','other','a','b']))
BOUNDS={'ekvv':{'eiyx'},'ekvw':{'eiyx'},'ekvx':{'ekvw','ekvv'},'ekvy':{'ekvx','ekvv'},'ekvz':{'ejsn','eispn'},'ekv2':{'eiag','eiah'},'ekv3':{'ekvv'},'ekv4':{'ekvy','ekvz','ekv2','ekv3'},'ekv6':{'ekv4'}}

def forbidden(*xs):raise ValueError('Unknown body-rest field input')
def function(params,result,fn):return FunctionValue(tuple(params),result,fn)
def rejects(call,phrase):
    try:call()
    except ValueError as e:assert phrase in str(e),str(e)
    else:raise AssertionError('Expected rejection: '+phrase)

def numbers():
    cuts=ConstructedCuts();m={};cuts.arithmetic(m);c,r=cuts.make,cuts.read
    m['ba']=lambda x:True if isinstance(r(x),Q) else False
    m|={'zzba':m['ba'],'zzbc':m['bc'],'be':lambda x:c(-r(x)),'sje':lambda x,y:c(r(x)/r(y)),'szi':lambda flag,x,y:x if flag else y,'soy':lambda V,s:c(Q(5,4)) if r(V)==5 and abs(r(s))==3 else forbidden()}
    return cuts,m

@lru_cache(None)
def core():return parse(read(CORE))

@lru_cache(None)
def fixture(root,mode='native'):
    doc=extract_document(core(),roots=[root],statement_indices=[]).document
    cuts=NUM|{'bg','be','sjd','sje','soy','szi'}|BOUNDS.get(root,set())
    if mode=='history':cuts.discard('eiah');cuts|={'eiad','eiae'}
    if mode=='pairs':cuts.add('ekce')
    abstract(doc,{d['name'] for d in doc['declarations'] if d['kind']=='definition' and d['name'] in cuts});doc=extract_document(doc,roots=[root],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==root);slots=[]
    for i,p in enumerate(d['parameters']):
        n='jbrf'+number_word(i);slots.append((n,p['sort']));doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=root,arguments=[dict(kind='call',symbol=n,arguments=[]) for n,s in slots])
    if isinstance(d['result'],dict):
        doc['declarations'].append(dict(kind='primitive',name='jbrfcapture',parameters=[d['result']],result='truth'));expr=dict(kind='call',symbol='jbrfcapture',arguments=[expr])
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(root,values,model,mode='native',domain=DOMAIN):
    doc,slots=fixture(root,mode);assert len(values)==len(slots),(root,len(values),len(slots));captured=[]
    def capture(x):captured.append(x);return True
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|model|{n:lambda x=x:x for (n,s),x in zip(slots,values)}|{'jbrfcapture':capture}
    result=evaluate_document(doc,individuals=domain,situations=('case','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=700000,memoize_definitions=True,memoize_expressions=True)[0]['value']
    return captured[0] if captured else result

def point(c,coords):return function(['individual'],RS,lambda role:c(coords[('x','y','z','t').index(role)]) if role in ('x','y','z','t') else c(0))
def relation(rows):return lambda *xs:xs in rows
def record_model(c,coords):return lambda record,role:c(coords[record][('x','y','z','t').index(role)]) if record in coords and role in ('x','y','z','t') else c(0)

@lru_cache(None)
def event_checks():
    cases=0;members={('eventa','process','case'),('eventb','process','case')}
    rows={('eventa','lab','old','case'),('eventa','own','new','case'),('eventb','lab2','old','case'),('eventb','own2','new','case')}
    mm={'eispo':relation(members),'eiyx':relation(rows)};vs=['process','old','new','case']
    assert run('ekvw',vs,mm);cases+=1
    assert run('ekvv',vs+['lab','own'],mm);cases+=1
    assert not run('ekvv',vs+['lab','own2'],mm);cases+=1
    for row in rows:
        assert not run('ekvw',vs,mm|{'eiyx':relation(rows-{row})});cases+=1
    for i in range(4):
        wrong=vs.copy();wrong[i]='other';assert not run('ekvw',wrong,mm);cases+=1
    assert not run('ekvw',vs,mm|{'eispo':lambda *xs:False});cases+=1
    for n in mm:rejects(lambda:run('ekvw',vs,mm|{n:forbidden}),'Unknown body-rest');cases+=1
    cuts,m=numbers();c=cuts.make
    coords={'a':(1,2,-1,1),'b':(Q(-5,2),2,-1,Q(11,10))}
    assert run('ekce',[c(5),c(3),point(c,coords['a']),point(c,coords['b'])],m);cases+=1
    for record in ('a','b'):
        for i in range(4):
            changed=coords|{record:tuple(x+1 if j==i else x for j,x in enumerate(coords[record]))}
            assert not run('ekce',[c(5),c(3),point(c,changed['a']),point(c,changed['b'])],m);cases+=1
    # Isolate all-pair routing in a two-individual diagnostic. The actual
    # four-coordinate body above is evaluated separately, not quadratically
    # for unrelated individual names at every false guard.
    for selected in product(('a','b'),repeat=2):
        frames=('a','a','b','case');vs=list(frames)+[c(5),c(3)]
        pair=lambda *xs:xs[:4]==frames and xs[4:]==selected
        nums=lambda record,role:c(0 if record=='a' else 1)
        wanted=(Q(5),Q(3),Q(selected[0]=='b'),Q(selected[1]=='b'))
        def key(V,s,old,new):return cuts.read(V),cuts.read(s),cuts.read(old('a')),cuts.read(new('a'))
        mm=m|{'ekvw':lambda *xs:xs==frames,'ekvv':pair,'zc6':nums,'ekce':lambda *xs:key(*xs)==wanted}
        assert run('ekvx',vs,mm,'pairs',('a','b'));cases+=1
        for i in range(4):
            bad=tuple(x+1 if j==i else x for j,x in enumerate(wanted))
            assert not run('ekvx',vs,mm|{'ekce':lambda *xs,bad=bad:key(*xs)==bad},'pairs',('a','b'));cases+=1
        assert not run('ekvx',vs,mm|{'ekvv':lambda *xs:xs[:4]==frames},'pairs',('a','b'));cases+=1
    rejects(lambda:run('ekvx',vs,mm|{'ekvv':forbidden},'pairs',('a','b')),'Unknown body-rest');cases+=1
    return dict(cases=cases,generic_frames_same_event_and_all_records=True,all_four_coordinates_both_directions=True)

@lru_cache(None)
def region_checks():
    cuts,m=numbers();c,r=cuts.make,cuts.read;cases=0;vs=['process','old','new','case',c(5),c(3)]
    coords={'a':(0,0,0,1),'b':(Q(-15,4),0,0,Q(5,4))}
    pair=lambda *xs:xs[:4]==tuple(vs[:4]) and xs[4:]==('a','b')
    region=function([RS]*4,'truth',lambda x,y,z,t:r(x)==0 and 0<=r(t)<=2)
    mm=m|{'ekvx':lambda *xs:True,'ekvv':pair,'zc6':record_model(c,coords)}
    assert run('ekvy',vs+[region],mm);cases+=1
    for changed in ({'b':(0,0,0,1)}, {'a':(3,0,0,1)}, {'b':(Q(-15,4),0,0,4)}):
        assert not run('ekvy',vs+[region],mm|{'zc6':record_model(c,coords|changed)});cases+=1
    assert not run('ekvy',vs+[function([RS]*4,'truth',lambda *xs:False)],mm);cases+=1
    assert not run('ekvy',vs+[region],mm|{'ekvv':lambda *xs:False});cases+=1
    # Actual native lg with lower/upper/time in the declared order.
    intervals=[c(0),c(2),c(1),c(2)]
    assert run('ekv3',vs+[region]+intervals,mm);cases+=1
    for bounds in ((Q(3,2),2,1,2),(0,Q(1,2),1,2),(0,2,Q(3,2),2),(0,2,0,1)):
        assert not run('ekv3',vs+[region]+list(map(c,bounds)),mm);cases+=1
    # A second outside-domain event still needs coordinates, but not this
    # body's local history interval. The membership guard remains explicit.
    outside=coords|{'lab2':(3,0,0,10),'own2':(Q(-135,4),0,0,Q(241,20))}
    pairs=lambda *xs:xs[:4]==tuple(vs[:4]) and xs[4:] in (('a','b'),('lab2','own2'))
    mm2=mm|{'ekvv':pairs,'zc6':record_model(c,outside)}
    assert run('ekvy',vs+[region],mm2);cases+=1
    assert run('ekv3',vs+[region]+intervals,mm2);cases+=1
    rejects(lambda:run('ekv3',vs+[region]+intervals,mm|{'ekvv':forbidden}),'Unknown body-rest');cases+=1
    return dict(cases=cases,same_inverse_region_and_nonempty_local_process=True,both_history_intervals_at_actual_coordinate_times=True,outside_local_region_not_discarded_from_coordinate_scope=True)

def scalar_oracle(sort,tag,c):
    if sort==RS:return c(tag)
    if sort=='truth':return tag<100
    if sort=='individual':return 'body' if tag<100 else 'other'
    if sort=='situation':return 'case' if tag<100 else 'other'
    return function(sort['parameters'],sort['result'],lambda *xs:scalar_oracle(sort['result'],tag,c))

def fingerprint(x,sort,cuts):
    if sort==RS:return cuts.read(x)
    if isinstance(sort,str):return x
    if sort['parameters']==['individual']:probes=[(a,) for a in ('x','y','z','body')]
    else:probes=[tuple(cuts.make(0) for _ in sort['parameters']),tuple(cuts.make(i+1) for i,_ in enumerate(sort['parameters']))]
    return tuple(fingerprint(x(*xs),sort['result'],cuts) for xs in probes)

def setup(root,fields):
    cuts,m=numbers();c=cuts.make;slots=fixture(root)[1]
    by={n:(n if t=='a' else 'case' if t=='d' else scalar_oracle(sort,i+1,c)) for i,((n,t),(_,sort)) in enumerate(zip(fields,slots))}
    by|={n:x for n,x in dict(oldframe='old',newframe='new',light=c(5),speed=c(3),oldlower=c(-2),oldupper=c(3),newlower=c(-3),newupper=c(4)).items() if n in by}
    values=[by[n] for n,t in fields];return cuts,m,values,by

def bound_rows(root,values,m,cuts):
    doc,_=fixture(root);sorts={d['name']:d['parameters'] for d in doc['declarations'] if d['kind']=='primitive'}
    expected={}
    def collect(n):
        def fn(*xs):expected.setdefault(n,set()).add(tuple(fingerprint(x,s,cuts) for x,s in zip(xs,sorts[n])));return True
        return fn
    targets=BOUNDS[root]|({'eisvi'} if root=='ekv4' else set())
    # Collect the composed routing, then independently assert the named role
    # map below; collection alone is not evidence of correct argument order.
    mm=m|{n:collect(n) for n in targets};assert run(root,values,mm)
    return expected,sorts,targets

@lru_cache(None)
def binding_checks():
    cases=0
    for root,fields in [('ekv2',MOTION),('ekv4',SETTING+CANDIDATE)]:
        cuts,m,values,by=setup(root,fields);rows,sorts,targets=bound_rows(root,values,m,cuts)
        def row(n,vals):return tuple(fingerprint(x,s,cuts) for x,s in zip(vals,sorts[n]))
        if root=='ekv2':
            for name,side in [('eiag','old'),('eiah','new')]:
                expected=[by['body'],by[side+'frame'],'case','lengthunit','timeunit',by[side+'lower'],by[side+'upper'],by['members'],*(by[side+a] for a in ('x','y','z'))]
                assert rows[name]=={row(name,expected)};cases+=1
        else:
            for name,fs in [('ekvy',LOCAL),('ekvz',FIELDS+CANDIDATE),('ekv2',MOTION),('ekv3',LOCAL+TIMES)]:assert rows[name]=={row(name,[by[n] for n,t in fs])};cases+=1
            assert rows['eisvi']=={row('eisvi',[by['body'],by['process'],by['oldframe'],by['region'],'case'])};cases+=1
        mm=m|{n:lambda *xs,n=n:row(n,xs) in rows[n] for n in targets}
        assert run(root,values,mm);cases+=1
        for i,((n,t),(_,sort)) in enumerate(zip(fields,fixture(root)[1])):
            bad=values.copy();bad[i]='other' if t in ('a','d') else scalar_oracle(sort,101+i,cuts.make)
            assert not run(root,bad,mm),(root,n);cases+=1
        for name in targets:
            assert not run(root,values,mm|{name:lambda *xs:False});cases+=1
            rejects(lambda:run(root,values,mm|{name:forbidden}),'Unknown body-rest');cases+=1
        if root=='ekv2':
            for side in ('old','new'):
                bad=by|{side+'upper':by[side+'lower']};assert not run(root,[bad[n] for n,t in fields],m|{n:lambda *xs:True for n in targets});cases+=1
            bad=by|{'newframe':by['oldframe']};assert not run(root,[bad[n] for n,t in fields],m|{n:lambda *xs:True for n in targets});cases+=1
            rejects(lambda:run(root,values,m|{'eiag':lambda *xs:True,'eiad':lambda *xs:True,'eiae':lambda *xs:False},'history'),'rational number domain');cases+=1
    return dict(cases=cases,every_body_process_frame_unit_period_and_field_role_checked=True,whole_body_motion_and_rest_not_replaced_by_markers=True,native_full_history_refused=True)

@lru_cache(None)
def physical_checks():
    cuts,m,values,by=setup('ekvz',FIELDS+CANDIDATE);c=cuts.make;cases=0
    # Independent expected rows use the actual transformed inverse region.
    newregion=run('s6m',[by['light'],by['speed'],by['region']],m)
    doc,_=fixture('ekvz');sorts={d['name']:d['parameters'] for d in doc['declarations'] if d['kind']=='primitive'}
    row=lambda name,xs:tuple(fingerprint(x,s,cuts) for x,s in zip(xs,sorts[name]))
    rows={'ejsn':set(),'eispn':set()}
    for side,region,ef,hf in [('old',by['region'],by['electricfield'],by['magneticfield']),('new',newregion,by['newelectric'],by['newmagnetic'])]:
        frame=by[side+'frame'];units=[by[n] for n in ('chargeunit','electricunit','magneticunit','forceunit')]
        rows['ejsn'].add(row('ejsn',[frame,'lengthunit','timeunit','case',region,*units,c(1),c(Q(1,5)),ef,hf]))
        rows['eispn'].add(row('eispn',[by['process'],frame,ef,hf,region,'case']))
    mm=m|{n:lambda *xs,n=n:row(n,xs) in rows[n] for n in rows}
    assert run('ekvz',values,mm);cases+=1
    for n,expected in rows.items():
        for item in expected:
            assert not run('ekvz',values,mm|{n:lambda *xs,n=n,item=item:row(n,xs) in rows[n]-{item}});cases+=1
        rejects(lambda:run('ekvz',values,mm|{n:forbidden}),'Unknown body-rest');cases+=1
    # Each explicit physical role must match both frame assignments. Numeric
    # V/v mutations are tested by native field/coordinate calculation below.
    for i,((n,t),(_,sort)) in enumerate(zip(FIELDS+CANDIDATE,fixture('ekvz')[1])):
        if n in ('light','speed'):continue
        bad=values.copy();bad[i]='other' if t in ('a','d') else scalar_oracle(sort,101+i,c)
        assert not run('ekvz',bad,mm),n;cases+=1
    return dict(cases=cases,both_physical_assignments_same_process_units_and_inverse_region=True,physical_attribution_separate_from_numeric_agreement=True)

def affine(c,r,rows):
    scalar=dict(kind='function',parameters=[RS]*4,result=RS)
    return function(['individual'],scalar,lambda role:function([RS]*4,RS,lambda *xs:c(rows[('x','y','z').index(role)][4]+sum(a*r(b) for a,b in zip(rows[('x','y','z').index(role)][:4],xs)))) if role in ('x','y','z') else function([RS]*4,RS,lambda *xs:c(0)))

@lru_cache(None)
def transformation_checks():
    cuts,m,values,by=setup('ekv6',SETTING);c,r=cuts.make,cuts.read;cases=0
    E=((1,2,3,4,5),(-2,1,0,3,-1),(3,0,-1,2,4));H=((0,1,2,-1,3),(2,-2,1,1,6),(-1,3,2,-2,1))
    by|={'electricfield':affine(c,r,E),'magneticfield':affine(c,r,H)};values=[by[n] for n,t in SETTING]
    sorts=next(d for d in fixture('ekv6')[0]['declarations'] if d['name']=='ekv4')['parameters']
    fixed=tuple(fingerprint(x,s,cuts) for x,s in zip(values,sorts));probes=((0,0,0,0),(1,2,-1,1),(-2,1,3,2))
    def expected(point,speed):
        x,y,z,t=map(Q,point);old=(Q(5,4)*(x+speed*t),y,z,Q(5,4)*(t+speed*x/25))
        e=[row[4]+sum(a*b for a,b in zip(row[:4],old)) for row in E];h=[row[4]+sum(a*b for a,b in zip(row[:4],old)) for row in H];ratio=Q(speed,5);g=Q(5,4)
        return ((e[0],g*(e[1]-ratio*h[2]),g*(e[2]+ratio*h[1])),(h[0],g*(h[1]+ratio*e[2]),g*(h[2]-ratio*e[1])))
    for speed in (-3,3):
        by['speed']=c(speed);values=[by[n] for n,t in SETTING];fixed=tuple(fingerprint(x,s,cuts) for x,s in zip(values,sorts))
        def gate(*xs):
            return tuple(fingerprint(x,s,cuts) for x,s in zip(xs[:-2],sorts))==fixed and all(r(xs[-2+side](axis)(*map(c,p)))==expected(p,speed)[side][j] for p in probes for side in (0,1) for j,axis in enumerate(('x','y','z')))
        assert run('ekv6',values,m|{'ekv4':gate});cases+=1
        assert not run('ekv6',values,m|{'ekv4':lambda *xs:False});cases+=1
        for side in (0,1):
            for axis in ('x','y','z'):
                symbol=('s6k','s6l')[side];actual=run(symbol,[c(5),c(speed),by['electricfield'],by['magneticfield']],m)
                damaged=function(actual.parameters,actual.result,lambda role,actual=actual,axis=axis:function([RS]*4,RS,lambda *xs:c(r(actual(role)(*xs))+(1 if role==axis else 0))))
                doc,slots=fixture('ekv6');doc=deepcopy(doc);abstract(doc,{symbol});doc=extract_document(doc,roots=['ekv6',*[n for n,s in slots]],statement_indices=[0]).document
                mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|m|{'ekv4':gate,symbol:lambda *xs,damaged=damaged:damaged}|{n:lambda x=x:x for (n,s),x in zip(slots,values)}
                result=evaluate_document(doc,individuals=DOMAIN,situations=('case','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=700000)[0]['value']
                assert not result;cases+=1
        rejects(lambda:run('ekv6',values,m|{'ekv4':forbidden}),'Unknown body-rest');cases+=1
    return dict(cases=cases,native_two_field_question_and_actual_transformed_answers=True,all_six_components_signs_and_inverse_coordinates_checked=True,not_limited_to_plane_waves=True)

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert len(new.document['statements'])==406 and new.document['statements']==old.document['statements']
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    assert selection_binding(new,[404,405])==selection_binding(old,[404,405])
    load_annotations(ROOT,BASIS,ANNOTATIONS);assert json.loads(read(ANNOTATIONS))['entries']==json.loads(read('data/problem-series-reduction-identifiers-v1.json'))['entries']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    assert not {'ekbw','ekbx','ekby','ekbz'}&{d['name'] for d in core()['declarations']}
    for style in ('compact','full'):
        text=format_graph(core(),style);assert parse(text)==parse(transcribe(text,alphabet='v2'))==core()
    return dict(new_definitions=len(MEANINGS),new_general_relations=len(PRIMITIVES),all_406_previous_statements_and_meanings_preserved=True,no_additional_source_unit_judged=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('events',event_checks),('regions',region_checks),('bindings',binding_checks),('physical',physical_checks),('transformation',transformation_checks),('structure',structure_checks)]}
    helpers=('compose_limits','compose_material_relative_frame','compose_material_body_motion','compose_field_equations','check_coordinate_correspondence','check_material_relative_frame','check_tau_differential','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|{DOC,*DEPENDENCIES,'scripts/compose_body_rest_field_method.py','scripts/check_body_rest_field_method.py','tests/test_body_rest_field_method.py',*(f'scripts/{n}.py' for n in helpers)}
    return dict(status='same_body_rest_frame_and_two_physical_field_answers_checked',document=FULL,**results,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
