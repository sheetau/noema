"""Check intervention solutions and their binding to physical records."""
from functools import lru_cache
from itertools import product
from fractions import Fraction as Q
import json
from noema.grammar import parse,format_graph,number_word
from noema.finite_semantics import FunctionValue,SequenceValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_material_relative_frame import NUM,RS,FS
from scripts.check_electric_action import setup as electric_setup
from scripts.compose_electric_response import ROOT,read,PARENT,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,LIBRARY,LIBRARY_BASIS,RENAMES,MODEL,GROUND,FIELDS,FIXED,PROFILES,ADAPTER,build,imported

DOC='docs/electric-response-v1.md';PRIOR='data/einstein-author-credit-review-v1.json';SOURCE='data/einstein-opening-obligations-v1.json'
STATE=dict(kind='function',parameters=['individual'],result='truth')
DOMAIN=('stimulus','current','body','carrier','frame','event','chargerecord','forcerecord','chargeunit','fieldunit','forceunit','lengthunit','timeunit','chargekind','forcekind','section','positive','x','y','z','t','other')

def forbidden(*xs):raise ValueError('Unknown electric-response input')

@lru_cache(None)
def fixture(symbol):
    doc=parse(read(CORE));doc['statements']=[]
    abstract(doc,NUM|({'eica'} if symbol=='eicd' else {'eibf'}))
    d=next(d for d in doc['declarations'] if d['name']==symbol);slots=[];arguments=[]
    for i,p in enumerate(d['parameters']):
        n='jerp'+number_word(i);slots.append((n,p['sort']))
        doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
        arguments.append(dict(kind='call',symbol=n,arguments=[]))
    doc['statements']=[dict(kind='ask',body=dict(kind='call',symbol=symbol,arguments=arguments))]
    return doc,slots

def run(symbol,values,model):
    doc,slots=fixture(symbol);assert len(slots)==len(values);model=dict(model)
    for (n,s),value in zip(slots,values,strict=True):
        if isinstance(s,dict) and s.get('kind')=='function' and not isinstance(value,FunctionValue):value=FunctionValue(tuple(s['parameters']),s['result'],value)
        model[n]=lambda value=value:value
    names={d['name'] for d in doc['declarations'] if d['kind']=='primitive'}
    return evaluate_document(doc,individuals=DOMAIN,situations=('case','on','off','other'),primitives={n:model.get(n,forbidden) for n in names},
        max_steps=2000000,memoize_definitions=False,memoize_expressions=False)[0]['value']

def values(f,fields):return [f[n] for n,_ in fields]
def state(a,i):return FunctionValue(('individual',),'truth',lambda n:n in ('stimulus','current') and (a if n=='stimulus' else i))
def variables(items=('stimulus','current')):return SequenceValue(items,'"individual"')

def model_fields(bits=(False,False,True,True)):
    return dict(variables=variables(),equations=lambda n,s:True if n=='stimulus' else bits[2*int(s('stimulus'))+int(s('current'))] if n=='current' else False,
        factor='stimulus',outcome='current',observed=state(True,True),realized=lambda s:True,
        stimulus=lambda s:s('stimulus'),response=lambda s:s('current'))

@lru_cache(None)
def contrast_checks():
    count=0
    for bits in product((False,True),repeat=4):
        f=model_fields(bits)
        on=[i for i in (False,True) if i==bits[2+int(i)]];off=[i for i in (False,True) if i==bits[int(i)]]
        expected=bool(on) and all(on) and bool(off) and not any(off)
        assert run('eib6',values(f,MODEL),{})==expected,bits;count+=1
    f=model_fields();assert run('eib7',values(f,GROUND),{})
    for n,value in (('factor','other'),('outcome','stimulus'),('variables',variables(('stimulus','stimulus','current'))),
        ('observed',state(False,False)),('observed',lambda n:n in ('stimulus','current','other')),
        ('realized',lambda s:s('stimulus')),('stimulus',lambda s:True),('response',lambda s:True)):
        assert not run('eib7',values(dict(f,**{n:value}),GROUND),{}),n
    try:run('eib7',values(dict(f,realized=forbidden),GROUND),{})
    except ValueError as e:assert 'Unknown electric-response' in str(e)
    else:raise AssertionError('Unknown realization accepted')
    return dict(binary_response_tables=count,independent_solution_enumeration=True,missing_cyclic_and_confounding_cases=True,
        structural_failures=8,unknown_realization_rejected=True)

