"""Check origin-clock placement, hypothetical calibration and rate answers."""
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
from scripts.check_tau_differential import ARITHMETIC, ConstructedCuts
from scripts.check_transverse_time import square_root
from scripts.check_real_products import MEANINGS, call as k, op, assertion, conjunction as both
from scripts.check_moving_light_trip import literal
from scripts.compose_origin_clock import ROOT, CUT, generic_composed, source_composed

REPORT=ROOT/'reports/origin-clock-v1.json'


def polynomial_checks():
    V,s,b,f,t,tau,t2,tau2,scale,offset,read,read2=map(lambda n:'v '+n,
        'light speed beta factor time proper last lastproper scale offset reading lastreading'.split())
    zero=literal(0);one=literal(1);mul=lambda a,b:k('ad',a,b)
    sub=lambda a,b:k('ab',a,k('ac',b));eq=lambda a,b:op('e',a,b)
    origin=k('suw',V,s,b,t,tau);factor=k('stt',V,s,f)
    pair=both(origin,k('suw',V,s,b,t2,tau2),factor)
    claims={
        'origin_time_is_contraction_factor_times_observer_time':assertion('light speed beta factor time proper',op('y',both(origin,factor),eq(tau,mul(f,t)))),
        'time_and_difference_rewrite_are_equal':assertion('factor time',eq(mul(f,t),sub(t,mul(sub(one,f),t)))) ,
        'all_origin_pairs_have_same_rate':assertion('light speed beta factor time proper last lastproper',op('y',pair,eq(sub(tau2,tau),mul(f,sub(t2,t))))),
        'positive_observer_duration_gives_positive_proper_duration':assertion('light speed beta factor time proper last lastproper',op('y',both(pair,k('aa',t,t2)),k('aa',tau,tau2))),
        'common_dial_offset_cancels_in_differences':assertion('scale offset time proper reading lastreading',op('y',both(k('sux',scale,offset,t,read),k('sux',scale,offset,tau,read2)),eq(sub(read2,read),mul(scale,sub(tau,t))))),
        'positive_duration_identifies_rate':assertion('factor other duration',op('y',both(k('aa',zero,'v duration'),eq(mul(f,'v duration'),mul('v other','v duration'))),eq(f,'v other'))),
        'negative_coordinate_time_is_allowed':assertion('',k('suw',literal(5),literal(3),literal(Fraction(5,4)),literal(-5),literal(-4))),
        'zero_speed_preserves_origin_time':assertion('light time',op('y',k('aa',zero,V),k('suw',V,zero,one,t,t))),
        'one_zero_event_identifies_rate':assertion('',op('y',eq(mul(literal(Fraction(4,5)),zero),mul(one,zero)),eq(literal(Fraction(4,5)),one))),
        'different_dial_offsets_cancel':assertion('',op('y',both(k('sux',one,zero,zero,zero),k('sux',one,one,literal(4),literal(5))),eq(sub(literal(5),zero),literal(4)))),
        'changing_dial_scale_preserves_rate':assertion('',op('y',both(k('sux',literal(2),zero,zero,zero),k('sux',literal(2),zero,literal(4),literal(8))),eq(literal(8),literal(4)))),
        'origin_rate_is_beta_instead_of_its_inverse':assertion('',eq(literal(Fraction(5,4)),literal(Fraction(4,5)))),
    }
    invalid={'one_zero_event_identifies_rate','different_dial_offsets_cancel','changing_dial_scale_preserves_rate','origin_rate_is_beta_instead_of_its_inverse'}
    rows={}
    for name,claim in claims.items():
        result=verify_universal(parse(generic_composed()[0]+claim),MEANINGS,timeout_ms=15000)[0]
        if result['status']!=('invalid' if name in invalid else 'valid'):raise ValueError('Origin clock algebra differs: '+name+repr(result))
        rows[name]=result
    return {'claims':rows,'rational_lemmas_only':True,'signed_coordinate_time_not_elapsed_duration':True}


EVENTS=('e0','e1','e2','a0','a1','b0','b1')
READS=('r0','r1','r2','ar0','ar1','br0','br1')
COORDS=('K0','K1','K2','k0','k1','k2','A0','A1','B0','B1')
DOMAIN=EVENTS+READS+COORDS+('clock','otherclock','rest','moving','origin','restplace','otherplace','time','length','x','y','z','t')


