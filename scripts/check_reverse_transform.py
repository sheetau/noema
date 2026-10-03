"""Verify signed composition while keeping reciprocity separate from phi=1."""
import argparse
from fractions import Fraction
import hashlib
import json

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.polynomial_proofs import verify_universal
from noema.script import encode, decode
from scripts.check_comoving_labels import values
from scripts.check_coordinate_correspondence import abstract
from scripts.check_described_appraisals import candidate
from scripts.check_rod_setup import callbacks, guarded
from scripts.check_real_products import MEANINGS, call, op, assertion, conjunction
from scripts.check_moving_light_trip import literal
from scripts.check_tau_differential import ARITHMETIC, ConstructedCuts
from scripts.check_transverse_time import square_root
from scripts.compose_reverse_transform import ROOT, CUT, generic_composed, source_composed

REPORT=ROOT/'reports/reverse-transform-v1.json'
DOMAIN=('event','f','m','l','x','y','z','t','alias')


def polynomial_checks():
    names='light speed beta plus minus x y z time xx yy zz tt xxx yyy zzz ttt'
    args=['v '+name for name in names.split()];V,v,b,p,m=args[:5]
    first,middle,last=args[5:9],args[9:13],args[13:17]
    mul=lambda x,y:call('ad',x,y);eq=lambda x,y:op('e',x,y)
    product=mul(p,m);zero=literal(0);one=literal(1);composite=call('src',*args)
    scaled=conjunction(*(eq(out,mul(product,value)) for out,value in zip(last,first)))
    claims={
        'opposite_speeds_have_same_positive_beta':assertion('light speed beta other',op('y',conjunction(call('sra',V,v,b),call('sra',V,call('ac',v),'v other')),eq(b,'v other'))),
        'two_applications_give_one_common_scale':assertion(names,op('y',composite,scaled)),
        'reciprocal_factors_give_identity':assertion(names,op('y',conjunction(composite,eq(product,one)),conjunction(*(eq(a,z) for a,z in zip(first,last))))),
        'nonzero_identity_probe_forces_product_one':assertion('plus minus x',op('y',conjunction(op('u',eq('v x',zero)),eq(mul(product,'v x'),'v x')),eq(product,one))),
        'reciprocity_forces_each_factor_one':assertion('',op('y',eq(mul(literal(2),literal(Fraction(1,2))),one),eq(literal(2),one))),
        'zero_origin_identity_forces_product_one':assertion('',op('y',eq(mul(literal(6),zero),zero),eq(literal(6),one))),
        'stationary_rescaling_is_identity':assertion('',eq(mul(literal(2),literal(7)),literal(7))),
    }
    rejected={'reciprocity_forces_each_factor_one','zero_origin_identity_forces_product_one','stationary_rescaling_is_identity'}
    rows={}
    for name,claim in claims.items():
        result=verify_universal(parse(generic_composed()[0]+claim),MEANINGS,timeout_ms=15000)[0]
        if result['status']!=('invalid' if name in rejected else 'valid'):raise ValueError('Reverse algebra differs: '+name+' '+repr(result))
        rows[name]=result
    return {'claims':rows,'rational_polynomial_lemmas_only':True,'relative_rest_alone_proves_identity':False,'phi_normalized_to_one':False}


def model_for(doc,label='reciprocal'):
    fixture=ConstructedCuts();n=fixture.read;c=fixture.make;model=guarded(doc);fixture.arithmetic(model)
    plus=0 if label=='zero_scale' else Fraction(5,2)
    minus=2 if label in ('nonreciprocal','zero_nonreciprocal') else Fraction(2,5)
    if label=='negative_pair':plus,minus=-1,-1
    first=[0]*4 if label in ('zero_input','zero_nonreciprocal') else [7,3,4,2]
    def transform(row,speed,scale):
        x,y,z,t=row;beta=Fraction(5,4)
        return [scale*beta*(x-speed*t),scale*y,scale*z,scale*beta*(t-Fraction(speed,25)*x)]
    middle=transform(first,3,plus)
    last=transform(middle,3 if label=='wrong_reverse_sign' else -3,plus if label=='same_phi_value_reused' else minus)
    if label=='wrong_final_time':last[3]+=1
    if label=='wrong_middle_record':middle[1]+=1
    coords={'f':first,'m':middle,'l':last,'alias':last.copy()}
    for key,value in {'yn':'x','yo':'y','yp':'z','zc7':'t','ra':'f','zbm':'m','zgi':'l','zb6':'motion'}.items():model[key]=lambda value=value:value
    model.update(tc=lambda:c(5),zb7=lambda:c(3),sky=lambda value:square_root(fixture,value),
        zc5=lambda record:record in coords,
        zc6=lambda record,role:c(coords.get(record,[0,0,0,0])[('x','y','z','t').index(role)] if role in ('x','y','z','t') else 0))
    seen=[]
    def coefficient(speed):
        value=n(speed);seen.append(value)
        return c((minus if value<0 else plus)/Fraction(5,4))
    callbacks(doc,model,{'zeq':coefficient})
    return model,fixture,coords,seen


