"""Check scalar composition, direction conventions and source condition scope."""
import argparse
from fractions import Fraction as F
import hashlib
import json

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
from scripts.check_angle_composition import model_arithmetic
from scripts.compose_axial_composition import ROOT, CUT, composed, k, op, both, v

REPORT=ROOT/'reports/axial-composition-v1.json'


def polynomial_checks():
    V,s,w,U,Z,b,Y=map(v,('light','speed','moving','result','other','beta','transverse'))
    zero=literal(0);one=literal(1);mul=lambda a,b:k('ad',a,b);add=lambda a,b:k('ab',a,b)
    lt=lambda a,b:k('aa',a,b);sq=lambda a:mul(a,a);eq=lambda a,b:op('e',a,b)
    relation=k('s3f',V,s,w,U);D=add(sq(V),mul(s,w))
    sublight=both(lt(zero,V),lt(sq(s),sq(V)),lt(sq(w),sq(V)))
    claims={
        'axial_components_give_scalar_formula':assertion('light speed moving beta result transverse',
            op('y',k('szl',V,s,b,w,zero,U,Y),both(relation,eq(Y,zero)))),
        'nonnegative_parallel_angle_matches_scalar_formula':assertion('light speed moving result',
            op('y',both(lt(zero,V),op('u',lt(s,zero)),op('u',lt(w,zero))),
                op('z',relation,k('s2o',V,s,w,one,zero,add(s,w),U)))),
        'signed_inputs_commute':assertion('light speed moving result',op('z',relation,k('s3f',V,w,s,U))),
        'result_is_unique':assertion('light speed moving result other',op('y',both(relation,k('s3f',V,s,w,Z)),eq(U,Z))),
        'zero_is_identity':assertion('light speed',op('y',lt(zero,V),k('s3f',V,s,zero,s))),
        'opposite_subluminal_inputs_cancel':assertion('light speed',op('y',both(lt(zero,V),lt(sq(s),sq(V))),k('s3f',V,s,k('ac',s),zero))),
        'signed_subluminal_denominator_positive':assertion('light speed moving',op('y',sublight,lt(zero,D))),
        'signed_subluminal_result_stays_subluminal':assertion('light speed moving result',op('y',both(sublight,relation),lt(sq(U),sq(V)))),
        'nonnegative_inputs_produce_nonnegative_result':assertion('light speed moving result',
            op('y',both(relation,op('u',lt(s,zero)),op('u',lt(w,zero))),op('u',lt(U,zero)))),
        'opposite_direction_signed_value':assertion('',k('s3f',*(literal(n) for n in (5,1,-3,F(-25,11))))),
        'axis_support_alone_allows_using_magnitude_as_component':assertion('',k('s3f',*(literal(n) for n in (5,1,3,F(-25,11))))),
        'zero_denominator_has_a_value':assertion('',k('s3f',*(literal(n) for n in (5,3,F(-25,3),0)))),
        'unrestricted_inputs_always_stay_below_light':assertion('',op('y',k('s3f',*(literal(n) for n in (5,6,1,F(175,31)))),lt(literal(F(175,31)),literal(5)))),
    }
    rows={};text=composed()[0]
    rejected={'axis_support_alone_allows_using_magnitude_as_component','zero_denominator_has_a_value','unrestricted_inputs_always_stay_below_light'}
    for name,claim in claims.items():
        doc=candidate(text,claim)
        doc['declarations']=[d for d in doc['declarations'] if d['name'] in {'aa','ab','ac','ad','sra','syq','szl','szw','s2n','s2o','s3f'}]
        result=verify_universal(doc,MEANINGS,timeout_ms=20000)[0]
        if result['status']!=('invalid' if name in rejected else 'valid'):raise ValueError('Axial algebra differs: '+name+repr(result))
        rows[name]=result
    return {'claims':rows,'rational_polynomial_lemmas_only':True,'real_cut_field_and_root_laws_proved':False,
        'subluminal_lemma_is_not_yet_alignment_to_following_prose':True}


