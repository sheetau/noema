"""Check the real leading limit, all shared roles and both agreement branches."""
from copy import deepcopy
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
from scripts.check_material_relative_frame import NUM
from scripts.check_light_energy_ratio import arithmetic
from scripts.check_mirror_energy_work import setting
from scripts.check_mirror_energy_principle import CONSTANTS as PRIOR_CONSTANTS
from scripts.check_wave_cycle_frequency import refused
from scripts.compose_pressure_leading_approximation import *
from scripts.read_pressure_leading_approximation import DOC,READING,build_reading

CONSTANTS=PRIOR_CONSTANTS|{'eisqw':'currenttheory','eisve':'experience','eisvf':'ratioexpansion','eisvg':'intro','eisvh':'display'}
DOMAIN=tuple(dict.fromkeys([*CONSTANTS.values(),*[n for n,t in TOTAL if t=='a'],'theory1','theory2','theory3','other','a','b']))
DEPENDENCIES=('reports/mirror-energy-principle-v1.json','reports/mirror-energy-work-v1.json')
CONSEQUENTS={'eku3':('eku2',TOTAL),'eku4':('ekuz',FAMILY)}
BOUNDARIES={'ekuz':{'sjr'},'eku3':{'ekt6','eku2'},'eku4':{'ekt6','ekuz'}}

@lru_cache(None)
def core():return parse(read(CORE))

@lru_cache(None)
def boundary(root,native_limit=False):
    doc=extract_document(core(),roots=[root],statement_indices=[]).document
    bounds=NUM|{'bg','be','sjd','sky','soy','szi','shu','sedi'}|BOUNDARIES.get(root,set())
    if native_limit:bounds.discard('sjr')
    if root in ('eku5','eku6','eku7','ekva','ekvb','ekvd','ekvf'):bounds|={'eku3','eku4','eku5','eku6','eku7','ekuf','ekuh','ekvc','ekve'};bounds.discard(root)
    abstract(doc,bounds);return extract_document(doc,roots=[root],statement_indices=[]).document

