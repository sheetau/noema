"""Check genuine possibility plus necessary, non-vacuous limits on deferral."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import Content,SequenceValue
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_limited_personal_deferral import ROOT,LIBRARY,BASIS,PRIMITIVES,MEANINGS,LIMITS,parents,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown
from scripts.check_covenant_nullity import normalized
from scripts.check_persistent_compact_progress import base as period_base,SCENES,DOMAIN,EXTRA as OLD_EXTRA

REPORT='reports/limited-personal-deferral-v1.json'
READING='data/limited-personal-deferral-reading-v1.json'
DOC='docs/limited-personal-deferral-v1.md'
INVENTORY='artifacts/written-units-v1/kant-1784.json'
PRIORS=('reports/personal-enlightenment-choice-v1.json','reports/fixed-compact-sentence-v1.json','reports/rational-self-imposition-v1.json','reports/persistent-compact-progress-v1.json')
EXTRA=OLD_EXTRA+'r zprior[] j[a].'
FOUR=' '.join('k zalpha[]' for _ in range(4))
CTX='k zreference[] k zcandidate[]'

def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(roots,query,boundaries=()):
    d=deepcopy(catalog().document)
    for x in d['declarations']:
        if x['name'] in boundaries:x.update(kind='primitive',parameters=[p['sort'] for p in x['parameters']]);x.pop('body')
    d.update(declarations=closure(d,roots),statements=[])
    return parse(format_graph(d,'compact')+EXTRA+query)
def run(d,v):return evaluate(d,v,DOMAIN,SCENES,True)
def content(points):return Content(SCENES,tuple(s in points for s in SCENES))
def base(d,bindings=('alpha',)*4):
    v={x['name']:unknown for x in d['declarations'] if x['kind']=='primitive'}
    v.update({'z'+n:lambda n=n:n for n in (*DOMAIN,*SCENES)})
    v.update(zbindings=lambda:SequenceValue(bindings,'"individual"'),h26fw=lambda a,r:'start',
        h26ax=lambda:'alpha',h26fz=lambda:'beta',h26f2=lambda:'reference')
    return v

@lru_cache(None)
def frame_checks():
    d=fixture(('r5kw',),'q[k r5kw[k zalpha[] k zbeta[] k zalpha[] k zalpha[] '+CTX+']].',('r5kn',));rows={}
    for variant in ('baseline_other_subject','nonhuman_actor','nonhuman_subject','missing_duties','excluded','cycle','outside_anchor','wrong_reference'):
        v=base(d);history=('start','middle','end')
        v['aa']=lambda p:p in DOMAIN and not(variant=='nonhuman_actor' and p=='alpha') and not(variant=='nonhuman_subject' and p=='beta')
        v['r5kn']=lambda s,p,role,r:(s,p,role,r)==('alpha','beta','beta','reference') and variant!='missing_duties'
        v['h26fy']=lambda *a:a==('alpha','beta','alpha','alpha','reference','candidate') and variant!='excluded'
        v['h257z']=lambda r,c,p:(r,c)==('reference','candidate') and p in history
        v['ic']=lambda a,b,c:c=='candidate' and a in history and b in history and (a!=b if variant=='cycle' else history.index(a)<history.index(b))
        if variant=='outside_anchor':v['h26fw']=lambda *a:'outer'
        if variant=='wrong_reference':v['zreference']=lambda:'assessment'
        actual=run(d,v);assert actual==[variant=='baseline_other_subject'],(variant,actual);rows[variant]=actual[0]
        assert v.get('h26ft',unknown) is unknown
    return dict(native_broad_candidate_frame=rows,no_self_duration_or_permission_prefilter=True,boundary='r5kn; complete duty mapping preserved')

@lru_cache(None)
def correspondence_checks():
    queries=''.join('q[t[k '+n+'[k '+b+'[] k zreference[]]][k zcandidate[]]].' for n,b in (('r5kx','zbindings'),('r5kr','zprior'),('r5ky','zbindings'),('r5ks','zprior')))
    d=fixture(('r5kx','r5kr','r5ky','r5ks'),queries,('r5jf','r5jd','r5kq'));rows={}
    for point in ('before','start','middle','end','after','outer'):
        v=base(d);v['zprior']=lambda:SequenceValue(('alpha','alpha','beta','alpha','alpha'),'"individual"')
        v['r5jf']=lambda p,r,c,s:(p,r,c,s)==('alpha','reference','candidate','start')
        v['r5jd']=lambda p,r,c,s,e:(p,r,c,s,e)==('alpha','reference','candidate','start','end')
        v['h26e3']=lambda p,r,c,t:(p,r,c)==('alpha','reference','candidate') and t in ('start','middle')
        history=('before','start','middle','end','after')
        v['h257z']=lambda r,c,t:(r,c)==('reference','candidate') and t in history
        v['ic']=lambda a,b,c:c=='candidate' and a in history and b in history and history.index(a)<history.index(b)
        v['r5kq']=lambda s,p,role,a,t,r,c,at:(s,p,role,r,c,at)==('alpha','alpha','beta','reference','candidate',point)
        actual=run(d,v);expected=[point in('start','middle')]*2+[point in('end','after')]*2
        assert actual==expected,(point,actual);rows[point]=actual
    return dict(bounded_self_old_new_content_correspondence=rows,
        qualification='Same source alpha, subject alpha, role beta, response alpha, period alpha and explicit bounded interval correspondence; quoted families remain different.',
        boundaries=['r5jf/r5jd; native period evidence preserved','r5kq; inquiry evidence preserved'])

def choice_model(d,variant='baseline',bindings=('alpha',)*4):
    v=period_base(d);actor,subject,response,period=bindings
    v.update(base(d,bindings))
    # Restore time inputs overwritten by base's unknown defaults.
    time=period_base(d)
    for name in ('h257z','ic','h26ex','h26e3'):v[name]=time[name]
    v['r5kn']=lambda s,p,role,r:(s,p,role,r)==('alpha',subject,'beta','reference')
    v['cg']=lambda p,a,t:(p,a,t)==(actor,response,'start') and variant!='no_action'
    def stance(p,response_,target,b,r,sign,at):
        code=normalized(target);items=normalized(b)
        if(p,response_,r,at)!=(actor,response,'reference','start'):return False
        if code==('r5ku',0):return variant=='renunciation' and items==('alpha',subject,'beta',response) and not sign
        if items!=bindings:return False
        if code==('r5kx',0):return (not sign and variant!='no_pause') or(sign and variant=='conflicting_pause')
        if code==('r5ky',0):return (sign and variant!='no_resume') or(not sign and variant=='conflicting_resume')
        return False
    v['h26ft']=stance
    if variant=='invalid_period':v['h26ex']=lambda *a:False;v['h26e3']=lambda *a:False
    return v

@lru_cache(None)
def choice_checks():
    query='q[t[k r5kz[k zbindings[] k zreference[]]][k zcandidate[]]].q[k r5k3['+FOUR+' '+CTX+']].'
    d=fixture(('r5kz','r5k3'),query,('r5kn',));rows={}
    expected={'baseline':[True,True],'no_action':[False,True],'no_pause':[False,True],
        'no_resume':[True,False],'conflicting_pause':[False,True],'conflicting_resume':[True,False],
        'renunciation':[True,False],'invalid_period':[False,False]}
    for variant,want in expected.items():
        actual=run(d,choice_model(d,variant));assert actual==want,(variant,actual);rows[variant]=actual
    other_query=query.replace('k r5k3[k zalpha[] k zalpha[]','k r5k3[k zalpha[] k zbeta[]')
    other=fixture(('r5kz','r5k3'),other_query,('r5kn',));v=choice_model(other,bindings=('alpha','beta','alpha','alpha'))
    assert run(other,v)==[True,False];rows['other_subject']=[True,False]
    # Endlessness is not proved by a finite model. Only its interface to the
    # new suspension and qualification is tested; prior rbz evidence is pinned.
    unending=fixture(('r5kz','r5k3'),query,('r5kn','r5jf'));v=choice_model(unending)
    v['r5jf']=lambda *a:a==('alpha','reference','candidate','start');v['h26ex']=lambda *a:False
    assert run(unending,v)==[True,False];rows['unending_interface']=[True,False]
    v=choice_model(d)
    # Supply the old policies positively, without supplying either new quoted
    # family. Extensional correspondence must not transfer an attitude.
    def old_policy(p,a,target,b,r,s,t):
        return (p,a,normalized(b),r,t)==('alpha','alpha',('alpha','alpha','beta','alpha','alpha'),'reference','start') and (
            (normalized(target)==('r5kr',0) and not s) or
            (normalized(target)==('r5ks',0) and s))
    v['h26ft']=old_policy
    assert run(d,v)==[False,False]
    v=choice_model(d);v['h26ft']=unknown
    try:run(d,v)
    except ValueError as e:assert 'Unknown' in str(e)
    else:raise AssertionError('Unknown policy accepted')
    return dict(native_suspension_and_separate_qualification=rows,
        old_quoted_policy_not_implicitly_transferred=True,unknown_rejected=True,
        boundaries=['r5kn','r5jf only for explicitly named unending interface case'])

@lru_cache(None)
def permission_checks():
    d=fixture(('r5k2',),'q[k r5k2['+FOUR+' '+CTX+']].');rows={}
    target=('alpha','alpha','beta',('r5kz',1),('alpha',)*4,'reference')
    for allow,oppose in product((False,True),repeat=2):
        v=base(d)
        v['h245c']=lambda *a:normalized(a)==(*target,True,'candidate') and allow
        v['h237z']=lambda *a:normalized(a)==(*target,False,'candidate') and oppose
        actual=run(d,v);assert actual==[allow and not oppose];rows[str((allow,oppose))]=actual[0]
    wrong={}
    for variant,pos,value in (('source',0,'beta'),('actor',1,'beta'),('role',2,'alpha'),('target',3,('r5kt',1)),('binding',4,('beta',)*4),('reference',5,'assessment'),('polarity',6,False),('candidate',7,'after')):
        v=base(d);want=list((*target,True,'candidate'));want[pos]=value
        v['h245c']=lambda *a:normalized(a)==tuple(want);v['h237z']=lambda *a:False
        actual=run(d,v);assert actual==[False];wrong[variant]=False
    return dict(unconflicted_positive_permission=rows,wrong_identity=wrong,native_r37c=True,world_and_choice_not_evaluated=True)

@lru_cache(None)
def possibility_checks():
    q='q[k r5k5[k zalpha[] k zreference[]]].q[k r5k5[k zbeta[] k zreference[]]].q[k r5k7[k zreference[]]].q[t[k r5la[]][k zouter[]]].'
    d=fixture(('r5k5','r5k7','r5la'),q,('r5kw','r5kz','r5k3'));rows={}
    first=('alpha','alpha','alpha','alpha','candidate');second=('beta','beta','beta','alpha','candidate')
    finite_unpermitted=('alpha','alpha','alpha','beta','candidate')
    other=('alpha','beta','beta','alpha','candidate');unending=('beta','beta','beta','beta','candidate')
    no_resume=('beta','beta','alpha','beta','after')
    cases={first,second,finite_unpermitted,other,unending,no_resume}
    for variant in ('baseline','missing_second','other_subject_permitted','unending_permitted','no_resume_permitted','split_candidates','empty_candidates','missing_duty_scope'):
        v=base(d);v['aa']=lambda p:p in DOMAIN
        scope=set(cases);execution=set(cases);permission={first,second};qualification={first,second,finite_unpermitted}
        if variant=='missing_second':permission.remove(second)
        if variant=='other_subject_permitted':permission.add(other)
        if variant=='unending_permitted':permission.add(unending)
        if variant=='no_resume_permitted':permission.add(no_resume)
        if variant=='split_candidates':
            permission.remove(first);permission.add((*first[:4],'after'));scope.add((*first[:4],'after'))
        if variant=='empty_candidates':scope=set()
        if variant=='missing_duty_scope':scope={x for x in scope if x[1]!='beta'}
        v['r5kw']=lambda a,s,r,p,ref,c:ref=='reference' and(a,s,r,p,c) in scope
        v['r5kz']=lambda b,ref:content({c for *xs,c in execution if tuple(xs)==normalized(b)}) if ref=='reference' else content(set())
        v['r5k3']=lambda a,s,r,p,ref,c:ref=='reference' and(a,s,r,p,c) in qualification
        v['h245c']=lambda source,actor,role,target,b,ref,sign,c:(source,role,normalized(target),ref,sign)==('alpha','beta',('r5kz',1),'reference',True) and normalized(b)[0]==actor and(*normalized(b),c) in permission
        v['h237z']=lambda *a:False
        actual=run(d,v)
        want={'baseline':[True,True,True,True],'missing_second':[True,False,True,False],
            'other_subject_permitted':[True,True,False,False],'unending_permitted':[True,True,False,False],
            'no_resume_permitted':[True,True,False,False],'split_candidates':[False,True,True,False],
            'empty_candidates':[False,False,True,False],'missing_duty_scope':[True,False,True,False]}[variant]
        assert actual==want,(variant,actual);rows[variant]=actual
    return dict(personal_possibilities_universal_limits_and_combination=rows,
        finite_qualified_but_unpermitted_case_retained=True,
        boundaries=['r5kw candidate frame','r5kz actual suspension','r5k3 qualification; each checked separately'],
        native=['r5k4','r5k5','r5k7','r5la','r37c'])

def reading_record():
    u=next(u for u in read(INVENTORY)['units'] if u['id']=='kant-1784:u0013');end=u['text'].index(';',2678)+1
    pages=read('data/personal-enlightenment-choice-reading-v1.json')['primary_pages']
    return dict(status='partial_personal_deferral_permission_and_necessary_limits',source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[2678,end],text=u['text'][2678:end]),
        interpretation=LIMITS,new_verified_characters=0,whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,
        primary_pages=pages,unresolved=['後世についての放棄','神聖な人類の権利と侵害・踏みにじる見立て','zwar/aber/mehr noch、全文への帰属と通読'],
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in (LIBRARY,BASIS,DOC,INVENTORY,*(x['path'] for x in pages),*PRIORS)})

@lru_cache(None)
def structure_checks():
    c=catalog();sources=parents();old={n:e for s in sources for n,e in s.entries.items()}
    for n in read(BASIS)['imported_symbols']:
        assert c.entries[n]['declaration']==old[n]['declaration'] and c.entries[n]['meaning_ja']==old[n]['meaning_ja']
    for p in PRIORS:validate_hashes(ROOT,read(p)['source_sha256'])
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b
    for notation in ('compact','full'):
        s=format_graph(c.document,notation);assert parse(s)==parse(transcribe(s,alphabet='v2'))==c.document
    assert read(READING)==reading_record() and len(sources[1].document['statements'])==104
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),roundtrips=True,preserved_main_statements=104,semantic_review_characters_added=0)

def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))

def build_report():
    results={}
    for name,fn in (('frame',frame_checks),('correspondence',correspondence_checks),('choice',choice_checks),('permission',permission_checks),('possibility',possibility_checks),('structure',structure_checks)):
        results[name]=fn();print(name+' checked',flush=True)
    paths=set(catalog().source_sha256)|{LIBRARY,BASIS,DOC,READING,INVENTORY,*PRIORS,*(x['path'] for x in read(READING)['primary_pages']),
        'scripts/compose_limited_personal_deferral.py','scripts/check_limited_personal_deferral.py','tests/test_limited_personal_deferral.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/compose_protected_remarks.py',
        'scripts/check_persistent_compact_progress.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/check_covenant_nullity.py'}
    return dict(status='personal_deferral_possibility_and_necessary_self_bounded_limits',document=LIBRARY,**results,
        alignment=dict(**reading_record()['source'],statements=[],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
