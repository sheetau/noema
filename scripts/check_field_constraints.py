"""Check divergence and derivative transport as explicit extra conditions."""
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
from scripts.check_rod_setup import callbacks
from scripts.check_field_transform import setup, affine_callback, field_values, OPS
from scripts.check_parallel_composition import transform
from scripts.check_field_equations import AXES, DOMAIN, jet_callback
from scripts.check_real_products import assertion
from scripts.check_moving_light_trip import literal
from scripts.compose_limits import call as k, op, both
from scripts.compose_field_constraints import ROOT, CUT, FIELD, POINT, REGION, JET, PARENT, NAMES, NEW_RESIDUALS, OLD_RESIDUALS, composed, generic_composed

REPORT=ROOT/'reports/field-constraints-v1.json'
E=tuple(tuple(F(v,2) for v in row) for row in ((1,2,3,30),(4,2,6,-30),(7,8,-3,-10)))
H=tuple(tuple(F(v,2) for v in row) for row in ((2,5,11,-10),(3,3,13,20),(17,19,-5,-10)))
DECLS='r ja[] '+JET+'.r jb[] '+JET+'.r jc[] '+JET+'.r jd[] '+JET+'.r je[] '+CUT+'.r jf[] '+CUT+'.'


def polynomial_checks():
    beta,ratio='v beta','v ratio';args=['v '+name for name in NAMES]
    old=[k(symbol,*args) for symbol in OLD_RESIDUALS];new=[k(symbol,beta,ratio,*args) for symbol in NEW_RESIDUALS]
    add=lambda a,b:k('ab',a,b);mul=lambda a,b:k('ad',a,b);sub=lambda a,b:add(a,k('ac',b))
    normal=op('e',mul(mul(beta,beta),sub(literal(1),mul(ratio,ratio))),literal(1))
    rows={}
    for index,label in enumerate(('electric_x','electric_y','electric_z','magnetic_x','magnetic_y','magnetic_z','divergence_electric','divergence_magnetic')):
        partners={0:6,3:7,6:0,7:3}
        rhs=mul(beta,add(old[index],mul(ratio,old[partners[index]]))) if index in partners else old[index]
        claim=op('e',new[index],rhs)
        if index not in partners:claim=op('y',normal,claim)
        doc=parse(generic_composed()[0]+assertion('beta ratio '+' '.join(NAMES),claim))
        result=verify_universal(doc,{'ab':'add','ac':'negate','ad':'multiply'},timeout_ms=20000,max_expansion=200000)[0]
        if result['status']!='valid':raise ValueError('Field residual identity not verified: '+label+repr(result))
        rows[label]=result
    return {'identities':rows,'time_coordinate':'u=V*t','normalized_beta_required_for_four_transverse_identities':True,
        'zero_old_eight_residuals_give_zero_new_eight_residuals':True,
        'rational_coefficient_algebra_only_not_actual_real_derivative_chain_rule':True}


def constraints_checks():
    query='q[k s5w[k je[] k ja[] k jb[]]].q[k s6r[k je[] k ja[] k jb[]]].'
    doc=abstract(candidate(composed()[0],DECLS+query),OPS);rows={}
    for label in ('baseline','electric_divergence','magnetic_divergence','invalid_diagonal','missing_curl','zero_light','negative_light','zero_fields'):
        fixture,model=setup(doc);c=fixture.make;e=[list(row) for row in E];h=[list(row) for row in H]
        if label=='electric_divergence':e[0][0]+=1
        if label=='magnetic_divergence':h[2][2]+=1
        if label=='invalid_diagonal':e[0][0]=128;e[2][2]=-129
        if label=='missing_curl':e[0][3]+=1
        if label=='zero_fields':e=h=[[0]*4 for _ in range(3)]
        callbacks(doc,model,{'ja':jet_callback(fixture,e),'jb':jet_callback(fixture,h)})
        model['je']=lambda:c(0 if label=='zero_light' else -5 if label=='negative_light' else 5)
        expected=[label not in ('missing_curl','zero_light','negative_light'),label in ('baseline','zero_fields')]
        actual=values(doc,model,DOMAIN)
        if actual!=expected:raise ValueError('Divergence constraint differs: '+label+repr(actual))
        rows[label]=actual
    return {'cases':rows,'diagonal_partials_not_in_old_six_equations':True,'all_twenty_four_values_checked':True}


