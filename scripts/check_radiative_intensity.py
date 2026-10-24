"""Check signed mean flux, approach-side scaling and relational left limits."""
from functools import lru_cache
from fractions import Fraction as Q
from itertools import product
import json,xml.etree.ElementTree as ET
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import FunctionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from noema.polynomial_proofs import verify_universal
from scripts.check_coordinate_correspondence import abstract
from scripts.check_clock_site_time import unknowns,forbidden
from scripts.check_material_relative_frame import NUM,RS
from scripts.check_aberration_line import setup
from scripts.check_wave_cycle_frequency import refused
from scripts.check_real_products import assertion,MEANINGS as POLYNOMIAL
from scripts.compose_radiative_intensity import *

DOC='docs/radiative-intensity-v1.md';SOURCE='data/einstein-radiative-intensity-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';FACSIMILE='artifacts/written-facsimiles-v1/einstein-1905-unlp-p912-0.jpg'
DEPENDENCIES=('reports/amplitude-specialization-v1.json','reports/observed-amplitude-v1.json','reports/energy-boundary-v1.json','reports/doppler-infinity-v1.json')
BOUNDS={'ekjh':{'sede'},'ekjo':{'ekjn'},'ekjp':{'ekjo'},'ekjr':{'ekjq'},'ekjs':{'ekjr'},'ekjt':{'ekjp','ekjr'},'ekjw':{'ekjm'},'ekjx':{'ekjt'}}

@lru_cache(None)
def core():return parse(read(CORE))

