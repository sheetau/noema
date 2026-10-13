"""Verify group-law distinctions and the action of signed parallel boosts."""
import argparse
from fractions import Fraction as F
import hashlib
from itertools import permutations
import json

from noema.finite_semantics import FunctionValue
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
from scripts.check_parallel_composition import transform
from scripts.compose_transform_group import ROOT, CUT, VECTOR, composed, generic_composed, k, op, both, v

REPORT=ROOT/'reports/transform-group-v1.json'


def finite_group_checks():
    text=generic_composed()[0]+'r da[a] c.r db[a a] a.r dc[] a.r dd[a] a.'
    text+='q[k s4t[p da p db]].q[k s4u[p da p db]].q[k s4v[p da p db k dc[]]].q[k s4w[p da p db k dc[] p dd]].q[k s4x[p da p db k dc[] p dd]].'
    doc=parse(text);rows={}
    loop=((0,1,2,3,4),(1,0,3,4,2),(2,4,0,1,3),(3,2,4,0,1),(4,3,1,2,0))
    perms=tuple(permutations(range(3)));index={p:i for i,p in enumerate(perms)}
    def inverse_perm(a):return index[tuple(perms[a].index(i) for i in range(3))]
    cases={
        'cyclic_three':(3,lambda x:True,lambda a,b:(a+b)%3,0,lambda a:(-a)%3,[True]*5),
        'noncommutative_permutations':(6,lambda x:True,lambda a,b:index[tuple(perms[a][perms[b][i]] for i in range(3))],0,inverse_perm,[True]*5),
        'empty_carrier':(3,lambda x:False,lambda a,b:(a+b)%3,0,lambda a:(-a)%3,[True,True,False,True,False]),
        'not_closed':(3,lambda x:x<2,lambda a,b:(a+b)%3,0,lambda a:(-a)%3,[False,True,True,False,False]),
        'nonassociative_loop':(5,lambda x:True,lambda a,b:loop[a][b],0,lambda a:a,[True,False,True,True,False]),
        'left_projection':(3,lambda x:True,lambda a,b:a,0,lambda a:a,[True,True,False,False,False]),
        'wrong_identity':(3,lambda x:True,lambda a,b:(a+b)%3,1,lambda a:(-a)%3,[True,True,False,False,False]),
        'wrong_inverse':(3,lambda x:True,lambda a,b:(a+b)%3,0,lambda a:a,[True,True,True,False,False]),
        'inverse_outside_carrier':(3,lambda x:x<2,lambda a,b:(a+b)%2 if a<2 and b<2 else 0,0,lambda a:2,[True,True,True,False,False]),
    }
    for label,(count,inside,operation,identity,inverse,expected) in cases.items():
        model={'da':inside,'db':operation,'dc':lambda:identity,'dd':inverse}
        actual=values(doc,model,tuple(range(count)))
        if actual!=expected:raise ValueError('Group laws differ: '+label+repr(actual))
        if label=='noncommutative_permutations' and not any(operation(a,b)!=operation(b,a) for a in range(count) for b in range(count)):raise ValueError('Noncommutative example became commutative')
        rows[label]=actual
    return {'cases':rows,'column_order':['closed','associative','two_sided_identity','two_sided_inverse','group'],
        'closure_alone_does_not_establish_group':True,'commutativity_not_required':True,'no_physical_primitives_used':True}


