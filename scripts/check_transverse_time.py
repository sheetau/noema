"""Check transverse components, both trial scopes and the y/z argument roles."""
import argparse
from fractions import Fraction
import hashlib
from math import isqrt
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
from scripts.compose_transverse_time import ROOT, CUT, TAU, generic_composed, source_composed, transverse_protocol

REPORT=ROOT/'reports/transverse-time-v1.json'


def square_root(fixture,value):
    n=fixture.read(value)
    if n<0:return fixture.make(0)  # Outside the source guard; never a root claim.
    a,b=isqrt(n.numerator),isqrt(n.denominator)
    if (a*a,b*b)!=(n.numerator,n.denominator):raise ValueError('Fixture square root is not rational')
    return fixture.make(Fraction(a,b))


def polynomial_checks():
    V,v,w,u,h,d,t,a,b,c,e,o=('v '+n for n in ('light','speed','transverse','other','length','duration','moment','a','b','c','timecoef','offset'))
    add=lambda x,y:call('ab',x,y);mul=lambda x,y:call('ad',x,y);lt=lambda x,y:call('aa',x,y)
    base=call('sla',V,v,w)
    first,middle,last=('v '+n for n in ('first','middle','last'))
    claims={
        'positive_transverse_component_unique':assertion('light speed transverse other',op('y',op('w',base,call('sla',V,v,u)),op('e',w,u))),
        'component_below_total_speed_when_motion_is_positive':assertion('light speed transverse',op('y',base,op('z',lt(w,V),lt(literal(0),v)))),
        'equal_transverse_legs_give_rest_time_midpoint':assertion('length transverse first middle last',op('y',call('slb',h,w,first,middle,last),call('siq',first,middle,last))),
        'derivative_time_terms_cancel':assertion('transverse a timecoef other',op('y',call('sja',literal(1),w,u),op('z',call('slc',w,a,e,u),op('e',a,literal(0))))),
        'stationary_path_norm_retains_total_light_speed':assertion('light speed transverse duration',op('y',base,op('e',add(mul(mul(v,d),mul(v,d)),mul(mul(w,d),mul(w,d))),mul(mul(V,d),mul(V,d))))),
        'total_light_speed_can_replace_transverse_component':assertion('',op('y',call('sla',literal(5),literal(3),literal(4)),op('e',literal(4),literal(5)))),
    }
    for axis in ('y','z'):
        x,y,z=('v '+n for n in ('x','y','z'))
        f=lambda xx,yy,zz,tt:call('sld',a,b,c,e,o,xx,yy,zz,tt)
        shifted=(x,add(y,h),z) if axis=='y' else (x,y,add(z,h))
        midpoint=call('siq',f(x,y,z,t),f(*shifted,add(t,d)),f(x,y,z,add(add(t,d),d)))
        premise=op('w',lt(literal(0),h),op('w',lt(literal(0),w),op('e',mul(w,d),h)))
        claims[axis+'_affine_midpoint_iff_zero_axis_coefficient']=assertion('a b c timecoef offset x y z moment length transverse duration',op('y',premise,op('z',midpoint,op('e',b if axis=='y' else c,literal(0)))))
    rows={}
    for name,claim in claims.items():
        result=verify_universal(parse(generic_composed()[0]+claim),MEANINGS,timeout_ms=15000)[0]
        if result['status']!=('invalid' if name=='total_light_speed_can_replace_transverse_component' else 'valid'):raise ValueError('Transverse algebra differs: '+name)
        rows[name]=result
    return {'claims':rows,'rational_polynomial_lemmas_only':True,'general_chain_rule_or_physical_geometry_proved':False}


