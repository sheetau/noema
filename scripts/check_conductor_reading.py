"""Check declared transport criteria, duration and same-trial possible outcomes."""
from functools import lru_cache
from itertools import product
from fractions import Fraction as Q
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
from scripts.compose_conductor_reading import ROOT,read,PARENT,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,WINDOW,WITNESS,RESPONSE,STANDARD,TRIAL,CAPACITY,ATTRIBUTION,HISTORY,PROFILES,build

DOC='docs/conductor-reading-v1.md';PRIOR='data/einstein-author-credit-review-v1.json';SOURCE='data/einstein-opening-obligations-v1.json'
DOMAIN=('body','standard','trial','frame','timeunit','chargeunit','section','positive','other');CONTEXTS=('source','result','other')

def forbidden(*xs):raise ValueError('Unknown conductor-reading input')

@lru_cache(None)
def fixture(symbol,native=False):
    doc=parse(read(CORE));doc['statements']=[]
    abstract(doc,NUM|{'eibf'}|({'eicg'} if symbol in ('eich','eici') and not native else set()))
    d=next(d for d in doc['declarations'] if d['name']==symbol);slots=[];arguments=[]
    for i,p in enumerate(d['parameters']):
        n='jcnd'+number_word(i);slots.append((n,p['sort']))
        doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
        arguments.append(dict(kind='call',symbol=n,arguments=[]))
    doc['statements']=[dict(kind='ask',body=dict(kind='call',symbol=symbol,arguments=arguments))]
    return doc,slots

def run(symbol,values,model,native=False):
    doc,slots=fixture(symbol,native);assert len(slots)==len(values);model=dict(model)
    for (n,s),value in zip(slots,values,strict=True):
        if isinstance(s,dict) and not isinstance(value,FunctionValue):value=FunctionValue(tuple(s['parameters']),s['result'],value)
        model[n]=lambda value=value:value
    names={d['name'] for d in doc['declarations'] if d['kind']=='primitive'}
    return evaluate_document(doc,individuals=DOMAIN,situations=CONTEXTS,primitives={n:model.get(n,forbidden) for n in names},
        max_steps=500000,memoize_definitions=False,memoize_expressions=False)[0]['value']

def values(f,fields):return [f[n] for n,_ in fields]

@lru_cache(None)
def window_checks():
    cuts,model=arithmetic();count=0
    for start,end in product((-1,0,1,2,3,4,5),repeat=2):
        for threshold,span in product((-1,0,1),(0,1,2)):
            expected=threshold>0 and span>0 and 0<=start<end<=4 and end-start>=span
            assert run('eice',[cuts.make(n) for n in (0,4,start,end,threshold,span)],model)==expected
            count+=1
    bad=FunctionValue(('number',),'truth',lambda n:False)
    try:run('eice',[cuts.make(n) for n in (0,4,1,3,1)]+[bad],model)
    except ValueError as e:assert 'not constructed' in str(e)
    else:raise AssertionError('Unknown duration accepted')
    return dict(cases=count,strict_positive_threshold_and_duration=True,exact_minimum_duration_allowed=True,unknown_cut_rejected=True)

def equal(x,y,sort,cuts):
    if isinstance(sort,str):return x==y
    if sort==RS:return cuts.read(x)==cuts.read(y)
    domains=[DOMAIN if s=='individual' else CONTEXTS if s=='situation' else [cuts.make(t) for t in (0,1)] for s in sort['parameters']]
    return all(equal(x(*ps),y(*ps),sort['result'],cuts) for ps in product(*domains))

@lru_cache(None)
def sorts(symbol):
    d=next(d for d in parse(read(CORE))['declarations'] if d['name']==symbol)
    return [p['sort'] for p in d['parameters']] if d['kind']=='definition' else d['parameters']

def setup():
    cuts,model=arithmetic();c=cuts.make;r=cuts.read
    def profile(n,source,operation,result):
        tag=100*CONTEXTS.index(source)+10*DOMAIN.index(operation)+CONTEXTS.index(result)
        good=(source,operation,result)==('source','trial','result')
        if n=='frame':return 'frame' if good else 'other'
        if n in ('lower','upper'):return c(tag+(4 if n=='upper' else 0))
        if n=='sections':return FunctionValue(('individual','individual'),'truth',lambda s,o:(s,o)==('section','positive' if good else 'other'))
        return FunctionValue(('individual','individual'),FS,lambda s,o:FunctionValue((RS,),RS,lambda t:c((tag+2)*(r(t) if n=='cumulative' else 1))))
    f=dict(standard='standard',body='body',source='source',timeunit='timeunit',quantityunit='chargeunit',threshold=c(1),minimumspan=c(2),operation='trial',alternative='result')
    for n,_ in PROFILES:f[n]=profile(n,'source','trial','result')
    history={n:(f['alternative'] if n=='context' else f[n]) for n,_ in HISTORY}
    response=history|{n:f[n] for n in ('threshold','minimumspan')}
    attribution=dict(standard=f['standard'],operation=f['operation'],source=f['source'])|history
    def match(xs,expected,types):return len(xs)==len(expected) and all(equal(x,y,t,cuts) for x,y,t in zip(xs,expected,types))
    model.update(zm=lambda b:b=='body',eirk=lambda b,o,s:(b,o,s)==('body','trial','source'),
        eirq=lambda st,b,o,s:(st,b,o,s)==('standard','body','trial','source'),
        zrdpossible=lambda:FunctionValue(('individual','individual','situation','situation'),'truth',lambda o,b,s,a:(o,b,s,a)==('trial','body','source','result')),
        eirp=lambda *xs:match(xs,values(f,STANDARD),sorts('eirp')),
        eirr=lambda *xs:match(xs,values(attribution,ATTRIBUTION),sorts('eirr')),
        eicg=lambda *xs:match(xs,values(response,RESPONSE),sorts('eicg')),
        eibf=lambda *xs:match(xs,values(history,HISTORY),sorts('eibf')))
    return cuts,model,f,profile,history

