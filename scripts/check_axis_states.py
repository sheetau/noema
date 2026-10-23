"""Check physical coordinate snapshots, uniqueness and complete time coverage."""
from functools import lru_cache
from fractions import Fraction as Q
from itertools import product
import json,re
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import FunctionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_moving_trip_geometry import NUM,numbers
from scripts.check_material_relative_frame import RS
from scripts.check_moving_axes import setup,DOMAIN
from scripts.check_rod_methods import value,relation
from scripts.compose_axis_states import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,MEANINGS,build

DOC='docs/axis-states-v1.md';SOURCE='data/einstein-axis-states-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';PRIOR='data/einstein-frame-instruments-review-v1.json'
DEPENDENCIES=('reports/moving-axes-v1.json','reports/frame-motion-v1.json')
POINTS=('context','scope','scene','other')
def forbidden(*xs):raise ValueError('Unknown axis-states input')
def constants():return {n:lambda x=x:x for n,x in {'ra':'frame','zbm':'moving','zb6':'scope','ta':'lengthunit','rb':'timeunit','yn':'x','yo':'y','yp':'z'}.items()}

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    boundaries=set(NUM)
    if name=='eiwf':boundaries|={'eiwd','eiwe','eiwc'}
    if name=='eiwg':boundaries|={'eiwd','eiwc'}
    if name=='eiwh':boundaries|={'eiwf','eiwg'}
    if name=='eiwj':boundaries|={'eivz','eiv7','eiwh','eiwi'}
    abstract(doc,boundaries);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name)
    if mode=='instance':
        added=[]
        def walk(node):
            if isinstance(node,list):return [walk(x) for x in node]
            if not isinstance(node,dict):return node
            if node.get('kind')=='forall' and node['sort']==RS:
                added.append(dict(name=node['variable'],sort=node['sort']));return walk(node['body'])
            return {k:walk(v) for k,v in node.items()}
        d['body']=walk(d['body']);d['parameters']+=added;assert len(added)==1
    slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jas'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    doc['statements']=[dict(kind='ask',body=dict(kind='call',symbol=name,arguments=args))];return doc,slots

