"""Verify affine coefficient reduction, origin bindings and unfixed scale."""
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
from scripts.compose_affine_time_form import ROOT, CUT, TAU, PHI, FAMILY, generic_composed, source_composed

REPORT=ROOT/'reports/affine-time-form-v1.json'
ZERO='k bb[n p a b]'


def polynomial_checks():
    V,v,p,q,r,a,o,i,x,y,z,t=('v '+n for n in ('light','speed','space','ycoef','zcoef','scale','offset','inverse','x','y','z','time'))
    add=lambda a,b:call('ab',a,b);mul=lambda a,b:call('ad',a,b);neg=lambda a:call('ac',a)
    constraints=call('slx',V,v,p,q,r,a,o);inverse=call('sly',V,v,i)
    affine=lambda offset,xx,yy,zz,tt:call('sld',p,q,r,a,offset,xx,yy,zz,tt)
    reduced=call('slz',V,v,a,i,x,t)
    zero=literal(0)
    normalized=op('w',op('e',p,neg(mul(mul(a,v),i))),op('w',op('e',q,zero),op('w',op('e',r,zero),op('e',o,zero))))
    claims={
        'partial_and_origin_constraints_give_time_form':assertion('light speed space ycoef zcoef scale offset inverse x y z time',op('y',op('w',constraints,inverse),op('e',affine(o,x,y,z,t),reduced))),
        'coefficient_conditions_iff_normalized_form':assertion('light speed space ycoef zcoef scale offset inverse',op('y',inverse,op('z',constraints,normalized))),
        'affine_value_at_zero_is_exactly_offset':assertion('space ycoef zcoef scale offset',op('e',affine(o,zero,zero,zero,zero),o)),
        'derivative_conditions_leave_additive_origin_free':assertion('light speed space scale offset inverse x y z time',op('y',op('w',call('skb',V,v,p,a),inverse),op('e',call('sld',p,zero,zero,a,o,x,y,z,t),add(reduced,o)))),
        'longitudinal_increment_has_space_coefficient':assertion('space ycoef zcoef scale offset x y z time step',op('e',add(affine(o,add(x,'v step'),y,z,t),neg(affine(o,x,y,z,t))),mul(p,'v step'))),
        'time_increment_has_scale_coefficient':assertion('space ycoef zcoef scale offset x y z time step',op('e',add(affine(o,x,y,z,add(t,'v step')),neg(affine(o,x,y,z,t))),mul(a,'v step'))),
        'derivatives_alone_force_zero_origin':assertion('',op('y',call('skb',literal(5),literal(3),literal(Fraction(-3,8)),literal(2)),op('e',call('sld',literal(Fraction(-3,8)),zero,zero,literal(2),literal(7),zero,zero,zero,zero),zero))),
        'coefficient_is_forced_to_one':assertion('',op('y',call('slx',literal(5),literal(3),literal(Fraction(-3,8)),zero,zero,literal(2),zero),op('e',literal(2),literal(1)))),
    }
    rows={}
    for name,claim in claims.items():
        result=verify_universal(parse(generic_composed()[0]+claim),MEANINGS,timeout_ms=15000)[0]
        if result['status']!=('invalid' if name in ('derivatives_alone_force_zero_origin','coefficient_is_forced_to_one') else 'valid'):
            raise ValueError('Affine coefficient lemma differs: '+name)
        rows[name]=result
    return {'claims':rows,'rational_polynomial_lemmas_only':True,'full_real_derivative_theorem_proved':False}


