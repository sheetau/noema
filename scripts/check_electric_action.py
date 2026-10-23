"""Check electric-force signs, units, records and local field evaluation."""
from functools import lru_cache
from itertools import product
from fractions import Fraction as Q
import json
from noema.grammar import parse,format_graph,number_word
from noema.finite_semantics import FunctionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_material_relative_frame import arithmetic,NUM,RS
from scripts.compose_electric_action import ROOT,read,PARENT,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,FIELDS,build

DOC='docs/electric-action-v1.md';PRIOR='data/einstein-author-credit-review-v1.json';SOURCE='data/einstein-opening-obligations-v1.json'
DOMAIN=('carrier','frame','event','chargerecord','forcerecord','chargeunit','fieldunit','forceunit','chargekind','forcekind','x','y','z','t','other')
CONTEXTS=('case','other');AXES=('x','y','z');ALLAXES=AXES+('t',)
TAU=dict(kind='function',parameters=[RS]*4,result=RS)

def forbidden(*args):raise ValueError('Unknown electric-action input')

@lru_cache(None)
def fixture(symbol):
    doc=parse(read(CORE));doc['statements']=[];abstract(doc,NUM)
    d=next(d for d in doc['declarations'] if d['name']==symbol);slots=[];arguments=[]
    for i,p in enumerate(d['parameters']):
        n='jeac'+number_word(i);slots.append((n,p['sort']))
        doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
        arguments.append(dict(kind='call',symbol=n,arguments=[]))
    doc['statements']=[dict(kind='ask',body=dict(kind='call',symbol=symbol,arguments=arguments))]
    return doc,slots

def run(symbol,values,model):
    doc,slots=fixture(symbol);assert len(slots)==len(values);model=dict(model)
    for (n,s),value in zip(slots,values,strict=True):
        if isinstance(s,dict) and not isinstance(value,FunctionValue):value=FunctionValue(tuple(s['parameters']),s['result'],value)
        model[n]=lambda value=value:value
    names={d['name'] for d in doc['declarations'] if d['kind']=='primitive'}
    return evaluate_document(doc,individuals=DOMAIN,situations=CONTEXTS,primitives={n:model.get(n,forbidden) for n in names},max_steps=500000,
        memoize_definitions=False,memoize_expressions=False)[0]['value']

def setup(charge=-2,conversion=Q(3,2)):
    cuts,model=arithmetic();r=cuts.read;model['aa']=lambda a,b:a<b
    for symbol,axis in zip(('yn','yo','yp','zc7'),ALLAXES):model[symbol]=lambda axis=axis:axis
    point=lambda a:cuts.make(dict(x=1,y=2,z=3,t=4).get(a,0))
    def field(axis):return FunctionValue(tuple([RS]*4),RS,lambda x,y,z,t:cuts.make({'x':r(x)+r(t),'y':r(y)-r(t),'z':2*r(z)}.get(axis,0)))
    magnetic=lambda axis:FunctionValue(tuple([RS]*4),RS,lambda *xs:cuts.make(0))
    electric=lambda a:cuts.make(dict(x=5,y=-2,z=6).get(a,0))
    force=lambda a:cuts.make(Q(charge)*conversion*r(electric(a)))
    region=lambda *xs:all(r(x)>=0 for x in xs)
    fields=dict(chargerecord='chargerecord',forcerecord='forcerecord',carrier='carrier',frame='frame',event='event',context='case',
        chargeunit='chargeunit',fieldunit='fieldunit',forceunit='forceunit',chargescale=Q(1),forcescale=Q(1),charge=cuts.make(charge),point=point,
        electricfield=field,magneticfield=magnetic,region=region,electric=electric,force=force,conversion=cuts.make(conversion))
    def vector_equal(x,y,axes=ALLAXES):return all(r(x(a))==r(y(a)) for a in axes)
    def field_equal(x,y):return all(r(x(a)(*[cuts.make(n) for n in row]))==r(y(a)(*[cuts.make(n) for n in row])) for a in AXES for row in ((1,2,3,4),(2,3,4,5)))
    def assigned(frame,e,h,region,ctx):
        return (frame,ctx)==('frame','case') and field_equal(e,field) and field_equal(h,magnetic) and [region(*[cuts.make(n) for n in row]) for row in ((1,2,3,4),(-1,2,3,4))]==[True,False]
    model.update(zor=lambda:'chargekind',zpn=lambda:'forcekind',
        zrdpointlike=lambda:FunctionValue(('individual','situation'),'truth',lambda b,c:(b,c)==('carrier','case')),
        zof=lambda u,k,s,c:(u,k,s,c) in (('chargeunit','chargekind',Q(1),'case'),('forceunit','forcekind',Q(1),'case')),
        zog=lambda rec,b,k,f,e,u,x,c:(rec,b,k,f,e,u,c)==('chargerecord','carrier','chargekind','frame','event','chargeunit','case') and r(x)==charge,
        zpb=lambda b,f,e,p,c:(b,f,e,c)==('carrier','frame','event','case') and vector_equal(p,point),
        zpc=lambda rec,b,k,f,e,u,x,c:(rec,b,k,f,e,u,c)==('forcerecord','carrier','forcekind','frame','event','forceunit','case') and vector_equal(x,force,AXES),
        znn=assigned,eirl=lambda rec,b,f,e,c:(rec,b,f,e,c)==('forcerecord','carrier','frame','event','case'),
        eirm=lambda q,e,f,x,c:(q,e,f,c)==('chargeunit','fieldunit','forceunit','case') and r(x)==conversion,
        eirn=lambda f,e,u,c:(f,u,c)==('frame','fieldunit','case') and field_equal(e,field))
    return cuts,model,fields

