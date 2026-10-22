"""Check named faculties, whole task ranges and stable-regime development."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import Content,FunctionValue,SequenceValue
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_faculty_development_room import ROOT,LIBRARY,BASIS,STATE,CONTEXT,SCOPE_NAMES,MEANINGS,PRIMITIVES,LIMITS,parent,main_catalog,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown

DOC='docs/faculty-development-room-v1.md';READING='data/faculty-development-room-reading-v1.json'
INVENTORY='artifacts/written-units-v1/kant-1784.json';SOURCE='data/tenth-paragraph-source-reading-v1.json';INDEX='data/semantic-review-index-v205.json'
PRIORS=('reports/civic-regime-barriers-v1.json','reports/civic-intellectual-options-v1.json','reports/faculty-opportunities-v1.json')
DOMAIN=('a','b');SCENES=('reference','anchor','w00','w01','w10','w11','middle','end','success','failure','other')
CONSTANTS=dict(community='b',order='a',lowerorder='a',higherorder='b',reference='reference',anchor='anchor',person='a',faculty='b',task='a',observer='a',start='w01',end='end',point='end')
CTX=tuple(CONSTANTS[n] for n in CONTEXT)
FAC=('community','person','faculty','task','reference','point')

def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def z(n):return 'k z'+n+'[]'
def args(ns):return ' '.join(z(n) for n in ns)
def content(f):return Content(SCENES,tuple(f(t) for t in SCENES))
def state(row):return FunctionValue(('individual',),'truth',lambda n:row[DOMAIN.index(n)])
def bits(s):return tuple(s(n) for n in DOMAIN)
def world(s):return 'w'+''.join(str(int(x)) for x in bits(s))
def seq(xs):return SequenceValue(tuple(xs),'"individual"')
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(roots,query,boundaries=('r6hf','r6fr')):
    d=deepcopy(catalog().document);d['statements']=[]
    for row in d['declarations']:
        if row['name'] in boundaries:row.update(kind='primitive',parameters=[p['sort'] for p in row['parameters']]);row.pop('body')
    d['declarations']=closure(d,roots)
    extra=''.join('r z'+n+'[] '+('a' if v in DOMAIN else 'd')+'.' for n,v in CONSTANTS.items())
    return parse(format_graph(d,'compact')+extra+query)

def model(d):
    v={r['name']:unknown for r in d['declarations'] if r['kind']=='primitive'}
    v.update({'z'+n:lambda v=v:v for n,v in CONSTANTS.items()})
    v.update(aa=lambda p:p=='a',h237c=lambda p,c,r:(p,c,r)==('a','b','reference'),
      h26yo=lambda c,p,a,r:(c,p,r)==('b','a','reference') and a in DOMAIN,
      h26ys=lambda c,p,t,r:(c,p,r)==('b','a','reference') and t in DOMAIN,
      h26yt=lambda t,m,r:t==m and r=='reference',
      h26zb=lambda c,p,f,r:(c,p,f,r)==('b','a','b','reference'),
      h26zc=lambda p,f,t,r:(p,f,r)==('a','b','reference') and t in DOMAIN,
      h26yu=lambda p,t,j,r,s:(p,r,s)==('a','reference','success') and t==j,
      ab=lambda f,p,t:(f,p)==('b','a'),ac=lambda p,f,j,t:(p,f,t)==('a','b','success'),
      fa=lambda p,j,t:(p,t)==('a','success'),fb=lambda j,m,t:j==m and t=='success',
      fc=lambda j,r,t:(r,t)==('a','success'),fd=lambda r,j,t:(r,t)==('a','success'),ad=lambda *a:False)
    v['h26yv']=lambda c,t,r,p,m,s:(c,r,p,m)==('b','reference','a','b') and t in DOMAIN
    def outcome(c,t,r,p,m,s,o):
        ok=(c,r,p,m)==('b','reference','a','b') and t in DOMAIN
        can=s=='end' or t=='b' and s in ('w00','w01','middle')
        return ok and o==('success' if can else 'failure')
    v['h26yw']=v['h26yx']=outcome
    def polity(c,o,r,t):
        return (c,r)==('b','reference') and (o=='a' and t in ('w00','w01','middle','end') or o=='b' and t in ('w10','w11'))
    v['r6fr']=polity;v['r6hf']=lambda c,o,p,a,r,t:polity(c,o,r,t) and p=='a' and (a=='a' or o=='b')
    def history(c,o,r,start,end,point):
        return (c,o,r)==('b','a','reference') and start in ('w00','w01') and end=='end' and point in (start,'middle',end)
    v['h26zd']=history
    v['h26ze']=lambda c,o,r,s,e,l,h:history(c,o,r,s,e,l) and history(c,o,r,s,e,h) and (s,'middle',e).index(l)<(s,'middle',e).index(h)
    v['h26zf']=lambda c,o,p,f,r,actor,m,s:(c,o,p,f,r,actor,m)==('b','a','a','b','reference','a','b') and s in ('w00','w01')
    v['h26zg']=v['h26zh']=lambda *a:v['h26zf'](*a[:-1]) and a[-1]=='end'
    v.update(h26yy=lambda *a:'w01',h26yz=lambda *a:'w10',h26y3=lambda *a:seq(DOMAIN),h26y5=lambda *a:'a',
      h26y4=lambda *a:True if a[-2]=='a' else not a[-1]('a'),h26y6=lambda *a:world(a[-1]),
      h26y7=lambda *a:state((True,False)),h26za=lambda *a:a==(*CTX,'a','b'))
    return v
def run(d,v,memo=True):return evaluate(d,v,DOMAIN,SCENES,memo)
def rejects(d,v):
    try:run(d,v)
    except ValueError as e:assert 'Unknown' in str(e),str(e)
    else:raise AssertionError('Unknown accepted')

@lru_cache(None)
def faculty_goal_checks():
    q='q[t[k r6hy['+args(('person','faculty','task','reference'))+']]['+z('point')+']].'
    d=fixture(('r6hy',),q);v=model(d);v['zpoint']=lambda:'success';assert run(d,v)==[True];cases={}
    for name in ('other_faculty','other_owner','unused_faculty','unsupported','guided','wrong_task','empty_matters','one_missing_matter'):
        w=dict(v)
        if name=='other_faculty':w['zfaculty']=lambda:'a'
        if name=='other_owner':w['ab']=lambda f,p,t:(f,p)==('b','b')
        if name=='unused_faculty':w['ac']=lambda p,f,j,t:f=='a'
        if name=='unsupported':w['fd']=lambda *a:False
        if name=='guided':w['ad']=lambda l,p,j,t:l!=p
        if name=='wrong_task':w['h26yu']=lambda p,t,j,r,s:t=='b'
        if name=='empty_matters':w['h26yt']=lambda *a:False
        if name=='one_missing_matter':w['h26yt']=lambda *a:True
        assert run(d,w)==[False],name;cases[name]=False
    # Two distinct reasoned judgments can cover the two matters.
    w=dict(v);w['h26yt']=lambda *a:True;w['h26yu']=lambda p,t,j,r,s:s=='success';assert run(d,w)==[True]
    q=''.join('q[k '+n+'['+args(FAC)+']].' for n in ('r6hz','r6h2'))
    d=fixture(('r6hz','r6h2'),q);v=model(d);assert run(d,v)==[True,True]
    v['zpoint']=lambda:'w01';assert run(d,v)==[False,True]
    v['h26yx']=lambda *a:False;assert run(d,v)==[False,False]
    for n in ('h26zb','h26zc','h26ys','h26yt','ab','ac','h26yu','h26yv','h26yw','h26yx'):
        w=model(d);w[n]=unknown;rejects(d,w)
    return dict(cases=cases,native_owned_and_used_rcr_faculty=True,all_matters_and_reasons=True,
      native_xd_xf_task_methods=True,unassessed_distinct_from_no_opportunity=True,unknown_rejected=True)

@lru_cache(None)
def endpoint_checks():
    q='q[k r6h3['+args((*SCOPE_NAMES,'end'))+']].';d=fixture(('r6h3',),q);v=model(d);assert run(d,v)==[True];cases={}
    for name in ('empty_history','missing_start','missing_end','reflexive_time','reverse_time','incomparable_middle','cycle','regime_switch_middle','extra_permission_middle','lost_permission_middle','end_ownership_lost','start_ownership_lost','empty_tasks','extra_unfulfilled_task','unassessed_start','unassessed_end','end_not_full','wrong_reference','same_start_end'):
        w=dict(v)
        if name=='empty_history':w['h26zd']=lambda *a:False
        if name=='missing_start':w['h26zd']=lambda *a:a[-1]!=a[-3] and v['h26zd'](*a)
        if name=='missing_end':w['h26zd']=lambda *a:a[-1]!=a[-2] and v['h26zd'](*a)
        if name=='reflexive_time':w['h26ze']=lambda *a:a[-2]==a[-1] or v['h26ze'](*a)
        if name=='reverse_time':w['h26ze']=lambda *a:v['h26ze'](*a[:-2],a[-1],a[-2])
        if name=='incomparable_middle':w['h26ze']=lambda *a:'middle' not in a[-2:] and v['h26ze'](*a)
        if name=='cycle':w['h26ze']=lambda *a:(a[-2],a[-1])==('end','w01') or v['h26ze'](*a)
        if name=='regime_switch_middle':w['r6fr']=lambda *a:a[-1]!='middle' and v['r6fr'](*a)
        if name=='extra_permission_middle':w['r6hf']=lambda *a:v['r6hf'](*a) or a[-1]=='middle'
        if name=='lost_permission_middle':w['r6hf']=lambda *a:a[-1]!='middle' and v['r6hf'](*a)
        if name=='end_ownership_lost':w['ab']=lambda f,p,t:t!='end' and v['ab'](f,p,t)
        if name=='start_ownership_lost':w['ab']=lambda f,p,t:t!='w01' and v['ab'](f,p,t)
        if name=='empty_tasks':w['h26zc']=lambda *a:False
        if name=='extra_unfulfilled_task':w['h26ys']=lambda c,p,t,r:t=='b'
        if name=='unassessed_start':w['h26yx']=lambda *a:a[-2]!='w01' and v['h26yx'](*a)
        if name=='unassessed_end':w['h26yx']=lambda *a:a[-2]!='end' and v['h26yx'](*a)
        if name=='end_not_full':w['h26yw']=w['h26yx']=lambda c,t,r,p,m,s,o:v['h26yw'](c,t,r,p,m,'w01' if s=='end' else s,o)
        if name=='wrong_reference':w['zreference']=lambda:'other'
        if name=='same_start_end':w['zend']=lambda:'w01'
        assert run(d,w)==[False],name;cases[name]=False
    # A faculty whose whole range was already exercisable may be maintained.
    w=dict(v);w['h26zc']=lambda p,f,t,r:v['h26zc'](p,f,t,r) and t=='b';assert run(d,w)==[True]
    for n in ('h26zd','h26ze','r6fr','r6hf'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    return dict(cases=cases,native_ta_strict_total_history=True,native_all_task_assessment_and_opportunity=True,
      already_full_faculty_may_be_preserved=True,intermediate_regime_or_permission_change_rejected=True,
      boundary='Only r6fr/r6hf concrete public-order and permission values; prior reports pin their native bodies.')

@lru_cache(None)
def development_checks():
    q='q[k r6h5['+args(SCOPE_NAMES)+']].';d=fixture(('r6h5',),q);v=model(d);assert run(d,v)==[True];cases={}
    for name in ('no_development_method','unassessed_result','outside_possible_result','unsuccessful_result','wrong_person_method','wrong_faculty_method','wrong_regime_method','unowned_start'):
        w=dict(v)
        if name=='no_development_method':w['h26zf']=lambda *a:False
        if name=='unassessed_result':w['h26zh']=lambda *a:False
        if name=='outside_possible_result':w['h26zg']=lambda *a:False
        if name=='unsuccessful_result':w['h26zg']=w['h26zh']=lambda *a:a[-1]=='failure'
        if name=='wrong_person_method':w['h26zf']=lambda *a:a[2]=='b'
        if name=='wrong_faculty_method':w['h26zf']=lambda *a:a[3]=='a'
        if name=='wrong_regime_method':w['h26zf']=lambda *a:a[1]=='b'
        if name=='unowned_start':w['ab']=lambda f,p,t:t!='w01' and v['ab'](f,p,t)
        assert run(d,w)==[False],name;cases[name]=False
    for n in ('h26zf','h26zg','h26zh'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    return dict(cases=cases,native_development_xd_and_endpoint_body=True,
      development_method_separate_from_task_execution=True,actual_development_not_asserted=True)

@lru_cache(None)
def scope_checks():
    q='q[k r6h6['+args(('community','order','reference','start'))+']].'
    d=fixture(('r6h6',),q,('r6h5','r6h2','r6hz'));base=model(d);rows=[]
    base['h26zb']=lambda c,p,f,r:(c,p,r)==('b','a','reference') and f in DOMAIN
    base['h26zc']=lambda p,f,t,r:(p,r)==('a','reference') and f==t
    base['r6h2']=lambda *a:True
    for initial in product((False,True),repeat=2):
        for opportunity in product((False,True),repeat=2):
            v=dict(base);v['r6hz']=lambda c,p,f,t,r,s:initial[DOMAIN.index(f)]
            v['r6h5']=lambda c,o,p,f,r,s:(c,o,p,r,s)==('b','a','a','reference','w01') and opportunity[DOMAIN.index(f)]
            want=all(opportunity) and not all(initial);assert run(d,v)==[want]
            rows.append(dict(initial=initial,opportunity=opportunity,value=want))
    v=dict(base);v.update(r6hz=lambda *a:a[2]=='b',r6h5=lambda *a:True);assert run(d,v)==[True]
    for name in ('empty_people','empty_faculties','unassessed_only_growth','no_unfulfilled_task','one_faculty_no_method','one_person_no_method'):
        w=dict(v)
        if name=='empty_people':w['h237c']=lambda *a:False
        if name=='empty_faculties':w['h26zb']=lambda *a:False
        if name=='unassessed_only_growth':w['r6h2']=lambda *a:a[2]=='b'
        if name=='no_unfulfilled_task':w['r6hz']=lambda *a:True
        if name=='one_faculty_no_method':w['r6h5']=lambda *a:a[3]=='b'
        if name=='one_person_no_method':
            w['aa']=lambda *a:True;w['h237c']=lambda *a:True;w['h26zb']=lambda *a:True;w['r6h5']=lambda *a:a[2]=='a'
        assert run(d,w)==[False],name
    # Full native composition has one unfulfilled and one already open task.
    native=fixture(('r6h6',),q);v=model(native);assert run(native,v)==[True]
    v['h26zc']=lambda p,f,t,r:(p,f,t,r)==('a','b','b','reference');assert run(native,v)==[False]
    return dict(all_faculties_matrix=rows,empty_population_and_faculty_scope_rejected=True,
      preservation_and_genuine_room_distinct=True,no_strict_increase_per_faculty=True,native_population_integration=True,
      boundary='r6h5/r6h2/r6hz only in the two-faculty truth table; full native one-faculty/two-task composition also executes.')

@lru_cache(None)
def causal_room_checks():
    q='q[k r6h7['+args(CONTEXT)+']].';d=fixture(('r6h7',),q,('r6hu','r6h6'));rows=[]
    for table in range(16):
        for holds in product((False,True),repeat=2):
            v=model(d);v['r6hu']=lambda *a:a==CTX
            v['h26y4']=lambda *a:True if a[-2]=='a' else bool(table&(1<<(2*int(a[-1]('a'))+int(a[-1]('b')))))
            v['r6h6']=lambda c,o,r,s:(c,o,r)==('b','a','reference') and s in ('w00','w01') and holds[int(s[-1])]
            sols=[b for b in (False,True) if b==bool(table&(1<<int(b)))];want=holds[1] and bool(sols) and all(holds[int(b)] for b in sols)
            assert run(d,v)==[want],(table,holds);rows.append(dict(table=table,holds=holds,value=want))
    # Native causal comparison + whole population development; only public norms are boundaries.
    native=fixture(('r6h7',),q);v=model(native);assert run(native,v)==[True]
    # An extra off solution with no development method is rejected.
    v['h26y4']=lambda *a:True if a[-2]=='a' else a[-1]('b')
    v['h26zf']=lambda *a:a[-1]!='w00' and model(native)['h26zf'](*a)
    assert run(native,v)==[False]
    return dict(equation_and_opportunity_cases=rows,actual_low_and_nonempty_all_off_solutions=True,
      native_r6hu_rw_and_development_population=True,nonobserved_off_solution_without_room_rejected=True,
      boundary='r6hu/r6h6 in the 64-case table; the native bodies execute together in the final two cases, with only r6fr/r6hf supplied as normative values.')

@lru_cache(None)
def adapter_checks():
    # Every outer development scope slot and every callback slot is recorded.
    q='q[k r6h5['+args(SCOPE_NAMES)+']].';d=fixture(('r6h5',),q,('r6h4','xd'));base=model(d);calls=[];goals=[]
    def goal(*a):goals.append(a);return content(lambda t:t=='end')
    def ability(p,g,s,av,possible,selected):
        calls.append(('xd',(p,s)));assert g==content(lambda t:t=='end')
        av('b','a','other');possible('b','a','other','failure');selected('b','a','other','failure');return True
    base.update(r6h4=goal,xd=ability)
    for n in ('h26zf','h26zg','h26zh'):
        def rec(*a,n=n):calls.append((n,a));return True
        base[n]=rec
    def expected(c):
        scope=tuple(c[n] for n in ('community','order','person','faculty','reference'))
        return [('xd',(c['person'],c['start']))]+[(n,(*scope,'b','a','other',*tail)) for n,tail in (('h26zf',()),('h26zg',('failure',)),('h26zh',('failure',)))]
    for changed in (None,*SCOPE_NAMES):
        c=dict(CONSTANTS);v=dict(base)
        if changed:c[changed]='other' if changed in ('reference','start') else ('b' if c[changed]=='a' else 'a');v['z'+changed]=lambda changed=changed:c[changed]
        calls.clear();goals.clear();run(d,v,False)
        assert calls==expected(c) and goals==[tuple(c[n] for n in SCOPE_NAMES)],(changed,calls,goals)
    # Task methods retain the task (not faculty) and forward arbitrary actor/point values.
    q=''.join('q[k '+n+'['+args(FAC)+']].' for n in ('r6hz','r6h2'))
    d=fixture(('r6hz','r6h2'),q,('r6hy','xd','xf'));v=model(d);calls.clear();goals.clear()
    v['r6hy']=goal;v['xd']=v['xf']=ability
    for n in ('h26yv','h26yw','h26yx'):
        def rec(*a,n=n):calls.append((n,a));return True
        v[n]=rec
    assert run(d,v,False)==[True,True]
    expected_calls=[('xd',('a','end'))]+[(n,('b','a','reference','b','a','other',*tail)) for n,tail in (('h26yv',()),('h26yw',('failure',)),('h26yx',('failure',)))]
    assert calls==expected_calls*2 and goals==[('a','b','a','reference')]*2,(calls,goals)
    return dict(all_six_development_scope_arguments_recorded=True,task_and_faculty_not_interchanged=True,
      callbacks_forward_actor_method_point_outcome=True,boundary='xd/xf and goal constructors only for call recording; their native bodies execute in other checks.')

@lru_cache(None)
def content_checks():
    q='q[k r6ia['+args(CONTEXT)+']].';d=fixture(('r6ia',),q);v=model(d);assert run(d,v)==[True]
    for name in ('unmapped_task','unmapped_person','no_faculty'):
        w=dict(v)
        if name=='unmapped_task':w['h26zc']=lambda p,f,t,r:t=='a'
        if name=='unmapped_person':w['h26za']=lambda *a:a==(*CTX,'b','b')
        if name=='no_faculty':w['h26zb']=lambda *a:False
        assert run(d,w)==[False],name
    fields=('observer','community','lowerorder','higherorder','reference')
    q='q[t[k r6ib['+args(fields)+']]['+z('anchor')+']].';d=fixture(('r6ib',),q,('r6hx','r6h7','r6ia'));base=model(d)
    for a,b,c in product((False,True),repeat=3):
        v=dict(base);v['r6hx']=lambda *xs:content(lambda t:a and xs==tuple(CONSTANTS[n] for n in fields) and t=='anchor')
        v['r6h7']=lambda *xs:b and xs==CTX;v['r6ia']=lambda *xs:c and xs==CTX
        assert run(d,v)==[a and b and c]
    for n in (*fields,'anchor'):
        w=dict(v);w['z'+n]=lambda n=n:'other' if n in ('reference','anchor') else ('b' if CONSTANTS[n]=='a' else 'a');assert run(d,w)==[False],n
    quoted=fixture(('r6ib',),'q[e[r d[p r6ib]][r d[p r6ib]]].')
    assert run(quoted,{r['name']:unknown for r in quoted['declarations'] if r['kind']=='primitive'})==[True]
    return dict(all_barrier_targets_mapped_to_same_faculty_tasks=True,three_conjuncts_and_all_context_slots=True,
      quotation_not_executed=True,boundary='r6hx/r6h7/r6ia only for combined-content wiring; mapping and room native bodies execute here, r6hx is pinned by the prior barrier report.')

def reading_record():
    u=next(u for u in read(INVENTORY)['units'] if u['id']=='kant-1784:u0017');phrase='ein Grad weniger von jener verschaft hingegen diesem Raum, sich nach allem seinen Vermögen auszubreiten';a=u['text'].index(phrase)
    return dict(status='same_regime_all_faculties_room_dependency',source_unit=u['id'],unit_sha256=u['text_sha256'],
      alignment=dict(segments=[dict(unit=u['id'],range=[a,a+len(phrase)],text=phrase,definitions=list(MEANINGS),status='explicit_interpretive_annotation')]),
      interpretation=LIMITS,whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,new_verified_characters=0,
      source_sha256={p:digest((ROOT/p).read_bytes()) for p in (LIBRARY,BASIS,DOC,SOURCE,INVENTORY,*PRIORS)})
@lru_cache(None)
def structure_checks():
    c=catalog();assert not c.document['statements']
    for p in (parent(),main_catalog()):
        for n,e in p.entries.items():
            if n in c.entries:assert c.entries[n]['declaration']==e['declaration'] and c.entries[n]['meaning_ja']==e['meaning_ja'],n
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
    assert ranks=={n:3 if n=='r6ib' else 0 for n in MEANINGS},ranks
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),minimum_quote_ranks=ranks,
      inherited_bodies_and_meanings_unchanged=True,roundtrips=True,new_verified_characters=0)

def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))
def build_report():
    results={}
    for n,f in (('faculty_goal',faculty_goal_checks),('endpoint',endpoint_checks),('development',development_checks),('scope',scope_checks),('causal_room',causal_room_checks),('adapters',adapter_checks),('content',content_checks),('structure',structure_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(catalog().source_sha256)|{LIBRARY,BASIS,DOC,READING,SOURCE,INVENTORY,INDEX,*PRIORS,
      'scripts/compose_faculty_development_room.py','scripts/check_faculty_development_room.py','tests/test_faculty_development_room.py',
      'scripts/compose_civic_regime_barriers.py','scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py'}
    return dict(status='same_regime_all_faculties_development_room_checked_partial',document=LIBRARY,**results,alignment=read(READING)['alignment'],
      whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
      source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