def formula_checks():
    expr=lambda value:'k bb['+literal(value)+']'
    rows={}
    for label,(speed,scale,x,y,z,t,offset) in {
        'baseline':(3,2,8,3,4,5,0),'other_scale':(3,3,8,3,4,5,0),
        'nonzero_origin':(3,2,8,3,4,5,7),'other_transverse_position':(3,2,8,-4,9,5,0),
        'stationary':(0,2,8,3,4,5,0),'negative_xprime':(3,2,-8,3,4,5,0),
    }.items():
        p=-Fraction(scale*speed,25-speed*speed)
        params=[p,0,0,scale,offset,x,y,z,t]
        text='r ja[] '+TAU+'.q[k sca[k smc['+' '.join(map(expr,params))+'] '+expr(p*x+scale*t+offset)+']].'
        text+='q[k sca[k smh['+' '.join(map(expr,[5,speed,scale,x,t]))+'] '+expr(p*x+scale*t)+']].'
        text+='q[k smg[k ja[]]].'
        doc=abstract(candidate(source_composed()[0],text),ARITHMETIC)
        fixture=ConstructedCuts();n=fixture.read;c=fixture.make;model=guarded(doc);fixture.arithmetic(model)
        callbacks(doc,model,{'ja':lambda x,y,z,t:c(p*n(x)+scale*n(t)+offset)})
        actual=values(doc,model,('object',))
        if actual!=[True,True,offset==0]:raise ValueError('Affine or normalized expression differs: '+label)
        rows[label]={'checks':actual,'tau':str(p*x+scale*t),'affine_value':str(p*x+scale*t+offset)}
    return {'cases':rows,'constructed_rational_cut_arithmetic':True,'transverse_inputs_not_hidden_scale_arguments':True}


def coefficient_checks():
    text='r ja[] '+TAU+'.r jb[] '+PHI+'.'
    for name in ('jc','jd','je','jf','jg','jh'):text+='r '+name+'[] '+CUT+'.'
    text+='q[k smr[k ja[] k bb[n p f b] k jc[] k bb[n p b b] k jb[] k jd[] k je[] k jf[] k jg[] k jh[]]].'
    doc=abstract(candidate(source_composed()[0],text),ARITHMETIC|{'smd','sjw','sjs'})
    rows={}
    names=('baseline','other_scale','offset_not_yet_removed','wrong_phi_value','space_time_swapped','nonzero_y','nonzero_z','wrong_longitudinal_sign','not_affine','missing_partial_binding','light_speed_boundary')
    for label in names:
        fixture=ConstructedCuts();n=fixture.read;c=fixture.make;model=guarded(doc);fixture.arithmetic(model)
        scale=3 if label=='other_scale' else 2;speed=5 if label=='light_speed_boundary' else 3
        coeff=[-Fraction(3*scale,16),0,0,scale,7 if label=='offset_not_yet_removed' else 0]
        if label=='space_time_swapped':coeff[0],coeff[3]=coeff[3],coeff[0]
        if label=='nonzero_y':coeff[1]=1
        if label=='nonzero_z':coeff[2]=1
        if label=='wrong_longitudinal_sign':coeff[0]=-coeff[0]
        f=lambda x,y,z,t:c(sum(k*n(value) for k,value in zip(coeff,(x,y,z,t)))+coeff[4])
        seen=[]
        def phi(v):
            seen.append(n(v));return c(scale+1 if label=='wrong_phi_value' else scale)
        callbacks(doc,model,{'ja':f,'jb':phi})
        for symbol,value in zip(('jc','jd','je','jf','jg','jh'),(speed,*coeff)):model[symbol]=lambda value=value:c(value)
        model['smd']=lambda fn,*cs:tuple(n(v) for v in cs)==tuple(coeff) and label!='not_affine'
        model['sjw']=lambda fn,x,y,z,t,px,pt:(n(x),n(y),n(z),n(t),n(px),n(pt))==(0,0,0,1,coeff[0],coeff[3]) and label!='missing_partial_binding'
        # Exact for these supplied affine functions only; not a derivative algorithm.
        model['sjs']=lambda domain,fn,p,derivative:domain(p) and n(fn(c(n(p)+1)))-n(fn(p))==n(derivative)
        actual=values(doc,model,('object',))[0]
        if actual!=(label in ('baseline','other_scale','offset_not_yet_removed')):raise ValueError('Coefficient/partial connection differs: '+label)
        if not seen or set(seen)!={speed}:raise ValueError('Coefficient was evaluated at something other than the selected speed')
        rows[label]=actual
    return {'cases':rows,'affine_membership_and_derivatives_are_fixture_oracles':True,'same_phi_speed_and_time_coefficient_bound':True}


