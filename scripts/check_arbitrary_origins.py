"""Check spatial shifts, possible choices and the scope of the global claim."""
import argparse
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
from scripts.check_tau_differential import ARITHMETIC, ConstructedCuts
from scripts.compose_arbitrary_origins import ROOT, CUT, TAU, generic_composed, source_composed

REPORT=ROOT/'reports/arbitrary-origins-v1.json'


def polynomial_checks():
    projection=lambda name:'i[x b y b z b time b][v '+name+']'
    shifted=lambda f,x,y,z:'k skh['+' '.join((f,x,y,z))+']'
    apply=lambda f:'c['+f+'][v dx v dy v dz v moment]'
    args='x y z dx dy dz moment';rows={}
    for axis,delta in (('x','dx'),('y','dy'),('z','dz'),('time','moment')):
        f=shifted(projection(axis),'v x','v y','v z')
        expected='v moment' if axis=='time' else call('ab','v '+axis,'v '+delta)
        claim=assertion(args,op('e',apply(f),expected))
        result=verify_universal(parse(generic_composed()[0]+claim),MEANINGS,timeout_ms=15000)[0]
        if result['status']!='valid':raise ValueError('Translation projection differs')
        rows[axis]=result
    f='i[x b y b z b time b][k ab[k ad[v x v y] k ad[v z v time]]]'
    twice=shifted(shifted(f,'v x','v y','v z'),'v ax','v ay','v az')
    combined=shifted(f,*(call('ab','v '+a,'v '+b) for a,b in (('x','ax'),('y','ay'),('z','az'))))
    result=verify_universal(parse(generic_composed()[0]+assertion(args+' ax ay az',op('e',apply(twice),apply(combined)))),MEANINGS,timeout_ms=15000)[0]
    if result['status']!='valid':raise ValueError('Successive spatial shifts differ')
    rows['composed_polynomial_example']=result
    return {'claims':rows,'rational_component_arithmetic_only':True,'physical_origin_independence_proved':False}


def choice_checks():
    doc=parse(generic_composed()[0]+'''
r ja[a a d] c.r jb[a a d d] c.r jc[a a d] c.r jd[] a.r je[] a.r jf[] a.r jg[] d.
q[k skj[k jd[] k jf[] k jg[] p ja p jb p jc]].
q[k skj[k je[] k jf[] k jg[] p ja p jb p jc]].
''')
    rows={};domain=('point1','point2','plan1','plan2','actor','other')
    for name in ('baseline','extra_failing_outcome','no_available_plan','no_outcome','wrong_actor','wrong_start',
        'only_first_point','success_from_different_trial','success_from_different_point','unavailable_success'):
        available={('actor','plan1','motion'),('actor','plan2','motion')}
        outcomes={('actor','plan1','motion','text'),('actor','plan2','motion','other')}
        successes={('plan1','point1','text'),('plan2','point2','other')}
        if name=='extra_failing_outcome':outcomes.add(('actor','plan1','motion','other'))
        if name=='no_available_plan':available=set()
        if name=='no_outcome':outcomes=set()
        if name=='only_first_point':successes.remove(('plan2','point2','other'))
        if name=='success_from_different_trial':successes={('plan2','point1','text'),('plan1','point2','other')}
        if name=='success_from_different_point':successes={('plan1','point2','text'),('plan2','point1','other')}
        if name=='unavailable_success':available=set();outcomes|={('actor','other','motion','text')}
        model={'aa':lambda a,b:a<b,'ab':lambda a,b:a+b,'ac':lambda a:-a,'ad':lambda a,b:a*b,
            'ja':lambda *args:args in available,'jb':lambda *args:args in outcomes,'jc':lambda *args:args in successes,
            'jd':lambda:'point1','je':lambda:'point2','jf':lambda:'other' if name=='wrong_actor' else 'actor',
            'jg':lambda:'text' if name=='wrong_start' else 'motion'}
        actual=values(doc,model,domain)
        expected=[True,True] if name in ('baseline','extra_failing_outcome','success_from_different_point') else [True,False] if name=='only_first_point' else [False,False]
        # Different plans may realize each point; the identity of plan1 is not
        # prescribed for point1. Swapped successful points are still possible.
        if actual!=expected:raise ValueError('Possible trial choice differs: '+name+repr(actual))
        rows[name]=actual
    return {'cases':rows,'pointwise_choices_need_not_use_one_plan':True,'possibility_not_guarantee_or_actual_occurrence':True}