def equal(x,y,sort,cuts):
    if isinstance(sort,str):return x==y
    if sort==RS:return cuts.read(x)==cuts.read(y)
    domains=[DOMAIN if s=='individual' else ('case','on','off','other') if s=='situation' else [cuts.make(t) for t in (0,1,4,8)] for s in sort['parameters']]
    return all(equal(x(*ps),y(*ps),sort['result'],cuts) for ps in product(*domains))

@lru_cache(None)
def sorts(symbol):return [p['sort'] for p in next(d for d in parse(read(CORE))['declarations'] if d['name']==symbol)['parameters']]

def physical_setup():
    cuts,model,f=electric_setup();r=cuts.read;c=cuts.make
    scope=lambda s,o:(s,o)==('section','positive')
    family=lambda rate:FunctionValue(('individual','individual'),FS,lambda s,o:FunctionValue((RS,),RS,lambda t:c(rate if scope(s,o) else 0)))
    f.update(body='body',lengthunit='lengthunit',timeunit='timeunit',lower=c(0),upper=c(8),sections=scope,
        cumulative=FunctionValue(('individual','individual'),FS,lambda s,o:FunctionValue((RS,),RS,lambda t:c(2*r(t) if scope(s,o) else 0))),
        current=family(2),section='section',orientation='positive',time=c(4),threshold=c(1))
    history=[f[n] for n in ('body','frame','context','timeunit','chargeunit','lower','upper','sections','cumulative','current')]
    model['eibf']=lambda *xs:all(equal(x,y,t,cuts) for x,y,t in zip(xs,history,sorts('eibf')))
    model['zzbv']=lambda b,e,ctx:(b,e,ctx)==('carrier','event','case')
    model['zzbu']=lambda e,fr,ctx,lu,tu,t,x,y,z:(e,fr,ctx,lu,tu)==('event','frame','case','lengthunit','timeunit') and tuple(map(r,(t,x,y,z)))==(4,1,2,3)
    model['eiro']=lambda b,fr,ctx,lu,tu,x,y,z,t:(b,fr,ctx,lu,tu)==('body','frame','case','lengthunit','timeunit') and tuple(map(r,(x,y,z,t)))==(1,2,3,4)
    return cuts,model,f

def mutate(value,sort,cuts):
    if sort in ('individual','situation'):return 'other'
    if sort=='number':return Q(2)
    if sort=='truth':return not value
    if sort==RS:return cuts.make(cuts.read(value)+1)
    def result(*xs):
        original=value(*xs)
        if sort['result']=='truth':return not original
        return mutate(original,sort['result'],cuts)
    return FunctionValue(tuple(sort['parameters']),sort['result'],result)

@lru_cache(None)
def record_checks():
    cuts,model,f=physical_setup()
    for n,fields in (('eica',FIELDS),('eicb',FIELDS),('eicc',FIELDS+[('threshold','h[b] c')])):assert run(n,values(f,fields),model)
    for (name,_),sort in zip(FIELDS,sorts('eica')):
        changed=dict(f);changed[name]=mutate(f[name],sort,cuts)
        assert not run('eica',values(changed,FIELDS),model),name
    for name in ('eiro','zzbu','zzbv','eirl','eibf'):
        assert not run('eica',values(f,FIELDS),dict(model,**{name:lambda *xs:False})),name
    assert not run('eicc',values(dict(f,threshold=cuts.make(2)),FIELDS+[('threshold','h[b] c')]),model)
    return dict(argument_mutations=len(FIELDS),missing_physical_connections=5,threshold_equality_rejected=True,
        native_electric_action_and_event=True,full_current_history_boundary='eibf')

