"""Verify reciprocal scales while exposing the unselected negative branch."""
import argparse
from fractions import Fraction as F
import hashlib
from itertools import product
import json
import xml.etree.ElementTree as ET
from noema.finite_semantics import Content
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.polynomial_proofs import verify_universal
from noema.script import encode, decode
from scripts.check_comoving_labels import values
from scripts.check_coordinate_correspondence import abstract
from scripts.check_described_appraisals import candidate
from scripts.check_rod_setup import callbacks, guarded
from scripts.check_field_transform import setup, affine_callback, OPS, E, H
from scripts.check_real_products import assertion
from scripts.check_moving_light_trip import literal
from scripts.compose_limits import call as k, app, op, both
from scripts.compose_field_equations import POINT, ROLES
from scripts.compose_field_scale_inverse import ROOT, PARENT, CUT, FIELD, composed, generic_composed

REPORT=ROOT/'reports/field-scale-inverse-v1.json'
DOMAIN=('x','y','z','t','other')


def polynomial_checks():
    mul=lambda a,b:k('ad',a,b);neg=lambda a:k('ac',a);add=lambda a,b:k('ab',a,b)
    a,b,beta,r,own,cross=('v '+n for n in ('first','second','beta','ratio','own','cross'))
    zero,one=literal(0),literal(1);eq=lambda x,y:op('e',x,y)
    normalized=eq(mul(mul(beta,beta),add(one,neg(mul(r,r)))),one)
    inverse=k('sam2',a,b);even=eq(a,b);positive=k('aa',zero,a)
    claims={
        'minus_roundtrip_scales_by_product':assertion('beta ratio first second own cross',op('y',normalized,eq(k('sax2',beta,r,a,b,own,cross),mul(mul(a,b),own)))),
        'plus_roundtrip_scales_by_product':assertion('beta ratio first second own cross',op('y',normalized,eq(k('say2',beta,r,a,b,own,cross),mul(mul(a,b),own)))),
        'reciprocal_scales_recover_both_sign_patterns':assertion('beta ratio first second own cross',op('y',both(normalized,inverse),both(eq(k('sax2',beta,r,a,b,own,cross),own),eq(k('say2',beta,r,a,b,own,cross),own)))),
        'nonzero_recovered_value_forces_reciprocity':assertion('first second own',op('y',both(op('u',eq(own,zero)),eq(mul(mul(a,b),own),own)),inverse)),
        'inverse_scales_are_nonzero':assertion('first second',op('y',inverse,both(op('u',eq(a,zero)),op('u',eq(b,zero))))),
        'inverse_and_even_allow_exactly_two_branches':assertion('first second',op('y',both(inverse,even),op('x',eq(a,one),eq(a,literal(-1))))),
        'positive_branch_selects_one':assertion('first second',op('y',both(inverse,even,positive),eq(a,one))),
        'negative_branch_is_a_counterexample_to_unit_conclusion':assertion('',both(k('sam2',literal(-1),literal(-1)),op('u',eq(literal(-1),one)))),
    };rows={}
    for name,claim in claims.items():
        result=verify_universal(parse(generic_composed()[0]+claim),{'aa':'less','ab':'add','ac':'negate','ad':'multiply'},timeout_ms=20000)[0]
        if result['status']!='valid':raise ValueError('Inverse-scale algebra differs: '+name+repr(result))
        rows[name]=result
    return {'claims':rows,'rational_polynomial_claims_only':True,'positive_branch_not_added_to_author_premise':True}


def inverse_field_checks():
    declarations='r ja[] '+FIELD+'.r jb[] '+FIELD+'.r jc[] '+CUT+'.r jd[] '+CUT+'.r je[] '+POINT+'.r jf[] '+CUT+'.r jg[] '+CUT+'.'
    forward=lambda name:k('sal2','k jf[]',k(name,'k jc[]','k jd[]','k ja[]','k jb[]'))
    opposite=k('bf',k('bb',literal(0)),'k jd[]');query=''
    coords=[app('k je[]',k(role)) for role in ROLES]
    for name,original in (('s6k','k ja[]'),('s6l','k jb[]')):
        recovered=k('sal2','k jg[]',k(name,'k jc[]',opposite,forward('s6k'),forward('s6l')))
        for role in ROLES[:3]:query+='q['+k('sca',app(app(recovered,k(role)),*coords),app(app(original,k(role)),*coords))+'].'
    doc=abstract(candidate(composed()[0],declarations+query),OPS);rows={}
    for speed in (F(0),F(3),F(-3)):
        for label,a,b in (('positive_reciprocal',F(2),F(1,2)),('negative_reciprocal',F(-2),F(-1,2)),('wrong_inverse',F(2),F(1)),('zero_forward',F(0),F(3))):
            fixture,model=setup(doc);c=fixture.make
            callbacks(doc,model,{'ja':affine_callback(doc,fixture,'ja',E),'jb':affine_callback(doc,fixture,'jb',H),'je':lambda role:c(1 if role in ('x','t') else 0)})
            model.update(jc=lambda:c(5),jd=lambda:c(speed),jf=lambda:c(a),jg=lambda:c(b))
            actual=values(doc,model,DOMAIN)
            if all(actual)!=(a*b==1):raise ValueError('Scaled field inverse differs: '+str((speed,label,actual)))
            rows[str(speed)+':'+label]=actual
    return {'cases':rows,'actual_six_component_and_inverse_coordinate_definitions_evaluated':True,
        'affine_rational_fixtures_only':True,'zero_forward_not_invertible':True}