def shift_checks():
    doc=abstract(candidate(source_composed()[0],'''
r ja[] '''+TAU+'''.r jb[] h[b] c.r jc[] h[b] c.r jd[] h[b] c.r je[] h[b] c.
q[k skk[k ja[] k jb[] k jc[] k jd[] k bb[n p d b] k bb[n p b b] k je[] k bb[n p c b]]].
'''),ARITHMETIC|{'skc'})
    rows={}
    for name in ('baseline','different_x','different_y','different_z','different_time','wrong_function','no_neighborhood'):
        fixture=ConstructedCuts();n=fixture.read;c=fixture.make;model=guarded(doc);fixture.arithmetic(model)
        params=[2,3,4,1]
        for i,axis in enumerate(('x','y','z','time')):
            if name=='different_'+axis:params[i]+=1
        for symbol,value in zip(('jb','jc','jd','je'),params):model[symbol]=lambda value=value:c(value)
        f=lambda x,y,z,t:x*x+2*y+3*z+(5 if name=='wrong_function' else 4)*t
        callbacks(doc,model,{'ja':lambda x,y,z,t:c(f(*(n(a) for a in (x,y,z,t))))})
        def neighborhood(fn,V,v,t,radius):
            return name!='no_neighborhood' and tuple(n(a) for a in (V,v,t,radius))==(3,1,1,2) and all(
                n(fn(c(dx),c(dy),c(dz),c(tm)))==(2+dx)**2+2*(3+dy)+3*(4+dz)+4*tm
                for dx,dy,dz,tm in ((0,0,0,1),(1,0,0,1),(0,1,0,1),(0,0,1,1),(0,0,0,2)))
        model['skc']=neighborhood
        actual=values(doc,model,('object',))[0]
        if actual!=(name=='baseline'):raise ValueError('Shifted neighborhood differs: '+name+repr(actual))
        rows[name]=actual
    return {'cases':rows,'neighborhood_is_a_binding_oracle':True,'spatial_shift_keeps_time_and_function_values':True}


