"""Check reparameterization, affine calibration and value-based graph matching."""
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
from scripts.compose_four_coordinates import ROOT, CUT, TAU, generic_composed, source_composed

REPORT=ROOT/'reports/four-coordinates-v1.json'
DOMAIN=('f0','m0','alias','bad','x','y','z','t')


def polynomial_checks():
    V,v,w,beta,a,phi,i,j,k,x,y,z,t=('v '+n for n in ('light','speed','component','beta','oldscale','scale','inverse','squaredinverse','lightinverse','x','y','z','time'))
    add=lambda a,b:call('ab',a,b);mul=lambda a,b:call('ad',a,b);sub=lambda a,b:add(a,call('ac',b))
    conjunction=lambda *xs:xs[0] if len(xs)==1 else op('w',xs[0],conjunction(*xs[1:]))
    beta_condition=call('sor',V,v,w,beta)
    common=conjunction(beta_condition,call('sos',a,phi,beta),call('sja',literal(1),w,i),call('sly',V,v,j),call('sja',literal(1),mul(V,V),k))
    xp=sub(x,mul(v,t))
    cx,cy,cz,ct,o,lx,ly,lz,iv=('v '+n for n in ('cx','cy','cz','ct','offset','lx','ly','lz','longinverse'))
    calibration=call('sow',V,v,w,cx,cy,cz,ct,o,lx,ly,lz)
    plane=lambda xx,yy,zz,tt:sub(add(mul(w,xx),mul(sub(V,v),add(yy,zz))),mul(mul(w,V),tt))
    claims={
        'time_form_preserved_by_phi_equals_a_beta':assertion('light speed component beta oldscale scale inverse squaredinverse lightinverse x time',op('y',common,op('e',call('slz',V,v,a,j,xp,t),call('sot',V,v,phi,beta,k,x,t)))),
        'longitudinal_form_preserved':assertion('light speed component beta oldscale scale inverse squaredinverse lightinverse x time',op('y',common,op('e',call('smy',V,a,j,xp),call('sou',v,phi,beta,x,t)))),
        'transverse_form_preserved':assertion('light speed component beta oldscale scale inverse squaredinverse lightinverse y',op('y',common,op('e',call('snx',V,a,i,y),call('sov',phi,y)))),
        'beta_squared_reciprocal_identity':assertion('light speed component beta squaredinverse',op('y',op('w',beta_condition,call('sly',V,v,j)),op('e',mul(beta,beta),mul(mul(V,V),j)))),
        'normalization_preserves_distinct_coefficient_values':assertion('beta oldscale scale',op('y',call('aa',literal(0),beta),op('z',op('e',mul(a,beta),mul(phi,beta)),op('e',a,phi)))),
        'affine_row_determined_by_origin_and_three_rays':assertion('light speed component cx cy cz ct offset lx ly lz longinverse inverse x y z time',op('y',conjunction(calibration,call('sja',literal(1),sub(V,v),iv),call('sja',literal(1),w,i)),op('e',call('sld',cx,cy,cz,ct,o,x,y,z,t),call('sox',v,lx,ly,lz,iv,i,x,y,z,t)))),
        'three_light_samples_alone_leave_an_affine_ambiguity':assertion('light speed component',conjunction(op('e',plane(V,literal(0),literal(0),literal(1)),literal(0)),op('e',plane(v,w,literal(0),literal(1)),literal(0)),op('e',plane(v,literal(0),w,literal(1)),literal(0)))),
        'unchanged_phi_is_valid_after_reparameterization':assertion('',op('y',call('sor',literal(5),literal(3),literal(4),literal(Fraction(5,4))),call('sos',literal(2),literal(2),literal(Fraction(5,4))))),
        'three_light_samples_force_the_moving_origin_value':assertion('',op('e',literal(4*3-20),literal(0))),
    }
    rejected={'unchanged_phi_is_valid_after_reparameterization','three_light_samples_force_the_moving_origin_value'}
    rows={}
    for name,claim in claims.items():
        result=verify_universal(parse(generic_composed()[0]+claim),MEANINGS,timeout_ms=15000)[0]
        if result['status']!=('invalid' if name in rejected else 'valid'):raise ValueError('Four coordinate algebra differs: '+name)
        rows[name]=result
    return {'claims':rows,'rational_polynomial_lemmas_only':True,'full_real_affine_extension_proved':False}


