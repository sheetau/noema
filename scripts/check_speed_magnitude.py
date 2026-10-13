"""Check nonnegative norms, transformed magnitudes and shared derivatives."""
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
from scripts.compose_speed_magnitude import ROOT, CUT, composed, k, op, both, v

REPORT=ROOT/'reports/speed-magnitude-v1.json'


def polynomial_checks():
    V,s,b,u,w,X,Y,W,U=map(v,('light','speed','beta','longitudinal','transverse','outx','outy','movingmag','resultmag'))
    zero=literal(0);names='light speed beta longitudinal transverse outx outy movingmag resultmag'
    before=k('szk',W,u,w);after=k('szk',U,X,Y);components=k('szl',V,s,b,u,w,X,Y)
    claims={
        'components_determine_magnitude_relation':assertion(names,op('y',both(components,before,after),k('szm',V,s,u,w,W,U))),
        'nonnegative_magnitude_unique':assertion('movingmag resultmag longitudinal transverse',op('y',both(before,k('szk',U,u,w)),op('e',W,U))),
        'zero_magnitude_iff_zero_components':assertion('longitudinal transverse',op('z',k('szk',zero,u,w),both(op('e',u,zero),op('e',w,zero)))),
        'reversing_components_preserves_magnitude':assertion('movingmag longitudinal transverse',op('z',before,k('szk',W,k('ac',u),k('ac',w)))),
        'negative_magnitude_branch_is_admissible':assertion('',k('szk',literal(-5),literal(3),literal(4))),
        'sum_of_components_is_magnitude':assertion('',k('szk',literal(7),literal(3),literal(4))),
        'opposing_velocities_can_give_zero_magnitude':assertion('',k('szm',*(literal(n) for n in (5,3,-3,0,3,0)))),
        'negative_denominator_does_not_make_magnitude_negative':assertion('',k('szm',*(literal(n) for n in (5,3,-15,20,25,25)))),
    }
    text=composed()[0];rows={}
    for name,claim in claims.items():
        doc=candidate(text,claim)
        doc['declarations']=[d for d in doc['declarations'] if d['name'] in {'aa','ab','ac','ad','sra','syq','szk','szl','szm'}]
        result=verify_universal(doc,MEANINGS,timeout_ms=20000)[0]
        expected='invalid' if name in ('negative_magnitude_branch_is_admissible','sum_of_components_is_magnitude') else 'valid'
        if result['status']!=expected:raise ValueError('Magnitude algebra differs: '+name+repr(result))
        rows[name]=result
    return {'claims':rows,'rational_polynomial_lemmas_only':True,'real_cut_field_and_derivative_theorems_proved':False}


def norm_checks():
    query=''.join('r j'+c+'[] '+CUT+'.' for c in 'abc')+'q[k szn[k ja[] k jb[] k jc[]]].'
    doc=abstract(candidate(composed()[0],query),ARITHMETIC);rows={}
    for label,(args,expected) in {
        'positive':((5,3,4),True),'negative_components':((5,-3,-4),True),'mixed_sign':((5,-3,4),True),
        'zero':((0,0,0),True),'negative_branch':((-5,3,4),False),'sum':((7,3,4),False),
        'one_zero_component':((3,-3,0),True),'zero_with_motion':((0,3,0),False),'invalid_cut':((128,0,0),False),
    }.items():
        fixture=ConstructedCuts();model=guarded(doc);fixture.arithmetic(model)
        for symbol,value in zip(('ja','jb','jc'),args):model[symbol]=lambda value=value:fixture.make(value)
        actual=values(doc,model,('object',))
        if actual!=[expected]:raise ValueError('Norm differs: '+label)
        rows[label]=actual
    query=''.join('r j'+c+'[] '+CUT+'.' for c in 'abcdef')+'q[k szp['+' '.join(k('j'+c) for c in 'abcdef')+']].'
    doc=abstract(candidate(composed()[0],query),ARITHMETIC);transformed={}
    for label,(args,expected) in {
        'parallel':((5,3,1,0,1,F(25,7)),True),'stationary_frame':((5,0,3,4,5,5),True),
        'cancellation':((5,3,-3,0,3,0),True),'negative_denominator':((5,3,-15,20,25,25),True),
        'negative_result':((5,3,1,0,1,F(-25,7)),False),'wrong_input_magnitude':((5,0,3,4,7,5),False),
        'zero_denominator':((5,3,F(-25,3),0,F(25,3),0),False),'light_boundary':((5,5,1,0,1,5),False),
    }.items():
        fixture=ConstructedCuts();model=guarded(doc);fixture.arithmetic(model)
        for symbol,value in zip(('j'+c for c in 'abcdef'),args):model[symbol]=lambda value=value:fixture.make(value)
        actual=values(doc,model,('object',))
        if actual!=[expected]:raise ValueError('Transformed magnitude differs: '+label+repr(actual))
        transformed[label]=actual
    return {'norms':rows,'transformed':transformed,'constructed_rational_cut_oracles_only':True}


