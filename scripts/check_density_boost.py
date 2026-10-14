"""Check velocity/current separation and the divergence connection of a boost."""
import argparse
from fractions import Fraction as F
import hashlib
from itertools import product
import json

from noema.extraction import extract_document
from noema.finite_semantics import FunctionValue
from noema.grammar import parse,format_graph,number_word
from noema.meaning_basis import audit_basis
from noema.polynomial_proofs import verify_universal
from noema.script import encode,decode
from scripts.check_comoving_labels import values
from scripts.check_coordinate_correspondence import abstract
from scripts.check_described_appraisals import candidate
from scripts.check_field_equations import AXES,field_callback,jet_callback
from scripts.check_field_constraints import transformed_jets
from scripts.check_convection_fields import matrices
from scripts.check_parallel_composition import transform
from scripts.check_plane_waveforms import setup as cut_setup,OPS
from scripts.check_rod_setup import callbacks
from scripts.check_real_products import MEANINGS as ARITHMETIC,assertion
from scripts.check_moving_light_trip import literal
from scripts.compose_field_constraints import NAMES,OLD_RESIDUALS,NEW_RESIDUALS
from scripts.compose_limits import call as k,app,op,both,v
from scripts.compose_density_boost import ROOT,PARENT,BUILDERS,FLOW,CURRENT,FACTOR,COMBINED,JETFLOW,INPUTS,CUT,ROLES,generic_composed,source_composed

REPORT=ROOT/'reports/density-boost-v1.json'
FACSIMILE=ROOT/'data/density-boost-facsimile-v1.json'
FIELDS=INPUTS+[(n,CUT) for n in ('jx','jy','jz','kx','ky','kz')]
SYMBOLS={name:'ju'+number_word(i) for i,(name,_) in enumerate(FIELDS)}
DOMAIN=AXES+('matter','old','new','event','other')
CENTER=(F(1),F(2),F(3),F(4))


def polynomial_checks():
    V,s,b,rho,rhop,ux,uy,uz,vx,vy,vz=map(v,('light','speed','beta','density','newdensity','ux','uy','uz','vx','vy','vz'))
    zero,one=literal(0),literal(1)
    mul=lambda a,b:k('ad',a,b);add=lambda a,b:k('ab',a,b);neg=lambda a:k('ac',a);sub=lambda a,b:add(a,neg(b))
    flow=k('semp',*map(v,FLOW.split()));current=k('semq',*map(v,CURRENT.split()))
    invflow=k('semp',V,neg(s),b,rhop,vx,vy,vz,rho,ux,uy,uz)
    invcurrent=k('semq',V,neg(s),b,rhop,*map(v,('kx','ky','kz')),rho,*map(v,('jx','jy','jz')))
    norm2=add(add(mul(ux,ux),mul(uy,uy)),mul(uz,uz));square=mul(V,V);D=sub(square,mul(s,ux))
    claims={
        'convective_factorization_implies_current_transform':assertion(COMBINED,op('y',k('sems',*map(v,COMBINED.split())),current)),
        'velocity_and_density_return_under_opposite_boost':assertion(FLOW,op('y',flow,invflow)),
        'current_and_density_return_under_opposite_boost':assertion(CURRENT,op('y',current,invcurrent)),
        'zero_density_stays_zero_for_finite_velocity':assertion(FLOW,op('y',both(flow,op('e',rho,zero)),op('e',rhop,zero))),
        'causal_velocity_has_positive_denominator':assertion('light speed beta ux uy uz',op('y',both(k('sra',V,s,b),op('u',k('aa',square,norm2))),k('aa',zero,D))),
        'causal_flow_preserves_density_sign':assertion(FLOW,op('y',both(flow,op('u',k('aa',square,norm2))),op('z',k('aa',zero,rho),k('aa',zero,rhop)))),
        'zero_density_factorization_determines_velocity':assertion(FACTOR,op('y',both(k('semr',*map(v,FACTOR.split())),op('e',rho,zero)),op('e',ux,zero))),
        'current_transform_requires_single_velocity':assertion(CURRENT,op('y',both(current,op('e',rho,zero)),op('e',v('jx'),zero))),
        'density_is_always_invariant':assertion('',op('y',
            k('semp',*(literal(x) for x in (5,3,F(5,4),4,1,-2,3,F(22,5),F(-25,11),F(-20,11),F(30,11)))),
            op('e',literal(4),literal(F(22,5))))),
    }
    rejected={'zero_density_factorization_determines_velocity','current_transform_requires_single_velocity','density_is_always_invariant'}
    rows={};base=generic_composed()[0]
    for name,claim in claims.items():
        result=verify_universal(parse(base+claim),ARITHMETIC,timeout_ms=25000)[0]
        if result['status']!=('invalid' if name in rejected else 'valid'):raise ValueError('Density/velocity algebra differs: '+name+' '+str(result['status']))
        rows[name]=result
    return dict(claims=rows,rational_algebra_only=True,density_not_used_as_a_velocity_divisor=True)


