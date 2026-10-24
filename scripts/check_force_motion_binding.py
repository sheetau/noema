"""Check actual three-component charge motion and the standard-frame bridge."""
from functools import lru_cache
from fractions import Fraction as Q
from itertools import product
import json,xml.etree.ElementTree as ET
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import FunctionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_clock_site_time import relation,perturb,unknowns,forbidden
from scripts.check_resting_charge_force import rest_setup,retag,RS,PS,TAU
from scripts.check_total_differential import OPERATIONS,setup as numeric_setup
from scripts.check_field_transform import field_values
from scripts.check_parallel_composition import transform
from scripts.compose_force_motion_binding import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,PARENT_BASIS,INDICES,MEANINGS,LOCAL,HISTORY,build

DOC='docs/force-motion-binding-v1.md';SOURCE='data/einstein-force-motion-binding-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json'
FACSIMILES=tuple('artifacts/written-facsimiles-v1/einstein-1905-unlp-p'+p+'-0.jpg' for p in ('909','910'))
DEPENDENCIES=('reports/force-interpretation-v1.json','reports/resting-charge-force-v1.json','reports/material-velocity-v1.json','reports/force-wordings-v1.json','reports/field-transform-v1.json')
AXES=('x','y','z','t');SITUATIONS=('case','other')
CONSTANTS={'ri':'case','rd':'author','eirf':'paper','zno':'scope','ra':'frame','zbm':'moving','zol':'carrier','zpo':'event','zpp':'chargerecord','zou':'chargeunit','zor':'chargekind','ta':'length','rb':'duration','zpq':'first','zpr':'second','eisqn':'intro',**dict(zip(('yn','yo','yp','zc7'),AXES))}
DOMAIN=tuple(dict.fromkeys((*CONSTANTS.values(),'a','b','other')))

