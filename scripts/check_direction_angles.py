"""Check inverse branches, oriented angles and zero-vector boundaries."""
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
from scripts.compose_direction_angles import ROOT, CUT, composed, k, op, both, v

REPORT=ROOT/'reports/direction-angles-v1.json'


def polynomial_checks():
    x,y,r,c,s,a,b,R,p,q,scale=map(v,('x','y','radius','cosine','sine','otherx','othery','otherradius','othercos','othersin','scale'))
    zero=literal(0);mul=lambda a,b:k('ad',a,b);neg=lambda a:k('ac',a)
    direction=k('szx',x,y,r,c,s);inverse=k('szy',x,y,c,s);principal=k('szz',x,y,c,s)
    params='x y radius otherx othery otherradius cosine sine'
    oriented=k('s2a',x,y,r,a,b,R,c,s);unsigned=k('s2b',x,y,r,a,b,R,c,s)
    claims={
        'direction_gives_positive_norm':assertion('x y radius cosine sine',op('y',direction,k('szk',r,x,y))),
        'positive_x_direction_is_principal_inverse':assertion('x y radius cosine sine',op('y',both(direction,k('aa',zero,x)),principal)),
        'negative_x_direction_is_inverse_but_not_principal':assertion('x y radius cosine sine',op('y',both(direction,k('aa',x,zero)),both(inverse,op('u',principal)))),
        'positive_scale_keeps_direction':assertion('x y radius cosine sine scale',op('y',both(direction,k('aa',zero,scale)),k('szx',mul(scale,x),mul(scale,y),mul(scale,r),c,s))),
        'negating_both_components_keeps_principal_ratio':assertion('x y cosine sine',op('z',principal,k('szz',neg(x),neg(y),c,s))),
        'principal_inverse_pair_is_unique':assertion('x y cosine sine othercos othersin',op('y',both(principal,k('szz',x,y,p,q)),both(op('e',c,p),op('e',s,q)))),
        'swapping_vectors_reverses_oriented_sine':assertion(params,op('z',oriented,k('s2a',a,b,R,x,y,r,c,neg(s)))),
        'swapping_vectors_preserves_unsigned_angle':assertion(params,op('z',unsigned,k('s2b',a,b,R,x,y,r,c,s))),
        'vertical_direction_is_valid':assertion('',k('szx',*(literal(n) for n in (0,5,5,0,1)))),
        'vertical_ratio_has_an_inverse':assertion('',k('szy',*(literal(n) for n in (0,5,0,1)))),
        'zero_vector_has_a_direction':assertion('',k('szx',*(literal(n) for n in (0,0,0,1,0)))),
        'principal_value_always_matches_actual_direction':assertion('',op('y',k('szz',*(literal(n) for n in (-3,4,F(3,5),F(-4,5)))),k('szx',*(literal(n) for n in (-3,4,5,F(3,5),F(-4,5)))))),
    }
    text=composed()[0];rows={}
    for name,claim in claims.items():
        doc=candidate(text,claim)
        doc['declarations']=[d for d in doc['declarations'] if d['name'] in {'aa','ab','ac','ad','szk','szw','szx','szy','szz','s2a','s2b'}]
        result=verify_universal(doc,MEANINGS,timeout_ms=20000)[0]
        rejected={'vertical_ratio_has_an_inverse','zero_vector_has_a_direction','principal_value_always_matches_actual_direction'}
        if result['status']!=('invalid' if name in rejected else 'valid'):raise ValueError('Angle algebra differs: '+name+repr(result))
        rows[name]=result
    return {'claims':rows,'rational_polynomial_lemmas_only':True,'analytic_arctangent_or_radian_measure_constructed':False}


