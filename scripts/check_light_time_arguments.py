"""Check quotient algebra, complete function arguments and same-event bindings."""
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
from scripts.check_rod_setup import callbacks, embedding, guarded
from scripts.check_rod_measurements import cut
from scripts.check_real_products import MEANINGS, call, op, assertion
from scripts.check_moving_light_trip import literal
from scripts.check_axial_clock_trip import arithmetic
from scripts.compose_light_time_arguments import ROOT, TAU, generic_composed, source_composed

REPORT=ROOT/'reports/light-time-arguments-v1.json'
ARITHMETIC_ABSTRACTIONS={'ba','sca','bg','bd','bf','shv','bj'}


def polynomial_checks():
    add=lambda x,y:call('ab',x,y);mul=lambda x,y:call('ad',x,y)
    sub=lambda x,y:add(x,call('ac',y));less=lambda x,y:call('aa',x,y)
    x,V,v,o,r,t,a,b,c=('v '+n for n in ('label','light','speed','outward','returning','moment','space','time','offset'))
    base=call('sjb',x,V,v,o,r)
    f=lambda xp,time:call('sjc',a,b,c,xp,time)
    midpoint=call('siq',f(literal(0),t),f(x,add(t,o)),f(literal(0),add(add(t,o),r)))
    nonzero='u[e['+x+']['+literal(0)+']]'
    claims={
        'positive_denominator_quotient_unique':assertion('label light outward returning',op('y',op('w',call('sja',x,V,o),call('sja',x,V,r)),op('e',o,r))),
        'positive_label_gives_causal_event_order':assertion('label light speed outward returning moment',op('y',op('w',base,less(literal(0),x)),op('w',less(t,add(t,o)),less(add(t,o),add(add(t,o),r))))),
        'affine_candidate_midpoint_iff_coefficient_condition':assertion('label light speed outward returning moment space time offset',op('y',op('w',base,nonzero),op('z',midpoint,op('e',add(mul(a,sub(mul(V,V),mul(v,v))),mul(b,v)),literal(0))))),
        'swapping_elapsed_times_preserves_quotients':assertion('label light speed outward returning',op('y',base,call('sjb',x,V,v,r,o))),
        'rest_time_is_always_synchronized_moving_time':assertion('label light speed outward returning moment',op('y',op('w',base,less(literal(0),x)),call('siq',t,add(t,o),add(add(t,o),r)))),
    }
    first,middle,last,x0,x1,x2=('v '+n for n in ('first','middle','last','xfirst','xmiddle','xlast'))
    guards=['u['+less(v,literal(0))+']',less(v,V),op('e',sub(x0,mul(v,first)),literal(0)),
        op('e',sub(x1,mul(v,middle)),x),op('e',sub(x2,mul(v,last)),literal(0))]
    premise=guards[0]
    for guard in guards[1:]:premise=op('w',premise,guard)
    light_legs=op('w',op('e',mul(V,sub(middle,first)),sub(x1,x0)),op('e',mul(V,sub(last,middle)),sub(x1,x2)))
    claims['same_event_coordinates_light_legs_iff_elapsed_quotients']=assertion(
        'label light speed first middle last xfirst xmiddle xlast',
        op('y',premise,op('z',light_legs,call('sjb',x,V,v,sub(middle,first),sub(last,middle)))))
    rows={}
    for name,claim in claims.items():
        result=verify_universal(parse(generic_composed()[0]+claim),MEANINGS,timeout_ms=15000)[0]
        expected='invalid' if name in ('swapping_elapsed_times_preserves_quotients','rest_time_is_always_synchronized_moving_time') else 'valid'
        if result['status']!=expected:raise ValueError('Light-time algebra differs: '+name)
        rows[name]=result
    return {'claims':rows,'rational_polynomial_lemmas_only':True,'tau_formula_derived':False}


def reciprocal_reuse():
    old=parse((ROOT/'examples/v011/real-products.noema').read_text(encoding='utf-8'))
    new=parse(source_composed()[0])
    first=next(d.copy() for d in old['declarations'] if d['name']=='cf')
    second=next(d.copy() for d in new['declarations'] if d['name']=='sjd')
    first.pop('name');second.pop('name')
    if first!=second:raise ValueError('Positive reciprocal no longer matches the preserved definition')
    return {'same_definition_modulo_symbol':True,'general_real_field_laws_proved':False}