def beta_checks():
    text='r ja[] '+CUT+'.r jb[] '+CUT+'.r jc[] '+CUT+'.q[k spa[k ja[] k jb[] k jc[]]].'
    doc=abstract(candidate(source_composed()[0],text),ARITHMETIC|{'sky'})
    rows={}
    for label,(args,expected) in {'baseline':((5,3,Fraction(5,4)),True),'other_speed':((5,4,Fraction(5,3)),True),'stationary':((5,0,1),True),
        'modern_speed_ratio':((5,3,Fraction(3,5)),False),'negative_root_branch':((5,3,Fraction(-5,4)),False),'wrong_scale':((5,3,2),False),
        'light_speed_boundary':((5,5,0),False),'negative_motion':((5,-3,Fraction(5,4)),False)}.items():
        fixture=ConstructedCuts();model=guarded(doc);fixture.arithmetic(model);model['sky']=lambda value:square_root(fixture,value)
        for symbol,value in zip(('ja','jb','jc'),args):model[symbol]=lambda value=value:fixture.make(value)
        actual=values(doc,model,('object',))[0]
        if actual!=expected:raise ValueError('Historical beta definition differs: '+label)
        rows[label]=actual
    return {'cases':rows,'exact_rational_square_roots_only':True,'beta_not_speed_ratio':True}


def point_model(doc,label='baseline'):
    fixture=ConstructedCuts();n=fixture.read;c=fixture.make;model=guarded(doc);fixture.arithmetic(model)
    speed=0 if label=='stationary' else 3;oldscale=3 if label=='other_old_scale' else 2
    beta=Fraction(1) if speed==0 else Fraction(5,4);phi=oldscale*beta
    first=[0,0,0,0] if label=='zero_origin' else [7,3,4,2]
    x,y,z,t=first
    def transformed(scale):return [scale*beta*(x-speed*t),scale*y,scale*z,scale*beta*(t-Fraction(speed,25)*x)]
    second=transformed(oldscale if label=='old_phi_reused' else phi)
    if label.startswith('wrong_') and label[6:] in ('x','y','z','t'):second[('x','y','z','t').index(label[6:])]+=1
    if label=='mixed_origins':second=[q+o for q,o in zip(second,(1,2,3,4))]
    if label=='wrong_time_sign':second[3]=phi*beta*(t+Fraction(speed,25)*x)
    coords={'f0':first,'m0':second,'alias':second.copy(),'bad':[value+1 for value in second]}
    for name,role in zip(('yn','yo','yp','zc7'),('x','y','z','t')):model[name]=lambda role=role:role
    model.update(tc=lambda:c(5),zb7=lambda:c(speed),sky=lambda value:square_root(fixture,value),
        zc5=lambda record:record in coords,
        zc6=lambda record,role:c(coords.get(record,[0,0,0,0])[('x','y','z','t').index(role)]))
    seen=[]
    def old_phi(value):seen.append(n(value));return c(oldscale)
    callbacks(doc,model,{'zeq':old_phi})
    return model,fixture,coords,seen


def equation_checks():
    text='r ja[] a.r jb[] a.q[k sph[k ja[] k jb[]]].q[k spg[k ja[] k jb[]]].'
    doc=abstract(candidate(source_composed()[0],text),ARITHMETIC|{'sky'})
    rows={}
    for label in ('baseline','zero_origin','stationary','other_old_scale','old_phi_reused','wrong_x','wrong_y','wrong_z','wrong_t','mixed_origins','wrong_time_sign'):
        model,fixture,coords,seen=point_model(doc,label);model.update(ja=lambda:'f0',jb=lambda:'m0')
        actual=values(doc,model,DOMAIN)
        if actual!=[label in ('baseline','zero_origin','stationary','other_old_scale')]*2:raise ValueError('Four equation values differ: '+label)
        if not seen or set(seen)!={0 if label=='stationary' else 3}:raise ValueError('Coefficient evaluated at another input')
        rows[label]={'accepted':actual,'first':list(map(str,coords['f0'])),'second':list(map(str,coords['m0']))}
    return {'cases':rows,'old_and_new_forms_checked_on_non_light_ray_inputs':True,'same_speed_for_all_four_components':True}


