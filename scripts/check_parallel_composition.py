"""Check composition coefficients, four coordinates and three-frame records."""
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
from scripts.compose_parallel_composition import ROOT, CUT, composed, k, op, both, v

REPORT=ROOT/'reports/parallel-composition-v1.json'
DOMAIN=('event','other','f','m','l','alias','x','y','z','t')


def polynomial_checks():
    V,s,w,b,c,B,U=map(v,('light','speed','moving','beta','otherbeta','combined','result'))
    mul=lambda x,y:k('ad',x,y);add=lambda x,y:k('ab',x,y);sub=lambda x,y:add(x,k('ac',y))
    eq=lambda x,y:op('e',x,y);zero=literal(0);one=literal(1);D=add(mul(V,V),mul(s,w))
    domain=both(k('sra',V,s,b),k('sra',V,w,c));speed=k('s3f',V,s,w,U)
    coeff=k('s4k',V,s,w,b,c,B)
    names='light speed moving beta otherbeta x y z time xx yy zz tt xxx yyy zzz ttt'
    coords=list(map(v,names.split()[5:]));first,middle,last=coords[:4],coords[4:8],coords[8:]
    chain=k('s4j',*map(v,names.split()))
    claims={
        'two_admissible_speeds_have_positive_denominator':assertion('light speed moving beta otherbeta',op('y',domain,k('aa',zero,D))),
        'composed_speed_remains_admissible':assertion('light speed moving beta otherbeta result',op('y',both(domain,speed),k('aa',mul(U,U),mul(V,V)))),
        'combined_coefficient_is_positive':assertion('light speed moving beta otherbeta combined',op('y',both(domain,coeff),k('aa',zero,B))),
        'combined_coefficient_satisfies_beta_of_composed_speed':assertion('light speed moving beta otherbeta combined result',op('y',both(domain,speed,coeff),k('sra',V,U,B))),
        'two_transformations_equal_one_with_composed_speed':assertion(names+' combined result',op('y',both(chain,speed,coeff),k('srb',V,U,B,one,*first,*last))),
        'transverse_coordinates_are_preserved':assertion(names,op('y',chain,both(eq(first[1],last[1]),eq(first[2],last[2])))),
        'opposite_speeds_compose_to_zero':assertion('light speed beta',op('y',k('sra',V,s,b),k('s3f',V,s,k('ac',s),zero))),
        'ordinary_addition_replaces_composed_speed':assertion('',k('s3f',*(literal(n) for n in (5,3,3,6)))),
        'betas_multiply_without_cross_term':assertion('',k('s4k',*(literal(n) for n in (5,3,3,F(5,4),F(5,4),F(25,16))))),
    }
    rejected={'ordinary_addition_replaces_composed_speed','betas_multiply_without_cross_term'}
    rows={};text=composed()[0]
    for name,claim in claims.items():
        doc=candidate(text,claim);doc['declarations']=[d for d in doc['declarations'] if d['name'] in {'aa','ab','ac','ad','sra','srb','s3f','s4j','s4k'}]
        result=verify_universal(doc,MEANINGS,timeout_ms=20000)[0]
        if result['status']!=('invalid' if name in rejected else 'valid'):raise ValueError('Parallel algebra differs: '+name+repr(result))
        rows[name]=result
    return {'claims':rows,'rational_polynomial_lemmas_only':True,'all_real_cut_field_and_root_laws_proved':False}


def transform(row,speed,light=F(5)):
    from math import isqrt
    square=light*light/(light*light-speed*speed)
    a,b=isqrt(square.numerator),isqrt(square.denominator)
    if a*a!=square.numerator or b*b!=square.denominator:raise ValueError('Fixture beta is irrational')
    beta=F(a,b);x,y,z,t=map(F,row)
    return [beta*(x-speed*t),y,z,beta*(t-speed*x/(light*light))]


def model_for(doc,label='baseline',speed=F(3),moving=F(3)):
    fixture=ConstructedCuts();make=fixture.make;model=guarded(doc);model_arithmetic(fixture,model)
    first=list(map(F,(7,3,4,2)));middle=transform(first,speed);last=transform(middle,moving)
    if label=='wrong_middle':middle[0]+=1
    if label=='wrong_time':last[3]+=1
    if label=='wrong_transverse':last[1]+=1
    if label=='naive_beta_product':
        # V=5,v=w=3: correct beta is 17/8, not 25/16.
        last[0]*=F(25,34);last[3]*=F(25,34)
    coords={'f':first,'m':middle,'l':last,'alias':last.copy()}
    if label=='conflicting_alias':coords['alias'][2]+=1
    for symbol,value in {'yn':'x','yo':'y','yp':'z','zc7':'t','ra':'f','zbm':'m','zlo':'l','zlp':'motion','ri':'text','ta':'y','rb':'t'}.items():model[symbol]=lambda value=value:value
    model.update(tc=lambda:make(5),zb7=lambda:make(speed),zlt=lambda:make(moving),
        zc5=lambda record:record in coords,
        zc6=lambda record,role:make(coords.get(record,[0]*4)[('x','y','z','t').index(role)] if role in ('x','y','z','t') else 0))
    return model,fixture,coords


