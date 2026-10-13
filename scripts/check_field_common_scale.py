"""Check common-factor scope and retain a local facsimile correction."""
import argparse
from fractions import Fraction as F
import hashlib
import json
import xml.etree.ElementTree as ET
from noema.finite_semantics import SequenceValue
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.polynomial_proofs import verify_universal
from noema.script import encode, decode
from scripts.check_comoving_labels import values
from scripts.check_coordinate_correspondence import abstract
from scripts.check_described_appraisals import candidate
from scripts.check_rod_setup import callbacks, guarded
from scripts.check_field_transform import setup, affine_callback, OPS, E, H, field_values
from scripts.check_field_constraints import jet_callback
from scripts.check_real_products import assertion
from scripts.compose_limits import call as k, op, both
from scripts.compose_field_common_scale import ROOT, PARENT, CUT, POINT, FIELD, REGION, composed, generic_composed

REPORT=ROOT/'reports/field-common-scale-v1.json'
DOMAIN=('x','y','z','t','other')
DECLS='r ja[] '+FIELD+'.r jb[] '+FIELD+'.r jc[] '+FIELD+'.r jd[] '+FIELD+'.r je[] '+CUT+'.r jf[] '+POINT+'.r jg[] '+REGION+'.'


def vector_checks():
    doc=abstract(parse(generic_composed()[0]+'r ja[] j[a].r jb[] '+CUT+'.r jc[] '+POINT+'.r jd[] '+POINT+'.q[k sag2[k ja[] k jb[] k jc[] k jd[]]].'),OPS)
    cases={
        'positive':(2,(1,2,3),(2,4,6),('x','y','z'),True),
        'negative':(-2,(1,2,3),(-2,-4,-6),('x','y','z'),True),
        'zero_factor':(0,(1,2,3),(0,0,0),('x','y','z'),True),
        'zero_vectors_factor_one':(1,(0,0,0),(0,0,0),('x','y','z'),True),
        'zero_vectors_factor_two':(2,(0,0,0),(0,0,0),('x','y','z'),True),
        'different_component_factors':(2,(1,2,3),(2,6,6),('x','y','z'),False),
        'nonproportional_vectors':(2,(1,0,0),(0,1,0),('x','y','z'),False),
        'empty_axes':(2,(1,2,3),(2,4,6),(),False),
        'duplicate_axes':(2,(1,2,3),(2,4,6),('x','x'),False),
        'reordered_axes':(2,(1,2,3),(2,4,6),('z','x','y'),True),
    };rows={}
    for label,(scale,left,right,axes,expected) in cases.items():
        fixture,model=setup(doc);model={n:f for n,f in model.items() if n in {d['name'] for d in doc['declarations'] if d['kind']=='primitive'}};c=fixture.make
        callbacks(doc,model,{'jc':lambda role:c(left[DOMAIN.index(role)] if role in DOMAIN[:3] else 99),
            'jd':lambda role:c(right[DOMAIN.index(role)] if role in DOMAIN[:3] else -99)})
        model.update(ja=lambda:SequenceValue(axes,'"individual"'),jb=lambda:c(scale))
        actual=values(doc,model,DOMAIN)
        if actual!=[expected]:raise ValueError('Common vector scalar differs: '+label)
        rows[label]=actual
    return {'cases':rows,'zero_factor_not_silently_excluded':True,'uniqueness_not_assumed_for_zero_vectors':True}


def point_checks():
    args='k je[] k ja[] k jb[] k jc[] k jd[] k jf[]'
    doc=abstract(candidate(composed()[0],DECLS+'q[k sah2['+args+']].'),OPS);rows={}
    leftE=[(0,0,0,0,a) for a in (1,2,3)];leftH=[(0,0,0,0,a) for a in (5,7,11)]
    for label in ('baseline',*(f'changed_{i}' for i in range(6)),'second_point_changes_factor','second_point_same_factor'):
        fixture,model=setup(doc);c=fixture.make;rightE=[list(r) for r in leftE];rightH=[list(r) for r in leftH]
        for row in rightE+rightH:row[4]*=2
        if label.startswith('changed_'):(rightE+rightH)[int(label[-1])][4]+=1
        if label=='second_point_changes_factor':rightE[0][3]=1
        callbacks(doc,model,{name:affine_callback(doc,fixture,name,matrix) for name,matrix in (('ja',leftE),('jb',leftH),('jc',rightE),('jd',rightH))})
        callbacks(doc,model,{'jf':lambda role:c(1 if role=='t' and label.startswith('second_point') else 0)})
        model['je']=lambda:c(2)
        actual=values(doc,model,DOMAIN);expected=label in ('baseline','second_point_same_factor')
        if actual!=[expected]:raise ValueError('Common six-component factor differs: '+label)
        rows[label]=actual
    return {'cases':rows,'same_scale_for_both_fields_and_all_six_components':True,'finite_point_checks_only':True}


