"""Check critical content, independent scope, frankness and quoted conjunction."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_frank_legal_criticism import ROOT,LIBRARY,BASIS,MEANINGS,PRIMITIVES,LIMITS,FRAME,NAMES,parent,dependencies,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown
from scripts import check_offered_judgments as offered

DOC='docs/frank-legal-criticism-v1.md';READING='data/frank-legal-criticism-reading-v1.json'
INDEX='data/semantic-review-index-v202.json';SOURCE='data/ninth-paragraph-source-reading-v2.json';INVENTORY='artifacts/written-units-v1/kant-1784.json'
PRIORS=('reports/legislative-formulations-v1.json','reports/legislative-thoughts-v1.json','reports/offered-judgments-v1.json')
DOMAIN=(*offered.DOMAIN,*FRAME,'faculty','criterion','secondcriterion')
SCENES=(*offered.SCENES,'history')
def z(n):return 'k z'+n+'[]'
def args(ns):return ' '.join(z(n) for n in ns)
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def codeid(c):return c.rank,json.loads(c.syntax)
FARGS=args((*FRAME,'reference'));PARGS=args(('person','activity','scholar','audience'))
MESSAGE='o a[r[p r53m]][r['+z('reference')+']]'
PROVIDER=(0,dict(kind='function_ref',symbol='h26ae'))
DEFECT=(0,dict(kind='function_ref',symbol='r326'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(roots,query,boundaries=()):
    d=deepcopy(catalog().document);d['statements']=[]
    for row in d['declarations']:
        if row['name'] in boundaries:row.update(kind='primitive',parameters=[p['sort'] for p in row['parameters']]);row.pop('body')
    extra=''.join('r z'+n+'[] '+('a' if n in DOMAIN else 'd')+'.' for n in (*DOMAIN,*SCENES))
    extra+='r znamepick[a '+' '.join('i[a]' for _ in DOMAIN)+'] i[a].r zrefpick[d '+' '.join('i[d]' for _ in SCENES)+'] i[d].'
    extra+='d h223g[item a] i[a][k znamepick[v item '+' '.join('r['+z(n)+']' for n in DOMAIN)+']].'
    extra+='d h223h[point d] i[d][k zrefpick[v point '+' '.join('r['+z(n)+']' for n in SCENES)+']].'
    extra+='r ztruth[a d d] c.d h26ae[item a reference d] e[b point[k ztruth[v item v reference v point]]].r zsavemessage[i[h[a] f]] c.r zcriteria[a] a.'
    p=parse('p:'+extra);ns={r['name'] for r in p['declarations']};d['declarations']=p['declarations']+[r for r in d['declarations'] if r['name'] not in ns]
    d['declarations']=closure(d,(*roots,*ns,'r53m'))
    return parse(format_graph(d,'compact')+'q[k zsavemessage['+MESSAGE+']].'+query)
def run(d,v):return evaluate(d,v,DOMAIN,SCENES,True)[1:]
def rejects(d,v):
    try:run(d,v)
    except ValueError as e:assert 'Unknown' in str(e),str(e)
    else:raise AssertionError('Unknown accepted')
def model(d):
    v,_=offered.model(d);v.update({'z'+n:lambda n=n:n for n in (*DOMAIN,*SCENES)})
    v['znamepick']=lambda p,*cs:cs[DOMAIN.index(p)];v['zrefpick']=lambda p,*cs:cs[SCENES.index(p)]
    v.update(r6cm=lambda *a:a==('ruler','people','community','baseline','oldform','reference'),
        r6co=lambda *a:a==('ruler','people','community','baseline','oldform','reference','history','reference'),
        h26tg=lambda s,c,r:(s,c,r)==('standard','community','reference'),
        ab=lambda f,p,t:(f,p,t)==('faculty','person','now'),ac=lambda p,f,a,t:(p,f,a,t)==('person','faculty','activity','now'),
        zcriteria=lambda i:'secondcriterion' if i=='second' else 'criterion',
        h26tj=lambda q,s,l,f,c,r:q in ('criterion','secondcriterion') and (s,l,f,c,r)==('standard','baseline','oldform','community','reference'),
        h243v=lambda q,l,r:q in ('criterion','secondcriterion') and (l,r)==('baseline','reference'),
        h243x=lambda i,l,q,c,r:(i,q) in (('item','criterion'),('second','secondcriterion')) and (l,r)==('baseline','reference') and codeid(c)==DEFECT,
        h26tk=lambda p,a,l,f,r:(p,a,l,f,r)==('person','activity','baseline','oldform','reference'),
        h26tl=lambda p,a,i,c,r,t:(p,a,r,t)==('person','activity','reference','now') and i in ('item','second') and codeid(c)==PROVIDER,
        h26tm=lambda *a:False)
    expected_issue=(0,dict(kind='apply',function=dict(kind='function_ref',symbol='r6cq'),arguments=[dict(kind='call',symbol='z'+n,arguments=[]) for n in (*FRAME,'reference')]))
    v['h26ti']=lambda i,p,r,c:i in ('item','second') and codeid(p)==PROVIDER and r=='reference' and codeid(c)==expected_issue
    return v

@lru_cache(None)
def criticism_checks():
    q='q[k r6cz['+args(('item','criterion'))+' '+FARGS+']].q[k r6c2['+PARGS+' '+args(('item','criterion'))+' '+FARGS+' '+z('now')+']].'
    d=fixture(('r6cz','r6c2'),q,('r6cm',));v=model(d);assert run(d,v)==[True,True];rows={}
    for case in ('different_law','different_form','unrelated_standard','wrong_criterion','wrong_defect_content','no_desirable_condition','no_own_judgment','no_acceptance','not_public','different_activity','not_own_voice','no_understanding','false_opinion','no_actual_defect','no_review_purpose'):
        w=dict(v);want=[False,False]
        if case=='different_law':w['h243x']=lambda i,l,*a:l=='other'
        if case=='different_form':w['h26tj']=lambda q,s,l,f,*a:f=='other'
        if case=='unrelated_standard':w['h26tj']=lambda q,s,*a:s=='other'
        if case=='wrong_criterion':w['zcriterion']=lambda:'secondcriterion'
        if case=='wrong_defect_content':w['h243x']=lambda i,l,q,c,r:codeid(c)==PROVIDER
        if case=='no_desirable_condition':w['h243v']=lambda *a:False
        if case in ('no_own_judgment','no_acceptance','not_public','different_activity','not_own_voice','no_understanding'):want=[True,False]
        if case=='no_own_judgment':w['h26ai']=lambda *a:False
        if case=='no_acceptance':w['h26af']=lambda *a:False
        if case=='not_public':w['ce']=lambda *a:False
        if case=='different_activity':w['f2']=lambda a,*rest:a=='other'
        if case=='not_own_voice':w['h253l']=lambda p,a,principal,*rest:principal=='other'
        if case=='no_understanding':w['ac']=lambda *a:False
        if case in ('false_opinion','no_actual_defect','no_review_purpose'):want=[True,True]
        if case=='false_opinion':w['ztruth']=lambda *a:False
        if case=='no_actual_defect':w['h243u']=lambda *a:True
        if case=='no_review_purpose':w['hzu']=lambda *a:False
        assert run(d,w)==want,case;rows[case]=want
    for n in ('h26tj','h243v','h243x','h26ai','h245q','ab','ac','f2'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    assert v['h243u'] is unknown and v['ztruth'] is unknown
    w=dict(v);w['zitem']=lambda:'alias';assert run(d,w)==[True,True]
    # Execute the reused defect content separately: quotation above must not execute it.
    native=fixture(('r326',),'q[t[k r326['+args(('baseline','criterion','reference'))+']]['+z('now')+']].')
    truth=[]
    for valid in (False,True):
        for fulfilled in (False,True):
            w=model(native);w['h243v']=lambda *a,b=valid:b;w['h243u']=lambda *a,b=fulfilled:b
            want=valid and not fulfilled;assert run(native,w)==[want];truth.append([valid,fulfilled,want])
    w=model(native);w['h243u']=unknown;rejects(native,w)
    return dict(cases=rows,defect_truth_table=truth,native_own_judgment_and_public_presentation=True,canonical_alias=True,
        unknown_rejected=True,boundary='r6cm only; complete legislative frame is pinned in legislative-formulations. r326 and r53n/r53q execute natively in separate checks.')

def action_query(thoughts=('item',),criticisms=('item',),combined=True):
    seq=lambda xs:'l[a]['+args(xs)+']'
    lists=(seq(thoughts)+' ') if combined else ''
    return 'q[k '+('r6c5' if combined else 'r6c4')+'['+PARGS+' '+lists+seq(criticisms)+' p zcriteria '+FARGS+' '+args(('history','reference','now'))+']].'

@lru_cache(None)
def frankness_checks():
    d=fixture(('r6c5',),action_query(),('r6cm','r6co'));v=model(d);assert run(d,v)==[True];rows={}
    for case in ('hides_presented_item','hides_unlisted_relevant_item','distorts_unlisted_relevant_item','no_fixed_undertaking','other_activity_scope','hides_only_unrelated_private_item','benign_omission','withheld_item_not_own','alias_instead_of_canonical_scope','presented_item_outside_scope','unknown_evasion'):
        w=dict(v);want=False
        if case=='hides_presented_item':w['h26tm']=lambda p,a,i,c,r,t:i=='item'
        if case in ('hides_unlisted_relevant_item','distorts_unlisted_relevant_item'):w['h26tm']=lambda p,a,i,c,r,t:i=='second'
        if case=='no_fixed_undertaking':w['h26tk']=lambda *a:False
        if case=='other_activity_scope':w['h26tl']=lambda p,a,i,c,r,t:a=='other'
        if case=='hides_only_unrelated_private_item':w['h26tm']=lambda p,a,i,c,r,t:i=='other';want=True
        if case=='benign_omission':want=True
        if case=='withheld_item_not_own':w['h26af']=lambda p,i,r,t:i=='item'
        if case=='alias_instead_of_canonical_scope':w['h26tl']=lambda p,a,i,c,r,t:i in ('item','alias')
        if case=='presented_item_outside_scope':w['h26tl']=lambda p,a,i,c,r,t:i=='second'
        if case=='unknown_evasion':w['h26tm']=unknown;rejects(d,w);rows[case]='rejected';continue
        assert run(d,w)==[want],case;rows[case]=want
    for n in ('h26tk','h26tl'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    # Scope holds item and second, while only item is publicly listed. This is
    # intentional: concealing second fails; an innocent omission still passes.
    return dict(cases=rows,independent_scope_exceeds_presented_sequence=True,no_all_private_thoughts_or_fearlessness_requirement=True,
        scope_completeness_is_explicit_interpretation_contract=True,unknown_rejected=True)

@lru_cache(None)
def conjunction_checks():
    rows={}
    for thoughts,crit in ((('item',),('item',)),(('item','second'),('item','second')),(('second',),('item',)),(('item',),('second',)),((),('item',)),(('item',),()),(('item','item'),('item','item'))):
        d=fixture(('r6c5',),action_query(thoughts,crit),('r6cm','r6co'));v=model(d);want=bool(thoughts and crit)
        assert run(d,v)==[want],(thoughts,crit);rows[str((thoughts,crit))]=want
    d=fixture(('r6c5',),action_query(('item',),('item','second')),('r6cm','r6co'));v=model(d)
    for case in ('second_wrong_criterion','second_elsewhere','second_not_presented','different_improvement_issue','adopted_only_before_future_presentation','different_history','different_prior_law','different_prior_form'):
        w=dict(v)
        if case=='second_wrong_criterion':w['zcriteria']=lambda i:'criterion'
        if case=='second_elsewhere':w['h26tl']=lambda p,a,i,c,r,t:i=='item' or a=='other'
        if case=='second_not_presented':w['f2']=lambda a,p,i,c,t:i=='item'
        if case=='different_improvement_issue':w['h26ti']=lambda *a:False
        if case=='adopted_only_before_future_presentation':w['r6co']=lambda *a:a[-1]=='now'
        if case=='different_history':w['r6co']=lambda *a:a[-2]=='later'
        if case=='different_prior_law':w['r6co']=lambda *a:a[3]=='other'
        if case=='different_prior_form':w['r6co']=lambda *a:a[4]=='other'
        assert run(d,w)==[False],case;rows[case]=False
    for n in ('r6co','zcriteria'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    return dict(cases=rows,all_items_and_shared_activity=True,different_criteria_allowed=True,fixed_prior_anchor_not_presentation_time=True,
        boundary='r6cm/r6co only; the prior-adoption report separately executes the complete adoption with a prior actor distinct from the current ruler.')

@lru_cache(None)
def binding_checks():
    seq=lambda xs:'l[a]['+args(xs)+']'
    thoughts=seq(('item',));crit=seq(('item','second'))
    def make(names,quoted,marked=0,expected_mark=0,swap_times=False):
        bindings=seq(names);candidate='reference' if swap_times else 'history';anchor='history' if swap_times else 'reference'
        code='k r6c7[r['+thoughts+'] r['+crit+'] r[p zcriteria] r['+z(candidate)+'] r['+z(anchor)+']]'
        content=('c[s['+code+']]['+bindings+' '+z('reference')+']') if quoted else 'k r6c6['+thoughts+' '+crit+' p zcriteria '+args((candidate,anchor))+' '+bindings+' '+z('reference')+']'
        d=fixture(('r6c7' if quoted else 'r6c6',),'q[t['+content+']['+z('now')+']].',('r6c5',));v=model(d)
        for n in DOMAIN:v['z'+n]=lambda:'alpha'
        for i,n in enumerate(NAMES):v['z'+n]=lambda i=i:'beta' if i==marked else 'alpha'
        v['zitem']=lambda:'alpha';v['zsecond']=lambda:'beta'
        slots=tuple('beta' if i==expected_mark else 'alpha' for i in range(10))
        expected=(*slots[:4],('alpha',),('alpha','beta'),*slots[4:],'reference','history','reference','now')
        v['zcriteria']=lambda x:'beta' if x=='alpha' else 'alpha'
        def body(*a):
            normalized=tuple(tuple(x.items) if hasattr(x,'items') else x for i,x in enumerate(a) if i!=6)
            # Exercise the function carried through both quote and direct paths.
            return normalized==expected and a[6]('alpha')=='beta' and a[6]('beta')=='alpha'
        v['r6c5']=body
        return evaluate(d,v,('alpha','beta'),SCENES,True)[1]
    for quoted in (False,True):
        for i in range(10):
            assert make(NAMES,quoted,i,i),(quoted,i)
            assert not make(NAMES,quoted,i,(i+1)%10),(quoted,i)
        assert not make(NAMES[:-1],quoted) and not make((*NAMES,'person'),quoted)
        assert not make(NAMES,quoted,swap_times=True)
    # Building the closed target may never run the action or the selector.
    code='k r6c7[r['+thoughts+'] r['+crit+'] r[p zcriteria] r['+z('history')+'] r['+z('reference')+']]'
    d=fixture(('r6c7',),'q[e['+code+']['+code+']].',('r6c5',));v=model(d);v['r6c5']=unknown;v['zcriteria']=unknown
    assert run(d,v)==[True]
    return dict(direct_and_quoted_targets=True,all_ten_slots_and_wrong_lengths_checked=True,closed_lists_selector_and_times_preserved=True,
        quote_does_not_execute_action_or_selector=True,finite_model='Two individuals, every marked/displaced slot; native action body checked separately.',boundary='r6c5 only')

def reading_record():
    u=next(u for u in read(INVENTORY)['units'] if u['id']=='kant-1784:u0016');f='mit einer freimüthigen Kritik der schon gegebenen';a=u['text'].index(f,390)
    return dict(status='frank_criticism_of_the_same_given_law_partial',source_unit=u['id'],unit_sha256=u['text_sha256'],
      alignment=dict(segments=[dict(unit=u['id'],range=[a,a+len(f)],text=f,definitions=list(MEANINGS),status='explicit_interpretive_annotation')]),interpretation=LIMITS,
      unresolved=['全臣民と全候補への許可、公的理性使用一般、sogar','国家元首の思考態度、啓蒙への照応、拡張、危険と洞察','実例、尊敬する君主の先行者不在、全文提示と通読'],
      whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,new_verified_characters=0,
      source_sha256={p:digest((ROOT/p).read_bytes()) for p in (LIBRARY,BASIS,DOC,INVENTORY,SOURCE,*PRIORS)})
@lru_cache(None)
def structure_checks():
    c=catalog();old=parent();assert not c.document['statements'] and len(old.document['statements'])==118
    for source in (old,*dependencies()):
        for n,e in source.entries.items():
            if n in c.entries:assert c.entries[n]['declaration']==e['declaration'] and c.entries[n]['meaning_ja']==e['meaning_ja']
    for p in (*PRIORS,SOURCE):validate_hashes(ROOT,read(p)['source_sha256'])
    validate_hashes(ROOT,read(BASIS)['import_source_sha256']);assert read(READING)==reading_record()
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b
    for notation in ('compact','full'):
        t=format_graph(c.document,notation);assert parse(t)==parse(transcribe(t,alphabet='v2'))==c.document
    ranks={};t=format_graph(c.document,'compact')
    for n in MEANINGS:
        for rank,label in enumerate(('','b','c')):
            try:parse(t+'q[e[r '+label+'[p '+n+']][r '+label+'[p '+n+']]].')
            except ValueError as e:assert 'Quoted evaluation' in str(e),str(e)
            else:ranks[n]=rank;break
    assert ranks=={n:int(n!='r6c3') for n in MEANINGS},ranks
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),inherited_meanings_preserved=True,roundtrips=True,minimum_quote_ranks=ranks,new_verified_characters=0)
def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))
def build_report():
    results={}
    for n,f in (('criticism',criticism_checks),('frankness',frankness_checks),('conjunction',conjunction_checks),('binding',binding_checks),('structure',structure_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(catalog().source_sha256)|{LIBRARY,BASIS,DOC,READING,INDEX,SOURCE,INVENTORY,*PRIORS,
      'scripts/compose_frank_legal_criticism.py','scripts/check_frank_legal_criticism.py','tests/test_frank_legal_criticism.py',
      'scripts/compose_legislative_thoughts.py','scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/compose_protected_remarks.py',
      'scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/check_offered_judgments.py'}
    return dict(status='frank_criticism_of_given_legislation_checked_partial',document=LIBRARY,**results,alignment=read(READING)['alignment'],
      whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
      source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