def full_jet_checks():
    decls=DECLS+'r jg[] '+FIELD+'.r jh[] '+FIELD+'.r ji[] '+REGION+'.r jj[] '+POINT+'.'
    doc=abstract(candidate(composed()[0],decls+'q[k s6s[k jg[] k jh[] k ji[] k jj[] k ja[] k jb[]]].'),OPS|{'s5t'});rows={}
    for label in ['baseline']+[f'changed_{field}_{i}' for field in ('E','H') for i in range(3)]+['wrong_point','outside_region']:
        fixture,model=setup(doc);c,n=fixture.make,fixture.read;e=[list(row) for row in E];h=[list(row) for row in H]
        if label.startswith('changed_'):
            _,field,i=label.split('_');i=int(i);(e if field=='E' else h)[i][i]+=1
        callbacks(doc,model,{'jg':affine_callback(doc,fixture,'jg',[(*row,0) for row in E]),
            'jh':affine_callback(doc,fixture,'jh',[(*row,0) for row in H]),'ji':lambda *xs:label!='outside_region',
            'jj':lambda role:c((1,2,3,5 if label=='wrong_point' else 4)[AXES.index(role)] if role in AXES else 0),
            'ja':jet_callback(fixture,e),'jb':jet_callback(fixture,h)})
        calls=[]
        def partial(fn,region,point,axis,value):
            coeff=tuple(n(fn(*(c(int(i==j)) for i in range(4)))) for j in range(4));calls.append((coeff,axis))
            return coeff in E+H and tuple(n(point(a)) for a in AXES)==(1,2,3,4) and region(*(point(a) for a in AXES)) and n(value)==coeff[AXES.index(axis)]
        model['s5t']=partial;actual=values(doc,model,DOMAIN)
        if actual!=[label=='baseline']:raise ValueError('Full jet binding differs: '+label)
        if label=='baseline' and len(set(calls))!=24:raise ValueError('Full jet did not use all twenty four partials')
        rows[label]=actual
    return {'cases':rows,'actual_derivative_relation_is_fixture_oracle':True,'six_previously_unused_diagonals_bound_to_same_fields':True}


def transformed_jets(e,h,speed):
    e=[(*row,0) for row in e];h=[(*row,0) for row in h]
    columns=[field_values(e,h,tuple(int(i==j) for i in range(4)),F(speed)) for j in range(4)]
    return ([[columns[j][0][i] for j in range(4)] for i in range(3)],[[columns[j][1][i] for j in range(4)] for i in range(3)])


def chain_checks():
    query='q[k s6w[k je[] k jf[] k ja[] k jb[] k jc[] k jd[]]].q[k s6r[k je[] k jc[] k jd[]]].'
    doc=abstract(candidate(composed()[0],DECLS+query),OPS);rows={}
    labels=['baseline','reverse_speed','zero_speed']+[f'changed_{field}_{i}_{j}' for field in ('E','H') for i in range(3) for j in range(4)]
    for label in labels:
        fixture,model=setup(doc);c=fixture.make;speed=-3 if label=='reverse_speed' else 0 if label=='zero_speed' else 3
        en,hn=transformed_jets(E,H,speed)
        if label.startswith('changed_'):
            _,field,i,j=label.split('_');(en if field=='E' else hn)[int(i)][int(j)]+=1
        callbacks(doc,model,{'ja':jet_callback(fixture,E),'jb':jet_callback(fixture,H),'jc':jet_callback(fixture,en),'jd':jet_callback(fixture,hn)})
        model.update(je=lambda:c(5),jf=lambda:c(speed));actual=values(doc,model,DOMAIN)
        expected=not label.startswith('changed_')
        if actual!=[expected,expected]:raise ValueError('Derivative transformation differs: '+label+repr(actual))
        rows[label]=actual
    return {'cases':rows,'every_new_derivative_mutated_individually':True,'coefficient_transform_not_a_differentiability_proof':True}


def counterexample_checks():
    query='q[k s5w[k je[] k ja[] k jb[]]].q[k s6r[k je[] k ja[] k jb[]]].q[k s6w[k je[] k jf[] k ja[] k jb[] k jc[] k jd[]]].q[k s6r[k je[] k jc[] k jd[]]].'
    doc=abstract(candidate(composed()[0],DECLS+query),OPS);rows={};zero=[[0]*4 for _ in range(3)]
    for label in ('electric','magnetic','zero_speed'):
        fixture,model=setup(doc);c=fixture.make;e=[row.copy() for row in zero];h=[row.copy() for row in zero]
        (h if label=='magnetic' else e)[0][0]=1;speed=0 if label=='zero_speed' else 3;en,hn=transformed_jets(e,h,speed)
        callbacks(doc,model,{'ja':jet_callback(fixture,e),'jb':jet_callback(fixture,h),'jc':jet_callback(fixture,en),'jd':jet_callback(fixture,hn)})
        model.update(je=lambda:c(5),jf=lambda:c(speed));actual=values(doc,model,DOMAIN)
        if actual!=[True,False,True,False]:raise ValueError('Missing-divergence counterexample not excluded')
        rows[label]=actual
    return {'cases':rows,'counterexamples_excluded_by_old_divergence_not_by_breaking_transform':True}


