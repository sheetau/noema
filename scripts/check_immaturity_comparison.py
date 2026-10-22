"""Check native topical capacity, same-state imputation and independent maxima."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_immaturity_comparison import ROOT,LIBRARY,BASIS,MEANINGS,PRIMITIVES,LIMITS,PROFILES,parent,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown

DOC='docs/immaturity-comparison-v1.md';READING='data/immaturity-comparison-reading-v1.json'
INDEX='data/semantic-review-index-v201.json';INVENTORY='artifacts/written-units-v1/kant-1784.json'
SOURCE='data/ninth-paragraph-source-reading-v1.json'
PRIORS=('reports/topical-standing-v1.json','reports/bodily-acquisition-v1.json','reports/eighth-paragraph-v1.json')
TOPICS=('religion','arts','sciences')
DOMAIN=('person','other','group',*TOPICS,'one','two','faculty','actone','acttwo','methodone','methodtwo')
SCENES=('reference','now','trial','good','bad')
def z(n):return 'k z'+n+'[]'
def args(ns):return ' '.join(z(n) for n in ns)
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def codeid(c):return c.rank,json.loads(c.syntax)
def literal(symbol,ns,rank=0):
    return (rank,dict(kind='apply',function=dict(kind='function_ref',symbol=symbol),arguments=[dict(kind='call',symbol='z'+n,arguments=[]) for n in ns]))
def applied(code,symbol):
    body=json.loads(code.syntax)
    if body.get('kind')!='apply' or body.get('function')!=dict(kind='function_ref',symbol=symbol):return None
    return tuple(a.get('symbol','').removeprefix('z') for a in body['arguments'])
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(query,roots):
    d=deepcopy(catalog().document);d['statements']=[]
    extra=''.join('r z'+n+'[] '+('a' if n in DOMAIN else 'd')+'.' for n in (*DOMAIN,*SCENES))
    extra+='r znamepick[a '+' '.join('i[a]' for n in DOMAIN)+'] i[a].'
    extra+='r zrefpick[d '+' '.join('i[d]' for n in SCENES)+'] i[d].'
    extra+='d h223g[item a] i[a][k znamepick[v item '+' '.join('r['+z(n)+']' for n in DOMAIN)+']].'
    extra+='d h223h[point d] i[d][k zrefpick[v point '+' '.join('r['+z(n)+']' for n in SCENES)+']].'
    extra+='d h26kb[matter a reference d] i[a][k h223g[v matter]].'
    p=parse('p:'+extra);ns={r['name'] for r in p['declarations']}
    d['declarations']=p['declarations']+[r for r in d['declarations'] if r['name'] not in ns]
    d['declarations']=closure(d,(*roots,*ns))
    return parse(format_graph(d,'compact')+query)
def run(d,v):return evaluate(d,v,DOMAIN,SCENES,True)
def rejects(d,v):
    try:run(d,v)
    except ValueError as e:assert 'Unknown' in str(e),str(e)
    else:raise AssertionError('Unknown accepted as incapacity or comparative maximum')
def model(d,passes=(True,False)):
    v={r['name']:unknown for r in d['declarations'] if r['kind']=='primitive'}
    v.update({'z'+n:lambda n=n:n for n in (*DOMAIN,*SCENES)})
    def task(c):
        a=applied(c,'r6bu');return a[0] if a in (('one','reference'),('two','reference')) else None
    def identity(p,c):return p=='person' and task(c) is not None
    v.update(znamepick=lambda p,*cs:cs[DOMAIN.index(p)],zrefpick=lambda p,*cs:cs[SCENES.index(p)],
        aa=lambda p:p in ('person','other'),h246c=lambda g,p,r:g=='group' and p in ('person','other') and r=='reference',
        h26ka=lambda p,t,m,r:(p,t,r)==('person','religion','reference') and m in ('one','two'),
        ab=lambda f,p,t:(f,p)==('faculty','person'),ac=lambda p,f,a,t:(p,f)==('person','faculty') and a in ('actone','acttwo') and t=='good',
        h227z=lambda a,m,r:(a,m) in (('actone','one'),('acttwo','two')) and r=='reference',ad=lambda *a:False,
        ae=lambda p,m,t:p=='person' and m in ('methodone','methodtwo') and t=='trial',
        af=lambda p,m,t,u:p=='person' and m in ('methodone','methodtwo') and t=='trial' and u in ('good','bad'),
        ap=lambda p,m,t,u:p=='person' and m in ('methodone','methodtwo') and t=='trial' and u==('good' if passes[m=='methodtwo'] else 'bad'),
        hzuq=lambda p,c,a,t:identity(p,c) and t=='trial',hzur=lambda p,c,a,t:identity(p,c),hzus=lambda p,c,t:identity(p,c) and t=='trial',
        hzut=lambda *a:False,hzuu=lambda p,c,m,a,t:identity(p,c) and m==('methodone' if task(c)=='one' else 'methodtwo'),hzuv=lambda p,c,m,a,t:identity(p,c),
        h26se=lambda p,c,t:p=='person' and codeid(c)==literal('r6by',('religion','reference'),1),
        h26sf=lambda topic,ref:topic in TOPICS and ref=='reference',h26j7=lambda topic,ref:(topic,ref)==('religion','reference'),
        h26si=lambda c,p,r:p=='group' and r=='reference',h26sj=lambda c,p,r:p=='group' and r=='reference')
    scores=dict(zip(TOPICS,(2,1,0)))
    def compare(left,right,people,reference):
        a,b=applied(left,'r6bz'),applied(right,'r6bz')
        return people=='group' and reference=='reference' and a is not None and b is not None and a[0] in TOPICS and b[0] in TOPICS and a[1]==b[1]=='reference' and scores[a[0]]<=scores[b[0]]
    v.update(h26sg=compare,h26sh=compare)
    return v

@lru_cache(None)
def capacity_checks():
    query=''.join('q[t[c[k '+n+'['+args(('religion','reference'))+']]['+z('person')+']]['+z('now')+']].' for n in ('r6bw','r6bx','r6by','r6bz'))
    d=fixture(query,('r6bw','r6bx','r6by','r6bz'));rows=[]
    for bits in product((False,True),repeat=2):
        got=run(d,model(d,bits));assert got==[True,all(bits),not all(bits),not all(bits)],(bits,got)
        rows.append(dict(task_capacities=list(bits),values=got))
    v=model(d);cases={}
    for case in ('empty_topic','missing_profile','changed_basis','unclassified_method','unassessed_method','wrong_matter_name','wrong_reference_name','no_imputation','wrong_state_imputation','wrong_person_imputation','only_preparation','guided','wrong_activity_matter'):
        w=dict(v);expected=[True,False,True,True]
        if case=='empty_topic':w['h26ka']=lambda *a:False;expected=[False]*4
        if case=='missing_profile':w['hzuq']=lambda p,c,a,t:applied(c,'r6bu')==('one','reference') and t=='trial';expected=[False]*4
        if case=='changed_basis':w['hzur']=lambda *a:False;expected=[False]*4
        if case=='unclassified_method':w['hzuv']=lambda p,c,m,a,t:m!='methodtwo';expected=[False]*4
        if case=='unassessed_method':w['ap']=lambda p,m,t,u:m!='methodtwo' and v['ap'](p,m,t,u);expected=[False]*4
        if case=='wrong_matter_name':w['znamepick']=lambda p,*cs:cs[DOMAIN.index('one' if p=='two' else p)];expected=[False]*4
        if case=='wrong_reference_name':w['zrefpick']=lambda p,*cs:cs[-1];expected=[False]*4
        if case=='no_imputation':w['h26se']=lambda *a:False;expected[-1]=False
        if case=='wrong_state_imputation':w['h26se']=lambda p,c,t:codeid(c)==literal('r6by',('arts','reference'),1);expected[-1]=False
        if case=='wrong_person_imputation':w['h26se']=lambda p,c,t:p=='other';expected[-1]=False
        if case=='only_preparation':w['hzuu']=lambda *a:False
        if case=='guided':w['ad']=lambda o,p,a,t:(o,p,t)==('other','person','good')
        if case=='wrong_activity_matter':w['h227z']=lambda a,m,r:(a,m,r)==('actone','sciences','reference')
        got=run(d,w);assert got==expected,(case,got,expected);cases[case]=got
    for n in ('h26ka','hzuq','hzuv','ap','h26se','h227z','ad'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    return dict(all_task_capacity_combinations=rows,cases=cases,native_capacity_and_self_use_bodies=True,
        assessed_incapacity_distinguished_from_unknown=True,same_state_imputation=True,unknown_rejected=True)

@lru_cache(None)
def comparison_checks():
    q=''.join('q[k '+n+'['+args(('religion','group','reference'))+']].' for n in ('r6b5','r6b6','r6b7'))
    d=fixture(q,('r6b5','r6b6','r6b7'));v=model(d);assert run(d,v)==[True]*3;count=0
    # One comparison can vary independently while the other remains maximal.
    for relation in ('h26sg','h26sh'):
        for levels in product(range(3),repeat=3):
            w=dict(v);score=dict(zip(TOPICS,levels))
            w[relation]=lambda a,b,p,r,score=score:applied(a,'r6bz')[0] in TOPICS and applied(b,'r6bz')[0] in TOPICS and score[applied(a,'r6bz')[0]]<=score[applied(b,'r6bz')[0]]
            maximum=levels[0]==max(levels);want=[maximum,True,maximum] if relation=='h26sg' else [True,maximum,maximum]
            assert run(d,w)==want,(relation,levels);count+=1
    rows={}
    for case in ('empty_scope','religion_outside_scope','empty_people','nonhuman_people','wrong_topic_name','wrong_reference_name','not_religion','no_harm','no_dishonor','incomparable_harm','cyclic_dishonor'):
        w=dict(v);want=[False]*3
        if case=='empty_scope':w['h26sf']=lambda *a:False
        if case=='religion_outside_scope':w['h26sf']=lambda t,r:t in ('arts','sciences')
        if case=='empty_people':w['h246c']=lambda *a:False
        if case=='nonhuman_people':w['aa']=lambda *a:False
        if case=='wrong_topic_name':w['znamepick']=lambda p,*cs:cs[DOMAIN.index('arts' if p=='religion' else p)]
        if case=='wrong_reference_name':w['zrefpick']=lambda p,*cs:cs[-1]
        if case=='not_religion':w['h26j7']=lambda *a:False;want=[True,True,False]
        if case=='no_harm':w['h26si']=lambda *a:False;want=[False,True,False]
        if case=='no_dishonor':w['h26sj']=lambda *a:False;want=[True,False,False]
        if case=='incomparable_harm':
            w['h26sg']=lambda a,b,p,r:v['h26sg'](a,b,p,r) and {applied(a,'r6bz')[0],applied(b,'r6bz')[0]}!={'religion','arts'};want=[False,True,False]
        if case=='cyclic_dishonor':
            w['h26sh']=lambda a,b,p,r:(applied(a,'r6bz')[0],applied(b,'r6bz')[0]) in {(x,x) for x in TOPICS}|{('religion','arts'),('arts','sciences'),('sciences','religion')};want=[True,False,False]
        got=run(d,w);assert got==want,(case,got,want);rows[case]=got
    for n in ('h26sf','h26sg','h26sh','h26si','h26sj','h246c'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    # Comparison must work even when the quoted state's truth is unavailable.
    w=dict(v)
    for n in ('h26ka','hzuq','ap','h26se','ab','ac'):w[n]=unknown
    assert run(d,w)==[True]*3
    return dict(independent_comparison_cases=count,cases=rows,tied_maxima_allowed=True,
        positive_harm_and_dishonor_separately_required=True,state_truth_not_executed=True,unknown_rejected=True)

@lru_cache(None)
def binding_checks():
    codes='r['+z('religion')+'] r['+z('reference')+']'
    q='q[e[k r6b2['+codes+']][r b[c[p r6bz]['+args(('religion','reference'))+']]]].'
    d=fixture(q,('r6b2',));v=model(d);assert run(d,v)==[True]
    for topic,ref in (('arts','reference'),('religion','now')):
        q='q[e[k r6b2['+codes+']][r b[c[p r6bz]['+args((topic,ref))+']]]].'
        e=fixture(q,('r6b2',));assert run(e,model(e))==[False]
    q='q[k r6b7['+args(('religion','group','reference'))+']].';d=fixture(q,('r6b7',));v=model(d);seen={n:[] for n in ('h26sg','h26sh','h26si','h26sj')}
    for n in seen:
        original=v[n]
        def record(*a,n=n,original=original):
            seen[n].append(tuple(codeid(x) if hasattr(x,'syntax') else x for x in a));return original(*a)
        v[n]=record
    assert run(d,v)==[True]
    for n in ('h26sg','h26sh'):
        assert seen[n] and all(row[-2:]==('group','reference') for row in seen[n])
        assert all(c==literal('r6bz',(topic,'reference'),1) for row in seen[n] for c in row[:2] for topic in [c[1]['arguments'][0]['symbol'].removeprefix('z')])
    assert seen['h26si']==seen['h26sj']==[(literal('r6bz',('religion','reference'),1),'group','reference')]
    return dict(quote_matches_independent_literal=True,comparison_and_positive_predicates_use_same_state=True,same_people_and_reference=True)

def reading_record():
    u=next(u for u in read(INVENTORY)['units'] if u['id']=='kant-1784:u0016')
    return dict(status='same_topical_immaturity_two_maxima_partial',source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[289,389],text=u['text'][289:389]),
        interpretation=LIMITS,whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,new_verified_characters=0,
        unresolved=['本文の著者・統治者全体・作品・比較集団・基準への参照供給','回顧・離脱句の説明・二理由と最上級評価の照応・追加提示','第一文全文帰属・通読'],
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in (LIBRARY,BASIS,DOC,INVENTORY,SOURCE,*PRIORS)})
@lru_cache(None)
def structure_checks():
    c=catalog();old=parent();assert not c.document['statements'] and len(old.document['statements'])==117
    for n,e in c.entries.items():
        if n in old.entries:assert e['declaration']==old.entries[n]['declaration'] and e['meaning_ja']==old.entries[n]['meaning_ja']
    for p in (*PRIORS,SOURCE):validate_hashes(ROOT,read(p)['source_sha256'])
    validate_hashes(ROOT,read(BASIS)['import_source_sha256']);assert read(READING)==reading_record()
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b
    for notation in ('compact','full'):
        t=format_graph(c.document,notation);assert parse(t)==parse(transcribe(t,alphabet='v2'))==c.document
    ranks={};t=format_graph(c.document,'compact')
    for name in MEANINGS:
        for rank,label in enumerate(('','b','c')):
            try:parse(t+'q[e[r '+label+'[p '+name+']][r '+label+'[p '+name+']]].')
            except ValueError as e:assert 'Quoted evaluation' in str(e),str(e)
            else:ranks[name]=rank;break
    assert ranks=={n:int(n not in ('r6bu','r6bv')) for n in MEANINGS},ranks
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),inherited_meanings_preserved=True,
        roundtrips=True,minimum_quote_ranks=ranks,new_verified_characters=0)
def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))
def build_report():
    results={}
    for n,f in (('capacity',capacity_checks),('comparisons',comparison_checks),('binding',binding_checks),('structure',structure_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(catalog().source_sha256)|{LIBRARY,BASIS,DOC,READING,INDEX,INVENTORY,SOURCE,*PRIORS,
        'scripts/compose_immaturity_comparison.py','scripts/check_immaturity_comparison.py','tests/test_immaturity_comparison.py',
        'scripts/compose_bodily_acquisition.py','scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py'}
    return dict(status='topical_self_incurred_immaturity_and_maxima_checked_partial',document=LIBRARY,**results,
        alignment=dict(**read(READING)['source'],statements=[],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
