"""Check maximum emphasis, past choice and nonexecution of enlightenment."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_retrospective_emphasis import ROOT,LIBRARY,BASIS,MEANINGS,PRIMITIVES,LIMITS,parent,build
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown

DOC='docs/retrospective-emphasis-v1.md';READING='data/retrospective-emphasis-reading-v1.json'
INDEX='data/semantic-review-index-v201.json';INVENTORY='artifacts/written-units-v1/kant-1784.json'
SOURCE='data/ninth-paragraph-source-reading-v1.json';PRIORS=('reports/topical-guardian-interest-v1.json','reports/eighth-paragraph-v1.json')
DOMAIN=('author','other','work','otherwork','activity','religion','arts','sciences')
SCENES=('reference','before','now','after')
TOPICS=('religion','arts','sciences')
def z(n):return 'k z'+n+'[]'
def args(ns):return ' '.join(z(n) for n in ns)
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def code_is_bi(c):return c.rank==0 and json.loads(c.syntax)==dict(kind='function_ref',symbol='bi')
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(query):
    d=deepcopy(catalog().document);d['statements']=[]
    extra=''.join('r z'+n+'[] '+('a' if n in DOMAIN else 'd')+'.' for n in (*DOMAIN,*SCENES))
    return parse(format_graph(d,'compact')+extra+query)
def run(d,v):return evaluate(d,v,DOMAIN,SCENES,True)
def rejects(d,v):
    try:run(d,v)
    except ValueError as e:assert 'Unknown' in str(e),str(e)
    else:raise AssertionError('Unknown accepted as priority')
def model(d,levels=(2,1,0)):
    v={r['name']:unknown for r in d['declarations'] if r['kind']=='primitive'}
    v.update({'z'+n:lambda n=n:n for n in (*DOMAIN,*SCENES)});score=dict(zip(TOPICS,levels))
    v.update(aa=lambda p:p in ('author','other'),
        ia=lambda author,now,p:(author,now)==('author','now') and p in ('before','now','after'),
        ic=lambda a,b,now:now=='now' and SCENES.index(a)<SCENES.index(b),
        h26sd=lambda a,w,c,t,r:(a,w,r)==('author','work','reference') and code_is_bi(c) and t in TOPICS,
        h26sc=lambda a,w,c,left,right,r,t:(a,w,r)==('author','work','reference') and code_is_bi(c) and t in ('before','now') and left in TOPICS and right in TOPICS and score[left]<=score[right],
        dg=lambda a,t:(a,t)==('activity','before'),df=lambda p,a,t:(p,a,t)==('author','activity','before'),
        h26sb=lambda a,w,c,topic,r,t:(a,w,topic,r,t)==('activity','work','religion','reference','before') and code_is_bi(c),
        h26j7=lambda topic,r:(topic,r)==('religion','reference'))
    return v
FRAME=args(('author','work'))+' r[p bi] '+args(('religion','reference','now'))

@lru_cache(None)
def maximum_checks():
    d=fixture('q[k r6bq['+FRAME+']].');cases=[]
    for levels in product(range(3),repeat=3):
        got=run(d,model(d,levels));assert got==[levels[0]==max(levels)],levels
        cases.append(dict(levels=list(levels),value=got[0]))
    v=model(d);rows={}
    for case in ('empty_scope','topic_outside_scope','missing_comparison','nonreflexive','cycle','wrong_author','wrong_work','wrong_concept','wrong_reference','wrong_point'):
        w=dict(v)
        if case=='empty_scope':w['h26sd']=lambda *a:False
        if case=='topic_outside_scope':w['h26sd']=lambda a,b,c,t,r:t in ('arts','sciences')
        if case=='missing_comparison':w['h26sc']=lambda a,b,c,l,r,ref,t:v['h26sc'](a,b,c,l,r,ref,t) and {l,r}!={'religion','arts'}
        if case=='nonreflexive':w['h26sc']=lambda a,b,c,l,r,ref,t:v['h26sc'](a,b,c,l,r,ref,t) and l!=r
        if case=='cycle':w['h26sc']=lambda a,b,c,l,r,ref,t:l==r or (l,r) in (('religion','arts'),('arts','sciences'),('sciences','religion'))
        if case in ('wrong_author','wrong_work','wrong_reference','wrong_point'):
            i={'wrong_author':0,'wrong_work':1,'wrong_reference':5,'wrong_point':6}[case]
            w['h26sc']=lambda *a,i=i:v['h26sc'](*(a[:i]+('after' if i>=5 else 'otherwork',)+a[i+1:]))
        if case=='wrong_concept':w['h26sc']=lambda *a:False
        got=run(d,w);assert got==[False],(case,got);rows[case]=got[0]
    for n in ('h26sd','h26sc'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    return dict(ordered_level_cases=cases,cases=rows,tied_maxima_allowed=True,full_preorder_and_membership_required=True,unknown_rejected=True)

@lru_cache(None)
def retrospective_checks():
    d=fixture('q[k r6bt['+args(('author','work','religion','reference','now'))+']].');v=model(d);assert run(d,v)==[True];rows={}
    for case in ('not_author','not_religious','no_setting','no_occurrence','no_participation','other_work','other_topic','other_reference','only_now','only_future','no_current_priority','no_prior_priority','missing_now','missing_past','cyclic_time','other_history'):
        w=dict(v)
        if case=='not_author':w['aa']=lambda *a:False
        if case=='not_religious':w['h26j7']=lambda *a:False
        if case=='no_setting':w['h26sb']=lambda *a:False
        if case=='no_occurrence':w['dg']=lambda *a:False
        if case=='no_participation':w['df']=lambda *a:False
        if case in ('other_work','other_topic','other_reference'):
            i={'other_work':1,'other_topic':3,'other_reference':4}[case]
            w['h26sb']=lambda *a,i=i:v['h26sb'](*(a[:i]+('after' if i==4 else 'otherwork',)+a[i+1:]))
        if case in ('only_now','only_future'):
            point='now' if case=='only_now' else 'after'
            w['dg']=lambda a,t,point=point:a=='activity' and t==point
            w['df']=lambda p,a,t,point=point:p=='author' and a=='activity' and t==point
            w['h26sb']=lambda a,b,c,topic,r,t,point=point:t==point
        if case in ('no_current_priority','no_prior_priority'):
            point='now' if case=='no_current_priority' else 'before'
            # At the altered point, religion is strictly lower than the others.
            w['h26sc']=lambda a,b,c,l,r,ref,t,point=point:((0 if l=='religion' else 1)<=(0 if r=='religion' else 1)) if t==point else v['h26sc'](a,b,c,l,r,ref,t)
        if case=='missing_now':w['ia']=lambda a,now,p:v['ia'](a,now,p) and p!='now'
        if case=='missing_past':w['ia']=lambda a,now,p:v['ia'](a,now,p) and p!='before'
        if case=='cyclic_time':w['ic']=lambda a,b,n:v['ic'](a,b,n) or (a,b)==('after','before')
        if case=='other_history':w['ia']=lambda a,n,p:a=='other' and p!='reference'
        got=run(d,w);assert got==[False],(case,got);rows[case]=got[0]
    for n in ('ia','ic','h26sb','h26sc','h26j7','dg','df'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    # The concept's inhabitants and their capacity/causal history are not evaluated.
    assert all(v[n] is unknown for n in ('ag','la','hzid','hziq','ab','ac'))
    return dict(cases=rows,same_past_setting_and_current_result=True,no_enlightenment_instance_required=True,unknown_rejected=True)

def reading_record():
    u=next(u for u in read(INVENTORY)['units'] if u['id']=='kant-1784:u0016')
    return dict(status='retrospective_religious_emphasis_partial',source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,154],text=u['text'][:154]),
        interpretation=LIMITS,whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,new_verified_characters=0,
        unresolved=['ichと同じ作品・本文現在の参照供給','離脱句の説明としての談話接続','統治者の関心の不在と有害さ・不名誉の最上級による二つの理由','全文帰属・通読'],
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in (LIBRARY,BASIS,DOC,INVENTORY,SOURCE,*PRIORS)})
@lru_cache(None)
def structure_checks():
    c=catalog();old=parent();assert not c.document['statements'] and len(old.document['statements'])==117
    for n,e in c.entries.items():
        if n in old.entries:assert e['declaration']==old.entries[n]['declaration'] and e['meaning_ja']==old.entries[n]['meaning_ja']
    for p in (*PRIORS,SOURCE):validate_hashes(ROOT,read(p)['source_sha256'])
    validate_hashes(ROOT,read(BASIS)['import_source_sha256'])
    assert read(READING)==reading_record()
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b
    for notation in ('compact','full'):
        t=format_graph(c.document,notation);assert parse(t)==parse(transcribe(t,alphabet='v2'))==c.document
    t=format_graph(c.document,'compact')
    for n in MEANINGS:parse(t+'q[e[r[p '+n+']][r[p '+n+']]].')
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),inherited_meanings_preserved=True,
        roundtrips=True,all_new_definitions_rank_zero=True,new_verified_characters=0)
def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))
def build_report():
    results={}
    for n,f in (('maximum',maximum_checks),('retrospective',retrospective_checks),('structure',structure_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(catalog().source_sha256)|{LIBRARY,BASIS,DOC,READING,INDEX,INVENTORY,SOURCE,*PRIORS,
        'scripts/compose_retrospective_emphasis.py','scripts/check_retrospective_emphasis.py','tests/test_retrospective_emphasis.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py'}
    return dict(status='retrospective_religious_emphasis_checked_partial',document=LIBRARY,**results,
        alignment=dict(**read(READING)['source'],statements=[],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
