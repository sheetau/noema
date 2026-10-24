"""Check full-vector boosts, physical frame bindings and the new wording."""
from functools import lru_cache
from fractions import Fraction as Q
from itertools import product
import json,re
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import FunctionValue,DescriptionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_clock_site_time import relation,perturb,unknowns,forbidden
from scripts.check_resting_charge_force import retag,RS,PS,TAU
from scripts.check_total_differential import OPERATIONS
from scripts.check_field_transform import setup as numeric_setup
from scripts.check_force_motion_binding import vector
from scripts.compose_comoving_wording import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,PARENT_BASIS,INDEX,MEANINGS,PAIR,CURRENT,LOCAL,RESPONSE,build

DOC='docs/comoving-wording-v1.md';SOURCE='data/einstein-comoving-wording-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';FACSIMILE='artifacts/written-facsimiles-v1/einstein-1905-unlp-p910-0.jpg'
DEPENDENCIES=('reports/electromotive-wording-v1.json','reports/resting-charge-force-v1.json','reports/force-motion-binding-v1.json','reports/velocity-opening-claim-v1.json','reports/first-principle-v1.json','reports/field-transform-v1.json')
AXES=('x','y','z','t');SITUATIONS=('case','other')
CONSTANTS={'ri':'case','rd':'author','eirf':'paper','zno':'scope','ra':'frame','zol':'carrier','zpo':'event','zou':'chargeunit','zot':'forceunit','ta':'length','rb':'duration','zpq':'first','zpr':'second','eisqn':'intro','eispp':'process',**dict(zip(('yn','yo','yp','zc7'),AXES))}
DOMAIN=tuple(dict.fromkeys((*CONSTANTS.values(),'comoving','chargerecord','forcerecord','fieldunit','a','b','other')))

@lru_cache(None)
def fixture(name,mode='native'):
    doc=extract_document(parse(read(FULL if name in ('s46','s6k','s6l') else CORE)),roots=[name],statement_indices=[]).document
    bounds=OPERATIONS|{'ejm2','ejsl','ejwr','ejwt','ejyb'}
    if mode=='witness':bounds|={'ejyv':{'ejys','ejyu'},'ejyw':{'ejyv'}}[name]
    abstract(doc,bounds);doc=extract_document(doc,roots=[name],statement_indices=[]).document
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
        n='jcmw'+number_word(i);slots.append((n,p['sort']));doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    if not any(d['name']=='ri' for d in doc['declarations']):doc['declarations'].append(dict(kind='primitive',name='ri',parameters=[],result='situation'))
    expr=dict(kind='call',symbol=name,arguments=[dict(kind='call',symbol=n,arguments=[]) for n,_ in slots])
    if d['result']=='content':expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='ri',arguments=[]))
    elif d['result']!='truth':
        doc['declarations'].append(dict(kind='primitive',name='jcmwcapture',parameters=[d['result']],result='truth'));expr=dict(kind='call',symbol='jcmwcapture',arguments=[expr])
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,args,m,mode='native',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(args)==len(slots)
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|m
    for (n,s),x in zip(slots,args):
        if isinstance(s,dict) and callable(x) and not isinstance(x,FunctionValue):x=FunctionValue(tuple(s['parameters']),s['result'],x)
        mm[n]=lambda x=x:x
    captured=[]
    def capture(x):captured.append(x);return True
    mm['jcmwcapture']=capture
    result=evaluate_document(doc,individuals=domain,situations=SITUATIONS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=3000000,memoize_definitions=True,memoize_expressions=True)[0]['value']
    return captured[0] if captured else result

def dot(a,b):return sum(x*y for x,y in zip(a,b))
def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def boost(p,u,V=Q(5),beta=Q(5,4)):
    squared=dot(u,u)
    if squared==0:return tuple(p)
    parallel=tuple(dot(u,p[:3])/squared*x for x in u)
    xyz=tuple(x-a+beta*(a-v*p[3]) for x,a,v in zip(p[:3],parallel,u))
    return xyz+(beta*(p[3]-dot(u,p[:3])/(V*V)),)
def mix(e,h,u,V=Q(5),beta=Q(5,4)):
    squared=dot(u,u)
    if squared==0:return tuple(e),tuple(h)
    output=[]
    for own,other,sign in ((e,h,1),(h,e,-1)):
        parallel=tuple(dot(u,own)/squared*x for x in u);extra=cross(u,other)
        output.append(tuple(a+beta*(x-a+sign*y/V) for x,a,y in zip(own,parallel,extra)))
    return tuple(output)

