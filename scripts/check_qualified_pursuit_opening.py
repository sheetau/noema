"""Check nonfactive goals, practical liberty and newly opened opportunities."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import Content,FunctionValue
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_qualified_pursuit_opening import ROOT,LIBRARY,BASIS,PRIMITIVES,MEANINGS,LIMITS,parents,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown
from scripts.check_covenant_nullity import normalized

DOC='docs/qualified-pursuit-opening-v1.md';READING='data/qualified-pursuit-opening-reading-v1.json';REPORT='reports/qualified-pursuit-opening-v1.json'
INVENTORY='artifacts/written-units-v1/kant-1784.json'
PRIORS=('reports/religious-collective-assessment-v1.json','reports/judgment-performance-quality-v1.json','reports/sixth-paragraph-v1.json')
SOURCES=('artifacts/judgment-performance-quality-v1/kant-aa08-040.html','artifacts/royal-writing-oversight-v1/page-491.jpg')
PEOPLE=('alice','bob');WORKS=('work','otherwork')
DOMAIN=(*PEOPLE,*WORKS,'topic','matter','authority','role','opening','other','group','epoch')
SCENES=('reference','candidate','past','now','future');TIMES=SCENES[2:]
EXTRA=''.join('r z'+n+'[] '+('a' if n in DOMAIN else 'd')+'.' for n in (*DOMAIN,*SCENES))+'r zprocess[a a] a.'
ARGS='k zalice[] k zwork[] k ztopic[] k znow[] k znow[]'
OPEN='k zgroup[] k ztopic[] k zreference[] k zcandidate[] k zpast[] k znow[] p zprocess'
FRAME='k zalice[] k zgroup[] k zepoch[] k zreference[] k zcandidate[] k znow[]'
SOURCE=FRAME+' k ztopic[] k zpast[] p zprocess'
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(roots,query,boundaries=(),names=False):
    d=deepcopy(catalog().document);extra=EXTRA
    if names:
        ds=[]
        for x in d['declarations']:
            if x['name']=='h223h':
                text='r znow[] d.d h223h[reference d] i[d][r[k znow[]]].'
                ds.extend(parse(format_graph(dict(d,declarations=ds,statements=[]),'compact')+text)['declarations'][len(ds):])
            else:ds.append(x)
        d['declarations']=ds;extra=extra.replace('r znow[] d.','')
    for x in d['declarations']:
        if x['name'] in boundaries:x.update(kind='primitive',parameters=[p['sort'] for p in x['parameters']]);x.pop('body')
    d.update(declarations=closure(d,roots),statements=[])
    return parse(format_graph(d,'compact')+extra+query)
def run(d,v):return evaluate(d,v,DOMAIN,SCENES,True)
def rejects(d,v):
    try:run(d,v)
    except ValueError as e:assert 'Unknown' in str(e)
    else:raise AssertionError('Unknown accepted')
def content(points):return Content(SCENES,tuple(s in points for s in SCENES))
def pair(p,w):return (p,w) in tuple(zip(PEOPLE,WORKS,strict=True))
def base(d):
    v={x['name']:unknown for x in d['declarations'] if x['kind']=='primitive'}
    v.update({'z'+n:lambda n=n:n for n in (*DOMAIN,*SCENES)})
    def aim(p,w,goal,bindings,anchor,point):
        return pair(p,w) and normalized((goal,bindings,anchor,point))==(('r5to',1),(p,'topic'),'now','future')
    v.update(aa=lambda p:p in PEOPLE,h26j7=lambda t,a:(t,a)==('topic','now'),
        h26ka=lambda p,t,m,a:p in PEOPLE and (t,m,a)==('topic','matter','now'),
        h26fx=lambda p,w,m,a:pair(p,w) and (m,a)==('matter','now'),
        h26hf=aim,h26kd=lambda p,s,a:p in PEOPLE and (s,a)==('authority','now'),h26ke=lambda p,a:'role',
        h237z=lambda *a:False,h26ho=lambda *a:False,
        dg=lambda w,s:w in WORKS and s=='future' or (w,s)==('opening','now'),
        df=lambda p,w,s:pair(p,w) and s=='future',ae=lambda p,w,s:pair(p,w) and s=='now',
        af=lambda p,w,s,t:pair(p,w) and (s,t)==('now','future'),
        h26kf=lambda p,w,t,a,s:pair(p,w) and (t,a)==('topic','now') and s in ('past','now'),
        h246c=lambda g,p,r:(g,r)==('group','reference') and p in PEOPLE,
        h257z=lambda r,c,p:(r,c)==('reference','candidate') and p in TIMES,
        ic=lambda a,b,c:c=='candidate' and a in TIMES and b in TIMES and TIMES.index(a)<TIMES.index(b),
        h26aa=lambda e,r:(e,r)==('epoch','reference'),h26ab=lambda e,r,c,p:(e,r,c)==('epoch','reference','candidate') and p in TIMES,
        h256o=lambda p,c,s:p in PEOPLE and c=='candidate' and s in TIMES,
        zprocess=lambda p,w:'opening',ag=lambda process,a,b:(process,a,b)==('opening','past','now'),
        la=lambda p,process,a,b:p in PEOPLE and (process,a,b)==('opening','past','now'))
    return v

@lru_cache(None)
def goal_checks():
    q='q[t[k r5to[l[a][k zalice[] k ztopic[]] k znow[]]][k zfuture[]]].'
    d=fixture(('r5to',),q,('r5tb',),True);rows={};calls=[]
    for attained in (False,True):
        v=base(d)
        def ability(topic,anchor,code):
            calls.append(normalized((topic,anchor,code)))
            valid=(topic,anchor)==('topic','now') and normalized(code)==('znow',0)
            return FunctionValue(('individual',),'content',lambda p:content({'future'} if attained and valid and p=='alice' else set()))
        v['r5tb']=ability;got=run(d,v);assert got==[attained];rows[str(attained)]=got
    # bind quantifies over all candidate individuals; eager evaluation also
    # calls the boundary for candidates excluded by the position constraints.
    assert ('topic','now',('znow',0)) in calls
    for foreign in ('person','topic'):
        v=base(d)
        def other_ability(topic,anchor,code):
            return FunctionValue(('individual',),'content',lambda p:content({'future'} if
                (p,topic,anchor)==('bob' if foreign=='person' else 'alice','matter' if foreign=='topic' else 'topic','now') else set()))
        v['r5tb']=other_ability;assert run(d,v)==[False]
    # The same goal adapter rejects a reference that names a different anchor.
    d2=fixture(('r5to',),q.replace('] k znow[]','] k zpast[]'),('r5tb',),True)
    v=base(d2);v['r5tb']=ability;assert run(d2,v)==[False]
    for bindings in ('l[a][]','l[a][k zalice[]]','l[a][k zalice[] k ztopic[] k zwork[]]'):
        bad=fixture(('r5to',),q.replace('l[a][k zalice[] k ztopic[]]',bindings),('r5tb',),True)
        v=base(bad);v['r5tb']=ability;assert run(bad,v)==[False]
    v=base(d);v['r5tb']=unknown;rejects(d,v)
    return dict(executed_goal_values=rows,same_person_topic_anchor_and_reference=True,exact_two_bindings=True,
        boundaries=['r5tb'],ability_native_evidence=PRIORS[0],unknown_rejected=True)

@lru_cache(None)
def pursuit_checks():
    q='q[k r5tq['+ARGS.replace('k znow[] k znow[]','k znow[] k zfuture[]')+']].'
    d=fixture(('r5tq',),q);rows={}
    for variant in ('baseline','not_occurring','other_participant','nonstudy','other_matter','nonreligious','other_goal_person','other_goal_topic','other_goal_anchor','other_goal_work','other_goal_point','other_goal_description'):
        v=base(d)
        if variant=='not_occurring':v['dg']=lambda *a:False
        if variant=='other_participant':v['df']=lambda p,w,s:p=='bob'
        if variant=='nonstudy':v['h26fx']=lambda *a:False
        if variant=='other_matter':v['h26ka']=lambda p,t,m,a:m=='other'
        if variant=='nonreligious':v['h26j7']=lambda *a:False
        if variant.startswith('other_goal'):
            wanted={'other_goal_person':('bob','topic'),'other_goal_topic':('alice','matter')}.get(variant,('alice','topic'))
            v['h26hf']=lambda p,w,g,b,a,s:normalized((g,b,a,s))==((('r5tr' if variant=='other_goal_description' else 'r5to'),1),wanted,'past' if variant=='other_goal_anchor' else 'now','now' if variant=='other_goal_point' else 'future') and w==('otherwork' if variant=='other_goal_work' else 'work')
        got=run(d,v);assert got==[variant=='baseline'],(variant,got);rows[variant]=got[0]
        assert v.get('h223h',unknown) is unknown and v.get('r5tb',unknown) is unknown
    for n in ('h26hf','dg','df','h26fx'):
        v=base(d);v[n]=unknown;rejects(d,v)
    return dict(cases=rows,goal_not_executed_by_pursuit=True,no_achieved_ability_inferred=True,unknown_rejected=True)

@lru_cache(None)
def opportunity_checks():
    d=fixture(('r5tv',),'q[k r5tv['+ARGS+']].');rows={}
    for variant in ('baseline','required','prohibited','other_role_rule','other_work_rule','other_source_rule','active_interference','inactive_interference','other_target_interference','unavailable','empty_results','foreign_result_work','no_result_pursuit','no_current_work'):
        v=base(d)
        if variant in ('required','prohibited','other_role_rule','other_work_rule','other_source_rule'):
            def norm(source,p,role,target,bindings,anchor,sign,point):
                return (source,p,role,normalized(target),normalized(bindings),anchor,sign,point)==(
                    'other' if variant=='other_source_rule' else 'authority','alice','other' if variant=='other_role_rule' else 'role',('r5ts',1),
                    ('alice','otherwork' if variant=='other_work_rule' else 'work','topic','role'),'now',variant=='required','now')
            v['h237z']=norm
        if variant in ('active_interference','inactive_interference','other_target_interference'):
            v['h26ho']=lambda event,p,target,b,a,s:(event,p,normalized(target),normalized(b),a,s)==('opening','alice',('r5ts',1),('alice','otherwork' if variant=='other_target_interference' else 'work','topic','role'),'now','past' if variant=='inactive_interference' else 'now')
        if variant=='unavailable':v['ae']=lambda *a:False
        if variant=='empty_results':v['af']=lambda *a:False
        if variant=='foreign_result_work':v['df']=lambda p,w,s:(p,w,s)==('alice','otherwork','future')
        if variant=='no_result_pursuit':v['h26hf']=lambda *a:False
        if variant=='no_current_work':
            old=v['dg'];v['dg']=lambda w,s:s!='now' and old(w,s)
        want=variant in ('baseline','other_role_rule','other_work_rule','other_source_rule','inactive_interference','other_target_interference','no_current_work')
        got=run(d,v);assert got==[want],(variant,got);rows[variant]=got[0]
    for n in ('h26kd','h237z','h26ho','ae','af','h26hf'):
        v=base(d);v[n]=unknown;rejects(d,v)
    return dict(cases=rows,no_positive_permission_required=True,current_execution_and_goal_achievement_not_required=True,same_possible_result=True,unknown_rejected=True)

@lru_cache(None)
def opening_checks():
    d=fixture(('r5tz','r5t3','r5t4'),'q[k r5tz['+OPEN+']].q[k r5t3['+SOURCE+']].'+''.join('q[t[k r5t4['+SOURCE+']][k z'+s+'[]]].' for s in ('past','now','future')));rows={}
    for variant in ('baseline','old_opportunity','unassessed_past','one_person_lacks_new_opportunity','wrong_transition','wrong_affected','not_opening_now','empty_group','missing_current_person','wrong_current','wrong_subject','wrong_history'):
        v=base(d);want=[False]*5
        if variant=='baseline':want=[True]*5
        if variant=='old_opportunity':v['ae']=lambda p,w,s:pair(p,w) and s in ('past','now');v['af']=lambda p,w,s,t:pair(p,w) and s in ('past','now') and t=='future'
        if variant=='unassessed_past':v['h26kf']=lambda p,w,t,a,s:s=='now'
        if variant=='one_person_lacks_new_opportunity':v['ae']=lambda p,w,s:(p,w,s)==('alice','work','now')
        if variant=='wrong_transition':v['ag']=lambda *a:False
        if variant=='wrong_affected':v['la']=lambda p,*a:p=='alice'
        if variant=='not_opening_now':v['dg']=lambda w,s:w in WORKS and s=='future'
        if variant=='empty_group':v['h246c']=lambda *a:False
        if variant=='missing_current_person':v['h246c']=lambda g,p,r:(g,p,r)==('group','alice','reference');want=[True,False,False,False,False]
        if variant=='wrong_current':v['zepoch']=lambda:'other';want=[True,False,False,False,False]
        if variant=='wrong_subject':v['ztopic']=lambda:'other'
        if variant=='wrong_history':v['zcandidate']=lambda:'reference'
        got=run(d,v);assert got==want,(variant,got);rows[variant]=got
    for n in ('h26kf','ag','la','h246c','h256o'):
        v=base(d);v[n]=unknown;rejects(d,v)
    return dict(cases=rows,native_candidate_pursuit_opportunity_transition_and_current_population=True,outer_point_does_not_rebind_current=True,no_single_shared_performance_required=True,unknown_rejected=True)

def reading_record():
    u=next(x for x in read(INVENTORY)['units'] if x['id']=='kant-1784:u0014');start=u['text'].index('Allein,');end=u['text'].index(' In diesem Betracht')
    return dict(status='qualified_pursuit_and_opening_dependency_partial',source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[start,end],text=u['text'][start:end]),interpretation=LIMITS,
        references=[dict(url='https://korpora.org/kant/aa08/040.html',path=SOURCES[0],observation_ja='同じ宗教的能力へのdahin、自由な本人の取り組みと新規開放を、後続の障害漸減・徴候と区別。')],
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,new_verified_characters=0,
        unresolved=['同じ現在人口・目標への障害漸減','場の比喩と現在進行の提示','自己責任の未成熟からの離脱との言い換え','徴候と著者帰属','第一文の条件付き問答','第二文の甚だしい不足','後続文と段落通読'],
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in (LIBRARY,BASIS,DOC,INVENTORY,*PRIORS,*SOURCES)})
@lru_cache(None)
def structure_checks():
    c=catalog()
    for old in parents():
        for n,e in old.entries.items():
            if n in c.entries:assert c.entries[n]['declaration']==e['declaration'] and c.entries[n]['meaning_ja']==e['meaning_ja']
    assert not c.document['statements'] and len(parents()[1].document['statements'])==108
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b
    for p in PRIORS:validate_hashes(ROOT,read(p)['source_sha256'])
    assert read(READING)==reading_record()
    for notation in ('compact','full'):
        s=format_graph(c.document,notation);assert parse(s)==parse(transcribe(s,alphabet='v2'))==c.document
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),new_statements=0,main_statements_preserved=108,roundtrips=True,new_verified_characters=0)
def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))
def build_report():
    results={}
    for n,f in (('goal',goal_checks),('pursuit',pursuit_checks),('opportunity',opportunity_checks),('opening',opening_checks),('structure',structure_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(catalog().source_sha256)|{READING,DOC,INVENTORY,*PRIORS,*SOURCES,
        'scripts/compose_qualified_pursuit_opening.py','scripts/check_qualified_pursuit_opening.py','tests/test_qualified_pursuit_opening.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/compose_protected_remarks.py','scripts/compose_present_epoch_assessment.py',
        'scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/check_covenant_nullity.py'}
    return dict(status='qualified_pursuit_opening_dependency_checked',document=LIBRARY,**results,
        alignment=dict(**read(READING)['source'],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,
        verified_full_units={'kant-1784':0,'einstein-1905':0},source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
