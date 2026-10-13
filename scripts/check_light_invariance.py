"""Check fixed points, nonzero denominators and the reviewed source equation."""
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
from scripts.check_written_math_corrections import reviewed_math
from scripts.compose_light_invariance import ROOT, CUT, composed, k, op, both, v

REPORT=ROOT/'reports/light-invariance-v1.json'


def polynomial_checks():
    V,w,U=map(v,('limit','moving','result'));zero=literal(0)
    add=lambda x,y:k('ab',x,y);lt=lambda x,y:k('aa',x,y);eq=lambda x,y:op('e',x,y)
    domain=both(lt(zero,V),op('u',eq(add(V,w),zero)))
    bounded=both(lt(zero,V),op('u',lt(w,zero)),lt(w,V))
    relation=k('s4c',V,w,U)
    claims={
        'specialized_equation_iff_nonzero_denominator_and_unchanged_value':assertion('limit moving result',op('z',relation,both(domain,eq(U,V)))),
        'nonnegative_subluminal_input_has_positive_denominator':assertion('limit moving',op('y',bounded,lt(zero,add(V,w)))),
        'bounded_input_constructs_unchanged_result':assertion('limit moving',op('y',bounded,k('s4c',V,w,V))),
        'signed_subluminal_input_constructs_unchanged_result':assertion('limit moving',op('y',both(lt(zero,V),lt(k('ac',V),w),lt(w,V)),k('s4c',V,w,V))),
        'exchange_of_inputs_preserves_specialized_equation':assertion('limit moving result',op('z',relation,k('s3f',V,w,V,U))),
        'singular_input_is_rejected':assertion('limit result',op('u',k('s4c',V,k('ac',V),U))),
        'equality_alone_establishes_equation_at_singularity':assertion('',k('s4c',*(literal(x) for x in (5,-5,5)))),
        'equation_alone_implies_subluminal_input':assertion('limit moving result',op('y',relation,bounded)),
        'unchanged_value_without_equation_is_sufficient':assertion('limit moving result',op('y',eq(U,V),relation)),
    }
    rejected={'equality_alone_establishes_equation_at_singularity','equation_alone_implies_subluminal_input','unchanged_value_without_equation_is_sufficient'}
    text=composed()[0];rows={}
    for name,claim in claims.items():
        doc=candidate(text,claim);doc['declarations']=[d for d in doc['declarations'] if d['name'] in {'aa','ab','ac','ad','s3f','s4c'}]
        result=verify_universal(doc,MEANINGS,timeout_ms=20000)[0]
        if result['status']!=('invalid' if name in rejected else 'valid'):raise ValueError('Light algebra differs: '+name+repr(result))
        rows[name]=result
    return {'claims':rows,'rational_polynomial_lemmas_only':True,'all_real_cut_field_laws_proved':False}


def expression_checks():
    query=''.join('r j'+c+'[] '+CUT+'.' for c in 'abc')
    query+='q[k s3s[k ja[] k jb[]]].q[k s4d[k ja[] k jb[] k jc[]]].q[k sca[k jc[] k ja[]]].q[k s4e[k ja[] k jb[]]].'
    doc=abstract(candidate(composed()[0],query),ARITHMETIC|{'sjt','sky'});rows={}
    cases={
        'ordinary':((5,1,5),[True]*4),'zero_input':((5,0,5),[True]*4),
        'near_upper_boundary':((1,F(999,1000),1),[True]*4),
        'wrong_result':((5,1,4),[True,False,False,True]),
        'negative_subluminal':((5,-1,5),[False,True,True,True]),
        'near_singular_boundary':((1,F(-999,1000),1),[False,True,True,True]),
        'at_light_boundary':((5,5,5),[False,True,True,True]),
        'above_light_boundary':((5,6,5),[False,True,True,True]),
        'negative_denominator':((5,-6,5),[False,True,True,True]),
        'singular_input':((5,-5,5),[False,False,True,True]),
        'zero_limit':((0,0,0),[False,False,True,True]),
        'negative_limit':((-5,1,-5),[False,False,True,True]),
        'invalid_cut':((128,1,128),[False,False,True,True]),
    }
    for label,(args,expected) in cases.items():
        for fallback in (0,17):
            fixture=ConstructedCuts();model=guarded(doc);model_arithmetic(fixture,model,fallback)
            for symbol,value in zip(('ja','jb','jc'),args):model[symbol]=lambda value=value:fixture.make(value)
            actual=values(doc,model,('object',))
            if actual!=expected:raise ValueError('Light specialization differs: '+label+repr(actual))
        rows[label]=actual
    universal=abstract(candidate(composed()[0],'q[t[k s4g[]][k ri[]]].'),ARITHMETIC|{'sjt','sky'})
    fixture=ConstructedCuts();model=guarded(universal);model_arithmetic(fixture,model)
    model.update(tc=lambda:fixture.make(5),ri=lambda:'text')
    try:values(universal,model,('object',))
    except SemanticError as error:
        if str(error)!='Cannot finitely quantify the rational number domain':raise
    else:raise ValueError('Universal light claim was finitely enumerated')
    return {'cases':rows,'column_order':['source_input_domain','specialized_equation','result_equals_limit','guarded_claim_instance'],
        'out_of_domain_implication_is_not_a_physical_instance':True,'undefined_reciprocal_fallback_cannot_admit_singularity':True,
        'unbounded_quantification_rejected_by_finite_evaluator':True}


