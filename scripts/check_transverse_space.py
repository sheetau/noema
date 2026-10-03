"""Check both transverse axes, their distinct events and the component speed."""
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
from scripts.check_real_products import MEANINGS, call, op, assertion
from scripts.check_moving_light_trip import literal
from scripts.check_tau_differential import ARITHMETIC, ConstructedCuts
from scripts.check_transverse_time import square_root
from scripts.compose_transverse_space import ROOT, generic_composed, source_composed

REPORT=ROOT/'reports/transverse-space-v1.json'
DOMAIN=('rs_y','ms_y','rs_z','ms_z','ray_y','ray_z','y0','y1','z0','z1','ry0','ry1','my0','my1','rz0','rz1','mz0','mz1',
    'rest','moving','x','y','z','t','time','length','axis_y','axis_z','other')


def polynomial_checks():
    V,v,w,a,i,j,h,t,x,q,extra=('v '+n for n in ('light','speed','component','scale','inverse','squaredinverse','distance','time','xprime','coordinate','extra'))
    mul=lambda a,b:call('ad',a,b);add=lambda a,b:call('ab',a,b)
    ray=call('snw',V,v,w,h,t,x);inverse=call('sja',literal(1),w,i);reduced=call('snx',V,a,i,h)
    claims={
        'chain_at_xprime_zero_iff_tau_and_reduced_coordinate':assertion('light speed component scale inverse squaredinverse distance time xprime tau coordinate',op('y',op('w',ray,op('w',inverse,call('sly',V,v,j))),op('z',call('snz',V,v,a,j,x,t,'v tau',q),op('w',op('e','v tau',mul(a,t)),op('e',q,reduced))))),
        'transverse_time_substitution_iff_coordinate_formula':assertion('light speed component scale inverse distance time coordinate',op('y',op('w',call('snw',V,v,w,h,t,literal(0)),inverse),op('z',call('sny',V,v,a,w,i,h,t,q),op('e',q,reduced)))),
        'xprime_zero_removes_longitudinal_time_term':assertion('light speed component scale inverse squaredinverse distance time xprime',op('y',op('w',ray,op('w',inverse,call('sly',V,v,j))),op('e',mul(V,call('slz',V,v,a,j,x,t)),reduced))),
        'rest_path_square_includes_longitudinal_motion':assertion('light speed component time',op('y',call('sla',V,v,w),op('e',mul(mul(V,t),mul(V,t)),add(mul(mul(v,t),mul(v,t)),mul(mul(w,t),mul(w,t)))))),
        'positive_diagonal_geometry_gives_transverse_travel_time':assertion('light speed component distance time',op('y',op('w',call('sla',V,v,w),op('w',call('aa',literal(0),t),op('w',call('aa',literal(0),h),op('e',mul(mul(V,t),mul(V,t)),add(mul(mul(v,t),mul(v,t)),mul(h,h)))))),op('e',h,mul(w,t)))),
        'stationary_limit_keeps_scale_a':assertion('light scale inverse distance',op('y',call('sja',literal(1),V,i),op('e',call('snx',V,a,i,h),mul(a,h)))),
        'extra_longitudinal_term_is_invisible_on_transverse_rays':assertion('light speed component scale inverse distance time xprime extra',op('y',ray,op('e',add(reduced,mul(extra,x)),reduced))),
        'total_speed_can_replace_component_in_denominator':assertion('',op('e',call('snx',literal(5),literal(2),literal(Fraction(1,4)),literal(8)),call('snx',literal(5),literal(2),literal(Fraction(1,5)),literal(8)))),
        'moving_clock_can_replace_rest_time':assertion('',op('y',call('snw',literal(5),literal(3),literal(4),literal(8),literal(2),literal(0)),op('e',literal(8),mul(literal(4),literal(4))))),
        'transverse_ray_agreement_forces_global_formula':assertion('',op('e',add(call('snx',literal(5),literal(2),literal(Fraction(1,4)),literal(8)),literal(1)),call('snx',literal(5),literal(2),literal(Fraction(1,4)),literal(8)))),
    }
    rejected={'total_speed_can_replace_component_in_denominator','moving_clock_can_replace_rest_time','transverse_ray_agreement_forces_global_formula'}
    rows={}
    for name,claim in claims.items():
        result=verify_universal(parse(generic_composed()[0]+claim),MEANINGS,timeout_ms=15000)[0]
        if result['status']!=('invalid' if name in rejected else 'valid'):raise ValueError('Transverse spatial algebra differs: '+name)
        rows[name]=result
    return {'claims':rows,'rational_polynomial_lemmas_only':True,'global_coordinate_transform_proved':False}