def coordinate_checks():
    query='q[k s4m[k ra[] k zbm[] k zlo[] k tc[] k zb7[] k zlt[]]].'
    query+='q[k s4l[k ra[] k zlo[] k tc[] k s3j[k tc[] k zb7[] k zlt[]]]].'
    doc=abstract(candidate(composed()[0],query),ARITHMETIC|{'sjt','sky'});rows={}
    cases={'baseline':(3,3),'opposite':(3,-3),'zero_first':(0,3),'zero_second':(3,0),
        'both_zero':(0,0),'different_speeds':(3,4),'negative_pair':(-3,-4),
        'wrong_middle':(3,3),'wrong_time':(3,3),'wrong_transverse':(3,3),'naive_beta_product':(3,3)}
    for label,(speed,moving) in cases.items():
        model,fixture,coords=model_for(doc,label,F(speed),F(moving));actual=values(doc,model,DOMAIN)
        expected=[False,True] if label=='wrong_middle' else [False,False] if label in ('wrong_time','wrong_transverse','naive_beta_product') else [True,True]
        if actual!=expected:raise ValueError('Parallel coordinates differ: '+label+repr(actual))
        rows[label]={'accepted':actual,'first':list(map(str,coords['f'])),'middle':list(map(str,coords['m'])),'last':list(map(str,coords['l']))}
    return {'cases':rows,'all_four_coordinates_checked':True,'same_middle_record_required':True,'retained_rational_cut_oracles_only':True}


def graph_checks():
    doc=abstract(candidate(composed()[0],'q[t[k s4q[]][k ri[]]].q[t[k s4r[]][k ri[]]].'),ARITHMETIC|{'sjt','sky','shd'});rows={}
    for label in ('baseline','missing_middle','missing_final','different_event','empty_scope','duplicate_alias',
        'conflicting_alias','wrong_middle','wrong_time','wrong_setting','same_frame'):
        model,_,_=model_for(doc,label)
        model['zc4']=lambda event:event=='event' and label!='empty_scope'
        charts={('event','f','f'),('event','m','m'),('event','l','l')}
        if label=='missing_middle':charts.remove(('event','m','m'))
        if label=='missing_final':charts.remove(('event','l','l'))
        if label=='different_event':charts.remove(('event','m','m'));charts.add(('other','m','m'))
        if label in ('duplicate_alias','conflicting_alias'):charts.add(('event','alias','l'))
        if label=='same_frame':model['zlo']=lambda:'m'
        model['shd']=lambda event,record,frame,setting:setting==('other' if label=='wrong_setting' else 'motion') and (event,record,frame) in charts
        actual=values(doc,model,DOMAIN)
        expected=[True,True] if label in ('baseline','duplicate_alias') else [False,True] if label=='wrong_middle' else [False,False]
        if actual!=expected:raise ValueError('Three-frame graph differs: '+label+repr(actual))
        rows[label]=actual
    return {'cases':rows,'same_event_and_setting_required':True,'empty_or_missing_records_rejected':True,
        'all_alias_records_checked':True,'physical_record_assignment_is_an_explicit_oracle':True}


def setup_checks():
    doc=candidate(composed()[0],'q[t[k s4p[]][k ri[]]].');rows={}
    for label in ('baseline','wrong_reference','wrong_axis','wrong_speed','wrong_unit','wrong_setting','same_frame'):
        model=guarded(doc);fixture=ConstructedCuts()
        for symbol,value in {'ra':'f','zbm':'m','zlo':'l','yn':'x','ta':'y','rb':'t','zlp':'motion','ri':'text'}.items():model[symbol]=lambda value=value:value
        model.update(zb7=lambda:fixture.make(3),zlt=lambda:fixture.make(4),zbo=lambda frame,role,setting:role)
        if label=='same_frame':model['zlo']=lambda:'m'
        def motion(moving,rest,axis,speed,length,time,setting):
            expected={('m','f','x',F(3),'y','t','motion'),
                ('l','f' if label=='wrong_reference' else 'm','z' if label=='wrong_axis' else 'x',
                 F(3) if label=='wrong_speed' else F(4),'z' if label=='wrong_unit' else 'y','t','other' if label=='wrong_setting' else 'motion')}
            return (moving,rest,axis,fixture.read(speed),length,time,setting) in expected
        model['zgj']=motion;actual=values(doc,model,DOMAIN)
        if actual!=[label=='baseline']:raise ValueError('Third frame setup differs: '+label)
        rows[label]=actual
    return {'cases':rows,'reference_frame_axis_speed_units_and_setting_retained':True,'physical_parallel_motion_is_an_explicit_oracle':True}