def reuse_checks():
    source=parse(source_composed()[0]);decls={d['name']:d for d in source['declarations']}
    old=parse((ROOT/'examples/v011/real-products.noema').read_text(encoding='utf-8'))
    root=next(d.copy() for d in old['declarations'] if d['name']=='cj');root['name']='sky'
    if root!=decls['sky']:raise ValueError('Square root differs from preserved definition')
    parent=parse((ROOT/'examples/v014/einstein-arbitrary-origins.noema').read_text(encoding='utf-8'))
    parent['declarations'].append(transverse_protocol(parent))
    expected=next(d for d in parse(format_graph(parent,'compact'))['declarations'] if d['name']=='slo')
    if expected!=decls['slo']:raise ValueError('Transverse protocol changed beyond its axis parameter and guard')
    return {'nonnegative_square_root_reused':True,'prior_trial_protocol_generalized_only_by_axis':True}


def speed_checks():
    doc=abstract(candidate(source_composed()[0],'r ja[] '+CUT+'.r jb[] '+CUT+'.r jc[] '+CUT+'.q[k skz[k ja[] k jb[] k jc[]]].'),ARITHMETIC|{'sky'})
    rows={}
    for name,(args,expected) in {
        'three_four_five':((5,3,4),True),'stationary_limit':((5,0,5),True),'other_triangle':((5,4,3),True),
        'negative_root':((5,3,-4),False),'zero_root':((5,3,0),False),'total_speed_substituted':((5,3,5),False),
        'light_speed_boundary':((5,5,0),False),'above_light_speed':((3,5,4),False),'negative_motion':((5,-3,4),False),
    }.items():
        fixture=ConstructedCuts();model=guarded(doc);fixture.arithmetic(model);model['sky']=lambda x:square_root(fixture,x)
        for symbol,value in zip(('ja','jb','jc'),args):model[symbol]=lambda value=value:fixture.make(value)
        actual=values(doc,model,('object',))[0]
        if actual!=expected:raise ValueError('Transverse square-root domain differs: '+name)
        rows[name]=actual
    return {'cases':rows,'exact_rational_root_fixtures_only':True,'total_speed_distinct_from_component':True}


def tau_checks():
    text='r ja[] '+TAU+'.'
    for name,args in (('skw','k bb[n p d b] k bb[n p c b] k bb[n p e b]'),('skx','k bb[n p e b] k bb[n p d b] k bb[n p c b]')):
        text+='q[k slf[k '+name+'[k ja[]] '+args+' k bb[n p b b] k bb[n p e b] k bb[n p i b]]].'
    for name,args in (('skw','k bb[n p d b] k bb[n p c b] k bb[n p e b]'),('skx','k bb[n p e b] k bb[n p d b] k bb[n p c b]')):
        text+='q[k sli[k '+name+'[k ja[]] '+args+' k bb[n p b b]]].'
    doc=abstract(candidate(source_composed()[0],text),ARITHMETIC|{'sjs'})
    rows={}
    for name in ('baseline','y_dependence','z_dependence','both_dependences','nonlinear_time','shifted_clock_origin'):
        fixture=ConstructedCuts();n=fixture.read;c=fixture.make;model=guarded(doc);fixture.arithmetic(model);calls=[]
        def function(x,y,z,t):
            args=tuple(n(q) for q in (x,y,z,t));calls.append(args);x,y,z,t=args
            return c(2*x+(2*y if name in ('y_dependence','both_dependences') else 0)+(3*z if name in ('z_dependence','both_dependences') else 0)+(t*t if name=='nonlinear_time' else 3*t)+(5 if name=='shifted_clock_origin' else 0))
        callbacks(doc,model,{'ja':function})
        model['sjs']=lambda domain,fn,p,value:domain(p) and n(value)==0 and all(n(fn(c(n(p)+h)))==n(fn(p)) for h in (-1,1,2))
        actual=values(doc,model,('object',))
        y=name not in ('y_dependence','both_dependences');z=name not in ('z_dependence','both_dependences')
        expected=[y and name!='nonlinear_time',z and name!='nonlinear_time',y,z]
        if actual!=expected:raise ValueError('Transverse tau arguments differ: '+name+repr(actual))
        required={(2,3,4,1),(2,11,4,3),(2,3,12,3),(2,3,4,5)}
        if not required.issubset(set(calls)):raise ValueError('Transverse reflection or return arguments missing')
        rows[name]=actual
    return {'cases':rows,'affine_fixture_partial_derivative_oracle':True,'equal_leg_midpoint_not_assumed_for_arbitrary_time_function':True}