def residual_checks(text):
    doc=extract_document(parse(text),roots=['sra',*OLD_RESIDUALS,*NEW_RESIDUALS],statement_indices=[]).document
    base=format_graph(doc,'compact');beta,ratio,rho,ux,uy,uz=map(v,('beta','ratio','density','ux','uy','uz'))
    mul=lambda a,b:k('ad',a,b);neg=lambda a:k('ac',a);add=lambda a,b:k('ab',a,b)
    old=[k(n,*map(v,NAMES)) for n in OLD_RESIDUALS]
    new=[k(n,beta,ratio,*map(v,NAMES)) for n in NEW_RESIDUALS]
    premise=both(k('sra',literal(1),ratio,beta),op('e',old[6],rho),
        *(op('e',old[i],neg(mul(rho,u))) for i,u in enumerate((ux,uy,uz))),
        *(op('e',old[i],literal(0)) for i in (3,4,5)))
    transformed_density=mul(beta,add(rho,neg(mul(ratio,mul(rho,ux)))))
    targets=[neg(mul(beta,add(mul(rho,ux),neg(mul(ratio,rho))))),neg(mul(rho,uy)),neg(mul(rho,uz)),
        mul(mul(beta,ratio),old[7]),literal(0),literal(0),transformed_density,mul(beta,old[7])]
    labels=('current_x','current_y','current_z','magnetic_x_needs_old_divergence','magnetic_y','magnetic_z','density_from_divergence','magnetic_divergence')
    rows={}
    for name,left,right in zip(labels,new,targets):
        claim=assertion('beta ratio density ux uy uz '+' '.join(NAMES),op('y',premise,op('e',left,right)))
        result=verify_universal(parse(base+claim),ARITHMETIC,timeout_ms=25000,max_expansion=250000)[0]
        if result['status']!='valid':raise ValueError('Convection residual identity differs: '+name+' '+str(result['status']))
        rows[name]=result
    return dict(identities=rows,time_coordinate='V*t',velocity_components_normalized_by_V=True,
        full_real_derivative_chain_rule_proved=False,zero_magnetic_divergence_is_an_extra_condition=True)


def expression(name):return k(SYMBOLS[name])


def point_value(prefix,field):
    coords=[app(expression(prefix+'point'),k(a)) for a in ROLES]
    if field=='velocity':return 'i[axis a]['+app(app(expression(prefix+'velocityfield'),'v axis'),*coords)+']'
    return app(expression(prefix+field+'field'),*coords)


def scalar_expressions():
    mapping={n:expression(n) for n in ('light','speed','jx','jy','jz','kx','ky','kz')}
    mapping.update(beta=k('soy',expression('light'),expression('speed')),density=point_value('old','density'),newdensity=point_value('new','density'))
    for prefix,names in (('old',('ux','uy','uz')),('new',('vx','vy','vz'))):
        mapping.update({n:app(point_value(prefix,'velocity'),k(role)) for n,role in zip(names,ROLES)})
    return mapping


def jet_expressions():
    mapping=scalar_expressions()
    mapping.update(velocity=point_value('old','velocity'),newvelocity=point_value('new','velocity'))
    mapping.update({n:expression('old'+n) for n in ('electricjet','magneticjet')})
    mapping.update({n:expression(n) for n in ('newelectricjet','newmagneticjet')})
    return mapping