def connection_checks():
    decls=DECLS+'r jg[] '+FIELD+'.r jh[] '+FIELD+'.r ji[] '+REGION+'.r jj[] '+POINT+'.'
    query='q[k s6x[k jg[] k jh[] k ji[] k jj[] k je[] k jf[] k ja[] k jb[] k jc[] k jd[]]].'
    doc=abstract(candidate(composed()[0],decls+query),OPS|{'s6s','s6w','s46'});rows={}
    newpoint=(F(1),F(2),F(-1),F(1));oldpoint=tuple(transform(newpoint,F(-3)));en,hn=transformed_jets(E,H,3)
    for label in ('baseline','wrong_inverse_map','swapped_old_jets','swapped_new_jets','outside_region','missing_chain'):
        fixture,model=setup(doc);c,n=fixture.make,fixture.read
        callbacks(doc,model,{'jg':affine_callback(doc,fixture,'jg',[(*row,0) for row in E]),'jh':affine_callback(doc,fixture,'jh',[(*row,0) for row in H]),
            'ji':lambda *xs:label!='outside_region' and n(xs[0])>0,
            'jj':lambda role:c(newpoint[AXES.index(role)] if role in AXES else 0),
            'ja':jet_callback(fixture,H if label=='swapped_old_jets' else E),'jb':jet_callback(fixture,E if label=='swapped_old_jets' else H),
            'jc':jet_callback(fixture,hn if label=='swapped_new_jets' else en),'jd':jet_callback(fixture,en if label=='swapped_new_jets' else hn)})
        model.update(je=lambda:c(5),jf=lambda:c(3))
        sort=next(d['result'] for d in doc['declarations'] if d['name']=='s46')
        def map_point(light,speed,point):
            coordinates=transform(tuple(n(point(a)) for a in AXES),n(speed),n(light))
            if label=='wrong_inverse_map':coordinates[0]+=1
            return FunctionValue(tuple(sort['parameters']),sort['result'],lambda role:c(coordinates[AXES.index(role)] if role in AXES else 0))
        model['s46']=map_point
        matrix=lambda jet:tuple(tuple(n(jet(component,axis)) for axis in AXES) for component in AXES[:3])
        def field_matrix(field):return tuple(tuple(n(field(a)(*(c(int(i==j)) for i in range(4)))) for j in range(4)) for a in AXES[:3])
        calls=[]
        def bind(e,h,region,point,ej,hj):
            em,hm=field_matrix(e),field_matrix(h);p=tuple(n(point(a)) for a in AXES);calls.append(p)
            expected=oldpoint if (em,hm)==(E,H) else newpoint
            return (em,hm) in ((E,H),(tuple(map(tuple,en)),tuple(map(tuple,hn)))) and p==expected and region(*(point(a) for a in AXES)) and matrix(ej)==em and matrix(hj)==hm
        model['s6s']=bind
        model['s6w']=lambda light,speed,e,h,new_e,new_h:label!='missing_chain' and (n(light),n(speed))==(5,3) and (matrix(e),matrix(h))==(E,H) and (matrix(new_e),matrix(new_h))==(tuple(map(tuple,en)),tuple(map(tuple,hn)))
        actual=values(doc,model,DOMAIN)
        if actual!=[label=='baseline']:raise ValueError('Same-point derivative connection differs: '+label+repr(actual))
        if label=='baseline' and set(calls)!={oldpoint,newpoint}:raise ValueError('Both coordinate points were not used')
        rows[label]=actual
    return {'cases':rows,'old_point_is_inverse_image_of_same_new_point':True,
        'derivative_and_chain_relations_are_explicit_fixture_oracles':True}


