"""Check receding directions, quantifier order, spatial angles and the printed law."""
from functools import lru_cache
from fractions import Fraction as Q
from itertools import product
from math import isqrt
import json
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_clock_site_time import unknowns,forbidden
from scripts.check_conductor_cases import sentinel,same_value
from scripts.check_material_relative_frame import NUM,RS
from scripts.check_wave_inquiry import arithmetic_model
from scripts.check_wave_transform_application import DOMAIN,CONSTANTS
from scripts.check_wave_cycle_frequency import refused
from scripts.check_resting_charge_force import retag
from scripts.check_velocity_angle_measure import branch_model
from scripts.compose_distant_direction_geometry import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,PARENT_BASIS,MEANINGS,PRIOR,SETTING,WITNESSES,COMBINED,build

DOC='docs/distant-direction-geometry-v1.md';SOURCE='data/einstein-distant-direction-geometry-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';FACSIMILE='artifacts/written-facsimiles-v1/einstein-1905-unlp-p911-0.jpg'
DEPENDENCIES=('reports/wave-cycle-frequency-v1.json','reports/distant-wave-source-v1.json','reports/velocity-angle-measure-v1.json','reports/wave-directions-v1.json')
BOUNDS={'ekdl':{'ekdk'},'ekdm':{'ekdl'},'ekdt':{'ekde','ekdm','ekds'},'ekdu':{'ekdt'}}

