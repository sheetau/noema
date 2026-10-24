"""Check physical identity, coherent units, actual acceleration and the rest-law condition."""
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
from scripts import check_attached_material_charge as old
from scripts import check_material_acceleration as analytic
from scripts.check_ninth_section_opening import lifted
from scripts.check_problem_series_reduction import collapse
from scripts.check_convective_foundation_reading import walk
from scripts.compose_point_particle_dynamics import *

DOC='docs/point-particle-dynamics-v1.md';SOURCE='data/einstein-point-particle-dynamics-obligations-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';FACSIMILE='artifacts/written-facsimiles-v1/einstein-p917-0.jpg'
DEPENDENCIES=('reports/material-acceleration-v1.json','reports/resting-charge-force-v1.json','reports/vacuum-field-domain-v1.json','reports/point-charge-calibration-v1.json')
CONSTANTS={'yn':'x','yo':'y','yp':'z','zc7':'t','ra':'frame','zor':'electriccharge'}
PEOPLE=tuple(dict.fromkeys([*CONSTANTS.values(),*[n for n,t in SETTING if t=='a'],'eventa','eventb','eventc','other','a','b']))
POINTS=('case','other');TIMES=(-1,0,1);TS=tuple('jpdt'+number_word(i) for i in range(3))
BOUNDS={'ek3p':{'ejsl','seob','seoa'},'ek3q':{'ek3p','sepp'},'ek3v':{'ejsn','ek3n','ek3o','ek3q','ek3u'},'ek3w':{'ek3r','ek3t'},'ek3x':{'ek3v','ek3w'}}
FIELDS_BY={'ek3n':UNITS,'ek3o':MASS,'ek3p':HISTORY,'ek3q':KINEMATIC,'ek3r':REST,'ek3s':SCALAR,'ek3t':VECTOR,'ek3u':CHARGE,'ek3v':SETTING,'ek3w':SETTING}
fn=old.fn;sort=old.sort;forbidden=old.forbidden

@lru_cache(None)
def core():return parse(read(CORE))

@lru_cache(None)
def boundary(root):
    doc=extract_document(core(),roots=[root],statement_indices=[]).document
    for i,d in enumerate(doc['declarations']):
        if d['kind']=='definition' and d['name'] in old.NUM|{'bg','bj','szi'}|BOUNDS.get(root,set()):doc['declarations'][i]=dict(kind='primitive',name=d['name'],parameters=[p['sort'] for p in d['parameters']],result=d['result'])
    return extract_document(doc,roots=[root],statement_indices=[]).document

@lru_cache(None)
def fixture(root,mode='sample'):
    doc=deepcopy(boundary(root));d=next(d for d in doc['declarations'] if d['name']==root)
    if root=='ek3p' and mode=='sample':
        def sample(node):
            if isinstance(node,list):return [sample(x) for x in node]
            if not isinstance(node,dict):return node
            if node.get('kind')=='forall' and node['sort']==old.RS:
                probes=[sample(old.replace(node['body'],node['variable'],dict(kind='call',symbol=n,arguments=[]))) for n in TS];body=probes[-1]
                for p in reversed(probes[:-1]):body=dict(kind='and',arguments=[p,body])
                return body
            return {k:sample(x) for k,x in node.items()}
        d['body']=sample(d['body'])
    doc['declarations'] += [dict(kind='primitive',name=n,parameters=[],result=old.RS) for n in TS]
    slots=[]
    for i,p in enumerate(d['parameters']):
        n='jpdarg'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=root,arguments=[dict(kind='call',symbol=n,arguments=[]) for n in slots])
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jpdpoint',parameters=[],result='situation'));expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='jpdpoint',arguments=[]))
    doc['declarations'].sort(key=lambda d:d['kind']!='primitive');doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(root,values,m,mode='sample'):
    doc,slots=fixture(root,mode);assert len(values)==len(slots)
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|{'jpdpoint':lambda:'case'}|m|{n:lambda x=x:x for n,x in zip(slots,values)}
    return evaluate_document(doc,individuals=PEOPLE,situations=POINTS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=500000,memoize_definitions=True,memoize_expressions=True)[0]['value']

