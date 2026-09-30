"""Check emitter independence, local clock bindings and scoped principle adoption."""
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
from scripts.check_real_products import MEANINGS, ZERO, ONE, TWO, assertion, call, conjunction, op
from scripts.check_roundtrip_speed import ARITHMETIC
from scripts.compose_emitted_light import ROOT, generic_composed, source_composed

REPORT=ROOT/'reports/emitted-light-v1.json'


def values(doc,model,domain):
    return [r['value'] for r in evaluate_document(doc,individuals=domain,situations=('text',),primitives=model,
        max_steps=3_000_000,memoize_definitions=True,memoize_expressions=True)]


def motion_checks():
    doc=parse(generic_composed()[0]+'''
r za[] a.r zb[] a.r zc[] a.r zd[] a.r ze[] d.
r zf[a] c.r zg[a a a a d] c.r zh[a a a d] c.r zi[a a a d] c.
q[k saz[k za[] k zb[] k zc[] k zd[] k ze[] p zf p zg p zh p zi]].''')
    rows=[]
    for body,emitted,resting,moving in product((False,True),repeat=4):
        model={**ARITHMETIC,'za':lambda:'ray','zb':lambda:'source','zc':lambda:'emission','zd':lambda:'frame','ze':lambda:'text',
            'zf':lambda source:body and source=='source',
            'zg':lambda *args:emitted and args==('ray','source','emission','frame','text'),
            'zh':lambda *args:resting and args==('source','frame','emission','text'),
            'zi':lambda *args:moving and args==('source','frame','emission','text')}
        actual=values(doc,model,('ray','source','emission','frame'))[0]
        if actual!=(body and emitted and resting!=moving):raise ValueError('Emitter motion classification differs')
        rows.append({'body':body,'emitted':emitted,'resting':resting,'moving':moving,'accepted':actual})
    return rows


def numeric_checks():
    cases={
        'baseline':((6,0,2,3,1,1,1),True),'common_origin_shift':((6,10,12,3,1,1,1),True),
        'length_unit_change':((600,0,2,3,Fraction(1,100),1,1),True),
        'time_unit_change':((6,0,200,3,1,Fraction(1,100),1),True),
        'speed_unit_change':((6,0,2,300,1,1,Fraction(1,100)),True),
        'unnecessary_roundtrip_factor':((6,0,2,6,1,1,1),False),
        'source_speed_added':((6,0,2,4,1,1,1),False),
        'mixed_clock_origins':((6,0,3,3,1,1,1),False),
        'zero_duration':((6,2,2,3,1,1,1),False),'reverse_duration':((6,2,0,3,1,1,1),False),
        'zero_path':((0,0,2,3,1,1,1),False),'zero_scale':((6,0,2,3,0,1,1),False)}
    def literal(x):
        value=Fraction(x)
        return 'n '+('u' if value<0 else 'p')+' '+number_word(abs(value.numerator))+' '+number_word(value.denominator)
    rows={}
    for name,(args,expected) in cases.items():
        doc=parse(generic_composed()[0]+'q['+call('say',*(literal(x) for x in args))+'].')
        actual=values(doc,ARITHMETIC,('object',))[0]
        if actual!=expected:raise ValueError('One-way arithmetic differs: '+name)
        rows[name]=actual
    return rows


def polynomial_checks():
    text=generic_composed()[0]
    d,a,b,v,ls,ts,vs,k,new=('v '+n for n in ('d','a','b','v','ls','ts','vs','k','new'))
    mul=lambda x,y:call('ad',x,y)
    add=lambda x,y:call('ab',x,y)
    pos=lambda x:call('aa',ZERO,x)
    rate=lambda *args:call('say',*args)
    base=rate(d,a,b,v,ls,ts,vs)
    claims={
        'same_origin_shift':assertion('d a b v ls ts vs k',op('z',base,rate(d,add(a,k),add(b,k),v,ls,ts,vs))),
        'unique_speed':assertion('d a b v ls ts vs new',op('y',conjunction(base,rate(d,a,b,new,ls,ts,vs)),op('e',v,new))),
        'roundtrip_uses_twice_one_way_distance':assertion('d a b v ls ts vs',op('z',call('saj',d,a,b,v,ls,ts,vs),rate(mul(TWO,d),a,b,v,ls,ts,vs))),
        'path_unit_compensation':assertion('d a b v ls ts vs k new',op('y',conjunction(pos(ls),pos(k),op('e',mul(k,new),mul(ls,d))),op('z',base,rate(new,a,b,v,k,ts,vs)))),
        'clock_unit_compensation':assertion('d a b v ls ts vs k new',op('y',conjunction(pos(k),pos(new),op('e',mul(k,new),ts)),op('z',base,rate(d,mul(k,a),mul(k,b),v,ls,new,vs)))),
        'speed_unit_compensation':assertion('d a b v ls ts vs k new',op('y',conjunction(pos(vs),pos(k),op('e',mul(k,new),mul(vs,v))),op('z',base,rate(d,a,b,new,ls,ts,k)))),
        'source_speed_can_be_added':assertion('d a b v ls ts vs k',op('y',base,rate(d,a,b,add(v,k),ls,ts,vs))),
    }
    rows={}
    for name,claim in claims.items():
        result=verify_universal(parse(text+claim),MEANINGS,timeout_ms=15000)[0]
        if result['status']!=('invalid' if name=='source_speed_can_be_added' else 'valid'):
            raise ValueError('One-way polynomial check differs: '+name)
        rows[name]=result
    return rows


