"""Check magnetic old/new wordings without asserting isolated poles exist."""
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
from scripts.check_comoving_wording import setup as base_setup,AXES,POINTS,cross
from scripts.check_electromotive_wording import setup as electric_setup
from scripts.compose_magnetomotive_wording import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,PARENT_BASIS,INDEX,MEANINGS,LOCAL,HISTORY,OLD,OLD_WITNESSES,NEW,NEW_WITNESSES,build

DOC='docs/magnetomotive-wording-v1.md';SOURCE='data/einstein-magnetomotive-wording-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';FACSIMILE='artifacts/written-facsimiles-v1/einstein-1905-unlp-p910-0.jpg'
DEPENDENCIES=('reports/comoving-wording-v1.json','reports/electromotive-wording-v1.json','reports/moving-field-definition-v1.json','reports/force-motion-binding-v1.json','reports/resting-charge-force-v1.json')
CONSTANTS={'ri':'case','rd':'author','eirf':'paper','zno':'scope','ra':'frame','zor':'chargekind','eisps':'polekind','zpn':'forcekind','zot':'forceunit','ta':'length','rb':'duration','zpr':'second','zps':'analogy','eisqv':'magterm','eispp':'process',**dict(zip(('yn','yo','yp','zc7'),AXES))}
DOMAIN=tuple(dict.fromkeys((*CONSTANTS.values(),'carrier','event','poleunit','amountrecord','newamountrecord','electricunit','magneticunit','fieldunit','baserecord','totalrecord','extrarecord','forcerecord','comoving','a','b','other')))
SITUATIONS=('case','other')
BOUNDS={'seoc','ejsl','ejsy','ejts','ejys','ejwr','ejym','ejyp','ejyq','ejyr'}

