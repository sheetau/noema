"""Check a shared motion factor, physical argument bindings and attention value."""
from functools import lru_cache
from fractions import Fraction as Q
from copy import deepcopy
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
from scripts.check_material_relative_frame import NUM
from scripts.check_light_energy_ratio import arithmetic,CONSTANTS as PRIOR_CONSTANTS,DOMAIN as PRIOR_DOMAIN
from scripts.check_conductor_cases import sentinel
from scripts.check_resting_charge_force import retag
from scripts.check_wave_cycle_frequency import refused
from scripts.check_calculation_discourse import symbol
from scripts.compose_energy_frequency_law import *
from scripts.read_energy_frequency_law import DOC,SOURCE,INVENTORY,READING,PRIOR,build_reading

CONSTANTS=PRIOR_CONSTANTS|{'eisua':'sharedlaw'}
DOMAIN=tuple(dict.fromkeys([*PRIOR_DOMAIN,*CONSTANTS.values(),'body']))
DEPENDENCIES=('reports/light-energy-ratio-v1.json','reports/observed-doppler-v1.json','reports/doppler-specialization-v1.json','reports/light-complex-v1.json','reports/velocity-axial-claim-v1.json')
BOUNDS={'ekp4':{'ekpm','ekp3'},'ekp5':{'ekp4'},'ekp6':{'ekp4','ekp5','ekps'},'ekqa':{'ekp7'}}

@lru_cache(None)
def core():return parse(read(CORE))

@lru_cache(None)
def boundary(name,binding=False):
    doc=extract_document(core(),roots=[name],statement_indices=[]).document
    bounds=NUM|{'bg','be','sjd','sky','soy','szi','shu','sedi'}|BOUNDS.get(name,set())
    if binding and name=='ekp3':bounds|={'ekpn','ekeu','seck'}
    abstract(doc,bounds);return extract_document(doc,roots=[name],statement_indices=[]).document

