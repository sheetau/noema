"""Check null-cone algebra, actual front membership and proof-status scoping."""
import argparse
from fractions import Fraction
import hashlib
import json

from noema.grammar import parse, format_graph
from noema.finite_semantics import Content
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
from scripts.compose_spherical_wave import ROOT, generic_composed, source_composed

REPORT=ROOT/'reports/spherical-wave-v1.json'


def polynomial_checks():
    names='light speed component beta phi inverse x y z time'
    V,v,w,b,p,i,x,y,z,t=('v '+name for name in names.split())
    mul=lambda a,b:call('ad',a,b);square=lambda a:mul(a,a);zero=literal(0)
    before=call('sqg',V,x,y,z,t)
    after=call('sqg',V,call('sou',v,p,b,x,t),call('sov',p,y),call('sov',p,z),call('sot',V,v,p,b,i,x,t))
    common=conjunction(call('sor',V,v,w,b),call('sja',literal(1),square(V),i))
    future=conjunction(common,call('aa',zero,p),call('aa',zero,t),op('e',before,zero))
    claims={
        'spherical_residual_scales_by_phi_squared':assertion(names,op('y',common,op('e',after,mul(square(p),before)))),
        'forward_null_equation_does_not_need_phi_one':assertion(names,op('y',conjunction(common,op('e',before,zero)),op('e',after,zero))),
        'nonzero_phi_preserves_null_equation_both_ways':assertion(names,op('y',conjunction(common,op('u',op('e',p,zero))),op('z',op('e',before,zero),op('e',after,zero)))),
        'positive_phi_keeps_future_null_points_future':assertion(names,op('y',future,call('aa',zero,call('sot',V,v,p,b,i,x,t)))),
        'nonempty_null_wave_determines_phi_to_one':assertion('',op('y',op('e',call('sqg',literal(5),zero,zero,literal(20),literal(4)),zero),op('e',literal(Fraction(5,2)),literal(1)))),
        'zero_scale_gives_a_nonzero_future_time':assertion('',call('aa',zero,call('sot',literal(5),literal(3),zero,literal(Fraction(5,4)),literal(Fraction(1,25)),literal(6),literal(2)))),
        'negative_scale_preserves_future_time':assertion('',call('aa',zero,call('sot',literal(5),literal(3),literal(Fraction(-5,2)),literal(Fraction(5,4)),literal(Fraction(1,25)),literal(6),literal(2)))),
    }
    rejected={'nonempty_null_wave_determines_phi_to_one','zero_scale_gives_a_nonzero_future_time','negative_scale_preserves_future_time'}
    rows={}
    for name,claim in claims.items():
        result=verify_universal(parse(generic_composed()[0]+claim),MEANINGS,timeout_ms=15000)[0]
        if result['status']!=('invalid' if name in rejected else 'valid'):raise ValueError('Spherical algebra differs: '+name+' '+repr(result))
        rows[name]=result
    return {'claims':rows,'rational_polynomial_lemmas_only':True,'physical_compatibility_proved':False}


DOMAIN=('wave','ray1','ray2','emit','hit1','hit2','inside','rest','moving','r0','r1','r2','ri','m0','m1','m2','mi','x','y','z','t')


