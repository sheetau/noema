"""Check risky undertaking, explicit prohibition and the republic quantifier."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import Content
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_republic_speech_prohibition import ROOT,LIBRARY,BASIS,OLD,OLD_BASIS,ACTION,MEANINGS,PRIMITIVES,LIMITS,parents,legacy,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown

DOC='docs/republic-speech-prohibition-v1.md';READING='data/republic-speech-prohibition-reading-v1.json'
SOURCE='data/tenth-paragraph-source-reading-v1.json';INVENTORY='artifacts/written-units-v1/kant-1784.json';INDEX='data/semantic-review-index-v203.json'
PRIORS=('reports/risk-undertaking-v1.json','reports/political-quoted-speech-v1.json','reports/republic-polity-v1.json')
DOMAIN=('a','b','c');SCENES=('reference','start','view','harm','safe')
CONSTANTS=dict(actor='c',community='b',activity='a',standard='a',role='b',reference='reference',point='start',other='safe')
REF='r[k zreference[]]'
def z(n):return 'k z'+n+'[]'
def args(ns):return ' '.join(z(n) for n in ns)
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def code(c):return c.rank,json.loads(c.syntax)
def atom(n):return dict(kind='call',symbol='z'+n,arguments=[])
def quoted(n,*arguments):return 2,dict(kind='apply',function=dict(kind='function_ref',symbol=n),arguments=[atom(a) for a in arguments])
def content(f):return Content(SCENES,tuple(f(t) for t in SCENES))
GOAL=quoted('r6f5','reference');TRIAL=quoted('r6f7','community','reference')
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(roots,query,boundaries=()):
    d=deepcopy(catalog().document);d['statements']=[]
    for r in d['declarations']:
        if r['name'] in boundaries:r.update(kind='primitive',parameters=[p['sort'] for p in r['parameters']]);r.pop('body')
    constants=''.join('r z'+n+'[] '+('a' if v in DOMAIN else 'd')+'.' for n,v in CONSTANTS.items())
    constants+='r zrefpick[d i[d] i[d]] i[d].d h223h[point d] i[d][k zrefpick[v point r[k zreference[]] r[k zother[]]]].'
    constants+='r zindpick[a i[a] i[a] i[a]] i[a].d h223g[person a] i[a][k zindpick[v person r[k zactivity[]] r[k zcommunity[]] r[k zactor[]]]].'
    prefix=parse('p:'+constants)['declarations'];names={r['name'] for r in prefix}
    d['declarations']=prefix+[r for r in d['declarations'] if r['name'] not in names]
    d['declarations']=closure(d,(*roots,*names))
    return parse(format_graph(d,'compact')+query)
def model(d):
    v={r['name']:unknown for r in d['declarations'] if r['kind']=='primitive'}
    v.update({'z'+n:lambda v=v:v for n,v in CONSTANTS.items()})
    v.update(zrefpick=lambda r,a,b:a if r=='reference' else b,zindpick=lambda p,a,b,c:{'a':a,'b':b,'c':c}[p])
    v.update(h26wa=lambda p,c,r,a,g,t,e:(p,c,r,a,code(g),t,e)==('c','b','reference','a',GOAL,'view','harm'),
      h26wb=lambda p,c,r,e:(p,c,r,e)==('c','b','reference','harm'),
      h26wc=lambda p,c,r,a,g,t:(p,c,r,a,code(g),t)==('c','b','reference','a',GOAL,'start'),
      h26wd=lambda p,c,r,a,g,t,e:(p,c,r,a,code(g),t,e)==('c','b','reference','a',GOAL,'start','view'),
      h26we=lambda p,c,r,a,t:(p,c,r,a,t)==('c','b','reference','a','start'),
      h26wf=lambda p,c,r,a,g,t:(p,c,r,a,code(g),t)==('c','b','reference','a',GOAL,'start'),
      h26wg=lambda p,c,r,a,t:(p,c,r,t)==('c','b','reference','start') and a in ('a','b'),
      h26wh=lambda c,r,s,p,role,a,g,sign,t:(c,r,s,p,role,code(g),sign,t)==('b','reference','a','c','b',TRIAL,False,'start') and a in ('a','b'))
    return v
def run(d,v):return evaluate(d,v,DOMAIN,SCENES,True)
def rejected(d,v):
    try:run(d,v)
    except ValueError as e:assert 'Unknown' in str(e),str(e)
    else:raise AssertionError('Unknown input accepted')

@lru_cache(None)
def target_checks():
    direct='k r6f6['+REF+']'
    trial='k r6ga[r[k zcommunity[]] '+REF+']'
    q='q[e['+direct+'][r c[c[p r6f5][k zreference[]]]]].q[e['+trial+'][r c[c[p r6f7][k zcommunity[] k zreference[]]]]].'
    d=fixture(('r6f6','r6ga'),q);assert run(d,{r['name']:unknown for r in d['declarations'] if r['kind']=='primitive'})==[True,True]
    q='q[t[c[s['+direct+']]['+args(('actor','activity'))+']]['+z('point')+']].'
    d=fixture(('r6f6',),q,('r6fy',));v=model(d);calls=[]
    def speech(p,a,r):calls.append((p,a,code(r)));return content(lambda t:(p,a,code(r),t)==('c','a',(0,atom('reference')),'start'))
    v['r6fy']=speech;assert run(d,v)==[True];assert set((p,a,json.dumps(r,sort_keys=True)) for p,a,r in calls)=={('c','a',json.dumps((0,atom('reference')),sort_keys=True))}
    for name in ('actor','activity','reference','point'):
        w=dict(v);w['z'+name]=lambda name=name:'safe' if name in ('reference','point') else 'b';assert run(d,w)==[False],name
    w=dict(v);w['zrefpick']=lambda r,a,b:b;assert run(d,w)==[False]
    w=dict(v);w['r6fy']=unknown;rejected(d,w)
    return dict(closed_goal_and_trial_syntax_checked=True,rank=2,quotation_construction_does_not_execute=True,
      same_actor_activity_reference_and_point=True,wrong_name_rejected=True,boundary='r6fy only: current same official quoted speech body is pinned in political-quoted-speech-v1.')

@lru_cache(None)
def undertaking_checks():
    q='q[t[c[k r6f7['+args(('community','reference'))+']]['+args(('actor','activity'))+']]['+z('point')+']].'
    d=fixture(('r6f7',),q);base=model(d);rows=[];names=tuple(PRIMITIVES)[:6]
    for bits in product((False,True),repeat=6):
        v=dict(base)
        for n,b in zip(names,bits):
            if not b:v[n]=lambda *a:False
        got=run(d,v);assert got==[all(bits)],(bits,got);rows.append(dict(bits=list(bits),value=got[0]))
    v=dict(base);old=v['h26wd'];v['h26wd']=lambda p,c,r,a,g,t,e:old(p,c,r,a,g,t,e) or (p,c,r,a,code(g),t,e)==('c','b','reference','a',GOAL,'start','safe')
    assert run(d,v)==[False]
    for n in names:
        v=dict(base);v[n]=unknown;rejected(d,v)
    for n in ('actor','community','activity','reference','point'):
        v=dict(base);v['z'+n]=lambda n=n:'safe' if n in ('reference','point') else ('a' if CONSTANTS[n]!='a' else 'b');assert run(d,v)==[False],n
    assert run(d,base)==[True] # All actual speech primitives remain unknown.
    return dict(native_rwg_rwh_rwi_matrix=rows,empty_views_and_unrecognized_risk_rejected=True,second_risk_free_view_rejected=True,
      actual_speech_or_harm_not_required=True,all_context_slots_checked=True,unknown_rejected=True)

@lru_cache(None)
def provider_checks():
    q='q[t[c[k r6f7['+args(('community','reference'))+']]['+args(('actor','activity'))+']]['+z('point')+']].'
    q='r zcapture['+ACTION+'] c.q[k zcapture[r c[c[p r6f5][k zother[]]]]].'+q
    d=fixture(('r6f7',),q,('rwi',));v=model(d)
    fields=('actor','activity','community','reference','point');cases=[]
    for changed in (None,*fields):
        expected=dict(CONSTANTS);w=dict(v);seen=[];probe=[]
        def capture(value):probe.append(value);return True
        w['zcapture']=capture
        if changed:
            expected[changed]='safe' if changed in ('reference','point') else ('b' if expected[changed]=='a' else 'a')
            w['z'+changed]=lambda changed=changed:expected[changed]
        for name in tuple(PRIMITIVES)[:6]:
            def record(*a,name=name):seen.append((name,tuple(code(x) if hasattr(x,'syntax') else x for x in a)));return True
            w[name]=record
        def invoke(p,a,g,t,prospects,adverse,recognizes,views,begins,pursues):
            assert (p,a)==(expected['actor'],expected['activity'])
            assert code(g)==quoted('r6f5','other' if expected['reference']=='safe' else 'reference')
            # Pass another checked closed goal through the callback, so an
            # adapter cannot silently capture the original rwi goal instead.
            alternate=probe[0]
            prospects('b','c',alternate,'view','harm');adverse('a','safe');recognizes('a','b',alternate,'harm')
            views('c','a',alternate,'reference','safe');begins('b','a','view');pursues('a','c',alternate,'safe')
            return t==expected['point']
        w['rwi']=invoke;assert evaluate(d,w,DOMAIN,SCENES,False)==[True,True],changed
        g=quoted('r6f5','other');c=expected['community'];r=expected['reference']
        block=[('h26wa',('b',c,r,'c',g,'view','harm')),('h26wb',('a',c,r,'safe')),('h26wc',('a',c,r,'b',g,'harm')),
          ('h26wd',('c',c,r,'a',g,'reference','safe')),('h26we',('b',c,r,'a','view')),('h26wf',('a',c,r,'c',g,'safe'))]
        assert seen==block*len(SCENES),(changed,seen);cases.append(changed or 'baseline')
    return dict(context_and_callback_slots_checked=cases,all_six_adapters_checked=True,description_structure_checked=True,
      boundary='rwi for argument recording only; its native body runs in undertaking_checks.')

@lru_cache(None)
def prohibition_checks():
    q='q[k r6gb['+args(('actor','community','standard','role'))+' '+REF+' '+z('point')+']].'
    d=fixture(('r6gb',),q);base=model(d);assert run(d,base)==[True];rows={}
    for variant in ('no_explicit_requirement','positive_requirement_only','second_candidate_unforbidden','empty_candidates'):
        v=dict(base)
        if variant=='empty_candidates':v['h26wg']=lambda *a:False
        elif variant=='positive_requirement_only':v['h26wh']=lambda c,r,s,p,role,a,g,sign,t:sign
        elif variant=='second_candidate_unforbidden':
            old=v['h26wh'];v['h26wh']=lambda c,r,s,p,role,a,g,sign,t:a=='a' and old(c,r,s,p,role,a,g,sign,t)
        else:v['h26wh']=lambda *a:False
        assert run(d,v)==[False],variant;rows[variant]=False
    for n in ('actor','community','standard','role','reference','point'):
        v=dict(base);v['z'+n]=lambda n=n:'safe' if n in ('reference','point') else ('a' if CONSTANTS[n]!='a' else 'b');assert run(d,v)==[False],n
    # Record each norm argument, including the two different candidate activities.
    calls=[];v=dict(base)
    def record(*a):calls.append(tuple(code(x) if hasattr(x,'syntax') else x for x in a));return True
    v['h26wh']=record;assert run(d,v)==[True]
    # The evaluator is eager, so the universal body also evaluates non-candidates.
    assert calls==[('b','reference','a','c','b',a,TRIAL,False,'start') for a in DOMAIN],calls
    for n in ('h26wg','h26wh','zindpick','zrefpick'):
        v=dict(base);v[n]=unknown;rejected(d,v)
    for n in ('zindpick','zrefpick'):
        v=dict(base);v[n]=(lambda p,a,b,c:a) if n=='zindpick' else (lambda r,a,b:b);assert run(d,v)==[False],n
    # No risk, commencement, utterance or positive-permission callback is used.
    for n in tuple(PRIMITIVES)[:6]:base[n]=unknown
    assert run(d,base)==[True]
    return dict(cases=rows,nonempty_all_candidates_required=True,explicit_negative_requirement=True,
      mere_absence_of_permission_insufficient=True,all_nine_requirement_arguments_recorded=True,
      attempted_or_successful_speech_not_executed=True,unknown_rejected=True)

@lru_cache(None)
def republic_checks():
    q='q[t[k r6gc['+args(('standard','role','reference'))+']]['+z('point')+']].'
    d=fixture(('r6gc',),q,('r6fu',));base=model(d)
    def values(republics=('b','c'),forbidden=('b','c')):
        v=dict(base)
        v['r6fu']=lambda p,r:content(lambda t:p in republics and (r,t)==('reference','start'))
        v['h26wg']=lambda p,c,r,a,t:p==c and r=='reference' and a=='a' and t=='start'
        v['h26wh']=lambda c,r,s,p,role,a,g,sign,t:p==c and p in forbidden and (r,s,role,code(g),sign,t)==(
          'reference','a','b',quoted('r6f7',{'a':'activity','b':'community','c':'actor'}[c],'reference'),False,'start')
        return v
    rows={}
    for name,reps,forb,want in (('two_republics',('b','c'),('b','c'),True),('second_not_forbidden',('b','c'),('b',),False),
      ('nonrepublic_not_forbidden',('b',),('b',),True),('no_republics',(),(),True)):
        assert run(d,values(reps,forb))==[want],name;rows[name]=want
    for n in ('standard','role','reference','point'):
        v=values();v['z'+n]=lambda n=n:'safe' if n in ('reference','point') else 'c'
        # A changed point/reference changes the classification range; use fixed
        # republics for the point check and the name guard for reference.
        if n in ('point','reference'):v['r6fu']=lambda p,r:content(lambda t:p in ('b','c'))
        assert run(d,v)==[False],n
    v=values();v['zrefpick']=lambda r,a,b:b;assert run(d,v)==[False]
    v=values();v['r6fu']=unknown;rejected(d,v)
    return dict(cases=rows,same_polity_as_actor_and_community=True,same_standard_role_reference_point=True,
      no_republic_existence_asserted=True,boundary='r6fu only: native institutional classification is pinned in republic-polity-v1.')

def reading_record():
    u=next(u for u in read(INVENTORY)['units'] if u['id']=='kant-1784:u0017');phrase='was ein Freistaat nicht wagen darf';a=u['text'].index(phrase)
    return dict(status='explicit_prudential_prohibition_of_same_official_speech_attempt',source_unit=u['id'],unit_sha256=u['text_sha256'],
      alignment=dict(segments=[dict(unit=u['id'],range=[a,a+len(phrase)],text=phrase,definitions=list(MEANINGS),status='explicit_interpretive_annotation')]),
      interpretation=LIMITS,whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,new_verified_characters=0,
      source_sha256={p:digest((ROOT/p).read_bytes()) for p in (LIBRARY,BASIS,DOC,SOURCE,INVENTORY,*PRIORS)})
@lru_cache(None)
def structure_checks():
    c=catalog();assert not c.document['statements'];ds,means=legacy()
    for d in ds:assert c.entries[d['name']]['declaration']==d
    for n,m in means.items():assert c.entries[n]['meaning_ja']==m
    for source in parents():
        for n,e in source.entries.items():
            if n in c.entries:assert c.entries[n]['declaration']==e['declaration'] and c.entries[n]['meaning_ja']==e['meaning_ja']
    for p in (*PRIORS,SOURCE):validate_hashes(ROOT,read(p)['source_sha256'])
    validate_hashes(ROOT,read(BASIS)['import_source_sha256']);assert read(READING)==reading_record()
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b
    for notation in ('compact','full'):
        t=format_graph(c.document,notation);assert parse(t)==parse(transcribe(t,alphabet='v2'))==c.document
    t=format_graph(c.document,'compact');ranks={}
    for n in MEANINGS:
        for rank,label in enumerate(('','b','c','d')):
            try:parse(t+'q[e[r '+label+'[p '+n+']][r '+label+'[p '+n+']]].')
            except ValueError as e:assert 'Quoted evaluation' in str(e),str(e)
            else:ranks[n]=rank;break
    assert ranks=={n:1 for n in MEANINGS},ranks
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),legacy_and_current_meanings_unchanged=True,
      minimum_quote_ranks=ranks,roundtrips=True,new_verified_characters=0)
def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))
def build_report():
    results={}
    for n,f in (('targets',target_checks),('undertaking',undertaking_checks),('providers',provider_checks),('prohibition',prohibition_checks),('republics',republic_checks),('structure',structure_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(catalog().source_sha256)|{LIBRARY,BASIS,DOC,READING,SOURCE,INVENTORY,INDEX,OLD,OLD_BASIS,*PRIORS,
      'scripts/compose_republic_speech_prohibition.py','scripts/check_republic_speech_prohibition.py','tests/test_republic_speech_prohibition.py',
      'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py'}
    return dict(status='risk_aware_official_speech_explicit_prudential_prohibition_checked_partial',document=LIBRARY,**results,alignment=read(READING)['alignment'],
      whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
      source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
