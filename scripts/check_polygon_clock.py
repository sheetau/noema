"""Check polygon observations without treating sampled legs as continua."""
import argparse
from fractions import Fraction
import hashlib
import json

from noema.finite_semantics import FunctionValue, SequenceValue
from noema.grammar import parse, format_graph, number_word
from noema.meaning_basis import audit_basis
from noema.polynomial_proofs import verify_universal
from noema.script import encode, decode
from scripts.check_comoving_labels import values
from scripts.check_coordinate_correspondence import abstract
from scripts.check_described_appraisals import candidate
from scripts.check_finite_paths import canonical
from scripts.check_rod_setup import guarded
from scripts.check_tau_differential import ARITHMETIC, ConstructedCuts
from scripts.check_transverse_time import square_root
from scripts.check_real_products import MEANINGS, call as k, op, assertion, conjunction as both
from scripts.compose_clock_transfer import generic_composed
from scripts.compose_polygon_clock import ROOT, CUT, PATH, COMPARE, composed

REPORT=ROOT/'reports/polygon-clock-v1.json'


def query_document(queries,parameters=COMPARE):
    names={n:'zz'+number_word(i) for i,(n,_) in enumerate(parameters)}
    text=''.join('r '+names[n]+'[] '+sort+'.' for n,sort in parameters)
    for symbol,items in queries:text+='q['+k(symbol,*(k(names[n]) for n,_ in items))+'].'
    return abstract(candidate(composed()[0],text),ARITHMETIC|{'sky','shd','qo'}),names


def bind_parameters(doc,model,names,inputs):
    decls={d['name']:d for d in doc['declarations']}
    for parameter,name in names.items():
        sort=decls[name]['result'];value=inputs[parameter]
        if isinstance(sort,dict) and sort['kind']=='sequence':value=SequenceValue(tuple(value),canonical(sort['element']))
        elif isinstance(sort,dict) and sort['kind']=='function' and callable(value) and not isinstance(value,FunctionValue):value=FunctionValue(tuple(sort['parameters']),sort['result'],value)
        model[name]=lambda value=value:value