def axis_model(doc,label='baseline'):
    fixture=ConstructedCuts();n=fixture.read;c=fixture.make;model=guarded(doc);fixture.arithmetic(model)
    speed=0 if label=='stationary_limit' else 5 if label=='light_speed_boundary' else 3
    component=5 if label=='stationary_limit' else 4
    coords={};paths={};ends={}
    for axis,t in (('y',2),('z',3)):
        slot=1 if axis=='y' else 2
        coords['r'+axis+'0']=[0,0,0,0];coords['m'+axis+'0']=[0,0,0,0]
        coords['r'+axis+'1']=[speed*t,0,0,t];coords['r'+axis+'1'][slot]=component*t
        coords['m'+axis+'1']=[0,0,0,2*t];coords['m'+axis+'1'][slot]=10*t
        paths['rs_'+axis]=5*t;paths['ms_'+axis]=10*t
        ends['rs_'+axis]=t;ends['ms_'+axis]=2*t
    if label=='nonzero_xprime':coords['ry1'][0]+=1
    if label=='wrong_rest_time':coords['ry1'][3]=3
    if label=='wrong_moving_time':coords['my1'][3]=2
    if label=='wrong_other_transverse':coords['ry1'][2]=1
    if label=='nonzero_moving_xi':coords['my1'][0]=1
    if label=='wrong_moving_distance':coords['my1'][1]=16
    if label=='reverse_direction':coords['my1'][1]=-20
    if label=='reuse_y_coordinates_for_z':coords['mz1'][2]=20
    if label=='diagonal_path_replaced_by_transverse_distance':paths['rs_y']=8
    if label=='negative_path_root':paths['rs_y']=-10
    for k,value in {'ra':'rest','zbm':'moving','rb':'time','ta':'length','yn':'x','yo':'y','yp':'y' if label=='duplicate_axes' else 'z','zc7':'t','zb6':'other' if label=='wrong_context' else 'motion'}.items():model[k]=lambda value=value:value
    axisof=lambda segment:'z' if segment.endswith('_z') else 'y'
    model.update(tc=lambda:c(5),zb7=lambda:c(speed),
        sky=lambda value:c(5) if label=='total_speed_as_component' else square_root(fixture,value),
        zfa=lambda axis:'rs_'+('z' if axis=='z' else 'y'),
        zfb=lambda axis:'ms_y' if label=='z_uses_y_segment' else 'ms_'+('z' if axis=='z' else 'y'),
        wf=lambda segment:'other' if label=='different_ray' and segment=='rs_y' else 'ray_'+axisof(segment),
        wi=lambda segment:'other' if label=='different_departure' and segment=='rs_y' else axisof(segment)+'0',
        wj=lambda segment:'other' if label=='different_arrival' and segment=='rs_y' else axisof(segment)+'1',
        wh=lambda segment:'other' if label=='wrong_emission' else axisof(segment)+'0',
        wo=lambda segment:c(1 if label=='nonzero_emission_clock' else 0),wp=lambda segment:c(ends.get(segment,2)),
        wq=lambda segment:c(paths.get(segment,10)),
        wa=lambda segment,f,tu,lu,ctx:segment in paths and f==('rest' if segment.startswith('rs') else 'moving') and (tu,lu,ctx)==('time','length','motion'),
        smk=lambda event,ctx:event in ('y0','z0') and ctx=='motion' and label!='wrong_origin',
        sfm=lambda ctx:ctx=='motion' and label!='wrong_motion',
        zdz=lambda event,f,ctx:('r' if f=='rest' else 'm')+(event if event in ('y0','y1','z0','z1') else 'y1'),
        zc6=lambda record,role:c(coords[record][('x','y','z','t').index(role)]),
        shd=lambda event,record,f,ctx:event in ('y0','y1','z0','z1') and ctx=='motion' and label!='missing_chart',
        zbo=lambda f,axis,ctx:'axis_'+('z' if axis=='z' else 'y'),
        zbw=lambda f,line,axis,ctx:(f,line,ctx)==('moving','axis_'+axis,'motion'),
        zdw=lambda ray,start,end,line,f,ctx:ray in ('ray_y','ray_z') and (start,end,line,f,ctx)==(ray[-1]+'0',ray[-1]+'1','axis_'+ray[-1],'moving','motion') and label!='wrong_axis_support')
    callbacks(doc,model,{'zd4':lambda x,y,z,t:c(2*n(t)-Fraction(3,8)*n(x)+(1 if label=='wrong_tau_function' else 0)),
        'zeq':lambda v:c(3 if label=='wrong_scale' else 2)})
    primitive_names={d['name'] for d in doc['declarations'] if d['kind']=='primitive'}
    return {k:v for k,v in model.items() if k in primitive_names},fixture


