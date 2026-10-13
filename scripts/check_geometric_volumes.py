"""Check integral reuse, certified scalar bounds and explicit volume wiring."""
import argparse
from fractions import Fraction as F
import hashlib
from itertools import product
import json

from noema.finite_semantics import FunctionValue, SequenceValue, evaluate_document
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.polynomial_proofs import verify_universal
from noema.script import encode, decode
from scripts.check_coordinate_correspondence import abstract
from scripts.check_described_appraisals import candidate
from scripts.check_plane_waveforms import setup, evaluate, OPS
from scripts.check_integrals import cell_value, CELL, ARITHMETIC
from scripts.check_real_products import MEANINGS, assertion
from scripts.check_moving_light_trip import literal
from scripts.compose_limits import call as k, app, op, both, v
from scripts.compose_geometric_volumes import ROOT, PARENT, INTEGRALS, ALIASES, BUILDERS, CUT, rename, integral_declarations, generic_composed, source_composed, core_composed

REPORT=ROOT/'reports/geometric-volumes-v1.json'


def reuse_checks(text):
    old=parse((ROOT/INTEGRALS).read_text(encoding='utf-8'))
    source=parse(text)
    declarations={d['name']:d for d in source['declarations']}
    for d in integral_declarations():
        if declarations[d['name']]!=d:raise ValueError('Imported integral changed')
    # Also compare the dependencies whose existing implementations are reused.
    for oldname,newname in (('la','sjo'),('lb','sjp'),('lg','sxs')):
        original=next(d for d in old['declarations'] if d['name']==oldname)
        adapted=rename(original)
        adapted['name']=newname
        if adapted!=declarations[newname]:
            raise ValueError('Integral dependency differs: '+oldname)
    products={'cd':'shv','cb':'shu','cc':'sah'}
    def adapt_product(node):
        if isinstance(node,list):return [adapt_product(value) for value in node]
        if not isinstance(node,dict):return node
        result={key:adapt_product(value) for key,value in node.items()}
        if result.get('kind')=='call' and result.get('symbol')=='ca':
            return {'kind':'call','symbol':'bc','arguments':[{'kind':'call','symbol':'bb','arguments':[
                {'kind':'number','numerator':0,'denominator':1}]},result['arguments'][0]]}
        if 'symbol' in result:result['symbol']=products.get(result['symbol'],result['symbol'])
        if result.get('kind')=='definition':result['name']=products.get(result['name'],result['name'])
        return result
    for oldname,newname in products.items():
        original=next(d for d in old['declarations'] if d['name']==oldname)
        if adapt_product(original)!=declarations[newname]:raise ValueError('Product dependency differs: '+oldname)
    return {'imported_definitions':7,'body_preserved_under_declared_symbol_mapping':True,
        'interval_validity_and_error_dependencies_match':True,'aliases':ALIASES,
        'product_absolute_value_and_nonnegative_product_match_after_expanding_zero_comparison':True}


