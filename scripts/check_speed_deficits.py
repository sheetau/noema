"""Check strict deficit bounds, substitution identity and quantified claim scope."""
import argparse
from fractions import Fraction as F
import hashlib
import json

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.polynomial_proofs import verify_universal
from noema.script import encode, decode
from noema.semantics import SemanticError
from scripts.check_comoving_labels import values
from scripts.check_coordinate_correspondence import abstract
from scripts.check_described_appraisals import candidate
from scripts.check_rod_setup import guarded
from scripts.check_real_products import MEANINGS, assertion
from scripts.check_moving_light_trip import literal
from scripts.check_tau_differential import ARITHMETIC, ConstructedCuts
from scripts.check_angle_composition import model_arithmetic
from scripts.compose_speed_deficits import ROOT, CUT, composed, k, op, both, v

REPORT=ROOT/'reports/speed-deficits-v1.json'


def polynomial_checks():
    V,a,g,h,U,G=map(v,('limit','amount','gap','othergap','result','another'))
    zero=literal(0);mul=lambda x,y:k('ad',x,y);add=lambda x,y:k('ab',x,y)
    sub=lambda x,y:add(x,k('ac',y));lt=lambda x,y:k('aa',x,y);eq=lambda x,y:op('e',x,y)
    gap=k('s3n',V,a,g);domain=both(k('s3n',V,sub(V,g),g),k('s3n',V,sub(V,h),h))
    A=sub(sub(add(V,V),g),h);D=add(mul(V,A),mul(g,h));relation=k('s3p',V,g,h,U)
    claims={
        'strict_shortfall_implies_positive_amount_below_limit':assertion('limit amount gap',op('y',gap,both(lt(zero,a),lt(a,V)))),
        'positive_amount_has_the_strict_shortfall':assertion('limit amount',op('z',k('s3n',V,a,sub(V,a)),both(lt(zero,a),lt(a,V)))),
        'shortfall_is_unique':assertion('limit amount gap another',op('y',both(gap,k('s3n',V,a,G)),eq(g,G))),
        'substitution_preserves_original_quotient':assertion('limit gap othergap result',
            op('y',domain,op('z',relation,k('s3f',V,sub(V,g),sub(V,h),U)))),
        'strict_deficits_make_numerator_and_denominator_positive':assertion('limit gap othergap',op('y',domain,both(lt(zero,A),lt(zero,D)))),
        'result_strictly_between_zero_and_limit':assertion('limit gap othergap result',op('y',relation,both(lt(zero,U),lt(U,V)))),
        'remaining_gap_identity':assertion('limit gap othergap result',op('y',relation,eq(mul(D,sub(V,U)),mul(V,mul(g,h))))),
        'interchanging_deficits_preserves_result':assertion('limit gap othergap result',op('z',relation,k('s3p',V,h,g,U))),
        'zero_deficit_is_admitted':assertion('',k('s3p',*(literal(n) for n in (5,0,4,5)))),
        'deficit_equal_to_limit_is_admitted':assertion('',k('s3p',*(literal(n) for n in (5,5,4,1)))),
        'strict_inequality_alone_establishes_equation':assertion('',op('y',lt(literal(1),literal(5)),k('s3p',*(literal(n) for n in (5,2,4,1))))),
        'zero_input_boundary_has_a_composition':assertion('',k('s3f',*(literal(n) for n in (5,0,1,1)))),
    }
    rejected={'zero_deficit_is_admitted','deficit_equal_to_limit_is_admitted','strict_inequality_alone_establishes_equation'}
    text=composed()[0];rows={}
    for name,claim in claims.items():
        doc=candidate(text,claim);doc['declarations']=[d for d in doc['declarations'] if d['name'] in {'aa','ab','ac','ad','s3f','s3n','s3p'}]
        result=verify_universal(doc,MEANINGS,timeout_ms=20000)[0]
        if result['status']!=('invalid' if name in rejected else 'valid'):raise ValueError('Deficit algebra differs: '+name+repr(result))
        rows[name]=result
    return {'claims':rows,'rational_polynomial_lemmas_only':True,'all_real_cut_order_and_field_laws_proved':False}