def calibration_checks():
    text='r ja[] '+TAU+'.r jb[] a.q[k spl[k ja[] k jb[] k tc[] k zb7[] c[k zeq[]][k zb7[]]]].'
    doc=abstract(candidate(source_composed()[0],text),ARITHMETIC|{'sky'})
    rows={}
    for label in ('x_row','y_row','z_row','missing_origin_constraint','offset_added','y_cross_term','z_cross_term','wrong_velocity','wrong_scale','time_role','nonlinear_same_five_values'):
        model,fixture,_,_=point_model(doc);n=fixture.read;c=fixture.make
        role='y' if label=='y_row' else 'z' if label=='z_row' else 't' if label=='time_role' else 'x'
        model['jb']=lambda:role
        seen=[]
        def row(x,y,z,t):
            x,y,z,t=(n(q) for q in (x,y,z,t));seen.append((x,y,z,t))
            result=Fraction(25,8)*(x-(4 if label=='wrong_velocity' else 3)*t) if role in ('x','t') else Fraction(5,2)*(y if role=='y' else z)
            if label=='missing_origin_constraint':result+=4*x+2*y+2*z-20*t
            if label=='offset_added':result+=1
            if label=='y_cross_term':result+=y
            if label=='z_cross_term':result+=z
            if label=='wrong_scale':result*=Fraction(3,2)
            if label=='nonlinear_same_five_values':result+=x*(x-3)*(x-5)
            return c(result)
        callbacks(doc,model,{'ja':row});actual=values(doc,model,DOMAIN)[0]
        if actual!=(label in ('x_row','y_row','z_row','nonlinear_same_five_values')):raise ValueError('Affine calibration conditions differ: '+label)
        if set(seen)!={(0,0,0,0),(3,0,0,1),(5,0,0,1),(3,4,0,1),(3,0,4,1)}:raise ValueError('Calibration arguments differ')
        rows[label]=actual
    return {'cases':rows,'affine_membership_is_separate_from_five_values':True,'nonlinear_counterexample_matches_five_values_only':True}


def graph_checks():
    doc=abstract(candidate(source_composed()[0],'q[k spi[p spg]].q[k spt[p shf p shg p she p shh]].'),ARITHMETIC|{'sky','sgw','shf','shg','she','shh'})
    rows={}
    for label in ('baseline','duplicate_value_records','excluded_alias_relation','spurious_relation','omitted_relation','empty_graph','different_value_alias'):
        model,fixture,coords,_=point_model(doc);n=fixture.read
        right={'m0','bad'}|({'alias'} if label in ('duplicate_value_records','excluded_alias_relation','different_value_alias') else set())
        pairs={('f0','m0')}
        if label=='duplicate_value_records':pairs.add(('f0','alias'))
        if label=='spurious_relation':pairs.add(('f0','bad'))
        if label=='omitted_relation':pairs=set()
        if label=='different_value_alias':coords['alias']=[value+2 for value in coords['m0']]
        model.update(shf=lambda record:record=='f0' and label!='empty_graph',shg=lambda record:record in right,
            she=lambda first,second:(first,second) in pairs,
            shh=lambda first,second:coords.get(first)==coords.get(second),
            sgw=lambda *args:label not in ('empty_graph','omitted_relation'))
        actual=values(doc,model,DOMAIN)
        expected=[label in ('baseline','duplicate_value_records','different_value_alias'),label!='excluded_alias_relation']
        if actual!=expected:raise ValueError('Value graph or alias closure differs: '+label+repr(actual))
        rows[label]=actual
    return {'cases':rows,'existence_and_functionality_are_oracles':True,'both_directions_and_equal_value_aliases_checked':True}


