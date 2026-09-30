"""Check two measurement settings without equating their length candidates."""
import argparse
from copy import deepcopy
from fractions import Fraction
import hashlib
from itertools import product
import json

from noema.finite_semantics import FunctionValue, evaluate_document
from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_described_appraisals import candidate
from scripts.check_described_explanations import symbol
from scripts.compose_rod_measurements import ROOT, generic_composed, source_composed

REPORT=ROOT/'reports/rod-measurements-v1.json'
ARITHMETIC={'aa':lambda a,b:a<b,'ab':lambda a,b:a+b,'ac':lambda a:-a,'ad':lambda a,b:a*b}


def values(doc,model,domain,scenes=('direct','slice','text')):
    return [r['value'] for r in evaluate_document(doc,individuals=domain,situations=scenes,primitives=model,
        max_steps=2_000_000,memoize_definitions=True,memoize_expressions=True)]


def cut(n):return FunctionValue(('number',),'truth',lambda q:q<n)


def fingerprint(value):return tuple(value(Fraction(q)) for q in range(-1,13))


def direct_checks():
    doc=parse(generic_composed()[0]+'''
r ya[] a.r yb[] a.r yc[] a.r yd[] a.r ye[] a.r yf[] h[b] c.r yg[] d.
r za[a] c.r zb[a] c.r zc[a] c.r zd[a a d] c.r ze[a a a d] c.r zf[a a a a a h[b] c d] c.
q[k sbe[k ya[] k yb[] k yc[] k yd[] k ye[] k yf[] k yg[] p za p zb p zc p zd p ze p zf]].''')
    rows=[]
    for bits in product((False,True),repeat=8):
        body,observer,ruler,bodyrest,observerrest,rulerrest,aligned,read=bits
        model={**ARITHMETIC,'ya':lambda:'rod','yb':lambda:'observer','yc':lambda:'ruler','yd':lambda:'frame',
            'ye':lambda:'unit','yf':lambda:cut(5),'yg':lambda:'direct',
            'za':lambda x:body and x=='rod','zb':lambda x:observer and x=='observer','zc':lambda x:ruler and x=='ruler',
            'zd':lambda obj,frame,context:(frame,context)==('frame','direct') and
                {'rod':bodyrest,'observer':observerrest,'ruler':rulerrest}.get(obj,False),
            'ze':lambda *args:aligned and args==('ruler','rod','frame','direct'),
            'zf':lambda who,ruler,obj,frame,unit,value,context:read and
                (who,ruler,obj,frame,unit,context)==('observer','ruler','rod','frame','unit','direct') and fingerprint(value)==fingerprint(cut(5))}
        actual=values(doc,model,('rod','observer','ruler','frame','unit'))[0]
        if actual!=all(bits):raise ValueError('Direct-measurement role or stationarity condition differs')
        rows.append({'conditions':list(bits),'accepted':actual})
    return rows