def shortfall_checks():
    query=''.join('r j'+c+'[] '+CUT+'.' for c in 'abc')+'q[k s3o[k ja[] k jb[] k jc[]]].q[k s3s[k ja[] k jb[]]].'
    doc=abstract(candidate(composed()[0],query),ARITHMETIC);rows={}
    for label,(args,expected) in {
        'ordinary':((5,3,2),[True,True]),'zero_amount':((5,0,5),[False,True]),
        'at_limit':((5,5,0),[False,False]),'negative_amount':((5,-1,6),[False,False]),
        'negative_gap':((5,6,-1),[False,False]),'wrong_gap':((5,3,1),[False,True]),
        'near_limit':((1,F(99,100),F(1,100)),[True,True]),'zero_limit':((0,0,0),[False,False]),
        'invalid_cut':((128,3,125),[False,False]),
    }.items():
        fixture=ConstructedCuts();model=guarded(doc);fixture.arithmetic(model)
        for symbol,value in zip(('ja','jb','jc'),args):model[symbol]=lambda value=value:fixture.make(value)
        actual=values(doc,model,('object',))
        if actual!=expected:raise ValueError('Strict shortfall differs: '+label)
        rows[label]=actual
    return {'cases':rows,'strict_deficit_domain_excludes_zero_amount_boundary':True}


def quotient_checks():
    query=''.join('r j'+c+'[] '+CUT+'.' for c in 'abcd')
    query+='q[k s3r[k ja[] k jb[] k jc[] k jd[]]].q[k bg[k jd[] k ja[]]].'
    doc=abstract(candidate(composed()[0],query),ARITHMETIC|{'sjt','sky'});rows={}
    for label,(args,expected) in {
        'baseline':((5,2,4,F(25,7)),[True,True]),'exchanged':((5,4,2,F(25,7)),[True,True]),
        'small_deficits':((5,1,1,F(200,41)),[True,True]),
        'very_near_limit':((1,F(1,100),F(1,100),F(19800,19801)),[True,True]),
        'wrong_value_below_limit':((5,2,4,1),[False,True]),'wrong_value_at_limit':((5,2,4,5),[False,False]),
        'zero_deficit':((5,0,4,5),[False,False]),'limit_deficit':((5,5,4,1),[False,True]),
        'both_limit_deficits':((5,5,5,0),[False,True]),'negative_deficit':((5,-1,4,F(175,31)),[False,False]),
        'zero_limit':((0,0,0,0),[False,False]),'negative_limit':((-5,2,4,0),[False,False]),
    }.items():
        for undefined_value in (0,17):
            fixture=ConstructedCuts();model=guarded(doc);model_arithmetic(fixture,model,undefined_value)
            for symbol,value in zip(('ja','jb','jc','jd'),args):model[symbol]=lambda value=value:fixture.make(value)
            actual=values(doc,model,('object',))
            if actual!=expected:raise ValueError('Substituted quotient differs: '+label+repr(actual))
        rows[label]=actual
    return {'cases':rows,'retained_rational_cuts_and_exact_fraction_arithmetic':True,
        'strict_bound_does_not_replace_equation':True,'out_of_domain_reciprocal_values_do_not_bypass_guard':True}


def bounded_claim_checks():
    query=''.join('r j'+c+'[] '+CUT+'.' for c in 'abc')+'q[k s3t[k ja[] k jb[] k jc[]]].q[k s3u[k ja[] k jb[] k jc[]]].'
    doc=abstract(candidate(composed()[0],query),ARITHMETIC|{'sjt','sky'});rows={}
    cases={'ordinary':(5,3,1),'zero_first':(5,0,1),'zero_second':(5,1,0),'both_zero':(5,0,0),
        'near_boundary':(1,F(99,100),F(99,100)),'at_boundary':(5,5,1),'above_boundary':(5,6,1),
        'negative_input':(5,-1,3),'zero_limit':(0,0,0),'invalid_cut':(128,1,1)}
    for label,args in cases.items():
        fixture=ConstructedCuts();model=guarded(doc);model_arithmetic(fixture,model)
        for symbol,value in zip(('ja','jb','jc'),args):model[symbol]=lambda value=value:fixture.make(value)
        valid=label in ('ordinary','zero_first','zero_second','both_zero','near_boundary')
        actual=values(doc,model,('object',))
        if actual!=[valid,True]:raise ValueError('Bounded claim instance differs: '+label)
        rows[label]=actual
    universal=abstract(candidate(composed()[0],'q[t[k s3w[]][k ri[]]].'),ARITHMETIC|{'sjt','sky'})
    model=guarded(universal);model_arithmetic(fixture,model);model.update(tc=lambda:fixture.make(5),ri=lambda:'text')
    try:values(universal,model,('object',))
    except SemanticError as error:
        if str(error)!='Cannot finitely quantify the rational number domain':raise
    else:raise ValueError('Universal real speed claim was finitely enumerated')
    return {'instances':rows,'computed_result_is_required_to_be_a_valid_composition':True,
        'full_real_quantification_not_replaced_by_samples':True,'unbounded_quantification_rejected_by_finite_evaluator':True}