def component_binding_checks():
    text=''.join('q[k spn[k zfh[k '+role+'[]] k '+role+'[]]].' for role in ('yn','yo','yp'))
    doc=abstract(candidate(source_composed()[0],text),ARITHMETIC|{'sky','she'})
    sort=next(d['result'] for d in doc['declarations'] if d['name']=='zfh');rows={}
    for label in ('baseline','wrong_x_function','wrong_y_function','wrong_z_function','swapped_transverse_functions','wrong_x_time_argument'):
        model,fixture,_,_=point_model(doc);n=fixture.read;c=fixture.make
        model['she']=lambda first,second:(first,second)==('f0','m0')
        def candidate_function(role):
            selected={'y':'z','z':'y'}.get(role,role) if label=='swapped_transverse_functions' else role
            def evaluate(x,y,z,t):
                x,y,z,t=(n(value) for value in (x,y,z,t))
                value=Fraction(25,8)*(x-3*(x if label=='wrong_x_time_argument' else t)) if selected=='x' else Fraction(5,2)*(y if selected=='y' else z)
                if label=='wrong_'+role+'_function':value+=1
                return c(value)
            return FunctionValue(tuple(sort['parameters']),sort['result'],evaluate)
        model['zfh']=candidate_function
        actual=values(doc,model,DOMAIN)
        expected=[label not in ('wrong_x_function','wrong_x_time_argument'),label not in ('wrong_y_function','swapped_transverse_functions'),label not in ('wrong_z_function','swapped_transverse_functions')]
        if actual!=expected:raise ValueError('Spatial row and same-event component differ: '+label)
        rows[label]=actual
    return {'cases':rows,'same_event_pair_is_an_oracle':True,'separate_spatial_rows_bound_to_corresponding_components':True}


def finite_refusals():
    rows={}
    for label,query in (('all_real_affine_membership','k spm[k ja[] k yn[] k tc[] k zb7[] c[k zeq[]][k zb7[]]]'),):
        doc=abstract(candidate(source_composed()[0],'r ja[] '+TAU+'.q['+query+'].'),ARITHMETIC|{'sky'})
        model,fixture,_,_=point_model(doc);callbacks(doc,model,{'ja':lambda x,y,z,t:fixture.make(Fraction(25,8)*(fixture.read(x)-3*fixture.read(t)))})
        try:values(doc,model,DOMAIN)
        except ValueError as error:
            if 'Cannot finitely quantify the rational number domain' not in str(error):raise
            rows[label]={'refused':True,'reason':str(error)}
        else:raise ValueError('Full affine representation replaced by five samples')
    return rows


def attribution_checks():
    doc=parse(source_composed()[0]);doc['statements']=doc['statements'][-3:];rows={}
    for label in ('baseline','wrong_author','wrong_scope','wrong_context','wrong_added_premise','wrong_extended_conclusion','wrong_rewrite_premise','wrong_old_form','wrong_new_form','wrong_beta_content'):
        model=guarded(doc)
        for k,v in {'zfi':'extension','zfj':'rewrite','zfk':'beta','rd':'author','rh':'scope','ri':'text'}.items():model[k]=lambda v=v:v
        symbol=lambda d:json.loads(d.syntax)['symbol']
        common=lambda a,s,c:(a,s,c)==('other' if label=='wrong_author' else 'author','other' if label=='wrong_scope' else 'scope','other' if label=='wrong_context' else 'text')
        model.update(zfl=lambda node,a,p,d,s,c:common(a,s,c) and (node,symbol(p),symbol(d))==('extension','spq' if label=='wrong_added_premise' else 'spo','spk' if label=='wrong_extended_conclusion' else 'spj'),
            zd3=lambda node,a,p,before,after,s,c:common(a,s,c) and (node,symbol(p),symbol(before),symbol(after))==('rewrite','spo' if label=='wrong_rewrite_premise' else 'spr','spk' if label=='wrong_old_form' else 'spj','spj' if label=='wrong_new_form' else 'spk'),
            uh=lambda node,a,d,s,c:common(a,s,c) and (node,symbol(d))==('beta','spk' if label=='wrong_beta_content' else 'spq'))
        actual=values(doc,model,('extension','rewrite','beta','author','scope'))
        expected=[label not in {'wrong_author','wrong_scope','wrong_context'}|bad for bad in ({'wrong_added_premise','wrong_extended_conclusion'},{'wrong_rewrite_premise','wrong_old_form','wrong_new_form'},{'wrong_beta_content'})]
        if actual!=expected:raise ValueError('Four-coordinate interpretation attribution differs: '+label)
        rows[label]=actual
    return rows