@lru_cache(None)
def setup():
    cuts,m=old.numbers();c,r=cuts.make,cuts.read
    by={n:('case' if t=='d' else n) for n,t in SETTING if t in ('a','d')}
    by.update(lengthscale=Q(1),timescale=Q(1),massscale=Q(1),forcescale=Q(1),chargescale=Q(1),mass=c(2),charge=c(-3),electricconversion=c(1),magneticconversion=c(1))
    by['domain']=fn(sort(DOMAIN),lambda t:abs(r(t))<2)
    by['curve']=fn(sort(CURVE),lambda t:old.point(c,(1+r(t)**2,2-2*r(t)**2,3+3*r(t)**2,r(t))))
    by['point']=by['curve'](c(0))
    for (n,t),a in zip(PROFILES,(2,-4,6)):by[n]=fn(sort(t),lambda time,a=a:c(a*r(time)))
    for (n,t),a in zip(ACCEL,(2,-4,6)):by[n]=c(a)
    by['region']=fn(sort(REGION),lambda *xs:True)
    # Nonconstant field: using a different point must change the result.
    by['electricfield']=fn(sort(FIELD),lambda axis:fn(sort('h['+' '.join([R]*4)+'] '+R),lambda x,y,z,t:c({'x':Q(-4,3)*r(x),'y':Q(4,3)*r(y),'z':Q(-4,3)*r(z)}.get(axis,0))))
    by['magneticfield']=fn(sort(FIELD),lambda axis:fn(sort('h['+' '.join([R]*4)+'] '+R),lambda *xs:c(7)))
    m|={'aa':lambda a,b:a<b,'ad':lambda a,b:a*b}|{n:lambda t=t:c(t) for n,t in zip(TS,TIMES)}
    def key(x):
        if isinstance(x,(list,tuple)):return tuple(key(y) for y in x)
        if not isinstance(x,FunctionValue):return x
        if x.parameters==('number',):return r(x)
        if x.parameters==('individual',) and x.result==old.PS:return tuple(key(x(a)) for a in ('x','y','z'))
        if x.parameters==('individual',) and x.result==old.RS:return tuple(r(x(a)) for a in ('x','y','z','t'))
        if x.parameters==(old.RS,) and x.result==old.PS:return tuple(key(x(c(t))) for t in TIMES)
        if x.parameters==(old.RS,) and x.result==old.RS:return tuple(r(x(c(t))) for t in TIMES)
        if x.parameters==(old.RS,) and x.result=='truth':return tuple(x(c(t)) for t in TIMES)
        if x.parameters==(old.RS,)*4 and x.result=='truth':return tuple(x(c(t),c(t),c(t),c(t)) for t in TIMES)
        if x.parameters==('individual',) and isinstance(x.result,dict):return tuple(tuple(r(x(a)(*(c(t) for i in range(4)))) for t in TIMES) for a in ('x','y','z'))
        raise AssertionError(('Unexpected function',x.parameters,x.result))
    return by,m,c,r,key

def vals(root,by):return [by[n] for n,t in FIELDS_BY[root]]

def contrasts(root,by,m,rows,key):
    rel=lambda rs:lambda *xs:key(xs) in rs
    good=m|{n:rel(rs) for n,rs in rows.items()};assert run(root,vals(root,by),good),root;count=1
    for n,rs in rows.items():
        for row in rs:
            assert not run(root,vals(root,by),good|{n:rel(rs-{row})}),(root,n);count+=1
            for i in range(len(row)):
                wrong=list(row);wrong[i]='wrong'
                assert not run(root,vals(root,by),good|{n:rel((rs-{row})|{tuple(wrong)})}),(root,n,i);count+=1
        old.reject(lambda:run(root,vals(root,by),good|{n:forbidden}),unknown=True);count+=1
    return count

