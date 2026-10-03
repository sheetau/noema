"""Check transformed material surfaces, frame-specific slices and semiaxes."""
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
from scripts.check_rod_setup import guarded
from scripts.check_real_products import MEANINGS, call, op, assertion, conjunction
from scripts.check_moving_light_trip import literal
from scripts.check_tau_differential import ARITHMETIC, ConstructedCuts
from scripts.check_transverse_time import square_root
from scripts.compose_sphere_slice import ROOT, CUT, generic_composed, source_composed

REPORT=ROOT/'reports/sphere-slice-v1.json'


def polynomial_checks():
    names='light speed beta radius x y z time xx yy zz tt';V,v,b,R,x,y,z,t,X,Y,Z,T=['v '+n for n in names.split()]
    zero=literal(0);one=literal(1);mul=lambda a,b:call('ad',a,b);add=lambda a,b:call('ab',a,b)
    sub=lambda a,b:add(a,call('ac',b));eq=lambda a,b:op('e',a,b)
    a,p,q='v axis','v cosine','v sine'
    claims={
        'sphere_and_moving_surface_are_equivalent':assertion(names,op('y',call('srb',V,v,b,one,x,y,z,t,X,Y,Z,T),op('z',call('ssu',R,X,Y,Z),call('ssv',V,v,b,R,x,y,z,t)))),
        'subtracting_center_motion_gives_zero_time_shape':assertion('light speed beta radius x y z time',op('z',call('ssv',V,v,b,R,add(x,mul(v,t)),y,z,t),call('ssv',V,v,b,R,x,y,z,zero))),
        'semiaxes_give_the_ellipsoid_equation':assertion('beta radius axis x y z',op('y',call('ssw',b,R,a,R,R),op('z',call('ssu',R,mul(b,x),y,z),call('ssx',a,R,x,y,z)))),
        'positive_semiaxis_intersections_are_on_surface':assertion('beta radius axis',op('y',call('ssw',b,R,a,R,R),conjunction(call('ssu',R,mul(b,a),zero,zero),call('ssu',R,zero,R,zero),call('ssu',R,zero,zero,R)))),
        'rotations_around_motion_axis_preserve_surface':assertion('axis radius x y z cosine sine',op('y',eq(add(mul(p,p),mul(q,q)),one),op('z',call('ssx',a,R,x,y,z),call('ssx',a,R,x,sub(mul(p,y),mul(q,z)),add(mul(q,y),mul(p,z)))))),
        'zero_velocity_has_equal_three_semiaxes':assertion('light beta radius axis',op('y',conjunction(call('sra',V,zero,b),call('ssw',b,R,a,R,R)),eq(a,R))),
        'contracted_endpoint_is_on_original_uncontracted_sphere':assertion('',op('y',call('ssv',literal(5),literal(3),literal(Fraction(5,4)),literal(5),literal(4),zero,zero,zero),call('ssu',literal(5),literal(4),zero,zero))),
        'diameter_can_replace_the_semiaxis':assertion('',call('ssw',literal(Fraction(5,4)),literal(5),literal(8),literal(5),literal(5))),
        'laboratory_simultaneity_is_moving_frame_simultaneity':assertion('',eq(literal(Fraction(3,5)),literal(Fraction(-3,5)))),
    }
    rejected={'contracted_endpoint_is_on_original_uncontracted_sphere','diameter_can_replace_the_semiaxis','laboratory_simultaneity_is_moving_frame_simultaneity'}
    rows={}
    for name,claim in claims.items():
        result=verify_universal(parse(generic_composed()[0]+claim),MEANINGS,timeout_ms=15000)[0]
        if result['status']!=('invalid' if name in rejected else 'valid'):raise ValueError('Sphere slice algebra differs: '+name+repr(result))
        rows[name]=result
    return {'claims':rows,'rational_polynomial_lemmas_only':True,'rigidity_or_material_boundary_proved':False}


EVENTS=('left','right','transverse','center','later')
REST=('rL','rR','rY','rO','rT');MOVING=('mL','mR','mY','mO','mT')
DOMAIN=EVENTS+REST+MOVING+('body','otherbody','orphan','rest','moving','origin','x','y','z','t','length','time')


