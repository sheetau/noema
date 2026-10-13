"""Check mixed fields, inverse coordinate arguments, and an insufficient premise."""
import argparse
from fractions import Fraction as F
import hashlib
from itertools import product
import json
import xml.etree.ElementTree as ET

from noema.finite_semantics import FunctionValue, Content
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.polynomial_proofs import verify_universal
from noema.script import encode, decode
from scripts.check_comoving_labels import values
from scripts.check_coordinate_correspondence import abstract
from scripts.check_described_appraisals import candidate
from scripts.check_rod_setup import callbacks, guarded
from scripts.check_tau_differential import ConstructedCuts
from scripts.check_angle_composition import model_arithmetic
from scripts.check_parallel_composition import transform
from scripts.check_field_equations import AXES, DOMAIN, ARITHMETIC
from scripts.check_real_products import assertion
from scripts.check_moving_light_trip import literal
from scripts.compose_limits import call as k, app, op, both
from scripts.compose_field_transform import ROOT, CUT, POINT, FIELD, REGION, ROLES, PARENT, composed, generic_composed
from scripts.compose_field_equations import JET

REPORT=ROOT/'reports/field-transform-v1.json'
OPS=ARITHMETIC|{'sjt','sky'}
E=((1,2,3,4,1),(2,-1,1,3,-2),(-1,3,2,-2,3))
H=((2,-1,2,1,4),(3,2,-1,2,-3),(1,4,3,-1,2))


def setup(doc):
    fixture=ConstructedCuts();model=guarded(doc);model_arithmetic(fixture,model)
    model['szi']=lambda condition,left,right:left if condition else right
    for name,value in zip(ROLES,AXES):model[name]=lambda value=value:value
    return fixture,model


def affine_callback(doc,fixture,name,matrix):
    sort=next(d['result']['result'] for d in doc['declarations'] if d['name']==name)
    def component(role):
        coeff=matrix[AXES.index(role)] if role in AXES[:3] else (0,0,0,0,0)
        return FunctionValue(tuple(sort['parameters']),sort['result'],lambda *xs:fixture.make(coeff[4]+sum(a*fixture.read(x) for a,x in zip(coeff,xs))))
    return component


def field_values(e,h,point,speed,light=F(5),coordinate_speed=None,mix=True):
    x=transform(point,-speed if coordinate_speed is None else coordinate_speed,light)
    ev=[F(row[4])+sum(a*b for a,b in zip(row,x)) for row in e]
    hv=[F(row[4])+sum(a*b for a,b in zip(row,x)) for row in h]
    beta=transform((0,0,0,1),speed,light)[3];ratio=speed/light
    if not mix:return ev,hv
    return ([ev[0],beta*(ev[1]-ratio*hv[2]),beta*(ev[2]+ratio*hv[1])],
        [hv[0],beta*(hv[1]+ratio*ev[2]),beta*(hv[2]-ratio*ev[1])])


def polynomial_checks():
    b,r,e,h=('v '+s for s in ('beta','ratio','own','cross'))
    minus=lambda a,c:k('s6b',b,r,a,c);plus=lambda a,c:k('s6c',b,r,a,c)
    square=lambda a:k('ad',a,a);sub=lambda a,c:k('ab',a,k('ac',c))
    normalized=op('e',k('ad',square(b),sub(literal(1),square(r))),literal(1))
    claims={
        'minus_pair_then_plus_pair_is_identity':assertion('beta ratio own cross',op('y',normalized,op('e',plus(minus(e,h),minus(h,e)),e))),
        'plus_pair_then_minus_pair_is_identity':assertion('beta ratio own cross',op('y',normalized,op('e',minus(plus(e,h),plus(h,e)),e))),
        'minus_pair_preserves_difference_of_squares':assertion('beta ratio own cross',op('y',normalized,op('e',sub(square(minus(e,h)),square(minus(h,e))),sub(square(e),square(h))))),
        'same_direction_mixing_is_its_own_inverse':assertion('',op('e',k('s6b',literal(F(5,4)),literal(F(3,5)),k('s6b',literal(F(5,4)),literal(F(3,5)),literal(2),literal(1)),k('s6b',literal(F(5,4)),literal(F(3,5)),literal(1),literal(2))),literal(2))),
    };rows={}
    for label,claim in claims.items():
        result=verify_universal(parse(generic_composed()[0]+claim),{'ab':'add','ac':'negate','ad':'multiply'},timeout_ms=15000)[0]
        if result['status']!=('invalid' if label=='same_direction_mixing_is_its_own_inverse' else 'valid'):raise ValueError('Field mixing algebra differs: '+label)
        rows[label]=result
    return {'claims':rows,'mixing_only_not_chain_rule_or_maxwell_covariance':True}