def protocol_checks():
    doc=abstract(candidate(source_composed()[0],'r ja[] a.r jb[] a.r jc[] d.r jd[] a.q[k slo[k ja[] k jb[] k jc[] k jd[]]].'),ARITHMETIC|{'qo','sgp'})
    rows={};domain=('trial','point','mirror','ca','cb','depart','reflect','arrive','ray','axisy','axisz','x','y','z','moving','time','other')
    for name in ('y_axis','z_axis','x_axis_rejected','wrong_support_direction','missing_return','wrong_return_clock','unsynchronized','wrong_context'):
        fixture=ConstructedCuts();n=fixture.read;c=fixture.make;model=guarded(doc);fixture.arithmetic(model)
        role='z' if name=='z_axis' else 'x' if name=='x_axis_rejected' else 'y';axis='axisz' if role=='z' else 'axisy'
        for k,v in {'ja':'trial','jb':'point','jc':'other' if name=='wrong_context' else 'motion','jd':role,'zbm':'moving','rb':'time','yo':'y','yp':'z'}.items():model[k]=lambda v=v:v
        places={('ca','point'),('cb','mirror'),('depart','point'),('reflect','mirror'),('arrive','point')};reads={'depart':0,'reflect':1,'arrive':2}
        legs={('ray','depart','reflect','moving'),('ray','reflect','arrive','moving')}
        if name=='missing_return':legs.remove(('ray','reflect','arrive','moving'))
        model.update(te=lambda tr:'ca',tf=lambda tr:'cb',qc=lambda tr:'point',qd=lambda tr:'mirror',qe=lambda tr:'depart',qf=lambda tr:'reflect',qg=lambda tr:'arrive',qh=lambda tr:'ray',
            qi=lambda tr:c(0),qj=lambda tr:c(1),qk=lambda tr:c(2),qb=lambda a,b,f,u,ctx,tr:(a,b,f,u,ctx,tr)==('ca','cb','moving','time','motion','trial'),
            ca=lambda clock:clock in ('ca','cb'),ci=lambda u:u=='time',cd=lambda a,b:(a,b)==('ca','cb'),cb=lambda obj,p,f:(obj,p) in places and f=='moving',cc=lambda clock,f:clock in ('ca','cb') and f=='moving',
            ce=lambda clock,e,f,u,value:e in reads and (clock,f,u)==('cb' if e=='reflect' or (name=='wrong_return_clock' and e=='arrive') else 'ca','moving','time') and n(value)==reads[e],
            cf=lambda r:r=='ray',cg=lambda *args:args in legs,ch=lambda r,e,f:(r,e,f)==('ray','reflect','moving'),
            qo=lambda a,b,f,u,ctx:(a,b,f,u,ctx)==('ca','cb','moving','time','motion') and name!='unsynchronized',
            zbo=lambda f,r,ctx:'axisz' if r=='z' else 'axisy',zbw=lambda f,a,r,ctx:(f,a,r,ctx)==('moving',axis,role,'motion'),
            zbz=lambda f,clock,ctx:clock in ('ca','cb') and (f,ctx)==('moving','motion'),zcu=lambda p,f,ctx:p in ('point','mirror') and (f,ctx)==('moving','motion'),
            zef=lambda r,a,b,line,f,ctx:(r,a,b,f) in legs and (line,ctx)==(axis,'motion') and name!='wrong_support_direction',
            sgp=lambda e,p,f,u,ctx,*args:(e,p) in places and (f,u,ctx)==('moving','time','motion'),zbe=lambda e,f,u,ctx:c(reads.get(e,0)))
        actual=values(doc,model,domain)[0]
        if actual!=(name in ('y_axis','z_axis')):raise ValueError('Axis-parametric clock trial differs: '+name+repr(actual))
        rows[name]=actual
    return {'cases':rows,'synchrony_and_local_times_are_oracles':True,'both_transverse_roles_tested':True}