def surface_model(doc,label='baseline'):
    fixture=ConstructedCuts();c=fixture.make;n=fixture.read;model=guarded(doc);fixture.arithmetic(model)
    speed=0 if label=='stationary' else -3 if label=='opposite_velocity' else 3
    beta=Fraction(1) if speed==0 else Fraction(5,4)
    axis=Fraction(5)/beta
    coords=dict(zip(REST,[[-axis,0,0,0],[axis,0,0,0],[0,5,0,0],[0,0,0,0],[speed+axis,0,0,1]]))
    if label=='no_zero_slice':
        for row in coords.values():row[0]+=speed;row[3]+=1
    for rr,mr in zip(REST,MOVING):
        x,y,z,t=coords[rr];coords[mr]=[beta*(x-speed*t),y,z,beta*(t-Fraction(speed,25)*x)]
    if label=='wrong_rest_point':coords['rR'][0]+=1
    if label=='wrong_moving_point':coords['mR'][0]+=1
    members={'left','right','transverse','later'}
    if label=='missing_surface_point':members.remove('left')
    if label=='interior_as_surface':members.add('center')
    if label=='unmeasured_surface_event':members.add('orphan')
    charts={(event,frame):record for frame,records in (('rest',REST),('moving',MOVING)) for event,record in zip(EVENTS,records)}
    for key,value in {'yn':'x','yo':'y','yp':'z','zc7':'t','ra':'rest','zbm':'moving','zhw':'body','zb6':'motion','ta':'length','rb':'time'}.items():model[key]=lambda value=value:value
    model.update(tc=lambda:c(5),zb7=lambda:c(5 if label=='light_speed_boundary' else speed),zhx=lambda:c(-5 if label=='negative_radius' else 5),sky=lambda value:square_root(fixture,value),
        zc5=lambda record:record in coords,
        zc6=lambda record,role:c(coords.get(record,[0,0,0,0])[('x','y','z','t').index(role)] if role in ('x','y','z','t') else 0),
        zc4=lambda event:event in EVENTS and label!='empty_event_scope',
        zhu=lambda body,event,setting:body==('otherbody' if label=='wrong_body' else 'body') and event in members and setting=='motion',
        zbq=lambda body,setting:(body,setting)==('body','motion') and label!='not_rigid',
        x4=lambda body,frame,setting:(body,frame,setting)==('body','moving','motion') and label!='not_stationary',
        zbn=lambda frame,setting:'origin',
        zbv=lambda frame,origin,setting:(frame,origin,setting)==('moving','origin','motion') and label!='wrong_origin_assignment',
        zhv=lambda body,place,frame,setting:(body,place,frame,setting)==('body','origin','moving','motion') and label!='wrong_center',
        zbo=lambda frame,role,setting:role,
        zgj=lambda moving,rest,axis,value,lengthunit,timeunit,setting:(moving,rest,axis,n(value),lengthunit,timeunit,setting)==('moving','rest','x',-speed if label=='wrong_motion' else speed,'length','time','motion'))
    if any(d['name']=='shd' and d['kind']=='primitive' for d in doc['declarations']):
        model['shd']=lambda event,record,frame,setting:setting=='motion' and charts.get((event,frame))==record
    return model,fixture,coords


def equation_checks():
    query='r ja[] a.r jb[] a.q[k ssn[k ja[] k jb[]]].q[k ssz[k jb[] k zhx[]]].q[k stc[k ja[] k zhx[]]].q[k std[k ja[] k zhx[]]].q[k stf[k ja[] k zhx[]]].q[k stj[k ja[] k zhx[]]].'
    doc=abstract(candidate(source_composed()[0],query),ARITHMETIC|{'sky'});rows={}
    for label,pair in (('baseline',('rR','mR')),('left_endpoint',('rL','mL')),('transverse_endpoint',('rY','mY')),('later_surface',('rT','mT')),('interior',('rO','mO')),('wrong_rest_point',('rR','mR')),('wrong_moving_point',('rR','mR')),('stationary',('rR','mR')),('opposite_velocity',('rR','mR')),('negative_radius',('rR','mR')),('light_speed_boundary',('rR','mR'))):
        model,_,coords=surface_model(doc,label);model.update(ja=lambda:pair[0],jb=lambda:pair[1])
        actual=values(doc,model,DOMAIN)
        expected=[label not in ('wrong_rest_point','wrong_moving_point','light_speed_boundary'),
            label not in ('interior','wrong_moving_point','negative_radius'),
            label not in ('interior','wrong_rest_point','negative_radius','light_speed_boundary')]
        expected+=([expected[2] and label!='later_surface']*3)
        if actual!=expected:raise ValueError('Surface equation or selected time differs: '+label+repr(actual))
        rows[label]={'accepted':actual,'rest':list(map(str,coords[pair[0]])),'moving':list(map(str,coords[pair[1]]))}
    return {'cases':rows,'sqrt_structure_and_three_equivalent_zero_slices_checked':True,'surface_not_solid_interior':True}