DECLS='r ja[] '+FIELD+'.r jb[] '+FIELD+'.r jc[] '+CUT+'.r jd[] '+CUT+'.r je[] '+POINT+'.r jf[] '+FIELD+'.r jg[] '+FIELD+'.r jh[] '+REGION+'.'
TRANS_E='k s6k[k jc[] k jd[] k ja[] k jb[]]'
TRANS_H='k s6l[k jc[] k jd[] k ja[] k jb[]]'


def component_checks():
    args=[app('k je[]',k(role)) for role in ROLES];query=''
    for actual,expected in ((TRANS_E,'k jf[]'),(TRANS_H,'k jg[]')):
        for role in ROLES[:3]:query+='q['+k('sca',app(app(actual,k(role)),*args),app(app(expected,k(role)),*args))+'].'
    doc=abstract(candidate(composed()[0],DECLS+query),OPS);rows={}
    cases=[(f'baseline_{speed}_{i}',F(speed),point) for speed in (0,3,-3) for i,point in enumerate(((0,0,0,0),(1,2,-1,1),(2,-1,3,-2)))]
    cases += [(label,F(3),(1,2,-1,1)) for label in ('forward_coordinates','unmoved_coordinates','unmixed_components','swapped_fields','wrong_ey_sign','wrong_ez_sign','wrong_hy_sign','wrong_hz_sign')]
    for label,speed,point in cases:
        fixture,model=setup(doc);c,n=fixture.make,fixture.read
        e,h=field_values(E,H,point,speed)
        if label=='forward_coordinates':e,h=field_values(E,H,point,speed,coordinate_speed=speed)
        if label=='unmoved_coordinates':e,h=field_values(E,H,point,speed,coordinate_speed=F(0))
        if label=='unmixed_components':e,h=field_values(E,H,point,speed,mix=False)
        if label=='swapped_fields':e,h=field_values(H,E,point,speed)
        rawE,rawH=field_values(E,H,point,speed,mix=False)
        beta=transform((0,0,0,1),speed)[3];ratio=speed/F(5)
        for bad,field,index,wrong in (('wrong_ey_sign',e,1,beta*(rawE[1]+ratio*rawH[2])),
            ('wrong_ez_sign',e,2,beta*(rawE[2]-ratio*rawH[1])),
            ('wrong_hy_sign',h,1,beta*(rawH[1]-ratio*rawE[2])),
            ('wrong_hz_sign',h,2,beta*(rawH[2]+ratio*rawE[1]))):
            if label==bad:field[index]=wrong
        expectedE=[(0,0,0,0,value) for value in e];expectedH=[(0,0,0,0,value) for value in h]
        callbacks(doc,model,{'ja':affine_callback(doc,fixture,'ja',E),'jb':affine_callback(doc,fixture,'jb',H),
            'jf':affine_callback(doc,fixture,'jf',expectedE),'jg':affine_callback(doc,fixture,'jg',expectedH),
            'je':lambda role:c(point[AXES.index(role)] if role in AXES else 0)})
        model.update(jc=lambda:c(5),jd=lambda:c(speed));actual=values(doc,model,DOMAIN)
        if all(actual)!=label.startswith('baseline'):raise ValueError('Field component evaluation differs: '+label+repr(actual))
        rows[label]=actual
    return {'cases':rows,'known_affine_fields_and_exact_constructed_rational_cuts':True,
        'inverse_coordinate_map_and_component_mixing_tested_separately':True}


