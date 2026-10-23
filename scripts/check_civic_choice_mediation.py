"""Check full-profile interventions and gradual mediated gains without extinction."""
from copy import deepcopy
from functools import lru_cache
from fractions import Fraction
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import FunctionValue,SequenceValue
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_civic_choice_mediation import ROOT,LIBRARY,BASIS,STATE,MEANINGS,PRIMITIVES,LIMITS,parent,choice,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown
from scripts.check_scoped_counts import arithmetic

DOC='docs/civic-choice-mediation-v1.md';READING='data/civic-choice-mediation-reading-v1.json'
INVENTORY='artifacts/written-units-v1/kant-1784.json';SOURCE='data/tenth-paragraph-source-reading-v1.json';INDEX='data/semantic-review-index-v206.json'
PRIORS=('reports/civic-feedback-v1.json','reports/self-directed-choice-v1.json')
DOMAIN=('a','b','c');PEOPLE=('a','b');PAIRS=tuple(product(PEOPLE,repeat=2))
ON=('start','middle','end');OFF=('offstart','offmiddle','offend');MIX=('mixstart','mixmiddle','mixend')
SCENES=(*ON,*OFF,*MIX,'reference','other')
CONSTANTS=dict(community='b',lowerorder='a',higherorder='b',reference='reference',start='start',end='end',point='end')
CONTEXT=tuple(CONSTANTS)[:-1];ARGS=' '.join('k z'+n+'[]' for n in CONTEXT)
LOWER=('r6ke','r6kc','r6jx','r6jy','r6kq','r6kp','r6kr')

def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def seq(xs):return SequenceValue(tuple(xs),'"individual"')
def state(a=True,b=False,c=True):return FunctionValue(('individual',),'truth',lambda x:dict(a=a,b=b,c=c)[x])
def bits(s):return tuple(s(x) for x in DOMAIN)
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(roots,query,boundaries=LOWER):
    d=deepcopy(catalog().document);d['statements']=[]
    for r in d['declarations']:
        if r['name'] in boundaries:r.update(kind='primitive',parameters=[p['sort'] for p in r['parameters']]);r.pop('body')
    d['declarations']=closure(d,roots)
    extra=''.join('r z'+n+'[] '+('a' if v in DOMAIN else 'd')+'.' for n,v in CONSTANTS.items())+'r zstate[] '+STATE+'.'
    return parse(format_graph(d,'compact')+extra+query)

def good(c,r):return(c,r)==('b','reference')
def context(*a):return tuple(a)==('b','a','b','reference','start','end')
def clock(s,e):return next((h for h in (ON,OFF,MIX) if(s,e)==(h[0],h[-1])),())
def dynamic(p,f,t):return (p,f)==('a','a') and t in ('middle','end') or (p,f)==('a','b') and t=='end'
def model(d,on=(0,2,4),off=(0,1,2),mixed=(0,1,2),bound=2):
    v={r['name']:unknown for r in d['declarations'] if r['kind']=='primitive'};v.update(arithmetic())
    v.update({'z'+n:lambda x=x:x for n,x in CONSTANTS.items()});v['zstate']=lambda:state(False,False,False)
    def mapped(*a):
        *ctx,s,t=a
        if not context(*ctx):return 'other'
        h=ON if s('c') else MIX if s('a') else OFF
        return h[ON.index(t)] if t in ON else t
    def profile(c,r,p,f,t):
        h=next((h for h in (ON,OFF,MIX) if t in h),())
        return good(c,r) and(p,f)in PAIRS and h==ON and dynamic(p,f,ON[h.index(t)])
    def score(c,r,t):
        for h,values in ((ON,on),(OFF,off),(MIX,mixed)):
            if t in h and good(c,r):return Fraction(values[h.index(t)])
        return Fraction(0)
    v.update(aa=lambda p:p in PEOPLE,h237c=lambda p,c,r:good(c,r) and p in PEOPLE,
      h26zj=lambda:'reference',h27b7=lambda c,r,p,f:good(c,r) and(p,f)in PAIRS,
      h27ch=lambda c,r,s,e,t:good(c,r) and t in clock(s,e),
      h27ci=lambda c,r,s,e,l,h:good(c,r) and l in clock(s,e) and h in clock(s,e) and clock(s,e).index(l)<clock(s,e).index(h),
      h27cm=lambda *a:seq(DOMAIN),h27cn=lambda *a:True if a[-2]=='a' else False if a[-2]=='b' else a[-1]('a'),
      h27co=lambda *a:'a',h27cp=lambda *a:state(),h27cq=mapped,h27c4=lambda c,r:Fraction(bound),
      h27c5=lambda *a:'c' if dynamic(*a[-3:]) else 'b',
      r6ke=lambda *a:context(*a),r6kc=lambda *a:context(*a[:-1]) and not a[-1]('b'),
      r6jx=lambda c,r,p,f,t:good(c,r) and(p,f)in PAIRS and t in (*ON,*OFF,*MIX),r6jy=profile,
      r6kq=lambda c,r,s,e:good(c,r) and bool(clock(s,e)),r6kp=score,
      r6kr=lambda c,r,s,e:good(c,r) and (s,e)==('start','end') and gradual(on,bound))
    return v
