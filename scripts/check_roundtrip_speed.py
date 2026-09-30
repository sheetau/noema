"""Separate physical bindings, scoped constancy and rational arithmetic evidence."""
import argparse
from copy import deepcopy
from fractions import Fraction
import hashlib
from itertools import product
import json

from noema.finite_semantics import FunctionValue, evaluate_document
from noema.grammar import format_graph, parse, number_word
from noema.meaning_basis import audit_basis
from noema.polynomial_proofs import verify_universal
from noema.script import encode, decode
from scripts.check_described_appraisals import candidate
from scripts.check_real_products import MEANINGS, ZERO, assertion, call, conjunction, op
from scripts.check_synchrony_network import source_model, values
from scripts.compose_roundtrip_speed import ROOT, generic_composed, source_composed

REPORT = ROOT/'reports/roundtrip-speed-v1.json'
ARITHMETIC = {'aa':lambda a,b:a<b, 'ab':lambda a,b:a+b, 'ac':lambda a:-a, 'ad':lambda a,b:a*b}


def numeric_checks():
    text = generic_composed()[0]
    rows = {}
    cases = {
        'baseline': ((6,0,4,3,1,1,1),True),
        'shift_both_times': ((6,10,14,3,1,1,1),True),
        'change_length_unit': ((600,0,4,3,Fraction(1,100),1,1),True),
        'change_time_unit': ((6,0,400,3,1,Fraction(1,100),1),True),
        'change_speed_unit': ((6,0,4,300,1,1,Fraction(1,100)),True),
        'negative_clock_origin': ((6,-10,-6,3,1,1,1),True),
        'one_way_instead_of_roundtrip': ((6,0,4,Fraction(3,2),1,1,1),False),
        'changed_departure_only': ((6,1,4,3,1,1,1),False),
        'zero_duration': ((6,4,4,3,1,1,1),False),
        'reversed_duration': ((6,4,0,3,1,1,1),False),
        'zero_distance': ((0,0,4,3,1,1,1),False),
        'negative_distance': ((-6,0,4,3,1,1,1),False),
        'negative_speed': ((6,0,4,-3,1,1,1),False),
        'unconverted_length': ((600,0,4,3,1,1,1),False),
        'zero_length_scale': ((6,0,4,3,0,1,1),False),
        'zero_time_scale': ((6,0,4,3,1,0,1),False),
        'negative_speed_scale': ((6,0,4,3,1,1,-1),False),
    }
    def literal(value):
        q=Fraction(value)
        return 'n '+('u' if q<0 else 'p')+' '+number_word(abs(q.numerator))+' '+number_word(q.denominator)
    for name,(args,expected) in cases.items():
        doc=parse(text+'q['+call('saj',*(literal(a) for a in args))+'].')
        actual=evaluate_document(doc,individuals=('object',),situations=('text',),primitives=ARITHMETIC)[0]['value']
        if actual!=expected: raise ValueError('Rate arithmetic differs: '+name)
        rows[name]=actual
    return rows


def polynomial_checks():
    text=generic_composed()[0]
    d,a,b,v,ls,ts,vs,k,new = ('v '+n for n in ('d','a','b','v','ls','ts','vs','k','new'))
    mul=lambda x,y:call('ad',x,y)
    add=lambda x,y:call('ab',x,y)
    positive=lambda x:call('aa',ZERO,x)
    rate=lambda *args:call('saj',*args)
    base=rate(d,a,b,v,ls,ts,vs)
    claims={
        'common_origin_shift':assertion('d a b v ls ts vs k',op('z',base,rate(d,add(a,k),add(b,k),v,ls,ts,vs))),
        'unique_speed_in_fixed_units':assertion('d a b v ls ts vs new',op('y',conjunction(base,rate(d,a,b,new,ls,ts,vs)),op('e',v,new))),
        'distance_reading_scale_compensation':assertion('d a b v ls ts vs k new',op('y',conjunction(positive(ls),positive(k),op('e',mul(k,new),mul(ls,d))),op('z',base,rate(new,a,b,v,k,ts,vs)))),
        'speed_reading_scale_compensation':assertion('d a b v ls ts vs k new',op('y',conjunction(positive(vs),positive(k),op('e',mul(k,new),mul(vs,v))),op('z',base,rate(d,a,b,new,ls,ts,k)))),
        'scaling_time_and_speed_together_preserves_rate':assertion('d a b v ls ts vs k',op('y',positive(k),op('z',base,rate(d,mul(k,a),mul(k,b),v,ls,ts,mul(vs,k))))),
        'zero_duration_rejected':assertion('d a v ls ts vs',op('u',rate(d,a,a,v,ls,ts,vs))),
        'reversed_times_rejected':assertion('d a b v ls ts vs',op('y',base,op('u',rate(d,b,a,v,ls,ts,vs)))),
        'only_one_clock_origin_shift_preserves_rate':assertion('d a b v ls ts vs k',op('y',base,op('z',rate(d,add(a,k),b,v,ls,ts,vs),op('e',k,ZERO)))),
    }
    # Correct time scaling uses the inverse numeric speed or time unit scale;
    # multiplying BOTH numeric time and the speed scale is deliberately false.
    expected={name:'valid' for name in claims}
    expected['scaling_time_and_speed_together_preserves_rate']='invalid'
    claims['consistent_time_unit_change']=assertion('d a b v ls ts vs k new',op('y',
        conjunction(positive(k),positive(new),op('e',mul(k,new),ts)),
        op('z',base,rate(d,mul(k,a),mul(k,b),v,ls,new,vs))))
    expected['consistent_time_unit_change']='valid'
    rows={}
    for name,claim in claims.items():
        result=verify_universal(parse(text+claim),MEANINGS,timeout_ms=15000)[0]
        if result['status']!=expected[name]: raise ValueError('Polynomial rate condition differs: '+name+' '+result['status'])
        rows[name]=result
    return rows


