"""Check physical regional charge and all-carrier velocity without finite proofs."""
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
from scripts.check_body_rest_field_method import numbers,point
from scripts.check_material_relative_frame import NUM,RS
from scripts.check_problem_series_reduction import collapse
from scripts.compose_convective_charge_setting import *

DOC='docs/convective-charge-setting-v1.md';SOURCE='data/einstein-convective-charge-obligations-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';FACSIMILE='artifacts/written-facsimiles-v1/einstein-p916-0.jpg'
DEPENDENCIES=('reports/convection-fields-v1.json','reports/local-density-v1.json','reports/additive-charge-v1.json','reports/material-velocity-v1.json','reports/vacuum-field-domain-v1.json')
CONSTANTS={'yn':'x','yo':'y','yp':'z','zc7':'t','zor':'electriccharge'}
PEOPLE=tuple(dict.fromkeys([*CONSTANTS.values(),*[n for n,t in COUPLED+VELOCITY if t=='a'],'a','b','other']))
BOUNDS={'ekxe':{'ejsl','seow','seor'},'ekxf':{'ekxe','sedi','seoj','sedm'},'ekxg':{'ekxf','sedi'},'ekxh':{'ejsl','seob','seoa'},'ekxi':{'ekxh','seoc'},'ekxj':{'ejsn','ekxg','semh'},'ekxl':{'ekxi'},'ekxm':{'ejsn','ekxk','ekxl'},'jccw':{'ekxj'}}
AXES=('x','y','z','t');PTS=((1,2,3,4),(5,6,7,8))
def forbidden(*xs):raise ValueError('Unknown convective charge input')
def reject(fn,unknown=False):
    try:fn()
    except ValueError as e:assert ('Unknown convective charge input' in str(e)) if unknown else any(x in str(e) for x in ('rational number domain','Finite function domain')),str(e)
    else:raise AssertionError('Unbounded or unknown input was accepted')
def fn(sort,body):return FunctionValue(tuple(sort['parameters']),sort['result'],body)
def sort(text):return parse('n:r jcc[] '+text+'.')['declarations'][0]['result']
PS=sort(POINT);BS=sort(BALL)

@lru_cache(None)
def core():return parse(read(CORE))
def replace_var(node,name,term):
    if isinstance(node,list):return [replace_var(x,name,term) for x in node]
    if not isinstance(node,dict):return node
    if node.get('kind')=='variable' and node['name']==name:return deepcopy(term)
    return {k:replace_var(v,name,term) for k,v in node.items()}