def geometry_checks():
    doc=abstract(candidate(source_composed()[0],'r ja[] a.r jb[] a.r jc[] d.q[k slp[k ja[] k jb[] k jc[]]].'),ARITHMETIC|{'sky','slo','skq'})
    rows={};domain=('trial','point','depart','reflect','arrive','r0','r1','r2','rest','x','y','z','t')
    names=('y_axis','z_axis','wrong_x_motion','other_transverse_coordinate_changes','wrong_return_position','wrong_outward_duration','wrong_return_duration','total_speed_as_component','negative_component','wrong_distance','missing_protocol','wrong_clock_function','wrong_context')
    for name in names:
        fixture=ConstructedCuts();n=fixture.read;c=fixture.make;model=guarded(doc);fixture.arithmetic(model);model['sky']=lambda value:square_root(fixture,value)
        role='z' if name=='z_axis' else 'y';axis=2 if role=='z' else 1;other=1 if axis==2 else 2
        coords={'r0':[5,3,7,1],'r1':[11,3,7,3],'r2':[17,3,7,5]};coords['r1'][axis]+=8
        if name=='wrong_x_motion':coords['r1'][0]+=1
        if name=='other_transverse_coordinate_changes':coords['r1'][other]+=1
        if name=='wrong_return_position':coords['r2'][axis]+=1
        if name=='wrong_outward_duration':coords['r1'][3]=4
        if name=='wrong_return_duration':coords['r2'][3]=6
        for k,v in {'ja':'trial','jb':role,'jc':'other' if name=='wrong_context' else 'motion','ra':'rest','yn':'x','yo':'y','yp':'z','zc7':'t'}.items():model[k]=lambda v=v:v
        model.update(qc=lambda tr:'point',qe=lambda tr:'depart',qf=lambda tr:'reflect',qg=lambda tr:'arrive',
            slo=lambda tr,p,ctx,axis:(tr,p,ctx,axis)==('trial','point','motion',role) and name!='missing_protocol',
            skq=lambda tr,ctx:(tr,ctx)==('trial','motion') and name!='wrong_clock_function',
            zdz=lambda e,f,ctx:{'depart':'r0','reflect':'r1','arrive':'r2'}.get(e,'r0'),
            zc6=lambda record,component:c(coords[record][('x','y','z','t').index(component)]),
            tc=lambda:c(5),zb7=lambda:c(3),zek=lambda tr,ctx:c(9 if name=='wrong_distance' else 8),
            zel=lambda tr,ctx:c(5 if name=='total_speed_as_component' else -4 if name=='negative_component' else 4))
        actual=values(doc,model,domain)[0]
        if actual!=(name in ('y_axis','z_axis')):raise ValueError('Transverse coordinate/time geometry differs: '+name+repr(actual))
        rows[name]=actual
    return {'cases':rows,'prior_trial_and_tau_binding_are_oracles':True,'fixed_xprime_and_other_transverse_coordinate':True}


def scope_checks():
    doc=abstract(candidate(source_composed()[0],'q[k sls[k zb6[]]].'),ARITHMETIC|{'sky','sfm','sbc','sio','slp'})
    rows={};domain=('ty','tz','other','x','y','z')
    for name in ('baseline','no_y_trial','no_z_trial','empty_scope','scope_incomplete','bad_y_trial','bad_z_trial','unexpected_axis','missing_light_law','wrong_motion','duplicate_roles','wrong_context'):
        fixture=ConstructedCuts();n=fixture.read;c=fixture.make;model=guarded(doc);fixture.arithmetic(model);model['sky']=lambda x:square_root(fixture,x)
        selected={('ty','y'),('tz','z')}
        if name=='no_y_trial':selected.remove(('ty','y'))
        if name=='no_z_trial':selected.remove(('tz','z'))
        if name=='empty_scope':selected=set()
        if name=='unexpected_axis':selected.add(('other','x'))
        for k,v in {'zb6':'other' if name=='wrong_context' else 'motion','yn':'x','yo':'y','yp':'y' if name=='duplicate_roles' else 'z'}.items():model[k]=lambda v=v:v
        model.update(tc=lambda:c(5),zb7=lambda:c(3),sfm=lambda ctx:ctx=='motion' and name!='wrong_motion',
            sbc=lambda V,ctx:n(V)==5 and ctx=='motion' and name!='missing_light_law',sio=lambda f:True,
            zem=lambda ctx:ctx=='motion' and name!='scope_incomplete',zej=lambda tr,axis,ctx:(tr,axis) in selected and ctx=='motion',
            slp=lambda tr,axis,ctx:(tr,axis) in {('ty','y'),('tz','z')} and ctx=='motion' and not(name=='bad_y_trial' and tr=='ty') and not(name=='bad_z_trial' and tr=='tz'))
        callbacks(doc,model,{'zd4':lambda x,y,z,t:c(n(t))})
        actual=values(doc,model,domain)[0]
        if actual!=(name=='baseline'):raise ValueError('Both transverse trial scopes differ: '+name+repr(actual))
        rows[name]=actual
    return {'cases':rows,'motion_light_law_tau_candidate_and_trial_conditions_are_oracles':True,'both_axes_nonempty_and_all_trials_checked':True}


