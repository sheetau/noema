"""Check field/axis bindings and six signs without sampling real derivatives."""
import argparse
from fractions import Fraction as F
import hashlib
import json
import xml.etree.ElementTree as ET

from noema.finite_semantics import FunctionValue
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.polynomial_proofs import verify_universal
from noema.script import encode, decode
from scripts.check_comoving_labels import values
from scripts.check_coordinate_correspondence import abstract
from scripts.check_described_appraisals import candidate
from scripts.check_rod_setup import guarded, callbacks
from scripts.check_tau_differential import ConstructedCuts
from scripts.check_real_products import MEANINGS as ARITHMETIC_MEANINGS, assertion
from scripts.compose_limits import call as k, op, both
from scripts.compose_field_equations import ROOT, CUT, TAU, POINT, REGION, FIELD, JET, PARENT, ROLES, composed, generic_composed

REPORT=ROOT/'reports/field-equations-v1.json'
ARITHMETIC={'ba','bb','bc','bg','bd','bf','shv','bj','sjd','sca','szi'}
AXES=('x','y','z','t');DOMAIN=AXES+('other',)
E=((1,2,3,12),(4,5,6,-12),(7,8,9,-4))
H=((2,5,11,-4),(3,7,13,8),(17,19,23,-4))


def setup(doc):
    fixture=ConstructedCuts();model=guarded(doc);fixture.arithmetic(model)
    model['szi']=lambda condition,a,b:a if condition else b
    for symbol,value in zip(ROLES,AXES):model[symbol]=lambda value=value:value
    return fixture,model


def polynomial_checks():
    V,r,p,n,s,t,u=('v '+a for a in ('light','rate','positive','negative','scale','secondrate','inverse'))
    relation=lambda r,p,n:k('s6a',V,r,p,n)
    mul=lambda a,b:k('ad',a,b);add=lambda a,b:k('ab',a,b)
    claims={
        'positive_denominator_form_iff_multiplied_form':assertion('light rate positive negative inverse',op('y',
            both(k('aa','n p a b',V),op('e',mul(V,u),'n p b b')),
            op('z',relation(r,p,n),op('e',mul(u,r),add(p,k('ac',n)))))),
        'scaling_all_three_values_preserves_equation':assertion('light rate positive negative scale',op('y',relation(r,p,n),relation(mul(s,r),mul(s,p),mul(s,n)))),
        'rate_unique_at_fixed_light_and_spatial_values':assertion('light rate secondrate positive negative',op('y',both(relation(r,p,n),relation(t,p,n)),op('e',r,t))),
        'reversing_spatial_difference_preserves_equation':assertion('light rate positive negative',op('y',relation(r,p,n),relation(r,n,p))),
    }
    rows={}
    for label,claim in claims.items():
        result=verify_universal(parse(generic_composed()[0]+claim),ARITHMETIC_MEANINGS,timeout_ms=15000)[0]
        expected='invalid' if label=='reversing_spatial_difference_preserves_equation' else 'valid'
        if result['status']!=expected:raise ValueError('Field algebra differs: '+label)
        rows[label]=result
    return {'claims':rows,'rational_algebra_not_a_derivative_proof':True}


def slice_checks():
    query='r ja[] '+TAU+'.r jb[] '+REGION+'.r jc[] '+POINT+'.r jd[] a.r je[] '+CUT+'.q[k s5t[k ja[] k jb[] k jc[] k jd[] k je[]]].'
    doc=abstract(candidate(composed()[0],query),ARITHMETIC|{'sjs'});rows={};coeff=(2,3,5,7);center=(1,2,3,4)
    for axis in range(4):
        for label in ('baseline','wrong_value','wrong_x','wrong_y','wrong_z','wrong_t','excluded_point','missing_derivative','invalid_axis'):
            fixture,model=setup(doc);c,n=fixture.make,fixture.read
            point=list(center)
            if label.startswith('wrong_') and label[6:] in AXES:point[AXES.index(label[6:])]+=1
            callbacks(doc,model,{'ja':lambda *xs:c(sum(a*n(x) for a,x in zip(coeff,xs))),
                'jb':lambda *xs:label!='excluded_point' and all(-10<n(x)<10 for x in xs),
                'jc':lambda role:c(point[AXES.index(role)] if role in AXES else 0)})
            model.update(jd=lambda:'other' if label=='invalid_axis' else AXES[axis],je=lambda:c(coeff[axis]+(label=='wrong_value')))
            observed=[]
            def derivative(domain,fn,at,value):
                observed.append(True)
                expected=lambda s:sum(a*(s if i==axis else center[i]) for i,a in enumerate(coeff))
                return label!='missing_derivative' and n(at)==center[axis] and n(value)==coeff[axis] and all(
                    domain(c(s)) and n(fn(c(s)))==expected(s) for s in (F(-1),F(0),F(1)))
            model['sjs']=derivative;actual=values(doc,model,DOMAIN)
            if actual!=[label=='baseline']:raise ValueError('Field derivative slice differs: '+str((axis,label,actual)))
            rows[AXES[axis]+':'+label]=actual
    return {'cases':rows,'derivative_relation_is_explicit_affine_fixture_oracle':True,
        'other_coordinates_held_fixed':True,'relative_domain_passed_to_derivative':True}