def model_for(doc,names,label):
    fixture=ConstructedCuts();c=fixture.make;n=fixture.read;model=guarded(doc);fixture.arithmetic(model)
    model['ba']=lambda x:isinstance(n(x),Fraction)
    positions=[[0,0,0],[15,0,0],[0,0,0]];times=[0,5,10]
    if label=='open_bend':positions[-1]=[15,15,0]
    if label=='triangle':positions=[[0,0,0],[3,0,0],[3,4,0],[0,0,0]];times=list(map(Fraction,[0,1,Fraction(7,3),4]))
    if label=='diagonal':positions[1]=[9,12,0]
    if label=='wrong_distance':positions[1][0]+=1
    if label=='negative_times':times=[t-20 for t in times]
    if label=='zero_duration':times[1]=times[0]
    offset=100 if label=='common_dial_offset' else 0
    events=['e'+str(i) for i in range(len(times))];legs=['leg'+str(i) for i in range(len(times)-1)]
    records={e:'r'+str(i) for i,e in enumerate(events)}
    coords={records[e]:list(map(Fraction,positions[i]+[times[i]])) for i,e in enumerate(events)}
    readings={e:Fraction(7+offset)+Fraction(4,5)*(t-times[0]) for e,t in zip(events,times)}
    if label=='reset_corner':readings[events[1]]+=1
    if label=='reset_last':readings[events[-1]]+=1
    start={s:events[i] for i,s in enumerate(legs)};end={s:events[i+1] for i,s in enumerate(legs)}
    places={e:'place'+str(i) for i,e in enumerate(events)}
    if positions[-1]==positions[0]:places[events[-1]]=places[events[0]]
    mids=[]
    for i in range(len(legs)):
        e='mid'+str(i);r='mr'+str(i);mids.append(e);records[e]=r;places[e]='mp'+str(i)
        coords[r]=[(a+b)/2 for a,b in zip(coords['r'+str(i)],coords['r'+str(i+1)])]
    if label=='detour':coords['mr0'][1]+=1
    if label=='uneven_progress':coords['mr0'][0]+=1
    if label=='disconnected_equal_record':
        end[legs[0]]='alias';records['alias']=records[events[1]];readings['alias']=readings[events[1]];places['alias']=places[events[1]]
    selected=list(legs)
    if label=='empty':selected=[]
    if label=='reordered':selected.reverse()
    if label=='duplicate_leg':selected=[legs[0]]+selected
    coords['initialrecord']=list(map(Fraction,positions[-1]+[times[0]+(1 if label=='not_simultaneous' else 0)]))
    records['initialreference']='initialrecord';places['initialreference']=places[events[-1]]
    initialreading=Fraction(7+offset)+(1 if label=='not_initially_equal' else 0)
    finalreading=initialreading+times[-1]-times[0]+(1 if label=='reference_wrong_rate' else 0)
    # A return starts at the same event for both clocks; an open path does not.
    initialevent=events[0] if positions[-1]==positions[0] else 'initialreference'
    initialrecord=records[initialevent]
    if label=='not_simultaneous':initialevent='initialreference';initialrecord='initialrecord'
    frame='rest';ctx='motion';unit='time'
    readtable={('clock',e):value for e,value in readings.items()}
    readtable[('reference',initialevent)]=initialreading;readtable[('reference',events[-1])]=finalreading
    domain=tuple(dict.fromkeys(['clock','reference','other','rest','time','second','x','y','z','t',
        *records,*coords,*places.values(),*legs]))
    model.update(tc=lambda:c(5),sky=lambda x:square_root(fixture,x),
        ca=lambda clock:clock in ('clock','reference'),ci=lambda unit:unit in ('time','second'),
        ra=lambda:frame,rb=lambda:unit,zik=lambda:'second',yn=lambda:'x',yo=lambda:'y',yp=lambda:'z',zc7=lambda:'t',
        xm=lambda clock,f,s:(clock,f,s)==('clock',frame,ctx),
        x4=lambda clock,f,s:f==frame and (clock,s) in {('clock','text'),('reference','text'),('reference',ctx)} and not(label=='reference_moves' and s==ctx),
        qo=lambda clock,ref,f,u,s:(clock,ref,f,u,s)==('clock','reference',frame,unit,'text') and label!='no_sync',
        zc4=lambda event:event in records,zc5=lambda rec:rec in coords,
        zc6=lambda rec,axis:c(coords.get(rec,[0]*4)[('x','y','z','t').index(axis)] if axis in ('x','y','z','t') else 0),
        shd=lambda event,rec,f,s:f==frame and records.get(event)==rec and (s==ctx or s=='text' and event in (events[0],initialevent)) and not(label=='missing_corner_record' and event==events[1]),
        cb=lambda event,place,f:f==frame and places.get(event)==place,
        ce=lambda clock,event,f,u,val:f==frame and u==unit and readtable.get((clock,event))==n(val) and not(label=='wrong_clock_at_corner' and event==events[1] and clock=='clock'))
    def located(clock,event,place,f,s):
        if f!=frame or places.get(event)!=place:return False
        if clock=='clock':return event in readings or event in mids and label!='missing_midpoint'
        return clock=='reference' and ((event==initialevent and s=='text') or (event==events[-1] and s==ctx and label!='reference_wrong_place'))
    model['zab']=located
    model['zil']=lambda source,target,scale,s:(source,target,n(scale),s)==('time','second',1,ctx)
    inputs=dict(segments=selected,start=lambda leg:start.get(leg,events[0]),end=lambda leg:end.get(leg,events[-1]),
        record=lambda event:records.get(event,'r0'),reading=lambda event:c(readings.get(event,0)),clock='clock',first=events[0],
        last=events[0] if label=='same_endpoint_event' else events[-1],speed=c(4 if label=='wrong_common_speed' else 3),setting=ctx,
        reference='clock' if label=='same_clock' else 'reference',initialevent=initialevent,initialrecord=initialrecord,
        referencestart=c(initialreading),referenceend=c(finalreading),initial='text')
    bind_parameters(doc,model,names,inputs)
    return model,fixture,domain,times,readings