def protocol_checks():
    doc=abstract(candidate(source_composed()[0],'''
r ja[] a.r jb[] a.r jc[] d.q[k skp[k ja[] k jb[] k jc[]]].
'''),ARITHMETIC|{'qo','sgp'})
    rows={};domain=('trial','point','mirror','ca','cb','depart','reflect','arrive','ray','axis','moving','time','other')
    for name in ('baseline_nonorigin','missing_outward','missing_return','wrong_reflection','different_return_place',
        'wrong_return_clock','unsynchronized','clock_not_stationary','clock_not_deployed','wrong_parallel_direction',
        'wrong_departure_point','wrong_trial_scope','duplicate_event','missing_local_time','wrong_context'):
        fixture=ConstructedCuts();n=fixture.read;c=fixture.make;model=guarded(doc);fixture.arithmetic(model)
        for k,v in {'ja':'trial','jb':'point','jc':'other' if name=='wrong_context' else 'motion','zbm':'moving','rb':'time','yn':'axis'}.items():model[k]=lambda v=v:v
        places={('ca','point'),('cb','mirror'),('depart','point'),('reflect','mirror'),('arrive','point')}
        if name=='different_return_place':places.remove(('arrive','point'));places.add(('arrive','mirror'))
        legs={('ray','depart','reflect','moving'),('ray','reflect','arrive','moving')}
        if name=='missing_outward':legs.remove(('ray','depart','reflect','moving'))
        if name=='missing_return':legs.remove(('ray','reflect','arrive','moving'))
        readings={'depart':0,'reflect':1,'arrive':2}
        model.update(te=lambda tr:'ca',tf=lambda tr:'cb',qc=lambda tr:'mirror' if name=='wrong_departure_point' else 'point',qd=lambda tr:'mirror',
            qe=lambda tr:'depart',qf=lambda tr:'reflect',qg=lambda tr:'depart' if name=='duplicate_event' else 'arrive',qh=lambda tr:'ray',
            qi=lambda tr:c(0),qj=lambda tr:c(1),qk=lambda tr:c(2),
            qb=lambda a,b,f,u,ctx,tr:(a,b,f,u,ctx,tr)==('ca','cb','moving','time','motion','trial') and name!='wrong_trial_scope',
            ca=lambda clock:clock in ('ca','cb'),ci=lambda u:u=='time',cd=lambda a,b:(a,b)==('ca','cb'),
            cb=lambda obj,p,f:(obj,p) in places and f=='moving',cc=lambda clock,f:clock in ('ca','cb') and f=='moving' and name!='clock_not_stationary',
            ce=lambda clock,e,f,u,value:e in readings and (clock,f,u)==('cb' if e=='reflect' or (name=='wrong_return_clock' and e=='arrive') else 'ca','moving','time') and n(value)==readings[e],
            cf=lambda ray:ray=='ray',cg=lambda *args:args in legs,ch=lambda ray,e,f:(ray,e,f)==('ray','reflect','moving') and name!='wrong_reflection',
            qo=lambda a,b,f,u,ctx:(a,b,f,u,ctx)==('ca','cb','moving','time','motion') and name!='unsynchronized',
            zbo=lambda f,r,ctx:'axis',zbw=lambda f,a,r,ctx:(f,a,r,ctx)==('moving','axis','axis','motion'),
            zbz=lambda f,clock,ctx:(f,ctx)==('moving','motion') and clock in ('ca','cb') and name!='clock_not_deployed',
            zcu=lambda p,f,ctx:p in ('point','mirror') and (f,ctx)==('moving','motion'),
            zef=lambda r,a,b,axis,f,ctx:(r,a,b,f) in legs and (axis,ctx)==('axis','motion') and name!='wrong_parallel_direction',
            sgp=lambda e,p,f,u,ctx,*args:(e,p) in places and (f,u,ctx)==('moving','time','motion') and name!='missing_local_time',
            zbe=lambda e,f,u,ctx:c(readings.get(e,0)))
        actual=values(doc,model,domain)[0]
        if actual!=(name=='baseline_nonorigin'):raise ValueError('Nonorigin trial differs: '+name+repr(actual))
        rows[name]=actual
    return {'cases':rows,'synchrony_and_local_time_are_oracles':True,'no_origin_assignment_or_axis_coincidence_required':True}


def possibility_checks():
    doc=abstract(candidate(source_composed()[0],'''
r ja[] h[b] c.r jb[] h[b] c.r jc[] h[b] c.r jd[] h[b] c.
q[k sks[k ja[] k jb[] k jc[] k jd[] k zb6[]]].
'''),ARITHMETIC|{'sko','sfm','sbc','skp','skq','sjh','skl'})
    rows={};domain=('point','trial','actor','other')
    names=('baseline','no_coordinate_place','no_available_trial','no_possible_outcome','wrong_trial_outcome',
        'wrong_place_in_alternative','wrong_speed_history','wrong_light_law','missing_trial','wrong_trial_point',
        'wrong_clock_function','wrong_departure_time','missing_local_regularity','wrong_actor','wrong_baseline')
    for name in names:
        fixture=ConstructedCuts();n=fixture.read;c=fixture.make;model=guarded(doc);fixture.arithmetic(model)
        for symbol,value in zip(('ja','jb','jc','jd'),(2,3,4,1)):model[symbol]=lambda value=value:c(value)
        model.update(zee=lambda:'other' if name=='wrong_actor' else 'actor',zb6=lambda:'other' if name=='wrong_baseline' else 'motion',
            tc=lambda:c(3),zb7=lambda:c(1),zec=lambda a,tr,ctx:(a,tr,ctx)==('actor','trial','motion') and name!='no_available_trial',
            zed=lambda a,tr,ctx,alt:(a,tr,ctx,alt)==('actor','other' if name=='wrong_trial_outcome' else 'trial','motion','text') and name!='no_possible_outcome',
            sko=lambda p,x,y,z,t,ctx:p=='point' and tuple(n(a) for a in (x,y,z,t))==(2,3,4,1) and ctx in ('motion','text') and name!='no_coordinate_place' and not(name=='wrong_place_in_alternative' and ctx=='text'),
            sfm=lambda ctx:ctx=='text' and name!='wrong_speed_history',sbc=lambda v,ctx:n(v)==3 and ctx=='text' and name!='wrong_light_law',
            skp=lambda tr,p,ctx:(tr,p,ctx)==('trial','other' if name=='wrong_trial_point' else 'point','text') and name!='missing_trial',
            skq=lambda tr,ctx:(tr,ctx)==('trial','text') and name!='wrong_clock_function',qe=lambda tr:'trial',
            sjh=lambda e,ctx:c(2 if name=='wrong_departure_time' else 1),
            skl=lambda f,x,y,z,V,v,t:tuple(n(a) for a in (x,y,z,V,v,t))==(2,3,4,3,1,1) and name!='missing_local_regularity')
        callbacks(doc,model,{'zd4':lambda x,y,z,t:c(n(t))})
        actual=values(doc,model,domain)[0]
        if actual!=(name=='baseline'):raise ValueError('Possible alternate origin differs: '+name+repr(actual))
        rows[name]=actual
    return {'cases':rows,'coordinate_history_trial_and_regularity_bindings_are_oracles':True,'possible_outcome_differs_from_start_context':True}


