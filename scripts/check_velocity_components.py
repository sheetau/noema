"""Check substitution, constant components, same-event bindings and attribution."""
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
from scripts.check_transverse_time import square_root
from scripts.compose_velocity_components import ROOT, CUT, composed, k, op, both, v

REPORT=ROOT/'reports/velocity-components-v1.json'
DOMAIN=('point','otherpoint','origin','later','other','r0','r1','m0','m1','bad','rest','moving','x','y','z','t','length','time','setup','result','author','scope')


def polynomial_checks():
    names='light speed beta longitudinal transverse x y z time xx yy zz tt'
    V,s,b,u,w,x,y,z,t,X,Y,Z,T=map(v,names.split())
    one=literal(1);zero=literal(0)
    D=k('ab',k('ad',V,V),k('ad',s,u))
    original=k('syp',u,w,X,Y,Z,T);result=k('syq',V,s,b,u,w,x,y,z,t)
    transform=k('srb',V,s,b,one,x,y,z,t,X,Y,Z,T)
    claims={
        'coordinate_substitution_preserves_both_motion_equations':assertion(names,op('y',both(transform,op('u',op('e',D,zero))),op('z',original,result))),
        'stationary_frame_recovers_original_components':assertion('light longitudinal transverse x y z time',op('y',k('aa',zero,V),op('z',k('syq',V,zero,one,u,w,x,y,z,t),k('syp',u,w,x,y,z,t)))),
        'nonzero_time_determines_both_components':assertion('longitudinal transverse x y z time other othertransverse',op('y',both(op('u',op('e',t,zero)),k('syp',u,w,x,y,z,t),k('syp',v('other'),v('othertransverse'),x,y,z,t)),both(op('e',u,v('other')),op('e',w,v('othertransverse'))))),
        'zero_denominator_never_defines_a_result':assertion('light speed beta longitudinal transverse x y z time',op('y',op('e',D,zero),op('u',result))),
        'signed_nonzero_denominator_is_allowed':assertion('',k('syq',*(literal(n) for n in (5,3,F(5,4),-10,2,35,-8,0,1)))),
        'ordinary_vector_addition_is_exact':assertion('',k('syq',*(literal(n) for n in (5,3,F(5,4),1,2,28,14,0,7)))),
        'transverse_component_is_unchanged':assertion('',k('syq',*(literal(n) for n in (5,3,F(5,4),1,2,25,14,0,7)))),
    }
    rows={};text=composed()[0]
    for name,claim in claims.items():
        doc=candidate(text,claim)
        doc['declarations']=[d for d in doc['declarations'] if d['name'] in {'aa','ab','ac','ad','sra','srb','syp','syq'}]
        result=verify_universal(doc,MEANINGS,timeout_ms=20000)[0]
        expected='invalid' if name in ('ordinary_vector_addition_is_exact','transverse_component_is_unchanged') else 'valid'
        if result['status']!=expected:raise ValueError('Velocity algebra differs: '+name+repr(result))
        rows[name]=result
    return {'claims':rows,'rational_polynomial_lemmas_only':True,'real_cut_field_laws_proved':False}


def equation_checks():
    symbols=['j'+c for c in 'abcdefghi']
    query=''.join('r '+s+'[] '+CUT+'.' for s in symbols)
    query+='q[k syt['+' '.join(k(s) for s in symbols)+']].'
    doc=abstract(candidate(composed()[0],query),ARITHMETIC|{'sky'});rows={}
    baseline=(5,3,F(5,4),1,2,25,10,0,7)
    cases={'baseline':(baseline,True),'stationary':((5,0,1,1,2,7,14,0,7),True),
        'negative_frame_velocity':((5,-3,F(5,4),1,2,-25,20,0,11),True),
        'negative_transverse':((5,3,F(5,4),1,-2,25,-10,0,7),True),
        'negative_denominator':((5,3,F(5,4),-10,2,35,-8,0,1),True),
        'origin_is_not_enough_to_identify_velocity':((5,3,F(5,4),4,-5,0,0,0,0),True),
        'zero_denominator_at_origin':((5,3,F(5,4),F(-25,3),2,0,0,0,0),False)}
    for label,index,value in (('ordinary_addition',5,28),('unchanged_transverse',6,14),('nonplanar',7,1),
        ('wrong_beta_branch',2,F(-5,4)),('invalid_component',3,128),('different_time',8,5)):
        row=list(baseline);row[index]=value;cases[label]=(row,False)
    for name,(args,expected) in cases.items():
        fixture=ConstructedCuts();model=guarded(doc);fixture.arithmetic(model)
        model['sky']=lambda value:square_root(fixture,value)
        for symbol,value in zip(symbols,args):model[symbol]=lambda value=value:fixture.make(value)
        actual=values(doc,model,('object',))
        if actual!=[expected]:raise ValueError('Velocity equation differs: '+name+repr(actual))
        rows[name]={'arguments':list(map(str,args)),'accepted':actual}
    return {'cases':rows,'constructed_rational_cut_oracles_only':True,'no_real_cut_sampling':True}


