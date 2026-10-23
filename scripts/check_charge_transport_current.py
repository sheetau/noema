"""Check transport signs, native composition and exact shared argument roles."""
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
from scripts.check_material_relative_frame import arithmetic,NUM
from scripts.compose_charge_transport_current import ROOT,read,PARENT,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,FIELDS,ELECTRIC,MATCH,MOTION,EXTRA,MEANINGS,build

DOC='docs/charge-transport-current-v1.md'
SOURCE='data/einstein-opening-obligations-v1.json'
PRIOR='data/einstein-author-credit-review-v1.json'
DOMAIN=('body','section','positive','charge','mass','frame','timeunit','chargeunit','other')
CONTEXTS=('case','other')

def forbidden(*args):raise ValueError('Unknown charge-transport input')

@lru_cache(None)
def fixture(symbol,native=False):
    doc=parse(read(CORE));doc['statements']=[]
    boundaries=set() if native else ({'eia3','eibc'} if symbol=='eibd' else {'eia5','li'})
    abstract(doc,NUM|boundaries)
    d=next(d for d in doc['declarations'] if d['name']==symbol);slots=[];arguments=[]
    for i,p in enumerate(d['parameters']):
        n='jctc'+number_word(i);slots.append((n,p['sort']))
        doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
        arguments.append(dict(kind='call',symbol=n,arguments=[]))
    doc['statements']=[dict(kind='ask',body=dict(kind='call',symbol=symbol,arguments=arguments))]
    return doc,slots

def run(symbol,values,model,native=False):
    doc,slots=fixture(symbol,native);assert len(slots)==len(values),(symbol,len(slots),len(values))
    model=dict(model)
    for (n,s),value in zip(slots,values,strict=True):
        if isinstance(s,dict) and not isinstance(value,FunctionValue):value=FunctionValue(tuple(s['parameters']),s['result'],value)
        model[n]=lambda value=value:value
    names={d['name'] for d in doc['declarations'] if d['kind']=='primitive'}
    return evaluate_document(doc,individuals=DOMAIN,situations=CONTEXTS,primitives={n:model.get(n,forbidden) for n in names},
        max_steps=300000,memoize_definitions=False,memoize_expressions=False)[0]['value']

def setup(coeff=(0,2,0),origin=0):
    cuts,model=arithmetic();r=cuts.read;coeff=tuple(map(Q,coeff))
    value=lambda t:Q(origin)+coeff[0]+coeff[1]*t+coeff[2]*t*t
    cumulative=lambda t:cuts.make(value(r(t)))
    base=['body','section','positive','charge','frame','case','timeunit','chargeunit',cuts.make(0),cuts.make(2),cumulative]
    def transferred(*xs):
        return tuple(xs[:8])==tuple(base[:8]) and r(xs[10])==value(r(xs[9]))-value(r(xs[8]))
    model.update(zm=lambda x:x=='body',zor=lambda:'charge',eiri=transferred)
    return cuts,model,base,value

@lru_cache(None)
def transport_checks():
    count=0
    for coeff,origin in product(((0,2,0),(0,-2,0),(0,0,0),(0,-2,1)),(0,17)):
        cuts,model,base,value=setup(coeff,origin);r=cuts.read
        for a,b in product((-1,0,Q(1,2),1,2,3),repeat=2):
            amount=value(b)-value(a);expected=0<=a<=b<=2
            assert run('eia4',base+[cuts.make(a),cuts.make(b),cuts.make(amount)],model)==expected
            assert not run('eia4',base+[cuts.make(a),cuts.make(b),cuts.make(amount+1)],model)
            count+=2
    cuts,model,base,value=setup();args=base+[cuts.make(0),cuts.make(1),cuts.make(2)]
    for i in range(8):
        changed=args.copy();changed[i]='other'
        assert not run('eia4',changed,model),FIELDS[i][0]
    assert not run('eia4',args,dict(model,eiri=lambda *xs:False))
    bad=args.copy();bad[10]=lambda t:cuts.make(4*cuts.read(t))
    assert not run('eia4',bad,model)
    try:run('eia4',args,dict(model,eiri=forbidden))
    except ValueError as e:assert 'Unknown charge-transport' in str(e)
    else:raise AssertionError('Unknown transfer accepted')
    # The sign convention counts signed amount times crossing direction.
    signed=[]
    for charge,direction in product((-1,1),repeat=2):
        rate=charge*direction;cuts,model,base,value=setup((0,rate,0))
        assert run('eia4',base+[cuts.make(0),cuts.make(1),cuts.make(rate)],model)
        signed.append([charge,direction,rate])
    return dict(interval_and_amount_cases=count,reference_mutations=8,sign_convention=signed,
        arbitrary_cumulative_origin_allowed=True,false_or_unknown_physical_transfer_not_inferred=True)