def alignment():
    artifact=json.loads((ROOT/'artifacts/written-units-v1/einstein-1905.json').read_text(encoding='utf-8'));rows=[]
    hashes=['0b5f39f615fe8ce3407f9e86fa405889e47213e7e5a6cdb86cadb6409a82b990','022b0a493a7742be8d706b380b62f7fef1a28f85af68c8a525b1c5adca7fb63e','ad6f70890a12d8f25cf83a9ebb72fac6316cf86f4e2e27c3ef03027f2b994c84','3e47ecca9e8e1dce7d52511272a395294f2376d296acb750f9c7cb37baa9fdc9']
    mhashes=['5789f9fd8ca6ee1a7ad7b9d6fdd7d9d84bd2ac37e2e0869db607ee20d6aa8e62','4e4203dfe2d4e8afa4bd7c14dabfe07b4c098336069ea67d7949431a0d04da26','7fe08f106eed593b27d4b56b5d87bb93c8c383efd0886ec0072c9924be8fc291']
    definitions=[['sph','spj','spr'],['spb','spc','spd','spe','spf','spg','spk'],['spa','spq'],['soy','soz','spa','spq']]
    for index,(digest,defs) in enumerate(zip(hashes,definitions),81):
        uid=f'einstein-1905:u{index:04d}';unit=next(u for u in artifact['units'] if u['id']==uid)
        if hashlib.sha256(unit['text'].encode('utf-8')).hexdigest()!=digest:raise ValueError('Four coordinates source changed')
        rows.append({'unit':uid,'unit_sha256':digest,'start':0,'end':len(unit['text']),'source':unit['text'],'definitions':defs,'status':'partial_explicit_reading','full_semantic_equivalence':False})
        for mid in unit['math_ids']:
            m=next(m for m in artifact['math'] if m['id']==mid);mdigest=mhashes[int(mid[1:])-134]
            if hashlib.sha256(m['mathml'].encode('utf-8')).hexdigest()!=mdigest:raise ValueError('Four coordinates math changed')
            rows.append({'unit':uid,'unit_sha256':digest,'math_id':mid,'math_sha256':mdigest,'definitions':defs,'status':'partial','full_semantic_equivalence':False})
    return {'segments':rows,'facsimile_checked':False,'verified_full_units':0,'coefficient_reparameterization_explicit':True,'affine_calibration_is_additional_interpretation':True}


def build_report():
    documents={}
    for compose in (generic_composed,source_composed):
        text,basis=compose();doc=parse(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text:raise ValueError('Stored four coordinates differ')
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Four-coordinate roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis)
    paths=[*documents,'data/four-coordinates-basis-v1.json','data/einstein-four-coordinates-basis-v1.json',
        'examples/v014/einstein-transverse-space.noema','examples/v014/transverse-space.noema',
        'scripts/compose_four_coordinates.py','scripts/check_four_coordinates.py','scripts/check_tau_differential.py','scripts/check_transverse_time.py',
        'noema/discourse.py','noema/finite_semantics.py','noema/polynomial_proofs.py']
    text=source_composed()[0];previous=(ROOT/'examples/v014/einstein-transverse-space.noema').read_text(encoding='utf-8')
    return {'status':'partial_four_coordinates_and_coefficient_reparameterization','documents':documents,
        'polynomial_lemmas':polynomial_checks(),'beta':beta_checks(),'four_equations':equation_checks(),
        'calibration':calibration_checks(),'component_binding':component_binding_checks(),'value_graph':graph_checks(),'finite_refusals':finite_refusals(),
        'attribution':attribution_checks(),'alignment':alignment(),'roundtrips':True,
        'verified_full_units':{'einstein-1905':0,'kant-1784':0},
        'notation_size':{'canonical_source_document_characters':len(text),'added_characters':len(text)-len(previous)},
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args();report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Four coordinates report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Four coordinate normalization, affine calibration and value graphs checked')


if __name__=='__main__':main()