def coordinate_checks():
    doc=abstract(candidate(source_composed()[0],'''
r ja[] a.r jb[] h[b] c.r jc[] h[b] c.r jd[] h[b] c.r je[] h[b] c.r jf[] d.
q[k sko[k ja[] k jb[] k jc[] k jd[] k je[] k jf[]]].
'''),ARITHMETIC|{'sij'})
    rows={};domain=('point','moment2','moment3','rest','moving','length','time','x','y','z')
    for name in ('baseline','wrong_x','wrong_y','wrong_z','wrong_time','no_moment','point_not_stationary','missing_coordinates','wrong_frame','wrong_context'):
        fixture=ConstructedCuts();c=fixture.make;model=guarded(doc);fixture.arithmetic(model)
        for symbol,value in {'ja':'point','jf':'other' if name=='wrong_context' else 'motion','ra':'moving' if name=='wrong_frame' else 'rest','zbm':'moving','ta':'length','rb':'time','yn':'x','yo':'y','yp':'z'}.items():model[symbol]=lambda value=value:value
        for symbol,value in zip(('jb','jc','jd','je'),(3,4,5,2)):model[symbol]=lambda value=value:c(value)
        moments={'moment2':2,'moment3':3}
        def coordinate(p,m,f,u,role,ctx):
            value={'x':3+moments.get(m,0),'y':4,'z':5}[role]
            if name=='wrong_'+role:value+=1
            return c(value)
        model.update(zb7=lambda:c(1),zdi=lambda p,ctx:(p,ctx)==('point','motion'),
            zcu=lambda p,f,ctx:(p,f,ctx)==('point','moving','motion'),
            x4=lambda p,f,ctx:(p,f,ctx)==('point','moving','motion') and name!='point_not_stationary',
            ys=lambda m,ctx:m in moments and ctx=='motion' and name!='no_moment',
            zce=lambda p,m,f,u,ctx:(p,f,u,ctx)==('point','rest','length','motion') and m in moments and name!='missing_coordinates',
            zcf=lambda m,f,u,ctx:(f,u,ctx)==('rest','time','motion') and m in moments,
            yl=lambda m,f,u,ctx:c(moments.get(m,0)+(1 if name=='wrong_time' else 0)),ym=coordinate,
            sij=lambda p,m,role,ctx,subtract,multiply:c(fixture.read(coordinate(p,m,'rest','length',role,ctx))-(moments.get(m,0)+(1 if name=='wrong_time' else 0) if role=='x' else 0)))
        actual=values(doc,model,domain)[0]
        if actual!=(name=='baseline'):raise ValueError('Auxiliary place coordinates differ: '+name+repr(actual))
        rows[name]=actual
    return {'cases':rows,'finite_constructed_coordinate_histories':True,'rest_x_minus_vt_not_moving_xi':True,'auxiliary_coordinate_operation_is_oracle':True}


