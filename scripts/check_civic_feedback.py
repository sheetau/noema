"""Check collective premise matching, full clocks and changing causal contrasts."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
from fractions import Fraction
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import Content,FunctionValue,SequenceValue
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_civic_feedback import ROOT,LIBRARY,BASIS,STATE,MEANINGS,PRIMITIVES,LIMITS,parent,germ,main_catalog,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown
from scripts.check_scoped_counts import arithmetic
from scripts.check_civic_disposition_profile import gradual,distance

DOC='docs/civic-feedback-v1.md';READING='data/civic-feedback-reading-v1.json'
INVENTORY='artifacts/written-units-v1/kant-1784.json';SOURCE='data/tenth-paragraph-source-reading-v1.json';INDEX='data/semantic-review-index-v206.json'
PRIORS=('reports/civic-disposition-profile-v1.json','reports/germ-figurative-connection-v1.json','reports/germ-regime-connection-v1.json')
DOMAIN=('a','b');ON=('start','middle','end');OFF=('offstart','offmiddle','offend');SCENES=(*ON,*OFF,'reference','other')
PAIRS=tuple(product(DOMAIN,repeat=2));CONSTANTS=dict(community='b',lowerorder='a',higherorder='b',reference='reference',start='start',end='end',point='end')
CONTEXT=tuple(CONSTANTS)[:-1];ARGS=' '.join('k z'+n+'[]' for n in CONTEXT);SCOPE=' '.join('k z'+n+'[]' for n in CONTEXT[:4])
LOWER=('r6jd','r6jx','r6jy','r6j3','r6j5')

def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def seq(xs):return SequenceValue(tuple(xs),'"individual"')
def state(a=True,b=False):return FunctionValue(('individual',),'truth',lambda x:a if x=='a' else b)
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

def model(d,on=(0,1,3),off=(0,0,0),bound=1):
    v={r['name']:unknown for r in d['declarations'] if r['kind']=='primitive'};v.update(arithmetic())
    v.update({'z'+n:lambda x=x:x for n,x in CONSTANTS.items()});v['zstate']=lambda:state()
    good=lambda c,r:(c,r)==('b','reference')
    selected=lambda c,l,h,r:(c,l,h,r)==('b','a','b','reference')
    context=lambda *a:tuple(a)==('b','a','b','reference','start','end')
    def clock(s,e):return ON if(s,e)==('start','end') else OFF if(s,e)==('offstart','offend') else ()
    def profile(c,r,p,f,t):
        values=on if t in ON else off if t in OFF else None
        times=ON if t in ON else OFF
        return good(c,r) and (p,f) in PAIRS and values is not None and bool(values[times.index(t)]&(1<<PAIRS.index((p,f))))
    def mapped(*a):
        *ctx,s,t=a
        if not context(*ctx):return 'other'
        return (ON if s('a') else OFF)[ON.index(t)] if t in ON else t
    v.update(aa=lambda p:p in DOMAIN,h237c=lambda p,c,r:good(c,r) and p in DOMAIN,
      h26zj=lambda:'reference',h26zi=selected,h27b5=lambda c,r:seq(DOMAIN if good(c,r) else ()),
      h27b6=lambda c,r,p:seq(DOMAIN if good(c,r) else ()),h27b7=lambda c,r,p,f:good(c,r) and(p,f)in PAIRS,
      h27cg=lambda c,r,p,f:Fraction(1),h27cj=lambda c,r:Fraction(bound),
      h27ch=lambda c,r,s,e,t:good(c,r) and t in clock(s,e),
      h27ci=lambda c,r,s,e,l,h:good(c,r) and l in clock(s,e) and h in clock(s,e) and clock(s,e).index(l)<clock(s,e).index(h),
      h27ck=lambda *a:seq(('a',)) if selected(*a) else seq(()),h27cl=lambda c,l,h,r,p:selected(c,l,h,r) and p=='a',
      h27cm=lambda *a:seq(('a',)),h27cn=lambda *a:a[-2]=='a',h27co=lambda *a:'a',h27cp=lambda *a:state(),h27cq=mapped,
      r6jd=lambda c,l,h,p:Content(SCENES,tuple((c,l,h)==('b','a','b') and p in DOMAIN and t=='start' for t in SCENES)),
      r6jx=lambda c,r,p,f,t:good(c,r) and(p,f)in PAIRS and t in (*ON,*OFF),r6jy=profile,
      r6j3=lambda c,r,s,e:good(c,r) and bool(clock(s,e)),
      r6j5=lambda c,r,s,e:good(c,r) and bool(clock(s,e)) and gradual(on if s=='start' else off,(1,1,1,1),bound))
    return v

def run(d,v,scenes=SCENES):return evaluate(d,v,DOMAIN,scenes,True)
def rejects(d,v):
    try:run(d,v)
    except ValueError as e:assert 'Unknown' in str(e),str(e)
    else:raise AssertionError('Unknown accepted')

@lru_cache(None)
def generalized_profile_checks():
    q='r zprofile[a a d] c.r zassessed[a a d] c.q[k r6ka[k zcommunity[] k zreference[] k zstart[] k zend[] p zprofile p zassessed]].'
    d=fixture(('r6ka',),q);rows=0
    for values in product(range(4),repeat=3):
        v=model(d,on=values);v['zprofile']=lambda p,f,t: t in ON and bool(values[ON.index(t)]&(1<<PAIRS.index((p,f))))
        v['zassessed']=lambda p,f,t:t in ON
        assert run(d,v,(*ON,'reference','other'))==[gradual(values,(1,1,1,1),1)],values;rows+=1
    q='r zprofile[a a d] c.r zexpected[] b.q[e[k r6j7[k zcommunity[] k zreference[] p zprofile k zstart[] k zend[]]][k zexpected[]]].'
    d=fixture(('r6j7',),q);weights=(Fraction(1,2),1,2,3)
    for left,right in product(range(16),repeat=2):
        v=model(d);v['h27cg']=lambda c,r,p,f:Fraction(weights[PAIRS.index((p,f))])
        v['zprofile']=lambda p,f,t:bool((left if t=='start' else right)&(1<<PAIRS.index((p,f))))
        v['zexpected']=lambda:distance(left,right,weights);assert run(d,v)==[True]
    return dict(native_64_trajectories_match_independent_oracle=rows,native_256_weighted_distances_match=True,no_existing_definition_changed=True)

@lru_cache(None)
def scope_clock_checks():
    q='q[k r6kb['+SCOPE+']].q[k r6kc['+ARGS+' k zstate[]]].'
    d=fixture(('r6kb','r6kc'),q);v=model(d);assert run(d,v)==[True,True]
    for flag in (False,True):w=dict(v);w['zstate']=lambda flag=flag:state(flag);assert run(d,w)==[True,True]
    # The false aggregate need not mean every contributor failed to develop.
    w=dict(v);w['h27ck']=lambda *a:seq(DOMAIN);w['h27cl']=lambda *a:True;w['zstate']=lambda:state(False)
    w['r6jd']=lambda c,l,h,p:Content(SCENES,tuple(t=='start' or(p=='b' and t=='offstart') for t in SCENES))
    assert run(d,w)==[True,True]
    cases={}
    for name in ('empty_contributors','omitted_contributor','duplicate_contributor','outsider','wrong_reference','wrong_comparison','missing_mapped_middle','extra_mapped_point','reversed_order','unassessed_counterfactual','false_factor_true_content'):
        w=dict(v);w['zstate']=lambda:state(False)
        if name=='empty_contributors':w['h27ck']=lambda *a:seq(());w['h27cl']=lambda *a:False
        if name=='omitted_contributor':w['h27cl']=lambda *a:True
        if name=='duplicate_contributor':w['h27ck']=lambda *a:seq(('a','a'))
        if name=='outsider':w['h27ck']=lambda *a:seq(('b',));w['h27cl']=lambda *a:a[-1]=='b';w['h237c']=lambda p,c,r:p=='a';w['h27b5']=lambda *a:seq(('a',))
        if name=='wrong_reference':w['zreference']=lambda:'other'
        if name=='wrong_comparison':w['zhigherorder']=lambda:'a'
        if name=='missing_mapped_middle':w['h27cq']=lambda *a:'offend' if a[-1]=='middle' and not a[-2]('a') else v['h27cq'](*a)
        if name=='extra_mapped_point':w['h27ch']=lambda *a:v['h27ch'](*a) or(a[2],a[3],a[4])==('offstart','offend','other')
        if name=='reversed_order':w['h27ci']=lambda c,r,s,e,l,h:v['h27ci'](c,r,s,e,h,l) if s=='offstart' else v['h27ci'](c,r,s,e,l,h)
        if name=='unassessed_counterfactual':w['r6j3']=lambda *a:a[-2]=='start'
        if name=='false_factor_true_content':w['r6jd']=lambda *a:Content(SCENES,tuple(t in ('start','offstart') for t in SCENES))
        actual=run(d,w);assert not all(actual),(name,actual);cases[name]=actual
    for n in ('h27ck','h27cl','h27cq','h27ch','h27ci','r6jd','r6j3'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    return dict(aggregate_false_allows_some_developed=True,contrasts=cases,unknown_rejected=True,
      boundary='r6jd and r6j3 are unchanged content/assessment boundaries. Their native bodies and dependencies are pinned by prior reports; all new scope, premise equality, onto/injective mapping and order conditions execute natively.')

@lru_cache(None)
def contrast_checks():
    d=fixture(('r6kd',),'q[k r6kd['+ARGS+' k zstate[]]].');cases={}
    for label,on,off,bound,expected in (
      ('growing_difference',(0,1,3),(0,0,0),1,True),
      ('common_change_only',(0,1,3),(0,1,3),1,False),
      ('constant_existing_difference',(0,1,3),(4,5,7),1,False),
      ('nonzero_initial_difference',(0,1,3),(4,4,4),1,True),
      ('both_sides_change',(0,1,3),(4,12,12),2,True),
      ('sudden_difference',(0,1,3),(0,1,0),1,False)):
        v=model(d,on,off,bound);v['zstate']=lambda:state(False);actual=run(d,v)
        assert actual==[expected],(label,actual);cases[label]=expected
    v=model(d);v['zstate']=lambda:state(False)
    for name in ('missing_on_assessment','missing_off_assessment'):
        w=dict(v)
        t='middle' if name=='missing_on_assessment' else 'offmiddle'
        w['r6jx']=lambda c,r,p,f,a,t=t:v['r6jx'](c,r,p,f,a) and not (a==t and p=='b' and f=='b')
        assert run(d,w)==[False],name;cases[name]=False
    calls=[];old=v['r6jy']
    def response(*a):calls.append(a);return old(*a)
    v['r6jy']=response;assert run(d,v)==[True]
    for p,f in PAIRS:
        for t in (*ON,*OFF):assert ('b','reference',p,f,t) in calls,(p,f,t)
    for n in ('r6jx','r6jy','h27cq','h27cg'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    # Check the values of each supplied component, not merely the aggregate
    # distance or the set of calls (both can hide a person/feature permutation).
    b=fixture(('r6kd',),'q[k r6kd['+ARGS+' k zstate[]]].',(*LOWER,'r6ka'))
    w=model(b);w['zstate']=lambda:state(False)
    w['r6jx']=lambda c,r,p,f,t:not (p=='a' and f=='b' and t=='offmiddle')
    def check_components(c,r,s,e,profile,assessed):
        assert (c,r,s,e)==('b','reference','start','end')
        for p,f,t in product(DOMAIN,DOMAIN,ON):
            off=OFF[ON.index(t)]
            assert profile(p,f,t)==(w['r6jy'](c,r,p,f,t)!=w['r6jy'](c,r,p,f,off)),(p,f,t)
            assert assessed(p,f,t)==(w['r6jx'](c,r,p,f,t) and w['r6jx'](c,r,p,f,off)),(p,f,t)
        return True
    w['r6ka']=check_components;assert run(b,w)==[True]
    return dict(contrasts=cases,all_people_features_and_both_world_times_forwarded=True,exact_profile_and_assessment_components=True,unknown_rejected=True,
      boundary='Previously verified r6jx/r6jy bodies are boundaries; new difference profiles, weighted metric, complete scopes and gradual path constraints execute natively. A separate r6ka boundary checks every supplied profile/assessment component to detect person/feature permutations.')

@lru_cache(None)
def causal_checks():
    d=fixture(('r6ke',),'q[k r6ke['+ARGS+']].');v=model(d);assert run(d,v)==[True];cases={}
    for name in ('observed_factor_false','observed_outside_variable','factor_outside_variables','duplicate_variables','unselected_comparison','observed_not_solution','shifted_observation','no_actual_gradual_change','common_change_only','constant_difference','missing_off_assessment'):
        w=dict(v)
        if name=='observed_factor_false':w['h27cp']=lambda *a:state(False)
        if name=='observed_outside_variable':w['h27cp']=lambda *a:state(True,True)
        if name=='factor_outside_variables':w['h27co']=lambda *a:'b'
        if name=='duplicate_variables':w['h27cm']=lambda *a:seq(('a','a'))
        if name=='unselected_comparison':w['h26zi']=lambda *a:False
        if name=='observed_not_solution':w['h27cn']=lambda *a:False
        if name=='shifted_observation':w['h27cq']=lambda *a:OFF[ON.index(a[-1])] if a[-1]in ON else a[-1]
        if name=='no_actual_gradual_change':w['r6j5']=lambda *a:False
        if name=='common_change_only':w=model(d,off=(0,1,3))
        if name=='constant_difference':w=model(d,off=(4,5,7))
        if name=='missing_off_assessment':w['r6j3']=lambda c,r,s,e:s=='start'
        actual=run(d,w);assert actual==[False],(name,actual);cases[name]=False
    for n in ('h27cn','h27cm','h27cp','h27co','h27cq','r6jd','r6jy'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    # Two-variable cyclic/non-deterministic equations: independent enumeration
    # checks both existence and universality, with only the content adapters bounded.
    b=fixture(('r6ke',),'q[k r6ke['+ARGS+']].',(*LOWER,'r6kc','r6kd'))
    rows=[]
    for table,ob in product(range(16),(False,True)):
        w=model(b);w['h27cm']=lambda *a:seq(DOMAIN);w['h27cp']=lambda *a,ob=ob:state(True,ob)
        w['h27cn']=lambda *a,table=table:True if a[-2]=='a' else bool(table&(1<<(2*int(a[-1]('a'))+int(a[-1]('b')))))
        w['r6kc']=lambda *a:True;w['r6kd']=lambda *a:not a[-1]('b')
        solutions={flag:[x for x in (False,True) if x==bool(table&(1<<(2*int(flag)+int(x))))] for flag in (False,True)}
        expected=bool(ob in solutions[True] and solutions[False] and all(not x for x in solutions[False]))
        assert run(b,w)==[expected],(table,ob,solutions);rows.append(dict(table=table,observed=ob,result=expected))
    return dict(native_model_and_full_new_adapters=True,contrasts=cases,all_32_equation_observation_rows=rows,unknown_rejected=True,
      boundary='All new adapters execute with lower r6jd/r6jx/r6jy/r6j3/r6j5 content boundaries already checked in pinned priors. Only the extra equation oracle also replaces r6kc/r6kd; native ru/rs/rv/rw always execute.')

@lru_cache(None)
def wrapper_checks():
    q='q[t[k r6kf[k zcommunity[] k zlowerorder[] k zhigherorder[] k zstart[]]][k zpoint[]]].'
    d=fixture(('r6kf',),q,('r6ke',));v=model(d);calls=[]
    def body(*a):calls.append(a);return a==('b','a','b','reference','start','end')
    v['r6ke']=body;rows=0
    for c,l,h,s,e in product(DOMAIN,DOMAIN,DOMAIN,('start','end'),('start','end')):
        w=dict(v)
        for n,x in zip(('community','lowerorder','higherorder','start','point'),(c,l,h,s,e)):w['z'+n]=lambda x=x:x
        calls.clear();assert run(d,w)==[(c,l,h,s,e)==('b','a','b','start','end')]
        assert (c,l,h,'reference',s,e) in calls;rows+=1
    return dict(all_32_bindings=rows,reference_from_prior_fixed_reference=True,boundary='Only r6ke is replaced; its native composition is tested separately.')

def reading_record():
    u=next(u for u in read(INVENTORY)['units'] if u['id']=='kant-1784:u0017')
    return dict(status='same_community_causal_feedback_partial',source_unit=u['id'],unit_sha256=u['text_sha256'],
      alignment=dict(segments=[dict(unit=u['id'],range=[871,931],text=u['text'][871:931],definitions=list(MEANINGS),status='explicit_interpretive_annotation')]),
      interpretation=LIMITS,whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,new_verified_characters=0,
      unresolved=['Wenn/soの全体量化と前件・後件の時点・人口','行為能力・政府原則・自己利益・機械以上の人間・尊厳・著者注'],
      source_sha256={p:digest((ROOT/p).read_bytes()) for p in (LIBRARY,BASIS,DOC,SOURCE,INVENTORY,*PRIORS,'data/civic-disposition-profile-reading-v1.json','data/germ-figurative-connection-reading-v1.json')})

@lru_cache(None)
def structure_checks():
    c=catalog();assert not c.document['statements']
    for prior in (parent(),germ(),main_catalog()):
        for n,e in prior.entries.items():
            if n in c.entries:assert c.entries[n]['declaration']==e['declaration'] and c.entries[n]['meaning_ja']==e['meaning_ja'],n
    for p in (*PRIORS,SOURCE):validate_hashes(ROOT,read(p)['source_sha256'])
    validate_hashes(ROOT,read(BASIS)['import_source_sha256']);assert read(READING)==reading_record()
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b,p
    for notation in ('compact','full'):
        t=format_graph(c.document,notation);assert parse(t)==parse(transcribe(t,alphabet='v2'))==c.document
    ranks={};text=format_graph(c.document,'compact')
    for n in MEANINGS:
        for rank,label in enumerate(('','b','c','d','e')):
            try:parse(text+'q[e[r '+label+'[p '+n+']][r '+label+'[p '+n+']]].')
            except ValueError as e:assert 'Quoted evaluation' in str(e),str(e)
            else:ranks[n]=rank;break
    assert ranks=={n:1 if n in ('r6kc','r6ke','r6kf') else 0 for n in MEANINGS},ranks
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),minimum_quote_ranks=ranks,
      imported_bodies_and_meanings_unchanged=True,roundtrips=True,new_verified_characters=0)

def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))
def build_report():
    results={}
    for n,f in (('profile',generalized_profile_checks),('scope_clock',scope_clock_checks),('contrast',contrast_checks),('causal',causal_checks),('wrapper',wrapper_checks),('structure',structure_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(catalog().source_sha256)|{LIBRARY,BASIS,DOC,READING,SOURCE,INVENTORY,INDEX,*PRIORS,
      'data/civic-disposition-profile-reading-v1.json','data/germ-figurative-connection-reading-v1.json',
      'scripts/compose_civic_feedback.py','scripts/check_civic_feedback.py','tests/test_civic_feedback.py',
      'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/check_scoped_counts.py','scripts/check_civic_disposition_profile.py'}
    return dict(status='same_community_causal_feedback_checked_partial',document=LIBRARY,**results,alignment=read(READING)['alignment'],
      whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
      source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
