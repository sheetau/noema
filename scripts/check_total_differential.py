"""Check uniform-remainder ingredients and reject axis-only evidence."""
import argparse
from fractions import Fraction as F
import hashlib
import json

from noema.finite_semantics import SequenceValue
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.polynomial_proofs import verify_universal
from noema.script import encode, decode
from scripts.check_comoving_labels import values
from scripts.check_coordinate_correspondence import abstract
from scripts.check_described_appraisals import candidate
from scripts.check_rod_setup import callbacks
from scripts.check_field_transform import setup as base_setup, affine_callback, OPS
from scripts.check_field_equations import AXES, DOMAIN as INDIVIDUALS, jet_callback
from scripts.check_field_constraints import E,H
from scripts.check_real_products import assertion
from scripts.check_moving_light_trip import literal
from scripts.compose_limits import call as k, app, op, both
from scripts.compose_total_differential import ROOT, CUT, POINT, FUNCTION, DOMAIN, FIELD, REGION, JET, PARENT, composed, generic_composed

REPORT=ROOT/'reports/total-differential-v1.json'
OPERATIONS=OPS|{'shu'}
DECLS='r ja[] j[a].r jb[] '+POINT+'.r jc[] '+FUNCTION+'.r jd[] '+POINT+'.r je[] '+POINT+'.r jf[] '+CUT+'.r jg[] '+DOMAIN+'.r jh[] '+CUT+'.'


def setup(doc):
    fixture,model=base_setup(doc);model['shu']=lambda value:fixture.make(abs(fixture.read(value)))
    names={d['name'] for d in doc['declarations'] if d['kind']=='primitive'}
    return fixture,{name:callback for name,callback in model.items() if name in names}


def polynomial_checks():
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    parent['statements']=[];parent['declarations']=[d for d in parent['declarations'] if d['name'] in ('aa','ab','ac','ad','shw')]
    text=format_graph(parent,'compact');v=lambda n:'v '+n
    add=lambda a,b:k('ab',a,b);mul=lambda a,b:k('ad',a,b);sub=lambda a,b:add(a,k('ac',b))
    def total(items):
        result=literal(0)
        for item in items:result=add(result,item)
        return result
    point=list(map(v,('x','y','z','t')));step=list(map(v,('hx','hy','hz','ht')));coeff=list(map(v,('a','b','c','d')))
    shifted=[add(x,h) for x,h in zip(point,step)];affine=lambda xs:k('shw',*coeff,v('offset'),*xs)
    quadratic=lambda xs:total(mul(x,x) for x in xs)
    affine_error=sub(sub(affine(shifted),affine(point)),total(mul(a,h) for a,h in zip(coeff,step)))
    quadratic_error=sub(sub(quadratic(shifted),quadratic(point)),total(mul(mul(literal(2),x),h) for x,h in zip(point,step)))
    magnitudes=list(map(v,('ax','ay','az','at')));norm=total(magnitudes);epsilon=v('epsilon')
    absolute_conditions=both(*(both(op('u',k('aa',a,literal(0))),op('e',mul(a,a),mul(h,h))) for a,h in zip(magnitudes,step)))
    h=v('h')
    claims={
        'affine_error_zero_for_all_four_increments':assertion('a b c d offset x y z t hx hy hz ht',op('e',affine_error,literal(0))),
        'quadratic_error_is_sum_of_squared_increments':assertion('x y z t hx hy hz ht',op('e',quadratic_error,quadratic(step))),
        'quadratic_uniform_remainder_bound':assertion('hx hy hz ht ax ay az at epsilon',op('y',both(absolute_conditions,k('aa',literal(0),norm),k('aa',norm,epsilon)),k('aa',quadratic(step),mul(epsilon,norm)))),
        'mixed_axis_counterexample_has_diagonal_value_half_h':assertion('h',op('e',mul(add(h,h),mul(literal(F(1,2)),h)),mul(h,h))),
        'every_positive_diagonal_step_violates_zero_gradient_bound':assertion('h',op('y',k('aa',literal(0),h),k('aa',mul(literal(F(1,8)),add(h,h)),mul(literal(F(1,2)),h)))),
    };rows={}
    for name,claim in claims.items():
        result=verify_universal(parse(text+claim),{'aa':'less','ab':'add','ac':'negate','ad':'multiply'},timeout_ms=20000,max_expansion=200000)[0]
        if result['status']!='valid':raise ValueError('Total differential algebra differs: '+name+repr(result))
        rows[name]=result
    return {'claims':rows,'rational_error_identities_and_bounds_only':True,'arbitrary_real_chain_rule_proved':False}


