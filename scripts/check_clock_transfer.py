"""Check separated starts, same-event arrival, motion samples and clock laws."""
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
from scripts.compose_clock_transfer import ROOT, CUT, COMMON, CONSTANTS, generic_composed, source_composed

REPORT=ROOT/'reports/clock-transfer-v1.json'
DOMAIN=('movingclock','reference','otherclock','A','B','midplace','departure','initialreference','arrival','middle','first','initial','last','mid','rest','time','second','length','x','y','z','t')


def polynomial_checks():
    T,f,A,B,C,D,g=map(lambda n:'v '+n,('duration','rate','movingstart','referencestart','movingend','referenceend','gap'))
    sub=lambda a,b:k('ab',a,k('ac',b));mul=lambda a,b:k('ad',a,b);eq=lambda a,b:op('e',a,b)
    one=literal(1);zero=literal(0);pre=k('swj',T,f,A,B,C,D)
    names='duration rate movingstart referencestart movingend referenceend'
    claims={
        'initial_sync_and_interval_laws_determine_arrival_gap':assertion(names,op('y',pre,eq(sub(D,C),mul(sub(one,f),T)))),
        'strictly_slower_clock_is_behind_at_arrival':assertion(names,op('y',both(pre,k('aa',f,one)),k('aa',C,D))),
        'common_initial_offset_preserves_arrival_difference':assertion(names+' offset',op('z',pre,k('swj',T,f,*(k('ab',value,'v offset') for value in (A,B,C,D))))),
        'arrival_difference_is_not_initial_coordinate_time':assertion('',op('y',k('swj',literal(10),literal(Fraction(4,5)),literal(7),literal(7),literal(15),literal(17)),eq(sub(literal(17),literal(15)),literal(2)))),
        'unsynchronized_start_adds_initial_offset_to_gap':assertion(names,op('y',both(k('aa',zero,T),eq(sub(C,A),mul(f,T)),eq(sub(D,B),T)),eq(sub(D,C),k('ab',sub(B,A),mul(sub(one,f),T))))),
        'unequal_start_readings_can_be_ignored':assertion('',op('y',both(eq(sub(literal(15),literal(7)),literal(8)),eq(sub(literal(18),literal(8)),literal(10))),eq(sub(literal(18),literal(15)),literal(2)))),
        'matching_endpoints_proves_linear_midpoint':assertion('',op('y',eq(sub(literal(30),zero),mul(literal(3),literal(10))),eq(literal(20),mul(literal(3),literal(5))))),
        'zero_duration_shows_positive_lag':assertion('',k('aa',zero,mul(sub(one,literal(Fraction(4,5))),zero))),
    }
    invalid={'unequal_start_readings_can_be_ignored','matching_endpoints_proves_linear_midpoint','zero_duration_shows_positive_lag'}
    rows={}
    for name,claim in claims.items():
        row=verify_universal(parse(generic_composed()[0]+claim),MEANINGS,timeout_ms=15000)[0]
        if row['status']!=('invalid' if name in invalid else 'valid'):raise ValueError('Transfer algebra differs: '+name+repr(row))
        rows[name]=row
    return {'claims':rows,'interval_clock_laws_are_explicit_premises':True,'endpoint_positions_do_not_prove_uniform_motion':True}