@lru_cache(None)
def fixture(name,mode='native'):
    doc=deepcopy(boundary(name,mode=='binding'))
    if mode.startswith('slot:') or mode=='binding':
        doc=retag(doc)
        for d in doc['declarations']:
            if d['kind']=='primitive':
                d['parameters']=['individual' if isinstance(s,dict) and s.get('kind')=='function' else s for s in d['parameters']]
                if isinstance(d['result'],dict) and d['result'].get('kind')=='function':d['result']='individual'
            else:
                for p in d['parameters']:
                    if isinstance(p['sort'],dict) and p['sort'].get('kind')=='function':p['sort']='individual'
        if mode.startswith('slot:'):
            d=next(d for d in doc['declarations'] if d['name']==name);body=d['body']['body'];pivot=int(mode.split(':')[1]);retained=None
            for i,(n,t) in enumerate(VARIABLES):
                assert body['kind']=='forall'
                if i==pivot:retained={k:body[k] for k in ('kind','variable','sort')}
                else:d['parameters'].append(dict(name=body['variable'],sort=body['sort']))
                body=body['body']
            d['body']['body']=retained|{'body':body}
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[]
    for i,p in enumerate(d['parameters']):
        n='jefl'+number_word(i);slots.append((n,p['sort']));doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=name,arguments=[dict(kind='call',symbol=n,arguments=[]) for n,s in slots])
    if d['result']=='content':
        if not any(x['name']=='ri' for x in doc['declarations']):doc['declarations'].append(dict(kind='primitive',name='ri',parameters=[],result='situation'))
        expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='ri',arguments=[]))
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,values,model,mode='native',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(values)==len(slots),(name,len(values),len(slots))
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|model|{n:lambda x=x:x for (n,s),x in zip(slots,values)}
    return evaluate_document(doc,individuals=domain,situations=('case','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=700000,memoize_definitions=True,memoize_expressions=True)[0]['value']

@lru_cache(None)
def numeric_checks():
    cuts,m=arithmetic();c,r=cuts.make,cuts.read;cases=0;pos={n:i for i,(n,t) in enumerate(TOTAL)};slots=fixture('ekp3')[1]
    values=['body' if t=='a' else 'case' if t=='d' else sentinel(s,1,cuts) for (n,t),(_,s) in zip(TOTAL,slots)]
    ratios=set();factors=set()
    for speed in (-3,0,3):
        root=Q(4,5) if speed else Q(1)
        for a in (-1,0,Q(1,3),1):
            D=(1-Q(speed,5)*a)/root;factors.add(D)
            for amplitude,volume in ((Q(3),Q(4)),(Q(5),Q(8))):
                for frequency in (Q(2),Q(7)):
                    energy=amplitude*amplitude*volume/6;ratios.add(energy/frequency)
                    by=dict(light=5,speed=speed,ax=a,anglecos=a,pi=Q(3,4),amplitude=amplitude,newamplitude=amplitude*D,volume=volume,newvolume=volume/D,energy=energy,newenergy=energy*D,frequency=frequency,newfrequency=frequency*D,rate=13)
                    row=values[:]
                    for n,x in by.items():row[pos[n]]=c(x)
                    assert run('ekp3',row,m);cases+=1
                    common=list(map(c,[by[n] for n,t in COMMON]));assert run('seck',common,m);cases+=1
                    for n in ('newenergy','newfrequency','energy','frequency'):
                        bad=row[:];bad[pos[n]]=c(by[n]+1);assert not run('ekp3',bad,m);cases+=1
                    # A phase rate is a different input, even when both are positive.
                    bad=row[:];bad[pos['frequency']]=c(13);assert not run('ekp3',bad,m);cases+=1
                    # Different factors on the two quantities fail the shared law.
                    bad=common[:];bad[-1]=c(frequency*(D+1));assert not run('seck',bad,m);cases+=1
                    # Equal numerical quantities are not a premise of the law.
                    assert energy!=frequency and energy*D!=frequency*D;cases+=1
    assert len(ratios)==4 and len(factors)>3
    common=list(map(c,(5,3,0,10,Q(25,2),2,Q(5,2))))
    unknowns(lambda mm:run('seck',common,mm),m,('ba','soy','sjd','sca'))
    unknowns(lambda mm:run('ekp3',row,mm),m,('ba','sky','soy','sca'))
    for undefined in (0,17):
        cuts,mm=arithmetic(undefined);c=cuts.make
        for i,x in ((0,0),(1,5),(1,-5),(2,2),(2,-2),(3,0),(4,0),(5,0),(6,0),(5,-1),(6,-1)):
            bad=[5,3,0,10,Q(25,2),2,Q(5,2)];bad[i]=x
            # An arbitrary finite off-domain boost must not defeat the guards.
            mod=mm|{'soy':lambda *xs:c(undefined)} if i in (0,1) else mm
            assert not run('seck',list(map(c,bad)),mod);cases+=1
    return dict(cases=cases,same_factor_for_distinct_energy_and_frequency_values=True,phase_rate_not_frequency=True,independent_energy_per_frequency_examples=len(ratios),distinct_motion_factors=len(factors),no_universal_energy_frequency_constant_imposed=True,finite_arithmetic_boundary_not_full_physical_model=True)

@lru_cache(None)
def binding_checks():
    cases=0;fields={'ekpn':TOTAL,'ekeu':EXTENDED,'seck':COMMON};pos={n:i for i,(n,t) in enumerate(TOTAL)}
    values=['a' if i%2==0 else 'b' for i in range(len(TOTAL))];values[pos['context']]='case'
    rows={n:tuple(values[pos[x]] for x,t in fs) for n,fs in fields.items()};m={n:lambda *xs,row=row:xs==row for n,row in rows.items()}
    assert run('ekp3',values,m,'binding',('a','b'));cases+=1
    for i,(name,t) in enumerate(TOTAL):
        bad=values[:];bad[i]='other' if t=='d' else ('b' if bad[i]=='a' else 'a')
        assert not run('ekp3',bad,m,'binding',('a','b'));cases+=1
        for target,fs in fields.items():
            wrong=tuple(bad[pos[n]] for n,t in fs)
            assert run('ekp3',values,m|{target:lambda *xs,row=wrong:xs==row},'binding',('a','b'))==(name not in {n for n,t in fs});cases+=1
    for target in fields:
        assert not run('ekp3',values,m|{target:lambda *xs:False},'binding',('a','b'));cases+=1
    unknowns(lambda mm:run('ekp3',values,mm,'binding',('a','b')),m,tuple(fields))
    for pivot,(var,sort) in enumerate(VARIABLES):
        mode=f'slot:{pivot}';base={n:'a' if i%2==0 else 'b' for i,(n,t) in enumerate(VARIABLES)};values=[base[n] for i,(n,t) in enumerate(VARIABLES) if i!=pivot]
        for value in ('a','b'):
            assigned=base|{var:value,'frame':'a','light':'a','scope':'b','portion':'b','context':'case'};row=tuple(assigned[n] for n,t in TOTAL)
            mm={'ra':lambda:'a','tc':lambda:'a','eisrx':lambda:'b','zvaa':lambda:'b','ekpm':lambda *xs,row=row:xs==row,'ekp3':lambda *xs,row=row:xs==row}
            assert run('ekp4',values,mm,mode,('a','b'));cases+=1
            assert not run('ekp4',values,mm|{'ekp3':lambda *xs:False},mode,('a','b'));cases+=1
            bad=assigned|{var:'a' if value=='b' else 'b'};wrong=tuple(bad[n] for n,t in TOTAL)
            assert not run('ekp4',values,mm|{'ekp3':lambda *xs,row=wrong:xs==row},mode,('a','b'));cases+=1
        assert run('ekp4',values,mm|{'ekpm':lambda *xs:False,'ekp3':lambda *xs:False},mode,('a','b'));cases+=1
        unknowns(lambda mod:run('ekp4',values,mod,mode,('a','b')),mm,('ekpm','ekp3'))
    refused(lambda:run('ekp4',[],{}));cases+=1
    return dict(cases=cases,all_70_roles_and_65_universal_bindings_checked=True,observer_motion_wave_and_both_quantities_share_one_assignment=True,native_unbounded_domain_refused=True)

@lru_cache(None)
def appraisal_checks():
    m={'zld':lambda subject,ctx:Q(8 if (symbol(subject),ctx)==('ekp4','case') else 2),'zle':lambda degree,ctx:ctx=='case' and degree>=5};cases=1
    assert run('ekp5',[],m)
    for patch in ({'zld':lambda *xs:Q(2)},{'zld':lambda subject,ctx:Q(8 if symbol(subject)=='ekps' else 2)},{'zld':lambda subject,ctx:Q(8 if symbol(subject)=='eke2' else 2)},{'zle':lambda degree,ctx:degree>=9},{'ri':lambda:'other'},{'zle':lambda degree,ctx:ctx=='other'}):
        assert not run('ekp5',[],m|patch);cases+=1
    assert run('ekp5',[],{'zld':lambda *xs:Q(2),'zle':lambda degree,ctx:degree>=1});cases+=1
    unknowns(lambda mm:run('ekp5',[],mm),m,('zld','zle'))
    assert run('ekp5',[],m|{n:forbidden for n in ('ekp4','ekp3','seck','ekpm')});cases+=1
    return dict(cases=cases,same_law_description_and_context_for_value_and_standard=True,no_fixed_threshold_or_truth_or_reader_reaction=True)

@lru_cache(None)
def presentation_checks():
    rows={'uh':{('sharedlaw','author','ekp4','section8','case'),('sharedlaw','author','ekp5','section8','case')},'eisra':{('sharedlaw','author','paper','energyintro','ekps','ekp4','section8','case')}}
    mm={n:relation(rs) for n,rs in rows.items()};cases=perturb(lambda mod:run('ekp6',[],mod),mm,rows)
    assert run('ekp6',[],mm|{n:forbidden for n in ('ekp4','ekp5','ekps')});cases+=1
    rows={'eir3':{('sharedlaw','author','paper','ekp7','case')},'ue':{('zerodisplay','sharedlaw','case')}};mm={n:relation(rs) for n,rs in rows.items()};cases+=perturb(lambda mod:run('ekqa',[],mod),mm,rows)
    assert not run('ekqa',[],{n:lambda *xs:True for n in rows}|{'eisua':lambda:'zerodisplay'});cases+=1
    return dict(cases=cases,law_and_attention_appraisal_separately_attributed=True,prior_general_law_reference_and_last_display_order_preserved=True,quoted_contents_not_executed=True)

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert len(new.document['statements'])==394 and new.document['statements'][:393]==old.document['statements']
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations'];assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    assert selection_binding(new,[392])==selection_binding(old,[392]);load_annotations(ROOT,BASIS,ANNOTATIONS)
    assert json.loads(read(ANNOTATIONS))['entries']==json.loads(read('data/light-energy-ratio-identifiers-v1.json'))['entries']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    names=set(selection_binding(new,[INDEX])['dependencies']);assert set(MEANINGS)|{'ekpm','eistm','eistj','ekmg','ekc7','eissk','eissl','eivu','ekes','eket','ekeu','seck','s2z','zld','zle'}<=names
    assert not {'seia','seib','seic'}&names
    setting_names={d['name'] for d in extract_document(new.document,roots=['ekpm'],statement_indices=[]).document['declarations']}
    assert {'ekn7','ekmg','eknw','ekd3','ekd4','ekes','ekdq','eivu','ekc7'}<=setting_names
    assert not {'ekp3','ekpn','ekeu','seck'}&setting_names
    # Existing physical-motion and cycle definitions are unchanged, including
    # their speed/observer propagation and the source/receiver distinction.
    declarations={d['name']:d for d in new.document['declarations']};prior={d['name']:d for d in old.document['declarations']}
    for n in ('ekpm','ekn7','eket','ekes','ekd3','ekd4','ekc7','eivu','ekeu','ekpn','seck','s2z'):assert declarations[n]==prior[n]
    reading=json.loads(read(READING));assert reading==build_reading();validate_hashes(ROOT,reading['source_sha256'])
    assert reading['selection']==selection_binding(new,[INDEX]);assert reading['reviewed_prose_characters']==133
    for style in ('compact','full'):
        body=format_graph(core(),style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core()
    return dict(new_definitions=len(MEANINGS),new_general_relations=0,new_reference_individuals=1,all_393_statements_and_judgments_preserved=True,physical_cycles_motion_and_integrals_reused_unchanged=True,reviewed_prose_characters=133,reviewed_math_elements=0)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,json.dumps(build_reading(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('numeric',numeric_checks),('bindings',binding_checks),('appraisal',appraisal_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    helpers=('compose_light_energy_ratio','compose_doppler_specialization','compose_material_relative_frame','compose_relativity_conjecture','compose_two_postulates','compose_doppler_infinity','compose_limits','check_coordinate_correspondence','check_clock_site_time','check_material_relative_frame','check_light_energy_ratio','check_conductor_cases','check_resting_charge_force','check_wave_cycle_frequency','check_calculation_discourse','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(json.loads(read(READING))['source_sha256'])|{DOC,SOURCE,INVENTORY,READING,*DEPENDENCIES,'scripts/compose_energy_frequency_law.py','scripts/check_energy_frequency_law.py','scripts/read_energy_frequency_law.py','tests/test_energy_frequency_law.py',*(f'scripts/{n}.py' for n in helpers)}
    return dict(status='same_energy_frequency_motion_law_and_attention_appraisal_checked',document=FULL,**results,alignment=dict(segments=json.loads(read(READING))['segments']),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
