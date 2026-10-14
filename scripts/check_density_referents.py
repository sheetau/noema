"""Check referent identity separately from the truth of the five equations."""
import argparse
from fractions import Fraction as F
import hashlib
from itertools import product
import json

from noema.grammar import parse,format_graph,number_word
from noema.meaning_basis import audit_basis
from noema.script import encode,decode
from scripts.check_comoving_labels import values
from scripts.check_coordinate_correspondence import abstract
from scripts.check_described_appraisals import candidate
from scripts.check_plane_waveforms import setup,OPS
from scripts.check_rod_setup import callbacks,guarded
from scripts.check_field_equations import AXES,field_callback,jet_callback
from scripts.check_material_charge import numbers
from scripts.check_parallel_composition import transform
from scripts.compose_limits import call as k
from scripts.compose_density_referents import ROOT,PARENT,INPUTS,BINDINGS,PARTIALS,FORMULA,BUILDERS

REPORT=ROOT/'reports/density-referents-v1.json'
SYMBOLS={name:'jl'+number_word(i) for i,(name,_) in enumerate(INPUTS)}
CENTER=tuple(map(F,(1,2,3,4)))
DOMAIN=AXES+('matter','event','old','new','other')


def fixture():
    text=''.join('r '+SYMBOLS[n]+'[] '+sort+'.' for n,sort in INPUTS)
    return text+''.join('q['+k(symbol,*(k(SYMBOLS[n]) for n,_ in inputs))+'].' for symbol,inputs in
        (('senu',BINDINGS),('senv',INPUTS),('sens',FORMULA),('sent',PARTIALS)))


def model_for(doc,config=None,variant='baseline'):
    config=dict(config or numbers());cuts,model=setup(doc);make,read=cuts.make,cuts.read
    for name in ('light','speed','beta','density','ux','uy','uz','newdensity','vx','vy','vz'):
        model[SYMBOLS[name]]=lambda name=name:make(config[name])
    for name,value in dict(matter='matter',event='event',oldframe='old',newframe='new',context='text').items():
        model[SYMBOLS[name]]=lambda value=value:value
    originalold=tuple(transform(CENTER,-config['speed']))
    oldpoint=list(originalold)
    if variant.startswith('coordinate_'):oldpoint[AXES.index(variant[-1])]+=1
    field=[[F(1),F(4),F(5),F(6)],[F(7),F(2),F(8),F(9)],[F(10),F(11),config['newdensity']-3,F(12)]]
    jet=[row[:] for row in field]
    if variant=='compensated_diagonals':jet[0][0]+=1;jet[1][1]-=1
    def region(*xs):return read(xs[0])>0
    callbacks(doc,model,{
        SYMBOLS['newfield']:field_callback(doc,cuts,SYMBOLS['newfield'],field),
        SYMBOLS['newelectricjet']:jet_callback(cuts,jet),SYMBOLS['region']:region,
        SYMBOLS['point']:lambda axis:make(CENTER[AXES.index(axis)] if axis in AXES else 0),
        SYMBOLS['oldpoint']:lambda axis:make(oldpoint[AXES.index(axis)] if axis in AXES else 0)})
    observed=set()
    def match(actual,expected,category,labels):
        expected=list(expected)
        for i,label in enumerate(labels):
            if variant==category+'_'+label:expected[i]='other'
        return list(actual)==expected
    def assignment(matter,frame,event,density,ux,uy,uz,context):
        if variant=='unknown_assignment':raise ValueError('Quantity assignment missing')
        if frame not in ('old','new'):return False
        names=('density','ux','uy','uz') if frame=='old' else ('newdensity','vx','vy','vz')
        return match((matter,frame,event,read(density),read(ux),read(uy),read(uz),context),
            ('matter',frame,'event',*(config[n] for n in names),'text'),frame+'_assignment',
            ('matter','frame','event','density','ux','uy','uz','context'))
    def frames(old,new,speed,context):
        if variant=='unknown_frames':raise ValueError('Frame configuration missing')
        return match((old,new,read(speed),context),('old','new',config['speed'],'text'),'frames',('old','new','speed','context'))
    def field_assignment(frame,fn,domain,context):
        if variant=='unknown_electric':raise ValueError('Electric assignment missing')
        coefficients=tuple(tuple(read(fn(axis)(*(make(int(i==j)) for i in range(4)))) for j in range(4)) for axis in AXES[:3])
        return match((frame,coefficients,domain(*(make(x) for x in CENTER)),context),
            ('new',tuple(map(tuple,field)),True,'text'),'electric',('frame','field','region','context'))
    callbacks(doc,model,{SYMBOLS['assigned']:assignment,SYMBOLS['electricassigned']:field_assignment,SYMBOLS['frames']:frames})
    model['va']=lambda frame:frame in ('old','new') and variant!='invalid_'+frame+'_frame'
    def location(matter,frame,event,point,context):
        if variant=='unknown_location':raise ValueError('Event location missing')
        if frame not in ('old','new'):return False
        # Coordinate contrasts intentionally satisfy the location relation. Only
        # the four-coordinate correspondence must reject the shifted old point.
        expected=tuple(oldpoint) if frame=='old' else CENTER
        return match((matter,frame,event,tuple(read(point(a)) for a in AXES),context),
            ('matter',frame,'event',expected,'text'),frame+'_location',('matter','frame','event','point','context'))
    def partial(fn,domain,point,axis,value):
        if variant=='unknown_partial':raise ValueError('Partial derivative interpretation missing')
        coefficients=tuple(read(fn(*(make(int(i==j)) for i in range(4)))) for j in range(4))
        observed.add((coefficients,axis))
        return variant!='missing_'+axis and coefficients in list(map(tuple,field)) and tuple(read(point(a)) for a in AXES)==CENTER and domain(*(point(a) for a in AXES)) and read(value)==coefficients[AXES.index(axis)]
    model.update(zpb=location,s5t=partial)
    names={d['name'] for d in doc['declarations'] if d['kind']=='primitive'}
    return {n:f for n,f in model.items() if n in names},observed


