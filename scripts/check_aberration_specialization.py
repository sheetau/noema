"""Check the whole general law, the actual right angle and its negative ratio."""
from functools import lru_cache
from fractions import Fraction as Q
from itertools import product
import json,re,xml.etree.ElementTree as ET
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_clock_site_time import unknowns,forbidden,relation,perturb
from scripts.check_conductor_cases import sentinel,same_value
from scripts.check_material_relative_frame import NUM,RS
from scripts.check_aberration_line import setup,run as line_run
from scripts.check_velocity_angle_measure import branch_model
from scripts.check_wave_cycle_frequency import refused
from scripts.check_resting_charge_force import retag
from scripts.check_aberration_presentation import CONSTANTS,DOMAIN
from scripts.compose_aberration_specialization import *

CONSTANTS=CONSTANTS|{'eissz':'lawintro','eiss2':'specialdisplay','eiss3':'aberrationname'}
DOMAIN=tuple(dict.fromkeys([*DOMAIN,*CONSTANTS.values()]))
DOC='docs/aberration-specialization-v1.md';SOURCE='data/einstein-aberration-specialization-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';FACSIMILE='artifacts/written-facsimiles-v1/einstein-1905-unlp-p912-0.jpg'
DEPENDENCIES=('reports/aberration-presentation-v1.json','reports/aberration-line-v1.json','reports/doppler-specialization-v1.json')
BOUNDS={'ekhn':{'ekgy'},'ekhp':{'ekhn','ekgo'},'ekhq':{'ekhn','ekho'},'ekhc':{'ekgy','ekgo'}}

@lru_cache(None)
def core():return parse(read(CORE))