def mutate(value,sort,cuts):
    if sort in ('individual','situation'):return 'other'
    if sort=='truth':return not value
    if sort==RS:return cuts.make(cuts.read(value)+1)
    return FunctionValue(tuple(sort['parameters']),sort['result'],lambda *xs:mutate(value(*xs),sort['result'],cuts))

@lru_cache(None)
def trial_checks():
    cuts,model,f,profile,history=setup();assert run('eich',values(f,TRIAL),model)
    for (n,_),sort in zip(TRIAL,sorts('eich')):
        changed=dict(f);changed[n]=mutate(f[n],sort,cuts)
        assert not run('eich',values(changed,TRIAL),model),n
    # A response attribution is independent of success: weak/short responses still fail.
    for missing in ('zm','eirp','eirq','eirk','eirr','eicg'):
        assert not run('eich',values(f,TRIAL),dict(model,**{missing:lambda *xs:False})),missing
    assert not run('eich',values(f,TRIAL),dict(model,zrdpossible=lambda:FunctionValue(('individual','individual','situation','situation'),'truth',lambda *xs:False)))
    for unknown in ('eirp','eirq','eirr'):
        try:run('eich',values(f,TRIAL),dict(model,**{unknown:forbidden}))
        except ValueError as e:assert 'Unknown conductor-reading' in str(e)
        else:raise AssertionError(unknown)
    # Real time is not a finite domain, even for a constant-rate fixture.
    wf=history|{n:f[n] for n in ('threshold','minimumspan')}
    wf.update(section='section',orientation='positive',start=f['lower'],end=f['upper'])
    for symbol,fields in (('eicf',WITNESS),('eicg',RESPONSE)):
        try:run(symbol,values(wf,fields),model,native=True)
        except ValueError as e:assert 'rational number domain' in str(e)
        else:raise AssertionError('Full real interval sampled')
    return dict(argument_mutations=len(TRIAL),missing_conditions=7,unknown_physical_inputs_rejected=True,
        full_interval_and_real_witness_quantifiers_refused=True,sustained_response_boundary='eicg')

@lru_cache(None)
def capacity_checks():
    cuts,model,f,profile,history=setup()
    for n,_ in PROFILES:f[n]=lambda s,o,a,n=n:profile(n,s,o,a)
    assert run('eici',values(f,CAPACITY),model)
    for n,_ in PROFILES:
        wrong=dict(f);wrong[n]=lambda s,o,a,n=n:profile(n,s,'other',a)
        assert not run('eici',values(wrong,CAPACITY),model),n
    for (n,_),sort in zip(STANDARD,sorts('eirp')):
        changed=dict(f);changed[n]=mutate(f[n],sort,cuts)
        assert not run('eici',values(changed,CAPACITY),model),n
    # No requirement that the original situation already has a current history.
    assert not model['eibf'](*[('source' if n=='context' else history[n]) for n,_ in HISTORY])
    assert run('eici',values(f,CAPACITY),model)
    assert not run('eici',values(f,CAPACITY),dict(model,eirq=lambda *xs:False))
    return dict(profile_index_mutations=len(PROFILES),fixed_standard_mutations=len(STANDARD),actual_source_current_not_required=True,
        same_operation_and_possible_result_required=True)

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements']==old.document['statements'] and len(new.document['statements'])==207
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read(PRIOR));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[206])==prior['selection']
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=parse(read(CORE))
    dependencies={d['name'] for d in extract_document(doc,roots=['eici'],statement_indices=[]).document['declarations']}
    assert not dependencies&{'eibx','eicd','eiaq'},dependencies
    decision=json.loads(read('data/conductor-reading-decision-v1.json'));validate_hashes(ROOT,decision['source_sha256'])
    unit=next(u for u in json.loads(read('artifacts/written-units-v1/einstein-1905.json'))['units'] if u['id']==decision['unit'])
    assert unit['text_sha256']==decision['source_text_sha256'] and decision['verified_full_units']==0
    assert decision['composition']=='eici' and decision['meaning_basis']==BASIS
    for occurrence in decision['occurrences']:
        start,end=occurrence['range'];assert unit['text'][start:end]==occurrence['source']
    for style in ('compact','full'):
        text=format_graph(doc,style);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    return dict(new_definitions=5,new_primitives=3,preserved_statements=207,author_review_preserved=True,
        rigid_carrier_history_and_binary_model_not_prerequisites=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)

def build_report():
    results=dict(window=window_checks(),trial=trial_checks(),capacity=capacity_checks(),structure=structure_checks())
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|{DOC,PRIOR,SOURCE,'data/conductor-reading-decision-v1.json',
        'scripts/compose_conductor_reading.py','scripts/check_conductor_reading.py','scripts/compose_limits.py','scripts/compose_material_relative_frame.py',
        'scripts/compose_charge_transport_capacity.py','scripts/check_material_relative_frame.py','scripts/check_tau_differential.py',
        'scripts/check_coordinate_correspondence.py','tests/test_conductor_reading.py'}
    return dict(status='standard_relative_conductor_reading_checked',document=FULL,**results,
        physical_standard_adequacy_automatically_proved=False,source_application_pending=True,source_text_coverage_added=False,
        verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