def clock_function_checks():
    doc=abstract(candidate(source_composed()[0],'r ja[] a.r jb[] d.q[k skq[k ja[] k jb[]]].'),ARITHMETIC|{'shd'})
    rows={};domain=('trial','depart','reflect','arrive','r0','r1','r2','rest','moving','x','y','z','t')
    for name in ('baseline','missing_chart','wrong_reflection_chart','wrong_departure_reading','wrong_return_reading',
        'wrong_x','wrong_y','wrong_z','wrong_time','wrong_velocity','wrong_frame','wrong_context'):
        fixture=ConstructedCuts();n=fixture.read;c=fixture.make;model=guarded(doc);fixture.arithmetic(model)
        for k,v in {'ja':'trial','jb':'other' if name=='wrong_context' else 'motion','ra':'moving' if name=='wrong_frame' else 'rest','yn':'x','yo':'y','yp':'z','zc7':'t'}.items():model[k]=lambda v=v:v
        coords={'r0':(5,4,5,2),'r1':(23,4,5,8),'r2':(14,4,5,11)}
        if name in ('wrong_x','wrong_y','wrong_z','wrong_time'):
            index={'wrong_x':0,'wrong_y':1,'wrong_z':2,'wrong_time':3}[name];row=list(coords['r1']);row[index]+=1;coords['r1']=tuple(row)
        lookup={'depart':'r0','reflect':'r0' if name=='wrong_reflection_chart' else 'r1','arrive':'r2'}
        model.update(qe=lambda tr:'depart',qf=lambda tr:'reflect',qg=lambda tr:'arrive',
            qi=lambda tr:c(37 if name=='wrong_departure_reading' else 36),qj=lambda tr:c(72),qk=lambda tr:c(109 if name=='wrong_return_reading' else 108),
            zb7=lambda:c(2 if name=='wrong_velocity' else 1),zdz=lambda e,f,ctx:lookup.get(e,'r0'),
            shd=lambda e,r,f,ctx:(e,r) in {('depart','r0'),('reflect','r1'),('arrive','r2')} and (f,ctx)==('rest','motion') and name!='missing_chart',
            zc6=lambda r,role:c(coords.get(r,(0,0,0,0))[('x','y','z','t').index(role)]))
        callbacks(doc,model,{'zd4':lambda x,y,z,t:c(-n(x)+2*n(y)+3*n(z)+8*n(t))})
        actual=values(doc,model,domain)[0]
        if actual!=(name=='baseline'):raise ValueError('Alternate trial tau binding differs: '+name+repr(actual))
        rows[name]=actual
    return {'cases':rows,'rest_chart_is_an_oracle':True,'all_three_event_readings_bound_to_one_function':True}


def finite_refusals():
    rows={}
    for name,query in (
        ('all_spatial_values','k skn[k ja[] k jb[] k jc[] k jd[]]'),
        ('all_spatial_choices','k skt[k jd[] k zb6[]]')):
        doc=abstract(candidate(source_composed()[0],'r ja[] '+TAU+'.r jb[] '+CUT+'.r jc[] '+CUT+'.r jd[] '+CUT+'.q['+query+'].'),ARITHMETIC|{'sio'})
        fixture=ConstructedCuts();model=guarded(doc);fixture.arithmetic(model)
        model.update(jb=lambda:fixture.make(3),jc=lambda:fixture.make(1),jd=lambda:fixture.make(0),zb6=lambda:'motion',sio=lambda f:True)
        callbacks(doc,model,{'ja':lambda x,y,z,t:fixture.make(fixture.read(t)),'zd4':lambda x,y,z,t:fixture.make(fixture.read(t))})
        try:values(doc,model,('object',))
        except ValueError as error:
            if 'Cannot finitely quantify the rational number domain' not in str(error):raise
            rows[name]={'refused':True,'reason':str(error)}
        else:raise ValueError('All real spatial values were replaced by finite samples')
    return rows