def remainder_checks():
    doc=abstract(parse(generic_composed()[0]+DECLS+'q[k s7w[k ja[] k jc[] k jb[] k jd[] k je[] k jf[]]].'),OPERATIONS);rows={}
    cases={
        'affine_mixed_step':('affine',(1,2,3,4),(1,-2,3,-1),(2,3,5,7),F(1,8),AXES,True),
        'affine_wrong_gradient':('affine',(1,2,3,4),(1,0,0,0),(3,3,5,7),F(1,8),AXES,False),
        'zero_step_is_not_punctured':('affine',(1,2,3,4),(0,0,0,0),(2,3,5,7),F(1,8),AXES,False),
        'zero_epsilon':('affine',(1,2,3,4),(1,0,0,0),(2,3,5,7),F(0),AXES,False),
        'negative_epsilon':('affine',(1,2,3,4),(1,0,0,0),(2,3,5,7),F(-1),AXES,False),
        'quadratic_small_mixed_step':('quadratic',(1,2,3,4),(F(1,64),F(-1,64),0,0),(2,4,6,8),F(1,8),AXES,True),
        'quadratic_at_strict_bound':('quadratic',(0,0,0,0),(F(1,8),0,0,0),(0,0,0,0),F(1,8),AXES,False),
        'quadratic_large_step':('quadratic',(0,0,0,0),(F(1,2),0,0,0),(0,0,0,0),F(1,8),AXES,False),
        'two_axes_only':('affine',(1,2,99,99),(1,-1,0,0),(2,3,0,0),F(1,8),('x','y'),True),
        'reordered_axes':('affine',(1,2,3,4),(1,-2,3,-1),(2,3,5,7),F(1,8),tuple(reversed(AXES)),True),
        'duplicate_axes':('affine',(0,0,0,0),(1,0,0,0),(2,3,5,7),F(1,8),('x','x'),False),
        'empty_axes':('affine',(0,0,0,0),(1,0,0,0),(2,3,5,7),F(1,8),(),False),
    }
    for label,(kind,point,step,gradient,epsilon,axes,expected) in cases.items():
        fixture,model=setup(doc);c,n=fixture.make,fixture.read
        def function(vector):
            xs=[n(vector(a)) for a in AXES]
            result=sum(x*x for x in xs) if kind=='quadratic' else 11+sum(a*x for a,x in zip((2,3,5,7),xs))
            return c(result+1000*n(vector('other')))
        callbacks(doc,model,{'jb':lambda role:c(point[AXES.index(role)] if role in AXES else 99),
            'jd':lambda role:c(gradient[AXES.index(role)] if role in AXES else 99),
            'je':lambda role:c(step[AXES.index(role)] if role in AXES else 99),'jc':function})
        model.update(ja=lambda:SequenceValue(axes,'"individual"'),jf=lambda:c(epsilon))
        actual=values(doc,model,INDIVIDUALS)
        if actual!=[expected]:raise ValueError('Uniform remainder ingredients differ: '+label+repr(actual))
        rows[label]=actual
    return {'cases':rows,'unlisted_coordinates_projected_to_zero_before_function_evaluation':True,
        'finite_remainder_checks_not_a_full_epsilon_delta_verification':True}


