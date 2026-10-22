"""Check public human agency, personal effects, collective release and priority."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_government_release import ROOT,LIBRARY,BASIS,GOAL,PRIMITIVES,MEANINGS,LIMITS,parents,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown

DOC='docs/government-release-v1.md';READING='data/government-release-reading-v1.json'
INVENTORY='artifacts/written-units-v1/kant-1784.json';INDEX='data/semantic-review-index-v196.json'
PRIORS=('reports/conscience-choice-v1.json','reports/grateful-regard-v1.json')
SOURCES=('data/eighth-paragraph-source-reading-v1.json','artifacts/government-release-v1/dwb-entschlagen.html',
    'artifacts/judgment-performance-quality-v1/kant-aa08-040.html')
DOMAIN=('actor','clerk','person','already','government','othergovernment','community','othercommunity','group','matter','judgment','role','activity','otheractivity','other')
SCENES=('reference','candidate','early','before','acted','last','now','later')
ORDER=('early','before','acted','last','now','later')
def z(n):return 'k z'+n+'[]'
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def identity(c):return c.rank,json.loads(c.syntax)
def names(ns):return ' '.join(z(n) for n in ns)
CODE='k r5zp['+' '.join('r['+z(n)+']' for n in ('government','community','reference'))+']'
COMMON='k r5zx[r['+z('reference')+']]'
SAVE='q[k zsave['+CODE+']].'
EPISODE=names(('actor','activity','government','group','community','reference','candidate','before','acted','last'))
PERSONAL=EPISODE.replace(z('group'),z('person'))
SHORT=names(('actor','activity','government','group','community','reference','candidate','last'))
CHOICE=names(('government','person','community','matter','judgment','reference','last'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(roots,query,boundaries=(),state_boundary=False):
    d=deepcopy(catalog().document)
    for x in d['declarations']:
        if x['name'] in boundaries:
            x.update(kind='primitive',parameters=[p['sort'] for p in x['parameters']]);x.pop('body')
    extra=''.join('r z'+n+'[] '+('a' if n in DOMAIN else 'd')+'.' for n in (*DOMAIN,*SCENES))
    extra+='r znamepick[a '+' '.join('i[a]' for _ in DOMAIN)+'] i[a].r zrefpick[d '+' '.join('i[d]' for _ in SCENES)+'] i[d].'
    extra+='d h223g[item a] i[a][k znamepick[v item '+' '.join('r['+z(n)+']' for n in DOMAIN)+']].'
    extra+='d h223h[point d] i[d][k zrefpick[v point '+' '.join('r['+z(n)+']' for n in SCENES)+']].'
    extra+='r zsave['+GOAL+'] c.r zassessed[a d] c.d zothergoal[group a] e[b point[e[v group][v group]]].'
    if state_boundary:
        extra+='r zfree[a a a d d] c.'
        stub='d zstub[government a community a reference d] h[a] e[i[person a][b point[k zfree[v government v person v community v reference v point]]]].'
        body=parse('p:'+extra+stub)['declarations'][-1]['body']
        next(x for x in d['declarations'] if x['name']=='r5zn')['body']=body
    prefix=parse('p:'+extra);replacements={x['name']:x for x in prefix['declarations'] if x['name'] in ('h223g','h223h')}
    additions=[x for x in prefix['declarations'] if x['name'] not in replacements]
    d['declarations']=additions+[replacements.get(x['name'],x) for x in d['declarations']]
    d.update(declarations=closure(d,(*roots,*(x['name'] for x in additions))),statements=[])
    return parse(format_graph(d,'compact')+query)
def run(d,v,domain=DOMAIN):return evaluate(d,v,domain,SCENES,True)
def rejects(d,v,domain=DOMAIN):
    try:run(d,v,domain)
    except ValueError as e:assert 'Unknown' in str(e),str(e)
    else:raise AssertionError('Unknown accepted')
def base(d):
    v={x['name']:unknown for x in d['declarations'] if x['kind']=='primitive'};saved={}
    v.update({'z'+n:lambda n=n:n for n in (*DOMAIN,*SCENES)})
    v.update(aa=lambda p:p in ('actor','clerk','person','already','other'),
        znamepick=lambda p,*cs:cs[DOMAIN.index(p)],zrefpick=lambda p,*cs:cs[SCENES.index(p)],
        zsave=lambda c:saved.update(code=identity(c)) is None,
        h237n=lambda g,c,p:(g,c)==('government','community'),h256s=lambda g,c,p:(g,c)==('government','community'),
        h246c=lambda g,p,r:(g,r)==('group','reference') and p in ('person','already'),
        h257z=lambda r,c,p:(r,c)==('reference','candidate') and p in ORDER,
        ic=lambda a,b,c:c=='candidate' and a in ORDER and b in ORDER and ORDER.index(a)<ORDER.index(b),
        r5y3=lambda p,m,r:(p,m,r)==('person','matter','reference'),
        h26nx=lambda p,m,j,r:(p,m,j,r)==('person','matter','judgment','reference'),
        h26ny=lambda p,c,r:'role' if (p,c,r)==('person','community','reference') else 'other',
        h26nz=lambda g,p,c,m,j,r,t:(g,p,c,m,j,r)==('government','person','community','matter','judgment','reference'),
        h237z=lambda *a:False,h245c=lambda *a:True,h26ho=lambda *a:False,
        dg=lambda a,p:(a,p)==('activity','last'),df=lambda p,a,t:(p,a,t)==('clerk','activity','last'),
        h26n2=lambda p,a,g,t:(p,a,g,t)==('clerk','activity','government','last'),
        zfree=lambda g,p,c,r,t:(g,c,r)==('government','community','reference') and p in ('person','already') and (t=='last' or p=='already'),
        zassessed=lambda *a:True)
    return v,saved

@lru_cache(None)
def government_checks():
    q='q[k r5zm['+CHOICE+']].q[k r5zr['+names(('government','person','community','reference','last'))+']].'
    q+='q[t[c[k r5zn['+names(('government','community','reference'))+']]['+z('person')+']]['+z('last')+']].'
    d=fixture(('r5zm','r5zr','r5zn'),q,('r5y3',));rows=[]
    for occurred,participated,official in product((False,True),repeat=3):
        v,_=base(d)
        v.update(dg=lambda a,t:occurred and (a,t)==('activity','last'),
            df=lambda p,a,t:participated and (p,a,t)==('clerk','activity','last'),
            h26n2=lambda p,a,g,t:official and (p,a,g,t)==('clerk','activity','government','last'),
            h26ho=lambda a,p,c,b,r,t:(a,p,identity(c),b.items,r,t)==('activity','person',(1,dict(kind='function_ref',symbol='r5y7')),
                ('person','community','matter','judgment','role'),'reference','last'))
        got=run(d,v);active=occurred and participated and official;assert got==[not active,active,not active]
        assert not v['aa']('government');rows.append(dict(occurred=occurred,participated=participated,official=official,result=got))
    for pos in range(4):
        v,_=base(d);old=v['h26n2']
        def wrong(*a):
            b=list(a);b[pos]='other' if pos<3 else 'now';return old(*b)
        v['h26n2']=wrong;v['h26ho']=lambda *a:True;assert run(d,v)==[True,False,True]
    for n in ('h237n','h256s'):
        v,_=base(d);v[n]=lambda *a:False;assert run(d,v)==[True,False,False]
    v,_=base(d);v['h245c']=lambda *a:False;assert run(d,v)==[False,False,False] # No positive permission is not active tutelage.
    for sign in (False,True):
        v,_=base(d);v['h237z']=lambda g,p,role,c,b,r,s,t:s==sign;assert run(d,v)==[False,True,False]
    for n in ('h26n2','h26ho','dg','df','h237n','h256s'):
        v,_=base(d);v[n]=unknown;rejects(d,v)
    return dict(eight_public_agency_cases=rows,organization_is_not_human=True,subordinate_official_interference_detected=True,
        all_four_official_capacity_arguments_checked=True,unpermitted_distinct_from_active_tutelage=True,unknown_rejected=True,
        boundary='Only the previously evaluated conscience classifier r5y3 is a scalar truth boundary. Government, public human participation, scopes, norms and interference execute natively.')

def episode_model(d):
    v,saved=base(d)
    v.update(ag=lambda a,f,l:(a,f,l)==('activity','before','last'),
        la=lambda p,a,f,l:(p,a,f,l)==('person','activity','before','last'),
        dg=lambda a,t:(a,t)==('activity','acted'),df=lambda p,a,t:(p,a,t)==('actor','activity','acted'),
        h26n2=lambda p,a,g,t:(p,a,g,t)==('actor','activity','government','acted'),
        g3=lambda a,p,c,t:(a,p,identity(c),t)==('activity','person',saved['code'],'last'))
    return v,saved
@lru_cache(None)
def episode_checks():
    q=SAVE+'q[k r5zs['+PERSONAL+']].q[k r5zv['+names(('actor','activity','government','person','community','reference','candidate','now'))+']].'
    d=fixture(('r5zp','r5zs','r5zv'),q,state_boundary=True);rows={}
    for case in ('baseline','already_free','not_free_after','no_process','not_affected','no_cause','other_beneficiary','other_state','no_action','no_actor','private_action','action_after_result','cyclic_order','wrong_government_kind'):
        v,_=episode_model(d)
        if case=='already_free':v['zfree']=lambda g,p,c,r,t:(g,p,c,r)==('government','person','community','reference')
        if case=='not_free_after':v['zfree']=lambda *a:False
        if case=='no_process':v['ag']=lambda *a:False
        if case=='not_affected':v['la']=lambda *a:False
        if case=='no_cause':v['g3']=lambda *a:False
        if case=='other_beneficiary':v['g3']=lambda a,p,c,t:(a,p,t)==('activity','already','last')
        if case=='other_state':v['g3']=lambda a,p,c,t:identity(c)==(0,dict(kind='function_ref',symbol='zothergoal'))
        if case=='no_action':v['dg']=lambda *a:False
        if case=='no_actor':v['df']=lambda *a:False
        if case=='private_action':v['h26n2']=lambda *a:False
        if case=='action_after_result':v['dg']=lambda a,t:(a,t)==('activity','later');v['df']=lambda p,a,t:(p,a,t)==('actor','activity','later')
        if case=='cyclic_order':v['ic']=lambda a,b,c:c=='candidate' and a!=b and a in ORDER and b in ORDER
        if case=='wrong_government_kind':v['h256s']=lambda *a:False
        got=run(d,v)
        personal=case=='baseline';benefit=case in ('baseline','already_free','no_process','not_affected','private_action','wrong_government_kind')
        assert got==[True,personal,benefit],(case,got);rows[case]=got[-2:]
    for n in ('ag','la','g3','h26n2','h257z','ic','zfree'):
        v,_=episode_model(d);v[n]=unknown;rejects(d,v)
    for n in ('government','community','reference'):
        v,_=episode_model(d)
        if n=='reference':v['zrefpick']=lambda p,*cs:cs[SCENES.index('later' if p==n else p)]
        else:v['znamepick']=lambda p,*cs:cs[DOMAIN.index('other' if p==n else p)]
        assert run(d,v)==[True,False,False]
    return dict(cases=rows,action_time_between_same_transition_endpoints=True,individual_not_group_is_causal_beneficiary=True,
        exact_same_freedom_code=True,result_need_not_persist_to_present=True,three_names_checked=True,unknown_rejected=True,
        boundary='The separately checked r5zn state uses a native function body with exact government/person/community/reference/time truth boundary; transition, public release act and causal benefit execute natively.')

@lru_cache(None)
def native_episode_checks():
    domain=('actor','person','government','community','group','matter','judgment','role','activity','other')
    q=SAVE+'q[k r5zt['+EPISODE+']].'
    d=fixture(('r5zp','r5zt'),q,('r5y3',))
    v,saved=episode_model(d)
    v['h246c']=lambda g,p,r:(g,p,r)==('group','person','reference')
    v['h237z']=lambda g,p,role,c,b,r,sign,t:(g,p,role,identity(c),b.items,r,sign,t)==(
        'government','person','role',(1,dict(kind='function_ref',symbol='r5y6')),('person','matter','judgment'),'reference',False,'before')
    # The same government withdraws its earlier prohibition; conduct stays quoted.
    assert run(d,v,domain)==[True,True]
    v['h26n2']=lambda *a:False;assert run(d,v,domain)==[True,False]
    for n in ('ab','ac','fc','ad'):assert v[n] is unknown
    return dict(native_government_norm_change_transition_cause_and_collective_release=True,
        same_official_capacity_required=True,actual_reasoning_not_executed=True,
        boundary='Only the unchanged conscience classifier r5y3 uses its previously tested scalar boundary. Freedom, prior prohibition, same-event individual transition and collective release execute together natively.')

@lru_cache(None)
def collective_checks():
    d=fixture(('r5zt',),'q[k r5zt['+EPISODE+']].',('r5ze','r5zr','r5zs'),True)
    def model():
        v,_=base(d)
        v.update(r5ze=lambda g,p,c,r,t:(g,c,r,t)==('government','community','reference','before') and p in ('person','already'),
            r5zr=lambda g,p,c,r,t:(g,p,c,r,t)==('government','person','community','reference','before'),
            r5zs=lambda a,x,g,p,c,r,h,f,t,l:(a,x,g,p,c,r,h,f,t,l)==('actor','activity','government','person','community','reference','candidate','before','acted','last'))
        return v
    rows={}
    for case in ('baseline','missing_person_effect','previously_free_loses_freedom','missing_prior_assessment','no_active_tutelage','empty_group','nonhuman_member'):
        v=model()
        if case=='missing_person_effect':v['r5zs']=lambda *a:False
        if case=='previously_free_loses_freedom':
            old=v['zfree'];v['zfree']=lambda g,p,c,r,t:old(g,p,c,r,t) and not(p=='already' and t=='last')
        if case=='missing_prior_assessment':v['r5ze']=lambda g,p,c,r,t:p=='person'
        if case=='no_active_tutelage':v['r5zr']=lambda *a:False
        if case=='empty_group':v['h246c']=lambda *a:False
        if case=='nonhuman_member':v['aa']=lambda p:p=='person'
        got=run(d,v);assert got==[case=='baseline'];rows[case]=got[0]
    for pos in range(10):
        v=model();old=v['r5zs']
        def wrong(*a):
            b=list(a);b[pos]='other' if pos<5 else 'later';return old(*b)
        v['r5zs']=wrong;assert run(d,v)==[False],pos
    for n in ('r5ze','r5zr','r5zs','zfree'):
        v=model();v[n]=unknown;rejects(d,v)
    return dict(cases=rows,all_newly_free_people_share_one_event=True,already_free_people_preserved_not_released_again=True,
        all_ten_episode_bindings_checked=True,unknown_rejected=True,
        boundary='The already checked personal state, prior assessment, active tutelage and personal transition are exact-argument boundaries. Collective quantification and final group freedom execute natively.')

@lru_cache(None)
def first_checks():
    domain=('actor','other','activity','otheractivity','government','othergovernment','community','othercommunity','group')
    generic=names(('actor','activity','group','reference','candidate','now','last'))+' p zassessed'
    q='q[k r5zz['+generic+']].q[k r5z2['+SHORT+' '+z('now')+' p zassessed]].'
    d=fixture(('r5zz','r5z2'),q,('r5zu',));rows={}
    basekey=('actor','activity','government','group','community','reference','candidate','last')
    for case in ('baseline','earlier_other_government','earlier_same_person','simultaneous_other','later_other','missing_comparison_assessment','only_later_unassessed','missing_selected_event','no_achievement','anchor_before_result','cyclic_order'):
        v,_=base(d);events={basekey}
        if case in ('earlier_other_government','simultaneous_other','later_other','earlier_same_person'):
            events.add(('actor' if case=='earlier_same_person' else 'other','otheractivity','othergovernment','group','othercommunity','reference','candidate',
                'last' if case=='simultaneous_other' else 'later' if case=='later_other' else 'early'))
        if case=='missing_selected_event':events={('actor','activity','othergovernment','group','othercommunity','reference','candidate','last')}
        if case=='no_achievement':events=set()
        if case=='missing_comparison_assessment':v['zassessed']=lambda a,p:(a,p)!=('other','early')
        if case=='only_later_unassessed':v['zassessed']=lambda a,p:p!='later'
        if case=='anchor_before_result':v['znow']=lambda:'before'
        if case=='cyclic_order':v['ic']=lambda a,b,c:c=='candidate' and a!=b and a in ORDER and b in ORDER
        v['r5zu']=lambda *a:a in events
        got=run(d,v,domain);ok=case in ('baseline','simultaneous_other','later_other','only_later_unassessed','missing_selected_event')
        assert got==[ok,ok and case!='missing_selected_event'],(case,got);rows[case]=got
    for n in ('r5zu','zassessed'):
        v,_=base(d);v['r5zu']=lambda *a:a==basekey;v[n]=unknown;rejects(d,v,domain)
    # The adapter rejects a different group or a different common description.
    for target,goal,expected in (('group',COMMON,True),('other',COMMON,False),('group','r[p zothergoal]',False)):
        q='q[c[k r5zy['+names(('group','reference','candidate'))+']]['+names(('actor','activity',target))+' '+goal+' '+z('last')+']].'
        changed=fixture(('r5zy','r5zx'),q,('r5zu',));v,_=base(changed);v['r5zu']=lambda *a:a==basekey
        assert run(changed,v,domain)==[expected]
    return dict(cases=rows,other_governments_and_same_actor_prior_events_compared=True,simultaneous_achievers_allowed=True,
        not_all_future_assessment_required=True,exact_common_description_and_group=True,selected_event_kept=True,unknown_rejected=True,
        boundary='Only the separately composed concrete release r5zu is a scalar event boundary here. Its government/community/end-point arguments remain explicit; rob and the achievement adapter execute natively.')

def reading_record():
    u=next(x for x in read(INVENTORY)['units'] if x['id']=='kant-1784:u0015');start=u['text'].index('der zuerst');end=u['text'].index('zu bedienen.')+len('zu bedienen.')
    return dict(status='government_side_release_and_first_achievement_dependency',
        source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[start,end],text=u['text'][start:end]),
        interpretation=LIMITS,evidence=[dict(path=SOURCES[1],url='https://www.dwds.de/wb/dwb/entschlagen',retrieved='2026-10-23',
            observation='第三義の対象から解き放す用法と、政府が精神を束縛から解く例を参照する。反射的な辞退又は単なる打撃の語義にしない。'),
            dict(path=SOURCES[2],url='https://korpora.org/kant/aa08/040.html',
            observation='33–35行の政府側という限定と良心事項の自由。20–25行の未到達の能力判断に照らし、政府側の解放から全員の実際の能力取得へ飛躍しない。')],
        unresolved=['原文の人類範囲・解放時の人口と同じ君主の政府・共同体・役職の設定','全比較者の評価の供給と主張の解釈、称揚根拠・恩恵・感謝・全基準への束縛',
            'wenigstens等の提示・著者帰属・sondern・一文全体と後続'],
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,new_verified_characters=0,
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in (LIBRARY,BASIS,DOC,INVENTORY,*PRIORS,*SOURCES)})
@lru_cache(None)
def structure_checks():
    c=catalog()
    for p in parents():
        for n,e in c.entries.items():
            if n in p.entries:assert e['declaration']==p.entries[n]['declaration'] and e['meaning_ja']==p.entries[n]['meaning_ja']
    assert not c.document['statements'] and len(parents()[2].document['statements'])==112
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b
    for p in PRIORS:validate_hashes(ROOT,read(p)['source_sha256'])
    assert read(READING)==reading_record()
    assert c.entries['r5zp']['declaration']['result'].get('rank',0)==0
    for notation in ('compact','full'):
        s=format_graph(c.document,notation);assert parse(s)==parse(transcribe(s,alphabet='v2'))==c.document
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),new_statements=0,main_statements_preserved=112,
        new_verified_characters=0,compact_full_v2_roundtrips=True,parent_meanings_preserved=True,existing_rob_reused=True)
def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))
def build_report():
    results={}
    for n,f in (('government',government_checks),('episode',episode_checks),('native_episode',native_episode_checks),('collective',collective_checks),('first',first_checks),('structure',structure_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(catalog().source_sha256)|{READING,DOC,INVENTORY,INDEX,*SOURCES,*PRIORS,
        'scripts/compose_government_release.py','scripts/check_government_release.py','tests/test_government_release.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py'}
    return dict(status='public_government_release_and_first_comparable_achievement_checked',document=LIBRARY,**results,
        alignment=dict(**read(READING)['source'],statements=[],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
