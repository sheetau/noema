"""Check shared conductor identity without presupposing the current conclusion."""
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
from scripts.check_material_relative_frame import arithmetic,NUM,RS,FS
from scripts.compose_conductor_reading import TRIAL
from scripts.compose_conductor_cases import ROOT,read,PARENT,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,CAPABILITIES,PREMISE,FIELDS,PREPARATION,MOTION,PAIR,PROFILES,build

DOC='docs/conductor-cases-v1.md';PRIOR='data/einstein-author-credit-review-v1.json';SOURCE='data/einstein-opening-obligations-v1.json';BINDING='data/conductor-case-binding-v1.json'
DOMAIN=('body','trial','other');CONTEXTS=('first','second','result_first','result_second','other')

def forbidden(*xs):raise ValueError('Unknown conductor-case input')

def same_value(x,y,sort,cuts):
    if isinstance(sort,str):return x==y
    if sort==RS:return cuts.read(x)==cuts.read(y)
    probe=['body' if s=='individual' else 'first' if s=='situation' else cuts.make(1) for s in sort['parameters']]
    return same_value(x(*probe),y(*probe),sort['result'],cuts)

@lru_cache(None)
def fixture(symbol,native_capacity=False):
    doc=parse(read(CORE));doc['statements']=[]
    abstract(doc,NUM|{'eia3','eibi'}|({'eich'} if native_capacity else {'eici'}))
    d=next(d for d in doc['declarations'] if d['name']==symbol);slots=[];arguments=[]
    for i,p in enumerate(d['parameters']):
        n='jccs'+number_word(i);slots.append((n,p['sort']))
        doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
        arguments.append(dict(kind='call',symbol=n,arguments=[]))
    doc['statements']=[dict(kind='ask',body=dict(kind='call',symbol=symbol,arguments=arguments))]
    return doc,slots

def run(symbol,values,model,native_capacity=False):
    doc,slots=fixture(symbol,native_capacity);assert len(slots)==len(values);model=dict(model)
    for (n,s),value in zip(slots,values,strict=True):
        if isinstance(s,dict) and not isinstance(value,FunctionValue):value=FunctionValue(tuple(s['parameters']),s['result'],value)
        model[n]=lambda value=value:value
    names={d['name'] for d in doc['declarations'] if d['kind']=='primitive'}
    return evaluate_document(doc,individuals=DOMAIN,situations=CONTEXTS,primitives={n:model.get(n,forbidden) for n in names},
        max_steps=500000,memoize_definitions=False,memoize_expressions=False)[0]['value']

def sentinel(sort,tag,cuts):
    if sort in ('individual','situation'):return ('first' if sort=='situation' else 'body') if tag<100 else 'other'
    if sort=='truth':return tag<100
    if sort==RS:return cuts.make(tag)
    return FunctionValue(tuple(sort['parameters']),sort['result'],lambda *xs:sentinel(sort['result'],tag,cuts))

def setup(symbol):
    cuts,model=arithmetic();slots=fixture(symbol)[1]
    fields=FIELDS if symbol in ('eicl','eicm') else PREMISE if symbol=='eick' else CAPABILITIES
    supplied=[sentinel(s,i+1,cuts) for i,(_,s) in enumerate(slots)];pos={n:i for i,(n,_) in enumerate(fields)}
    def gate(names,enabled,xs):
        return enabled and len(xs)==len(names) and all(same_value(x,supplied[pos[n]],slots[pos[n]][1],cuts) for x,n in zip(xs,names))
    caps=[['standard','right',c+'context','timeunit','quantityunit','threshold','minimumspan']+['trial'+n for n,_ in PROFILES] for c in ('first','second')]
    def local(bits):
        # relative motion, first/second capacity, preparation, current agreement
        calls=[]
        def capacity(*xs):
            i=len(calls);calls.append(i);assert i<2
            return gate(caps[i],bits[i+1],xs)
        return dict(model,eici=capacity,eia3=lambda *xs:gate([n for n,_ in MOTION],bits[0],xs),
            eirs=lambda *xs:gate([n for n,_ in PREPARATION],bits[3],xs),
            eibi=lambda *xs:gate(['right' if n=='body' else n for n,_ in PAIR],bits[4],xs))
    return cuts,supplied,slots,fields,local