def finite_refusals():
    rows={}
    for name,query in (('small_transverse_steps','k slg[k ja[] k jd[] k jd[] k jd[] k jd[] k jb[] k jc[]]'),
        ('all_space_premise','k sll[k ja[] k jd[] k jb[]]'),('all_space_zero_partials','k slm[k ja[] k jd[]]')):
        doc=abstract(candidate(source_composed()[0],'r ja[] '+TAU+'.r jb[] '+CUT+'.r jc[] '+CUT+'.r jd[] '+CUT+'.q['+query+'].'),ARITHMETIC)
        fixture=ConstructedCuts();model=guarded(doc);fixture.arithmetic(model)
        model.update(jb=lambda:fixture.make(4),jc=lambda:fixture.make(1),jd=lambda:fixture.make(0))
        callbacks(doc,model,{'ja':lambda x,y,z,t:fixture.make(fixture.read(t))})
        try:values(doc,model,('object',))
        except ValueError as error:
            if 'Cannot finitely quantify the rational number domain' not in str(error):raise
            rows[name]={'refused':True,'reason':str(error)}
        else:raise ValueError('Transverse real quantification replaced by samples')
    return rows


def attribution_checks():
    doc=parse(source_composed()[0]);doc['statements']=doc['statements'][-2:];rows={}
    for name in ('baseline','wrong_author','wrong_scope','wrong_context','wrong_speed_content','missing_highlight','wrong_premise','wrong_conclusion','wrong_earlier_argument'):
        model=guarded(doc)
        for k,v in {'zen':'speed','zeo':'inference','zea':'earlier','rd':'author','rh':'scope','ri':'text'}.items():model[k]=lambda v=v:v
        symbol=lambda d:json.loads(d.syntax)['symbol'];bad={'wrong_author','wrong_scope','wrong_context'}
        common=lambda a,s,c:(a,s,c)==('other' if name=='wrong_author' else 'author','other' if name=='wrong_scope' else 'scope','other' if name=='wrong_context' else 'text')
        model.update(uh=lambda node,a,d,s,c:common(a,s,c) and (node,symbol(d))==('speed','slu' if name=='wrong_speed_content' else 'slw'),
            zei=lambda node,a,s,c:common(a,s,c) and node=='speed' and name!='missing_highlight',
            zc=lambda node,a,p,d,s,c:common(a,s,c) and (node,symbol(p),symbol(d))==('inference','slw' if name=='wrong_premise' else 'slu','skv' if name=='wrong_conclusion' else 'slv'),
            zep=lambda node,a,earlier,s,c:common(a,s,c) and (node,earlier)==('inference','other' if name=='wrong_earlier_argument' else 'earlier'))
        actual=values(doc,model,('speed','inference','earlier','author','scope'))
        if actual!=[name not in bad|{'wrong_speed_content','missing_highlight'},name not in bad|{'wrong_premise','wrong_conclusion','wrong_earlier_argument'}]:raise ValueError('Transverse analogy attribution differs')
        rows[name]=actual
    return rows