@lru_cache(None)
def fixture(name,mode='native'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    bounds=NUM|{'bg','sjd','sje','szi','soy','sky','shu'}
    if mode!='full':bounds|=BOUNDS.get(name,set())|{'ejor','sedi'}
    if mode=='quantified':bounds.add('seag')
    abstract(doc,bounds);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name)
    if mode=='pointwise':
        found=[]
        def expose(node):
            if isinstance(node,list):return [expose(x) for x in node]
            if not isinstance(node,dict):return node
            if node.get('kind')=='forall' and node['sort']==RS:
                found.append(dict(name=node['variable'],sort=RS));return expose(node['body'])
            return {k:expose(x) for k,x in node.items()}
        d['body']=expose(d['body']);assert len(found)==1;d['parameters']+=found
    if mode=='quantified':
        def replace(node):
            if node==RS:return 'individual'
            if isinstance(node,list):return [replace(x) for x in node]
            if isinstance(node,dict):return {k:replace(x) for k,x in node.items()}
            return node
        doc=replace(doc);d=next(d for d in doc['declarations'] if d['name']==name)
    if mode.startswith('slot:'):
        doc=retag(doc)
        for dec in doc['declarations']:
            if dec['kind']=='primitive':
                dec['parameters']=['individual' if isinstance(t,dict) else t for t in dec['parameters']]
                if isinstance(dec['result'],dict):dec['result']='individual'
            else:
                for p in dec['parameters']:
                    if isinstance(p['sort'],dict):p['sort']='individual'
        d=next(d for d in doc['declarations'] if d['name']==name)
        pivot=int(mode.split(':')[1]);node=d['body']['body'];retained=None
        for i in range(len(WITNESSES)):
            assert node['kind']=='exists'
            if i==pivot:retained={k:node[k] for k in ('kind','variable','sort')}
            else:d['parameters'].append(dict(name=node['variable'],sort=node['sort']))
            node=node['body']
        d['body']['body']=retained|{'body':node}
    slots=[]
    for i,p in enumerate(d['parameters']):
        n='jddg'+number_word(i);slots.append((n,p['sort']));doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=name,arguments=[dict(kind='call',symbol=n,arguments=[]) for n,s in slots])
    if d['result']=='content':
        if not any(x['name']=='ri' for x in doc['declarations']):doc['declarations'].append(dict(kind='primitive',name='ri',parameters=[],result='situation'))
        expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='ri',arguments=[]))
    elif isinstance(d['result'],dict):
        doc['declarations'].append(dict(kind='primitive',name='jddgcapture',parameters=[d['result']],result='truth'));expr=dict(kind='call',symbol='jddgcapture',arguments=[expr])
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,values,model,mode='native',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(values)==len(slots),(name,len(values),len(slots));captured=[]
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|model|{n:lambda x=x:x for (n,s),x in zip(slots,values)}
    def capture(value):captured.append(value);return True
    mm['jddgcapture']=capture
    result=evaluate_document(doc,individuals=domain,situations=('case','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=700000,memoize_definitions=True,memoize_expressions=True)[0]['value']
    return captured[0] if captured else result

def arithmetic():
    cuts,m=arithmetic_model();c,r=cuts.make,cuts.read
    def sqrt(value):
        x=r(value)
        if x<0:return forbidden()
        a,b=isqrt(x.numerator),isqrt(x.denominator)
        if a*a!=x.numerator or b*b!=x.denominator:return forbidden()
        return c(Q(a,b))
    m|={'sky':sqrt,'shu':lambda x:c(abs(r(x)))}
    return cuts,m

@lru_cache(None)
def source_curve_checks():
    cuts,m=arithmetic();c,r=cuts.make,cuts.read;cases=0
    for direction,distance,position in product(((1,0,0),(-1,0,0),(Q(3,5),Q(4,5),0),(0,Q(3,5),Q(4,5))), (1,5,100),((0,0,0),(1,-2,3))):
        source=run('ekdg',list(map(c,(*direction,distance))),m)
        displacement=run('ekdh',list(map(c,(*direction,distance,*position))),m)
        assert tuple(r(source(a)) for a in ('x','y','z'))==tuple(-distance*n for n in direction);cases+=1
        assert tuple(r(displacement(a)) for a in ('x','y','z'))==tuple(p+distance*n for p,n in zip(position,direction));cases+=1
        curve=run('ekdi',list(map(c,(*direction,distance))),m)
        for t in (-3,0,2):
            point=curve(c(t));assert tuple(r(point(a)) for a in ('x','y','z','t'))==(*(-distance*n for n in direction),t);cases+=1
    unknowns(lambda model:run('ekdh',list(map(c,(1,0,0,5,1,2,3))),model)('x'),m,('bf','shv','szi'))
    return dict(cases=cases,source_to_observer_orientation_preserved=True,each_distance_has_constant_spatial_curve_and_actual_time_coordinate=True)

@lru_cache(None)
def limit_point_checks():
    cuts,m=arithmetic();c,r=cuts.make,cuts.read;cases=0
    pairs=(((1,0,0),(0,3,4)),((Q(3,5),Q(4,5),0),(-4,3,0)),((0,Q(3,5),Q(4,5)),(0,-4,3)))
    for direction,position in pairs:
        previous=None
        for parameter in (Q(10),Q(25),Q(50),Q(100)):
            distance=(parameter**2-25)/(2*parameter);length=(parameter**2+25)/(2*parameter)
            d=[p+distance*n for p,n in zip(position,direction)];errors=[abs(x/length-n) for x,n in zip(d,direction)]
            if previous is not None:assert max(errors)<previous
            previous=max(errors)
            for epsilon in (Q(1),Q(1,2),Q(1,10),Q(1,100)):
                expected=all(x<epsilon for x in errors)
                assert run('ekdj',list(map(c,(*direction,*position,distance,epsilon))),m)==expected;cases+=1
            # Strict inequality rejects its exact largest component-error boundary.
            assert not run('ekdj',list(map(c,(*direction,*position,distance,max(errors)))),m);cases+=1
    for direction in ((1,0,0),(-1,0,0),(0,1,0),(0,0,1)):
        for distance in (Q(1),Q(10),Q(100)):
            assert run('ekdj',list(map(c,(*direction,0,0,0,distance,Q(1,1000)))),m);cases+=1
    # Coinciding source and observer does not acquire an arbitrary direction.
    for bad in ((1,0,0,-2,0,0,2,1),(0,0,0,0,0,0,1,1),(1,0,0,0,0,0,0,1),(1,0,0,0,0,0,1,0)):
        assert not run('ekdj',list(map(c,bad)),m);cases+=1
    unknowns(lambda model:run('ekdj',list(map(c,(1,0,0,0,3,4,12,Q(1,2)))),model),m,('sky','shu','bg'))
    return dict(cases=cases,exact_rational_distances_and_component_errors=True,strict_error_bound_and_collision_rejection=True,finite_examples_not_full_limit_proof=True)

@lru_cache(None)
def limit_scope_checks():
    cuts,m=arithmetic();c,r=cuts.make,cuts.read;cases=0
    # Native tail guard and point predicate; p=0 makes every tested square root exact.
    for cutoff,distance in product((Q(-1),Q(0),Q(2)),(-1,0,1,2,3)):
        args=list(map(c,(1,0,0,0,0,0,Q(1,10),cutoff,distance)))
        assert run('ekdk',args,m,'pointwise')==(cutoff>0);cases+=1
    # Force a failed far point to distinguish R>cutoff from R<cutoff or one chosen R.
    doc,slots=fixture('ekdk','pointwise')
    # A second fixture boundary is installed by the documented abstract helper below.
    for cutoff,distance in product((1,2,3),(0,1,2,3,4)):
        assert tail_boundary(cutoff,distance,m,c)==(distance<=cutoff);cases+=1
    truth=lambda *xs:True
    qm={'ba':truth,'bg':truth,'sca':truth,'bb':lambda x:'a','seag':lambda *xs:'a'}
    for mapping in ({'a':'a','b':'b'},{'a':'b','b':'a'},{'a':'a','b':'a'},{'a':'b','b':'b'}):
        rows={('a',)*6+(epsilon,cutoff) for epsilon,cutoff in mapping.items()}
        good=qm|{'ekdk':lambda *xs,rows=rows:tuple(xs) in rows}
        assert run('ekdl',['a']*6,good,'quantified',('a','b'));cases+=1
        for row in rows:
            assert not run('ekdl',['a']*6,qm|{'ekdk':lambda *xs,rows=rows,row=row:tuple(xs) in rows-{row}},'quantified',('a','b'));cases+=1
    positions=set(product(('a','b'),repeat=3))
    gate=lambda *xs:xs[:3]==('a','a','a') and tuple(xs[3:]) in positions
    assert run('ekdm',['a']*3,qm|{'ekdl':gate},'quantified',('a','b'));cases+=1
    for missing in positions:
        assert not run('ekdm',['a']*3,qm|{'ekdl':lambda *xs,missing=missing:xs[:3]==('a','a','a') and tuple(xs[3:]) in positions-{missing}},'quantified',('a','b'));cases+=1
    for root,args in [('ekdk',(1,0,0,0,0,0,Q(1,10),2)),('ekdl',(1,0,0,0,0,0)),('ekdm',(1,0,0))]:
        refused(lambda root=root,args=args:run(root,list(map(c,args)),m))
    return dict(cases=cases,all_distances_beyond_fixed_cutoff=True,forall_epsilon_exists_cutoff_order_checked=True,every_finite_position_slot_checked=True,full_real_quantification_refused=True)

@lru_cache(None)
def tail_fixture():
    from copy import deepcopy
    doc,slots=fixture('ekdk','pointwise');doc=deepcopy(doc);abstract(doc,{'ekdj'})
    return extract_document(doc,roots=[],statement_indices=[0]).document,slots

def tail_boundary(cutoff,distance,m,c):
    doc,slots=tail_fixture();values=list(map(c,(1,0,0,0,0,0,Q(1,10),cutoff,distance)))
    mm=m|{'ekdj':lambda *xs:False}|{n:lambda x=x:x for (n,s),x in zip(slots,values)}
    return evaluate_document(doc,individuals=DOMAIN,situations=('case',),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},memoize_definitions=True,memoize_expressions=True)[0]['value']

@lru_cache(None)
def spatial_angle_checks():
    cuts,m=arithmetic();c=cuts.make;cases=0
    examples=[((1,0,0),(3,0,0),3,1,0),((1,0,0),(-3,0,0),3,-1,0),((0,0,1),(3,4,0),5,0,1),((Q(3,5),Q(4,5),0),(0,0,7),7,0,1),((0,Q(3,5),Q(4,5)),(0,3,4),5,1,0),((Q(3,5),Q(4,5),0),(3,0,0),3,Q(3,5),Q(4,5))]
    for n,u,s,co,si in examples:
        values=[*n,*u,s,co,si];assert run('ekdn',list(map(c,values)),m);cases+=1
        for i in (6,7):
            changed=values[:];changed[i]+=1;assert not run('ekdn',list(map(c,changed)),m);cases+=1
        if si>0:
            changed=values[:];changed[8]=-si;assert not run('ekdn',list(map(c,changed)),m);cases+=1
        for scalar in (2,3):
            assert run('ekdn',list(map(c,(*n,*(scalar*x for x in u),scalar*s,co,si))),m);cases+=1
    for n in ((1,0,0),(0,1,0),(0,0,1),(Q(3,5),Q(4,5),0),(-1,0,0)):
        co=Q(n[0]);si=Q(0) if abs(co)==1 else Q(1) if co==0 else Q(4,5)
        assert run('ekdp',list(map(c,(*n,3,co,si))),m);cases+=1
        assert not run('ekdp',list(map(c,(*n,-3,co,si))),m);cases+=1
        assert not run('ekdp',list(map(c,(*n,0,co,si))),m);cases+=1
    unknowns(lambda model:run('ekdn',list(map(c,(*examples[-1][0],*examples[-1][1],*examples[-1][2:]))),model),m,('sca','shv','bc'))
    return dict(cases=cases,three_spatial_components_and_speed_norm_used=True,upper_semicircle_keeps_opposite_and_right_angles=True,negative_and_zero_speed_not_unsigned_speed=True)

@lru_cache(None)
def real_angle_checks():
    cuts,m=arithmetic();c=cuts.make;mm=branch_model(cuts,m);cases=0
    for direction,co,si in [((1,0,0),1,0),((-1,0,0),-1,0),((0,0,1),0,1),((Q(3,5),Q(4,5),0),Q(3,5),Q(4,5)),((-Q(3,5),0,Q(4,5)),-Q(3,5),Q(4,5))]:
        ratio=si/co if co else Q(0);principal=0 if ratio==0 else 1 if ratio>0 else -1
        angle=2 if co==0 else principal if co>0 else principal+4
        values=[*direction,3,co,si,ratio,principal,4,angle]
        assert run('ekdq',list(map(c,values)),mm);cases+=1
        vector=[*direction,3,0,0,3,co,si,ratio,principal,4,angle]
        assert run('ekdo',list(map(c,vector)),mm);cases+=1
        for i in (4,5,6,7,8,9):
            changed=values[:];changed[i]+=Q(1,2);assert not run('ekdq',list(map(c,changed)),mm);cases+=1
        for wrong in (angle+8,angle-8,-4):
            changed=values[:];changed[-1]=wrong;assert not run('ekdq',list(map(c,changed)),mm);cases+=1
    unknowns(lambda model:run('ekdq',list(map(c,values)),model),mm,('ejor','sedi'))
    refused(lambda:run('ekdq',list(map(c,values)),m,'full'))
    return dict(cases=cases,real_angle_not_identified_with_cosine=True,zero_half_pi_and_positive_pi_branches=True,rational_pi_atan_boundaries_not_true_values=True)

@lru_cache(None)
def printed_checks():
    cuts,m=arithmetic();c,r=cuts.make,cuts.read;mm=branch_model(cuts,m);cases=0
    directions=[(1,0,0),(-1,0,0),(0,1,0),(0,0,1),(Q(3,5),Q(4,5),0)]
    for n,rate,cycle in product(directions,(Q(2),Q(8)),(Q(4),Q(8))):
        co=Q(n[0]);si=Q(0) if abs(co)==1 else Q(1) if co==0 else Q(4,5)
        ratio=si/co if co else Q(0);principal=0 if not ratio else 1 if ratio>0 else -1
        angle=2 if co==0 else principal if co>0 else principal+4
        factor=Q(5,4)*(1-co*Q(3,5));newrate=rate*factor;nu=rate/cycle;newnu=newrate/cycle
        assert r(run('ekdr',list(map(c,(5,3,nu,co))),m))==newnu;cases+=1
        values=[cycle,5,3,*n,rate,newrate,cycle/rate,cycle/newrate,nu,newnu,co,si,ratio,principal,4,angle]
        assert run('ekds',list(map(c,values)),mm);cases+=1
        for i in (3,7,9,10,11,12,17):
            changed=values[:];changed[i]+=Q(1,2);assert not run('ekds',list(map(c,changed)),mm);cases+=1
    unknowns(lambda model:run('ekdr',list(map(c,(5,3,2,Q(3,5)))),model),m,('sky','sjd','shv'))
    return dict(cases=cases,printed_positive_sqrt_form_equals_same_cycle_factor=True,angle_direction_and_two_frequencies_share_inputs=True)

@lru_cache(None)
def binding_checks():
    cuts,m=arithmetic();c,r=cuts.make,cuts.read;slots=fixture('ekdt')[1];pos={n:i for i,(n,t) in enumerate(SETTING)}
    values=[n if t=='a' else 'case' if t=='d' else sentinel(s,i+1,cuts) for i,((n,t),(_,s)) in enumerate(zip(SETTING,slots))]
    fixed=dict(light=5,rate=8,ax=Q(3,5),ay=Q(4,5),az=0,pi=4,cycle=8,oldperiod=1,newperiod=Q(5,4),frequency=1,newfrequency=Q(4,5),anglecos=Q(3,5),anglesin=Q(4,5),ratio=Q(4,3),principal=1,angle=1)
    for n,x in fixed.items():values[pos[n]]=c(x)
    def matches(xs,expected,sorts):return len(xs)==len(expected) and all(same_value(x,y,s,cuts) for x,y,s in zip(xs,expected,sorts))
    parent=lambda *xs:matches(xs,values[:len(PRIOR)],[s for n,s in slots[:len(PRIOR)]])
    direction=lambda *xs:tuple(map(r,xs))==(Q(3,5),Q(4,5),Q(0))
    expected=[Q(3) if n=='speed' else Q(32,5) if n=='newrate' else Q(fixed[n]) for n,t in COMBINED]
    composed=lambda *xs:tuple(map(r,xs))==tuple(expected)
    # A numerical boundary for wiring; parent rejects the perturbed light role.
    mm=m|{'soy':lambda *xs:c(Q(5,4)),'zb7':lambda:c(3),'ekde':parent,'ekdm':direction,'ekds':composed}
    assert run('ekdt',values,mm);cases=1
    for i,(n,s) in enumerate(slots):
        changed=values[:];changed[i]=sentinel(s,100+i,cuts);assert not run('ekdt',changed,mm);cases+=1
    for n in ('ekde','ekdm','ekds'):
        assert not run('ekdt',values,mm|{n:lambda *xs:False});cases+=1
    unknowns(lambda model:run('ekdt',values,model),mm,('ekde','ekdm','ekds'))
    return dict(cases=cases,all_52_roles_and_same_pi_direction_frequency_bound=True,finite_source_setting_not_replaced_by_an_infinite_real_coordinate=True)

@lru_cache(None)
def witness_checks():
    cases=0
    for pivot,(name,sort) in enumerate(WITNESSES):
        for target in ('a','b','unavailable'):
            expected={n:'a' for n,t in SETTING};expected.update(frame='a',scope='b',context='case',light='a');expected[name]=target
            values=[expected[n] for i,(n,t) in enumerate(WITNESSES) if i!=pivot];row=tuple(expected[n] for n,t in SETTING)
            m={'ra':lambda:'a','eisrx':lambda:'b','tc':lambda:'a','ekdt':lambda *xs,row=row:tuple(xs)==row}
            assert run('ekdu',values,m,'slot:'+str(pivot),('a','b'))==(target!='unavailable');cases+=1
            if target!='unavailable':assert not run('ekdu',values,m|{'ekdt':lambda *xs:False},'slot:'+str(pivot),('a','b'));cases+=1
    cuts,m=arithmetic();refused(lambda:run('ekdu',[],m|{'tc':lambda:cuts.make(5),'ekdt':lambda *xs:True}))
    return dict(cases=cases,witnesses=len(WITNESSES),every_shared_witness_and_absent_value_checked=True,full_function_domain_refused=True)

@lru_cache(None)
def source_record():
    previous=json.loads(read('data/einstein-wave-cycle-frequency-reading-v1.json'))
    return dict(status='asymptotic_direction_angle_and_printed_factor_prepared_not_whole_source',units=previous['units'],observations=['原刊911頁の源―観測者の線と速度の角を、源から観測者へ向く方向と正の+x速度の角と読む。この規約でcosφ=aとなりM0333の符号と一致する。','unendlich fernは有限距離の大きさだけでは代用しない。数学的な遠距離配置族とその方向極限を構成した。実際の源と観測者への役割の帰属と著者提示は未完であり、新しい本文範囲・全単位判断は追加しない。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in (INVENTORY,FACSIMILE,DOC,'data/einstein-wave-cycle-frequency-reading-v1.json')})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements']==old.document['statements'] and len(new.document['statements'])==370
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    assert all(d['kind']=='definition' for d in new.document['declarations'][len(old.document['declarations']):])
    load_annotations(ROOT,BASIS,ANNOTATIONS)
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    dependencies={d['name'] for d in extract_document(new.document,roots=['ekdt'],statement_indices=[]).document['declarations']}
    assert {'ekde','ekcl','ekdd','ekc3','ekc7','sedi','ejot','ejor','seag','seah','seal','sky','seat','ekdm','ekdq','ekdr'}<=dependencies
    assert not dependencies&{'ekbw','ekbx','ekby','ekbz'}
    core=parse(read(CORE))
    for style in ('compact','full'):
        body=format_graph(core,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=len(MEANINGS),new_primitives=0,old_370_statements_and_judgments_preserved=True,no_new_source_completion_claim=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('source_curve',source_curve_checks),('limit_point',limit_point_checks),('limit_scope',limit_scope_checks),('spatial_angle',spatial_angle_checks),('real_angle',real_angle_checks),('printed',printed_checks),('binding',binding_checks),('witness',witness_checks),('structure',structure_checks)]}
    helpers=('check_coordinate_correspondence','check_clock_site_time','check_conductor_cases','check_material_relative_frame','check_wave_inquiry','check_wave_transform_application','check_wave_cycle_frequency','check_resting_charge_force','check_velocity_angle_measure','compose_wave_cycle_frequency','compose_field_equations','compose_material_relative_frame','compose_relativity_conjecture','compose_electromotive_wording','compose_limits','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,*DEPENDENCIES,'scripts/compose_distant_direction_geometry.py','scripts/check_distant_direction_geometry.py','tests/test_distant_direction_geometry.py',*(f'scripts/{n}.py' for n in helpers)}
    return dict(status='asymptotic_source_direction_spatial_angle_and_printed_factor_dependencies_checked',document=FULL,**results,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
