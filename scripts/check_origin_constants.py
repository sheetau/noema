"""Check constant scope, context changes and normalized candidate functions."""
import argparse
from fractions import Fraction
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
from scripts.check_rod_setup import callbacks, guarded
from scripts.check_real_products import MEANINGS, call, op, assertion
from scripts.check_moving_light_trip import literal
from scripts.check_tau_differential import ARITHMETIC, ConstructedCuts
from scripts.check_transverse_time import square_root
from scripts.check_four_coordinates import point_model, DOMAIN
from scripts.compose_origin_constants import ROOT, CUT, OFFSETS, generic_composed, source_composed

REPORT=ROOT/'reports/origin-constants-v1.json'
PARAMETERS=''.join('r '+name+'[] '+CUT+'.' for name in ('ja','jb','jc','jd'))
ARGS=' '.join('k '+name+'[]' for name in ('ja','jb','jc','jd'))


def polynomial_checks():
    names='cx cy cz ct offset dx dy dz dt output x y z time'
    cx,cy,cz,ct,o,dx,dy,dz,dt,out,x,y,z,t=('v '+n for n in names.split())
    add=lambda a,b:call('ab',a,b);mul=lambda a,b:call('ad',a,b)
    sub=lambda a,b:add(a,call('ac',b));zero=literal(0)
    offset=add(add(add(add(add(o,out),mul(cx,dx)),mul(cy,dy)),mul(cz,dz)),mul(ct,dt))
    row=lambda xx,yy,zz,tt,oo:call('sld',cx,cy,cz,ct,oo,xx,yy,zz,tt)
    claims={
        'input_and_output_origin_shifts_only_change_the_constant':assertion(names,op('e',call('sps',cx,cy,cz,ct,o,dx,dy,dz,dt,out,x,y,z,t),row(x,y,z,t,offset))),
        'zero_input_recovers_the_additive_constant':assertion('cx cy cz ct offset',op('e',row(zero,zero,zero,zero,o),o)),
        'common_constant_cancels_in_coordinate_differences':assertion(names,op('e',sub(row(x,y,z,t,o),row(dx,dy,dz,dt,o)),row(sub(x,dx),sub(y,dy),sub(z,dz),sub(t,dt),zero))),
        'constant_value_unique_at_any_shared_input':assertion(names,op('z',op('e',row(x,y,z,t,o),row(x,y,z,t,out)),op('e',o,out))),
        'positive_beta_keeps_candidate_scales_distinct':assertion('cx cy ct',op('y',call('aa',zero,ct),op('z',op('e',mul(cx,ct),mul(cy,ct)),op('e',cx,cy)))),
        'changing_constant_by_input_preserves_differences':assertion('',op('e',sub(add(literal(7),literal(2)),add(literal(3),literal(1))),sub(literal(7),literal(3)))),
        'independent_components_require_a_shared_constant':assertion('',op('e',literal(1),literal(2))),
    }
    rejected={'changing_constant_by_input_preserves_differences','independent_components_require_a_shared_constant'}
    rows={}
    for name,claim in claims.items():
        result=verify_universal(parse(generic_composed()[0]+claim),MEANINGS,timeout_ms=15000)[0]
        if result['status']!=('invalid' if name in rejected else 'valid'):raise ValueError('Origin algebra differs: '+name)
        rows[name]=result
    return {'claims':rows,'rational_polynomial_lemmas_only':True,'general_real_field_proof':False}


def set_offsets(model,fixture,offsets):
    for symbol,value in zip(('ja','jb','jc','jd'),offsets):model[symbol]=lambda value=value:fixture.make(value)


def translated_model(doc,offsets=(4,1,2,3)):
    model,fixture,coords,seen=point_model(doc)
    # Caller order is time, x, y, z; coordinate records store x, y, z, time.
    shift=(offsets[1],offsets[2],offsets[3],offsets[0])
    coords['m0']=[value+shift[i] for i,value in enumerate(coords['m0'])]
    coords['alias']=coords['m0'].copy()
    coords['bad']=[value+1 for value in coords['m0']]
    set_offsets(model,fixture,offsets)
    return model,fixture,coords,seen