def region_checks():
    args=[app('k je[]',k(role)) for role in ROLES]
    doc=abstract(candidate(composed()[0],DECLS+'q['+app(k('s6m','k jc[]','k jd[]','k jh[]'),*args)+'].'),OPS);rows={}
    # Old region: x>0 and t<1. Domain membership is checked at the old point.
    for speed,point in ((3,(1,0,0,0)),(3,(-1,0,0,F(1,2))),(3,(1,0,0,F(9,10))),(-3,(1,0,0,F(1,2))),(0,(1,0,0,0)),(3,(0,0,0,0))):
        fixture,model=setup(doc);c,n=fixture.make,fixture.read;old=transform(point,F(-speed))
        callbacks(doc,model,{'je':lambda role:c(point[AXES.index(role)] if role in AXES else 0),
            'jh':lambda x,y,z,t:n(x)>0 and n(t)<1})
        model.update(jc=lambda:c(5),jd=lambda:c(speed));actual=values(doc,model,DOMAIN)
        if actual!=[old[0]>0 and old[3]<1]:raise ValueError('Pulled-back region differs')
        rows[str((speed,point))]={'accepted':actual[0],'old_point':[str(x) for x in old],
            'unchanged_numeric_point_would_be_inside':point[0]>0 and point[3]<1}
    return {'cases':rows,'region_and_fields_use_same_inverse_map':True}


def equation_checks():
    declarations=DECLS+'r ji['+FIELD+'] '+JET+'.'
    jet=lambda field:k('ji',field)
    query='q['+k('s5w','k jc[]',jet('k ja[]'),jet('k jb[]'))+'].q['+k('s5w','k jc[]',jet(TRANS_E),jet(TRANS_H))+'].'
    doc=abstract(candidate(composed()[0],declarations+query),OPS);rows={}
    zero=((0,0,0,0,0),)*3
    scenarios={
        'zero_fields':(zero,zero,F(3),[True,True]),
        'constant_fields':(tuple((0,0,0,0,n) for n in (1,2,3)),tuple((0,0,0,0,n) for n in (4,5,6)),F(3),[True,True]),
        'plane_profile_forward_boost':((zero[0],(1,0,0,-5,2),zero[0]),(zero[0],zero[0],(1,0,0,-5,2)),F(3),[True,True]),
        'plane_profile_reverse_boost':((zero[0],(1,0,0,-5,2),zero[0]),(zero[0],zero[0],(1,0,0,-5,2)),F(-3),[True,True]),
        'nonzero_divergence_counterexample':(((1,0,0,0,0),zero[0],zero[0]),zero,F(3),[True,False]),
        'counterexample_zero_speed_masks_failure':(((1,0,0,0,0),zero[0],zero[0]),zero,F(0),[True,True]),
        'arbitrary_affine_fields_not_solutions':(E,H,F(3),[False,False]),
    }
    for label,(e,h,speed,expected) in scenarios.items():
        fixture,model=setup(doc);c,n=fixture.make,fixture.read
        callbacks(doc,model,{'ja':affine_callback(doc,fixture,'ja',e),'jb':affine_callback(doc,fixture,'jb',h)})
        model.update(jc=lambda:c(5),jd=lambda:c(speed))
        sort=next(d['result'] for d in doc['declarations'] if d['name']=='ji')
        def known_affine_jet(field):
            # These inputs are solely the affine functions constructed above and
            # their explicitly linear Noema transforms. This is a fixture oracle,
            # not a derivative estimator or a verifier for arbitrary functions.
            def derivative(component,axis):
                if component not in AXES[:3] or axis not in AXES:return c(0)
                fn=field(component);origin=[c(0)]*4;point=origin.copy();point[AXES.index(axis)]=c(1)
                return c(n(fn(*point))-n(fn(*origin)))
            return FunctionValue(tuple(sort['parameters']),sort['result'],derivative)
        model['ji']=known_affine_jet;actual=values(doc,model,DOMAIN)
        if actual!=expected:raise ValueError('Transformed six equations differ: '+label+repr(actual))
        rows[label]=actual
    return {'cases':rows,'jet_is_oracle_for_supplied_affine_functions_only':True,
        'six_old_curl_equations_alone_are_insufficient':True,
        'counterexample':{'electric':['x','0','0'],'magnetic':['0','0','0'],'light':'5','speed':'3','beta':'5/4',
            'transformed_electric_x':'(5/4)*(xi+3*tau)','time_derivative':'15/4','magnetic_curl_x':'0'},
        'all_real_chain_rule_or_vacuum_covariance_proved':False}