def wave_model(doc,label='baseline'):
    fixture=ConstructedCuts();n=fixture.read;c=fixture.make;model=guarded(doc);fixture.arithmetic(model)
    phi=Fraction(0) if label=='zero_scale' else Fraction(-5,2) if label=='negative_scale' else Fraction(5,2)
    beta=Fraction(5,4)
    coords={'r0':[0,0,0,0],'r1':[6,0,8,2],'r2':[0,6,8,2],'ri':[1,0,0,1]}
    for a,b in (('r0','m0'),('r1','m1'),('r2','m2'),('ri','mi')):
        x,y,z,t=coords[a];coords[b]=[phi*beta*(x-3*t),phi*y,phi*z,phi*beta*(t-Fraction(3,25)*x)]
    if label=='wrong_transformed_point':coords['m1'][2]+=1
    if label=='unremoved_origin_constant':coords['m1'][3]+=1
    for key,value in {'yn':'x','yo':'y','yp':'z','zc7':'t','ra':'rest','zbm':'moving','zfu':'wave','zfv':'emit','zfw':'hit1','zb6':'motion'}.items():model[key]=lambda value=value:value
    model.update(tc=lambda:c(5),zb7=lambda:c(3),sky=lambda value:square_root(fixture,value),
        zc5=lambda record:record in coords,
        zc6=lambda record,role:c(coords.get(record,[0,0,0,0])[('x','y','z','t').index(role)] if role in ('x','y','z','t') else 0))
    callbacks(doc,model,{'zeq':lambda speed:c(phi/beta)})
    charts={('emit','rest'):'r0',('hit1','rest'):'r1',('hit2','rest'):'r2',('inside','rest'):'ri',
        ('emit','moving'):'m0',('hit1','moving'):'m1',('hit2','moving'):'m2',('inside','moving'):'mi'}
    members={'ray1','ray2'} if label!='empty_wave' else set()
    if label=='missing_direction':members.remove('ray2')
    arrivals={('ray1','emit','hit1','rest'),('ray1','emit','hit1','moving'),('ray2','emit','hit2','rest'),('ray2','emit','hit2','moving')}
    if label=='extra_arrival':arrivals|={('ray1','emit','inside','rest'),('ray1','emit','inside','moving')}
    if label=='missing_moving_arrival':arrivals.remove(('ray2','emit','hit2','moving'))
    if label=='wrong_emission':arrivals={tuple('inside' if i==1 else q for i,q in enumerate(row)) for row in arrivals}
    model.update(zc4=lambda event:event in ('emit','hit1','hit2','inside') and label!='empty_event_scope',
        zdz=lambda event,frame,setting:charts.get((event,frame),'r0'),
        zft=lambda wave,ray,setting:wave=='wave' and ray in members and setting=='motion',
        cf=lambda ray:ray in ('ray1','ray2') and not(label=='nonlight_member' and ray=='ray2'),
        cg=lambda ray,emission,event,frame:(ray,emission,event,frame) in arrivals)
    primitive_names={d['name'] for d in doc['declarations'] if d['kind']=='primitive'}
    if 'shd' in primitive_names:model['shd']=lambda event,record,frame,setting:setting=='motion' and charts.get((event,frame))==record
    if 'smk' in primitive_names:model['smk']=lambda event,setting:(event,setting)==('emit','motion') and label!='nonzero_emission_origin'
    return model,fixture,coords


def equation_checks():
    query='r ja[] a.r jb[] a.q[k spg[k ja[] k jb[]]].q[k sqk[k ja[] k tc[]]].q[k sqk[k jb[] k tc[]]].q[k sql[k jb[] k tc[]]].'
    doc=abstract(candidate(source_composed()[0],query),ARITHMETIC|{'sky'});rows={}
    for label in ('baseline','second_direction','off_cone','negative_scale','zero_scale','wrong_transformed_point','unremoved_origin_constant','emission_point'):
        model,fixture,coords=wave_model(doc,label)
        pair={'second_direction':('r2','m2'),'off_cone':('ri','mi'),'emission_point':('r0','m0')}.get(label,('r1','m1'))
        model.update(ja=lambda:pair[0],jb=lambda:pair[1])
        actual=values(doc,model,DOMAIN)
        expected=[label not in ('wrong_transformed_point','unremoved_origin_constant'),label!='off_cone',label not in ('off_cone','wrong_transformed_point','unremoved_origin_constant'),label in ('baseline','second_direction')]
        if actual!=expected:raise ValueError('Sphere equation or future side differs: '+label+repr(actual))
        rows[label]={'accepted':actual,'input':list(map(str,coords[pair[0]])),'output':list(map(str,coords[pair[1]]))}
    return {'cases':rows,'zero_scale_preserves_equation_but_not_future_front':True,'origin_and_future_conditions_separate':True}


