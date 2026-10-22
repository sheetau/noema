"""Check actual contrivance, unexecuted causal purposes and complete noninterference."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_deliberate_retention import ROOT,LIBRARY,BASIS,MEANINGS,PRIMITIVES,LIMITS,parent,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown

DOC='docs/deliberate-retention-v1.md';READING='data/deliberate-retention-reading-v1.json'
INDEX='data/semantic-review-index-v200.json';INVENTORY='artifacts/written-units-v1/kant-1784.json'
PRIORS=('reports/collective-retention-v1.json','reports/guardian-purpose-v1.json')
SOURCE='data/eighth-paragraph-source-reading-v2.json'
DOMAIN=('actor','target','other','activity','otheract','group');SCENES=('reference','first','middle','last','after')
def z(n):return 'k z'+n+'[]'
def args(ns):return ' '.join(z(n) for n in ns)
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def codeid(c):return c.rank,json.loads(c.syntax)
STATE='r[c[p r6ap]['+z('reference')+']]'
TIMES='r[p zhistory] r[p zbefore] r['+z('first')+'] r['+z('last')+']'
GOAL='r b[c[p r6aq]['+args(('activity','target'))+' '+TIMES+' '+STATE+']]'
FACTOR='r[c[p r2mj]['+z('first')+']]'
EFFECT='r[c[p r2mk][p zhistory p zbefore '+args(('first','last'))+' c[p r6ap]['+z('reference')+']]]'
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(query):
    d=deepcopy(catalog().document)
    extra=''.join('r z'+n+'[] '+('a' if n in DOMAIN else 'd')+'.' for n in (*DOMAIN,*SCENES))
    extra+='r znamepick[a '+' '.join('i[a]' for n in DOMAIN)+'] i[a].r zrefpick[d '+' '.join('i[d]' for n in SCENES)+'] i[d].'
    extra+='d h223g[item a] i[a][k znamepick[v item '+' '.join('r['+z(n)+']' for n in DOMAIN)+']].'
    extra+='d h223h[point d] i[d][k zrefpick[v point '+' '.join('r['+z(n)+']' for n in SCENES)+']].'
    extra+='r zhistory[d] c.r zbefore[d d] c.r ztargets[a] c.r zinterventions[a a a] c.'
    extra+='r zsavestate[i[h[a] e]] c.r zsavegoal[i b[e]] c.r zsaveactual[i b[e]] c.r zsavefactor[i[h[a] e]] c.r zsaveeffect[i[h[a] e]] c.'
    p=parse('p:'+extra);ns={r['name'] for r in p['declarations']}
    d['declarations']=p['declarations']+[r for r in d['declarations'] if r['name'] not in ns]
    pre='q[k zsavestate['+STATE+']].q[k zsavegoal['+GOAL+']].q[k zsavefactor['+FACTOR+']].q[k zsaveeffect['+EFFECT+']].'
    return parse(format_graph(d,'compact')+pre+query)
def run(d,v):return evaluate(d,v,DOMAIN,SCENES,True)[4:]
def rejects(d,v):
    try:run(d,v)
    except ValueError as e:assert 'Unknown' in str(e),str(e)
    else:raise AssertionError('Unknown supplied as known absence or purpose')
def model(d):
    v={r['name']:unknown for r in d['declarations'] if r['kind']=='primitive'};saved={}
    v.update({'z'+n:lambda n=n:n for n in (*DOMAIN,*SCENES)})
    for key in ('state','goal','actual','factor','effect'):
        v['zsave'+key]=lambda c,key=key:saved.update({key:codeid(c)}) is None
    v.update(znamepick=lambda p,*cs:cs[DOMAIN.index(p)],zrefpick=lambda p,*cs:cs[SCENES.index(p)],
        zhistory=lambda p:p in SCENES[1:],zbefore=lambda p,q:SCENES.index(p)<SCENES.index(q),
        aa=lambda p:p in ('actor','target','other'),dg=lambda a,t:(a,t)==('activity','first'),
        df=lambda p,a,t:(p,a,t)==('actor','activity','first'),
        h26rh=lambda p,r,t:p=='target' and r=='reference' and t in SCENES[1:],
        h26ri=lambda a,p,s,r,t:(a,p,r,t)==('activity','target','reference','first') and codeid(s)==saved['state'],
        h26rj=lambda *a:a==('actor','activity','reference','first'),
        h26rk=lambda p,a,g,t:(p,a,t)==('actor','activity','first') and codeid(g)==saved['goal'],
        hzie=lambda a,f,p,e,t:(a,p)==('activity','target') and t in ('last','after') and codeid(f)==saved['factor'] and codeid(e)==saved['effect'],
        h246c=lambda g,p,r:g=='group' and r=='reference' and p in ('target','other'),
        ztargets=lambda p:p in ('target','other'),zinterventions=lambda *a:False)
    return v,saved

@lru_cache(None)
def state_checks():
    q=''.join('q[t[c[k r6ap['+z('reference')+']]['+z(p)+']]['+z('first')+']].' for p in ('target','actor','activity'))
    d=fixture(q);v,_=model(d);assert run(d,v)==[True,False,False]
    w=dict(v);w['aa']=lambda *a:False;assert run(d,w)==[False]*3
    w=dict(v);w['h26rh']=lambda p,r,t:r=='after';assert run(d,w)==[False]*3
    for n in ('aa','h26rh'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    return dict(same_human_and_reference=True,no_equation_with_intellectual_immaturity=True,unknown_rejected=True)

@lru_cache(None)
def attainment_checks():
    q=''.join('q[t[k r6aq['+args(('activity','target'))+' '+TIMES+' '+STATE+']]['+z(t)+']].' for t in ('first','last','after'))
    d=fixture(q);v,_=model(d);assert run(d,v)==[False,True,True];rows={}
    for case in ('no_occurrence','no_cause','other_activity','other_target','intermediate_loss','late_acquisition','missing_endpoint','cyclic_history','equal_endpoints','reversed_interval'):
        w=dict(v)
        if case=='no_occurrence':w['dg']=lambda *a:False
        if case=='no_cause':w['hzie']=lambda *a:False
        if case=='other_activity':w['hzie']=lambda a,*rest:a=='otheract'
        if case=='other_target':w['hzie']=lambda a,f,p,e,t:p=='other'
        if case=='intermediate_loss':w['h26rh']=lambda p,r,t:(p,r)==('target','reference') and t!='middle'
        if case=='late_acquisition':w['h26rh']=lambda p,r,t:(p,r)==('target','reference') and t in ('last','after')
        if case=='missing_endpoint':w['zhistory']=lambda t:t not in ('reference','last')
        if case=='cyclic_history':w['zbefore']=lambda p,q:SCENES.index(p)<SCENES.index(q) or (p,q)==('last','first')
        if case=='equal_endpoints':w['zlast']=lambda:'first'
        if case=='reversed_interval':w['zfirst']=lambda:'last';w['zlast']=lambda:'first'
        got=run(d,w);assert got==[False]*3,(case,got);rows[case]=got
    for n in ('dg','hzie','h26rh','zhistory','zbefore'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    return dict(cases=rows,native_whole_interval_and_same_act_cause=True,goal_not_achieved_before_its_end=True,unknown_rejected=True)

@lru_cache(None)
def purpose_checks():
    q='q[k zsaveactual[k r6ar[r['+z('activity')+'] r['+z('target')+'] '+TIMES+' '+STATE+']]].'
    d=fixture(q);v,saved=model(d)
    for n in ('dg','df','h26rh','hzie','zhistory','zbefore'):v[n]=unknown
    assert run(d,v)==[True];assert saved['actual']==saved['goal']
    args0=['r['+z('activity')+']','r['+z('target')+']','r[p zhistory]','r[p zbefore]','r['+z('first')+']','r['+z('last')+']',STATE]
    replacements=['r['+z('otheract')+']','r['+z('other')+']','r[i[t d][u[k zhistory[v t]]]]','r[i[a d b d][k zbefore[v b v a]]]','r['+z('middle')+']','r['+z('after')+']','r[i[p a][b t[u[t[c[k r6ap['+z('reference')+']][v p]][v t]]]]]']
    for i,replacement in enumerate(replacements):
        changed=list(args0);changed[i]=replacement;dd=fixture('q[k zsaveactual[k r6ar['+' '.join(changed)+']]].');vv,ss=model(dd)
        assert run(dd,vv)==[True];assert ss['actual']!=ss['goal'],i
    return dict(all_seven_goal_arguments_checked=True,constructed_quote_matches_independent_literal=True,goal_truth_and_feasibility_not_executed=True)

@lru_cache(None)
def intervention_checks():
    q='q[k r6at['+args(('actor','activity','target'))+' '+TIMES+' '+args(('reference','first'))+']].'
    d=fixture(q);v,_=model(d);assert run(d,v)==[True];rows={}
    for case in ('unexecuted','nonparticipant','accidental','not_contrivance','other_purpose','not_currently_raw','wrong_state','wrong_actor','wrong_target','wrong_activity','wrong_reference','wrong_point','wrong_first','wrong_activity_name','wrong_target_name','wrong_reference_name','future_failure','future_unknown'):
        w=dict(v)
        if case=='unexecuted':w['dg']=lambda *a:False
        if case=='nonparticipant':w['df']=lambda *a:False
        if case=='accidental':w['h26rj']=lambda *a:False
        if case=='not_contrivance':w['h26ri']=lambda *a:False
        if case=='other_purpose':w['h26rk']=lambda *a:False
        if case=='not_currently_raw':w['h26rh']=lambda *a:False
        if case=='wrong_state':w['h26ri']=lambda a,p,s,r,t:False
        if case=='wrong_actor':w['h26rk']=lambda p,a,g,t:p=='other'
        if case=='wrong_target':w['h26ri']=lambda a,p,s,r,t:p=='other'
        if case=='wrong_activity':w['h26rk']=lambda p,a,g,t:a=='otheract'
        if case=='wrong_reference':w['h26ri']=lambda a,p,s,r,t:r=='after'
        if case=='wrong_point':w['h26rj']=lambda p,a,r,t:t=='middle'
        if case=='wrong_first':w['zfirst']=lambda:'middle'
        if case in ('wrong_activity_name','wrong_target_name'):
            item='activity' if case=='wrong_activity_name' else 'target'
            w['znamepick']=lambda p,*cs,item=item:cs[DOMAIN.index('other' if p==item else p)]
            w['h26rk']=lambda *a:True
        if case=='wrong_reference_name':w['zrefpick']=lambda p,*cs:cs[-1];w['h26rk']=lambda *a:True;w['h26ri']=lambda *a:True;w['h26rh']=lambda *a:True
        if case=='future_failure':w['h26rh']=lambda p,r,t:(p,r,t)==('target','reference','first');w['hzie']=lambda *a:False
        if case=='future_unknown':w['hzie']=unknown;w['zhistory']=unknown;w['zbefore']=unknown
        got=run(d,w);assert got==[case in ('future_failure','future_unknown')],(case,got);rows[case]=got[0]
    for n in ('aa','dg','df','h26rh','h26ri','h26rj','h26rk','znamepick','zrefpick'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    # Actual goal adoption with an unknown future remains possible; current state is assessed.
    return dict(cases=rows,same_actual_activity_actor_target_state_and_point=True,failed_interference_still_counts=True,
        future_retention_cause_and_history_not_executed_when_adopting_goal=True,unknown_current_inputs_rejected=True)

@lru_cache(None)
def absence_checks():
    d=fixture('q[k r6au[p ztargets p zinterventions]].q[k r6av['+args(('group','reference'))+' p zinterventions]].');v,_=model(d)
    assert run(d,v)==[True,True];count=0
    for actor in DOMAIN:
        for activity in DOMAIN:
            for target in ('target','other'):
                w=dict(v);w['zinterventions']=lambda a,b,c,row=(actor,activity,target):(a,b,c)==row
                assert run(d,w)==[False,False];count+=1
    w=dict(v);w['zinterventions']=lambda a,b,c:c=='actor';assert run(d,w)==[True,True]
    w=dict(v);w['ztargets']=lambda *a:False;w['h246c']=lambda *a:False;assert run(d,w)==[False,False]
    w=dict(v);w['h246c']=lambda g,p,r:g=='group' and r=='reference' and p=='activity';assert run(d,w)==[True,False]
    for n in ('zinterventions','ztargets','h246c'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    return dict(all_single_intervention_locations=count,any_target_and_any_actor_activity_checked=True,empty_and_nonhuman_population_rejected=True,
        unrelated_target_ignored=True,unknown_rejected=True,boundary='The complete intervention relation is an explicit input here. Source-time coverage and all purpose periods remain to be connected; no single checked period proves total noninterference.')

def reading_record():
    u=next(x for x in read(INVENTORY)['units'] if x['id']=='kant-1784:u0015')
    return dict(status='deliberate_same_state_retention_partial',source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[1210,1354],text=u['text'][1210:1354]),
        interpretation=LIMITS,whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,new_verified_characters=0,
        unresolved=['von selbstとnach und nachを伴う同じ状態からの離脱過程','全関連時機・目的期間にわたる非介入とwenn man nur nicht','本文設定・全文帰属・通読'],
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in (LIBRARY,BASIS,DOC,INVENTORY,*PRIORS,SOURCE)})
@lru_cache(None)
def structure_checks():
    c=catalog();old=parent();assert not c.document['statements'];assert len(old.document['statements'])==116
    for n,e in c.entries.items():
        if n in old.entries:assert e['declaration']==old.entries[n]['declaration'] and e['meaning_ja']==old.entries[n]['meaning_ja']
    for p in (*PRIORS,SOURCE):validate_hashes(ROOT,read(p)['source_sha256'])
    validate_hashes(ROOT,read(BASIS)['import_source_sha256'])
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b
    assert read(READING)==reading_record()
    for notation in ('compact','full'):
        t=format_graph(c.document,notation);assert parse(t)==parse(transcribe(t,alphabet='v2'))==c.document
    t=format_graph(c.document,'compact');ranks={}
    for name in ('r6ap','r6aq','r6at','r6av'):
        for rank,label in enumerate(('','b','c','d','e')):
            try:parse(t+'q[e[r '+label+'[p '+name+']][r '+label+'[p '+name+']]].')
            except ValueError as e:assert 'Quoted evaluation' in str(e),str(e)
            else:ranks[name]=rank;break
    assert ranks=={'r6ap':0,'r6aq':1,'r6at':1,'r6av':0},ranks
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),unchanged_manuscript_statements=116,
        inherited_meanings_preserved=True,roundtrips=True,minimum_quote_ranks=ranks,new_verified_characters=0)
def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))
def build_report():
    results={}
    for n,f in (('state',state_checks),('attainment',attainment_checks),('purpose',purpose_checks),('intervention',intervention_checks),('absence',absence_checks),('structure',structure_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(catalog().source_sha256)|{LIBRARY,BASIS,DOC,READING,INDEX,INVENTORY,*PRIORS,SOURCE,
        'scripts/compose_deliberate_retention.py','scripts/check_deliberate_retention.py','tests/test_deliberate_retention.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py'}
    return dict(status='deliberate_contrivance_for_retention_checked_partial',document=LIBRARY,**results,
        alignment=dict(**read(READING)['source'],statements=[],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