def finite_refusals():
    decls='r ja[] '+FIELD+'.r jb[] '+FIELD+'.r jc[] '+REGION+'.r jd[] '+POINT+'.r je[] '+CUT+'.r jf[] '+CUT+'.'
    queries={'local_full_constraints':'k s6y[k ja[] k jb[] k jc[] k jd[] k je[]]',
        'all_region_constraints':'k s6z[k ja[] k jb[] k jc[] k je[]]',
        'actual_derivatives_and_chain_rule_premise':'k s72[k ja[] k jb[] k jc[] k jd[] k je[] k jf[]]'};rows={}
    for label,query in queries.items():
        doc=abstract(candidate(composed()[0],decls+'q['+query+'].'),OPS);fixture,model=setup(doc);c=fixture.make
        callbacks(doc,model,{'ja':affine_callback(doc,fixture,'ja',[(*row,0) for row in E]),'jb':affine_callback(doc,fixture,'jb',[(*row,0) for row in H]),
            'jc':lambda *xs:True,'jd':lambda role:c(0)})
        model.update(je=lambda:c(5),jf=lambda:c(3))
        try:values(doc,model,DOMAIN)
        except ValueError as error:
            if 'Cannot finitely quantify the rational number domain' not in str(error):raise
            rows[label]={'refused':True,'reason':str(error)}
        else:raise ValueError('Finite evaluation replaced full derivative constraints')
    return rows


def alignment():
    path=ROOT/'artifacts/written-units-v1/einstein-1905.json';source=json.loads(path.read_text(encoding='utf-8'))
    inventory=json.loads((ROOT/'reports/written-units-v1.json').read_text(encoding='utf-8'))
    if hashlib.sha256(path.read_bytes()).hexdigest()!=inventory['works']['einstein-1905']['units_sha256']:raise ValueError('Constraint source inventory differs')
    rows=[]
    for index,mid in ((157,'M0291'),(158,'M0292')):
        unit=next(u for u in source['units'] if u['id']==f'einstein-1905:u{index:04}');m=next(m for m in source['math'] if m['id']==mid)
        if hashlib.sha256(unit['text'].encode('utf-8')).hexdigest()!=unit['text_sha256'] or hashlib.sha256(m['mathml'].encode('utf-8')).hexdigest()!=m['sha256']:raise ValueError('Constraint source hash differs')
        rows.append(dict(unit=unit['id'],unit_sha256=unit['text_sha256'],math_id=mid,math_sha256=m['sha256'],definitions=['s6q','s6r','s6s','s6t','s6u','s6v','s6w','s6x','s6y','s6z','s72','s73'],
            status='explicit_interpretive_annotation',full_semantic_equivalence=False))
    return {'segments':rows,'additional_mathematical_conditions_not_explicit_source_words':True,
        'previous_author_attribution_not_rewritten':True,'new_source_text_ranges':0,'verified_full_units':0}


def build_report():
    documents={}
    for builder,name in ((generic_composed,'field-constraints'),(composed,'einstein-field-constraints')):
        text,basis=builder();doc=parse(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text or json.loads((ROOT/('data/'+name+'-basis-v1.json')).read_text(encoding='utf-8'))!=basis:raise ValueError('Stored field constraints differ')
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Field constraint roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis)
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    if doc['statements']!=parent['statements']:raise ValueError('Author statements were changed by mathematical annotation')
    paths=list(documents)+['data/field-constraints-basis-v1.json','data/einstein-field-constraints-basis-v1.json',PARENT,
        'scripts/compose_field_constraints.py','scripts/check_field_constraints.py','scripts/check_field_transform.py','scripts/check_field_equations.py',
        'scripts/check_tau_differential.py','noema/discourse.py','noema/finite_semantics.py','noema/polynomial_proofs.py',
        'artifacts/written-units-v1/einstein-1905.json','reports/written-units-v1.json']
    return {'status':'explicit_extra_divergence_and_derivative_transport_conditions','documents':documents,
        'residual_identities':polynomial_checks(),'constraints':constraints_checks(),'full_jet_binding':full_jet_checks(),
        'chain_coefficients':chain_checks(),'counterexamples':counterexample_checks(),'same_point_connection':connection_checks(),'finite_refusals':finite_refusals(),
        'alignment':alignment(),'roundtrips':True,'author_statements_unchanged':True,
        'verified_full_units':{'einstein-1905':0,'kant-1784':0},
        'notation_size':{'canonical_source_document_characters':len(text),'added_characters':len(text)-len((ROOT/PARENT).read_text(encoding='utf-8'))},
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args();report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Field constraint report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Divergence, all derivatives, residual identities and counterexample exclusion checked')


if __name__=='__main__':main()