def origin_checks():
    text='r ja[] a.r jb[] d.q[k smk[k ja[] k jb[]]].q[k sml[k jb[]]].'
    doc=abstract(candidate(source_composed()[0],text),ARITHMETIC|{'shd','sio'})
    rows={};domain=('event','other','origin','resttuple','movingtuple','rest','moving','x','y','z','time')
    for label in ('baseline','wrong_place','unassigned_origin','missing_rest_chart','missing_moving_chart','rest_clock_not_zero','moving_clock_not_zero','auxiliary_origin_not_zero','moving_position_not_zero','wrong_context','tau_offset_not_zero','missing_tau_correspondence'):
        fixture=ConstructedCuts();n=fixture.read;c=fixture.make;model=guarded(doc);fixture.arithmetic(model)
        coords={'resttuple':[0,0,0,0],'movingtuple':[0,0,0,0]}
        if label=='rest_clock_not_zero':coords['resttuple'][3]=1
        if label=='moving_clock_not_zero':coords['movingtuple'][3]=1
        if label=='auxiliary_origin_not_zero':coords['resttuple'][0]=1
        if label=='moving_position_not_zero':coords['movingtuple'][1]=1
        for k,v in {'ja':'event','jb':'other' if label=='wrong_context' else 'motion','ra':'rest','zbm':'moving','yn':'x','yo':'y','yp':'z','zc7':'time'}.items():model[k]=lambda v=v:v
        model.update(zbn=lambda f,ctx:'origin',zb7=lambda:c(3),
            zbv=lambda f,p,ctx:(f,p,ctx)==('moving','origin','motion') and label!='unassigned_origin',
            cb=lambda event,p,f:(event,p,f)==('event','origin','moving') and label!='wrong_place',
            zdz=lambda event,f,ctx:'resttuple' if f=='rest' else 'movingtuple',
            shd=lambda event,record,f,ctx:event=='event' and ctx=='motion' and record==('resttuple' if f=='rest' else 'movingtuple') and not(label=='missing_rest_chart' and f=='rest') and not(label=='missing_moving_chart' and f=='moving'),
            zc6=lambda record,role:c(coords[record][('x','y','z','time').index(role)]),sio=lambda fn:label!='missing_tau_correspondence')
        callbacks(doc,model,{'zd4':lambda x,y,z,t:c(2*n(t)-Fraction(3,8)*n(x)+(7 if label=='tau_offset_not_zero' else 0))})
        actual=values(doc,model,domain)
        expected=[label in ('baseline','tau_offset_not_zero','missing_tau_correspondence'),label=='baseline']
        if actual!=expected:raise ValueError('Coincident origin and tau binding differs: '+label+repr(actual))
        rows[label]=actual
    return {'cases':rows,'measurement_charts_and_tau_correspondence_are_oracles':True,'same_event_in_both_frames_required':True}


def uncertainty_checks():
    text='r ja[] a.r jb[] d.r jc[] d.r jd[] d.r je[] '+CUT+'.'
    domain='i[speed '+CUT+'][w[k ba[v speed]][w[k bc['+ZERO+' v speed]][k bg[v speed k bb[n p f b]]]]]'
    text+='q[k sma[k ja[] k jb[] '+domain+' p zet k zer[] p sca k jc[] k jd[] k je[]]].'
    text+='q[k sms[k zeq[] k zer[] k jb[] k je[]]].'
    doc=abstract(candidate(source_composed()[0],text),ARITHMETIC)
    rows={}
    for label in ('two_values','same_values','first_excluded','second_excluded','empty_candidates','later_stage','wrong_agent','speed_outside_domain','wrong_current_function','same_value_at_selected_speed','different_value_at_another_speed'):
        fixture=ConstructedCuts();n=fixture.read;c=fixture.make;model=guarded(doc);fixture.arithmetic(model)
        for k,v in {'ja':'other' if label=='wrong_agent' else 'agent','jb':'other' if label=='later_stage' else 'motion','jc':'motion','jd':'text'}.items():model[k]=lambda v=v:v
        model['je']=lambda:c(5 if label=='speed_outside_domain' else 2 if label=='different_value_at_another_speed' else 3)
        def val(stage,speed):
            if stage!='text':return 2
            return 2 if label=='same_values' else 2+(n(speed)-3)**2 if label in ('same_value_at_selected_speed','different_value_at_another_speed') else 3
        sort=next(d['result']['result'] for d in doc['declarations'] if d['name']=='zer')
        callbacks(doc,model,{'zer':lambda stage:FunctionValue(tuple(sort['parameters']),sort['result'],lambda speed:c(val(stage,speed))),
            'zeq':lambda speed:c(4 if label=='wrong_current_function' else 2)})
        model['zet']=lambda agent,stage,alternative:agent=='agent' and stage=='motion' and alternative in ('motion','text') and label!='empty_candidates' and not(label=='first_excluded' and alternative=='motion') and not(label=='second_excluded' and alternative=='text')
        actual=values(doc,model,('agent','other'))
        expected=[label in ('two_values','wrong_current_function','different_value_at_another_speed'),label!='wrong_current_function']
        if actual!=expected:raise ValueError('Coefficient alternatives or current family binding differs: '+label+repr(actual))
        rows[label]=actual
    return {'cases':rows,'pointwise_witnesses_only':True,'one_equal_value_does_not_identify_functions':True,'knowledge_in_general_not_defined':True}