def ray_checks():
    text='q[k soc[k zfa[k yo[]] k zfb[k yo[]] k yo[] k zb6[]]].q[k soc[k zfa[k yp[]] k zfb[k yp[]] k yp[] k zb6[]]].'
    doc=abstract(candidate(source_composed()[0],text),ARITHMETIC|{'sky','smk','sfm','shd'})
    rows={}
    cases={
        'baseline':[True,True],'stationary_limit':[True,True],
        **{label:[False,True] for label in ('nonzero_xprime','wrong_rest_time','wrong_moving_time','wrong_other_transverse','nonzero_moving_xi','wrong_moving_distance','reverse_direction','diagonal_path_replaced_by_transverse_distance','negative_path_root','different_ray','different_departure','different_arrival')},
        'reuse_y_coordinates_for_z':[True,False],'z_uses_y_segment':[True,False],
        **{label:[False,False] for label in ('duplicate_axes','total_speed_as_component','wrong_origin','wrong_motion','missing_chart','wrong_axis_support','wrong_tau_function','wrong_context','light_speed_boundary','wrong_emission','nonzero_emission_clock')},
    }
    for label,expected in cases.items():
        model,_=axis_model(doc,label);actual=values(doc,model,DOMAIN)
        if actual!=expected:raise ValueError('Both transverse ray geometries differ: '+label+repr(actual))
        rows[label]=actual
    return {'cases':rows,'origin_motion_and_measurement_charts_are_oracles':True,'distinct_axis_events_and_distances':True,'rest_path_is_diagonal':True}


def equation_checks():
    text=''.join('q[k '+name+'[k wj[k zfb[k '+axis+'[]]] k '+axis+'[] k zb6[]]].' for axis in ('yo','yp') for name in ('soe','sof','sog'))
    doc=abstract(candidate(source_composed()[0],text),ARITHMETIC|{'sky'})
    rows={}
    cases={'baseline':[True]*6,'stationary_limit':[True]*6,
        'nonzero_xprime':[False,False,True,True,True,True],
        'wrong_moving_time':[False,True,True,True,True,True],
        'wrong_moving_distance':[False,True,False,True,True,True],
        'wrong_scale':[False,True,False,False,True,False],
        'total_speed_as_component':[False]*6,'light_speed_boundary':[False]*6,
        'reuse_y_coordinates_for_z':[True,True,True,False,True,False]}
    for label,expected in cases.items():
        model,_=axis_model(doc,label);actual=values(doc,model,DOMAIN)
        if actual!=expected:raise ValueError('Transverse spatial formulas differ: '+label+repr(actual))
        rows[label]=actual
    return {'cases':rows,'y_distance_eight_gives_eta_twenty':True,'z_distance_twelve_gives_zeta_thirty':True,'same_v_and_phi_used_for_both_axes':True}