def clock_model(doc,label='baseline'):
    fixture=ConstructedCuts();c=fixture.make;n=fixture.read;model=guarded(doc);fixture.arithmetic(model)
    model['ba']=lambda value:isinstance(n(value),Fraction)
    speed=0 if label=='stationary' else -3 if label=='negative_velocity' else 3
    factor=Fraction(1) if speed==0 else Fraction(4,5);beta=1/factor
    times=[0,5,10] if label!='no_time_width' else [0,0,0]
    if label=='negative_times':times=[-10,-5,0]
    coords={};charts={};dial={};record_event=dict(zip(READS,EVENTS))
    selections={'motion':set(READS[:3]),'text':set(READS[3:5]),'other':set(READS[5:])}
    for index,t in enumerate(times):
        x=speed*t;proper=factor*t
        if label=='different_linear_rate':proper=Fraction(t,2)
        if label=='off_origin':x+=Fraction(4,5);proper=beta*(t-Fraction(speed,25)*x)
        if label=='wrong_position' and index==1:x+=1
        if label=='nonlinear_clock' and index==2:proper+=1
        coords['K'+str(index)]=[x,0,0,t];coords['k'+str(index)]=[1 if label=='off_origin' else 0,0,0,proper]
        event='e'+str(index);charts[(event,'rest','motion')]='K'+str(index);charts[(event,'moving','motion')]='k'+str(index)
        dial[event]=proper+(7 if label=='dial_offset' else 0)
    for letter,context,system,prefix in (('a','text','rest','A'),('b','other','moving','B')):
        for index in range(2):
            event=letter+str(index);coords[prefix+str(index)]=[0,0,0,index*5]
            charts[(event,system,context)]=prefix+str(index);dial[event]=index*5
    if label=='empty_actual':selections['motion']=set()
    if label=='one_event':selections['motion']={'r0'}
    place=lambda event:'restplace' if event.startswith('a') else 'origin'
    for symbol,value in {'zie':'clock','ra':'rest','zbm':'moving','rb':'time','ta':'length','yn':'x','yo':'y','yp':'z','zc7':'t','zb6':'motion'}.items():model[symbol]=lambda value=value:value
    model.update(tc=lambda:c(5),zb7=lambda:c(speed),sky=lambda value:square_root(fixture,value),
        ca=lambda obj:obj=='clock',ci=lambda unit:unit=='time',
        x4=lambda obj,frame,context:obj=='clock' and (frame,context) in {('moving','motion'),('rest','text'),('moving','other')} and not(label=='not_stationary' and context=='motion'),
        zid=lambda obj,frame,actual,trial:obj=='clock' and actual=='motion' and (frame,trial) in {('rest','text'),('moving','other')} and not(label=='rest_setup_unavailable' and frame=='rest') and not(label=='moving_setup_unavailable' and frame=='moving'),
        zai=lambda obj,frame,context:obj=='clock' and (frame,context) in {('moving','motion'),('rest','text'),('moving','other')} and not(label=='incomplete_records' and context=='motion'),
        zac=lambda record,obj,context:obj=='clock' and record in selections.get(context,set()),
        zad=lambda record:record_event.get(record,'e0'),zae=lambda record:place(record_event.get(record,'e0')),
        zag=lambda record:c(dial.get(record_event.get(record,'e0'),0)),
        zc4=lambda event:event in EVENTS,
        zc5=lambda record:record in coords,
        zc6=lambda record,axis:c(coords.get(record,[0]*4)[('x','y','z','t').index(axis)] if axis in ('x','y','z','t') else 0),
        zdz=lambda event,frame,context:'K0' if label=='wrong_candidate_record' and (event,frame,context)==('e1','rest','motion') else charts.get((event,frame,context),'K0'),
        shd=lambda event,record,frame,context:charts.get((event,frame,context))==record and not(label=='missing_observer_chart' and (event,frame)==('e1','rest')),
        zbn=lambda frame,context:'otherplace' if label=='wrong_origin' else 'origin',
        zbv=lambda frame,origin,context:(frame,origin,context)==('moving','origin','motion'),
        cb=lambda obj,p,frame:(obj=='clock' and (p,frame)==('origin','moving')) or (obj in EVENTS and p==place(obj) and ((obj.startswith('a') and frame=='rest') or (not obj.startswith('a') and frame=='moving'))),
        zab=lambda obj,event,p,frame,context:obj=='clock' and p==place(event) and (event,frame,context) in charts and not(label=='wrong_clock_place' and event=='e1'),
        ce=lambda obj,event,frame,unit,value:obj==('otherclock' if label=='replaced_clock' and event=='e1' else 'clock') and unit==('length' if label=='wrong_unit' and event=='e1' else 'time') and event in dial and n(value)==dial[event] and ((event.startswith('a') and frame=='rest') or (not event.startswith('a') and frame=='moving')) and not(label=='missing_reading' and event=='e1'))
    return model,fixture,coords


