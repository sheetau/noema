"""Check the reviewed root/quotient expression without discarding denominator signs."""
import argparse
from fractions import Fraction as F
import hashlib
import json

from noema.finite_semantics import FunctionValue
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.polynomial_proofs import verify_universal
from noema.script import encode, decode
from scripts.check_comoving_labels import values
from scripts.check_coordinate_correspondence import abstract
from scripts.check_described_appraisals import candidate
from scripts.check_rod_setup import guarded
from scripts.check_real_products import MEANINGS, assertion
from scripts.check_moving_light_trip import literal
from scripts.check_tau_differential import ARITHMETIC, ConstructedCuts
from scripts.check_transverse_time import square_root
from scripts.check_written_math_corrections import reviewed_math
from scripts.compose_angle_composition import ROOT, CUT, composed, k, op, both, v

REPORT=ROOT/'reports/angle-composition-v1.json'


def polynomial_checks():
    V,s,W,c,h,r,U,u,y=map(v,('light','speed','moving','cosine','sine','radical','result','longitudinal','transverse'))
    zero=literal(0);mul=lambda a,b:k('ad',a,b);sq=lambda a:mul(a,a);lt=lambda a,b:k('aa',a,b)
    D=k('ab',sq(V),mul(mul(s,W),c));core=(V,s,W,c,h)
    quotient=k('s2o',*core,r,U);squared=k('s2p',*core,U)
    domain=lt(sq(s),sq(V));root=k('s2n',*core,r)
    claims={
        'positive_denominator_recovers_unsquared_expression':assertion('light speed moving cosine sine radical result',
            op('y',both(root,domain,lt(zero,D)),op('z',quotient,squared))),
        'polar_components_preserve_squared_magnitude':assertion('light speed moving cosine sine longitudinal transverse result',
            op('y',k('s2q',u,y,W,c,h),op('z',squared,k('szm',V,s,u,y,W,U)))),
        'nonnegative_velocities_are_symmetric':assertion('light speed moving cosine sine radical result',
            op('y',both(op('u',lt(s,zero)),op('u',lt(W,zero))),op('z',quotient,k('s2o',V,W,s,c,h,r,U)))),
        'sine_orientation_does_not_change_expression':assertion('light speed moving cosine sine radical result',
            op('z',quotient,k('s2o',V,s,W,c,k('ac',h),r,U))),
        'subluminal_inputs_have_positive_denominator':assertion('light speed moving cosine sine',
            op('y',both(lt(zero,V),domain,op('u',lt(W,zero)),lt(W,V),k('szw',c,h)),lt(zero,D))),
        'positive_frame_unsigned_angle_matches_components':assertion('speed longitudinal transverse moving cosine sine',
            op('y',both(lt(zero,s),k('s2b',s,zero,s,u,y,W,c,h)),k('s2q',u,y,W,c,h))),
        'parallel_reviewed_value':assertion('',k('s2o',*(literal(x) for x in (5,3,1,1,0,4,F(25,7))))),
        'snapshot_sine_denominator_value_is_reviewed_value':assertion('',k('s2o',*(literal(x) for x in (5,3,1,1,0,4,4)))),
        'negative_denominator_preserves_negative_quotient':assertion('',k('s2o',*(literal(x) for x in (5,3,25,F(-3,5),F(4,5),20,-25)))),
        'squaring_cannot_select_quotient_sign':assertion('',op('y',k('s2p',*(literal(x) for x in (5,3,25,F(-3,5),F(4,5),25))),
            k('s2o',*(literal(x) for x in (5,3,25,F(-3,5),F(4,5),20,25))))),
    }
    text=composed()[0];rows={}
    for name,claim in claims.items():
        doc=candidate(text,claim)
        doc['declarations']=[d for d in doc['declarations'] if d['name'] in {'aa','ab','ac','ad','szk','szm','szw','s2b','s2n','s2o','s2p','s2q'}]
        result=verify_universal(doc,MEANINGS,timeout_ms=20000)[0]
        rejected={'snapshot_sine_denominator_value_is_reviewed_value','squaring_cannot_select_quotient_sign'}
        if result['status']!=('invalid' if name in rejected else 'valid'):raise ValueError('Angle composition algebra differs: '+name+repr(result))
        rows[name]=result
    return {'claims':rows,'rational_polynomial_lemmas_only':True,'all_real_cut_field_and_root_laws_proved':False}


