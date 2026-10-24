"""Check instantaneous-rest witnesses and physically bound unit test forces."""
from functools import lru_cache
from fractions import Fraction as Q
from itertools import product
import json,re,xml.etree.ElementTree as ET
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import FunctionValue,DescriptionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_clock_site_time import relation,perturb,unknowns,forbidden
from scripts.check_electric_action import setup as electric_setup
from scripts.check_material_relative_frame import NUM,RS,arithmetic
from scripts.compose_resting_charge_force import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,PARENT_BASIS,INDICES,MEANINGS,LOCAL,REST,build

DOC='docs/resting-charge-force-v1.md';SOURCE='data/einstein-resting-charge-force-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';FACSIMILE='artifacts/written-facsimiles-v1/einstein-1905-unlp-p909-0.jpg'
DEPENDENCIES=('reports/moving-unit-charge-v1.json','reports/point-charge-calibration-v1.json','reports/material-velocity-v1.json','reports/electric-action-v1.json','reports/moving-field-definition-v1.json')
AXES=('x','y','z','t');SITUATIONS=('case','other')
PS=dict(kind='function',parameters=['individual'],result=RS)
TAU=dict(kind='function',parameters=[RS]*4,result=RS)
CONSTANTS={'ri':'case','rd':'author','eirf':'paper','zno':'scope','ra':'frame','zbm':'moving','zol':'carrier','zpo':'event','zpp':'chargerecord','eisqk':'movingrecord','zpe':'forcerecord','zpf':'movingforce','zor':'chargekind','zpn':'forcekind','zou':'chargeunit','zot':'forceunit','ta':'length','rb':'duration','zpg':'previous','zph':'standingclaim','zpi':'instantclaim','eispj':'oldnotation','eispv':'newnotation',**dict(zip(('yn','yo','yp','zc7'),AXES))}
DOMAIN=tuple(dict.fromkeys((*CONSTANTS.values(),'fieldunit','other','a','b')))

def retag(node):
    if isinstance(node,list):return [retag(x) for x in node]
    if not isinstance(node,dict):return node
    result={key:retag(value) for key,value in node.items()}
    if node.get('kind') in ('exists','forall') and isinstance(node['sort'],dict):result['sort']='individual'
    return result