@lru_cache(None)
def fixture(root,mode='sample'):
    doc=deepcopy(core())
    if root=='jccw':
        original=next(d for d in doc['declarations'] if d['name']=='ekxm')
        def find(node):
            if isinstance(node,list):
                for child in node:
                    result=find(child)
                    if result is not None:return result
            elif isinstance(node,dict):
                if node.get('kind')=='exists' and node.get('sort')=='individual':return node
                for child in node.values():
                    result=find(child)
                    if result is not None:return result
        body=find(original['body']);assert body is not None
        leaf=body
        for n,t in WITNESSES:assert leaf['kind']=='exists' and leaf['sort']==sort(t);leaf=leaf['body']
        assert leaf['symbol']=='ekxj'
        pointarg=leaf['arguments'][len(SETTING)];assert pointarg['kind']=='variable'
        doc['declarations'].append(dict(kind='definition',name='jccw',parameters=deepcopy(original['parameters'])+[dict(name=pointarg['name'],sort=PS)],result='truth',body=deepcopy(body)))
    for i,d in enumerate(doc['declarations']):
        if d['kind']=='definition' and d['name'] in (NUM|{'bg','be','bj','sje'}|BOUNDS.get(root,set())):
            doc['declarations'][i]=dict(kind='primitive',name=d['name'],parameters=[p['sort'] for p in d['parameters']],result=d['result'])
    doc=extract_document(doc,roots=[root],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==root)
    if mode.startswith('slot:'):
        doc=collapse(doc);d=next(d for d in doc['declarations'] if d['name']==root)
        pivot=int(mode.split(':')[1]);body=d['body'];kept=None
        for i in range(len(WITNESSES)):
            assert body['kind']=='exists'
            if i==pivot:kept={k:body[k] for k in ('kind','variable','sort')}
            else:d['parameters'].append(dict(name=body['variable'],sort=body['sort']))
            body=body['body']
        d['body']=kept|dict(body=body)
    elif mode=='sample':
        def sample(node):
            if isinstance(node,list):return [sample(x) for x in node]
            if not isinstance(node,dict):return node
            if node.get('kind') in ('forall','exists'):
                samples=next((names for s,names in ((RS,('jccra','jccrb')),(PS,('jccpa','jccpb')),(BS,('jccba','jccbb')),(sort(DOMAIN),('jccda','jccdb')),(sort(CURVE),('jccca','jcccb'))) if s==node['sort']),None)
                if samples:
                    return dict(kind='and' if node['kind']=='forall' else 'or',arguments=[sample(replace_var(node['body'],node['variable'],dict(kind='call',symbol=n,arguments=[]))) for n in samples])
            return {k:sample(v) for k,v in node.items()}
        # The point variable is already substituted before the witness chain.
        # Capture its term from ekxj instead of assuming the alpha-normalized name.
        if root=='ekxm':
            def witness(node):
                if isinstance(node,list):return [witness(x) for x in node]
                if not isinstance(node,dict):return node
                if node.get('kind')=='exists' and node.get('sort')=='individual':
                    chain=node
                    for n,t in WITNESSES:assert chain['kind']=='exists';chain=chain['body']
                    assert chain['symbol']=='ekxj'
                    return dict(kind='call',symbol='jccwitness',arguments=chain['arguments'][:len(SETTING)+1])
                return {k:witness(v) for k,v in node.items()}
            d['body']=witness(d['body'])
            doc['declarations'].append(dict(kind='primitive',name='jccwitness',parameters=[p['sort'] for p in d['parameters']]+[PS],result='truth'))
        d['body']=sample(d['body'])
    extras={'jccra':RS,'jccrb':RS,'jccpa':PS,'jccpb':PS,'jccba':BS,'jccbb':BS,'jccda':sort(DOMAIN),'jccdb':sort(DOMAIN),'jccca':sort(CURVE),'jcccb':sort(CURVE)}
    if not mode.startswith('slot:'):doc['declarations'] += [dict(kind='primitive',name=n,parameters=[],result=s) for n,s in extras.items()]
    slots=[]
    for i,p in enumerate(d['parameters']):
        n='jccarg'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    doc['statements']=[dict(kind='ask',body=dict(kind='call',symbol=root,arguments=[dict(kind='call',symbol=n,arguments=[]) for n in slots]))]
    doc['declarations'].sort(key=lambda d:d['kind']!='primitive')
    return doc,slots

