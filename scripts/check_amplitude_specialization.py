"""Check the same zero angle, amplitude-square ratio and strict form comparison."""
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
from scripts.check_aberration_line import setup
from scripts.check_velocity_angle_measure import branch_model
from scripts.check_distant_direction_geometry import run as geometry_run
from scripts.check_wave_cycle_frequency import refused
from scripts.check_resting_charge_force import retag
from scripts.check_observed_amplitude import CONSTANTS,DOMAIN
from scripts.compose_amplitude_specialization import *
CONSTANTS=CONSTANTS|{'eistc':'axialintro','eistd':'axialamplitude'}
DOMAIN=tuple(dict.fromkeys([*DOMAIN,*CONSTANTS.values()]))
DOC='docs/amplitude-specialization-v1.md';SOURCE='data/einstein-amplitude-specialization-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';FACSIMILE='artifacts/written-facsimiles-v1/einstein-1905-unlp-p912-0.jpg'
DEPENDENCIES=('reports/observed-amplitude-v1.json','reports/wave-amplitudes-v1.json','reports/doppler-specialization-v1.json')
BOUNDS={'ekiv':{'ekib'},'ekix':{'ekiv','ekij'},'ekiy':{'ekiv','ekiw'}}

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
        d=next(d for d in doc['declarations'] if d['name']==name);iscontent=d['result']=='content';body=d['body']['body'] if iscontent else d['body'];pivot=int(mode.split(':')[1]);retained=None
        fields=VARIABLES
        for i in range(len(fields)):
            assert body['kind']=='forall'
            if i==pivot:retained={k:body[k] for k in ('kind','variable','sort')}
            else:d['parameters'].append(dict(name=body['variable'],sort=body['sort']))
            body=body['body']
        if iscontent:d['body']['body']=retained|{'body':body}
        else:d['body']=retained|{'body':body}
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[]
    for i,p in enumerate(d['parameters']):
        n='jams'+number_word(i);slots.append((n,p['sort']));doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=name,arguments=[dict(kind='call',symbol=n,arguments=[]) for n,s in slots])
    if d['result']=='content':
        if not any(x['name']=='ri' for x in doc['declarations']):doc['declarations'].append(dict(kind='primitive',name='ri',parameters=[],result='situation'))
        expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='ri',arguments=[]))
    elif isinstance(d['result'],dict):
        doc['declarations'].append(dict(kind='primitive',name='jamscapture',parameters=[d['result']],result='truth'));expr=dict(kind='call',symbol='jamscapture',arguments=[expr])
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,values,model,mode='native',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(values)==len(slots),(name,len(values),len(slots));captured=[]
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|model|{n:lambda x=x:x for (n,s),x in zip(slots,values)}
    def capture(x):captured.append(x);return True
    mm['jamscapture']=capture
    result=evaluate_document(doc,individuals=domain,situations=('case','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=700000,memoize_definitions=True,memoize_expressions=True)[0]['value']
    return captured[0] if captured else result

@lru_cache(None)
def numeric_checks():
    cuts,m=setup();c,r=cuts.make,cuts.read;cases=0
    for V,ratio,A in product((Q(1),Q(5),Q(13)),(Q(-3,5),Q(0),Q(1,100),Q(3,5),Q(99,100)),(Q(0),Q(1,4),Q(3))):
        speed=V*ratio;expected=A*A*(1-ratio)/(1+ratio)
        assert r(run('ekiu',list(map(c,(V,speed,A))),m))==expected;cases+=1
        assert r(run('ekii',list(map(c,(V,speed,1,A))),m))==expected;cases+=1
        assert r(run('ekiu',list(map(c,(V*7,speed*7,A))),m))==expected;cases+=1
        if ratio and A:
            assert expected!=A*A*(1+ratio)/(1-ratio);cases+=1
    assert r(run('ekiu',list(map(c,(5,3,10))),m))==25;cases+=1
    # Formula is for the squared magnitude, not for the magnitude or a square-root denominator.
    assert r(run('ekii',list(map(c,(5,3,1,10))),m))==25!=20;cases+=1
    unknowns(lambda model:run('ekiu',list(map(c,(5,3,10))),model),m,('sjd','shv','bf','bd'))
    return dict(cases=cases,general_form_at_unit_cosine_matches_special_square_ratio=True,difference_over_sum_and_squares_preserved=True,near_light_speed_zero_amplitude_and_scaled_units_checked=True)

@lru_cache(None)
def condition_checks():
    cuts,m=setup();c,r=cuts.make,cuts.read;slots=fixture('ekiv')[1]
    values=[n if t=='a' else 'case' if t=='d' else False if t=='c' else sentinel(s,i+1,cuts) for i,((n,t),(_,s)) in enumerate(zip(SETTING,slots))]
    pos={n:i for i,(n,t) in enumerate(SETTING)};cases=0
    for n,x in dict(light=5,speed=3,amplitude=10,newamplitude=5,angle=0,anglecos=1).items():values[pos[n]]=c(x)
    gate=lambda *xs:len(xs)==len(values) and all(same_value(x,y,s,cuts) for x,y,(_,s) in zip(xs,values,slots))
    mm=m|{'ekib':gate};assert run('ekiv',values,mm);cases+=1
    for i,(n,s) in enumerate(slots):
        changed=values[:];changed[i]=not changed[i] if s=='truth' else sentinel(s,100+i,cuts)
        assert not run('ekiv',changed,mm),(i,n);cases+=1
    for angle in (-4,-1,1,2,4,8):
        changed=values[:];changed[pos['angle']]=c(angle);assert not run('ekiv',changed,m|{'ekib':lambda *xs:True});cases+=1
    for side in (False,True):
        values[pos['magneticside']]=side;assert run('ekiv',values,m|{'ekib':lambda *xs:True});assert run('ekiw',values,m);cases+=2
    for name,x in (('newamplitude',25),('newamplitude',Q(5,2)),('amplitude',5),('light',10),('speed',1)):
        changed=values[:];changed[pos[name]]=c(x);assert not run('ekiw',changed,m);cases+=1
    unknowns(lambda model:run('ekiv',values,model),m|{'ekib':lambda *xs:True},('ekib','sca'))
    unknowns(lambda model:run('ekiw',values,model),m,('sca','sjd'))
    # The existing real-angle body distinguishes 0, pi/2 and pi; pi=4 here is
    # solely the explicitly abstracted branch diagnostic, not production pi.
    for n,co,si,angle in (((1,0,0),1,0,0),((-1,0,0),-1,0,4),((0,1,0),0,1,2)):
        actual=list(map(c,(*n,3,co,si,0,0,4,angle)))
        assert geometry_run('ekdq',actual,branch_model(cuts,m));cases+=1
        actual[-1]=c(0);assert geometry_run('ekdq',actual,branch_model(cuts,m))==(co==1);cases+=1
    return dict(cases=cases,all_63_setting_roles_and_same_side_bound=True,actual_old_real_angle_zero_not_just_cosine_one=True,nonnegative_amplitudes_inherited_from_ekib=True)

@lru_cache(None)
def universal_checks():
    cases=0
    for root,conclusion in [('ekix','ekij'),('ekiy','ekiw')]:
        for pivot,(name,t) in enumerate(VARIABLES):
            for target in ((False,True) if t=='c' else ('a','b','unavailable')):
                expected={n:False if t=='c' else 'a' for n,t in SETTING};expected.update(context='case',scope='b');expected[name]=target
                row=tuple(expected[n] for n,t in SETTING);vals=[expected[n] for i,(n,t) in enumerate(VARIABLES) if i!=pivot]
                mm={'ra':lambda:'a','tc':lambda:'a','eisrx':lambda:'b','ekiv':lambda *xs,row=row:tuple(xs)==row,conclusion:lambda *xs:False}
                mode='slot:'+str(pivot)
                assert run(root,vals,mm,mode,('a','b'))==(target=='unavailable');cases+=1
                assert run(root,vals,mm|{conclusion:lambda *xs,row=row:tuple(xs)==row},mode,('a','b'));cases+=1
        unknowns(lambda model:run(root,vals,model,mode,('a','b')),mm,('ekiv',conclusion))
        cuts,m=setup();refused(lambda root=root:run(root,[],m|{'tc':lambda:cuts.make(5),'ekiv':lambda *xs:True,conclusion:lambda *xs:True}))
    return dict(cases=cases,universal_roles_each=59,same_domain_old_new_magnitudes_and_side=True,unknown_conclusion_not_vacuously_accepted=True)

@lru_cache(None)
def presentation_checks():
    rows={
     'ekiz':{'eisox':{('amplitudedisplay','ekik','case')},'eissb':{('axialintro','amplitudedisplay','author','ekix','ekiy','scope','case')},'eistb':{('ekiy','ekix','scope','case')},'uf':{('author','axialintro','axialamplitude','case')},'ue':{('axialintro','axialamplitude','case')}},
     'ekjc':{'eisox':{('axialamplitude','ekiy','case')}},
     'ekjb':{'eir3':{('axialintro','author','paper','ekja','case')},'ue':{('amplitudedisplay','axialintro','case')}},
     'ekje':{'eir3':{('axialamplitude','author','paper','ekjd','case')},'ue':{('axialintro','axialamplitude','case')}}}
    cases=0
    for root,rs in rows.items():cases+=perturb(lambda model:run(root,[],model),{n:relation(vs) for n,vs in rs.items()},rs)
    base={n:relation(vs) for n,vs in rows['ekiz'].items()}
    assert not run('ekiz',[],base|{'eistb':relation({('ekix','ekiy','scope','case')})});cases+=1
    assert not run('ekiz',[],base|{'eistb':relation({('ekiy','ekiy','scope','case')})});cases+=1
    assert run('ekiz',[],base|{n:forbidden for n in ('ekik','ekix','ekiy','eissp')});cases+=1
    return dict(cases=cases,relative_clause_same_restricted_forms_and_colon_preserved=True,strict_comparison_not_absolute_clarity_or_reverse_order=True,quoted_physics_not_executed=True)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));math={x['id']:x for x in inv['math']};segments=[]
    readings={'M0346':'φ=0','M0347':'A′²=A²(1−v/V)/(1+v/V)'}
    for i in range(198,200):
        u=inv['units'][i];assert digest(u['text'].encode())==u['text_sha256']
        segments.append(dict(unit=u['id'],unit_sha256=u['text_sha256'],text=u['text'],range=[0,len(u['text'])],statements=[381+i-198],math=[dict(id=n,sha256=math[n]['sha256'],reading=readings[n]) for n in u['math_ids']],source_nonblank_characters=len(re.sub(r'\s|\[M\d+\]','',u['text']))))
    assert segments[0]['text'].startswith('welche Gleichung') and 'einfachere' in segments[0]['text']
    tokens=[x.text for x in ET.fromstring(math['M0347']['mathml']).iter() if x.text]
    assert tokens.count('=')==1 and tokens.count('−')==1 and tokens.count('+')==1
    return dict(status='relative_clause_zero_angle_and_comparatively_simpler_square_ratio_collated',segments=segments,observations=LIMITS,source_sha256={p:digest((ROOT/p).read_bytes()) for p in (INVENTORY,FACSIMILE,'data/wave-amplitudes-facsimile-v1.json',DOC)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert len(new.document['statements'])==383 and new.document['statements'][:381]==old.document['statements']
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    oldann=json.loads(read('data/observed-amplitude-identifiers-v1.json'));ann=load_annotations(ROOT,BASIS,ANNOTATIONS)
    assert ann.annotations['entries']==oldann['entries']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    for style in ('compact','full'):
        body=format_graph(core(),style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core()
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=len(MEANINGS),new_general_relations=1,new_references=2,old_381_statements_and_judgments_preserved=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('numeric',numeric_checks),('condition',condition_checks),('universal',universal_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    helpers=('check_coordinate_correspondence','check_clock_site_time','check_conductor_cases','check_material_relative_frame','check_aberration_line','check_velocity_angle_measure','check_distant_direction_geometry','check_wave_cycle_frequency','check_resting_charge_force','check_observed_amplitude','compose_observed_amplitude','compose_aberration_presentation','compose_material_relative_frame','compose_relativity_conjecture','compose_two_postulates','compose_limits','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,*DEPENDENCIES,'scripts/compose_amplitude_specialization.py','scripts/check_amplitude_specialization.py','tests/test_amplitude_specialization.py',*(f'scripts/{n}.py' for n in helpers)}
    rows=[dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],statements=s['statements'],definitions=list(MEANINGS),status='explicit_interpretive_annotation') for s in source_record()['segments']]
    return dict(status='same_zero_angle_amplitude_square_ratio_and_strict_form_comparison_connected',document=FULL,**results,alignment=dict(segments=rows),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
