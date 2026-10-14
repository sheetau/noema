"""Review one source formula without treating physics proofs as translation."""
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
from scripts.check_field_equations import AXES,field_callback,jet_callback
from scripts.check_rod_setup import callbacks,guarded
from scripts.compose_limits import call as k,app,op,both,v
from scripts.compose_density_formula import ROOT,PARENT,BUILDERS,FLOW,RATIONAL,FORMULA,PARTIALS,CUT,generic_composed

REPORT=ROOT/'reports/density-formula-v1.json'
REVIEW=ROOT/'data/density-formula-review-v1.json'
SYMBOLS={name:'jk'+number_word(i) for i,(name,_) in enumerate(PARTIALS)}
CENTER=tuple(map(F,(1,2,3,4)))
DOMAIN=AXES+('other',)
RELATIONS=('velocity_longitudinal','velocity_second','velocity_third','density_divergence','density_boost')
OBLIGATIONS=('source_form','algebraic_scope','shared_density','derivative_referents','unwanted_premises',
             'source_context_bindings','discourse_role','concept_grounding','source_truth','whole_unit_decision')


def review_packet(packet,doc):
    if packet.get('version')!='density-formula-review-v1' or packet.get('unit')!='einstein-1905:u0236' or packet.get('math_id')!='M0390':
        raise ValueError('Review source identity differs')
    byname={d['name']:d for d in doc['declarations']}
    if packet.get('document')!='examples/v014/einstein-density-formula.noema' or packet.get('definition')!='sens' or packet.get('derivative_connection')!='sent':
        raise ValueError('Review definition identity differs')
    bindings=packet.get('parameter_bindings',[])
    if len(bindings)!=len(byname['sens']['parameters']) or [b['index'] for b in bindings]!=list(range(len(FORMULA))):
        raise ValueError('Review parameter map is incomplete or duplicated')
    if any(not b.get('source') or not b.get('meaning') for b in bindings):raise ValueError('Unexplained parameter map')
    relations=packet.get('source_relations',[])
    if tuple(r['id'] for r in relations)!=RELATIONS:raise ValueError('Five source relations must be reviewed separately')
    if [r['output_parameter'] for r in relations]!=[8,9,10,7,7]:raise ValueError('Shared density or velocity output was moved')
    if [r['input_parameters'] for r in relations]!=[[0,1,4],[0,1,2,4,5],[0,1,2,4,6],[11],[0,1,2,3,4]]:
        raise ValueError('Source relation input references differ')
    for r in relations:
        if not r.get('formula') or any(type(i) is not int or not 0<=i<len(bindings) for i in r['input_parameters']):
            raise ValueError('Invalid source relation references')
    checks=packet.get('checks',[])
    if tuple(c['id'] for c in checks)!=OBLIGATIONS:raise ValueError('Incomplete unit review obligations')
    for c in checks:
        if c.get('status') not in ('checked','open','not_a_translation_gate') or not c.get('evidence') or not c.get('limit'):
            raise ValueError('Review status lacks evidence or its limit')
        if c['status']=='not_a_translation_gate' and c['id']!='source_truth':raise ValueError('A translation obligation was silently excluded')
    if checks[8]['status']!='not_a_translation_gate':raise ValueError('Source truth is not a translation obligation')
    open_items=[c['id'] for c in checks if c['status']=='open']
    if not {'source_context_bindings','discourse_role','concept_grounding','whole_unit_decision'}<=set(open_items):
        raise ValueError('Current review cannot close unresolved semantic obligations')
    if packet.get('semantic_completion') is not False:raise ValueError('This packet is not a completion certificate')
    return dict(checked=[c['id'] for c in checks if c['status']=='checked'],open=open_items,
        source_truth_is_not_a_translation_gate=True,decision='partial',semantic_completion=False)