def run(root,vs,m,mode='sample',domain=PEOPLE):
    doc,slots=fixture(root,mode);assert len(vs)==len(slots),(root,len(vs),len(slots))
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|m|{n:lambda x=x:x for n,x in zip(slots,vs)}
    return evaluate_document(doc,individuals=domain,situations=('case','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=600000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def setup():
    cuts,m=numbers();c,r=cuts.make,cuts.read
    def field(values):return fn(sort(FIELD),lambda a:fn(sort(TAU),lambda *xs:c(values[AXES.index(a)] if a in AXES[:3] else 0)))
    by={n:n for n,t in COUPLED+VELOCITY if t=='a'}|{'context':'case'}
    by|={n:c(x) for n,x in dict(light=5,pi=3,upper=3,density=2,normalized=24,electricconversion=1,magneticconversion=Q(1,5)).items()}
    points=[point(c,p) for p in PTS]
    by|={'point':points[0],'electricfield':field((1,2,3)),'magneticfield':field((4,5,6)),'velocityfield':field((1,-2,3)),
         'region':fn(sort(REGION),lambda *xs:tuple(map(r,xs)) in PTS),'densityfield':fn(sort(TAU),lambda *xs:c(24)),
         'chargefield':fn(sort(TAU),lambda *xs:c(2)),'velocity':point(c,(1,-2,3,0)),
         'electricjet':fn(sort(JET),lambda a,b:c(1)),'magneticjet':fn(sort(JET),lambda a,b:c(2)),
         'sets':fn(sort(SETS),lambda region:True),'total':fn(sort(TOTAL),lambda region:c(8)),
         'charge':fn(sort(PROFILE),lambda radius:c(8*r(radius)**3)),
         'volume':fn(sort(PROFILE),lambda radius:c(4*r(radius)**3)),
         'average':fn(sort(PROFILE),lambda radius:c(2)),
         'domain':fn(sort(DOMAIN),lambda time:0<r(time)<3),
         'curve':fn(sort(CURVE),lambda time:point(c,(r(time),2*r(time),3*r(time),r(time))))}
    balls=[fn(BS,lambda p:False),fn(BS,lambda p:True)]
    m|={'jccpa':lambda:points[0],'jccpb':lambda:points[1],'jccra':lambda:c(1),'jccrb':lambda:c(2),
        'jccba':lambda:balls[0],'jccbb':lambda:balls[1],'jccda':lambda:by['domain'],'jccdb':lambda:by['domain'],
        'jccca':lambda:by['curve'],'jcccb':lambda:by['curve']}
    def key(x):
        if isinstance(x,(tuple,list)):return tuple(key(y) for y in x)
        if not isinstance(x,FunctionValue):return x
        if x.parameters==('number',):return r(x)
        if x.parameters==('individual',) and x.result==RS:return tuple(r(x(a)) for a in AXES)
        if x.parameters==(PS,) and x.result=='truth':return tuple(x(p) for p in points)
        while isinstance(x,FunctionValue):
            f=x.implementation;code=getattr(f,'__code__',None)
            if code is None:return f
            closed=dict(zip(code.co_freevars,(cell.cell_contents for cell in (getattr(f,'__closure__',None) or ()))))
            if 'raw' not in closed:return f
            x=closed['raw']
        return x
    def relation(rows):return lambda *xs:key(xs) in rows
    return by,m,c,r,key,relation,points,balls

def contrasts(root,vs,m,rows,key):
    relation=lambda rs:lambda *xs:key(xs) in rs
    m=m|{n:relation(rs) for n,rs in rows.items()};assert run(root,vs,m);cases=1
    for n,rs in rows.items():
        for row in rs:
            assert not run(root,vs,m|{n:relation(rs-{row})}),(root,n);cases+=1
            for i,x in enumerate(row):
                wrong=list(row);wrong[i]='other' if isinstance(x,str) else 'wrong'
                assert not run(root,vs,m|{n:relation((rs-{row})|{tuple(wrong)})}),(root,n,i);cases+=1
        reject(lambda:run(root,vs,m|{n:forbidden}),True);cases+=1
    return cases

@lru_cache(None)
def local_checks():
    by,m,c,r,key,rel,points,balls=setup();cases=0
    values=lambda fs:[by[n] for n,t in fs]
    rows={'ejsn':{key(values(FIELD_SETTING))},'ekxg':{key([by[n] if n not in ('density','normalized') else c(2 if n=='density' else 24) for n,t in NORMAL])},
          'semh':{key([by[n] for n in ('electricfield','magneticfield','region','point','light')]+[c(24),by['velocity'],by['electricjet'],by['magneticjet']])}}
    cases+=contrasts('ekxj',values(COUPLED),m,rows,key)
    rows={'ekxh':{key(values(TRACK))},'seoc':{key(values(TRACK[:5])+[by['event'],by['point'],c(1),c(-2),c(3)])},
          'eisqd':{key([by[n] for n in ('matter','frame','event','lengthunit','timeunit','point','context')])}}
    member=lambda *xs:xs==('matter','distribution','case')
    mm=m|{'zqn':lambda:fn(sort('h[a a d] c'),member)}
    cases+=contrasts('ekxi',values(VELOCITY),mm,rows,key)
    assert not run('ekxi',values(VELOCITY),mm|{n:rel(rs) for n,rs in rows.items()}|{'zqn':lambda:fn(sort('h[a a d] c'),lambda *xs:False)});cases+=1
    for rho in (-2,0,2):
        base=values(NORMAL);base[-2:]=[c(rho),c(12*rho)]
        mm=m|{'ekxf':lambda *xs:True,'sedi':lambda pi:r(pi)==3}
        assert run('ekxg',base,mm);cases+=1
        bad=base.copy();bad[-1]=c(12*rho+1);assert not run('ekxg',bad,mm);cases+=1
    return dict(cases=cases,same_charge_units_point_fields_and_all_velocity_components=True,native_signed_four_pi_normalization=True)

@lru_cache(None)
def amount_checks():
    by,m,c,r,key,rel,points,balls=setup();vs=[by[n] for n,t in REGIONAL_TOTAL];cases=0
    # All selected regions, including a zero-valued empty region, carry the
    # physical kind/frame/event/time/units. Additivity is a prior checked boundary.
    by['total']=fn(sort(TOTAL),lambda region:c(0 if not region(points[0]) else -3));vs=[by[n] for n,t in REGIONAL_TOTAL]
    rows={'eisvx':{key(['distribution','electriccharge','frame','event',c(4),b,'lengthunit','timeunit','chargeunit',by['total'](b),'case']) for b in balls}}
    mm=m|{'ejsl':lambda *xs:True,'seow':lambda *xs:True,'seor':lambda *xs:True}
    cases+=contrasts('ekxe',vs,mm,rows,key)
    reject(lambda:run('ekxe',vs,mm|{'eisvx':lambda *xs:True},'native'));cases+=1
    # Native spatial balls are sampled only to distinguish which region the
    # same total receives; the radius quantifier itself is two explicit probes.
    center=PTS[0]
    def volume_total(ball):
        # Radius 1 excludes distance 1; radius 2 includes it.
        edge=point(c,(center[0]+1,*center[1:]));return c(64 if ball(edge) else 8)
    by['total']=fn(sort(TOTAL),volume_total)
    vs=[by[n] for n,t in LOCAL]
    mm=m|{'ekxe':lambda *xs:True,'sedi':lambda pi:r(pi)==3,'seoj':lambda *xs:True,
          'sedm':lambda radius,pi,vol:r(pi)==3 and r(vol)==4*r(radius)**3}
    assert run('ekxf',vs,mm);cases+=1
    for name in ('sets','total','charge','volume'):
        changed=by.copy()
        if name=='sets':changed[name]=fn(sort(SETS),lambda ball:False)
        elif name=='total':changed[name]=fn(sort(TOTAL),lambda ball:c(9))
        else:changed[name]=fn(sort(PROFILE),lambda radius:c(9))
        assert not run('ekxf',[changed[n] for n,t in LOCAL],mm),name;cases+=1
    for name in ('ekxe','sedi','seoj','sedm'):reject(lambda:run('ekxf',vs,mm|{name:forbidden}),True);cases+=1
    reject(lambda:run('ekxf',vs,mm,'native'));cases+=1
    return dict(cases=cases,all_regional_totals_have_physical_charge_kind_and_same_time_units=True,ball_total_and_volume_profiles_connected=True,full_region_and_radius_domains_refused=True)

@lru_cache(None)
def carrier_checks():
    by,m,c,r,key,rel,points,balls=setup();cases=0
    member=fn(sort('h[a a d] c'),lambda matter,dist,ctx:matter in ('a','b') and (dist,ctx)==('distribution','case'))
    positions={key([a,'frame','event',by['point'],'case']) for a in ('a','b')}
    units={key([a,'frame','event','lengthunit','timeunit',by['point'],'case']) for a in ('a','b')}
    mm=m|{'zqn':lambda:member,'zpb':rel(positions),'eisqd':rel(units)}
    for rho in (-1,0,1):
        vs=[by[n] if n!='normalized' else c(rho) for n,t in SUPPORT]
        assert run('ekxk',vs,mm);cases+=1
        assert run('ekxk',vs,mm|{'zpb':lambda *xs:False})==(rho==0);cases+=1
    rows={'ejsl':{key([by[n] for n,t in CHART])},'seob':{key([by[n] for n,t in TRACK[:5]])}}
    events={1:'a',2:'b'}
    for time,event in events.items():
        rows.setdefault('seoa',set()).add(key([by[n] for n,t in TRACK[:5]]+[event,c(time)]))
        rows.setdefault('eisqd',set()).add(key(['matter','frame',event,'lengthunit','timeunit',by['curve'](c(time)),'case']))
    cases+=contrasts('ekxh',[by[n] for n,t in TRACK],m,rows,key)
    reject(lambda:run('ekxh',[by[n] for n,t in TRACK],m|{n:rel(rs) for n,rs in rows.items()},'native'));cases+=1
    # Every carrier, not merely one representative, must receive the same
    # Eulerian velocity at its own point. Function witnesses are explicit probes.
    velocity=by['velocity'];rows={'ekxi':set()}
    for a in ('a','b'):
        vals=by|{'matter':a};rows['ekxi'].add(key([vals[n] for n,t in VELOCITY]))
    vs=[by[n] for n,t in FLOW]
    cases+=contrasts('ekxl',vs,mm,rows,key)
    return dict(cases=cases,zero_density_does_not_require_carriers_or_zero_velocity=True,all_carriers_and_entire_charted_history_checked=True,history_and_function_samples_are_diagnostic_only=True)

@lru_cache(None)
def regional_checks():
    cases=0
    # Test each existential slot separately with two distinguishing values.
    for pivot,(name,t) in enumerate(WITNESSES):
        fixed={n:'a' if i%2==0 else 'b' for i,(n,t) in enumerate(SETTING+[('point',POINT)]+WITNESSES)}
        vs=[fixed[n] for n,t in SETTING+[('point',POINT)]]+[fixed[n] for i,(n,t) in enumerate(WITNESSES) if i!=pivot]
        # Situation slots stay situations when functional sorts collapse.
        fixed['context']='case';vs[3]='case'
        for target in ('a','b','missing'):
            row=tuple((fixed|{name:target})[n] for n,t in COUPLED)
            assert run('jccw',vs,{'ekxj':lambda *xs,row=row:xs==row},f'slot:{pivot}',('a','b'))==(target!='missing');cases+=1
        reject(lambda:run('jccw',vs,{'ekxj':forbidden},f'slot:{pivot}',('a','b')),True);cases+=1
    by,m,c,r,key,rel,points,balls=setup();vs=[by[n] for n,t in SETTING]
    rows={'ejsn':{key([by[n] for n,t in FIELD_SETTING])},'ekxl':{key([by[n] for n,t in FLOW])},
          'jccwitness':{key(vs+[p]) for p in points},
          'ekxk':{key([by[n] if n not in ('point','normalized') else p if n=='point' else c(24) for n,t in SUPPORT]) for p in points}}
    cases+=contrasts('ekxm',vs,m,rows,key)
    empty=vs.copy();empty[4]=fn(sort(REGION),lambda *xs:False)
    assert not run('ekxm',empty,m|{n:lambda *xs:True for n in rows});cases+=1
    reject(lambda:run('jccw',vs+[points[0]],m|{'ekxj':lambda *xs:True},'native'));cases+=1
    return dict(cases=cases,all_nine_shared_witness_positions_checked=True,nonempty_region_all_points_and_all_carriers=True,native_unbounded_witness_domain_refused=True)

@lru_cache(None)
def source_record():
    units=json.loads(read(INVENTORY))['units'][226:232]
    for u in units:assert digest(u['text'].encode())==u['text_sha256']
    return dict(version='einstein-convective-charge-obligations-v1',kind='dependency_scope_not_semantic_review',units=[dict(unit=u['id'],unit_sha256=u['text_sha256'],text=u['text']) for u in units],resolved_dependencies=list(MEANINGS),observations=['原刊916頁でM0383の電気側にρu、磁気側に1/V、M0384に電気側の三対角偏微分の和を確認した。','ρの説明は4π倍であり、速度は同じ電気量の三成分である。後続M0389の磁気側に1/Vがない印刷を保存する。'],unresolved=['小さい剛体とイオン・電子という担体の読み','電荷が同じ担体へ不変に結び付く仮定','Lorentzの電気力学と動く物体の光学の電磁的基礎という位置付け','著者の出発点、where説明、原系の指示と見出しの本文接続'],whole_unit_reviewed=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in (INVENTORY,FACSIMILE,DOC)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert len(new.document['statements'])==408 and new.document['statements']==old.document['statements']
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    assert selection_binding(new,[407])==selection_binding(old,[407])
    load_annotations(ROOT,BASIS,ANNOTATIONS)
    assert json.loads(read(ANNOTATIONS))['entries']==json.loads(read('data/eighth-section-heading-identifiers-v1.json'))['entries']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    names={d['name'] for d in core()['declarations']}
    assert set(MEANINGS)|{'eisvx','ejsn','eirm','eiru','seor','seow','seoj','seml','seoc','eisqd','semh','semg','seme','semd','zqn'}<=names
    assert not names&{'ejso','ejsk','semf','semi','semk','ekbw','ekbx','ekby','ekbz'}
    for style in ('compact','full'):
        body=format_graph(core(),style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core()
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=9,new_general_physical_relations=1,all_408_assertions_and_meanings_preserved=True,no_vacuum_or_printed_transformed_equations_added=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('local',local_checks),('amount',amount_checks),('carriers',carrier_checks),('regional',regional_checks),('structure',structure_checks)]}
    helpers=('compose_limits','compose_material_relative_frame','compose_field_equations','compose_local_density','compose_additive_charge','compose_material_velocity','compose_vacuum_field_domain','compose_doppler_infinity','check_body_rest_field_method','check_material_relative_frame','check_problem_series_reduction','check_tau_differential','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,*DEPENDENCIES,'scripts/compose_convective_charge_setting.py','scripts/check_convective_charge_setting.py','tests/test_convective_charge_setting.py',*(f'scripts/{n}.py' for n in helpers)}
    return dict(status='physical_convective_charge_setting_connected',document=FULL,**results,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
