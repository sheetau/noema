"""Check the hypothetical volume separately from the actual transformed one."""
from functools import lru_cache
from fractions import Fraction as Q
from itertools import product
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
from scripts.check_conductor_cases import sentinel,same_value
from scripts.check_resting_charge_force import retag
from scripts.check_material_relative_frame import NUM
from scripts.check_light_region_slices import setup
from scripts.check_density_unit_scope import CONSTANTS as PRIOR,DOMAIN as PREVIOUS
from scripts.check_wave_cycle_frequency import refused
from scripts.compose_equal_volume_supposition import *
from scripts.review_equal_volume_supposition import DOC,SOURCE,INVENTORY,READING,build_reading

CONSTANTS=PRIOR|{'eistn':'equalvolumesentence','zvaa':'portion'}
DOMAIN=tuple(dict.fromkeys([*PREVIOUS,*CONSTANTS.values(),*[n for n,t in TOTAL if t=='a']]))
DEPENDENCIES=('reports/mean-light-energy-v1.json','reports/light-region-slices-v1.json','reports/density-unit-scope-v1.json')
BOUNDS={'ekmo':{'ekmi','ekmj'},'ekmp':{'ekmo'},'ekmt':{'ekmo'},'ekmv':{'ekmi','ekmj'},'ekms':{'ekmo','ekmt'},'ekmr':{'ekmt','ekmq'},'ekmu':{'eklq','eklr','ekmv'}}

@lru_cache(None)
def core():return parse(read(CORE))