@lru_cache(None)
def fixture(root,mode='native'):
    doc=deepcopy(boundary(root,mode=='native_limit'));d=next(d for d in doc['declarations'] if d['name']==root)
    if mode.startswith('slot:'):
        doc=retag(doc)
        for dec in doc['declarations']:
            if dec['kind']=='primitive':
                dec['parameters']=['individual' if isinstance(s,dict) and s.get('kind')=='function' else s for s in dec['parameters']]
                if isinstance(dec['result'],dict) and dec['result'].get('kind')=='function':dec['result']='individual'
            else:
                for p in dec['parameters']:
                    if isinstance(p['sort'],dict) and p['sort'].get('kind')=='function':p['sort']='individual'
        d=next(d for d in doc['declarations'] if d['name']==root);body=d['body']['body'];pivot=int(mode.split(':')[1]);retained=None
        for i,(n,t) in enumerate(VARIABLES):
            assert body['kind']=='forall'
            if i==pivot:retained={k:body[k] for k in ('kind','variable','sort')}
            else:d['parameters'].append(dict(name=body['variable'],sort=body['sort']))
            body=body['body']
        d['body']['body']=retained|dict(body=body)
    slots=[]
    for i,p in enumerate(d['parameters']):
        n='jpla'+number_word(i);slots.append((n,p['sort']));doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=root,arguments=[dict(kind='call',symbol=n,arguments=[]) for n,s in slots])
    if d['result']=='content':
        if not any(x['name']=='ri' for x in doc['declarations']):doc['declarations'].append(dict(kind='primitive',name='ri',parameters=[],result='situation'))
        expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='ri',arguments=[]))
    elif isinstance(d['result'],dict):
        doc['declarations'].append(dict(kind='primitive',name='jplacapture',parameters=[d['result']],result='truth'));expr=dict(kind='call',symbol='jplacapture',arguments=[expr])
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(root,values,model,mode='native',domain=DOMAIN):
    doc,slots=fixture(root,mode);assert len(values)==len(slots),(root,len(values),len(slots));captured=[]
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|model|{n:lambda x=x:x for (n,s),x in zip(slots,values)}
    def capture(x):captured.append(x);return True
    mm['jplacapture']=capture
    result=evaluate_document(doc,individuals=domain,situations=('case','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=700000,memoize_definitions=True,memoize_expressions=True)[0]['value']
    return captured[0] if captured else result

@lru_cache(None)
def analytic_checks():
    cuts,m=arithmetic();c,r=cuts.make,cuts.read;_,by=setting(cuts);cases=0
    for A in (0,2,5):
        for cosine in (-1,Q(0),Q(3,5),1):
            pi=Q(3,4);V=Q(5);K=2*A*A/(8*pi);L=K*cosine*cosine;values=list(map(c,(pi,A,V,cosine)))
            fn=run('ekux',values,m);assert r(run('ekuw',list(map(c,(pi,A,cosine))),m))==L;cases+=1
            for ratio in (Q(-3,4),Q(-1,2),Q(-1,20),Q(0),Q(1,20),Q(1,2),Q(3,4)):
                exact=K*(cosine-ratio)**2/(1-ratio*ratio);assert r(fn(c(ratio)))==exact;cases+=1
                residual=K*(-2*cosine*ratio+(1+cosine*cosine)*ratio*ratio)/(1-ratio*ratio);assert exact-L==residual;cases+=1
                if abs(ratio)<=Q(1,2):assert abs(residual)<=4*K*abs(ratio);cases+=1
            def limit(domain,function,point,value):
                return r(point)==0 and r(value)==L and all(domain(c(t))==(abs(t)<1) for t in (-2,-1,Q(-1,2),0,Q(1,2),1,2)) and all(r(function(c(t)))==K*(cosine-t)**2/(1-t*t) for t in (Q(-1,2),Q(-1,20),0,Q(1,20),Q(1,2)))
            mm=m|{'sjr':limit};assert run('ekuz',values,mm);cases+=1
            assert not run('ekuz',values,mm|{'sjr':lambda *xs:False});cases+=1
            unknowns(lambda model:run('ekuz',values,model),mm,('sjr',))
            current=by|{n:c(x) for n,x in dict(pi=pi,amplitude=A,anglecos=cosine,pressure=L).items()}
            assert run('eku2',[current[n] for n,t in TOTAL],m);cases+=1
            current['pressure']=c(L+1);assert not run('eku2',[current[n] for n,t in TOTAL],m);cases+=1
    for field,x in [('pi',-1),('light',-5),('amplitude',-1),('anglecos',2),('anglecos',-2)]:
        bad=dict(pi=Q(3,4),amplitude=5,light=5,anglecos=Q(3,5))|{field:x}
        assert not run('ekuz',[c(bad[n]) for n,t in FAMILY],m|{'sjr':lambda *xs:True});cases+=1
    # Light is held positive and fixed along each family; its magnitude cancels
    # in the ratio formula, so changing positive V need not change the values.
    for V in (2,5,13):
        fn=run('ekux',list(map(c,(Q(3,4),5,V,Q(3,5)))),m)
        assert r(fn(c(Q(1,10))))==Q(625,297);cases+=1
    # Nonzero linear coefficient distinguishes a leading term from order one.
    K=Q(25,3);cosine=Q(3,5);linear=-2*K*cosine
    slopes=[]
    for n in (20,40,80):
        t=Q(1,n);exact=K*(cosine-t)**2/(1-t*t);slopes.append(abs((exact-K*cosine*cosine)/t-linear));cases+=1
        assert exact!=K*cosine*cosine and linear!=0;cases+=1
    assert slopes[0]>slopes[1]>slopes[2]>0;cases+=1
    refused(lambda:run('ekuz',list(map(c,(Q(3,4),5,5,Q(3,5)))),m,'native_limit'));cases+=1
    return dict(cases=cases,same_dimensionless_family_value_and_real_limit_bound=True,zero_amplitude_and_grazing_angle_without_relative_division=True,leading_order_distinguished_from_linear_order=True,native_infinite_limit_refused=True)

@lru_cache(None)
def quantifier_checks():
    cases=0
    for root,(con,fs) in CONSEQUENTS.items():
        for pivot,(variable,sort) in enumerate(VARIABLES):
            for target in ((False,True) if sort=='c' else ('a','b','unavailable')):
                assigned={n:False if t=='c' else ('a' if i%2==0 else 'b') for i,(n,t) in enumerate(TOTAL)}|dict(frame='a',light='a',scope='b',context='case');assigned[variable]=target
                row=tuple(assigned[n] for n,t in TOTAL);expected=tuple(assigned[n] for n,t in fs);values=[assigned[n] for i,(n,t) in enumerate(VARIABLES) if i!=pivot]
                mm={'ra':lambda:'a','tc':lambda:'a','eisrx':lambda:'b','ekt6':lambda *xs,row=row:xs==row};mode=f'slot:{pivot}'
                assert run(root,values,mm|{con:lambda *xs:False},mode,('a','b'))==(target=='unavailable');cases+=1
                assert run(root,values,mm|{con:lambda *xs,expected=expected:xs==expected},mode,('a','b'));cases+=1
            unknowns(lambda model:run(root,values,model,mode,('a','b')),mm|{con:lambda *xs:True},('ekt6',))
        cuts,m=arithmetic();refused(lambda:run(root,[],m|{'tc':lambda:cuts.make(5),'ekt6':lambda *xs:True,con:lambda *xs:True}));cases+=1
    return dict(cases=cases,all_98_shared_roles_and_boolean_side_preserved=True,raw_equation_and_analytic_family_use_same_setting=True,native_unbounded_domains_preserved=True)

@lru_cache(None)
def agreement_checks():
    cases=0;selected={'theory1','theory2'}
    rows={'eisvd':{(t,'paper','section8','case') for t in selected},'eisvc':{(t,'eku5','section8','case') for t in selected|{'experience'}}}
    cases+=perturb(lambda model:run('eku7',[],model),{n:relation(rs) for n,rs in rows.items()},rows)
    # Additional theories are not ignored; no theory, one theory and inclusion
    # of the current theory fail independently of numerical/content agreement.
    for chosen,want in [(set(),False),({'theory1'},False),({'theory1','theory2'},True),({'theory1','theory2','theory3'},True),({'theory1','currenttheory'},False)]:
        mm={'eisvd':relation({(t,'paper','section8','case') for t in chosen}),'eisvc':relation({(t,'eku5','section8','case') for t in chosen|{'experience'}})}
        assert run('eku7',[],mm)==want;cases+=1
        if want:
            for removed in chosen|{'experience'}:
                bad=mm|{'eisvc':relation({(t,'eku5','section8','case') for t in (chosen|{'experience'})-{removed}})}
                assert not run('eku7',[],bad);cases+=1
    # A source supplying the unrestricted equation or exact pressure law does
    # not supply the same restricted result, even if the other branch does.
    for alternative in ('eku3','ekuf'):
        for source in selected|{'experience'}:
            wrong={((t,alternative if t==source else 'eku5','section8','case')) for t in selected|{'experience'}}
            assert not run('eku7',[],{'eisvd':relation(rows['eisvd']),'eisvc':relation(wrong)});cases+=1
    return dict(cases=cases,experience_and_every_selected_other_theory_share_same_approximation=True,plural_nonempty_scope_and_current_theory_exclusion=True,no_exact_law_or_unrestricted_equation_substitution=True)

@lru_cache(None)
def presentation_checks():
    cases=0
    rows={
      'eku5':{'eisbn':{('eku3','ratioexpansion',Q(0),'case')}},
      'ekva':{'zc':{('intro','author','eku6','eku5','section8','case')},'uh':{('intro','author','eku7','section8','case')},'eisra':{('intro','author','paper','display','ekuf','eku5','section8','case')},'ue':{('intro','display','case')}},
      'ekvb':{'eislo':{('pressurename','ekuh','paper','case')},'eisox':{('display','eku5','case')}},
      'ekvd':{'eir3':{('intro','author','paper','ekvc','case')},'ue':{('display','intro','case')}},
      'ekvf':{'eir3':{('display','author','paper','ekve','case')},'ue':{('intro','display','case')}},
    }
    # Keep the preceding full pressure display distinct from this new display.
    constants={'eisu7':lambda:'previouspressure'}
    rows['ekva']['eisra']={('intro','author','paper','previouspressure','ekuf','eku5','section8','case')}
    rows['ekvd']['ue']={('previouspressure','intro','case')}
    domain=(*DOMAIN,'previouspressure')
    for root,rs in rows.items():cases+=perturb(lambda model:run(root,[],model,domain=domain),constants|{n:relation(r) for n,r in rs.items()},rs)
    assert not run('eku5',[],{'eisbn':relation({('eku3','ratioexpansion',Q(1),'case')})});cases+=1
    mm={n:lambda:Content(('case','other'),(True,False)) for n in ('ekuf','eku4')}
    assert run('eku6',[],mm);cases+=1
    for n in mm:assert not run('eku6',[],mm|{n:lambda:Content(('case','other'),(False,False))});cases+=1
    unknowns(lambda model:run('eku6',[],model),mm,tuple(mm))
    return dict(cases=cases,zero_order_exactly_selected=True,prior_formula_derivation_agreement_name_display_and_attribution_bound=True,quoted_result_not_executed_as_exact_truth=True,no_added_colon=True)

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert len(new.document['statements'])==406 and new.document['statements'][:404]==old.document['statements']
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    assert selection_binding(new,[402,403])==selection_binding(old,[402,403])
    load_annotations(ROOT,BASIS,ANNOTATIONS);assert json.loads(read(ANNOTATIONS))['entries']==json.loads(read('data/mirror-energy-principle-identifiers-v1.json'))['entries']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    deps=set(selection_binding(new,INDICES)['dependencies']);assert set(MEANINGS)|{'sjr','eisbn','ekuh','ekt3','eifk','eisqw'}<=deps
    assert not {'ekbw','ekbx','ekby','ekbz'}&deps
    for style in ('compact','full'):
        body=format_graph(core(),style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core()
    reading=json.loads(read(READING));assert reading==build_reading();validate_hashes(ROOT,reading['source_sha256'])
    assert reading['reviewed_prose_characters']==80 and reading['reviewed_math_elements']==1
    return dict(new_definitions=len(MEANINGS),new_general_relations=2,new_reference_individuals=len(PRIMITIVES)-2,all_404_previous_statements_and_meanings_preserved=True,introduction_and_approximation_display_collated=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,json.dumps(build_reading(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('analytic',analytic_checks),('quantifiers',quantifier_checks),('agreement',agreement_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    helpers=('compose_limits','compose_material_relative_frame','compose_relativity_conjecture','compose_two_postulates','compose_doppler_infinity','compose_mirror_energy_principle','check_coordinate_correspondence','check_clock_site_time','check_resting_charge_force','check_material_relative_frame','check_light_energy_ratio','check_mirror_energy_work','check_mirror_energy_principle','check_wave_cycle_frequency','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(json.loads(read(READING))['source_sha256'])|{READING,DOC,*DEPENDENCIES,'scripts/compose_pressure_leading_approximation.py','scripts/read_pressure_leading_approximation.py','scripts/check_pressure_leading_approximation.py','tests/test_pressure_leading_approximation.py',*(f'scripts/{n}.py' for n in helpers)}
    return dict(status='pressure_leading_limit_and_both_agreement_branches_checked',document=FULL,**results,alignment=dict(segments=json.loads(read(READING))['segments']),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