def polynomial_checks():
    mul=lambda a,b:k('ad',a,b)
    add=lambda a,b:k('ab',a,b)
    sub=lambda a,b:add(a,k('ac',b))
    sq=lambda a:mul(a,a)
    zero,one=literal(0),literal(1)
    x,y,fx,fy=map(v,('x','y','fx','fy'))
    graphs=both(k('seea',x,fx),k('seea',y,fy),op('u',k('aa',y,x)))
    pi,R,D,L,H=map(v,('pi','radius','factor','lower','upper'))
    primitive=lambda t:k('seef',pi,R,D,t)
    volume=mul(literal(F(4,3)),mul(pi,mul(R,sq(R))))
    bound=v('bound')
    tag=v('tag')
    height=lambda t:k('seec',pi,R,D,t)
    error=sub(mul(sub(H,L),height(tag)),sub(primitive(H),primitive(L)))
    residual=mul(mul(pi,sq(D)),mul(sub(H,L),sub(mul(literal(F(1,3)),add(sq(H),add(mul(H,L),sq(L)))),sq(tag))))
    claims={
        'reciprocal_profile_is_decreasing':assertion('x y fx fy',op('y',graphs,op('u',k('aa',fx,fy)))),
        'profile_has_uniform_lipschitz_bound':assertion('x y fx fy',op('y',graphs,op('u',k('aa',mul(literal(2),sub(y,x)),sub(fx,fy))))),
        'sphere_primitive_endpoints':assertion('pi radius',op('e',
            sub(k('seef',pi,R,one,R),k('seef',pi,R,one,k('ac',R))),volume)),
        'ellipsoid_primitive_endpoints':assertion('pi radius factor bound',op('y',op('e',mul(D,bound),R),
            op('e',mul(D,sub(primitive(bound),primitive(k('ac',bound)))),volume))),
        'quadratic_cell_error_identity':assertion('pi radius factor lower upper tag',op('e',error,residual)),
        'primitive_differences_telescope':assertion('pi radius factor lower upper tag',op('e',
            add(sub(primitive(tag),primitive(L)),sub(primitive(H),primitive(tag))),sub(primitive(H),primitive(L)))),
        'volume_ratio_from_two_endpoint_values':assertion('radius pi factor lower upper',op('y',both(
            k('seed',R,pi,L),k('seee',R,pi,D,H)),op('e',mul(D,H),L))),
        'wrong_pi_scale_counterexample':assertion('',k('seea',literal(0),literal(4))),
        'missing_cube_counterexample':assertion('',k('seed',literal(2),literal(3),literal(16))),
        'unchanged_volume_counterexample':assertion('',k('seee',literal(1),literal(3),literal(2),literal(4))),
    }
    rows={}
    for name,claim in claims.items():
        result=verify_universal(parse(generic_composed()[0]+claim),MEANINGS,timeout_ms=20000)[0]
        if result['status']!=('invalid' if name.endswith('counterexample') else 'valid'):
            raise ValueError('Geometric volume algebra differs: '+name+repr(result))
        rows[name]=result
    return {'claims':rows,'rational_polynomial_lemmas_only':True,
        'fundamental_theorem_or_change_of_variables_proved':False,'all_real_pi_existence_and_uniqueness_proved':False}


def pi_enclosures():
    base=generic_composed()[0]
    queries='''r zp[] j[h[b] b].r zf[b] b.r zs[] b.
q[k mb[k zp[] n p a b n p b b]].
q[e[k md[k zp[] p zf]][k zs[]]].'''
    tag=app(v('cell'),literal(2))
    step='i[state c cell h[b] b]['+both(v('state'),k('seea',tag,k('zf',tag)))+']'
    queries+='q['+op('q',k('zp'),op('e',literal(0),literal(0)),step)+'].'
    doc=parse(base+queries)
    rows=[]
    previous=None
    for size in (4,8,16,32):
        totals=[]
        for right in (False,True):
            cells=tuple((F(i,size),F(i+1,size),F(i+int(right),size)) for i in range(size))
            total=sum(F(1,size)/(1+tag*tag) for _,_,tag in cells)
            model={**ARITHMETIC,'zp':lambda:SequenceValue(tuple(cell_value(c) for c in cells),json.dumps(CELL,sort_keys=True,separators=(',',':'))),
                'zf':lambda x:1/(1+x*x),'zs':lambda:total}
            actual=[row['value'] for row in evaluate_document(doc,individuals=('object',),situations=('now',),primitives=model,max_steps=5_000_000)]
            if actual!=[True]*3:raise ValueError('Pi rectangle sum or partition differs')
            totals.append(4*total)
        upper,lower=totals
        if upper-lower!=F(2,size):raise ValueError('Pi enclosure width differs from telescoping endpoints')
        if previous and not (previous[0]<lower<upper<previous[1]):raise ValueError('Pi enclosures not nested')
        previous=lower,upper
        rows.append({'partition_cells':size,'lower':str(lower),'upper':str(upper),'width':str(upper-lower),
            'left_and_right_partitions_checked':True,'profile_graph_checked_at_every_tag':True})
    return {'cases':rows,'finite_enclosures_not_exact_pi':True,'rational_arithmetic_only':True}


