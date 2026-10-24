"""Check separated density premises, shared frame roles and source attribution."""
from functools import lru_cache
from fractions import Fraction as Q
import json
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import evaluate_document,Content
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,validate_hashes,selection_binding
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_clock_site_time import relation,perturb,unknowns,forbidden
from scripts.check_resting_charge_force import retag
from scripts.check_conductor_cases import sentinel,same_value
from scripts.check_material_relative_frame import NUM
from scripts.check_aberration_line import setup
from scripts.check_wave_cycle_frequency import refused
from scripts.check_radiative_density import CONSTANTS,DOMAIN
from scripts.compose_density_relativity import *
from scripts.review_density_relativity import DOC,SOURCE,INVENTORY,READING,build_reading

CONSTANTS=CONSTANTS|{'eistk':'section8','eistl':'densitysentence','eiscg':'relativity'}
DOMAIN=tuple(dict.fromkeys([*DOMAIN,*CONSTANTS.values()]))
DEPENDENCIES=('reports/radiative-density-v1.json','reports/observed-amplitude-v1.json','reports/two-postulates-v1.json','reports/relativity-conjecture-v1.json')
BOUNDS={'eklf':{'eket'},'eklg':{'ekkz','ekk4'},'eklh':{'ekkz','ekk4'},'ekli':{'eklf','eklg'},'eklj':{'eklf','eklh'},'eklk':{'eifj','ekli'}}

@lru_cache(None)
def core():return parse(read(CORE))

