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
from scripts.compose_density_unit_scope import *
from scripts.review_density_unit_scope import DOC,SOURCE,INVENTORY,READING,build_reading

CONSTANTS=CONSTANTS|{'eistk':'section8','eistl':'densitysentence','eiscg':'relativity'}
DOMAIN=tuple(dict.fromkeys([*DOMAIN,*CONSTANTS.values()]))
DEPENDENCIES=('reports/density-relativity-v1.json','reports/radiative-density-v1.json')
BOUNDS={'eklp':{'eklf'},'eklq':{'eklp','eklg'},'eklr':{'eklp','eklh'},'ekls':{'eifj','eklq'}}

@lru_cache(None)
def core():return parse(read(CORE))

@lru_cache(None)
def fixture(name,mode='native'):
    doc=extract_document(core(),roots=[name],statement_indices=[]).document
    bounds=NUM|{'bg','sjd','sky','soy','szi','shu','sedi'}|BOUNDS.get(name,set())
    if name in ('eklt','eklv'):bounds|={'eifj','eklq','eklr','ekls'}
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
    cuts,m=setup();c,r=cuts.make,cuts.read;slots=fixture('eklp')[1];cases=0
    values=[n if t=='a' else 'case' if t=='d' else sentinel(sort,i+1,cuts) for i,((n,t),(_,sort)) in enumerate(zip(BASE,slots))];pos={n:i for i,(n,t) in enumerate(BASE)}
    values[pos['coefficient']]=c(Q(5,16))
    expected=[]
    for frame in ('frame',CONSTANTS['zbm']):expected.append(tuple(frame if n=='frame' else values[pos[n]] for n,t in COEFFICIENT))
    sorts=[slots[pos[n]] for n,t in COEFFICIENT]
    norm=lambda xs:tuple(r(x) if isinstance(sort,dict) else x for x,(_,sort) in zip(xs,sorts))
    rows={'eiste':{norm(row) for row in expected}}
    mm=m|{'eklf':lambda *xs:gate(xs,values,slots,cuts),'eiste':lambda *xs:norm(xs) in rows['eiste']}
    cases+=perturb(lambda model:run('eklp',values,model),mm,rows,norm)
    for i,(_,sort) in enumerate(slots):
        bad=values[:];bad[i]=sentinel(sort,100+i,cuts)
        assert not run('eklp',bad,mm),(i,BASE[i]);cases+=1
    # A bad energy unit passed the old predicate because it was unused there.
    bad=values[:];bad[pos['energyunit']]='other'
    assert not run('eklp',bad,mm|{'eklf':lambda *xs:True});cases+=1
    assert run('eklp',values,mm|{'eistj':forbidden,'ekkz':forbidden,'ekk4':forbidden});cases+=1
    unknowns(lambda model:run('eklp',values,model),mm,('eklf','eiste'))
    return dict(cases=cases,both_frame_calibrations_and_all_their_arguments_required=True,uncalibrated_energy_unit_rejected=True,density_model_adoption_not_moved_into_premise=True)

@lru_cache(None)
def quantifier_checks():
    cases=0
    for name,conclusion in [('eklq','eklg'),('eklr','eklh')]:
        for pivot,(var,sort) in enumerate(VARIABLES):
            mode=f'slot:{pivot}';base={n:('a' if i%2==0 else 'b') for i,(n,t) in enumerate(VARIABLES)};values=[base[n] for i,(n,t) in enumerate(VARIABLES) if i!=pivot]
            for target in ('a','b'):
                expected=base|{var:target,'frame':'a','light':'a','scope':'b','context':'case'};row=tuple(expected[n] for n,t in BASE)
                mm={'ra':lambda:'a','tc':lambda:'a','eisrx':lambda:'b','eklp':lambda *xs,row=row:xs==row,conclusion:lambda *xs,row=row:xs==row}
                assert run(name,values,mm,mode,('a','b'));cases+=1
                wrong=expected|{var:'b' if target=='a' else 'a'};badrow=tuple(wrong[n] for n,t in BASE)
                assert not run(name,values,mm|{conclusion:lambda *xs,badrow=badrow:xs==badrow},mode,('a','b'));cases+=1
            assert run(name,values,mm|{'eklp':lambda *xs:False,conclusion:lambda *xs:False},mode,('a','b'));cases+=1
            unknowns(lambda model:run(name,values,model,mode,('a','b')),mm,('eklp',conclusion))
        refused(lambda:run(name,[],{'eklp':lambda *xs:False,conclusion:lambda *xs:True,'tc':lambda:'a'}));cases+=1
    return dict(cases=cases,all_60_quantified_roles_same_in_premise_and_conclusion=True,all_values_not_only_one_success=True,infinite_real_function_domains_refused=True)