def polynomial_checks():
    V,a,b,c,ab,bc,left,right=map(v,('light','first','second','third','firstpair','secondpair','left','right'))
    zero=literal(0);mul=lambda x,y:k('ad',x,y);eq=lambda x,y:op('e',x,y)
    bound=lambda x:both(k('aa',zero,V),k('aa',mul(x,x),mul(V,V)))
    compose=lambda x,y,z:k('s3f',V,x,y,z)
    beta,otherbeta=map(v,('beta','otherbeta'));x,t=map(v,('x','time'))
    probe1=k('srb',V,a,beta,literal(1),zero,zero,zero,literal(1),x,zero,zero,t)
    probe2=k('srb',V,b,otherbeta,literal(1),zero,zero,zero,literal(1),x,zero,zero,t)
    claims={
        'composition_closed_on_signed_subluminal_speeds':assertion('light first second third',op('y',both(bound(a),bound(b),compose(a,b,c)),bound(c))),
        'composition_is_associative':assertion('light first second third firstpair secondpair left right',op('y',
            both(bound(a),bound(b),bound(c),compose(a,b,ab),compose(b,c,bc),compose(ab,c,left),compose(a,bc,right)),eq(left,right))),
        'zero_is_a_two_sided_identity':assertion('light first',op('y',bound(a),both(compose(a,zero,a),compose(zero,a,a)))),
        'negative_speed_is_a_two_sided_inverse_in_same_domain':assertion('light first',op('y',bound(a),both(bound(k('ac',a)),compose(a,k('ac',a),zero),compose(k('ac',a),a,zero)))),
        'same_unit_time_probe_determines_speed':assertion('light first second beta otherbeta x time',op('y',both(probe1,probe2),eq(a,b))),
        'positive_only_domain_contains_every_inverse':assertion('',k('aa',zero,literal(-3))),
        'zero_event_alone_determines_speed':assertion('',op('y',both(
            k('srb',*(literal(x) for x in (5,3,F(5,4),1,0,0,0,0,0,0,0,0))),
            k('srb',*(literal(x) for x in (5,4,F(5,3),1,0,0,0,0,0,0,0,0)))),eq(literal(3),literal(4)))),
    }
    rejected={'positive_only_domain_contains_every_inverse','zero_event_alone_determines_speed'}
    rows={};text=composed()[0]
    for name,claim in claims.items():
        doc=candidate(text,claim);doc['declarations']=[d for d in doc['declarations'] if d['name'] in {'aa','ab','ac','ad','sra','srb','s3f'}]
        result=verify_universal(doc,MEANINGS,timeout_ms=20000)[0]
        if result['status']!=('invalid' if name in rejected else 'valid'):raise ValueError('Group algebra differs: '+name+repr(result))
        rows[name]=result
    return {'claims':rows,'rational_polynomial_lemmas_only':True,'all_real_cut_field_and_root_laws_proved':False}


def coordinate_checks():
    text=composed()[0];query='r ja[] '+VECTOR+'.r jb[] '+VECTOR+'.r jc[] '+CUT+'.r jd[] '+CUT+'.'
    query+='q[k s45[k tc[] k jc[]]].q[k s5a[k tc[] k jc[] k jd[] k ja[]]].q[k s5b[k tc[] k ja[]]].q[k s5c[k tc[] k jc[] k ja[]]].'
    query+='q[k sho[k shx[] k s46[k tc[] k jc[] k ja[]] k jb[] p sca]].'
    doc=abstract(candidate(text,query),ARITHMETIC|{'sjt','sky','szi'});rows={}
    vector_sort=next(d for d in doc['declarations'] if d['name']=='ja')['result']
    for label,(speed,moving,point) in {
        'ordinary':(3,3,(7,3,4,2)),'negative':(-3,4,(7,3,4,2)),
        'zero_speed':(0,3,(7,3,4,2)),'inverse_pair':(3,-3,(7,3,4,2)),
        'zero_event':(3,4,(0,0,0,0)),'time_probe':(4,3,(0,0,0,1)),
        'wrong_time':(3,3,(7,3,4,2)),'wrong_transverse':(3,3,(7,3,4,2)),
        'extra_role_values':(3,3,(7,3,4,2)),
    }.items():
        fixture=ConstructedCuts();model=guarded(doc);model_arithmetic(fixture,model)
        model['szi']=lambda choose,left,right:left if choose else right
        expected=transform(point,F(speed));expected[3]+=int(label=='wrong_time');expected[1]+=int(label=='wrong_transverse')
        def vector(row,extra):return FunctionValue(tuple(vector_sort['parameters']),vector_sort['result'],lambda role:fixture.make(row[('x','y','z','t').index(role)] if role in ('x','y','z','t') else extra))
        for symbol,value in {'yn':'x','yo':'y','yp':'z','zc7':'t'}.items():model[symbol]=lambda value=value:value
        model.update(tc=lambda:fixture.make(5),jc=lambda:fixture.make(speed),jd=lambda:fixture.make(moving),
            ja=lambda:vector(point,99 if label=='extra_role_values' else 0),jb=lambda:vector(expected,17))
        actual=values(doc,model,('x','y','z','t','extra'))
        expected_truth=[True]*4+[label not in ('wrong_time','wrong_transverse')]
        if actual!=expected_truth:raise ValueError('Group action differs: '+label+repr(actual))
        rows[label]=actual
    return {'cases':rows,'column_order':['speed_domain','composition_instance','identity_instance','inverse_instance','expected_four_coordinates'],
        'coordinate_equality_not_function_implementation_identity':True,'only_four_roles_are_coordinate_components':True,
        'arithmetic_and_conditional_cut_selection_are_explicit_oracles':True}


