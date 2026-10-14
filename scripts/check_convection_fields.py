"""Check signed convection terms, twenty-one partials and the printed variant."""
import argparse
from fractions import Fraction as F
import hashlib
from itertools import product
import json

from noema.finite_semantics import FunctionValue
from noema.grammar import parse,format_graph,number_word
from noema.meaning_basis import audit_basis
from noema.polynomial_proofs import verify_universal
from noema.script import encode,decode
from scripts.check_comoving_labels import values
from scripts.check_coordinate_correspondence import abstract
from scripts.check_described_appraisals import candidate
from scripts.check_field_equations import AXES,field_callback,jet_callback
from scripts.check_plane_waveforms import setup as cut_setup,OPS
from scripts.check_rod_setup import callbacks
from scripts.check_real_products import MEANINGS as ARITHMETIC,assertion
from scripts.check_moving_light_trip import literal
from scripts.compose_limits import call as k,app,op,both,v
from scripts.compose_convection_fields import ROOT,PARENT,BUILDERS,INPUTS,POINT_FIELDS,REGIONAL,BALANCE,ROOTS,generic_composed

REPORT=ROOT/'reports/convection-fields-v1.json'
FACSIMILE=ROOT/'data/convection-fields-facsimile-v1.json'
SYMBOLS={name:'jw'+number_word(i) for i,(name,_) in enumerate(INPUTS)}
DOMAIN=AXES+('matter','frame','event','other')
CENTER=(F(1),F(2),F(3),F(4))


def polynomial_checks():
    light,rate,positive,negative,density,drift,other,C,charge,xx,yy,zz=map(v,('light','rate','positive','negative','density','drift','other','conversion','charge','xx','yy','zz'))
    zero,one=literal(0),literal(1)
    add=lambda a,b:k('ab',a,b);neg=lambda a:k('ac',a);mul=lambda a,b:k('ad',a,b)
    rel=lambda r=rate,d=density,u=drift:k('sema',light,r,positive,negative,d,u)
    dense=lambda d=density,q=charge:k('semb',d,q,C,xx,yy,zz)
    claims={
        'zero_density_reduces_to_source_free_balance':assertion('light rate positive negative drift',op('z',rel(d=zero),both(k('aa',zero,light),op('e',rate,mul(light,add(positive,neg(negative))))))),
        'reversing_charge_and_flow_together_preserves_current':assertion('light rate positive negative density drift',op('z',rel(),rel(d=neg(density),u=neg(drift)))),
        'fixed_current_determines_rate_uniquely':assertion('light rate positive negative density drift other',op('y',both(rel(),rel(r=other)),op('e',rate,other))),
        'zero_density_does_not_force_zero_velocity':assertion('light rate positive negative drift',op('y',rel(d=zero),op('e',drift,zero))),
        'reversing_density_alone_always_preserves_equation':assertion('light rate positive negative density drift',op('y',rel(),rel(d=neg(density)))),
        'trace_fixes_scaled_density':assertion('density other charge conversion xx yy zz',op('y',both(dense(),dense(d=other)),op('e',density,other))),
        'positive_conversion_fixes_charge':assertion('density charge other conversion xx yy zz',op('y',both(dense(),dense(q=other)),op('e',charge,other))),
        'scaled_density_is_not_always_charge':assertion('density charge conversion xx yy zz',op('y',dense(),op('e',density,charge))),
        'magnetic_forms_agree_at_unit_light':assertion('rate positive negative',op('z',k('sema',one,rate,positive,negative,zero,zero),op('e',rate,add(positive,neg(negative))))),
        'nonunit_light_and_nonzero_curl_distinguish_printed_form':assertion('light rate positive negative',op('y',both(rel(d=zero,u=zero),op('u',op('e',light,one)),op('u',op('e',positive,negative))),op('u',op('e',rate,add(positive,neg(negative)))))),
    }
    invalid={'zero_density_does_not_force_zero_velocity','reversing_density_alone_always_preserves_equation','scaled_density_is_not_always_charge'}
    rows={}
    for label,claim in claims.items():
        result=verify_universal(parse(generic_composed()[0]+claim),ARITHMETIC,timeout_ms=20000)[0]
        if result['status']!=('invalid' if label in invalid else 'valid'):raise ValueError('Convection algebra differs: '+label)
        rows[label]=result
    return dict(claims=rows,rational_algebra_only=True,full_real_field_transformation_proved=False)


def expression(name):return k(SYMBOLS[name])


