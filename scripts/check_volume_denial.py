"""Check denial scope, reference, contrast and a nonzero-speed equal-volume example."""
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
from scripts.check_equal_volume_supposition import CONSTANTS as PRIOR,DOMAIN as PREVIOUS
from scripts.check_wave_cycle_frequency import refused
from scripts.compose_volume_denial import *
from scripts.review_volume_denial import DOC,SOURCE,INVENTORY,READING,build_reading

CONSTANTS=PRIOR|{'eisto':'denialsentence'}
DOMAIN=tuple(dict.fromkeys([*PREVIOUS,*CONSTANTS.values(),*[n for n,t in TOTAL if t=='a']]))
DEPENDENCIES=('reports/equal-volume-supposition-v1.json','reports/light-region-slices-v1.json','reports/mean-light-energy-v1.json')
BOUNDS={'ekm3':{'ekmo','ekmz'},'ekm4':{'ekmo','ekmz'},'ekm5':{'ekm4'},'ekm6':{'ekmo'},'sedp':{'sede'}}

@lru_cache(None)
def core():return parse(read(CORE))

@lru_cache(None)
def fixture(name,mode='native'):
    doc=extract_document(core(),roots=[name],statement_indices=[]).document
    bounds=NUM|{'bg','be','sjd','sky','soy','szi','shu','sedi'}|BOUNDS.get(name,set())
    if name in ('ekm7','eknb'):bounds|={'ekms','ekm3','ekm6'}
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
        fields=VARIABLES
        for i,(n,t) in enumerate(fields):
            assert body['kind']==('exists' if name=='ekm6' else 'forall')
            if i==pivot:retained={k:body[k] for k in ('kind','variable','sort')}
            else:d['parameters'].append(dict(name=body['variable'],sort=body['sort']))
            body=body['body']
        d['body']['body']=retained|{'body':body}
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[]
    for i,p in enumerate(d['parameters']):
        n='jvde'+number_word(i);slots.append((n,p['sort']));doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=name,arguments=[dict(kind='call',symbol=n,arguments=[]) for n,s in slots])
    if d['result']=='content':
        if not any(x['name']=='ri' for x in doc['declarations']):doc['declarations'].append(dict(kind='primitive',name='ri',parameters=[],result='situation'))
        expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='ri',arguments=[]))
    elif isinstance(d['result'],dict):
        doc['declarations'].append(dict(kind='primitive',name='jvdecapture',parameters=[d['result']],result='truth'));expr=dict(kind='call',symbol='jvdecapture',arguments=[expr])
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,values,model,mode='native',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(values)==len(slots),(name,len(values),len(slots));captured=[]
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|model|{n:lambda x=x:x for (n,s),x in zip(slots,values)}
    def capture(x):captured.append(x);return True
    mm['jvdecapture']=capture
    result=evaluate_document(doc,individuals=domain,situations=('case','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=700000,memoize_definitions=True,memoize_expressions=True)[0]['value']
    return captured[0] if captured else result


@lru_cache(None)
def denial_checks():
    cuts,m=setup();c,r=cuts.make,cuts.read;cases=0;slots=fixture('ekmz')[1]
    values=[n if t=='a' else 'case' if t=='d' else sentinel(s,i+1,cuts) for i,((n,t),(_,s)) in enumerate(zip(TOTAL,slots))]
    positions={n:i for i,(n,t) in enumerate(TOTAL)}
    for a,b in product((Q(1),Q(2),Q(8)),repeat=2):
        values[positions['volume']]=c(a);values[positions['newvolume']]=c(b)
        assert run('ekmz',values,m)==(a==b);cases+=1
        assert run('ekm2',values,m)==(a!=b);cases+=1
    # No hypothetical comparison volume or energy ratio occurs in this target.
    declaration=next(d for d in core()['declarations'] if d['name']=='ekmz')
    refs=[dict(kind='variable',name=declaration['parameters'][positions[n]]['name']) for n in ('volume','newvolume')]
    assert len(declaration['parameters'])==70 and declaration['body']==dict(kind='call',symbol='ekl6',arguments=refs)
    for truth in (False,True):
        mm={'ekm4':lambda truth=truth:Content(('case','other'),(truth,truth))}
        assert run('ekm5',[],mm)==(not truth);cases+=1
    unknowns(lambda model:run('ekmz',values,model),m,('sca','bg'))
    return dict(cases=cases,actual_volume_equality_negated=True,conditional_energy_ratio_not_negated=True,not_all_equal_kept_separate=True)


@lru_cache(None)
def quantifier_checks():
    cases=0
    for name in ('ekm3','ekm4','ekm6'):
        for pivot,(var,sort) in enumerate(VARIABLES):
            mode=f'slot:{pivot}';base={n:'a' if i%2==0 else 'b' for i,(n,t) in enumerate(VARIABLES)}
            values=(['b'] if name=='ekm6' else [])+[base[n] for i,(n,t) in enumerate(VARIABLES) if i!=pivot]
            fixed={'frame':'a','light':'a','scope':'b','context':'case','portion':'b'}
            mm={'ra':lambda:'a','tc':lambda:'a','eisrx':lambda:'b','zvaa':lambda:'b'}
            for target in ('a','b'):
                assigned=base|{var:target}|fixed;row=tuple(assigned[n] for n,t in TOTAL)
                model=mm|{'ekmo':lambda *xs,row=row:xs==row,'ekmz':lambda *xs,row=row:xs==row}
                assert run(name,values,model,mode,('a','b'))==(name!='ekm3');cases+=1
                bad=assigned|{var:'b' if target=='a' else 'a'};wrong=tuple(bad[n] for n,t in TOTAL)
                if name=='ekm6':
                    assert not run(name,values,model|{'ekmo':lambda *xs:False},mode,('a','b'))
                else:
                    assert run(name,values,model|{'ekmz':lambda *xs,row=wrong:xs==row},mode,('a','b'))==(name=='ekm3')
                cases+=1
            assert run(name,values,model|{'ekmo':lambda *xs:False,'ekmz':lambda *xs:False},mode,('a','b'))==(name!='ekm6');cases+=1
            unknowns(lambda model:run(name,values,model,mode,('a','b')),model,('ekmo',) if name=='ekm6' else ('ekmo','ekmz'))
        refused(lambda:run(name,['portion'] if name=='ekm6' else [],{'ekmo':lambda *xs:False,'ekmz':lambda *xs:True,'tc':lambda:'a'}));cases+=1
    # A mixed scope has one equal and one unequal case. Forall-not is false,
    # whereas not-forall is true. Use the native inner negation at every slot.
    for pivot,(var,sort) in enumerate(VARIABLES):
        mode=f'slot:{pivot}';values=['a']*(len(VARIABLES)-1);index=next(i for i,(n,t) in enumerate(TOTAL) if n==var)
        mm={'ra':lambda:'a','tc':lambda:'a','eisrx':lambda:'b','zvaa':lambda:'b','ekmo':lambda *xs:True,'ekmz':lambda *xs,index=index:xs[index]=='a'}
        assert not run('ekm3',values,mm,mode,('a','b'));cases+=1
        all_equal=run('ekm4',values,mm,mode,('a','b'));assert not all_equal;cases+=1
        assert run('ekm5',[],{'ekm4':lambda:Content(('case','other'),(all_equal,all_equal))});cases+=1
    return dict(cases=cases,all_65_roles_bound_in_each_scope=True,same_portion_fixed_and_dimension_parameter_checked=True,forall_not_distinguished_from_not_forall_in_mixed_scope=True,native_infinite_domains_refused=True)


@lru_cache(None)
def counterexample_checks():
    cuts,m=setup();c,r=cuts.make,cuts.read;cases=0;observed=[];pi=Q(3,4);V=Q(5);speed=Q(3);beta=Q(5,4);R0=Q(2)
    for n,e,h in [((Q(1,3),Q(2,3),Q(2,3)),(-2,2,-1),(-2,-1,2)),((Q(0),Q(1),Q(0)),(5,0,0),(0,0,-5))]:
        e=tuple(map(Q,e));h=tuple(map(Q,h));D=beta*(1-n[0]*speed/V)
        nn=((n[0]-speed/V)/(1-n[0]*speed/V),n[1]/D,n[2]/D)
        ee=(e[0],beta*(e[1]-speed/V*h[2]),beta*(e[2]+speed/V*h[1]))
        hh=(h[0],beta*(h[1]+speed/V*e[2]),beta*(h[2]-speed/V*e[1]))
        A=Q(3) if D==1 else Q(5);B=D*A;S=Q(4,3)*pi*R0**3;SS=S/D
        for values in ((*n,*e,*h),(*nn,*ee,*hh)):
            assert run('seaj',list(map(c,values)),m);cases+=1
        transform=(V,speed,*e,*h,*ee,*hh)
        assert run('sdz2',list(map(c,transform)),m);cases+=1
        for i in range(8,14):
            bad=list(transform);bad[i]+=Q(1,7);assert not run('sdz2',list(map(c,bad)),m);cases+=1
        direction=(V,speed,Q(2),*n,Q(2)*D,*nn)
        assert run('sdq2',list(map(c,direction)),m);cases+=1
        for i in range(6,10):
            bad=list(direction);bad[i]+=Q(1,7);assert not run('sdq2',list(map(c,bad)),m);cases+=1
        for field,amplitude in ((e,A),(h,A),(ee,B),(hh,B)):
            assert run('seal',list(map(c,(*field,amplitude))),m);cases+=1
        seen=[]
        def integral(lo,hi,f,value):
            lo,hi,value=map(r,(lo,hi,value));samples=tuple(r(f(c(x))) for x in (0,Q(1,3),1));seen.append((lo,hi,samples,value))
            return any((lo,hi)==(-R0/factor,R0/factor) and value==S/factor and samples==tuple(pi*(R0**2-(factor*x)**2) for x in (0,Q(1,3),1)) for factor in (1,D))
        mm=m|{'sedi':lambda x:r(x)==pi,'sede':integral}
        assert run('sedp',list(map(c,(V,speed,*n,R0,pi,S,SS))),mm);cases+=1
        assert len(seen)==2 and seen[0][:2]==(-R0,R0) and seen[1][:2]==(-R0/D,R0/D);cases+=1
        assert run('sech',list(map(c,(V,speed,n[0],S,SS))),m);cases+=1
        for area,amplitude in ((S,A),(SS,B)):
            density=amplitude**2/(8*pi);energy=density*area
            assert run('ekmh',list(map(c,(area,density,energy))),m);cases+=1
        slots=fixture('ekmz')[1];values=[name if t=='a' else 'case' if t=='d' else sentinel(s,i+1,cuts) for i,((name,t),(_,s)) in enumerate(zip(TOTAL,slots))]
        for name,value in dict(volume=S,newvolume=SS).items():values[next(i for i,(name0,t) in enumerate(TOTAL) if name==name0)]=c(value)
        assert run('ekmz',values,m)==(D==1);cases+=1
        assert run('ekm2',values,m)==(D!=1);cases+=1
        observed.append(dict(direction=list(map(str,n)),factor=str(D),old_volume=str(S),new_volume=str(SS),old_amplitude=str(A),new_amplitude=str(B),old_energy=str(A*A*S/(8*pi)),new_energy=str(B*B*SS/(8*pi))))
    assert observed[0]['old_energy']==observed[0]['new_energy']=='12'
    assert observed[0]['factor']=='1' and observed[1]['factor']=='5/4'
    return dict(cases=cases,nonzero_transverse_wave_at_nonzero_speed=True,all_six_transformed_components_and_four_wave_parameters_checked=True,equal_and_unequal_volume_cases=observed,pi_is_only_a_rational_diagnostic=True,full_physical_model_existence_not_automatically_proved=True)


@lru_cache(None)
def presentation_checks():
    rows={'uh':{('denialsentence','author','ekm3','section8','case')},'eisra':{('denialsentence','author','paper','equalvolumesentence','ekms','ekm3','section8','case')},'eisnp':{('denialsentence','author','equalvolumesentence','ekms','denialsentence','ekm3','ekm6','case')}}
    mm={n:relation(rs) for n,rs in rows.items()};cases=perturb(lambda model:run('ekm7',[],model),mm,rows)
    unknowns(lambda model:run('ekm7',[],model),mm,tuple(rows))
    for n,old,new in [('uh','ekm3','ekm5'),('eisra','ekms','ekmr'),('eisnp','ekms','ekmr')]:
        changed={tuple(new if x==old else x for x in row) for row in rows[n]}
        assert not run('ekm7',[],mm|{n:relation(changed)});cases+=1
    outer={'eir3':{('denialsentence','author','paper','ekna','case')},'ue':{('equalvolumesentence','denialsentence','case')}}
    mm={n:relation(rs) for n,rs in outer.items()};cases+=perturb(lambda model:run('eknb',[],model),mm,outer)
    assert not run('eknb',[],{n:lambda *xs:True for n in outer}|{'eisto':lambda:'equalvolumesentence'});cases+=1
    return dict(cases=cases,author_attribution_does_not_execute_physics=True,denial_reference_and_contrast_all_required=True,actual_equal_volume_not_conditional_ratio_is_denied=True,weaker_reading_not_silently_substituted=True)


@lru_cache(None)
def reading_checks():
    reading=json.loads(read(READING));assert reading==build_reading();validate_hashes(ROOT,reading['source_sha256'])
    u=json.loads(read(INVENTORY))['units'][202]
    assert reading['source']==u['text'][390:421] and reading['source_nonblank_characters']==26
    assert reading['selection']==selection_binding(load_catalog(ROOT,BASIS),[INDEX])
    assert reading['reviewed_prose_characters']==26 and reading['reviewed_math_elements']==0 and reading['verified_full_units']==0
    old=json.loads(read('data/einstein-equal-volume-supposition-sentence-reading-v1.json'))
    assert old['range'][1]<reading['range'][0] and old['reviewed_prose_characters']+127+26==327
    return dict(source_range=[390,421],reviewed_prose_characters=26,reviewed_math_elements=0,first_three_sentences_prose_characters=327,whole_unit_not_certified=True,strong_reading_and_counterexample_explicit=True)


@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert len(new.document['statements'])==388 and new.document['statements'][:387]==old.document['statements']
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    for index in (385,386):assert selection_binding(new,[index])==selection_binding(old,[index])
    load_annotations(ROOT,BASIS,ANNOTATIONS)
    assert json.loads(read(ANNOTATIONS))['entries']==json.loads(read('data/equal-volume-supposition-identifiers-v1.json'))['entries']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    names=set(selection_binding(new,[INDEX])['dependencies'])
    assert set(MEANINGS)-{'ekm4','ekm5'}<=names
    assert {'eisra','eisnp','uh','zvaa','ekmo','ekms','ekl6','eistm'}<=names
    assert not {'ekm4','ekm5'}&names and len(VARIABLES)==65
    for style in ('compact','full'):
        body=format_graph(core(),style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core()
    return dict(new_definitions=len(MEANINGS),new_general_relations=0,new_reference_individuals=1,all_387_statements_and_judgments_preserved=True,one_new_sentence_statement=True,weaker_reading_not_in_attribution_dependencies=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,json.dumps(build_reading(),ensure_ascii=False,indent=2)+'\n')


@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('denial',denial_checks),('quantifiers',quantifier_checks),('counterexample',counterexample_checks),('presentation',presentation_checks),('reading',reading_checks),('structure',structure_checks)]}
    helpers=('compose_equal_volume_supposition','compose_material_relative_frame','compose_relativity_conjecture','compose_two_postulates','compose_doppler_infinity','compose_limits','check_coordinate_correspondence','check_clock_site_time','check_conductor_cases','check_resting_charge_force','check_material_relative_frame','check_light_region_slices','check_equal_volume_supposition','check_wave_cycle_frequency','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(json.loads(read(READING))['source_sha256'])|{DOC,SOURCE,INVENTORY,READING,*DEPENDENCIES,'scripts/compose_volume_denial.py','scripts/check_volume_denial.py','scripts/review_volume_denial.py','tests/test_volume_denial.py',*(f'scripts/{n}.py' for n in helpers)}
    u=json.loads(read(INVENTORY))['units'][202]
    return dict(status='volume_denial_third_sentence_checked_with_explicit_scope_and_counterexample',document=FULL,**results,alignment=dict(segments=[dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[390,421],source=u['text'][390:421],statements=[INDEX],definitions=list(MEANINGS),status='explicit_interpretive_annotation')]),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