def fixed_point_checks():
    # Use independent operators to check that s4b is not a velocity-specific token.
    x=v('value');three=k('bb',literal(3));zero=k('bb',literal(0))
    queries=''
    for body,point in ((x,three),(k('bd',x,k('bb',literal(1))),three),(k('shv',x,x),zero),(k('shv',x,x),three)):
        queries+='q['+k('s4b','i[value '+CUT+']['+body+']',point)+'].'
    doc=abstract(candidate(composed()[0],queries),ARITHMETIC)
    fixture=ConstructedCuts();model=guarded(doc);fixture.arithmetic(model)
    actual=values(doc,model,('object',))
    if actual!=[True,False,True,False]:raise ValueError('Generic fixed point differs')
    return {'identity_at_three':actual[0],'translation_by_one_at_three':actual[1],'squaring_at_zero':actual[2],'squaring_at_three':actual[3]}


def source_checks():
    doc=abstract(candidate(composed()[0],'q[t[k s4h[]][k ri[]]].'),ARITHMETIC|{'sjt','sky','szs'});rows={}
    for label,args in {'baseline':(5,1,5),'zero_input':(5,0,5),'wrong_result':(5,1,4),
        'different_limit':(6,1,5),'raw_transcription_result':(5,1,F(9,2)),
        'at_light_boundary':(5,5,5),'negative_input':(5,-1,5),'singularity':(5,-5,5),
        'missing_speed_binding':(5,1,5),'wrong_physical_context':(5,1,5)}.items():
        fixture=ConstructedCuts();model=guarded(doc);model_arithmetic(fixture,model)
        for symbol,value in zip(('tc','zkq','zkp'),args):model[symbol]=lambda value=value:fixture.make(value)
        model.update(ri=lambda:'text',zke=lambda:'other' if label=='wrong_physical_context' else 'motion',
            szs=lambda value,context:fixture.read(value)==args[-1] and context=='motion' and label!='missing_speed_binding')
        actual=values(doc,model,('object',))
        if actual!=[label in ('baseline','zero_input')]:raise ValueError('Source light binding differs: '+label)
        rows[label]=actual
    return {'cases':rows,'speed_binding_is_an_explicit_oracle':True,'frame_speed_not_set_to_light_speed':True}


def attribution_checks():
    doc=parse(composed()[0]);doc['statements']=doc['statements'][-2:];rows={}
    for label in ('baseline','wrong_author','wrong_scope','wrong_context','reversed_inference','formula_replaced_by_general_claim'):
        model=guarded(doc)
        for symbol,value in {'zlm':'claim','zln':'formula','rd':'author','zkf':'scope','ri':'text'}.items():model[symbol]=lambda value=value:value
        name=lambda description:json.loads(description.syntax)['symbol']
        def matches(author,scope,context):
            return (author,scope,context)==('other' if label=='wrong_author' else 'author','other' if label=='wrong_scope' else 'scope','other' if label=='wrong_context' else 'text')
        def follows(node,author,before,after,scope,context):
            return node=='claim' and matches(author,scope,context) and (name(before),name(after))==(('s4g','s4i') if label=='reversed_inference' else ('s4i','s4g'))
        def asserts(node,author,content,scope,context):
            return node=='formula' and matches(author,scope,context) and name(content)==('s4g' if label=='formula_replaced_by_general_claim' else 's4h')
        model.update(zc=follows,uh=asserts);actual=values(doc,model,('claim','formula','author','scope','other'))
        expected={'baseline':[True,True],'reversed_inference':[False,True],'formula_replaced_by_general_claim':[True,False]}.get(label,[False,False])
        if actual!=expected:raise ValueError('Light attribution differs: '+label)
        rows[label]=actual
    return {'cases':rows,'quoted_content_not_evaluated_as_global_truth':True}