def signed_beta_checks():
    query='r ja[] '+CUT+'.r jb[] '+CUT+'.q[k srd[k tc[] k ja[] k jb[]]].'
    doc=abstract(candidate(source_composed()[0],query),ARITHMETIC|{'sky'});rows={}
    for label,(speed,beta,expected) in {
        'positive':(3,Fraction(5,4),True),'negative':(-3,Fraction(5,4),True),'stationary':(0,1,True),
        'negative_beta':(-3,Fraction(-5,4),False),'wrong_beta':(-3,Fraction(3,5),False),
        'positive_boundary':(5,0,False),'negative_boundary':(-5,0,False),'outside':(-6,0,False)}.items():
        model,fixture,_,_=model_for(doc);model.update(ja=lambda:fixture.make(speed),jb=lambda:fixture.make(beta))
        actual=values(doc,model,DOMAIN)[0]
        if actual!=expected:raise ValueError('Signed beta differs: '+label)
        rows[label]=actual
    return {'cases':rows,'old_positive_speed_definition_unchanged':True}


def composition_checks():
    query='r ja[] a.r jb[] a.r jc[] a.q[k srf[k ja[] k jb[] k jc[]]].q[k srg[k ja[] k jc[] k srh[]]].q[k shh[k ja[] k jc[]]].q[t[k sro[]][k zb6[]]].'
    doc=abstract(candidate(source_composed()[0],query),ARITHMETIC|{'sky'});rows={}
    expected={
        'reciprocal':[True]*4,'nonreciprocal':[True,True,False,False],'negative_pair':[True]*4,
        'zero_scale':[True,True,False,False],'zero_input':[True]*4,'zero_nonreciprocal':[True,True,True,False],
        'wrong_reverse_sign':[False,False,False,True],'same_phi_value_reused':[False,False,False,True],
        'wrong_final_time':[False,False,False,True],'wrong_middle_record':[False,True,True,True]}
    for label,result in expected.items():
        model,_,coords,seen=model_for(doc,label);model.update(ja=lambda:'f',jb=lambda:'m',jc=lambda:'l')
        actual=values(doc,model,DOMAIN)
        if actual!=result:raise ValueError('Two transformations differ: '+label+repr(actual))
        if set(seen)!={Fraction(3),Fraction(-3)}:raise ValueError('Opposite arguments to same function lost')
        rows[label]={'accepted':actual,'first':list(map(str,coords['f'])),'middle':list(map(str,coords['m'])),'last':list(map(str,coords['l']))}
    return {'cases':rows,'same_function_at_opposite_velocities':True,'reciprocal_unequal_values_supported':True}


def graph_checks():
    query='q[t[k srl[]][k zb6[]]].q[t[k srm[]][k zb6[]]].q[t[k srn[]][k zb6[]]].q[t[k srr[]][k zb6[]]].'
    doc=abstract(candidate(source_composed()[0],query),ARITHMETIC|{'sky','shd'});rows={}
    for label in ('reciprocal','nonreciprocal','missing_third_record','wrong_event','empty_scope','duplicate_alias','conflicting_alias','zero_only'):
        model,_,coords,_=model_for(doc,'zero_nonreciprocal' if label=='zero_only' else label)
        model['zc4']=lambda event:event=='event' and label!='empty_scope'
        pairs={('event','f','f'),('event','m','m')}
        if label!='missing_third_record':pairs.add(('alias' if label=='wrong_event' else 'event','l','l'))
        if label in ('duplicate_alias','conflicting_alias'):
            pairs.add(('event','alias','l'))
            if label=='conflicting_alias':coords['alias'][0]+=1
        model['shd']=lambda event,record,frame,setting:setting=='motion' and (event,record,frame) in pairs
        actual=values(doc,model,DOMAIN)
        expected=[label in ('reciprocal','nonreciprocal','duplicate_alias','zero_only'),
            label in ('reciprocal','nonreciprocal','duplicate_alias','zero_only'),
            label in ('reciprocal','duplicate_alias','zero_only'),label in ('reciprocal','duplicate_alias')]
        if actual!=expected:raise ValueError('Three-frame quantified graph differs: '+label+repr(actual))
        rows[label]=actual
    return {'cases':rows,'every_event_has_three_records':True,'all_record_choices_not_only_one_witness':True,'physical_record_assignment_is_an_oracle':True}