@lru_cache(None)
def derivative_checks():
    count=0;calls=0
    for coeff in ((0,2,0),(0,-2,0),(0,0,0),(0,-2,1)):
        cuts,model,base,value=setup(coeff);r=cuts.read
        def history(*xs):
            return tuple(xs[:8])==tuple(base[:8]) and r(xs[8])==0 and r(xs[9])==2 and all(r(xs[10](cuts.make(t)))==value(t) for t in (0,1,2))
        def derivative(domain,fn,time,rate):
            nonlocal calls
            calls+=1
            assert [domain(cuts.make(t)) for t in (-1,0,1,2,3)]==[False,True,True,True,False]
            assert all(r(fn(cuts.make(t)))==value(t) for t in (0,1,2))
            return r(rate)==coeff[1]+2*coeff[2]*r(time)
        model.update(eia5=history,li=derivative)
        electric=base[:3]+base[4:]
        for t,wrong in product((0,Q(1,2),1,2), (False,True)):
            rate=coeff[1]+2*coeff[2]*t+int(wrong)
            assert run('eia7',electric+[cuts.make(t),cuts.make(rate)],model)==(not wrong)
            count+=1
        changed=base.copy();changed[3]='mass'
        assert not run('eia6',changed+[cuts.make(1),cuts.make(coeff[1]+2*coeff[2])],model)
        assert not run('eia7',electric+[cuts.make(3),cuts.make(coeff[1]+6*coeff[2])],model)
        assert not run('eia7',electric+[cuts.make(1),cuts.make(coeff[1]+2*coeff[2])],dict(model,eia5=lambda *xs:False))
    return dict(rate_cases=count,derivative_calls=calls,charge_kind_fixed=True,closed_interval_passed_to_li=True,
        boundary_inputs=['eia5 full transport history','li exact polynomial derivative fixture'],
        full_derivative_theorem_proved=False)

@lru_cache(None)
def comparison_checks():
    counts={}
    for scenario in ('match','opposite','changed_midcourse','same_total','rescaled_time'):
        cuts,model=arithmetic();r=cuts.read
        first=lambda t:cuts.make(2*r(t))
        def second(t):
            e=r(t)-5
            return cuts.make(-2*e if scenario=='opposite' else 2*e+e*(2-e) if scenario=='changed_midcourse' else 2 if scenario=='same_total' else 2*e)
        last=9 if scenario=='rescaled_time' else 7
        prefix=[cuts.make(x) for x in (0,2,5,last,5)]+[first,second]
        results=[]
        for t in (-1,0,Q(1,2),1,Q(3,2),2,3):
            expected=0<=t<=2 and last==7 and r(first(cuts.make(t)))==r(second(cuts.make(t+5)))
            result=run('eibb',prefix+[cuts.make(t)],model);assert result==expected;results.append(result)
        counts[scenario]=results
    return dict(snapshot_cases=35,scenarios=counts,signed_values_compared=True,
        equal_total_or_endpoints_do_not_replace_full_history=True)

def same_value(x,y,sort,cuts):
    if sort in ('individual','situation','truth'):return x==y
    if sort.get('result')=='truth' and sort.get('parameters')==['number']:return cuts.read(x)==cuts.read(y)
    # Sentinel callbacks of the exact declared sort, including nested families.
    args=['body' if s=='individual' else cuts.make(1) for s in sort['parameters']]
    return same_value(x(*args),y(*args),sort['result'],cuts)

