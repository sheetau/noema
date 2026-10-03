"""Verify catch-up equations and their event/clock/observer bindings."""
import argparse
from fractions import Fraction
import hashlib
import json

from noema.finite_semantics import evaluate_document
from noema.grammar import parse, format_graph, number_word
from noema.meaning_basis import audit_basis
from noema.polynomial_proofs import verify_universal
from noema.script import encode, decode
from scripts.check_described_appraisals import candidate
from scripts.check_real_products import MEANINGS, ZERO, call, op, conjunction, assertion
from scripts.check_rod_comparison import callbacks, guarded
from scripts.check_rod_measurements import ARITHMETIC, cut, fingerprint
from scripts.compose_moving_light_trip import ROOT, generic_composed, source_composed

REPORT=ROOT/'reports/moving-light-trip-v1.json'


def values(doc,model,domain):
    return [r['value'] for r in evaluate_document(doc,individuals=domain,situations=('motion','slice','text','other'),
        primitives=model,max_steps=2_000_000,memoize_definitions=True,memoize_expressions=True)]


def literal(x):
    x=Fraction(x)
    return 'n '+('u' if x<0 else 'p')+' '+number_word(abs(x.numerator))+' '+number_word(x.denominator)


def numeric_checks():
    cases={
        'moving':((8,3,1,2,6,8),True),
        'fractional_times':((6,3,1,0,3,Fraction(9,2)),True),
        'stationary_limit':((6,3,0,0,2,4),True),
        'shifted_time_origin':((8,3,1,-10,-6,-4),True),
        'wrong_midpoint_assumption':((8,3,1,2,6,10),False),
        'reversed_denominators':((8,3,1,2,4,8),False),
        'initial_length_substituted':((10,3,1,2,6,8),False),
        'zero_length':((0,3,1,2,6,8),False),
        'zero_duration':((8,3,1,2,2,8),False),
        'light_speed_boundary':((8,3,3,2,6,8),False),
        'above_light_speed':((8,3,4,2,6,8),False),
        'negative_rod_speed':((8,3,-1,2,6,8),False),
    }
    rows={}
    for name,(args,expected) in cases.items():
        doc=parse(generic_composed()[0]+'q['+call('sda',*(literal(x) for x in args))+'].q['+call('sdd',*(literal(x) for x in args[-3:]))+'].')
        actual=values(doc,ARITHMETIC,('object',))
        if actual[0]!=expected:raise ValueError('Moving light numeric condition differs: '+name)
        rows[name]={'travel_relation':actual[0],'midpoint':actual[1]}
    return rows


def polynomial_checks():
    r,V,v,a,b,c,x,k=('v '+n for n in ('r','light','speed','a','b','c','origin','shift'))
    add=lambda p,q:call('ab',p,q)
    sub=lambda p,q:add(p,call('ac',q))
    mul=lambda p,q:call('ad',p,q)
    base=call('sda',r,V,v,a,b,c)
    claims={
        'intersection_equations_equal_travel_equations':assertion('r light speed a b c origin',op('z',call('sdc',x,r,V,v,a,b,c),base)),
        'positive_motion_outward_leg_longer':assertion('r light speed a b c',op('y',conjunction(base,call('aa',ZERO,v)),call('aa',sub(c,b),sub(b,a)))),
        'midpoint_exactly_at_zero_speed':assertion('r light speed a b c',op('y',base,op('z',call('sdd',a,b,c),op('e',v,ZERO)))),
        'common_time_origin_shift':assertion('r light speed a b c shift',op('z',base,call('sda',r,V,v,add(a,k),add(b,k),add(c,k)))),
        'common_length_and_speed_scale':assertion('r light speed a b c shift',op('y',call('aa',ZERO,k),op('z',base,call('sda',mul(k,r),mul(k,V),mul(k,v),a,b,c)))),
        'moving_clocks_always_pass_midpoint':assertion('r light speed a b c',op('y',base,call('sdd',a,b,c))),
    }
    rows={}
    for name,claim in claims.items():
        result=verify_universal(parse(generic_composed()[0]+claim),MEANINGS,timeout_ms=15000)[0]
        expected='invalid' if name=='moving_clocks_always_pass_midpoint' else 'valid'
        if result['status']!=expected:raise ValueError('Catch-up algebra differs: '+name)
        rows[name]=result
    return rows