def field_callback(doc,fixture,name,matrix):
    sort=next(d['result']['result'] for d in doc['declarations'] if d['name']==name)
    def component(role):
        coeff=matrix[AXES.index(role)] if role in AXES[:3] else (0,0,0,0)
        return FunctionValue(tuple(sort['parameters']),sort['result'],lambda *xs:fixture.make(sum(a*fixture.read(x) for a,x in zip(coeff,xs))))
    return component


def jet_callback(fixture,matrix):
    return lambda component,axis:fixture.make(matrix[AXES.index(component)][AXES.index(axis)] if component in AXES[:3] and axis in AXES else 0)


def jet_checks(balance=False):
    declarations='r ja[] '+FIELD+'.r jb[] '+FIELD+'.r jc[] '+REGION+'.r jd[] '+POINT+'.r je[] '+JET+'.r jf[] '+JET+'.r jg[] '+CUT+'.'
    query='q[k s5w[k jg[] k je[] k jf[]]].' if balance else 'q[k s5u[k ja[] k jb[] k jc[] k jd[] k je[] k jf[]]].'
    doc=abstract(candidate(composed()[0],declarations+query),ARITHMETIC|({'s5t'} if not balance else set()));rows={}
    labels=['baseline']+[f'changed_{field}_{i}_{j}' for field in ('E','H') for i in range(3) for j in range(4) if i!=j]
    labels+=['swapped_fields','wrong_point','wrong_region','missing_derivative'] if not balance else ['zero_fields','static_nonzero_divergence','zero_light','negative_light','wrong_light','invalid_rate']
    for label in labels:
        fixture,model=setup(doc);c,n=fixture.make,fixture.read;e=[list(row) for row in E];h=[list(row) for row in H]
        if label.startswith('changed_'):
            _,field,i,j=label.split('_');(e if field=='E' else h)[int(i)][int(j)]+=1
        if label=='zero_fields':e=h=[[0]*4 for _ in range(3)]
        if label=='static_nonzero_divergence':e=[[1,0,0,0],[0,0,0,0],[0,0,0,0]];h=[[0]*4 for _ in range(3)]
        if label=='invalid_rate':e[0][3]=128
        callbacks(doc,model,{'ja':field_callback(doc,fixture,'ja',H if label=='swapped_fields' else E),
            'jb':field_callback(doc,fixture,'jb',E if label=='swapped_fields' else H),
            'jc':lambda *xs:label!='wrong_region',
            'jd':lambda role:c((1,2,3,5 if label=='wrong_point' else 4)[AXES.index(role)] if role in AXES else 0),
            'je':jet_callback(fixture,e),'jf':jet_callback(fixture,h)})
        model['jg']=lambda:c({'zero_light':0,'negative_light':-2,'wrong_light':3}.get(label,2))
        def derivative(fn,region,point,axis,value):
            if label=='missing_derivative' or tuple(n(point(a)) for a in AXES)!=(1,2,3,4):return False
            if not region(*(point(a) for a in AXES)):return False
            coefficients=tuple(n(fn(*(c(int(i==j)) for i in range(4)))) for j in range(4))
            return coefficients in E+H and n(value)==coefficients[AXES.index(axis)]
        if not balance:model['s5t']=derivative
        actual=values(doc,model,DOMAIN);expected=label in ('baseline','zero_fields','static_nonzero_divergence')
        if actual!=[expected]:raise ValueError('Field jet differs: '+str((balance,label,actual)))
        rows[label]=actual
    return {'cases':rows,'partial_derivatives_are_oracles':not balance,'all_six_nonzero_time_rates_exercised':True,
        'one_at_a_time_changes_cover_all_eighteen_used_partials':True}