def polynomial_checks():
    mul=lambda a,b:k('ad',a,b);add=lambda a,b:k('ab',a,b);sub=lambda a,b:add(a,k('ac',b));eq=lambda a,b:op('e',a,b)
    square=mul(v('light'),v('light'));delta=sub(literal(1),mul(mul(v('ux'),v('speed')),v('inverselight')))
    defined=both(k('sra',v('light'),v('speed'),v('beta')),eq(mul(square,v('inverselight')),literal(1)),
        eq(mul(v('beta'),v('inversebeta')),literal(1)),eq(mul(delta,v('reciprocal')),literal(1)))
    source=both(eq(v('vx'),mul(sub(v('ux'),v('speed')),v('reciprocal'))),
        eq(v('vy'),mul(mul(v('uy'),v('reciprocal')),v('inversebeta'))),
        eq(v('vz'),mul(mul(v('uz'),v('reciprocal')),v('inversebeta'))),
        eq(v('newdensity'),add(add(v('newexx'),v('neweyy')),v('newezz'))),
        eq(v('newdensity'),mul(mul(v('beta'),delta),v('density'))))
    formula=k('senr',*map(v,RATIONAL.split()))
    def concrete(config):
        row=dict(config,newexx=F(1),neweyy=F(2),newezz=config['newdensity']-3)
        return k('senr',*(literal(row[n]) for n in RATIONAL.split()))
    reversed_denominator=numbers(velocity=(10,0,0));negative=numbers(density=-4)
    claims={
        'five_fraction_relations_iff_isolated_formula':assertion(RATIONAL+' inverselight inversebeta reciprocal',op('y',defined,op('z',source,formula))),
        'negative_nonzero_denominator_is_not_omitted':assertion('',concrete(reversed_denominator)),
        'formula_imposes_subluminal_material_speed':assertion('',op('y',concrete(reversed_denominator),k('aa',literal(10),literal(5)))),
        'formula_requires_positive_density':assertion('',op('y',concrete(negative),k('aa',literal(0),literal(-4)))),
    }
    rows={};base=generic_composed()[0]
    for name,claim in claims.items():
        result=verify_universal(parse(base+claim),MEANINGS,timeout_ms=25000,max_expansion=250000)[0]
        want='invalid' if name in ('formula_imposes_subluminal_material_speed','formula_requires_positive_density') else 'valid'
        if result['status']!=want:raise ValueError('Source formula equivalence '+name+': '+result['status'])
        rows[name]=result
    return dict(claims=rows,rational_defined_domain_equivalence_only=True,empirical_electrodynamics_proved=False)


def expression(name):return k(SYMBOLS[name])


def fixture():
    text=''.join('r '+SYMBOLS[n]+'[] '+sort+'.' for n,sort in PARTIALS)
    queries=[k('sens',*(expression(n) for n,_ in FORMULA)),k('sent',*(expression(n) for n,_ in PARTIALS)),
        k('semt',*(expression(n) for n in FLOW.split())),k('semd',expression('newelectricjet'),expression('newdensity'))]
    return text+''.join('q['+q+'].' for q in queries)