def domain_checks():
    doc=abstract(candidate(composed()[0],'r ja[] '+CUT+'.r jb[] '+CUT+'.q[k s45[k ja[] k jb[]]].'),ARITHMETIC)
    rows={}
    for label,(light,speed,expected) in {
        'positive':(5,3,True),'negative':(5,-3,True),'zero':(5,0,True),
        'near_positive_boundary':(1,F(999,1000),True),'near_negative_boundary':(1,F(-999,1000),True),
        'positive_boundary':(5,5,False),'negative_boundary':(5,-5,False),
        'outside':(5,6,False),'zero_light':(0,0,False),'negative_light':(-5,3,False),
        'invalid_cut':(128,3,False),
    }.items():
        fixture=ConstructedCuts();model=guarded(doc);fixture.arithmetic(model)
        model.update(ja=lambda:fixture.make(light),jb=lambda:fixture.make(speed))
        actual=values(doc,model,('object',))
        if actual!=[expected]:raise ValueError('Signed group domain differs: '+label)
        rows[label]=actual
    return {'cases':rows,'both_signs_and_zero_retained':True,'light_speed_boundaries_excluded':True}


def quantification_checks():
    rows={}
    for symbol in ('s47','s5d','s5e'):
        args='k tc[]'+(' k tc[] k tc[]' if symbol=='s5d' else '')
        doc=abstract(candidate(composed()[0],'q[k '+symbol+'['+args+']].'),ARITHMETIC|{'sjt','sky','szi'})
        fixture=ConstructedCuts();model=guarded(doc);model_arithmetic(fixture,model);model['szi']=lambda choose,left,right:left if choose else right
        model.update(tc=lambda:fixture.make(5),yn=lambda:'x',yo=lambda:'y',yp=lambda:'z',zc7=lambda:'t')
        try:values(doc,model,('x','y','z','t'))
        except SemanticError as error:
            if str(error)!='Cannot finitely quantify the rational number domain':raise
            rows[symbol]=str(error)
        else:raise ValueError('Unbounded group or function domain was finitely enumerated')
    return {'rejections':rows,'real_group_and_function_equality_not_sampled':True}


