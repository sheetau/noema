"""Check finite energy accounting, the shared mirror quantities and four-sentence presentation."""
from copy import deepcopy
from functools import lru_cache
from fractions import Fraction as Q
import json
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,validate_hashes,selection_binding
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_clock_site_time import relation,perturb,unknowns,forbidden
from scripts.check_resting_charge_force import retag
from scripts.check_material_relative_frame import NUM
from scripts.check_light_energy_ratio import arithmetic
from scripts.check_mirror_energy_work import setting,mutate,scalar,run as prior_run,CONSTANTS as PRIOR_CONSTANTS
from scripts.check_reflected_light_inquiry import normalize
from scripts.check_wave_cycle_frequency import refused
from scripts.compose_mirror_energy_principle import *
from scripts.read_mirror_energy_principle import DOC,READING,INVENTORY,build_reading

CONSTANTS=PRIOR_CONSTANTS|{'rd':'author','eirf':'paper','eisuv':'previous','eisu3':'first','eisu4':'second','eisu5':'third','eisu6':'fourth','eisu7':'display','eisva':'principlename','eisvb':'pressurename'}
DOMAIN=tuple(dict.fromkeys([*CONSTANTS.values(),*[n for n,t in TOTAL if t=='a'],'other','a','b']))
DEPENDENCIES=('reports/mirror-energy-work-v1.json','reports/reflected-return-quantities-v1.json')
CONSEQUENTS={'ekub':('ekuu',TOTAL),'ekuc':('ekuv',TOTAL),'ekud':('ektz',[(n,R) for n in ('incoming','outgoing','work')]),'ekue':('ekt2',[(n,R) for n in ('pressure','speed','work')]),'ekuf':('ekt4',TOTAL),'ekua':('ekt7',ENERGIES)}
QROOTS=[*CLAIMS,'ekug','ekuh','ekua']
BOUNDARIES={'ekt6':{'ektx','ekt5'},'ekua':{'ekt5','ekt7'},'ekug':{'ekt6'},'ekuh':{'ekt6'}}|{n:{'ekt6',con} for n,(con,fs) in CONSEQUENTS.items() if n!='ekua'}

def quantified_fields(root):return NAME_VARIABLES if root=='ekuh' else PRINCIPLE_VARIABLES if root=='ekua' else VARIABLES
def source_fields(root):return BUDGET if root=='ekua' else TOTAL
def is_universal(root):return root not in ('ekug','ekuh')

@lru_cache(None)
def core():return parse(read(CORE))

@lru_cache(None)
def boundary(root):
    doc=extract_document(core(),roots=[root],statement_indices=[]).document
    bounds=NUM|{'bg','be','sjd','sky','soy','szi','shu','sedi'}|BOUNDARIES.get(root,set())
    if root in ('ekui','ekuj','ekuk','ekul','ekum','ekun','ekuo','ekup','ekur','ekut'):
        bounds|=set(QROOTS)|{'ekui','ekuj','ekuq','ekus'}
        bounds.discard(root)
    abstract(doc,bounds);return extract_document(doc,roots=[root],statement_indices=[]).document