def placement_checks():
    query='q[k suz[k zie[] k zb6[]]].q[k svb[k zie[] k zb6[]]].q[t[k sve[]][k zb6[]]].q[t[k svh[]][k zb6[]]].q[t[k svk[]][k zb6[]]].'
    doc=abstract(candidate(source_composed()[0],query),ARITHMETIC|{'sky','shd'});rows={}
    labels=('baseline','stationary','negative_velocity','negative_times','rest_setup_unavailable','moving_setup_unavailable',
        'not_stationary','incomplete_records','missing_observer_chart','wrong_candidate_record','wrong_origin','wrong_clock_place',
        'missing_reading','replaced_clock','wrong_unit','dial_offset','off_origin','wrong_position','nonlinear_clock','different_linear_rate','empty_actual','one_event','no_time_width')
    for label in labels:
        model,_,_=clock_model(doc,label);actual=values(doc,model,DOMAIN)
        capability=label not in ('rest_setup_unavailable','moving_setup_unavailable')
        placed=label not in ('not_stationary','incomplete_records','missing_observer_chart','wrong_candidate_record','wrong_origin','wrong_clock_place','missing_reading','replaced_clock','wrong_unit','dial_offset','off_origin','empty_actual')
        equation=label not in ('wrong_candidate_record','off_origin','wrong_position','nonlinear_clock','different_linear_rate','empty_actual')
        derived=label not in ('wrong_candidate_record','off_origin','nonlinear_clock','different_linear_rate','empty_actual')
        expected=[capability,placed,capability and placed,equation,derived]
        if actual!=expected:raise ValueError('Clock placement or equation differs: '+label+repr(actual))
        rows[label]=actual
    return {'cases':rows,'alternative_settings_not_simultaneous_rest':True,'calibration_and_equations_checked_separately':True,
        'complete_reading_scope_and_physical_charts_are_oracles':True}


def answer_checks():
    query='r ja[] '+CUT+'.q[k svc[k zie[] k ja[] k zb6[]]].q[h[k svd[]][k ja[]]].'
    doc=abstract(candidate(source_composed()[0],query),ARITHMETIC|{'sky','shd'});rows={}
    for label,rate,expected in (
        ('baseline',Fraction(4,5),True),('wrong_answer',Fraction(5,4),False),('unit_answer',1,False),
        ('stationary',1,True),('negative_velocity',Fraction(4,5),True),('negative_times',Fraction(4,5),True),
        ('one_event',Fraction(4,5),False),('no_time_width',Fraction(4,5),False),('nonlinear_clock',Fraction(4,5),False),
        ('dial_offset',Fraction(4,5),False),('missing_observer_chart',Fraction(4,5),False),('rest_setup_unavailable',Fraction(4,5),True),
        ('different_linear_rate',Fraction(1,2),True)):
        model,fixture,_=clock_model(doc,label);model['ja']=lambda:fixture.make(rate);actual=values(doc,model,DOMAIN)
        if actual!=[expected]*2:raise ValueError('Clock rate answer differs: '+label+repr(actual))
        rows[label]={'rate':str(rate),'accepted':actual}
    return {'cases':rows,'typed_question_checks_actual_rate_predicate':True,'positive_time_width_required':True,'expected_answer_not_inserted_in_question':True}


def frame_checks():
    query='q[k suz[k zie[] k zb6[]]].q[k svb[k zie[] k zb6[]]].q[k x4[k zie[] k ra[] k zb6[]]].'
    doc=abstract(candidate(source_composed()[0],query),ARITHMETIC|{'sky','shd'});rows={}
    for label in ('baseline','collapsed_frames'):
        model,_,_=clock_model(doc)
        if label=='collapsed_frames':model['ra']=lambda:'moving'
        actual=values(doc,model,DOMAIN)
        if actual!=([True,True,False] if label=='baseline' else [False,False,True]):raise ValueError('Distinct frame clock setup differs')
        rows[label]=actual
    return rows