def source_checks():
    doc=abstract(candidate(composed()[0],'q[t[k s5z[]][k ri[]]].'),ARITHMETIC|{'s5y'});rows={}
    for label in ('baseline','wrong_frame','wrong_context','swapped_fields','wrong_region','wrong_light','equations_fail'):
        fixture,model=setup(doc);c,n=fixture.make,fixture.read
        model.update(ra=lambda:'rest',ri=lambda:'text',tc=lambda:c(2))
        callbacks(doc,model,{'znl':field_callback(doc,fixture,'znl',E),'znm':field_callback(doc,fixture,'znm',H),'znk':lambda *xs:True})
        def fingerprint(field):return tuple(n(field(a)(c(1),c(0),c(0),c(0))) for a in AXES[:3])
        def bind(frame,e,h,region,context):
            return (frame,context)==('other' if label=='wrong_frame' else 'rest','other' if label=='wrong_context' else 'text') and (
                fingerprint(e),fingerprint(h))==(((2,3,17),(1,4,7)) if label=='swapped_fields' else ((1,4,7),(2,3,17))) and label!='wrong_region' and region(c(0),c(0),c(0),c(0))
        model['znn']=bind
        model['s5y']=lambda e,h,region,light:label!='equations_fail' and fingerprint(e)==(1,4,7) and fingerprint(h)==(2,3,17) and region(c(0),c(0),c(0),c(0)) and n(light)==(3 if label=='wrong_light' else 2)
        actual=values(doc,model,DOMAIN+('rest',))
        if actual!=[label=='baseline']:raise ValueError('Source field binding differs: '+label)
        rows[label]=actual
    return {'cases':rows,'full_region_equation_is_explicit_oracle':True,'rest_frame_and_same_light_preserved':True}


def finite_refusals():
    decls='r ja[] '+FIELD+'.r jb[] '+FIELD+'.r jc[] '+REGION+'.r jd[] '+POINT+'.r je[] '+CUT+'.'
    queries={'partial_limit':'k s5t[c[k ja[]][k yn[]] k jc[] k jd[] k yn[] k je[]]',
        'existence_of_derivative_maps':'k s5x[k ja[] k jb[] k jc[] k jd[] k je[]]',
        'all_points_of_region':'k s5y[k ja[] k jb[] k jc[] k je[]]'};rows={}
    for label,query in queries.items():
        doc=abstract(candidate(composed()[0],decls+'q['+query+'].'),ARITHMETIC);fixture,model=setup(doc);c=fixture.make
        callbacks(doc,model,{'ja':field_callback(doc,fixture,'ja',E),'jb':field_callback(doc,fixture,'jb',H),
            'jc':lambda *xs:True,'jd':lambda role:c(0)})
        model['je']=lambda:c(2)
        try:values(doc,model,DOMAIN)
        except ValueError as error:
            if 'Cannot finitely quantify the rational number domain' not in str(error):raise
            rows[label]={'refused':True,'reason':str(error)}
        else:raise ValueError('Finite evaluator accepted full field condition: '+label)
    return rows


def attribution_checks():
    doc=parse(composed()[0]);doc['statements']=doc['statements'][-1:];rows={}
    for label in ('baseline','wrong_author','wrong_scope','wrong_context','wrong_content'):
        model=guarded(doc)
        for name,value in {'znp':'node','rd':'author','zno':'scope','ri':'text'}.items():model[name]=lambda value=value:value
        model['ug']=lambda node,who,content,scope,context:(node,who,scope,context)==('node','other' if label=='wrong_author' else 'author',
            'other' if label=='wrong_scope' else 'scope','other' if label=='wrong_context' else 'text') and json.loads(content.syntax)['symbol']==('s5s' if label=='wrong_content' else 's5z')
        actual=values(doc,model,('node','author','scope','other'))
        if actual!=[label=='baseline']:raise ValueError('Field assumption attribution differs: '+label)
        rows[label]=actual
    return {'cases':rows,'assumed_content_not_executed_as_physical_truth':True}


