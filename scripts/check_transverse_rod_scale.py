"""Verify endpoint timing, positive measured lengths and scale normalization."""
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
from scripts.check_real_products import MEANINGS, call, op, assertion, conjunction
from scripts.check_moving_light_trip import literal
from scripts.check_tau_differential import ARITHMETIC, ConstructedCuts
from scripts.check_transverse_time import square_root
from scripts.compose_transverse_rod_scale import ROOT, CUT, generic_composed, source_composed

REPORT=ROOT/'reports/transverse-rod-scale-v1.json'


def polynomial_checks():
    names='light speed beta scale proper x y z time tau';args=['v '+name for name in names.split()]
    V,v,b,p,l,x,y,z,t,tau=args;zero=literal(0);one=literal(1)
    mul=lambda a,b:call('ad',a,b);eq=lambda a,b:op('e',a,b)
    a,m,f,r=('v '+n for n in ('plus','minus','forward','reverse'))
    rod=call('sru',l,a,m,f,r)
    claims={
        'endpoint_coordinates_follow_from_four_equations':assertion(names,op('y',call('srt',*args),conjunction(eq(x,mul(v,t)),eq(z,zero),eq(mul(p,y),l)))),
        'positive_equal_lengths_give_positive_equal_factors':assertion('proper plus minus forward reverse',op('y',rod,conjunction(eq(a,m),call('aa',zero,a),call('aa',zero,m)))),
        'reciprocity_and_measured_symmetry_fix_both_factors':assertion('proper plus minus forward reverse',op('y',conjunction(rod,eq(mul(a,m),one)),conjunction(eq(a,one),eq(m,one),eq(f,l),eq(r,l)))),
        'explicit_positive_branch_fixes_the_factors':assertion('plus minus',op('y',call('srv',a,m),conjunction(eq(a,one),eq(m,one)))),
        'same_nonzero_proper_length_and_same_extent_give_same_factor':assertion('proper plus minus forward',op('y',conjunction(op('u',eq(l,zero)),eq(mul(a,f),l),eq(mul(m,f),l)),eq(a,m))),
        'positive_length_relations_make_equalities_equivalent':assertion('proper plus minus forward reverse',op('y',conjunction(call('aa',zero,l),call('aa',zero,f),call('aa',zero,r),eq(mul(a,f),l),eq(mul(m,r),l)),op('z',eq(f,r),eq(a,m)))),
        'reciprocity_and_evenness_without_sign_force_one':assertion('',op('y',conjunction(eq(mul(literal(-1),literal(-1)),one),eq(literal(-1),literal(-1))),eq(literal(-1),one))),
        'positive_evenness_without_reciprocity_forces_one':assertion('',op('y',conjunction(eq(literal(2),literal(2)),call('aa',zero,literal(2))),eq(literal(2),one))),
        'zero_rod_length_identifies_the_factors':assertion('',op('y',conjunction(eq(mul(literal(2),zero),zero),eq(mul(literal(3),zero),zero)),eq(literal(2),literal(3)))),
    }
    rejected={'reciprocity_and_evenness_without_sign_force_one','positive_evenness_without_reciprocity_forces_one','zero_rod_length_identifies_the_factors'}
    rows={}
    for name,claim in claims.items():
        result=verify_universal(parse(generic_composed()[0]+claim),MEANINGS,timeout_ms=15000)[0]
        if result['status']!=('invalid' if name in rejected else 'valid'):raise ValueError('Rod scale algebra differs: '+name+repr(result))
        rows[name]=result
    return {'claims':rows,'rational_polynomial_lemmas_only':True,'absolute_distance_alone_excludes_negative_phi':False}


DOMAIN=('rod','lo','hi','e0','e1','e2','e3','lr','hr','lm','hm','rlr','rhr','rlm','rhm','rest','moving','x','y','z','t','p0','p1','p2','p3','length','time','other')