@lru_cache(None)
def fixture(name,mode='native'):
    doc=extract_document(core(),roots=[name],statement_indices=[]).document
    bounds=NUM|{'bg','sjd','sky','soy','szi','shu','sedi'}|BOUNDS.get(name,set())
    if name in ('eklm','eklo'):bounds|={'eifj','ekli','eklj','eklk'}
    abstract(doc,bounds);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    if mode.startswith('slot:'):
        doc=retag(doc)
        for d in doc['declarations']:
            if d['kind']=='primitive':
                d['parameters']=['individual' if isinstance(s,dict) and s.get('kind')=='function' else s for s in d['parameters']]
                if isinstance(d['result'],dict) and d['result'].get('kind')=='function':d['result']='individual'
            else:
                for p in d['parameters']:
                    if isinstance(p['sort'],dict) and p['sort'].get('kind')=='function':p['sort']='individual'
        d=next(d for d in doc['declarations'] if d['name']==name);body=d['body']['body'];pivot=int(mode.split(':')[1]);retained=None
        for i,(n,t) in enumerate(VARIABLES):
            assert body['kind']=='forall'
            if i==pivot:retained={k:body[k] for k in ('kind','variable','sort')}
            else:d['parameters'].append(dict(name=body['variable'],sort=body['sort']))
            body=body['body']
        d['body']['body']=retained|{'body':body}
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[]
    for i,p in enumerate(d['parameters']):
        n='jdrc'+number_word(i);slots.append((n,p['sort']));doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=name,arguments=[dict(kind='call',symbol=n,arguments=[]) for n,s in slots])
    if d['result']=='content':
        if not any(x['name']=='ri' for x in doc['declarations']):doc['declarations'].append(dict(kind='primitive',name='ri',parameters=[],result='situation'))
        expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='ri',arguments=[]))
    elif isinstance(d['result'],dict):
        doc['declarations'].append(dict(kind='primitive',name='jdrccapture',parameters=[d['result']],result='truth'));expr=dict(kind='call',symbol='jdrccapture',arguments=[expr])
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,values,model,mode='native',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(values)==len(slots),(name,len(values),len(slots));captured=[]
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|model|{n:lambda x=x:x for (n,s),x in zip(slots,values)}
    def capture(x):captured.append(x);return True
    mm['jdrccapture']=capture
    result=evaluate_document(doc,individuals=domain,situations=('case','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=700000,memoize_definitions=True,memoize_expressions=True)[0]['value']
    return captured[0] if captured else result

def gate(xs,ys,slots,cuts):return len(xs)==len(ys) and all(same_value(x,y,s,cuts) for x,y,(_,s) in zip(xs,ys,slots))

@lru_cache(None)
def model_checks():
    cuts,m=setup();c,r=cuts.make,cuts.read;cases=0;slots=fixture('eklf')[1]
    values=[n if t=='a' else 'case' if t=='d' else sentinel(s,i+1,cuts) for i,((n,t),(_,s)) in enumerate(zip(BASE,slots))];pos={n:i for i,(n,t) in enumerate(BASE)}
    for n,value in dict(light=5,speed=3,rate=1,ax=0,ay=1,az=0,ex=0,ey=0,ez=5,hx=5,hy=0,hz=0,amplitude=5,newamplitude=Q(25,4),coefficient=Q(5,16),pi=4,cycle=8,oldperiod=8,newperiod=Q(32,5),frequency=Q(1,8),newfrequency=Q(5,32),newoffset=2).items():values[pos[n]]=c(value)
    models=[];averages=[]
    def collect(target):
        def accept(*xs):target.append(xs);return True
        return accept
    mm=m|{'sedi':lambda x:r(x)==4,'eket':lambda *xs:gate(xs,values[:60],slots[:60],cuts),'ekkz':collect(models),'ekk4':collect(averages)}
    for name in ('eklf','eklg','eklh'):assert run(name,values,mm);cases+=1
    assert len(models)==len(averages)==2
    mp={n:i for i,(n,t) in enumerate(DENSITY_MODEL)};ap={n:i for i,(n,t) in enumerate(CYCLE)}
    for i in range(2):
        assert (models[i][mp['frame']],models[i][mp['scope']])==('frame' if i==0 else CONSTANTS['zbm'],'section8');cases+=1
        expected=(0,0,5,5,0,0) if i==0 else (0,0,Q(25,4),5,Q(15,4),0)
        assert tuple(r(models[i][mp[n]]) for n in ('ex','ey','ez','hx','hy','hz'))==expected;cases+=1
        assert r(models[i][mp['phase']](*map(c,(1,2,3,4))))==(Q(18,5) if i==0 else Q(19,4));cases+=1
        assert tuple(r(averages[i][ap[n]]) for n in ('light','coefficient','rate','offset','period','frequency','density'))==((5,Q(5,16),1,0,8,Q(1,8),Q(25,32)) if i==0 else (5,Q(5,16),Q(5,4),2,Q(32,5),Q(5,32),Q(625,512)));cases+=1
    mm=m|{'sedi':lambda x:r(x)==4,'eket':lambda *xs:gate(xs,values[:60],slots[:60],cuts),'ekkz':lambda *xs:any(gate(xs,row,fixture('ekkz')[1],cuts) for row in models),'ekk4':lambda *xs:any(gate(xs,row,fixture('ekk4')[1],cuts) for row in averages)}
    for i,(_,s) in enumerate(slots):
        bad=values[:];bad[i]=sentinel(s,100+i,cuts)
        try:results=[run(name,bad,mm) for name in ('eklf','eklg','eklh')]
        except (ValueError,ZeroDivisionError):pass
        else:assert not all(results),(i,BASE[i])
        cases+=1
    # Neither the old nor the new adoption is needed to satisfy the premise.
    assert run('eklf',values,mm|{'ekkz':forbidden,'ekk4':forbidden,'eistj':forbidden});cases+=1
    assert not run('eklg',values,mm|{'ekkz':lambda *xs:False});assert not run('eklh',values,mm|{'ekk4':lambda *xs:False});cases+=2
    for name in ('eklg','eklh'):unknowns(lambda model:run(name,values,model),mm,('ekkz','ekk4'))
    for pi,A in ((Q(4),Q(0)),(Q(3),Q(2)),(Q(4),Q(25,4))):assert r(run('ekle',[c(pi),c(A)],m))==A*A/(8*pi);cases+=1
    return dict(cases=cases,all_64_roles_connected_across_setting_and_two_conclusions=True,new_density_adoption_not_assumed_in_premise=True,distinct_phase_period_and_amplitude_in_each_frame=True,density_scope_section_eight_wave_scope_inherited=True)

@lru_cache(None)
def quantifier_checks():
    cases=0
    for name,conclusion in [('ekli','eklg'),('eklj','eklh')]:
        for pivot,(var,sort) in enumerate(VARIABLES):
            mode=f'slot:{pivot}';base={n:('a' if i%2==0 else 'b') for i,(n,t) in enumerate(VARIABLES)};values=[base[n] for i,(n,t) in enumerate(VARIABLES) if i!=pivot]
            for target in ('a','b'):
                expected=base|{var:target,'frame':'a','light':'a','scope':'b','context':'case'};row=tuple(expected[n] for n,t in BASE)
                mm={'ra':lambda:'a','tc':lambda:'a','eisrx':lambda:'b','eklf':lambda *xs,row=row:xs==row,conclusion:lambda *xs,row=row:xs==row}
                assert run(name,values,mm,mode,('a','b'));cases+=1
                wrong=expected|{var:'b' if target=='a' else 'a'};badrow=tuple(wrong[n] for n,t in BASE)
                assert not run(name,values,mm|{conclusion:lambda *xs,badrow=badrow:xs==badrow},mode,('a','b'));cases+=1
            assert run(name,values,mm|{'eklf':lambda *xs:False,conclusion:lambda *xs:False},mode,('a','b'));cases+=1
            unknowns(lambda model:run(name,values,model,mode,('a','b')),mm,('eklf',conclusion))
        refused(lambda:run(name,[],{'eklf':lambda *xs:False,conclusion:lambda *xs:True,'tc':lambda:'a'}));cases+=1
    return dict(cases=cases,all_60_quantified_roles_same_in_premise_and_conclusion=True,all_values_not_only_one_success=True,infinite_real_function_domains_refused=True)

@lru_cache(None)
def presentation_checks():
    cases=0
    for first in (False,True):
        for second in (False,True):
            assert run('eklk',[],{'eifj':lambda a=first:Content(('case','other'),(a,a)),'ekli':lambda b=second:Content(('case','other'),(b,b))})==(first and second);cases+=1
    rows={'eisch':{('relativity','eifj','section8','case')},'uh':{('densitysentence','author','ekli','section8','case'),('densitysentence','author','eklj','section8','case')},'zc':{('densitysentence','author','eklk','eklj','section8','case')}}
    mm={n:relation(rs) for n,rs in rows.items()};cases+=perturb(lambda model:run('eklm',[],model),mm,rows)
    assert not run('eklm',[],mm|{'zc':relation({('densitysentence','author','eklj','eklk','section8','case')})});cases+=1
    outer={'eir3':{('densitysentence','author','paper','ekln','case')},'ue':{('intensityclaim','densitysentence','case')}}
    cases+=perturb(lambda model:run('eklo',[],model),{n:relation(rs) for n,rs in outer.items()},outer)
    assert not run('eklo',[],{n:lambda *xs:True for n in outer}|{'eistl':lambda:'intensityclaim'});cases+=1
    return dict(cases=cases,same_relativity_principle_and_old_density_as_grounds=True,must_follow_direction_retained=True,quoted_physics_not_executed=True,author_and_document_and_prior_order_connected=True)

@lru_cache(None)
def reading_checks():
    reading=json.loads(read(READING));assert reading==build_reading();validate_hashes(ROOT,reading['source_sha256'])
    u=json.loads(read(INVENTORY))['units'][202];assert reading['source']==u['text'][:163] and reading['source_nonblank_characters']==141
    assert reading['selection']==selection_binding(load_catalog(ROOT,BASIS),[INDEX])
    assert reading['verified_full_units']==0 and not reading['whole_paragraph_complete']
    assert reading['reviewed_prose_characters']==127 and reading['reviewed_math_elements']==2
    return dict(source_range=[0,163],source_nonblank_characters=141,reviewed_prose_characters=127,reviewed_math_elements=2,first_sentence_complete_under_explicit_reading=True,whole_unit_not_certified=True)

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert len(new.document['statements'])==386 and new.document['statements'][:INDEX]==old.document['statements']
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    load_annotations(ROOT,BASIS,ANNOTATIONS);oldann=json.loads(read('data/radiative-density-identifiers-v1.json'));ann=json.loads(read(ANNOTATIONS))
    assert ann['entries'][:-1]==oldann['entries'] and ann['entries'][-1]['forms'][0]['text']=='Relativitätsprinzip'
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    ds={d['name']:d for d in new.document['declarations']};assert ds['ekll']['body']==dict(kind='call',symbol='eiscg',arguments=[])
    premise=extract_document(new.document,roots=['eklf'],statement_indices=[]).document
    assert not {'eistj','ekkz','ekk4','eklb','eklc','ekld','eklg','eklh'}&{d['name'] for d in premise['declarations']}
    names=set(selection_binding(new,[INDEX])['dependencies']);assert set(MEANINGS)|{'eifj','eiscg','eiste','eistj','ekk4','ekia','eisrx','eistk','zc','uh'}<=names
    for style in ('compact','full'):
        body=format_graph(core(),style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core()
    return dict(new_definitions=len(MEANINGS),new_general_relations=0,new_reference_individuals=2,previous_385_statements_and_meanings_preserved=True,conclusion_adoption_excluded_from_premise=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,json.dumps(build_reading(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('model',model_checks),('quantifiers',quantifier_checks),('presentation',presentation_checks),('reading',reading_checks),('structure',structure_checks)]}
    helpers=('compose_radiative_density','compose_wave_transform_application','compose_material_relative_frame','compose_relativity_conjecture','compose_two_postulates','compose_doppler_infinity','compose_limits','check_coordinate_correspondence','check_clock_site_time','check_resting_charge_force','check_conductor_cases','check_material_relative_frame','check_aberration_line','check_wave_cycle_frequency','check_radiative_density','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(json.loads(read(SOURCE))['source_sha256'])|{SOURCE,DOC,INVENTORY,READING,*DEPENDENCIES,'scripts/compose_density_relativity.py','scripts/check_density_relativity.py','scripts/review_density_relativity.py','tests/test_density_relativity.py',*(f'scripts/{n}.py' for n in helpers)}
    u=json.loads(read(INVENTORY))['units'][202]
    return dict(status='density_relativity_first_sentence_checked',document=FULL,**results,alignment=dict(segments=[dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,163],source=u['text'][:163],statements=[INDEX],definitions=list(MEANINGS),status='explicit_interpretive_annotation')]),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