def coefficient_checks():
    query=''.join('q[t[k '+name+'[]][k ri[]]].' for name in ('saq2','sar2','sas2','sat2'))
    doc=abstract(candidate(composed()[0],query),OPS);rows={}
    cases={'positive_unit':(3,1,1),'negative_unit':(3,-1,-1),'reciprocal_unequal':(3,2,F(1,2)),
        'equal_two':(3,2,2),'both_zero':(3,0,0),'zero_speed_unit':(0,1,1),'light_speed_excluded':(5,1,1),'negative_light_speed_excluded':(-5,1,1)}
    for label,(speed,a,b) in cases.items():
        fixture,model=setup(doc);c,n=fixture.make,fixture.read
        callbacks(doc,model,{'znz':lambda value:c(a if n(value)==speed else b)})
        model.update(tc=lambda:c(5),zb7=lambda:c(speed),ri=lambda:'text')
        actual=values(doc,model,DOMAIN);admissible=abs(speed)<5
        expected=[admissible and a*b==1,admissible and a==b,admissible and a*b==1 and a==b,admissible and a==1]
        if actual!=expected:raise ValueError('Source coefficient branch differs: '+label+repr(actual))
        rows[label]=actual
    return {'cases':rows,'source_negative_branch_kept_as_true_premise_false_conclusion':True,
        'physical_symmetry_argument_not_evaluated':True}


def final_premise_checks():
    doc=abstract(candidate(composed()[0],'q[t[k sav2[]][k ri[]]].'),{'sak2','sat2'});rows=[]
    for common,unit in product((False,True),repeat=2):
        model=guarded(doc);model.update(ri=lambda:'text',sak2=lambda:Content(('motion','text','other'),(False,common,False)),sat2=lambda:Content(('motion','text','other'),(False,unit,False)))
        result=values(doc,model,DOMAIN)
        if result!=[common and unit]:raise ValueError('Final normalization premise differs')
        rows.append(dict(common_scale=common,unit=unit,result=result))
    return rows


def normalized_binding_checks():
    doc=abstract(candidate(composed()[0],'q[t[k sau2[]][k ri[]]].'),OPS|{'saj2','sai2'});rows={}
    for label in ('baseline','wrong_context','unequal_domains','nonunit_factor_expected'):
        fixture,model=setup(doc);c,n=fixture.make,fixture.read
        callbacks(doc,model,{'znl':affine_callback(doc,fixture,'znl',E),'znm':affine_callback(doc,fixture,'znm',H),
            'znr':affine_callback(doc,fixture,'znr',E),'zns':affine_callback(doc,fixture,'zns',H),'znk':lambda *xs:True,'znt':lambda *xs:True})
        model.update(tc=lambda:c(5),zb7=lambda:c(0),ra=lambda:'rest',zbm=lambda:'moving',ri=lambda:'text',
            znn=lambda frame,e,h,region,ctx:ctx==('other' if label=='wrong_context' else 'text'),saj2=lambda a,b:label!='unequal_domains')
        def global_scale(scale,e,h,newE,newH,region):
            if n(scale)!=(2 if label=='nonunit_factor_expected' else 1):return False
            point=[c(a) for a in (1,0,0,1)]
            return region(*point) and all(n(a(role)(*point))==n(b(role)(*point)) for a,b in ((e,newE),(h,newH)) for role in DOMAIN[:3])
        model['sai2']=global_scale;actual=values(doc,model,(*DOMAIN,'rest','moving'))
        if actual!=[label=='baseline']:raise ValueError('Final unit-scale wiring differs: '+label)
        rows[label]=actual
    return {'cases':rows,'global_domain_and_proportionality_are_fixture_oracles':True}


def attribution_checks():
    source=parse(composed()[0]);rows={}
    for i,(node,kind,contents) in enumerate((('zn3','uh',('saq2',)),('zn4','uh',('sar2',)),('zn5','zc',('sas2','sat2')),('zn6','zc',('sav2','sau2')))):
        doc=dict(source,statements=[source['statements'][-4+i]])
        for label in ('baseline','wrong_author','wrong_scope','wrong_context','wrong_content'):
            model=guarded(doc)
            for name,value in {node:'node','rd':'author','zno':'scope','ri':'text'}.items():model[name]=lambda value=value:value
            def attributed(n,who,*args):
                descriptions,scope,ctx=args[:-2],args[-2],args[-1]
                return (n,who,scope,ctx)==('node','other' if label=='wrong_author' else 'author','other' if label=='wrong_scope' else 'scope','other' if label=='wrong_context' else 'text') and tuple(json.loads(d.syntax)['symbol'] for d in descriptions)==(('other',)*len(contents) if label=='wrong_content' else contents)
            model[kind]=attributed;actual=values(doc,model,('node','author','scope','other'))
            if actual!=[label=='baseline']:raise ValueError('Coefficient discourse differs')
            rows[node+':'+label]=actual
    return {'cases':rows,'claims_and_inferences_do_not_execute_quoted_truth':True}


