"""Check real quoted support states in causal one- and multi-step paths."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_social_attitude_paths import ROOT,LIBRARY,BASIS,STATE,MAPS,MEANINGS,PRIMITIVES,LIMITS,parents,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown

DOC='docs/social-attitude-paths-v1.md';READING='data/social-attitude-paths-reading-v1.json'
INDEX='data/semantic-review-index-v198.json';INVENTORY='artifacts/written-units-v1/kant-1784.json'
PRIORS=('reports/shared-liberty-policy-v1.json','reports/transmitted-profiles-v1.json','reports/communicated-attitudes-v1.json')
PEOPLE=('origin','relay','target','other')
STEPS=('first','second','third')
DOMAIN=(*PEOPLE,*STEPS,'actfirst','actsecond','actthird','procfirst','procsecond','procthird')
SCENES=('reference','zero','firstact','firstend','secondact','secondend','thirdact','thirdend','anchor')
STATE_CODE='k r56o[r[k zreference[]]]'
POLICY_CODE='k r56k[r[k zreference[]]]'
SAVE='q[k zsavestate['+STATE_CODE+']].q[k zsavepolicy['+POLICY_CODE+']].'
MAP_ARGS=' '.join('p z'+n for n,t in MAPS)
FRAME=STATE_CODE+' p zhistory p zbefore'
def z(n):return 'k z'+n+'[]'
def args(ns):return ' '.join(z(n) for n in ns)
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def codeid(c):return c.rank,json.loads(c.syntax)
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)

@lru_cache(None)
def fixture(roots,query):
    d=deepcopy(catalog().document)
    for row in d['declarations']:
        if row['name'] in ('r56l','r5xh'):
            row.update(kind='primitive',parameters=[p['sort'] for p in row['parameters']]);row.pop('body')
    extra=''.join('r z'+n+'[] '+('a' if n in DOMAIN else 'd')+'.' for n in (*DOMAIN,*SCENES))
    extra+=''.join('r z'+n+'[a] '+t+'.' for n,t in MAPS)
    extra+='r zhistory[d] c.r zbefore[d d] c.r zsavestate['+STATE+'] c.r zsavepolicy[i c[e]] c.'
    extra+='d zfirsts[person a] a['+z('first')+'].d ztails[person a] j[a][l[a]['+z('second')+']].'
    extra+='r zrefpick[d '+' '.join('i[d]' for n in SCENES)+'] i[d].'
    extra+='d h223h[point d] i[d][k zrefpick[v point '+' '.join('r['+z(n)+']' for n in SCENES)+']].'
    prefix=parse('p:'+extra);ns={r['name'] for r in prefix['declarations']}
    d['declarations']=prefix['declarations']+[r for r in d['declarations'] if r['name'] not in ns]
    d.update(declarations=closure(d,(*roots,'r56o','r56k',*ns)),statements=[])
    return parse(format_graph(d,'compact')+SAVE+query)
def run(d,v):return evaluate(d,v,DOMAIN,SCENES,True)[2:]
def rejects(d,v):
    try:run(d,v)
    except ValueError as e:assert 'Unknown' in str(e),str(e)
    else:raise AssertionError('Unknown accepted')

def model(d):
    v={r['name']:unknown for r in d['declarations'] if r['kind']=='primitive'};saved={}
    v.update({'z'+n:lambda n=n:n for n in (*DOMAIN,*SCENES)})
    rows={
        'first':dict(sender='origin',recipient='relay',activity='actfirst',process='procfirst',start='zero',acted='firstact',end='firstend'),
        'second':dict(sender='relay',recipient='target',activity='actsecond',process='procsecond',start='firstend',acted='secondact',end='secondend'),
        'third':dict(sender='target',recipient='other',activity='actthird',process='procthird',start='secondend',acted='thirdact',end='thirdend'),
    }
    holds={(p,t):False for p in DOMAIN for t in SCENES}
    for p,start in (('origin','zero'),('relay','firstend'),('target','secondend'),('other','thirdend')):
        for t in SCENES[SCENES.index(start):]:holds[p,t]=True
    v.update(zrefpick=lambda p,*cs:cs[SCENES.index(p)],zsavestate=lambda c:saved.update(state=codeid(c)) is None,
        zsavepolicy=lambda c:saved.update(policy=codeid(c)) is None,aa=lambda p:p in PEOPLE,
        r56l=lambda r:r=='reference',h26pg=lambda p,c,t:codeid(c)==saved['policy'] and holds[p,t],
        zhistory=lambda t:t!='reference',zbefore=lambda a,b:SCENES.index(a)<SCENES.index(b))
    for n,t in MAPS:v['z'+n]=lambda step,n=n:rows.get(step,rows['first'])[n]
    v['ag']=lambda pr,a,b:any((pr,a,b)==(r['process'],r['start'],r['end']) for r in rows.values())
    v['la']=lambda p,pr,a,b:any((p,pr,a,b)==(r['recipient'],r['process'],r['start'],r['end']) for r in rows.values())
    v['dg']=lambda a,t:any((a,t) in ((r['activity'],r['acted']),(r['process'],r['end'])) for r in rows.values())
    v['df']=lambda p,a,t:any((p,a,t)==(r['sender'],r['activity'],r['acted']) for r in rows.values())
    v['h6a']=lambda a,pr,t:any((a,pr,t)==(r['activity'],r['process'],r['acted']) for r in rows.values())
    v['h26ph']=lambda a,p,c,t:codeid(c)==saved['state'] and any((a,p,t)==(r['activity'],r['recipient'],r['end']) for r in rows.values())
    v['h26pi']=lambda a,p,c,t:codeid(c)==saved['state'] and any((a,p,t)==(r['activity'],r['sender'],r['acted']) for r in rows.values())
    return v,rows,holds,saved

def path_query(length=2,retained=True,fixed=False):
    tail='l[a]['+args(STEPS[1:length])+']';target=('relay','target','other')[length-1]
    common=args(('first',))+' '+tail+' '+args(('origin',target))+' '
    if fixed:return 'q[k r56v['+common+z('reference')+' p zhistory p zbefore '+MAP_ARGS+' '+z('anchor')+']].'
    return 'q[k '+('r56u' if retained else 'r56t')+'['+common+FRAME+' '+MAP_ARGS+(' '+z('anchor') if retained else '')+']].'

@lru_cache(None)
def acquisition_checks():
    q='q[k r56r['+args(('origin','relay','actfirst','procfirst','zero','firstact','firstend'))+' '+FRAME+']].'
    d=fixture(('r56r',),q);out={}
    for case in ('same','no_actual_source_state','already_target_state','no_result_state','not_manifestation','not_result_cause','wrong_cause_state','wrong_cause_person','wrong_cause_time','wrong_part','no_process','no_participation','history_gap','reverse_order'):
        v,rows,holds,saved=model(d)
        if case=='no_actual_source_state':holds['origin','firstact']=False
        if case=='already_target_state':holds['relay','zero']=True
        if case=='no_result_state':holds['relay','firstend']=False
        if case=='not_manifestation':v['h26pi']=lambda *a:False
        if case=='not_result_cause':v['h26ph']=lambda *a:False
        if case=='wrong_cause_state':v['h26ph']=lambda a,p,c,t:codeid(c)!=saved['state']
        if case=='wrong_cause_person':v['h26ph']=lambda a,p,c,t:p=='target'
        if case=='wrong_cause_time':v['h26ph']=lambda a,p,c,t:t=='anchor'
        if case=='wrong_part':v['h6a']=lambda *a:False
        if case=='no_process':v['ag']=lambda *a:False
        if case=='no_participation':v['df']=lambda *a:False
        if case=='history_gap':v['zhistory']=lambda t:t not in ('reference','firstact')
        if case=='reverse_order':v['zbefore']=lambda a,b:SCENES.index(a)>SCENES.index(b)
        got=run(d,v);assert got==[case=='same'],(case,got);out[case]=got[0]
    for n in ('h26ph','h26pi','h26pg','ag','h6a'):
        v,*_=model(d);v[n]=unknown;rejects(d,v)
    for acted in ('zero','firstend','secondact'):
        q='q[k r56r['+args(('origin','relay','actfirst','procfirst','zero',acted,'firstend'))+' '+FRAME+']].'
        x=fixture(('r56r',),q);v,rows,holds,_=model(x);rows['first']['acted']=acted
        assert run(x,v)==[acted!='secondact']
    return dict(cases=out,activity_may_precede_or_coincide_with_completion=True,activity_after_result_rejected=True,
        same_rank_two_state_for_truth_manifestation_and_result=True,unknown_rejected=True)

@lru_cache(None)
def path_checks():
    out={}
    for length in (1,2,3):
        d=fixture(('r56t',),path_query(length,False));v,*_=model(d);assert run(d,v)==[True];out[str(length)]=True
    d=fixture(('r56t',),path_query(2,False))
    for case in ('disconnected_sender','backward_effect','wrong_terminal','missing_second_effect','self_step','wrong_first_sender'):
        v,rows,holds,_=model(d)
        if case=='disconnected_sender':rows['second']['sender']='origin'
        if case=='backward_effect':
            rows['second']['start']='zero';rows['second']['acted']='firstact';holds['relay','firstact']=True
        if case=='wrong_terminal':rows['second']['recipient']='other';holds['other','secondend']=True
        if case=='missing_second_effect':v['h26ph']=lambda a,*rest:a!='actsecond'
        if case=='self_step':rows['second']['recipient']='relay'
        if case=='wrong_first_sender':rows['first']['sender']='other';holds['other','firstact']=True
        assert run(d,v)==[False],case;out[case]=False
    # The link admits an influence at the same coarse point as the preceding acquisition.
    v,rows,holds,_=model(d);rows['second']['acted']='firstend';assert run(d,v)==[True]
    return dict(cases=out,unbounded_finite_fold_not_fixed_length=True,previous_recipient_is_next_actor=True,
        previous_acquisition_not_after_next_manifestation=True,coarse_simultaneous_link_allowed=True)

@lru_cache(None)
def retention_checks():
    d=fixture(('r56u',),path_query());out={}
    for case in ('retained','terminal_relapse','terminal_absent_now','intermediate_later_loss','origin_later_loss','anchor_outside_history','anchor_before_acquisition'):
        v,rows,holds,_=model(d)
        if case=='terminal_relapse':holds['target','thirdact']=False
        if case=='terminal_absent_now':holds['target','anchor']=False
        if case=='intermediate_later_loss':holds['relay','anchor']=False
        if case=='origin_later_loss':holds['origin','anchor']=False
        if case=='anchor_outside_history':v['zhistory']=lambda t:t not in ('reference','anchor')
        if case=='anchor_before_acquisition':v['zanchor']=lambda:'firstend'
        got=run(d,v);assert got==[case in ('retained','intermediate_later_loss','origin_later_loss')],(case,got);out[case]=got[0]
    return dict(cases=out,final_same_person_property_process_and_history_retained=True,intermediates_not_required_to_retain_forever=True)

@lru_cache(None)
def common_state_checks():
    d=fixture(('r56v',),path_query(fixed=True));out={}
    for case in ('shared_policy','empty_policy_scope','wrong_reference_name','other_policy_supported','unknown_support'):
        v,rows,holds,saved=model(d)
        if case=='empty_policy_scope':v['r56l']=lambda *a:False
        if case=='wrong_reference_name':v['zrefpick']=lambda p,*cs:cs[1]
        if case=='other_policy_supported':v['h26pg']=lambda p,c,t:codeid(c)!=saved['policy'] and holds[p,t]
        if case=='unknown_support':v['h26pg']=unknown;rejects(d,v);continue
        got=run(d,v);assert got==[case=='shared_policy'],(case,got);out[case]=got[0]
    return dict(cases=out,actual_r56n_support_state_executes=True,policy_realization_stays_unknown=True,
        boundary='Only r56l, the independently checked nonempty eligible-setting condition, is a boundary. Actual r56o/r56n/r56m/r56k, reference checks, all state transitions, rank-two identities and support relations execute. No freedom-policy truth or utterance-reception values are supplied.')

@lru_cache(None)
def foreign_reach_checks():
    # Reuse individual constants as roles/communities, but keep each role's arguments exact.
    regions=args(('origin','first','actfirst','procfirst','second','actsecond'))
    path=args(('first',))+' l[a]['+z('second')+'] '+args(('origin','target','reference'))+' p zhistory p zbefore '+MAP_ARGS+' '+z('anchor')
    q='q[k r56x['+regions+' '+path+']].'
    q+='q[k r56y['+regions+' '+args(('origin','reference'))+' p zfirsts p ztails p zhistory p zbefore '+MAP_ARGS+' '+z('anchor')+']].'
    d=fixture(('r56x','r56y'),q);out={}
    for case in ('foreign_reached','same_source_jurisdiction','not_foreign_member','wrong_foreign_government','wrong_foreign_office','origin_not_local','unrelated_terminal','no_acquisition'):
        v,rows,holds,_=model(d)
        v['r5xh']=lambda p,o,c,t:(p,o,c,t)==('origin','first','actfirst','anchor')
        v['h26hi']=lambda p,o,c,t:(p,o,c,t) in (('origin','first','actfirst','anchor'),('target','second','actsecond','anchor'))
        v['h237n']=lambda g,c,t:(g,c,t)==('procfirst','actsecond','anchor')
        v['h256s']=v['h237n'];v['h256p']=lambda o,g,t:(o,g,t)==('second','procfirst','anchor')
        if case=='same_source_jurisdiction':
            old=v['h26hi'];v['h26hi']=lambda p,o,c,t:old(p,o,c,t) or (p,o,c,t)==('target','first','actfirst','anchor')
        if case=='not_foreign_member':v['h26hi']=lambda p,o,c,t:p=='origin'
        if case=='wrong_foreign_government':v['h237n']=lambda *a:False
        if case=='wrong_foreign_office':v['h256p']=lambda *a:False
        if case=='origin_not_local':v['h26hi']=lambda p,o,c,t:p=='target' and o=='second'
        if case=='unrelated_terminal':rows['second']['recipient']='other';holds['other','secondend']=True
        if case=='no_acquisition':holds['target','firstend']=True
        got=run(d,v);assert got==[case=='foreign_reached']*2,(case,got);out[case]=got
    # A different label for the same community does not satisfy the explicit inequality.
    same=fixture(('r56w',),'q[k r56w['+args(('origin','first','actfirst','procfirst','second','actfirst','origin','target','anchor'))+']].')
    v,_,_,_=model(same);v.update(r5xh=lambda *a:True,h26hi=lambda p,o,c,t:(p=='origin' and o=='first') or (p=='target' and o=='second'),h237n=lambda *a:True,h256s=lambda *a:True,h256p=lambda *a:True)
    assert run(same,v)==[False]
    return dict(cases=out,distinct_community_and_outside_original_jurisdiction=True,
        same_path_endpoints_as_political_people=True,one_verified_foreign_recipient_not_everyone=True,
        foreign_government_not_a_person_or_required_monarchy=True,
        boundary='r5xh is the separately checked source-monarch classification. All jurisdiction connections, foreign government primitives, existential recipient and the actual causal path execute; foreign policy realization is still unknown.')

def reading_record():
    u=next(x for x in read(INVENTORY)['units'] if x['id']=='kant-1784:u0015')
    return dict(status='social_acquisition_paths_for_the_same_liberty_attitude_partial',source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[890,1049],text=u['text'][890:1049]),
        interpretation=LIMITS,whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,new_verified_characters=0,
        unresolved=['先行例と共通方針の同じ精神への照応','元と国外の統治圏・経路証人の本文設定','外的障害・格闘の必要・政府の自己誤解','auch/selbst、全文帰属・通読'],
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in (LIBRARY,BASIS,DOC,INVENTORY,*PRIORS,'data/eighth-paragraph-source-reading-v1.json')})

@lru_cache(None)
def structure_checks():
    c=catalog();assert not c.document['statements'];assert len(parents()[1].document['statements'])==114
    for old in parents():
        for n,e in c.entries.items():
            if n in old.entries:assert e['declaration']==old.entries[n]['declaration'] and e['meaning_ja']==old.entries[n]['meaning_ja']
    for p in PRIORS:validate_hashes(ROOT,read(p)['source_sha256'])
    validate_hashes(ROOT,read(BASIS)['import_source_sha256'])
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b
    assert read(READING)==reading_record()
    for notation in ('compact','full'):
        t=format_graph(c.document,notation);assert parse(t)==parse(transcribe(t,alphabet='v2'))==c.document
    # The quoted policy itself contains public presentations. The social route
    # must not require their realization; check its generic body separately.
    active={r['name'] for r in closure(c.document,['r56u'])}
    assert not {'f2','f3','h6e','h6g','h6i','g3'}&active
    t=format_graph(c.document,'compact');ranks={}
    for name in ('r56n','r56p','r56v'):
        for rank,label in enumerate(('','b','c','d','e','f')):
            try:parse(t+'q[e[r '+label+'[p '+name+']][r '+label+'[p '+name+']]].')
            except ValueError as e:assert 'Quoted evaluation' in str(e),str(e)
            else:ranks[name]=rank;break
    assert ranks['r56n']==2 and ranks['r56p']==3
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),unchanged_manuscript_statements=114,
        inherited_meanings_preserved=True,roundtrips=True,minimum_quote_ranks=ranks,new_verified_characters=0,
        no_required_message_reception_or_rank_zero_cause=True)
def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))
def build_report():
    results={}
    for n,f in (('acquisition',acquisition_checks),('path',path_checks),('retention',retention_checks),('common_state',common_state_checks),('foreign_reach',foreign_reach_checks),('structure',structure_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(catalog().source_sha256)|{LIBRARY,BASIS,DOC,READING,INDEX,INVENTORY,*PRIORS,'data/eighth-paragraph-source-reading-v1.json',
        'scripts/compose_social_attitude_paths.py','scripts/check_social_attitude_paths.py','tests/test_social_attitude_paths.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py'}
    return dict(status='same_attitude_causal_paths_and_final_retention_checked_partial',document=LIBRARY,**results,
        alignment=dict(**read(READING)['source'],statements=[],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