POINTS=tuple(tuple(map(Q,p)) for p in ((0,0,0,0),(1,0,0,0),(0,1,0,0),(0,0,1,0),(0,0,0,1),(1,2,-1,3),(-2,1,3,-1)))
ECOEFF=((1,2,0,1,2),(-1,0,2,1,3),(0,1,1,-1,1))
HCOEFF=((0,1,-1,1,2),(2,0,1,0,-1),(1,-1,0,2,3))
def values(rows,p):return tuple(dot(row[:4],p)+row[4] for row in rows)

def memo_field(field,s):
    # Memoize only evaluated native values, keyed by all four exact coordinates.
    # This does not replace the native transform by the expected-value oracle.
    @lru_cache(None)
    def value(a,point):return s['r'](field(a)(*[s['c'](x) for x in point]))
    return FunctionValue(('individual',),TAU,lambda a:FunctionValue(tuple([RS]*4),RS,lambda *xs:s['c'](value(a,tuple(map(s['r'],xs))))))

def setup(name,u=(1,2,2),speed=3):
    cuts,m=numeric_setup(fixture(name)[0]);c,r=cuts.make,cuts.read;m|={n:lambda x=x:x for n,x in CONSTANTS.items()}
    m['shu']=lambda value:c(abs(r(value)))
    vec=lambda xs:vector(c,tuple(map(Q,xs)));pv=lambda p:tuple(r(p(a)) for a in AXES)
    u=tuple(map(Q,u));speed=Q(speed);beta=Q(1) if speed==0 else Q(5,4);old=POINTS[5];new=boost(old,u,beta=beta)
    def field(rows):return FunctionValue(('individual',),TAU,lambda a:FunctionValue(tuple([RS]*4),RS,lambda *xs:c(values(rows,tuple(map(r,xs)))[AXES.index(a)] if a in AXES[:3] else 0)))
    E,H=field(ECOEFF),field(HCOEFF);reg=FunctionValue(tuple([RS]*4),'truth',lambda *xs:r(xs[0])>=0)
    def converted(p):
        oldp=boost(p,tuple(-x for x in u),beta=beta)
        return mix(values(ECOEFF,oldp),values(HCOEFF,oldp),u,beta=beta)
    def newfield(which):return FunctionValue(('individual',),TAU,lambda a:FunctionValue(tuple([RS]*4),RS,lambda *xs:c(converted(tuple(map(r,xs)))[which][AXES.index(a)] if a in AXES[:3] else 0)))
    newE,newH=newfield(0),newfield(1)
    newreg=FunctionValue(tuple([RS]*4),'truth',lambda *xs:boost(tuple(map(r,xs)),tuple(-x for x in u),beta=beta)[0]>=0)
    response=FunctionValue((PS,RS),PS,lambda p,amount:vec(tuple(r(amount)*x for x in converted(pv(p))[0])))
    mapping=FunctionValue((PS,),PS,lambda p:vec(boost(pv(p),u,beta=beta)))
    def one(x):
        if isinstance(x,DescriptionValue):return json.loads(x.syntax).get('symbol')
        if not isinstance(x,FunctionValue):return x
        if x.parameters==('number',):return r(x)
        if x.parameters==('individual',) and x.result==RS:return pv(x)
        if x.parameters==('individual',):return tuple(r(x(a)(*[c(t) for t in p])) for p in POINTS for a in AXES[:3])
        if x.parameters==tuple([RS]*4):return tuple(x(*[c(t) for t in p]) for p in POINTS)
        if x.parameters==(PS,):return tuple(pv(x(vec(p))) for p in POINTS)
        if x.parameters==(PS,RS):return tuple(pv(x(vec(p),c(q))) for p in (old,new) for q in (-1,0,1))
        raise ValueError('Unknown comoving fixture function')
    norm=lambda xs:tuple(one(x) for x in xs);rel=lambda rows:lambda *xs:norm(xs) in rows
    m|={'tc':lambda:c(5),'zpj':lambda:vec(old),'znl':lambda:E,'znm':lambda:H,'znk':lambda:reg}
    fields=('carrier','comoving','event','chargerecord','forcerecord','chargeunit','fieldunit','forceunit','length','duration',vec(new),newE,newH,newreg,vec(converted(new)[0]),'case',response)
    rows={'ejm2':{norm(('frame','comoving','case',*[c(x) for x in u]))},'ejsl':{(f,'length','duration','case') for f in ('frame','comoving')},'eisqt':{norm(('frame','comoving','length','duration',mapping,'case'))},'ejwr':{norm(('carrier','comoving','event',vec(new),'case'))},'eispn':{norm(('process',f,e,h,region,'case')) for f,e,h,region in [('frame',E,H,reg),('comoving',newE,newH,newreg)]},'ejwt':{norm(fields)}}
    m|={n:rel(rs) for n,rs in rows.items()}
    return dict(c=c,r=r,m=m,vec=vec,pv=pv,u=u,uv=vec(u),speed=c(speed),old=old,new=new,E=E,H=H,reg=reg,newE=newE,newH=newH,newreg=newreg,response=response,mapping=mapping,norm=norm,rel=rel,rows=rows,fields=fields,args=[vec(u),c(speed),'comoving','chargerecord','forcerecord','fieldunit',response,'case'])