def setup_checks():
    doc=abstract(candidate(source_composed()[0],'q[t[k srk[]][k zb6[]]].'),ARITHMETIC|{'sky','shd','smk','sfc'});rows={}
    for label in ('baseline','wrong_velocity','wrong_reference','wrong_axis','wrong_unit','not_parallel','third_time_nonzero','third_origin_not_coincident','earlier_origins_not_zero'):
        model,fixture,coords,_=model_for(doc);coords['zero']=[0,0,0,1 if label=='third_time_nonzero' else 0]
        model.update(zgk=lambda:'event',zbn=lambda frame,setting:'place',zdz=lambda event,frame,setting:'zero',
            zbv=lambda frame,origin,setting:(frame,origin,setting)==('l','place','motion'),
            cb=lambda event,place,frame:(event,place,frame)==('event','place','l') and label!='third_origin_not_coincident',
            shd=lambda event,record,frame,setting:(event,record,frame,setting)==('event','zero','l','motion'),
            smk=lambda event,setting:(event,setting)==('event','motion') and label!='earlier_origins_not_zero',
            sfc=lambda first,second,setting:(first,second,setting)==('m','l','motion') and label!='not_parallel',
            zbo=lambda frame,role,setting:'x',ta=lambda:'y',rb=lambda:'t')
        def motion(moving,reference,axis,speed,lengthunit,timeunit,setting):
            return (moving,reference,axis,fixture.read(speed),lengthunit,timeunit,setting)==(
                'l','f' if label=='wrong_reference' else 'm','z' if label=='wrong_axis' else 'x',
                3 if label=='wrong_velocity' else -3,'z' if label=='wrong_unit' else 'y','t','motion')
        model['zgj']=motion
        actual=values(doc,model,DOMAIN+('zero','place'))[0]
        if actual!=(label=='baseline'):raise ValueError('Third-frame motion or common zero differs: '+label)
        rows[label]=actual
    return {'cases':rows,'signed_velocity_units_frame_axis_and_zero_time_checked':True,'trajectory_and_parallel_axes_are_oracles':True}


def attribution_checks():
    doc=parse(source_composed()[0]);doc['statements']=doc['statements'][-7:];rows={}
    for label in ('baseline','wrong_author','wrong_scope','wrong_context','wrong_unknown_stage','wrong_function','wrong_setup','wrong_composition','wrong_rest','wrong_identity','wrong_reciprocity','lost_clarity_claim'):
        model=guarded(doc)
        constants={'zgt':'unknown','zgn':'task','zgo':'setup','zgp':'compose','zgq':'rest','zgr':'identity','zgs':'reciprocity','rd':'author','rh':'scope','ri':'text','zgl':'motion'}
        for key,value in constants.items():model[key]=lambda value=value:value
        sym=lambda d:json.loads(d.syntax)['symbol']
        common=lambda a,s,c:(a,s,c)==('other' if label=='wrong_author' else 'author','other' if label=='wrong_scope' else 'scope','other' if label=='wrong_context' else 'text')
        model.update(uh=lambda node,a,d,s,c:common(a,s,c) and (node,sym(d))==('unknown','sqd' if label=='wrong_unknown_stage' else 'srp'),
            zgm=lambda node,a,d,stage,s,c:common(a,s,c) and (node,sym(d),stage)==('task','zeq' if label=='wrong_function' else 'spc','motion'),
            ug=lambda node,a,d,s,c:common(a,s,c) and (node,sym(d))==('setup','srl' if label=='wrong_setup' else 'srk'),
            zdg=lambda node,a,d,s,c:common(a,s,c) and (node,sym(d))==('identity','srs' if label=='lost_clarity_claim' else 'srn'))
        triples={('compose','srq','srn' if label=='wrong_composition' else 'srm'),('rest','srm','srn' if label=='wrong_rest' else 'srs'),
            ('identity','srs','sro' if label=='wrong_identity' else 'srn'),('reciprocity','srr','srn' if label=='wrong_reciprocity' else 'sro')}
        model['zc']=lambda node,a,p,d,s,c:common(a,s,c) and (node,sym(p),sym(d)) in triples
        actual=values(doc,model,tuple(value for key,value in constants.items() if key not in ('ri','zgl')))
        bads=({'wrong_unknown_stage'},{'wrong_function'},{'wrong_setup'},{'wrong_composition'},{'wrong_rest'},{'wrong_identity','lost_clarity_claim'},{'wrong_reciprocity'})
        expected=[label not in {'wrong_author','wrong_scope','wrong_context'}|bad for bad in bads]
        if actual!=expected:raise ValueError('Reverse transform attribution differs: '+label+repr(actual))
        rows[label]=actual
    return rows