CASES={
    # V, v, w, cosine, sine, U
    'parallel':((5,3,1,1,0,F(25,7)),True),
    'snapshot_denominator':((5,3,1,1,0,4),False),
    'light_speed_oblique':((5,3,5,F(3,5),F(4,5),5),True),
    'light_speed_negative_transverse':((5,3,5,F(3,5),F(-4,5),5),True),
    'light_speed_negative_longitudinal':((5,3,5,F(-3,5),F(4,5),5),True),
    'vertical':((5,3,5,0,1,5),True),
    'cancellation':((5,3,3,-1,0,0),True),
    'zero_point_speed':((5,3,0,1,0,3),True),
    'zero_frame_speed':((5,0,5,F(3,5),F(4,5),5),True),
    'signed_negative_frame':((5,-3,1,1,0,F(25,11)),True),
    'negative_denominator_signed_value':((5,3,25,F(-3,5),F(4,5),-25),True),
    'negative_denominator_nonnegative_norm':((5,3,25,F(-3,5),F(4,5),25),False),
    'negative_root_branch':((5,3,1,1,0,F(-25,7)),False),
    'zero_denominator':((5,5,5,-1,0,0),False),
    'negative_radicand':((5,6,10,0,1,0),False),
    'zero_light_speed':((0,3,1,1,0,0),False),
    'negative_magnitude':((5,3,-1,1,0,0),False),
    'invalid_circle':((5,3,0,0,0,3),False),
    'invalid_cut':((128,3,1,1,0,0),False),
}


def model_arithmetic(fixture,model,undefined_value=0):
    fixture.arithmetic(model)
    def reciprocal(value):
        n=fixture.read(value)
        if not n:return fixture.make(undefined_value)
        return fixture.make(1/n)
    def root(value):
        if fixture.read(value)<0:return fixture.make(undefined_value)
        return square_root(fixture,value)
    model.update(sjt=reciprocal,sky=root)


def expression_checks():
    query=''.join('r j'+c+'[] '+CUT+'.' for c in 'abcdef')+'q[k s2t['+' '.join(k('j'+c) for c in 'abcdef')+']].'
    doc=abstract(candidate(composed()[0],query),ARITHMETIC|{'sjt','sky'});rows={}
    for label,(args,expected) in CASES.items():
        # The finite evaluator is eager; operation oracles are totalized outside
        # their domains. Domain conjuncts must reject either arbitrary value.
        for undefined_value in (0,17):
            fixture=ConstructedCuts();model=guarded(doc);model_arithmetic(fixture,model,undefined_value)
            for symbol,value in zip(('j'+c for c in 'abcdef'),args):model[symbol]=lambda value=value:fixture.make(value)
            actual=values(doc,model,('object',))
            if actual!=[expected]:raise ValueError('Root or quotient differs: '+label+repr(actual))
        rows[label]=actual
    return {'cases':rows,'constructed_rational_cuts_with_exact_root_oracles':True,
        'domain_rejection_unchanged_under_two_arbitrary_out_of_domain_oracle_values':True,
        'no_finite_sampling_of_real_cut_universe':True}


def component_checks():
    query=''.join('r j'+c+'[] '+CUT+'.' for c in 'abcde')+'q[k s2u['+' '.join(k('j'+c) for c in 'abcde')+']].'
    doc=abstract(candidate(composed()[0],query),ARITHMETIC);rows={}
    for label,(args,expected) in {
        'positive':((3,4,5,F(3,5),F(4,5)),True),
        'negative_transverse':((3,-4,5,F(3,5),F(4,5)),True),
        'oriented_negative_sine':((3,-4,5,F(3,5),F(-4,5)),True),
        'negative_longitudinal':((-3,4,5,F(-3,5),F(4,5)),True),
        'principal_branch_mismatch':((-3,4,5,F(3,5),F(-4,5)),False),
        'negative_frame_unsigned_mismatch':((3,4,5,F(-3,5),F(4,5)),False),
        'vertical':((0,5,5,0,1),True),'zero_with_arbitrary_circle':((0,0,0,0,1),True),
        'wrong_magnitude':((3,4,6,F(3,5),F(4,5)),False),
        'invalid_circle':((0,0,0,0,0),False),
    }.items():
        fixture=ConstructedCuts();model=guarded(doc);fixture.arithmetic(model)
        for symbol,value in zip(('j'+c for c in 'abcde'),args):model[symbol]=lambda value=value:fixture.make(value)
        actual=values(doc,model,('object',))
        if actual!=[expected]:raise ValueError('Angle component correspondence differs: '+label)
        rows[label]=actual
    return {'cases':rows,'zero_magnitude_algebra_is_not_a_geometric_direction_claim':True}