@lru_cache(None)
def fixture(name,mode='native'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    bounds=OPERATIONS|{'seob','senz','sjs','ejsl','ejsy','ejtu','ejwr','ejwv','ejs3','scm2'}
    bounds|={'ejxm':{'ejxl'},'ejxo':{'ejxm'},'ejxp':{'ejxo'},'ejxq':{'ejxo'},'ejxr':{'ejxp'}}.get(name,set())
    if mode=='witness':bounds|={'ejxl':{'ejxk'},'ejxn':{'ejxm'}}[name]
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
        n='jfmb'+number_word(i);slots.append((n,p['sort']));doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
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

def vector(c,coordinates):
    return FunctionValue(('individual',),RS,lambda a:c(coordinates[AXES.index(a)] if a in AXES[:len(coordinates)] else 0))

def motion_setup(velocity=(1,-2,3),acceleration=(0,0,0),variant='baseline'):
    s=rest_setup(velocity,acceleration,variant);c,r=s['c'],s['r'];p=s['point'];domain,curve=s['args'][-2:]
    args=['carrier','moving','event','chargerecord','chargeunit','length','duration',p,vector(c,velocity),'case',domain,curve]
    def one(x):
        if not isinstance(x,FunctionValue):return x
        if x.parameters==('number',):return r(x)
        if x.parameters==('individual',):return tuple(r(x(a)) for a in AXES)
        if x.parameters==(RS,) and x.result=='truth':return tuple(x(c(t)) for t in (3,4,5))
        if x.parameters==(RS,) and x.result==PS:return tuple(tuple(r(x(c(t))(a)) for a in AXES) for t in (3,4,5))
        raise ValueError('Unexpected motion fixture function')
    norm=lambda xs:tuple(one(x) for x in xs);rel=lambda rows:lambda *xs:norm(xs) in rows
    rows={'eisqc':{('carrier','case')},'ejsl':{('moving','length','duration','case')},'eisqd':{norm(('carrier','moving','event','length','duration',p,'case'))},'zof':{('chargeunit','chargekind',Q(1),'case')},'zog':{('chargerecord','carrier','chargekind','moving','event','chargeunit',Q(1),'case')}}
    m=s['m']|{n:rel(rs) for n,rs in rows.items()}|{'bg':lambda a,b:r(a)<r(b),'aa':lambda a,b:a<b}
    wanted=norm(('carrier','moving','case',domain,curve))
    m['seob']=lambda *xs:variant!='missing_history' and norm(xs)==wanted
    return s|dict(args=args,m=m,norm=norm,rows=rows,rel=rel)

@lru_cache(None)
def motion_checks():
    cases=0
    for vel in ((1,0,0),(-1,0,0),(0,1,0),(0,0,-1),(1,-2,3),(0,0,0)):
        s=motion_setup(vel,(2,-3,4));assert run('ejxk',s['args'],s['m'])==any(vel);assert len(s['observed'])==3;cases+=1
    s=motion_setup();m=s['m'];args=s['args'];cases+=perturb(lambda mm:run('ejxk',args,mm),m,s['rows'],s['norm'])
    for i,(name,t) in enumerate(HISTORY):
        bad=list(args)
        if t in ('a','d'):bad[i]='other'
        elif name=='domain':bad[i]=FunctionValue((RS,),'truth',lambda t:False)
        elif name=='curve':bad[i]=FunctionValue((RS,),PS,lambda t:vector(s['c'],(99,99,99,99)))
        else:bad[i]=vector(s['c'],(99,99,99,99))
        assert not run('ejxk',bad,m),name;cases+=1
    for axis in range(3):
        values=[1,-2,3];values[axis]+=1;bad=list(args);bad[8]=vector(s['c'],values)
        assert not run('ejxk',bad,m),axis;cases+=1
    for variant in ('isolated','one_sided','missing_history'):
        changed=motion_setup(variant=variant);assert not run('ejxk',changed['args'],changed['m']);cases+=1
    assert not run('ejxk',args,m|{'yo':lambda:'x'});cases+=1
    assert run('ejxk',args,m|{n:forbidden for n in ('xm','zok','zpa','x4')});cases+=1
    unknowns(lambda mm:run('ejxk',args,mm),m,('seob','senz','sjs','zpb'))
    try:run('ejxl',args[:10],m)
    except ValueError as e:assert 'Finite function domain' in str(e) or 'rational number domain' in str(e),str(e)
    else:raise AssertionError('Full physical history silently sampled')
    return dict(cases=cases,arbitrary_three_component_velocity=True,same_charge_history_units_and_event=True,nonzero_acceleration_allowed=True,all_history_slots_and_velocity_components_distinguished=True,full_function_domain_refused=True,history_interior_and_derivative_oracles_explicit=True)

@lru_cache(None)
def witness_checks():
    cases=0
    for name,callee in [('ejxl','ejxk'),('ejxn','ejxm')]:
        args=['a']*9+['case'] if name=='ejxl' else ['case']
        for witnesses in product(('a','b'),repeat=2 if name=='ejxl' else 1):
            target=tuple(args)+witnesses if name=='ejxl' else (witnesses[0],'case')
            m={callee:lambda *xs,target=target:xs==target}
            assert run(name,args,m,'witness',('a','b'));cases+=1
            for i in range(len(target)):
                # Every position is demanded; an out-of-domain witness or a
                # changed free argument cannot be supplied by a different slot.
                bad=target[:i]+('unavailable',)+target[i+1:]
                assert not run(name,args,{callee:lambda *xs,bad=bad:xs==bad},'witness',('a','b'));cases+=1
        unknowns(lambda mm:run(name,args,mm,'witness',('a','b')),{callee:lambda *xs:True},(callee,))
    return dict(cases=cases,every_existential_and_free_slot_checked=True,two_value_diagnostic_only=True)

def field_setup(name):
    cuts,m=numeric_setup(fixture(name)[0]);c,r=cuts.make,cuts.read
    m|={n:lambda x=x:x for n,x in CONSTANTS.items()}
    old=(Q(1),Q(2),Q(-1),Q(1));new=tuple(transform(old,Q(3),Q(5)))
    e=((1,0,0,0,1),(0,1,0,0,1),(0,0,1,0,2));h=((0,0,0,0,2),(0,0,0,0,1),(0,0,0,0,3))
    def field(rows):return FunctionValue(('individual',),TAU,lambda a:FunctionValue(tuple([RS]*4),RS,lambda *xs:c(sum(Q(z)*r(x) for z,x in zip(rows[AXES.index(a)][:4],xs))+rows[AXES.index(a)][4] if a in AXES[:3] else 0)))
    fields=(field(e),field(h));force=field_values(e,h,new,Q(3))[0]
    p,pnew=vector(c,old),vector(c,new);reg=FunctionValue(tuple([RS]*4),'truth',lambda *xs:True)
    m|={'tc':lambda:c(5),'zb7':lambda:c(3),'zpj':lambda:p,'zpk':lambda:pnew,'znl':lambda:fields[0],'znm':lambda:fields[1],'zpm':lambda:vector(c,force),'znr':lambda:fields[0],'znt':lambda:reg,'znk':lambda:reg}
    def point(x):return tuple(r(x(a)) for a in AXES)
    return dict(c=c,r=r,m=m,old=old,new=new,p=p,pnew=pnew,force=force,point=point,fields=fields)

@lru_cache(None)
def bridge_checks():
    cases=0;s=field_setup('ejxm');c=s['c'];velocity=vector(c,(1,-2,3));seen=[]
    def local(*xs):
        seen.append(xs);return xs[:7]==('carrier','frame','event','chargerecord','chargeunit','length','duration') and s['point'](xs[7])==s['old'] and s['point'](xs[8])==(1,-2,3,0) and xs[9]=='case'
    m=s['m']|{'ejxl':local,'ejsy':lambda ctx:ctx=='case'}
    assert run('ejxm',[velocity,'case'],m);cases+=1
    for n in ('ejxl','ejsy'):
        assert not run('ejxm',[velocity,'case'],m|{n:lambda *xs:False});cases+=1
    assert not run('ejxm',[velocity,'case'],m|{'znk':lambda:FunctionValue(tuple([RS]*4),'truth',lambda *xs:False)});cases+=1
    unknowns(lambda mm:run('ejxm',[velocity,'case'],mm),m,('ejxl','ejsy','znk'))
    s=field_setup('ejxo')
    m=s['m']|{'ejxm':lambda vel,ctx:s['point'](vel)==(3,0,0,0) and ctx=='case'}
    assert run('ejxo',['case'],m);cases+=1
    for speed in (-3,0,4,5,6):
        assert not run('ejxo',['case'],m|{'zb7':lambda speed=speed:s['c'](speed)});cases+=1
    assert not run('ejxo',['case'],m|{'ejxm':lambda vel,ctx:s['point'](vel)==(0,3,0,0)});cases+=1
    s=field_setup('ejxp');m=s['m']|{'ejxo':lambda ctx:ctx=='case','ejtu':lambda ctx:ctx=='case','ejsl':lambda *xs:xs==('moving','length','duration','case'),'eisqd':lambda b,f,e,lu,tu,p,ctx:(b,f,e,lu,tu,ctx)==('carrier','moving','event','length','duration','case') and s['point'](p)==s['new'],'ejwr':lambda b,f,e,p,ctx:(b,f,e,ctx)==('carrier','moving','event','case') and s['point'](p)==s['new']}
    assert run('ejxp',['case'],m);cases+=1
    for n in ('ejxo','ejtu','ejsl','eisqd','ejwr'):
        assert not run('ejxp',['case'],m|{n:lambda *xs:False}),n;cases+=1
    # Let the physical boundary accept changed coordinates: the actual
    # Lorentz mapping must still distinguish every one of four components.
    permissive=m|{'eisqd':lambda *xs:True,'ejwr':lambda *xs:True}
    for i in range(4):
        bad=list(s['new']);bad[i]+=1
        assert not run('ejxp',['case'],permissive|{'zpk':lambda bad=bad:vector(s['c'],bad)});cases+=1
    assert run('ejxp',['case'],m|{'zpa':forbidden,'xm':forbidden});cases+=1
    unknowns(lambda mm:run('ejxp',['case'],mm),m,('ejxo','ejtu','ejsl','eisqd','ejwr'))
    return dict(cases=cases,arbitrary_velocity_not_equated_with_standard_x_case=True,actual_signed_boost_speed_shared=True,all_four_native_coordinate_components_checked=True,instantaneous_rest_not_inferred_from_point_mapping=True)

@lru_cache(None)
def wording_checks():
    cases=0;s=field_setup('ejxq')
    def remainder(e,h):return tuple(s['r'](e(a)) for a in AXES[:3])==(2,3,1) and tuple(s['r'](h(a)) for a in AXES[:3])==(2,1,3)
    m=s['m']|{'ejxo':lambda ctx:True,'scm2':remainder}
    assert run('ejxq',[],m);cases+=1
    assert not run('ejxq',[],m|{'scm2':lambda *xs:False});cases+=1
    assert run('ejxq',[],m|{'ejxo':lambda ctx:False,'scm2':lambda *xs:False});cases+=1
    unknowns(lambda mm:run('ejxq',[],mm),m,('ejxo','scm2'))
    s=field_setup('ejxr');m=s['m']|{'ejxp':lambda ctx:True,'ejwv':lambda ctx:ctx=='case','ejs3':lambda *xs:True}
    assert run('ejxr',[],m);cases+=1
    for i in range(3):
        bad=list(s['force']);bad[i]+=1
        assert not run('ejxr',[],m|{'zpm':lambda bad=bad:vector(s['c'],bad)});cases+=1
    # Old-point field (2,3,1) and the first-order response are both distinct
    # from the comoving exact response at nonzero speed.
    for bad in ((2,3,1),(2,Q(6,5),Q(8,5))):
        assert not run('ejxr',[],m|{'zpm':lambda bad=bad:vector(s['c'],bad)});cases+=1
    for n in ('ejwv','ejs3'):
        assert not run('ejxr',[],m|{n:lambda *xs:False});cases+=1
    bad=list(s['new']);bad[0]+=1
    assert not run('ejxr',[],m|{'zpk':lambda:vector(s['c'],bad)});cases+=1
    assert run('ejxr',[],m|{'ejxp':lambda ctx:False,'ejwv':lambda ctx:False});cases+=1
    assert run('ejxr',[],m|{n:forbidden for n in ('zpl','scf2','zpa','xm')});cases+=1
    unknowns(lambda mm:run('ejxr',[],mm),m,('ejxp','ejwv','ejs3'))
    return dict(cases=cases,same_old_point_fixed_fields_in_remainder=True,native_inverse_coordinates_and_field_mixture=True,three_force_components_checked=True,finite_speed_linear_formula_rejected=True,old_frame_force_not_equated=True,global_field_identity_and_remainder_are_explicit_boundaries=True)

@lru_cache(None)
def presentation_checks():
    cases=0
    for name,node,claim in [('ejxs','first','ejxq'),('ejxv','second','ejxr')]:
        rows={'uh':{(node,'author',claim,'scope','case')}};m={n:relation(rs) for n,rs in rows.items()}
        cases+=perturb(lambda mm:run(name,[],mm),m,rows)
        assert run(name,[],m|{claim:forbidden});cases+=1
    for name,node,prior,message in [('ejxu','first','intro','ejxt'),('ejxx','second','first','ejxw')]:
        rows={'eir3':{(node,'author','paper',message,'case')},'ue':{(prior,node,'case')}}
        cases+=perturb(lambda mm:run(name,[],mm),{n:relation(rs) for n,rs in rows.items()},rows)
    return dict(cases=cases,same_author_and_order=True,quoted_partial_contents_not_executed=True)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));units=[]
    for i in (173,174):
        u=inv['units'][i];assert u['id']==f'einstein-1905:u{i+1:04d}' and digest(u['text'].encode())==u['text_sha256']
        start=u['text'].index('Ist ein');end=u['text'].index('bewegt,')+len('bewegt,')
        units.append(dict(unit=u['id'],unit_sha256=u['text_sha256'],text=u['text'],premise_range=[start,end],premise=u['text'][start:end],statement=167+i-173))
    m=next(m for m in inv['math'] if m['id']=='M0318');assert digest(m['mathml'].encode())==m['sha256'] and ''.join(ET.fromstring(m['mathml']).itertext())=='v/V'
    page=next(x for x in inv['annotations'] if x['id']=='A0024');assert page['kind']=='page' and page['source_id']=='910'
    return dict(status='physical_motion_dependency_and_explicit_standard_case_not_whole_review',units=units,math=m,page_boundary=page,observations=['原刊909末尾–910頁の二項を連続して確認した。M0318はv/V。A0024は頁区切りで脚注ではない。','共通の点状単位電気量の非零瞬間速度を三つの座標時刻微分へ結ぶ。加速度0は要求しない。','現行の変換はx方向標準配置であり、その速度と対象の実際の三速度の一致を追加する。任意方向の全文完成へ格上げしない。'],remaining=['任意方向の軸選択と場・力の成分対応','第一項の追加の機械的寄与の帰属','引用語と旧来／新しいの対比','両項の全単位意味判断'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in (INVENTORY,DOC,*FACSIMILES)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert len(new.document['statements'])==360
    assert [i for i,(a,b) in enumerate(zip(old.document['statements'],new.document['statements'])) if a!=b]==INDICES
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    assert selection_binding(new,[163,164,165,166,358,359])==selection_binding(old,[163,164,165,166,358,359])
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);names=set(selection_binding(new,INDICES)['dependencies'])
    assert {'ejxk','ejxm','ejxo','ejxp','ejxq','ejxr','seoc','ejwv','ejs3','s6k','scm2'}<=names
    assert not names&{'xm','zok','zpa','scn2','sco2','scp2','scf2','eisqg','eisqh'}
    assert set(MEANINGS)-names=={'ejxn'} # General existential remains available.
    core=parse(read(CORE))
    for style in ('compact','full'):
        b=format_graph(core,style);assert parse(b)==parse(transcribe(b,alphabet='v2'))==core
    assert json.loads(json.dumps(source_record(),ensure_ascii=False))==json.loads(read(SOURCE))
    return dict(new_definitions=len(MEANINGS),new_primitives=0,replaced_statements=INDICES,other_358_statements_and_judgments_preserved=True,whole_unit_completion_not_claimed=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('motion',motion_checks),('witness',witness_checks),('bridge',bridge_checks),('wording',wording_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    helpers=('compose_vacuum_field_domain','compose_material_relative_frame','compose_material_velocity','compose_relativity_conjecture','compose_two_postulates','compose_field_equations','compose_force_wordings','compose_rest_force','compose_limits','check_coordinate_correspondence','check_clock_site_time','check_resting_charge_force','check_total_differential','check_field_transform','check_parallel_composition','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,*DEPENDENCIES,'scripts/compose_force_motion_binding.py','scripts/check_force_motion_binding.py','tests/test_force_motion_binding.py',*(f'scripts/{n}.py' for n in helpers)}
    segments=[dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['premise_range'],source=s['premise'],statements=[s['statement']],definitions=list(MEANINGS),status='partial_explicit_reading') for s in source_record()['units']]
    return dict(status='physical_charge_motion_and_standard_comoving_connection_checked',document=FULL,**results,alignment=dict(segments=segments),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=source_record()['remaining'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
