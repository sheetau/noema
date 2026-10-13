"""Check shared profiles, component mixing and the limits of finite checking."""
import argparse
from fractions import Fraction as F
import hashlib
from itertools import product
import json

from noema.extraction import extract_document
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.polynomial_proofs import verify_universal
from noema.script import encode, decode
from scripts.check_comoving_labels import values
from scripts.check_coordinate_correspondence import abstract
from scripts.check_described_appraisals import candidate
from scripts.check_rod_setup import guarded, callbacks
from scripts.check_field_equations import AXES, DOMAIN, ARITHMETIC
from scripts.check_tau_differential import ConstructedCuts
from scripts.check_angle_composition import model_arithmetic
from scripts.check_parallel_composition import transform
from scripts.check_real_products import MEANINGS as OPS_MEANINGS, assertion
from scripts.check_moving_light_trip import literal
from scripts.compose_limits import call as k, app, op, v
from scripts.compose_plane_waveforms import ROOT, PARENT, CUT, PROFILE, ROLES, AMPLITUDES, source_composed, core_composed

REPORT=ROOT/'reports/plane-waveforms-v1.json'
OPS=ARITHMETIC|{'sky','sjt','be'}


def setup(doc):
    fixture=ConstructedCuts();model=guarded(doc);model_arithmetic(fixture,model)
    # All registered values are rational embeddings, without a magnitude cap.
    model['ba']=lambda x: isinstance(fixture.read(x),F)
    model['be']=lambda x:fixture.make(-fixture.read(x))
    model['szi']=lambda condition,left,right:left if condition else right
    for symbol,axis in zip(ROLES,AXES):model[symbol]=lambda axis=axis:axis
    return fixture,model


def evaluate(doc,model):
    names={d['name'] for d in doc['declarations'] if d['kind']=='primitive'}
    return values(doc,{name:value for name,value in model.items() if name in names},DOMAIN)


def polynomial_checks(text):
    doc=extract_document(parse(text),roots=['s6b','s6c'],statement_indices=[]).document
    base=format_graph(doc,'compact');beta,ratio,own,cross,wave=map(v,('beta','ratio','own','cross','wave'))
    mul=lambda a,b:k('ad',a,b)
    claims={}
    for name in ('s6b','s6c'):
        claims[name+'_commutes_with_shared_profile']=assertion('beta ratio own cross wave',op('e',
            k(name,beta,ratio,mul(own,wave),mul(cross,wave)),mul(k(name,beta,ratio,own,cross),wave)))
    claims['different_profiles_are_not_interchangeable']=assertion('',op('e',
        k('s6b',literal(1),literal(1),literal(2),literal(6)),literal(0)))
    rows={}
    for name,claim in claims.items():
        result=verify_universal(parse(base+claim),{n:OPS_MEANINGS[n] for n in ('ab','ac','ad')},timeout_ms=20000)[0]
        if result['status']!=('invalid' if name.startswith('different') else 'valid'):raise ValueError('Profile factoring differs: '+name)
        rows[name]=result
    return {'claims':rows,'rational_algebra_only':True,'real_cut_field_laws_proved':False}


SCALARS=tuple('j'+n for n in 'bcdefghijklmnopqrstuvwx')
INPUTS=SCALARS[:12] # V, v, w, a,b,c, Ex,Ey,Ez,Hx,Hy,Hz
COORDS=SCALARS[12:16]
EXPECTED=SCALARS[16:22]
DECLS='r ja[] '+PROFILE+'.'+''.join('r '+n+'[] '+CUT+'.' for n in SCALARS)


def wave_queries():
    V,s,w,a,b,c,*amplitudes=map(k,INPUTS)
    old=[k('sdx2',k('ja'),V,w,a,b,c,*part) for part in (amplitudes[:3],amplitudes[3:])]
    explicit=[k(name,k('ja'),V,s,w,a,b,c,*amplitudes) for name in ('sd22','sd23')]
    mixed=[k(name,V,s,*old) for name in ('s6k','s6l')]
    point=list(map(k,COORDS));query=''
    for left,right in zip(explicit,mixed):
        for role in ROLES[:3]:query+='q['+k('sca',app(app(left,k(role)),*point),app(app(right,k(role)),*point))+'].'
    for field,outputs in zip(explicit,(EXPECTED[:3],EXPECTED[3:])):
        for role,value in zip(ROLES[:3],outputs):query+='q['+k('sca',app(app(field,k(role)),*point),k(value))+'].'
    return query