def counterexample_checks():
    doc=abstract(parse(generic_composed()[0]+DECLS+'q[k s7w[k ja[] k jc[] k jb[] k jd[] k je[] k jf[]]].'),OPERATIONS);rows={}
    for step in (F(1,2),F(1,16),F(1,256)):
        for direction in (*AXES,'xt'):
            fixture,model=setup(doc);c,n=fixture.make,fixture.read
            def function(point):
                x,t=n(point('x')),n(point('t'));denominator=abs(x)+abs(t)
                return c(x*t/denominator if denominator else 0)
            callbacks(doc,model,{'jb':lambda role:c(0),'jd':lambda role:c(0),'jc':function,
                'je':lambda role:c(step if role in (('x','t') if direction=='xt' else (direction,)) else 0)})
            model.update(ja=lambda:SequenceValue(AXES,'"individual"'),jf=lambda:c(F(1,8)))
            actual=values(doc,model,INDIVIDUALS)
            if actual!=[direction!='xt']:raise ValueError('Axis-only differentiability evidence was accepted')
            rows[str(step)+':'+direction]=actual
    return {'cases':rows,'function':'F(x,y,z,t)=x*t/(abs(x)+abs(t)), with zero on x=t=0',
        'all_coordinate_axis_remainders_zero_but_mixed_direction_fails':True,
        'all_positive_diagonal_scales_also_checked_by_rational_inequality':True}


def field_binding_checks():
    decls='r ja[] '+FIELD+'.r jb[] '+FIELD+'.r jc[] '+REGION+'.r jd[] '+POINT+'.r je[] '+JET+'.r jf[] '+JET+'.'
    args='k ja[] k jb[] k jc[] k jd[] k je[] k jf[]'
    doc=abstract(candidate(composed()[0],decls+'q[k s74['+args+']].q[k s6s['+args+']].q[k s75['+args+']].'),OPERATIONS|{'s7x','s6s'});rows={}
    for label in ('baseline','wrong_gradient','wrong_point','outside_region','partials_only','total_only'):
        fixture,model=setup(doc);c,n=fixture.make,fixture.read;gradient=[list(row) for row in E]
        if label=='wrong_gradient':gradient[1][2]+=1
        callbacks(doc,model,{'ja':affine_callback(doc,fixture,'ja',[(*row,0) for row in E]),'jb':affine_callback(doc,fixture,'jb',[(*row,0) for row in H]),
            'jc':lambda *xs:label!='outside_region','jd':lambda role:c((1,2,3,5 if label=='wrong_point' else 4)[AXES.index(role)] if role in AXES else 0),
            'je':jet_callback(fixture,gradient),'jf':jet_callback(fixture,H)})
        seen=[]
        def total(axes,function,domain,point,grad):
            p=tuple(n(point(a)) for a in AXES);g=tuple(n(grad(a)) for a in AXES);seen.append(g)
            return label!='partials_only' and axes.items==AXES and p==(1,2,3,4) and domain(point) and g in E+H and n(function(point))==sum(a*b for a,b in zip(g,p))
        model['s7x']=total;model['s6s']=lambda *args:label!='total_only'
        actual=values(doc,model,INDIVIDUALS)
        full=label in ('baseline','total_only');partial=label!='total_only'
        if actual!=[full,partial,full and partial]:raise ValueError('Field total/partial binding differs: '+label+repr(actual))
        if label=='baseline' and set(seen)!=set(E+H):raise ValueError('All six component gradients were not used')
        rows[label]=actual
    return {'cases':rows,'total_and_partial_derivative_relations_are_fixture_oracles':True,'same_six_gradients_and_four_coordinate_order':True}


