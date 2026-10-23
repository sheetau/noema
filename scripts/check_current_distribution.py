"""Check complete section scope, distribution bindings and local comparisons."""
from fractions import Fraction as Q
from functools import lru_cache
from itertools import product
import json
from noema.grammar import parse,format_graph,number_word
from noema.finite_semantics import FunctionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_material_relative_frame import arithmetic,NUM,RS
from scripts.check_charge_transport_current import same_value
from scripts.compose_current_distribution import ROOT,read,PARENT,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,SCOPE_FIELDS,HISTORY,PAIR,MOTION,EXTRA,MEANINGS,build

DOC='docs/current-distribution-v1.md';SOURCE='data/einstein-opening-obligations-v1.json';PRIOR='data/einstein-author-credit-review-v1.json'
DOMAIN=('body','a','b','positive','negative','frame','timeunit','chargeunit','charge','other')
CONTEXTS=('first','second','other')
SECTIONS=tuple(product(('a','b'),('positive','negative')))

def forbidden(*args):raise ValueError('Unknown current-distribution input')

@lru_cache(None)
def fixture(symbol,native=False):
    doc=parse(read(CORE));doc['statements']=[]
    boundaries=set() if native else ({'eia3','eibi'} if symbol=='eibj' else {'eibg'} if symbol=='eibh' else {'eiba','eibc'})
    abstract(doc,NUM|boundaries)
    d=next(d for d in doc['declarations'] if d['name']==symbol);slots=[];arguments=[]
    for i,p in enumerate(d['parameters']):
        n='jcdi'+number_word(i);slots.append((n,p['sort']))
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

def setup(scenario='match'):
    cuts,model=arithmetic();r=cuts.read
    def value(case,s,o,t,integrated=False):
        offset=5 if case=='second' else 0;e=t-offset
        ss={'a':'b','b':'a'}.get(s,s) if case=='second' and scenario=='swap_sections' else s
        sign=-1 if o=='negative' else 1
        if case=='second' and scenario=='reverse_orientation':sign=-sign
        a,b=(1,1) if ss=='a' else (3,-1)
        result=a*e+b*e*e/2 if integrated else a+b*e
        if case=='second' and scenario=='hidden_branch' and s=='b':result+=(e if integrated else 1)
        if case=='second' and scenario=='midcourse' and s=='b':result+=(e*e-e*e*e/3 if integrated else e*(2-e))
        return sign*result+(17 if integrated and case=='second' else 0)
    def family(case,integrated):return lambda s,o:FunctionValue((RS,),RS,lambda t:cuts.make(value(case,s,o,r(t),integrated)))
    scope=lambda s,o:(s,o) in SECTIONS
    fields=dict(body='body',timeunit='timeunit',quantityunit='chargeunit',sections=scope,offset=cuts.make(5))
    for case,offset in (('first',0),('second',5)):
        fields.update({case+'frame':'frame',case+'context':case,case+'lower':cuts.make(offset),case+'upper':cuts.make(offset+2),
            case+'cumulative':family(case,True),case+'current':family(case,False)})
    def physical(body,s,o,context):
        actual=set(SECTIONS)
        if context=='second' and scenario=='scope_loss':actual.remove(('b','negative'))
        if context=='second' and scenario=='scope_extra':actual.add(('other','positive'))
        return body=='body' and context in ('first','second') and (s,o) in actual
    calls=[];comparisons=[]
    def history(*xs):
        body,s,o,frame,context,timeunit,unit,lower,upper,cumulative,current=xs
        calls.append((s,o,context))
        if context not in ('first','second'):return False
        offset=5 if context=='second' else 0
        return (body=='body' and frame=='frame' and timeunit=='timeunit' and unit=='chargeunit'
            and r(lower)==offset and r(upper)==offset+2 and
            all(r(fn(cuts.make(t+offset)))==value(context,s,o,Q(t+offset),integrated)
                for fn,integrated in ((cumulative,True),(current,False)) for t in (0,1,2))
            and not (scenario=='missing_history' and context=='second' and (s,o)==('b','negative')))
    def comparison(*xs):
        body,s,o,timeunit,unit=xs[:5];comparisons.append((s,o))
        sides=[]
        for start in (5,11):
            frame,context,lower,upper,cumulative,current=xs[start:start+6]
            sides.append(history(body,s,o,frame,context,timeunit,unit,lower,upper,cumulative,current))
        # This is a declared full-history boundary on these fixture profiles.
        # Samples verify arguments; they do not certify an arbitrary real function.
        assert r(xs[17])==5
        unequal=scenario in ('swap_sections','reverse_orientation') or (s=='b' and scenario in ('hidden_branch','midcourse'))
        return all(sides) and not unequal if (s,o) in SECTIONS else True
    model.update(zm=lambda b:b=='body',eirj=physical,eiba=history,eibc=comparison)
    return cuts,model,fields,value,calls,comparisons