def transfer_model(doc,label='baseline'):
    fixture=ConstructedCuts();c=fixture.make;n=fixture.read;model=guarded(doc);fixture.arithmetic(model)
    model['ba']=lambda x:isinstance(n(x),Fraction)
    t0=-20 if label=='negative_times' else 10;t1=t0+10
    start=[2,3,4,t0];end=[32,3,4,t1]
    if label=='diagonal':end[:3]=[20,27,4]
    if label=='backward':end[0]=-28
    if label=='wrong_endpoint_distance':end[0]+=1
    mid=[Fraction(a+b,2) for a,b in zip(start,end)]
    if label=='detour':mid[1]+=1
    if label=='nonuniform_progress':mid[0]+=3
    if label=='outside_interval':mid=[99,99,99,t1+10]
    coords={'first':start,'initial':end[:3]+[t0+1 if label=='not_simultaneous' else t0],'last':end,'mid':mid}
    offset=100 if label=='common_dial_offset' else 0
    reads={'movingstart':7+offset,'referencestart':7+offset,'movingend':15+offset,'referenceend':17+offset}
    if label=='unequal_initial':reads['referencestart']+=1;reads['referenceend']+=1
    if label=='reset_during_trip':reads['movingend']+=1
    if label=='reference_wrong_rate':reads['referenceend']+=1
    individual={'movingclock':'movingclock','reference':'movingclock' if label=='same_clock' else 'reference',
        'placea':'A','placeb':'A' if label=='same_place' else 'B','departure':'departure','initialreference':'initialreference','arrival':'arrival',
        'firstrecord':'first','initialrecord':'initial','lastrecord':'last','initial':'motion' if label=='collapsed_contexts' else 'text','motion':'motion'}
    for name,sort in COMMON:
        symbol=CONSTANTS[name];value=reads[name] if sort==CUT else individual[name]
        model[symbol]=(lambda value=value:c(value)) if sort==CUT else (lambda value=value:value)
    for symbol,value in {'ra':'rest','rb':'time','ta':'length','yn':'x','yo':'y','yp':'z','zc7':'t','zik':'second'}.items():model[symbol]=lambda value=value:value
    chart={('departure','text'):'first',('initialreference','text'):'initial',('departure','motion'):'first',('arrival','motion'):'last',('middle','motion'):'mid'}
    placements={('movingclock','departure','A','text'),('reference','initialreference','B','text'),('movingclock','departure','A','motion'),('movingclock','arrival','B','motion'),('reference','arrival','B','motion'),('movingclock','middle','midplace','motion')}
    if label=='reference_wrong_place':placements.remove(('reference','arrival','B','motion'))
    if label=='missing_middle':placements.remove(('movingclock','middle','midplace','motion'))
    readingvalues={('movingclock','departure'):reads['movingstart'],('reference','initialreference'):reads['referencestart'],('movingclock','arrival'):reads['movingend'],('reference','arrival'):reads['referenceend']}
    if label=='different_arrival_event':readingvalues.pop(('reference','arrival'))
    model.update(tc=lambda:c(5),zb7=lambda:c(4 if label=='wrong_speed' else 0 if label=='zero_speed' else 3),sky=lambda x:square_root(fixture,x),
        ca=lambda obj:obj in ('movingclock','reference'),ci=lambda unit:unit in ('time','second'),
        x4=lambda obj,frame,ctx:frame=='rest' and (obj,ctx) in {('movingclock','text'),('reference','text'),('reference','motion')} and not(label=='reference_moved' and (obj,ctx)==('reference','motion')) and not(label=='not_initially_stationary' and (obj,ctx)==('movingclock','text')),
        xm=lambda obj,frame,ctx:(obj,frame,ctx)==('movingclock','rest','motion'),
        qo=lambda first,second,frame,unit,ctx:(first,second,frame,unit,ctx)==('movingclock','reference','rest','time','text') and label!='no_initial_sync',
        zc4=lambda event:event in ('departure','initialreference','arrival','middle'),zc5=lambda record:record in coords,
        zc6=lambda record,axis:c(coords.get(record,[0]*4)[('x','y','z','t').index(axis)] if axis in ('x','y','z','t') else 0),
        shd=lambda event,record,frame,ctx:frame=='rest' and chart.get((event,ctx))==record and not(label=='departure_not_preserved' and (event,ctx)==('departure','motion')),
        zab=lambda obj,event,place,frame,ctx:frame=='rest' and (obj,event,place,ctx) in placements,
        cb=lambda event,place,frame:frame=='rest' and (event,place) in {('departure','A'),('initialreference','B'),('arrival','B'),('middle','midplace')},
        ce=lambda clock,event,frame,unit,value:frame=='rest' and unit==('second' if label=='wrong_reading_unit' else 'time') and readingvalues.get((clock,event))==n(value),
        zil=lambda source,target,scale,ctx:(source,target,n(scale),ctx)==('time','second',1,'motion'))
    return model,fixture,coords,reads


