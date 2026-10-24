"""Check enclosed energy integrals, both ratios, zero angle and discourse roles."""
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
from noema.polynomial_proofs import verify_universal
from scripts.check_coordinate_correspondence import abstract
from scripts.check_clock_site_time import relation,perturb,unknowns,forbidden
from scripts.check_material_relative_frame import NUM
from scripts.check_light_region_slices import setup
from scripts.check_light_volume_ratio import CONSTANTS as PRIOR_CONSTANTS,DOMAIN as PRIOR_DOMAIN
from scripts.check_conductor_cases import sentinel,same_value
from scripts.check_resting_charge_force import retag
from scripts.check_wave_cycle_frequency import refused
from scripts.check_real_products import assertion,MEANINGS as POLYNOMIAL
from scripts.compose_light_complex import generic_composed
from scripts.compose_light_energy_ratio import *
from scripts.read_light_energy_ratio import DOC,SOURCE,INVENTORY,READING,PRIOR,build_reading

CONSTANTS=PRIOR_CONSTANTS|{'eist2':'energyintro','eist3':'energydisplay','eist4':'zerointro','eist5':'zerodisplay','eist6':'oldenergyname','eist7':'newenergyname'}
DOMAIN=tuple(dict.fromkeys([*PRIOR_DOMAIN,*CONSTANTS.values()]))
DEPENDENCIES=('reports/light-volume-ratio-v1.json','reports/mean-light-energy-v1.json','reports/observed-amplitude-v1.json','reports/amplitude-specialization-v1.json','reports/doppler-specialization-v1.json')
BOUNDS={'ekpm':{'ekn7','sede'},'ekpn':{'ekpl'},'ekpo':{'ekpm'},'ekpp':{'ekpm'},'ekpr':{'ekpm','ekmj','ekoz','ekij'},'ekps':{'ekpm','ekpn'},'ekpt':{'ekpm'},'ekpw':{'ekpt','ekpn'},'ekpx':{'ekpt','ekpv'},'ekpy':{'ekpo','ekpp','ekpr','ekps','ekpe','ekpw','ekpx'},'ekp2':{'ekpz'}}

@lru_cache(None)
def core():return parse(read(CORE))

@lru_cache(None)
def boundary(name):
    # Cache the small abstraction once per root, rather than extracting the
    # inherited physical corpus again for every quantified slot.
    doc=extract_document(core(),roots=[name],statement_indices=[]).document
    abstract(doc,NUM|{'bg','be','sjd','sky','soy','szi','shu','sedi'}|BOUNDS.get(name,set()))
    return extract_document(doc,roots=[name],statement_indices=[]).document