def adapter_setup(scenario='response'):
    cuts,model,base=physical_setup();c=cuts.make;r=cuts.read
    zero_field=lambda a:FunctionValue(tuple([RS]*4),RS,lambda *xs:c(0))
    zero_vector=lambda a:c(0)
    def row(s):
        on=s('stimulus');response=(on if scenario=='response' else True if scenario=='confounded' else False)
        f=dict(base,context='on' if on else 'off')
        if not on:f.update(electricfield=zero_field,electric=zero_vector,force=zero_vector)
        f['current']=FunctionValue(('individual','individual'),FS,lambda sec,ori:FunctionValue((RS,),RS,lambda t:c(2*response if (sec,ori)==('section','positive') else 0)))
        f['cumulative']=FunctionValue(('individual','individual'),FS,lambda sec,ori:FunctionValue((RS,),RS,lambda t:c(2*response*r(t) if (sec,ori)==('section','positive') else 0)))
        return f
    expected_sorts=sorts('eica')
    def records(*xs):
        context=xs[[n for n,_ in FIELDS].index('context')]
        if context not in ('on','off'):return False
        if scenario=='missing_off' and context=='off':return False
        expected=row(state(context=='on',context=='on'))
        return all(equal(x,expected[n],t,cuts) for x,(n,_),t in zip(xs,FIELDS,expected_sorts))
    model['eica']=records
    f=model_fields();f.update({n:base[n] for n,_ in FIXED})
    for n,_ in PROFILES:
        result_sort=sorts('eicd')[[name for name,_ in ADAPTER].index(n)]['result']
        def select(s,n=n,t=result_sort):
            value=row(s)[n]
            return FunctionValue(tuple(t['parameters']),t['result'],value) if isinstance(t,dict) and not isinstance(value,FunctionValue) else value
        f[n]=select
    return cuts,model,f

@lru_cache(None)
def adapter_checks():
    for scenario in ('response','confounded','no_response','missing_off'):
        cuts,model,f=adapter_setup(scenario)
        assert run('eicd',values(f,ADAPTER),model)==(scenario=='response'),scenario
    cuts,model,f=adapter_setup();count=0
    # Every physical profile must select the same solution, including the off branch.
    for n,_ in PROFILES:
        original=f[n]
        # Changes confined to the off solution expose checks that only inspect the observation.
        profile_sort=sorts('eicd')[[name for name,_ in ADAPTER].index(n)]
        changed=dict(f)
        changed[n]=lambda s,original=original,t=profile_sort['result']:original(s) if s('stimulus') else mutate(original(s),t,cuts)
        assert not run('eicd',values(changed,ADAPTER),model),n;count+=1
    for n,t in FIXED:
        if n=='threshold':continue
        sort=sorts('eicd')[[name for name,_ in ADAPTER].index(n)]
        changed=dict(f);changed[n]=mutate(f[n],sort,cuts)
        assert not run('eicd',values(changed,ADAPTER),model),n
    return dict(scenarios=4,off_solution_profile_mutations=count,fixed_physical_argument_mutations=len(FIXED)-1,
        same_solution_index_required=True,physical_record_boundary='eica',native_force_and_current_thresholds=True)

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements']==old.document['statements'] and len(new.document['statements'])==207
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    original={d['name']:d for d in parse(read(LIBRARY))['declarations']}
    reverse={v:k for k,v in RENAMES.items()}
    def restore(x):
        if isinstance(x,list):return [restore(y) for y in x]
        if isinstance(x,dict):
            y={k:restore(v) for k,v in x.items()}
            if x.get('kind')=='definition':y['name']=reverse[x['name']]
            if x.get('kind')=='call':y['symbol']=reverse[x['symbol']]
            return y
        return x
    assert all(restore(d)==original[reverse[d['name']]] for d in imported()['declarations'])
    prior=json.loads(read(PRIOR));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[206])==prior['selection']
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=parse(read(CORE))
    for style in ('compact','full'):
        text=format_graph(doc,style);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    return dict(new_definitions=12,new_primitives=0,unchanged_imported_definitions=6,preserved_statements=207,author_review_preserved=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)

def build_report():
    results=dict(contrast=contrast_checks(),records=record_checks(),adapter=adapter_checks(),structure=structure_checks())
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|{DOC,PRIOR,SOURCE,LIBRARY,LIBRARY_BASIS,
        'scripts/compose_electric_response.py','scripts/check_electric_response.py','scripts/compose_limits.py','scripts/compose_material_relative_frame.py',
        'scripts/compose_electric_action.py','scripts/compose_current_distribution.py','scripts/compose_field_equations.py',
        'scripts/check_material_relative_frame.py','scripts/check_electric_action.py','scripts/check_tau_differential.py','scripts/check_coordinate_correspondence.py','tests/test_electric_response.py'}
    return dict(status='grounded_electric_response_model_checked',document=FULL,**results,
        physical_causal_model_validity_proved=False,conductor_classification_complete=False,source_text_coverage_added=False,
        verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