def physical_checks():
    args=' '.join('k '+CONSTANTS[n]+'[]' for n,_ in COMMON)
    query='q[k swm['+args+']].q[k swo[k ziv[] k zix[] k zb7[]]].q[k swx[k zie[] k ziv[] k zix[] k zi5[]]].q[k swr['+args+']].q[t[k swv[]][k zi5[]]].'
    doc=abstract(candidate(source_composed()[0],query),ARITHMETIC|{'sky','shd','qo'});rows={}
    labels=('baseline','negative_times','common_dial_offset','diagonal','backward','same_clock','same_place','collapsed_contexts','not_simultaneous',
        'no_initial_sync','not_initially_stationary','reference_moved','reference_wrong_place','different_arrival_event','wrong_reading_unit','departure_not_preserved',
        'unequal_initial','reset_during_trip','reference_wrong_rate','wrong_speed','zero_speed','wrong_endpoint_distance','detour','nonuniform_progress','missing_middle','outside_interval')
    for label in labels:
        model,_,_,_=transfer_model(doc,label);actual=values(doc,model,DOMAIN)
        physical=label not in ('same_clock','same_place','collapsed_contexts','not_simultaneous','no_initial_sync','not_initially_stationary','reference_moved','reference_wrong_place','different_arrival_event','wrong_reading_unit','departure_not_preserved','unequal_initial')
        endpoints=label not in ('wrong_speed','zero_speed','wrong_endpoint_distance')
        samples=label not in ('detour','nonuniform_progress')
        law=physical and endpoints and label not in ('reset_during_trip','reference_wrong_rate')
        comparison=label not in ('unequal_initial','reset_during_trip','reference_wrong_rate','wrong_speed','zero_speed')
        expected=[physical,endpoints,samples,law,comparison]
        if actual!=expected:raise ValueError('Clock transfer physical condition differs: '+label+repr(actual))
        rows[label]=actual
    return {'cases':rows,'three_distinct_events_and_two_places':True,'full_time_coverage_not_certified_by_samples':True,'synchronization_and_charts_are_oracles':True}


def gap_checks():
    query=''.join('r '+name+'[] '+CUT+'.' for name in ('ja','jb','jc','jd','je'))
    query+='q[k swk[k ja[] k jb[] k jc[] k jd[] k je[]]].q[t[k swv[]][k zi5[]]].q[k sxa[k ja[]]].'
    doc=abstract(candidate(source_composed()[0],query),ARITHMETIC|{'sky','shd','qo'});rows={}
    for label in ('baseline','common_dial_offset','negative_times','wrong_gap','exact_as_approximation','wrong_duration','wrong_conversion','unsynchronized_start'):
        model,fixture,_,_=transfer_model(doc,'unequal_initial' if label=='unsynchronized_start' else label)
        args=[1,10,3 if label=='wrong_gap' else 2,2 if label=='exact_as_approximation' else Fraction(9,5),Fraction(1,5)]
        if label=='wrong_duration':args[1]=20
        if label=='wrong_conversion':model['zil']=lambda *args:False
        for name,value in zip(('ja','jb','jc','jd','je'),args):model[name]=lambda value=value:fixture.make(value)
        actual=values(doc,model,DOMAIN)
        expected=[label in ('baseline','common_dial_offset','negative_times'),label!='unsynchronized_start',label not in ('unsynchronized_start','wrong_conversion')]
        if actual!=expected:raise ValueError('Arrival second gap differs: '+label+repr(actual))
        rows[label]=actual
    return {'cases':rows,'baseline_seconds':{'duration':'10','exact_gap':'2','approximation':'9/5','error':'1/5'},'rate_difference_not_absolute_time_used':True}


def infinite_conditions_refused():
    rows={}
    for name,query in {'trajectory':'q[k swq[k zie[] k ziv[] k zix[] k zi5[]]].','asymptotic_duration':'q[k swy[k bb[n p k b]]].'}.items():
        doc=abstract(candidate(source_composed()[0],query),ARITHMETIC|{'sky','shd','qo'});model,_,_,_=transfer_model(doc)
        try:values(doc,model,DOMAIN)
        except ValueError as error:
            if 'rational number domain' not in str(error):raise
            rows[name]=str(error)
        else:raise ValueError('Continuous condition was finitely sampled: '+name)
    return rows