@lru_cache(None)
def logical_checks():
    count=0
    for symbol in ('eick','eicl','eicm'):
        cuts,supplied,slots,fields,local=setup(symbol)
        for bits in product((False,True),repeat=5):
            premise=all(bits[:4]);expected=premise if symbol=='eick' else ((not premise) or bits[4]) if symbol=='eicl' else premise and bits[4]
            assert run(symbol,supplied,local(bits))==expected,(symbol,bits);count+=1
    cuts,supplied,slots,fields,local=setup('eicm')
    try:run('eicm',supplied,dict(local((True,)*5),eirs=forbidden))
    except ValueError as e:assert 'Unknown conductor-case' in str(e)
    else:raise AssertionError('Unknown preparation accepted')
    return dict(truth_combinations=count,unequal_currents_can_falsify_conditional=True,
        false_premise_not_a_realized_case=True,unknown_preparation_rejected=True)

@lru_cache(None)
def binding_checks():
    cuts,supplied,slots,fields,local=setup('eicm')
    assert run('eicm',supplied,local((True,)*5))
    for i,(_,sort) in enumerate(slots):
        changed=supplied.copy();changed[i]=sentinel(sort,100+i,cuts)
        assert not run('eicm',changed,local((True,)*5)),fields[i][0]
        original=supplied[i];supplied[i]=changed[i]
        assert run('eicm',changed,local((True,)*5)),fields[i][0]
        supplied[i]=original
    return dict(shared_argument_mutations=len(slots),distinguishing_slot_variants=len(slots),
        all_slots_reach_the_intended_condition=True,boundaries=['eia3','eici','eibi'])

@lru_cache(None)
def capacity_checks():
    cuts,model=arithmetic();r=cuts.read;c=cuts.make
    def profile(n,source,operation,result):
        tag=100*CONTEXTS.index(source)+10*DOMAIN.index(operation)+CONTEXTS.index(result)
        if n=='frame':return 'body'
        if n in ('lower','upper'):return c(tag+(4 if n=='upper' else 0))
        if n=='sections':return FunctionValue(('individual','individual'),'truth',lambda a,b:(a,b)==('body','trial'))
        return FunctionValue(('individual','individual'),FS,lambda a,b:FunctionValue((RS,),RS,lambda t:c((tag+1)*(r(t) if n=='cumulative' else 1))))
    f=dict(standard='body',right='body',firstcontext='first',secondcontext='second',timeunit='trial',quantityunit='body',threshold=c(1),minimumspan=c(2))
    for n,_ in PROFILES:f['trial'+n]=lambda s,o,a,n=n:profile(n,s,o,a)
    types=[p['sort'] for p in next(d for d in parse(read(CORE))['declarations'] if d['name']=='eich')['parameters']]
    def local(missing=None):
        def trial(*xs):
            source=xs[2];operation=xs[7];result=xs[8]
            expected_result={'first':'result_first','second':'result_second'}.get(source)
            expected_operation='trial' if source=='first' else 'other'
            if source==missing or result!=expected_result or operation!=expected_operation:return False
            expected=dict(standard=f['standard'],body=f['right'],source=source,timeunit=f['timeunit'],quantityunit=f['quantityunit'],
                threshold=f['threshold'],minimumspan=f['minimumspan'],operation=operation,alternative=result)
            for n,_ in PROFILES:expected[n]=profile(n,source,operation,result)
            return all(same_value(x,expected[n],t,cuts) for x,(n,_),t in zip(xs,TRIAL,types))
        return dict(model,eich=trial)
    values=lambda f:[f[n] for n,_ in CAPABILITIES]
    assert run('eicj',values(f),local(),True)
    for missing in ('first','second'):assert not run('eicj',values(f),local(missing),True)
    for n,_ in PROFILES:
        if n in ('frame','sections'):continue
        bad=dict(f);bad['trial'+n]=lambda s,o,a,n=n:profile(n,'first',o,a)
        assert not run('eicj',values(bad),local(),True),n
    return dict(native_capacity_existentials=True,different_successful_operations_and_results_allowed=True,
        either_missing_capacity_rejected=True,source_profile_substitutions_rejected=4,trial_boundary='eich')