def source_checks():
    doc=candidate(source_composed()[0],'''
r ja[] d.r jb[] h[a a a a d] c.r jc[] h[h[b] c h[b] c] c.r jd[] h[h[b] c] c.
r je[] h[h[b] c d] c.r jf[] h[h[b] c h[b] c h[b] c h[b] c h[b] c h[b] c] c.
q[k sdg[k ja[] k jb[] k jc[] k jd[]]].q[k sdi[k ja[] k je[] k jf[]]].''')
    domain=('rod','ca','cb','enda','endb','r1','r2','r3','e1','e2','e3','p1','p2','p3','l1','l2','l3',
        'reference','frame','timeunit','lengthunit','speedunit','ray','trial','observera','observerb','other')
    records={'r1':('ca','enda','e1','p1','l1',2),'r2':('cb','endb','e2','p2','l2',6),'r3':('ca','enda','e3','p3','l3',8)}
    numeric={fingerprint(cut(i)):i for i in range(13)}
    cases=('baseline','missing_outward_leg','missing_return_leg','wrong_reflection','not_vacuum',
        'duplicate_event','different_trial','observer_not_near_clock','observer_not_comoving','observer_not_applying',
        'wrong_criterion','wrong_second_observer','wrong_return_clock','wrong_return_place','wrong_return_reading',
        'local_clock_not_stationary','local_clock_not_synced','carried_clock_current_place_missing','missing_record',
        'wrong_length','wrong_length_setting','wrong_speed_unit','missing_setting_connection','wrong_light_speed',
        'wrong_rod_speed','wrong_context')
    rows={}
    for name in cases:
        model=guarded(doc)
        constants={'ja':'other' if name=='wrong_context' else 'motion','ra':'frame','rb':'timeunit','rc':'reference',
            'ta':'lengthunit','tb':'other' if name=='wrong_speed_unit' else 'speedunit','yf':'other' if name=='wrong_length_setting' else 'slice',
            'xi':'rod','xn':'enda','xo':'endb','zaj':'ca','zak':'cb','zas':'r1','zat':'r2','zau':'r3',
            'zaw':'trial','zax':'ray','zay':'observera','zaz':'observera' if name=='wrong_second_observer' else 'observerb'}
        for key,val in constants.items():model[key]=lambda val=val:val
        model.update(zav=lambda:cut(10 if name=='wrong_length' else 8),tc=lambda:cut(4 if name=='wrong_light_speed' else 3),
            yb=lambda:cut(2 if name=='wrong_rod_speed' else 1))
        def row(r):return records.get(r,records['r1'])
        model.update(zad=lambda r:'e1' if name=='duplicate_event' and r=='r3' else row(r)[2],
            zae=lambda r:'p1' if name=='wrong_return_place' and r=='r3' else row(r)[3],zaf=lambda r:row(r)[4],
            zag=lambda r:cut(9 if name=='wrong_return_reading' and r=='r3' else row(r)[5]),zah=lambda r:cut(row(r)[5]),
            zac=lambda r,clock,ctx:r in records and clock==row(r)[0] and ctx=='motion' and not(name=='missing_record' and r=='r3'),
            ca=lambda c:c in ('ca','cb','l1','l2','l3','reference'),ci=lambda u:u=='timeunit',
            cc=lambda c,f:f=='frame' and c in ('l1','l2','l3','reference') and not(name=='local_clock_not_stationary' and c=='l3'),
            xm=lambda c,f,ctx:c in ('ca','cb') and (f,ctx)==('frame','motion'),
            zaa=lambda c,end,rod,ctx:(c,end) in (('ca','enda'),('cb','endb')) and (rod,ctx)==('rod','motion'),
            xf=lambda end,rod,f,ctx:end in ('enda','endb') and (rod,f,ctx)==('rod','frame','motion'))
        model['xg']=lambda end,event,place,f,ctx:(f,ctx)==('frame','motion') and any((end,event,place)==(r[1],r[2],r[3]) for r in records.values())
        model['zab']=lambda clock,event,place,f,ctx:(f,ctx)==('frame','motion') and any((clock,event,place)==(r[0],r[2],r[3]) for r in records.values()) and not(name=='carried_clock_current_place_missing' and event=='e3')
        model['cb']=lambda obj,place,f:f=='frame' and any((obj,place) in ((r[2],r[3]),(r[4],r[3])) for r in records.values())
        def read(clock,event,f,u,value):
            return (f,u)==('frame','timeunit') and any(event==r[2] and clock in (r[0],r[4]) and fingerprint(value)==fingerprint(cut(r[5])) for r in records.values()) and not(name=='wrong_return_clock' and clock=='ca' and event=='e3')
        model.update(ce=read,cf=lambda r:r=='ray',
            cg=lambda ray,start,end,frame:ray=='ray' and frame=='frame' and (start,end) in (('e1','e2'),('e2','e3')) and not(
                name=='missing_outward_leg' and start=='e1' or name=='missing_return_leg' and start=='e2'),
            ch=lambda *args:args==('ray','e1' if name=='wrong_reflection' else 'e2','frame'),
            tk=lambda *args:name!='not_vacuum' and args in (('ray','e1','e2','frame'),('ray','e2','e3','frame')),
            za4=lambda *args:args==('other' if name=='different_trial' else 'trial','ray','e1','e2','e3','frame','motion'),
            xb=lambda who:who in ('observera','observerb'),
            zap=lambda who,clock,ctx:(who,clock,ctx) in (('observera','ca','motion'),('observerb','cb','motion')) and not(name=='observer_not_near_clock' and who=='observerb'),
            zaq=lambda who,clock,f,ctx:f=='frame' and (who,clock,ctx) in (('observera','ca','motion'),('observerb','cb','motion')) and not(name=='observer_not_comoving' and who=='observerb'),
            zar=lambda who,ca,cb,trial,criterion,ctx:who in ('observera','observerb') and (ca,cb,trial,ctx)==('ca','cb','trial','motion') and json.loads(criterion.syntax)['symbol']==('sdb' if name=='wrong_criterion' else 'bi') and not(name=='observer_not_applying' and who=='observerb'),
            ti=lambda u:u=='lengthunit',tj=lambda *args:args==('lengthunit','timeunit','speedunit'),
            yx=lambda *args:name!='missing_setting_connection' and args==('motion','slice'))
        def relation(*args):
            length,light,speed,first,middle,last=(numeric[fingerprint(x)] for x in args)
            return length>0 and 0<=speed<light and first<middle<last and (light-speed)*(middle-first)==length and (light+speed)*(last-middle)==length
        callbacks(doc,model,{
            'jb':lambda clock,ref,f,u,ctx:clock in ('l1','l2','l3') and (ref,f,u,ctx)==('reference','frame','timeunit','motion') and not(name=='local_clock_not_synced' and clock=='l3'),
            'jc':lambda a,b:fingerprint(a)==fingerprint(b),'jd':lambda value:True,
            'je':lambda length,ctx:fingerprint(length)==fingerprint(cut(8)) and ctx=='slice','jf':relation})
        actual=values(doc,model,domain)
        protocol_bad=set(cases[1:19])|{'wrong_context'}
        rates_bad={'wrong_length','wrong_length_setting','wrong_speed_unit','missing_setting_connection','wrong_light_speed','wrong_rod_speed','wrong_context','wrong_return_reading'}
        expected=[name not in protocol_bad,name not in rates_bad]
        if actual!=expected:raise ValueError('Moving light-trip source differs: '+name+' '+repr(actual)+' '+repr(expected))
        rows[name]=actual
    return {'cases':rows,'carried_clock_rest_not_required':True,'full_real_conditions_evaluated':False,
        'integer_fixture_oracles_for_readings_synchrony_and_formula':True,
        'physical_worldlines_derived_from_all_source_relations':False}