def semiaxis_checks():
    text='r ja[] '+CUT+'.r jb[] '+CUT+'.r jc[] '+CUT+'.q[k stg[k zhx[] k ja[] k jb[] k jc[]]].'
    doc=abstract(candidate(source_composed()[0],text),ARITHMETIC|{'sky'});rows={}
    for label,args in {'baseline':(4,5,5),'diameter':(8,5,5),'transverse_contraction':(4,4,4),'swapped_axes':(5,4,5),'negative_axis':(-4,5,5),'stationary':(5,5,5),'opposite_velocity':(4,5,5),'light_speed_boundary':(0,5,5),'negative_radius':(4,5,5)}.items():
        model,fixture,_=surface_model(doc,label)
        for name,value in zip(('ja','jb','jc'),args):model[name]=lambda value=value:fixture.make(value)
        actual=values(doc,model,DOMAIN)[0]
        if actual!=(label in ('baseline','stationary','opposite_velocity')):raise ValueError('Sphere semiaxes differ: '+label)
        rows[label]=actual
    return {'cases':rows,'semiaxis_not_diameter':True,'two_transverse_axes_keep_the_radius':True}


def membership_checks():
    doc=abstract(candidate(source_composed()[0],''.join('q[t[k '+name+'[]][k zb6[]]].' for name in ('stn','stp','stq','sts'))),ARITHMETIC|{'sky','shd'});rows={}
    labels=('baseline','missing_surface_point','interior_as_surface','unmeasured_surface_event','wrong_body','empty_event_scope','wrong_rest_point','wrong_moving_point','wrong_center','not_rigid','not_stationary','wrong_origin_assignment','wrong_motion','no_zero_slice')
    for label in labels:
        model,_,_=surface_model(doc,label);actual=values(doc,model,DOMAIN)
        if label=='baseline':expected=[True]*4
        elif label in ('missing_surface_point','interior_as_surface','unmeasured_surface_event','wrong_body','empty_event_scope'):expected=[False]*4
        elif label=='wrong_rest_point':expected=[True,False,False,False]
        elif label in ('wrong_moving_point','wrong_center','not_rigid','not_stationary','wrong_origin_assignment','wrong_motion'):expected=[False,True,True,True]
        else:expected=[True,True,False,False]
        if actual!=expected:raise ValueError('Material surface membership differs: '+label+repr(actual))
        rows[label]=actual
    return {'cases':rows,'same_body_and_all_selected_records_checked':True,'zero_time_slice_must_be_nonempty':True,'physical_boundary_and_charts_are_oracles':True,'continuous_spatial_coverage_proved':False}


def simultaneity_checks():
    query='r ja[] a.r jb[] a.r jc[] a.r jd[] a.q[k sca[k zc6[k ja[] k zc7[]] k zc6[k jb[] k zc7[]]]].q[k sca[k zc6[k jc[] k zc7[]] k zc6[k jd[] k zc7[]]]].'
    doc=abstract(candidate(source_composed()[0],query),ARITHMETIC|{'sky'});rows={}
    for label in ('baseline','stationary'):
        model,fixture,coords=surface_model(doc,label)
        for name,value in zip(('ja','jb','jc','jd'),('rL','rR','mL','mR')):model[name]=lambda value=value:value
        actual=values(doc,model,DOMAIN)
        if actual!=[True,label=='stationary']:raise ValueError('Frame simultaneity collapsed')
        rows[label]={'equal_times':actual,'moving_times':[str(coords['mL'][3]),str(coords['mR'][3])]}
    return {'cases':rows,'same_lab_time_does_not_select_same_moving_time':True}


def attribution_checks():
    doc=parse(source_composed()[0]);doc['statements']=doc['statements'][-6:];rows={}
    for label in ('baseline','wrong_author','wrong_scope','wrong_context','wrong_equations','missing_clock_topic','wrong_setup','wrong_transform','wrong_slice','wrong_shape','wrong_axes'):
        model=guarded(doc)
        constants={'zht':'heading','zhy':'setup','zhz':'transform','zh2':'slice','zh3':'shape','zh4':'axes','rd':'author','rh':'scope','ri':'text'}
        for key,value in constants.items():model[key]=lambda value=value:value
        sym=lambda d:json.loads(d.syntax)['symbol']
        common=lambda a,s,c:(a,s,c)==('other' if label=='wrong_author' else 'author','other' if label=='wrong_scope' else 'scope','other' if label=='wrong_context' else 'text')
        model.update(zhr=lambda node,a,e,subjects,s,c:common(a,s,c) and node=='heading' and sym(e)==('spg' if label=='wrong_equations' else 'ssn') and {sym(d) for d in subjects.items}==({'sta'} if label=='missing_clock_topic' else {'sta','stb'}),
            ug=lambda node,a,d,s,c:common(a,s,c) and (node,sym(d))==('setup','stp' if label=='wrong_setup' else 'stn'),
            uh=lambda node,a,d,s,c:common(a,s,c) and (node,sym(d))==('axes','sts' if label=='wrong_axes' else 'str'))
        triples={('transform','sto','stq' if label=='wrong_transform' else 'stp'),('slice','stp','stp' if label=='wrong_slice' else 'stq'),('shape','stq','stp' if label=='wrong_shape' else 'sts')}
        model['zc']=lambda node,a,p,d,s,c:common(a,s,c) and (node,sym(p),sym(d)) in triples
        actual=values(doc,model,tuple(v for k,v in constants.items() if k!='ri'))
        bads=({'wrong_equations','missing_clock_topic'},{'wrong_setup'},{'wrong_transform'},{'wrong_slice'},{'wrong_shape'},{'wrong_axes'})
        expected=[label not in {'wrong_author','wrong_scope','wrong_context'}|bad for bad in bads]
        if actual!=expected:raise ValueError('Sphere section attribution differs: '+label)
        rows[label]=actual
    return rows