@lru_cache(None)
def integration_checks():
    cuts,model=arithmetic();doc,slots=fixture('eibd');args=[]
    def sentinel(sort,tag):
        if sort in ('individual','situation'):return 'case' if sort=='situation' else 'body'
        if sort=='truth':return tag<100
        if sort.get('parameters')==['number'] and sort.get('result')=='truth':return cuts.make(tag)
        return FunctionValue(tuple(sort['parameters']),sort['result'],lambda *xs:sentinel(sort['result'],tag))
    for i,(_,s) in enumerate(slots):args.append(sentinel(s,i+1))
    fields=MOTION+EXTRA;pos={n:i for i,(n,_) in enumerate(fields)}
    match_positions=[pos['right' if n=='body' else n] for n,_ in MATCH]
    def gate(indices,enabled):
        def check(*xs):
            assert len(xs)==len(indices)
            return enabled and all(same_value(x,args[i],slots[i][1],cuts) for x,i in zip(xs,indices))
        return check
    for first,second in product((False,True),repeat=2):
        local=dict(model,eia3=gate(list(range(len(MOTION))),first),eibc=gate(match_positions,second))
        assert run('eibd',args,local)==(first and second)
    local=dict(model,eia3=gate(list(range(len(MOTION))),True),eibc=gate(match_positions,True))
    for i,(_,sort) in enumerate(slots):
        changed=args.copy();changed[i]='other' if sort in ('individual','situation') else sentinel(sort,100+i)
        assert not run('eibd',changed,local),fields[i][0]
        original=args[i];args[i]=changed[i]
        assert run('eibd',changed,local),('distinct slot accepted',fields[i][0])
        args[i]=original
    refused=[]
    for symbol in ('eia5','eiba','eibc'):
        d,ss=fixture(symbol,True)
        if symbol=='eia5':_,mm,aa,_=setup();model2=mm;values=aa
        elif symbol=='eiba':
            cc,mm,aa,_=setup();model2=mm;values=aa[:3]+aa[4:]+[lambda t:cc.make(2)]
        else:
            cc,model2=arithmetic();model2.update(zor=lambda:'charge',zm=lambda x:True,eiri=lambda *xs:True)
            values=['body','section','positive','timeunit','chargeunit']
            for offset in (0,5):values+=['frame','case',cc.make(offset),cc.make(offset+2),lambda t:cc.make(0),lambda t:cc.make(0)]
            values+=[cc.make(5)]
        try:run(symbol,values,model2,True)
        except ValueError as e:assert 'rational number domain' in str(e),(symbol,str(e))
        else:raise AssertionError('Full real history sampled: '+symbol)
        refused.append(symbol)
    return dict(shared_argument_mutations=len(slots),distinguishing_slot_variants=len(slots),motion_and_current_truth_cases=4,
        right_body_and_same_case_references_preserved=True,full_real_domains_refused=refused)

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
    return dict(new_definitions=8,new_primitives=1,preserved_statements=207,author_review_preserved=True,core_roundtrips=['compact','full','v2'])

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)

def build_report():
    results={n:fn() for n,fn in [('transport',transport_checks),('derivative',derivative_checks),('comparison',comparison_checks),('integration',integration_checks),('structure',structure_checks)]}
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|{DOC,SOURCE,PRIOR,
        'scripts/compose_charge_transport_current.py','scripts/check_charge_transport_current.py','scripts/compose_limits.py',
        'scripts/compose_material_relative_frame.py','scripts/compose_relative_history_match.py','scripts/check_material_relative_frame.py',
        'scripts/check_tau_differential.py','scripts/check_coordinate_correspondence.py','tests/test_charge_transport_current.py'}
    return dict(status='charge_transport_current_dependency_checked',document=FULL,**results,
        full_real_domain_evaluated=False,source_text_coverage_added=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