@lru_cache(None)
def fixture(name,mode='native'):
    doc=extract_document(core(),roots=[name],statement_indices=[]).document
    bounds=NUM|{'bg','sjd','sky','soy','szi','shu','ejor','sedi'}|BOUNDS.get(name,set())
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
        d=next(d for d in doc['declarations'] if d['name']==name);body=d['body']['body'];pivot=int(mode.split(':')[1]);retained=None
        for i in range(len(VARIABLES)):
            assert body['kind']=='forall'
            if i==pivot:retained={k:body[k] for k in ('kind','variable','sort')}
            else:d['parameters'].append(dict(name=body['variable'],sort=body['sort']))
            body=body['body']
        d['body']['body']=retained|{'body':body}
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[]
    for i,p in enumerate(d['parameters']):
        n='jabs'+number_word(i);slots.append((n,p['sort']));doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=name,arguments=[dict(kind='call',symbol=n,arguments=[]) for n,s in slots])
    if d['result']=='content':
        if not any(x['name']=='ri' for x in doc['declarations']):doc['declarations'].append(dict(kind='primitive',name='ri',parameters=[],result='situation'))
        expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='ri',arguments=[]))
    elif isinstance(d['result'],dict):
        doc['declarations'].append(dict(kind='primitive',name='jabscapture',parameters=[d['result']],result='truth'));expr=dict(kind='call',symbol='jabscapture',arguments=[expr])
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,values,model,mode='native',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(values)==len(slots),(name,len(values),len(slots));captured=[]
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|model|{n:lambda x=x:x for (n,s),x in zip(slots,values)}
    def capture(x):captured.append(x);return True
    mm['jabscapture']=capture
    result=evaluate_document(doc,individuals=domain,situations=('case','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=700000,memoize_definitions=True,memoize_expressions=True)[0]['value']
    return captured[0] if captured else result

@lru_cache(None)
def numeric_checks():
    cuts,m=setup();c,r=cuts.make,cuts.read;cases=0
    # The RHS identity holds algebraically even outside the physical statement's domain.
    for V,ratio in product((Q(1),Q(5),Q(13)),(Q(-2),Q(-3,5),Q(0),Q(1,100),Q(3,5),Q(99,100),Q(1),Q(2))):
        speed=V*ratio
        assert r(run('ekhm',list(map(c,(V,speed))),m))==-ratio;cases+=1
        assert r(run('sdo2',list(map(c,(V,speed,0))),m))==-ratio;cases+=1
        assert r(run('ekhm',list(map(c,(V*7,speed*7))),m))==-ratio;cases+=1
        if ratio:assert r(run('ekhm',list(map(c,(V,speed))),m))!=ratio;cases+=1
    unknowns(lambda mm:run('ekhm',list(map(c,(5,3))),mm),m,('sjd','shv','bf'))
    return dict(cases=cases,negative_ratio_matches_zero_cosine_general_rhs=True,scale_invariant_and_negative_sign_preserved=True,outside_domain_algebra_not_physical_claim=True)

def setting_values(cuts,name='ekhn'):
    slots=fixture(name)[1]
    return [n if t=='a' else 'case' if t=='d' else sentinel(s,i+1,cuts) for i,((n,t),(_,s)) in enumerate(zip(SETTING,slots))]

@lru_cache(None)
def condition_checks():
    cuts,m=setup();c,r=cuts.make,cuts.read;slots=fixture('ekhn')[1];values=setting_values(cuts);pos={n:i for i,(n,t) in enumerate(SETTING)};cases=0
    # P=4 is solely a branch-boundary diagnostic model, never the production value of pi.
    for n,x in dict(light=5,speed=3,pi=4,angle=2,anglecos=0,newanglecos=Q(4,5),ax=0,ay=1,az=0).items():values[pos[n]]=c(x)
    gate=lambda *xs:all(same_value(x,y,s,cuts) for x,y,(_,s) in zip(xs,values,slots))
    mm=m|{'ekgy':gate};assert run('ekhn',values,mm);cases+=1
    for i,(n,s) in enumerate(slots):
        changed=values[:];changed[i]=sentinel(s,100+i,cuts);assert not run('ekhn',changed,mm),(i,n);cases+=1
    for angle in (-2,0,1,3,4,6):
        changed=values[:];changed[pos['angle']]=c(angle)
        assert not run('ekhn',changed,m|{'ekgy':lambda *xs:True});cases+=1
    changed=values[:];changed[pos['pi']]=c(8);assert not run('ekhn',changed,m|{'ekgy':lambda *xs:True});cases+=1
    unknowns(lambda model:run('ekhn',values,model),mm,('ekgy','sca','shv'))
    # Independently execute the inherited real-angle branch body for spatial directions.
    for n,co,si,angle in (((1,0,0),1,0,0),((-1,0,0),-1,0,4),((0,1,0),0,1,2),((0,0,-1),0,1,2)):
        actual=list(map(c,(*n,3,co,si,0,0,4,angle)))
        assert run('ekdq',actual,branch_model(cuts,m));cases+=1
        actual[-1]=c(2);assert run('ekdq',actual,branch_model(cuts,m))==(co==0);cases+=1
    # The line reading's true cosine is 4/5, not the source's printed -3/5.
    assert r(line_run('ekgr',list(map(c,(5,3,0,1,0))),m))==Q(4,5);cases+=1
    assert not run('ekgo',values,m) and not run('ekho',values,m);cases+=2
    values[pos['newanglecos']]=c(Q(-3,5));assert run('ekgo',values,m) and run('ekho',values,m);cases+=2
    for n,x in (('newanglecos',Q(3,5)),('newanglecos',Q(-5,3)),('light',10),('speed',1)):
        changed=values[:];changed[pos[n]]=c(x);assert not run('ekho',changed,m);cases+=1
    unknowns(lambda model:run('ekho',values,model),m,('sca','sjd'))
    return dict(cases=cases,all_65_setting_roles_bound=True,actual_old_angle_equals_same_pi_over_two=True,literal_line_inconsistency_preserved=True,boundary_model_not_exact_pi=True)

@lru_cache(None)
def universal_checks():
    cases=0
    for root,premise,conclusion in [('ekhc','ekgy','ekgo'),('ekhp','ekhn','ekgo'),('ekhq','ekhn','ekho')]:
        for pivot,(name,t) in enumerate(VARIABLES):
            for target in ('a','b','unavailable'):
                expected={n:'a' for n,t in SETTING};expected.update(context='case',scope='b');expected[name]=target
                row=tuple(expected[n] for n,t in SETTING);vals=[expected[n] for i,(n,t) in enumerate(VARIABLES) if i!=pivot]
                mm={'ra':lambda:'a','tc':lambda:'a','eisrx':lambda:'b',premise:lambda *xs,row=row:tuple(xs)==row,conclusion:lambda *xs:False}
                assert run(root,vals,mm,'slot:'+str(pivot),('a','b'))==(target=='unavailable');cases+=1
                assert run(root,vals,mm|{conclusion:lambda *xs,row=row:tuple(xs)==row},'slot:'+str(pivot),('a','b'));cases+=1
        unknowns(lambda model:run(root,vals,model,'slot:'+str(pivot),('a','b')),mm,(premise,conclusion))
        cuts,m=setup();refused(lambda root=root:run(root,[],m|{'tc':lambda:cuts.make(5),premise:lambda *xs:True,conclusion:lambda *xs:True}))
    return dict(cases=cases,contents=3,universal_slots_each=61,full_general_scope_and_same_special_assignment=True,unknown_consequents_rejected_even_under_false_premise=True)

@lru_cache(None)
def presentation_checks():
    rows={
     'ekhr':{'eisox':{('angledisplay','ekhc','case')},'eisch':{('aberrationname','ekhc','scope','case')},'uh':{('lawintro','author','ekhc','scope','case')}},
     'ekhs':{'eissb':{('lawintro','angledisplay','author','ekhp','ekhq','scope','case')},'eissp':{('ekhq','scope','case')},'uf':{('author','lawintro','specialdisplay','case')},'ue':{('lawintro','specialdisplay','case')}},
     'ekhw':{'eisox':{('specialdisplay','ekhq','case')}},
     'ekhv':{'eir3':{('lawintro','author','paper','ekhu','case')},'ue':{('angledisplay','lawintro','case')}},
     'ekhy':{'eir3':{('specialdisplay','author','paper','ekhx','case')},'ue':{('lawintro','specialdisplay','case')}}}
    cases=0
    for root,rs in rows.items():cases+=perturb(lambda mm:run(root,[],mm),{n:relation(vs) for n,vs in rs.items()},rs)
    whole={n:relation(set().union(*(rows[root].get(n,set()) for root in ('ekhr','ekhs')))) for n in set(rows['ekhr'])|set(rows['ekhs'])}
    assert run('ekht',[],whole|{n:forbidden for n in ('ekhc','ekhp','ekhq')});cases+=1
    for n in whole:
        assert not run('ekht',[],whole|{n:lambda *xs:False});cases+=1
    return dict(cases=cases,law_name_general_scope_actual_angle_clarity_and_display_connected=True,quoted_physics_not_evaluated=True)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));math={x['id']:x for x in inv['math']};segments=[]
    readings={'M0341':'φ=π/2','M0342':'cosφ′=−v/V'}
    for i in range(194,196):
        u=inv['units'][i];assert digest(u['text'].encode())==u['text_sha256']
        segments.append(dict(unit=u['id'],unit_sha256=u['text_sha256'],text=u['text'],range=[0,len(u['text'])],statements=[377+i-194],math=[dict(id=n,sha256=math[n]['sha256'],reading=readings[n]) for n in u['math_ids']],source_nonblank_characters=len(re.sub(r'\s|\[M\d+\]','',u['text']))))
    assert 'Aberrationsgesetz in seiner allgemeinsten Form' in segments[0]['text'] and 'einfache Gestalt' in segments[0]['text']
    tokens=[x.text for x in ET.fromstring(math['M0342']['mathml']).iter() if x.text]
    assert tokens.count('=')==1 and tokens.count('−')==1
    return dict(status='named_general_law_and_right_angle_form_collated',segments=segments,observations=LIMITS,source_sha256={p:digest((ROOT/p).read_bytes()) for p in (INVENTORY,FACSIMILE,DOC)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert len(new.document['statements'])==379 and new.document['statements'][:377]==old.document['statements']
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    ann=load_annotations(ROOT,BASIS,ANNOTATIONS);assert ann.annotations['entries'][-1]['forms'][0]['text']=='Aberrationsgesetz'
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    for style in ('compact','full'):
        body=format_graph(core(),style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core()
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=len(MEANINGS),new_general_relations=0,new_references=3,old_377_statements_and_judgments_preserved=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('numeric',numeric_checks),('condition',condition_checks),('universal',universal_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    helpers=('check_coordinate_correspondence','check_clock_site_time','check_conductor_cases','check_material_relative_frame','check_aberration_line','check_aberration_presentation','check_wave_cycle_frequency','check_resting_charge_force','check_velocity_angle_measure','compose_aberration_presentation','compose_material_relative_frame','compose_relativity_conjecture','compose_two_postulates','compose_limits','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,*DEPENDENCIES,'scripts/compose_aberration_specialization.py','scripts/check_aberration_specialization.py','tests/test_aberration_specialization.py',*(f'scripts/{n}.py' for n in helpers)}
    rows=[dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],statements=s['statements'],definitions=list(MEANINGS),status='explicit_interpretive_annotation') for s in source_record()['segments']]
    return dict(status='named_general_aberration_law_and_right_angle_display_connected',document=FULL,**results,alignment=dict(segments=rows),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})