def source_checks():
    doc=abstract(candidate(composed()[0],'q[t[k sak2[]][k ri[]]].'),OPS|{'sai2','saj2'});rows={}
    # These supplied relations check wiring; real-domain quantification is separately refused.
    for speed in (F(0),F(3),F(-3)):
        for label in ('baseline','wrong_context','unequal_regions','wrong_factor','field_mismatch'):
            fixture,model=setup(doc);c,n=fixture.make,fixture.read
            callbacks(doc,model,{'znl':affine_callback(doc,fixture,'znl',E),'znm':affine_callback(doc,fixture,'znm',H),
                'znr':affine_callback(doc,fixture,'znr',[(0,0,0,0,a) for a in (17,19,23)]),
                'zns':affine_callback(doc,fixture,'zns',[(0,0,0,0,a) for a in (29,31,37)]),
                'znk':lambda *xs:n(xs[0])>=0,'znt':lambda *xs:True,'znz':lambda value:c(2+n(value)/3)})
            model.update(tc=lambda:c(5),zb7=lambda:c(speed),ra=lambda:'rest',zbm=lambda:'moving',ri=lambda:'text')
            model['znn']=lambda frame,e,h,region,context:context==('other' if label=='wrong_context' else 'text') and frame in ('rest','moving')
            model['saj2']=lambda left,right:label!='unequal_regions'
            def proportional(scale,e,h,newE,newH,region):
                if n(scale)!=(99 if label=='wrong_factor' else 2+speed/3):return False
                for point in ((F(1),F(0),F(0),F(0)),(F(0),F(0),F(0),F(1))):
                    ev,hv=field_values(E,H,point,speed)
                    for field,expected in ((e,ev),(h,hv)):
                        if [n(field(role)(*(c(x) for x in point))) for role in DOMAIN[:3]]!=expected:return False
                origin=[c(0)]*4
                return label!='field_mismatch' and [n(newE(r)(*origin)) for r in DOMAIN[:3]]==[17,19,23] and [n(newH(r)(*origin)) for r in DOMAIN[:3]]==[29,31,37] and region(c(1),c(0),c(0),c(0))
            model['sai2']=proportional;actual=values(doc,model,(*DOMAIN,'rest','moving'))
            if actual!=[label=='baseline']:raise ValueError('Source factor/field wiring differs: '+str((speed,label,actual)))
            rows[str(speed)+':'+label]=actual
    return {'cases':rows,'global_proportionality_and_domain_equality_are_explicit_oracles':True,
        'actual_mixed_fields_and_inverse_coordinates_evaluated':True,'arbitrary_real_field_proof':False}


def counterexample_checks():
    # Two constant electric fields (1,0,0) and (0,1,0), magnetic fields zero.
    # Their 24 partial values are all zero, so both satisfy even the eight balances.
    from scripts.compose_field_equations import JET
    doc=abstract(candidate(composed()[0],'r ja[] '+JET+'.r jb[] '+JET+'.q[k s6r[k tc[] k ja[] k jb[]]].'),OPS)
    fixture,model=setup(doc)
    callbacks(doc,model,{'ja':jet_callback(fixture,((0,0,0,0),)*3),'jb':jet_callback(fixture,((0,0,0,0),)*3)})
    model['tc']=lambda:fixture.make(5);result=values(doc,model,DOMAIN)
    if result!=[True]:raise ValueError('Constant-field zero gradients violate balances')
    false_scale=both(op('e',k('ad','v scale','n p b b'),'n p a b'),op('e',k('ad','v scale','n p a b'),'n p b b'))
    algebra=verify_universal(parse('n:r ad[b b] b.'+assertion('scale',op('u',false_scale))),{'ad':'multiply'},timeout_ms=20000)[0]
    if algebra['status']!='valid':raise ValueError('Nonproportional constant fields were not separated')
    return {'first_electric':[1,0,0],'second_electric':[0,1,0],'both_magnetic':[0,0,0],
        'all_partial_values_supplied_as_zero':True,'eight_algebraic_balances':result,'no_common_rational_scalar':algebra,
        'meaning':'Constant fields have zero derivatives; common differential equations alone do not identify their values or a shared scale.',
        'does_not_refute_unformalized_physical_identification_premises':True}


def attribution_checks():
    doc=parse(composed()[0]);doc['statements']=doc['statements'][-1:];rows={}
    for index in range(-1,5):
        model=guarded(doc)
        for name,value in {'zn2':'node','rd':'author','zno':'scope','ri':'text'}.items():model[name]=lambda value=value:value
        expected=['node','author','sak2','scope','text']
        if index>=0:expected[index]='other'
        model['uh']=lambda node,author,content,scope,context:[node,author,json.loads(content.syntax)['symbol'],scope,context]==expected
        actual=values(doc,model,('node','author','scope','other'))
        if actual!=[index==-1]:raise ValueError('Scale claim attribution differs')
        rows[str(index)]=actual
    return {'cases':rows,'claim_not_evaluated_as_truth':True}


def finite_refusal():
    doc=abstract(candidate(composed()[0],DECLS+'q[k sai2[k je[] k ja[] k jb[] k jc[] k jd[] k jg[]]].'),OPS)
    fixture,model=setup(doc);c=fixture.make
    callbacks(doc,model,{n:affine_callback(doc,fixture,n,[(0,0,0,0,0)]*3) for n in ('ja','jb','jc','jd')})
    callbacks(doc,model,{'jg':lambda *xs:True});model['je']=lambda:c(1)
    try:values(doc,model,DOMAIN)
    except ValueError as error:
        if 'Cannot finitely quantify the rational number domain' not in str(error):raise
        return {'refused':True,'reason':str(error)}
    raise ValueError('Full-region scaling was replaced by finite sampling')


