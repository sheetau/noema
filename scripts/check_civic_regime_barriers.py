"""Check regime matching in every causal solution and assessed task barriers."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import Content,FunctionValue,SequenceValue
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_civic_regime_barriers import ROOT,LIBRARY,BASIS,OLD,OLD_BASIS,STATE,CONTEXT,MEANINGS,PRIMITIVES,LIMITS,parent,main_catalog,legacy,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown

DOC='docs/civic-regime-barriers-v1.md';READING='data/civic-regime-barriers-reading-v1.json'
INVENTORY='artifacts/written-units-v1/kant-1784.json';SOURCE='data/tenth-paragraph-source-reading-v1.json';INDEX='data/semantic-review-index-v205.json'
PRIORS=('reports/civic-intellectual-options-v1.json','reports/civic-advantage-appearance-v1.json','reports/assessed-barriers-v1.json','reports/republic-polity-v1.json')
DOMAIN=('a','b');ROWS=tuple(product((False,True),repeat=2));SCENES=('reference','anchor','w00','w01','w10','w11','success','failure','other')
CONSTANTS=dict(community='b',lowerorder='a',higherorder='b',reference='reference',anchor='anchor',person='a',task='b',observer='a')
CTX=tuple(CONSTANTS[n] for n in CONTEXT)
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def z(n):return 'k z'+n+'[]'
def args(ns):return ' '.join(z(n) for n in ns)
def state(row):return FunctionValue(('individual',),'truth',lambda n:row[DOMAIN.index(n)])
def bits(s):return tuple(s(n) for n in DOMAIN)
def world(s):return 'w'+''.join(str(int(x)) for x in bits(s))
def content(f):return Content(SCENES,tuple(f(t) for t in SCENES))
def seq(xs):return SequenceValue(tuple(xs),'"individual"')
def normalized(xs):return tuple(bits(x) if isinstance(x,FunctionValue) else x for x in xs)
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(roots,query,boundaries=('r6hf','r6fr')):
    d=deepcopy(catalog().document);d['statements']=[]
    for row in d['declarations']:
        if row['name'] in boundaries:row.update(kind='primitive',parameters=[p['sort'] for p in row['parameters']]);row.pop('body')
    d['declarations']=closure(d,roots)
    extra=''.join('r z'+n+'[] '+('a' if v in DOMAIN else 'd')+'.' for n,v in CONSTANTS.items())+'r zstate[] '+STATE+'.'
    return parse(format_graph(d,'compact')+extra+query)
def model(d,table=3):
    v={r['name']:unknown for r in d['declarations'] if r['kind']=='primitive'}
    v.update({'z'+n:lambda v=v:v for n,v in CONSTANTS.items()});v['zstate']=lambda:state((False,False))
    v.update(aa=lambda p:p=='a',h237c=lambda p,c,r:(p,c,r)==('a','b','reference'),
      h26yo=lambda c,p,a,r:(c,p,r)==('b','a','reference') and a in DOMAIN,
      h26ys=lambda c,p,task,r:(c,p,task,r)==('b','a','b','reference'),h26yt=lambda task,m,r:(task,m,r)==('b','b','reference'),
      h26yy=lambda c,r,a:'w01',h26yz=lambda c,r,a:'w10')
    def polity(c,o,r,t):return (c,r)==('b','reference') and t.startswith('w') and o==('b' if t[1]=='1' else 'a')
    v['r6fr']=polity
    v['r6hf']=lambda c,o,p,a,r,t:polity(c,o,r,t) and p=='a' and(a=='a' or a=='b' and t[1]=='1')
    v.update(h26y3=lambda *a:seq(DOMAIN if a==CTX else ()),h26y5=lambda *a:'a',
      h26y4=lambda *a:True if a[-2]=='a' else bool(table & (1<<(2*int(a[-1]('a'))+int(a[-1]('b'))))),
      h26y6=lambda *a:world(a[-1]),h26y7=lambda *a:state((True,False)),
      h26za=lambda *a:a==(*CTX,'a','b'))
    v.update(ab=lambda f,p,t:(f,p,t)==('b','a','success'),ac=lambda p,f,j,t:(p,f,j,t)==('a','b','b','success'),
      fa=lambda p,j,t:(p,j,t)==('a','b','success'),fb=lambda j,m,t:(j,m,t)==('b','b','success'),
      fc=lambda j,r,t:(j,r,t)==('b','a','success'),fd=lambda r,j,t:(r,j,t)==('a','b','success'),ad=lambda *a:False,
      h26yu=lambda p,task,j,r,t:(p,task,j,r,t)==('a','b','b','reference','success'))
    v['h26yv']=lambda c,task,r,p,m,t:(c,task,r,p,m)==('b','b','reference','a','b') and t.startswith('w')
    v['h26yw']=lambda c,task,r,p,m,t,o:(c,task,r,p,m)==('b','b','reference','a','b') and t.startswith('w') and o==('success' if t[2]=='1' else 'failure')
    v['h26yx']=v['h26yw'];return v
def run(d,v,memo=True):return evaluate(d,v,DOMAIN,SCENES,memo)
def rejects(d,v):
    try:run(d,v)
    except ValueError as e:assert 'Unknown' in str(e),str(e)
    else:raise AssertionError('Unknown accepted')

@lru_cache(None)
def regime_matching_checks():
    q='q[k r6ht['+args(CONTEXT)+' k zstate[]]].';d=fixture(('r6ht',),q);base=model(d)
    for row in ROWS:
        v=dict(base);v['zstate']=lambda row=row:state(row);assert run(d,v)==[True],row
    cases={}
    for name in ('extra_low_permission','missing_low_permission','missing_high_permission','wrong_order','not_operating','wrong_mapping','wrong_person_permission'):
        v=dict(base);old=v['r6hf']
        if name=='extra_low_permission':v['r6hf']=lambda c,o,p,a,r,t:old(c,o,p,a,r,t) or (p,a,t)==('a','b','w00')
        if name=='missing_low_permission':v['r6hf']=lambda c,o,p,a,r,t:old(c,o,p,a,r,t) and not(a=='a' and t=='w00')
        if name=='missing_high_permission':
            v['zstate']=lambda:state((True,True));v['r6hf']=lambda c,o,p,a,r,t:old(c,o,p,a,r,t) and not(a=='b' and t=='w11')
        if name=='wrong_order':v['zlowerorder']=lambda:'b'
        if name=='not_operating':v['r6fr']=lambda *a:False
        if name=='wrong_mapping':v['h26y6']=lambda *a:'w10'
        if name=='wrong_person_permission':v['r6hf']=lambda c,o,p,a,r,t:old(c,o,p,a,r,t) and not(p=='a' and t=='w00')
        assert run(d,v)==[False],name;cases[name]=False
    # The all-solutions requirement reaches non-observed w11, not just w10.
    d=fixture(('r6hu',),'q[k r6hu['+args(CONTEXT)+']].');v=model(d,10);assert run(d,v)==[True]
    old=v['r6hf'];v['r6hf']=lambda c,o,p,a,r,t:old(c,o,p,a,r,t) and not(a=='b' and t=='w11');assert run(d,v)==[False]
    for n in ('h26y3','h26y4','h26y5','h26y6','r6hf','r6fr'):
        v=model(d);v[n]=unknown;rejects(d,v)
    return dict(all_four_assignments_matched=True,cases=cases,matching_is_bidirectional=True,nonobserved_solution_mismatch_rejected=True,
      native_intervention_quantifiers_and_strict_civic_inclusion=True,unknown_rejected=True,
      boundaries='r6hf and r6fr only: concrete normative-option and public-order values. Their native bodies and source/role/description bindings are pinned in prior reports.')

def independent(table):
    solutions={f:[b for b in (False,True) if b==bool(table&(1<<(2*int(f)+int(b))))] for f in (False,True)}
    return bool(solutions[False]) and True in solutions[False] and bool(solutions[True]) and not any(solutions[True])
@lru_cache(None)
def causal_checks():
    q='q[k r6hv['+args((*CONTEXT,'person','task'))+']].';d=fixture(('r6hv',),q);rows=[]
    for table in range(16):
        v=model(d,table);got=run(d,v);want=independent(table);assert got==[want],(table,got)
        rows.append(dict(table=table,barrier=want))
    v=model(d);assert run(d,v)==[True];cases={}
    for name in ('empty_variables','duplicate_variables','missing_factor','no_solutions','wrong_observation','observed_low','wrong_observed_point','high_attainable','unassessed_high','unassessed_low','no_methods_high','empty_task','outside_task_scope','nonmember'):
        w=dict(v);want=name=='no_methods_high'
        if name=='empty_variables':w['h26y3']=lambda *a:seq(())
        if name=='duplicate_variables':w['h26y3']=lambda *a:seq(('a','b','a'))
        if name=='missing_factor':w['h26y3']=lambda *a:seq(('b',))
        if name=='no_solutions':w['h26y4']=lambda *a:not a[-1](a[-2])
        if name=='wrong_observation':w['h26y7']=lambda *a:state((True,True))
        if name=='observed_low':w['h26y7']=lambda *a:state((False,True))
        if name=='wrong_observed_point':w['h26yz']=lambda *a:'w11'
        if name=='high_attainable':w['h26yx']=w['h26yw']=lambda c,task,r,p,m,t,o:o=='success'
        if name=='unassessed_high':w['h26yx']=lambda *a:a[-2]!='w10' and v['h26yx'](*a)
        if name=='unassessed_low':w['h26yx']=lambda *a:a[-2]!='w01' and v['h26yx'](*a)
        if name=='no_methods_high':w['h26yv']=lambda *a:a[-1]!='w10' and v['h26yv'](*a)
        if name=='empty_task':w['h26yt']=lambda *a:False
        if name=='outside_task_scope':w['h26ys']=lambda *a:False
        if name=='nonmember':w['h237c']=lambda *a:False
        assert run(d,w)==[want],(name,run(d,w));cases[name]=want
    for n in ('h26y7','h26yv','h26yw','h26yx','h26yt','h26yu'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    return dict(boolean_equation_tables=rows,independent_solution_enumeration=True,cases=cases,
      native_rwx_rww_ru_rv_rw_xd_xg_and_r6hh=True,actual_observation_and_same_task_content_checked=True,
      known_no_available_methods_distinct_from_unassessed_method=True,unknown_rejected=True)

@lru_cache(None)
def target_scope_checks():
    q='q[k r6hw['+args(CONTEXT)+']].';d=fixture(('r6hw',),q,('r6hu','r6hv'));base=model(d);rows=[]
    for selected in product((False,True),repeat=2):
        for holds in product((False,True),repeat=2):
            v=dict(base);v['r6hu']=lambda *a:a==CTX
            v['h26za']=lambda *a:a[:-2]==CTX and a[-2]=='a' and selected[DOMAIN.index(a[-1])]
            v['r6hv']=lambda *a:a[:-2]==CTX and a[-2]=='a' and holds[DOMAIN.index(a[-1])]
            want=any(selected) and all(not s or h for s,h in zip(selected,holds));assert run(d,v)==[want]
            rows.append(dict(selected=selected,holds=holds,value=want))
    native=fixture(('r6hw',),q);v=model(native);assert run(native,v)==[True]
    for name in ('empty_targets','extra_target','wrong_task','wrong_person'):
        w=dict(v)
        if name=='empty_targets':w['h26za']=lambda *a:False
        if name=='extra_target':w['h26za']=lambda *a:a[-2]=='a'
        if name=='wrong_task':w['h26za']=lambda *a:a==(*CTX,'a','a')
        if name=='wrong_person':w['h26za']=lambda *a:a==(*CTX,'b','b')
        assert run(native,w)==[False],name
    v['h26za']=unknown;rejects(native,v)
    return dict(nonempty_all_targets_matrix=rows,native_causal_target_integration=True,extra_incomplete_or_outside_target_rejected=True,
      boundary='r6hu/r6hv only in the scope matrix; the native matching and causal bodies execute in the second part.')

@lru_cache(None)
def adapter_checks():
    q='q[k r6hv['+args((*CONTEXT,'person','task'))+']].';d=fixture(('r6hv',),q,('r6hu','rwx'));v=model(d);calls=[]
    watched=('h26y3','h26y4','h26y5','h26y6','h26y7','h26yz','h26yv','h26yw','h26yx')
    for n in watched:
        old=v[n]
        def rec(*a,n=n,old=old):calls.append((n,normalized(a)));return True if n in ('h26yv','h26yw','h26yx') else old(*a)
        v[n]=rec
    v['r6hu']=lambda *a:True
    def sample(person,goal,variables,equations,factor,mapping,available,possible,selected,point,observed):
        equations('b',state((False,False)));mapping(state((False,False)))
        available('b','a','w11');possible('b','a','w11','failure');selected('b','a','w11','failure');return True
    def checked(*a):
        person,goal,variables,equations,factor,mapping,available,possible,selected,point,observed=a
        assert person=='a' and goal==content(lambda t:t=='success') and variables.items==DOMAIN and factor=='a' and point=='w10' and bits(observed)==(True,False)
        return sample(*a)
    v['rwx']=checked;assert run(d,v,False)==[True]
    def expected(c):
        ctx=tuple(c[n] for n in CONTEXT);scope=(c['community'],c['task'],c['reference'])
        return {'h26y3':ctx,'h26y4':(*ctx,'b',(False,False)),'h26y5':ctx,'h26y6':(*ctx,(False,False)),'h26y7':ctx,
          'h26yz':(c['community'],c['reference'],c['anchor']),
          'h26yv':(*scope,'b','a','w11'),'h26yw':(*scope,'b','a','w11','failure'),'h26yx':(*scope,'b','a','w11','failure')}
    assert len(calls)==len(watched) and dict(calls)==expected(CONSTANTS),calls
    for n in (*CONTEXT,'person','task'):
        changed=dict(CONSTANTS);changed[n]='other' if n in ('reference','anchor') else ('b' if changed[n]=='a' else 'a')
        w=dict(v);w['z'+n]=lambda n=n,changed=changed:changed[n];w['rwx']=sample;calls.clear();run(d,w,False)
        assert len(calls)==len(watched) and dict(calls)==expected(changed),(n,calls)
    return dict(all_seven_context_and_target_slots_recorded=True,native_goal_content_bound=True,
      provider_callbacks_keep_fixed_task_and_forward_actor_method_point_outcome=True,
      boundary='r6hu/rwx only for call recording; both native bodies execute in causal and target-scope checks.')

@lru_cache(None)
def content_checks():
    fields=('observer','community','lowerorder','higherorder','reference')
    q='q[t[k r6hx['+args(fields)+']]['+z('anchor')+']].'
    d=fixture(('r6hx',),q,('r6hs','r6hw'));base=model(d)
    for appearance,barrier in product((False,True),repeat=2):
        v=dict(base);v['r6hs']=lambda *a:content(lambda t:appearance and a==('a','b','a','b','reference') and t=='anchor')
        v['r6hw']=lambda *a:barrier and a==CTX;assert run(d,v)==[appearance and barrier]
    for n in (*fields,'anchor'):
        w=dict(v);w['z'+n]=lambda n=n:'other' if n in ('reference','anchor') else ('b' if CONSTANTS[n]=='a' else 'a');assert run(d,w)==[False],n
    for n in ('r6hs','r6hw'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    quoted=fixture(('r6hx',),'q[e[r d[p r6hx]][r d[p r6hx]]].')
    assert run(quoted,{r['name']:unknown for r in quoted['declarations'] if r['kind']=='primitive'})==[True]
    return dict(appearance_and_barrier_both_required=True,same_observer_community_orders_reference_and_point=True,
      quotation_not_executed=True,boundary='r6hs/r6hw only for whole-content wiring; r6hs native appearance is pinned and r6hw executes natively in this report.')

def reading_record():
    u=next(u for u in read(INVENTORY)['units'] if u['id']=='kant-1784:u0017');phrase='und setzt ihr doch unübersteigliche Schranken';a=u['text'].index(phrase)
    return dict(status='same_civic_regimes_causal_barriers_dependency',source_unit=u['id'],unit_sha256=u['text_sha256'],
      alignment=dict(segments=[dict(unit=u['id'],range=[a,a+len(phrase)],text=phrase,definitions=list(MEANINGS),status='explicit_interpretive_annotation')]),
      interpretation=LIMITS,whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,new_verified_characters=0,
      source_sha256={p:digest((ROOT/p).read_bytes()) for p in (LIBRARY,BASIS,DOC,SOURCE,INVENTORY,*PRIORS)})
@lru_cache(None)
def structure_checks():
    c=catalog();assert not c.document['statements']
    for p in (parent(),main_catalog()):
        for n,e in p.entries.items():
            if n in c.entries:assert c.entries[n]['declaration']==e['declaration'] and c.entries[n]['meaning_ja']==e['meaning_ja'],n
    ds,means=legacy()
    for row in ds:
        assert c.entries[row['name']]['declaration']==row
        if row['name'] in means:assert c.entries[row['name']]['meaning_ja']==means[row['name']]
    for p in (*PRIORS,SOURCE):validate_hashes(ROOT,read(p)['source_sha256'])
    validate_hashes(ROOT,read(BASIS)['import_source_sha256']);assert read(READING)==reading_record()
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b
    for notation in ('compact','full'):
        t=format_graph(c.document,notation);assert parse(t)==parse(transcribe(t,alphabet='v2'))==c.document
    ranks={};t=format_graph(c.document,'compact')
    for n in MEANINGS:
        for rank,label in enumerate(('','b','c','d')):
            try:parse(t+'q[e[r '+label+'[p '+n+']][r '+label+'[p '+n+']]].')
            except ValueError as e:assert 'Quoted evaluation' in str(e),str(e)
            else:ranks[n]=rank;break
    assert ranks=={n:3 if n=='r6hx' else 0 for n in MEANINGS},ranks
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),minimum_quote_ranks=ranks,
      inherited_bodies_and_meanings_unchanged=True,roundtrips=True,new_verified_characters=0)
def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))
def build_report():
    results={}
    for n,f in (('regime_matching',regime_matching_checks),('causal',causal_checks),('target_scope',target_scope_checks),('adapters',adapter_checks),('content',content_checks),('structure',structure_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(catalog().source_sha256)|{LIBRARY,BASIS,DOC,READING,SOURCE,INVENTORY,INDEX,OLD,OLD_BASIS,*PRIORS,
      'scripts/compose_civic_regime_barriers.py','scripts/check_civic_regime_barriers.py','tests/test_civic_regime_barriers.py',
      'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py'}
    return dict(status='same_civic_regimes_causal_assessed_barriers_checked_partial',document=LIBRARY,**results,alignment=read(READING)['alignment'],
      whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
      source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