def rod_model(doc,label='baseline'):
    fixture=ConstructedCuts();n=fixture.read;c=fixture.make;model=guarded(doc);fixture.arithmetic(model)
    plus,minus={'reciprocal_unequal':(2,Fraction(1,2)),'equal_not_reciprocal':(2,2),'negative_pair':(-1,-1),'zero_factor':(0,1)}.get(label,(1,1))
    proper=0 if label=='zero_length' else 6
    coords={};charts={};events={'motion':('e0','e1'),'other':('e2','e3'),'text':('e0','e1')}
    places={'motion':('p0','p1'),'other':('p2','p3'),'text':('p0','p1')}
    lengths={};speeds={'motion':3,'other':-3,'text':4}
    for scene,speed,factor,prefix in (('motion',3,plus,''),('other',-3,minus,'r')):
        extent=Fraction(proper,factor) if factor else Fraction(0);lengths[scene]=abs(extent)
        for high,event in enumerate(events[scene]):
            time=3 if label=='nonsimultaneous' and scene=='motion' and high else 2
            x=speed*time;y=extent if high else 0
            rest=[x,y,0,time];moving=[0,proper if high else 0,0,Fraction(4,5)*factor*time]
            rr=prefix+('hr' if high else 'lr');mr=prefix+('hm' if high else 'lm')
            coords[rr]=rest;coords[mr]=moving;charts[event,'rest',scene]=rr;charts[event,'moving',scene]=mr
    lengths['text']=6
    if label=='wrong_high_y':coords['hr'][1]+=1
    if label=='wrong_axis_coordinate':coords['hm'][0]=1
    if label=='wrong_length_candidate':lengths['motion']+=1
    for key,value in {'yn':'x','yo':'y','yp':'z','zc7':'t','ra':'rest','zbm':'moving','zgu':'rod','zgv':'lo','zgw':'hi','zb6':'motion','zg2':'other','ta':'length','rb':'time'}.items():model[key]=lambda value=value:value
    model.update(tc=lambda:c(5),zb7=lambda:c(3),zgz=lambda:c(proper),sky=lambda value:square_root(fixture,value),
        zc5=lambda record:record in coords,
        zc6=lambda record,role:c(coords.get(record,[0,0,0,0])[('x','y','z','t').index(role)] if role in ('x','y','z','t') else 0),
        zc4=lambda event:event in ('e0','e1','e2','e3'),
        zgx=lambda scene:events[scene][0],zgy=lambda scene:events[scene][1],
        zdz=lambda event,frame,scene:charts.get((event,frame,scene),'lr'),
        zha=lambda scene:c(lengths[scene]),zhb=lambda scene:c(speeds[scene]),
        zhd=lambda scene:'x',zhc=lambda scene:scene in ('motion','other'),
        xa=lambda rod:rod=='rod',zbq=lambda rod,scene:rod=='rod' and label!='not_rigid',
        x4=lambda rod,frame,scene:(rod,frame)==('rod','moving'),
        zbo=lambda frame,role,scene:role,
        yu=lambda rod,frame,axis,scene:(rod,frame,axis)==('rod','moving','y'),
        zbw=lambda frame,axis,role,scene:(frame,axis,role)==('moving','y','y'),
        zbs=lambda first,second,scene:(first,second)==('x','y') and label!='not_transverse',
        xf=lambda endpoint,rod,frame,scene:endpoint in ('lo','hi') and rod=='rod' and frame in ('rest','moving') and not(label=='wrong_rod_endpoint' and endpoint=='hi'),
        xg=lambda endpoint,event,place,frame,scene:(endpoint,event,place) in {('lo',events[scene][0],places[scene][0]),('hi',events[scene][1],places[scene][1])} and frame in ('rest','moving') and not(label=='wrong_event_location' and endpoint=='hi'),
        cb=lambda event,place,frame:frame in ('rest','moving') and (event,place) in {('e0','p0'),('e1','p1'),('e2','p2'),('e3','p3')})
    def motion(moving,reference,axis,speed,lengthunit,timeunit,scene):
        expected=speeds[scene]
        return (moving,reference,axis,n(speed),lengthunit,timeunit)==('moving','rest','x',-expected if label=='wrong_motion_sign' else expected,'time' if label=='wrong_units' else 'length','time')
    model['zgj']=motion
    model['za']=lambda rod,frame,unit,value,scene:rod=='rod' and unit=='length' and n(value)==(proper if frame=='moving' else lengths[scene]) and frame in ('rest','moving')
    def distance(low,high,frame,unit,value):
        factor=plus if (low,high)==('p0','p1') else minus if (low,high)==('p2','p3') else 0
        return bool(factor) and (frame,unit)==('rest','length') and n(value)==abs(Fraction(proper,factor))
    model['th']=distance
    callbacks(doc,model,{'zeq':lambda speed:c((minus if n(speed)<0 else plus)/Fraction(5,4))})
    primitives={d['name'] for d in doc['declarations'] if d['kind']=='primitive'}
    if 'shd' in primitives:model['shd']=lambda event,record,frame,scene:charts.get((event,frame,scene))==record
    return model,fixture,coords,lengths