def sampled_fields():
    coords=[app(expression('point'),k(role)) for role in ('yn','yo','yp','zc7')]
    return dict(density=app(expression('densityfield'),*coords),
        velocity='i[axis a]['+app(app(expression('velocityfield'),'v axis'),*coords)+']')


def setup_document(text):
    if set(SYMBOLS.values()) & {d['name'] for d in parse(text)['declarations']}:raise ValueError('Convection fixture symbols collide')
    extra=''.join('r '+SYMBOLS[n]+'[] '+sort+'.' for n,sort in INPUTS)
    point_values=sampled_fields()
    balance=[point_values[n] if n in point_values else expression(n) for n,_ in BALANCE]
    queries=[k('semd',expression('electricjet'),point_values['density']),k('seme',*balance),k('semf',*balance),
        k('semg',*(expression(n) for n in ('electric','magnetic','region','point','electricjet','magneticjet'))),
        k('semn',*(expression(n) for n,_ in INPUTS)),k('semo',*(expression(n) for n,_ in INPUTS))]
    return abstract(candidate(text,extra+''.join('q['+q+'].' for q in queries)),OPS|{'s5t','sedi'})


def matrices(light=F(5),density=F(4),velocity=(F(1),F(-2),F(3)),printed=False):
    e=[[F(2),F(3),F(5),F(0)],[F(7),F(3),F(11),F(0)],[F(13),F(17),density-5,F(0)]]
    h=[[F(19),F(23),F(29),F(0)],[F(31),F(37),F(41),F(0)],[F(43),F(47),F(53),F(0)]]
    for i in range(3):
        j,l=(i+1)%3,(i+2)%3
        e[i][3]=light*(h[l][j]-h[j][l])-density*velocity[i]
        h[i][3]=(1 if printed else light)*(e[j][l]-e[l][j])
    return e,h


def model_for(doc,*,light=F(5),density=F(4),velocity=(F(1),F(-2),F(3)),printed=False,variant='baseline'):
    fixture,model=cut_setup(doc);c,n=fixture.make,fixture.read
    e,h=matrices(light,density,velocity,printed);ej=[row[:] for row in e];hj=[row[:] for row in h]
    if variant.startswith('jet_'):
        _,field,i,j=variant.split('_');(ej if field=='E' else hj)[int(i)][int(j)]+=F(1,4)
    wrongpoint=tuple(x+(1 if i==0 and variant=='wrong_point' else 0) for i,x in enumerate(CENTER))
    declared_light=F(0) if variant=='zero_light' else F(-5) if variant=='negative_light' else light
    rho=density+(1 if variant=='density_value' else 0)
    charge=density/12+(1 if variant=='charge_value' else 0)
    speed=tuple(x+(1 if i==0 and variant=='velocity_value' else 0) for i,x in enumerate(velocity))
    def constant_vector(role):
        sort=next(d['result']['result'] for d in doc['declarations'] if d['name']==SYMBOLS['velocityfield'])
        value=speed[AXES.index(role)] if role in AXES[:3] else F(0)
        return FunctionValue(tuple(sort['parameters']),sort['result'],lambda *xs:c(value))
    def region(*xs):return variant!='outside_region' and n(xs[0])>0
    callbacks(doc,model,{
        SYMBOLS['electric']:field_callback(doc,fixture,SYMBOLS['electric'],h if variant=='swapped_fields' else e),
        SYMBOLS['magnetic']:field_callback(doc,fixture,SYMBOLS['magnetic'],e if variant=='swapped_fields' else h),
        SYMBOLS['region']:region,SYMBOLS['point']:lambda axis:c(wrongpoint[AXES.index(axis)] if axis in AXES else 0),
        SYMBOLS['electricjet']:jet_callback(fixture,ej),SYMBOLS['magneticjet']:jet_callback(fixture,hj),
        SYMBOLS['densityfield']:lambda *xs:c(rho),SYMBOLS['chargefield']:lambda *xs:c(charge),SYMBOLS['velocityfield']:constant_vector})
    for name,value in (('matter','matter'),('frame','frame'),('event','event'),('context','text')):model[SYMBOLS[name]]=lambda value=value:value
    model[SYMBOLS['light']]=lambda:c(declared_light);model[SYMBOLS['pi']]=lambda:c(3)
    observed=set()
    def partial(fn,domain,point,axis,value):
        if variant=='unknown_partial':raise ValueError('Partial derivative interpretation missing')
        coefficients=tuple(n(fn(*(c(int(i==j)) for i in range(4)))) for j in range(4))
        observed.add((coefficients,axis))
        return variant!='missing_partial' and coefficients in [tuple(row) for row in e+h] and tuple(n(point(a)) for a in AXES)==CENTER and domain(*(point(a) for a in AXES)) and n(value)==coefficients[AXES.index(axis)]
    model['s5t']=partial
    model['sedi']=lambda pi:variant!='missing_pi' and n(pi)==3
    model['va']=lambda frame:frame=='frame' and variant!='not_frame'
    def field_values(field):
        return tuple(tuple(n(field(a)(*(c(int(i==j)) for i in range(4)))) for j in range(4)) for a in AXES[:3])
    def match(actual,expected,category,labels):
        expected=list(expected)
        for i,label in enumerate(labels):
            if variant==category+'_'+label:expected[i]='other'
        return list(actual)==expected
    def assign(matter,frame,densityfield,chargefield,velocityfield,domain,context):
        if variant=='unknown_assignment':raise ValueError('Charge/flow assignment missing')
        probe=[c(x) for x in CENTER]
        return match((matter,frame,context),('matter','frame','text'),'assignment',('matter','frame','context')) and variant!='assignment_region' and domain(*probe) and n(densityfield(*probe))==density and n(chargefield(*probe))==density/12 and tuple(n(velocityfield(a)(*probe)) for a in AXES[:3])==velocity
    callbacks(doc,model,{SYMBOLS['assigned']:assign})
    model['znn']=lambda frame,ef,hf,domain,context:match((frame,context),('frame','text'),'field',('frame','context')) and field_values(ef)==tuple(map(tuple,e)) and field_values(hf)==tuple(map(tuple,h)) and variant!='field_region' and domain(*(c(x) for x in CENTER))
    model['zpb']=lambda matter,frame,event,point,context:match((matter,frame,event,context),('matter','frame','event','text'),'location',('matter','frame','event','context')) and tuple(n(point(a)) for a in AXES)==CENTER
    return model,observed