def graph_checks():
    query='q[k syw[]].q[k syx[]].q[t[k syy[]][k ri[]]].q[t[k syz[]][k ri[]]].'
    doc=abstract(candidate(composed()[0],query),ARITHMETIC|{'sky','shd'});rows={}
    for label in ('baseline','negative_transverse','wrong_fixed_component','changed_later_motion','missing_moving_record',
        'missing_rest_record','empty_history','wrong_point','different_event_pair','extra_bad_record','wrong_frame_motion','wrong_axis','wrong_setting'):
        fixture=ConstructedCuts();c=fixture.make;model=guarded(doc);fixture.arithmetic(model)
        w=-2 if label=='negative_transverse' else 2
        coords={'r0':[0,0,0,0],'r1':[25,5*w,0,7],'m0':[0,0,0,0],'m1':[5,5*w,0,5],'bad':[25,13,0,7]}
        if label=='changed_later_motion':coords['m1'][0]=6
        charts={('origin','rest'):'r0',('later','rest'):'r1',('origin','moving'):'m0',('later','moving'):'m1'}
        if label=='missing_moving_record':del charts['later','moving']
        if label=='missing_rest_record':del charts['later','rest']
        if label=='different_event_pair':charts['later','moving']='m0'
        for symbol,value in {'zkb':'point','zke':'motion','ra':'rest','zbm':'moving','yn':'x','yo':'y','yp':'z','zc7':'t','ta':'length','rb':'time','ri':'text'}.items():model[symbol]=lambda value=value:value
        model.update(tc=lambda:c(5),zb7=lambda:c(3),zkc=lambda:c(2 if label=='wrong_fixed_component' else 1),zkd=lambda:c(w),
            sky=lambda value:square_root(fixture,value),
            zka=lambda point,event,setting:point==('otherpoint' if label=='wrong_point' else 'point') and event in ('origin','later') and setting==('other' if label=='wrong_setting' else 'motion') and label!='empty_history',
            zc4=lambda event:event in ('origin','later'),zc5=lambda record:record in coords,
            zc6=lambda record,role:c(coords.get(record,[0,0,0,0])[('x','y','z','t').index(role)] if role in ('x','y','z','t') else 0),
            shd=lambda event,record,frame,setting:setting=='motion' and (charts.get((event,frame))==record or (label=='extra_bad_record' and (event,record,frame)==('later','bad','rest'))),
            zbo=lambda frame,axis,setting:axis,
            zgj=lambda moving,rest,axis,speed,length,time,setting:(moving,rest,axis,fixture.read(speed),length,time,setting)==('moving','rest','y' if label=='wrong_axis' else 'x',4 if label=='wrong_frame_motion' else 3,'length','time','motion'))
        original=label not in ('wrong_fixed_component','changed_later_motion','missing_moving_record','empty_history','wrong_point','wrong_frame_motion','wrong_axis','wrong_setting')
        paired=label not in ('changed_later_motion','missing_moving_record','missing_rest_record','empty_history','wrong_point','different_event_pair','extra_bad_record','wrong_setting')
        output=label not in ('wrong_fixed_component','missing_rest_record','empty_history','wrong_point','extra_bad_record','wrong_setting')
        expected=[original,paired,original and paired,output];actual=values(doc,model,DOMAIN)
        if actual!=expected:raise ValueError('Motion graph differs: '+label+repr(actual)+' expected '+repr(expected))
        rows[label]=actual
    return {'cases':rows,'same_event_and_point_required':True,'fixed_components_outside_event_quantifiers':True,
        'all_real_times_exist_proved':False,'shd_and_arithmetic_are_explicit_test_oracles':True}