def physical_checks():
    queries=[('sxg',PATH),('sxl',COMPARE),('sxm',COMPARE),('sxn',COMPARE),('sxo',PATH)]
    doc,names=query_document(queries);rows={}
    labels=('baseline','open_bend','triangle','diagonal','negative_times','common_dial_offset','wrong_distance','zero_duration','reset_corner',
        'reset_last','detour','uneven_progress','disconnected_equal_record','empty','reordered','duplicate_leg','not_simultaneous',
        'not_initially_equal','reference_wrong_rate','reference_moves','no_sync','missing_corner_record','wrong_clock_at_corner',
        'missing_midpoint','reference_wrong_place','same_endpoint_event','same_clock','wrong_common_speed')
    for label in labels:
        model,_,domain,_,_=model_for(doc,names,label);actual=values(doc,model,domain)
        geometry=label not in ('wrong_distance','zero_duration','detour','uneven_progress','disconnected_equal_record','empty','reordered','duplicate_leg','missing_corner_record','wrong_clock_at_corner','same_endpoint_event','wrong_common_speed')
        comparison=label not in ('not_simultaneous','not_initially_equal','reference_moves','no_sync','reference_wrong_place','same_endpoint_event','same_clock')
        laws=label not in ('reset_corner','reset_last','reference_wrong_rate','same_endpoint_event','wrong_common_speed')
        gap=label not in ('reset_last','not_initially_equal','reference_wrong_rate','same_endpoint_event','wrong_common_speed')
        closed=label not in ('open_bend','same_endpoint_event')
        expected=[geometry,comparison,laws,gap,closed]
        if actual!=expected:raise ValueError('Polygon physical case differs: '+label+repr(actual)+' != '+repr(expected))
        rows[label]=actual
    return {'cases':rows,'same_corner_event_and_reading_function':True,'endpoint_conditions_do_not_establish_complete_trajectory':True}


def fold_checks():
    # Independent numerical sums and event chaining, separate from geometry.
    parameters=[('segments','j[a]'),('measure','h[a] '+CUT),('start','h[a] a'),('end','h[a] a'),('first','a'),('last','a')]
    doc,names=query_document([('sxc',[parameters[i] for i in (0,2,3,4,5)])],parameters)
    result=[]
    for size in (0,1,2,5,16,24):
        fixture=ConstructedCuts();model=guarded(doc);fixture.arithmetic(model)
        domain=tuple('p'+str(i) for i in range(size+1))+tuple('s'+str(i) for i in range(size))
        mapping={'s'+str(i):Fraction(i-3,7) for i in range(size)}
        model_inputs=dict(segments=list(mapping),measure=lambda seg:fixture.make(mapping.get(seg,0)),
            start=lambda seg:'p'+seg[1:] if seg in mapping else 'p0',
            end=lambda seg:'p'+str(int(seg[1:])+1) if seg in mapping else 'p0',first='p0',last='p'+str(size))
        bind_parameters(doc,model,names,model_inputs)
        sumdoc=parse(format_graph(doc,'compact')+'q[k sca[k sxd['+k(names['segments'])+' '+k(names['measure'])+'] k bb['+literal(sum(mapping.values(),Fraction(0)))+']]].')
        actual=values(sumdoc,model,domain)
        if actual!=[True,True]:raise ValueError('Polygon fold differs: '+str(size)+repr(actual))
        result.append({'length':size,'sum':str(sum(mapping.values(),Fraction(0))),'accepted':actual})
    return result


def observed_totals_checks():
    base,names=query_document([],PATH);arguments=[k(names[n]) for n,_ in PATH];rows={}
    for label in ('baseline','triangle','open_bend','reset_corner','duplicate_leg'):
        model,_,domain,times,readings=model_for(base,names,label)
        total=times[-1]-times[0];elapsed=readings['e'+str(len(times)-1)]-readings['e0']
        if label=='duplicate_leg':total+=times[1]-times[0];elapsed+=readings['e1']-readings['e0']
        query=''.join('q['+k('sca',k(symbol,*arguments),k('bb',literal(value)))+'].' for symbol,value in (('sxj',total),('sxk',elapsed)))
        doc=candidate(format_graph(base,'compact'),query);actual=values(doc,model,domain)
        if actual!=[True,True]:raise ValueError('Observed polygon totals differ: '+label)
        rows[label]={'duration':str(total),'elapsed':str(elapsed),'accepted':actual}
    return {'cases':rows,'invalid_duplicate_path_still_counts_each_occurrence':True,'totals_alone_do_not_prove_path_or_interval_laws':True}


