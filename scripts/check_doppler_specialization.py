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
from scripts.compose_doppler_specialization import *
from noema.finite_semantics import FunctionValue
from scripts.check_distant_direction_geometry import arithmetic
from scripts.check_clock_site_time import relation,perturb
import re

CONSTANTS=CONSTANTS|{'eissm':'claim','eissn':'dopplerdisplay','eisso':'angular','eissq':'specialization','eissr':'axialdisplay','eisss':'lawname'}
DOMAIN=tuple(dict.fromkeys([*DOMAIN,*CONSTANTS.values()]))

DOC='docs/doppler-specialization-v1.md';SOURCE='data/einstein-doppler-specialization-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';FACSIMILE='artifacts/written-facsimiles-v1/einstein-1905-unlp-p911-0.jpg'
DEPENDENCIES=('reports/observed-doppler-v1.json','reports/distant-direction-geometry-v1.json','reports/wave-cycle-frequency-v1.json','reports/wave-transform-application-v1.json')
BOUNDS={'ekey':{'eket'},'eke2':{'ekev','eket','ekeu'},'eke3':{'ekey','ekez'},'eke4':{'ekey','ekeu'}}

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
        for i in range(len(QUANTIFIED)):
            assert node['kind']=='forall'
            if i==pivot:retained={k:node[k] for k in ('kind','variable','sort')}
            else:d['parameters'].append(dict(name=node['variable'],sort=node['sort']))
            node=node['body']
        d['body']['body']=retained|{'body':node}
    slots=[]
    for i,p in enumerate(d['parameters']):
        n='jdsp'+number_word(i);slots.append((n,p['sort']));doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=name,arguments=[dict(kind='call',symbol=n,arguments=[]) for n,s in slots])
    if d['result']=='content':
        if not any(x['name']=='ri' for x in doc['declarations']):doc['declarations'].append(dict(kind='primitive',name='ri',parameters=[],result='situation'))
        expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='ri',arguments=[]))
    elif isinstance(d['result'],dict):
        doc['declarations'].append(dict(kind='primitive',name='jdspcapture',parameters=[d['result']],result='truth'));expr=dict(kind='call',symbol='jdspcapture',arguments=[expr])
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,values,model,mode='native',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(values)==len(slots),(name,len(values),len(slots));captured=[]
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|model|{n:lambda x=x:x for (n,s),x in zip(slots,values)}
    def capture(value):captured.append(value);return True
    mm['jdspcapture']=capture
    result=evaluate_document(doc,individuals=domain,situations=('case','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=700000,memoize_definitions=True,memoize_expressions=True)[0]['value']
    return captured[0] if captured else result

@lru_cache(None)
def numeric_checks():
    cuts,m=arithmetic();c,r=cuts.make,cuts.read;cases=0
    # q is the exact positive root of (1-ratio)/(1+ratio).
    for root,light,frequency in product((Q(1,100),Q(1,10),Q(1,3),Q(1,2),Q(2,3),Q(9,10)),(Q(1),Q(5),Q(13)),(Q(1,4),Q(2))):
        ratio=(1-root*root)/(1+root*root);speed=light*ratio
        values=list(map(c,(light,speed,frequency)))
        assert r(run('ekew',values,m))==frequency*root;cases+=1
        assert run('ekex',values,m);cases+=1
        assert run('ekev',values[:2],m);cases+=1
        assert r(run('ekew',list(map(c,(light*7,speed*7,frequency))),m))==frequency*root;cases+=1
        assert frequency*root!=frequency/root and frequency*root>0;cases+=1
    for light,speed in product((-1,0,1,5),(-5,-1,0,1,3,5,6)):
        assert run('ekev',list(map(c,(light,speed))),m)==(0<speed<light);cases+=1
    # Outside the positive-speed statement domain the bare expression does not make a physical claim.
    assert r(run('ekew',list(map(c,(5,0,2))),m))==2;cases+=1
    assert r(run('ekew',list(map(c,(5,-3,2))),m))==4;cases+=1
    unknowns(lambda model:run('ekew',list(map(c,(5,3,2))),model),m,('sky','sjd','shv'))
    return dict(cases=cases,positive_square_root_ratio_matches_general_form=True,near_light_speed_and_scaled_units_checked=True,no_small_speed_truncation=True)

@lru_cache(None)
def lift_checks():
    from copy import deepcopy
    old=extract_document(parse(read(PARENT)),roots=list(LIFT),statement_indices=[]).document
    new=parse(read(CORE));ds={d['name']:d for d in new['declarations']};original={d['name']:d for d in old['declarations']};reverse={n:o for o,n in LIFT.items()}
    left=deepcopy(old);right=deepcopy(old);cases=0
    for previous,name in LIFT.items():
        d=deepcopy(ds[name]);speed=d['parameters'].pop(0)['name'];speedvar=dict(kind='variable',name=speed)
        def restore(node):
            nonlocal cases
            if isinstance(node,list):return [restore(x) for x in node]
            if not isinstance(node,dict):return node
            if node==speedvar:cases+=1;return dict(kind='call',symbol='zb7',arguments=[])
            out={k:restore(x) for k,x in node.items()}
            if node.get('kind')=='call' and node['symbol'] in reverse:
                assert node['arguments'][0]==speedvar
                out['symbol']=reverse[node['symbol']];out['arguments']=out['arguments'][1:];cases+=1
            return out
        d['body']=restore(d['body']);right['declarations'].append(d)
        expected=deepcopy(original[previous]);expected['name']=name;left['declarations'].append(expected)
    # Normalize once for the whole batch; this also detects captured or unbound variables.
    assert parse(format_graph(left,'compact'))==parse(format_graph(right,'compact'))
    deps={d['name'] for d in extract_document(new,roots=['eket','ekeu'],statement_indices=[]).document['declarations']}
    assert not deps&({'zb7'}|set(LIFT))
    assert set(LIFT.values())<=deps
    return dict(cases=cases,lifted_definitions=12,all_speed_calls_share_first_argument=True,specializing_speed_to_original_symbol_restores_all_original_bodies=True,no_old_fixed_speed_dependency_in_general_rule=True)

@lru_cache(None)
def region_checks():
    cuts,m=arithmetic();c,r=cuts.make,cuts.read;cases=0
    def gamma(V,speed):return c(1/r(m['sky'](c(1-(r(speed)/r(V))**2))))
    m=m|{'soy':gamma}
    region=FunctionValue((RS,)*3,'truth',lambda x,y,z:r(x)>0 and r(y)==2 and r(z)==-1)
    for ratio in (Q(3,5),Q(5,13),Q(15,17)):
        speed=5*ratio;g=r(gamma(c(5),c(speed)))
        mapped=run('eken',[c(speed),region,c(0),c(3),c(5)],m)
        for x,t in product((-10,0,1),(0,1,2,3)):
            oldx=g*(x+speed*t);oldt=g*(t+speed*x/25)
            assert mapped(c(x),c(2),c(-1),c(t))==(oldx>0 and 0<=oldt<=3);cases+=1
            assert not mapped(c(x),c(3),c(-1),c(t));cases+=1
    return dict(cases=cases,actual_parameterized_region_uses_same_inverse_speed=True,old_time_interval_and_spatial_region_preserved=True)

@lru_cache(None)
def condition_checks():
    cuts,m=arithmetic();c,r=cuts.make,cuts.read;slots=fixture('ekey')[1];names=[n for n,t in EXTENDED]
    values=[n if t=='a' else 'case' if t=='d' else sentinel(s,i+1,cuts) for i,((n,t),(_,s)) in enumerate(zip(EXTENDED,slots))]
    pos={n:i for i,n in enumerate(names)}
    for n,x in dict(speed=3,light=5,angle=0,frequency=2,newfrequency=1).items():values[pos[n]]=c(x)
    def gate(*xs):return all(same_value(x,y,s,cuts) for x,y,(_,s) in zip(xs,values,slots))
    mm=m|{'eket':gate};assert run('ekey',values,mm);cases=1
    for i,(n,s) in enumerate(slots):
        changed=values[:];changed[i]=sentinel(s,100+i,cuts);assert not run('ekey',changed,mm),(i,n);cases+=1
    for angle in (Q(-4),Q(-1),Q(1),Q(2),Q(4),Q(8)):
        changed=values[:];changed[pos['angle']]=c(angle);assert not run('ekey',changed,m|{'eket':lambda *xs:True});cases+=1
    assert run('ekez',values,m);cases+=1
    for name,val in (('newfrequency',-1),('newfrequency',4),('frequency',1),('speed',0)):
        changed=values[:];changed[pos[name]]=c(val);assert not run('ekez',changed,m);cases+=1
    unknowns(lambda model:run('ekey',values,model),mm,('eket','sca','bg'))
    # Existing real-angle convention distinguishes phi=0 from phi=pi and a right angle.
    from scripts.check_distant_direction_geometry import run as geometry
    gm=branch_model(cuts,m)
    for n,co,si,angle in (((1,0,0),1,0,0),((-1,0,0),-1,0,4),((0,1,0),0,1,2)):
        actual=[*n,3,co,si,0,0,4,angle]
        assert geometry('ekdq',list(map(c,actual)),gm);cases+=1
        actual[-1]=0;assert geometry('ekdq',list(map(c,actual)),gm)==(co==1);cases+=1
    return dict(cases=cases,all_60_setting_roles_bound=True,zero_actual_angle_not_any_cosine_assignment=True,same_new_frequency_and_positive_root=True)

@lru_cache(None)
def universal_checks():
    cases=0
    for root,premise,conclusion in (('eke2','eket','ekeu'),('eke3','ekey','ekez'),('eke4','ekey','ekeu')):
        for pivot,(name,sort) in enumerate(QUANTIFIED):
            for target in ('a','b','unavailable'):
                expected={n:'a' for n,t in EXTENDED};expected.update(frame='a',scope='b',context='case',light='a');expected[name]=target
                values=[expected[n] for i,(n,t) in enumerate(QUANTIFIED) if i!=pivot];row=tuple(expected[n] for n,t in EXTENDED);mode='slot:'+str(pivot)
                mm={'ra':lambda:'a','eisrx':lambda:'b','tc':lambda:'a','ekev':lambda *xs:True,premise:lambda *xs,row=row:tuple(xs)==row,conclusion:lambda *xs:False}
                assert run(root,values,mm,mode,('a','b'))==(target=='unavailable');cases+=1
                assert run(root,values,mm|{conclusion:lambda *xs,row=row:tuple(xs)==row},mode,('a','b'));cases+=1
                assert run(root,values,mm|{premise:lambda *xs:False},mode,('a','b'));cases+=1
                if target!='unavailable':
                    assert not run(root,values,mm|{conclusion:lambda *xs,row=row:tuple(xs)!=row},mode,('a','b'));cases+=1
        unknowns(lambda model:run(root,values,model,mode,('a','b')),mm,(premise,conclusion))
        cuts,m=arithmetic();refused(lambda:run(root,[],m|{'tc':lambda:cuts.make(5),premise:lambda *xs:True,conclusion:lambda *xs:True,'ekev':lambda *xs:True}))
    return dict(cases=cases,quantified_slots_per_content=len(QUANTIFIED),all_speeds_and_same_assignments_in_three_contents=True,missing_values_vacuity_and_unknown_inputs_distinguished=True)

@lru_cache(None)
def presentation_checks():
    rows={
     'eke5':{'eissb':{('specialization','dopplerdisplay','author','ekeb','eke2','scope','case')},'eisch':{('lawname','eke2','scope','case')}},
     'eke6':{'eissb':{('specialization','dopplerdisplay','author','eke4','eke3','scope','case')},'eissp':{('eke3','scope','case')},'uf':{('author','specialization','axialdisplay','case')},'ue':{('specialization','axialdisplay','case')}},
     'ekfc':{'eisox':{('axialdisplay','eke3','case')}},
     'ekfb':{'eir3':{('specialization','author','paper','ekfa','case')},'ue':{('dopplerdisplay','specialization','case')}},
     'ekfe':{'eir3':{('axialdisplay','author','paper','ekfd','case')},'ue':{('specialization','axialdisplay','case')}}}
    cases=0
    for root,rs in rows.items():cases+=perturb(lambda model:run(root,[],model),{n:relation(vs) for n,vs in rs.items()},rs)
    whole={n:relation(set().union(*(rows[root].get(n,set()) for root in ('eke5','eke6')))) for n in set(rows['eke5'])|set(rows['eke6'])}
    assert run('eke7',[],whole|{n:forbidden for n in ('ekeb','eke2','eke3','eke4')});cases+=1
    for n in ('eissp','eisch'):
        assert not run('eke7',[],whole|{n:lambda *xs:False});cases+=1
    return dict(cases=cases,name_general_speed_zero_angle_clarity_and_display_preserved=True,no_quoted_physical_law_evaluated_by_attribution=True)

@lru_cache(None)
def source_record():
    import xml.etree.ElementTree as ET
    inv=json.loads(read(INVENTORY));math={x['id']:x for x in inv['math']};segments=[]
    readings={'M0334':'φ=0','M0335':'ν′=ν*sqrt((1−v/V)/(1+v/V))'}
    for i in range(189,191):
        u=inv['units'][i];assert digest(u['text'].encode())==u['text_sha256']
        segments.append(dict(unit=u['id'],unit_sha256=u['text_sha256'],text=u['text'],range=[0,len(u['text'])],statements=[372+i-189],math=[dict(id=n,sha256=math[n]['sha256'],reading=readings[n]) for n in u['math_ids']],source_nonblank_characters=len(re.sub(r'\s|\[M\d+\]','',u['text']))))
    assert 'Doppelersche Prinzip' in segments[0]['text']
    tokens=[x.text for x in ET.fromstring(math['M0335']['mathml']).iter() if x.text]
    assert tokens.count('=')==1 and tokens.count('−')==1 and tokens.count('+')==1
    return dict(status='named_doppler_law_arbitrary_speeds_zero_angle_and_display_collated',segments=segments,observations=LIMITS,source_sha256={p:digest((ROOT/p).read_bytes()) for p in (INVENTORY,FACSIMILE,'artifacts/written-facsimiles-v1/einstein-1905-unlp-p912-0.jpg',DOC)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert len(new.document['statements'])==374 and new.document['statements'][:372]==old.document['statements']
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    annotations=load_annotations(ROOT,BASIS,ANNOTATIONS);assert annotations.annotations['entries'][-1]['forms'][0]['text']=='Doppelersche Prinzip'
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    core=parse(read(CORE))
    for style in ('compact','full'):
        body=format_graph(core,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=len(MEANINGS),new_general_relations=1,new_references=3,old_372_statements_and_judgments_preserved=True,printed_designation_not_silently_corrected=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('numeric',numeric_checks),('lift',lift_checks),('region',region_checks),('condition',condition_checks),('universal',universal_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    helpers=('check_coordinate_correspondence','check_clock_site_time','check_conductor_cases','check_material_relative_frame','check_wave_inquiry','check_wave_transform_application','check_wave_cycle_frequency','check_distant_direction_geometry','check_resting_charge_force','check_velocity_angle_measure','compose_observed_doppler','compose_material_relative_frame','compose_relativity_conjecture','compose_two_postulates','compose_limits','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,*DEPENDENCIES,'scripts/compose_doppler_specialization.py','scripts/check_doppler_specialization.py','tests/test_doppler_specialization.py',*(f'scripts/{n}.py' for n in helpers)}
    rows=[dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],statements=s['statements'],definitions=list(MEANINGS),status='explicit_interpretive_annotation') for s in source_record()['segments']]
    return dict(status='all_admissible_speeds_and_named_zero_angle_doppler_form_connected',document=FULL,**results,alignment=dict(segments=rows),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