def expected_values(inputs,point,profile,mode='baseline'):
    V,s,w,a,b,c,*amplitudes=map(F,inputs)
    old=transform(point, -s if mode!='forward_coordinates' else s,V)
    if mode=='unchanged_coordinates':old=point
    phase=w*(old[3]-sum(d*x for d,x in zip((a,b,c),old[:3]))/V)
    if mode=='wrong_phase':phase+=1
    value=profile(phase)
    ex,ey,ez,hx,hy,hz=amplitudes
    beta=transform((0,0,0,1),s,V)[3];r=s/V
    result=[ex,beta*(ey-r*hz),beta*(ez+r*hy),hx,beta*(hy+r*ez),beta*(hz-r*ey)]
    if mode=='unmixed_amplitudes':result=amplitudes
    for label,index,val in (('wrong_ey_sign',1,beta*(ey+r*hz)),('wrong_ez_sign',2,beta*(ez-r*hy)),
                           ('wrong_hy_sign',4,beta*(hy-r*ez)),('wrong_hz_sign',5,beta*(hz+r*ey))):
        if mode==label:result[index]=val
    return [x*value for x in result]


def waveform_checks(texts):
    docs=[abstract(candidate(text,DECLS+wave_queries()),OPS) for text in texts]
    profiles={'linear':lambda q:q,'quadratic':lambda q:q*q+q+1,'constant':lambda q:F(2)}
    directions=((1,0,0),(0,1,0),(F(3,5),F(4,5),0),(F(1,3),F(2,3),F(2,3)))
    point=(F(1),F(2),F(-1),F(1,2));amps=(2,3,-1,4,-2,5)
    cases=[]
    for speed,direction,pname in product((-3,0,3),directions,profiles):
        cases.append((f'valid_{len(cases)}',(5,speed,2,*direction,*amps),profiles[pname],'baseline'))
    for mode in ('forward_coordinates','unchanged_coordinates','wrong_phase','unmixed_amplitudes',
                 'wrong_ey_sign','wrong_ez_sign','wrong_hy_sign','wrong_hz_sign'):
        cases.append((mode,(5,3,2,F(3,5),F(4,5),0,*amps),profiles['quadratic'],mode))
    rows={}
    for name,inputs,profile,mode in cases:
        expected=expected_values(inputs,point,profile,mode)
        results=[]
        for doc in docs:
            fixture,model=setup(doc)
            callbacks(doc,model,{'ja':lambda x:fixture.make(profile(fixture.read(x)))})
            for symbol,value in zip(SCALARS,(*inputs,*point,*expected)):model[symbol]=lambda value=value:fixture.make(value)
            result=evaluate(doc,model)
            if result[:6]!=[True]*6 or all(result[6:])!=(mode=='baseline'):raise ValueError('Plane waveform differs: '+name+repr(result))
            results.append(result)
        if results[0]!=results[1]:raise ValueError('Standalone waveform differs')
        rows[name]=results[0]
    return {'cases':rows,'cumulative_and_standalone_agree':True,
        'shared_profile_and_inverse_coordinate_map_checked':True,
        'profiles_are_exact_rational_functions_not_claimed_sine':True,
        'general_real_function_identity_proved':False}