def equation_checks():
    doc=abstract(candidate(source_composed()[0],PARAMETERS+'r je[] a.r jf[] a.q[k spu[k je[] k jf[] '+ARGS+']].'),ARITHMETIC|{'sky'})
    rows={}
    cases=('independent','all_zero','only_time','only_x','only_y','only_z','negative_constants','wrong_time','wrong_x','wrong_y','wrong_z','one_shared_constant','zero_origin_formula_reused')
    for label in cases:
        offsets={'all_zero':(0,0,0,0),'only_time':(4,0,0,0),'only_x':(0,1,0,0),'only_y':(0,0,2,0),'only_z':(0,0,0,3),'negative_constants':(-4,-1,-2,-3)}.get(label,(4,1,2,3))
        model,fixture,coords,seen=translated_model(doc,offsets)
        model.update(je=lambda:'f0',jf=lambda:'m0')
        if label.startswith('wrong_'):coords['m0'][('x','y','z','time').index(label[6:])]+=1
        if label=='one_shared_constant':set_offsets(model,fixture,(4,4,4,4))
        if label=='zero_origin_formula_reused':set_offsets(model,fixture,(0,0,0,0))
        actual=values(doc,model,DOMAIN)[0]
        expected=label in cases[:7]
        if actual!=expected:raise ValueError('Independent origin constants differ: '+label)
        if set(seen)!={3}:raise ValueError('Scale used a different velocity')
        rows[label]={'accepted':actual,'offsets_time_x_y_z':list(offsets),'second':list(map(str,coords['m0']))}
    return {'cases':rows,'zero_and_independent_offsets_permitted':True,'same_scale_and_speed':True}


def graph_checks():
    doc=abstract(candidate(source_composed()[0],PARAMETERS+'r je[] d.q[k spy['+ARGS+' k je[]]].'),ARITHMETIC|{'sky','spw','spx','spv'})
    rows={};domain=DOMAIN+('f1','m1')
    for label in ('two_records_common_constants','second_record_changed_constant','different_value_each_component','duplicate_value_alias','missing_alias_relation','extra_relation','missing_relation','empty_scope','wrong_setting'):
        model,fixture,coords,_=translated_model(doc)
        model['zc6']=lambda record,role:fixture.make(coords.get(record,[0,0,0,0])[('x','y','z','t').index(role)] if role in ('x','y','z','t') else 0)
        coords['f1']=[2,1,3,1]
        coords['m1']=[Fraction(-25,8)+1,Fraction(5,2)+2,Fraction(15,2)+3,Fraction(19,8)+4]
        if label=='second_record_changed_constant':coords['m1'][0]+=1
        if label=='different_value_each_component':coords['m1']=[value+1 for value in coords['m1']]
        left={'f0','f1'} if label!='empty_scope' else set()
        right={'m0','m1','bad'}|({'alias'} if label in ('duplicate_value_alias','missing_alias_relation') else set())
        pairs={('f0','m0'),('f1','m1')}
        if label=='duplicate_value_alias':pairs.add(('f0','alias'))
        if label=='extra_relation':pairs.add(('f0','bad'))
        if label=='missing_relation':pairs.remove(('f1','m1'))
        seen=[]
        def setting_ok(setting):seen.append(setting);return setting=='other'
        model.update(je=lambda:'motion' if label=='wrong_setting' else 'other',
            spw=lambda record,setting:setting_ok(setting) and record in left,
            spx=lambda record,setting:setting_ok(setting) and record in right,
            spv=lambda first,second,setting:setting_ok(setting) and (first,second) in pairs)
        actual=values(doc,model,domain)[0]
        if actual!=(label in ('two_records_common_constants','duplicate_value_alias')):raise ValueError('Common constants or graph equality differs: '+label)
        if set(seen)!={model['je']()}:raise ValueError('Graph silently reused the old setting')
        rows[label]=actual
    return {'cases':rows,'existence_functionality_and_both_directions_evaluated':True,'record_assignment_relations_are_oracles':True,'two_distinct_inputs_share_constants':True}