def premise_checks():
    text='q[k soi[k zb6[]]].'
    doc=abstract(candidate(source_composed()[0],text),ARITHMETIC|{'soc','sbc','smw','smu','smj'})
    rows={}
    for label in ('baseline','no_y_ray','no_z_ray','z_uses_y_segment','missing_rest_law','missing_moving_law','bad_z_rest_segment','bad_z_moving_segment','missing_tau_form','wrong_context'):
        model,fixture=axis_model(doc,label);n=fixture.read
        model.update(soc=lambda r,m,axis,ctx:(r,m,ctx)==('rs_'+axis,'ms_'+axis,'motion') and not(label=='no_y_ray' and axis=='y') and not(label=='no_z_ray' and axis=='z'),
            sbc=lambda V,ctx:n(V)==5 and ctx=='motion' and label!='missing_rest_law',
            smw=lambda frame,V,ctx:frame=='moving' and n(V)==5 and ctx=='motion' and label!='missing_moving_law',
            smu=lambda segment,V,ctx,sync,rate,frame:n(V)==5 and ctx=='motion' and frame==('rest' if segment.startswith('rs') else 'moving') and not(label=='bad_z_rest_segment' and segment=='rs_z') and not(label=='bad_z_moving_segment' and segment=='ms_z'),
            smj=lambda fn,phi,V,v:n(V)==5 and n(v)==3 and n(phi(v))==2 and label!='missing_tau_form')
        actual=values(doc,model,DOMAIN)[0]
        if actual!=(label=='baseline'):raise ValueError('Both transverse premise scopes differ: '+label)
        rows[label]=actual
    return {'cases':rows,'premise_components_are_oracles':True,'both_axes_required':True}


def attribution_checks():
    doc=parse(source_composed()[0]);doc['statements']=doc['statements'][-5:];rows={}
    for label in ('baseline','wrong_author','wrong_scope','wrong_context','wrong_both_axes_content','wrong_prior_argument','wrong_eta_chain','wrong_time_condition','wrong_substitution_premise','wrong_eta_formula','wrong_zeta_formula','missing_second_analogy'):
        model=guarded(doc)
        for k,v in {'zfg':'both','zfc':'chain','zfd':'time','zfe':'eta','zff':'zeta','ze6':'prior','rd':'author','rh':'scope','ri':'text'}.items():model[k]=lambda v=v:v
        symbol=lambda d:json.loads(d.syntax)['symbol']
        common=lambda a,s,c:(a,s,c)==('other' if label=='wrong_author' else 'author','other' if label=='wrong_scope' else 'scope','other' if label=='wrong_context' else 'text')
        def inference(node,a,p,d,s,c):
            expected={'chain':('sok','som' if label=='wrong_eta_chain' else 'sol'),
                'time':('sok','sol' if label=='wrong_time_condition' else 'som'),
                'zeta':('sop','soo' if label=='wrong_zeta_formula' else 'soq')}
            return common(a,s,c) and node in expected and (symbol(p),symbol(d))==expected[node]
        def analogy(node,a,earlier,s,c):
            return common(a,s,c) and (node,earlier) in (('both','other' if label=='wrong_prior_argument' else 'prior'),('zeta','eta')) and not(label=='missing_second_analogy' and node=='zeta')
        model.update(ug=lambda node,a,d,s,c:common(a,s,c) and (node,symbol(d))==('both','sok' if label=='wrong_both_axes_content' else 'soj'),
            zc=inference,zep=analogy,zd3=lambda node,a,p,before,after,s,c:common(a,s,c) and (node,symbol(p),symbol(before),symbol(after))==('eta','sok' if label=='wrong_substitution_premise' else 'son','sol','soq' if label=='wrong_eta_formula' else 'soo'))
        actual=values(doc,model,('both','chain','time','eta','zeta','prior','author','scope'))
        expected=[True]*5
        if label in ('wrong_author','wrong_scope','wrong_context'):expected=[False]*5
        else:
            failures={'wrong_both_axes_content':0,'wrong_prior_argument':0,'wrong_eta_chain':1,'wrong_time_condition':2,'wrong_substitution_premise':3,'wrong_eta_formula':3,'wrong_zeta_formula':4,'missing_second_analogy':4}
            if label in failures:expected[failures[label]]=False
        if actual!=expected:raise ValueError('Transverse analogy or substitution attribution differs: '+label)
        rows[label]=actual
    return rows


