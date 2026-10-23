"""Check actual response versus admissible possible charge transport."""
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
from scripts.check_material_relative_frame import arithmetic,NUM,RS,FS
from scripts.compose_charge_transport_capacity import ROOT,read,PARENT,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,HISTORY,WITNESS,RESPONSE,TRIAL,PROFILES,CAPACITY,MOTION,DISTRIBUTION,EXTRA,build

DOC='docs/charge-transport-capacity-v1.md';SOURCE='data/einstein-opening-obligations-v1.json';PRIOR='data/einstein-author-credit-review-v1.json'
DOMAIN=('body','good','bad','section','positive','frame','timeunit','chargeunit','other')
CONTEXTS=('source','result','first','second','other')

def forbidden(*args):raise ValueError('Unknown transport-capacity input')

def same_value(x,y,sort,cuts):
    if sort in ('individual','situation','truth'):return x==y
    if sort.get('parameters')==['number'] and sort.get('result')=='truth':return cuts.read(x)==cuts.read(y)
    probe=['body' if s=='individual' else 'source' if s=='situation' else cuts.make(1) for s in sort['parameters']]
    return same_value(x(*probe),y(*probe),sort['result'],cuts)

@lru_cache(None)
def fixture(symbol,native=False):
    doc=parse(read(CORE));doc['statements']=[]
    boundaries=set() if native else ({'eibj','eibo'} if symbol=='eibp' else {'eibf'} if symbol=='eibl' else {'eibm'})
    abstract(doc,NUM|boundaries)
    d=next(d for d in doc['declarations'] if d['name']==symbol);slots=[];arguments=[]
    for i,p in enumerate(d['parameters']):
        n='jctm'+number_word(i);slots.append((n,p['sort']))
        doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
        arguments.append(dict(kind='call',symbol=n,arguments=[]))
    doc['statements']=[dict(kind='ask',body=dict(kind='call',symbol=symbol,arguments=arguments))]
    return doc,slots

def run(symbol,values,model,native=False):
    doc,slots=fixture(symbol,native);assert len(slots)==len(values),(symbol,len(slots),len(values));model=dict(model)
    for (n,s),value in zip(slots,values,strict=True):
        if isinstance(s,dict) and not isinstance(value,FunctionValue):value=FunctionValue(tuple(s['parameters']),s['result'],value)
        model[n]=lambda value=value:value
    names={d['name'] for d in doc['declarations'] if d['kind']=='primitive'}
    return evaluate_document(doc,individuals=DOMAIN,situations=CONTEXTS,primitives={n:model.get(n,forbidden) for n in names},
        max_steps=700000,memoize_definitions=False,memoize_expressions=False)[0]['value']

@lru_cache(None)
def threshold_checks():
    cuts,model=arithmetic();count=0
    for rate,bound in product((-3,-1,Q(-1,2),0,Q(1,2),1,3),(-1,0,Q(1,2),1,2,3)):
        assert run('eibk',[cuts.make(rate),cuts.make(bound)],model)==(bound>=0 and abs(rate)>bound);count+=1
    bad=FunctionValue(('number',),'truth',lambda x:False)
    assert not run('eibk',[cuts.make(1),cuts.make(0)],dict(model,ba=lambda x:False))
    try:run('eibk',[cuts.make(1),bad],model)
    except ValueError as e:assert 'not constructed' in str(e)
    else:raise AssertionError('Unknown cut accepted')
    return dict(cases=count,both_signs_allowed=True,zero_equality_and_negative_threshold_rejected=True,unknown_cut_rejected=True)

def history_fixture(rate=2):
    cuts,model=arithmetic();r=cuts.read
    scope=FunctionValue(('individual','individual'),'truth',lambda s,o:(s,o)==('section','positive'))
    cumulative=FunctionValue(('individual','individual'),FS,lambda s,o:FunctionValue((RS,),RS,lambda t:cuts.make(rate*r(t))))
    current=FunctionValue(('individual','individual'),FS,lambda s,o:FunctionValue((RS,),RS,lambda t:cuts.make(rate)))
    fields=dict(body='body',frame='frame',context='source',timeunit='timeunit',quantityunit='chargeunit',
        lower=cuts.make(0),upper=cuts.make(2),sections=scope,cumulative=cumulative,current=current,threshold=cuts.make(1),section='section',orientation='positive',time=cuts.make(1))
    expected=[fields[n] for n,_ in HISTORY];sorts=[p['sort'] for p in next(d for d in parse(read(CORE))['declarations'] if d['name']=='eibf')['parameters']]
    model['eibf']=lambda *xs:all(same_value(x,y,t,cuts) for x,y,t in zip(xs,expected,sorts))
    return cuts,model,fields