def inverse_checks():
    args=[app('k je[]',k(role)) for role in ROLES]
    opposite=k('bf',k('bb',literal(0)),'k jd[]');query=''
    for operation,original in (('s6k','k ja[]'),('s6l','k jb[]')):
        recovered=k(operation,'k jc[]',opposite,TRANS_E,TRANS_H)
        for role in ROLES[:3]:query+='q['+k('sca',app(app(recovered,k(role)),*args),app(app(original,k(role)),*args))+'].'
    recovered_region=k('s6m','k jc[]',opposite,k('s6m','k jc[]','k jd[]','k jh[]'))
    query+='q['+op('z',app(recovered_region,*args),app('k jh[]',*args))+'].'
    doc=abstract(candidate(composed()[0],DECLS+query),OPS);rows={}
    for speed in (0,3,-3):
        for point in ((1,2,-1,F(1,2)),(-1,0,0,F(1,2))):
            fixture,model=setup(doc);c,n=fixture.make,fixture.read
            callbacks(doc,model,{'ja':affine_callback(doc,fixture,'ja',E),'jb':affine_callback(doc,fixture,'jb',H),
                'je':lambda role:c(point[AXES.index(role)] if role in AXES else 0),'jh':lambda x,y,z,t:n(x)>0 and n(t)<1})
            model.update(jc=lambda:c(5),jd=lambda:c(speed));actual=values(doc,model,DOMAIN)
            if actual!=[True]*7:raise ValueError('Inverse field and region transformation differs')
            rows[str((speed,point))]=actual
    return {'cases':rows,'both_mixing_and_coordinate_pullback_reversed':True,'finite_affine_fixtures_not_all_real_function_proof':True}


def premise_checks():
    doc=abstract(candidate(composed()[0],'q[t[k s6p[]][k ri[]]].'),{'s5z','sso','s45'});rows=[]
    for old,coordinates,admissible in product((False,True),repeat=3):
        model=guarded(doc);model.update(ri=lambda:'text',tc=lambda:ConstructedCuts().make(5),zb7=lambda:ConstructedCuts().make(3),
            s5z=lambda:Content(('motion','text','other'),(False,old,False)),
            sso=lambda:Content(('motion','text','other'),(False,coordinates,False)),s45=lambda light,speed:admissible)
        actual=values(doc,model,DOMAIN)
        if actual!=[old and coordinates and admissible]:raise ValueError('Partial transformation premise differs')
        rows.append({'old_equations':old,'coordinate_transform':coordinates,'admissible':admissible,'accepted':actual[0]})
    return {'cases':rows,'premise_is_not_claimed_sufficient_for_conclusion':True}


def attribution_checks():
    doc=parse(composed()[0]);doc['statements']=doc['statements'][-1:];rows={}
    for label in ('baseline','wrong_author','wrong_scope','wrong_context','reversed_inference','wrong_premise','wrong_conclusion'):
        model=guarded(doc)
        for name,value in {'znq':'node','rd':'author','zno':'scope','ri':'text'}.items():model[name]=lambda value=value:value
        def relation(node,who,premise,conclusion,scope,context):
            expected=('s6o','s6p') if label=='reversed_inference' else ('s5z' if label=='wrong_premise' else 's6p','s5z' if label=='wrong_conclusion' else 's6o')
            return (node,who,scope,context)==('node','other' if label=='wrong_author' else 'author','other' if label=='wrong_scope' else 'scope','other' if label=='wrong_context' else 'text') and (json.loads(premise.syntax)['symbol'],json.loads(conclusion.syntax)['symbol'])==expected
        model['zc']=relation;actual=values(doc,model,('node','author','scope','other'))
        if actual!=[label=='baseline']:raise ValueError('Transformation attribution differs: '+label)
        rows[label]=actual
    return {'cases':rows,'claimed_inference_does_not_certify_its_validity':True,'quoted_contents_not_executed_as_truth':True}


def finite_refusal():
    doc=abstract(candidate(composed()[0],DECLS+'q[k s6n[k jc[] k jd[] k ja[] k jb[] k jh[]]].'),OPS)
    fixture,model=setup(doc);c=fixture.make
    callbacks(doc,model,{'ja':affine_callback(doc,fixture,'ja',E),'jb':affine_callback(doc,fixture,'jb',H),'jh':lambda *xs:True})
    model.update(jc=lambda:c(5),jd=lambda:c(3))
    try:values(doc,model,DOMAIN)
    except ValueError as error:
        if 'Cannot finitely quantify the rational number domain' not in str(error):raise
        return {'refused':True,'reason':str(error)}
    raise ValueError('Finite evaluator accepted full transformed field equations')