@lru_cache(None)
def current_separation_checks():
    cuts,supplied,slots,fields,local=setup('eicm');pos={n:i for i,(n,_) in enumerate(fields)};c=cuts.make;r=cuts.read
    # These explicitly linear fixture profiles define the whole comparison boundary.
    # The samples below check their forwarding, not arbitrary real histories.
    for a,b in ((0,0),(1,0),(-1,1)):
        for mismatch in (False,True):
            values=supplied.copy();values[pos['threshold']]=c(100);values[pos['minimumspan']]=c(100)
            values[pos['offset']]=c(0)
            for case in ('first','second'):
                delta=int(mismatch and case=='second')
                values[pos[case+'current']]=FunctionValue(('individual','individual'),FS,
                    lambda s,o,delta=delta:FunctionValue((RS,),RS,lambda t:c(a+b*r(t)+delta)))
            def current_match(*xs):
                first=xs[9];second=xs[15]
                return all(r(first('body','trial')(c(t)))==r(second('body','trial')(c(t))) for t in (0,1,2))
            model=dict(eia3=lambda *xs:True,eici=lambda *xs:True,eirs=lambda *xs:True,eibi=current_match)
            assert run('eicm',values,model)==(not mismatch)
            assert run('eicl',values,model)==(not mismatch)
    return dict(linear_profile_cases=6,zero_small_and_sign_changing_currents_allowed=True,
        capacity_threshold_not_applied_to_actual_currents=True,comparison_boundary='eibi on declared linear histories')

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements']==old.document['statements'] and len(new.document['statements'])==207
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read(PRIOR));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[206])==prior['selection']
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=parse(read(CORE))
    declarations={d['name']:d for d in doc['declarations']}
    clause=declarations['eicl']['body'];assert clause['kind']=='implies'
    assert [x['symbol'] for x in clause['arguments']]==['eick','eibi']
    dependencies={d['name'] for d in extract_document(doc,roots=['eick'],statement_indices=[]).document['declarations']}
    assert not dependencies&{'eibi','eibj'},dependencies
    binding=json.loads(read(BINDING));validate_hashes(ROOT,binding['source_sha256'])
    unit=next(u for u in json.loads(read('artifacts/written-units-v1/einstein-1905.json'))['units'] if u['id']==binding['unit'])
    assert binding['verified_full_units']==0 and len(binding['occurrences'])==6
    for occurrence in binding['occurrences']:
        start,end=occurrence['range'];assert unit['text'][start:end]==occurrence['source'] and occurrence['body_parameter']=='right'
    for style in ('compact','full'):
        text=format_graph(doc,style);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    return dict(new_definitions=4,new_primitives=1,preserved_statements=207,author_review_preserved=True,
        current_agreement_not_in_premise=True,source_reference_occurrences=6)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)

def build_report():
    results=dict(logic=logical_checks(),bindings=binding_checks(),capacity=capacity_checks(),currents=current_separation_checks(),structure=structure_checks())
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|{DOC,PRIOR,SOURCE,BINDING,
        'scripts/compose_conductor_cases.py','scripts/check_conductor_cases.py','scripts/compose_conductor_reading.py','scripts/compose_current_distribution.py',
        'scripts/compose_material_relative_frame.py','scripts/compose_limits.py',
        'scripts/check_material_relative_frame.py','scripts/check_tau_differential.py','scripts/check_coordinate_correspondence.py','tests/test_conductor_cases.py'}
    return dict(status='conductor_cases_premise_conclusion_checked',document=FULL,**results,
        physical_current_invariance_proved=False,source_application_complete=False,source_text_coverage_added=False,
        verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
