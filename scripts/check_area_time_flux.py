"""Check area/time normalization and the bindings of five quantity records."""
import argparse
from fractions import Fraction as F
import hashlib
from itertools import product
import json

from noema.grammar import parse,format_graph,number_word
from noema.meaning_basis import audit_basis
from noema.polynomial_proofs import verify_universal
from noema.script import encode,decode
from scripts.check_comoving_labels import values
from scripts.check_coordinate_correspondence import abstract
from scripts.check_described_appraisals import candidate
from scripts.check_plane_waveforms import setup,OPS
from scripts.check_real_products import MEANINGS,assertion
from scripts.check_moving_light_trip import literal
from scripts.check_mirror_reflection import fixture_numbers
from scripts.check_rod_setup import callbacks
from scripts.compose_limits import call as k,op,both,v
from scripts.compose_area_time_flux import (ROOT,PARENT,BUILDERS,INPUTS,RECORDS,TARGETS,KINDS,
    NORMAL,TOTAL,COMBINED,ALL,CUT,generic_composed)

REPORT=ROOT/'reports/area-time-flux-v1.json'
SYMBOLS={name:'jz'+number_word(i) for i,(name,_) in enumerate(INPUTS)}
PI='jzzzz'
DOMAIN=('episode','mirror','patch','interval','incominglight','outgoinglight','frame','observer',
    'area','time','energy','other',*[name+field for name in RECORDS for field in ('record','unit')])


def polynomial_checks():
    norm=k('sela',*map(v,NORMAL.split()))
    total=k('selb',*map(v,TOTAL.split()))
    difference=op('e',v('work'),k('ab',v('incoming'),k('ac',v('outgoing'))))
    zero=literal(0)
    second={n:v(n+'other') if n in ('incoming','outgoing','work') else v(n) for n in NORMAL.split()}
    rate_equal=both(*(op('e',v(n),v(n+'other')) for n in ('incoming','outgoing','work')))
    example=(2,3,2,F(1,2),F(3,2),F(1,3),F(1,12),F(1,4))
    negative=(2,3,F(1,2),2,F(-3,2),F(1,12),F(1,3),F(-1,4))
    claims={
        'common_area_time_preserves_total_balance':assertion(NORMAL,op('y',both(norm,difference),total)),
        'positive_area_time_recovers_rate_balance':assertion(NORMAL,op('y',both(norm,total),difference)),
        'positive_area_time_makes_rates_unique':assertion(NORMAL+' incomingother outgoingother workother',
            op('y',both(norm,k('sela',*(second[n] for n in NORMAL.split()))),rate_equal)),
        'zero_area_is_not_a_normalization':assertion(NORMAL,op('y',op('e',v('area'),zero),op('u',norm))),
        'zero_duration_is_not_a_normalization':assertion(NORMAL,op('y',op('e',v('duration'),zero),op('u',norm))),
        'nonunit_area_and_time_are_allowed':assertion('',k('sela',*map(literal,example))),
        'negative_work_is_allowed':assertion('',both(k('sela',*map(literal,negative)),k('selb',*map(literal,negative[2:5])))),
        'total_energy_equals_its_normalized_rate':assertion('',op('y',k('sela',*map(literal,example)),
            op('e',literal(example[2]),literal(example[5])))),
        'area_alone_is_sufficient':assertion('',op('y',k('sela',*map(literal,example)),
            op('e',literal(example[2]),k('ad',literal(example[0]),literal(example[5]))))),
    }
    rows={}
    text=generic_composed()[0]
    for name,claim in claims.items():
        result=verify_universal(parse(text+claim),MEANINGS,timeout_ms=30000)[0]
        expected='invalid' if name in ('total_energy_equals_its_normalized_rate','area_alone_is_sufficient') else 'valid'
        if result['status']!=expected:raise ValueError('Area/time proof '+name+': '+repr(result))
        rows[name]=result
    return dict(claims=rows,rational_polynomial_proofs_only=True,all_real_cut_laws_proved=False,
        physical_energy_principle_proved=False)


def query_document(text):
    declared={d['name'] for d in parse(text)['declarations']}
    if (set(SYMBOLS.values())|{PI}) & declared:raise ValueError('Fixture identifier collision')
    extra=''.join('r '+SYMBOLS[name]+'[] '+sort+'.' for name,sort in INPUTS)+'r '+PI+'[] '+CUT+'.'
    converted={n:k('bj',k(SYMBOLS[n+'scale']),k(SYMBOLS[n+'value'])) for n in RECORDS}
    fields=lambda names:[converted[n] if n in converted else k(SYMBOLS[n]) for n in names.split()]
    queries=[k('selg',*(k(SYMBOLS[n]) for n,_ in INPUTS)),k('seld',*fields(NORMAL)),
        k('self',*fields(COMBINED)),k('seli',*(k(PI) if n=='conversion' else k(SYMBOLS[n]) for n,_ in INPUTS)),
        k('sele',*fields(TOTAL))]
    return extra+''.join('q['+expr+'].' for expr in queries)