def values(fields,layout):return [fields[n] for n,_ in layout]
def case_fields(fields,case):return {n:fields[case+n] if n in ('frame','context','lower','upper','cumulative','current') else fields[n] for n,_ in HISTORY}

@lru_cache(None)
def scope_checks():
    cuts,model,fields,_,_,_=setup();count=0
    for bits in product((False,True),repeat=4):
        chosen={pair for pair,yes in zip(SECTIONS,bits) if yes};scope=lambda s,o:(s,o) in chosen
        assert run('eibe',['body','first',scope],model)==all(bits);count+=1
    for extra in (('other','positive'),('a','other'),('positive','a')):
        scope=lambda s,o:(s,o) in set(SECTIONS)|{extra}
        assert not run('eibe',['body','first',scope],model);count+=1
    assert not run('eibe',['other','first',fields['sections']],model)
    assert not run('eibe',['body','other',fields['sections']],model)
    assert not run('eibe',['body','first',lambda *xs:False],dict(model,eirj=lambda *xs:False))
    try:run('eibe',['body','first',fields['sections']],dict(model,eirj=forbidden))
    except ValueError as e:assert 'Unknown current-distribution' in str(e)
    else:raise AssertionError('Unknown scope accepted')
    return dict(subset_and_extra_cases=count,empty_physical_scope_rejected=True,unknown_scope_rejected=True,
        body_context_and_orientation_preserved=True)

@lru_cache(None)
def distribution_checks():
    results={}
    for scenario in ('match','scope_loss','scope_extra','missing_history','hidden_branch','midcourse','swap_sections','reverse_orientation'):
        cuts,model,fields,_,calls,comparisons=setup(scenario)
        prepared=run('eibg',values(fields,PAIR),model)
        assert prepared==(scenario not in ('scope_loss','scope_extra','missing_history'))
        complete=run('eibi',values(fields,PAIR),model)
        assert complete==(scenario=='match')
        if scenario=='match':
            assert set(SECTIONS)<=set(comparisons)
            assert {(s,o,c) for s,o in SECTIONS for c in ('first','second')}<=set(calls)
        results[scenario]=dict(prepared=prepared,whole_distribution=complete)
    # Each single failing pair must veto the universal distribution, including the last pair.
    cuts,model,fields,_,_,comparisons=setup()
    for rejected in SECTIONS:
        def unequal(*xs):return tuple(xs[1:3])!=rejected
        assert not run('eibi',values(fields,PAIR),dict(model,eibc=unequal))
    # Mutation tests bind complete one-case metadata and family selection.
    first=case_fields(fields,'first');count=0
    for n,t in HISTORY:
        changed=dict(first)
        if t in ('a','d'):changed[n]='other'
        elif n in ('lower','upper'):changed[n]=cuts.make(cuts.read(first[n])+1)
        elif n=='sections':changed[n]=lambda *xs:False
        else:changed[n]=lambda s,o:FunctionValue((RS,),RS,lambda t:cuts.make(99))
        assert not run('eibf',values(changed,HISTORY),model),n;count+=1
    return dict(scenarios=results,individual_failing_pairs=len(SECTIONS),single_history_argument_mutations=count,
        all_section_orientation_pairs_visited=True,boundary_inputs=['eiba continuous physical history','eibc continuous history equality'])