def binding_checks(texts):
    names=tuple('j'+n for n in 'abcdefghijklm')
    # V,v,a,b,c,R,P,S,S',power,newpower,E,E'. P=3 is ONLY a
    # rational stand-in after replacing the unbounded pi predicate by an oracle.
    # No such fixture is a model of the actual definition of pi.
    args=list(map(k,names));V,s,a,b,c,R,pi,S,newS,p,newp,E,newE=args
    queries=''.join('q['+k(name,*values)+'].' for name,values in (
        ('sedp',[V,s,a,b,c,R,pi,S,newS]), ('sedn',[R,pi,S]),
        ('sedq',[V,s,a,p,newp,S,newS,pi,E,newE]), ('sedr',[pi,p,k('shv',E,k('sjd',S))])))
    docs=[abstract(candidate(text,''.join('r '+n+'[] '+CUT+'.' for n in names)+queries),OPS|{'sedi','sede'}) for text in texts]
    def run(numbers,pi_known=True,integrals_known=True,wrong_bounds=False):
        rows=[];observations=[]
        for doc in docs:
            fixture,model=setup(doc);make,read=fixture.make,fixture.read
            for name,value in zip(names,numbers,strict=True):model[name]=lambda value=value:make(value)
            light,speed,ax,ay,az,radius,constant,oldvol,newvol,power,newpower,energy,newenergy=map(F,numbers)
            beta=F(5,4) if speed else F(1)
            D=beta*(1-ax*speed/light) if light else F(1)
            sampled=[]
            def integral(lower,upper,function,value):
                lo,hi,val=read(lower),read(upper),read(value)
                # A deliberately finite binding fixture for two known families.
                # Sample fingerprints are not a certificate of global equality.
                samples=tuple(read(function(make(x))) for x in (F(0),F(1,2),F(1)))
                sampled.append((str(lo),str(hi),str(val),list(map(str,samples))))
                accepted=False
                for factor in (F(1),D):
                    width=radius/factor if factor else F(0)
                    expected_samples=tuple(constant*(radius*radius-factor*factor*x*x) for x in (F(0),F(1,2),F(1)))
                    expected_volume=F(4,3)*constant*radius**3/factor if factor else F(0)
                    accepted |= ((lo,hi)==(-width,width+(1 if wrong_bounds else 0)) and samples==expected_samples and val==expected_volume)
                return integrals_known and accepted
            model.update(sedi=lambda candidate:pi_known and read(candidate)==constant,sede=integral)
            rows.append(evaluate(doc,model));observations.append(sampled)
        if rows[0]!=rows[1] or observations[0]!=observations[1]:raise ValueError('Standalone volume bindings differ')
        return rows[0]
    cases=[]
    for speed,ax,radius in product((-3,0,3),(-1,0,1),(1,2)):
        beta=F(5,4) if speed else F(1);D=beta*(1-ax*F(speed,5))
        constant=F(3);S=F(4,3)*constant*radius**3;E=F(2);power=8*constant*E/S
        numbers=(5,speed,ax,1 if ax==0 else 0,0,radius,constant,S,S/D,power,power*D**2,E,E*D)
        result=run(numbers)
        if result!=[True]*4:raise ValueError('Volume or 8*pi binding differs')
        cases.append({'speed':speed,'ax':ax,'radius':radius,'results':result})
    base=[5,3,0,1,0,1,3,4,F(16,5),12,F(75,4),2,F(5,2)]
    fixtures={
        'unknown_pi':({},dict(pi_known=False),[False]*4),
        'missing_integral_premise':({},dict(integrals_known=False),[False,True,True,True]),
        'mismatched_integration_bounds':({},dict(wrong_bounds=True),[False,True,True,True]),
        'wrong_sphere_volume':({7:8},{},[False,False,False,False]),
        'wrong_ellipsoid_volume':({8:4},{},[False,True,False,True]),
        'wrong_energy_coefficient':({11:16,12:20},{},[True,True,False,False]),
        'zero_radius':({5:0},{},[False,False,True,True]),
        'negative_radius':({5:-1},{},[False,False,True,True]),
        'nonunit_direction':({4:1},{},[False,True,True,True]),
        'zero_density_and_power':({9:0,10:0,11:0,12:0},{},[True,True,False,True]),
    }
    contrasts={}
    for name,(changes,options,expected) in fixtures.items():
        numbers=base.copy()
        for index,value in changes.items():numbers[index]=value
        actual=run(numbers,**options)
        if actual!=expected:raise ValueError('Volume binding contrast failed: '+name+repr(actual))
        contrasts[name]=actual
    return {'cases':cases,'contrasts':contrasts,'standalone_agrees':True,
        'pi_and_global_integrals_are_assumed_oracles':True,'stand_in_constant_is_not_pi':True,
        'profile_samples_check_argument_wiring_only':True,'not_a_model_of_unabstracted_pi_definition':True}