@lru_cache(None)
def numeric_checks():
    by,m,c,r,key=setup();cases=0
    for mass,charge,a,e,want in [(2,-3,2,Q(-4,3),True),(2,3,2,Q(4,3),True),(2,0,0,7,True),(2,0,1,7,False),(0,3,0,0,False),(-2,3,-2,Q(4,3),False),(2,-3,-4,Q(8,3),True),(2,-3,2,Q(4,3),False)]:
        assert run('ek3s',list(map(c,(mass,charge,a,e))),m)==want;cases+=1
    assert run('ek3t',vals('ek3t',by),m);cases+=1
    for n,t in ACCEL:
        assert not run('ek3t',vals('ek3t',by|{n:c(r(by[n])+1)}),m);cases+=1
    assert not run('ek3t',vals('ek3t',by|{'point':old.point(c,(2,2,3,0))}),m);cases+=1
    assert not run('ek3t',vals('ek3t',by),m|{'yo':lambda:'x'});cases+=1
    assert run('ek3r',vals('ek3r',by),m);cases+=1
    for n,t in PROFILES:
        assert not run('ek3r',vals('ek3r',by|{n:fn(sort(t),lambda time:c(1))}),m);cases+=1
    # Unit relation is native rational arithmetic with actual dimension assignments.
    for scales in ((1,1,1,1),(Q(1,100),1,Q(1,1000),Q(1,100000)),(2,3,5,Q(10,9))):
        b=by|dict(zip(('lengthscale','timescale','massscale','forcescale'),map(Q,scales)))
        rows={(b[u],Q(l),Q(ms),Q(t),b[s],'case') for u,l,ms,t,s in [('lengthunit',1,0,0,'lengthscale'),('timeunit',0,0,1,'timescale'),('massunit',0,1,0,'massscale'),('forceunit',1,1,-2,'forcescale')]}
        mm=m|{'eisqb':lambda *xs:xs in rows}
        assert run('ek3n',vals('ek3n',b),mm);cases+=1
        for row in rows:
            assert not run('ek3n',vals('ek3n',b),m|{'eisqb':lambda *xs:xs in rows-{row}});cases+=1
        assert not run('ek3n',vals('ek3n',b|{'forcescale':b['forcescale']*2}),m|{'eisqb':lambda *xs:True});cases+=1
    for n in ('lengthscale','timescale','massscale','forcescale'):
        assert not run('ek3n',vals('ek3n',by|{n:Q(0)}),m|{'eisqb':lambda *xs:True});cases+=1
    return dict(cases=cases,signed_and_zero_charge_numeric_law=True,all_three_local_field_components=True,instantaneous_rest_allows_nonzero_acceleration=True,three_coherent_scale_choices_and_incoherent_rejection=True)

@lru_cache(None)
def physical_checks():
    by,m,c,r,key=setup();cases=0
    rows={'eisww':{key(vals('ek3o',by))}}
    cases+=contrasts('ek3o',by,m,rows,key)
    for mass in (0,-1):assert not run('ek3o',vals('ek3o',by|{'mass':c(mass)}),m|{'eisww':lambda *xs:True});cases+=1
    rows={'eisqc':{('matter','case')},'zof':{('chargeunit','electriccharge',Q(1),'case')},'zog':{key(['chargerecord','matter','electriccharge','frame','event','chargeunit',by['charge'],'case'])}}
    cases+=contrasts('ek3u',by,m,rows,key)
    assert not run('ek3u',vals('ek3u',by|{'charge':c(0)}),m|{n:lambda *xs:True for n in rows});cases+=1
    fields={'ejsn':FIELDS,'ek3n':UNITS,'ek3o':MASS,'ek3q':KINEMATIC,'ek3u':CHARGE}
    rows={n:{key([by[x] for x,t in fs])} for n,fs in fields.items()}
    cases+=contrasts('ek3v',by,m,rows,key)
    assert not run('ek3v',vals('ek3v',by|{'electricconversion':c(2)}),m|{n:lambda *xs:True for n in fields});cases+=1
    rows={'ek3p':{key([by[n] for n,t in HISTORY])},'sepp':{key([by[n] for n,t in AT])}}
    cases+=contrasts('ek3q',by,m,rows,key)
    for rest,law in product((False,True),repeat=2):
        assert run('ek3w',vals('ek3w',by),m|{'ek3r':lambda *xs:rest,'ek3t':lambda *xs:law})==((not rest) or law);cases+=1
    return dict(cases=cases,same_particle_event_units_fields_and_trajectory=True,physical_mass_and_charge_not_arbitrary_numbers=True,rest_condition_does_not_assume_equation=True)

@lru_cache(None)
def history_checks():
    by,m,c,r,key=setup();events=('eventa','eventb','eventc')
    rows={'ejsl':{key([by[n] for n,t in CHART])},'seob':{key([by[n] for n,t in TRACK])},'seoa':{key([by[n] for n,t in TRACK]+[e,c(t)]) for e,t in zip(events,TIMES)},'eisqd':{key(['matter','frame',e,'lengthunit','timeunit',by['curve'](c(t)),'case']) for e,t in zip(events,TIMES)}}
    relation=lambda rs:lambda *xs:key(xs) in rs
    good=m|{n:relation(rs) for n,rs in rows.items()};assert run('ek3p',vals('ek3p',by),good);cases=1
    for n in ('ejsl','seob','eisqd'):
        for row in rows[n]:assert not run('ek3p',vals('ek3p',by),good|{n:relation(rows[n]-{row})});cases+=1
        old.reject(lambda:run('ek3p',vals('ek3p',by),good|{n:forbidden}),unknown=True);cases+=1
    # A second recorded event at the same time must also use the same units.
    extra=key([by[n] for n,t in TRACK]+['other',c(1)])
    assert not run('ek3p',vals('ek3p',by),good|{'seoa':relation(rows['seoa']|{extra})});cases+=1
    for t in TIMES:
        region=fn(sort(REGION),lambda x,y,z,time,t=t:r(time)!=t)
        assert not run('ek3p',vals('ek3p',by|{'region':region}),good);cases+=1
    old.reject(lambda:run('ek3p',vals('ek3p',by),good,mode='native'));cases+=1
    return dict(cases=cases,whole_selected_history_has_explicit_units_and_field_domain=True,extra_records_not_ignored=True,native_real_time_not_finitely_certified=True)