def attribution_checks():
    doc=parse(composed()[0]);doc['statements']=doc['statements'][-1:];rows={}
    for label in ('baseline','wrong_author','wrong_scope','wrong_context','reversed_inference','closure_replaces_group'):
        model=guarded(doc)
        for symbol,value in {'zlu':'group','rd':'author','zlq':'scope','ri':'text'}.items():model[symbol]=lambda value=value:value
        def attributed(node,author,premise,conclusion,scope,context):
            names=tuple(json.loads(d.syntax)['symbol'] for d in (premise,conclusion))
            expected=('s5f','s5g') if label=='reversed_inference' else ('s5g','s5g') if label=='closure_replaces_group' else ('s5g','s5f')
            return (node,author,scope,context)==('group','other' if label=='wrong_author' else 'author','other' if label=='wrong_scope' else 'scope','other' if label=='wrong_context' else 'text') and names==expected
        model['zc']=attributed;actual=values(doc,model,('group','author','scope','other'))
        if actual!=[label=='baseline']:raise ValueError('Group attribution differs: '+label)
        rows[label]=actual
    return {'cases':rows,'quoted_claim_not_evaluated_as_global_truth':True,'closure_alone_not_certified_as_sufficient':True}


def alignment():
    path=ROOT/'artifacts/written-units-v1/einstein-1905.json';source=json.loads(path.read_text(encoding='utf-8'))
    inventory=json.loads((ROOT/'reports/written-units-v1.json').read_text(encoding='utf-8'))
    if hashlib.sha256(path.read_bytes()).hexdigest()!=inventory['works']['einstein-1905']['units_sha256']:raise ValueError('Group source inventory differs')
    unit=next(u for u in source['units'] if u['id']=='einstein-1905:u0149')
    if hashlib.sha256(unit['text'].encode('utf-8')).hexdigest()!=unit['text_sha256']:raise ValueError('Group source text differs')
    text=unit['text'];first=text.index('man sieht');dash=text.index('—');last=text.rindex('—')+1
    common=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],definitions=['s44','s45','s46','s47','s5a','s5b','s5c','s5d','s5e','s5f','s5g'],status='partial_explicit_reading',full_semantic_equivalence=False)
    return {'segments':[dict(common,start=a,end=b,source=text[a:b]) for a,b in ((first,dash),(last,len(text)))],
        'verified_full_units':0,'necessity_parenthesis_unwritten':True,'alternative_derivation_modality_unwritten':True,
        'group_expanded_as_modern_axioms_explicit':True,'full_facsimile_review':False}


def build_report():
    documents={}
    for compose,basispath in ((generic_composed,'data/group-laws-basis-v1.json'),(composed,'data/transform-group-basis-v1.json')):
        text,basis=compose();doc=parse(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text or json.loads((ROOT/basispath).read_text(encoding='utf-8'))!=basis:raise ValueError('Stored group artifacts differ')
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Group roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis)
    paths=list(documents)+['data/group-laws-basis-v1.json','data/transform-group-basis-v1.json','examples/v014/einstein-parallel-composition.noema',
        'scripts/compose_transform_group.py','scripts/check_transform_group.py','scripts/check_parallel_composition.py',
        'scripts/check_angle_composition.py','scripts/check_tau_differential.py','scripts/check_transverse_time.py',
        'noema/discourse.py','noema/finite_semantics.py','noema/polynomial_proofs.py',
        'artifacts/written-units-v1/einstein-1905.json','reports/written-units-v1.json']
    return {'status':'partial_parallel_transform_group_with_generic_group_laws','documents':documents,
        'finite_groups':finite_group_checks(),'polynomial_lemmas':polynomial_checks(),'coordinate_action':coordinate_checks(),'speed_domain':domain_checks(),
        'unbounded_quantification':quantification_checks(),'attribution':attribution_checks(),'alignment':alignment(),'roundtrips':True,
        'verified_full_units':{'einstein-1905':0,'kant-1784':0},
        'notation_size':{'canonical_source_document_characters':len(text),'added_characters':len(text)-len((ROOT/'examples/v014/einstein-parallel-composition.noema').read_text(encoding='utf-8'))},
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args();report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Transform group report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Generic groups, signed composition, four-coordinate action and attribution checked')


if __name__=='__main__':main()