def harmonic_checks(text):
    decls='r ja[] '+PROFILE+'.r jb[] '+PROFILE+'.r jc[] '+CUT+'.'
    queries='q[k sdu2[k ja[] k jb[]]].q[k sdt2[k ja[] k jb[] k jc[]]].'
    doc=abstract(candidate(text,decls+queries),OPS|{'sjs'})
    # Exact polynomial functions and their supplied analytical derivatives.
    # Passing at one point does not certify the all-real oscillator condition.
    cases={
        'correct_initial_jet':((0,1),(1,),0,[True,True]),
        'linear_pair_fails_away_from_origin':((0,1),(1,),1,[True,False]),
        'scaled_jet_wrong_normalization':((0,2),(2,),0,[False,True]),
        'shifted_profile_wrong_origin':((1,1),(1,),0,[False,False]),
        'wrong_cosine_sign':((0,1),(-1,),0,[False,False]),
        'wrong_sine_slope':((0,2),(1,),0,[True,False]),
        'wrong_cosine_slope':((0,1),(1,1),0,[True,False]),
    };rows={}
    for name,(S,C,point,expected) in cases.items():
        fixture,model=setup(doc);registry={}
        def polynomial(coeffs):
            def function(x):return fixture.make(sum(a*fixture.read(x)**i for i,a in enumerate(coeffs)))
            registry[function]=coeffs
            return function
        callbacks(doc,model,{'ja':polynomial(S),'jb':polynomial(C)});model['jc']=lambda:fixture.make(point)
        def unwrap(function):
            while function.implementation not in registry:
                impl=function.implementation
                free=dict(zip(impl.__code__.co_freevars,(cell.cell_contents for cell in impl.__closure__ or ())))
                function=free.get('raw')
                if function is None:raise ValueError('Unregistered polynomial derivative requested')
            return registry[function.implementation]
        def derivative(domain,function,where,result):
            coeffs=unwrap(function);p=fixture.read(where)
            return domain(where) and fixture.read(result)==sum(i*a*p**(i-1) for i,a in enumerate(coeffs) if i)
        model['sjs']=derivative
        result=evaluate(doc,model)
        if result!=expected:raise ValueError('Harmonic local condition differs: '+name+repr(result))
        rows[name]=result
    # Even with exact registered arithmetic, all-real quantification is refused.
    refusals={}
    for name,query,abstracted in (
        ('global','q[k sdv2[k ja[] k jb[]]].',OPS),
        ('raw_derivative','q[k sdt2[k ja[] k jb[] k jc[]]].',OPS)):
        raw=abstract(candidate(text,decls+query),abstracted);fixture,model=setup(raw)
        callbacks(raw,model,{'ja':lambda x:x,'jb':lambda x:fixture.make(1)})
        model['jc']=lambda:fixture.make(0)
        try:evaluate(raw,model)
        except ValueError as exc:
            if 'Cannot finitely quantify the rational number domain' not in str(exc):raise
            refusals[name]=str(exc)
        else:raise ValueError('All-real calculus certified by finite sampling')
    return {'cases':rows,'refusals':refusals,'local_derivative_oracle_only':True,
            'sine_existence_and_uniqueness_proved':False}


def domain_checks(text):
    query='q['+k('sdy2',*map(k,INPUTS))+'].'
    doc=abstract(candidate(text,DECLS+query),OPS);rows={}
    base=list(map(F,(5,3,2,0,1,0,2,3,-1,4,-2,5)))
    cases={'valid':base}
    for name,index,value in (('zero_light',0,0),('negative_light',0,-5),('light_speed',1,5),
            ('superluminal',1,6),('zero_rate',2,0),('negative_rate',2,-2),('nonunit',3,1)):
        args=base.copy();args[index]=F(value);cases[name]=args
    for name,args in cases.items():
        fixture,model=setup(doc)
        for symbol,value in zip(INPUTS,args):model[symbol]=lambda value=value:fixture.make(value)
        result=evaluate(doc,model)
        if result!=[name=='valid']:raise ValueError('Wave domain differs: '+name)
        rows[name]=result
    return rows