def fixture_model(doc,*,speed=3,amplitude=2,area=2,duration=3,scales=(1,1,1,1,1),changes=None,row_change=None,flag=None):
    fixture,model=setup(doc);make,read=fixture.make,fixture.read
    V,speed,A,a,*_=fixture_numbers(speed,1,amplitude)
    B,b,_=fixture_numbers(speed,1,amplitude)[-3:]
    pi=F(3);C=8*pi;area,duration=map(F,(area,duration))
    incoming=A*A*(V*a-speed)/C;outgoing=B*B*(speed-V*b)/C
    pressure=2*A*A*(V*a-speed)**2/(C*(V*V-speed*speed));work=pressure*speed
    config=dict(zip(ALL.split(),(V,speed,A,a,B,b,C,incoming,outgoing,pressure,work)))
    for name in ('episode','mirror','patch','interval','incominglight','outgoinglight','frame','observer'):config[name]=name
    config.update(areakind='area',timekind='time',energykind='energy',context='motion')
    totals=dict(area=area,duration=duration,inenergy=area*duration*incoming,
        outenergy=area*duration*outgoing,workenergy=area*duration*work)
    profiles,records,owners=[],[],[]
    for i,name in enumerate(RECORDS):
        scale=F(scales[i]);value=totals[name]/scale;kind=config[KINDS[name]]
        config.update({name+'record':name+'record',name+'unit':name+'unit',name+'scale':scale,name+'value':value})
        profiles.append([name+'unit',kind,scale,'motion'])
        records.append([name+'record',TARGETS[name],kind,'frame','episode',name+'unit',value,'motion'])
        owners.append([name+'record','observer','motion'])
    config.update(changes or {})
    for i,name in enumerate(RECORDS):records[i][6]=F(config[name+'value'])
    if row_change:
        table,row,column,value=row_change
        {'records':records,'profiles':profiles,'owners':owners}[table][row][column]=value
    for name,sort in INPUTS:
        if name in ('recordedby','exchange'):continue
        value=config[name]
        if sort in ('b',CUT):value=F(value)
        model[SYMBOLS[name]]=(lambda value=value:make(value)) if sort==CUT else (lambda value=value:value)
    model[PI]=lambda:make(pi)
    model.update(sedi=lambda value:flag!='unknown_pi' and read(value)==pi,
        cf=lambda target:target in ('incominglight','outgoinglight'),va=lambda frame:frame=='frame',
        xb=lambda observer:observer=='observer',x4=lambda observer,frame,context:flag!='wrong_rest_frame' and
            (observer,frame,context)==('observer','frame','motion'),
        zof=lambda unit,kind,scale,context:[unit,kind,scale,context] in profiles)
    def reading(record,target,kind,frame,event,unit,value,context):
        if flag=='unknown_readings':raise ValueError('Reading interpretation missing')
        return [record,target,kind,frame,event,unit,read(value),context] in records
    def exchange(*args):
        if flag=='unknown_exchange':raise ValueError('Exchange interpretation missing')
        return flag!='nonuniform_exchange' and args==('episode','mirror','patch','interval','incominglight','outgoinglight','frame','motion')
    model['zog']=reading
    callbacks(doc,model,{SYMBOLS['recordedby']:lambda record,observer,context:[record,observer,context] in owners,
        SYMBOLS['exchange']:exchange})
    return model


def evaluate(doc,model):
    used={d['name'] for d in doc['declarations'] if d['kind']=='primitive'}
    return values(doc,{name:value for name,value in model.items() if name in used},DOMAIN)