def run(name,args,m,mode='boundary',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(args)==len(slots)
    mm=constants()|m|{n:lambda x=x:x for n,x in zip(slots,args)}
    return evaluate_document(doc,individuals=domain,situations=POINTS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=500000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def unknowns(check,m,names):
    for n in names:
        try:check(m|{n:forbidden})
        except ValueError as e:assert 'Unknown axis-states' in str(e),str(e)
        else:raise AssertionError(('Unknown input accepted',n))

def perturb(check,m,rows,norm=lambda xs:tuple(value(x) for x in xs)):
    count=1;assert check(m)
    for n,rs in rows.items():
        for row in rs:
            assert not check(m|{n:lambda *xs,rs=rs-{row}:norm(xs) in rs}),(n,row);count+=1
            for i in range(len(row)):
                bad=tuple('wrong' if i==j else x for j,x in enumerate(row))
                assert not check(m|{n:lambda *xs,rs=(rs-{row})|{bad}:norm(xs) in rs}),(n,i);count+=1
    unknowns(check,m,rows);return count

@lru_cache(None)
def coordinate_checks():
    cuts,m,fs,_=setup();c=cuts.make;r=cuts.read
    coords={a:r(fs[i]('guide')(c(Q(1)))) for i,a in enumerate(('x','y','z'))}
    def record(p,moment,f,lu,a,ctx):
        if (p,moment,f,lu)!=('guide','point','frame','lengthunit') or a not in coords or ctx not in ('context','scene'):forbidden()
        return c(coords[a])
    rows={'zce':{('guide','point','frame','lengthunit',ctx) for ctx in ('context','scene')},'zcf':{('point','frame','timeunit',ctx) for ctx in ('context','scene')}}
    m|={n:relation(rs) for n,rs in rows.items()};m|={'ym':record,'yl':lambda *xs:c(Q(1))}
    check=lambda mm:run('eiwc',['guide','point','context','scene'],mm)
    count=perturb(check,m,rows)
    for a in coords:
        assert not check(m|{'ym':lambda *xs,a=a:c(coords[a]+1) if xs[4]==a and xs[5]=='scene' else record(*xs)});count+=1
    assert not check(m|{'yl':lambda *xs:c(Q(2 if xs[-1]=='scene' else 1))});count+=1
    unknowns(check,m,('ym','yl','ba','sca'))
    rows={n:{row for row in rs if row[-1]=='context'} for n,rs in rows.items()}
    check=lambda mm:run('eiwe',['body','guide','point','context'],mm)
    count+=perturb(check,m,rows)
    for a in coords:
        assert not check(m|{'ym':lambda *xs,a=a:c(coords[a]+1) if xs[4]==a else record(*xs)});count+=1
    for time in (-1,3):
        assert not check(m|{'yl':lambda *xs,time=time:c(Q(time))});count+=1
    unknowns(check,m,('ym','yl','eislu','eisls','eislt'))
    return dict(cases=count,all_three_coordinates_and_same_rest_time_checked=True,record_values_bound_to_physical_history=True)

def objects():
    return {'x':'body','y':'second','z':'other'},{'body':('guide','hidden'),'second':('otherguide',),'other':('point',)}

@lru_cache(None)
def metadata_checks():
    lines,_=objects()
    rows={'zcn':{('point',)},'zbv':{('moving','origin','scene')},'zbw':{('moving',line,a,'scene') for a,line in lines.items()}}
    m={n:relation(rs) for n,rs in rows.items()}|{'zcl':lambda p:'scene','zbn':lambda *xs:'origin','zbo':lambda f,a,ctx:lines[a]}
    check=lambda mm:run('eiwd',['point','context'],mm);count=perturb(check,m,rows)
    for n,extra in (('zbv',('moving','otherorigin','scene')),('zbw',('moving','guide','x','scene')),('zbw',('moving','body','other','scene'))):
        assert not check(m|{n:relation(rows[n]|{extra})});count+=1
    assert not check(m|{'zbn':lambda f,ctx:'otherorigin' if ctx=='scene' else 'origin'});count+=1
    for axis in lines:
        assert not check(m|{'zbo':lambda f,a,ctx,axis=axis:'hidden' if a==axis and ctx=='scene' else lines[a]});count+=1
    unknowns(check,m,('zcl','zbn','zbo'))
    return dict(cases=count,same_origin_and_exact_three_roles_in_snapshot=True,no_whole_history_imposed_on_snapshot=True)

def population_setup():
    cuts,m=numbers();c=cuts.make;r=cuts.read;lines,members=objects()
    norm=lambda xs:tuple(r(x) if isinstance(x,FunctionValue) else value(x) for x in xs)
    selected={(body,p) for body,ps in members.items() for p in (*ps,'origin')}
    m|={'zci':lambda hist:'context','zcl':lambda pose:'scene','zbn':lambda *xs:'origin','zbo':lambda f,a,ctx:lines[a],'eirh':lambda body,p,ctx:ctx=='context' and p in members.get(body,()),'yl':lambda *xs:c(Q(1))}
    return cuts,m,norm,selected

@lru_cache(None)
def assignment_checks():
    cuts,m,norm,selected=population_setup()
    rows={'zcn':{('point',)},'zcf':{('guide','frame','timeunit',ctx) for ctx in ('scope','context')},'zck':{('body','guide','point','frame','timeunit',Q(1),'context')},'eiwd':{('point','context')},'eiwe':{(b,p,'guide','context') for b,p in selected},'eiwc':{(p,'guide','context','scene') for b,p in selected}}
    m|={n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}
    check=lambda mm:run('eiwf',['body','guide','point'],mm)
    count=perturb(check,m,rows,norm)
    assert not check(m|{'eirh':lambda b,p,ctx:(b,p) in {('body','otherorigin')} or m['eirh'](b,p,ctx)});count+=1
    unknowns(check,m,('zci','zcl','zbn','zbo','eirh','yl'))
    rows={'eiwd':{('point','context'),('otherguide','context')},'eiwc':{(p,'guide','scene','other') for b,p in selected}}
    m|={n:relation(rs) for n,rs in rows.items()};m['zcl']=lambda p:'scene' if p=='point' else 'other'
    count+=perturb(lambda mm:run('eiwg',['point','otherguide','guide','context'],mm),m,rows)
    return dict(cases=count,all_axis_members_and_origin_bound_to_same_history_and_snapshot=True,extra_hidden_member_cannot_be_omitted=True,distinct_state_identifiers_can_describe_equal_configuration=True)

@lru_cache(None)
def uniqueness_checks():
    domain=('a','b');pairs=list(product(domain,repeat=2));count=0
    for assigned_bits in product((False,True),repeat=2):
        assigned={p for p,on in zip(domain,assigned_bits) if on}
        for equal_bits in product((False,True),repeat=4):
            same={pair for pair,on in zip(pairs,equal_bits) if on}
            m={'zci':lambda h:'context','eiwf':lambda h,t,p:p in assigned,'eiwg':lambda a,b,t,ctx:(a,b) in same}
            expected=bool(assigned) and all((a,b) in same for a,b in product(assigned,repeat=2))
            assert run('eiwh',['a','b'],m,domain=domain)==expected;count+=1
    return dict(cases=count,existence_and_all_corresponding_states_checked=True,duplicate_equal_descriptions_allowed_but_conflicting_state_rejected=True)

@lru_cache(None)
def coverage_checks():
    cuts,m=numbers();c=cuts.make;r=cuts.read
    values={p:Q(10) for p in DOMAIN};values.update(guide=Q(0),point=Q(2),hidden=Q(1),second=Q(1))
    rows={'ys':{('guide','context'),('point','context')},'zcf':{(p,'frame','timeunit','context') for p in DOMAIN}}
    m|={n:relation(rs) for n,rs in rows.items()};m|={'yl':lambda p,*xs:c(values[p]),'eisls':lambda *xs:c(Q(0)),'eislt':lambda *xs:c(Q(2))}
    count=0
    for time,expected in ((-1,False),(0,True),(1,False),(2,True),(3,False)):
        assert run('eiwi',[c(Q(time)),'context'],m)==expected;count+=1
    for witness in ('hidden','second'):
        check=lambda mm:run('eiwi',[c(Q(1)),'context'],mm)
        amended=m|{'ys':relation(rows['ys']|{(witness,'context')})}
        assert check(amended);count+=1
        assert not check(amended|{'zcf':relation(rows['zcf']-{(witness,'frame','timeunit','context')})});count+=1
    unknowns(lambda mm:run('eiwi',[c(Q(0)),'context'],mm),m,('ys','zcf','yl','eisls','eislt'))
    return dict(cases=count,missing_intermediate_real_time_detected=True,alternative_and_duplicate_time_records_allowed=True)

@lru_cache(None)
def candidate_checks():
    cuts,m=numbers();c=cuts.make;r=cuts.read
    norm=lambda xs:tuple(r(x) if isinstance(x,FunctionValue) else value(x) for x in xs)
    rows={'zch':{('body','scope')},'eivz':{('context',)},'eiv7':{('moving','context')},'eiwh':{('body',p) for p in ('guide','point')},'eiwi':{(Q(1),'context')}}
    ys={(p,ctx) for p in ('guide','point') for ctx in ('scope','context')};alltime={('frame','moving',p,'context') for p in ('guide','point')}
    m|={n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}
    m|={'zci':lambda h:'context','ys':relation(ys),'eisla':relation(alltime),'eisls':lambda *xs:c(Q(0)),'eislt':lambda *xs:c(Q(2))}
    check=lambda mm:run('eiwj',['body',c(Q(1))],mm,'instance');count=perturb(check,m,rows,norm)
    for row in ys:
        assert not check(m|{'ys':relation(ys-{row})});count+=1
    for row in alltime:
        assert not check(m|{'eisla':relation(alltime-{row})});count+=1
    assert not check(m|{'ys':lambda *xs:False,'eisla':lambda *xs:False});count+=1
    for t in (-1,0,1,2,3):
        assert run('eiwj',['body',c(Q(t))],m|{'eiwi':lambda *xs:False},'instance')==(t not in (0,1,2));count+=1
    unknowns(check,m,('zci','ys','eisla','eisls','eislt'))
    try:run('eiwj',['body'],m)
    except ValueError as e:assert 'rational number domain' in str(e) or 'Finite function domain' in str(e),str(e)
    else:raise AssertionError('All real-time coverage silently sampled')
    return dict(cases=count,same_motion_geometry_and_complete_time_population=True,full_interval_coverage_not_finitely_sampled=True)

def source_record():
    inv=json.loads(read(INVENTORY));u=inv['units'][43];assert u['id']=='einstein-1905:u0044'
    start=u['text'].index('Jeder Zeit');end=u['text'].index(' und wir',start);text=u['text'][start:end]
    receipt='artifacts/einstein-moving-trip-v1/retrieval.json';paths={INVENTORY,DOC,receipt}
    for row in json.loads(read(receipt))['sources']:
        assert digest((ROOT/row['path']).read_bytes())==row['sha256'];paths.add(row['path'])
    return dict(version='einstein-axis-states-source-reading-v1',unit=u['id'],unit_sha256=u['text_sha256'],range=[start,end],text=text,source_nonblank_characters=sum(not c.isspace() for c in re.sub(r'\[M\d+\]','',text)),pages=['897'],observations=['Jeder Zeitの全時刻とeine bestimmte Lageの配置一意性を接続する。','配置を記述する状態は複数でも、同じ原点・全軸の同時刻配置は一致する。'],semantic_completion=False,remaining=['平行となる一つの候補運動の存在と採用','対称性の理由・第一文の設定指示・時刻tの説明','u0044全体の本文統合と意味判断'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements']==old.document['statements'] and len(new.document['statements'])==268
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read(PRIOR));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[267])==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);assert json.loads(read(ANNOTATIONS))['entries']==json.loads(read('data/moving-axes-identifiers-v1.json'))['entries']
    doc=parse(read(CORE));assert not doc['statements'];assert 'zcm' not in {d['name'] for d in doc['declarations']}
    for style in ('compact','full'):
        body=format_graph(doc,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=len(MEANINGS),new_primitives=0,preserved_statements=268,prior_meanings_and_reviews_preserved=True,configuration_equivalence_composed_from_coordinates=True,whole_unit_completion=False)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:fn() for n,fn in [('coordinates',coordinate_checks),('metadata',metadata_checks),('assignment',assignment_checks),('uniqueness',uniqueness_checks),('coverage',coverage_checks),('candidate',candidate_checks),('structure',structure_checks)]}
    source=source_record();paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source['source_sha256'])|{SOURCE,DOC,INVENTORY,PRIOR,*DEPENDENCIES,'scripts/compose_axis_states.py','scripts/check_axis_states.py','tests/test_axis_states.py','scripts/check_moving_axes.py','scripts/check_material_axes.py','scripts/check_moving_trip_geometry.py','scripts/check_coordinate_correspondence.py','scripts/check_rod_methods.py','scripts/check_material_relative_frame.py','scripts/check_tau_differential.py','scripts/compose_moving_axes.py','scripts/compose_material_axes.py','scripts/compose_rod_methods.py','scripts/compose_material_relative_frame.py','scripts/compose_limits.py'}
    return dict(status='definite_axis_states_and_full_time_coverage_checked',document=FULL,**results,alignment=dict(segments=[dict(unit=source['unit'],unit_sha256=source['unit_sha256'],range=source['range'],source=source['text'],definitions=list(MEANINGS),status='explicit_interpretive_annotation')]),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=source['remaining'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