def front_checks():
    query='q[k sqo[k zfu[] k zfv[] k zb6[]]].q[k sqn[k zfu[] k zfv[] k ra[] k zb6[]]].q[k sqn[k zfu[] k zfv[] k zbm[] k zb6[]]].'
    doc=abstract(candidate(source_composed()[0],query),ARITHMETIC|{'sky','shd','smk'});rows={}
    labels=('baseline','missing_direction','extra_arrival','missing_moving_arrival','wrong_emission','empty_wave','empty_event_scope','nonlight_member','nonzero_emission_origin','zero_scale','negative_scale','wrong_transformed_point')
    for label in labels:
        model,_,_=wave_model(doc,label);actual=values(doc,model,DOMAIN)
        expected=[label not in ('empty_wave','nonlight_member','nonzero_emission_origin'),
            label in ('baseline','missing_moving_arrival','nonzero_emission_origin','zero_scale','negative_scale','wrong_transformed_point'),
            label in ('baseline','nonzero_emission_origin')]
        if actual!=expected:raise ValueError('Wave front membership differs: '+label+repr(actual))
        rows[label]=actual
    return {'cases':rows,'both_directions_and_nonempty_arrivals_checked':True,'measurement_and_emission_origin_are_oracles':True,'continuous_spatial_coverage_proved':False}


def source_binding_checks():
    query='q[t[k sqq[]][k zb6[]]].q[t[k sqr[]][k zb6[]]].q[t[k sqs[]][k zb6[]]].q[t[k sqz[]][k zb6[]]].'
    doc=abstract(candidate(source_composed()[0],query),ARITHMETIC|{'sky','shd','smk','spk','shi'});rows={}
    for label in ('baseline','missing_transform_premise','missing_record_existence','missing_moving_arrival','wrong_emission','nonzero_emission_origin','negative_scale','zero_scale','wrong_moving_record'):
        model,_,_=wave_model(doc,label)
        model['spk']=lambda:Content(('motion','text','other'),(label!='missing_transform_premise',)*3)
        model['shi']=lambda:Content(('motion','text','other'),(label!='missing_record_existence',)*3)
        if label=='wrong_moving_record':
            earlier=model['zdz'];model['zdz']=lambda event,frame,setting:'r1' if (event,frame)==('hit1','moving') else earlier(event,frame,setting)
        actual=values(doc,model,DOMAIN)
        expected=[label!='wrong_emission',label!='wrong_moving_record',label not in ('missing_transform_premise','wrong_emission'),label in ('baseline','wrong_moving_record')]
        if actual!=expected:raise ValueError('Source equation or extension premise differs: '+label+repr(actual))
        rows[label]=actual
    return {'cases':rows,'selected_record_must_belong_to_same_event_and_frame':True,'full_transform_and_record_existence_are_oracles':True}


def compatibility_checks():
    # Contents have the same three possible situations and one shared interpretation.
    text=generic_composed()[0]+'''r ja[d] c.r jb[d] c.r jc[d] c.
d jd[] e[b setting[k jb[v setting]]].d je[] e[b setting[k jc[v setting]]].
q[k sqh[p ja k jd[] k je[]]].'''
    doc=parse(text);rows={}
    cases={'same_setting':({'motion'},{'motion'},{'motion'},True),
        'different_settings':({'motion','text'},{'motion'},{'text'},False),
        'empty_admissible':(set(),{'motion'},{'motion'},False),
        'shared_but_excluded':({'other'},{'motion'},{'motion'},False),
        'not_every_setting':({'motion','text'},{'motion'},{'motion','text'},True),
        'first_false':({'motion'},set(),{'motion'},False),
        'second_false':({'motion'},{'motion'},set(),False)}
    for label,(allowed,first,second,expected) in cases.items():
        model=guarded(doc);model.update(ja=lambda s:s in allowed,jb=lambda s:s in first,jc=lambda s:s in second)
        actual=values(doc,model,('object',))[0]
        if actual!=expected:raise ValueError('Shared-setting compatibility differs: '+label)
        rows[label]=actual
    return {'cases':rows,'shared_interpretation_required':True,'actual_physical_model_constructed':False}


def proof_status_checks():
    doc=candidate(source_composed()[0],'q[t[k sqx[]][k ri[]]].');rows={}
    for label in ('not_yet_supplied','supplied_here','different_target','later_stage_only','different_agent','different_scope','no_candidate_proof'):
        model=guarded(doc)
        for key,value in {'rd':'author','rh':'scope','ri':'text','zfx':'motion'}.items():model[key]=lambda value=value:value
        def supplied(proof,agent,content,stage,scope):
            if label in ('not_yet_supplied','no_candidate_proof'):return False
            return (proof,agent,json.loads(content.syntax)['symbol'],stage,scope)==(
                'proof','other' if label=='different_agent' else 'author',
                'squ' if label=='different_target' else 'sqw','text' if label=='later_stage_only' else 'motion',
                'other' if label=='different_scope' else 'scope')
        model['zfr']=supplied
        actual=values(doc,model,('author','scope','other') if label=='no_candidate_proof' else ('author','scope','other','proof'))[0]
        if actual!=(label!='supplied_here'):raise ValueError('Proof status scoping differs: '+label)
        rows[label]=actual
    return {'cases':rows,'no_factiveness_inferred':True,'later_stage_does_not_rewrite_prior_status':True}


