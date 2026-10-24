"""Check physical realizations and non-invariant electric/magnetic presence."""
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
from scripts.check_clock_site_time import relation,perturb,unknowns,forbidden
from scripts.check_resting_charge_force import retag,RS,PS,TAU
from scripts.check_total_differential import OPERATIONS
from scripts.check_comoving_wording import setup as base_setup,mix,AXES
from scripts.compose_physical_field_dependence import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,PARENT_BASIS,INDEX,MEANINGS,CONFIG,UNITS,RESPONSES,PAIR,COMPARE,build

DOC='docs/physical-field-dependence-v1.md';SOURCE='data/einstein-physical-field-dependence-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';FACSIMILE='artifacts/written-facsimiles-v1/einstein-1905-unlp-p910-0.jpg'
DEPENDENCIES=('reports/magnetomotive-wording-v1.json','reports/comoving-wording-v1.json','reports/moving-field-definition-v1.json','reports/field-dependence-v1.json')
CONSTANTS={'ri':'case','rd':'author','eirf':'paper','zno':'scope','zor':'chargekind','eisps':'polekind','eisqw':'theory','zpt':'dependence','zps':'analogy','ta':'length','rb':'duration',**dict(zip(('yn','yo','yp','zc7'),AXES))}
DOMAIN=tuple(dict.fromkeys((*CONSTANTS.values(),'process','frame','comoving','chargeunit','poleunit','electricunit','magneticunit','forceunit','a','b','other')))
SITUATIONS=('case','other')