def attribution_checks():
    doc=parse(composed()[0]);doc['statements']=doc['statements'][-2:];rows={}
    for label in ('baseline','wrong_author','wrong_scope','wrong_context','setup_replaced_by_result','reversed_inference'):
        model=guarded(doc)
        for symbol,value in {'zlr':'setup','zls':'result','rd':'author','zlq':'scope','ri':'text'}.items():model[symbol]=lambda value=value:value
        name=lambda d:json.loads(d.syntax)['symbol']
        def common(author,scope,context):return (author,scope,context)==('other' if label=='wrong_author' else 'author','other' if label=='wrong_scope' else 'scope','other' if label=='wrong_context' else 'text')
        model['ug']=lambda node,author,body,scope,context:common(author,scope,context) and node=='setup' and name(body)==('s4r' if label=='setup_replaced_by_result' else 's4p')
        model['zc']=lambda node,author,before,after,scope,context:common(author,scope,context) and node=='result' and (name(before),name(after))==(('s4r','s4s') if label=='reversed_inference' else ('s4s','s4r'))
        actual=values(doc,model,('setup','result','author','scope','other'))
        expected={'baseline':[True,True],'setup_replaced_by_result':[False,True],'reversed_inference':[True,False]}.get(label,[False,False])
        if actual!=expected:raise ValueError('Parallel attribution differs: '+label)
        rows[label]=actual
    return {'cases':rows,'quoted_physics_not_evaluated_as_global_truth':True}


def alignment():
    path=ROOT/'artifacts/written-units-v1/einstein-1905.json';source=json.loads(path.read_text(encoding='utf-8'))
    inventory=json.loads((ROOT/'reports/written-units-v1.json').read_text(encoding='utf-8'))
    if hashlib.sha256(path.read_bytes()).hexdigest()!=inventory['works']['einstein-1905']['units_sha256']:raise ValueError('Parallel source inventory differs')
    rows=[]
    for index in (147,148,149):
        unit=next(u for u in source['units'] if u['id']==f'einstein-1905:u{index:04}')
        if hashlib.sha256(unit['text'].encode('utf-8')).hexdigest()!=unit['text_sha256']:raise ValueError('Parallel source text differs')
        start=unit['text'].index('Führen wir') if index==147 else 0
        end=unit['text'].index(';')+1 if index==149 else len(unit['text'])
        common=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],definitions=['s4l','s4m','s4n','s4o','s4p','s4q','s4r','s4s'],status='partial_explicit_reading',full_semantic_equivalence=False)
        rows.append(dict(common,start=start,end=end,source=unit['text'][start:end]))
        for mid in unit['math_ids']:
            if mid in ('M0274','M0275'):continue
            item=next(m for m in source['math'] if m['id']==mid)
            if hashlib.sha256(item['mathml'].encode('utf-8')).hexdigest()!=item['sha256']:raise ValueError('Parallel source math differs')
            rows.append(dict(common,math_id=mid,math_sha256=item['sha256']))
    return {'segments':rows,'verified_full_units':0,'alternative_derivation_modality_unwritten':True,
        'following_group_claim_unwritten':True,'facsimile_scope':'Third-frame setup and M0285 visually compared on stored p906; not a full semantic review'}


def build_report():
    text,basis=composed();doc=parse(text)
    if (ROOT/basis['document']).read_text(encoding='utf-8')!=text or json.loads((ROOT/'data/parallel-composition-basis-v1.json').read_text(encoding='utf-8'))!=basis:raise ValueError('Stored parallel artifacts differ')
    for notation in ('compact','full'):
        form=format_graph(doc,notation)
        if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Parallel roundtrip differs')
    paths=[basis['document'],'data/parallel-composition-basis-v1.json','examples/v014/einstein-light-invariance.noema',
        'scripts/compose_parallel_composition.py','scripts/check_parallel_composition.py','scripts/check_angle_composition.py',
        'scripts/check_tau_differential.py','scripts/check_transverse_time.py','noema/discourse.py','noema/finite_semantics.py',
        'noema/polynomial_proofs.py','artifacts/written-units-v1/einstein-1905.json','reports/written-units-v1.json',
        'artifacts/written-facsimiles-v1/einstein-1905-p906.jpg']
    return {'status':'partial_parallel_transform_composition_with_three_frame_records','documents':{basis['document']:audit_basis(doc,basis)},
        'polynomial_lemmas':polynomial_checks(),'coordinates':coordinate_checks(),'record_graph':graph_checks(),
        'setup':setup_checks(),'attribution':attribution_checks(),'alignment':alignment(),'roundtrips':True,
        'verified_full_units':{'einstein-1905':0,'kant-1784':0},
        'notation_size':{'canonical_source_document_characters':len(text),'added_characters':len(text)-len((ROOT/'examples/v014/einstein-light-invariance.noema').read_text(encoding='utf-8'))},
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args();report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Parallel composition report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Parallel composition coefficients, coordinates, record graph and attribution checked')


if __name__=='__main__':main()
