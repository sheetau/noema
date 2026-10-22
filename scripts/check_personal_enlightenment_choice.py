"""Check duty coverage, inquiry, temporal scopes and distinct practical choices."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import Content,SequenceValue
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_personal_enlightenment_choice import ROOT,LIBRARY,BASIS,PRIMITIVES,MEANINGS,LIMITS,parent,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown
from scripts.check_covenant_nullity import normalized
from scripts.check_persistent_compact_progress import base as period_base,SCENES,DOMAIN,EXTRA

REPORT='reports/personal-enlightenment-choice-v1.json'
READING='data/personal-enlightenment-choice-reading-v1.json'
DOC='docs/personal-enlightenment-choice-v1.md'
INVENTORY='artifacts/written-units-v1/kant-1784.json'
PAGE='artifacts/personal-enlightenment-v1/page-490.jpg'
PRIORS=('reports/fixed-compact-sentence-v1.json','reports/cognitive-acquisition-v1.json','reports/human-enlightenment-block-v1.json','reports/persistent-compact-progress-v1.json','reports/civic-levy-refusal-v1.json')
FIVE=' '.join('k zalpha[]' for _ in range(5))
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
def base(d,bindings=('alpha',)*5):
    v={x['name']:unknown for x in d['declarations'] if x['kind']=='primitive'}
    v.update({'z'+n:lambda n=n:n for n in (*DOMAIN,*SCENES)})
    v.update(zbindings=lambda:SequenceValue(bindings,'"individual"'),h26fw=lambda r,c:'start',h26ar=lambda r:'assessment')
    return v

def duty_model(d,variant='baseline'):
    v=base(d);v['h26ar']=unknown
    v['aa']=lambda p:p=='alpha' and variant!='nonhuman'
    v['h26ad']=lambda i,r:r=='reference' and i in DOMAIN
    def duty(source,person,role,target,b,r,sign,point):
        return (source,person,role,normalized(target),r,sign,point)==('alpha','alpha','beta',('r5kl',1),'reference',variant!='negative_requirement','reference') and normalized(b) in(('alpha','alpha'),('alpha','beta')) and variant!='no_duties'
    v['h237z']=duty
    v['h226u']=lambda p,r,t:(p,r)==('alpha','reference') and t in DOMAIN and not(variant=='missing_topic' and t=='beta')
    v['h26fu']=lambda topic,item,r:r=='reference' and topic==item and not(variant=='unmapped_duty' and item=='beta')
    if variant=='wrong_reference':v['zreference']=lambda:'assessment'
    return v

@lru_cache(None)
def duty_checks():
    d=fixture(('r5kn','r5ko'),'q[k r5kn[k zalpha[] k zalpha[] k zbeta[] k zreference[]]].q[k r5ko[k zalpha[] k zalpha[] k zbeta[] k zbeta[] k zreference[]]].');rows={}
    for variant in ('baseline','no_duties','negative_requirement','nonhuman','missing_topic','unmapped_duty','wrong_reference'):
        actual=run(d,duty_model(d,variant));assert actual==[variant=='baseline']*2,(variant,actual);rows[variant]=actual
    for n in ('h237z','h26fu','h226u'):
        v=duty_model(d);v[n]=unknown
        try:run(d,v)
        except ValueError as e:assert 'Unknown' in str(e)
        else:raise AssertionError(n)
    return dict(native_complete_duty_mapping=rows,knowledge_success_not_evaluated=True,unknown_rejected=True,boundaries=[])

@lru_cache(None)
def goal_checks():
    adapters={}
    for root,target in (('r5kl','r5cl'),('r5kp','r5aa')):
        d=fixture((root,),'q[t[k '+root+'[k zbindings[] k zreference[]]][k zcandidate[]]].',(target,));positions=[]
        for i in range(2):
            b=tuple('beta' if j==i else 'alpha' for j in range(2));v=base(d,b)
            expected=(*b,'reference',*(['assessment'] if root=='r5kl' else []),'candidate')
            v[target]=lambda *a:a==expected
            assert run(d,v)==[True]
            v['zbindings']=lambda:SequenceValue(('alpha',)*2,'"individual"');assert run(d,v)==[False];positions.append(i)
        for length in (1,3):
            v['zbindings']=lambda:SequenceValue(('alpha',)*length,'"individual"');assert run(d,v)==[False]
        adapters[root]=positions
    d=fixture(('r5kq',),'q[k r5kq[k zalpha[] k zalpha[] k zbeta[] k zbeta[] k zbeta[] '+CTX+' k zstart[]]].',('r5ko',));rows={}
    for variant in ('baseline','no_duty_topic','not_inquiry','no_action','dead','outside_history','no_goal','other_actor','other_activity','other_goal','other_bindings','other_reference','other_point'):
        v=base(d)
        v['r5ko']=lambda *a:a==('alpha','alpha','beta','beta','reference') and variant!='no_duty_topic'
        v['h257z']=lambda r,c,p:(r,c,p)==('reference','candidate','start') and variant!='outside_history'
        v['h256o']=lambda p,c,t:(p,c,t)==('alpha','candidate','start') and variant!='dead'
        v['h26fx']=lambda *a:a==('alpha','beta','beta','reference') and variant!='not_inquiry'
        v['cg']=lambda p,a,t:(p,a,t)==('alpha','beta','start') and variant!='no_action'
        expected=['alpha','beta',('r5kp',0),('alpha','beta'),'reference','start']
        changes={'other_actor':(0,'beta'),'other_activity':(1,'alpha'),'other_goal':(2,('r5kl',0)),
            'other_bindings':(3,('beta','alpha')),'other_reference':(4,'assessment'),'other_point':(5,'end')}
        if variant in changes:i,value=changes[variant];expected[i]=value
        v['h26fv']=lambda *a:normalized(a)==tuple(expected) and variant!='no_goal'
        actual=run(d,v);assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
    return dict(two_object_goal_adapters=adapters,native_inquiry_execution_and_goal=rows,
        boundaries=['r5cl/r5aa for goal adapters only','r5ko for inquiry wiring; native mapping checked separately'],quoted_goal_not_executed=True)

def temporal_model(d,point='start',bindings=('alpha',)*5):
    v=base(d,bindings);history=('before','start','middle','end','after')
    source,person,role,response,period=bindings
    v['h26fw']=lambda a,r:'start' if(a,r)==(response,'reference') else 'before'
    v['r5jd']=lambda p,r,c,s,e:(p,r,c,s,e)==(period,'reference','candidate','start','end')
    v['h26e3']=lambda p,r,c,t:(p,r,c)==(period,'reference','candidate') and t in ('start','middle')
    v['h257z']=lambda r,c,t:(r,c)==('reference','candidate') and t in history
    v['ic']=lambda a,b,c:c=='candidate' and a in history and b in history and history.index(a)<history.index(b)
    v['r5kq']=lambda s,p,role_,a,t,r,c,at:(s,p,role_,r,c,at)==(source,person,role,'reference','candidate',point)
    return v

@lru_cache(None)
def temporal_checks():
    queries=''.join('q[t[k '+n+'[l[a]['+(FIVE if n!='r5ku' else FOUR)+'] k zreference[]]][k zcandidate[]]].' for n in ('r5kr','r5ks','r5ku'))
    d=fixture(('r5kr','r5ks','r5ku'),queries,('r5jd','r5kq'));rows={}
    for p in ('before','start','middle','end','after','outer'):
        actual=run(d,temporal_model(d,p));expected=[p in('start','middle'),p in('end','after'),p in('start','middle','end','after')]
        assert actual==expected,(p,actual);rows[p]=actual
    adapters={}
    for root,length in (('r5kr',5),('r5ks',5),('r5ku',4)):
        d=fixture((root,),'q[t[k '+root+'[k zbindings[] k zreference[]]][k zcandidate[]]].',('r5jd','r5kq'));positions=[]
        for i in range(length):
            five=tuple('beta' if j==i else 'alpha' for j in range(5));v=temporal_model(d,'end' if root=='r5ks' else 'start',five)
            v['zbindings']=lambda:SequenceValue(five[:length],'"individual"')
            assert run(d,v)==[True],(root,i)
            v['zbindings']=lambda:SequenceValue(('alpha',)*length,'"individual"')
            # With a different response, the default anchor is before the event;
            # future continuation still includes it, but the anchor identity
            # is separately checked in actual choices below.
            assert run(d,v)==[root=='r5ku' and i==3],(root,i);positions.append(i)
        for size in (length-1,length+1):
            v['zbindings']=lambda:SequenceValue(('alpha',)*size,'"individual"');assert run(d,v)==[False]
        adapters[root]=positions
    return dict(native_temporal_quantification=rows,exact_binding_lengths=adapters,
        boundaries=['r5jd for interval wiring; native interval in choice checks','r5kq; inquiry tested natively separately'])

@lru_cache(None)
def choice_checks():
    d=fixture(('r5kt','r5kv'),'q[k r5kt['+FIVE+' '+CTX+']].q[k r5kv['+FOUR+' '+CTX+']].',('r5kn',));rows={}
    defer={('r5kr',5,False),('r5ks',5,True)};renounce={('r5ku',4,False)}
    cases={'defer':defer,'renounce':renounce,'neither':set(),'both':defer|renounce,
        'no_resumption':{('r5kr',5,False)},'no_pause':{('r5ks',5,True)},
        'conflicting_pause':defer|{('r5kr',5,True)},'conflicting_resume':defer|{('r5ks',5,False)},
        'conflicting_renunciation':renounce|{('r5ku',4,True)},
        'other_period_resume':renounce,'no_action':defer,'no_scope':defer,'wrong_anchor':defer,'invalid_period':defer}
    def model(variant):
        v=period_base(d);v['h26fw']=lambda a,r:'middle' if variant=='wrong_anchor' else 'start'
        v['r5kn']=lambda s,p,role,r:(s,p,role,r)==('alpha','alpha','alpha','reference') and variant!='no_scope'
        v['cg']=lambda p,a,t:(p,a,t)==('alpha','alpha','start') and variant!='no_action'
        def policy(p,response,target,b,r,sign,at):
            name,rank=normalized(target);bindings=normalized(b)
            if(p,response,r,at,rank)!=('alpha','alpha','reference','start',0):return False
            if variant=='other_period_resume' and(name,bindings,sign)==('r5ks',('alpha',)*4+('beta',),True):return True
            return bindings==('alpha',)*len(bindings) and(name,len(bindings),sign) in cases[variant]
        v['h26ft']=policy
        if variant=='invalid_period':v['h26ex']=lambda *a:False
        return v
    for variant in cases:
        actual=run(d,model(variant));expected=[variant=='defer',variant=='renounce']
        assert actual==expected,(variant,actual);rows[variant]=actual
    for n in ('h26ft','cg','h26fw'):
        v=model('defer');v[n]=unknown
        try:run(d,v)
        except ValueError as e:assert 'Unknown' in str(e)
        else:raise AssertionError(n)
    return dict(distinct_deferred_and_renounced_choices=rows,native_bounded_period_and_history=True,
        actual_future_execution_not_evaluated=True,unknown_choice_rejected=True,boundary='r5kn only; native duty mapping above')

def reading_record():
    u=next(u for u in read(INVENTORY)['units'] if u['id']=='kant-1784:u0013');end=u['text'].index('es sei',2678)
    pages=[*read('data/fixed-compact-sentence-reading-v1.json')['original_pages'],dict(path=PAGE,url='https://api.digitale-sammlungen.de/iiif/image/v2/bsb10926843_00530/full/full/0/default.jpg',sha256=digest((ROOT/PAGE).read_bytes()))]
    return dict(status='partial_personal_enlightenment_choices',source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[2678,end],text=u['text'][2678:end]),
        interpretation=LIMITS,new_verified_characters=0,whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,
        primary_pages=pages,primary_evidence=[dict(url='https://korpora.org/kant/aa08/039.html',lines='33–37',observation='本人の一時延期と、本人・後代についての放棄を対照する。原刊489頁末から490頁冒頭も表示して照合した。')],
        unresolved=['規範出所・立場の固定、kannの許容と本人・期間の限定','後世についての放棄','神聖な人類の権利と侵害・踏みにじる見立て','zwar/aber/mehr noch、全文帰属・通読'],
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in (LIBRARY,BASIS,DOC,INVENTORY,*(x['path'] for x in pages),*PRIORS)})

@lru_cache(None)
def structure_checks():
    c=catalog();old=parent()
    for n in read(BASIS)['imported_symbols']:
        assert c.entries[n]['declaration']==old.entries[n]['declaration'] and c.entries[n]['meaning_ja']==old.entries[n]['meaning_ja']
    for p in PRIORS:validate_hashes(ROOT,read(p)['source_sha256'])
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b
    for notation in ('compact','full'):
        s=format_graph(c.document,notation);assert parse(s)==parse(transcribe(s,alphabet='v2'))==c.document
    assert read(READING)==reading_record() and len(old.document['statements'])==104
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),roundtrips=True,preserved_main_statements=104,semantic_review_characters_added=0)

def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))

def build_report():
    results={}
    for name,fn in (('duty',duty_checks),('goals',goal_checks),('temporal',temporal_checks),('choice',choice_checks),('structure',structure_checks)):
        results[name]=fn();print(name+' checked',flush=True)
    paths=set(catalog().source_sha256)|{LIBRARY,BASIS,DOC,READING,INVENTORY,*PRIORS,*(x['path'] for x in read(READING)['primary_pages']),
        'scripts/compose_personal_enlightenment_choice.py','scripts/check_personal_enlightenment_choice.py','tests/test_personal_enlightenment_choice.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/compose_protected_remarks.py',
        'scripts/check_persistent_compact_progress.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/check_covenant_nullity.py'}
    return dict(status='personal_epistemic_duty_and_distinct_deferral_renunciation_choices',document=LIBRARY,**results,
        alignment=dict(**reading_record()['source'],statements=[],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
