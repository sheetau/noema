"""Check complete posterity, chosen renunciation and shared rights appraisals."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import Content,SequenceValue
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_renunciation_rights import ROOT,LIBRARY,BASIS,PRIMITIVES,MEANINGS,LIMITS,parents,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown
from scripts.check_covenant_nullity import normalized
from scripts.check_posterity_harm import SCENES,DOMAIN,EXTRA,epoch_model

REPORT='reports/renunciation-rights-v1.json'
READING='data/renunciation-rights-reading-v1.json'
DOC='docs/renunciation-rights-v1.md'
INVENTORY='artifacts/written-units-v1/kant-1784.json'
PRIORS=('reports/limited-personal-deferral-v1.json','reports/personal-enlightenment-choice-v1.json','reports/posterity-harm-v1.json','reports/fixed-compact-sentence-v1.json')
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
def run(d,v,domain=DOMAIN):return evaluate(d,v,domain,SCENES,True)
def content(points):return Content(SCENES,tuple(s in points for s in SCENES))
def base(d,bindings=('alpha',)*4):
    v={x['name']:unknown for x in d['declarations'] if x['kind']=='primitive'}
    v.update({'z'+n:lambda n=n:n for n in (*DOMAIN,'gamma',*SCENES)})
    v.update(zbindings=lambda:SequenceValue(bindings,'"individual"'),h26fw=lambda a,r:'anchor',
        h26ax=lambda:'alpha',h26fz=lambda:'beta',h26f2=lambda:'reference',h256m=lambda:'beta',h26ar=lambda r:'baseline')
    return v

@lru_cache(None)
def scope_checks():
    d=fixture(('r5lc',),'q[k r5lc['+FOUR+' '+CTX+']].',('r5kn',));rows={}
    variants=('baseline','missing_farther_member','missing_later_member','empty_group','nonhuman_member',
        'no_posterity','uncovered','overlap','wrong_anchor','wrong_reference','unmapped_member','nonhuman_actor')
    for variant in variants:
        v=epoch_model(d,variant);v.update(h26fw=lambda a,r:'later' if variant=='wrong_anchor' else 'anchor',h26ax=lambda:'alpha',h26fz=lambda:'beta')
        v['r5kn']=lambda s,p,role,r:(s,role,r)==('alpha','beta','reference') and p in DOMAIN and not(variant=='unmapped_member' and p=='beta')
        if variant=='nonhuman_actor':v['aa']=lambda p:p=='beta'
        actual=run(d,v,(*DOMAIN,'gamma'));assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
    v=epoch_model(d);v.update(h26fw=lambda a,r:'anchor',h26ax=lambda:'alpha',h26fz=lambda:'beta',r5kn=unknown)
    try:run(d,v,(*DOMAIN,'gamma'))
    except ValueError as e:assert 'Unknown' in str(e)
    else:raise AssertionError('Unknown duties accepted')
    return dict(native_epoch_complete_posterity_and_choice_anchor=rows,boundary='r5kn; complete duty mapping pinned',unknown_duty_rejected=True)

def future_model(d,point='later',person='beta',bindings=('alpha',)*4):
    v=base(d,bindings);actor,response,earlier,group=bindings[:4]
    v['r5lb']=lambda a,b,e,g,r,c:(a,b,e,g,r,c)==(actor,response,earlier,group,'reference','candidate')
    v['h246c']=lambda g,p,r:(g,r)==(group,'reference') and p in DOMAIN
    v['r5jy']=lambda p,e,r,c,t:(e,r,c)==(earlier,'reference','candidate') and(p,t) in(('beta','later'),('alpha','farther'))
    v['r5kq']=lambda s,p,role,a,topic,r,c,t:(s,p,role,r,c,t)==('alpha',person,'beta','reference','candidate',point)
    period=bindings[4] if len(bindings)==5 else 'alpha'
    v['r5jd']=lambda p,r,c,start,end:(p,r,c,start,end)==(period,'reference','candidate','anchor','later')
    history=('anchor','later','farther')
    v['ic']=lambda a,b,c:c=='candidate' and a in history and b in history and history.index(a)<history.index(b)
    return v

@lru_cache(None)
def future_checks():
    rows={};boundaries=('r5lb','r5jy','r5kq','r5jd')
    for root,length in (('r5ld',4),('r5le',5)):
        d=fixture((root,),'q[t[k '+root+'[k zbindings[] k zreference[]]][k zcandidate[]]].',boundaries)
        for person in DOMAIN:
            for point in ('anchor','later','farther','outside'):
                v=future_model(d,point,person,('alpha',)*length)
                actual=run(d,v);want=(person,point) in(('beta','later'),('alpha','farther'))
                assert actual==[want],(root,person,point,actual);rows[root+':'+person+':'+point]=actual[0]
        for i in range(length):
            b=tuple('beta' if i==j else 'alpha' for j in range(length));v=future_model(d,bindings=b)
            assert run(d,v)==[True],(root,i)
            v['zbindings']=lambda:SequenceValue(('alpha',)*length,'"individual"');assert run(d,v)==[False],(root,i)
        for size in (length-1,length+1):
            v=future_model(d,bindings=('alpha',)*length);v['zbindings']=lambda:SequenceValue(('alpha',)*size,'"individual"')
            assert run(d,v)==[False]
        v=future_model(d,bindings=('alpha',)*length)
        v['r5jd']=lambda p,r,c,start,end:(p,r,c,start,end)==('alpha','reference','candidate','anchor','farther')
        assert run(d,v)==[root=='r5ld']
        rows[root+':inquiry_before_resumption_end']=root=='r5ld'
    return dict(posterity_point_and_end_inclusive=rows,all_binding_positions_and_exact_lengths=True,
        boundaries=['r5lb; native scope above','r5jy; native in scope above and pinned','r5kq; pinned native inquiry','r5jd; pinned native bounded interval'])

@lru_cache(None)
def choice_checks():
    d=fixture(('r5lh',),'q[t[k r5lh[k zbindings[] k zreference[]]][k zcandidate[]]].',('r5lc',));rows={}
    def model(variant='baseline',b=('alpha',)*4):
        v=base(d,b);actor,response,_,_=b
        v['r5lc']=lambda *a:a==(*b,'reference','candidate') and variant!='missing_duties'
        v['cg']=lambda p,a,t:(p,a,t)==(actor,response,'anchor') and variant!='no_action'
        def policy(p,a,target,bindings,r,sign,t):
            code=normalized(target);items=normalized(bindings)
            expected=[actor,response,'reference','anchor']
            changes={'wrong_actor':(0,'beta'),'wrong_response':(1,'beta'),'wrong_reference':(2,'outside'),'wrong_anchor':(3,'later')}
            if variant in changes:i,value=changes[variant];expected[i]=value
            if(p,a,r,t)!=tuple(expected):return False
            if code==('r5ld',0):
                want=b if variant!='wrong_bindings' else ('beta',)*4
                return items==want and ((not sign and variant!='no_policy') or (sign and variant=='conflict'))
            if code==('r5le',0):return sign and items==(*b,'beta' if variant=='other_period_resume' else 'alpha') and variant in('resume','other_period_resume')
            return False
        v['h26ft']=policy
        return v
    for variant in ('baseline','missing_duties','no_action','no_policy','conflict','resume','other_period_resume','wrong_actor','wrong_response','wrong_bindings','wrong_reference','wrong_anchor'):
        actual=run(d,model(variant));assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
    for i in range(4):
        b=tuple('beta' if i==j else 'alpha' for j in range(4));v=model(b=b);assert run(d,v)==[True]
        v['zbindings']=lambda:SequenceValue(('alpha',)*4,'"individual"');assert run(d,v)==[False]
    for n in ('cg','h26ft','h26fw'):
        v=model();v[n]=unknown
        try:run(d,v)
        except ValueError as e:assert 'Unknown' in str(e)
        else:raise AssertionError(n)
    return dict(native_choice_and_no_resumption=rows,quoted_future_not_executed=True,unknown_rejected=True,boundary='r5lc; scope checked separately')

@lru_cache(None)
def rights_checks():
    results={}
    d=fixture(('r5lg',),'q[t[k r5lg[k zbindings[] k zreference[]]][k zcandidate[]]].',('r5kv',))
    for i in range(2):
        b=tuple('beta' if j==i else 'alpha' for j in range(2));v=base(d,b)
        v['r5kv']=lambda *a:a==('alpha',b[0],'beta',b[1],'reference','candidate')
        assert run(d,v)==[True]
        v['zbindings']=lambda:SequenceValue(('alpha',)*2,'"individual"');assert run(d,v)==[False]
    for length in (1,3):
        v['zbindings']=lambda:SequenceValue(('alpha',)*length,'"individual"');assert run(d,v)==[False]
    results['r5lg_self_choice_fixed_source_and_role']=True
    for root,target,length in (('r5li','r5lg',2),('r5lj','r5lh',4)):
        d=fixture((root,),'q[t[k '+root+'[k zbindings[]]][k zcandidate[]]].',(target,))
        v=base(d,('alpha',)*length);v[target]=lambda b,r:content({'candidate'}) if(normalized(b),r)==(('alpha',)*length,'reference') else content(set())
        assert run(d,v)==[True];v['h26f2']=lambda:'outside';assert run(d,v)==[False];results[root]=True
    d=fixture(('r5lk',),'q[t[k r5lk[k zalpha[] k zanchor[] k zlater[]]][k zcandidate[]]].',('r5cs',));v=base(d)
    v['r5cs']=lambda *a:a==('alpha','reference','baseline','candidate','anchor','later')
    assert run(d,v)==[True];v['h26ar']=lambda r:'outside';assert run(d,v)==[False]
    for root,target,length in (('r5lm','r5li',2),('r5ln','r5lj',4)):
        d=fixture((root,),'q[k '+root+'[k zalpha[] '+' '.join('k zalpha[]' for _ in range(length))+' k zcandidate[]]].')
        expected=('alpha','alpha','alpha','beta',(target,0),('alpha',)*length,'reference','candidate')
        rows={}
        for variant in ('baseline','no_infringement','no_disrespect','other_rights','other_actor','other_role','other_target','other_bindings','other_reference','other_candidate'):
            v=base(d);wanted=list(expected)
            changes={'other_rights':(1,'beta'),'other_actor':(2,'beta'),'other_role':(3,'alpha'),'other_target':(4,('r5lg',0)),
                'other_bindings':(5,('beta',)*length),'other_reference':(6,'outside'),'other_candidate':(7,'baseline')}
            if variant in changes:i,value=changes[variant];wanted[i]=value
            v['h26bt']=lambda *a:normalized(a)==tuple(wanted) and variant!='no_infringement'
            v['h26bv']=lambda *a:normalized(a)==tuple(wanted) and variant!='no_disrespect'
            actual=run(d,v);assert actual==[variant=='baseline'],(root,variant,actual);rows[variant]=actual[0]
        results[root]=rows
    return dict(fixed_reference_adapters=results,native_dual_appraisal=True,progress_uses_same_three_way_disjunction=True,appraisal_does_not_execute_choice=True,
        boundaries=['r5kv only for self choice adapter; pinned native personal choice','r5lg/r5lh only for fixed-reference adapter checks','r5cs only for progress adapter; pinned definition unchanged'])

@lru_cache(None)
def combined_checks():
    d=fixture(('r5lo',),'q[t[k r5lo[]][k zoutside[]]].',('r5lg','r5lh','r5lc','r5kn','ta'));rows={}
    for variant in ('baseline','no_rights','not_sacred','no_self_appraisal','no_posterity_appraisal','wrong_protected_rights','wrong_evaluation_point','no_executed_renunciation','no_executed_and_no_rights'):
        v=base(d);v['aa']=lambda p:p in DOMAIN;v['ta']=lambda *a:True
        v['r5kn']=lambda s,p,role,r:(s,role,r)==('alpha','beta','reference')
        v['h257z']=lambda r,c,t:(r,c,t)==('reference','candidate','anchor')
        v['r5lc']=lambda a,b,e,g,r,c:(a,b,e,g,r,c)==('beta','alpha','alpha','alpha','reference','candidate')
        v['h26f3']=lambda target,b,r,c:r=='reference' and c=='candidate' and (
            (normalized(target)==('r5lg',0) and normalized(b)==('alpha','alpha')) or
            (normalized(target)==('r5lh',0) and normalized(b)==('beta','alpha','alpha','alpha')))
        active=variant not in('no_executed_renunciation','no_executed_and_no_rights')
        v['r5lg']=lambda b,r:content({'candidate'}) if active and (normalized(b),r)==(('alpha','alpha'),'reference') else content(set())
        v['r5lh']=lambda b,r:content({'candidate'}) if active and (normalized(b),r)==(('beta','alpha','alpha','alpha'),'reference') else content(set())
        v['h26f4']=lambda s,rights,h,development,r:(s,rights,h,normalized(development),r)==('alpha','alpha','beta',('r5lk',0),'reference') and variant not in('no_rights','no_executed_and_no_rights')
        v['h26f5']=lambda rights,s,r:(rights,s,r)==('alpha','alpha','reference') and variant!='not_sacred'
        def appraisal(s,rights,actor,role,target,b,r,c):
            wanted_rights='beta' if variant=='wrong_protected_rights' else 'alpha'
            wanted_point='baseline' if variant=='wrong_evaluation_point' else 'candidate'
            if(s,rights,role,r,c)!=('alpha',wanted_rights,'beta','reference',wanted_point):return False
            return ((actor,normalized(target),normalized(b))==('alpha',('r5li',0),('alpha','alpha')) and variant!='no_self_appraisal') or (
                (actor,normalized(target),normalized(b))==('beta',('r5lj',0),('beta','alpha','alpha','alpha')) and variant!='no_posterity_appraisal')
        v['h26bt']=appraisal;v['h26bv']=appraisal
        actual=run(d,v);assert actual==[variant in('baseline','no_executed_renunciation')],(variant,actual);rows[variant]=actual[0]
    return dict(shared_rights_and_both_conditional_branches=rows,rights_not_conditional_on_actual_renunciation=True,
        native=['r5lo','r5ll','r5lm','r5ln'],boundaries=['r5lg/r5lh actual conduct','r5lc/r5kn scope','ta valid timeline; native in scope evidence'])

def reading_record():
    u=next(x for x in read(INVENTORY)['units'] if x['id']=='kant-1784:u0013');start=u['text'].index('aber auf sie',2678)
    pages=read('data/personal-enlightenment-choice-reading-v1.json')['primary_pages']
    return dict(status='partial_personal_and_posterity_renunciation_rights',source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[start,2985],text=u['text'][start:2985]),
        interpretation=LIMITS,new_verified_characters=0,whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,
        primary_pages=pages,unresolved=['足による踏みつけの見立ての提示','mehr nochの増幅、zwar/aberの対照','全文への帰属と通読'],
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
    assert read(READING)==reading_record() and len(sources[2].document['statements'])==104
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),roundtrips=True,preserved_main_statements=104,semantic_review_characters_added=0)

def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))

def build_report():
    results={}
    for name,fn in (('scope',scope_checks),('future',future_checks),('choice',choice_checks),('rights',rights_checks),('combined',combined_checks),('structure',structure_checks)):
        results[name]=fn();print(name+' checked',flush=True)
    paths=set(catalog().source_sha256)|{LIBRARY,BASIS,DOC,READING,INVENTORY,*PRIORS,*(x['path'] for x in read(READING)['primary_pages']),
        'scripts/compose_renunciation_rights.py','scripts/check_renunciation_rights.py','tests/test_renunciation_rights.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/compose_protected_remarks.py',
        'scripts/check_posterity_harm.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/check_covenant_nullity.py'}
    return dict(status='personal_and_posterity_renunciation_as_infringement_of_same_rights',document=LIBRARY,**results,
        alignment=dict(**reading_record()['source'],statements=[],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
