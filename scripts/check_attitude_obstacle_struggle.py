"""Check candidate-dependent paths, actual countereffort and nonvacuous need."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import FunctionValue,SequenceValue
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_attitude_obstacle_struggle import ROOT,LIBRARY,BASIS,MEANINGS,PRIMITIVES,LIMITS,STATE,ASSIGNMENT,WITNESSES,MAPS,MODELS,GOAL_FIELDS,parents,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown

DOC='docs/attitude-obstacle-struggle-v1.md';READING='data/attitude-obstacle-struggle-reading-v1.json'
INDEX='data/semantic-review-index-v198.json';INVENTORY='artifacts/written-units-v1/kant-1784.json'
PRIORS=('reports/social-attitude-paths-v1.json','reports/government-self-misunderstanding-v1.json','reports/personal-salvation-judgment-v1.json')
DOMAIN=('a','b','c','d');SCENES=('reference','now','later','on','off')
REGION_VALUES=('a','b','c','d','a','b')
def z(n):return 'k z'+n+'[]'
def args(ns):return ' '.join(z(n) for n in ns)
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def codeid(c):return c.rank,json.loads(c.syntax)
GOAL_ARGS=args((*REGION_VALUES,'c','b','reference'))+' '+' '.join('p z'+n for n,t in WITNESSES)
MODEL_ARGS=' '.join('p z'+n for n,t in MODELS)
CONDITIONS='l[a]['+args(('a','b'))+']'
STATE_CODE='k r56o[r['+z('reference')+']]'
SAVE='q[k zsavestate['+STATE_CODE+']].q[k zsavepolicy[k r56k[r['+z('reference')+']]]].'
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(roots,query,boundaries=(),extra=''):
    d=deepcopy(catalog().document)
    for r in d['declarations']:
        if r['name'] in (*boundaries,'r56l'):
            assert r['result']=='truth';r.update(kind='primitive',parameters=[p['sort'] for p in r['parameters']]);r.pop('body')
    prefix=''.join('r z'+n+'[] '+('a' if n in DOMAIN else 'd')+'.' for n in (*DOMAIN,*SCENES))
    prefix+='r zsavestate['+STATE+'] c.r zsavepolicy[i c[e]] c.r zrefpick[d '+' '.join('i[d]' for n in SCENES)+'] i[d].'
    prefix+='d h223h[point d] i[d][k zrefpick[v point '+' '.join('r['+z(n)+']' for n in SCENES)+']].'
    prefix+='r zfirst[d] a.r zrest[d] j[a].r zhistoryrow[d d] c.r zbeforerow[d d d] c.'
    prefix+='d zhistory[scene d] h[d] c[i[point d][k zhistoryrow[v scene v point]]].'
    prefix+='d zbefore[scene d] h[d d] c[i[left d right d][k zbeforerow[v scene v left v right]]].'
    for n,t in MAPS:
        prefix+='r z'+n+'row[d a] '+t+'.d z'+n+'[scene d] h[a] '+t+'[i[step a][k z'+n+'row[v scene v step]]].'
    prefix+='r zvariables[a] j[a].r zfactor[a] a.r zequationrow[a a '+ASSIGNMENT+'] c.'
    prefix+='d zequations[condition a] h[a '+ASSIGNMENT+'] c[i[var a state '+ASSIGNMENT+'][k zequationrow[v condition v var v state]]].'
    prefix+='r zworldrow[a '+ASSIGNMENT+'] d.d zworlds[condition a] h['+ASSIGNMENT+'] d[i[state '+ASSIGNMENT+'][k zworldrow[v condition v state]]].'
    prefix+='r zmatchrow[a '+ASSIGNMENT+' '+ASSIGNMENT+'] c.d zmatches[condition a] h['+ASSIGNMENT+' '+ASSIGNMENT+'] c[i[left '+ASSIGNMENT+' right '+ASSIGNMENT+'][k zmatchrow[v condition v left v right]]].'
    prefix+='r zevaluatedrow[a d] c.d zevaluated[condition a] h[d] c[i[point d][k zevaluatedrow[v condition v point]]].'
    prefix+='r zcases[d] c.r zgoalrow[d] c.r zundertakenrow[d] c.d zgoal[] e[b point[k zgoalrow[v point]]].d zundertaken[] e[b point[k zundertakenrow[v point]]].'
    p=parse('p:'+prefix+extra);ns={r['name'] for r in p['declarations']}
    d['declarations']=p['declarations']+[r for r in d['declarations'] if r['name'] not in ns]
    d.update(declarations=closure(d,(*roots,'r56o','r56k',*ns)),statements=[])
    return parse(format_graph(d,'compact')+SAVE+query)
def run(d,v):return evaluate(d,v,DOMAIN,SCENES,True)[2:]
def rejects(d,v):
    try:run(d,v)
    except ValueError as e:assert 'Unknown' in str(e),str(e)
    else:raise AssertionError('Unknown input accepted')
def model(d):
    v={r['name']:unknown for r in d['declarations'] if r['kind']=='primitive'};saved={}
    v.update({'z'+n:lambda n=n:n for n in (*DOMAIN,*SCENES)})
    v.update(zsavestate=lambda c:saved.update(state=codeid(c)) is None,zsavepolicy=lambda c:saved.update(policy=codeid(c)) is None,
        zrefpick=lambda p,*cs:cs[SCENES.index(p)],r56l=lambda r:r=='reference',aa=lambda p:p in ('a','b'),
        h26pg=lambda p,c,t:p=='a' and codeid(c)==saved['policy'],
        dg=lambda act,t:act=='c',df=lambda p,act,t:(p,act)==('a','c'),
        h26pi=lambda act,p,c,t:(act,p)==('c','a') and codeid(c)==saved['state'],
        h26po=lambda p,act,r,t:(p,act,r)==('a','c','reference'),
        h26pn=lambda act,cond,p,c,r,t:(act,cond,p,r)==('c','d','b','reference') and codeid(c)==saved['state'],
        zfirst=lambda t:'a' if t=='on' else 'b',zrest=lambda t:SequenceValue(('c',) if t=='on' else ('d',),'"individual"'),
        zhistoryrow=lambda scene,t:scene==t,zbeforerow=lambda scene,l,r:l=='reference' and r==scene,
        zvariables=lambda cond:SequenceValue((cond,'c'),'"individual"'),zfactor=lambda cond:cond,
        zequationrow=lambda cond,var,s:var==cond,zworldrow=lambda cond,s:'on' if cond=='a' else 'off',
        zmatchrow=lambda cond,l,r:cond in ('a','b'),zevaluatedrow=lambda cond,t:t==('on' if cond=='a' else 'off'),
        zcases=lambda t:t in ('now','later'),zgoalrow=lambda t:t!='on',zundertakenrow=lambda t:t=='now')
    for n,t in MAPS:v['z'+n+'row']=lambda scene,step,t=t:('a' if scene=='on' else 'b') if t=='a' else scene
    return v,saved

@lru_cache(None)
def candidate_goal_checks():
    q=''.join('q[t[k r57a['+GOAL_ARGS+']]['+z(t)+']].' for t in ('on','off'))
    d=fixture(('r57a',),q,('r56x',));v,_=model(d);seen=[]
    def path(*a):
        t=a[-1];seen.append(t)
        expected='a' if t=='on' else 'b';tail=('c',) if t=='on' else ('d',)
        fixed=a[:6]==REGION_VALUES and a[8:11]==('c','b','reference')
        return fixed and (a[6],tuple(a[7].items))==(expected,tail) and a[11](t) and not a[11]('reference') and a[12]('reference',t) and all(f('c')==(expected if kind=='a' else t) for f,(n,kind) in zip(a[13:20],MAPS))
    v['r56x']=path;assert run(d,v)==[True,True];assert set(seen)==set(SCENES)
    for n in ('zfirst','zrest','zsenderrow','zrecipientrow','zactivityrow','zprocessrow','zstartrow','zactedrow','zendrow','zhistoryrow','zbeforerow'):
        w=dict(v)
        if n=='zfirst':w[n]=lambda t:'c'
        elif n=='zrest':w[n]=lambda t:SequenceValue((),'"individual"')
        elif n in ('zhistoryrow','zbeforerow'):w[n]=lambda *a:False
        elif n in ('zstartrow','zactedrow','zendrow'):w[n]=lambda *a:'reference'
        else:w[n]=lambda *a:'d'
        assert run(d,w)==[False,False],n
    w=dict(v);w['r56x']=unknown;rejects(d,w)
    return dict(candidate_specific_path_history_order_and_seven_maps=True,same_fixed_regions_people_reference=True,
        boundary='r56x has separate native path/retention/region evidence. Here every argument and candidate-dependent function reaches that boundary; no full unbounded path search is claimed.')

@lru_cache(None)
def necessity_checks():
    d=fixture(('r57b',),'q[k r57b[k zgoal[] k zundertaken[] p zcases]].');rows=0
    for goals in product((False,True),repeat=2):
        for acts in product((False,True),repeat=2):
            v,_=model(d);v['zgoalrow']=lambda t:goals[('now','later').index(t)] if t in ('now','later') else True
            v['zundertakenrow']=lambda t:acts[('now','later').index(t)] if t in ('now','later') else False
            got=run(d,v);expected=any(goals) and all(not g or a for g,a in zip(goals,acts));assert got==[expected],(goals,acts,got);rows+=1
    v,_=model(d);v['zcases']=lambda *a:False;assert run(d,v)==[False]
    for n in ('zcases','zgoalrow','zundertakenrow'):
        v,_=model(d);v[n]=unknown;rejects(d,v)
    return dict(two_outcome_truth_combinations=rows,impossible_goal_and_empty_scope_rejected=True,
        goal_not_implied_by_activity=True,unknown_rejected=True,native_situations_and_quantifiers=True)

@lru_cache(None)
def counteractivity_checks():
    q='q[k r57d['+args(('a','b','c','d'))+' '+STATE_CODE+' '+args(('reference','now'))+']].q[t[k r57e['+args(('b','d','reference'))+']]['+z('now')+']].'
    d=fixture(('r57d','r57e'),q);rows={}
    for case in ('present','no_state','no_manifestation','no_effort','no_opposition','no_activity','no_participant','other_condition','other_beneficiary','other_state','wrong_reference_name'):
        v,s=model(d)
        failures={'no_state':'h26pg','no_manifestation':'h26pi','no_effort':'h26po','no_opposition':'h26pn','no_activity':'dg','no_participant':'df'}
        if case in failures:v[failures[case]]=lambda *a:False
        if case=='other_condition':v['h26pn']=lambda act,c,*a:c=='a'
        if case=='other_beneficiary':v['h26pn']=lambda act,c,p,*a:p=='a'
        if case=='other_state':v['h26pn']=lambda act,c,p,state,*a:codeid(state)!=s['state']
        if case=='wrong_reference_name':v['zrefpick']=lambda p,*cs:cs[-1]
        got=run(d,v);assert got==[case=='present']*2,(case,got);rows[case]=got
    for n in ('h26po','h26pn','h26pg'):
        v,_=model(d);v[n]=unknown;rejects(d,v)
    # The beneficiary may act personally; no unequal-person requirement is added.
    d2=fixture(('r57d',),'q[k r57d['+args(('a','a','c','d'))+' '+STATE_CODE+' '+args(('reference','now'))+']].')
    v,s=model(d2);v['h26pn']=lambda act,c,p,state,r,t:(act,c,p,r)==('c','d','a','reference') and codeid(state)==s['state'];assert run(d2,v)==[True]
    return dict(cases=rows,beneficiary_or_other_holder_can_act=True,actual_shared_policy_quote_executed=True,
        policy_realization_and_success_not_required=True,unknown_rejected=True,
        boundary='Only shared-policy eligibility r56l is bounded here. Native r56n/r56q actual attitude, quote identity, occurrence, participation, exertion and opposition execute.')

@lru_cache(None)
def plural_model_checks():
    q='q[k r57f['+args(('d','b','b'))+' '+CONDITIONS+' '+args(('reference','now'))+' k zgoal[] '+MODEL_ARGS+']].'
    d=fixture(('r57f',),q,('r563','r564','r566'));v,_=model(d);seen=[]
    v['r563']=lambda *a:a==('d','b','reference','now')
    v['r564']=lambda g,c,p,cond,r,t:(g,c,p,r,t)==('d','b','b','reference','now') and cond in ('a','b')
    def profile(cond,ref,variables,equations,factor,worlds,matches,evaluated,goal):
        seen.append(cond);s=FunctionValue(('individual',),'truth',lambda v:v=='a');t='on' if cond=='a' else 'off'
        return ref=='reference' and variables.items==(cond,'c') and factor==cond and equations(cond,s) and not equations('d',s) and worlds(s)==t and matches(s,s) and evaluated(t) and not evaluated('reference') and goal.situations==SCENES and goal.values==(True,True,True,False,True)
    v['r566']=profile;assert run(d,v)==[True];assert set(seen)==set(DOMAIN)
    for name in ('r563','r564','r566'):
        w=dict(v);w[name]=lambda *a:False;assert run(d,w)==[False]
    for cond in ('a','b'):
        w=dict(v);w['r566']=lambda c,*a:c!=cond;assert run(d,w)==[False]
    for literal in ('l[a][]','l[a]['+z('a')+']','l[a]['+args(('a','a'))+']'):
        doc=fixture(('r57f',),q.replace(CONDITIONS,literal),('r563','r564','r566'));assert run(doc,v)==[False]
    w=dict(v);w['r566']=unknown;rejects(d,w)
    return dict(two_distinct_conditions_required=True,every_condition_checked=True,same_goal_for_all_condition_models=True,
        boundary='Native plural/list quantification and per-condition model selectors; r563/r564/r566 have native institutional/error/intervention evidence in the prior report.')

@lru_cache(None)
def scope_checks():
    q='q[k r57h['+args(('d','b','b'))+' '+CONDITIONS+' '+z('reference')+' p zcases]].'
    d=fixture(('r57h',),q,('r564',));v,_=model(d)
    v['r564']=lambda g,c,p,cond,r,t:(g,c,p,r)==('d','b','b','reference') and cond in ('a','b') and t in ('now','later')
    assert run(d,v)==[True]
    for cond,t in product(('a','b'),('now','later')):
        w=dict(v);w['r564']=lambda g,c,p,item,r,point:(item,point)!=(cond,t);assert run(d,w)==[False]
    w=dict(v);w['zcases']=lambda *a:False;assert run(d,w)==[False]
    w=dict(v);w['r564']=unknown;rejects(d,w)
    # Every selected obstacle has its own activity witness; the full finite domain is used.
    extra='r zcounter[a a d d] c.d r57e[target a condition a reference d] e[b point[k zcounter[v target v condition v reference v point]]].'
    q='q[t[k r57g['+z('b')+' '+CONDITIONS+' '+z('reference')+']]['+z('now')+']].'
    d=fixture(('r57g',),q,extra=extra);v,_=model(d);v['zcounter']=lambda *a:a[0]=='b' and a[2:] ==('reference','now');assert run(d,v)==[True]
    for cond in ('a','b'):
        w=dict(v);w['zcounter']=lambda p,c,r,t:c!=cond;assert run(d,w)==[False]
    return dict(all_background_conditions_in_all_cases=True,empty_case_range_rejected=True,all_conditions_need_counteractivity=True,
        boundary='r564/r57e separately checked; finite all-condition and all-case quantifiers run without trimming their domains.')

@lru_cache(None)
def combined_checks():
    extra='r zboundgoal[a a a d d] c.d r57a['+GOAL_FIELDS+'] e[b point[k zboundgoal[v government v foreigncommunity v target v reference v point]]].'
    extra+='r zcounter[a j[a] d d] c.d r57g[target a conditions j[a] reference d] e[b point[k zcounter[v target v conditions v reference v point]]].'
    q='q[k r57i['+GOAL_ARGS+' '+CONDITIONS+' '+z('now')+' '+MODEL_ARGS+' p zcases]].'
    d=fixture(('r57i',),q,('r57f','r57h'),extra);v,_=model(d)
    v['zboundgoal']=lambda g,c,p,r,t:(g,c,p,r)==('d','b','b','reference') and t in ('now','later')
    v['zcounter']=lambda p,cs,r,t:(p,tuple(cs.items),r)==('b',('a','b'),'reference') and t in ('now','later')
    v['r57f']=lambda g,c,p,cs,r,at,goal,*ms:(g,c,p,tuple(cs.items),r,at)==('d','b','b',('a','b'),'reference','now') and goal.situations==SCENES and goal.values==tuple(t in ('now','later') for t in SCENES)
    v['r57h']=lambda g,c,p,cs,r,cases:(g,c,p,tuple(cs.items),r)==('d','b','b',('a','b'),'reference') and tuple(t for t in SCENES if cases(t))==('now','later')
    assert run(d,v)==[True];rows={}
    for case in ('no_current_arrival','no_current_effort','successful_effort_free_future','no_obstacles','changed_background','impossible_goal'):
        w=dict(v)
        if case=='no_current_arrival':w['zboundgoal']=lambda g,c,p,r,t:t=='later';w['r57f']=lambda *a:True
        if case=='no_current_effort':w['zcounter']=lambda p,cs,r,t:t=='later'
        if case=='successful_effort_free_future':w['zcounter']=lambda p,cs,r,t:t=='now'
        if case=='no_obstacles':w['r57f']=lambda *a:False
        if case=='changed_background':w['r57h']=lambda *a:False
        if case=='impossible_goal':w['zboundgoal']=lambda *a:False;w['r57f']=lambda *a:True
        got=run(d,w);assert got==[False],(case,got);rows[case]=got[0]
    return dict(cases=rows,current_arrival_effort_and_nonvacuous_necessity_separated=True,
        same_foreign_government_target_conditions_reference_and_goal=True,
        boundary='The separately checked goal, obstacle bundle, counteractivity bundle and background guard are boundaries. Their exact argument connections and r57b necessity execute natively; no full-source truth or unbounded model exhaustiveness is proved.')

def reading_record():
    u=next(x for x in read(INVENTORY)['units'] if x['id']=='kant-1784:u0015')
    return dict(status='foreign_attitude_obstacles_and_necessary_countereffort_partial',source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[890,1049],text=u['text'][890:1049]),
        interpretation=LIMITS,whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,new_verified_characters=0,
        unresolved=['本文の統治圏・経路・モデルと関連経過の設定','先行自由例と同じ精神への照応','auch/selbst・全文帰属と通読'],
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in (LIBRARY,BASIS,DOC,INVENTORY,*PRIORS,'data/eighth-paragraph-source-reading-v1.json')})
@lru_cache(None)
def structure_checks():
    c=catalog();assert not c.document['statements'];assert len(parents()[2].document['statements'])==114
    for old in parents():
        for n,e in c.entries.items():
            if n in old.entries:assert e['declaration']==old.entries[n]['declaration'] and e['meaning_ja']==old.entries[n]['meaning_ja']
    for p in PRIORS:validate_hashes(ROOT,read(p)['source_sha256'])
    validate_hashes(ROOT,read(BASIS)['import_source_sha256'])
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b
    assert read(READING)==reading_record()
    for notation in ('compact','full'):
        t=format_graph(c.document,notation);assert parse(t)==parse(transcribe(t,alphabet='v2'))==c.document
    t=format_graph(c.document,'compact');ranks={}
    for name in ('r57a','r57b','r57e','r57i'):
        for rank,label in enumerate(('','b','c','d','e')):
            try:parse(t+'q[e[r '+label+'[p '+name+']][r '+label+'[p '+name+']]].')
            except ValueError as e:assert 'Quoted evaluation' in str(e),str(e)
            else:ranks[name]=rank;break
    assert len(ranks)==4
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),unchanged_manuscript_statements=114,inherited_meanings_preserved=True,
        roundtrips=True,minimum_quote_ranks=ranks,new_verified_characters=0)
def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))
def build_report():
    results={}
    for n,f in (('candidate_goal',candidate_goal_checks),('necessity',necessity_checks),('counteractivity',counteractivity_checks),('plural_models',plural_model_checks),('scope',scope_checks),('combined',combined_checks),('structure',structure_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(catalog().source_sha256)|{LIBRARY,BASIS,DOC,READING,INDEX,INVENTORY,*PRIORS,'data/eighth-paragraph-source-reading-v1.json',
        'scripts/compose_attitude_obstacle_struggle.py','scripts/check_attitude_obstacle_struggle.py','tests/test_attitude_obstacle_struggle.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/compose_paired_influence.py','scripts/compose_social_attitude_paths.py',
        'scripts/check_pastoral_roles.py','scripts/check_motive_causes.py'}
    return dict(status='foreign_attitude_plural_obstacles_countereffort_and_necessity_checked_partial',document=LIBRARY,**results,
        alignment=dict(**read(READING)['source'],statements=[],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