def cut(number):return FunctionValue(('number',),'truth',lambda q:q<number)


def fingerprint(value):return tuple(value(Fraction(q)) for q in range(-1,14))


def source_checks():
    doc=candidate(source_composed()[0],'''
r za[] h[a a a a d] c.r zb[] h[h[b] c h[b] c h[b] c h[b] c] c.
q[k sbb[k tc[] k ri[] k za[] k zb[]]].''')
    signatures={d['name']:d['result'] for d in doc['declarations'] if d['name'] in ('za','zb')}
    # ray, source, emission, first, last, firstclock, lastclock, firstplace, lastplace, firsttime, lasttime, path
    records={
        'whole':('rayone','restsource','depart','depart','arrive','clocka','clockb','placea','placeb',0,2,6),
        'part':('rayone','restsource','depart','middle','arrive','clockc','clockb','placec','placeb',1,2,3),
        'moving':('raytwo','movesource','emit','emit','receive','clockd','clocke','placed','placee',10,11,3)}
    domain=tuple(dict.fromkeys((*records,*(x for row in records.values() for x in row[:9]),
        'reference','frame','timeunit','lengthunit','speedunit','other')))
    base={'records':records,'selected':set(records),'complete':True,'reference':'reference','speed':3,
        'rest':{('restsource','frame','depart','text')},'moving':{('movesource','frame','emit','text')},
        'clocks':{'clocka','clockb','clockc','clockd','clocke','reference'},'propagation':set(),
        'vacuum':set(),'locations':set(),'stationary':set(),'emissions':set(), 'reads':{}}
    for ray,source,emission,first,last,ca,cb,pa,pb,start,end,path in records.values():
        base['emissions'].add((ray,source,emission,'frame','text'))
        base['propagation'].add((ray,first,last,'frame'))
        if first!=emission:base['propagation'].add((ray,emission,first,'frame'))
        base['vacuum'].add((ray,first,last,'frame'))
        base['locations'].update({(ca,pa,'frame'),(cb,pb,'frame'),(first,pa,'frame'),(last,pb,'frame')})
        base['reads'][ca,first,'frame','timeunit']=start
        base['reads'][cb,last,'frame','timeunit']=end
    base['stationary']={(clock,'frame') for clock in base['clocks']}
    cases={'both_emitter_states_and_subsegment':(base,True)}
    changed=deepcopy(base)
    changed['rest'].remove(('restsource','frame','depart','text'))
    changed['moving'].add(('restsource','frame','depart','text'))
    cases['only_emitter_motion_class_changes']=(changed,True)
    changed=deepcopy(base);changed['selected']={'whole','part'}
    cases['no_claim_that_both_emitter_states_exist']=(changed,True)
    for name,key,value in (
        ('empty_segments','selected',set()),('incomplete_scope','complete',False),('wrong_common_reference','reference','clocka'),
        ('wrong_common_speed','speed',4),('missing_emission','emissions',set()),('unknown_motion','moving',set())):
        changed=deepcopy(base);changed[key]=value;cases[name]=(changed,False)
    changed=deepcopy(base);changed['rest'].add(('movesource','frame','emit','text'))
    cases['contradictory_motion']=(changed,False)
    changed=deepcopy(base);changed['moving']={('movesource','frame','receive','text')}
    cases['motion_at_wrong_event']=(changed,False)
    for name,key,item in (
        ('missing_subsegment_origin','propagation',('rayone','depart','middle','frame')),
        ('missing_propagation','propagation',('raytwo','emit','receive','frame')),
        ('nonvacuum_segment','vacuum',('raytwo','emit','receive','frame')),
        ('moving_measurement_clock','stationary',('clocke','frame')),
        ('endpoint_clock_remote','locations',('clocke','placee','frame')),
        ('endpoint_event_remote','locations',('receive','placee','frame'))):
        changed=deepcopy(base);changed[key].remove(item);cases[name]=(changed,False)
    changed=deepcopy(base);changed['reads']['clocke','receive','frame','timeunit']=12
    cases['wrong_endpoint_read']=(changed,False)
    changed=deepcopy(base);changed['records']['moving']=(*changed['records']['moving'][:-1],4)
    cases['moving_source_produces_different_speed']=(changed,False)
    changed=deepcopy(base);changed['records']['part']=(*changed['records']['part'][:-1],4)
    cases['whole_path_agrees_but_subsegment_disagrees']=(changed,False)
    for variant in ('wrong_emitter','wrong_ray','wrong_length_unit','wrong_speed_unit','wrong_time_unit',
                    'unsynced_endpoint','wrong_path_binding','foreign_context_scope'):
        cases[variant]=(deepcopy(base),False)
    rows={}
    fingerprints={fingerprint(cut(n)):n for n in range(13)}
    for name,(facts,expected) in cases.items():
        def forbidden(*args):raise ValueError('Full real-cut physical semantics were unexpectedly evaluated')
        model={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
        model.update(ra=lambda:'frame',rb=lambda:'other' if name=='wrong_time_unit' else 'timeunit',
            rc=lambda:facts['reference'],ri=lambda:'text',ta=lambda:'other' if name=='wrong_length_unit' else 'lengthunit',
            tb=lambda:'other' if name=='wrong_speed_unit' else 'speedunit',tc=lambda:cut(facts['speed']),
            ws=lambda frame,tu,lu,context:facts['complete'],
            wa=lambda segment,frame,tu,lu,context:segment in facts['selected'] and (frame,tu,lu,context)==(
                'frame','timeunit','lengthunit','other' if name=='foreign_context_scope' else 'text'),
            wb=lambda body:body in ('restsource','movesource'),wc=lambda *args:args in facts['emissions'],
            wd=lambda *args:args in facts['rest'],we=lambda *args:args in facts['moving'],
            cf=lambda ray:ray in ('rayone','raytwo'),cg=lambda *args:args in facts['propagation'],tk=lambda *args:args in facts['vacuum'],
            ca=lambda clock:clock in facts['clocks'],cb=lambda *args:args in facts['locations'],cc=lambda *args:args in facts['stationary'],
            ci=lambda unit:unit=='timeunit',ti=lambda unit:unit=='lengthunit',tj=lambda lu,tu,su:(lu,tu,su)==('lengthunit','timeunit','speedunit'))
        for index,symbol in enumerate(('wf','wg','wh','wi','wj','wk','wl','wm','wn')):
            model[symbol]=lambda segment,index=index:('movesource' if name=='wrong_emitter' and index==1 else
                'raytwo' if name=='wrong_ray' and index==0 else facts['records'].get(segment,('other',)*9)[index])
        for index,symbol in enumerate(('wo','wp','wq'),start=9):
            model[symbol]=lambda segment,index=index:cut(facts['records'][segment][index] if segment in facts['records'] else 0)
        def reading(clock,event,frame,unit,value):
            number=facts['reads'].get((clock,event,frame,unit))
            return number is not None and fingerprint(value)==fingerprint(cut(number))
        model['ce']=reading
        def path_length(segment,ray,start,end,frame,unit,value,context):
            row=facts['records'].get(segment)
            return row is not None and name!='wrong_path_binding' and (ray,start,end,frame,unit,context)==(
                row[0],row[3],row[4],'frame','lengthunit','text') and fingerprint(value)==fingerprint(cut(row[11]))
        model['wr']=path_length
        def synchrony(clock,reference,frame,unit,context):
            return clock in facts['clocks'] and (reference,frame,unit,context)==('reference','frame','timeunit','text') and not(
                name=='unsynced_endpoint' and clock=='clocke')
        def rate(path,start,end,speed):
            numbers=[fingerprints.get(fingerprint(value)) for value in (path,start,end,speed)]
            if any(n is None for n in numbers):return False
            length,first,last,value=numbers
            return length>0 and last>first and value>0 and value*(last-first)==length
        model['za']=lambda:FunctionValue(tuple(signatures['za']['parameters']),signatures['za']['result'],synchrony)
        model['zb']=lambda:FunctionValue(tuple(signatures['zb']['parameters']),signatures['zb']['result'],rate)
        actual=values(doc,model,domain)[0]
        if actual!=expected:raise ValueError('Emitted-light source binding differs: '+name)
        rows[name]=actual
    return {'cases':rows,'supplied_synchrony_and_rational_rate_oracles':True,'full_real_cut_physics_evaluated':False,
        'probe_scope':'Only the explicit integer embeddings 0..12 in this fixture; not arbitrary real-cut equality.'}


def attribution_checks():
    doc=parse(source_composed()[0])
    old=parse((ROOT/'examples/v014/einstein-law-invariance.noema').read_text(encoding='utf-8'))
    if doc['statements'][:-2]!=old['statements']:raise ValueError('Previous statements changed')
    doc['statements']=doc['statements'][-2:]
    rows={}
    for variant in ('baseline','wrong_definition','missing_first_principle','missing_second_principle',
                    'wrong_following_scope','wrong_author','wrong_context'):
        def forbidden(*args):raise ValueError('Physical principle was evaluated during attribution')
        model={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
        model.update(wt=lambda:'definition',wu=lambda:'introduction',wv=lambda:'following',rd=lambda:'author',rh=lambda:'scope',ri=lambda:'text')
        model['vl']=lambda node,author,content,scope,context:(node,author,json.loads(content.syntax)['symbol'],scope,context)==(
            'definition','author','saw' if variant=='wrong_definition' else 'sbd','scope','text')
        def adopted(node,author,content,scope,context):
            name=json.loads(content.syntax)['symbol']
            return (node,author,scope,context)==('introduction','other' if variant=='wrong_author' else 'author',
                'scope' if variant=='wrong_following_scope' else 'following','other' if variant=='wrong_context' else 'text') and name in (
                    {'sbd'} if variant=='missing_first_principle' else {'saw'} if variant=='missing_second_principle' else {'saw','sbd'})
        model['ug']=adopted
        actual=values(doc,model,('definition','introduction','following','author','scope','other'))
        expected=[variant!='wrong_definition',variant not in ('missing_first_principle','missing_second_principle','wrong_following_scope','wrong_author','wrong_context')]
        if actual!=expected:raise ValueError('Two-principle attribution differs')
        rows[variant]=actual
    return rows


def alignment():
    artifact=json.loads((ROOT/'artifacts/written-units-v1/einstein-1905.json').read_text(encoding='utf-8'))
    hashes={24:'259ed66553491289a51c6b9407d38d11c0c9bce56e97b500158518a157730d00',
        26:'229be1fbad0cd8ce2fddbd73e0dc71424c9ff6a0d96dcd0cef23f16e8f1f85f7',
        27:'b696e06cb39f485ca0fcf4f2662bbcd65f185a857f2f3cd703dee86d873043b4',
        28:'346149c0fdfc91b3b96f6693f9ace0ece6bc56c4fbb023856581e34516a549c4'}
    math_hashes={'M0041':'fad146c158bc7dc725209b362adcee4dfb08d7da13a15bf61ab90897102da806',
        'M0042':'5b9efd0af2b9888458899f242088025a511f8d036eafe22f9b00f0ee03d75930'}
    rows=[]
    for number in hashes:
        unit=next(u for u in artifact['units'] if u['id']==f'einstein-1905:u{number:04d}')
        if hashlib.sha256(unit['text'].encode('utf-8')).hexdigest()!=hashes[number]:raise ValueError('Emitted-light source differs')
        rows.append({'unit':unit['id'],'unit_sha256':hashes[number],'start':0,'end':len(unit['text']),
            'source':unit['text'],'definitions':['sax','sba','sbb','sbc','sbd'],
            'status':'partial_explicit_reading','full_semantic_equivalence':False})
        for identifier in unit['math_ids']:
            math=next(m for m in artifact['math'] if m['id']==identifier)
            if hashlib.sha256(math['mathml'].encode('utf-8')).hexdigest()!=math_hashes[identifier]:raise ValueError('Emitted-light math differs')
            rows.append({'unit':unit['id'],'unit_sha256':hashes[number],'math_id':identifier,'math_sha256':math_hashes[identifier],
                'definitions':['sax','sbc'],'status':'partial','full_semantic_equivalence':False})
    return {'segments':rows,'verified_full_units':0}


def build_report():
    import z3
    documents={}
    for compose in (generic_composed,source_composed):
        text,basis=compose()
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text:raise ValueError('Stored emitted-light document differs')
        doc=parse(text)
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Emitted-light roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis)
    files=[*documents,'data/emitted-light-basis-v1.json','data/einstein-emitted-light-basis-v1.json',
        'examples/v014/einstein-law-invariance.noema','scripts/compose_emitted_light.py','scripts/check_emitted_light.py',
        'noema/discourse.py','noema/finite_semantics.py','noema/polynomial_proofs.py']
    return {'status':'partial_emitter_independence_and_synchronized_path_time','documents':documents,
        'motion':motion_checks(),'numeric':numeric_checks(),'polynomial':polynomial_checks(),
        'source_adapter':source_checks(),'attribution':attribution_checks(),'alignment':alignment(),
        'roundtrips':True,'z3_version':z3.get_version_string(),
        'general_real_cut_physical_law_verified':False,'verified_full_units':{'einstein-1905':0,'kant-1784':0},
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in files}}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args()
    report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Emitted-light report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:
            json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Emission, one-way rates, synchronized endpoint bindings and two-principle adoption checked')


if __name__=='__main__':main()