CASES={
    # x, y, radius, cosine, sine, first vector's signed axial component
    'first_quadrant':((3,4,5,F(3,5),F(4,5),2),[True]*6),
    'scaled_vector':((6,8,10,F(3,5),F(4,5),2),[True]*6),
    'negative_x_direction':((-3,4,5,F(-3,5),F(4,5),2),[True,True,False,True,True,True]),
    'negative_x_principal':((-3,4,5,F(3,5),F(-4,5),2),[False,True,True,False,False,True]),
    'negative_y_direction':((3,-4,5,F(3,5),F(-4,5),2),[True,True,True,True,False,True]),
    'negative_y_unsigned':((3,-4,5,F(3,5),F(4,5),2),[False,False,False,False,True,True]),
    'vertical':((0,5,5,0,1,2),[True,False,False,True,True,True]),
    'opposite_axis':((-5,0,5,-1,0,2),[True,True,False,True,True,True]),
    'zero_vector':((0,0,0,1,0,2),[False,False,False,False,False,True]),
    'zero_frame_velocity':((3,4,5,F(3,5),F(4,5),0),[True,True,True,False,False,True]),
    'negative_frame_oriented':((3,4,5,F(-3,5),F(-4,5),-2),[False,True,False,True,False,True]),
    'negative_frame_unsigned':((3,4,5,F(-3,5),F(4,5),-2),[False,False,False,False,True,True]),
    'not_unit_circle':((3,4,5,3,4,2),[False]*6),
    'negative_radius':((3,4,-5,F(3,5),F(4,5),2),[False,True,True,False,False,True]),
    'wrong_radius':((3,4,6,F(3,5),F(4,5),2),[False,True,True,False,False,True]),
}


def angle_checks():
    query=''.join('r j'+c+'[] '+CUT+'.' for c in 'abcdefg')
    query+='q[k s2d[k ja[] k jb[] k jc[] k jd[] k je[]]].q[k s2e[k ja[] k jb[] k jd[] k je[]]].q[k s2f[k ja[] k jb[] k jd[] k je[]]].'
    pair='k jf[] k bb[n p a b] k jg[] k ja[] k jb[] k jc[] k jd[] k je[]'
    query+='q[k s2g['+pair+']].q[k s2h['+pair+']].q[k s2j[k s2i[k jd[] k je[]]]].'
    doc=abstract(candidate(composed()[0],query),ARITHMETIC|{'szi'});rows={}
    for label,(args,expected) in CASES.items():
        fixture=ConstructedCuts();model=guarded(doc);fixture.arithmetic(model)
        model['szi']=lambda choose,left,right:left if choose else right
        for symbol,value in zip(('j'+c for c in 'abcdefg'),(*args,abs(args[-1]))):model[symbol]=lambda value=value:fixture.make(value)
        actual=values(doc,model,('object',))
        if actual!=expected:raise ValueError('Angle branches differ: '+label+repr(actual))
        rows[label]=actual
    return {'cases':rows,'constructed_rational_cut_and_selector_oracles':True,'circle_pair_preserves_orientation_but_not_winding_count':True}


def source_checks():
    doc=abstract(candidate(composed()[0],'q[t[k s2k[]][k ri[]]].q[t[k s2l[]][k ri[]]].q[t[k s2m[]][k ri[]]].'),ARITHMETIC|{'sky','syw','szt'})
    angle_type=next(d['result'] for d in doc['declarations'] if d['name']=='zkt');rows={}
    for label in ('first_quadrant','negative_x_direction','negative_x_principal','negative_y_direction','negative_y_unsigned','vertical','zero_vector','zero_frame_velocity','negative_frame_unsigned','wrong_motion_scope','wrong_component_context'):
        args=CASES[label if label in CASES else 'first_quadrant'][0]
        x,y,r,cosine,sine,speed=args;fixture=ConstructedCuts();c=fixture.make;n=fixture.read;model=guarded(doc);fixture.arithmetic(model)
        model.update(zkc=lambda:c(x),zkd=lambda:c(y),zkq=lambda:c(r),zb7=lambda:c(speed),ri=lambda:'text',zke=lambda:'motion',
            sky=lambda value:square_root(fixture,value),syw=lambda:label!='wrong_motion_scope',
            szt=lambda value,setting:n(value)==r and setting==('other' if label=='wrong_component_context' else 'motion'),
            zkt=lambda:FunctionValue(tuple(angle_type['parameters']),angle_type['result'],lambda choose:c(cosine if choose else sine)))
        expected=([False]*3 if label.startswith('wrong_') else [CASES[label][1][i] for i in (1,2,4)])
        actual=values(doc,model,('object',))
        if actual!=expected:raise ValueError('Source angle readings differ: '+label+repr(actual))
        rows[label]=actual
    return {'cases':rows,'existing_motion_and_component_conditions_are_explicit_oracles':True,
        'principal_branch_not_silently_attributed':True,'geometric_angle_and_inverse_ratio_not_globally_identical':True}