def attribution_checks():
    doc=parse(source_composed()[0]);doc['statements']=doc['statements'][-2:]
    rows={}
    for name in ('baseline','wrong_previous_setting','missing_extension','wrong_principle','wrong_conclusion','wrong_author','wrong_scope'):
        model=guarded(doc)
        for key,val in {'za2':'setting','za3':'result','zal':'carriedsetting','rd':'author','xy':'scope','ri':'text'}.items():model[key]=lambda val=val:val
        common=lambda author,scope,ctx:(author,scope,ctx)==('other' if name=='wrong_author' else 'author','other' if name=='wrong_scope' else 'scope','text')
        model['ug']=lambda node,author,desc,scope,ctx:node=='setting' and common(author,scope,ctx) and json.loads(desc.syntax)['symbol']=='sdh'
        model['zao']=lambda prior,added,scope,ctx:name!='missing_extension' and (prior,added,scope,ctx)==('other' if name=='wrong_previous_setting' else 'carriedsetting','setting','scope','text')
        model['zc']=lambda node,author,premise,conclusion,scope,ctx:node=='result' and common(author,scope,ctx) and json.loads(premise.syntax)['symbol']==('saw' if name=='wrong_principle' else 'sbd') and json.loads(conclusion.syntax)['symbol']==('scd' if name=='wrong_conclusion' else 'sdj')
        actual=values(doc,model,('setting','result','carriedsetting','author','scope','other'))
        expected=[name not in ('wrong_previous_setting','missing_extension','wrong_author','wrong_scope'),name not in ('wrong_principle','wrong_conclusion','wrong_author','wrong_scope')]
        if actual!=expected:raise ValueError('Moving light derivation attribution differs')
        rows[name]=actual
    return rows


