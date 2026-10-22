"""Check the integrated qualification, metaphor, comparison and quoted speech."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import Content,FunctionValue
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.compose_qualified_speech_sentence import ROOT,FULL,CORE,BASIS,ANNOTATIONS,LEGACY,MEANINGS,PRIMITIVES,LIMITS,NODE_INFO,parent,dependencies,legacy,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown

DOC='docs/qualified-speech-sentence-v1.md';READING='data/qualified-speech-sentence-reading-v1.json'
REPORT='reports/qualified-speech-sentence-v1.json';INDEX='data/semantic-review-index-v203.json'
INVENTORY='artifacts/written-units-v1/kant-1784.json';SOURCE='data/tenth-paragraph-source-reading-v1.json';LEXICAL='data/shadow-reading-review-v2.json'
PRIORS=tuple('reports/'+p+'-v1.json' for p in ('political-quoted-speech','republic-speech-prohibition','military-peace-guarantee','enlightened-person-conditions','prospect-grounded-apprehension','cast-shadow','described-apprehension','legislative-freedom-sentence'))
DOMAIN=('a','b');SCENES=('reference','now','outer','other','context')
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def unit():return next(u for u in read(INVENTORY)['units'] if u['id']=='kant-1784:u0017')
def content(f):return Content(SCENES,tuple(f(t) for t in SCENES))
def atom(n):return dict(kind='call',symbol=n,arguments=[])
def desc(rank,body):return rank,json.dumps(body,sort_keys=True)
def applied(n,*args,rank=7):return desc(rank,dict(kind='apply',function=dict(kind='function_ref',symbol=n),arguments=[atom(a) for a in args]))
def code(n):return desc(5,atom(n))
def norm(xs):return tuple(desc(v.rank,json.loads(v.syntax)) if hasattr(v,'syntax') else v for v in xs)
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(roots,query,boundaries=(),names=False):
    d=deepcopy(catalog().document);d['statements']=[]
    for r in d['declarations']:
        if r['name'] in boundaries:r.update(kind='primitive',parameters=[p['sort'] for p in r['parameters']]);r.pop('body')
    extra='r za[] a.r zb[] a.r zcommunity[] a.r znow[] d.r zouter[] d.r h26wo[] a.r h26wp[] d.'
    if names:
        extra+='r znpick[a i[a] i[a]] i[a].d h223g[item a] i[a][k znpick[v item r[k h26wo[]] r[k zcommunity[]]]].'
        extra+='r zrp[d i[d] i[d]] i[d].d h223h[item d] i[d][k zrp[v item r[k h26wp[]] r[k zouter[]]]].'
    prefix=parse('p:'+extra)['declarations'];ns={r['name'] for r in prefix}
    d['declarations']=prefix+[r for r in d['declarations'] if r['name'] not in ns]
    d['declarations']=closure(d,(*roots,*ns));return parse(format_graph(d,'compact')+query)
def model(d):
    v={r['name']:unknown for r in d['declarations'] if r['kind']=='primitive'}
    v.update(za=lambda:'a',zb=lambda:'b',zcommunity=lambda:'b',znow=lambda:'now',zouter=lambda:'outer',h26wo=lambda:'a',h26wp=lambda:'reference',
      h26wr=lambda:'a',h26ws=lambda:'b',h26km=lambda:'reference',h26kn=lambda _: 'now',
      znpick=lambda item,a,b:a if item=='a' else b,zrp=lambda item,a,b:a if item=='reference' else b)
    return v
def run(d,v,domain=DOMAIN):return evaluate(d,v,domain,SCENES,True)
def rejects(d,v,domain=DOMAIN):
    try:run(d,v,domain)
    except ValueError as e:assert 'Unknown' in str(e),str(e)
    else:raise AssertionError('Unknown accepted')

@lru_cache(None)
def shadow_checks():
    q='q[t[c[k r6gd[k h26wp[]]][k za[]]][k znow[]]].'
    d=fixture(('r6gd',),q);v=model(d)
    v.update(h26wi=lambda r,s,p,t:(r,s,p,t)==('reference','a','a','now'),
      h26wj=lambda r,p,l,path,t:(r,p,l,path,t)==('reference','a','b','b','now'),
      h26wk=lambda r,path,b,t:(r,path,b,t)==('reference','b','b','now'),
      h26wl=lambda r,b,path,t:(r,b,path,t)==('reference','b','b','now'),
      h26wm=lambda r,b,path,t:(r,b,path,t)==('reference','b','b','now'),
      h26wn=lambda r,region,l,t:(r,region,l,t)==('reference','a','b','now'))
    assert run(d,v)==[True];cases={}
    for n in ('h26wi','h26wj','h26wk','h26wl','h26wm','h26wn'):
        w=dict(v);w[n]=lambda *a:False;assert run(d,w)==[False],n;cases[n]=False
        w=dict(v);w[n]=unknown;rejects(d,w)
    for n,value in (('h26wp','outer'),('za','b'),('znow','other')):
        w=dict(v);w[n]=lambda value=value:value;assert run(d,w)==[False],n
    # Capture each wrapper input with independently varied callback positions.
    b=fixture(('r6gd',),q,('rvt',));w=model(b);calls=[]
    for n in ('h26wi','h26wj','h26wk','h26wl','h26wm','h26wn'):
        def rec(*args,n=n):calls.append((n,args));return True
        w[n]=rec
    def region(s,b,r,t,contains,emits,route,clear,intercepts,opaque):
        if (s,b,r,t)!=('a','b','a','now'):return False
        for fn,n,arity in ((contains,'h26wn',3),(emits,'h26wi',3),(route,'h26wj',4),(clear,'h26wk',3),(intercepts,'h26wl',3),(opaque,'h26wm',3)):
            for bits in product(DOMAIN,repeat=arity-1):
                before=len(calls);fn(*bits,'other');assert calls[before:]==[(n,('reference',*bits,'other'))]
        return True
    w['rvt']=region;assert run(b,w)==[True]
    return dict(native_shadow_region=True,cases=cases,empty_region_and_missing_optical_conditions_rejected=True,
      all_six_wrapper_argument_positions_checked=True,boundary='rvt only in the separate adapter test; the full native optical body runs above.')

@lru_cache(None)
def literal_checks():
    d=fixture(('r6ge',),'q[t[c[k r6ge[k h26wp[]]][k za[]]][k znow[]]].',names=True);v=model(d)
    v.update(h26u4=lambda p,e,t:(p,e,t)==('a','b','now'),h26u5=lambda e,g,t:(e,norm((g,))[0],t)==('b',applied('r6gd','h26wp',rank=0),'now'),
      h26u6=lambda e,t:(e,t)==('b','now'),h26u7=lambda e,t,p:(e,t,p)==('b','now','other'),h26va=lambda p,r,x:(p,r,x)==('a','reference','other'))
    assert run(d,v)==[False]
    for n in ('h26u4','h26u5','h26u6','h26u7','h26va'):
        w=dict(v);w[n]=lambda *a:False;assert run(d,w)==[True],n
        w=dict(v);w[n]=unknown;rejects(d,w)
    w=dict(v);w['h26u5']=lambda *a:False;w['zrp']=lambda item,a,b:b;assert run(d,w)==[False]
    assert all(v[n] is unknown for n in ('h26wi','h26wj','h26wk','h26wl','h26wm','h26wn'))
    q=fixture(('r6gl',),'q[e[k r6gl[r[k h26wp[]]]][r h[c[p r6ge][k h26wp[]]]]].')
    assert run(q,{r['name']:unknown for r in q['declarations'] if r['kind']=='primitive'})==[True]
    return dict(native_literal_fear_and_negation=True,same_closed_shadow_target=True,actual_shadow_existence_not_required=True,
      bad_reference_name_rejected=True,quoted_depiction_not_executed=True)

@lru_cache(None)
def content_checks():
    q=''.join('q[t[k '+n+'[]][k '+point+'[]]].' for point in ('znow','zouter') for n in ('r6gi','r6gj','r6gk'))
    d=fixture(('r6gk',),q,('r6f4','r6gc'));v=model(d)
    def values(left=True,right=True):
        w=dict(v);w['r6f4']=lambda top,c,r:content(lambda t:left and c in DOMAIN and(top,r,t)==('a','reference','now'))
        w['r6gc']=lambda s,role,r:content(lambda t:right and(s,role,r,t)==('a','b','reference','now'));return w
    for a,b in product((False,True),repeat=2):assert run(d,values(a,b))==[a,b,a and b]*2
    w=values();w['r6f4']=lambda top,c,r:content(lambda t:c=='a');assert run(d,w)==[False,True,False]*2
    for n,value in (('h26wo','b'),('h26wp','outer'),('h26kn','other'),('h26wr','b'),('h26ws','a')):
        w=values();w[n]=lambda *a,value=value:value;assert not run(d,w)[2],n
    for n in ('r6f4','r6gc'):
        w=values();w[n]=unknown;rejects(d,w)
    q='q[t[c[k r6gh[k zb[] k h26wp[]]][k za[]]][k znow[]]].q[t[c[k r6gf[k h26wp[]]][k za[]]][k znow[]]].q[t[c[k r6gg[k zb[] k h26wp[]]][k za[]]][k znow[]]].'
    b=fixture(('r6gh','r6gf','r6gg'),q,('r6f3','r6et','r6fo'),names=True);w=model(b)
    w.update(r6f3=lambda p,c,r,t:(p,c,norm((r,))[0],t)==('a','b',desc(0,atom('h26wp')),'now'),
      r6et=lambda p,r:content(lambda t:(p,r,t)==('a','reference','now')),r6fo=lambda p,c,r:content(lambda t:(p,c,r,t)==('a','b','reference','now')))
    assert run(b,w)==[True]*3
    for n in ('r6f3','r6et','r6fo'):
        bad=dict(w);bad[n]=unknown;rejects(b,bad)
    for name,value in (('za','b'),('zb','a'),('h26wp','outer'),('znow','other')):
        bad=dict(w);bad[name]=lambda value=value:value;assert run(b,bad)!=[True]*3,name
    return dict(both_sides_required=True,all_communities_quantified=True,fixed_present_at_both_outer_points=True,same_person_fear_army_and_ability=True,
      boundaries='r6f4/r6gc for the two whole contents; r6f3/r6et/r6fo for profile projection. Unchanged full bodies and meanings are pinned in prior reports.')

def check_rows(d,rows,v,domain):
    def values(expected):
        w=dict(v);w.update({n:lambda *a,allowed=rs:norm(a) in allowed for n,rs in expected.items()});return w
    assert run(d,values(rows),domain)==[True];mutations=0
    for n,rs in rows.items():
        for row in rs:
            for i in range(len(row)):
                changed=deepcopy(rows);changed[n].remove(row);bad=list(row);bad[i]='__mismatch__';changed[n].add(tuple(bad))
                assert run(d,values(changed),domain)==[False],(n,i);mutations+=1
    for n in rows:
        w=values(rows);w[n]=unknown;rejects(d,w,domain)
    return mutations,values(rows)

@lru_cache(None)
def discourse_checks():
    nodes=(*NODE_INFO,'h26um');domain=(*nodes,'author','topic','scope','community','standard','role','wrong')
    def values(d):
        v=model(d);v.update({n:lambda n=n:n for n in nodes})
        v.update(wa=lambda:'author',h26wo=lambda:'topic',h26wt=lambda:'scope',h26wr=lambda:'standard',h26ws=lambda:'role',
          h26wq=lambda:'context',zcommunity=lambda:'community',znpick=lambda item,a,b:a if item=='topic' else b);return v
    d=fixture(('r6gm',),'q[k r6gm[k zcommunity[]]].',names=True);v=values(d);whole=code('r6gk')
    boundary=applied('r6fp','h26wo','zcommunity','h26wp');pair=applied('r6ez','h26wo','h26wp')
    rows={
      'h26nq':{('h26xb','author','scope','h26xc',boundary,applied('r6ex','h26wo','h26wp'),'context')},
      'h26nn':{('h26xc','author','scope',boundary,pair,'context')},
      'h26wu':{('h26xd','author','scope',boundary,applied('r6ge','h26wp'),applied('r6gf','h26wp'),'context')},
      'h26wv':{('h26xe','author','scope',boundary,pair,applied('r6gg','zcommunity','h26wp'),'context')},
      'h26ww':{('h26w7','author',whole,boundary,applied('r6gh','zcommunity','h26wp'),'community','reference','now','context')}}
    first,checked=check_rows(d,rows,v,domain)
    w=dict(checked);w['znpick']=lambda item,a,b:a;assert run(d,w,domain)==[False]
    w=dict(checked);w['zrp']=lambda item,a,b:b;assert run(d,w,domain)==[False]
    q=fixture(('r6gn',),'q[k r6gn[]].',('r6gm',),names=True);v=values(q)
    target=applied('r6f5','h26wp',rank=2)
    pairs=(('h26um','h26w4'),('h26w5','h26w6'),('h26w6','h26w7'),('h26xa','h26xg'),('h26xc','h26xd'),('h26xd','h26xe'),('h26xe','h26xf'),('h26xf','h26xg'),('h26xg','h26xi'),('h26xi','h26xk'),('h26xk','h26xl'))
    rows={
      'h26ub':{('h26w4','author',whole,'context')},'h26uc':{('h26w5','author',whole,code('r6ei'),whole,'context')},
      'h26wx':{('h26w6','author',whole,code('r6ei'),whole,'context')},'r6gm':{(c,) for c in domain},
      'h26wz':{('h26xi','author',whole,code('r6gi'),code('r6gj'),'context')},
      'h26wy':{(n,'author',whole,'h26xk',target,'context') for n in ('h26xh','h26xj')},
      'h26w2':{('h26xk','author',whole,target,applied('r2ug','h26wp',rank=1),applied('r2uh','h26wp',rank=1),'context')},
      'ue':{(a,b,'context') for a,b in pairs}}
    second,checked=check_rows(q,rows,v,domain)
    return dict(argument_mutations=first+second,same_complete_profile_for_self_metaphor_and_simultaneous_contrast=True,
      same_quoted_permission_and_obedience=True,both_anaphors_bound=True,previous_sentence_and_order_bound=True,quotation_not_executed=True,unknown_rejected=True,
      boundary='r6gm only in whole-disourse scope test; its actual body and inherited r6e5/r6fq/r6e2 constructors execute separately above.')

FRAGMENTS=(
 ('Aber auch nur derjenige, der, ',['r6gi','h26uc','h26wx','h26ww'],'先行文への対照と追加、発言能力から人物条件への必要条件。'),
 ('selbst aufgeklärt, ',['r6e5','r6ex','h26nq'],'宗教・法・統治を含む同じ本人の判断能力を強調。'),
 ('sich nicht vor Schatten fürchtet, ',['r6gd','r6ge','r6gf','h26wu'],'字義の影への恐れの否定を、同じ人の根拠のない恐れの不在へ比喩として結ぶ。'),
 ('zugleich aber ',['h26wv','r6fp'],'同じ本人・点で精神的条件に軍隊条件を対照的に加える。'),
 ('ein wohldisciplinirtes zahlreiches Heer ',['r6fh','r6fb'],'同じ軍隊の軍事的任務、人数、全計画の要求適合。'),
 ('zum Bürgen der öffentlichen Ruhe ',['r6fl','r6fm','r572'],'同じ共同体の公的平穏への、通常の全関連事態・背景での保証。'),
 ('zur Hand hat, – ',['r6fo','r6fp'],'同じ本人が現在利用できる同じ制度・軍隊。'),
 ('kann das sagen, ',['r6f3','r6gi','h26wy'],'同じ引用方針・許可・平穏を両立できる政治的能力とdasの照応。'),
 ('was ein Freistaat nicht wagen darf: ',['r6gc','r6fu','r6gb','r6gj','h26wz','h26wy'],'明示した共和政の種類について、同じ引用発言の危険認識付き試みへの政治的禁止。'),
 ('räsonnirt so viel ihr wollt, ',['r2ug','r2ue','h26w2'],'同じ出所・全宛先について、各人が望む量の議論への許可。'),
 ('und worüber ihr wollt; ',['r2ug','r2ue','h26w2'],'同じ人の全話題と全量の組合せへの許可。'),
 ('nur gehorcht!',['r2uh','r2uf','r6fv','h26w2'],'この同じ呼びかけへの唯一の留保として、指示に従う履行を要求する命令。'))
def reading_record():
    u=unit();cursor=0;clauses=[]
    for fragment,ns,reading in FRAGMENTS:
        assert u['text'][cursor:cursor+len(fragment)]==fragment,(cursor,fragment)
        assert all(n in catalog().entries for n in ns),ns
        clauses.append(dict(range=[cursor,cursor+len(fragment)],text=fragment,definitions=ns,reading=reading));cursor+=len(fragment)
    assert cursor==303 and sum(not c.isspace() for c in u['text'][:cursor])==257
    return dict(status='qualified_speech_sentence_reviewed_under_explicit_reading',reviewer='assistant_review',document=FULL,meaning_basis=BASIS,
      source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,cursor],text=u['text'][:cursor]),selection=selection_binding(catalog(),[119]),
      clauses=clauses,interpretation=LIMITS,unresolved=[],decision='equivalent_under_stated_reading_for_qualified_speech_sentence',
      whole_sentence_semantically_verified=True,whole_unit_semantically_verified=False,newly_reviewed_sentence_characters=257,semantic_equivalence_automatically_proved=False,
      holistic_review=[r for _,_,r in FRAGMENTS]+['12断片と原文第一文を通読し、否定・量化・能力・禁止・同時性・比喩・引用と留保、同じ本人と主体・基準の束縛を確認した。後続の三文はこの判断に含まない。'],
      source_sha256={p:digest((ROOT/p).read_bytes()) for p in (FULL,CORE,BASIS,ANNOTATIONS,DOC,INVENTORY,SOURCE,LEXICAL,*PRIORS)})
@lru_cache(None)
def structure_checks():
    c=catalog();old=parent();assert c.document['statements'][:-1]==old.document['statements'] and len(c.document['statements'])==120
    for source in (old,*dependencies()):
        for n,e in source.entries.items():
            if n in c.entries:assert c.entries[n]['declaration']==e['declaration'] and c.entries[n]['meaning_ja']==e['meaning_ja'],n
    for ds,ms,_ in legacy():
        for row in ds:assert c.entries[row['name']]['declaration']==row and c.entries[row['name']]['meaning_ja']==ms[row['name']]
    reviews=load_reviews(ROOT,INDEX)['works']['kant-1784'];assert len(reviews)==19
    for row in reviews:assert row['selection']==selection_binding(c,[s['index'] for s in row['selection']['statements']])
    for p in (*PRIORS,SOURCE):validate_hashes(ROOT,read(p)['source_sha256'])
    validate_hashes(ROOT,read(BASIS)['import_source_sha256']);load_annotations(ROOT,BASIS,ANNOTATIONS)
    assert read(ANNOTATIONS)['entries']==read('data/legislative-freedom-sentence-identifiers-v1.json')['entries']
    assert read(READING)==reading_record()
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b,p
    core=parse((ROOT/CORE).read_text(encoding='utf-8'))
    for notation in ('compact','full'):
        t=format_graph(core,notation);assert parse(t)==parse(transcribe(t,alphabet='v2'))==core
    ranks={};t=format_graph(core,'compact')
    for n in MEANINGS:
        for rank,label in enumerate(('','b','c','d','e','f','g','h')):
            try:parse(t+'q[e[r '+label+'[p '+n+']][r '+label+'[p '+n+']]].')
            except ValueError as e:assert 'Quoted evaluation' in str(e),str(e)
            else:ranks[n]=rank;break
    assert ranks=={n:5 if n=='r6gn' else 0 if n in ('r6gd','r6gf') else 1 for n in MEANINGS},ranks
    return dict(preserved_statements=119,added_statements=1,preserved_whole_unit_reviews=19,new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),
      minimum_quote_ranks=ranks,roundtrip_scope='new core compact/full/v2; inherited manuscript and meanings unchanged')
def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))
def build_report():
    results={}
    for n,f in (('shadow',shadow_checks),('literal',literal_checks),('content',content_checks),('discourse',discourse_checks),('structure',structure_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(build())|set(catalog().source_sha256)|{INDEX,READING,DOC,INVENTORY,SOURCE,LEXICAL,*PRIORS,
      'scripts/compose_qualified_speech_sentence.py','scripts/check_qualified_speech_sentence.py','tests/test_qualified_speech_sentence.py',
      'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/compose_prince_sentence.py','scripts/compose_qualified_prince_frame.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py'}
    return dict(status='qualified_speech_sentence_checked_under_explicit_reading',document=FULL,**results,
      alignment=dict(**read(READING)['source'],statements=[119],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
      whole_sentence_semantically_verified=True,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
      source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