def alignment():
    reviewed=reviewed_math()['M0273'];path=ROOT/'artifacts/written-units-v1/einstein-1905.json'
    source=json.loads(path.read_text(encoding='utf-8'));rows=[]
    inventory=json.loads((ROOT/'reports/written-units-v1.json').read_text(encoding='utf-8'))
    if hashlib.sha256(path.read_bytes()).hexdigest()!=inventory['works']['einstein-1905']['units_sha256']:raise ValueError('Source inventory differs')
    for index,defs in ((145,['s4b','s4e','s4f','s4g','s4i']),(146,['s4c','s4d','s4h'])):
        unit=next(u for u in source['units'] if u['id']==f'einstein-1905:u{index:04}')
        if hashlib.sha256(unit['text'].encode('utf-8')).hexdigest()!=unit['text_sha256']:raise ValueError('Source text differs')
        common=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],definitions=defs,status='partial_explicit_reading',full_semantic_equivalence=False)
        rows.append(dict(common,start=0,end=len(unit['text']),source=unit['text']))
        for mid in unit['math_ids']:
            item=next(m for m in source['math'] if m['id']==mid)
            row=dict(common,math_id=mid,math_sha256=item['sha256'])
            if mid=='M0273':
                if reviewed['unit']!=unit['id'] or reviewed['snapshot_math_sha256']!=item['sha256']:raise ValueError('Correction target differs')
                row.update(correction_id=reviewed['correction_id'],reviewed_math_sha256=reviewed['reviewed_math_sha256'])
            rows.append(row)
    return {'segments':rows,'reviewed_layer_explicit':True,'snapshot_modified':False,'verified_full_units':0,
        'nonnegative_same_axis_reading_explicit':True,'following_transformation_composition_unwritten':True}


def build_report():
    text,basis=composed();doc=parse(text)
    if (ROOT/basis['document']).read_text(encoding='utf-8')!=text or json.loads((ROOT/'data/light-invariance-basis-v1.json').read_text(encoding='utf-8'))!=basis:raise ValueError('Stored light artifacts differ')
    for notation in ('compact','full'):
        form=format_graph(doc,notation)
        if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Light roundtrip differs')
    paths=[basis['document'],'data/light-invariance-basis-v1.json','examples/v014/einstein-speed-deficits.noema',
        'scripts/compose_light_invariance.py','scripts/check_light_invariance.py','scripts/check_angle_composition.py',
        'scripts/check_written_math_corrections.py','data/written-math-corrections-v1.json',
        'scripts/check_tau_differential.py','scripts/check_transverse_time.py','noema/discourse.py','noema/finite_semantics.py',
        'noema/polynomial_proofs.py','artifacts/written-units-v1/einstein-1905.json','reports/written-units-v1.json',
        'artifacts/written-facsimiles-v1/einstein-1905-p906.jpg']
    return {'status':'partial_reviewed_light_speed_invariance','documents':{basis['document']:audit_basis(doc,basis)},
        'polynomial_lemmas':polynomial_checks(),'expression':expression_checks(),'fixed_points':fixed_point_checks(),
        'source_bindings':source_checks(),'attribution':attribution_checks(),'alignment':alignment(),
        'roundtrips':True,'verified_full_units':{'einstein-1905':0,'kant-1784':0},
        'notation_size':{'canonical_source_document_characters':len(text),'added_characters':len(text)-len((ROOT/'examples/v014/einstein-speed-deficits.noema').read_text(encoding='utf-8'))},
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args();report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Light invariance report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Fixed points, specialized quotient, source correction and attribution checked')


if __name__=='__main__':main()