def alignment():
    path=ROOT/'artifacts/written-units-v1/einstein-1905.json';source=json.loads(path.read_text(encoding='utf-8'))
    inventory=json.loads((ROOT/'reports/written-units-v1.json').read_text(encoding='utf-8'))
    if hashlib.sha256(path.read_bytes()).hexdigest()!=inventory['works']['einstein-1905']['units_sha256']:raise ValueError('Field source inventory differs')
    rows=[]
    for index in (153,154):
        unit=next(u for u in source['units'] if u['id']==f'einstein-1905:u{index:04}')
        common=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],definitions=['s5t','s5u','s5v','s5w','s5x','s5y','s5z'],status='partial_explicit_reading',full_semantic_equivalence=False)
        if hashlib.sha256(unit['text'].encode('utf-8')).hexdigest()!=unit['text_sha256']:raise ValueError('Field source text differs')
        if index==153:
            start=unit['text'].index('mögen');rows.append(dict(common,start=start,end=len(unit['text']),source=unit['text'][start:]))
        for mid in unit['math_ids']:
            m=next(m for m in source['math'] if m['id']==mid)
            if hashlib.sha256(m['mathml'].encode('utf-8')).hexdigest()!=m['sha256']:raise ValueError('Field source math differs')
            rows.append(dict(common,math_id=mid,math_sha256=m['sha256']))
    # Independently retain the derivative order in the pinned MathML table.
    m=next(m for m in source['math'] if m['id']=='M0287');ns='{http://www.w3.org/1998/Math/MathML}'
    fractions=[]
    for row in ET.fromstring(m['mathml']).iter(ns+'mtr'):
        for cell in row:
            for fraction in cell.iter(ns+'mfrac'):
                pair=tuple(''.join(node.itertext()) for node in fraction)
                if pair!=('1','V'):fractions.append(pair)
    expected=[('∂X','∂t'),('∂N','∂y'),('∂M','∂z'),('∂L','∂t'),('∂Y','∂z'),('∂Z','∂y'),
        ('∂Y','∂t'),('∂L','∂z'),('∂N','∂x'),('∂M','∂t'),('∂Z','∂x'),('∂X','∂z'),
        ('∂Z','∂t'),('∂M','∂x'),('∂L','∂y'),('∂N','∂t'),('∂X','∂y'),('∂Y','∂x')]
    if fractions!=expected:raise ValueError('Pinned six derivative equations differ')
    return {'segments':rows,'source_derivative_order':[list(p) for p in fractions],
        'electric_magnetic_force_and_vacuum_concepts_unwritten':True,'divergence_conditions_not_added':True,'facsimile_review':False,'verified_full_units':0}


def build_report():
    documents={}
    for builder,name in ((generic_composed,'field-equations'),(composed,'einstein-field-equations')):
        text,basis=builder();doc=parse(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text or json.loads((ROOT/('data/'+name+'-basis-v1.json')).read_text(encoding='utf-8'))!=basis:raise ValueError('Stored field artifacts differ')
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Field roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis)
    paths=list(documents)+['data/field-equations-basis-v1.json','data/einstein-field-equations-basis-v1.json',PARENT,
        'scripts/compose_field_equations.py','scripts/check_field_equations.py','scripts/check_tau_differential.py',
        'noema/discourse.py','noema/finite_semantics.py','noema/polynomial_proofs.py',
        'artifacts/written-units-v1/einstein-1905.json','reports/written-units-v1.json']
    return {'status':'partial_six_scalar_field_equations','documents':documents,'polynomial_lemmas':polynomial_checks(),
        'partial_slices':slice_checks(),'derivative_bindings':jet_checks(),'six_balances':jet_checks(True),
        'source_bindings':source_checks(),'finite_refusals':finite_refusals(),'attribution':attribution_checks(),
        'alignment':alignment(),'roundtrips':True,'verified_full_units':{'einstein-1905':0,'kant-1784':0},
        'notation_size':{'canonical_source_document_characters':len(text),'added_characters':len(text)-len((ROOT/PARENT).read_text(encoding='utf-8'))},
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args();report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Field report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Field slices, eighteen partials, six balances and source assumption checked')


if __name__=='__main__':main()