def endpoint_checks():
    query='r ja[] a.r jb[] a.r jc[] a.r jd[] a.q[k srz[k ja[] k jb[] k jc[] k jd[] k zb7[] k zgz[]]].q[k sry[k jb[] k zb7[] k zgz[] c[k spc[]][k zb7[]]]].'
    doc=abstract(candidate(source_composed()[0],query),ARITHMETIC|{'sky'});rows={}
    for label in ('baseline','reciprocal_unequal','negative_pair','nonsimultaneous','wrong_high_y','wrong_axis_coordinate','zero_length','zero_factor'):
        model,_,coords,_=rod_model(doc,label)
        for key,value in {'ja':'lr','jb':'hr','jc':'lm','jd':'hm'}.items():model[key]=lambda value=value:value
        actual=values(doc,model,DOMAIN)
        expected=[label in ('baseline','reciprocal_unequal','negative_pair'),label not in ('wrong_high_y','zero_factor')]
        if actual!=expected:raise ValueError('Endpoint algebra or simultaneity differs: '+label+repr(actual))
        rows[label]={'accepted':actual,'high_rest':list(map(str,coords['hr'])),'high_moving':list(map(str,coords['hm']))}
    return {'cases':rows,'signed_extent_not_automatically_positive_length':True,'rest_frame_simultaneity_required':True}


def measurement_checks():
    doc=abstract(candidate(source_composed()[0],'q[t[k sse[]][k zb6[]]].q[t[k ssg[]][k zb6[]]].'),ARITHMETIC|{'sky','shd'});rows={}
    for label in ('baseline','reciprocal_unequal','negative_pair','wrong_length_candidate','wrong_rod_endpoint','wrong_event_location','nonsimultaneous','not_rigid','not_transverse','wrong_motion_sign','wrong_units','zero_length'):
        model,_,_,_=rod_model(doc,label);actual=values(doc,model,DOMAIN)
        expected=[label in ('baseline','reciprocal_unequal','negative_pair','wrong_length_candidate'),label in ('baseline','reciprocal_unequal')]
        if actual!=expected:raise ValueError('Measured rod length differs: '+label+repr(actual))
        rows[label]=actual
    return {'cases':rows,'same_rod_endpoints_events_units_and_distance_checked':True,'coordinate_measurements_are_oracles':True}


def symmetry_checks():
    query='r ja[d] c.r jb[d] '+CUT+'.r jc[d] '+CUT+'.q[k ssc[p ja p jb p jc]].'
    doc=abstract(candidate(source_composed()[0],query),ARITHMETIC);rows={}
    for label in ('opposite_equal','opposite_unequal','same_sign_unequal','different_speeds_different_lengths','empty_scope','excluded_mismatch','zero_length','negative_length'):
        fixture=ConstructedCuts();c=fixture.make;model=guarded(doc);fixture.arithmetic(model)
        model.update(ja=lambda scene:False if label=='empty_scope' else scene=='motion' if label=='excluded_mismatch' else scene in ('motion','other'),
            jb=lambda scene:c(3 if scene=='motion' or label=='same_sign_unequal' else -4 if label=='different_speeds_different_lengths' else -3),
            jc=lambda scene:c(0 if label=='zero_length' else -6 if label=='negative_length' else 6 if scene=='motion' or label=='opposite_equal' else 7))
        actual=values(doc,model,('object',))[0]
        expected=label in ('opposite_equal','different_speeds_different_lengths','excluded_mismatch')
        if actual!=expected:raise ValueError('Speed magnitude symmetry differs: '+label)
        rows[label]=actual
    return {'cases':rows,'symmetry_is_relative_to_explicit_setting_scope':True,'physical_isotropy_not_derived':True}


def normalization_checks():
    query='r ja[] a.r jb[] a.q[t[k sro[]][k zb6[]]].q[t[k ssi[]][k zb6[]]].q[t[k ssk[]][k zb6[]]].q[t[k ssm[]][k zb6[]]].q[t[k ssl[]][k zb6[]]].q[k ssn[k ja[] k jb[]]].'
    doc=abstract(candidate(source_composed()[0],query),ARITHMETIC|{'sky'});rows={}
    for label in ('baseline','reciprocal_unequal','equal_not_reciprocal','negative_pair','wrong_units','not_transverse'):
        model,_,_,_=rod_model(doc,label);model.update(ja=lambda:'hr',jb=lambda:'hm')
        actual=values(doc,model,DOMAIN)
        expected={
            'baseline':[True]*6,'reciprocal_unequal':[True,False,False,False,False,False],
            'equal_not_reciprocal':[False,True,True,False,False,False],
            'negative_pair':[True,True,True,False,False,False],
            'wrong_units':[True,False,True,True,True,True],
            'not_transverse':[True,False,True,True,True,True]}[label]
        if actual!=expected:raise ValueError('Reciprocity, symmetry or positive branch differs: '+label+repr(actual))
        rows[label]=actual
    return {'cases':rows,'physical_symmetry_and_algebraic_conditions_separate':True,'unknown_function_definition_unchanged':True}