@lru_cache(None)
def witness_checks():
    count=0
    for rate,t,s,o in product((-2,0,1,2),(-1,0,1,2,3),('section','other'),('positive','other')):
        cuts,model,fields=history_fixture(rate);fields.update(time=cuts.make(t),section=s,orientation=o)
        assert run('eibl',[fields[n] for n,_ in WITNESS],model)==(abs(rate)>1 and 0<=t<=2 and s=='section' and o=='positive');count+=1
    cuts,model,fields=history_fixture()
    assert not run('eibl',[fields[n] for n,_ in WITNESS],dict(model,eibf=lambda *xs:False))
    try:run('eibl',[fields[n] for n,_ in WITNESS],dict(model,eibf=forbidden))
    except ValueError as e:assert 'Unknown transport-capacity' in str(e)
    else:raise AssertionError('Unknown history accepted')
    return dict(witness_cases=count,invalid_and_unknown_histories_rejected=True,full_history_boundary='eibf')

def capacity_fixture(allowed=True,possible=True,success=True):
    cuts,model=arithmetic();r=cuts.read;calls=[]
    def tag(source,operation,alternative):return 1+100*CONTEXTS.index(source)+10*DOMAIN.index(operation)+CONTEXTS.index(alternative)
    def profile(name,source,operation,alternative):
        n=tag(source,operation,alternative)
        if name=='frame':return 'frame'
        if name=='lower':return cuts.make(n)
        if name=='upper':return cuts.make(n+2)
        if name=='sections':return FunctionValue(('individual','individual'),'truth',lambda s,o:(s,o)==('section','positive'))
        return FunctionValue(('individual','individual'),FS,lambda s,o:FunctionValue((RS,),RS,lambda t:cuts.make(n+(r(t) if name=='cumulative' else 0))))
    fields=dict(body='body',source='source',timeunit='timeunit',quantityunit='chargeunit',threshold=cuts.make(1))
    for n,t in PROFILES:fields[n]=lambda s,o,a,n=n:profile(n,s,o,a)
    model.update(zm=lambda b:b=='body',eirk=lambda b,o,s:allowed and (b,o,s)==('body','good','source'),
        zrdpossible=lambda:FunctionValue(('individual','individual','situation','situation'),'truth',lambda o,b,s,a:possible and (o,b,s,a)==('good','body','source','result')))
    def response(*xs):
        body,frame,context,timeunit,unit,lower,upper,sections,cumulative,current,threshold=xs
        calls.append((body,context,r(lower)))
        n=tag('source','good','result')
        return (success and (body,frame,context,timeunit,unit)==('body','frame','result','timeunit','chargeunit')
            and r(lower)==n and r(upper)==n+2 and r(threshold)==1
            and {(s,o) for s,o in product(DOMAIN,repeat=2) if sections(s,o)}=={('section','positive')}
            and r(cumulative('section','positive')(cuts.make(n)))==2*n and r(current('section','positive')(cuts.make(n)))==n)
    model['eibm']=response
    return cuts,model,fields,profile,calls

@lru_cache(None)
def modal_checks():
    cases=0
    for allowed,possible,success in product((False,True),repeat=3):
        cuts,model,fields,profile,calls=capacity_fixture(allowed,possible,success)
        assert run('eibo',[fields[n] for n,_ in CAPACITY],model)==(allowed and possible and success);cases+=1
    cuts,model,fields,profile,calls=capacity_fixture()
    # The source itself never has a successful response; the possible result does.
    assert run('eibo',[fields[n] for n,_ in CAPACITY],model)
    trial=dict(fields,operation='good',alternative='result')
    for n,t in PROFILES:trial[n]=profile(n,'source','good','result')
    assert run('eibn',[trial[n] for n,_ in TRIAL],model)
    for n,t in TRIAL:
        changed=dict(trial)
        if t in ('a','d'):changed[n]='other'
        elif n in ('threshold','lower','upper'):changed[n]=cuts.make(cuts.read(trial[n])+1)
        elif n=='sections':changed[n]=lambda *xs:False
        else:changed[n]=FunctionValue(('individual','individual'),FS,lambda *xs:FunctionValue((RS,),RS,lambda t:cuts.make(999)))
        assert not run('eibn',[changed[n] for n,_ in TRIAL],model),n
    # Swap just one profile's source/operation/result indices; the response cannot be borrowed.
    for name,t in PROFILES:
        if name in ('frame','sections'):continue
        changed=dict(fields);changed[name]=lambda s,o,a,name=name:profile(name,'other',o,a)
        assert not run('eibo',[changed[n] for n,_ in CAPACITY],model),name
    unknown=dict(model,eirk=forbidden)
    try:run('eibo',[fields[n] for n,_ in CAPACITY],unknown)
    except ValueError as e:assert 'Unknown transport-capacity' in str(e)
    else:raise AssertionError('Unknown trial accepted')
    return dict(three_condition_combinations=cases,trial_argument_mutations=len(TRIAL),cross_source_profiles_rejected=4,
        no_current_in_source_required=True,no_guarantee_for_all_possible_results=True,unknown_trial_rejected=True,
        response_boundary='eibm real-time existence')