def evaluate(doc,model):
    names={d['name'] for d in doc['declarations'] if d['kind']=='primitive'}
    return values(doc,{n:x for n,x in model.items() if n in names},DOMAIN)


def binding_checks(texts):
    docs=[setup_document(text) for text in texts]
    def run(**options):
        rows=[];observed=[]
        for doc in docs:
            model,seen=model_for(doc,**options);rows.append(evaluate(doc,model));observed.append(len(seen))
        if rows[0]!=rows[1]:raise ValueError('Extracted convection field differs')
        return rows[0],observed
    cases=[]
    for light,density,velocity,printed in product((F(1),F(5)),(F(-4),F(0),F(4)),((F(1),F(-2),F(3)),(F(-1),F(2),F(-3))),(False,True)):
        row,observed=run(light=light,density=density,velocity=velocity,printed=printed)
        standard=not printed or light==1;raw=printed or light==1
        if row!=[True,standard,raw,True,standard,raw] or observed!=[21,21]:raise ValueError('Convection current sign, density or printed form differs')
        cases.append(dict(light=str(light),density=str(density),velocity=list(map(str,velocity)),printed_fixture=printed,results=row,distinct_partials=21))
    contrasts={}
    # Change each actually used partial. The three unused H diagonal entries remain free.
    for field in ('E','H'):
        for i,j in product(range(3),range(4)):
            name=f'jet_{field}_{i}_{j}';row,_=run(variant=name)
            if field=='H' and i==j:
                if row!=[True,True,False,True,True,False]:raise ValueError('Unused magnetic diagonal became a source assumption')
            elif row[3] or row[4] or row[5]:raise ValueError('Changed derivative not bound to its field: '+name)
            contrasts[name]=row
    for variant in ('zero_light','negative_light','density_value','charge_value','velocity_value','wrong_point','outside_region',
        'swapped_fields','missing_partial','missing_pi','not_frame','field_frame','field_context','field_region',
        *('location_'+f for f in ('matter','frame','event','context')),
        *('assignment_'+f for f in ('matter','frame','context','region'))):
        row,_=run(variant=variant)
        if row[4] or row[5]:raise ValueError('Convection source binding lost: '+variant)
        contrasts[variant]=row
    for doc in docs:
        for variant,message in (('unknown_partial','Partial derivative interpretation missing'),('unknown_assignment','Charge/flow assignment missing')):
            model,_=model_for(doc,variant=variant)
            try:evaluate(doc,model)
            except ValueError as exc:
                if message not in str(exc):raise
            else:raise ValueError('Unknown convection input supplied')
    return dict(cases=cases,contrasts=contrasts,standalone_agrees=True,unknown_inputs_refused=True,
        all_twenty_one_used_partials_checked=True,magnetic_diagonal_partials_not_required=True,
        real_arithmetic_abstracted_to_registered_rational_cuts=True,derivatives_use_explicit_affine_oracle=True,
        pi_integral_abstracted_with_synthetic_value_three=True,full_real_domain_or_physical_assignment_proved=False)