def alignment():
    artifact=json.loads((ROOT/'artifacts/written-units-v1/einstein-1905.json').read_text(encoding='utf-8'));rows=[]
    unit_hashes=['7f3efa93e2ab7906c7f43254e25f0748d511ac50da09fab841dc046a200f93b0','c78058a1360dc2a207ef857cf23da0f751be67c0fa8276960e76c684cae69fe7','ad6f70890a12d8f25cf83a9ebb72fac6316cf86f4e2e27c3ef03027f2b994c84','6b5807ef1f04e6e218f3a774d532266ed89e6b55d60c3ba55f48c807d8682ea0','bb8c8605c55dcc2d650e87ecb9fb01b1c2a95e0fd8e03e2c87c2cf5ebeaf3b0b','35db3680de823dfa7e1eef299ccbb58c1230669aca3eaf36925ca1d133a7c8c1','856cc99d87343400dc05fe7d03fa666602a1d92c4fb0ee1f5ae2f0a5fb218eb8','b5ab13824f87d4b275e421df997ff7e7a012559a5dfdc4970abf0994e4cb19f5']
    math_hashes=['7551f0ded25f18a627b8127a4fc8e28fa453ea27e9dd70198de9da75e4595d90','9e78802b4747d5f381a71e0357e7f1c2aec0044c5d3e6b4ce25e0b265dad277d','586db76cd5211766e6d23436f5cadf6b1f775e64657395a733bc2f366fee8c50','74b304d8ff270c2ed78e89069ca9a9c5a4d1b0c807167b301b8f6fdcfef333ed']
    definitions=[['soc','sod','soi','soj'],['soe','sol'],['sof','som'],['sof','som'],['son','soo'],['sob','sog','soo'],['sop','soq'],['sob','sog','soq']]
    for index,(digest,defs) in enumerate(zip(unit_hashes,definitions),73):
        uid=f'einstein-1905:u{index:04d}';unit=next(u for u in artifact['units'] if u['id']==uid)
        if hashlib.sha256(unit['text'].encode('utf-8')).hexdigest()!=digest:raise ValueError('Transverse space source changed')
        rows.append({'unit':uid,'unit_sha256':digest,'start':0,'end':len(unit['text']),'source':unit['text'],'definitions':defs,'status':'partial_explicit_reading','full_semantic_equivalence':False})
        for mid in unit['math_ids']:
            m=next(m for m in artifact['math'] if m['id']==mid);mdigest=math_hashes[int(mid[1:])-130]
            if hashlib.sha256(m['mathml'].encode('utf-8')).hexdigest()!=mdigest:raise ValueError('Transverse space math changed')
            rows.append({'unit':uid,'unit_sha256':digest,'math_id':mid,'math_sha256':mdigest,'definitions':defs,'status':'partial','full_semantic_equivalence':False})
    return {'segments':rows,'facsimile_checked':False,'verified_full_units':0,'both_axis_equations_restricted_to_their_rays':True}


def build_report():
    documents={}
    for compose in (generic_composed,source_composed):
        text,basis=compose();doc=parse(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text:raise ValueError('Stored transverse space differs')
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Transverse space roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis)
    paths=[*documents,'data/transverse-space-basis-v1.json','data/einstein-transverse-space-basis-v1.json',
        'examples/v014/einstein-longitudinal-light.noema','examples/v014/longitudinal-light.noema',
        'scripts/compose_transverse_space.py','scripts/check_transverse_space.py','scripts/check_tau_differential.py','scripts/check_transverse_time.py',
        'noema/discourse.py','noema/finite_semantics.py','noema/polynomial_proofs.py']
    text=source_composed()[0];previous=(ROOT/'examples/v014/einstein-longitudinal-light.noema').read_text(encoding='utf-8')
    return {'status':'partial_transverse_spatial_light_substitutions','documents':documents,
        'polynomial_lemmas':polynomial_checks(),'axis_ray_geometry':ray_checks(),'equations':equation_checks(),
        'both_axis_premises':premise_checks(),'attribution':attribution_checks(),'alignment':alignment(),'roundtrips':True,
        'verified_full_units':{'einstein-1905':0,'kant-1784':0},
        'notation_size':{'canonical_source_document_characters':len(text),'added_characters':len(text)-len(previous)},
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args();report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Transverse space report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Both transverse ray geometries and spatial coordinate substitutions checked')


if __name__=='__main__':main()