def alignment():
    artifact=json.loads((ROOT/'artifacts/written-units-v1/einstein-1905.json').read_text(encoding='utf-8'))
    entries=[(36,'a77fa87978ee78333c0975f86f66418f78dd34e933030d3cc8236b5ed09d895c'),
        (37,'89c036813f96312336434516a8c0ec45b86488545ebc6a39954e731cd0b7f35c'),
        (38,'856cc99d87343400dc05fe7d03fa666602a1d92c4fb0ee1f5ae2f0a5fb218eb8'),
        (39,'add79ca90f60bae6dafe96e229aa6348715b007fbd48985c9c11fcc41aaa8955'),
        (40,'7e75b87effaf07397f5bd678f7aab178e644c2e48aca3ae656e991b7032d6e6f')]
    hashes={'M0060':'9fed7b73a7257834866d6b5a4a9d7e776bcdb70ecdbbeff1d255eb4b6ad2225d',
        'M0061':'8d83f3cef0b58ca52b0aa5534f72101449a38e3ebdd949ea4079215d68ff9d5d',
        'M0062':'ce040065006fc7e2d92e03d76b9ea5deb8b719d434ed01ecf36905eeb94e3d77'}
    rows=[]
    for number,digest in entries:
        unit=next(u for u in artifact['units'] if u['id']==f'einstein-1905:u{number:04d}')
        if hashlib.sha256(unit['text'].encode('utf-8')).hexdigest()!=digest:raise ValueError('Moving light source changed')
        if number in (36,38,40):
            end=unit['text'].index('.')+1 if number==40 else len(unit['text'])
            rows.append({'unit':unit['id'],'unit_sha256':digest,'start':0,'end':end,'source':unit['text'][:end],
                'definitions':['sdf','sdg','sdi','sdj'],'status':'partial_explicit_reading','full_semantic_equivalence':False})
        for math_id in unit['math_ids']:
            if math_id not in hashes:continue
            math=next(m for m in artifact['math'] if m['id']==math_id)
            if hashlib.sha256(math['mathml'].encode('utf-8')).hexdigest()!=hashes[math_id]:raise ValueError('Moving trip formula changed')
            rows.append({'unit':unit['id'],'unit_sha256':digest,'math_id':math_id,'math_sha256':hashes[math_id],
                'definitions':['sda','sdb','sdi'],'status':'partial','full_semantic_equivalence':False})
    return {'segments':rows,'verified_full_units':0}


def build_report():
    documents={}
    for compose in (generic_composed,source_composed):
        text,basis=compose();doc=parse(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text:raise ValueError('Stored light trip differs')
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Light trip roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis)
    paths=[*documents,'data/moving-light-trip-basis-v1.json','data/einstein-moving-light-trip-basis-v1.json',
        'examples/v014/einstein-carried-clocks.noema','scripts/compose_moving_light_trip.py','scripts/check_moving_light_trip.py',
        'noema/discourse.py','noema/finite_semantics.py','noema/polynomial_proofs.py']
    current=source_composed()[0];previous=(ROOT/'examples/v014/einstein-carried-clocks.noema').read_text(encoding='utf-8')
    return {'status':'partial_moving_endpoint_light_times_and_observer_midpoint_application','documents':documents,
        'numeric':numeric_checks(),'polynomial':polynomial_checks(),'source_adapter':source_checks(),'attribution':attribution_checks(),
        'alignment':alignment(),'roundtrips':True,'verified_full_units':{'einstein-1905':0,'kant-1784':0},
        'notation_size':{'canonical_source_document_characters':len(current),'added_declarations_and_statements_characters':len(current)-len(previous)},
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args()
    report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Moving light report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Moving light equations, polynomial consequences, event bindings and observer attributions checked')


if __name__=='__main__':main()