def expression_checks():
    query=''.join('r j'+c+'[] '+CUT+'.' for c in 'abcd')+'q[k s3g[k ja[] k jb[] k jc[] k jd[]]].'
    doc=abstract(candidate(composed()[0],query),ARITHMETIC|{'sjt','sky'});rows={}
    cases={
        'forward':((5,3,1,F(25,7)),True),'opposed':((5,3,-1,F(25,11)),True),
        'negative_result':((5,1,-3,F(-25,11)),True),'magnitude_substituted':((5,1,-3,F(25,11)),False),
        'both_negative':((5,-3,-1,F(-25,7)),True),'cancellation':((5,3,-3,0),True),
        'zero_frame':((5,0,3,3),True),'zero_point':((5,3,0,3),True),'both_zero':((5,0,0,0),True),
        'negative_denominator':((5,3,-25,11),True),'zero_denominator':((5,3,F(-25,3),0),False),
        'light_boundary':((5,5,1,5),True),'outside_boost_domain':((5,6,1,F(175,31)),True),
        'zero_light':((0,3,1,4),False),'negative_light':((-5,3,1,F(25,7)),False),
        'invalid_cut':((128,0,0,0),False),'ordinary_sum':((5,3,1,4),False),
    }
    for name,(args,expected) in cases.items():
        for undefined_value in (0,17):
            fixture=ConstructedCuts();model=guarded(doc);model_arithmetic(fixture,model,undefined_value)
            for symbol,value in zip(('ja','jb','jc','jd'),args):model[symbol]=lambda value=value:fixture.make(value)
            actual=values(doc,model,('object',))
            if actual!=[expected]:raise ValueError('Signed scalar expression differs: '+name+repr(actual))
        rows[name]=actual
    return {'cases':rows,'constructed_rational_cut_oracles':True,
        'out_of_domain_reciprocal_values_do_not_bypass_guard':True,'expression_domain_separate_from_physical_boost_domain':True}


def direction_checks():
    query=''.join('r j'+c+'[] '+CUT+'.' for c in 'abc')+'q[k s3h[k ja[] k jb[]]].q[k s3i[k ja[] k jb[] k jc[]]].'
    doc=abstract(candidate(composed()[0],query),ARITHMETIC);rows={}
    for label,(args,expected) in {
        'forward':((3,0,3),[True,True]),'backward':((-3,0,3),[True,False]),
        'zero':((0,0,0),[True,False]),'transverse':((0,3,3),[False,False]),
        'oblique':((3,4,5),[False,False]),'wrong_magnitude':((3,0,4),[True,False]),
        'negative_magnitude':((3,0,-3),[True,False]),'invalid_cut':((128,0,128),[False,False]),
    }.items():
        fixture=ConstructedCuts();model=guarded(doc);fixture.arithmetic(model)
        for symbol,value in zip(('ja','jb','jc'),args):model[symbol]=lambda value=value:fixture.make(value)
        actual=values(doc,model,('object',))
        if actual!=expected:raise ValueError('Axis or positive direction differs: '+label)
        rows[label]=actual
    return {'cases':rows,'zero_vector_has_axial_support_but_no_positive_direction':True}


def source_checks():
    doc=abstract(candidate(composed()[0],'q[t[k s3k[]][k ri[]]].q[t[k s3l[]][k ri[]]].q[t[k s3m[]][k ri[]]].'),
        ARITHMETIC|{'sjt','sky','syw','szt','szs'});rows={}
    cases={
        # v, moving x, moving y, w, U; premise, conclusion, implication
        'forward':((3,1,0,1,F(25,7)),[True,True,True]),
        'backward_point':((3,-1,0,1,F(25,11)),[False,False,True]),
        'negative_frame':((-3,1,0,1,F(25,11)),[False,False,True]),
        'signed_negative_result':((-3,1,0,1,F(-25,11)),[False,False,True]),
        'zero_frame':((0,1,0,1,1),[False,True,True]),
        'zero_point':((3,0,0,0,3),[False,True,True]),
        'oblique_light':((3,3,4,5,5),[False,True,True]),
        'wrong_result':((3,1,0,1,4),[True,False,False]),
        'wrong_moving_magnitude':((3,1,0,2,F(25,7)),[False,False,True]),
        'wrong_motion':((3,1,0,1,F(25,7)),[False,True,True]),
        'wrong_context':((3,1,0,1,F(25,7)),[False,False,True]),
        'missing_rest_derivative':((3,1,0,1,F(25,7)),[True,False,False]),
    }
    for label,(args,expected) in cases.items():
        speed,x,y,w,result=args;fixture=ConstructedCuts();make=fixture.make;n=fixture.read;model=guarded(doc);model_arithmetic(fixture,model)
        model.update(tc=lambda:make(5),zb7=lambda:make(speed),zkc=lambda:make(x),zkd=lambda:make(y),zkq=lambda:make(w),
            zkp=lambda:make(result),ri=lambda:'text',zke=lambda:'other' if label=='wrong_context' else 'motion',
            syw=lambda:label!='wrong_motion',szt=lambda value,context:n(value)==w and context=='motion',
            szs=lambda value,context:n(value)==result and result>=0 and context=='motion' and label!='missing_rest_derivative')
        actual=values(doc,model,('object',))
        if actual!=expected:raise ValueError('Source conditional binding differs: '+label+repr(actual))
        rows[label]=actual
    return {'cases':rows,'motion_and_derivative_oracles_are_explicit':True,
        'conditional_truth_not_confused_with_actual_premise_or_conclusion':True}