def attribution_checks():
    doc=parse(source_composed()[0]);doc['statements']=doc['statements'][-3:];rows={}
    for label in ('baseline','wrong_author','wrong_scope','wrong_context','wrong_setup','wrong_idealization','wrong_conclusion'):
        model=guarded(doc);constants={'zi6':'setup','zi7':'conclusion','zja':'idealization','rd':'author','rh':'scope','ri':'text'}
        for name,value in constants.items():model[name]=lambda value=value:value
        sym=lambda d:json.loads(d.syntax)['symbol']
        common=lambda a,s,c:(a,s,c)==('other' if label=='wrong_author' else 'author','other' if label=='wrong_scope' else 'scope','other' if label=='wrong_context' else 'text')
        model.update(ug=lambda node,a,d,s,c:common(a,s,c) and (node,sym(d))==('setup','swt' if label=='wrong_setup' else 'sws'),
            zfl=lambda node,a,p,d,s,c:common(a,s,c) and (node,sym(p),sym(d))==('idealization','sws','swv' if label=='wrong_idealization' else 'swt'),
            zc=lambda node,a,p,d,s,c:common(a,s,c) and (node,sym(p),sym(d))==('conclusion','swu','swz' if label=='wrong_conclusion' else 'sww'))
        actual=values(doc,model,tuple(v for k,v in constants.items() if k!='ri'))
        expected=[label not in ('wrong_author','wrong_scope','wrong_context',bad) for bad in ('wrong_setup','wrong_idealization','wrong_conclusion')]
        if actual!=expected:raise ValueError('Transfer attribution differs: '+label)
        rows[label]=actual
    return rows


def alignment():
    path=ROOT/'artifacts/written-units-v1/einstein-1905.json';artifact=json.loads(path.read_text(encoding='utf-8'))
    inventory=json.loads((ROOT/'reports/written-units-v1.json').read_text(encoding='utf-8'))
    if hashlib.sha256(path.read_bytes()).hexdigest()!=inventory['works']['einstein-1905']['units_sha256']:raise ValueError('Pinned transfer source differs')
    unit=next(u for u in artifact['units'] if u['id']=='einstein-1905:u0126');names=['swm','swo','swp','swq','swr','swv','swk','sww','swy']
    if hashlib.sha256(unit['text'].encode('utf-8')).hexdigest()!=unit['text_sha256']:raise ValueError('Clock transfer unit differs')
    rows=[dict(unit=unit['id'],unit_sha256=unit['text_sha256'],start=0,end=len(unit['text']),source=unit['text'],definitions=names,status='partial_explicit_reading',full_semantic_equivalence=False)]
    for mid in unit['math_ids']:
        item=next(m for m in artifact['math'] if m['id']==mid)
        if hashlib.sha256(item['mathml'].encode('utf-8')).hexdigest()!=item['sha256']:raise ValueError('Clock transfer math differs')
        rows.append(dict(unit=unit['id'],unit_sha256=unit['text_sha256'],math_id=mid,math_sha256=item['sha256'],definitions=names,status='partial',full_semantic_equivalence=False))
    return {'segments':rows,'facsimile_checked':False,'verified_full_units':0,'acceleration_response_not_derived':True,'distinctive_consequence_appraisal_unwritten':True}


def build_report():
    documents={}
    for compose in (generic_composed,source_composed):
        text,basis=compose();doc=parse(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text:raise ValueError('Stored transfer differs')
        if json.loads((ROOT/('data/'+basis['document'].split('/')[-1].replace('.noema','-basis-v1.json'))).read_text(encoding='utf-8'))!=basis:raise ValueError('Stored transfer basis differs')
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Transfer roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis)
    paths=[*documents,'data/clock-transfer-basis-v1.json','data/einstein-clock-transfer-basis-v1.json',
        'examples/v014/clock-delay.noema','examples/v014/einstein-clock-delay.noema',
        'scripts/compose_clock_transfer.py','scripts/check_clock_transfer.py','scripts/check_tau_differential.py','scripts/check_transverse_time.py',
        'reports/written-units-v1.json','artifacts/written-units-v1/einstein-1905.json',
        'noema/discourse.py','noema/finite_semantics.py','noema/polynomial_proofs.py']
    text=source_composed()[0];previous=(ROOT/'examples/v014/einstein-clock-delay.noema').read_text(encoding='utf-8')
    return {'status':'partial_initial_sync_straight_transfer_and_arrival_comparison','documents':documents,
        'polynomial_lemmas':polynomial_checks(),'physical_setup':physical_checks(),'arrival_gap':gap_checks(),
        'infinite_conditions':infinite_conditions_refused(),'attribution':attribution_checks(),'alignment':alignment(),'roundtrips':True,
        'verified_full_units':{'einstein-1905':0,'kant-1784':0},'notation_size':{'canonical_source_document_characters':len(text),'added_characters':len(text)-len(previous)},
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args();report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Clock transfer report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Initial synchronization, straight transfer and same-event arrival checked')


if __name__=='__main__':main()