@lru_cache(None)
def fixture(name,mode='native'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    boundaries=NUM|{'sjs','seob','senz','ejtr','ejsl'}
    boundaries|={'ejww':{'ejwu'},'ejwx':{'ejwr','ejwv'}}.get(name,set())
    if mode=='witness':boundaries|={'ejwr':{'ejwq'},'ejwu':{'ejwt'},'ejwv':{'ejwt'},'ejwy':{'ejts'}}[name]
    abstract(doc,boundaries);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    if mode=='witness':
        doc=retag(doc)
        for d in doc['declarations']:
            if d['kind']=='primitive':
                d['parameters']=['individual' if isinstance(s,dict) else s for s in d['parameters']]
                if isinstance(d['result'],dict):d['result']='individual'
            else:
                for p in d['parameters']:
                    if isinstance(p['sort'],dict):p['sort']='individual'
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[]
    for i,p in enumerate(d['parameters']):
        n='jrcf'+number_word(i);slots.append((n,p['sort']));doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    if not any(d['name']=='ri' for d in doc['declarations']):doc['declarations'].append(dict(kind='primitive',name='ri',parameters=[],result='situation'))
    expr=dict(kind='call',symbol=name,arguments=[dict(kind='call',symbol=n,arguments=[]) for n,_ in slots])
    if d['result']=='content':expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='ri',arguments=[]))
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,args,m,mode='native',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(args)==len(slots)
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|m
    for (n,s),x in zip(slots,args):
        if isinstance(s,dict) and callable(x) and not isinstance(x,FunctionValue):x=FunctionValue(tuple(s['parameters']),s['result'],x)
        mm[n]=lambda x=x:x
    return evaluate_document(doc,individuals=domain,situations=SITUATIONS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=600000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def force_setup():
    cuts,m,f=electric_setup(1,1);c,r=cuts.make,cuts.read
    f|={'lengthunit':'length','timeunit':'duration'}
    for (n,_),(_,sort) in zip(LOCAL,fixture('ejwt')[1]):
        if isinstance(sort,dict) and not isinstance(f[n],FunctionValue):f[n]=FunctionValue(tuple(sort['parameters']),sort['result'],f[n])
    response=FunctionValue((PS,RS),PS,lambda p,a:FunctionValue(('individual',),RS,lambda axis:c(r(a)*r(f['electricfield'](axis)(*[p(n) for n in AXES])))))
    f['response']=response
    points=[tuple(map(Q,row)) for row in ((1,2,3,4),(2,3,4,5))]
    def one(x):
        if isinstance(x,DescriptionValue):return json.loads(x.syntax)['symbol']
        if not isinstance(x,FunctionValue):return x
        if x.parameters==('number',):return r(x)
        if x.parameters==('individual',) and x.result==RS:return tuple(r(x(a)) for a in AXES)
        if x.parameters==('individual',):return tuple(r(x(a)(*[c(t) for t in p])) for a in AXES[:3] for p in points)
        if x.parameters==tuple([RS]*4):return tuple(x(*[c(t) for t in p]) for p in points)
        if x.parameters==(PS,RS):return tuple(r(x(FunctionValue(('individual',),RS,lambda a,p=p:c(p[AXES.index(a)] if a in AXES else 0)),c(amount))(axis)) for p in points for amount in (-1,0,1) for axis in AXES[:3])
        raise ValueError('Unknown force function fingerprint')
    norm=lambda xs:tuple(one(x) for x in xs);rel=lambda rows:lambda *xs:norm(xs) in rows
    args=[f[n] for n,_ in LOCAL]+[response]
    fields=['chargekind','frame','length','duration','chargeunit','forceunit',f['region'],'case',response,'fieldunit',c(1),f['electricfield']]
    rows={'va':{('frame',)},'eisqc':{('carrier','case')},'eisqd':{norm(('carrier','frame','event','length','duration',f['point'],'case'))},'ejsl':{('frame','length','duration','case')},'eispt':{norm(fields[:9])},'eispu':{norm(('chargekind','chargeunit','fieldunit','forceunit',c(1),'case'))},'ejtr':{norm((f['electricfield'],response,c(1),f['region']))}}
    m|={n:rel(rs) for n,rs in rows.items()}
    return dict(c=c,r=r,m=m,f=f,args=args,rows=rows,norm=norm,rel=rel)

@lru_cache(None)
def force_checks():
    s=force_setup();m=s['m'];args=s['args'];cases=perturb(lambda mm:run('ejwt',args,mm),m,s['rows'],s['norm'])
    for i,(name,t) in enumerate(LOCAL):
        bad=list(args)
        if t in ('a','d'):bad[i]='other'
        elif name=='region':bad[i]=lambda *xs:False
        elif name in ('electricfield','magneticfield'):bad[i]=lambda axis:FunctionValue(tuple([RS]*4),RS,lambda *xs:s['c'](99))
        else:bad[i]=lambda axis:s['c'](99)
        assert not run('ejwt',bad,m),name;cases+=1
    for n in ('eirl','eirm','eirn','znn','zpc','zpb','zog','zof'):
        assert not run('ejwt',args,m|{n:lambda *xs:False}),n;cases+=1
        unknowns(lambda mm:run('ejwt',args,mm),m,(n,))
    for axis in AXES[:3]:
        wrong=FunctionValue(('individual',),RS,lambda a,axis=axis:s['c'](s['r'](s['f']['force'](a))+(a==axis)))
        bad=list(args);bad[14]=wrong
        assert not run('ejws',bad[:-1],m|{'zpc':lambda *xs:True});cases+=1
    # With identical force magnitudes a permutation still changes components.
    wrong=FunctionValue(('individual',),RS,lambda a:s['f']['force']({'x':'z','z':'x'}.get(a,a)))
    bad=list(args);bad[14]=wrong
    assert not run('ejws',bad[:-1],m|{'zpc':lambda *xs:True});cases+=1
    assert run('ejwt',args,m|{'x4':forbidden,'zpa':forbidden,'xm':forbidden,'s5y':forbidden});cases+=1
    return dict(cases=cases,native_unit_charge_and_electric_force_binding=True,all_three_components_not_just_magnitude=True,physical_response_and_all_units_shared=True,full_response_law_and_coordinate_system_are_explicit_boundaries=True)

def rest_setup(velocity=(0,0,0),acceleration=(0,0,0),variant='baseline'):
    cuts,m=arithmetic();c,r=cuts.make,cuts.read
    point=FunctionValue(('individual',),RS,lambda a:c(dict(zip(AXES,(1,2,3,4))).get(a,0)))
    domain=FunctionValue((RS,),'truth',lambda t:True if variant not in ('isolated','one_sided') else r(t)==4 if variant=='isolated' else r(t)>=4)
    def at(t):
        d=r(t)-4;coords=tuple(Q(i+1)+Q(velocity[i])*d+Q(acceleration[i])*d*d for i in range(3))+(r(t),)
        return FunctionValue(('individual',),RS,lambda a:c(coords[AXES.index(a)] if a in AXES else 0))
    curve=FunctionValue((RS,),PS,at);args=['carrier','moving','event',point,'case',domain,curve]
    samepoint=lambda p:tuple(r(p(a)) for a in AXES)==(1,2,3,4)
    m|={'seob':lambda b,f,ctx,d,cv:(b,f,ctx)==('carrier','moving','case') and variant!='missing_history',
        'senz':lambda d,t:variant not in ('isolated','one_sided') and r(t)==4 and d(t),
        'zpb':lambda b,f,e,p,ctx:(b,f,e,ctx)==('carrier','moving','event','case') and samepoint(p)}
    observed=[]
    def derivative(d,fn,t,value):
        center=r(t);f0=r(fn(c(center)));left=r(fn(c(center-1)));right=r(fn(c(center+1)))
        slope=(right-left)/2;quad=(right+left-2*f0)/2
        assert all(r(fn(c(center+step)))==f0+slope*step+quad*step*step for step in (-2,2))
        observed.append(slope);return d(t) and slope==r(value)
    m['sjs']=derivative
    return dict(args=args,m=m,c=c,r=r,point=point,observed=observed)

@lru_cache(None)
def rest_checks():
    cases=0
    for vel,acc,want in [((0,0,0),(0,0,0),True),((0,0,0),(2,-3,1),True),((1,0,0),(0,0,0),False),((0,-1,0),(0,0,0),False),((0,0,1),(0,0,0),False)]:
        s=rest_setup(vel,acc);assert run('ejwq',s['args'],s['m'])==want;assert len(s['observed'])==3;cases+=1
    for variant in ('isolated','one_sided','missing_history'):
        s=rest_setup(variant=variant);assert not run('ejwq',s['args'],s['m']);cases+=1
    s=rest_setup()
    for i in (0,1,2,4):
        args=list(s['args']);args[i]='other';assert not run('ejwq',args,s['m']);cases+=1
    args=list(s['args']);args[3]=FunctionValue(('individual',),RS,lambda a:s['c'](99))
    assert not run('ejwq',args,s['m']);cases+=1
    unknowns(lambda mm:run('ejwq',s['args'],mm),s['m'],('seob','senz','zpb','sjs'))
    assert run('ejwq',s['args'],s['m']|{'x4':forbidden,'zpa':forbidden,'xm':forbidden});cases+=1
    try:run('ejwr',s['args'][:5],s['m'])
    except ValueError as e:assert 'Finite function domain' in str(e) or 'rational number domain' in str(e),str(e)
    else:raise AssertionError('Full trajectory function domain silently sampled')
    return dict(cases=cases,native_three_coordinate_derivatives_zero=True,nonzero_acceleration_allowed=True,history_interior_and_derivative_oracles_explicit=True,full_function_domain_refused=True)

@lru_cache(None)
def witness_checks():
    cases=0
    for name,callee in [('ejwr','ejwq'),('ejwu','ejwt'),('ejwv','ejwt'),('ejwy','ejts')]:
        doc,_=fixture(name,'witness');base={d['name']:lambda:'a' for d in doc['declarations'] if d['kind']=='primitive' and not d['parameters'] and d['result']=='individual'}
        base|={'bb':lambda x:'a','ri':lambda:'case'}
        args=['a','a','a','a','case'] if name=='ejwr' else ['case'] if name in ('ejwu','ejwv') else []
        for first,second in product(('a','b'),repeat=2):
            if name=='ejwr':target=('a','a','a','a','case',first,second)
            elif name=='ejwy':target=('a','a','a','a','a','a','a','case',second,first,'a','a')
            else:target=tuple(first if i==6 else 'case' if i==15 else second if i==16 else 'a' for i in range(17))
            m=base|{callee:lambda *xs,target=target:xs==target}
            assert run(name,args,m,'witness',('a','b'));cases+=1
            assert not run(name,args,base|{callee:lambda *xs:False},'witness',('a','b'));cases+=1
        unknowns(lambda mm:run(name,args,mm,'witness',('a','b')),base|{callee:lambda *xs:True},(callee,))
    return dict(cases=cases,two_witness_slots_distinguished=True,diagnostic_retagging_only_not_native_domain_proof=True)

@lru_cache(None)
def conditional_checks():
    s=rest_setup();cases=0
    for rest,result in product((False,True),repeat=2):
        m={'x4':lambda *xs,rest=rest:rest and xs==('carrier','frame','case'),'ejwu':lambda ctx,result=result:result and ctx=='case'}
        assert run('ejww',[],m)==(not rest or result);cases+=1
        m={'zpk':lambda:s['point'],'ejwr':lambda b,f,e,p,ctx,rest=rest:rest and (b,f,e,ctx)==('carrier','moving','event','case'),'ejwv':lambda ctx,result=result:result and ctx=='case'}
        assert run('ejwx',[],m)==(not rest or result);cases+=1
    return dict(cases=cases,two_separate_conditions_not_simultaneously_asserted=True)

@lru_cache(None)
def presentation_checks():
    cases=0
    for name,node,claim,notation,rule in [('ejwz','standingclaim','ejww','oldnotation','ejs4'),('ejw2','instantclaim','ejwx','newnotation','ejtx')]:
        rows={'uh':{(node,'author',claim,'scope','case')},'eispi':{(notation,rule,'paper','case')}}
        if name=='ejwz':rows['eisql']={(node,'author','ejwy',claim,'scope','case')}
        m={n:relation(rs) for n,rs in rows.items()};cases+=perturb(lambda mm:run(name,[],mm),m,rows)
        assert run(name,[],m|{n:forbidden for n in ('ejwy','ejww','ejwx','ejs4','ejtx')});cases+=1
    for name,node,prior,message in [('ejw4','standingclaim','previous','ejw3'),('ejw6','instantclaim','standingclaim','ejw5')]:
        rows={'eir3':{(node,'author','paper',message,'case')},'ue':{(prior,node,'case')}}
        cases+=perturb(lambda mm:run(name,[],mm),{n:relation(rs) for n,rs in rows.items()},rows)
    return dict(cases=cases,definition_reference_not_new_definition_or_proof=True,notation_author_and_order_bound=True)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));u=inv['units'][172];assert u['id']=='einstein-1905:u0173' and digest(u['text'].encode())==u['text_sha256']
    starts=[u['text'].index('Ruht diese'),u['text'].index('Ruht die Elektrizitätsmenge')];ends=[starts[1]-1,u['text'].index(' Die ersten')]
    segments=[]
    for start,end,mathid,statement,expected in zip(starts,ends,('M0316','M0317'),INDICES,('X,Y,Z','X′,Y′,Z′')):
        math=next(m for m in inv['math'] if m['id']==mathid);assert digest(math['mathml'].encode())==math['sha256'] and ''.join(ET.fromstring(math['mathml']).itertext())==expected
        text=u['text'][start:end];segments.append(dict(range=[start,end],text=text,math=math,statement=statement,source_nonblank_characters=len(re.sub(r'\s|\[M\d+\]','',text))))
    return dict(status='partial_rest_and_instantaneous_rest_force_reading',unit=u['id'],unit_sha256=u['text_sha256'],segments=segments,observations=['原刊909頁の第四・第五文を再読した。Kへの静止と、kへの少なくとも当該瞬間の静止を区別する。','definitionsgemäßを既存の場の定義への参照として保持し、力を同じ対象・出来事・系・単位へ結ぶ。','M0316はX,Y,Z、M0317はX′,Y′,Z′であり、力はそれぞれの系で測る。'],remaining=['第一文の最終六式の解釈導入','第六文の電気側三式と二つの言い表しへの導入','u0173全六文の通読判断'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in (INVENTORY,DOC,FACSIMILE)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert len(new.document['statements'])==358
    assert [i for i,(a,b) in enumerate(zip(old.document['statements'],new.document['statements'])) if a!=b]==INDICES
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    assert selection_binding(new,[157,158,159,160,161,162,163,164])==selection_binding(old,[157,158,159,160,161,162,163,164])
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);names=set(selection_binding(new,INDICES)['dependencies'])
    assert set(MEANINGS)|{'seoc','eibs','ejts','eisqd','eisqc','eispi','eisql'}<=names
    assert not names&{'sce2','scf2','zpa','xm','s5y','eisqg','eisqh'}
    core=parse(read(CORE))
    for style in ('compact','full'):
        body=format_graph(core,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core
    assert json.loads(json.dumps(source_record(),ensure_ascii=False))==json.loads(read(SOURCE))
    return dict(new_definitions=len(MEANINGS),new_general_relations=1,new_references=1,replaced_statements=INDICES,other_356_statements_and_prior_judgments_preserved=True,whole_unit_review_not_claimed=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('force',force_checks),('rest',rest_checks),('witness',witness_checks),('conditional',conditional_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    helpers=('compose_vacuum_field_domain','compose_material_relative_frame','compose_relativity_conjecture','compose_two_postulates','compose_field_equations','compose_material_velocity','compose_electric_action','compose_moving_field_definition','compose_rest_force','compose_limits','check_coordinate_correspondence','check_clock_site_time','check_electric_action','check_material_relative_frame','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,*DEPENDENCIES,'scripts/compose_resting_charge_force.py','scripts/check_resting_charge_force.py','tests/test_resting_charge_force.py',*(f'scripts/{n}.py' for n in helpers)}
    s=source_record();segments=[]
    for part in s['segments']:
        row=dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=part['range'],source=part['text'],statements=[part['statement']],definitions=list(MEANINGS),status='explicit_interpretive_annotation')
        segments.extend([row,dict(row,math_id=part['math']['id'],math_sha256=part['math']['sha256'])])
    return dict(status='rest_and_instantaneous_rest_unit_charge_force_connected',document=FULL,**results,alignment=dict(segments=segments),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=s['remaining'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