def finite_refusals():
    queries={'open_ball':'k s7u[k ja[] k jc[] k jg[] k jb[] k jh[]]',
        'uniform_total_differential':'k s7x[k ja[] k jc[] k jg[] k jb[] k jd[]]'};rows={}
    for label,query in queries.items():
        doc=abstract(parse(generic_composed()[0]+DECLS+'q['+query+'].'),OPERATIONS);fixture,model=setup(doc);c,n=fixture.make,fixture.read
        callbacks(doc,model,{'jb':lambda role:c(0),'jd':lambda role:c(0),'jc':lambda point:c(0),'jg':lambda point:True})
        model.update(ja=lambda:SequenceValue(AXES,'"individual"'),jh=lambda:c(1))
        try:values(doc,model,INDIVIDUALS)
        except ValueError as error:
            if 'Cannot finitely quantify the rational number domain' not in str(error):raise
            rows[label]={'refused':True,'reason':str(error)}
        else:raise ValueError('Finite sampling replaced uniform neighborhood quantification')
    return rows


def alignment():
    path=ROOT/'artifacts/written-units-v1/einstein-1905.json';source=json.loads(path.read_text(encoding='utf-8'))
    inventory=json.loads((ROOT/'reports/written-units-v1.json').read_text(encoding='utf-8'))
    if hashlib.sha256(path.read_bytes()).hexdigest()!=inventory['works']['einstein-1905']['units_sha256']:raise ValueError('Differential source inventory differs')
    rows=[]
    for index,mid in ((157,'M0291'),(158,'M0292')):
        unit=next(u for u in source['units'] if u['id']==f'einstein-1905:u{index:04}');m=next(m for m in source['math'] if m['id']==mid)
        if hashlib.sha256(unit['text'].encode('utf-8')).hexdigest()!=unit['text_sha256'] or hashlib.sha256(m['mathml'].encode('utf-8')).hexdigest()!=m['sha256']:raise ValueError('Differential source hash differs')
        rows.append(dict(unit=unit['id'],unit_sha256=unit['text_sha256'],math_id=mid,math_sha256=m['sha256'],definitions=['s7q','s7r','s7s','s7t','s7u','s7v','s7w','s7x','s7y','s7z','s74','s75','s76'],status='explicit_interpretive_annotation',full_semantic_equivalence=False))
    return {'segments':rows,'additional_local_regularity_not_explicit_source_words':True,'new_source_text_ranges':0,'verified_full_units':0}


def build_report():
    documents={}
    for builder,name in ((generic_composed,'total-differential'),(composed,'einstein-total-differential')):
        text,basis=builder();doc=parse(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text or json.loads((ROOT/('data/'+name+'-basis-v1.json')).read_text(encoding='utf-8'))!=basis:raise ValueError('Stored total differential differs')
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Total differential roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis)
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    if doc['statements']!=parent['statements']:raise ValueError('Author statements changed')
    paths=list(documents)+['data/total-differential-basis-v1.json','data/einstein-total-differential-basis-v1.json',PARENT,
        'scripts/compose_total_differential.py','scripts/check_total_differential.py','scripts/check_field_transform.py','scripts/check_field_constraints.py',
        'scripts/check_tau_differential.py','noema/discourse.py','noema/finite_semantics.py','noema/polynomial_proofs.py',
        'artifacts/written-units-v1/einstein-1905.json','reports/written-units-v1.json']
    return {'status':'uniform_total_differentiability_and_axis_only_counterexample','documents':documents,
        'polynomial_lemmas':polynomial_checks(),'remainder':remainder_checks(),'mixed_direction_counterexample':counterexample_checks(),
        'field_binding':field_binding_checks(),'finite_refusals':finite_refusals(),'alignment':alignment(),
        'roundtrips':True,'author_statements_unchanged':True,'verified_full_units':{'einstein-1905':0,'kant-1784':0},
        'notation_size':{'canonical_source_document_characters':len(text),'added_characters':len(text)-len((ROOT/PARENT).read_text(encoding='utf-8'))},
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args();report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Total differential report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Uniform remainder, mixed-axis counterexample and field gradients checked')


if __name__=='__main__':main()