@lru_cache(None)
def fixture(name,mode='native'):
    doc=deepcopy(boundary(name))
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
            d=next(d for d in doc['declarations'] if d['name']==name);isname=name in ('ekpo','ekpp');body=d['body'] if isname else d['body']['body'];variables=name_variables('energy' if name=='ekpo' else 'newenergy')[1] if isname else VARIABLES
            pivot=int(mode.split(':')[1]);retained=None
            for i,(n,t) in enumerate(variables):
                assert body['kind']==('exists' if isname else 'forall')
                if i==pivot:retained={k:body[k] for k in ('kind','variable','sort')}
                else:d['parameters'].append(dict(name=body['variable'],sort=body['sort']))
                body=body['body']
            if isname:d['body']=retained|{'body':body}
            else:d['body']['body']=retained|{'body':body}
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[]
    for i,p in enumerate(d['parameters']):
        n='jler'+number_word(i);slots.append((n,p['sort']));doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=name,arguments=[dict(kind='call',symbol=n,arguments=[]) for n,s in slots])
    if d['result']=='content':
        if not any(x['name']=='ri' for x in doc['declarations']):doc['declarations'].append(dict(kind='primitive',name='ri',parameters=[],result='situation'))
        expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='ri',arguments=[]))
    elif isinstance(d['result'],dict):
        doc['declarations'].append(dict(kind='primitive',name='jlercapture',parameters=[d['result']],result='truth'));expr=dict(kind='call',symbol='jlercapture',arguments=[expr])
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,values,model,mode='native',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(values)==len(slots),(name,len(values),len(slots));captured=[]
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|model|{n:lambda x=x:x for (n,s),x in zip(slots,values)}
    def capture(x):captured.append(x);return True
    mm['jlercapture']=capture
    result=evaluate_document(doc,individuals=domain,situations=('case','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=700000,memoize_definitions=True,memoize_expressions=True)[0]['value']
    return captured[0] if captured else result

def arithmetic(undefined=0):
    cuts,m=setup();c,r=cuts.make,cuts.read;root=m['sky']
    return cuts,m|{'sjd':lambda x:c(1/r(x) if r(x) else undefined),'sky':lambda x:root(x) if r(x)>=0 else c(undefined)}

@lru_cache(None)
def numeric_checks():
    cuts,m=arithmetic();c,r=cuts.make,cuts.read;cases=0
    for speed in (-3,0,3):
        root=Q(4,5) if speed else Q(1)
        for co in (-1,Q(-3,5),0,Q(1,3),1):
            D=(1-Q(speed,5)*co)/root;pi=Q(3,4);A=Q(5);newA=A*D;S=Q(8);newS=S/D;E=A*A*S/(8*pi);newE=newA*newA*newS/(8*pi)
            row=(5,speed,co,pi,A,newA,S,newS,E,newE)
            assert r(run('ekpj',list(map(c,row[:3])),m))==D;cases+=1
            assert r(run('ekpk',list(map(c,row[3:8])),m))==D;cases+=1
            assert run('ekpl',list(map(c,row)),m);cases+=1
            for i in range(3,10):
                bad=list(row);bad[i]+=Q(1,7)
                # A common pi factor cancels from the middle quotient. Its
                # physical binding is checked in the integral setting instead.
                assert run('ekpl',list(map(c,bad)),m)==(i==3);cases+=1
            bad=list(row);bad[8],bad[9]=bad[9],bad[8]
            assert run('ekpl',list(map(c,bad)),m)==(D==1);cases+=1
            bad=list(row);bad[6],bad[7]=bad[7],bad[6]
            assert run('ekpl',list(map(c,bad)),m)==(D==1);cases+=1
        special=(1-Q(speed,5))/root
        assert r(run('ekpu',list(map(c,(5,speed))),m))==special;cases+=1
        values=[n if t=='a' else 'case' if t=='d' else sentinel(s,1,cuts) for (n,t),(_,s) in zip(TOTAL,fixture('ekpv')[1])];pos={n:i for i,(n,t) in enumerate(TOTAL)}
        for n,x in dict(light=5,speed=speed,energy=8,newenergy=8*special).items():values[pos[n]]=c(x)
        assert run('ekpv',values,m);cases+=1
        values[pos['newenergy']]=c(8*special+1);assert not run('ekpv',values,m);cases+=1
    base=(5,3,0,Q(3,4),5,Q(25,4),8,Q(32,5),Q(100,3),Q(125,3))
    unknowns(lambda mm:run('ekpl',list(map(c,base)),mm),m,('ba','sky','sjd','sca'))
    for undefined in (0,17):
        cuts,mm=arithmetic(undefined);c=cuts.make
        for i,x in ((0,0),(1,5),(1,-5),(2,2),(2,-2),(3,0),(3,-1),(4,0),(4,-1),(5,-1),(6,0),(7,0),(8,0),(8,-1),(9,-1)):
            bad=list(base);bad[i]=x
            assert not run('ekpl',list(map(c,bad)),mm),(i,x,undefined);cases+=1
    return dict(cases=cases,both_equalities_and_middle_density_volume_products_preserved=True,zero_angle_radical_and_ratio_direction_checked=True,invalid_denominators_rejected_under_two_off_domain_values=True)

@lru_cache(None)
def physical_checks():
    cuts,m=arithmetic();c,r=cuts.make,cuts.read;slots=fixture('ekpm')[1];pos={n:i for i,(n,t) in enumerate(TOTAL)};cases=0
    values=[n if t=='a' else 'case' if t=='d' else sentinel(s,i+1,cuts) for i,((n,t),(_,s)) in enumerate(zip(TOTAL,slots))]
    numbers=dict(light=5,speed=3,ax=0,ay=1,az=0,anglecos=0,amplitude=5,newamplitude=Q(25,4),radius=2,pi=Q(3,4),volume=8,newvolume=Q(32,5),energy=Q(100,3),newenergy=Q(125,3))
    for n,x in numbers.items():values[pos[n]]=c(x)
    target=[values[pos[n]] for n,t in SETTING];targetsort=[slots[pos[n]][1] for n,t in SETTING];seen=[]
    def same_setting(*xs):return all(same_value(a,b,s,cuts) for a,b,s in zip(xs,target,targetsort))
    def integral(lo,hi,f,value):
        bounds=(r(lo),r(hi));samples=tuple(r(f(c(x))) for x in (0,Q(1,3),1));value=r(value);seen.append((bounds,samples,value))
        for D,S,A,E in ((Q(1),Q(8),Q(5),Q(100,3)),(Q(5,4),Q(32,5),Q(25,4),Q(125,3))):
            for weight,total in ((Q(1),S),(A*A/6,E)):
                if bounds==(-2/D,2/D) and samples==tuple(weight*Q(3,4)*(4-D*D*x*x) for x in (0,Q(1,3),1)) and value==total:return True
        return False
    mm=m|{'ekn7':same_setting,'sedi':lambda x:r(x)==Q(3,4),'sede':integral}
    assert run('ekpm',values,mm);assert len(seen)==4;cases+=2
    for i,(_,sort) in enumerate(slots):
        if TOTAL[i][0] in ('light','speed'):continue
        bad=values[:];bad[i]=sentinel(sort,100+i,cuts)
        assert not run('ekpm',bad,mm),(i,TOTAL[i]);cases+=1
    for n,x in [('light',10),('speed',0)]:
        bad=values[:];bad[pos[n]]=c(x)
        # Both numerical changes have rational boosts at this test boundary.
        mod=mm|{'soy':lambda *xs:c(1)} if n=='light' else mm
        assert not run('ekpm',bad,mod);cases+=1
    unknowns(lambda model:run('ekpm',values,model),mm,('ekn7','sedi','sede'))
    for missing in (Q(100,3),Q(125,3),Q(8),Q(32,5)):
        assert not run('ekpm',values,mm|{'sede':lambda lo,hi,f,x,missing=missing:r(x)!=missing and integral(lo,hi,f,x)});cases+=1
    # Zero old energy and a wrong new energy are rejected at the integral
    # boundary even if the remaining physical setting is accepted.
    for name in ('energy','newenergy'):
        bad=values[:];bad[pos[name]]=c(0);assert not run('ekpm',bad,mm);cases+=1
    # Native zero-angle guard: retain the physical condition at its boundary.
    zm=m|{'ekpm':lambda *xs:True};zero=values[:];zero[pos['angle']]=c(0)
    assert run('ekpt',zero,zm);cases+=1
    for angle in (Q(1),Q(-1)):
        bad=zero[:];bad[pos['angle']]=c(angle);assert not run('ekpt',bad,zm);cases+=1
    assert not run('ekpt',zero,zm|{'ekpm':lambda *xs:False});cases+=1
    unknowns(lambda model:run('ekpt',zero,model),zm,('ekpm','sca'))
    return dict(cases=cases,same_two_weighted_and_unweighted_integrals_bound_to_70_roles=True,energy_product_and_ratio_not_assumed=True,real_angle_zero_not_only_cosine_one=True,rational_pi_diagnostic_not_circle_constant=True)

@lru_cache(None)
def binding_checks():
    cases=0
    for name,premise,targets0 in [('ekpr','ekpm',('ekmj','ekoz','ekij')),('ekps','ekpm',('ekpn',)),('ekpw','ekpt',('ekpn',)),('ekpx','ekpt',('ekpv',))]:
        for pivot,(var,sort) in enumerate(VARIABLES):
            mode=f'slot:{pivot}';base={n:'a' if i%2==0 else 'b' for i,(n,t) in enumerate(VARIABLES)};values=[base[n] for i,(n,t) in enumerate(VARIABLES) if i!=pivot]
            for value in ('a','b'):
                assigned=base|{var:value,'frame':'a','light':'a','scope':'b','portion':'b','context':'case','magneticside':False};row=tuple(assigned[n] for n,t in TOTAL)
                fields={target:(SETTING if target=='ekoz' else AMPLITUDE if target=='ekij' else TOTAL) for target in targets0};targets={n:tuple(assigned[x] for x,t in fs) for n,fs in fields.items()}
                mm={'ra':lambda:'a','tc':lambda:'a','eisrx':lambda:'b','zvaa':lambda:'b',premise:lambda *xs,row=row:xs==row}|{n:lambda *xs,row=row:xs==row for n,row in targets.items()}
                assert run(name,values,mm,mode,('a','b'));cases+=1
                for target in targets:
                    assert not run(name,values,mm|{target:lambda *xs:False},mode,('a','b'));cases+=1
                    bad=assigned|{var:'a' if value=='b' else 'b'};wrong=tuple(bad[x] for x,t in fields[target])
                    assert run(name,values,mm|{target:lambda *xs,row=wrong:xs==row},mode,('a','b'))==(var not in {n for n,t in fields[target]});cases+=1
            assert run(name,values,mm|{premise:lambda *xs:False}|{n:lambda *xs:False for n in targets},mode,('a','b'));cases+=1
            unknowns(lambda mod:run(name,values,mod,mode,('a','b')),mm,(premise,*targets))
        refused(lambda:run(name,[],{}));cases+=1
    values=['a' if i%2==0 else 'b' for i in range(len(TOTAL))];pos={n:i for i,(n,t) in enumerate(TOTAL)};values[pos['context']]='case';row=tuple(values[pos[n]] for n,t in DISPLAY)
    assert run('ekpn',values,{'ekpl':lambda *xs:xs==row},'binding',('a','b'));cases+=1
    for n,t in DISPLAY:
        bad=values[:];bad[pos[n]]='b' if bad[pos[n]]=='a' else 'a';assert not run('ekpn',bad,{'ekpl':lambda *xs:xs==row},'binding',('a','b'));cases+=1
    for name,which in [('ekpo','energy'),('ekpp','newenergy')]:
        variables=name_variables(which)[1]
        for pivot,(var,sort) in enumerate(variables):
            base={n:'a' if i%2==0 else 'b' for i,(n,t) in enumerate(variables)};values=['b','a','case']+[base[n] for i,(n,t) in enumerate(variables) if i!=pivot];mode=f'slot:{pivot}'
            for value in ('a','b'):
                assigned=base|{var:value,'frame':'a','light':'a','scope':'b','portion':'b','context':'case',which:'a'};row=tuple(assigned[n] for n,t in TOTAL)
                mm={'ra':lambda:'a','tc':lambda:'a','eisrx':lambda:'b','ekpm':lambda *xs,row=row:xs==row}
                assert run(name,values,mm,mode,('a','b'));cases+=1
                assert not run(name,values,mm|{'ekpm':lambda *xs:False},mode,('a','b'));cases+=1
                for i in range(3):
                    bad=values[:];bad[i]='other' if i==2 else ('b' if bad[i]=='a' else 'a');assert not run(name,bad,mm,mode,('a','b'));cases+=1
            unknowns(lambda mod:run(name,values,mod,mode,('a','b')),mm,('ekpm',))
        cuts,m=arithmetic();refused(lambda:run(name,['body',cuts.make(8),'case'],m));cases+=1
    return dict(cases=cases,all_65_shared_context_roles_and_64_name_witnesses_checked=True,same_total_and_zero_angle_settings_shared=True,native_infinite_domains_refused=True)

@lru_cache(None)
def polynomial_checks():
    mul=lambda a,b:k('ad',a,b);sub=lambda a,b:k('ab',a,k('ac',b));eq=lambda a,b:op('e',a,b);one='n p b b';zero='n p a b'
    A,B,S,T,E,N,C,D,invE=map(v,('oldamp','newamp','oldvol','newvol','oldenergy','newenergy','conversion','factor','involdenergy'))
    pre=both(k('aa',zero,C),eq(mul(C,E),mul(mul(A,A),S)),eq(mul(C,N),mul(mul(B,B),T)),eq(mul(B,B),mul(mul(A,A),mul(D,D))),eq(mul(D,T),S),eq(mul(E,invE),one))
    claims={'density_amplitude_volume_to_energy_ratio':assertion('oldamp newamp oldvol newvol oldenergy newenergy conversion factor involdenergy',op('y',pre,eq(mul(N,invE),D)))}
    r,h,g=map(v,('ratio','root','special'));pre=both(k('aa',zero,h),k('aa',zero,g),eq(mul(h,h),sub(one,mul(r,r))),eq(mul(mul(g,g),k('ab',one,r)),sub(one,r)),k('aa',r,one),k('aa',k('ac',one),r))
    claims['positive_zero_angle_square_root_identity']=assertion('ratio root special',op('y',pre,eq(mul(g,h),sub(one,r))))
    base=generic_composed()[0];rows={n:verify_universal(parse(base+s),POLYNOMIAL,timeout_ms=20000)[0] for n,s in claims.items()};assert all(r['status']=='valid' for r in rows.values()),rows
    return dict(lemmas=rows,rational_polynomial_only=True,positive_root_branch_preserved=True,integral_and_square_root_existence_not_automatically_proved=True)

@lru_cache(None)
def presentation_checks():
    rows={'eislo':{('oldenergyname','ekpo','paper','case'),('newenergyname','ekpp','paper','case')},'zc':{('energyintro','author','ekpr','ekps','section8','case')},'uh':{('energyintro','author','ekps','section8','case')},'eisox':{('energydisplay','ekps','case'),('zerodisplay','ekpx','case')},'uf':{('author','energyintro','energydisplay','case'),('author','zerointro','zerodisplay','case')},'ue':{('energyintro','energydisplay','case'),('energydisplay','zerointro','case'),('zerointro','zerodisplay','case')},'eisra':{('energyintro','author','paper','volumeintro','ekpe','ekpr','section8','case'),('zerointro','author','paper','energydisplay','ekps','ekpw','section8','case')},'eissb':{('zerointro','energydisplay','author','ekpw','ekpx','section8','case')},'eistb':{('ekpx','ekpw','section8','case')}}
    mm={n:relation(rs) for n,rs in rows.items()};cases=perturb(lambda mod:run('ekpy',[],mod),mm,rows)
    assert run('ekpy',[],mm|{n:forbidden for n in ('ekpo','ekpp','ekpr','ekps','ekpe','ekpw','ekpx')});cases+=1
    rows={'eir3':{('energyintro','author','paper','ekpz','case')},'ue':{('volumeintro','energyintro','case')}};mm={n:relation(rs) for n,rs in rows.items()};cases+=perturb(lambda mod:run('ekp2',[],mod),mm,rows)
    for n,val in [('eist2','volumeintro'),('eist3','energyintro'),('eist4','energydisplay'),('eist5','zerointro'),('eist7','oldenergyname')]:assert not run('ekp2',[],{n:lambda *xs:True for n in rows}|{n:lambda:val});cases+=1
    return dict(cases=cases,names_consequence_both_displays_relative_clause_and_strict_comparison_preserved=True,quoted_contents_not_executed=True)

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert len(new.document['statements'])==393 and new.document['statements'][:392]==old.document['statements']
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations'];assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    assert selection_binding(new,[391])==selection_binding(old,[391]);load_annotations(ROOT,BASIS,ANNOTATIONS)
    ann=json.loads(read(ANNOTATIONS));assert ann['entries'][:-2]==json.loads(read('data/light-volume-ratio-identifiers-v1.json'))['entries']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    names=set(selection_binding(new,[INDEX])['dependencies']);assert set(MEANINGS)|{'ekmg','ekn7','eistj','eistm','ekdq','ekij','eislo','eistb'}<=names
    setting_names={d['name'] for d in extract_document(new.document,roots=['ekpm'],statement_indices=[]).document['declarations']}
    assert {'ekn7','ekmg','eknw','ekdq'}<=setting_names
    assert not {'ekmj','ekoz','ekij','ekpl','ekpn','ekpv','sech','ekml'}&setting_names
    reading=json.loads(read(READING));assert reading==build_reading();validate_hashes(ROOT,reading['source_sha256'])
    assert reading['selection']==selection_binding(new,[INDEX]);assert reading['reviewed_math_elements']==5
    for style in ('compact','full'):
        body=format_graph(core(),style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core()
    return dict(new_definitions=len(MEANINGS),new_general_relations=0,new_reference_individuals=6,all_392_statements_and_judgments_preserved=True,reviewed_prose_characters=reading['reviewed_prose_characters'],reviewed_math_elements=5)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,json.dumps(build_reading(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('numeric',numeric_checks),('physical',physical_checks),('bindings',binding_checks),('polynomial',polynomial_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    helpers=('compose_light_volume_ratio','compose_mean_light_energy','compose_observed_amplitude','compose_material_relative_frame','compose_relativity_conjecture','compose_two_postulates','compose_doppler_infinity','compose_limits','compose_light_complex','check_coordinate_correspondence','check_clock_site_time','check_material_relative_frame','check_light_region_slices','check_light_volume_ratio','check_conductor_cases','check_resting_charge_force','check_wave_cycle_frequency','check_real_products','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(json.loads(read(READING))['source_sha256'])|{DOC,SOURCE,INVENTORY,READING,*DEPENDENCIES,'scripts/compose_light_energy_ratio.py','scripts/check_light_energy_ratio.py','scripts/read_light_energy_ratio.py','tests/test_light_energy_ratio.py',*(f'scripts/{n}.py' for n in helpers)}
    return dict(status='same_light_energy_names_general_ratio_and_zero_angle_checked',document=FULL,**results,alignment=dict(segments=json.loads(read(READING))['segments']),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