def model_for(doc,config=None,changes=None,variant='baseline'):
    original=dict(config or numbers());row=dict(original);row.update(changes or {})
    cuts,model=setup(doc);make,read=cuts.make,cuts.read
    for name in FLOW.split():model[SYMBOLS[name]]=lambda name=name:make(row[name])
    field=[[F(1),F(4),F(5),F(6)],[F(7),F(2),F(8),F(9)],[F(10),F(11),original['newdensity']-3,F(12)]]
    jet=[r[:] for r in field]
    if variant.startswith('jet_'):
        _,i,j=variant.split('_');jet[int(i)][int(j)]+=1
    if variant=='compensated_diagonals':jet[0][0]+=1;jet[1][1]-=1
    if variant=='field_diagonal':field[0][0]+=1
    if variant=='field_offdiagonal':field[0][1]+=1
    point=tuple(x+1 if i==0 and variant=='wrong_point' else x for i,x in enumerate(CENTER))
    def region(*xs):return variant!='outside_region' and read(xs[0])>0
    callbacks(doc,model,{
        SYMBOLS['newfield']:field_callback(doc,cuts,SYMBOLS['newfield'],field),SYMBOLS['newelectricjet']:jet_callback(cuts,jet),
        SYMBOLS['region']:region,SYMBOLS['point']:lambda axis:make(point[AXES.index(axis)] if axis in AXES else 0)})
    observed=set()
    def partial(fn,domain,location,axis,value):
        if variant=='unknown_partial':raise ValueError('Partial derivative interpretation missing')
        coefficients=tuple(read(fn(*(make(int(i==j)) for i in range(4)))) for j in range(4))
        observed.add((coefficients,axis))
        return variant!='missing_'+axis and coefficients in list(map(tuple,field)) and tuple(read(location(a)) for a in AXES)==CENTER and \
            domain(*(location(a) for a in AXES)) and read(value)==coefficients[AXES.index(axis)]
    model['s5t']=partial
    used={d['name'] for d in doc['declarations'] if d['kind']=='primitive'}
    return {n:f for n,f in model.items() if n in used},observed


def finite_checks(texts):
    docs=[abstract(candidate(text,fixture()),OPS|{'s5t'}) for text in texts]
    def run(**options):
        rows=[]
        for doc in docs:
            model,observed=model_for(doc,**options);rows.append(values(doc,model,DOMAIN))
            if {axis for _,axis in observed}!=set(AXES[:3]) or len(observed)!=3:raise ValueError('Wrong partial derivative scope')
        if rows[0]!=rows[1]:raise ValueError('Source and extracted isolated formulas differ')
        return rows[0]
    cases=[]
    for speed,density,velocity in product((-3,0,3),(-4,0,4),((1,-2,3),(0,0,0),(10,0,0))):
        config=numbers(speed=speed,density=density,velocity=velocity)
        row=run(config=config)
        if row!=[True]*4:raise ValueError('Five equations gained an extra premise')
        cases.append(dict(speed=speed,density=density,velocity=list(velocity),results=row))
    contrasts={}
    for i,j in product(range(3),range(4)):
        variant=f'jet_{i}_{j}';row=run(variant=variant)
        if row!=([False,False,True,False] if i==j else [True]*4):raise ValueError('Derivative subset differs')
        contrasts[variant]=row
    for variant in ('compensated_diagonals','field_diagonal','wrong_point','outside_region','missing_x','missing_y','missing_z'):
        row=run(variant=variant)
        if row!=[True,False,True,True]:raise ValueError('Same trace was mistaken for actual derivatives: '+variant)
        contrasts[variant]=row
    if run(variant='field_offdiagonal')!=[True]*4:raise ValueError('Irrelevant field derivative restricted source formula')
    contrasts['field_offdiagonal']=[True]*4
    config=numbers()
    for name in FLOW.split():
        # Keep the square root rational when changing V alone; beta is still wrong.
        changed=F(15,4) if name=='light' else config[name]+1
        row=run(changes={name:changed})
        if row!=[False,False,False,name!='newdensity']:raise ValueError('Scalar identity ignored: '+name)
        contrasts['scalar_'+name]=row
    row=run(changes={'ux':F(25,3)})
    if row!=[False,False,False,True]:raise ValueError('Undefined denominator accepted')
    contrasts['zero_denominator']=row
    for doc in docs:
        for name in ('newfield','region','point','newelectricjet'):
            model,_=model_for(doc);model[SYMBOLS[name]]=guarded(doc)[SYMBOLS[name]]
            try:values(doc,model,DOMAIN)
            except ValueError as exc:
                if 'Unrelated primitive' not in str(exc):raise
            else:raise ValueError('Unknown derivative input filled in')
        model,_=model_for(doc,variant='unknown_partial')
        try:values(doc,model,DOMAIN)
        except ValueError as exc:
            if 'Partial derivative interpretation missing' not in str(exc):raise
        else:raise ValueError('Unknown derivative became a numerical equality')
    return dict(cases=cases,contrasts=contrasts,standalone_agrees=True,exactly_three_new_diagonal_partials=True,
        old_field_magnetic_and_other_derivatives_not_executed=True,unknown_inputs_refused=True,
        full_source_context_or_author_introduction_completed=False)


