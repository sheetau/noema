"""Verify common conversion and divergence bindings for material charge."""
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
from scripts.check_material_charge import numbers
from scripts.check_field_equations import AXES,jet_callback
from scripts.check_rod_setup import callbacks,guarded
from scripts.compose_limits import call as k,op,both,v
from scripts.compose_charge_normalization import ROOT,PARENT,BUILDERS,SCALE,TOTAL,PI,BOUND,INPUTS,CELL,FLOW,CUT,generic_composed
from scripts.compose_material_charge import INPUTS as MATERIAL

REPORT=ROOT/'reports/charge-normalization-v1.json'
FIELDS=BOUND+[('conversion',CUT)]
SYMBOLS={name:'js'+number_word(i) for i,(name,_) in enumerate(FIELDS)}
DOMAIN=AXES+('matter','oldframe','newframe','oldslice','newslice','other')


def configuration(conversion=12,**options):
    row=numbers(**options);row.update(pi=F(3),conversion=F(conversion))
    row.update(normalized=row['conversion']*row['density'],newnormalized=row['conversion']*row['newdensity'])
    return row


def polynomial_checks():
    mul=lambda a,b:k('ad',a,b);eq=lambda a,b:op('e',a,b)
    scale=k('senj',*map(v,SCALE.split()));total=k('senk',*map(v,TOTAL.split()))
    base=configuration();zero=configuration(density=0)
    concrete=lambda row:k('senk',*(literal(row[n]) for n in TOTAL.split()))
    wrong=dict(base);wrong['newdensity']/=2;wrong['newcharge']/=2
    normflow=[literal(wrong['normalized'] if n=='density' else wrong['newnormalized'] if n=='newdensity' else wrong[n]) for n in FLOW.split()]
    claims={
        'common_conversion_transfers_density_boost':assertion(SCALE,op('y',scale,k('semp',*map(v,FLOW.split())))),
        'converted_material_charge_is_invariant':assertion(TOTAL,op('y',total,eq(v('charge'),v('newcharge')))),
        'normalized_old_total_is_scaled_charge':assertion(TOTAL,op('y',total,eq(mul(v('normalized'),v('volume')),mul(v('conversion'),v('charge'))))),
        'normalized_new_total_is_scaled_charge':assertion(TOTAL,op('y',total,eq(mul(v('newnormalized'),v('newvolume')),mul(v('conversion'),v('newcharge'))))),
        'normalized_totals_also_agree':assertion(TOTAL,op('y',total,eq(mul(v('normalized'),v('volume')),mul(v('newnormalized'),v('newvolume'))))),
        'normalized_total_is_physical_charge':assertion('',op('y',concrete(base),eq(literal(base['normalized']*base['volume']),literal(base['charge'])))),
        'different_conversions_still_preserve_physical_charge':assertion('',op('y',both(k('semp',*normflow),
            eq(literal(wrong['normalized']),mul(literal(12),literal(wrong['density']))),
            eq(literal(wrong['newnormalized']),mul(literal(24),literal(wrong['newdensity'])))),eq(literal(wrong['charge']),literal(wrong['newcharge'])))),
        'zero_density_uniquely_identifies_conversion':assertion('',op('y',both(concrete(zero),concrete(dict(zero,conversion=F(24)))),eq(literal(12),literal(24)))),
    }
    rejected={'normalized_total_is_physical_charge','different_conversions_still_preserve_physical_charge','zero_density_uniquely_identifies_conversion'}
    rows={};text=generic_composed()[0]
    for name,claim in claims.items():
        result=verify_universal(parse(text+claim),MEANINGS,timeout_ms=25000,max_expansion=250000)[0]
        if result['status']!=('invalid' if name in rejected else 'valid'):raise ValueError('Charge conversion proof '+name+': '+result['status'])
        rows[name]=result
    return dict(claims=rows,rational_common_factor_only=True,actual_pi_value_proved=False,all_real_cut_laws_proved=False)


def expression(name):return k(SYMBOLS[name])


def fixture():
    text=''.join('r '+SYMBOLS[n]+'[] '+sort+'.' for n,sort in FIELDS)
    fields=lambda names:[expression(n) for n in names.split()]
    norm={n:expression(n) for n in FLOW.split()};norm.update(density=expression('normalized'),newdensity=expression('newnormalized'))
    queries=[k('senl',*fields(SCALE)),k('senm',*fields(TOTAL)),k('senn',*fields(PI)),
        k('seno',*(expression(n) for n,_ in INPUTS)),k('senp',*fields(PI),expression('electricjet'),expression('newelectricjet')),
        k('senq',*(expression(n) for n,_ in BOUND)),k('senh',*fields(CELL)),k('seni',*(expression(n) for n,_ in MATERIAL)),
        k('semt',*(norm[n] for n in FLOW.split())),k('sca',expression('charge'),expression('newcharge'))]
    return text+''.join('q['+q+'].' for q in queries)