@lru_cache(None)
def fixture(name,mode='native'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    bounds=OPERATIONS|{'ejts','ejm2','ejsl'}
    if name=='ejzl':bounds|={'ejzk','ejzj','ejym','ejyp','ejyq','ejyr'}
    if name in ('ejzo','ejzp'):bounds|={'ejzn','ejzo'}-{name}
    if mode.startswith('slot:'):bounds|={'ejzl','ejzm'}
    abstract(doc,bounds);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    if mode.startswith('slot:'):
        doc=retag(doc)
        for d in doc['declarations']:
            if d['kind']=='primitive':
                d['parameters']=['individual' if isinstance(s,dict) else s for s in d['parameters']]
                if isinstance(d['result'],dict):d['result']='individual'
            else:
                for p in d['parameters']:
                    if isinstance(p['sort'],dict):p['sort']='individual'
        d=next(d for d in doc['declarations'] if d['name']==name);pivot=int(mode.split(':')[1]);retained=None
        for i in range(len(CONFIG+UNITS+RESPONSES)):
            node=d['body'];assert node['kind']=='exists';d['body']=node['body']
            if i==pivot:retained={k:node[k] for k in ('kind','variable','sort')}
            else:d['parameters'].append(dict(name=node['variable'],sort=node['sort']))
        assert retained is not None;d['body']=retained|{'body':d['body']}
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[]
    for i,p in enumerate(d['parameters']):
        n='jpfd'+number_word(i);slots.append((n,p['sort']));doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
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
    return evaluate_document(doc,individuals=domain,situations=SITUATIONS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=1200000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def setup(e=(0,0,0),h=(0,0,1),u=(3,0,0)):
    s=base_setup('ejyu',u);c,r,vec,pv=s['c'],s['r'],s['vec'],s['pv'];norm=s['norm'];rel=lambda rows:lambda *xs:norm(xs) in rows
    field=lambda xyz:FunctionValue(('individual',),TAU,lambda a:FunctionValue(tuple([RS]*4),RS,lambda *xs:c(xyz[AXES.index(a)] if a in AXES[:3] else 0)))
    er,hr=mix(tuple(map(Q,e)),tuple(map(Q,h)),tuple(map(Q,u)));E,H,newE,newH=map(field,(e,h,er,hr))
    response=lambda xyz:FunctionValue((PS,RS),PS,lambda p,q:vec(tuple(r(q)*x for x in xyz)))
    fe,fm,se,sm=map(response,(e,h,er,hr));units=['chargeunit','poleunit','electricunit','magneticunit','forceunit']
    first=['process','frame',E,H,s['reg'],'case',*units,fe,fm]
    second=['process','comoving',newE,newH,s['newreg'],'case',*units,se,sm]
    pair=['theory','process','frame','comoving',vec(s['old']),s['uv'],c(3),E,H,s['reg'],'case',*units,fe,fm,se,sm]
    rows={
        'znn':{norm((f,e,h,region,'case')) for f,e,h,region in [('frame',E,H,s['reg']),('comoving',newE,newH,s['newreg'])]},
        'eispn':{norm(('process',f,e,h,region,'case')) for f,e,h,region in [('frame',E,H,s['reg']),('comoving',newE,newH,s['newreg'])]},
        'ejts':{norm((kind,f,'length','duration',amount,'forceunit',region,'case',resp,fu,c(1),field)) for f,region,ef,hf,re,rh in [('frame',s['reg'],E,H,fe,fm),('comoving',s['newreg'],newE,newH,se,sm)] for kind,amount,fu,resp,field in [('chargekind','chargeunit','electricunit',re,ef),('polekind','poleunit','magneticunit',rh,hf)]},
        'ejm2':{norm(('frame','comoving','case',*[c(x) for x in u]))},
        'ejsl':{(f,'length','duration','case') for f in ('frame','comoving')},
        'eisqt':{norm(('frame','comoving','length','duration',s['mapping'],'case'))},
        'eisqx':{('theory','process','case')},
        'ejzk':{norm(('frame','comoving',s['uv'],c(3),'case'))},
        'ejzj':{norm(first),norm(second)},
    }
    m=s['m']|{n:lambda x=x:x for n,x in CONSTANTS.items()}|{n:rel(rs) for n,rs in rows.items()};observed=[]
    def transformed(name,args,value):observed.append((name,norm(args)));return value
    m|={'ejym':lambda *xs:transformed('ejym',xs,vec(s['new'])),'ejyp':lambda *xs:transformed('ejyp',xs,newE),'ejyq':lambda *xs:transformed('ejyq',xs,newH),'ejyr':lambda *xs:transformed('ejyr',xs,s['newreg'])}
    return s|dict(m=m,rows=rows,norm=norm,rel=rel,E=E,H=H,newE=newE,newH=newH,first=first,second=second,pair=pair,observed=observed)

@lru_cache(None)
def realization_checks():
    s=setup();rows={n:{row for row in s['rows'][n] if row[0 if n=='znn' else 1]=='frame'} for n in ('znn','eispn','ejts')}
    cases=perturb(lambda mm:run('ejzj',s['first'],mm),s['m'],rows,s['norm'])
    assert run('ejzj',s['second'],s['m']);cases+=1
    assert not run('ejzj',s['first'],s['m']|{'eisps':lambda:'chargekind'});cases+=1
    for i in range(6,11):
        args=s['first'][:];args[i]='other';assert not run('ejzj',args,s['m']),i;cases+=1
    return dict(cases=cases,same_process_two_physical_field_kinds=True,all_five_units_and_two_static_responses_bound=True,static_field_definitions_are_prior_pinned_boundary=True)

@lru_cache(None)
def geometry_checks():
    cases=0
    for u in ((3,0,0),(-3,0,0),(0,3,0),(0,0,-3),(1,2,2)):
        s=setup(u=u);args=['frame','comoving',s['uv'],s['c'](3),'case'];assert run('ejzk',args,s['m']);cases+=1
    rows={n:s['rows'][n] for n in ('ejm2','ejsl','eisqt')}
    cases+=perturb(lambda mm:run('ejzk',args,mm),s['m'],rows,s['norm'])
    for i in (0,1,4):
        bad=args[:];bad[i]='other';assert not run('ejzk',bad,s['m']);cases+=1
    bad=args[:];bad[2]=s['vec']((0,0,0));bad[3]=s['c'](0);assert not run('ejzk',bad,s['m']);cases+=1
    return dict(cases=cases,nonzero_arbitrary_direction_relative_motion=True,whole_frame_motion_and_full_coordinate_correspondence=True,rotation_or_units_only_not_used_as_motion=True)

@lru_cache(None)
def pair_checks():
    s=setup();rows={n:s['rows'][n] for n in ('eisqx','ejzk','ejzj')}
    cases=perturb(lambda mm:run('ejzl',s['pair'],mm),s['m'],rows,s['norm'])
    expected={'ejym':s['norm']((s['c'](5),s['c'](3),s['uv'],s['vec'](s['old']))),'ejyp':s['norm']((s['c'](5),s['c'](3),s['uv'],s['E'],s['H'])),'ejyq':s['norm']((s['c'](5),s['c'](3),s['uv'],s['E'],s['H'])),'ejyr':s['norm']((s['c'](5),s['c'](3),s['uv'],s['reg']))}
    assert all(xs==expected[n] for n,xs in s['observed']) and set(n for n,_ in s['observed'])==set(expected);cases+=1
    for field,old in [('ejyp',s['E']),('ejyq',s['H']),('ejyr',s['reg'])]:
        assert not run('ejzl',s['pair'],s['m']|{field:lambda *xs,old=old:old}),field;cases+=1
    for i in (0,1,2,3,10):
        bad=s['pair'][:];bad[i]='other';assert not run('ejzl',bad,s['m']),i;cases+=1
    return dict(cases=cases,theory_allowed_same_process_pair=True,same_event_inverse_fields_and_region_bound=True,same_five_units_and_four_responses=True,native_geometry_and_realization_checked_separately=True)

@lru_cache(None)
def presence_checks():
    cases=0
    for u in ((3,0,0),(-3,0,0),(0,3,0),(1,2,2)):
        for e,h,kind,want in [((0,0,0),(0,0,1),'chargekind',True),((0,0,1),(0,0,0),'polekind',True),((0,0,0),(0,0,1),'polekind',False),((0,0,1),(0,0,0),'chargekind',False),((1,2,3),(2,1,3),'chargekind',False),((0,0,0),(0,0,0),'polekind',False)]:
            s=setup(e,h,u);args=[kind,s['vec'](s['old']),s['uv'],s['c'](3),s['E'],s['H']]
            assert run('ejzm',args,s['m'])==want,(u,e,h,kind);cases+=1
    s=setup(h=(3,0,0));args=['chargekind',s['vec'](s['old']),s['uv'],s['c'](3),s['E'],s['H']]
    assert not run('ejzm',args,s['m']);cases+=1
    args[0]='other';assert not run('ejzm',args,s['m']);cases+=1
    for electric,magnetic in product((False,True),repeat=2):
        m={'ejzn':lambda theory,kind,ctx:theory=='theory' and ctx=='case' and {'chargekind':electric,'polekind':magnetic}[kind]}
        assert run('ejzo',['theory','case'],m)==(electric and magnetic);cases+=1
    return dict(cases=cases,native_electric_and_magnetic_zero_nonzero_witnesses=True,both_nonzero_value_changes_not_sufficient=True,parallel_and_zero_fields_can_remain_unchanged=True,both_kinds_required_but_not_same_process=True)

@lru_cache(None)
def binding_checks():
    witnesses=CONFIG+UNITS+RESPONSES;cases=0
    for pivot,(slot,_) in enumerate(witnesses):
        args=['a','a','case']+['a']*(len(witnesses)-1)
        for value,want in [('a',True),('b',True),('unavailable',False)]:
            values={n:'a' for n,_ in witnesses}|{'theory':'a','kind':'a','context':'case',slot:value}
            pair=tuple(values[n] for n,_ in PAIR);compare=tuple(values[n] for n,_ in COMPARE)
            m={'ejzl':lambda *xs,pair=pair:xs==pair,'ejzm':lambda *xs,compare=compare:xs==compare}
            assert run('ejzn',args,m,'slot:'+str(pivot),('a','b'))==want,slot;cases+=1
        values={n:'a' for n,_ in witnesses}|{'theory':'a','kind':'a','context':'case'};pair=tuple(values[n] for n,_ in PAIR);compare=tuple(values[n] for n,_ in COMPARE)
        m={'ejzl':lambda *xs,pair=pair:xs==pair,'ejzm':lambda *xs,compare=compare:xs==compare}
        for free in range(3):
            bad=args[:];bad[free]='other' if free==2 else 'b';assert not run('ejzn',bad,m,'slot:'+str(pivot),('a','b'));cases+=1
        for callee in ('ejzl','ejzm'):
            assert not run('ejzn',args,m|{callee:lambda *xs:False},'slot:'+str(pivot),('a','b'));cases+=1
    unknowns(lambda mm:run('ejzn',args,mm,'slot:'+str(pivot),('a','b')),m,('ejzl','ejzm'))
    s=setup()
    try:run('ejzn',['theory','chargekind','case'],s['m'])
    except ValueError as e:assert 'rational number domain' in str(e) or 'Finite function domain' in str(e),str(e)
    else:raise AssertionError('Full real field witness domain silently sampled')
    return dict(cases=cases,every_witness_and_three_free_slots_distinguished=True,one_existential_at_a_time_others_explicitly_instantiated=True,two_value_diagnostic_not_whole_domain_proof=True,full_native_function_domain_refused=True)

@lru_cache(None)
def presentation_checks():
    rows={'eisqy':{('theory','paper','eigj','scope','case')},'ejzo':{('theory','case')}}
    cases=perturb(lambda mm:run('ejzp',[],mm),{n:relation(rs) for n,rs in rows.items()},rows)
    rows={'uh':{('dependence','author','ejzp','scope','case')}};m={n:relation(rs) for n,rs in rows.items()}
    cases+=perturb(lambda mm:run('ejzq',[],mm),m,rows);assert run('ejzq',[],m|{'ejzp':forbidden});cases+=1
    rows={'eir3':{('dependence','author','paper','ejzr','case')},'ue':{('analogy','dependence','case')}}
    cases+=perturb(lambda mm:run('ejzs',[],mm),{n:relation(rs) for n,rs in rows.items()},rows)
    return dict(cases=cases,same_developed_theory_project_document_and_scope=True,author_and_order_maintained=True,quoted_claim_not_executed=True)

@lru_cache(None)
def source_record():
    u=json.loads(read(INVENTORY))['units'][175];assert u['id']=='einstein-1905:u0176' and digest(u['text'].encode())==u['text_sha256']
    start=u['text'].index('daß die elektrischen');text=u['text'][start:]
    return dict(status='physical_field_dependence_clause_connected_unit_incomplete',unit=u['id'],unit_sha256=u['text_sha256'],range=[start,len(u['text'])],text=text,math=[],source_nonblank_characters=len(re.sub(r'\s','',text)),observations=['原刊910頁の末尾節を、単位試験量への電気側・磁気側の局所作用の有無が理論全体で運動状態に独立ではないという読みで扱う。','同じ理論の許容過程・二系・出来事・場・単位・応答を結び、電気側と磁気側に別々の許容証人を認める。全場・全速度で変化するとはしない。'],remaining=['電動力の補助概念だけの役割、同じ概念の導入とこの事情による理由、Man siehtの提示','u0176全体の通読判断と後続単位'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in (INVENTORY,FACSIMILE,DOC)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert len(new.document['statements'])==360 and [i for i,(a,b) in enumerate(zip(old.document['statements'],new.document['statements'])) if a!=b]==[INDEX]
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    assert selection_binding(new,[167,168,169])==selection_binding(old,[167,168,169])
    load_annotations(ROOT,BASIS,ANNOTATIONS)
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    names=set(selection_binding(new,[INDEX])['dependencies']);assert set(MEANINGS)|{'eisqx','eisqy','eispn','ejts','ejym','ejyp','ejyq','eisqt','ejm2','scv2'}<=names
    assert not names&{'scx2','scw2','sdf2','sdg2'}
    core=parse(read(CORE))
    for style in ('compact','full'):
        b=format_graph(core,style);assert parse(b)==parse(transcribe(b,alphabet='v2'))==core
    assert json.loads(read(SOURCE))==json.loads(json.dumps(source_record(),ensure_ascii=False))
    return dict(new_definitions=len(MEANINGS),new_general_relations=2,new_references=1,other_359_statements_preserved=True,whole_unit_review_not_yet_added=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('realization',realization_checks),('geometry',geometry_checks),('pair',pair_checks),('presence',presence_checks),('binding',binding_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    helpers=('check_coordinate_correspondence','check_clock_site_time','check_resting_charge_force','check_total_differential','check_comoving_wording','compose_vacuum_field_domain','compose_material_relative_frame','compose_relativity_conjecture','compose_two_postulates','compose_field_equations','compose_field_transform','compose_force_wordings','compose_moving_field_definition','compose_electromotive_wording','compose_limits','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,*DEPENDENCIES,'scripts/compose_physical_field_dependence.py','scripts/check_physical_field_dependence.py','tests/test_physical_field_dependence.py',*(f'scripts/{n}.py' for n in helpers)}
    s=source_record();row=dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],statements=[INDEX],definitions=list(MEANINGS),status='explicit_interpretive_annotation')
    return dict(status='physical_frame_dependent_electric_and_magnetic_presence_connected',document=FULL,**results,alignment=dict(segments=[row]),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