def literal(value):
    from scripts.check_moving_light_trip import literal as make
    return make(value)


def polynomial_checks():
    sub=lambda a,b:k('ab',a,k('ac',b));mul=lambda a,b:k('ad',a,b);add=lambda a,b:k('ab',a,b);eq=lambda a,b:op('e',a,b)
    a,b,c,f,g,T,U=map(lambda n:'v '+n,('first','middle','last','rate','otherrate','duration','nextduration'))
    claims={
        'shared_corner_differences_telescope':assertion('first middle last',eq(add(sub(b,a),sub(c,b)),sub(c,a))),
        'common_rate_factors_over_legs':assertion('rate duration nextduration',eq(add(mul(f,T),mul(f,U)),mul(f,add(T,U)))),
        'different_rates_cannot_use_first_rate_for_total':assertion('rate otherrate duration nextduration',eq(add(mul(f,T),mul(g,U)),mul(f,add(T,U)))),
        'same_position_does_not_imply_same_time':assertion('',op('y',eq(literal(0),literal(0)),eq(literal(0),literal(10)))),
        'same_speed_reverse_direction_same_factor':assertion('speed rate light',op('z',k('stt','v light','v speed','v rate'),k('stt','v light',k('ac','v speed'),'v rate'))),
        'two_leg_clock_laws_yield_total_gap':assertion('first middle last referencefirst referencelast rate duration nextduration',
            op('y',both(eq(a,'v referencefirst'),eq(sub(b,a),mul(f,T)),eq(sub(c,b),mul(f,U)),eq(sub('v referencelast','v referencefirst'),add(T,U))),
                eq(sub('v referencelast',c),mul(sub(literal(1),f),add(T,U))))),
    }
    rows={}
    for name,claim in claims.items():
        row=verify_universal(parse(generic_composed()[0]+claim),MEANINGS,timeout_ms=15000)[0]
        expected='invalid' if name in ('different_rates_cannot_use_first_rate_for_total','same_position_does_not_imply_same_time') else 'valid'
        if row['status']!=expected:raise ValueError('Polygon algebra differs: '+name+repr(row))
        rows[name]=row
    return rows


def infinite_checks():
    rows={}
    for label,query in (('all_times',None),('all_finite_paths','q[t[k sxq[]][k ri[]]].')):
        doc,names=query_document([('sxh',PATH)])
        if query:doc=candidate(format_graph(doc,'compact'),query)
        model,_,domain,_,_=model_for(doc,names,'baseline');model['ri']=lambda:'text'
        try:values(doc,model,domain)
        except ValueError as error:
            required='rational number domain' if label=='all_times' else 'sequence'
            if required not in str(error).lower():raise
            rows[label]=str(error)
        else:raise ValueError('Infinite polygon claim sampled: '+label)
    return rows


def attribution_checks():
    doc=parse(composed()[0]);doc['statements']=doc['statements'][-3:];rows={}
    for label in ('baseline','wrong_author','wrong_scope','wrong_context','wrong_result','wrong_return','wrong_clear'):
        model=guarded(doc)
        for name,value in {'zjb':'polygon','zjc':'return','rd':'author','rh':'scope','ri':'text'}.items():model[name]=lambda value=value:value
        common=lambda a,s,c:(a,s,c)==('other' if label=='wrong_author' else 'author','other' if label=='wrong_scope' else 'scope','other' if label=='wrong_context' else 'text')
        symbol=lambda d:json.loads(d.syntax)['symbol']
        model['uh']=lambda node,a,d,s,c:common(a,s,c) and (node,symbol(d)) in {('polygon','sxr' if label=='wrong_result' else 'sxq'),('return','sxq' if label=='wrong_return' else 'sxr')}
        model['zdg']=lambda node,a,d,s,c:common(a,s,c) and (node,symbol(d))==('polygon','sxr' if label=='wrong_clear' else 'sxq')
        actual=values(doc,model,('polygon','return','author','scope','other'))
        expected=[label not in ('wrong_author','wrong_scope','wrong_context',bad) for bad in ('wrong_result','wrong_clear','wrong_return')]
        if actual!=expected:raise ValueError('Polygon attribution differs: '+label)
        rows[label]=actual
    return rows