@lru_cache(None)
def fixture(name,mode='native'):
    doc=extract_document(core(),roots=[name],statement_indices=[]).document
    bounds=NUM|{'bg','sjd','soy','sky','szi','shu'}|BOUNDS.get(name,set())
    abstract(doc,bounds);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    if mode=='finite':
        def replace(node):
            if node==RS:return 'individual'
            if isinstance(node,list):return [replace(x) for x in node]
            if isinstance(node,dict):return {k:replace(x) for k,x in node.items()}
            return node
        doc=replace(doc)
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[]
    for i,p in enumerate(d['parameters']):
        n='jrif'+number_word(i);slots.append((n,p['sort']));doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=name,arguments=[dict(kind='call',symbol=n,arguments=[]) for n,s in slots])
    if isinstance(d['result'],dict):
        doc['declarations'].append(dict(kind='primitive',name='jrifcapture',parameters=[d['result']],result='truth'));expr=dict(kind='call',symbol='jrifcapture',arguments=[expr])
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,values,model,mode='native',domain=('a','b','body')):
    doc,slots=fixture(name,mode);assert len(values)==len(slots),(name,len(values),len(slots));captured=[]
    mm=model|{n:lambda x=x:x for (n,s),x in zip(slots,values)}
    def capture(x):captured.append(x);return True
    mm['jrifcapture']=capture
    result=evaluate_document(doc,individuals=domain,situations=('case','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=300000,memoize_definitions=True,memoize_expressions=True)[0]['value']
    return captured[0] if captured else result

def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def dot(a,b):return sum(x*y for x,y in zip(a,b))

@lru_cache(None)
def flux_checks():
    cuts,m=setup();c,r=cuts.make,cuts.read;cases=0
    directions=((1,0,0),(-1,0,0),(0,0,1),(Q(3,5),Q(4,5),0))
    for n,E,H,coef in product(directions,((1,2,3),(0,3,4)),((4,5,6),(0,-4,3)),(Q(2,3),Q(3))):
        actual=r(run('ekjf',list(map(c,(coef,*n,*E,*H))),m));expected=coef*dot(n,cross(E,H));assert actual==expected;cases+=1
        reverse=r(run('ekjf',list(map(c,(coef,*n,*H,*E))),m));assert reverse==-expected;cases+=1
    for n,coef,mean,A in product(directions,(Q(2,3),Q(3)),(Q(0),Q(1,2),Q(2)),(Q(0),Q(3),Q(5))):
        E=(-A*n[1],A*n[0],0) if not n[2] else (A,0,0);H=cross(n,E);I=coef*mean*A*A
        values=list(map(c,(coef,*n,*E,*H,mean,A,I)))
        assert run('ekjj',values,m);cases+=1
        bad=values[:];bad[-1]=c(I+1);assert not run('ekjj',bad,m);cases+=1
        bad=values[:];bad[0]=c(0);assert not run('ekjj',bad,m);cases+=1
        if A:
            bad=values[:];bad[-2]=c(-A);assert not run('ekjj',bad,m);cases+=1
            wrong=list(map(c,(coef,*n,*E,*[-x for x in H],mean,A,-I)))
            assert not run('ekjj',wrong,m);cases+=1
    unknowns(lambda mm:run('ekjf',list(map(c,(2,1,0,0,0,3,4,0,-4,3))),mm),m,('shv','bd','bf'))
    return dict(cases=cases,cross_product_order_and_direction_retained=True,transverse_model_gives_coefficient_times_mean_square_times_amplitude_squared=True,zero_amplitude_and_zero_mean_allowed_without_divergence=True)

@lru_cache(None)
def average_checks():
    cuts,m=setup();c,r=cuts.make,cuts.read;cases=0
    flux=(Q(2),Q(2,3),Q(1,3),Q(2,3),Q(1),Q(2),Q(3),Q(4),Q(5),Q(6));K=flux[0]*dot(flux[1:4],cross(flux[4:7],flux[7:10]));assert K==-4
    for slope,offset,lo,hi in ((0,1,0,2),(1,0,0,3),(2,-1,-2,1),(-1,3,1,4)):
        profile=FunctionValue((RS,),RS,lambda t,a=slope,b=offset:c(a*r(t)+b))
        integral=K*(Q(slope*slope,3)*(hi**3-lo**3)+slope*offset*(hi**2-lo**2)+offset*offset*(hi-lo));mean=integral/(hi-lo)
        values=[*map(c,flux),profile,*map(c,(lo,hi,integral,mean))]
        def integrated(a,b,function,result):
            return r(a)==lo and r(b)==hi and r(result)==integral and all(r(function(c(t)))==K*(slope*t+offset)**2 for t in (-2,0,1,3))
        mm=m|{'sede':integrated}
        assert run('ekjh',values,mm);cases+=1
        fn=run('ekjg',values[:11],m)
        for t in (-2,0,1,3):assert r(fn(c(t)))==K*(slope*t+offset)**2;cases+=1
        for i in range(len(values)):
            bad=values[:];bad[i]=FunctionValue((RS,),RS,lambda t:c(r(profile(t))+1)) if i==10 else c(r(bad[i])+Q(1,7))
            assert not run('ekjh',bad,mm),(slope,offset,i);cases+=1
        for lower,upper in ((hi,lo),(lo,lo)):
            bad=values[:];bad[11:13]=map(c,(lower,upper));assert not run('ekjh',bad,mm);cases+=1
        unknowns(lambda mm:run('ekjh',values,mm),mm,('sede','ba','sca'))
    # The actual Riemann definition remains an infinite-domain requirement.
    doc=extract_document(core(),roots=['sede'],statement_indices=[]).document
    assert any(d['kind']=='definition' and d['name']=='sede' for d in doc['declarations'])
    return dict(cases=cases,same_profile_interval_integral_and_average=True,signed_flux_and_nonconstant_profile_retained=True,integral_boundary_probes_not_a_general_integration_proof=True,cycle_average_not_silently_fixed_to_half=True)

@lru_cache(None)
def scaling_checks():
    cuts,m=setup();c,r=cuts.make,cuts.read;cases=0;witnesses=[]
    for V,ratio,coef,mean,A in product((Q(5),Q(2,3)),(Q(1,5),Q(3,5),Q(12,13)),(Q(2,3),Q(3)),(Q(0),Q(1,2)),(Q(0),Q(2))):
        speed=V*ratio;I=coef*mean*A*A;received=I*(V+speed)/(V-speed)
        assert r(run('ekjk',list(map(c,(V,speed,coef,mean,A))),m))==received;cases+=1
        assert r(run('ekjl',list(map(c,(V,speed,I))),m))==received;cases+=1
        assert run('ekjm',list(map(c,(V,I,speed,received))),m);cases+=1
        assert not run('ekjm',list(map(c,(V,I,speed,received+1))),m);cases+=1
        if I:assert received>I and received!=I*(V-speed)/(V+speed);cases+=1
    for V,I,M in product((Q(5),Q(2,3)),(Q(1,7),Q(3)),map(Q,(-10,0,1,100,10**12))):
        delta=V*I/(2*(I+max(M,0)));speed=V-delta/2;received=I*(V+speed)/(V-speed)
        assert 0<delta<=V/2 and M<received
        assert r(run('ekju',list(map(c,(V,I,M))),m))==delta;cases+=1
        assert run('ekjv',list(map(c,(V,I,M,speed))),m);cases+=1
        assert not run('ekjv',list(map(c,(V,I,M,V-delta))),m);cases+=1
        witnesses.append(dict(light=str(V),incident=str(I),bound=str(M),radius=str(delta),speed=str(speed),received=str(received)))
    for V,eps in product((Q(5),Q(2,3)),(Q(1,10**12),Q(1,10),Q(10))):
        speed=V-min(eps,V)/2;I=Q(2);received=I*(V+speed)/(V-speed)
        assert V-eps<speed<V and 0<speed
        assert run('ekjm',list(map(c,(V,I,speed,received))),m);cases+=1
    for speed in (-1,0,6):
        assert not run('ekjm',list(map(c,(5,1,speed,Q(5+speed,5-speed)))),m);cases+=1
    try:run('ekjm',list(map(c,(5,1,5,100))),m)
    except (ValueError,ZeroDivisionError) as exc:assert isinstance(exc,ZeroDivisionError) or 'Unknown' in str(exc)
    else:raise AssertionError('Invented a finite boundary value')
    cases+=1
    for speed in (Q(1),Q(4),Q(4999,1000)):
        assert run('ekjm',list(map(c,(5,0,speed,0))),m);cases+=1
        assert r(run('ekjl',list(map(c,(5,speed,0))),m))==0;cases+=1
    unknowns(lambda mm:run('ekjv',list(map(c,(5,2,100,Q(499,100)))),mm),m,('sjd','bg','shv'))
    return dict(cases=cases,head_on_ratio_is_reciprocal_of_receding_ratio=True,positive_incident_threshold_witnesses=witnesses,arbitrarily_close_nonempty_points_have_explicit_witnesses=True,no_finite_light_speed_value_or_zero_input_divergence=True)

@lru_cache(None)
def point_checks():
    cuts,m=setup();c,r=cuts.make,cuts.read;cases=0
    graph=FunctionValue((RS,RS),'truth',lambda x,y:r(y)==2*r(x))
    for boundary,radius,x,y,M in product((3,5),(-1,0,2),(1,3,4,5),(2,6,8,10),(0,6,10)):
        near=radius>0 and boundary-radius<x<boundary and y==2*x
        assert run('ekjn',[graph,*map(c,(boundary,radius,x,y))],m)==near;cases+=1
        assert run('ekjq',[graph,*map(c,(boundary,M,radius,x,y))],m)==(not near or M<y);cases+=1
    empty=FunctionValue((RS,RS),'truth',lambda *xs:False)
    assert run('ekjq',[empty,*map(c,(5,100,2,4,8))],m);cases+=1
    unknowns(lambda mm:run('ekjn',[graph,*map(c,(5,2,4,8))],mm),m,('ba','bg','bf'))
    return dict(cases=cases,both_neighborhood_endpoints_excluded=True,all_outputs_and_strict_threshold_preserved=True,empty_local_implication_is_not_divergence=True)

@lru_cache(None)
def quantifier_checks():
    domain=('a','b');pairs=list(product(domain,repeat=2));graph=FunctionValue(('individual','individual'),'truth',lambda *xs:True);cases=0
    basic={'ba':lambda x:True,'bb':lambda x:'a','bg':lambda x,y:True}
    for bits in product((False,True),repeat=4):
        table=dict(zip(pairs,bits))
        mm=basic|{'ekjn':lambda G,B,d,x,y: B=='b' and d=='a' and table[x,y]}
        assert run('ekjo',[graph,'b','a'],mm,'finite',domain)==any(bits);cases+=1
        assert not run('ekjo',[graph,'a','a'],mm,'finite',domain);cases+=1
        mm=basic|{'ekjq':lambda G,B,M,d,x,y:table[x,y]}
        assert run('ekjr',[graph,'b','a','b'],mm,'finite',domain)==all(bits);cases+=1
    for bits in product((False,True),repeat=2):
        table=dict(zip(domain,bits));mm=basic|{'ekjo':lambda G,B,d:B=='b' and table[d]}
        assert run('ekjp',[graph,'b'],mm,'finite',domain)==all(bits);cases+=1
        assert not run('ekjp',[graph,'a'],mm,'finite',domain);cases+=1
    for bits in product((False,True),repeat=4):
        table=dict(zip(pairs,bits));mm=basic|{'ekjp':lambda G,B:B=='b','ekjr':lambda G,B,M,d:B=='b' and table[M,d]}
        for M in domain:
            assert run('ekjs',[graph,'b',M],mm,'finite',domain)==any(table[M,d] for d in domain);cases+=1
        expected=all(any(table[M,d] for d in domain) for M in domain)
        assert run('ekjt',[graph,'b'],mm,'finite',domain)==expected;cases+=1
        assert not run('ekjt',[graph,'b'],mm|{'ekjp':lambda G,B:False},'finite',domain);cases+=1
    diagonal=basic|{'ekjp':lambda G,B:True,'ekjr':lambda G,B,M,d:M==d}
    assert run('ekjt',[graph,'b'],diagonal,'finite',domain);cases+=1
    assert not any(all(M==d for M in domain) for d in domain);cases+=1
    # A small second output is enough to defeat a bound, regardless of a high one.
    for bad in pairs:
        assert not run('ekjr',[graph,'b','a','b'],basic|{'ekjq':lambda G,B,M,d,x,y,bad=bad:(x,y)!=bad},'finite',domain);cases+=1
    unknowns(lambda mm:run('ekjt',[graph,'b'],mm,'finite',domain),diagonal,('ekjp','ekjr','ba'))
    cuts,m=setup();c,r=cuts.make,cuts.read;realgraph=FunctionValue((RS,RS),'truth',lambda *xs:True)
    for name in ('ekjp','ekjt'):
        refused(lambda name=name:run(name,[realgraph,c(5)],m|{'ekjo':lambda *xs:True,'ekjp':lambda *xs:True,'ekjr':lambda *xs:True}));cases+=1
    return dict(cases=cases,arbitrarily_small_nonempty_neighborhoods_required=True,each_bound_gets_its_own_radius=True,every_relational_output_checked=True,native_real_quantifiers_not_replaced_by_finite_tables=True)

@lru_cache(None)
def binding_checks():
    cuts,m=setup();c,r=cuts.make,cuts.read;cases=0
    gate=lambda V,I,speed,received:tuple(map(r,(V,I,speed,received)))==(5,2,3,8)
    for V,I,expected in ((5,2,True),(7,2,False),(5,3,False)):
        fn=run('ekjw',list(map(c,(V,I))),m|{'ekjm':gate})
        assert fn(c(3),c(8))==expected;cases+=1
        assert not fn(c(8),c(3));cases+=1
    def limit(G,V):
        return r(V)==5 and G(c(3),c(8)) and not G(c(3),c(7)) and G(c(4),c(18))
    mm=m|{'ekjt':limit}
    assert run('ekjx',list(map(c,(5,2))),mm);cases+=1
    for V,I in ((7,2),(5,3),(5,0),(-5,2)):
        assert not run('ekjx',list(map(c,(V,I))),mm);cases+=1
    unknowns(lambda model:run('ekjx',list(map(c,(5,2))),model),mm,('ekjt','bg'))
    return dict(cases=cases,same_positive_light_and_incident_are_fixed_outside_graph=True,graph_input_output_not_interchanged=True)

@lru_cache(None)
def polynomial_checks():
    # Clearing positive denominators exposes exact algebra certificates. These
    # are rational polynomial lemmas, not an automatic real-cut limit theorem.
    base='n:r aa[b b] c.r ab[b b] b.r ac[b] b.r ad[b b] b.'
    z='n p a b';two='n p c b';one='n p b b'
    mul=lambda a,b:k('ad',a,b);add=lambda a,b:k('ab',a,b);sub=lambda a,b:add(a,k('ac',b));lt=lambda a,b:k('aa',a,b);eq=lambda a,b:op('e',a,b)
    V,I,M,N,d,speed,out=map(v,('light','incident','bound','nonnegative','radius','speed','output'))
    prem=both(lt(z,V),lt(z,I),op('u',lt(N,z)),op('u',lt(N,M)),lt(z,d),eq(mul(mul(two,add(I,N)),d),mul(V,I)),lt(z,speed),lt(speed,V),lt(sub(V,d),speed),eq(mul(sub(V,speed),out),mul(I,add(V,speed))))
    claims={
        'positive_radius_certificate_forces_above_bound':assertion('light incident bound nonnegative radius speed output',op('y',prem,lt(M,out))),
        'radius_at_most_half_light':assertion('light incident nonnegative radius',op('y',both(lt(z,V),lt(z,I),op('u',lt(N,z)),lt(z,d),eq(mul(mul(two,add(I,N)),d),mul(V,I))),op('u',lt(V,mul(two,d))))),
        'zero_incident_has_zero_finite_output':assertion('light speed output',op('y',both(lt(z,speed),lt(speed,V),eq(mul(sub(V,speed),out),z)),eq(out,z))),
    }
    ratio,power,gen,simpl=map(v,('ratio','power','general','simplified'))
    claims['head_on_ratio_clears_same_positive_denominator']=assertion('ratio power general simplified',op('y',both(lt(z,ratio),lt(ratio,one),eq(mul(sub(one,mul(ratio,ratio)),gen),mul(power,mul(add(one,ratio),add(one,ratio)))),eq(mul(sub(one,ratio),simpl),mul(power,add(one,ratio)))),eq(gen,simpl)))
    rows={}
    for n,claim in claims.items():
        result=verify_universal(parse(base+claim),POLYNOMIAL,timeout_ms=20000)[0];assert result['status']=='valid',(n,result);rows[n]=result
    return dict(lemmas=rows,real_cut_limit_automatically_proved=False)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));u=inv['units'][200];assert u['id']=='einstein-1905:u0201' and digest(u['text'].encode())==u['text_sha256']
    math={x['id']:x for x in inv['math']};assert ''.join(ET.fromstring(math['M0348']['mathml']).itertext()).strip()=='V'
    return dict(status='mean_flux_and_finite_left_boundary_prepared_source_integration_pending',units=[dict(unit=u['id'],unit_sha256=u['text_sha256'],text=u['text'],math=[dict(id=n,sha256=math[n]['sha256'],mathml=math[n]['mathml']) for n in u['math_ids']])],observations=LIMITS,unresolved=[LIMITS[-1]],interpretation_references=['https://www.feynmanlectures.caltech.edu/II_27.html','https://ocw.mit.edu/courses/2-71-optics-spring-2009/c15fc0942eac409b6adb1b558c210c00_LDlGKU0ryQ8.pdf'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in (INVENTORY,FACSIMILE,DOC)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert len(new.document['statements'])==383 and new.document['statements']==old.document['statements']
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    assert all(d['kind']=='definition' for d in new.document['declarations'][len(old.document['declarations']):])
    load_annotations(ROOT,BASIS,ANNOTATIONS)
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    doc=core()
    for style in ('compact','full'):
        body=format_graph(doc,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=len(MEANINGS),new_primitives=0,old_383_statements_and_judgments_preserved=True,no_new_source_completion_claim=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('flux',flux_checks),('average',average_checks),('scaling',scaling_checks),('point',point_checks),('quantifier',quantifier_checks),('binding',binding_checks),('polynomial',polynomial_checks),('structure',structure_checks)]}
    helpers=('check_coordinate_correspondence','check_clock_site_time','check_material_relative_frame','check_aberration_line','check_distant_direction_geometry','check_wave_inquiry','check_wave_cycle_frequency','check_real_products','compose_amplitude_specialization','compose_doppler_infinity','compose_material_relative_frame','compose_limits','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,*DEPENDENCIES,'scripts/compose_radiative_intensity.py','scripts/check_radiative_intensity.py','tests/test_radiative_intensity.py',*(f'scripts/{n}.py' for n in helpers),'noema/polynomial_proofs.py'}
    return dict(status='mean_radiative_flux_and_finite_left_boundary_dependencies_checked',document=FULL,**results,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