def attribution_checks():
    doc=parse(source_composed()[0]);doc['statements']=doc['statements'][-9:];rows={}
    for label in ('baseline','wrong_author','wrong_scope','wrong_context','gap_is_falsity','wrong_task','wrong_reason','wrong_assumption','wrong_rest_equation','wrong_transform','wrong_wave_conclusion','wrong_added_premise','wrong_compatibility'):
        model=guarded(doc)
        constants={'zfy':'gap','zfz':'task','zgc':'assumption','zgd':'rest','zge':'transform','zgf':'wave','zgg':'compatibility','zgh':'extra','rd':'author','rh':'scope','ri':'text','zfx':'motion'}
        for key,value in constants.items():model[key]=lambda value=value:value
        sym=lambda d:json.loads(d.syntax)['symbol']
        common=lambda a,s,c:(a,s,c)==('other' if label=='wrong_author' else 'author','other' if label=='wrong_scope' else 'scope','other' if label=='wrong_context' else 'text')
        model.update(uh=lambda node,a,d,s,c:common(a,s,c) and (node,sym(d))==('gap','sqw' if label=='gap_is_falsity' else 'sqx'),
            zga=lambda node,a,d,stage,s,c:common(a,s,c) and (node,sym(d),stage)==('task','sqw' if label=='wrong_task' else 'squ','motion'),
            zgb=lambda node,a,d,task,s,c:common(a,s,c) and (node,sym(d),task)==('gap','sqw' if label=='wrong_reason' else 'sqx','task'),
            ug=lambda node,a,d,s,c:common(a,s,c) and (node,sym(d))==('assumption','sqv' if label=='wrong_assumption' else 'sqp'),
            zd3=lambda node,a,p,b,e,s,c:common(a,s,c) and (node,sym(p),sym(b),sym(e))==('transform','sqs','sqq','sqv' if label=='wrong_transform' else 'sqr'),
            zfl=lambda node,a,p,e,s,c:common(a,s,c) and (node,sym(p),sym(e))==('extra','sqp' if label=='wrong_added_premise' else 'sqz','sqv'))
        triples={('rest','sqy','sqr' if label=='wrong_rest_equation' else 'sqq'),
            ('wave','sqr','sqk' if label=='wrong_wave_conclusion' else 'sqv'),
            ('compatibility','sqv','squ' if label=='wrong_compatibility' else 'sqw')}
        model['zc']=lambda node,a,p,e,s,c:common(a,s,c) and (node,sym(p),sym(e)) in triples
        actual=values(doc,model,tuple(v for k,v in constants.items() if k not in ('ri','zfx')))
        expected=[label not in ('wrong_author','wrong_scope','wrong_context',bad) for bad in ('gap_is_falsity','wrong_task','wrong_reason','wrong_assumption','wrong_rest_equation','wrong_transform','wrong_wave_conclusion','wrong_added_premise','wrong_compatibility')]
        if actual!=expected:raise ValueError('Proof and wave attribution differs: '+label+repr(actual))
        rows[label]=actual
    return rows