def setup_document(text):
    if set(SYMBOLS.values()) & {d['name'] for d in parse(text)['declarations']}:raise ValueError('Density boost fixture symbols collide')
    extra=''.join('r '+SYMBOLS[n]+'[] '+sort+'.' for n,sort in FIELDS)
    scalar,jet=scalar_expressions(),jet_expressions();queries=[]
    for symbol,fields in (('semt',FLOW),('semu',CURRENT),('semv',FACTOR),('semw',COMBINED)):
        queries.append(k(symbol,*(scalar[n] for n in fields.split())))
    queries += [k(symbol,*(jet[n] for n,_ in JETFLOW)) for symbol in ('semx','semy','semz','sena')]
    queries.append(k('senb',*(expression(n) for n,_ in INPUTS)))
    queries.append(k('semf',scalar['light'],scalar['newdensity'],jet['newvelocity'],jet['newelectricjet'],jet['newmagneticjet']))
    return abstract(candidate(text,extra+''.join('q['+q+'].' for q in queries)),OPS|{'s5t','sedi'})


def fixture_data(speed=F(3),density=F(4),velocity=(F(1),F(-2),F(3)),magnetic_zero=True):
    V=F(5);beta=transform((0,0,0,1),speed)[3];D=V*V-speed*velocity[0]
    newdensity=beta*D*density/(V*V)
    newvelocity=((V*V*(velocity[0]-speed)/D,V*V*velocity[1]/(beta*D),V*V*velocity[2]/(beta*D)) if D else (F(0),F(0),F(0)))
    e,h=matrices(V,density,velocity)
    if magnetic_zero:h[2][2]=-h[0][0]-h[1][1]
    en,hn=transformed_jets(e,h,speed)
    j=tuple(density*u for u in velocity)
    current=(beta*(j[0]-speed*density),j[1],j[2])
    return dict(speed=speed,density=density,velocity=velocity,newdensity=newdensity,newvelocity=newvelocity,
        beta=beta,D=D,electric=e,magnetic=h,newelectric=en,newmagnetic=hn,current=j,newcurrent=current,
        point=CENTER,newpoint=tuple(transform(CENTER,speed)))