def attribution_checks():
    doc=parse(composed()[0]);doc['statements']=doc['statements'][-2:];rows={}
    for label in ('baseline','wrong_author','wrong_scope','wrong_context','wrong_setup','wrong_premise','wrong_result'):
        model=guarded(doc)
        for symbol,value in {'zkg':'setup','zkh':'result','rd':'author','zkf':'scope','ri':'text'}.items():model[symbol]=lambda value=value:value
        sym=lambda desc:json.loads(desc.syntax)['symbol']
        common=lambda author,scope,context:(author,scope,context)==('other' if label=='wrong_author' else 'author','other' if label=='wrong_scope' else 'scope','other' if label=='wrong_context' else 'text')
        model['ug']=lambda node,author,body,scope,context:common(author,scope,context) and (node,sym(body))==('setup','syy' if label=='wrong_setup' else 'sza')
        model['zc']=lambda node,author,premise,result,scope,context:common(author,scope,context) and (node,sym(premise),sym(result))==('result','sza' if label=='wrong_premise' else 'syy','sza' if label=='wrong_result' else 'syz')
        expected=[label not in ('wrong_author','wrong_scope','wrong_context','wrong_setup'),label not in ('wrong_author','wrong_scope','wrong_context','wrong_premise','wrong_result')]
        actual=values(doc,model,DOMAIN)
        if actual!=expected:raise ValueError('Velocity attribution differs: '+label)
        rows[label]=actual
    return {'cases':rows,'quoted_physics_is_not_executed_or_endorsed':True}


def alignment():
    path=ROOT/'artifacts/written-units-v1/einstein-1905.json';artifact=json.loads(path.read_text(encoding='utf-8'))
    inventory=json.loads((ROOT/'reports/written-units-v1.json').read_text(encoding='utf-8'))
    if hashlib.sha256(path.read_bytes()).hexdigest()!=inventory['works']['einstein-1905']['units_sha256']:raise ValueError('Pinned velocity source differs')
    rows=[]
    for index,defs in ((130,['syu','syw','sza']),(131,['syr','syu']),(132,['syu']),(133,['syx','syy','syz']),(134,['syt','syv','syz'])):
        uid=f'einstein-1905:u{index:04}';unit=next(u for u in artifact['units'] if u['id']==uid)
        if hashlib.sha256(unit['text'].encode('utf-8')).hexdigest()!=unit['text_sha256']:raise ValueError('Velocity source text differs')
        start=unit['text'].index('Führt man') if index==133 else 0
        rows.append(dict(unit=uid,unit_sha256=unit['text_sha256'],start=start,end=len(unit['text']),source=unit['text'][start:],definitions=defs,status='partial_explicit_reading',full_semantic_equivalence=False))
        for mid in unit['math_ids']:
            if mid=='M0249':continue  # The question's frame mention is not this substitution clause.
            item=next(m for m in artifact['math'] if m['id']==mid)
            if hashlib.sha256(item['mathml'].encode('utf-8')).hexdigest()!=item['sha256']:raise ValueError('Velocity source math differs')
            rows.append(dict(unit=uid,unit_sha256=unit['text_sha256'],math_id=mid,math_sha256=item['sha256'],definitions=defs,status='partial',full_semantic_equivalence=False))
    return {'segments':rows,'verified_full_units':0,'facsimile_checked':False,'task_question_unwritten':True,
        'nonzero_denominator_is_explicit_domain_condition':True}


def build_report():
    text,basis=composed();doc=parse(text)
    if (ROOT/basis['document']).read_text(encoding='utf-8')!=text:raise ValueError('Stored velocity components differ')
    if json.loads((ROOT/'data/velocity-components-basis-v1.json').read_text(encoding='utf-8'))!=basis:raise ValueError('Stored velocity basis differs')
    for notation in ('compact','full'):
        form=format_graph(doc,notation)
        if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Velocity roundtrip differs')
    paths=[basis['document'],'data/velocity-components-basis-v1.json','examples/v014/einstein-earth-clocks.noema',
        'scripts/compose_velocity_components.py','scripts/check_velocity_components.py','scripts/check_tau_differential.py',
        'scripts/check_transverse_time.py','noema/polynomial_proofs.py','noema/finite_semantics.py','noema/discourse.py',
        'reports/written-units-v1.json','artifacts/written-units-v1/einstein-1905.json']
    return {'status':'partial_planar_velocity_components_and_substitution','documents':{basis['document']:audit_basis(doc,basis)},
        'polynomial_lemmas':polynomial_checks(),'equations':equation_checks(),'motion_graph':graph_checks(),
        'attribution':attribution_checks(),'alignment':alignment(),'roundtrips':True,
        'verified_full_units':{'einstein-1905':0,'kant-1784':0},
        'notation_size':{'canonical_source_document_characters':len(text),'added_characters':len(text)-len((ROOT/'examples/v014/einstein-earth-clocks.noema').read_text(encoding='utf-8'))},
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args();report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Velocity components report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Planar motion, velocity substitution, fixed components and same-event bindings checked')


if __name__=='__main__':main()