@lru_cache(None)
def integration_checks():
    cuts,model=arithmetic();doc,slots=fixture('eibp');supplied=[]
    def sentinel(sort,tag):
        if sort in ('individual','situation'):return ('first' if sort=='situation' else 'body') if tag<100 else 'other'
        if sort=='truth':return tag<100
        if sort.get('parameters')==['number'] and sort.get('result')=='truth':return cuts.make(tag)
        return FunctionValue(tuple(sort['parameters']),sort['result'],lambda *xs:sentinel(sort['result'],tag))
    for i,(_,s) in enumerate(slots):supplied.append(sentinel(s,i+1))
    fields=MOTION+DISTRIBUTION+EXTRA;pos={n:i for i,(n,_) in enumerate(fields)}
    def gate(indices,enabled,xs):return enabled and all(same_value(x,supplied[i],slots[i][1],cuts) for x,i in zip(xs,indices,strict=True))
    mappings=[[pos['right'],pos[c+'context'],pos['timeunit'],pos['quantityunit'],pos['threshold']]+[pos['trial'+n] for n,_ in PROFILES] for c in ('first','second')]
    def local(bits):
        calls=[]
        def capacity(*xs):
            i=len(calls);calls.append(i);assert i<2
            return gate(mappings[i],bits[i+1],xs)
        return dict(model,eibj=lambda *xs:gate(list(range(len(MOTION+DISTRIBUTION))),bits[0],xs),eibo=capacity)
    for bits in product((False,True),repeat=3):assert run('eibp',supplied,local(bits))==all(bits)
    for i,(_,sort) in enumerate(slots):
        changed=supplied.copy();changed[i]='other' if sort in ('individual','situation') else sentinel(sort,100+i)
        assert not run('eibp',changed,local((True,True,True))),fields[i][0]
        original=supplied[i];supplied[i]=changed[i]
        assert run('eibp',changed,local((True,True,True))),fields[i][0];supplied[i]=original
    cuts,model,fields=history_fixture()
    try:run('eibm',[fields[n] for n,_ in RESPONSE],model,True)
    except ValueError as e:assert 'rational number domain' in str(e),str(e)
    else:raise AssertionError('Continuous-time existence sampled')
    return dict(shared_argument_mutations=len(slots),distinguishing_slot_variants=len(slots),truth_combinations=8,
        same_right_body_with_both_source_contexts=True,native_real_time_existence_refused=True)

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements']==old.document['statements'] and len(new.document['statements'])==207
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    assert '物理的に可能' in new.entries['zrdpossible']['meaning_ja']
    prior=json.loads(read(PRIOR));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[206])==prior['selection']
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=parse(read(CORE))
    for style in ('compact','full'):
        text=format_graph(doc,style);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    return dict(new_definitions=6,new_primitives=1,preserved_statements=207,existing_possible_outcome_relation_reused=True,
        author_review_preserved=True,core_roundtrips=['compact','full','v2'])

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)

def build_report():
    results={n:fn() for n,fn in [('threshold',threshold_checks),('witness',witness_checks),('modal',modal_checks),('integration',integration_checks),('structure',structure_checks)]}
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|{DOC,SOURCE,PRIOR,
        'scripts/compose_charge_transport_capacity.py','scripts/check_charge_transport_capacity.py','scripts/compose_limits.py',
        'scripts/compose_material_relative_frame.py','scripts/compose_current_distribution.py','scripts/compose_charge_transport_current.py','scripts/compose_relative_history_match.py',
        'scripts/check_charge_transport_current.py','scripts/check_material_relative_frame.py','scripts/check_tau_differential.py',
        'scripts/check_coordinate_correspondence.py','tests/test_charge_transport_capacity.py'}
    return dict(status='charge_transport_capacity_dependency_checked',document=FULL,**results,
        full_real_domain_evaluated=False,source_text_coverage_added=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