def constancy_checks():
    text=generic_composed()[0]+'''r za[a] c.r zb[a h[b] c] c.r zc[] h[b] c.q[k sak[k zc[] p za p zb]].'''
    doc=parse(text)
    rows=[]
    for selected in product((False,True),repeat=2):
        for matches in product((False,True),repeat=4):
            actual=[]
            for value in (0,1):
                model={**ARITHMETIC,'za':lambda trial:selected[('first','second').index(trial)],
                    'zb':lambda trial,cut:matches[2*('first','second').index(trial)+int(cut(Fraction(0)))],
                    'zc':lambda:FunctionValue(('number',),'truth',lambda q:q<value)}
                observed=values(doc,model,('first','second'))[0]
                expected=any(selected) and all(not chosen or matches[2*i+value] for i,chosen in enumerate(selected))
                if observed!=expected: raise ValueError('Trial-local values confused with shared value')
                actual.append(observed)
            rows.append({'selected':list(selected),'matches':list(matches),'common_candidates':actual})
    return rows


def source_checks():
    doc=candidate(source_composed()[0],'''r za[] h[h[b] c h[b] c h[b] c h[b] c] c.
q[k sam[k tc[] k ri[] k za[]]].''')
    signature=next(d['result'] for d in doc['declarations'] if d['name']=='za')
    trials=('trialone','trialtwo')
    domain=(*trials,'clocka','clockb','clockc','placea','placeb','placec','departone','reflectone','arriveone','rayone',
        'departtwo','reflecttwo','arrivetwo','raytwo','frame','unit','lengthunit','speedunit','other')
    records={trial:('placea','placeb' if trial=='trialone' else 'placec',*(prefix+suffix for prefix in ('depart','reflect','arrive','ray')))
        for trial,suffix in zip(trials,('one','two'))}
    base={'selected':set(trials),'complete':True,'timeunit':'unit','lengthunit':'lengthunit','speedunit':'speedunit',
        'clocks':{'clocka','clockb','clockc'},'stationary':{('clocka','frame'),('clockb','frame'),('clockc','frame')},
        'locations':{('clocka','placea','frame'),('clockb','placeb','frame'),('clockc','placec','frame')},'propagation':set(),'vacuum':set(),
        'reflection':set(),'light':{'rayone','raytwo'},'distance':{'trialone':6,'trialtwo':3},
        'readings':{'trialone':(0,2,4),'trialtwo':(10,11,12)},'rate':3,'distance_matches':True,'same_construction':True}
    for trial,(pa,pb,depart,reflect,arrive,ray) in records.items():
        base['locations'].update({(depart,pa,'frame'),(reflect,pb,'frame'),(arrive,pa,'frame')})
        base['propagation'].update({(ray,depart,reflect,'frame'),(ray,reflect,arrive,'frame')})
        base['reflection'].add((ray,reflect,'frame'))
    base['vacuum']=set(base['propagation'])
    cases={'baseline':(base,True)}
    shifted=deepcopy(base); shifted['readings']['trialone']=(0,99,4)
    cases['reflection_clock_offset_does_not_change_roundtrip_rate']=(shifted,True)
    for name,key,value in (
        ('empty_trials','selected',set()),('incomplete_scope','complete',False),('wrong_time_unit','timeunit','other'),
        ('wrong_length_unit','lengthunit','other'),('wrong_speed_unit','speedunit','other'),
        ('wrong_value','rate',4),('wrong_distance_binding','distance_matches',False),
        ('different_clock_construction','same_construction',False)):
        changed=deepcopy(base); changed[key]=value; cases[name]=(changed,False)
    for name,key,item in (
        ('return_not_in_vacuum','vacuum',('rayone','reflectone','arriveone','frame')),
        ('outgoing_not_in_vacuum','vacuum',('rayone','departone','reflectone','frame')),
        ('missing_return_leg','propagation',('rayone','reflectone','arriveone','frame')),
        ('wrong_arrival_place','locations',('arriveone','placea','frame')),
        ('moving_departure_clock','stationary',('clocka','frame')),
        ('missing_reflection','reflection',('rayone','reflectone','frame')),
        ('not_light','light','rayone')):
        changed=deepcopy(base); changed[key].remove(item); cases[name]=(changed,False)
    changed=deepcopy(base); changed['distance']['trialtwo']=4
    cases['different_rates_across_trials']=(changed,False)
    for variant in ('return_read_on_other_clock','swapped_first_and_last','wrong_trial_distance','wrong_trial_return'):
        cases[variant]=(deepcopy(base),False)
    def cut(value):return FunctionValue(('number',),'truth',lambda q:q<value)
    def fingerprint(value):return tuple(value(Fraction(n)) for n in range(-1,101))
    fingerprints={fingerprint(cut(n)):n for n in range(100)}
    rows={}
    for name,(facts,expected) in cases.items():
        model=source_model(doc)
        model.update(ta=lambda:facts['lengthunit'],tb=lambda:facts['speedunit'],tc=lambda:cut(facts['rate']),
            rb=lambda:facts['timeunit'],tl=lambda frame,tu,lu,context:facts['complete'],
            td=lambda trial,frame,tu,lu,context:trial in facts['selected'] and (frame,tu,lu,context)==('frame','unit','lengthunit','text'),
            te=lambda trial:'clocka',tf=lambda trial:'clockb' if trial=='trialone' else 'clockc',tg=lambda trial:cut(facts['distance'].get('trialone' if name=='wrong_trial_distance' else trial,0)),
            ti=lambda unit:unit=='lengthunit',tj=lambda lu,tu,su:(lu,tu,su)==('lengthunit','unit','speedunit'),
            th=lambda pa,pb,frame,unit,distance:facts['distance_matches'] and (pa,frame,unit)==('placea','frame','lengthunit')
                and pb in ('placeb','placec') and fingerprint(distance)==fingerprint(cut(facts['distance']['trialone' if pb=='placeb' else 'trialtwo'])),
            tk=lambda *args:args in facts['vacuum'],ca=lambda c:c in facts['clocks'],cc=lambda *args:args in facts['stationary'],
            cb=lambda *args:args in facts['locations'],cd=lambda a,b:facts['same_construction'] and a=='clocka' and b in ('clockb','clockc'),
            cf=lambda ray:ray in facts['light'],cg=lambda *args:args in facts['propagation'],ch=lambda *args:args in facts['reflection'])
        for index,symbol in enumerate(('qc','qd','qe','qf','qg','qh')):
            model[symbol]=lambda trial,index=index: ('arrivetwo' if name=='wrong_trial_return' and index==4 and trial=='trialone'
                else records.get(trial,('other',)*6)[index])
        for index,symbol in enumerate(('qi','qj','qk')):
            model[symbol]=lambda trial,index=index:cut(facts['readings'].get(trial,(0,0,0))[(2-index if name=='swapped_first_and_last' else index)])
        def reading(clock,event,frame,unit,value):
            for trial,record in records.items():
                for i,evt in enumerate(record[2:5]):
                    remote_clock='clockb' if trial=='trialone' else 'clockc'
                    expected_clock=remote_clock if i==1 or (name=='return_read_on_other_clock' and i==2) else 'clocka'
                    if (clock,event,frame,unit)==(expected_clock,evt,'frame','unit'):
                        return fingerprint(value)==fingerprint(cut(facts['readings'][trial][i]))
            return False
        model['ce']=reading
        def criterion(distance,start,end,rate):
            numbers=[fingerprints.get(fingerprint(c)) for c in (distance,start,end,rate)]
            if any(n is None for n in numbers):return False
            d,a,b,v=numbers
            return d>0 and b>a and v>0 and v*(b-a)==2*d
        model['za']=lambda:FunctionValue(tuple(signature['parameters']),signature['result'],criterion)
        actual=values(doc,model,domain)[0]
        if actual!=expected:raise ValueError('Source roundtrip binding differs: '+name)
        rows[name]=actual
    return {'cases':rows,'criterion_is_injected_rational_fixture':True,'full_real_cut_law_evaluated':False,
        'probe_limit':'Only explicitly supplied integer embeddings in 0..99; not arbitrary real-cut equality.'}


