"""Check complete current population and fixed-time collective dialogue adapters."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import Content,Message,FunctionValue
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_present_epoch_assessment import ROOT,LIBRARY,BASIS,MEANINGS,LIMITS,parent,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown
from scripts.check_covenant_nullity import normalized

DOC='docs/present-epoch-assessment-v1.md'
READING='data/present-epoch-assessment-reading-v1.json'
REPORT='reports/present-epoch-assessment-v1.json'
INVENTORY='artifacts/written-units-v1/kant-1784.json'
PRIORS=('reports/collective-attainment-v1.json','reports/qualified-judgment-v1.json','reports/epoch-undertakings-v1.json','reports/sixth-paragraph-v1.json')
PEOPLE=('alice','bob','carol');DOMAIN=(*PEOPLE,'group','epoch','pastperson','futureperson','outsider','topic','matter')
SCENES=('reference','candidate','past','now','future','outside');TIMES=('past','now','future')
EXTRA=''.join('r z'+n+'[] '+('a' if n in DOMAIN else 'd')+'.' for n in (*DOMAIN,*SCENES))
EXTRA+='r zassessed[a] e.r zcapable[a] e.r zprogress[] e.r zstandard[h[a] c h[a] c d] c.'
FRAME='k zalice[] k zgroup[] k zepoch[] k zreference[] k zcandidate[] k znow[]'
CHECKED=FRAME+' p zassessed p zstandard';ATTAINED=CHECKED+' p zcapable';CONTRAST=ATTAINED+' k zprogress[]'

def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(roots,query,boundaries=(),extra=''):
    d=deepcopy(catalog().document)
    for x in d['declarations']:
        if x['name'] in boundaries:x.update(kind='primitive',parameters=[p['sort'] for p in x['parameters']]);x.pop('body')
    d.update(declarations=closure(d,roots),statements=[])
    return parse(format_graph(d,'compact')+EXTRA+extra+query)
def content(points):return Content(SCENES,tuple(p in points for p in SCENES))
def run(d,v):return evaluate(d,v,DOMAIN,SCENES,True)
def rejects_unknown(d,v):
    try:run(d,v)
    except ValueError as e:assert 'Unknown' in str(e)
    else:raise AssertionError('Unknown accepted')
def base(d,capable=(True,True,False),assessed=(True,True,True),progress=True,threshold=2):
    v={x['name']:unknown for x in d['declarations'] if x['kind']=='primitive'}
    v.update({'z'+n:lambda n=n:n for n in (*DOMAIN,*SCENES)})
    def standard(people,success,point):
        return point=='now' and all(people(p)==(p in PEOPLE) for p in DOMAIN) and sum(success(p) for p in DOMAIN)>=threshold
    v.update(aa=lambda p:p in (*PEOPLE,'pastperson','futureperson'),
        h26aa=lambda *a:a==('epoch','reference'),
        h257z=lambda r,c,p:(r,c)==('reference','candidate') and p in TIMES,
        ic=lambda a,b,c:c=='candidate' and a in TIMES and b in TIMES and TIMES.index(a)<TIMES.index(b),
        h26ab=lambda e,r,c,p:(e,r,c)==('epoch','reference','candidate') and p in TIMES,
        h246c=lambda g,p,r:(g,r)==('group','reference') and p in PEOPLE,
        h256o=lambda p,c,t:c=='candidate' and (p in PEOPLE and t in TIMES or (p,t) in (('pastperson','past'),('futureperson','future'))),
        zassessed=lambda p:content({'now'} if p in PEOPLE and assessed[PEOPLE.index(p)] else set()),
        zcapable=lambda p:content({'now'} if p in PEOPLE and capable[PEOPLE.index(p)] else set()),
        zprogress=lambda:content({'now'} if progress else set()),zstandard=standard)
    return v

@lru_cache(None)
def frame_checks():
    d=fixture(('r5sc',),'q[k r5sc['+FRAME+']].');rows={}
    for variant in ('baseline','omit_living','include_past','include_future','include_nonhuman','empty','speaker_outside','wrong_epoch','current_outside','hole','wrong_reference','wrong_candidate'):
        v=base(d)
        if variant in ('omit_living','include_past','include_future','include_nonhuman','empty'):
            members={'omit_living':PEOPLE[:2],'include_past':(*PEOPLE,'pastperson'),'include_future':(*PEOPLE,'futureperson'),
                'include_nonhuman':(*PEOPLE,'outsider'),'empty':()}[variant]
            v['h246c']=lambda g,p,r:(g,r)==('group','reference') and p in members
        if variant=='speaker_outside':v['zalice']=lambda:'pastperson'
        if variant=='wrong_epoch':v['zepoch']=lambda:'group'
        if variant=='current_outside':v['znow']=lambda:'outside'
        if variant=='hole':v['h26ab']=lambda e,r,c,p:(e,r,c)==('epoch','reference','candidate') and p in ('past','future')
        if variant=='wrong_reference':v['zreference']=lambda:'outside'
        if variant=='wrong_candidate':v['zcandidate']=lambda:'outside'
        actual=run(d,v);assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
    for name in ('aa','h246c','h256o','h26aa','h26ab','h257z','ic'):
        v=base(d);v[name]=unknown;rejects_unknown(d,v)
    return dict(complete_current_population=rows,epoch_interval_and_current_point_checked=True,unknown_rejected=True)

@lru_cache(None)
def collective_checks():
    specs=(('r5sd',CHECKED),('r5se',ATTAINED),('r5sf',FRAME+' k zprogress[]'),('r5sg',CONTRAST))
    d=fixture(tuple(n for n,_ in specs),''.join('q[k '+n+'['+a+']].' for n,a in specs));count=0
    for capability in product((False,True),repeat=3):
        for assessment in product((False,True),repeat=3):
            for progress in (False,True):
                checked=all(assessment);attained=checked and sum(capability)>=2
                actual=run(d,base(d,capability,assessment,progress))
                assert actual==[checked,attained,progress,checked and not attained and progress],(capability,assessment,progress,actual)
                count+=1
    rows={}
    for variant in ('two_of_three','unanimity','outsider_success','other_time_capability','other_time_progress','invalid_standard','unassessed'):
        v=base(d);want=[True,True,True,False]
        if variant=='unanimity':v=base(d,threshold=3);want=[True,False,True,True]
        if variant=='outsider_success':v['zcapable']=lambda p:content({'now'} if p in ('alice','outsider') else set());want=[True,False,True,True]
        if variant=='other_time_capability':v['zcapable']=lambda p:content({'past'});want=[True,False,True,True]
        if variant=='other_time_progress':v['zprogress']=lambda:content({'future'});want=[True,True,False,False]
        if variant=='invalid_standard':v['zstandard']=lambda *a:True;want=[False,False,True,False]
        if variant=='unassessed':v=base(d,assessed=(True,True,False));want=[False,False,True,False]
        actual=run(d,v);assert actual==want,(variant,actual);rows[variant]=actual
    for n in ('zassessed','zcapable','zstandard','zprogress'):
        v=base(d);v[n]=unknown;rejects_unknown(d,v)
    return dict(combinations=count,same_current_group_and_criterion=rows,unknown_rejected=True,numeric_threshold_only_test_fixture=True)

@lru_cache(None)
def fixed_dialogue_checks():
    specs=(('r5sh',ATTAINED),('r5si',CONTRAST),('r5sl',ATTAINED),('r5sm',FRAME+' k zprogress[]'))
    queries=''.join('q[t[k '+n+'['+a+']][k z'+p+'[]]].' for n,a in specs for p in ('past','now','future'))
    queries+='l[k r5sj['+ATTAINED+']].l[k r5sk['+CONTRAST+']].'
    d=fixture(tuple(n for n,_ in specs)+('r5sj','r5sk'),queries);rows=[]
    for capability,assessed,progress in product(((False,False,False),(True,True,False)),(True,False),(True,False)):
        v=base(d,capability,(assessed,)*3,progress);actual=run(d,v)
        attained=assessed and sum(capability)>=2;contrast=assessed and not attained and progress;negative=assessed and not attained
        assert actual[:12]==[x for value in (attained,contrast,negative,progress) for x in (value,)*3]
        question,answer=actual[-2:];assert isinstance(question,Message) and isinstance(answer,Message)
        assert question.force=='ask' and answer.force=='assert'
        assert question.content.values==(attained,)*len(SCENES) and answer.content.values==(contrast,)*len(SCENES)
        rows.append(dict(assessed=assessed,attained=attained,progress=progress,contrast=contrast))
    return dict(cases=rows,outer_point_does_not_rebind_present=True,question_and_assertion_distinct=True,no_actual_speech_inferred=True)

@lru_cache(None)
def quality_binding_checks():
    extra='r zanchor[] d.r ztopics[a a a d] c.r znames[a] i[a].r zsecure[a a a d d] c.r zadequate[a a a d d] c.'
    suffix='p zstandard k ztopic[] k zanchor[] p ztopics p znames r[k zanchor[]] r[p zsecure] r[p zadequate]'
    queries=''.join('q[k '+root+'['+FRAME+' '+suffix+(' k zprogress[]' if root=='r5sp' else '')+']].' for root in ('r5sn','r5so','r5sp','r5sq'))
    d=fixture(('r5sn','r5so','r5sp','r5sq'),queries,('r5sd','r5se','r5sg','hzvr','hzvs'),extra)
    calls=[]
    def values(checked=True,capable=True):
        v=base(d);v['zanchor']=lambda:'now';v['ztopics']=unknown;v['znames']=unknown;v['zsecure']=unknown;v['zadequate']=unknown
        def wrapped(*a,ability=False):
            calls.append((ability,normalized(a[:2]+a[4:])))
            correct=normalized(a[:2]+a[4:])==('topic','now',('zanchor',0),('zsecure',0),('zadequate',0))
            return FunctionValue(('individual',),'content',lambda p:content({'now'} if correct and p=='alice' and (capable if ability else checked) else set()))
        v['hzvr']=wrapped;v['hzvs']=lambda *a:wrapped(*a,ability=True)
        def boundary(*a,kind):
            if a[:6]!=('alice','group','epoch','reference','candidate','now'):return False
            check=a[6]('alice').values[3];ability=a[8]('alice').values[3] if len(a)>8 else False
            if kind=='checked':return check
            if kind=='attained':return check and ability
            return check and not ability and a[9].values[3]
        v['r5sd']=lambda *a:boundary(*a,kind='checked');v['r5se']=lambda *a:boundary(*a,kind='attained');v['r5sg']=lambda *a:boundary(*a,kind='contrast')
        return v
    rows={}
    for checked,capable in product((False,True),repeat=2):
        actual=run(d,values(checked,capable));assert actual==[checked,checked and capable,checked and not capable,checked and not capable]
        rows[str((checked,capable))]=actual
    for name in ('zanchor','zreference','zcandidate','znow'):
        v=values();v[name]=lambda:'outside';assert run(d,v)==[False]*4,name
    v=values();v['ztopic']=lambda:'matter';assert run(d,v)==[False]*4
    v=values();v['hzvr']=unknown;rejects_unknown(d,v)
    assert calls and all(a[1][2:]==(('zanchor',0),('zsecure',0),('zadequate',0)) for a in calls)
    return dict(same_quality_task_and_anchor=rows,wrong_reference_candidate_anchor_and_topic_refused=True,
        quality_descriptions_not_executed=True,boundaries=['r5sd','r5se','r5sg','hzvr','hzvs'],unknown_rejected=True)

def reading_record():
    u=next(x for x in read(INVENTORY)['units'] if x['id']=='kant-1784:u0014')
    return dict(status='present_epoch_assessment_dependency_partial',source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,147],text=u['text'][:147]),
        interpretation=LIMITS,whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,new_verified_characters=0,
        primary_pages=[dict(path='artifacts/royal-writing-oversight-v1/page-491.jpg',sha256=digest((ROOT/'artifacts/royal-writing-oversight-v1/page-491.jpg').read_bytes()),visually_inspected=True)],
        unresolved=['宗教的対象範囲とsicher und gutの具体的な読解','集団到達基準の意味規約と採用','同じ集団の進行内容','条件付きの問い・denn/nun・aber wohl・現在と著者帰属','第七段落全文の通読'],
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in (LIBRARY,BASIS,DOC,INVENTORY,*PRIORS,'artifacts/royal-writing-oversight-v1/page-491.jpg')})

@lru_cache(None)
def structure_checks():
    c=catalog();old=parent()
    for n,e in old.entries.items():
        if n in c.entries:assert c.entries[n]['declaration']==e['declaration'] and c.entries[n]['meaning_ja']==e['meaning_ja']
    assert not c.document['statements'] and len(old.document['statements'])==108
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b
    assert read(READING)==reading_record()
    for p in PRIORS:validate_hashes(ROOT,read(p)['source_sha256'])
    for notation in ('compact','full'):
        s=format_graph(c.document,notation);assert parse(s)==parse(transcribe(s,alphabet='v2'))==c.document
    return dict(new_definitions=len(MEANINGS),new_primitives=0,new_statements=0,main_statements_preserved=108,roundtrips=True,new_verified_characters=0)

def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))
def build_report():
    results={}
    for n,f in (('frame',frame_checks),('collective',collective_checks),('dialogue',fixed_dialogue_checks),('quality',quality_binding_checks),('structure',structure_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(catalog().source_sha256)|{READING,DOC,INVENTORY,*PRIORS,'artifacts/royal-writing-oversight-v1/page-491.jpg',
        'scripts/compose_present_epoch_assessment.py','scripts/check_present_epoch_assessment.py','tests/test_present_epoch_assessment.py',
        'scripts/compose_collective_attainment.py','scripts/compose_qualified_judgment.py','scripts/compose_grounded_step.py',
        'scripts/compose_qualitative_influence.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/check_covenant_nullity.py'}
    return dict(status='present_epoch_assessment_dependency_checked',document=LIBRARY,**results,
        alignment=dict(**read(READING)['source'],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