def attribution_checks():
    doc=parse(composed()[0]);doc['statements']=doc['statements'][-2:];rows={}
    for label in ('baseline','wrong_author','wrong_scope','wrong_context','principal_substituted','readings_swapped'):
        model=guarded(doc)
        for symbol,value in {'zku':'ratio','zkv':'geometry','rd':'author','zkf':'scope','ri':'text'}.items():model[symbol]=lambda value=value:value
        def attributed(node,author,body,scope,context):
            target='s2k' if node=='ratio' else 's2m'
            if label=='principal_substituted' and node=='ratio':target='s2l'
            if label=='readings_swapped':target='s2m' if node=='ratio' else 's2k'
            return (author,scope,context)==('other' if label=='wrong_author' else 'author','other' if label=='wrong_scope' else 'scope','other' if label=='wrong_context' else 'text') and json.loads(body.syntax)['symbol']==target
        model['uh']=attributed;actual=values(doc,model,('ratio','geometry','author','scope','other'))
        expected=[label=='baseline',label in ('baseline','principal_substituted')]
        if actual!=expected:raise ValueError('Angle attribution differs')
        rows[label]=actual
    return {'cases':rows,'quoted_angle_constraints_are_not_evaluated_or_endorsed':True}


def alignment():
    path=ROOT/'artifacts/written-units-v1/einstein-1905.json';artifact=json.loads(path.read_text(encoding='utf-8'))
    inventory=json.loads((ROOT/'reports/written-units-v1.json').read_text(encoding='utf-8'))
    if hashlib.sha256(path.read_bytes()).hexdigest()!=inventory['works']['einstein-1905']['units_sha256']:raise ValueError('Pinned angle source differs')
    rows=[]
    for index,defs in ((138,['s2e','s2k']),(139,['s2h','s2m'])):
        uid=f'einstein-1905:u{index:04}';unit=next(u for u in artifact['units'] if u['id']==uid)
        if hashlib.sha256(unit['text'].encode('utf-8')).hexdigest()!=unit['text_sha256']:raise ValueError('Angle source text differs')
        end=unit['text'].index(' Nach einfacher Rechnung') if index==139 else len(unit['text'])
        common=dict(unit=uid,unit_sha256=unit['text_sha256'],definitions=defs,status='partial_explicit_reading',full_semantic_equivalence=False)
        rows.append(dict(common,start=0,end=end,source=unit['text'][:end]))
        for mid in unit['math_ids']:
            item=next(m for m in artifact['math'] if m['id']==mid)
            if hashlib.sha256(item['mathml'].encode('utf-8')).hexdigest()!=item['sha256']:raise ValueError('Angle source math differs')
            rows.append(dict(common,math_id=mid,math_sha256=item['sha256']))
    return {'segments':rows,'verified_full_units':0,'facsimile_checked':False,'historical_branch_convention_unresolved':True,
        'geometric_unsigned_reading_explicit':True,'calculation_transition_and_M0257_unwritten':True}


def build_report():
    text,basis=composed();doc=parse(text)
    if (ROOT/basis['document']).read_text(encoding='utf-8')!=text:raise ValueError('Stored angles differ')
    if json.loads((ROOT/'data/direction-angles-basis-v1.json').read_text(encoding='utf-8'))!=basis:raise ValueError('Angle basis differs')
    for notation in ('compact','full'):
        form=format_graph(doc,notation)
        if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Angle roundtrip differs')
    paths=[basis['document'],'data/direction-angles-basis-v1.json','examples/v014/einstein-speed-magnitude.noema',
        'scripts/compose_direction_angles.py','scripts/check_direction_angles.py','scripts/check_tau_differential.py','scripts/check_transverse_time.py',
        'noema/discourse.py','noema/finite_semantics.py','noema/polynomial_proofs.py','artifacts/written-units-v1/einstein-1905.json','reports/written-units-v1.json']
    return {'status':'partial_unit_circle_angles_and_explicit_inverse_branches','documents':{basis['document']:audit_basis(doc,basis)},
        'polynomial_lemmas':polynomial_checks(),'angles':angle_checks(),'source_readings':source_checks(),'attribution':attribution_checks(),'alignment':alignment(),
        'roundtrips':True,'verified_full_units':{'einstein-1905':0,'kant-1784':0},
        'reference':{'url':'https://dlmf.nist.gov/4.23','checked_on':'2026-10-13','scope':'General inverse relations versus principal branches; not evidence of Einstein historical branch choice'},
        'notation_size':{'canonical_source_document_characters':len(text),'added_characters':len(text)-len((ROOT/'examples/v014/einstein-speed-magnitude.noema').read_text(encoding='utf-8'))},
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args();report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Angle report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Unit-circle angles, inverse branches, orientation and source readings checked')


if __name__=='__main__':main()