def attribution_checks():
    doc=parse(source_composed()[0])
    previous=parse((ROOT/'examples/v014/einstein-event-time.noema').read_text(encoding='utf-8'))
    if doc['statements'][:-1]!=previous['statements']:raise ValueError('Prior assertions changed')
    doc['statements']=doc['statements'][-1:]
    rows={}
    for variant in ('baseline','no_adoption','no_experience_basis','wrong_content','wrong_author','wrong_scope','wrong_experience'):
        def forbidden(*args):raise ValueError('Physical law executed while only attributing its adoption')
        model={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
        model.update(tm=lambda:'law',rd=lambda:'author',tn=lambda:'experience',rh=lambda:'scope',ri=lambda:'text')
        model['ug']=lambda node,author,content,scope,context:variant!='no_adoption' and (node,author,json.loads(content.syntax)['symbol'],scope,context)==(
            'law','other' if variant=='wrong_author' else 'author','san' if variant=='wrong_content' else 'sao',
            'other' if variant=='wrong_scope' else 'scope','text')
        model['to']=lambda node,author,evidence,scope,context:variant!='no_experience_basis' and (node,author,evidence,scope,context)==(
            'law','author','other' if variant=='wrong_experience' else 'experience','scope','text')
        actual=values(doc,model,('law','author','experience','scope','other'))[0]
        if actual!=(variant=='baseline'):raise ValueError('Empirical adoption attribution differs')
        rows[variant]=actual
    return rows


def alignment():
    artifact=json.loads((ROOT/'artifacts/written-units-v1/einstein-1905.json').read_text(encoding='utf-8'))
    hashes={19:'00804cdefb656e2e6297aab9f3868b3aed836d823fb99a58b124fc0598b7eb33',
        20:'2fdaa0cdb5fb75402e26f485273bf58df66d752a26182052fe485d4ae0a220f3',
        21:'091ef6a862e075f2cfa94a0c7250950445f47f97817f48d5bdf4fe624099599b'}
    rows=[]
    for index in (19,20,21):
        unit=next(u for u in artifact['units'] if u['id']==f'einstein-1905:u{index:04d}')
        if hashlib.sha256(unit['text'].encode('utf-8')).hexdigest()!=hashes[index]:raise ValueError('Roundtrip source changed')
        row={'unit':unit['id'],'unit_sha256':hashes[index],'status':'partial_explicit_reading',
             'definitions':['sai','sal','sam','san','sao'],'full_semantic_equivalence':False}
        if index==20:
            math=next(m for m in artifact['math'] if m['id']=='M0040')
            if hashlib.sha256(math['mathml'].encode('utf-8')).hexdigest()!='540c2f8a99022e08a3073a57ed05c4ab6135c1f23baab7507f326695efe65593':raise ValueError('Roundtrip formula changed')
            row.update(math_id='M0040',math_sha256=math['sha256'])
        else:row.update(start=0,end=len(unit['text']),source=unit['text'])
        rows.append(row)
    return {'segments':rows,'verified_full_units':0}


def build_report():
    import z3
    documents={}
    for compose in (generic_composed,source_composed):
        text,basis=compose()
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text:raise ValueError('Stored rate differs')
        doc=parse(text)
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Rate roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis)
    files=[*documents,'data/roundtrip-speed-basis-v1.json','data/einstein-roundtrip-speed-basis-v1.json',
        'examples/v014/einstein-event-time.noema','examples/v011/real-products.noema',
        'scripts/compose_roundtrip_speed.py','scripts/check_roundtrip_speed.py',
        'noema/discourse.py','noema/finite_semantics.py','noema/polynomial_proofs.py']
    return {'status':'partial_roundtrip_rate_and_empirical_adoption','documents':documents,
        'numeric':numeric_checks(),'polynomial':polynomial_checks(),'constancy':constancy_checks(),
        'source_adapter':source_checks(),'attribution':attribution_checks(),'alignment':alignment(),
        'roundtrips':True,'general_real_cut_rate_law_machine_verified':False,'z3_version':z3.get_version_string(),
        'verified_full_units':{'einstein-1905':0,'kant-1784':0},
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in files}}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args()
    report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Roundtrip speed report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:
            json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Roundtrip numeric, unit, scope, physical-binding and empirical-adoption checks passed')


if __name__=='__main__':main()