def finite_checks(texts):
    docs=[abstract(candidate(text,fixture()),OPS|{'s5t'}) for text in texts]
    def run(**options):
        rows=[]
        for doc in docs:
            model,observed=model_for(doc,**options);rows.append(values(doc,model,DOMAIN))
            if {a for _,a in observed}!=set(AXES[:3]) or len(observed)!=3:raise ValueError('Unwanted derivative scope')
        if rows[0]!=rows[1]:raise ValueError('Extracted referents differ')
        return rows[0]
    cases=[]
    for speed,density,velocity in product((-3,0,3),(-4,0,4),((1,-2,3),(0,0,0),(10,0,0))):
        row=run(config=numbers(speed=speed,density=density,velocity=velocity))
        if row!=[True]*4:raise ValueError('Consistent referents rejected')
        cases.append(dict(speed=speed,density=density,velocity=list(velocity),results=row))
    variants=['frames_'+n for n in ('old','new','speed','context')]
    for prefix in ('old','new'):
        variants+= [prefix+'_location_'+n for n in ('matter','frame','event','point','context')]
        variants+= [prefix+'_assignment_'+n for n in ('matter','frame','event','density','ux','uy','uz','context')]
    variants+=['electric_'+n for n in ('frame','field','region','context')]
    variants+=['invalid_old_frame','invalid_new_frame']+['coordinate_'+axis for axis in AXES]
    contrasts={}
    for variant in variants:
        row=run(variant=variant)
        if row!=[False,False,True,True]:raise ValueError('Numerical agreement replaced referents: '+variant)
        contrasts[variant]=row
    derivatives={}
    for variant in ('compensated_diagonals','missing_x','missing_y','missing_z'):
        row=run(variant=variant)
        if row!=[True,False,True,False]:raise ValueError('Referents replaced actual derivatives')
        derivatives[variant]=row
    for doc in docs:
        for variant in ('unknown_assignment','unknown_frames','unknown_electric','unknown_location','unknown_partial'):
            model,_=model_for(doc,variant=variant)
            try:values(doc,model,DOMAIN)
            except ValueError as exc:
                if 'missing' not in str(exc):raise
            else:raise ValueError('Unknown interpretation filled in')
    return dict(cases=cases,binding_contrasts=contrasts,derivative_contrasts=derivatives,
        standalone_agrees=True,unknown_interpretations_refused=True,exactly_three_new_partials=True,
        no_old_field_or_magnetic_conditions_executed=True,actual_physical_assignments_validated=False)


def build_report():
    texts=[];documents={};sizes={}
    for builder,stem in BUILDERS:
        text,basis=builder();doc=parse(text);texts.append(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text or json.loads((ROOT/('data/'+stem+'-basis-v1.json')).read_text(encoding='utf-8'))!=basis:raise ValueError('Stored referents differ')
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Referents roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis);sizes[stem]=dict(characters=len(text),statements=len(doc['statements']))
    doc,parent=parse(texts[0]),parse((ROOT/PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])]!=parent['declarations'] or doc['statements']!=parent['statements']:raise ValueError('Parent changed')
    previous=json.loads((ROOT/'reports/density-formula-v1.json').read_text(encoding='utf-8'))
    segment=dict(previous['alignment']['segments'][0]);segment.update(definitions=['senu','senv'],review_ja='同じ物質・出来事・文脈に新旧の量を結び、必要な新電場だけを参照する。関係引数の実際の物理的解釈と著者の導入は未完。')
    paths=[*documents,PARENT,*['data/'+stem+'-basis-v1.json' for _,stem in BUILDERS],
        'reports/density-formula-v1.json','data/density-formula-review-v1.json',
        'scripts/compose_density_referents.py','scripts/check_density_referents.py',
        'scripts/compose_density_formula.py','scripts/check_material_charge.py','scripts/check_parallel_composition.py',
        'scripts/check_field_equations.py','scripts/check_comoving_labels.py','scripts/check_coordinate_correspondence.py',
        'scripts/check_described_appraisals.py','scripts/check_plane_waveforms.py','scripts/check_rod_setup.py',
        'noema/finite_semantics.py','noema/extraction.py']
    return dict(status='partial_isolated_formula_referents',documents=documents,sizes=sizes,finite=finite_checks(texts),
        alignment=dict(segments=[segment],semantic_completion=False),new_definitions=2,new_primitives=0,new_author_statements=0,
        parent_preserved=True,roundtrips=True,verified_full_units={'kant-1784':0,'einstein-1905':0},
        remaining=['author_introduction','physical_concept_grounding','whole_unit_semantic_review'],
        source_sha256={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths})


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');options=parser.parse_args();report=build_report()
    if options.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Referents report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Shared matter/event/frames, coordinates and required electric partials checked')


if __name__=='__main__':main()
