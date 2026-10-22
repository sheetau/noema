"""Check qualitative graduality and the same person's self-caused departure."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_gradual_self_departure import ROOT,LIBRARY,BASIS,MEANINGS,PRIMITIVES,LIMITS,parents,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown

DOC='docs/gradual-self-departure-v1.md';READING='data/gradual-self-departure-reading-v1.json'
INDEX='data/semantic-review-index-v200.json';INVENTORY='artifacts/written-units-v1/kant-1784.json'
PRIORS=('reports/deliberate-retention-v1.json','reports/self-achievement-v1.json','reports/self-formed-course-v1.json','reports/departure-hindrance-trend-v1.json')
SOURCE='data/eighth-paragraph-source-reading-v2.json'
DOMAIN=('person','other','process','part');SCENES=('reference','first','early','middle','late','last')
def z(n):return 'k z'+n+'[]'
def args(ns):return ' '.join(z(n) for n in ns)
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def codeid(c):return c.rank,json.loads(c.syntax)
TIME='p zhistory p zbefore '+args(('first','last'))
PROFILE=TIME+' p zassessed p zatleast p zsmall'
BOUND=args(('person','process','reference'))+' '+TIME
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(query):
    d=deepcopy(catalog().document)
    extra=''.join('r z'+n+'[] '+('a' if n in DOMAIN else 'd')+'.' for n in (*DOMAIN,*SCENES))
    extra+='r zhistory[d] c.r zbefore[d d] c.r zassessed[d] c.r zatleast[d d] c.r zsmall[d d] c.'
    extra+='r zrefpick[d '+' '.join('i[d]' for n in SCENES)+'] i[d].'
    extra+='d h223h[point d] i[d][k zrefpick[v point '+' '.join('r['+z(n)+']' for n in SCENES)+']].'
    extra+='r zsave[i[h[a] e]] c.'
    p=parse('p:'+extra);ns={r['name'] for r in p['declarations']}
    d['declarations']=p['declarations']+[r for r in d['declarations'] if r['name'] not in ns]
    return parse(format_graph(d,'compact')+'q[k zsave[r[c[p r6ay]['+z('reference')+']]]].'+query)
def run(d,v):return evaluate(d,v,DOMAIN,SCENES,True)[1:]
def rejects(d,v):
    try:run(d,v)
    except ValueError as e:assert 'Unknown' in str(e),str(e)
    else:raise AssertionError('Unknown accepted as progress')
def model(d,levels=(0,1,2,3,4)):
    v={r['name']:unknown for r in d['declarations'] if r['kind']=='primitive'};saved={}
    v.update({'z'+n:lambda n=n:n for n in (*DOMAIN,*SCENES)})
    score=dict(zip(SCENES,(0,*levels)))
    v.update(zsave=lambda c:saved.update(goal=codeid(c)) is None,zrefpick=lambda p,*cs:cs[SCENES.index(p)],
        zhistory=lambda p:p in SCENES[1:],zbefore=lambda p,q:SCENES.index(p)<SCENES.index(q),
        zassessed=lambda t:True,zatleast=lambda a,b:score[a]>=score[b],zsmall=lambda a,b:score[b]-score[a]<=1,
        aa=lambda p:p in ('person','other'),h26rh=lambda p,r,t:(p,r)==('person','reference') and score[t]<2,
        ag=lambda *a:a==('process','first','last'),la=lambda *a:a==('person','process','first','last'),
        dg=lambda *a:a==('process','last'),df=lambda *a:a==('person','process','last'),
        h4m=lambda *a:a==('part','person','last'),h4n=lambda *a:a==('person','part','process','last'),
        g3=lambda proc,p,code,t:(proc,p,t)==('process','person','last') and codeid(code)==saved['goal'],
        h26rn=lambda *a:a==('person','process','reference','first','last'),
        h26ro=lambda p,r,t:(p,r)==('person','reference'),
        h26rl=lambda p,r,a,b:(p,r)==('person','reference') and score[a]>=score[b],
        h26rm=lambda p,r,a,b:(p,r)==('person','reference') and score[b]-score[a]<=1)
    return v

@lru_cache(None)
def gradual_checks():
    d=fixture('q[k r6ax['+PROFILE+']].');rows={}
    patterns={
        'staged':((0,1,2,3,4),True),'plateau':((0,1,1,2,3),True),'setback':((0,1,0,1,2),True),
        'single_jump':((0,0,0,0,3),False),'jump_with_other_progress':((0,1,4,4,4),False),
        'flat':((1,1,1,1,1),False),'lower_end':((2,3,2,1,1),False),
        'only_intermediate_times':((0,0,2,2,2),False),'first_equals_last':((1,2,3,2,1),False)}
    for case,(levels,expected) in patterns.items():
        got=run(d,model(d,levels));assert got==[expected],(case,got);rows[case]=got[0]
    count=0
    # Across all 64 paths with fixed 0/3 endpoints, a numeric fixture's small-step
    # interpretation reduces to no adjacent positive jump above 1. This oracle
    # does not duplicate the definition's all-pairs/middle-point construction.
    for middle in product(range(4),repeat=3):
        levels=(0,*middle,3);expected=all(b-a<=1 for a,b in zip(levels,levels[1:]))
        assert run(d,model(d,levels))==[expected],levels;count+=1
    v=model(d)
    for case in ('unassessed_middle','missing_endpoint','cyclic_time','nonreflexive','incomparable','nontransitive','nonpositive_gain_rejected'):
        w=dict(v)
        if case=='unassessed_middle':w['zassessed']=lambda t:t!='middle'
        if case=='missing_endpoint':w['zhistory']=lambda t:t not in ('reference','last')
        if case=='cyclic_time':w['zbefore']=lambda a,b:SCENES.index(a)<SCENES.index(b) or (a,b)==('last','first')
        if case=='nonreflexive':w['zatleast']=lambda a,b:v['zatleast'](a,b) and (a,b)!=('middle','middle')
        if case=='incomparable':w['zatleast']=lambda a,b:v['zatleast'](a,b) and {a,b}!={'first','middle'}
        if case=='nontransitive':w['zatleast']=lambda a,b:v['zatleast'](a,b) or (a,b) in (('first','early'),('early','middle'))
        if case=='nonpositive_gain_rejected':w['zsmall']=lambda a,b:v['zsmall'](a,b) and a!=b
        got=run(d,w);assert got==[False],(case,got);rows[case]=False
    for n in ('zhistory','zbefore','zassessed','zatleast','zsmall'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    return dict(cases=rows,fixed_endpoint_paths=count,allows_setbacks_and_plateaus=True,rejects_unresolved_large_jumps=True,
        preorder_and_all_interval_assessment_checked=True,unknown_rejected=True)

@lru_cache(None)
def departure_checks():
    d=fixture('q[k r6az['+BOUND+']].q[k r6a2['+BOUND+']].');v=model(d);assert run(d,v)==[True,True];rows={}
    for case in ('not_initially_raw','still_raw','no_change_process','other_affected_person','not_occurring','not_active','no_mental_part','no_self_work','no_same_result','external_only','wrong_reference_name','wrong_result_content'):
        w=dict(v)
        if case=='not_initially_raw':w['h26rh']=lambda *a:False
        if case=='still_raw':w['h26rh']=lambda *a:True
        if case=='no_change_process':w['ag']=lambda *a:False
        if case=='other_affected_person':w['la']=lambda p,proc,a,b:p=='other'
        if case=='not_occurring':w['dg']=lambda *a:False
        if case=='not_active':w['df']=lambda *a:False
        if case=='no_mental_part':w['h4m']=lambda *a:False
        if case=='no_self_work':w['h4n']=lambda *a:False
        if case=='no_same_result':w['g3']=lambda *a:False
        if case=='external_only':w['h26rn']=lambda *a:False
        if case=='wrong_reference_name':w['zrefpick']=lambda p,*cs:cs[-1];w['g3']=lambda *a:True
        if case=='wrong_result_content':w['g3']=lambda proc,p,code,t:codeid(code)[1].get('function',{}).get('symbol')=='r6ap'
        got=run(d,w);assert got==([True,False] if case=='external_only' else [False,False]),(case,got);rows[case]=got
    for n in ('aa','h26rh','ag','la','dg','df','h4m','h4n','g3','h26rn','zrefpick'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    return dict(cases=rows,native_rcp_same_state_transition_and_native_self_work=True,
        initiative_distinct_from_participation=True,closed_result_description_checked=True,unknown_rejected=True)

@lru_cache(None)
def state_measure_checks():
    q='q[k r6a3['+args(('person','reference'))+' '+TIME+']].'
    d=fixture(q);v=model(d);assert run(d,v)==[True];rows={}
    for case in ('raw_at_high_level','free_at_low_level','wrong_person_scale','wrong_reference_scale','consistent_setback'):
        w=dict(v)
        if case=='raw_at_high_level':w['h26rh']=lambda p,r,t:(p,r)==('person','reference') and t in ('first','early','late')
        if case=='free_at_low_level':w['h26rh']=lambda p,r,t:(p,r)==('person','reference') and t=='early'
        if case=='wrong_person_scale':w['h26rl']=lambda p,r,a,b:p=='other'
        if case=='wrong_reference_scale':w['h26rl']=lambda p,r,a,b:r=='last'
        if case=='consistent_setback':w=model(d,(0,1,0,1,2))
        got=run(d,w);assert got==[case=='consistent_setback'],(case,got);rows[case]=got[0]
    for n in ('h26rh','h26rl'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    return dict(cases=rows,state_cut_consistent_with_same_qualitative_scale=True,within_state_levels_and_reentry_allowed=True,unknown_rejected=True)

@lru_cache(None)
def combined_checks():
    d=fixture('q[k r6a4['+BOUND+']].');v=model(d);assert run(d,v)==[True];rows={}
    for case in ('setback','no_initiative','single_jump','unassessed','wrong_scale_person','wrong_small_reference','wrong_process','wrong_interval','state_scale_mismatch'):
        w=dict(v)
        if case=='setback':w=model(d,(0,1,0,1,2))
        if case=='no_initiative':w['h26rn']=lambda *a:False
        if case=='single_jump':w=model(d,(0,0,0,0,3))
        if case=='unassessed':w['h26ro']=lambda p,r,t:t!='middle'
        if case=='wrong_scale_person':w['h26rl']=lambda p,r,a,b:p=='other'
        if case=='wrong_small_reference':w['h26rm']=lambda p,r,a,b:r=='last'
        if case=='wrong_process':w['h26rn']=lambda p,proc,r,a,b:proc=='other'
        if case=='wrong_interval':w['h26rn']=lambda p,proc,r,a,b:(a,b)==('early','last')
        if case=='state_scale_mismatch':w['h26rh']=lambda p,r,t:(p,r)==('person','reference') and t in ('first','early','late')
        got=run(d,w);assert got==[case=='setback'],(case,got);rows[case]=got[0]
    for n in ('h26rl','h26rm','h26rn','h26ro'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    return dict(cases=rows,native_transition_graduality_and_state_cut_combined=True,same_person_reference_process_and_interval=True,
        no_universal_ban_on_education_or_assistance=True,unknown_rejected=True)

def reading_record():
    u=next(x for x in read(INVENTORY)['units'] if x['id']=='kant-1784:u0015')
    return dict(status='gradual_self_departure_partial',source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[1210,1354],text=u['text'][1210:1354]),
        interpretation=LIMITS,whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,new_verified_characters=0,
        unresolved=['全関連時機・目的期間にわたる非介入','Die Menschenの範囲・wenn man nur nichtの条件と限定','本文設定・全文帰属・通読'],
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in (LIBRARY,BASIS,DOC,INVENTORY,*PRIORS,SOURCE)})
@lru_cache(None)
def structure_checks():
    c=catalog();assert not c.document['statements'];assert len(parents()[1].document['statements'])==116
    for old in parents():
        for n,e in c.entries.items():
            if n in old.entries:assert e['declaration']==old.entries[n]['declaration'] and e['meaning_ja']==old.entries[n]['meaning_ja']
    for p in (*PRIORS,SOURCE):validate_hashes(ROOT,read(p)['source_sha256'])
    validate_hashes(ROOT,read(BASIS)['import_source_sha256'])
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b
    assert read(READING)==reading_record()
    for notation in ('compact','full'):
        t=format_graph(c.document,notation);assert parse(t)==parse(transcribe(t,alphabet='v2'))==c.document
    t=format_graph(c.document,'compact');ranks={}
    for name in ('r6ax','r6ay','r6az','r6a4'):
        for rank,label in enumerate(('','b','c','d','e')):
            try:parse(t+'q[e[r '+label+'[p '+name+']][r '+label+'[p '+name+']]].')
            except ValueError as e:assert 'Quoted evaluation' in str(e),str(e)
            else:ranks[name]=rank;break
    assert ranks=={'r6ax':0,'r6ay':0,'r6az':1,'r6a4':1},ranks
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),unchanged_manuscript_statements=116,
        inherited_meanings_preserved=True,roundtrips=True,minimum_quote_ranks=ranks,new_verified_characters=0)
def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))
def build_report():
    results={}
    for n,f in (('gradual',gradual_checks),('departure',departure_checks),('state_measure',state_measure_checks),('combined',combined_checks),('structure',structure_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(catalog().source_sha256)|{LIBRARY,BASIS,DOC,READING,INDEX,INVENTORY,*PRIORS,SOURCE,
        'scripts/compose_gradual_self_departure.py','scripts/check_gradual_self_departure.py','tests/test_gradual_self_departure.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py'}
    return dict(status='gradual_self_departure_checked_partial',document=LIBRARY,**results,
        alignment=dict(**read(READING)['source'],statements=[],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