def pi_binding_checks(text):
    doc=abstract(candidate(text,'r ja[] '+CUT+'.q[k sedi[k ja[]]].'),OPS|{'sede'})
    results={}
    for label,known,wrong_value,wrong_profile in (('bound',True,False,False),('unknown_integral',False,False,False),
                                                ('wrong_quarter',True,True,False),('wrong_profile',True,False,True)):
        fixture,model=setup(doc);read,make=fixture.read,fixture.make
        model['ja']=lambda:make(3)
        def integral(lo,hi,function,value):
            samples=tuple(read(function(make(q))) for q in (F(0),F(1,2),F(1)))
            return known and (read(lo),read(hi),read(value))==(0,1,3 if wrong_value else F(3,4)) and samples==(
                (1,1,1) if wrong_profile else (1,F(4,5),F(1,2)))
        model['sede']=integral
        actual=evaluate(doc,model)
        if actual!=[label=='bound']:raise ValueError('Pi integral arguments differ')
        results[label]=actual
    return {'cases':results,'oracle_wiring_only_not_certification_of_candidate_three':True}


def refusals(text):
    rows={}
    for name,query in (('pi','q[k sedi[k bb[n p d b]]].'),('sphere','q[k sedm[k bb[n p b b] k bb[n p d b] k bb[n p e b]]].')):
        doc=candidate(text,query);fixture,model=setup(doc);model.update(ARITHMETIC)
        try:evaluate(doc,model)
        except ValueError as exc:
            if 'Cannot finitely quantify the rational number domain' not in str(exc):raise
            rows[name]={'refused':True,'reason':str(exc)}
        else:raise ValueError('A finite model certified an unbounded integral')
    return rows


def alignment():
    source=json.loads((ROOT/'artifacts/written-units-v1/einstein-1905.json').read_text(encoding='utf-8'))
    rows=[]
    for mid,defs in (('M0349',['sedi','sedr']),('M0350',['sedi','sedr']),('M0362',['sedp','sech']),('M0365',['sedq'])):
        item=next(m for m in source['math'] if m['id']==mid);unit=next(u for u in source['units'] if mid in u['math_ids'])
        rows.append({'unit':unit['id'],'unit_sha256':unit['text_sha256'],'math_id':mid,'math_sha256':item['sha256'],
            'definitions':defs,'status':'partial','review_ja':'πを積分で指定し、球・楕円体の断面積積分と8πの係数を記述した。一般測度との一致、積分法則の機械証明、エネルギー密度の物理法則と観測への帰属は未完。'})
    return {'segments':rows,'semantic_completion':False,'new_source_ranges':False}


def build_report():
    documents,sizes,texts={},{},[]
    for builder,stem in BUILDERS:
        text,basis=builder();doc=parse(text);texts.append(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text or json.loads((ROOT/('data/'+stem+'-basis-v1.json')).read_text(encoding='utf-8'))!=basis:raise ValueError('Stored geometric volumes differ')
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Volume roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis);sizes[stem]={'characters':len(text),'statements':len(doc['statements'])}
    doc,parent=parse(texts[1]),parse((ROOT/PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])]!=parent['declarations'] or doc['statements']!=parent['statements']:raise ValueError('Parent changed')
    paths=[*documents,PARENT,INTEGRALS,'data/integrals-basis-v1.json',*['data/'+stem+'-basis-v1.json' for _,stem in BUILDERS],
        'scripts/compose_geometric_volumes.py','scripts/check_geometric_volumes.py','scripts/check_integrals.py',
        'scripts/check_plane_waveforms.py','scripts/check_tau_differential.py','noema/extraction.py','noema/finite_semantics.py',
        'noema/polynomial_proofs.py','artifacts/written-units-v1/einstein-1905.json']
    return json.loads(json.dumps({'status':'partial_pi_and_section_integrals_not_general_measure_or_physical_completion',
        'documents':documents,'sizes':sizes,'reuse':reuse_checks(texts[1]),'polynomial':polynomial_checks(),
        'pi_enclosures':pi_enclosures(),'bindings':binding_checks(texts[1:]),'pi_binding':pi_binding_checks(texts[2]),
        'refusals':refusals(texts[2]),'alignment':alignment(),'roundtrips':True,'parent_preserved':True,
        'new_primitives':0,'new_author_statements':0,'verified_full_units':{'kant-1784':0,'einstein-1905':0},
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}},ensure_ascii=False))


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');args=cli.parse_args();report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Geometric volume report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Pi and section integrals specified; finite bounds and conditional bindings checked')


if __name__=='__main__':main()