def binding_checks(texts):
    docs=[abstract(candidate(text,query_document(text)),OPS|{'sedi'}) for text in texts]
    def run(**options):
        rows=[evaluate(doc,fixture_model(doc,**options)) for doc in docs]
        if rows[0]!=rows[1]:raise ValueError('Extracted normalization differs')
        return rows[0]
    cases=[]
    for speed,amplitude,extent,scales in product((-3,0,3),(0,2),((1,1),(2,3),(F(1,2),7)),((1,1,1,1,1),(2,3,5,7,11))):
        row=run(speed=speed,amplitude=amplitude,area=extent[0],duration=extent[1],scales=scales)
        if row!=[True]*5:raise ValueError('Valid area/time configuration failed')
        cases.append(dict(speed=speed,amplitude=amplitude,area=str(extent[0]),duration=str(extent[1]),scales=list(scales),results=row))
    contrasts={}
    def check(name,expected,**options):
        actual=run(**options)
        if actual!=expected:raise ValueError(name+': '+repr(actual))
        contrasts[name]=actual
    for row in range(5):
        for column,label in ((1,'target'),(2,'kind'),(3,'frame'),(4,'event'),(5,'unit'),(7,'context')):
            check('record_'+str(row)+'_wrong_'+label,[False,True,True,False,True],row_change=('records',row,column,'other'))
        check('record_'+str(row)+'_wrong_owner',[False,True,True,False,True],row_change=('owners',row,1,'other'))
        check('record_'+str(row)+'_wrong_unit_kind',[False,True,True,False,True],row_change=('profiles',row,1,'other'))
    for name in ('episode','mirror','patch','interval','incominglight','outgoinglight','frame','observer','context'):
        check('wrong_'+name,[False,True,True,False,True],changes={name:'other'})
    for field in ('areakind','timekind'):
        check(field+'_confused_with_energy',[False,True,True,False,True],changes={field:'energy'})
    for flag in ('wrong_rest_frame','nonuniform_exchange'):
        check(flag,[False,True,True,False,True],flag=flag)
    for field in ('areavalue','durationvalue'):
        for value in (0,-1):
            check(field+'_'+str(value),[True,False,False,False,True],changes={field:value})
    check('total_energy_replaced_by_rate',[True,False,False,False,False],changes={'inenergyvalue':F(1,3)})
    check('time_factor_omitted',[True,False,False,False,False],changes={'inenergyvalue':F(2,3)})
    check('work_sign_reversed',[True,False,False,False,False],changes={'workenergyvalue':F(-3,2)})
    check('wrong_reflection_amplitude',[True,True,False,False,True],changes={'finalamplitude':2})
    check('scale_changed_without_conversion',[False,False,False,False,True],changes={'areascale':2})
    check('zero_unit_scale',[False,False,False,False,True],changes={'areascale':0})
    check('negative_unit_scale',[False,False,False,False,True],changes={'areascale':-1})
    check('missing_pi_condition',[True,True,True,False,True],flag='unknown_pi')
    for pressure in (1,99):
        check('stationary_pressure_'+str(pressure),[True]*5,speed=0,changes={'pressure':pressure})
    for doc in docs:
        for flag,message in (('unknown_readings','Reading interpretation missing'),('unknown_exchange','Exchange interpretation missing')):
            try:evaluate(doc,fixture_model(doc,flag=flag))
            except ValueError as exc:
                if message not in str(exc):raise
            else:raise ValueError('Missing interpretation supplied: '+flag)
    return dict(cases=cases,contrasts=contrasts,standalone_agrees=True,unknown_readings_and_exchange_refused=True,
        actual_real_arithmetic_abstracted_to_registered_rational_cuts=True,pi_integral_abstracted=True,
        physical_area_time_measurement_and_uniformity_proved=False,stationary_pressure_determined=False)


def alignment():
    source=json.loads((ROOT/'artifacts/written-units-v1/einstein-1905.json').read_text(encoding='utf-8'))
    unit=next(u for u in source['units'] if u['id']=='einstein-1905:u0222')
    excerpts=['Die auf die Flächeneinheit des Spiegels pro Zeiteinheit auftreffende (im ruhenden System gemessene) Energie',
        'Die von der Flächeneinheit des Spiegels in der Zeiteinheit sich entfernende Energie',
        'die vom Lichtdrucke in der Zeiteinheit geleistete Arbeit']
    segments=[]
    for excerpt in excerpts:
        if unit['text'].count(excerpt)!=1:raise ValueError('Ambiguous area/time source range')
        start=unit['text'].index(excerpt)
        segments.append(dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[start,start+len(excerpt)],text=excerpt,
            definitions=['seld','sele','selg','selh','seli'],status='partial',
            review_ja='一様・定常な比較設定で五記録を同じ系と交換設定へ結び、面積と時間を共有して入出エネルギーと仕事を正規化する。測度・時計・物理的帰属の構成とエネルギー原理の証明は未完。'))
    return dict(segments=segments,semantic_completion=False)


def build_report():
    documents,sizes,texts={},{},[]
    for builder,stem in BUILDERS:
        text,basis=builder();doc=parse(text);texts.append(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text or json.loads((ROOT/('data/'+stem+'-basis-v1.json')).read_text(encoding='utf-8'))!=basis:
            raise ValueError('Stored area/time document differs')
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Area/time roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis);sizes[stem]=dict(characters=len(text),statements=len(doc['statements']))
    doc,parent=parse(texts[1]),parse((ROOT/PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])]!=parent['declarations'] or doc['statements']!=parent['statements']:
        raise ValueError('Parent changed')
    paths=[*documents,PARENT,*['data/'+stem+'-basis-v1.json' for _,stem in BUILDERS],
        'scripts/compose_area_time_flux.py','scripts/check_area_time_flux.py','scripts/compose_light_pressure.py',
        'scripts/check_mirror_reflection.py','scripts/check_plane_waveforms.py','scripts/check_rod_setup.py',
        'scripts/check_comoving_labels.py','scripts/check_real_products.py','noema/finite_semantics.py','noema/polynomial_proofs.py',
        'noema/extraction.py','artifacts/written-units-v1/einstein-1905.json']
    return dict(status='partial_common_area_time_flux_normalization',documents=documents,sizes=sizes,
        polynomial=polynomial_checks(),binding=binding_checks(texts[1:]),alignment=alignment(),
        new_definitions=9,new_primitives=0,new_author_statements=0,parent_preserved=True,roundtrips=True,
        verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths})


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args()
    report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Area/time report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:
            json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Shared area/time normalization, signed work and quantity bindings checked')


if __name__=='__main__':main()