def source_checks():
    doc=abstract(candidate(composed()[0],'q[t[k s2v[]][k ri[]]].'),ARITHMETIC|{'sjt','sky','syw','szt','szs'})
    angle_type=next(d['result'] for d in doc['declarations'] if d['name']=='zkt');rows={}
    labels=('parallel','vertical','cancellation','negative_denominator_signed_value','negative_denominator_nonnegative_norm',
        'snapshot_denominator','wrong_motion_scope','wrong_moving_magnitude','wrong_rest_magnitude','wrong_context')
    for label in labels:
        args,valid=CASES[label if label in CASES else 'parallel'];V,s,W,c,h,U=args
        fixture=ConstructedCuts();make=fixture.make;n=fixture.read;model=guarded(doc);model_arithmetic(fixture,model)
        model.update(tc=lambda:make(V),zb7=lambda:make(s),zkq=lambda:make(W),zkp=lambda:make(U),ri=lambda:'text',
            zke=lambda:'other' if label=='wrong_context' else 'motion',syw=lambda:label!='wrong_motion_scope',
            szt=lambda value,setting:n(value)==W and setting=='motion' and label!='wrong_moving_magnitude',
            szs=lambda value,setting:n(value)==U and U>=0 and setting=='motion' and label!='wrong_rest_magnitude',
            zkt=lambda:FunctionValue(tuple(angle_type['parameters']),angle_type['result'],lambda choose:make(c if choose else h)))
        actual=values(doc,model,('object',));expected=valid and U>=0 and not label.startswith('wrong_')
        if actual!=[expected]:raise ValueError('Source magnitude binding differs: '+label)
        rows[label]=actual
    return {'cases':rows,'motion_and_derivative_conditions_are_explicit_oracles':True,
        'nonnegative_speed_binding_can_conflict_with_negative_denominator':True}


def attribution_checks():
    doc=parse(composed()[0]);doc['statements']=doc['statements'][-1:];rows={}
    for label in ('baseline','wrong_author','wrong_scope','wrong_context','angle_only_content'):
        model=guarded(doc)
        for symbol,value in {'zkw':'formula','rd':'author','zkf':'scope','ri':'text'}.items():model[symbol]=lambda value=value:value
        def attributed(node,author,body,scope,context):
            return (node,author,scope,context)==('formula','other' if label=='wrong_author' else 'author',
                'other' if label=='wrong_scope' else 'scope','other' if label=='wrong_context' else 'text') and json.loads(body.syntax)['symbol']==('s2m' if label=='angle_only_content' else 's2v')
        model['uh']=attributed;actual=values(doc,model,('formula','author','scope','other'))
        if actual!=[label=='baseline']:raise ValueError('Formula attribution differs')
        rows[label]=actual
    return {'cases':rows,'quoted_formula_not_evaluated_as_truth':True}


def alignment():
    reviewed=reviewed_math()['M0257'];path=ROOT/'artifacts/written-units-v1/einstein-1905.json'
    source=json.loads(path.read_text(encoding='utf-8'));unit=next(u for u in source['units'] if u['id']==reviewed['unit'])
    if hashlib.sha256(unit['text'].encode('utf-8')).hexdigest()!=unit['text_sha256']:raise ValueError('Source formula unit differs')
    return {'segments':[dict(unit=unit['id'],unit_sha256=unit['text_sha256'],start=0,end=len(unit['text']),source=unit['text'],
        definitions=['s2r','s2s','s2t','s2v'],status='partial_explicit_reading',full_semantic_equivalence=False,
        math_id='M0257',math_sha256=reviewed['snapshot_math_sha256'],reviewed_math_sha256=reviewed['reviewed_math_sha256'],
        correction_id=reviewed['correction_id'])],
        'reviewed_layer_explicit':True,'snapshot_modified':False,'verified_full_units':0,
        'facsimile_scope':'M0257 expression visually compared on stored p906 scan; historical angle convention not established',
        'calculation_transition_and_symmetry_appraisal_unwritten':True,'historical_angle_and_domain_conventions_unresolved':True}


def build_report():
    text,basis=composed();doc=parse(text)
    if (ROOT/basis['document']).read_text(encoding='utf-8')!=text:raise ValueError('Stored composition differs')
    if json.loads((ROOT/'data/angle-composition-basis-v1.json').read_text(encoding='utf-8'))!=basis:raise ValueError('Composition basis differs')
    for notation in ('compact','full'):
        form=format_graph(doc,notation)
        if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Composition roundtrip differs')
    paths=[basis['document'],'data/angle-composition-basis-v1.json','examples/v014/einstein-direction-angles.noema',
        'scripts/compose_angle_composition.py','scripts/check_angle_composition.py','scripts/check_written_math_corrections.py',
        'scripts/check_tau_differential.py','scripts/check_transverse_time.py','data/written-math-corrections-v1.json',
        'artifacts/written-facsimiles-v1/einstein-1905-p906.jpg','artifacts/written-units-v1/einstein-1905.json',
        'reports/written-units-v1.json','noema/discourse.py','noema/finite_semantics.py','noema/polynomial_proofs.py']
    return {'status':'partial_reviewed_angle_composition_with_signed_quotient','documents':{basis['document']:audit_basis(doc,basis)},
        'polynomial_lemmas':polynomial_checks(),'expression':expression_checks(),'component_connection':component_checks(),
        'source_bindings':source_checks(),'attribution':attribution_checks(),'alignment':alignment(),
        'roundtrips':True,'verified_full_units':{'einstein-1905':0,'kant-1784':0},
        'notation_size':{'canonical_source_document_characters':len(text),'added_characters':len(text)-len((ROOT/'examples/v014/einstein-direction-angles.noema').read_text(encoding='utf-8'))},
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args();report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Angle composition report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Reviewed angle formula, signs, component connection and source bindings checked')


if __name__=='__main__':main()