def alignment():
    path=ROOT/'artifacts/written-units-v1/einstein-1905.json';artifact=json.loads(path.read_text(encoding='utf-8'))
    inventory=json.loads((ROOT/'reports/written-units-v1.json').read_text(encoding='utf-8'))
    if hashlib.sha256(path.read_bytes()).hexdigest()!=inventory['works']['einstein-1905']['units_sha256']:raise ValueError('Pinned source artifact differs')
    hashes=['32b7574fa03e69d2584b370f552609b4ae086006a86253d0718362ce7a17a6e8','c14b3594b6f39201397b3f2cea09bc2cb74a53feac150e3615940afa723e9da5','793fa21bede5b93b6058cac6ec5ceb2e8d2d76d813b5c0fa99942066e22d4857','4bb7b78603e9658bafa8852cd3257339aff4e7d7c370ae6374daaf0449ef2b5d','e8f2d073881ee4ef444daccf08b5c2105ce1f96bc05bbd40909e06d68b10615e']
    definitions=[['srp'],['srd','sre','srf','sri','srj','srk','srl'],['srf','srg','srh','srm'],['srg','srm','srn','srs'],['srh','sro','srr']];rows=[]
    for index,(digest,defs) in enumerate(zip(hashes,definitions),92):
        uid=f'einstein-1905:u{index:04}';unit=next(u for u in artifact['units'] if u['id']==uid)
        if hashlib.sha256(unit['text'].encode('utf-8')).hexdigest()!=digest:raise ValueError('Reverse source unit changed')
        rows.append({'unit':uid,'unit_sha256':digest,'start':0,'end':len(unit['text']),'source':unit['text'],'definitions':defs,'status':'partial_explicit_reading','full_semantic_equivalence':False})
        for mid in unit['math_ids']:
            item=next(m for m in artifact['math'] if m['id']==mid)
            if hashlib.sha256(item['mathml'].encode('utf-8')).hexdigest()!=item['sha256']:raise ValueError('Reverse source math changed')
            rows.append({'unit':uid,'unit_sha256':digest,'math_id':mid,'math_sha256':item['sha256'],'definitions':defs,'status':'partial','full_semantic_equivalence':False})
    return {'segments':rows,'facsimile_checked':False,'verified_full_units':0,'relative_rest_to_identity_is_attributed_not_proved':True,'nonzero_probe_is_an_explicit_sufficient_premise':True}


def build_report():
    documents={}
    for compose in (generic_composed,source_composed):
        text,basis=compose();doc=parse(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text:raise ValueError('Stored reverse document differs')
        if json.loads((ROOT/('data/'+basis['document'].split('/')[-1].replace('.noema','-basis-v1.json'))).read_text(encoding='utf-8'))!=basis:raise ValueError('Stored reverse basis differs')
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Reverse roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis)
    paths=[*documents,'data/reverse-transform-basis-v1.json','data/einstein-reverse-transform-basis-v1.json',
        'examples/v014/spherical-wave.noema','examples/v014/einstein-spherical-wave.noema',
        'scripts/compose_reverse_transform.py','scripts/check_reverse_transform.py','scripts/check_tau_differential.py','scripts/check_transverse_time.py',
        'reports/written-units-v1.json','artifacts/written-units-v1/einstein-1905.json',
        'noema/discourse.py','noema/finite_semantics.py','noema/polynomial_proofs.py']
    text=source_composed()[0];previous=(ROOT/'examples/v014/einstein-spherical-wave.noema').read_text(encoding='utf-8')
    return {'status':'partial_signed_reverse_transform_and_reciprocal_scale','documents':documents,
        'polynomial_lemmas':polynomial_checks(),'signed_beta':signed_beta_checks(),'composition':composition_checks(),
        'three_frame_graph':graph_checks(),'third_frame_setup':setup_checks(),'attribution':attribution_checks(),
        'alignment':alignment(),'roundtrips':True,'verified_full_units':{'einstein-1905':0,'kant-1784':0},
        'notation_size':{'canonical_source_document_characters':len(text),'added_characters':len(text)-len(previous)},
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args();report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Reverse transform report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Signed composition, three-frame records and reciprocal scale checked')


if __name__=='__main__':main()