@lru_cache(None)
def fixture(root,mode='native'):
    doc=deepcopy(boundary(root));d=next(d for d in doc['declarations'] if d['name']==root)
    if mode.startswith('slot:'):
        doc=retag(doc)
        for dec in doc['declarations']:
            if dec['kind']=='primitive':
                dec['parameters']=['individual' if isinstance(s,dict) and s.get('kind')=='function' else s for s in dec['parameters']]
                if isinstance(dec['result'],dict) and dec['result'].get('kind')=='function':dec['result']='individual'
            else:
                for p in dec['parameters']:
                    if isinstance(p['sort'],dict) and p['sort'].get('kind')=='function':p['sort']='individual'
        d=next(d for d in doc['declarations'] if d['name']==root);body=d['body'] if root=='ekuh' else d['body']['body'];pivot=int(mode.split(':')[1]);retained=None
        for i,(n,t) in enumerate(quantified_fields(root)):
            assert body['kind']==('forall' if is_universal(root) else 'exists')
            if i==pivot:retained={k:body[k] for k in ('kind','variable','sort')}
            else:d['parameters'].append(dict(name=body['variable'],sort=body['sort']))
            body=body['body']
        if root=='ekuh':d['body']=retained|dict(body=body)
        else:d['body']['body']=retained|dict(body=body)
    slots=[]
    for i,p in enumerate(d['parameters']):
        n='jmep'+number_word(i);slots.append((n,p['sort']));doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=root,arguments=[dict(kind='call',symbol=n,arguments=[]) for n,s in slots])
    if d['result']=='content':
        if not any(x['name']=='ri' for x in doc['declarations']):doc['declarations'].append(dict(kind='primitive',name='ri',parameters=[],result='situation'))
        expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='ri',arguments=[]))
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(root,values,model,mode='native',domain=DOMAIN):
    doc,slots=fixture(root,mode);assert len(values)==len(slots),(root,len(values),len(slots))
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|model|{n:lambda x=x:x for (n,s),x in zip(slots,values)}
    return evaluate_document(doc,individuals=domain,situations=('case','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=700000,memoize_definitions=True,memoize_expressions=True)[0]['value']

@lru_cache(None)
def budget_checks():
    cuts,m=arithmetic();c,r=cuts.make,cuts.read;values,by=setting(cuts);norm=normalize(cuts);cases=0
    # Independent finite totals: area 8, K duration 15/8, hence scale 15.
    row={n:by[n] for n,t in BUDGET if n in by}|dict(frame='K',scope='section8',region=scalar(cuts,lambda *xs:0),lower=c(Q(-5,8)),upper=c(Q(5,4)),area=c(8),arriving=c(525),returning=c(Q(525,4)),transmitted=c(0),mechanical=c(270),other=c(0))
    # The physical correspondence itself is checked with a domain predicate.
    from noema.finite_semantics import FunctionValue
    from scripts.check_material_relative_frame import RS
    row['region']=FunctionValue((RS,)*4,'truth',lambda *xs:True)
    expected=norm([row[n] for n,t in BUDGET]);base=[row[n] for n,t in BUDGET];mm=m|{'eisu2':lambda *xs:norm(xs)==expected}
    assert run('ekt5',base,mm);cases+=1
    for i in range(len(base)):assert not run('ekt5',mutate(base,i,BUDGET,fixture('ekt5')[1],cuts),mm),BUDGET[i];cases+=1
    for field,value in [('upper',Q(-5,8)),('area',0),('area',-1),('arriving',-1),('returning',-1),('transmitted',-1)]:
        bad=row|{field:c(value)};assert not run('ekt5',[bad[n] for n,t in BUDGET],m|{'eisu2':lambda *xs:True});cases+=1
    for field in ('mechanical','other'):
        bad=row|{field:c(-9)};assert run('ekt5',[bad[n] for n,t in BUDGET],m|{'eisu2':lambda *xs:True});cases+=1
    unknowns(lambda model:run('ekt5',base,model),mm,('eisu2',))
    assert not run('ekt7',[row[n] for n,t in ENERGIES],m);cases+=1
    # Full physical assembly: independently evaluate the inverse-front region.
    def inside_k(x,y,z,t):return abs(Q(5,4)*(x+3*t))<=10 and abs(y)<=9 and abs(z)<=8 and -4<=Q(5,4)*(t+Q(3,25)*x)<=4 and -1<=t<=1
    row['region']=FunctionValue((RS,)*4,'truth',lambda *xs:inside_k(Q(5,4)*(r(xs[0])-3*r(xs[3])),r(xs[1]),r(xs[2]),Q(5,4)*(r(xs[3])-Q(3,25)*r(xs[0]))) and r(xs[0])<=3*r(xs[3]))
    expected=norm([row[n] for n,t in BUDGET]);full=norm(values)
    mm=m|{'ektx':lambda *xs:norm(xs)==full,'ekt5':lambda *xs:norm(xs)==expected,'eisls':lambda *xs:c(-1),'eislt':lambda *xs:c(1)}
    assert run('ekt6',values,mm);cases+=1
    for i in range(len(values)):assert not run('ekt6',mutate(values,i,TOTAL,fixture('ekt6')[1],cuts),mm),TOTAL[i];cases+=1
    for symbol in ('ektx','ekt5'):assert not run('ekt6',values,mm|{symbol:lambda *xs:False});cases+=1
    unknowns(lambda model:run('ekt6',values,model),mm,('ektx','ekt5'))
    # No conservation, work-product or pressure conclusion is a premise.
    assert not prior_run('ektz',[by[n] for n in ('incoming','outgoing','work')],m);cases+=1
    assert not prior_run('ekt4',values,m);cases+=1
    return dict(cases=cases,all_finite_budget_roles_and_102_shared_slots_checked=True,same_area_interval_units_and_physical_roles=True,conservation_not_in_adoption=True,signed_nonmechanical_and_mechanical_exchange_preserved=True)

@lru_cache(None)
def equation_checks():
    cuts,m=arithmetic();c,r=cuts.make,cuts.read;_,by=setting(cuts);cases=0
    for speed in (-3,0,3):
        for angle in (Q(1,3),Q(4,5),1):
            ratio=Q(speed,5);den=1-ratio*ratio;num=1-2*ratio*angle+ratio*ratio;A=Q(5);pi=Q(3,4)
            returnedA=A*num/den;returnedcos=(2*ratio-(1+ratio*ratio)*angle)/num
            incoming=A*A/(8*pi)*(5*angle-speed);outgoing=returnedA**2/(8*pi)*(speed-5*returnedcos)
            pressure=2*A*A/(8*pi)*(angle-ratio)**2/den;work=pressure*speed
            assert incoming-outgoing==work;cases+=1
            current=by|{n:c(x) for n,x in dict(speed=speed,anglecos=angle,pi=pi,amplitude=A,labamplitude=returnedA,labanglecos=returnedcos,incoming=incoming,outgoing=outgoing,pressure=pressure,work=work).items()}
            for root in ('ekuu','ekuv'):assert run(root,[current[n] for n,t in TOTAL],m);cases+=1
            for root,field in [('ekuu','incoming'),('ekuv','outgoing')]:
                bad=current|{field:c(r(current[field])+1)};assert not run(root,[bad[n] for n,t in TOTAL],m);cases+=1
            for root,fs in [('ektz',('incoming','outgoing','work')),('ekt2',('pressure','speed','work'))]:assert prior_run(root,[current[n] for n in fs],m);cases+=1
            assert prior_run('ekt4',[current[n] for n,t in TOTAL],m);cases+=1
    for P in (0,2,13):assert prior_run('ekt2',list(map(c,(P,0,0))),m);cases+=1
    for transmitted,other,mechanical in [(0,0,3),(7,-4,2),(2,5,-3)]:
        returning=Q(11);arriving=returning+transmitted+mechanical+other;nums=(arriving,returning,transmitted,mechanical,other)
        assert run('ekt7',list(map(c,nums)),m);cases+=1
        for i in range(5):
            bad=list(nums);bad[i]+=1;assert not run('ekt7',list(map(c,bad)),m);cases+=1
    unknowns(lambda model:run('ekt7',list(map(c,nums)),model),m,('sca',))
    return dict(cases=cases,all_five_conservation_terms_distinguished=True,printed_flux_pressure_and_work_compared=True,zero_speed_work_does_not_determine_pressure=True,numerical_examples_not_restrictions_on_source_setting=True)

@lru_cache(None)
def quantifier_checks():
    cases=0
    for root in QROOTS:
        fields=quantified_fields(root);source=source_fields(root);isname=root=='ekuh';pred='ekt5' if root=='ekua' else 'ekt6'
        for pivot,(variable,sort) in enumerate(fields):
            for target in ((False,True) if sort=='c' else ('a','b','unavailable')):
                assigned={n:False if t=='c' else ('a' if i%2==0 else 'b') for i,(n,t) in enumerate(source)}|dict(context='case')
                if root!='ekua':assigned.update(frame='a',light='a',scope='b')
                if isname:assigned.update(patch='a',pressure='b')
                assigned[variable]=target;row=tuple(assigned[n] for n,t in source);values=[assigned[n] for i,(n,t) in enumerate(fields) if i!=pivot]
                if isname:values=['a','b','case',*values]
                mm={'ra':lambda:'a','tc':lambda:'a','eisrx':lambda:'b',pred:lambda *xs,row=row:xs==row};mode=f'slot:{pivot}'
                if is_universal(root):
                    con,fs=CONSEQUENTS[root];expected=tuple(assigned[n] for n,t in fs)
                    assert run(root,values,mm|{con:lambda *xs:False},mode,('a','b'))==(target=='unavailable');cases+=1
                    assert run(root,values,mm|{con:lambda *xs,expected=expected:xs==expected},mode,('a','b'));cases+=1
                else:
                    assert run(root,values,mm,mode,('a','b'))==(target!='unavailable');cases+=1
                    assert not run(root,values,mm|{pred:lambda *xs:False},mode,('a','b'));cases+=1
            unknowns(lambda model:run(root,values,model,mode,('a','b')),mm|({CONSEQUENTS[root][0]:lambda *xs:True} if is_universal(root) else {}),(pred,))
        cuts,m=arithmetic();native=['patch',cuts.make(5),'case'] if isname else []
        model=m|{'tc':lambda:cuts.make(5),pred:lambda *xs:True}|({CONSEQUENTS[root][0]:lambda *xs:True} if is_universal(root) else {})
        refused(lambda:run(root,native,model));cases+=1
    assert len(VARIABLES)==98 and len(NAME_VARIABLES)==96
    return dict(cases=cases,all_98_shared_and_96_naming_slots_checked=True,general_principle_all_budget_roles_quantified=True,boolean_side_and_native_infinite_domains_preserved=True)

@lru_cache(None)
def presentation_checks():
    rows={
      'ekuk':{'uh':{('first','author','ekub','section8','case')},'zdg':{('first','author','ekub','section8','case')}},
      'ekul':{'uh':{('second','author','ekuc','section8','case')}},
      'ekum':{'eisch':{('principlename','ekua','section8','case')},'zc':{('third','author','ekui','ekud','section8','case')},'uh':{('third','author','ekud','section8','case')},'eisra':{('third','author','paper',node,prev,'ekud','section8','case') for node,prev in [('first','ekub'),('second','ekuc')]}},
      'ekun':{'eislo':{('pressurename','ekuh','paper','case')},'eisra':{('fourth','author','paper','third','ekud','ekue','section8','case')},'zc':{('fourth','author','ekuj','ekuf','section8','case')},'uf':{('author','fourth','display','case')},'ue':{('fourth','display','case')}},
      'ekup':{'eisox':{('display','ekuf','case')}},
      'ekur':{'eir3':{('first','author','paper','ekuq','case')},'ue':{('previous','first','case')}},
      'ekut':{'eir3':{('display','author','paper','ekus','case')},'ue':{('fourth','display','case')}},
    };cases=0
    for root,rs in rows.items():cases+=perturb(lambda model:run(root,[],model),{n:relation(r) for n,r in rs.items()},rs)
    merged={}
    for root in ('ekuk','ekul','ekum','ekun'):
        for n,rs in rows[root].items():merged.setdefault(n,set()).update(rs)
    merged['ue'].update({(a,b,'case') for a,b in [('first','second'),('second','third'),('third','fourth')]})
    cases+=perturb(lambda model:run('ekuo',[],model),{n:relation(rs) for n,rs in merged.items()},merged)
    # Verify cited premise contents separately, in one shared situation. They
    # deliberately exclude the conclusion, and presentation never executes them.
    from noema.finite_semantics import Content
    for root,names in [('ekui',('ekug','ekub','ekuc','ekua')),('ekuj',('ekug','ekub','ekuc','ekud','ekue'))]:
        mm={n:lambda:Content(('case','other'),(True,False)) for n in names}
        assert run(root,[],mm);cases+=1
        for n in names:
            assert not run(root,[],mm|{n:lambda:Content(('case','other'),(False,False))});cases+=1
        unknowns(lambda model:run(root,[],model),mm,names)
    return dict(cases=cases,four_sentences_order_and_distinct_nodes=True,obviousness_energy_principle_two_expressions_and_work_reference_bound=True,pressure_name_condition_colon_display_and_attribution=True,quoted_claims_not_executed_to_establish_presentation=True)

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert len(new.document['statements'])==404 and new.document['statements'][:402]==old.document['statements']
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    assert selection_binding(new,[400,401])==selection_binding(old,[400,401])
    load_annotations(ROOT,BASIS,ANNOTATIONS);past=json.loads(read('data/mirror-energy-work-identifiers-v1.json'))['entries'];entries=json.loads(read(ANNOTATIONS))['entries'];assert entries[:len(past)]==past and len(entries)==len(past)+2
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    deps=set(selection_binding(new,INDICES)['dependencies']);assert set(MEANINGS)|{'eisud','eisu2','ektx','ektz','ekt2','ekt4','zdg','eisch','eislo'}<=deps
    assert not {'ekbw','ekbx','ekby','ekbz'}&deps
    for style in ('compact','full'):
        body=format_graph(core(),style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core()
    reading=json.loads(read(READING));assert reading==build_reading();validate_hashes(ROOT,reading['source_sha256'])
    assert reading['reviewed_prose_characters']==359 and reading['reviewed_math_elements']==5
    return dict(new_definitions=len(MEANINGS),new_general_relations=1,new_reference_individuals=len(PRIMITIVES)-1,all_402_previous_statements_and_meanings_preserved=True,all_four_sentences_and_pressure_display_collated=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,json.dumps(build_reading(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('budget',budget_checks),('equations',equation_checks),('quantifiers',quantifier_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    helpers=('compose_limits','compose_material_relative_frame','compose_relativity_conjecture','compose_two_postulates','compose_doppler_infinity','compose_field_equations','compose_mirror_energy_work','compose_mirror_surface_pressure','compose_mirror_wave_quantities','check_coordinate_correspondence','check_clock_site_time','check_resting_charge_force','check_material_relative_frame','check_light_energy_ratio','check_mirror_energy_work','check_reflected_light_inquiry','check_wave_cycle_frequency','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(json.loads(read(READING))['source_sha256'])|{READING,DOC,*DEPENDENCIES,'scripts/compose_mirror_energy_principle.py','scripts/read_mirror_energy_principle.py','scripts/check_mirror_energy_principle.py','tests/test_mirror_energy_principle.py',*(f'scripts/{n}.py' for n in helpers)}
    return dict(status='mirror_energy_principle_and_pressure_presentation_checked',document=FULL,**results,alignment=dict(segments=json.loads(read(READING))['segments']),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