def model_for(doc,*,config=None,changes=None,variant='baseline'):
    original=dict(config or configuration());row=dict(original);row.update(changes or {})
    cuts,model=setup(doc);make,read=cuts.make,cuts.read
    for name,sort in FIELDS:
        if name in ('assigned','paired','frames','electricjet','newelectricjet','jetassigned'):continue
        if sort==CUT:model[SYMBOLS[name]]=lambda name=name:make(row[name])
        else:model[SYMBOLS[name]]=lambda name=name:'motion' if name=='context' else name
    old=[[original['normalized'],F(1),F(2),F(3)],[F(4),F(0),F(5),F(6)],[F(7),F(8),F(0),F(9)]]
    new=[[original['newnormalized'],F(1),F(2),F(3)],[F(4),F(0),F(5),F(6)],[F(7),F(8),F(0),F(9)]]
    shown_old=[r[:] for r in old];shown_new=[r[:] for r in new]
    if variant.startswith('jet_'):
        _,side,i,j=variant.split('_');(shown_old if side=='old' else shown_new)[int(i)][int(j)]+=F(1)
    model['sedi']=lambda pi:variant!='missing_pi' and read(pi)==3
    def match(actual,expected,category,labels):
        expected=list(expected)
        for i,label in enumerate(labels):
            if variant==category+'_'+label:expected[i]=expected[i]+1 if isinstance(expected[i],F) else 'text' if label=='context' else 'other'
        return list(actual)==expected
    def assigned(matter,frame,slice,density,volume,charge,context):
        return any(match((matter,frame,slice,read(density),read(volume),read(charge),context),
            ('matter',side+'frame',side+'slice',row[d],row[w],row[q],'motion'),side,
            ('matter','frame','slice','density','volume','charge','context')) for side,d,w,q in (
                ('old','density','volume','charge'),('new','newdensity','newvolume','newcharge')))
    def assignedjet(matter,frame,slice,jet,context):
        numeric=tuple(tuple(read(jet(a,b)) for b in AXES) for a in AXES[:3])
        return any(numeric==tuple(map(tuple,expected)) and match((matter,frame,slice,context),
            ('matter',side+'frame',side+'slice','motion'),'trace'+side,('matter','frame','slice','context')) for side,expected in (('old',old),('new',new)))
    callbacks(doc,model,{
        SYMBOLS['assigned']:assigned,SYMBOLS['electricjet']:jet_callback(cuts,shown_old),SYMBOLS['newelectricjet']:jet_callback(cuts,shown_new),
        SYMBOLS['jetassigned']:assignedjet,
        SYMBOLS['paired']:lambda *a:match(a,('matter','oldframe','newframe','oldslice','newslice','motion'),'pair',
            ('matter','oldframe','newframe','oldslice','newslice','context')),
        SYMBOLS['frames']:lambda old,new,speed,context:match((old,new,read(speed),context),
            ('oldframe','newframe',row['speed'],'motion'),'frame',('oldframe','newframe','speed','context'))})
    used={d['name'] for d in doc['declarations'] if d['kind']=='primitive'}
    return {n:f for n,f in model.items() if n in used}


