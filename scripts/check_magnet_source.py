"""Check source attribution, exterior field witnesses and comparison binding."""
from functools import lru_cache
from itertools import product
import json
from noema.grammar import parse,format_graph,number_word
from noema.finite_semantics import FunctionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.extraction import extract_document
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_material_relative_frame import arithmetic,NUM,RS
from scripts.check_electric_action import setup as electric_setup
from scripts.check_conductor_cases import sentinel,same_value
from scripts.check_magnetic_action import mutate
from scripts.compose_magnet_source import ROOT,read,PARENT,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,SOURCE,WITNESS,CASES,PREMISE,FIELDS,CONDUCTOR_PREMISE,case_args,build
from scripts.compose_current_distribution import PAIR

DOC='docs/magnet-source-v1.md';PRIOR='data/einstein-author-credit-review-v1.json'
BINDING='data/magnet-source-reading-v1.json';OBLIGATIONS='data/einstein-opening-obligations-v1.json'
DOMAIN=('body','frame','condition','fieldunit','magneticunit','lengthunit','timeunit','x','y','z','t','other')
CONTEXTS=('case','first','second','other');AXES=('x','y','z');ROLES=AXES+('t',)

def forbidden(*xs):raise ValueError('Unknown magnet-source input')

@lru_cache(None)
def fixture(symbol):
    doc=parse(read(CORE));doc['statements']=[]
    abstract(doc,NUM|({'eick','eibi','eicr'} if symbol not in ('eicq','eicr') else set()))
    d=next(d for d in doc['declarations'] if d['name']==symbol);slots=[];arguments=[]
    for i,p in enumerate(d['parameters']):
        n='jmsc'+number_word(i);slots.append((n,p['sort']))
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
    return evaluate_document(doc,individuals=DOMAIN,situations=CONTEXTS,primitives={n:model.get(n,forbidden) for n in names},
        max_steps=500000,memoize_definitions=False,memoize_expressions=False)[0]['value']

def values(f,fields):return [f[n] for n,_ in fields]

def witness_setup(magnetic=(1,-2,3)):
    cuts,model,old=electric_setup();c=cuts.make;r=cuts.read
    field=lambda axis:FunctionValue(tuple([RS]*4),RS,lambda x,y,z,t:c((r(x)+r(t))*dict(zip(AXES,magnetic)).get(axis,0)))
    f={n:old[n] for n,_ in SOURCE if n in old}
    f.update(body='body',lengthunit='lengthunit',timeunit='timeunit',electricunit='fieldunit',magneticunit='magneticunit',
        sourcecondition='condition',magneticfield=field,point=old['point'],magnetic=lambda a:c(5*dict(zip(AXES,magnetic)).get(a,0)))
    def field_equal(a,b):
        return all(r(a(axis)(*[c(t) for t in row]))==r(b(axis)(*[c(t) for t in row])) for axis in AXES for row in ((1,2,3,4),(2,3,4,5)))
    def region_equal(a,b):return all(a(*[c(t) for t in row])==b(*[c(t) for t in row]) for row in ((1,2,3,4),(-1,2,3,4)))
    def source(*xs):
        return tuple(xs[:8])==tuple(values(f,SOURCE)[:8]) and field_equal(xs[8],f['electricfield']) and field_equal(xs[9],field) and region_equal(xs[10],f['region'])
    model.update(zm=lambda b:b=='body',eirx=lambda b,ctx,condition:(b,ctx,condition)==('body','case','condition'),eirw=source,
        znn=lambda frame,e,b,region,ctx:(frame,ctx)==('frame','case') and field_equal(e,f['electricfield']) and field_equal(b,field) and region_equal(region,f['region']),
        eirn=lambda frame,field_arg,unit,ctx:(frame,ctx)==('frame','case') and ((unit=='fieldunit' and field_equal(field_arg,f['electricfield'])) or (unit=='magneticunit' and field_equal(field_arg,field))),
        eiro=lambda body,frame,ctx,lu,tu,x,y,z,t:(body,frame,ctx,lu,tu)==('body','frame','case','lengthunit','timeunit') and r(x)<=0)
    return cuts,model,f

@lru_cache(None)
def witness_checks():
    count=0
    for components in product((-1,0,1),repeat=3):
        cuts,model,f=witness_setup(components)
        assert run('eicq',values(f,WITNESS),model)==any(components);count+=1
    cuts,model,f=witness_setup();assert run('eicq',values(f,WITNESS),model)
    for (name,_),(_,sort) in zip(WITNESS,fixture('eicq')[1]):
        changed=dict(f);changed[name]=mutate(f[name],sort,cuts)
        assert not run('eicq',values(changed,WITNESS),model),name
    for name in ('zm','eirx','eirw','eirn','znn'):
        assert not run('eicq',values(f,WITNESS),dict(model,**{name:lambda *xs:False})),name
    assert not run('eicq',values(f,WITNESS),dict(model,eiro=lambda *xs:True))
    # Nonzero ambient field and correct numeric evaluation cannot replace the source.
    assert not run('eicq',values(f,WITNESS),dict(model,eirw=lambda *xs:False,eirx=lambda *xs:True))
    try:run('eicq',values(f,WITNESS),dict(model,eirw=forbidden))
    except ValueError as e:assert 'Unknown magnet-source' in str(e)
    else:raise AssertionError('Unknown source accepted')
    try:run('eicr',values(f,SOURCE),model)
    except ValueError as e:assert 'rational number domain' in str(e)
    else:raise AssertionError('Full point function domain sampled')
    return dict(signed_component_cases=count,argument_mutations=len(WITNESS),physical_boundary_failures=6,
        native_field_evaluation=True,ambient_field_not_sufficient=True,interior_point_rejected=True,
        unknown_source_rejected=True,full_point_domain_refused=True)