def amplitude_checks(text):
    names=tuple('j'+n for n in 'abcdefghijklmn')
    declarations=''.join('r '+n+'[] '+CUT+'.' for n in names)
    doc=abstract(candidate(text,declarations+'q['+k('sdz2',*map(k,names))+'].'),OPS)
    rows={}
    for speed in (-3,0,3):
        inputs=(5,speed,2,3,-1,4,-2,5)
        expected=expected_values((5,speed,2,0,1,0,*inputs[2:]),(0,0,0,0),lambda phase:F(1))
        for component in (-1,0,1,2,3,4,5):
            outputs=expected.copy()
            if component>=0:outputs[component]+=1
            fixture,model=setup(doc)
            for symbol,value in zip(names,(*inputs,*outputs)):model[symbol]=lambda value=value:fixture.make(value)
            result=evaluate(doc,model)
            if result!=[component==-1]:raise ValueError('Amplitude relation differs')
            rows[f'{speed}:{component}']=result
    return rows


def alignment():
    path=ROOT/'artifacts/written-units-v1/einstein-1905.json';source=json.loads(path.read_text(encoding='utf-8'))
    inventory=json.loads((ROOT/'reports/written-units-v1.json').read_text(encoding='utf-8'))
    if hashlib.sha256(path.read_bytes()).hexdigest()!=inventory['works']['einstein-1905']['units_sha256']:raise ValueError('Snapshot differs')
    rows=[]
    for math_id,names in {'M0320':['sdv2','sdx2','sd24'],'M0325':['sdz2','sd22','sd23']}.items():
        item=next(m for m in source['math'] if m['id']==math_id);unit=next(u for u in source['units'] if math_id in u['math_ids'])
        if hashlib.sha256(item['mathml'].encode('utf-8')).hexdigest()!=item['sha256']:raise ValueError('MathML differs')
        rows.append({'unit':unit['id'],'unit_sha256':unit['text_sha256'],'math_id':math_id,'math_sha256':item['sha256'],
            'definitions':names,'status':'partial','review_ja':'正弦を初期値問題で指定し、同じ位相を六成分で共有する波形の部分対応。全域の存在・一意性の機械的証明、光源・観測者・遠方近似・物理的な測定との対応は未完。'})
    return {'segments':rows,'semantic_completion':False,'new_source_ranges':False}


def build_report():
    documents={};sizes={};texts=[]
    for builder,stem in ((source_composed,'einstein-plane-waveforms'),(core_composed,'plane-waveforms-core')):
        text,basis=builder();doc=parse(text);texts.append(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text or json.loads((ROOT/('data/'+stem+'-basis-v1.json')).read_text(encoding='utf-8'))!=basis:raise ValueError('Stored waveforms differ')
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Waveform roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis)
        sizes[stem]={'characters':len(text),'statements':len(doc['statements'])}
    source=parse(texts[0]);parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    if source['declarations'][:len(parent['declarations'])]!=parent['declarations'] or source['statements']!=parent['statements']:raise ValueError('Parent changed')
    paths=[*documents,PARENT,'data/einstein-plane-waveforms-basis-v1.json','data/plane-waveforms-core-basis-v1.json',
        'scripts/compose_plane_waveforms.py','scripts/check_plane_waveforms.py','scripts/check_tau_differential.py',
        'scripts/check_angle_composition.py','scripts/check_transverse_time.py','scripts/check_parallel_composition.py',
        'noema/extraction.py','noema/polynomial_proofs.py','noema/finite_semantics.py','noema/discourse.py',
        'artifacts/written-units-v1/einstein-1905.json','reports/written-units-v1.json']
    return json.loads(json.dumps({'status':'partial_harmonic_profile_and_plane_field_transform',
        'documents':documents,'sizes':sizes,'polynomial':polynomial_checks(texts[0]),'waveforms':waveform_checks(texts),
        'harmonic':harmonic_checks(texts[1]),'domains':domain_checks(texts[1]),'amplitudes':amplitude_checks(texts[1]),'alignment':alignment(),
        'parent_preserved':True,'roundtrips':True,'new_primitives':0,'new_author_statements':0,
        'verified_full_units':{'kant-1784':0,'einstein-1905':0},
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}},ensure_ascii=False))


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');args=cli.parse_args()
    report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Plane waveform report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Shared waveforms, six amplitudes, inverse coordinates and harmonic conditions checked')


if __name__=='__main__':main()