@lru_cache(None)
def snapshot_checks():
    cases=0;results={}
    for scenario in ('match','hidden_branch','midcourse','swap_sections','reverse_orientation'):
        cuts,model,fields,value,_,_=setup(scenario);r=cuts.read
        # Validity of the full physical histories is an input here. Native eibg was checked separately.
        model['eibg']=lambda *xs:True
        matching=[]
        for s,o,t in product(('a','b','other'),('positive','negative'),(-1,0,1,2,3)):
            expected=(s,o) in SECTIONS and 0<=t<=2 and value('first',s,o,Q(t))==value('second',s,o,Q(t+5))
            result=run('eibh',values(fields,PAIR)+[s,o,cuts.make(t)],model)
            assert result==expected;(matching.append([s,o,t]) if result else None);cases+=1
        results[scenario]=matching
    cuts,model,fields,_,_,_=setup();model['eibg']=lambda *xs:False
    assert not run('eibh',values(fields,PAIR)+['a','positive',cuts.make(1)],model)
    return dict(snapshot_cases=cases,matching=results,same_sum_does_not_merge_sections=True,invalid_pair_rejected=True)

@lru_cache(None)
def integration_checks():
    cuts,model=arithmetic();doc,slots=fixture('eibj');supplied=[]
    def sentinel(sort,tag):
        if sort in ('individual','situation'):return 'first' if sort=='situation' else 'body'
        if sort=='truth':return tag<100
        if sort.get('parameters')==['number'] and sort.get('result')=='truth':return cuts.make(tag)
        return FunctionValue(tuple(sort['parameters']),sort['result'],lambda *xs:sentinel(sort['result'],tag))
    for i,(_,s) in enumerate(slots):supplied.append(sentinel(s,i+1))
    fields=MOTION+EXTRA;pos={n:i for i,(n,_) in enumerate(fields)};pair_positions=[pos['right' if n=='body' else n] for n,_ in PAIR]
    def gate(indices,enabled):
        def check(*xs):
            assert len(xs)==len(indices)
            return enabled and all(same_value(x,supplied[i],slots[i][1],cuts) for x,i in zip(xs,indices))
        return check
    for first,second in product((False,True),repeat=2):
        local=dict(model,eia3=gate(list(range(len(MOTION))),first),eibi=gate(pair_positions,second))
        assert run('eibj',supplied,local)==(first and second)
    local=dict(model,eia3=gate(list(range(len(MOTION))),True),eibi=gate(pair_positions,True))
    for i,(_,sort) in enumerate(slots):
        changed=supplied.copy();changed[i]='other' if sort in ('individual','situation') else sentinel(sort,100+i)
        assert not run('eibj',changed,local),fields[i][0]
        original=supplied[i];supplied[i]=changed[i];assert run('eibj',changed,local),fields[i][0];supplied[i]=original
    cuts,model,fields,_,_,_=setup();model.update(zor=lambda:'charge',eiri=lambda *xs:True)
    try:run('eibf',values(case_fields(fields,'first'),HISTORY),model,True)
    except ValueError as e:assert 'rational number domain' in str(e),str(e)
    else:raise AssertionError('Full real history replaced by finite samples')
    return dict(shared_argument_mutations=len(slots),distinguishing_slot_variants=len(slots),truth_combinations=4,
        right_body_and_two_case_scope_preserved=True,native_full_real_history_refused=True)

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
    return dict(new_definitions=6,new_primitives=1,preserved_statements=207,author_review_preserved=True,core_roundtrips=['compact','full','v2'])

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)

def build_report():
    results={n:fn() for n,fn in [('scope',scope_checks),('distribution',distribution_checks),('snapshots',snapshot_checks),('integration',integration_checks),('structure',structure_checks)]}
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|{DOC,SOURCE,PRIOR,
        'scripts/compose_current_distribution.py','scripts/check_current_distribution.py','scripts/compose_limits.py',
        'scripts/compose_material_relative_frame.py','scripts/compose_charge_transport_current.py','scripts/compose_relative_history_match.py',
        'scripts/check_charge_transport_current.py','scripts/check_material_relative_frame.py',
        'scripts/check_tau_differential.py','scripts/check_coordinate_correspondence.py','tests/test_current_distribution.py'}
    return dict(status='current_distribution_dependency_checked',document=FULL,**results,
        full_real_domain_evaluated=False,source_text_coverage_added=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