def run(d,v,scenes=SCENES,domain=DOMAIN):return evaluate(d,v,domain,scenes,True)
def rejects(d,v):
    try:run(d,v)
    except ValueError as e:assert 'Unknown' in str(e),str(e)
    else:raise AssertionError('Unknown accepted')
def gradual(values,bound):
    def middle(i,j):return any(min(values[i],values[j])<values[m]<max(values[i],values[j]) for m in range(i+1,j))
    return bool(bound>0 and values[-1]>values[0] and middle(0,len(values)-1) and
        all(abs(values[j]-values[i])<=bound or middle(i,j) for i in range(len(values)) for j in range(i+1,len(values))))

def bounded_adapters(v):
    # Native bodies are checked separately below. Read providers dynamically so
    # mutations still check the same content/clock inputs in structural tests.
    ctx=('b','a','b','reference','start','end')
    slots=tuple(product(PEOPLE,PEOPLE,ON))
    v['r6ku']=lambda *a:context(*a[:-1]) and a[-1] in {v['h27c5'](*ctx,*slot) for slot in slots}
    v['r6kv']=lambda *a:context(*a) and all(v['h27c5'](*ctx,*slot) in v['h27cm'](*ctx).items and v['h27c5'](*ctx,*slot)!=v['h27co'](*ctx) for slot in slots)
    def assessed(*a):
        *given,s=a
        if not context(*given):return False
        mapped=lambda t:v['h27cq'](*given,s,t)
        return bool(v['r6kc'](*given,s) and v['r6kq']('b','reference',mapped('start'),mapped('end')) and
            all(v['r6jx']('b','reference',p,f,mapped(t)) and s(v['h27c5'](*given,p,f,t))==v['r6jy']('b','reference',p,f,mapped(t)) for p,f,t in slots))
    def gain(*a):
        *given,s=a
        if not context(*given):return False
        observed=v['h27cp'](*given)
        return gradual(tuple(v['r6kp']('b','reference',v['h27cq'](*given,observed,t))-v['r6kp']('b','reference',v['h27cq'](*given,s,t)) for t in ON),v['h27c4']('b','reference'))
    v['r6kw']=assessed;v['r6kx']=gain
    return v

@lru_cache(None)
def contrast_checks():
    q='r zscore[d] b.r zbaseline[d] b.q[k r6kt[k zcommunity[] k zreference[] k zstart[] k zend[] p zscore p zbaseline]].'
    d=fixture(('r6kt',),q);rows=0
    for delta,base in product(product(range(-1,3),repeat=3),((0,0,0),(1,2,3),(3,1,4))):
        v=model(d,bound=1)
        v['zscore']=lambda t:Fraction(delta[ON.index(t)]+base[ON.index(t)]) if t in ON else Fraction(0)
        v['zbaseline']=lambda t:Fraction(base[ON.index(t)]) if t in ON else Fraction(0)
        assert run(d,v,(*ON,'reference','other'))==[gradual(delta,1)],(delta,base);rows+=1
    cases={}
    for label,values,bound,expected in (
      ('negative_initial_advantage',(-2,-1,0,1),1,True),('local_regression',(0,2,1,3),2,True),
      ('plateau',(0,1,1,2),1,True),('jump',(0,0,0,3),1,False),('unchanging_advantage',(2,2,2,2),1,False),
      ('zero_bound',(0,1,2,3),0,False),('large_downward_jump',(0,4,1,5),2,False)):
        times=('start','step','middle','end');v=model(d,bound=bound)
        v['h27ch']=lambda c,r,s,e,t:good(c,r) and(s,e)==('start','end') and t in times
        v['h27ci']=lambda c,r,s,e,l,h:l in times and h in times and times.index(l)<times.index(h)
        v['zscore']=lambda t:Fraction(values[times.index(t)]) if t in times else Fraction(0)
        v['zbaseline']=lambda t:Fraction(0)
        assert run(d,v,(*times,'reference','other'))==[expected],label;cases[label]=expected
    # The adapter must supply the exact same clock/reference in both trajectories.
    d=fixture(('r6kx',),'q[k r6kx['+ARGS+' k zstate[]]].',(*LOWER,'r6kt'));v=model(d)
    def components(c,r,s,e,score,baseline):
        assert(c,r,s,e)==('b','reference','start','end')
        for t in ON:
            assert score(t)==v['r6kp'](c,r,t)
            assert baseline(t)==v['r6kp'](c,r,OFF[ON.index(t)])
        return True
    v['r6kt']=components;assert run(d,v)==[True]
    return dict(native_difference_trajectories=rows,contrasts=cases,exact_two_score_component_bindings=True)