def context_checks():
    queries='r ja[] d.r jb[] a.r jc[] a.q[k spv[k jb[] k jc[] k ja[]]].q[k spw[k jb[] k ja[]]].q[k spx[k jc[] k ja[]]].q[t[k sqa[]][k ja[]]].'
    doc=abstract(candidate(source_composed()[0],queries),{'shd'});rows={}
    for label in ('no_assumption','assumption_adopted','conditions_changed','wrong_setting','different_events','wrong_frame'):
        model=guarded(doc)
        for key,value in {'ja':'motion' if label=='wrong_setting' else 'other','jb':'first','jc':'second','ra':'rest','zbm':'moving','zfm':'text'}.items():model[key]=lambda value=value:value
        model['zc4']=lambda event:event in ('event','other_event')
        pairs={('event','first','rest','other'),('other_event' if label=='different_events' else 'event','second','rest' if label=='wrong_frame' else 'moving','other')}
        model.update(shd=lambda event,record,frame,setting:(event,record,frame,setting) in pairs,
            zfn=lambda setting:setting=='other' and label!='conditions_changed',
            zfo=lambda stage,setting:stage=='text' and setting=='other' and label!='assumption_adopted')
        actual=values(doc,model,('event','other_event','first','second','rest','moving'))
        expected=[label not in ('wrong_setting','different_events','wrong_frame'),label!='wrong_setting',label not in ('wrong_setting','wrong_frame'),label not in ('assumption_adopted','conditions_changed','wrong_setting')]
        if actual!=expected:raise ValueError('Origin convention, frame or shared event differs: '+label)
        rows[label]=actual
    return {'cases':rows,'absence_of_assumption_does_not_assert_unequal_origins':True,'same_event_and_supplied_context_checked':True,'physical_measurement_assignment_is_an_oracle':True}


def uncertainty_model(doc,label='two_values'):
    fixture=ConstructedCuts();c=fixture.make;n=fixture.read;model=guarded(doc);fixture.arithmetic(model)
    model.update(tc=lambda:c(5),zee=lambda:'agent',zfm=lambda:'motion' if label=='old_stage' else 'text',sky=lambda value:square_root(fixture,value))
    sort=next(d['result']['result'] for d in doc['declarations'] if d['name']=='zer')
    def old_value(stage,speed):
        if stage!='other':return 2
        return 2 if label=='same_values' else 2+(n(speed)-3)**2 if label in ('same_at_one_speed','different_at_another_speed') else 3
    callbacks(doc,model,{'zeq':lambda speed:c(4 if label=='wrong_current_family' else 2),
        'zer':lambda stage:FunctionValue(tuple(sort['parameters']),sort['result'],lambda speed:c(old_value(stage,speed)))})
    model['zet']=lambda agent,stage,alternative:agent=='agent' and stage=='text' and alternative in ('text','other') and label!='empty_candidates' and not(label=='second_excluded' and alternative=='other')
    return model,fixture


def uncertainty_checks():
    query='r ja[] '+CUT+'.r jb[] d.q[k sqe[k zfm[] k jb[] k ja[]]].q[k sqf[k ja[]]].'
    doc=abstract(candidate(source_composed()[0],query),ARITHMETIC|{'sky'});rows={}
    for label in ('two_values','same_values','second_excluded','empty_candidates','old_stage','wrong_current_family','same_at_one_speed','different_at_another_speed','outside_domain'):
        model,fixture=uncertainty_model(doc,label)
        speed=5 if label=='outside_domain' else 4 if label=='different_at_another_speed' else 3
        model.update(ja=lambda:fixture.make(speed),jb=lambda:'other')
        actual=values(doc,model,('agent',))
        expected=[label in ('two_values','wrong_current_family','different_at_another_speed'),label!='wrong_current_family']
        if actual!=expected:raise ValueError('Normalized candidate uncertainty differs: '+label+repr(actual))
        rows[label]=actual
    return {'cases':rows,'normalized_phi_not_the_old_coefficient':True,'pointwise_witnesses_only':True,'one_value_does_not_identify_the_function':True,'full_epistemic_theory':False}


def finite_refusals():
    rows={}
    for label,query in (('one_constant_tuple_for_all_records','k spz[k zfm[]]'),('full_normalized_uncertainty','t[k sqd[]][k zfm[]]')):
        doc=abstract(candidate(source_composed()[0],'q['+query+'].'),ARITHMETIC|{'sky'})
        model,_=uncertainty_model(doc)
        try:values(doc,model,('agent',))
        except ValueError as error:
            if 'Cannot finitely quantify the rational number domain' not in str(error):raise
            rows[label]={'refused':True,'reason':str(error)}
        else:raise ValueError('Full real quantifier replaced by samples: '+label)
    return rows