def binding_checks():
    query='r ja[] '+CUT+'.q[k szs[k ja[] k zke[]]].q[k szt[k ja[] k zke[]]].q[k szu[k ja[] k zke[]]].q[k szv[k ja[] k zke[]]].'
    doc=abstract(candidate(composed()[0],query),ARITHMETIC|{'sjs','shd'});decls={d['name']:d for d in doc['declarations']};rows={}
    domain=('e0','e1','r0','r1','m0','m1','point','otherpoint','rest','moving','x','y','z','t')
    for label in ('baseline','negative_components','zero','wrong_candidate','negative_candidate','swapped_functions',
        'wrong_derivative','different_derivative_time','point_outside_domain','missing_rest_record','wrong_point','wrong_context','wrong_U_label','wrong_w_label','moving_components_changed'):
        fixture=ConstructedCuts();c=fixture.make;n=fixture.read;model=guarded(doc);fixture.arithmetic(model)
        slopes=(0,0) if label=='zero' else (-3,-4) if label=='negative_components' else (3,4)
        magnitude=0 if label=='zero' else 5;proposal=4 if label=='wrong_candidate' else -5 if label=='negative_candidate' else magnitude
        retained={}
        def function(symbol,slope):
            sort=decls[symbol]['result'];impl=lambda time:c(slope*n(time));retained[impl]=slope
            return FunctionValue(tuple(sort['parameters']),sort['result'],impl)
        def slope_of(value):
            while isinstance(value,FunctionValue):
                impl=value.implementation
                if impl in retained:return retained[impl]
                code=getattr(impl,'__code__',None)
                if code is None:break
                cells=dict(zip(code.co_freevars,(cell.cell_contents for cell in (getattr(impl,'__closure__',None) or ()))))
                value=cells.get('raw')
            raise ValueError('Derivative fixture received an unknown function')
        x=function('zkk',slopes[1] if label=='swapped_functions' else slopes[0]);y=function('zkl',slopes[0] if label=='swapped_functions' else slopes[1])
        sort=decls['zkj']['result'];times=FunctionValue(tuple(sort['parameters']),sort['result'],lambda time:0<=n(time)<=1)
        coords={'r0':(0,0,0,0),'m0':(0,0,0,0),'r1':(*slopes,0,1),'m1':(*slopes,0,1)}
        for symbol,value in {'zkb':'point','ra':'rest','zbm':'moving','zke':'other' if label=='wrong_context' else 'motion','yn':'x','yo':'y','yp':'z','zc7':'t'}.items():model[symbol]=lambda value=value:value
        def derivative(selected,function,instant,value):
            slope=slope_of(function)
            return selected(instant) and n(value)==slope and not(label=='different_derivative_time' and slope==4 and n(instant)!=1)
        model.update(ja=lambda:c(proposal),zkj=lambda:times,zkk=lambda:x,zkl=lambda:y,zkm=lambda:c(2 if label=='point_outside_domain' else 0),
            zkn=lambda:c(4 if label=='wrong_derivative' else slopes[0]),zko=lambda:c(slopes[1]),
            zkc=lambda:c(4 if label=='moving_components_changed' else slopes[0]),zkd=lambda:c(slopes[1]),
            zkp=lambda:c(6 if label=='wrong_U_label' else magnitude),zkq=lambda:c(6 if label=='wrong_w_label' else magnitude),
            sjs=derivative,zka=lambda point,event,setting:(point,setting)==('otherpoint' if label=='wrong_point' else 'point','motion') and event in ('e0','e1'),
            zc4=lambda event:event in ('e0','e1'),zc5=lambda record:record in coords,
            zc6=lambda record,role:c(coords.get(record,(0,0,0,0))[('x','y','z','t').index(role)] if role in ('x','y','z','t') else 0),
            shd=lambda event,record,frame,setting:setting=='motion' and (event,record,frame) in {('e0','r0','rest'),('e1','r1','rest'),('e0','m0','moving'),('e1','m1','moving')} and not(label=='missing_rest_record' and record=='r1'))
        bad={'wrong_candidate','negative_candidate','wrong_point','wrong_context'}
        expected=[label not in bad|{'swapped_functions','wrong_derivative','different_derivative_time','point_outside_domain','missing_rest_record'},
            label not in bad|{'moving_components_changed'},label not in {'wrong_candidate','negative_candidate','wrong_U_label'},label not in {'wrong_candidate','negative_candidate','wrong_w_label'}]
        actual=values(doc,model,domain)
        if actual!=expected:raise ValueError('Derivative or magnitude binding differs: '+label+repr(actual))
        rows[label]=actual
    return {'cases':rows,'derivative_oracle_recognizes_retained_affine_functions_only':True,
        'derivatives_not_inferred_by_sampling':True,'all_real_times_exist_proved':False}