def attribution_checks():
    doc=parse(composed()[0]);doc['statements']=doc['statements'][-1:];rows={}
    for label in ('baseline','wrong_author','wrong_scope','wrong_context','reversed','general_angle_formula'):
        model=guarded(doc)
        for symbol,value in {'zlf':'axial','rd':'author','zkf':'scope','ri':'text'}.items():model[symbol]=lambda value=value:value
        def follows(node,author,before,after,scope,context):
            pair=(json.loads(before.syntax)['symbol'],json.loads(after.syntax)['symbol'])
            target=('s3l','s3k') if label=='reversed' else ('s3k','s2v') if label=='general_angle_formula' else ('s3k','s3l')
            return (node,author,scope,context)==('axial','other' if label=='wrong_author' else 'author',
                'other' if label=='wrong_scope' else 'scope','other' if label=='wrong_context' else 'text') and pair==target
        model['zc']=follows;actual=values(doc,model,('axial','author','scope','other'))
        if actual!=[label=='baseline']:raise ValueError('Axial conclusion attribution differs')
        rows[label]=actual
    return {'cases':rows,'quoted_direction_and_formula_contents_not_evaluated':True}


def alignment():
    path=ROOT/'artifacts/written-units-v1/einstein-1905.json';source=json.loads(path.read_text(encoding='utf-8'))
    inventory=json.loads((ROOT/'reports/written-units-v1.json').read_text(encoding='utf-8'))
    if hashlib.sha256(path.read_bytes()).hexdigest()!=inventory['works']['einstein-1905']['units_sha256']:raise ValueError('Axial source inventory differs')
    rows=[]
    for index,mids,defs in ((141,('M0260','M0261','M0262'),['s3h','s3i','s3k']),(142,('M0263',),['s3g','s3j','s3l'])):
        unit=next(u for u in source['units'] if u['id']==f'einstein-1905:u{index:04}')
        if hashlib.sha256(unit['text'].encode('utf-8')).hexdigest()!=unit['text_sha256']:raise ValueError('Axial source text differs')
        start=unit['text'].index('Hat auch') if index==141 else 0
        common=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],definitions=defs,status='partial_explicit_reading',full_semantic_equivalence=False)
        rows.append(dict(common,start=start,end=len(unit['text']),source=unit['text'][start:]))
        for mid in mids:
            item=next(m for m in source['math'] if m['id']==mid)
            if hashlib.sha256(item['mathml'].encode('utf-8')).hexdigest()!=item['sha256']:raise ValueError('Axial math differs')
            rows.append(dict(common,math_id=mid,math_sha256=item['sha256']))
    return {'segments':rows,'verified_full_units':0,'positive_direction_is_an_explicit_reading':True,
        'historical_sign_convention_unresolved':True,'following_subluminal_prose_and_deficit_argument_unwritten':True,
        'facsimile_scope':'M0263 and the immediately preceding axial-direction clause compared on stored p906 scan; no whole-page semantic verification'}


def build_report():
    text,basis=composed();doc=parse(text)
    if (ROOT/basis['document']).read_text(encoding='utf-8')!=text or json.loads((ROOT/'data/axial-composition-basis-v1.json').read_text(encoding='utf-8'))!=basis:raise ValueError('Stored axial artifacts differ')
    for notation in ('compact','full'):
        form=format_graph(doc,notation)
        if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Axial roundtrip differs')
    paths=[basis['document'],'data/axial-composition-basis-v1.json','examples/v014/einstein-calculation-discourse.noema',
        'scripts/compose_axial_composition.py','scripts/check_axial_composition.py','scripts/check_angle_composition.py',
        'scripts/check_tau_differential.py','scripts/check_transverse_time.py','noema/discourse.py','noema/finite_semantics.py',
        'noema/polynomial_proofs.py','artifacts/written-units-v1/einstein-1905.json','reports/written-units-v1.json',
        'artifacts/written-facsimiles-v1/einstein-1905-p906.jpg']
    return {'status':'partial_axial_composition_with_explicit_direction_and_signed_result','documents':{basis['document']:audit_basis(doc,basis)},
        'polynomial_lemmas':polynomial_checks(),'expression':expression_checks(),'directions':direction_checks(),
        'source_bindings':source_checks(),'attribution':attribution_checks(),'alignment':alignment(),
        'roundtrips':True,'verified_full_units':{'einstein-1905':0,'kant-1784':0},
        'notation_size':{'canonical_source_document_characters':len(text),'added_characters':len(text)-len((ROOT/'examples/v014/einstein-calculation-discourse.noema').read_text(encoding='utf-8'))},
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args();report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Axial composition report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Axial composition, signed bounds, direction conditions and source attribution checked')


if __name__=='__main__':main()