def attribution_checks():
    doc=parse(source_composed()[0]);doc['statements']=doc['statements'][-2:];rows={}
    for label in ('baseline','wrong_author','wrong_scope','wrong_context','old_unknown_content','wrong_condition','zero_origin_conclusion'):
        model=guarded(doc)
        for key,value in {'zfp':'unknown','zfq':'relaxation','rd':'author','rh':'scope','ri':'text'}.items():model[key]=lambda value=value:value
        symbol=lambda d:json.loads(d.syntax)['symbol']
        common=lambda a,s,c:(a,s,c)==('other' if label=='wrong_author' else 'author','other' if label=='wrong_scope' else 'scope','other' if label=='wrong_context' else 'text')
        model.update(uh=lambda node,a,d,s,c:common(a,s,c) and (node,symbol(d))==('unknown','smp' if label=='old_unknown_content' else 'sqd'),
            zc=lambda node,a,p,d,s,c:common(a,s,c) and (node,symbol(p),symbol(d))==('relaxation','smo' if label=='wrong_condition' else 'sqa','spk' if label=='zero_origin_conclusion' else 'sqb'))
        actual=values(doc,model,('unknown','relaxation','author','scope'))
        expected=[label not in {'wrong_author','wrong_scope','wrong_context','old_unknown_content'},label not in {'wrong_author','wrong_scope','wrong_context','wrong_condition','zero_origin_conclusion'}]
        if actual!=expected:raise ValueError('Origin assertion attribution differs: '+label)
        rows[label]=actual
    return rows


def alignment():
    artifact=json.loads((ROOT/'artifacts/written-units-v1/einstein-1905.json').read_text(encoding='utf-8'))
    unit=next(u for u in artifact['units'] if u['id']=='einstein-1905:u0085')
    digest='b535ff072428fe122e7bd1948027a3d49d43ce3e9be5a1e2c97dae869dbd1806'
    if hashlib.sha256(unit['text'].encode('utf-8')).hexdigest()!=digest:raise ValueError('Origin constants source changed')
    defs=['spu','spv','spw','spx','spy','spz','sqa','sqb','sqc','sqd','sqe','sqf']
    rows=[{'unit':unit['id'],'unit_sha256':digest,'start':0,'end':len(unit['text']),'source':unit['text'],'definitions':defs,'status':'partial_explicit_reading','full_semantic_equivalence':False}]
    expected={'M0137':'e30d00663991386dd192857546f6c039b1f9a56d995a8e4c95789c40764cada8','M0138':'35d6c10b7951f0b3bffc37d697478962ef369bf2966173f808ff56fa35d08280','M0139':'700a7fdfb3e6ad045fb18df09fc70eee7632677a54d49c061b0177d7e5bd8931'}
    for mid in unit['math_ids']:
        item=next(m for m in artifact['math'] if m['id']==mid)
        if hashlib.sha256(item['mathml'].encode('utf-8')).hexdigest()!=expected[mid]:raise ValueError('Origin source math changed')
        rows.append({'unit':unit['id'],'unit_sha256':digest,'math_id':mid,'math_sha256':expected[mid],'definitions':defs,'status':'partial','full_semantic_equivalence':False})
    return {'segments':rows,'facsimile_checked':False,'verified_full_units':0,'no_assumption_distinct_from_unequal_origins':True,'candidate_family_is_partial_interpretation':True}


def build_report():
    documents={}
    for compose in (generic_composed,source_composed):
        text,basis=compose();doc=parse(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text:raise ValueError('Stored origin document differs')
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Origin roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis)
    paths=[*documents,'data/origin-constants-basis-v1.json','data/einstein-origin-constants-basis-v1.json',
        'examples/v014/four-coordinates.noema','examples/v014/einstein-four-coordinates.noema',
        'scripts/compose_origin_constants.py','scripts/check_origin_constants.py','scripts/check_four_coordinates.py',
        'scripts/check_tau_differential.py','scripts/check_transverse_time.py',
        'noema/discourse.py','noema/finite_semantics.py','noema/polynomial_proofs.py']
    text=source_composed()[0];previous=(ROOT/'examples/v014/einstein-four-coordinates.noema').read_text(encoding='utf-8')
    return {'status':'partial_independent_origin_constants_and_normalized_uncertainty','documents':documents,
        'polynomial_lemmas':polynomial_checks(),'four_offsets':equation_checks(),'constant_graph':graph_checks(),
        'context_and_assumptions':context_checks(),'uncertainty':uncertainty_checks(),'finite_refusals':finite_refusals(),
        'attribution':attribution_checks(),'alignment':alignment(),'roundtrips':True,
        'verified_full_units':{'einstein-1905':0,'kant-1784':0},
        'notation_size':{'canonical_source_document_characters':len(text),'added_characters':len(text)-len(previous)},
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args();report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Origin constants report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Independent constant scope, changed origin contexts and normalized uncertainty checked')


if __name__=='__main__':main()