def alignment():
    path=ROOT/'artifacts/written-units-v1/einstein-1905.json';artifact=json.loads(path.read_text(encoding='utf-8'))
    inventory=json.loads((ROOT/'reports/written-units-v1.json').read_text(encoding='utf-8'))
    if hashlib.sha256(path.read_bytes()).hexdigest()!=inventory['works']['einstein-1905']['units_sha256']:raise ValueError('Pinned polygon source differs')
    unit=next(u for u in artifact['units'] if u['id']=='einstein-1905:u0127');defs=['sxg','sxh','sxi','sxl','sxm','sxn','sxo','sxp','sxq','sxr']
    if hashlib.sha256(unit['text'].encode('utf-8')).hexdigest()!=unit['text_sha256']:raise ValueError('Polygon text differs')
    rows=[dict(unit=unit['id'],unit_sha256=unit['text_sha256'],start=0,end=len(unit['text']),source=unit['text'],definitions=defs,status='partial_explicit_reading',full_semantic_equivalence=False)]
    for mid in unit['math_ids']:
        item=next(m for m in artifact['math'] if m['id']==mid)
        if hashlib.sha256(item['mathml'].encode('utf-8')).hexdigest()!=item['sha256']:raise ValueError('Polygon math differs')
        rows.append(dict(unit=unit['id'],unit_sha256=unit['text_sha256'],math_id=mid,math_sha256=item['sha256'],definitions=defs,status='partial',full_semantic_equivalence=False))
    return {'segments':rows,'facsimile_checked':False,'verified_full_units':0,'common_speed_inherited_from_previous_result':True,'acceleration_response_not_derived':True}


def build_report():
    text,basis=composed();doc=parse(text)
    if (ROOT/basis['document']).read_text(encoding='utf-8')!=text:raise ValueError('Stored polygon differs')
    if json.loads((ROOT/'data/polygon-clock-basis-v1.json').read_text(encoding='utf-8'))!=basis:raise ValueError('Polygon basis differs')
    for notation in ('compact','full'):
        form=format_graph(doc,notation)
        if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Polygon roundtrip differs')
    paths=[basis['document'],'data/polygon-clock-basis-v1.json','examples/v014/einstein-clock-transfer.noema','examples/v014/clock-transfer.noema',
        'scripts/compose_polygon_clock.py','scripts/check_polygon_clock.py','scripts/check_tau_differential.py','scripts/check_transverse_time.py',
        'reports/written-units-v1.json','artifacts/written-units-v1/einstein-1905.json','noema/discourse.py','noema/finite_semantics.py','noema/polynomial_proofs.py']
    previous=(ROOT/'examples/v014/einstein-clock-transfer.noema').read_text(encoding='utf-8')
    return {'status':'partial_polygon_clock_and_same_place_return','documents':{basis['document']:audit_basis(doc,basis)},
        'physical_setup':physical_checks(),'finite_folds':fold_checks(),'observed_totals':observed_totals_checks(),'polynomial_lemmas':polynomial_checks(),
        'infinite_conditions':infinite_checks(),'attribution':attribution_checks(),'alignment':alignment(),'roundtrips':True,
        'verified_full_units':{'einstein-1905':0,'kant-1784':0},
        'notation_size':{'canonical_source_document_characters':len(text),'added_characters':len(text)-len(previous)},
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args();report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Polygon report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Polygon clocks and return comparison checked')


if __name__=='__main__':main()