def source_checks():
    query='q[t[k s3x[]][k ri[]]].q[t[k s3z[]][k ri[]]].q[t[k s3y[]][k ri[]]].'
    doc=abstract(candidate(composed()[0],query),ARITHMETIC|{'sjt','sky','szs'});rows={}
    cases={
        # limit, v, w, kappa, lambda, U
        'baseline':((5,3,1,2,4,F(25,7)),[True]*3),
        'swapped_deficit_references':((5,3,1,4,2,F(25,7)),[False,False,True]),
        'mismatched_moving_value':((5,3,2,2,4,F(25,7)),[False,False,True]),
        'wrong_result':((5,3,1,2,4,1),[True,False,False]),
        'zero_velocity_boundary':((5,0,1,5,4,1),[False]*3),
        'light_velocity_boundary':((5,5,1,0,4,5),[False]*3),
        'negative_deficit':((5,6,1,-1,4,F(175,31)),[False]*3),
        'different_limit':((6,3,1,2,4,F(25,7)),[False]*3),
        'missing_rest_derivative':((5,3,1,2,4,F(25,7)),[True,False,True]),
        'wrong_physical_context':((5,3,1,2,4,F(25,7)),[True,False,True]),
    }
    for label,(args,expected) in cases.items():
        fixture=ConstructedCuts();make=fixture.make;n=fixture.read;model=guarded(doc);model_arithmetic(fixture,model)
        for symbol,value in zip(('tc','zb7','zkq','zlg','zlh','zkp'),args):model[symbol]=lambda value=value:make(value)
        model.update(ri=lambda:'text',zke=lambda:'other' if label=='wrong_physical_context' else 'motion',
            szs=lambda value,context:n(value)==args[-1] and args[-1]>=0 and context=='motion' and label!='missing_rest_derivative')
        actual=values(doc,model,('object',))
        if actual!=expected:raise ValueError('Source deficit bindings differ: '+label+repr(actual))
        rows[label]=actual
    return {'cases':rows,'derivative_binding_is_an_explicit_oracle':True,
        'same_references_required_for_substitution_and_previous_equation':True}


def attribution_checks():
    doc=parse(composed()[0]);doc['statements']=doc['statements'][-4:];rows={}
    for label in ('baseline','wrong_author','wrong_context','wrong_global_scope','wrong_local_scope',
        'reversed_general_inference','substitution_replaced_by_conclusion','proof_target_replaced'):
        model=guarded(doc)
        for symbol,value in {'zli':'claim','zlj':'substitution','zlk':'local','zll':'argument','rd':'author','zkf':'global','ri':'text'}.items():model[symbol]=lambda value=value:value
        symbol=lambda description:json.loads(description.syntax)['symbol']
        def context_matches(author,context):return (author,context)==('other' if label=='wrong_author' else 'author','other' if label=='wrong_context' else 'text')
        def scope_matches(scope,expected):return scope==('other' if label=='wrong_'+expected+'_scope' else expected)
        def follows(node,author,before,after,scope,context):
            target=('s3w','s4a') if label=='reversed_general_inference' else ('s4a','s3w')
            if node=='argument':target=('s3z','s3y')
            return context_matches(author,context) and scope_matches(scope,'global' if node=='claim' else 'local') and (symbol(before),symbol(after))==target
        def assumes(node,author,content,scope,context):
            return node=='substitution' and context_matches(author,context) and scope_matches(scope,'local') and symbol(content)==('s3y' if label=='substitution_replaced_by_conclusion' else 's3x')
        def presented(proof,author,content,stage,scope):
            return proof=='argument' and context_matches(author,stage) and scope_matches(scope,'global') and symbol(content)==('s3y' if label=='proof_target_replaced' else 's3w')
        model.update(zc=follows,ug=assumes,zfr=presented);actual=values(doc,model,('claim','substitution','argument','author','local','global','other'))
        expected={'baseline':[True]*4,'wrong_author':[False]*4,'wrong_context':[False]*4,
            'wrong_global_scope':[False,True,True,False],'wrong_local_scope':[True,False,False,True],
            'reversed_general_inference':[False,True,True,True],'substitution_replaced_by_conclusion':[True,False,True,True],
            'proof_target_replaced':[True,True,True,False]}[label]
        if actual!=expected:raise ValueError('Deficit argument attribution differs: '+label+repr(actual))
        rows[label]=actual
    return {'cases':rows,'quoted_claim_substitution_and_argument_not_evaluated':True,
        'presentation_as_proof_does_not_certify_validity':True}