@lru_cache(None)
def acceleration_checks():
    # Evaluate the new wrapper with the unchanged native sepp and registered
    # polynomial interpretations of its all-real premises, never inferred samples.
    doc=extract_document(core(),roots=['ek3q'],statement_indices=[]).document
    for i,d in enumerate(doc['declarations']):
        if d['kind']=='definition' and d['name'] in analytic.ABSTRACT|{'ek3p'}:doc['declarations'][i]=dict(kind='primitive',name=d['name'],parameters=[p['sort'] for p in d['parameters']],result=d['result'])
    doc=extract_document(doc,roots=['ek3q'],statement_indices=[]).document
    declarations=''.join('r '+analytic.SYMBOLS[n]+'[] '+t+'.' for n,t in analytic.LAW)+'r jpdlength[] a.r jpdtime[] a.r jpdregion[] '+REGION+'.'
    call=k('ek3q',*[k(analytic.SYMBOLS[n]) for n,t in AT],k('jpdlength'),k('jpdtime'),k('jpdregion'))
    doc=parse(format_graph(doc,'compact')+declarations+'q['+call+'].');cases=0
    for variant in ('baseline','local_interval','fake_velocity_field','sample_alias_field','wrong_acceleration','wrong_point','proper_parameter','missing_history','isolated','one_sided','empty_domain','wrong_matter','wrong_frame','wrong_event','wrong_context'):
        model=analytic.PolynomialModel(doc,variant,velocity=(0,0,0))
        model.model.update(jpdlength=lambda:'lengthunit',jpdtime=lambda:'timeunit',jpdregion=lambda:fn(sort(REGION),lambda *xs:True))
        model.model['ek3p']=lambda matter,frame,ctx,domain,curve,L,T,region:(matter,frame,ctx,L,T)==('matter','frame','text','lengthunit','timeunit') and analytic.unwrap(curve).implementation in model.curves
        primitives={d['name']:model.model[d['name']] for d in doc['declarations'] if d['kind']=='primitive'}
        actual=[r['value'] for r in evaluate_document(doc,individuals=analytic.PEOPLE+('lengthunit','timeunit'),situations=('text','other'),primitives=primitives,max_steps=5000000)]
        assert actual==[variant in ('baseline','local_interval')],variant;cases+=1
    return dict(cases=cases,native_second_derivative_wrapper_on_registered_polynomials=True,finite_alias_velocity_field_rejected=True,zero_velocity_with_nonzero_acceleration=True,general_cut_limits_proved=False)