def finite_refusals():
    rows={}
    queries={
        'global_affine_representation':'k smd[k ja[] '+ZERO+' '+ZERO+' '+ZERO+' k bb[n p c b] '+ZERO+']',
        'full_time_formula':'k smi[k ja[] k bb[n p f b] k bb[n p d b] k bb[n p c b]]',
        'full_current_family_identity':'k smq[k zeq[] k zer[] k zes[] p ba]',
        'some_real_speed_distinguishes_candidates':'k smb[k zee[] k zes[] p ba p zet k zer[] p sca]',
    }
    for label,query in queries.items():
        doc=abstract(candidate(source_composed()[0],'r ja[] '+TAU+'.q['+query+'].'),ARITHMETIC)
        fixture=ConstructedCuts();model=guarded(doc);fixture.arithmetic(model)
        model.update(zee=lambda:'agent',zes=lambda:'motion',zet=lambda *args:True)
        sort=next(d['result']['result'] for d in doc['declarations'] if d['name']=='zer')
        callbacks(doc,model,{'ja':lambda x,y,z,t:fixture.make(2*fixture.read(t)),
            'zeq':lambda speed:fixture.make(2),
            'zer':lambda stage:FunctionValue(tuple(sort['parameters']),sort['result'],lambda speed:fixture.make(2))})
        try:values(doc,model,('agent',))
        except ValueError as error:
            if 'Cannot finitely quantify the rational number domain' not in str(error):raise
            rows[label]={'refused':True,'reason':str(error)}
        else:raise ValueError('Full real function condition replaced by samples')
    return rows


def attribution_checks():
    doc=parse(source_composed()[0]);doc['statements']=doc['statements'][-3:];rows={}
    for label in ('baseline','wrong_author','wrong_scope','wrong_context','wrong_origin_content','missing_brevity','wrong_premise','wrong_formula','wrong_unknown_content'):
        model=guarded(doc)
        for k,v in {'zev':'origin','zeu':'inference','zew':'unknown','rd':'author','rh':'scope','ri':'text'}.items():model[k]=lambda v=v:v
        symbol=lambda d:json.loads(d.syntax)['symbol']
        common=lambda a,s,c:(a,s,c)==('other' if label=='wrong_author' else 'author','other' if label=='wrong_scope' else 'scope','other' if label=='wrong_context' else 'text')
        model.update(ug=lambda node,a,d,s,c:common(a,s,c) and (node,symbol(d))==('origin','smn' if label=='wrong_origin_content' else 'smo'),
            zex=lambda node,a,s,c:common(a,s,c) and node=='origin' and label!='missing_brevity',
            zc=lambda node,a,p,d,s,c:common(a,s,c) and (node,symbol(p),symbol(d))==('inference','smo' if label=='wrong_premise' else 'smm','smo' if label=='wrong_formula' else 'smn'),
            uh=lambda node,a,d,s,c:common(a,s,c) and (node,symbol(d))==('unknown','smn' if label=='wrong_unknown_content' else 'smp'))
        actual=values(doc,model,('author','origin','inference','unknown','scope'))
        commonbad={'wrong_author','wrong_scope','wrong_context'}
        expected=[label not in commonbad|{'wrong_origin_content','missing_brevity'},label not in commonbad|{'wrong_premise','wrong_formula'},label not in commonbad|{'wrong_unknown_content'}]
        if actual!=expected:raise ValueError('Affine time attribution differs: '+label)
        rows[label]=actual
    return rows