def attribution_checks():
    doc=parse(source_composed()[0]);doc['statements']=doc['statements'][-2:];rows={}
    for name in ('baseline','wrong_author','wrong_scope','wrong_context','wrong_possibility','missing_highlight','wrong_premise','wrong_global_equation'):
        model=guarded(doc)
        for k,v in {'zeg':'choice','zeh':'inference','rd':'author','rh':'scope','ri':'text'}.items():model[k]=lambda v=v:v
        symbol=lambda d:json.loads(d.syntax)['symbol']
        common=lambda a,s,c:(a,s,c)==('other' if name=='wrong_author' else 'author','other' if name=='wrong_scope' else 'scope','other' if name=='wrong_context' else 'text')
        model.update(uh=lambda node,a,d,s,c:common(a,s,c) and (node,symbol(d))==('choice','ske' if name=='wrong_possibility' else 'sku'),
            zei=lambda node,a,s,c:common(a,s,c) and node=='choice' and name!='missing_highlight',
            zc=lambda node,a,p,d,s,c:common(a,s,c) and (node,symbol(p),symbol(d))==('inference','ske' if name=='wrong_premise' else 'sku','skg' if name=='wrong_global_equation' else 'skv'))
        actual=values(doc,model,('choice','inference','author','scope'));bad={'wrong_author','wrong_scope','wrong_context'}
        if actual!=[name not in bad|{'wrong_possibility','missing_highlight'},name not in bad|{'wrong_premise','wrong_global_equation'}]:raise ValueError('Arbitrary-origin attribution differs')
        rows[name]=actual
    return rows


def alignment():
    artifact=json.loads((ROOT/'artifacts/written-units-v1/einstein-1905.json').read_text(encoding='utf-8'))
    unit=next(u for u in artifact['units'] if u['id']=='einstein-1905:u0058');digest='aaf3e6f0074746f5214ec50f0cc7db0c57dca4aaa4b21a7e41a69bb989b539a3'
    math=next(m for m in artifact['math'] if m['id']=='M0105');mdigest='00c54ebd10cc5df750055f36c9ded18b8cb4393d7cbc5f9a2228543bea6bb95d'
    if hashlib.sha256(unit['text'].encode('utf-8')).hexdigest()!=digest:raise ValueError('Arbitrary-origin source changed')
    if hashlib.sha256(math['mathml'].encode('utf-8')).hexdigest()!=mdigest:raise ValueError('Arbitrary-origin coordinates changed')
    return {'segments':[{'unit':unit['id'],'unit_sha256':digest,'start':0,'end':len(unit['text']),'source':unit['text'],
        'definitions':['ski','skj','skl','skm','skn','sks','skt','sku','skv'],'status':'partial_explicit_reading','full_semantic_equivalence':False},
        {'unit':unit['id'],'unit_sha256':digest,'math_id':'M0105','math_sha256':mdigest,'definitions':['skn','skt','skv'],'status':'partial','full_semantic_equivalence':False}],
        'facsimile_checked':False,'verified_full_units':0,'same_time_parameter_retained':True}


def build_report():
    documents={}
    for compose in (generic_composed,source_composed):
        text,basis=compose();doc=parse(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text:raise ValueError('Stored arbitrary origins differ')
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Arbitrary-origin roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis)
    paths=[*documents,'data/arbitrary-origins-basis-v1.json','data/einstein-arbitrary-origins-basis-v1.json',
        'examples/v014/einstein-tau-differential.noema','scripts/compose_arbitrary_origins.py','scripts/check_arbitrary_origins.py',
        'scripts/check_tau_differential.py','noema/discourse.py','noema/finite_semantics.py','noema/polynomial_proofs.py']
    text=source_composed()[0];previous=(ROOT/'examples/v014/einstein-tau-differential.noema').read_text(encoding='utf-8')
    return {'status':'partial_arbitrary_origins_possible_choices_and_global_equation','documents':documents,
        'polynomial_lemmas':polynomial_checks(),'possible_choices':choice_checks(),'shifted_neighborhoods':shift_checks(),
        'nonorigin_protocol':protocol_checks(),'source_possibility':possibility_checks(),
        'place_coordinates':coordinate_checks(),'clock_function':clock_function_checks(),'finite_refusals':finite_refusals(),
        'attribution':attribution_checks(),'alignment':alignment(),'roundtrips':True,
        'verified_full_units':{'einstein-1905':0,'kant-1784':0},
        'notation_size':{'canonical_source_document_characters':len(text),'added_characters':len(text)-len(previous)},
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args();report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Arbitrary-origin report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Spatial shifts, possible nonorigin trials and real-space scope checked')


if __name__=='__main__':main()