@lru_cache(None)
def fixture(name,mode='native'):
    doc=extract_document(core(),roots=[name],statement_indices=[]).document
    bounds=NUM|{'bg','be','sjd','sky','soy','szi','shu','sedi'}|BOUNDS.get(name,set())
    if name in ('ekmw','ekmy'):bounds|={'ekms','ekmu','ekmr'}
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
        fields=COMPARISON_VARIABLES if name=='ekmr' else VARIABLES
        for i,(n,t) in enumerate(fields):
            assert body['kind']=='forall'
            if i==pivot:retained={k:body[k] for k in ('kind','variable','sort')}
            else:d['parameters'].append(dict(name=body['variable'],sort=body['sort']))
            body=body['body']
        d['body']['body']=retained|{'body':body}
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[]
    for i,p in enumerate(d['parameters']):
        n='jevs'+number_word(i);slots.append((n,p['sort']));doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=name,arguments=[dict(kind='call',symbol=n,arguments=[]) for n,s in slots])
    if d['result']=='content':
        if not any(x['name']=='ri' for x in doc['declarations']):doc['declarations'].append(dict(kind='primitive',name='ri',parameters=[],result='situation'))
        expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='ri',arguments=[]))
    elif isinstance(d['result'],dict):
        doc['declarations'].append(dict(kind='primitive',name='jevscapture',parameters=[d['result']],result='truth'));expr=dict(kind='call',symbol='jevscapture',arguments=[expr])
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,values,model,mode='native',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(values)==len(slots),(name,len(values),len(slots));captured=[]
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|model|{n:lambda x=x:x for (n,s),x in zip(slots,values)}
    def capture(x):captured.append(x);return True
    mm['jevscapture']=capture
    result=evaluate_document(doc,individuals=domain,situations=('case','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=700000,memoize_definitions=True,memoize_expressions=True)[0]['value']
    return captured[0] if captured else result

def gate(xs,ys,slots,cuts):return len(xs)==len(ys) and all(same_value(x,y,s,cuts) for x,y,(_,s) in zip(xs,ys,slots))
def values_for(cuts,root='ekmo'):
    return [n if t=='a' else 'case' if t=='d' else sentinel(s,i+1,cuts) for i,((n,t),(_,s)) in enumerate(zip(TOTAL,fixture(root)[1]))]

@lru_cache(None)
def background_checks():
    cuts,m=setup();c,r=cuts.make,cuts.read;cases=0;slots=fixture('ekmo')[1];values=values_for(cuts);pos={n:i for i,(n,t) in enumerate(TOTAL)}
    values[pos['amplitude']]=c(5);values[pos['energy']]=c(Q(100,3))
    mm=m|{n:lambda *xs:gate(xs,values,slots,cuts) for n in ('ekmi','ekmj')}
    assert run('ekmo',values,mm);cases+=1
    for i,(_,sort) in enumerate(slots):
        bad=values[:];bad[i]=sentinel(sort,100+i,cuts);assert not run('ekmo',bad,mm),(i,TOTAL[i]);cases+=1
    for name in ('ekmi','ekmj'):
        assert not run('ekmo',values,mm|{name:lambda *xs:False});cases+=1
    for n in ('amplitude','energy'):
        for x in (-1,0):
            bad=values[:];bad[pos[n]]=c(x)
            assert not run('ekmo',bad,m|{'ekmi':lambda *xs:True,'ekmj':lambda *xs:True});cases+=1
    unknowns(lambda model:run('ekmo',values,model),mm,('ekmi','ekmj'))
    return dict(cases=cases,all_70_physical_roles_shared=True,positive_old_denominators_required=True,actual_new_volume_not_forced_equal=True)

@lru_cache(None)
def comparison_checks():
    cuts,m=setup();c,r=cuts.make,cuts.read;cases=0;values=values_for(cuts);slots=fixture('ekmo')[1];pos={n:i for i,(n,t) in enumerate(TOTAL)}
    given=dict(pi=Q(3,4),amplitude=5,newamplitude=Q(25,4),volume=8,newvolume=Q(32,5),energy=Q(100,3),newenergy=Q(125,3))
    for n,x in given.items():values[pos[n]]=c(x)
    mm=m|{'ekmo':lambda *xs:gate(xs,values,slots,cuts),'sedi':lambda x:r(x)==Q(3,4)}
    hypovol=Q(8);hypoenergy=r(run('ekmn',list(map(c,(Q(3,4),Q(25,4),hypovol))),m))
    assert hypoenergy==Q(625,12) and hypoenergy!=given['newenergy'];cases+=1
    actual=values+[c(hypovol)]
    assert run('ekmp',actual,mm) and run('ekmt',actual,mm) and run('ekmq',actual,mm);cases+=3
    # The same scalar is never substituted into the actual newvolume/newenergy.
    assert r(actual[pos['newvolume']])==Q(32,5) and r(actual[pos['newenergy']])==Q(125,3);cases+=1
    assert hypoenergy/given['energy']==Q(25,16) and given['newenergy']/given['energy']==Q(5,4);cases+=1
    for hv in (Q(0),Q(-1),Q(4),Q(32,5)):
        bad=values+[c(hv)];assert not run('ekmp',bad,mm) and not run('ekmt',bad,mm);cases+=2
    assert not run('ekmq',values+[c(Q(32,5))],mm);cases+=1
    for i,(_,sort) in enumerate(slots):
        bad=actual[:];bad[i]=sentinel(sort,100+i,cuts);assert not run('ekmt',bad,mm),(i,TOTAL[i]);cases+=1
    # A separate unequal-amplitude arithmetic diagnostic of the native conclusion.
    for A,B,S in product((Q(1),Q(2)),(Q(0),Q(3)),(Q(1),Q(2))):
        row=values[:]
        for n,x in dict(amplitude=A,newamplitude=B,volume=S,energy=A*A*S/6).items():row[pos[n]]=c(x)
        assert run('ekmq',row+[c(S)],m);cases+=1
        row[pos['energy']]=c(r(row[pos['energy']])+1)
        assert run('ekmq',row+[c(S)],m)==(B==0);cases+=1
    unknowns(lambda model:run('ekmt',actual,model),mm,('ekmo','sedi','sca'))
    return dict(cases=cases,comparison_nonempty_when_actual_volumes_differ=True,actual_and_hypothetical_energy_ratios_distinguished=True,old_new_amplitudes_and_units_held_fixed=True,diagnostic=dict(old_volume='8',actual_new_volume='32/5',old_energy='100/3',actual_new_energy='125/3',hypothetical_new_energy='625/12',actual_ratio='5/4',hypothetical_ratio='25/16'))

@lru_cache(None)
def quantifier_checks():
    cases=0
    for name,premise,conclusion in [('ekmv','ekmi','ekmj'),('ekms','ekmo','ekmt'),('ekmr','ekmt','ekmq')]:
        fields=COMPARISON_VARIABLES if name=='ekmr' else VARIABLES
        original=COMPARISON if name=='ekmr' else TOTAL
        for pivot,(var,sort) in enumerate(fields):
            mode=f'slot:{pivot}';base={n:'a' if i%2==0 else 'b' for i,(n,t) in enumerate(fields)}
            values=[base[n] for i,(n,t) in enumerate(fields) if i!=pivot]
            for target in ('a','b'):
                assigned=base|{var:target,'frame':'a','light':'a','scope':'b','context':'case','portion':'b'}
                row=tuple(assigned[n] for n,t in original)
                resultrow=row+(assigned['volume'],) if name=='ekms' else row
                mm={'ra':lambda:'a','tc':lambda:'a','eisrx':lambda:'b','zvaa':lambda:'b',premise:lambda *xs,row=row:xs==row,conclusion:lambda *xs,row=resultrow:xs==row}
                assert run(name,values,mm,mode,('a','b'));cases+=1
                bad=assigned|{var:'b' if target=='a' else 'a'}
                wrong=tuple(bad[n] for n,t in original)
                if name=='ekms':wrong+=(bad['volume'],)
                assert not run(name,values,mm|{conclusion:lambda *xs,row=wrong:xs==row},mode,('a','b'));cases+=1
            assert run(name,values,mm|{premise:lambda *xs:False,conclusion:lambda *xs:False},mode,('a','b'));cases+=1
            unknowns(lambda model:run(name,values,model,mode,('a','b')),mm,(premise,conclusion))
        refused(lambda:run(name,[],{premise:lambda *xs:False,conclusion:lambda *xs:True,'tc':lambda:'a'}));cases+=1
    return dict(cases=cases,all_65_or_66_roles_bound_same_in_premise_and_conclusion=True,explicit_comparison_volume_is_old_volume_in_construction=True,comparison_variable_not_bound_to_actual_new_volume=True,infinite_function_domains_refused=True)

@lru_cache(None)
def presentation_checks():
    cases=0
    for truths in product((False,True),repeat=3):
        mm={n:lambda a=a:Content(('case','other'),(a,a)) for n,a in zip(('eklq','eklr','ekmv'),truths)}
        assert run('ekmu',[],mm)==all(truths);cases+=1
    rows={'eislz':{('equalvolumesentence','author','ekms','section8','case')},'zc':{('equalvolumesentence','author','ekmu','ekmr','section8','case')},'uh':{('equalvolumesentence','author','ekmr','section8','case')}}
    mm={n:relation(rs) for n,rs in rows.items()};cases+=perturb(lambda model:run('ekmw',[],model),mm,rows)
    assert not run('ekmw',[],mm|{'zc':relation({('equalvolumesentence','author','ekmr','ekmu','section8','case')})});cases+=1
    unknowns(lambda model:run('ekmw',[],model),mm,tuple(rows))
    outer={'eir3':{('equalvolumesentence','author','paper','ekmx','case')},'eisd3':{('equalvolumesentence','portion','paper','case')},'ue':{('densitysentence','equalvolumesentence','case')}}
    mm={n:relation(rs) for n,rs in outer.items()};cases+=perturb(lambda model:run('ekmy',[],model),mm,outer)
    assert not run('ekmy',[],{n:lambda *xs:True for n in outer}|{'eistn':lambda:'densitysentence'});cases+=1
    return dict(cases=cases,hypothetical_construction_not_actual_volume_claim=True,daher_grounds_and_result_direction_retained=True,same_portion_author_document_and_sentence_order=True,quoted_physics_not_executed=True)

@lru_cache(None)
def reading_checks():
    reading=json.loads(read(READING));assert reading==build_reading();validate_hashes(ROOT,reading['source_sha256'])
    u=json.loads(read(INVENTORY))['units'][202]
    assert reading['source']==u['text'][164:389] and reading['source_nonblank_characters']==195
    assert reading['selection']==selection_binding(load_catalog(ROOT,BASIS),[INDEX])
    assert reading['reviewed_prose_characters']==174 and reading['reviewed_math_elements']==3 and reading['verified_full_units']==0
    old=json.loads(read('data/einstein-density-unit-scope-sentence-reading-v1.json'))
    assert old['range'][1]<reading['range'][0] and old['reviewed_prose_characters']+174==301
    return dict(source_range=[164,389],reviewed_prose_characters=174,reviewed_math_elements=3,first_and_second_sentences_prose_characters=301,whole_unit_not_certified=True)

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert len(new.document['statements'])==387 and new.document['statements'][:386]==old.document['statements']
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    assert selection_binding(new,[385])==selection_binding(old,[385])
    load_annotations(ROOT,BASIS,ANNOTATIONS)
    assert json.loads(read(ANNOTATIONS))['entries']==json.loads(read('data/mean-light-energy-identifiers-v1.json'))['entries']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    names=set(selection_binding(new,[INDEX])['dependencies'])
    assert set(MEANINGS)|{'eistm','eiste','eistj','eislz','zc','uh','eisd3','zvaa','ekmi','ekmj','eklq','eklr'}<=names
    assert len(VARIABLES)==65 and len(COMPARISON_VARIABLES)==66
    for style in ('compact','full'):
        body=format_graph(core(),style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core()
    return dict(new_definitions=len(MEANINGS),new_general_relations=0,new_reference_individuals=1,all_386_statements_and_judgments_preserved=True,one_new_sentence_statement=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,json.dumps(build_reading(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('background',background_checks),('comparison',comparison_checks),('quantifiers',quantifier_checks),('presentation',presentation_checks),('reading',reading_checks),('structure',structure_checks)]}
    helpers=('compose_mean_light_energy','compose_material_relative_frame','compose_relativity_conjecture','compose_two_postulates','compose_doppler_infinity','compose_limits','check_coordinate_correspondence','check_clock_site_time','check_conductor_cases','check_resting_charge_force','check_material_relative_frame','check_light_region_slices','check_density_unit_scope','check_wave_cycle_frequency','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(json.loads(read(READING))['source_sha256'])|{DOC,SOURCE,INVENTORY,READING,*DEPENDENCIES,'scripts/compose_equal_volume_supposition.py','scripts/check_equal_volume_supposition.py','scripts/review_equal_volume_supposition.py','tests/test_equal_volume_supposition.py',*(f'scripts/{n}.py' for n in helpers)}
    u=json.loads(read(INVENTORY))['units'][202]
    return dict(status='equal_volume_conditional_second_sentence_checked',document=FULL,**results,alignment=dict(segments=[dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[164,389],source=u['text'][164:389],statements=[INDEX],definitions=list(MEANINGS),status='explicit_interpretive_annotation')]),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