def model_for(doc,*,speed=F(3),density=F(4),velocity=(F(1),F(-2),F(3)),magnetic_zero=True,variant='baseline'):
    data=fixture_data(speed,density,velocity,magnetic_zero)
    fixture,model=cut_setup(doc);c,n=fixture.make,fixture.read
    matrices_by_prefix={'old':(data['electric'],data['magnetic']),'new':(data['newelectric'],data['newmagnetic'])}
    points={'old':CENTER,'new':data['newpoint']};rhos={'old':density,'new':data['newdensity']};flows={'old':velocity,'new':data['newvelocity']}
    if variant=='new_density':rhos['new']+=1
    if variant.startswith('new_velocity_'):
        values=list(flows['new']);values['xyz'.index(variant[-1])]+=1;flows['new']=tuple(values)
    if variant=='forward_instead_of_inverse':flows['new']=fixture_data(-speed,density,velocity,magnetic_zero)['newvelocity']
    if variant=='wrong_new_point':points['new']=tuple(x+(1 if i==0 else 0) for i,x in enumerate(points['new']))
    scalars=dict(matter='matter',event='event',oldframe='old',newframe='new',context='text')
    for name,value in scalars.items():model[SYMBOLS[name]]=lambda value=value:value
    for name,value in (('light',F(5)),('speed',speed),('pi',F(3))):model[SYMBOLS[name]]=lambda value=value:c(value)
    for name,value in zip(('jx','jy','jz','kx','ky','kz'),data['current']+data['newcurrent']):
        model[SYMBOLS[name]]=lambda name=name,value=value:c(value+(1 if variant=='current_'+name else 0))
    def region(prefix,xs):
        if variant==prefix+'_outside_region':return False
        coords=tuple(n(x) for x in xs)
        return (coords if prefix=='old' else transform(coords,-speed))[0]>0
    def constant_field(prefix,role):
        sort=next(d['result']['result'] for d in doc['declarations'] if d['name']==SYMBOLS[prefix+'velocityfield'])
        val=flows[prefix][AXES.index(role)] if role in AXES[:3] else F(0)
        return FunctionValue(tuple(sort['parameters']),sort['result'],lambda *xs:c(val))
    for prefix,(ef,hf) in matrices_by_prefix.items():
        ej,hj=[row[:] for row in ef],[row[:] for row in hf]
        if variant.startswith(prefix+'_jet_'):
            _,_,field,i,j=variant.split('_');(ej if field=='E' else hj)[int(i)][int(j)]+=F(1,4)
        callbacks(doc,model,{
            SYMBOLS[prefix+'electric']:field_callback(doc,fixture,SYMBOLS[prefix+'electric'],hf if variant==prefix+'_swapped_fields' else ef),
            SYMBOLS[prefix+'magnetic']:field_callback(doc,fixture,SYMBOLS[prefix+'magnetic'],ef if variant==prefix+'_swapped_fields' else hf),
            SYMBOLS[prefix+'region']:lambda *xs,prefix=prefix:region(prefix,xs),
            SYMBOLS[prefix+'point']:lambda axis,prefix=prefix:c(points[prefix][AXES.index(axis)] if axis in AXES else 0),
            SYMBOLS[prefix+'electricjet']:jet_callback(fixture,ej),SYMBOLS[prefix+'magneticjet']:jet_callback(fixture,hj),
            SYMBOLS[prefix+'densityfield']:lambda *xs,prefix=prefix:c(rhos[prefix]),
            SYMBOLS[prefix+'chargefield']:lambda *xs,prefix=prefix:c(rhos[prefix]/12+(1 if variant==prefix+'_charge' else 0)),
            SYMBOLS[prefix+'velocityfield']:lambda role,prefix=prefix:constant_field(prefix,role)})
    def match(actual,expected,category,labels):
        expected=list(expected)
        for i,label in enumerate(labels):
            if variant==category+'_'+label:expected[i]='other'
        return list(actual)==expected
    def fields_matrix(field):return tuple(tuple(n(field(a)(*(c(int(i==j)) for i in range(4)))) for j in range(4)) for a in AXES[:3])
    def assignment(matter,frame,rhofn,chargefn,ufn,domain,context):
        if variant=='unknown_assignment':raise ValueError('Density/flow assignment missing')
        if frame not in ('old','new'):return False
        probe=tuple(c(x) for x in (CENTER if frame=='old' else data['newpoint']))
        rho=density if frame=='old' else data['newdensity'];u=velocity if frame=='old' else data['newvelocity']
        return match((matter,frame,context),('matter',frame,'text'),frame+'_assignment',('matter','frame','context')) and variant!=frame+'_assignment_region' and domain(*probe) and n(rhofn(*probe))==rho and n(chargefn(*probe))==rho/12 and tuple(n(ufn(a)(*probe)) for a in AXES[:3])==u
    def frames(old,new,value,context):
        if variant=='unknown_frames':raise ValueError('Frame configuration missing')
        return match((old,new,context),('old','new','text'),'frames',('old','new','context')) and n(value)==(-speed if variant=='frames_speed' else speed)
    callbacks(doc,model,{SYMBOLS['assigned']:assignment,SYMBOLS['frames']:frames})
    model['va']=lambda frame:frame in ('old','new')
    def field_assignment(frame,ef,hf,domain,context):
        if frame not in ('old','new'):return False
        expected=matrices_by_prefix[frame];probe=CENTER if frame=='old' else data['newpoint']
        return match((frame,context),(frame,'text'),frame+'_field',('frame','context')) and fields_matrix(ef)==tuple(map(tuple,expected[0])) and fields_matrix(hf)==tuple(map(tuple,expected[1])) and variant!=frame+'_field_region' and domain(*(c(x) for x in probe))
    def location(matter,frame,event,point,context):
        if frame not in ('old','new'):return False
        return match((matter,frame,event,context),('matter',frame,'event','text'),frame+'_location',('matter','frame','event','context')) and tuple(n(point(a)) for a in AXES)==(CENTER if frame=='old' else data['newpoint'])
    def partial(fn,domain,point,axis,value):
        if variant=='unknown_partial':raise ValueError('Derivative interpretation missing')
        coords=tuple(n(point(a)) for a in AXES)
        coeff=tuple(n(fn(*(c(int(i==j)) for i in range(4)))) for j in range(4))
        for prefix,(ef,hf) in matrices_by_prefix.items():
            if coords!=(CENTER if prefix=='old' else data['newpoint']):continue
            if variant==prefix+'_missing_magnetic_diagonal' and any(coeff==tuple(row) and axis==AXES[i] for i,row in enumerate(hf)):return False
            if coeff in [tuple(row) for row in ef+hf] and domain(*(point(a) for a in AXES)) and n(value)==coeff[AXES.index(axis)]:return True
        return False
    model.update(znn=field_assignment,zpb=location,s5t=partial,sedi=lambda pi:variant!='missing_pi' and n(pi)==3)
    return model,data