@lru_cache(None)
def boost_checks():
    cases=0
    for u in ((3,0,0),(-3,0,0),(0,3,0),(0,0,-3),(1,2,2),(2,-1,2),(-2,-2,1),(0,0,0)):
        speed=0 if not any(u) else 3;s=setup('ejym',u,speed);args=[s['c'](5),s['speed'],s['uv']]
        for p in POINTS:
            out=run('ejym',args+[s['vec'](p)],s['m']);actual=s['pv'](out);expected=boost(p,u,beta=Q(1) if speed==0 else Q(5,4));assert actual==expected;cases+=1
            back=run('ejym',[s['c'](5),s['speed'],s['vec']([-x for x in u]),out],s['m']);assert s['pv'](back)==p;cases+=1
            assert 25*actual[3]**2-dot(actual[:3],actual[:3])==25*p[3]**2-dot(p[:3],p[:3]);cases+=1
    s=setup('ejyk')
    for speed,u,want in [(3,(1,2,2),True),(-3,(1,2,2),False),(2,(1,2,2),False),(0,(0,0,0),True),(5,(3,4,0),False)]:
        assert run('ejyk',[s['c'](5),s['c'](speed),s['vec'](u)],s['m'])==want;cases+=1
    for signed in (-3,3):
        s=setup('s46',(signed,0,0));m=s['m']
        for p in POINTS:
            old=run('s46',[s['c'](5),s['c'](signed),s['vec'](p)],m)
            new=run('ejym',[s['c'](5),s['c'](3),s['uv'],s['vec'](p)],m)
            assert s['pv'](old)==s['pv'](new);cases+=1
    return dict(cases=cases,arbitrary_direction_signed_velocity_and_zero_limit=True,native_inverse_and_spacetime_interval=True,existing_standard_x_transform_agrees=True,nonnegative_speed_bound_to_three_velocity_components=True)

@lru_cache(None)
def field_checks():
    cases=0
    for u in ((3,0,0),(-3,0,0),(0,3,0),(0,0,-3),(1,2,2),(-2,-2,1),(0,0,0)):
        speed=0 if not any(u) else 3;s=setup('ejyp',u,speed);args=[s['c'](5),s['speed'],s['uv'],s['E'],s['H']]
        for p in POINTS:
            # Returned functions retain their evaluator's step counter. Give
            # each point a fresh evaluator, preserving the bounded native check.
            newE=memo_field(run('ejyp',args,s['m']),s);newH=memo_field(run('ejyq',args,s['m']),s);newreg=run('ejyr',args[:3]+[s['reg']],s['m'])
            inverse=[s['c'](5),s['speed'],s['vec']([-x for x in u]),newE,newH]
            restoredE=run('ejyp',inverse,s['m']);restoredH=run('ejyq',inverse,s['m'])
            xs=[s['c'](x) for x in p]
            for actual,expected,restored,original in [(newE,s['newE'],restoredE,s['E']),(newH,s['newH'],restoredH,s['H'])]:
                assert tuple(s['r'](actual(a)(*xs)) for a in AXES[:3])==tuple(s['r'](expected(a)(*xs)) for a in AXES[:3]);cases+=1
                assert tuple(s['r'](restored(a)(*xs)) for a in AXES[:3])==tuple(s['r'](original(a)(*xs)) for a in AXES[:3]);cases+=1
            assert newreg(*xs)==s['newreg'](*xs);cases+=1
    for signed in (-3,3):
        s=setup('s6k',(signed,0,0));oldargs=[s['c'](5),s['c'](signed),s['E'],s['H']];args=[s['c'](5),s['c'](3),s['uv'],s['E'],s['H']]
        for oldname,newname in [('s6k','ejyp'),('s6l','ejyq')]:
            old=run(oldname,oldargs,s['m']);new=run(newname,args,s['m'])
            assert s['norm']((old,))==s['norm']((new,));cases+=1
    s=setup('ejyp');atnew=[s['c'](x) for x in s['new']];atold=[s['c'](x) for x in s['old']]
    actual=run('ejyp',[s['c'](5),s['speed'],s['uv'],s['E'],s['H']],s['m'])
    assert tuple(s['r'](actual(a)(*atnew)) for a in AXES[:3])!=tuple(s['r'](s['E'](a)(*atold)) for a in AXES[:3]);cases+=1
    return dict(cases=cases,both_fields_mixed_and_inverse_coordinates_evaluated=True,native_field_inverse_and_region_pullback=True,standard_six_component_formulas_agree=True,untransformed_old_force_not_copied=True,rational_cut_fixtures_only=True)