def source_record(doc):
    packet=json.loads(REVIEW.read_text(encoding='utf-8'));review=review_packet(packet,doc)
    facsimile=json.loads((ROOT/packet['facsimile_record']).read_text(encoding='utf-8'))
    source=json.loads((ROOT/'artifacts/written-units-v1/einstein-1905.json').read_text(encoding='utf-8'))
    unit=next(u for u in source['units'] if u['id']==packet['unit']);math=next(m for m in source['math'] if m['id']==packet['math_id'])
    if math['id'] not in unit['math_ids'] or facsimile['snapshot_math_sha256'][math['id']]!=math['sha256']:raise ValueError('Reviewed source mathematics changed')
    for asset in [facsimile['pdf'],*facsimile['images']]:
        if hashlib.sha256((ROOT/asset['path']).read_bytes()).hexdigest()!=asset['sha256']:raise ValueError('Reviewed facsimile changed')
    alignment=dict(segments=[dict(unit=unit['id'],unit_sha256=unit['text_sha256'],math_id=math['id'],math_sha256=math['sha256'],
        definitions=['senr','sens','sent'],status='partial',review_ja='五つの等式の条件を単独化し、新側の必要な三微分へ結ぶ。記号の文脈上の参照先とwobeiによる導入は未完。物理命題の真理の証明と翻訳の意味確認を分け、完成へ昇格しない。')],semantic_completion=False)
    return review,alignment


def build_report():
    documents,sizes,texts={},{},[]
    for builder,stem in BUILDERS:
        text,basis=builder();doc=parse(text);texts.append(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text or json.loads((ROOT/('data/'+stem+'-basis-v1.json')).read_text(encoding='utf-8'))!=basis:raise ValueError('Stored density formula differs')
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Density formula roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis);sizes[stem]=dict(characters=len(text),statements=len(doc['statements']))
    doc,parent=parse(texts[1]),parse((ROOT/PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])]!=parent['declarations'] or doc['statements']!=parent['statements']:raise ValueError('Parent changed')
    review,alignment=source_record(doc)
    paths=[*documents,PARENT,*['data/'+stem+'-basis-v1.json' for _,stem in BUILDERS],
        'data/density-formula-review-v1.json','data/density-boost-facsimile-v1.json',
        'scripts/compose_density_formula.py','scripts/check_density_formula.py','scripts/compose_density_boost.py',
        'scripts/check_material_charge.py','scripts/check_field_equations.py','scripts/check_comoving_labels.py',
        'scripts/check_coordinate_correspondence.py','scripts/check_described_appraisals.py','scripts/check_plane_waveforms.py',
        'scripts/check_real_products.py','scripts/check_moving_light_trip.py','scripts/check_rod_setup.py',
        'noema/finite_semantics.py','noema/polynomial_proofs.py','noema/extraction.py','artifacts/written-units-v1/einstein-1905.json']
    return dict(status='partial_isolated_source_formula_and_explicit_review_obligations',documents=documents,sizes=sizes,
        polynomial=polynomial_checks(),finite=finite_checks(texts[1:]),unit_review=review,alignment=alignment,
        new_definitions=3,new_primitives=0,new_author_statements=0,parent_preserved=True,roundtrips=True,
        verified_full_units={'kant-1784':0,'einstein-1905':0},source_sha256={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths})


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');options=parser.parse_args()
    report=build_report()
    if options.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Density formula report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Isolated source equations, three partials and open semantic review obligations checked')


if __name__=='__main__':main()