def case_setup(symbol):
    cuts,model=arithmetic();slots=fixture(symbol)[1]
    fields=CASES if symbol=='eics' else PREMISE if symbol=='eict' else FIELDS
    supplied=[sentinel(s,i+1,cuts) for i,(_,s) in enumerate(slots)];pos={n:i for i,(n,_) in enumerate(fields)}
    def gate(names,enabled,xs):
        return enabled and len(xs)==len(names) and all(same_value(x,supplied[pos[n]],slots[pos[n]][1],cuts) for x,n in zip(xs,names))
    source_names=[[a.removeprefix('v ') for a in case_args(case)] for case in ('first','second')]
    def local(bits):
        calls=[]
        def magnet(*xs):
            i=len(calls);calls.append(i);assert i<2
            return gate(source_names[i],bits[i+1],xs)
        return dict(model,eick=lambda *xs:gate([n for n,_ in CONDUCTOR_PREMISE],bits[0],xs),eicr=magnet,
            eibi=lambda *xs:gate(['right' if n=='body' else n for n,_ in PAIR],bits[3],xs))
    return cuts,supplied,slots,fields,local

@lru_cache(None)
def case_checks():
    count=0
    for symbol in ('eics','eict','eicu','eicv'):
        cuts,supplied,slots,fields,local=case_setup(symbol)
        for bits in product((False,True),repeat=4):
            premise=all(bits[:3]);expected=all(bits[1:3]) if symbol=='eics' else premise if symbol=='eict' else (not premise or bits[3]) if symbol=='eicu' else premise and bits[3]
            assert run(symbol,supplied,local(bits))==expected,(symbol,bits);count+=1
    cuts,supplied,slots,fields,local=case_setup('eicv')
    for i,(_,sort) in enumerate(slots):
        changed=supplied.copy();changed[i]=sentinel(sort,100+i,cuts)
        assert not run('eicv',changed,local((True,)*4)),fields[i][0]
        original=supplied[i];supplied[i]=changed[i]
        assert run('eicv',changed,local((True,)*4)),fields[i][0]
        supplied[i]=original
    return dict(truth_combinations=count,shared_argument_mutations=len(slots),distinguishing_slot_variants=len(slots),
        current_agreement_not_assumed=True,different_field_values_allowed=True,boundaries=['eick','eicr','eibi'])

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements']==old.document['statements'] and len(new.document['statements'])==207
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read(PRIOR));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[206])==prior['selection']
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=parse(read(CORE));declarations={d['name']:d for d in doc['declarations']}
    clause=declarations['eicu']['body'];assert clause['kind']=='implies' and [a['symbol'] for a in clause['arguments']]==['eict','eibi']
    dependencies={d['name'] for d in extract_document(doc,roots=['eict'],statement_indices=[]).document['declarations']}
    assert 'eibi' not in dependencies
    exists=declarations['eicr']['body'];assert exists['kind']=='exists' and exists['body']['kind']=='exists'
    binding=json.loads(read(BINDING));validate_hashes(ROOT,binding['source_sha256'])
    unit=next(u for u in json.loads(read('artifacts/written-units-v1/einstein-1905.json'))['units'] if u['id']==binding['unit'])
    assert binding['verified_full_units']==0 and binding['source_text_sha256']==unit['text_sha256'] and len(binding['occurrences'])==6
    for occurrence in binding['occurrences']:
        start,end=occurrence['range'];assert unit['text'][start:end]==occurrence['source'] and occurrence['body_parameter']=='left'
    for style in ('compact','full'):
        text=format_graph(doc,style);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    return dict(new_definitions=6,new_primitives=2,preserved_statements=207,author_review_preserved=True,source_reference_occurrences=6)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)

def build_report():
    results=dict(witness=witness_checks(),cases=case_checks(),structure=structure_checks())
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|{DOC,PRIOR,BINDING,OBLIGATIONS,
        'scripts/compose_magnet_source.py','scripts/check_magnet_source.py','scripts/compose_conductor_cases.py','scripts/compose_current_distribution.py',
        'scripts/compose_material_relative_frame.py','scripts/compose_limits.py','scripts/compose_field_equations.py','scripts/compose_rest_force.py',
        'scripts/check_conductor_cases.py','scripts/check_magnetic_action.py','scripts/check_electric_action.py','scripts/check_material_relative_frame.py',
        'scripts/check_tau_differential.py','scripts/check_coordinate_correspondence.py','tests/test_magnet_source.py'}
    return dict(status='magnet_source_and_cases_checked',document=FULL,**results,source_application_complete=False,
        physical_field_generation_proved=False,source_text_coverage_added=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