def attribution_checks():
    doc=parse(composed()[0]);doc['statements']=doc['statements'][-2:];rows={}
    for label in ('baseline','wrong_author','wrong_scope','wrong_context','swapped_methods','swapped_labels'):
        model=guarded(doc)
        for symbol,value in {'zkr':'U','zks':'w','rd':'author','zkf':'scope','ri':'text'}.items():model[symbol]=lambda value=value:value
        sym=lambda d:json.loads(d.syntax)['symbol']
        def naming(node,author,method,meaning,scope,context):
            pair=('szs','szu') if node=='U' else ('szt','szv')
            if label=='swapped_methods':pair=('szt' if node=='U' else 'szs',pair[1])
            if label=='swapped_labels':pair=(pair[0],'szv' if node=='U' else 'szu')
            return (author,scope,context)==('other' if label=='wrong_author' else 'author','other' if label=='wrong_scope' else 'scope','other' if label=='wrong_context' else 'text') and (sym(method),sym(meaning))==pair
        model['zb']=naming;actual=values(doc,model,('U','w','author','scope','other'))
        if actual!=[label=='baseline']*2:raise ValueError('Magnitude naming differs')
        rows[label]=actual
    return {'cases':rows,'methods_and_labels_quoted_without_evaluation':True}


def alignment():
    path=ROOT/'artifacts/written-units-v1/einstein-1905.json';artifact=json.loads(path.read_text(encoding='utf-8'))
    inventory=json.loads((ROOT/'reports/written-units-v1.json').read_text(encoding='utf-8'))
    if hashlib.sha256(path.read_bytes()).hexdigest()!=inventory['works']['einstein-1905']['units_sha256']:raise ValueError('Pinned magnitude source differs')
    rows=[]
    for uid in ('einstein-1905:u0135','einstein-1905:u0136'):
        unit=next(u for u in artifact['units'] if u['id']==uid)
        if hashlib.sha256(unit['text'].encode('utf-8')).hexdigest()!=unit['text_sha256']:raise ValueError('Magnitude source text differs')
        start=unit['text'].index('Wir setzen:') if uid.endswith('135') else 0
        common=dict(unit=uid,unit_sha256=unit['text_sha256'],definitions=['szn','szq','szr','szs','szt','szu','szv'],status='partial_explicit_reading',full_semantic_equivalence=False)
        rows.append(dict(common,start=start,end=len(unit['text']),source=unit['text'][start:]))
        if uid.endswith('136'):
            item=next(m for m in artifact['math'] if m['id']=='M0252')
            if hashlib.sha256(item['mathml'].encode('utf-8')).hexdigest()!=item['sha256']:raise ValueError('Magnitude math differs')
            rows.append(dict(common,math_id=item['id'],math_sha256=item['sha256']))
    return {'segments':rows,'verified_full_units':0,'facsimile_checked':False,'nonnegative_magnitude_convention_explicit':True,
        'approximation_and_angle_formula_unwritten':True}


def build_report():
    text,basis=composed();doc=parse(text)
    if (ROOT/basis['document']).read_text(encoding='utf-8')!=text:raise ValueError('Stored magnitude differs')
    if json.loads((ROOT/'data/speed-magnitude-basis-v1.json').read_text(encoding='utf-8'))!=basis:raise ValueError('Magnitude basis differs')
    for notation in ('compact','full'):
        form=format_graph(doc,notation)
        if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Magnitude roundtrip differs')
    paths=[basis['document'],'data/speed-magnitude-basis-v1.json','examples/v014/einstein-motion-question.noema',
        'scripts/compose_speed_magnitude.py','scripts/check_speed_magnitude.py','scripts/check_tau_differential.py',
        'noema/discourse.py','noema/finite_semantics.py','noema/polynomial_proofs.py',
        'artifacts/written-units-v1/einstein-1905.json','reports/written-units-v1.json']
    return {'status':'partial_nonnegative_speed_magnitudes_and_shared_derivatives','documents':{basis['document']:audit_basis(doc,basis)},
        'polynomial_lemmas':polynomial_checks(),'norms':norm_checks(),'derivative_bindings':binding_checks(),'attribution':attribution_checks(),'alignment':alignment(),
        'roundtrips':True,'verified_full_units':{'einstein-1905':0,'kant-1784':0},
        'notation_size':{'canonical_source_document_characters':len(text),'added_characters':len(text)-len((ROOT/'examples/v014/einstein-motion-question.noema').read_text(encoding='utf-8'))},
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args();report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Magnitude report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Nonnegative speed magnitudes, component transformations and shared derivatives checked')


if __name__=='__main__':main()