@lru_cache(None)
def binder_checks():
    cases=0;doc=boundary('ek3x')
    # Rational scales are diagnostic slots too. Collapse their sorts only in
    # this binding fixture, and replace the fixed real unit with a fixed atom.
    def collapse_numbers(node):
        if node=='number':return 'individual'
        if isinstance(node,list):return [collapse_numbers(x) for x in node]
        if not isinstance(node,dict):return node
        if node.get('kind')=='call' and node.get('symbol')=='bb':return dict(kind='call',symbol='jpdunit',arguments=[])
        return {k:collapse_numbers(x) for k,x in node.items()}
    doc=collapse(collapse_numbers(doc));doc['declarations'].append(dict(kind='primitive',name='jpdunit',parameters=[],result='individual'))
    doc['declarations'].sort(key=lambda d:d['kind']!='primitive')
    doc=extract_document(doc,roots=['ek3x'],statement_indices=[]).document
    for pivot in range(len(CASES)):
        f,d,slots,var,body=lifted(doc,'ek3x',pivot,len(CASES),'forall')
        calls={x['symbol']:x for x in walk(body) if x.get('kind')=='call'};assert calls['ek3v']['arguments']==calls['ek3w']['arguments']
        env={p['name']:'case' if p['sort']=='situation' else 'a' for p in d['parameters']}
        def row(pick):
            values=env|{var:pick};return tuple(values[x['name']] if x['kind']=='variable' else 'a' for x in calls['ek3v']['arguments'])
        for selected,allowed,want in [(('a','b'),('a','b'),True),(('a','b'),('a',),False),(('b',),('a',),False),((),(),True)]:
            hs,ls={row(x) for x in selected},{row(x) for x in allowed}
            mm={n:lambda x=env[p['name']]:x for n,p in zip(slots,d['parameters'])}|{'ra':lambda:'a','jpdunit':lambda:'a','ek3v':lambda *xs:xs in hs,'ek3w':lambda *xs:xs in ls}
            assert evaluate_document(f,individuals=('a','b'),situations=POINTS,primitives=mm,max_steps=20000)[0]['value']==want;cases+=1
    return dict(cases=cases,all_setting_binders_shared=len(CASES),context_and_coordinate_point_are_distinct=True,native_quantifiers_preserved=True)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));math={m['id']:m for m in inv['math']};segments=[]
    for u in inv['units'][238:243]:
        assert digest(u['text'].encode())==u['text_sha256'];ms=[math[n] for n in u['math_ids']]
        for m in ms:assert digest(m['mathml'].encode())==m['sha256']
        segments.append(dict(unit=u['id'],text=u['text'],unit_sha256=u['text_sha256'],math=ms))
    return dict(version='einstein-point-particle-dynamics-obligations-v1',segments=segments,semantic_completion=False,observations=['原刊917頁の§10見出し、点状の電荷εを持つ粒子と以下のElektronの命名、nur folgendes annehmen、瞬間静止と次の時間部分、三行のμ d²x/dt²=εX等、x,y,zと低速時のμの意味説明を視認した。','局所的な三式の物理的設定と条件を構成する。次の時間部分・限定した仮定・命名・意味説明・見出し・著者提示の全文統合は未完。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in (INVENTORY,FACSIMILE,DOC)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    before=load_catalog(ROOT,PARENT_BASIS);after=load_catalog(ROOT,BASIS)
    assert after.document['statements']==before.document['statements'] and len(after.document['statements'])==413
    assert after.document['declarations'][:len(before.document['declarations'])]==before.document['declarations']
    assert all(after.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in before.entries.items())
    assert selection_binding(after,[412])==selection_binding(before,[412]);load_annotations(ROOT,BASIS,ANNOTATIONS)
    assert json.loads(read(ANNOTATIONS))['entries']==json.loads(read('data/charge-constancy-claim-identifiers-v1.json'))['entries']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    olddoc=parse(read('examples/v014/material-acceleration.noema'));current={d['name']:d for d in core()['declarations']}
    for d in olddoc['declarations']:
        if d['name'] in ('sepn','sepo','sepp'):assert current[d['name']]==d
    assert len(MEANINGS)==11 and len(PRIMITIVES)==1
    hypothesis=extract_document(core(),roots=['ek3v'],statement_indices=[]).document
    assert not {'ek3s','ek3t','ek3w','ek3x','ejso','ejsm'}&{d['name'] for d in hypothesis['declarations']}
    for style in ('compact','full'):
        body=format_graph(core(),style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core()
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=11,new_general_relations=1,new_statements=0,all_413_prior_statements_and_meanings_preserved=True,law_and_vacuum_not_assumed_in_setting=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('numeric',numeric_checks),('physical',physical_checks),('history',history_checks),('acceleration',acceleration_checks),('binder',binder_checks),('structure',structure_checks)]}
    helpers=('compose_limits','compose_material_relative_frame','compose_material_velocity','compose_material_acceleration','compose_vacuum_field_domain','compose_field_equations','compose_doppler_infinity','compose_relativity_conjecture','check_attached_material_charge','check_body_rest_field_method','check_material_relative_frame','check_tau_differential','check_ninth_section_opening','check_convective_foundation_reading','check_problem_series_reduction','check_material_acceleration','check_plane_waveforms','check_rod_setup','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,*DEPENDENCIES,'examples/v014/material-acceleration.noema','scripts/compose_point_particle_dynamics.py','scripts/check_point_particle_dynamics.py','tests/test_point_particle_dynamics.py',*(f'scripts/{n}.py' for n in helpers)}
    return dict(status='point_particle_local_rest_dynamics_pending_full_source_claim',document=FULL,**results,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