def inference_premise_checks():
    query=''.join('q[t[k '+symbol+'[]][k zb6[]]].' for symbol in ('ssh','ssq','ssr','sss','sst'))
    doc=abstract(candidate(source_composed()[0],query),ARITHMETIC|{'sky','shd'});rows={}
    for label in ('baseline','reciprocal_unequal','equal_not_reciprocal','negative_pair','nonsimultaneous','wrong_units','mixed_reverse_events'):
        model,_,_,_=rod_model(doc,label)
        if label=='mixed_reverse_events':model['zgx']=lambda scene:'e0'
        actual=values(doc,model,DOMAIN)
        expected={'baseline':[True]*4,'reciprocal_unequal':[True,False,False,False],
            'equal_not_reciprocal':[True,True,True,False]}.get(label,[False]*4)+[True]
        if actual!=expected:raise ValueError('Two physical measurement premises differ: '+label+repr(actual))
        rows[label]=actual
    return {'cases':rows,'both_motion_settings_use_same_rod_and_proper_length':True,'each_setting_has_its_own_events_and_places':True}


def attribution_checks():
    doc=parse(source_composed()[0]);doc['statements']=doc['statements'][-10:];rows={}
    for label in ('baseline','wrong_author','wrong_scope','wrong_context','wrong_function','wrong_setup','wrong_endpoints','wrong_length','wrong_symmetry','lost_clarity','wrong_equal_lengths','wrong_evenness','wrong_positive_premise','wrong_phi_one','wrong_final_rewrite'):
        model=guarded(doc)
        constants={'zhh':'question','zhi':'setup','zhj':'endpoints','zhk':'length','zhl':'symmetry','zhm':'equal','zhn':'even','zhq':'positive','zho':'one','zhp':'final','rd':'author','rh':'scope','ri':'text'}
        for key,value in constants.items():model[key]=lambda value=value:value
        sym=lambda d:json.loads(d.syntax)['symbol']
        common=lambda a,s,c:(a,s,c)==('other' if label=='wrong_author' else 'author','other' if label=='wrong_scope' else 'scope','other' if label=='wrong_context' else 'text')
        model.update(zhg=lambda node,a,f,s,c:common(a,s,c) and (node,sym(f))==('question','zeq' if label=='wrong_function' else 'spc'),
            ug=lambda node,a,d,s,c:common(a,s,c) and (node,sym(d))==('setup','ssf' if label=='wrong_setup' else 'sse'),
            zhf=lambda node,a,f,d,s,c:common(a,s,c) and (node,sym(f),sym(d))==('length','spc','ssf' if label=='wrong_length' else 'ssg'),
            uh=lambda node,a,d,s,c:common(a,s,c) and (node,sym(d))==('symmetry','ssk' if label=='wrong_symmetry' else 'ssi'),
            zdg=lambda node,a,d,s,c:common(a,s,c) and (node,sym(d))==('symmetry','ssk' if label=='lost_clarity' else 'ssi'),
            zfl=lambda node,a,p,d,s,c:common(a,s,c) and (node,sym(p),sym(d))==('positive','ssk' if label=='wrong_positive_premise' else 'sss','ssm'),
            zd3=lambda node,a,p,b,e,s,c:common(a,s,c) and (node,sym(p),sym(b),sym(e)) in {
                ('final','ssp','spk','spk' if label=='wrong_final_rewrite' else 'sso'),
                ('even','ssh','ssj','ssl' if label=='wrong_evenness' else 'ssk')})
        triples={('endpoints','sse','ssg' if label=='wrong_endpoints' else 'ssf'),('equal','ssq','ssk' if label=='wrong_equal_lengths' else 'ssj'),
            ('one','ssm','ssk' if label=='wrong_phi_one' else 'ssl')}
        model['zc']=lambda node,a,p,d,s,c:common(a,s,c) and (node,sym(p),sym(d)) in triples
        actual=values(doc,model,tuple(v for k,v in constants.items() if k!='ri'))
        bads=({'wrong_function'},{'wrong_setup'},{'wrong_endpoints'},{'wrong_length'},{'wrong_symmetry','lost_clarity'},{'wrong_equal_lengths'},{'wrong_evenness'},{'wrong_positive_premise'},{'wrong_phi_one'},{'wrong_final_rewrite'})
        expected=[label not in {'wrong_author','wrong_scope','wrong_context'}|bad for bad in bads]
        if actual!=expected:raise ValueError('Rod normalization attribution differs: '+label)
        rows[label]=actual
    return rows