def alignment():
    path=ROOT/'artifacts/written-units-v1/einstein-1905.json';source=json.loads(path.read_text(encoding='utf-8'))
    inventory=json.loads((ROOT/'reports/written-units-v1.json').read_text(encoding='utf-8'))
    if hashlib.sha256(path.read_bytes()).hexdigest()!=inventory['works']['einstein-1905']['units_sha256']:raise ValueError('Field transform inventory differs')
    rows=[]
    for index in (156,157,158,160):
        unit=next(u for u in source['units'] if u['id']==f'einstein-1905:u{index:04}')
        if hashlib.sha256(unit['text'].encode('utf-8')).hexdigest()!=unit['text_sha256']:raise ValueError('Field transform source text differs')
        for mid in unit['math_ids']:
            m=next(m for m in source['math'] if m['id']==mid)
            if hashlib.sha256(m['mathml'].encode('utf-8')).hexdigest()!=m['sha256']:raise ValueError('Field transform source math differs')
            rows.append(dict(unit=unit['id'],unit_sha256=unit['text_sha256'],math_id=mid,math_sha256=m['sha256'],
                definitions=['s6f','s6g','s6i','s6j','s6k','s6l','s6m','s6n','s6o','s6p','soy'],status='partial_explicit_reading',full_semantic_equivalence=False))
    # Check the displayed mixed derivative numerators in document order.
    ns='{http://www.w3.org/1998/Math/MathML}';numerators=[]
    for mid in ('M0291','M0292'):
        m=next(m for m in source['math'] if m['id']==mid)
        for fraction in ET.fromstring(m['mathml']).iter(ns+'mfrac'):
            numerator=''.join(fraction[0].itertext());denominator=''.join(fraction[1].itertext())
            if numerator.startswith('∂'):numerators.append((numerator,denominator))
    expected=[('∂X','∂τ'),('∂β(N−vVY)','∂η'),('∂β(M+vVZ)','∂ζ'),
        ('∂β(Y−vVN)','∂τ'),('∂L','∂ζ'),('∂β(N−vVY)','∂ξ'),
        ('∂β(Z+vVM)','∂τ'),('∂β(M+vVZ)','∂ξ'),('∂L','∂η'),
        ('∂L','∂τ'),('∂β(Y−vVN)','∂ζ'),('∂β(Z+vVM)','∂η'),
        ('∂β(M+vVZ)','∂τ'),('∂β(Z+vVM)','∂ξ'),('∂X','∂ζ'),
        ('∂β(N−vVY)','∂τ'),('∂X','∂η'),('∂β(Y−vVN)','∂ξ')]
    if numerators!=expected:raise ValueError('Transformed six equation order differs: '+repr(numerators))
    return {'segments':rows,'source_derivative_order':[list(p) for p in numerators],
        'prose_without_explicit_range_not_counted':True,'physical_moving_field_identification_unwritten':True,
        'insufficient_displayed_premise_recorded':True,'facsimile_review':False,'verified_full_units':0}


def build_report():
    documents={}
    for builder,name in ((generic_composed,'field-transform'),(composed,'einstein-field-transform')):
        text,basis=builder();doc=parse(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text or json.loads((ROOT/('data/'+name+'-basis-v1.json')).read_text(encoding='utf-8'))!=basis:raise ValueError('Stored field transform artifacts differ')
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Field transform roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis)
    paths=list(documents)+['data/field-transform-basis-v1.json','data/einstein-field-transform-basis-v1.json',PARENT,
        'scripts/compose_field_transform.py','scripts/check_field_transform.py','scripts/check_field_equations.py',
        'scripts/check_tau_differential.py','scripts/check_angle_composition.py','scripts/check_parallel_composition.py',
        'noema/discourse.py','noema/finite_semantics.py','noema/polynomial_proofs.py',
        'artifacts/written-units-v1/einstein-1905.json','reports/written-units-v1.json']
    return {'status':'partial_field_transform_with_insufficient_premise_counterexample','documents':documents,
        'polynomial_lemmas':polynomial_checks(),'components':component_checks(),'regions':region_checks(),
        'equations_and_counterexample':equation_checks(),'inverse':inverse_checks(),'premise':premise_checks(),'attribution':attribution_checks(),
        'finite_refusal':finite_refusal(),'alignment':alignment(),'roundtrips':True,
        'verified_full_units':{'einstein-1905':0,'kant-1784':0},
        'notation_size':{'canonical_source_document_characters':len(text),'added_characters':len(text)-len((ROOT/PARENT).read_text(encoding='utf-8'))},
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args();report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Field transform report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Field mixing, pullback, six equations and insufficient-premise counterexample checked')


if __name__=='__main__':main()