@lru_cache(None)
def presentation_checks():
    cases=0
    for first in (False,True):
        for second in (False,True):
            assert run('ekls',[],{'eifj':lambda a=first:Content(('case','other'),(a,a)),'eklq':lambda b=second:Content(('case','other'),(b,b))})==(first and second);cases+=1
    rows={'eisch':{('relativity','eifj','section8','case')},'uh':{('densitysentence','author','eklq','section8','case'),('densitysentence','author','eklr','section8','case')},'zc':{('densitysentence','author','ekls','eklr','section8','case')}}
    mm={n:relation(rs) for n,rs in rows.items()};cases+=perturb(lambda model:run('eklt',[],model),mm,rows)
    assert not run('eklt',[],mm|{'zc':relation({('densitysentence','author','eklr','ekls','section8','case')})});cases+=1
    outer={'eir3':{('densitysentence','author','paper','eklu','case')},'ue':{('intensityclaim','densitysentence','case')}}
    cases+=perturb(lambda model:run('eklv',[],model),{n:relation(rs) for n,rs in outer.items()},outer)
    assert not run('eklv',[],{n:lambda *xs:True for n in outer}|{'eistl':lambda:'intensityclaim'});cases+=1
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
    assert len(new.document['statements'])==386 and new.document['statements'][:INDEX]==old.document['statements'][:INDEX]
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    load_annotations(ROOT,BASIS,ANNOTATIONS)
    assert json.loads(read(ANNOTATIONS))['entries']==json.loads(read('data/density-relativity-identifiers-v1.json'))['entries']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    premise=extract_document(new.document,roots=['eklp'],statement_indices=[]).document
    names={d['name'] for d in premise['declarations']};assert 'eiste' in names and not {'eistj','ekkz','ekk4','eklb','eklc','ekld','eklg','eklh'}&names
    names=set(selection_binding(new,[INDEX])['dependencies']);assert set(MEANINGS)|{'eifj','eiscg','eiste','eistj','ekk4','ekia','eisrx','eistk','zc','uh'}<=names
    assert not {'ekli','eklj','eklk','eklm','ekln','eklo'}&names
    for style in ('compact','full'):
        body=format_graph(core(),style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core()
    r=json.loads(read(READING));assert r['supersedes_for_current_snapshot']=='data/einstein-density-relativity-sentence-reading-v1.json'
    return dict(new_definitions=len(MEANINGS),new_general_relations=0,new_reference_individuals=0,previous_385_statements_and_meanings_preserved=True,only_unregistered_first_sentence_revised=True,conclusion_adoption_excluded_from_premise=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,json.dumps(build_reading(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('model',model_checks),('quantifiers',quantifier_checks),('presentation',presentation_checks),('reading',reading_checks),('structure',structure_checks)]}
    helpers=('compose_density_relativity','compose_observed_intensity','compose_material_relative_frame','compose_relativity_conjecture','compose_two_postulates','compose_doppler_infinity','compose_limits','check_coordinate_correspondence','check_clock_site_time','check_resting_charge_force','check_conductor_cases','check_material_relative_frame','check_aberration_line','check_wave_cycle_frequency','check_radiative_density','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(json.loads(read(SOURCE))['source_sha256'])|set(json.loads(read(READING))['source_sha256'])|{SOURCE,DOC,INVENTORY,READING,*DEPENDENCIES,'scripts/compose_density_unit_scope.py','scripts/check_density_unit_scope.py','scripts/review_density_unit_scope.py','tests/test_density_unit_scope.py',*(f'scripts/{n}.py' for n in helpers)}
    u=json.loads(read(INVENTORY))['units'][202]
    return dict(status='calibrated_density_relativity_first_sentence_checked',document=FULL,**results,alignment=dict(segments=[dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,163],source=u['text'][:163],statements=[INDEX],definitions=list(MEANINGS),status='explicit_interpretive_annotation')]),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