def alignment():
    path=ROOT/'artifacts/written-units-v1/einstein-1905.json';artifact=json.loads(path.read_text(encoding='utf-8'))
    inventory=json.loads((ROOT/'reports/written-units-v1.json').read_text(encoding='utf-8'))
    if hashlib.sha256(path.read_bytes()).hexdigest()!=inventory['works']['einstein-1905']['units_sha256']:raise ValueError('Pinned source differs')
    definitions=[['srw','srz','ssa','sse'],['sry','ssf'],['ssf'],['sry','ssf'],['ssb','ssc','ssd','ssg','ssi'],['ssh','ssj'],['ssr','sst'],['ssk','sst'],['sro','ssm','ssl','sss'],['ssn','sso','ssp'],['spq'],['soy','soz','spa','spq']];rows=[]
    for index,defs in enumerate(definitions,97):
        uid=f'einstein-1905:u{index:04}';unit=next(u for u in artifact['units'] if u['id']==uid);digest=unit['text_sha256']
        if hashlib.sha256(unit['text'].encode('utf-8')).hexdigest()!=digest:raise ValueError('Rod source changed')
        rows.append({'unit':uid,'unit_sha256':digest,'start':0,'end':len(unit['text']),'source':unit['text'],'definitions':defs,'status':'partial_explicit_reading','full_semantic_equivalence':False})
        for mid in unit['math_ids']:
            item=next(m for m in artifact['math'] if m['id']==mid)
            if hashlib.sha256(item['mathml'].encode('utf-8')).hexdigest()!=item['sha256']:raise ValueError('Rod source math changed')
            rows.append({'unit':uid,'unit_sha256':digest,'math_id':mid,'math_sha256':item['sha256'],'definitions':defs,'status':'partial','full_semantic_equivalence':False})
    return {'segments':rows,'facsimile_checked':False,'verified_full_units':0,'positive_branch_is_explicit_interpretation':True,'whole_material_segment_not_yet_defined':True}


def build_report():
    documents={}
    for compose in (generic_composed,source_composed):
        text,basis=compose();doc=parse(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text:raise ValueError('Stored rod scale document differs')
        if json.loads((ROOT/('data/'+basis['document'].split('/')[-1].replace('.noema','-basis-v1.json'))).read_text(encoding='utf-8'))!=basis:raise ValueError('Stored rod scale basis differs')
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Rod scale roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis)
    paths=[*documents,'data/transverse-rod-scale-basis-v1.json','data/einstein-transverse-rod-scale-basis-v1.json',
        'examples/v014/reverse-transform.noema','examples/v014/einstein-reverse-transform.noema',
        'scripts/compose_transverse_rod_scale.py','scripts/check_transverse_rod_scale.py','scripts/check_tau_differential.py','scripts/check_transverse_time.py',
        'reports/written-units-v1.json','artifacts/written-units-v1/einstein-1905.json',
        'noema/discourse.py','noema/finite_semantics.py','noema/polynomial_proofs.py']
    text=source_composed()[0];previous=(ROOT/'examples/v014/einstein-reverse-transform.noema').read_text(encoding='utf-8')
    return {'status':'partial_transverse_rod_and_phi_normalization','documents':documents,
        'polynomial_lemmas':polynomial_checks(),'endpoints':endpoint_checks(),'measurements':measurement_checks(),'symmetry':symmetry_checks(),
        'normalization':normalization_checks(),'inference_premises':inference_premise_checks(),'attribution':attribution_checks(),'alignment':alignment(),'roundtrips':True,
        'verified_full_units':{'einstein-1905':0,'kant-1784':0},
        'notation_size':{'canonical_source_document_characters':len(text),'added_characters':len(text)-len(previous)},
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args();report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Rod scale report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Transverse endpoints, physical lengths, symmetry and positive scale checked')


if __name__=='__main__':main()