def alignment():
    path=ROOT/'artifacts/written-units-v1/einstein-1905.json';source=json.loads(path.read_text(encoding='utf-8'))
    inventory=json.loads((ROOT/'reports/written-units-v1.json').read_text(encoding='utf-8'))
    if hashlib.sha256(path.read_bytes()).hexdigest()!=inventory['works']['einstein-1905']['units_sha256']:raise ValueError('Deficit source inventory differs')
    rows=[]
    for index,defs in ((143,['s3o','s3v','s3w','s3x','s4a']),(144,['s3q','s3r','s3y','s3z'])):
        unit=next(u for u in source['units'] if u['id']==f'einstein-1905:u{index:04}')
        if hashlib.sha256(unit['text'].encode('utf-8')).hexdigest()!=unit['text_sha256']:raise ValueError('Deficit source text differs')
        common=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],definitions=defs,status='partial_explicit_reading',full_semantic_equivalence=False)
        rows.append(dict(common,start=0,end=len(unit['text']),source=unit['text']))
        for mid in unit['math_ids']:
            item=next(m for m in source['math'] if m['id']==mid)
            if hashlib.sha256(item['mathml'].encode('utf-8')).hexdigest()!=item['sha256']:raise ValueError('Deficit source math differs')
            rows.append(dict(common,math_id=mid,math_sha256=item['sha256']))
    return {'segments':rows,'verified_full_units':0,'zero_velocity_boundary_not_silently_added_to_strict_deficit_argument':True,
        'nonnegative_same_axis_reading_explicit':True,'following_light_speed_invariance_unwritten':True,
        'facsimile_scope':'u0143 condition and M0271 compared on stored p906 scan; no whole-page semantic verification'}


def build_report():
    text,basis=composed();doc=parse(text)
    if (ROOT/basis['document']).read_text(encoding='utf-8')!=text or json.loads((ROOT/'data/speed-deficits-basis-v1.json').read_text(encoding='utf-8'))!=basis:raise ValueError('Stored deficits artifacts differ')
    for notation in ('compact','full'):
        form=format_graph(doc,notation)
        if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Deficit roundtrip differs')
    paths=[basis['document'],'data/speed-deficits-basis-v1.json','examples/v014/einstein-axial-composition.noema',
        'scripts/compose_speed_deficits.py','scripts/check_speed_deficits.py','scripts/check_angle_composition.py',
        'scripts/check_tau_differential.py','scripts/check_transverse_time.py','noema/discourse.py','noema/finite_semantics.py',
        'noema/polynomial_proofs.py','artifacts/written-units-v1/einstein-1905.json','reports/written-units-v1.json',
        'artifacts/written-facsimiles-v1/einstein-1905-p906.jpg']
    return {'status':'partial_strict_deficit_argument_and_quantified_subluminal_bound','documents':{basis['document']:audit_basis(doc,basis)},
        'polynomial_lemmas':polynomial_checks(),'shortfalls':shortfall_checks(),'quotient':quotient_checks(),
        'bounded_claim':bounded_claim_checks(),'source_bindings':source_checks(),'attribution':attribution_checks(),'alignment':alignment(),
        'roundtrips':True,'verified_full_units':{'einstein-1905':0,'kant-1784':0},
        'notation_size':{'canonical_source_document_characters':len(text),'added_characters':len(text)-len((ROOT/'examples/v014/einstein-axial-composition.noema').read_text(encoding='utf-8'))},
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args();report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Speed deficit report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Strict deficits, substituted quotient, quantified bounds and argument scope checked')


if __name__=='__main__':main()