def source_checks():
    doc=candidate(source_composed()[0],'''
r ya[] d.r yb[] d.r yc[] h[b] c.r yd[] h[b] c.
r ye[] h[h[b] c] c.r yf[] h[a a a a d] c.r yg[] h[h[b] c h[b] c] c.
q[k sbh[k yc[] k ya[] k ye[]]].
q[k sbj[k yd[] k yb[] k yf[] k ye[] k yg[]]].''')
    signatures={d['name']:d['result'] for d in doc['declarations'] if d['name'] in ('ye','yf','yg')}
    domain=('rod','otherrod','ruler','otherruler','observer','restframe','moveframe','reference',
        'endone','endtwo','eventone','eventtwo','clockone','clocktwo','placeone','placetwo','lengthunit','timeunit','other')
    base={'ruler':'ruler','secondend':'endtwo','firstclock':'clockone','secondclock':'clocktwo',
        'reference':'reference','directframe':'moveframe','directvalue':5,'slicevalue':4,'distance':4,
        'firsttime':10,'lasttime':10,'targettime':10,'firstread':10,'lastread':10,
        'stationary':{('rod','moveframe','direct'),('observer','moveframe','direct'),('ruler','moveframe','direct'),('ruler','restframe','slice')},
        'clocksrest':{('clockone','restframe'),('clocktwo','restframe'),('reference','restframe')},
        'ends':{('endone','rod','restframe','slice'),('endtwo','rod','restframe','slice')},
        'positions':{('endone','eventone','placeone','restframe','slice'),('endtwo','eventtwo','placetwo','restframe','slice')},
        'clocklocations':{('clockone','placeone','restframe'),('clocktwo','placetwo','restframe'),
                          ('eventone','placeone','restframe'),('eventtwo','placetwo','restframe')},
        'moving':{('rod','restframe','direct'),('rod','restframe','slice')},'alignment':True,'direct_read':True,'distance_read':True}
    cases={'different_values_in_distinct_settings':(base,[True,True])}
    same=deepcopy(base);same.update(slicevalue=5,distance=5)
    cases['equal_values_are_not_forbidden']=(same,[True,True])
    moving=deepcopy(base);moving['moving'].add(('observer','restframe','slice'))
    cases['observer_may_move_in_method_b']=(moving,[True,True])
    for name,key,item,expected in (
        ('rod_not_comoving','stationary',('rod','moveframe','direct'),[False,True]),
        ('observer_not_comoving','stationary',('observer','moveframe','direct'),[False,True]),
        ('ruler_not_comoving','stationary',('ruler','moveframe','direct'),[False,True]),
        ('ruler_not_resting_in_method_b','stationary',('ruler','restframe','slice'),[True,False]),
        ('moving_endpoint_clock','clocksrest',('clocktwo','restframe'),[True,False]),
        ('endpoint_not_on_rod','ends',('endtwo','rod','restframe','slice'),[True,False]),
        ('endpoint_at_wrong_event','positions',('endtwo','eventtwo','placetwo','restframe','slice'),[True,False]),
        ('clock_at_wrong_place','clocklocations',('clocktwo','placetwo','restframe'),[True,False]),
        ('motion_missing_for_a','moving',('rod','restframe','direct'),[False,True])):
        changed=deepcopy(base);changed[key].remove(item);cases[name]=(changed,expected)
    for name,key,value,expected in (
        ('different_ruler','ruler','otherruler',[False,False]),('same_endpoint_twice','secondend','endone',[True,False]),
        ('wrong_reference','reference','clockone',[True,False]),('wrong_first_clock','firstclock','clocktwo',[True,False]),
        ('wrong_direct_frame','directframe','restframe',[False,True]),('missing_alignment','alignment',False,[False,True]),
        ('missing_direct_read','direct_read',False,[False,True]),('missing_distance_read','distance_read',False,[True,False]),
        ('wrong_distance_candidate','slicevalue',5,[True,False]),('zero_length','slicevalue',0,[True,False])):
        changed=deepcopy(base);changed[key]=value;cases[name]=(changed,expected)
    changed=deepcopy(base);changed.update(lasttime=11,lastread=11)
    cases['different_endpoint_times']=(changed,[True,False])
    changed=deepcopy(base);changed.update(firsttime=11,lasttime=11,firstread=11,lastread=11)
    cases['equal_times_but_not_the_specified_time']=(changed,[True,False])
    for name in ('mix_measurement_contexts','unsynced_second_clock','wrong_length_unit'):
        cases[name]=(deepcopy(base),[False,False] if name in ('mix_measurement_contexts','wrong_length_unit') else [True,False])
    numbers={fingerprint(cut(n)):n for n in range(13)}
    rows={}
    for name,(facts,expected) in cases.items():
        def forbidden(*args):raise ValueError('Full real-cut conditions unexpectedly evaluated')
        model={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
        constants={'ra':'restframe','rb':'timeunit','rc':facts['reference'],'ta':'other' if name=='wrong_length_unit' else 'lengthunit',
            'xi':'rod','xj':facts['ruler'],'xk':'observer','xl':facts['directframe'],'xn':'endone','xo':facts['secondend'],
            'xp':'eventone','xq':'eventtwo','xr':facts['firstclock'],'xs':facts['secondclock'],'xt':'placeone','xu':'placetwo',
            'ya':'slice' if name=='mix_measurement_contexts' else 'direct','yb':'direct' if name=='mix_measurement_contexts' else 'slice'}
        for key,value in constants.items():model[key]=lambda value=value:value
        for key,value in {'x2':facts['firsttime'],'x3':facts['lasttime'],'xv':facts['targettime'],'yc':facts['directvalue'],'yd':facts['slicevalue']}.items():
            model[key]=lambda value=value:cut(value)
        model.update(xa=lambda x:x=='rod',xb=lambda x:x=='observer',xc=lambda x:x in ('ruler','otherruler'),
            va=lambda frame:frame in ('restframe','moveframe'),
            vb=lambda *args:args==('restframe','moveframe','direct'),vc=lambda *args:args==('restframe','moveframe','direct'),
            xm=lambda *args:args in facts['moving'],x4=lambda *args:args in facts['stationary'],
            xd=lambda *args:facts['alignment'] and args==('ruler','rod','moveframe','direct'),
            xe=lambda obs,ruler,rod,frame,unit,value,context:facts['direct_read'] and
                (obs,ruler,rod,frame,unit,context)==('observer','ruler','rod','moveframe','lengthunit','direct') and fingerprint(value)==fingerprint(cut(5)),
            xf=lambda *args:args in facts['ends'],xg=lambda *args:args in facts['positions'],
            ca=lambda clock:clock in ('clockone','clocktwo','reference'),cc=lambda *args:args in facts['clocksrest'],
            cb=lambda *args:args in facts['clocklocations'],ci=lambda unit:unit=='timeunit',ti=lambda unit:unit=='lengthunit',
            th=lambda a,b,frame,unit,value:(a,b,frame,unit)==('placeone','placetwo','restframe','lengthunit') and fingerprint(value)==fingerprint(cut(facts['distance'])),
            xh=lambda obs,ruler,a,b,frame,unit,value,context:facts['distance_read'] and
                (obs,ruler,a,b,frame,unit,context)==('observer','ruler','placeone','placetwo','restframe','lengthunit','slice') and fingerprint(value)==fingerprint(cut(facts['distance'])))
        def reading(clock,event,frame,unit,value):
            expected_read={('clockone','eventone','restframe','timeunit'):facts['firstread'],
                           ('clocktwo','eventtwo','restframe','timeunit'):facts['lastread']}.get((clock,event,frame,unit))
            return expected_read is not None and fingerprint(value)==fingerprint(cut(expected_read))
        model['ce']=reading
        callbacks={
            'ye':lambda value:numbers.get(fingerprint(value),0)>0,
            'yf':lambda clock,ref,frame,unit,context:clock in ('clockone','clocktwo') and
                (ref,frame,unit,context)==('reference','restframe','timeunit','slice') and not(name=='unsynced_second_clock' and clock=='clocktwo'),
            'yg':lambda first,last:fingerprint(first)==fingerprint(last)}
        for key,callback in callbacks.items():
            model[key]=lambda key=key,callback=callback:FunctionValue(tuple(signatures[key]['parameters']),signatures[key]['result'],callback)
        actual=values(doc,model,domain)
        if actual!=expected:raise ValueError('Rod measurement setting differs: '+name+' '+repr(actual))
        rows[name]=actual
    return {'cases':rows,'direct_candidate':5,'endpoint_candidate':4,
        'supplied_synchrony_positive_length_and_equality_oracles':True,'full_real_cut_physics_evaluated':False,
        'probe_scope':'Only the supplied integer embeddings 0..12; not arbitrary real-cut equality.',
        'lorentz_contraction_relation_derived':False}


def attribution_checks():
    doc=parse(source_composed()[0])
    previous=parse((ROOT/'examples/v014/einstein-emitted-light.noema').read_text(encoding='utf-8'))
    if doc['statements'][:-2]!=previous['statements']:raise ValueError('Previous source statements changed')
    doc['statements']=doc['statements'][-2:]
    rows={}
    for variant in ('baseline','swapped_methods','missing_first','missing_second','wrong_scope','wrong_author'):
        def forbidden(*args):raise ValueError('Measurement content executed during attribution')
        model={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
        model.update(xw=lambda:'methoda',xx=lambda:'methodb',rd=lambda:'author',xy=lambda:'thought',ri=lambda:'text')
        def described(node,author,method,scope,context):
            pairs={('methoda','sbk' if variant=='swapped_methods' else 'sbi'),('methodb','sbi' if variant=='swapped_methods' else 'sbk')}
            return (node,symbol(method)) in pairs and (author,scope,context)==(
                'other' if variant=='wrong_author' else 'author','other' if variant=='wrong_scope' else 'thought','text') and not(
                    variant=='missing_first' and node=='methoda' or variant=='missing_second' and node=='methodb')
        model['xz']=described
        actual=values(doc,model,('methoda','methodb','author','thought','other'))
        expected=([True,True] if variant=='baseline' else [False,True] if variant=='missing_first' else [True,False] if variant=='missing_second' else [False,False])
        if actual!=expected:raise ValueError('Measurement-method attribution differs')
        rows[variant]=actual
    return rows


def alignment():
    artifact=json.loads((ROOT/'artifacts/written-units-v1/einstein-1905.json').read_text(encoding='utf-8'))
    hashes={30:'2b7229adb80dffd30b97d8cc300e3f744ae18be2ca827091d6cec17fa43c5aab',
        31:'73c00c97caeacda681d9ed3325ee353dcdf0e44dd86760bfa8f31e2b73986c24'}
    rows=[]
    for number,digest in hashes.items():
        unit=next(u for u in artifact['units'] if u['id']==f'einstein-1905:u{number:04d}')
        if hashlib.sha256(unit['text'].encode('utf-8')).hexdigest()!=digest:raise ValueError('Rod source changed')
        rows.append({'unit':unit['id'],'unit_sha256':digest,'start':0,'end':len(unit['text']),
            'source':unit['text'],'definitions':['sbe','sbf','sbh','sbi','sbj','sbk'],
            'status':'partial_explicit_reading','full_semantic_equivalence':False})
        if number==31:
            math=next(m for m in artifact['math'] if m['id']=='M0048')
            expected='5d313ada269dfc2378f1e53604207c23be5b19c12a7415b78f9838fcdfea5eef'
            if hashlib.sha256(math['mathml'].encode('utf-8')).hexdigest()!=expected:raise ValueError('Specified time symbol changed')
            rows.append({'unit':unit['id'],'unit_sha256':digest,'math_id':'M0048','math_sha256':expected,
                'definitions':['sbj','sbk'],'status':'partial','full_semantic_equivalence':False})
    return {'segments':rows,'verified_full_units':0}


def build_report():
    documents={}
    for compose in (generic_composed,source_composed):
        text,basis=compose()
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text:raise ValueError('Stored rod measurement differs')
        doc=parse(text)
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Rod measurement roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis)
    paths=[*documents,'data/rod-measurements-basis-v1.json','data/einstein-rod-measurements-basis-v1.json',
        'examples/v014/einstein-emitted-light.noema','scripts/compose_rod_measurements.py','scripts/check_rod_measurements.py',
        'noema/discourse.py','noema/finite_semantics.py']
    return {'status':'partial_distinct_rod_measurement_operations','documents':documents,
        'direct_conditions':direct_checks(),'source_adapter':source_checks(),'attribution':attribution_checks(),
        'alignment':alignment(),'roundtrips':True,'verified_full_units':{'einstein-1905':0,'kant-1784':0},
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args()
    report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Rod measurement report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:
            json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Direct measurement conditions, distinct settings, simultaneous endpoints and method attributions checked')


if __name__=='__main__':main()