def evaluate(doc,model,indices=None):
    if indices is not None:doc={**doc,'statements':[doc['statements'][i] for i in indices]}
    names={d['name'] for d in doc['declarations'] if d['kind']=='primitive'}
    return values(doc,{n:x for n,x in model.items() if n in names},DOMAIN)


def binding_checks(texts):
    docs=[setup_document(text) for text in texts]
    def run(indices=None,**options):
        rows=[]
        for doc in docs:
            model,data=model_for(doc,**options);rows.append(evaluate(doc,model,indices))
        if rows[0]!=rows[1]:raise ValueError('Extracted density transformation differs')
        return rows[0],data
    cases=[]
    for speed,density,velocity,zero in product((F(-3),F(0),F(3)),(F(-4),F(0),F(4)),((F(1),F(-2),F(3)),(F(5),F(0),F(0))),(False,True)):
        row,data=run(speed=speed,density=density,velocity=velocity,magnetic_zero=zero)
        expected=[True]*6+[zero or speed==0,zero,True,False]
        if row!=expected:raise ValueError('Density divergence or magnetic prerequisite differs: '+repr((speed,density,velocity,zero,row)))
        cases.append(dict(speed=str(speed),density=str(density),velocity=list(map(str,velocity)),newdensity=str(data['newdensity']),newvelocity=list(map(str,data['newvelocity'])),zero_magnetic_divergence=zero,results=row))
    edges={}
    row,data=run(velocity=(F(25,3),F(1),F(-2)))
    if row[:4]!=[False,True,False,False] or any(row[4:9]):raise ValueError('Zero denominator accepted or current transform rejected')
    edges['zero_denominator']=row
    row,data=run(velocity=(F(10),F(1),F(-2)))
    if row[:9]!=[True]*9 or data['newdensity']>=0:raise ValueError('Formal negative denominator silently restricted')
    edges['negative_denominator']=dict(results=row,newdensity=str(data['newdensity']))
    contrasts={}
    for prefix in ('old','new'):
        for field,i,j in product(('E','H'),range(3),range(4)):
            name=f'{prefix}_jet_{field}_{i}_{j}';row,_=run(variant=name)
            if row[8]:raise ValueError('Derivative was not bound across frames: '+name)
            contrasts[name]=row
    variants=['new_density','new_velocity_x','new_velocity_y','new_velocity_z','forward_instead_of_inverse','wrong_new_point','missing_pi',
        'frames_old','frames_new','frames_context','frames_speed']
    for prefix in ('old','new'):
        variants += [prefix+'_'+name for name in ('charge','swapped_fields','outside_region','missing_magnetic_diagonal',
            'field_frame','field_context','field_region','location_matter','location_frame','location_event','location_context',
            'assignment_matter','assignment_frame','assignment_context','assignment_region')]
    for variant in variants:
        row,_=run(variant=variant)
        if row[8]:raise ValueError('Frame or quantity correspondence lost: '+variant)
        contrasts[variant]=row
    current_contrasts={}
    for name in ('jx','jy','jz','kx','ky','kz'):
        row,_=run(indices=range(4),variant='current_'+name)
        if row!=[True,False,False,False]:raise ValueError('Independent current value replaced')
        current_contrasts[name]=row
    for doc in docs:
        for variant,message in (('unknown_assignment','Density/flow assignment missing'),('unknown_frames','Frame configuration missing'),('unknown_partial','Derivative interpretation missing')):
            model,_=model_for(doc,variant=variant)
            try:evaluate(doc,model,(8,))
            except ValueError as exc:
                if message not in str(exc):raise
            else:raise ValueError('Unknown boost interpretation supplied')
    return dict(cases=cases,edge_cases=edges,contrasts=contrasts,current_contrasts=current_contrasts,standalone_agrees=True,
        unknown_inputs_refused=True,real_arithmetic_abstracted_to_registered_rational_cuts=True,
        derivatives_use_explicit_affine_oracle=True,pi_integral_abstracted_with_synthetic_value_three=True,
        density_and_velocity_not_recovered_by_dividing_current=True,full_real_field_transformation_proved=False)