def alignment():
    artifact=json.loads((ROOT/'artifacts/written-units-v1/einstein-1905.json').read_text(encoding='utf-8'))
    hashes=['cf2cc28bf0e10b0ba62d24e8dab3f7a62c723e9577e865a933da9cbb9b07d902','0f6ba2657250679177c450733a1f6b975bc01a188585f5492e6853fe6db16c78','a5285db7b7e0c75e976f1618a3037a1ed2ebedcce05a1fd44e4f8f38f5b3105d','5ffadc919ae1147b6ca607a646a894f803114a487a6773f53596f693f9976b10','b6b93209f26003f1a6ac6322e21a456a1c4203f625f57319b42613ce91af963b','7586e175815928fff932ecfa340d4646ba175f85e1d2e7b0ba320db8faadafe1']
    mhashes=['fad146c158bc7dc725209b362adcee4dfb08d7da13a15bf61ab90897102da806','a22f9d2e64a30566446e64b3fca56b6ee0202d38a4497125aa6cb027bd2e19d6','185377cad6d20f36cfc42bcaa81120c25441ce5fc3a9a47381bab55b64e0af02','fad146c158bc7dc725209b362adcee4dfb08d7da13a15bf61ab90897102da806','30611cf3d0a64f690b362d16c07361bf72a67e259eba401fa884a3839498cb29','ce1fe35a439c6cce1a9ac3bc4f692f19fb594b7df0d422719e00cc0a015f3d93','1ba223ea6ed0ca02b50d4b095d8960d114981a5366fe4c3cc1d2d5a3f633fd8a','fad146c158bc7dc725209b362adcee4dfb08d7da13a15bf61ab90897102da806']
    defs=[['sqh','sqi','squ','sqw','sqx'],['sqm','sqn','sqo','sqp','sqy'],['sqj','sqk','sqq'],['sqs','sqt'],['sqj','sqk','sqr'],['sqh','sqn','sqv','sqw','sqz']];rows=[]
    for index,(digest,definitions) in enumerate(zip(hashes,defs),86):
        uid=f'einstein-1905:u{index:04}';unit=next(u for u in artifact['units'] if u['id']==uid)
        if hashlib.sha256(unit['text'].encode('utf-8')).hexdigest()!=digest:raise ValueError('Wave source changed')
        rows.append({'unit':uid,'unit_sha256':digest,'start':0,'end':len(unit['text']),'source':unit['text'],'definitions':definitions,'status':'partial_explicit_reading','full_semantic_equivalence':False})
        for mid in unit['math_ids']:
            item=next(m for m in artifact['math'] if m['id']==mid);mdigest=mhashes[int(mid[1:])-140]
            if hashlib.sha256(item['mathml'].encode('utf-8')).hexdigest()!=mdigest:raise ValueError('Wave source math changed')
            rows.append({'unit':uid,'unit_sha256':digest,'math_id':mid,'math_sha256':mdigest,'definitions':definitions,'status':'partial','full_semantic_equivalence':False})
    return {'segments':rows,'facsimile_checked':False,'verified_full_units':0,'proof_attribution_is_not_a_verified_proof':True,'future_front_has_additional_premises':True}


def build_report():
    documents={}
    for compose in (generic_composed,source_composed):
        text,basis=compose();doc=parse(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text:raise ValueError('Stored sphere document differs')
        if json.loads((ROOT/('data/'+basis['document'].split('/')[-1].replace('.noema','-basis-v1.json'))).read_text(encoding='utf-8'))!=basis:raise ValueError('Stored sphere basis differs')
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Sphere roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis)
    paths=[*documents,'data/spherical-wave-basis-v1.json','data/einstein-spherical-wave-basis-v1.json',
        'examples/v014/origin-constants.noema','examples/v014/einstein-origin-constants.noema',
        'scripts/compose_spherical_wave.py','scripts/check_spherical_wave.py','scripts/check_tau_differential.py','scripts/check_transverse_time.py',
        'noema/discourse.py','noema/finite_semantics.py','noema/polynomial_proofs.py']
    text=source_composed()[0];previous=(ROOT/'examples/v014/einstein-origin-constants.noema').read_text(encoding='utf-8')
    return {'status':'partial_spherical_wave_and_compatibility_discourse','documents':documents,
        'polynomial_lemmas':polynomial_checks(),'sphere_equations':equation_checks(),'wave_front':front_checks(),'source_binding':source_binding_checks(),
        'compatibility':compatibility_checks(),'proof_status':proof_status_checks(),'attribution':attribution_checks(),
        'alignment':alignment(),'roundtrips':True,'verified_full_units':{'einstein-1905':0,'kant-1784':0},
        'notation_size':{'canonical_source_document_characters':len(text),'added_characters':len(text)-len(previous)},
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args();report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Sphere report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Spherical equations, complete finite fronts and scoped proof status checked')


if __name__=='__main__':main()