def finite_checks(texts):
    docs=[abstract(candidate(text,fixture()),OPS|{'sedi'}) for text in texts]
    def run(**options):
        rows=[values(doc,model_for(doc,**options),DOMAIN) for doc in docs]
        if rows[0]!=rows[1]:raise ValueError('Extracted charge conversion differs')
        return rows[0]
    cases=[]
    for speed,density,conversion in product((-3,0,3),(-4,0,4),(1,12,28)):
        row=run(config=configuration(speed=speed,density=density,conversion=conversion))
        pi_ok=conversion==12 or density==0
        if row!=[True,True,pi_ok,pi_ok,pi_ok,pi_ok,True,True,True,True]:raise ValueError('Common factor or pi specialization differs')
        cases.append(dict(speed=speed,density=density,conversion=conversion,results=row))
    contrasts={}
    specs={
        'missing_pi':[True,True,False,False,False,False,True,True,True,True],
        **{side+'_'+name:[True,True,True,False,True,False,True,False,True,True] for side in ('old','new') for name in ('matter','frame','slice','density','volume','charge','context')},
        **{'pair_'+name:[True,True,True,False,True,False,True,False,True,True] for name in ('matter','oldframe','newframe','oldslice','newslice','context')},
        **{'frame_'+name:[True,True,True,False,True,False,True,False,True,True] for name in ('oldframe','newframe','speed','context')},
        **{'trace'+side+'_'+name:[True,True,True,True,True,False,True,True,True,True] for side in ('old','new') for name in ('matter','frame','slice','context')},
    }
    for variant,want in specs.items():
        row=run(variant=variant)
        if row!=want:raise ValueError('Density or trace binding accepted a wrong reference: '+repr((variant,row)))
        contrasts[variant]=row
    jets=[]
    for side,i,j in product(('old','new'),range(3),range(4)):
        variant=f'jet_{side}_{i}_{j}';row=run(variant=variant)
        want=[True,True,True,True,i!=j,False,True,True,True,True]
        if row!=want:raise ValueError('Divergence or actual jet assignment ignores mutation: '+variant)
        jets.append(dict(side=side,component=i,axis=j,results=row))
    numeric={}
    changes={
        'physical_density_replaced_by_normalized':{'density':F(48),'charge':F(528)},
        'new_conversion_doubled':{'newdensity':F(11,5),'newcharge':F(22)},
        'normalized_density_changed':{'normalized':F(49)},
        'new_normalized_density_changed':{'newnormalized':F(269,5)},
        'conversion_zero':{'conversion':F(0)},'conversion_negative':{'conversion':F(-12)},
        'different_pi':{'pi':F(7)},
    }
    for name,change in changes.items():
        row=run(changes=change)
        if name in ('conversion_zero','conversion_negative'):
            want=[False,False,True,True,True,True,True,True,True,True]
        elif name=='different_pi':want=[True,True,False,False,False,False,True,True,True,True]
        elif name in ('normalized_density_changed','new_normalized_density_changed'):
            want=[False,False,False,False,False,False,True,True,False,True]
        else:want=[False,False,False,False,False,False,False,False,True,False]
        if row!=want:raise ValueError('Numeric normalization misuse accepted: '+repr((name,row,want)))
        numeric[name]=row
    for doc in docs:
        for name in ('assigned','paired','frames','jetassigned','electricjet','newelectricjet'):
            model=model_for(doc);model[SYMBOLS[name]]=guarded(doc)[SYMBOLS[name]]
            try:values(doc,model,DOMAIN)
            except ValueError as exc:
                if 'Unrelated primitive' not in str(exc):raise
            else:raise ValueError('Unknown charge or derivative interpretation supplied')
        model=model_for(doc);model['sedi']=guarded(doc)['sedi']
        try:values(doc,model,DOMAIN)
        except ValueError as exc:
            if 'Unrelated primitive' not in str(exc):raise
        else:raise ValueError('Unknown pi replaced by a numerical constant')
    return dict(cases=cases,binding_contrasts=contrasts,jet_mutations=jets,numeric_contrasts=numeric,
        standalone_agrees=True,unknown_relations_and_pi_refused=True,pi_oracle_is_synthetic=True,
        actual_pi_approximated_or_proved=False,full_field_derivatives_or_boost_proved=False)


def alignment():
    source=json.loads((ROOT/'artifacts/written-units-v1/einstein-1905.json').read_text(encoding='utf-8'))
    unit=next(u for u in source['units'] if u['id']=='einstein-1905:u0238')
    excerpt='so bleibt seine Ladung auch';start=unit['text'].index(excerpt)
    return dict(segments=[dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[start,start+len(excerpt)],text=excerpt,
        definitions=['senj','senk','senl','senm','senn','seno','senp','senq'],status='explicit_interpretive_annotation',
        review_ja='前版の一様並進の解釈注記を精密化し、発散・4πの換算・電荷密度・体積・総量を結ぶ。新たな原文範囲は追加しない。任意運動の保存則・単位の実現・全場の微分と変換・全文意味一致は未完。')],semantic_completion=False)


def build_report():
    documents,sizes,texts={},{},[]
    for builder,stem in BUILDERS:
        text,basis=builder();doc=parse(text);texts.append(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text or json.loads((ROOT/('data/'+stem+'-basis-v1.json')).read_text(encoding='utf-8'))!=basis:raise ValueError('Stored charge normalization differs')
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Charge normalization roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis);sizes[stem]=dict(characters=len(text),statements=len(doc['statements']))
    doc,parent=parse(texts[1]),parse((ROOT/PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])]!=parent['declarations'] or doc['statements']!=parent['statements']:raise ValueError('Parent changed')
    paths=[*documents,PARENT,*['data/'+stem+'-basis-v1.json' for _,stem in BUILDERS],
        'scripts/compose_charge_normalization.py','scripts/check_charge_normalization.py','scripts/compose_material_charge.py',
        'scripts/check_material_charge.py','scripts/check_comoving_labels.py','scripts/check_coordinate_correspondence.py',
        'scripts/check_described_appraisals.py','scripts/check_plane_waveforms.py','scripts/check_real_products.py','scripts/check_moving_light_trip.py',
        'scripts/check_field_equations.py','scripts/check_rod_setup.py','noema/finite_semantics.py','noema/polynomial_proofs.py','noema/extraction.py',
        'artifacts/written-units-v1/einstein-1905.json']
    return dict(status='partial_divergence_normalization_and_material_charge',documents=documents,sizes=sizes,
        polynomial=polynomial_checks(),finite=finite_checks(texts[1:]),alignment=alignment(),new_definitions=8,new_primitives=0,new_author_statements=0,
        parent_preserved=True,roundtrips=True,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths})


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');options=parser.parse_args()
    report=build_report()
    if options.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Charge normalization report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Shared conversion, divergence traces and material charge bindings checked')


if __name__=='__main__':main()