def expression_checks():
    doc=abstract(candidate(source_composed()[0],'''
r ja[] '''+TAU+'''.r jb[] h[b] c.r jc[] h[b] c.r jd[] h[b] c.r je[] h[b] c.
q[k sjg[k ja[] k jb[] k jc[] k jd[] k je[]]].'''),ARITHMETIC_ABSTRACTIONS|{'sje'})
    rows={}
    names=('baseline','shifted_time_origin','negative_label_algebra_only','wrong_outward_denominator','wrong_return_denominator',
        'wrong_tau_space_sign','rest_time_function','ignores_time','invalid_function_value','invalid_input',
        'light_speed_boundary','above_light_speed','negative_speed')
    for name in names:
        model=guarded(doc);arithmetic(model);calls=[]
        label=-12 if name=='negative_label_algebra_only' else 12
        speed=3 if name=='light_speed_boundary' else 4 if name=='above_light_speed' else -1 if name=='negative_speed' else 1
        time=2 if name=='shifted_time_origin' else 0
        model.update(jb=lambda:cut(label),jc=lambda:cut(3),jd=lambda:cut(speed),je=lambda:cut(time))
        def divide(n,d):
            n,d=embedding(n),embedding(d)
            if name=='wrong_outward_denominator' and d==2:d=4
            if name=='wrong_return_denominator' and d==4:d=2
            # The rejected v>V fixture is outside the partial operation domain.
            if d<=0 or Fraction(n,d).denominator!=1:return cut(0)
            return cut(n//d)
        def function(x,y,z,t):
            args=tuple(embedding(q) for q in (x,y,z,t));calls.append(args);x,y,z,t=args
            if name=='invalid_function_value':return cut(30)
            if name=='rest_time_function':return cut(t)
            return cut((0 if name=='ignores_time' else 2*t)+(1 if name=='wrong_tau_space_sign' else -1)*Fraction(x,4))
        model['sje']=divide
        if name=='invalid_input':model['ba']=lambda v:abs(embedding(v))<30 and embedding(v)!=12
        callbacks(doc,model,{'ja':function})
        actual=values(doc,model,('object',))[0]
        expected=name in ('baseline','shifted_time_origin','negative_label_algebra_only')
        if actual!=expected:raise ValueError('Expanded tau expression differs: '+name+repr(actual))
        if name in ('baseline','shifted_time_origin'):
            expected_args={(0,0,0,time),(12,0,0,time+6),(0,0,0,time+9)}
            if set(calls)!=expected_args:raise ValueError('Tau argument tuple changed')
        rows[name]={'condition':actual,'argument_tuples':[list(args) for args in sorted(set(calls))]}
    return {'cases':rows,'constructed_integer_cuts_and_division_oracles':True,'negative_label_not_a_causal_trip_claim':True}


def source_checks():
    doc=abstract(candidate(source_composed()[0],'q[k sjl[k zb6[]]].'),ARITHMETIC_ABSTRACTIONS|{'six','sbc','sba','shd','sio'})
    rows={};domain=('depart','reflect','arrive','ray','out','back','r0','r1','r2','rest','moving','time','length','x','y','z','t','axis','trial','other')
    names=('baseline','missing_prior_trip','constant_speed_not_assumed','missing_outward_segment','missing_return_segment',
        'different_outward_ray','different_return_ray','swapped_segment_events','missing_rest_chart','wrong_coordinate_event',
        'wrong_outward_start_time','wrong_return_end_time','wrong_outward_path','wrong_return_path',
        'outward_not_in_law_scope','return_not_in_law_scope','wrong_axis','return_off_axis',
        'wrong_auxiliary_label','wrong_departure_label','wrong_y','wrong_z','wrong_function_binding','candidate_fails_correspondence',
        'wrong_clock_reading','wrong_rest_frame','wrong_time_unit','wrong_length_unit','wrong_context','negative_label','light_speed_boundary')
    for name in names:
        model=guarded(doc);arithmetic(model)
        constants={'ra':'moving' if name=='wrong_rest_frame' else 'rest','zbm':'moving','rb':'length' if name=='wrong_time_unit' else 'time',
            'ta':'time' if name=='wrong_length_unit' else 'length','zb6':'other' if name=='wrong_context' else 'motion',
            'zdq':'trial','zdx':'out','zdy':'back','yn':'x','yo':'y','yp':'z','zc7':'t'}
        for k,v in constants.items():model[k]=lambda v=v:v
        tuples={'depart':'r0','reflect':'r1','arrive':'r2'}
        if name=='wrong_coordinate_event':tuples['reflect']='r0'
        coords={'r0':(1 if name=='wrong_departure_label' else 0,0,0,0),
            'r1':(18,1 if name=='wrong_y' else 0,1 if name=='wrong_z' else 0,6),'r2':(9,0,0,9)}
        legs={'out':('depart','reflect',0,6,18),'back':('reflect','arrive',6,9,9)}
        def leg(s):return legs.get(s,legs['out'])
        model.update(six=lambda ctx:ctx=='motion' and name!='missing_prior_trip',
            sbc=lambda v,ctx:embedding(v)==3 and ctx=='motion' and name!='constant_speed_not_assumed',
            sba=lambda s,v,ctx,*args:s in legs and embedding(v)==3 and ctx=='motion' and not(name=='missing_'+('outward' if s=='out' else 'return')+'_segment'),
            shd=lambda e,t,f,ctx:(e,t) in {('depart','r0'),('reflect','r1'),('arrive','r2')} and (f,ctx)==('rest','motion') and not(name=='missing_rest_chart' and e=='arrive'),
            sio=lambda f:name!='candidate_fails_correspondence',
            zdz=lambda e,f,ctx:tuples.get(e,'r0'),zc6=lambda tup,r:cut(coords.get(tup,(0,0,0,0))[('x','y','z','t').index(r)]),
            tc=lambda:cut(1 if name=='light_speed_boundary' else 3),zb7=lambda:cut(1),
            zdt=lambda:cut(-12 if name=='negative_label' else 16 if name=='wrong_auxiliary_label' else 12),
            qe=lambda tr:'depart',qf=lambda tr:'reflect',qg=lambda tr:'arrive',qh=lambda tr:'ray',
            qi=lambda tr:cut(0),qj=lambda tr:cut(10 if name=='wrong_clock_reading' else 9),qk=lambda tr:cut(18),
            wa=lambda s,f,t,l,ctx:s in legs and (f,t,l,ctx)==('rest','time','length','motion') and not(name==('outward' if s=='out' else 'return')+'_not_in_law_scope'),
            wf=lambda s:'other' if name=='different_'+('outward' if s=='out' else 'return')+'_ray' else 'ray',
            wi=lambda s:leg(s)[1] if name=='swapped_segment_events' else leg(s)[0],wj=lambda s:leg(s)[1],
            wo=lambda s:cut(1 if name=='wrong_outward_start_time' and s=='out' else leg(s)[2]),
            wp=lambda s:cut(10 if name=='wrong_return_end_time' and s=='back' else leg(s)[3]),
            wq=lambda s:cut(leg(s)[4]+(1 if name=='wrong_'+('outward' if s=='out' else 'return')+'_path' else 0)),
            zbo=lambda f,r,ctx:'axis',zbw=lambda f,a,r,ctx:(f,a,r,ctx)==('rest','axis','x','motion') and name!='wrong_axis',
            zdw=lambda r,a,b,axis,f,ctx:(r,axis,f,ctx)==('ray','axis','rest','motion') and (a,b) in {('depart','reflect'),('reflect','arrive')} and not(name=='return_off_axis' and a=='reflect'))
        callbacks(doc,model,{'zd4':lambda x,y,z,t:cut(2*embedding(t)+(1 if name=='wrong_function_binding' else -1)*Fraction(embedding(x),4))})
        actual=values(doc,model,domain)[0]
        if actual!=(name=='baseline'):raise ValueError('Light-time source coupling differs: '+name+repr(actual))
        rows[name]=actual
    return {'cases':rows,'prior_trip_light_law_segment_measurement_charts_and_candidate_are_oracles':True,
        'constructed_integer_cut_operations_are_oracles':True,'full_physical_derivation_proved':False}


def attribution_checks():
    doc=parse(source_composed()[0]);doc['statements']=doc['statements'][-1:];rows={}
    for name in ('baseline','wrong_author','wrong_premise','wrong_before','wrong_after','wrong_scope','wrong_context'):
        model=guarded(doc)
        for k,v in {'zd2':'rewrite','rd':'author','rh':'scope','ri':'text'}.items():model[k]=lambda v=v:v
        symbol=lambda d:json.loads(d.syntax)['symbol']
        model['zd3']=lambda n,a,p,b,c,s,ctx:(n,a,s,ctx)==('rewrite','other' if name=='wrong_author' else 'author','other' if name=='wrong_scope' else 'scope','other' if name=='wrong_context' else 'text') and (symbol(p),symbol(b),symbol(c))==('sjl' if name=='wrong_premise' else 'sjm','siy' if name=='wrong_before' else 'siz','sjm' if name=='wrong_after' else 'sjn')
        actual=values(doc,model,('rewrite','author','scope'))[0]
        if actual!=(name=='baseline'):raise ValueError('Clock equation reformulation attribution differs')
        rows[name]=actual
    return rows


def alignment():
    artifact=json.loads((ROOT/'artifacts/written-units-v1/einstein-1905.json').read_text(encoding='utf-8'));rows=[]
    for uid,digest,mid,mdigest,defs in (
        ('einstein-1905:u0051','07a0a0ca9af7c3dcaeb84f27f6691d4226fb9d6c41c32c92d462f8430444a9a8','M0099','700a7fdfb3e6ad045fb18df09fc70eee7632677a54d49c061b0177d7e5bd8931',['sjj','sjk','sjl','sjm']),
        ('einstein-1905:u0052','f924b6f1554c1639a7ca909d4509ff6ab1f6b6a0e3c9b4456e45cda7279ca1d8','M0100','4c71fca794b6470984ef5bfc2130b129b69ecbf9c0bcb216fbc12aef96f6dd4e',['sjf','sjg','sjn']),
        ('einstein-1905:u0053','19b139e874970012bf62b5d0ecf7059f7ff16929c41929f3f8223cf0e3be30bf','M0101','acc12892bded67277296a0d76e811b12c38004da5e2aeefc9e277cad48a216e4',['sjf','sjg','sjn'])):
        unit=next(u for u in artifact['units'] if u['id']==uid);math=next(m for m in artifact['math'] if m['id']==mid)
        if hashlib.sha256(unit['text'].encode('utf-8')).hexdigest()!=digest:raise ValueError('Light-time source changed')
        if hashlib.sha256(math['mathml'].encode('utf-8')).hexdigest()!=mdigest:raise ValueError('Light-time formula changed')
        rows+=[{'unit':uid,'unit_sha256':digest,'start':0,'end':len(unit['text']),'source':unit['text'],'definitions':defs,
            'status':'partial_explicit_reading','full_semantic_equivalence':False},
            {'unit':uid,'unit_sha256':digest,'math_id':mid,'math_sha256':mdigest,'definitions':defs,'status':'partial','full_semantic_equivalence':False}]
    return {'segments':rows,'facsimile_checked':False,'verified_full_units':0,'left_and_right_math_fragments_joined':True}


def build_report():
    documents={}
    for compose in (generic_composed,source_composed):
        text,basis=compose();doc=parse(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text:raise ValueError('Stored light-time arguments differ')
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Light-time roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis)
    paths=[*documents,'data/light-time-arguments-basis-v1.json','data/einstein-light-time-arguments-basis-v1.json',
        'examples/v014/einstein-axial-clock-trip.noema','examples/v011/real-products.noema',
        'scripts/compose_light_time_arguments.py','scripts/check_light_time_arguments.py',
        'noema/discourse.py','noema/finite_semantics.py','noema/polynomial_proofs.py']
    text=source_composed()[0];previous=(ROOT/'examples/v014/einstein-axial-clock-trip.noema').read_text(encoding='utf-8')
    return {'status':'partial_light_time_arguments_and_clock_equation_reformulation','documents':documents,
        'polynomial_lemmas':polynomial_checks(),'reciprocal_reuse':reciprocal_reuse(),'expanded_expression':expression_checks(),
        'source_coupling':source_checks(),'attribution':attribution_checks(),'alignment':alignment(),'roundtrips':True,
        'verified_full_units':{'einstein-1905':0,'kant-1784':0},
        'notation_size':{'canonical_source_document_characters':len(text),'added_characters':len(text)-len(previous)},
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args();report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Light-time report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Light-time arguments, quotient lemmas and same-event coupling checked')


if __name__=='__main__':main()