def attribution_checks():
    doc=parse(source_composed()[0]);doc['statements']=doc['statements'][-5:];rows={}
    for label in ('baseline','wrong_author','wrong_scope','wrong_context','wrong_setup','wrong_question','wrong_equations','wrong_clear','wrong_derived'):
        model=guarded(doc);constants={'zif':'setup','zig':'question','zii':'equations','zij':'derived','rd':'author','rh':'scope','ri':'text'}
        for name,value in constants.items():model[name]=lambda value=value:value
        sym=lambda d:json.loads(d.syntax)['symbol']
        common=lambda a,s,c:(a,s,c)==('other' if label=='wrong_author' else 'author','other' if label=='wrong_scope' else 'scope','other' if label=='wrong_context' else 'text')
        model.update(ug=lambda node,a,d,s,c:common(a,s,c) and (node,sym(d))==('setup','svh' if label=='wrong_setup' else 'sve'),
            zih=lambda node,a,d,s,c:common(a,s,c) and (node,sym(d))==('question','sip' if label=='wrong_question' else 'svd'),
            zdg=lambda node,a,d,s,c:common(a,s,c) and (node,sym(d))==('equations','svk' if label=='wrong_clear' else 'svh'))
        triples={('equations','svi','svk' if label=='wrong_equations' else 'svh'),('derived','svl','svh' if label=='wrong_derived' else 'svk')}
        model['zc']=lambda node,a,p,d,s,c:common(a,s,c) and (node,sym(p),sym(d)) in triples
        actual=values(doc,model,tuple(v for k,v in constants.items() if k!='ri'))
        expected=[label not in ('wrong_author','wrong_scope','wrong_context',bad) for bad in ('wrong_setup','wrong_question','wrong_equations','wrong_clear','wrong_derived')]
        if actual!=expected:raise ValueError('Clock attribution differs: '+label)
        rows[label]=actual
    return rows


def alignment():
    path=ROOT/'artifacts/written-units-v1/einstein-1905.json';artifact=json.loads(path.read_text(encoding='utf-8'))
    inventory=json.loads((ROOT/'reports/written-units-v1.json').read_text(encoding='utf-8'))
    if hashlib.sha256(path.read_bytes()).hexdigest()!=inventory['works']['einstein-1905']['units_sha256']:raise ValueError('Pinned clock source differs')
    rows=[]
    defs=[['suy','suz','svb','svc','svd','sve'],['svf','svg','svh'],['svf'],['svh'],['svg'],['svl','svk'],['svj','svk']]
    for index,names in enumerate(defs,118):
        unit=next(u for u in artifact['units'] if u['id']==f'einstein-1905:u{index:04}')
        if hashlib.sha256(unit['text'].encode('utf-8')).hexdigest()!=unit['text_sha256']:raise ValueError('Clock unit differs')
        rows.append(dict(unit=unit['id'],unit_sha256=unit['text_sha256'],start=0,end=len(unit['text']),source=unit['text'],definitions=names,status='partial_explicit_reading',full_semantic_equivalence=False))
        for mid in unit['math_ids']:
            item=next(m for m in artifact['math'] if m['id']==mid)
            if hashlib.sha256(item['mathml'].encode('utf-8')).hexdigest()!=item['sha256']:raise ValueError('Clock math differs')
            rows.append(dict(unit=unit['id'],unit_sha256=unit['text_sha256'],math_id=mid,math_sha256=item['sha256'],definitions=names,status='partial',full_semantic_equivalence=False))
    return {'segments':rows,'facsimile_checked':False,'verified_full_units':0,'capability_and_actual_placement_separate':True,'per_unit_delay_and_approximation_not_yet_connected':True}


def build_report():
    documents={}
    for compose in (generic_composed,source_composed):
        text,basis=compose();doc=parse(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text:raise ValueError('Stored origin clock differs')
        if json.loads((ROOT/('data/'+basis['document'].split('/')[-1].replace('.noema','-basis-v1.json'))).read_text(encoding='utf-8'))!=basis:raise ValueError('Stored origin clock basis differs')
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Origin clock roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis)
    paths=[*documents,'data/origin-clock-basis-v1.json','data/einstein-origin-clock-basis-v1.json',
        'examples/v014/shape-contraction.noema','examples/v014/einstein-shape-contraction.noema',
        'scripts/compose_origin_clock.py','scripts/check_origin_clock.py','scripts/check_tau_differential.py','scripts/check_transverse_time.py',
        'reports/written-units-v1.json','artifacts/written-units-v1/einstein-1905.json',
        'noema/discourse.py','noema/finite_semantics.py','noema/polynomial_proofs.py']
    text=source_composed()[0];previous=(ROOT/'examples/v014/einstein-shape-contraction.noema').read_text(encoding='utf-8')
    return {'status':'partial_origin_clock_setup_question_and_time_equations','documents':documents,
        'polynomial_lemmas':polynomial_checks(),'placement':placement_checks(),'answers':answer_checks(),'frames':frame_checks(),'attribution':attribution_checks(),
        'alignment':alignment(),'roundtrips':True,'verified_full_units':{'einstein-1905':0,'kant-1784':0},
        'notation_size':{'canonical_source_document_characters':len(text),'added_characters':len(text)-len(previous)},
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args();report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Origin clock report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Origin clock calibration, placement, rate question and equations checked')


if __name__=='__main__':main()