def alignment():
    path=ROOT/'artifacts/written-units-v1/einstein-1905.json';artifact=json.loads(path.read_text(encoding='utf-8'))
    inventory=json.loads((ROOT/'reports/written-units-v1.json').read_text(encoding='utf-8'))
    if hashlib.sha256(path.read_bytes()).hexdigest()!=inventory['works']['einstein-1905']['units_sha256']:raise ValueError('Pinned sphere source differs')
    definitions=[['sta','stb','ssn'],['ssy','ssz','stk','stn'],['ssy','ssz','stk'],['stl','stm','std'],['ste','stf','stq'],['sti','stj','sts'],['sth','stg','str']];rows=[]
    for index,defs in enumerate(definitions,109):
        uid=f'einstein-1905:u{index:04}';unit=next(u for u in artifact['units'] if u['id']==uid);digest=unit['text_sha256']
        if hashlib.sha256(unit['text'].encode('utf-8')).hexdigest()!=digest:raise ValueError('Sphere source changed')
        rows.append({'unit':uid,'unit_sha256':digest,'start':0,'end':len(unit['text']),'source':unit['text'],'definitions':defs,'status':'partial_explicit_reading','full_semantic_equivalence':False})
        for mid in unit['math_ids']:
            item=next(m for m in artifact['math'] if m['id']==mid)
            if hashlib.sha256(item['mathml'].encode('utf-8')).hexdigest()!=item['sha256']:raise ValueError('Sphere source math changed')
            rows.append({'unit':uid,'unit_sha256':digest,'math_id':mid,'math_sha256':item['sha256'],'definitions':defs,'status':'partial','full_semantic_equivalence':False})
    return {'segments':rows,'facsimile_checked':False,'verified_full_units':0,'mathml_sqrt_structure_preserved':True,'source_axes_read_as_semiaxes':True}


def build_report():
    documents={}
    for compose in (generic_composed,source_composed):
        text,basis=compose();doc=parse(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text:raise ValueError('Stored sphere slice differs')
        if json.loads((ROOT/('data/'+basis['document'].split('/')[-1].replace('.noema','-basis-v1.json'))).read_text(encoding='utf-8'))!=basis:raise ValueError('Stored sphere basis differs')
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Sphere slice roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis)
    paths=[*documents,'data/sphere-slice-basis-v1.json','data/einstein-sphere-slice-basis-v1.json',
        'examples/v014/transverse-rod-scale.noema','examples/v014/einstein-transverse-rod-scale.noema',
        'scripts/compose_sphere_slice.py','scripts/check_sphere_slice.py','scripts/check_tau_differential.py','scripts/check_transverse_time.py',
        'reports/written-units-v1.json','artifacts/written-units-v1/einstein-1905.json',
        'noema/discourse.py','noema/finite_semantics.py','noema/polynomial_proofs.py']
    text=source_composed()[0];previous=(ROOT/'examples/v014/einstein-transverse-rod-scale.noema').read_text(encoding='utf-8')
    return {'status':'partial_physical_sphere_and_frame_bound_slice','documents':documents,
        'polynomial_lemmas':polynomial_checks(),'equations':equation_checks(),'semiaxes':semiaxis_checks(),
        'material_surface':membership_checks(),'simultaneity':simultaneity_checks(),'attribution':attribution_checks(),
        'alignment':alignment(),'roundtrips':True,'verified_full_units':{'einstein-1905':0,'kant-1784':0},
        'notation_size':{'canonical_source_document_characters':len(text),'added_characters':len(text)-len(previous)},
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args();report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Sphere slice report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Material sphere, frame time slice, rotations and positive semiaxes checked')


if __name__=='__main__':main()