@lru_cache(None)
def fixture(name,mode='native'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    bounds=OPERATIONS|BOUNDS
    if mode!='full':bounds.add('svy')
    if mode=='witness':bounds|={'ejy4':{'ejy3','ejsj'},'ejy7':{'ejy6','ejzi'},'ejzb':{'ejza'},'ejzc':{'ejy4','ejy7','ejzb'}}[name]
    if name=='ejzi':bounds.add('ejy5')
    if name=='ejzd':bounds.add('ejy4')
    abstract(doc,bounds);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    if mode=='instance':
        d=next(d for d in doc['declarations'] if d['name']==name)
        old=next(d for d in doc['declarations'] if d['name']=='ejy6')['parameters']
        for parameter in old[:6]+old[7:]:
            node=d['body'];assert node['kind']=='exists' and node['sort']==parameter['sort']
            d['parameters'].append(dict(name=node['variable'],sort=node['sort']));d['body']=node['body']
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
        n='jmmw'+number_word(i);slots.append((n,p['sort']));doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
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
    return evaluate_document(doc,individuals=domain,situations=SITUATIONS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=900000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def setup():
    s=base_setup('ejyu');c,r,vec,pv=s['c'],s['r'],s['vec'],s['pv'];m=s['m']|{n:lambda x=x:x for n,x in CONSTANTS.items()}
    old=s['old'];new=s['new'];point=vec(old);velocity=s['uv'];zero=vec((0,0,0))
    def at(field,p):return tuple(r(field(a)(*[c(x) for x in pv(p)])) for a in AXES[:3])
    static=FunctionValue((PS,RS),PS,lambda p,q:vec(tuple(r(q)*x for x in at(s['H'],p))))
    newstatic=FunctionValue((PS,RS),PS,lambda p,q:vec(tuple(r(q)*x for x in at(s['newH'],p))))
    def force(p,amount,u):
        uv=pv(u)[:3];extra=cross(uv,at(s['E'],p));square=sum(x*x for x in uv)/25
        return vec(tuple(r(amount)*(a-b/5+(i+1)*square) for i,(a,b) in enumerate(zip(at(s['H'],p),extra))))
    dynamic=FunctionValue((PS,RS,PS),PS,force)
    times=FunctionValue((RS,),'truth',lambda t:Q(2)<r(t)<Q(4))
    curve=FunctionValue((RS,),PS,lambda t:vec(tuple(old[i]+s['u'][i]*(r(t)-old[3]) for i in range(3))+(r(t),)))
    def one(x):
        if isinstance(x,DescriptionValue):return json.loads(x.syntax).get('symbol')
        if not isinstance(x,FunctionValue):return x
        if x.parameters==('number',):return r(x)
        if x.parameters==('individual',) and x.result==RS:return pv(x)
        if x.parameters==('individual',):return tuple(r(x(a)(*[c(t) for t in p])) for p in (old,new,POINTS[0]) for a in AXES[:3])
        if x.parameters==tuple([RS]*4):return tuple(x(*[c(t) for t in p]) for p in (old,new,POINTS[0]))
        if x.parameters==(PS,RS):return tuple(pv(x(vec(p),c(q))) for p in (old,new) for q in (-1,0,1))
        if x.parameters==(PS,RS,PS):return tuple(pv(x(vec(p),c(q),vec(u))) for p in (old,new) for q in (-1,0,1) for u in ((0,0,0),(1,2,2),(2,-1,2)))
        if x.parameters==(RS,):return tuple(pv(x(c(t))) if x.result==PS else x(c(t)) for t in (2,3,4))
        raise ValueError('Unexpected magnetic fixture function')
    norm=lambda xs:tuple(one(x) for x in xs);rel=lambda rows:lambda *xs:norm(xs) in rows
    local=['carrier','event','poleunit','amountrecord',point,velocity,'case']
    oldargs=local+[dynamic,static,'electricunit','magneticunit','baserecord','totalrecord','extrarecord']
    newargs=local+[c(3),'comoving','newamountrecord','fieldunit','forcerecord',newstatic]
    base=vec(at(s['H'],point));total=dynamic(point,c(1),velocity);extra=vec(tuple(a-b for a,b in zip(pv(total)[:3],pv(base)[:3])));newforce=vec(at(s['newH'],vec(new)))
    rows={
        'ejsl':{('frame','length','duration','case')},
        'eisqd':{norm(('carrier',f,'event','length','duration',p,'case')) for f,p in [('frame',point),('comoving',vec(new))]},
        'zof':{('poleunit','polekind',Q(1),'case')},
        'zog':{(rec,'carrier','polekind',f,'event','poleunit',Q(1),'case') for rec,f in [('amountrecord','frame'),('newamountrecord','comoving')]},
        'seoc':{norm(('carrier','frame','case',times,curve,'event',point,*[c(x) for x in s['u']]))},
        'eisqp':{norm(('polekind','frame','length','duration','poleunit','forceunit',s['E'],s['H'],s['reg'],'case',dynamic))},
        'ejts':{norm(('polekind',f,'length','duration','poleunit','forceunit',reg,'case',response,fu,c(1),field)) for f,reg,response,fu,field in [('frame',s['reg'],static,'magneticunit',s['H']),('comoving',s['newreg'],newstatic,'fieldunit',s['newH'])]},
        'eirn':{norm(('frame',s['E'],'electricunit','case'))},
        'eispu':{norm(('polekind','poleunit','electricunit','forceunit',c(1),'case'))},
        'zpc':{norm((record,'carrier','forcekind',frame,'event','forceunit',value,'case')) for record,frame,value in [('baserecord','frame',base),('totalrecord','frame',total),('extrarecord','frame',extra),('forcerecord','comoving',newforce)]},
        'ejys':{norm((velocity,c(3),'comoving','case'))},
        'ejwr':{norm(('carrier','comoving','event',vec(new),'case'))},
        'eispn':{norm(('process',f,e,h,reg,'case')) for f,e,h,reg in [('frame',s['E'],s['H'],s['reg']),('comoving',s['newE'],s['newH'],s['newreg'])]},
    }
    m|={n:rel(rs) for n,rs in rows.items()}
    m['zrdpointlike']=lambda:FunctionValue(('individual','situation'),'truth',lambda obj,ctx:(obj,ctx)==('carrier','case'))
    observed=[]
    def transform(name,args,value):observed.append((name,norm(args)));return value
    m|={'ejym':lambda *xs:transform('ejym',xs,vec(new)),'ejyp':lambda *xs:transform('ejyp',xs,s['newE']),'ejyq':lambda *xs:transform('ejyq',xs,s['newH']),'ejyr':lambda *xs:transform('ejyr',xs,s['newreg'])}
    return s|dict(m=m,norm=norm,rel=rel,rows=rows,local=local,oldargs=oldargs,newargs=newargs,history=local+[times,curve],dynamic=dynamic,static=static,newstatic=newstatic,base=base,total=total,extra=extra,newforce=newforce,observed=observed)

@lru_cache(None)
def motion_checks():
    s=setup();rows={n:s['rows'][n] for n in ('ejsl','eisqd','zof','zog','seoc')}
    rows['eisqd']={row for row in rows['eisqd'] if row[1]=='frame'};rows['zog']={row for row in rows['zog'] if row[3]=='frame'}
    cases=perturb(lambda mm:run('ejy3',s['history'],mm),s['m'],rows,s['norm'])
    assert not run('ejy3',s['history'],s['m']|{'zrdpointlike':lambda:FunctionValue(('individual','situation'),'truth',lambda *xs:False)});cases+=1
    for i in range(len(HISTORY)):
        bad=list(s['history']);bad[i]='other' if HISTORY[i][1] in ('a','d') else s['vec']((0,0,0,0)) if i in (4,5) else FunctionValue((RS,),PS,lambda t:s['vec']((99,99,99,99))) if i==8 else FunctionValue((RS,),'truth',lambda t:False)
        assert not run('ejy3',bad,s['m']),i;cases+=1
    assert run('ejy3',s['history'],s['m']|{n:forbidden for n in ('eisqc','zol','zou','ejxm')});cases+=1
    return dict(cases=cases,same_pole_kind_unit_value_motion_and_point=True,all_history_slots_checked=True,previous_native_derivative_body_is_pinned_boundary=True,no_fixed_electric_carrier_required=True)

@lru_cache(None)
def approximation_checks():
    cases=0
    for u,e in [((1,0,0),(2,1,3)),((0,-2,0),(2,1,3)),((0,0,3),(2,1,3)),((1,-2,2),(2,1,3)),((-1,2,-2),(0,0,0)),((1,2,2),(2,4,4))]:
        for quadratic,cubic in [((0,0,0),(0,0,0)),((2,-3,4),(0,0,0)),((2,-3,4),(1,0,-2))]:
            s=electric_setup('ejx6',u,tuple(-x for x in e),quadratic,cubic);args=s['approx'][:];args[2]=s['vec'](e)
            assert run('ejy5',args,s['m']);assert len(s['observations'])==3;cases+=1
    for axis in range(3):
        bad=[0,0,0];bad[axis]=1
        for kw in ({'wrong_linear':bad},{'offset':bad}):
            s=electric_setup('ejx6',magnetic=(-2,-1,-3),**kw);args=s['approx'][:];args[2]=s['vec']((2,1,3));assert not run('ejy5',args,s['m']);cases+=1
    s=electric_setup('ejx6',magnetic=(2,1,3));assert not run('ejy5',s['approx'],s['m']);cases+=1
    unknowns(lambda mm:run('ejy5',s['approx'],mm),s['m'],('svy',))
    try:run('ejy5',s['approx'],s['m'],'full')
    except ValueError as e:assert 'rational number domain' in str(e) or 'Finite function domain' in str(e),str(e)
    else:raise AssertionError('All-real magnetic asymptotic domain silently sampled')
    return dict(cases=cases,negative_cross_product_all_directions=True,second_and_third_order_errors_allowed=True,every_constant_and_linear_component_error_rejected=True,polynomial_fixtures_not_general_asymptotic_proof=True,full_function_domain_refused=True)

@lru_cache(None)
def force_checks():
    s=setup();rows={n:s['rows'][n] for n in ('eisqp','ejts','eirn','eispu','zpc')};rows['ejts']={row for row in rows['ejts'] if row[1]=='frame'};rows['zpc']={row for row in rows['zpc'] if row[3]=='frame'}
    cases=perturb(lambda mm:run('ejy6',s['oldargs'],mm),s['m'],rows,s['norm'])
    for i in range(7,len(OLD)):
        bad=s['oldargs'][:];bad[i]='other' if OLD[i][1]=='a' else FunctionValue((PS,RS,PS) if i==7 else (PS,RS),PS,lambda *xs:s['vec']((99,99,99)))
        assert not run('ejy6',bad,s['m']),i;cases+=1
    for i in range(3):
        changed=list(s['pv'](s['extra'])[:3]);changed[i]+=1
        good=s['norm'](('extrarecord','carrier','forcekind','frame','event','forceunit',s['extra'],'case'));bad=s['norm'](('extrarecord','carrier','forcekind','frame','event','forceunit',s['vec'](changed),'case'))
        assert not run('ejy6',s['oldargs'],s['m']|{'zpc':s['rel'](s['rows']['zpc']-{good}|{bad})});cases+=1
    assert run('ejy6',s['oldargs'],s['m']|{'svy':forbidden,'ejy5':forbidden});cases+=1
    wanted=s['norm']((s['c'](5),s['uv'],s['vec'](tuple(s['r'](s['E'](a)(*[s['c'](x) for x in s['old']])) for a in AXES[:3])),s['base'],s['vec'](s['old']),s['dynamic']))
    assert run('ejzi',s['local']+[s['dynamic']],s['m']|{'ejy5':lambda *xs:s['norm'](xs)==wanted});cases+=1
    roleargs=[s['extra'],'case']+s['local'][:-1]+s['oldargs'][7:]
    rolemodel=s['m']|{'ejy4':lambda *xs:s['norm'](xs)==s['norm'](s['local']),'svy':forbidden,'ejy5':forbidden}
    # Instantiate every named existential once with the physical witnesses;
    # this checks the native body, not existence over the whole function domain.
    assert run('ejzd',roleargs,rolemodel,'instance');cases+=1
    assert not run('ejzd',[s['base']]+roleargs[1:],rolemodel,'instance');cases+=1
    return dict(cases=cases,same_pole_static_dynamic_residual_and_three_records=True,all_old_response_units_and_record_arguments_checked=True,physical_role_does_not_assume_approximation=True)

@lru_cache(None)
def comoving_checks():
    s=setup();rows={n:s['rows'][n] for n in ('ejys','ejwr','eisqd','zof','zog','eispn','ejts','zpc')}
    rows['eisqd']={row for row in rows['eisqd'] if row[1]=='comoving'};rows['zog']={row for row in rows['zog'] if row[3]=='comoving'};rows['ejts']={row for row in rows['ejts'] if row[1]=='comoving'};rows['zpc']={row for row in rows['zpc'] if row[3]=='comoving'}
    cases=perturb(lambda mm:run('ejza',s['newargs'],mm),s['m'],rows,s['norm'])
    expected={'ejym':s['norm']((s['c'](5),s['c'](3),s['uv'],s['vec'](s['old']))),'ejyp':s['norm']((s['c'](5),s['c'](3),s['uv'],s['E'],s['H'])),'ejyq':s['norm']((s['c'](5),s['c'](3),s['uv'],s['E'],s['H'])),'ejyr':s['norm']((s['c'](5),s['c'](3),s['uv'],s['reg']))}
    assert all(xs==expected[n] for n,xs in s['observed']) and set(n for n,_ in s['observed'])==set(expected);cases+=1
    assert not run('ejza',s['newargs'],s['m']|{'ejyq':lambda *xs:s['H']});cases+=1
    assert not run('ejza',s['newargs'],s['m']|{'ejym':lambda *xs:s['vec'](s['old'])});cases+=1
    assert run('ejza',s['newargs'],s['m']|{n:forbidden for n in ('zpl','zpm','zol','zou','zbm','ejwt')});cases+=1
    return dict(cases=cases,physical_boost_and_same_pole_instantaneous_rest=True,same_new_amount_record_and_force=True,both_transformed_fields_same_inverse_region_and_point=True,previous_native_transform_and_static_field_definitions_are_pinned_boundaries=True)

@lru_cache(None)
def quantifier_checks():
    cases=0;local=['a']*6+['case']
    for name,callee,ws_count in [('ejy4','ejy3',2),('ejy7','ejy6',7),('ejzb','ejza',6)]:
        patterns=[('a',)*ws_count,('b',)*ws_count]+[tuple('b' if i==j else 'a' for i in range(ws_count)) for j in range(ws_count)]
        for ws in patterns:
            target=tuple(local)+ws;m={callee:lambda *xs,target=target:xs==target,'ejsy':lambda *xs:True,'ejsj':lambda *xs:True,'ejy5':lambda *xs:True,'znl':lambda:'a','znm':lambda:'a','tc':lambda:'a','znk':lambda:'a'}
            # Quantifier diagnostics abstract the numeric point evaluation below.
            if name=='ejy7':m|={'ejzi':lambda *xs,ws=ws:xs==tuple(local)+(ws[0],)}
            assert run(name,local,m,'witness',('a','b'));cases+=1
            for i in range(len(target)):
                bad=target[:i]+('unavailable',)+target[i+1:]
                assert not run(name,local,m|{callee:lambda *xs,bad=bad:xs==bad},'witness',('a','b'));cases+=1
    for slot in range(6):
        target=tuple('b' if i==slot else 'a' for i in range(6))+('case',)
        for old,new in product((False,True),repeat=2):
            m={'ejy4':lambda *xs,target=target:xs==target,'ejy7':lambda *xs,old=old:old,'ejzb':lambda *xs,new=new:new}
            assert run('ejzc',[],m,'witness',('a','b'))==(old and new);cases+=1
    s=setup()
    for name in ('ejy4','ejy7','ejzb'):
        try:run(name,s['local'],s['m'])
        except ValueError as e:assert 'rational number domain' in str(e) or 'Finite function domain' in str(e),str(e)
        else:raise AssertionError('Magnetic witnesses silently sampled')
    return dict(cases=cases,every_old_new_witness_and_free_slot_checked=True,both_analogous_wordings_required_for_each_pole_motion=True,two_value_diagnostic_only=True,full_native_function_domain_refused=True)

@lru_cache(None)
def presentation_checks():
    rows={'uh':{('analogy','author','ejzc','scope','case')},'eisqu':{('analogy','author','ejze','ejzc','scope','case')},'eisqq':{('magterm','ejzd','analogy','paper','case')}}
    m={n:relation(rs) for n,rs in rows.items()};cases=perturb(lambda mm:run('ejzf',[],mm),m,rows)
    assert run('ejzf',[],m|{n:forbidden for n in ('ejzc','ejze','ejzd')});cases+=1
    rows={'eir3':{('analogy','author','paper','ejzg','case')},'ue':{('second','analogy','case')}}
    cases+=perturb(lambda mm:run('ejzh',[],mm),{n:relation(rs) for n,rs in rows.items()},rows)
    return dict(cases=cases,author_analogy_source_target_and_quoted_term=True,quotation_not_execution=True)

@lru_cache(None)
def source_record():
    u=json.loads(read(INVENTORY))['units'][175];assert u['id']=='einstein-1905:u0176' and digest(u['text'].encode())==u['text_sha256']
    end=u['text'].index(' Man sieht');text=u['text'][:end]
    return dict(status='magnetic_analogy_first_sentence_connected_unit_not_complete',unit=u['id'],unit_sha256=u['text_sha256'],range=[0,end],text=text,math=[],source_nonblank_characters=len(re.sub(r'\s','',text)),observations=['原刊910頁の冒頭一文は直前の二つの電気側の言い表しへの磁気側の類推。静止磁気基準、負の外積による一次追加、共動系の変換後磁気側の場と同系の力を対応させる。','点状単位磁極は仮定上の試験系として条件文に置き、孤立磁荷の実在を前提にしない。'],remaining=['u0176後半の補助概念だけの役割、系依存性による導入理由、Man siehtの提示と全単位通読判断','u0177以降と二作品全体'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in (INVENTORY,FACSIMILE,DOC)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert len(new.document['statements'])==360 and [i for i,(a,b) in enumerate(zip(old.document['statements'],new.document['statements'])) if a!=b]==[INDEX]
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    assert selection_binding(new,[167,168])==selection_binding(old,[167,168])
    load_annotations(ROOT,BASIS,ANNOTATIONS)
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    names=set(selection_binding(new,[INDEX])['dependencies']);assert set(MEANINGS)|{'eisps','eisqp','ejts','ejys','ejwr','ejyq','scq2','eisqu','eisqq'}<=names
    core=parse(read(CORE))
    for style in ('compact','full'):
        b=format_graph(core,style);assert parse(b)==parse(transcribe(b,alphabet='v2'))==core
    assert json.loads(read(SOURCE))==json.loads(json.dumps(source_record(),ensure_ascii=False))
    return dict(new_definitions=len(MEANINGS),new_general_relations=1,new_references=1,other_359_statements_preserved=True,whole_unit_review_not_yet_added=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('motion',motion_checks),('approximation',approximation_checks),('force',force_checks),('comoving',comoving_checks),('quantifier',quantifier_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    helpers=('check_coordinate_correspondence','check_clock_site_time','check_resting_charge_force','check_total_differential','check_comoving_wording','check_electromotive_wording','compose_vacuum_field_domain','compose_material_relative_frame','compose_material_velocity','compose_relativity_conjecture','compose_two_postulates','compose_field_equations','compose_force_wordings','compose_rest_force','compose_moving_field_definition','compose_electromotive_wording','compose_limits','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,*DEPENDENCIES,'scripts/compose_magnetomotive_wording.py','scripts/check_magnetomotive_wording.py','tests/test_magnetomotive_wording.py',*(f'scripts/{n}.py' for n in helpers)}
    s=source_record();row=dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],statements=[INDEX],definitions=list(MEANINGS),status='explicit_interpretive_annotation')
    return dict(status='magnetic_old_and_new_force_wordings_connected',document=FULL,**results,alignment=dict(segments=[row]),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