def alignment():
    path=ROOT/'artifacts/written-units-v1/einstein-1905.json';source=json.loads(path.read_text(encoding='utf-8'))
    inventory=json.loads((ROOT/'reports/written-units-v1.json').read_text(encoding='utf-8'))
    if hashlib.sha256(path.read_bytes()).hexdigest()!=inventory['works']['einstein-1905']['units_sha256']:raise ValueError('Scale source inventory differs')
    correction=json.loads((ROOT/'data/field-common-scale-facsimile-v1.json').read_text(encoding='utf-8'))
    if hashlib.sha256((ROOT/correction['image']).read_bytes()).hexdigest()!=correction['image_sha256']:raise ValueError('Facsimile image changed')
    rows=[]
    for index in (163,164):
        unit=next(u for u in source['units'] if u['id']==f'einstein-1905:u{index:04}')
        if hashlib.sha256(unit['text'].encode('utf-8')).hexdigest()!=unit['text_sha256']:raise ValueError('Scale source text differs')
        base=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],definitions=['sag2','sah2','sai2','saj2','sak2'],status='partial_explicit_reading',full_semantic_equivalence=False)
        if index==163:
            start=unit['text'].index('die in den Gleichungssystemen an entsprechenden Stellen');end=unit['text'].index(' Es gelten')
            rows.append(dict(base,start=start,end=end,source=unit['text'][start:end]))
        for mid in unit['math_ids']:
            if mid in ('M0301','M0302'):continue # Prior equivalence reasoning remains unwritten.
            m=next(m for m in source['math'] if m['id']==mid)
            if hashlib.sha256(m['mathml'].encode('utf-8')).hexdigest()!=m['sha256']:raise ValueError('Scale source math differs')
            rows.append(dict(base,math_id=mid,math_sha256=m['sha256']))
    m=next(m for m in source['math'] if m['id']=='M0307');ns='{http://www.w3.org/1998/Math/MathML}'
    if m['sha256']!=correction['correction']['snapshot_math_sha256']:raise ValueError('Correction target changed')
    raw=[''.join(cell.itertext()) for cell in ET.fromstring(m['mathml']).iter(ns+'mtd')]
    expected=['X′','=ψ(v)X,','L′','=ψ(v)L,','Y′','=ψ(v)β(Y−vVN),','M′','=ψ(v)β(M+vVz),','Z′','=ψ(v)β(Z+vVM),','N′','=ψ(v)β(N−vVY).']
    if raw!=expected:raise ValueError('Six proportionality equations differ: '+repr(raw))
    normalized=raw.copy();normalized[7]=normalized[7].replace('z','Z')
    return {'segments':rows,'raw_math_cells':raw,'facsimile_corrected_math_cells':normalized,
        'facsimile_scope':'M0307 component symbols and six common factors visually checked on extracted printed p908; no full semantic review',
        'inference_before_conclusion_clause_unwritten':True,'verified_full_units':0}


def build_report():
    documents={}
    for builder,name in ((generic_composed,'field-common-scale'),(composed,'einstein-field-common-scale')):
        text,basis=builder();doc=parse(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text or json.loads((ROOT/('data/'+name+'-basis-v1.json')).read_text(encoding='utf-8'))!=basis:raise ValueError('Stored common scale differs')
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Common scale roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis)
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    if doc['statements'][:-1]!=parent['statements'] or doc['declarations'][:len(parent['declarations'])]!=parent['declarations']:raise ValueError('Parent scale source changed')
    paths=list(documents)+['data/field-common-scale-basis-v1.json','data/einstein-field-common-scale-basis-v1.json',PARENT,
        'scripts/compose_field_common_scale.py','scripts/check_field_common_scale.py','scripts/check_field_transform.py','scripts/check_field_constraints.py',
        'data/field-common-scale-facsimile-v1.json','artifacts/written-facsimiles-v1/einstein-1905-unlp-p908-0.jpg',
        'artifacts/written-units-v1/einstein-1905.json','reports/written-units-v1.json','noema/discourse.py','noema/finite_semantics.py']
    return {'status':'partial_common_field_factor_and_insufficient_premise_counterexample','documents':documents,
        'vectors':vector_checks(),'points':point_checks(),'source':source_checks(),'counterexample':counterexample_checks(),
        'attribution':attribution_checks(),'finite_refusal':finite_refusal(),'alignment':alignment(),'roundtrips':True,'parent_preserved':True,
        'verified_full_units':{'einstein-1905':0,'kant-1784':0},
        'notation_size':{'canonical_source_document_characters':len(text),'added_characters':len(text)-len((ROOT/PARENT).read_text(encoding='utf-8'))},
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args();report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Common scale report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Common scale, nonproportional solutions, source attribution and facsimile correction checked')


if __name__=='__main__':main()