@lru_cache(None)
def scope_content_checks():
    d=fixture(('r6ku','r6kv','r6kw'),'r zvariable[] a.q[k r6ku['+ARGS+' k zvariable[]]].q[k r6kv['+ARGS+']].q[k r6kw['+ARGS+' k zstate[]]].')
    v=model(d);v['zvariable']=lambda:'c';assert run(d,v)==[True,True,True]
    v['zstate']=lambda:state();assert run(d,v)==[True,True,True]
    v['zvariable']=lambda:'a';assert run(d,v)==[False,True,True]
    cases={}
    for label in ('alias_cause','outside_model','missing_mapped_assessment','false_profile_label','invalid_ability_scope','invalid_causal_clock'):
        w=dict(v)
        if label=='alias_cause':w['h27c5']=lambda *a:'a'
        if label=='outside_model':w['h27cm']=lambda *a:seq(('a','b'))
        if label=='missing_mapped_assessment':w['r6jx']=lambda *a:not (a[-3:]==('b','b','middle'))
        if label=='false_profile_label':w['r6jy']=lambda *a:False
        if label=='invalid_ability_scope':w['r6kq']=lambda *a:False
        if label=='invalid_causal_clock':w['r6kc']=lambda *a:False
        result=run(d,w);assert not all(result[1:]),(label,result);cases[label]=result
    # One distinguished tuple per trial detects person/feature/time permutations.
    b=fixture(('r6kw',),'q[k r6kw['+ARGS+' k zstate[]]].');rows=0
    for target in product(PEOPLE,PEOPLE,ON):
        w=model(b);w['zstate']=lambda:state(True,False,True)
        w['h27c5']=lambda *a:'c' if a[-3:]==target else 'b'
        w['r6jy']=lambda c,r,p,f,t:good(c,r) and(p,f,t)==target
        assert run(b,w)==[True],target
        w['h27c5']=lambda *a:'b';assert run(b,w)==[False],target;rows+=1
    for n in ('h27c5','h27cm','h27co','h27cq','r6jx','r6jy','r6kq','r6kc'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    return dict(contrasts=cases,all_12_distinguished_content_bindings=rows,shared_variables_with_consistent_contents_allowed=True,
      full_scope_mask_and_model_membership_native=True,unknown_rejected=True,
      boundary='Unchanged r6kc, r6kq, r6jx and r6jy are pinned lower boundaries. New full-scope quantification, variable selection and content equality execute natively.')

@lru_cache(None)
def mediation_checks():
    d=fixture(('r6kz',),'q[k r6kz['+ARGS+']].',(*LOWER,'r6ku','r6kv','r6kw','r6kx'));v=bounded_adapters(model(d));assert run(d,v)==[True];cases={}
    for label,on,mixed,expected in (
      ('both_sides_grow',(0,2,4),(0,1,2),True),
      ('common_growth',(0,2,4),(0,2,4),False),
      ('constant_existing_advantage',(1,3,5),(0,2,4),False),
      ('nonzero_initial_advantage',(1,3,5),(0,1,2),True),
      ('counterfactual_grows_faster',(0,1,2),(0,2,4),False)):
        w=bounded_adapters(model(d,on=on,mixed=mixed));actual=run(d,w);assert actual==[expected],(label,actual);cases[label]=expected
    for label in ('no_feedback','no_actual_growth','bad_variable_map','missing_hybrid_assessment','false_hybrid_content','missing_off_assessment','no_off_solution','one_off_source_without_gain','one_on_solution_unassessed'):
        w=bounded_adapters(model(d))
        if label=='no_feedback':w['r6ke']=lambda *a:False
        if label=='no_actual_growth':w['r6kr']=lambda *a:False
        if label=='bad_variable_map':w['h27c5']=lambda *a:'a'
        if label=='missing_hybrid_assessment':w['r6kq']=lambda c,r,s,e:s!='mixstart'
        if label=='false_hybrid_content':w['r6jy']=lambda *a:True if a[-1]=='mixmiddle' else v['r6jy'](*a)
        if label=='missing_off_assessment':w['r6kq']=lambda c,r,s,e:s!='offstart'
        # An unmasked downstream variable with no hybrid fixed point is
        # checked in the separate fixed-point table below.
        if label=='no_off_solution':w['h27cn']=lambda *a:not a[-1]('c') if a[-2]=='c' and not a[-1]('a') else v['h27cn'](*a)
        if label=='one_off_source_without_gain':w['h27cn']=lambda *a:a[-1]('c') if a[-2]=='c' and not a[-1]('a') else v['h27cn'](*a)
        if label=='one_on_solution_unassessed':
            w['h27cn']=lambda *a:a[-1]('c') if a[-2]=='c' and a[-1]('a') else v['h27cn'](*a)
            w['r6kq']=lambda c,r,s,e:s!='mixstart'
        assert run(d,w)==[False],label;cases[label]=False
    for n in ('h27cn','h27cp','h27cq','h27c5','r6kp'):
        w=bounded_adapters(model(d));w[n]=unknown;rejects(d,w)
    # Enumerate cyclic/non-deterministic equations for an unmasked downstream
    # variable. Only mask/content/gain adapters are boundaries in this oracle.
    b=fixture(('r6ky',),'q[k r6ky['+ARGS+' k zstate[]]].',(*LOWER,'r6ku','r6kw','r6kx'))
    rows=[]
    for table in range(4):
        w=model(b);w['r6ku']=lambda *a:a[-1]=='c';w['r6kw']=lambda *a:True
        w['r6kx']=lambda *a:not a[-1]('b')
        w['h27cn']=lambda *a,table=table:bool(table&(1<<int(a[-1]('b')))) if a[-2]=='b' else v['h27cn'](*a)
        solutions=[x for x in (False,True) if x==bool(table&(1<<int(x)))]
        expected=bool(solutions and all(not x for x in solutions))
        assert run(b,w)==[expected],(table,solutions);rows.append(dict(table=table,solutions=solutions,result=expected))
    return dict(native_structural_interventions_and_top_level_composition=True,contrasts=cases,native_all_four_downstream_fixed_point_tables=rows,unknown_rejected=True,
      boundary='r6ke/r6kc and prior ability/profile bodies are unchanged pinned boundaries. Main structural tests bound r6ku/r6kv/r6kw/r6kx after checking their native bodies separately; this avoids multiplying full-history comparisons by every assignment of every nested intervention. r6ky/r6kz and ru/rs/rv/rw execute natively. The separate downstream oracle isolates nonempty/all-solutions behavior.')

@lru_cache(None)
def intervention_binding_checks():
    # Inspect every argument passed to rw without enumerating a large state
    # domain; native rw is independently exercised above.
    d=fixture(('r6ky',),'q[k r6ky['+ARGS+' k zstate[]]].',(*LOWER,'rw','r6kw','r6kx'));v=model(d);calls=[]
    v['r6kw']=lambda *a:context(*a[:-1]) and bits(a[-1])==(True,False,False)
    v['r6kx']=lambda *a:context(*a[:-1]) and bits(a[-1])==(True,False,False)
    def rw(variables,equations,mask,assigned,predicate):
        assert variables.items==DOMAIN
        for s in (state(*bits_) for bits_ in product((False,True),repeat=3)):
            for x in DOMAIN:
                assert equations(x,s)==v['h27cn'](*('b','a','b','reference','start','end'),x,s)
            assert predicate(s)==(bits(s)==(True,False,False))
        assert tuple(mask(x) for x in DOMAIN)==(True,True,True)
        assert tuple(assigned(x) for x in DOMAIN)==(True,False,False)
        calls.append(True);return True
    v['rw']=rw;assert run(d,v)==[True];assert calls
    d=fixture(('r6kz',),'q[k r6kz['+ARGS+']].',(*LOWER,'r6kv','r6kw','r6ky','rw'));v=model(d);calls=[]
    v['r6kv']=lambda *a:context(*a)
    def checked(*a):assert context(*a[:-1]);calls.append(('checked',bits(a[-1])));return True
    def mediated(*a):assert context(*a[:-1]);calls.append(('mediated',bits(a[-1])));return True
    v['r6kw']=checked;v['r6ky']=mediated
    def rw_top(variables,equations,mask,assigned,predicate):
        assert variables.items==DOMAIN
        assert tuple(mask(x) for x in DOMAIN)==(True,False,False)
        flag=assigned('a');assert all(assigned(x)==flag for x in DOMAIN)
        for candidate in (state(flag,False,False),state(flag,False,True)):
            for x in DOMAIN:assert equations(x,candidate)==v['h27cn']('b','a','b','reference','start','end',x,candidate)
            before=len(calls);assert predicate(candidate)
            expected=[('checked',bits(candidate))]+([] if flag else [('mediated',bits(candidate))])
            assert calls[before:]==expected,(flag,calls[before:])
        return True
    v['rw']=rw_top;assert run(d,v)==[True]
    assert calls[0]==('checked',(True,False,True))
    d=fixture(('r6k2',),'q[t[k r6k2[k zcommunity[] k zlowerorder[] k zhigherorder[] k zstart[]]][k zpoint[]]].',('r6kz',));v=model(d);rows=0
    v['r6kz']=lambda *a:context(*a)
    for c,l,h,s,e in product(PEOPLE,PEOPLE,PEOPLE,('start','end'),('start','end')):
        w=dict(v)
        for n,x in zip(('community','lowerorder','higherorder','start','point'),(c,l,h,s,e)):w['z'+n]=lambda x=x:x
        assert run(d,w,domain=PEOPLE)==[(c,l,h,s,e)==('b','a','b','start','end')];rows+=1
    return dict(exact_model_mask_assignment_and_predicate=True,exact_observation_on_and_off_content_and_source_bindings=True,all_32_wrapper_bindings=rows)

def reading_record():
    u=next(u for u in read(INVENTORY)['units'] if u['id']=='kant-1784:u0017')
    return dict(status='same_population_mental_trajectory_choice_mediation_partial',source_unit=u['id'],unit_sha256=u['text_sha256'],
      alignment=dict(segments=[dict(unit=u['id'],range=[871,1000],text=u['text'][871:1000],definitions=list(MEANINGS),status='explicit_interpretive_annotation')]),
      interpretation=LIMITS,whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,new_verified_characters=0,
      unresolved=['Wenn/soの全体量化と前件・後件の時点・人口','政府原則・自己利益・機械以上の人間・尊厳・著者注・全文帰属'],
      source_sha256={p:digest((ROOT/p).read_bytes()) for p in (LIBRARY,BASIS,DOC,SOURCE,INVENTORY,*PRIORS,'data/civic-feedback-reading-v1.json','data/self-directed-choice-reading-v1.json')})

@lru_cache(None)
def structure_checks():
    c=catalog();assert not c.document['statements']
    for prior in (parent(),choice()):
        for n,e in prior.entries.items():
            if n in c.entries:assert c.entries[n]['declaration']==e['declaration'] and c.entries[n]['meaning_ja']==e['meaning_ja'],n
    for p in (*PRIORS,SOURCE):validate_hashes(ROOT,read(p)['source_sha256'])
    validate_hashes(ROOT,read(BASIS)['import_source_sha256']);assert read(READING)==reading_record()
    for p,b in build().items():assert(ROOT/p).read_text(encoding='utf-8')==b,p
    for notation in ('compact','full'):
        t=format_graph(c.document,notation);assert parse(t)==parse(transcribe(t,alphabet='v2'))==c.document
    ranks={};text=format_graph(c.document,'compact')
    for n in MEANINGS:
        for rank,label in enumerate(('','b','c','d','e')):
            try:parse(text+'q[e[r '+label+'[p '+n+']][r '+label+'[p '+n+']]].')
            except ValueError as e:assert 'Quoted evaluation' in str(e),str(e)
            else:ranks[n]=rank;break
    assert ranks=={n:1 if n in ('r6kw','r6ky','r6kz','r6k2') else 0 for n in MEANINGS},ranks
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),minimum_quote_ranks=ranks,
      imported_bodies_and_meanings_unchanged=True,roundtrips=True,new_verified_characters=0)

def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))
def build_report():
    results={}
    for n,f in (('contrast',contrast_checks),('scope_content',scope_content_checks),('mediation',mediation_checks),('bindings',intervention_binding_checks),('structure',structure_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(catalog().source_sha256)|{LIBRARY,BASIS,DOC,READING,SOURCE,INVENTORY,INDEX,*PRIORS,
      'data/civic-feedback-reading-v1.json','data/self-directed-choice-reading-v1.json',
      'scripts/compose_civic_choice_mediation.py','scripts/check_civic_choice_mediation.py','tests/test_civic_choice_mediation.py',
      'scripts/compose_civic_feedback.py','scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py',
      'scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/check_scoped_counts.py'}
    return dict(status='same_population_mental_trajectory_choice_mediation_checked_partial',document=LIBRARY,**results,alignment=read(READING)['alignment'],
      whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
      source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