def facsimile_check():
    ledger=json.loads(FACSIMILE.read_text(encoding='utf-8'))
    for item in [ledger['pdf'],*ledger['images']]:
        if hashlib.sha256((ROOT/item['path']).read_bytes()).hexdigest()!=item['sha256']:raise ValueError('Convection facsimile changed')
    source=json.loads((ROOT/'artifacts/written-units-v1/einstein-1905.json').read_text(encoding='utf-8'))
    byid={m['id']:m for m in source['math']}
    for name,digest in ledger['snapshot_math_sha256'].items():
        if byid[name]['sha256']!=digest:raise ValueError('Convection snapshot changed')
    if ledger['discrepancy']['is_transcription_correction'] or ledger['snapshot_modified']:raise ValueError('Printed equation was silently corrected')
    return ledger


def alignment():
    source=json.loads((ROOT/'artifacts/written-units-v1/einstein-1905.json').read_text(encoding='utf-8'))
    units={u['id'].split(':')[-1]:u for u in source['units']};math={m['id']:m for m in source['math']};segments=[]
    for uid,mid,definitions in (('u0229','M0383',['semc','seme','semg','semh','semj']),('u0231','M0384',['semd']),
        ('u0232','M0385',['seml']),('u0232','M0386',['seme','semn']),('u0234','M0389',['semf','semi','semk','semo'])):
        unit=units[uid]
        segments.append(dict(unit=unit['id'],unit_sha256=unit['text_sha256'],math_id=mid,math_sha256=math[mid]['sha256'],
            definitions=definitions,status='partial',review_ja='同じ場・地点の偏微分に密度と流速を結び、原刊の変換後の磁気側の係数相違を別に保持する。全実関数の微分・変換、物理的帰属と全文意味一致は未完。'))
    unit=units['u0232'];excerpt='die [M0385]-fache Dichte der Elektrizität und ([M0386]) den Geschwindigkeitsvektor der Elektrizität bedeutet.'
    if unit['text'].count(excerpt)!=1:raise ValueError('Ambiguous charge density source range')
    start=unit['text'].index(excerpt)
    segments.append(dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[start,start+len(excerpt)],text=excerpt,
        definitions=['semd','seml','semm','semn'],status='partial',review_ja='規格化した密度が電荷密度の4π倍であることと、同じ物質・系・地点への速度成分場の帰属を明示する。電気量の測定、電子・イオンの意味、単位系、全文意味一致は未完。'))
    return dict(segments=segments,semantic_completion=False)


def build_report():
    documents,sizes,texts={},{},[]
    for builder,stem in BUILDERS:
        text,basis=builder();doc=parse(text);texts.append(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text or json.loads((ROOT/('data/'+stem+'-basis-v1.json')).read_text(encoding='utf-8'))!=basis:raise ValueError('Stored convection fields differ')
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Convection fields roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis);sizes[stem]=dict(characters=len(text),statements=len(doc['statements']))
    doc,parent=parse(texts[1]),parse((ROOT/PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])]!=parent['declarations'] or doc['statements']!=parent['statements']:raise ValueError('Parent changed')
    facsimile=facsimile_check()
    paths=[*documents,PARENT,*['data/'+stem+'-basis-v1.json' for _,stem in BUILDERS],
        'data/convection-fields-facsimile-v1.json','scripts/compose_convection_fields.py','scripts/check_convection_fields.py',
        'scripts/check_field_equations.py','scripts/check_plane_waveforms.py','scripts/check_rod_setup.py',
        'scripts/check_comoving_labels.py','scripts/check_real_products.py','noema/finite_semantics.py','noema/polynomial_proofs.py',
        'noema/extraction.py','artifacts/written-units-v1/einstein-1905.json']
    return dict(status='partial_convection_field_equations_and_printed_magnetic_variant',documents=documents,sizes=sizes,
        polynomial=polynomial_checks(),binding=binding_checks(texts[1:]),facsimile=facsimile,alignment=alignment(),
        new_definitions=15,new_primitives=0,new_author_statements=0,parent_preserved=True,roundtrips=True,
        verified_full_units={'kant-1784':0,'einstein-1905':0},source_sha256={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in paths})


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args()
    report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Convection fields report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:
            json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Convection terms, density, field bindings and printed magnetic variant checked')


if __name__=='__main__':main()