@lru_cache(None)
def physical_checks():
    s=setup('ejys');rows={n:s['rows'][n] for n in ('ejm2','ejsl','eisqt')};args=[s['uv'],s['speed'],'comoving','case']
    cases=perturb(lambda mm:run('ejys',args,mm),s['m'],rows,s['norm'])
    for i in range(4):
        bad=list(args);bad[i]=s['vec']((2,1,2)) if i==0 else s['c'](0) if i==1 else 'other'
        assert not run('ejys',bad,s['m']);cases+=1
    s=setup('ejyu');rows={n:s['rows'][n] for n in ('ejwr','eispn','ejwt')};m=s['m'];cases+=perturb(lambda mm:run('ejyu',s['args'],mm),m,rows,s['norm'])
    for i in range(len(CURRENT)):
        bad=list(s['args']);bad[i]=s['vec']((2,1,2)) if i==0 else s['c'](0) if i==1 else FunctionValue((PS,RS),PS,lambda *xs:s['vec']((99,99,99))) if i==6 else 'other'
        assert not run('ejyu',bad,m),i;cases+=1
    for n in ('zol','zpo','zou','zot'):
        assert not run('ejyu',s['args'],m|{n:lambda:'other'});cases+=1
    assert not run('ejyu',s['args'],m|{'zpj':lambda:s['vec']((9,8,7,6))});cases+=1
    assert run('ejyu',s['args'],m|{n:forbidden for n in ('zpl','zpm','zb7','zbm','zpk','zpa','xm')});cases+=1
    return dict(cases=cases,whole_frame_motion_and_physical_chart_correspondence=True,same_process_and_instantaneous_rest=True,all_current_force_units_records_and_response_slots_checked=True,old_fixed_k_and_force_values_not_required=True,prior_physical_motion_rest_and_force_definitions_are_explicit_boundaries=True)

@lru_cache(None)
def quantifier_checks():
    cases=0
    for selected,result in product(product((False,True),repeat=2),repeat=2):
        m={'ejyb':lambda u,ctx:selected[('a','b').index(u)] and ctx=='case','ejyv':lambda u,ctx:result[('a','b').index(u)] and ctx=='case'}
        assert run('ejyw',[],m,'witness',('a','b'))==all(not a or b for a,b in zip(selected,result));cases+=1
    patterns=[('a',)*6,('b',)*6]+[tuple('b' if i==j else 'a' for i in range(6)) for j in range(6)]
    for ws in patterns:
        target=('a',*ws,'case');m={'ejys':lambda *xs,ws=ws:xs==('a',ws[0],ws[1],'case'),'ejyu':lambda *xs,target=target:xs==target}
        assert run('ejyv',['a','case'],m,'witness',('a','b'));cases+=1
        for i in range(len(target)):
            bad=target[:i]+('unavailable',)+target[i+1:]
            assert not run('ejyv',['a','case'],m|{'ejyu':lambda *xs,bad=bad:xs==bad},'witness',('a','b'));cases+=1
        assert not run('ejyv',['a','case'],m|{'ejys':lambda *xs:False},'witness',('a','b'));cases+=1
    unknowns(lambda mm:run('ejyv',['a','case'],mm,'witness',('a','b')),m,('ejys','ejyu'))
    s=setup('ejyv')
    try:run('ejyv',[s['uv'],'case'],s['m'])
    except ValueError as e:assert 'rational number domain' in str(e) or 'Finite function domain' in str(e),str(e)
    else:raise AssertionError('All-real comoving speed or response witnesses silently sampled')
    return dict(cases=cases,all_velocity_candidates_and_same_six_witnesses=True,every_witness_and_free_slot_distinguished=True,two_value_diagnostic_only=True,full_function_domain_refused=True)