def facsimile_check():
    ledger=json.loads(FACSIMILE.read_text(encoding='utf-8'))
    for item in [ledger['pdf'],*ledger['images']]:
        if hashlib.sha256((ROOT/item['path']).read_bytes()).hexdigest()!=item['sha256']:raise ValueError('Density boost facsimile changed')
    source=json.loads((ROOT/'artifacts/written-units-v1/einstein-1905.json').read_text(encoding='utf-8'))
    for m in source['math']:
        if m['id'] in ledger['snapshot_math_sha256'] and m['sha256']!=ledger['snapshot_math_sha256'][m['id']]:raise ValueError('Density boost snapshot changed')
    return ledger


def alignment():
    source=json.loads((ROOT/'artifacts/written-units-v1/einstein-1905.json').read_text(encoding='utf-8'))
    unit=next(u for u in source['units'] if u['id']=='einstein-1905:u0236');math=next(m for m in source['math'] if m['id']=='M0390')
    return dict(segments=[dict(unit=unit['id'],unit_sha256=unit['text_sha256'],math_id=math['id'],math_sha256=math['sha256'],
        definitions=['semp','semq','semr','semt','semu','semv','semx','semy','senb'],status='partial',
        review_ja='三速度と符号付き密度の変換を、同じ物質・出来事・二系・点の場と発散へ結ぶ。零密度と零分母を区別する。電流の変換と対流への分解、磁気側の零発散の追加条件、原刊の磁気側の印刷形を別に保持する。全実解析・全文意味一致は未完。')],semantic_completion=False)


def build_report():
    documents,sizes,texts={},{},[]
    for builder,stem in BUILDERS:
        text,basis=builder();doc=parse(text);texts.append(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text or json.loads((ROOT/('data/'+stem+'-basis-v1.json')).read_text(encoding='utf-8'))!=basis:raise ValueError('Stored density boost differs')
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Density boost roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis);sizes[stem]=dict(characters=len(text),statements=len(doc['statements']))
    doc,parent=parse(texts[1]),parse((ROOT/PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])]!=parent['declarations'] or doc['statements']!=parent['statements']:raise ValueError('Parent changed')
    paths=[*documents,PARENT,*['data/'+stem+'-basis-v1.json' for _,stem in BUILDERS],
        'data/density-boost-facsimile-v1.json','scripts/compose_density_boost.py','scripts/check_density_boost.py',
        'scripts/check_convection_fields.py','scripts/check_field_equations.py','scripts/check_field_constraints.py',
        'scripts/compose_field_constraints.py','scripts/check_parallel_composition.py','scripts/check_plane_waveforms.py',
        'scripts/check_rod_setup.py','scripts/check_comoving_labels.py','scripts/check_real_products.py',
        'noema/finite_semantics.py','noema/polynomial_proofs.py','noema/extraction.py','artifacts/written-units-v1/einstein-1905.json']
    return dict(status='partial_velocity_density_current_boost_and_divergence_connection',documents=documents,sizes=sizes,
        polynomial=polynomial_checks(),residuals=residual_checks(texts[1]),binding=binding_checks(texts[1:]),facsimile=facsimile_check(),alignment=alignment(),
        new_definitions=13,new_primitives=0,new_author_statements=0,parent_preserved=True,roundtrips=True,
        verified_full_units={'kant-1784':0,'einstein-1905':0},source_sha256={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in paths})


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args()
    report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Density boost report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:
            json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Velocity/density/current boost, field divergence and frame bindings checked')


if __name__=='__main__':main()