def alignment():
    path=ROOT/'artifacts/written-units-v1/einstein-1905.json';source=json.loads(path.read_text(encoding='utf-8'))
    inventory=json.loads((ROOT/'reports/written-units-v1.json').read_text(encoding='utf-8'))
    if hashlib.sha256(path.read_bytes()).hexdigest()!=inventory['works']['einstein-1905']['units_sha256']:raise ValueError('Inverse scale source changed')
    meta=json.loads((ROOT/'data/field-scale-inverse-facsimile-v1.json').read_text(encoding='utf-8'))
    if hashlib.sha256((ROOT/meta['image']).read_bytes()).hexdigest()!=meta['image_sha256']:raise ValueError('Coefficient scan changed')
    rows=[];maths={}
    for index in (165,166,168,169,170,171,172):
        unit=next(u for u in source['units'] if u['id']==f'einstein-1905:u{index:04}')
        if hashlib.sha256(unit['text'].encode('utf-8')).hexdigest()!=unit['text_sha256']:raise ValueError('Coefficient text differs')
        base=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],definitions=['saq2','sar2','sas2','sat2','sau2','sav2'],status='partial_explicit_reading',full_semantic_equivalence=False)
        if index in (169,171):rows.append(dict(base,start=0,end=len(unit['text']),source=unit['text']))
        for mid in unit['math_ids']:
            if mid in ('M0308','M0309'):continue
            m=next(m for m in source['math'] if m['id']==mid)
            if hashlib.sha256(m['mathml'].encode('utf-8')).hexdigest()!=m['sha256']:raise ValueError('Coefficient math differs')
            maths[mid]=''.join(ET.fromstring(m['mathml']).itertext());rows.append(dict(base,math_id=mid,math_sha256=m['sha256']))
    expected={'M0310':'−v','M0311':'φ(v).φ(−v)=1','M0312':'φ(v)=φ(−v)','M0313':'φ(v)=1','M0314':'X′=X,L′=L,Y′=β(Y−vVN),M′=β(M+vVZ),Z′=β(Z+vVM),N′=β(N−vVY).'}
    if maths!=expected:raise ValueError('Source inverse/normalized equations differ: '+repr(maths))
    return {'segments':rows,'source_math_text':maths,'notation_reading':meta['notation_reading'],
        'facsimile_scope':'Printed p909 coefficient relations and final six equations inspected; not whole-page semantic verification',
        'two_inverse_constructions_and_symmetry_reason_unwritten':True,'positive_branch_justification_unwritten':True,'verified_full_units':0}


def build_report():
    documents={}
    for builder,name in ((generic_composed,'field-scale-inverse'),(composed,'einstein-field-scale-inverse')):
        text,basis=builder();doc=parse(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text or json.loads((ROOT/('data/'+name+'-basis-v1.json')).read_text(encoding='utf-8'))!=basis:raise ValueError('Stored inverse scales differ')
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Inverse scale roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis)
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    if doc['statements'][:-4]!=parent['statements'] or doc['declarations'][:len(parent['declarations'])]!=parent['declarations']:raise ValueError('Parent inverse source changed')
    paths=list(documents)+['data/field-scale-inverse-basis-v1.json','data/einstein-field-scale-inverse-basis-v1.json',PARENT,
        'scripts/compose_field_scale_inverse.py','scripts/check_field_scale_inverse.py','scripts/check_field_transform.py',
        'data/field-scale-inverse-facsimile-v1.json','artifacts/written-facsimiles-v1/einstein-1905-unlp-p909-0.jpg',
        'artifacts/written-units-v1/einstein-1905.json','reports/written-units-v1.json','noema/discourse.py','noema/finite_semantics.py','noema/polynomial_proofs.py']
    return {'status':'partial_inverse_coefficient_and_explicit_negative_branch','documents':documents,
        'polynomial_lemmas':polynomial_checks(),'inverse_fields':inverse_field_checks(),'coefficient_branches':coefficient_checks(),
        'normalization_premise':final_premise_checks(),'normalized_binding':normalized_binding_checks(),'attribution':attribution_checks(),
        'alignment':alignment(),'roundtrips':True,'parent_preserved':True,'verified_full_units':{'einstein-1905':0,'kant-1784':0},
        'notation_size':{'canonical_source_document_characters':len(text),'added_characters':len(text)-len((ROOT/PARENT).read_text(encoding='utf-8'))},
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args();report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Inverse scale report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Inverse scales, signed branches and source normalization checked')


if __name__=='__main__':main()