@lru_cache(None)
def arithmetic_checks():
    cuts,model,fields=setup();count=0
    for charge,electric,conversion in product((-2,0,Q(1,2),3),(-3,0,4),(-1,0,Q(1,2),2)):
        force=charge*electric*conversion
        assert run('eibq',[cuts.make(x) for x in (charge,electric,conversion,force)],model)==(conversion>0)
        assert not run('eibq',[cuts.make(x) for x in (charge,electric,conversion,force+1)],model);count+=2
    for charge in (-2,0,3):
        cuts,model,fields=setup(charge)
        assert run('eibr',[fields[n] for n in ('charge','electric','conversion','force')],model)
        for axis in AXES:
            wrong=lambda a:cuts.make(cuts.read(fields['force'](a))+(a==axis))
            assert not run('eibr',[fields['charge'],fields['electric'],fields['conversion'],wrong],model)
    assert not run('eibr',[fields[n] for n in ('charge','electric','conversion','force')],dict(model,yo=lambda:'x'))
    return dict(scalar_cases=count,vector_cases=12,duplicate_axis_rejected=True,negative_and_zero_charge_supported=True)

@lru_cache(None)
def record_checks():
    cuts,model,fields=setup();r=cuts.read
    assert run('eibs',[fields[n] for n,_ in FIELDS],model)
    for n,t in FIELDS:
        changed=dict(fields)
        if t in ('a','d'):changed[n]='other'
        elif t=='b':changed[n]=Q(2)
        elif n in ('charge','conversion'):changed[n]=cuts.make(r(fields[n])+1)
        elif n=='region':changed[n]=lambda *xs:False
        elif n in ('electricfield','magneticfield'):changed[n]=lambda a:FunctionValue(tuple([RS]*4),RS,lambda *xs:cuts.make(99))
        else:changed[n]=lambda a:cuts.make(99)
        assert not run('eibs',[changed[n] for n,_ in FIELDS],model),n
    for n in ('eirl','eirm','eirn','znn','zpc','zpb','zog','zof'):
        assert not run('eibs',[fields[n] for n,_ in FIELDS],dict(model,**{n:lambda *xs:False})),n
    try:run('eibs',[fields[n] for n,_ in FIELDS],dict(model,eirl=forbidden))
    except ValueError as e:assert 'Unknown electric-action' in str(e)
    else:raise AssertionError('Unknown force attribution accepted')
    # Coherent rescalings change displayed values and conversion together.
    for charge,conversion in ((0,1),(2,1),(-2,Q(1,2)),(1,3)):
        c,m,f=setup(charge,conversion);assert run('eibs',[f[n] for n,_ in FIELDS],m)
    return dict(argument_mutations=len(FIELDS),physical_record_failures=8,coherent_value_settings=4,
        native_charge_record_and_field_evaluation=True,unknown_attribution_rejected=True,
        electric_contribution_not_total_force=True)

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements']==old.document['statements'] and len(new.document['statements'])==207
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read(PRIOR));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[206])==prior['selection']
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=parse(read(CORE))
    for style in ('compact','full'):
        text=format_graph(doc,style);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    return dict(new_definitions=3,new_primitives=3,preserved_statements=207,author_review_preserved=True,core_roundtrips=['compact','full','v2'])

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)

def build_report():
    results=dict(arithmetic=arithmetic_checks(),records=record_checks(),structure=structure_checks())
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|{DOC,SOURCE,PRIOR,
        'scripts/compose_electric_action.py','scripts/check_electric_action.py','scripts/compose_limits.py',
        'scripts/compose_material_relative_frame.py','scripts/compose_field_equations.py','scripts/compose_rest_force.py',
        'scripts/check_material_relative_frame.py','scripts/check_tau_differential.py','scripts/check_coordinate_correspondence.py','tests/test_electric_action.py'}
    return dict(status='electric_action_dependency_checked',document=FULL,**results,
        empirical_law_proved=False,source_text_coverage_added=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