def alignment():
    artifact=json.loads((ROOT/'artifacts/written-units-v1/einstein-1905.json').read_text(encoding='utf-8'));rows=[]
    entries=(
        ('einstein-1905:u0059','e42a253701532e6f8c87f38848b7f107fccbac56eeaebda094e79121df420f46',['skz','slp','sls','slt','slu'],[
            ('M0106','72ee6ce9a02f5c99610fece9d3fa55204babda81fb36ca5fd8b238fde134e495'),('M0107','c912c500979e56eb818f0a914ae903cc477c24063e9ebbd8a31a9f9e8f1fda04'),('M0108','4017c119c73b11d909ec1d7566cc177afbf214faf8d026f03e001345f887f5a4')]),
        ('einstein-1905:u0060','14cf34cc3a3e271592c19a2c088158fba3b6874f9aad6e6d157095504559d736',['skw','sli','slm','slv'],[('M0109','05d863b6b0ab24edb510a3e149e5ce0b2f09b68fe39035b674b6383b69c95ab5')]),
        ('einstein-1905:u0061','455386cb6d175dbebc5e9af9e0d92e0b89275302718e55827d95cee5a99ed3a2',['skx','sli','slm','slv'],[('M0110','5fb2e7ece38df0f7cf284a51cc60fe390abf143ec620a164febf8a77f56cdb6c')]))
    for uid,digest,defs,maths in entries:
        unit=next(u for u in artifact['units'] if u['id']==uid)
        if hashlib.sha256(unit['text'].encode('utf-8')).hexdigest()!=digest:raise ValueError('Transverse source changed')
        rows.append({'unit':uid,'unit_sha256':digest,'start':0,'end':len(unit['text']),'source':unit['text'],'definitions':defs,'status':'partial_explicit_reading','full_semantic_equivalence':False})
        for mid,mdigest in maths:
            m=next(m for m in artifact['math'] if m['id']==mid)
            if hashlib.sha256(m['mathml'].encode('utf-8')).hexdigest()!=mdigest:raise ValueError('Transverse math changed')
            rows.append({'unit':uid,'unit_sha256':digest,'math_id':mid,'math_sha256':mdigest,'definitions':defs,'status':'partial','full_semantic_equivalence':False})
    return {'segments':rows,'facsimile_checked':False,'verified_full_units':0,'transverse_component_not_total_speed':True}


def build_report():
    documents={}
    for compose in (generic_composed,source_composed):
        text,basis=compose();doc=parse(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text:raise ValueError('Stored transverse time differs')
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Transverse time roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis)
    paths=[*documents,'data/transverse-time-basis-v1.json','data/einstein-transverse-time-basis-v1.json',
        'examples/v014/einstein-arbitrary-origins.noema','examples/v011/real-products.noema',
        'scripts/compose_transverse_time.py','scripts/check_transverse_time.py','scripts/check_tau_differential.py',
        'noema/discourse.py','noema/finite_semantics.py','noema/polynomial_proofs.py']
    text=source_composed()[0];previous=(ROOT/'examples/v014/einstein-arbitrary-origins.noema').read_text(encoding='utf-8')
    return {'status':'partial_transverse_light_and_zero_time_partials','documents':documents,'polynomial_lemmas':polynomial_checks(),
        'reuse':reuse_checks(),'component_speed':speed_checks(),'tau_arguments_and_partials':tau_checks(),
        'axis_protocol':protocol_checks(),'coordinate_geometry':geometry_checks(),'trial_scope':scope_checks(),
        'finite_refusals':finite_refusals(),'attribution':attribution_checks(),'alignment':alignment(),'roundtrips':True,
        'verified_full_units':{'einstein-1905':0,'kant-1784':0},
        'notation_size':{'canonical_source_document_characters':len(text),'added_characters':len(text)-len(previous)},
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args();report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Transverse report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Transverse components, y/z trial scopes and zero-partial bindings checked')


if __name__=='__main__':main()