def alignment():
    artifact=json.loads((ROOT/'artifacts/written-units-v1/einstein-1905.json').read_text(encoding='utf-8'));rows=[]
    entries=(
        ('einstein-1905:u0062','c2c9f28feab40584b4e0bb6f5d3048d629228c9f68eb4d01748abb20d0a28a7d',['smd','sme','smf','smm'],[('M0111','700a7fdfb3e6ad045fb18df09fc70eee7632677a54d49c061b0177d7e5bd8931')]),
        ('einstein-1905:u0063','9fb3b0a74ad53e1ea92bcacbffca829131c7d546a13170fae1b910193dc73dba',['smh','smi','smj','smn'],[('M0112','3f374d01fb620d1f76819488beb804776a723ce60d522ef62eb8a61b5e57aabe')]),
        ('einstein-1905:u0064','7fa94b491da65dd0b7546e50842ecfd4c684a4e2162104cfcfeb7b1cbdb9de4e',['sma','smb','smj','smk','sml','smo','smp','smq','smr'],[
            ('M0113','042b89ad42ef414a9da2ee9d15aec02f2a6176fd7affd185ae633e9eea190de2'),('M0114','b7d0bd6d5b7cce011239b3dfd3dc6b04923c155e19f76c99ecdf593c228edb57'),
            ('M0115','2f2fdc1fbf92378b4b4b7b6595b152caa0828803e8f25965683ea9be5076bba3'),('M0116','103f515a57432e988c887a7f1454e0bcceb13f6b751a41b5ccce4e4c35a95a57'),('M0117','2647dd13cdecfceb48ac1b9f39431cd758a364bd52fd43ecc15b154d573d7a4b')]))
    for uid,digest,defs,maths in entries:
        unit=next(u for u in artifact['units'] if u['id']==uid)
        if hashlib.sha256(unit['text'].encode('utf-8')).hexdigest()!=digest:raise ValueError('Affine time source changed')
        rows.append({'unit':uid,'unit_sha256':digest,'start':0,'end':len(unit['text']),'source':unit['text'],'definitions':defs,'status':'partial_explicit_reading','full_semantic_equivalence':False})
        for mid,mdigest in maths:
            m=next(m for m in artifact['math'] if m['id']==mid)
            if hashlib.sha256(m['mathml'].encode('utf-8')).hexdigest()!=mdigest:raise ValueError('Affine time math changed')
            rows.append({'unit':uid,'unit_sha256':digest,'math_id':mid,'math_sha256':mdigest,'definitions':defs,'status':'partial','full_semantic_equivalence':False})
    return {'segments':rows,'facsimile_checked':False,'verified_full_units':0,'origin_choice_and_unfixed_scale_separated':True}


def build_report():
    documents={}
    for compose in (generic_composed,source_composed):
        text,basis=compose();doc=parse(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text:raise ValueError('Stored affine time form differs')
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Affine time roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis)
    paths=[*documents,'data/affine-time-form-basis-v1.json','data/einstein-affine-time-form-basis-v1.json',
        'examples/v014/einstein-transverse-time.noema','examples/v014/transverse-time.noema',
        'scripts/compose_affine_time_form.py','scripts/check_affine_time_form.py','scripts/check_tau_differential.py',
        'noema/discourse.py','noema/finite_semantics.py','noema/polynomial_proofs.py']
    text=source_composed()[0];previous=(ROOT/'examples/v014/einstein-transverse-time.noema').read_text(encoding='utf-8')
    return {'status':'partial_affine_time_formula_origin_and_unfixed_scale','documents':documents,
        'polynomial_lemmas':polynomial_checks(),'expressions':formula_checks(),'coefficient_binding':coefficient_checks(),
        'origin_convention':origin_checks(),'unfixed_scale':uncertainty_checks(),'finite_refusals':finite_refusals(),
        'attribution':attribution_checks(),'alignment':alignment(),'roundtrips':True,
        'verified_full_units':{'einstein-1905':0,'kant-1784':0},
        'notation_size':{'canonical_source_document_characters':len(text),'added_characters':len(text)-len(previous)},
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args();report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Affine time report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Affine coefficient constraints, coincident origins and unfixed functions checked')


if __name__=='__main__':main()