@lru_cache(None)
def presentation_checks():
    rows={'uh':{('second','author','ejyw','scope','case')},'eisqr':{('first','second','scope','case')},'eislk':{('second','intro',Q(2),'paper','case')}}
    m={n:relation(rs) for n,rs in rows.items()};cases=perturb(lambda mm:run('ejyx',[],mm),m,rows)
    assert run('ejyx',[],m|{'ejyw':forbidden});cases+=1
    rows={'eir3':{('second','author','paper','ejyz','case')},'ue':{('first','second','case')}}
    cases+=perturb(lambda mm:run('ejy2',[],mm),{n:relation(rs) for n,rs in rows.items()},rows)
    return dict(cases=cases,same_author_order_second_item_and_new_wording=True,quoted_law_not_executed=True)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));u=inv['units'][174];assert u['id']=='einstein-1905:u0175' and digest(u['text'].encode())==u['text_sha256'] and not u['math_ids']
    starts=[0]+[u['text'].index(t) for t in ('so ist','welche man','(Neue')];ends=starts[1:]+[len(u['text'])]
    clauses=[dict(range=[a,b],text=u['text'][a:b]) for a,b in zip(starts,ends)];assert ''.join(c['text'] for c in clauses)==u['text']
    return dict(status='complete_second_wording_source_collation_not_automatic_equivalence',unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],text=u['text'],math=[],clauses=clauses,source_nonblank_characters=len(re.sub(r'\s','',u['text'])),observations=['原刊910頁の第二項全体を読む。条件、力とその対象の場所の電気側の場との等値、対象に相対静止する系への場の変換、新しい言い方を保持する。','前段の少なくとも当該瞬間という静止条件を共有し、対象が加速する場合でも瞬間の共動系を選べる読みを採る。','任意方向に対し同じ向きの軸と共通原点を選ぶ純粋boostの代表を構成する。Kでの力の数値を新系へ無条件にコピーしない。'],remaining=['全単位判断は別の記録で行う','u0176以降と二作品全体は未完'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in (INVENTORY,DOC,FACSIMILE)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert len(new.document['statements'])==360 and [i for i,(a,b) in enumerate(zip(old.document['statements'],new.document['statements'])) if a!=b]==[INDEX]
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    assert selection_binding(new,[163,164,165,166,167,358,359])==selection_binding(old,[163,164,165,166,167,358,359])
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);names=set(selection_binding(new,[INDEX])['dependencies'])
    assert set(MEANINGS)|{'eisqt','ejm2','ejwr','ejwt','eispn','ejyb','sci2'}<=names
    assert not names&{'ejxo','ejxp','ejxr','scp2','xm','zpa','zpl','zpm','zbm','zb7','zpk'}
    core=parse(read(CORE))
    for style in ('compact','full'):
        b=format_graph(core,style);assert parse(b)==parse(transcribe(b,alphabet='v2'))==core
    assert json.loads(json.dumps(source_record(),ensure_ascii=False))==json.loads(read(SOURCE))
    return dict(new_definitions=len(MEANINGS),new_general_relations=1,new_references=0,replaced_statement=INDEX,other_359_statements_and_judgments_preserved=True,semantic_judgment_separate=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('boost',boost_checks),('field',field_checks),('physical',physical_checks),('quantifier',quantifier_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    helpers=('compose_vacuum_field_domain','compose_material_relative_frame','compose_relativity_conjecture','compose_two_postulates','compose_field_equations','compose_field_transform','compose_force_wordings','compose_rest_force','compose_resting_charge_force','compose_moving_field_definition','compose_limits','check_coordinate_correspondence','check_clock_site_time','check_resting_charge_force','check_total_differential','check_force_motion_binding','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,*DEPENDENCIES,'scripts/compose_comoving_wording.py','scripts/check_comoving_wording.py','tests/test_comoving_wording.py',*(f'scripts/{n}.py' for n in helpers)}
    s=source_record();row=dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],statements=[INDEX],definitions=list(MEANINGS),status='explicit_interpretive_annotation')
    return dict(status='arbitrary_direction_comoving_force_wording_checked',document=FULL,**results,alignment=dict(segments=[row]),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
