"""Check full sentence binding, discourse and the two-sentence ninth paragraph."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import Content
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest,selection_binding,validate_hashes,REQUIREMENTS
from noema.script import transcribe
from scripts.compose_legislative_freedom_sentence import ROOT,FULL,CORE,BASIS,ANNOTATIONS,MEANINGS,PRIMITIVES,LIMITS,NODE_INFO,parent,dependency,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown

DOC='docs/legislative-freedom-sentence-v1.md';READING='data/legislative-freedom-sentence-reading-v1.json'
PARAGRAPH='data/ninth-paragraph-reading-v1.json';REVIEW='data/ninth-paragraph-review-v1.json'
REPORT='reports/legislative-freedom-sentence-v1.json';INDEX='data/semantic-review-index-v202.json'
INVENTORY='artifacts/written-units-v1/kant-1784.json';SOURCE='data/ninth-paragraph-source-reading-v2.json'
FIRST='data/religious-emphasis-sentence-reading-v1.json'
PRIORS=tuple('reports/'+p+'-v1.json' for p in ('royal-example','enlightened-thinking','legislative-safety-insight','legislative-public-permissions','legislative-formulations','legislative-thoughts','frank-legal-criticism','religious-emphasis-sentence'))
DOMAIN=('alpha','beta');SCENES=('reference','history','now','outer')
PAIRS=(('alpha','beta'),('beta','alpha'))
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def unit():return next(u for u in read(INVENTORY)['units'] if u['id']=='kant-1784:u0016')
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(roots,query,boundaries=(),extra=''):
    d=deepcopy(catalog().document);d['statements']=[]
    for row in d['declarations']:
        if row['name'] in boundaries:row.update(kind='primitive',parameters=[p['sort'] for p in row['parameters']]);row.pop('body')
    added=parse('p:'+extra)['declarations'] if extra else []
    ns={r['name'] for r in added};d['declarations']=added+[r for r in d['declarations'] if r['name'] not in ns]
    d['declarations']=closure(d,(*roots,*ns));return parse(format_graph(d,'compact')+query)
def run(d,v,domain=DOMAIN,scenes=SCENES):return evaluate(d,v,domain,scenes,True)
def rejects(d,v,domain=DOMAIN,scenes=SCENES):
    try:run(d,v,domain,scenes)
    except ValueError as e:assert 'Unknown' in str(e),str(e)
    else:raise AssertionError('Unknown accepted')
def content(f):return Content(SCENES,tuple(f(t) for t in SCENES))
def model(d):
    v={r['name']:unknown for r in d['declarations'] if r['kind']=='primitive'}
    v.update(wa=lambda:'alpha',h26mu=lambda:'alpha',h26ul=lambda:'beta',h26uj=lambda:'reference',h26kk=lambda:'alpha',
      h26km=lambda:'reference',h26kl=lambda w:'history',h26kn=lambda w:'now',h26sp=lambda p,c,r:p,
      znow=lambda:'now',zouter=lambda:'outer',zalpha=lambda:'alpha',zbeta=lambda:'beta',
      r6dw=lambda p,c,r,t:(p,c) in PAIRS and(r,t)==('reference','now'),
      r6d2=lambda p,c,g,r,h,a,m,s:content(lambda t:(p,c) in PAIRS and(g,r,h,a,m,s,t)==(p,'reference','history','now',p,'alpha','now')),
      r6ed=lambda e,a,w,p,c,g,r,h,t,m,s,x:(e,a,w,p,c,g,r,h,t,m,s,x)==('beta','alpha','beta','alpha','beta','alpha','reference','history','now','alpha','alpha','now'),
      r6bo=lambda p,c,g,r:(p,c) in PAIRS and(g,r)==(p,'reference'),
      h246c=lambda g,p,r:g in DOMAIN and p in DOMAIN and r=='reference',h247d=lambda p,r:p,cd=lambda s,r:s in DOMAIN and r=='reference',
      r6dg=lambda p,c,u,s,r,a,t:(p,c) in PAIRS and(u,s) in (('alpha','alpha'),('beta','beta')) and(r,a,t)==('reference','now','now'),
      r6dj=lambda p,c,u,s,r,a,h,t:(p,c) in PAIRS and(u,s) in (('alpha','alpha'),('beta','beta')) and(r,a,h,t)==('reference','now','history','now'),
      r6dq=lambda p,c,g,r,h,a:content(lambda t:(p,c) in PAIRS and(g,r,h,a,t)==(p,'reference','history','now','now')))
    return v

@lru_cache(None)
def content_checks():
    ns=('r6eg','r6eh','r6ei');q=''.join('q[t[k '+n+'[]][k z'+t+'[]]].' for t in ('now','outer') for n in ns)
    d=fixture(ns,q,('r6dw','r6d2','r6ed'),'r znow[] d.r zouter[] d.');v=model(d);assert run(d,v)==[True]*6;rows={}
    for case in ('second_head_no_insight','no_example','unsupported_head_not_required','vacuous_general_still_needs_example','wrong_subjects','wrong_reference','wrong_history','wrong_now','wrong_topic','wrong_king','wrong_author','wrong_public'):
        w=dict(v);want=[False,False,False]
        if case=='second_head_no_insight':w['r6d2']=lambda p,*a:content(lambda t:p=='alpha' and t=='now');want=[False,True,False]
        if case=='no_example':w['r6ed']=lambda *a:False;want=[True,False,False]
        if case=='unsupported_head_not_required':
            w['r6dw']=lambda p,c,r,t:(p,c,r,t)==('alpha','beta','reference','now')
            w['r6d2']=lambda p,*a:content(lambda t:p=='alpha' and t=='now');want=[True,True,True]
        if case=='vacuous_general_still_needs_example':w['r6dw']=lambda *a:False;w['r6ed']=lambda *a:False;want=[True,False,False]
        if case=='wrong_subjects':w['h26sp']=lambda p,*a:'beta' if p=='alpha' else 'alpha'
        if case=='wrong_reference':w['h26uj']=lambda:'outer';want=[True,False,False]
        if case=='wrong_history':w['h26kl']=lambda *a:'outer'
        if case=='wrong_now':w['h26kn']=lambda *a:'outer';want=[True,False,False]
        if case=='wrong_topic':w['h26kk']=lambda:'beta'
        if case=='wrong_king':w['h26mu']=lambda:'beta';want=[True,False,False]
        if case=='wrong_author':w['wa']=lambda:'beta';want=[True,False,False]
        if case=='wrong_public':w['h26ul']=lambda:'alpha';want=[True,False,False]
        got=run(d,w);assert got==want*2,(case,got,want);rows[case]=want
    for n in ('r6dw','r6d2','r6ed','h26sp'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    # Each of the three witnesses can vary independently on two values.
    ed=fixture(('r6eh',),'q[t[k r6eh[]][k znow[]]].',('r6ed',),'r znow[] d.')
    for community,manner,example in product(DOMAIN,repeat=3):
        w=model(ed);target=(example,'alpha','beta','alpha',community,'alpha','reference','history','now',manner,'alpha','now')
        w['r6ed']=lambda *a,target=target:a==target;assert run(ed,w)==[True]
    return dict(cases=rows,all_general_heads_and_communities=True,three_independent_witnesses_on_two_values=8,fixed_present_at_both_outer_points=True,
      boundary='r6dw/r6d2/r6ed only; their bodies are checked by pinned dependency reports. r6ee/r6ef/r6eg/r6eh/r6ei and all new quantification execute natively.')

@lru_cache(None)
def focus_checks():
    ns=('r6ej','r6ek','r6el');q=''.join('q[t[k '+n+'[k zalpha[] k zbeta[]]][k znow[]]].' for n in ns)
    d=fixture(ns,q,('r6bo','r6dg','r6dj','r6dq'),'r zalpha[] a.r zbeta[] a.r znow[] d.');v=model(d);assert run(d,v)==[True]*3;rows={}
    for case in ('thoughts_not_allowed','criticism_not_allowed','unsafe','one_subject_excluded','wrong_role','wrong_subject_group','wrong_history'):
        w=dict(v);want=[True]*3
        if case=='thoughts_not_allowed':w['r6dg']=lambda *a:False;want[0]=False
        if case=='criticism_not_allowed':w['r6dj']=lambda *a:False;want[1]=False
        if case=='unsafe':w['r6dq']=lambda *a:content(lambda t:False);want[2]=False
        if case=='one_subject_excluded':w['r6dj']=lambda p,c,u,*a:u=='alpha';want[1]=False
        if case=='wrong_role':w['h247d']=lambda *a:'alpha';want[:2]=[False,False]
        if case=='wrong_subject_group':w['h26sp']=lambda *a:'beta';want=[False]*3
        if case=='wrong_history':w['h26kl']=lambda *a:'outer';want[1:]=[False,False]
        assert run(d,w)==want,case;rows[case]=want
    for n in ('r6bo','r6dg','r6dj','r6dq','h247d','h246c'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    return dict(cases=rows,same_two_subjects_and_scholar_roles=True,criticism_not_inferred_from_basic_permission=True,
      boundary='r6bo/r6dg/r6dj/r6dq only, each with exact role/context bindings; new focus quantification and conjunction execute')

def code(n,rank=5,ref=False):return rank,json.dumps(dict(kind='function_ref',symbol=n) if ref else dict(kind='call',symbol=n,arguments=[]),sort_keys=True)
def norm(xs):return tuple((v.rank,json.dumps(json.loads(v.syntax),sort_keys=True)) if hasattr(v,'syntax') else v for v in xs)
@lru_cache(None)
def discourse_checks():
    d=fixture(('r6em',),'q[k r6em[]].');nodes=(*NODE_INFO,'h26sv','h26sw','h26nb');domain=(*nodes,'author','king','other');scenes=('context',)
    whole=code('r6ei');fn=lambda n:code(n,4,True)
    expected={
      'h26ub':{('h26um','author',whole,'context')},
      'h26uc':{('h26un','author',whole,code('r6ch'),whole,'context')},
      'h26ud':{('h26uo','author',whole,fn('r6ee'),fn('r6ef'),'context')},
      'h26t3':{('h26uq','author','h26sw',code('bi',0,True),'context')},
      'h26ug':{('h26up','author',whole,code('r6cc'),fn('r6ef'),'context')},
      'h26ue':{('h26ur','author',whole,fn('r6el'),'h26us','context')},
      'h26uf':{('h26ut','author',whole,fn('r6ej'),fn('r6ek'),'context')},
      'h26uh':{('h26uw','author',whole,code('r6eg'),code('r6eh'),fn('r6d4'),'context')},
      'h26ui':{('h26ux','author',whole,code('r6eh'),fn('r6d4'),fn('r6ea'),'context')},
      'h26m3':{('h26uy','author','h26nb','king','context'),('h26uz','author','h26uy','king','context')},
      'ue':{(a,b,'context') for a,b in (('h26sv','h26um'),('h26sw','h26uq'),('h26uo','h26up'),('h26up','h26u2'),('h26uu','h26uv'),('h26u3','h26uw'),('h26uw','h26ux'),('h26uy','h26uz'))}}
    def values(rows):
        v={r['name']:unknown for r in d['declarations'] if r['kind']=='primitive'}
        v.update({n:lambda n=n:n for n in nodes});v.update(wa=lambda:'author',h26mu=lambda:'king',h26uk=lambda:'context')
        v.update({n:lambda *a,allowed=rs:norm(a) in allowed for n,rs in rows.items()});return v
    assert run(d,values(expected),domain,scenes)==[True];count=0
    for n,rs in expected.items():
        for row in rs:
            for i in range(len(row)):
                changed=deepcopy(expected);changed[n].remove(row);bad=list(row);bad[i]='other';changed[n].add(tuple(bad))
                assert run(d,values(changed),domain,scenes)==[False],(n,i);count+=1
    for a,b in (('h26um','h26sv'),('h26uq','h26sw'),('h26uy','h26uz')):
        v=values(expected);v[a]=lambda b=b:b
        for n in expected:v[n]=lambda *a:True
        assert run(d,v,domain,scenes)==[False]
    for n in expected:
        v=values(expected);v[n]=unknown;rejects(d,v,domain,scenes)
    v=values(expected)
    for n in ('h26tx','h26t4','h26ua','h26nf','h26to','h26tp'):assert v[n] is unknown
    return dict(argument_mutations=count,all_discourse_contexts_and_contents_bound=True,quotation_not_executed=True,
      same_named_monarch=True,distinct_nodes=True,unknown_rejected=True)

FRAGMENTS=(
 ('Aber ',['h26uc'],'宗教を最大の論述重点に置く第一文との対照。'),
 ('die Denkungsart eines Staatsoberhaupts, ',['r6ee','r6ef','r6dy'],'一般的な国家元首の本人に属する持続的な判断の仕方。'),
 ('der die erstere begünstigt, ',['r6dw','r6dv','r6d3'],'同じ元首が第一文の啓蒙を実務的に後押しするという条件。'),
 ('geht noch weiter, und sieht ein: ',['r6d2','r6dz','h26ug'],'宗教から立法へ及ぶ同じ思考態度と根拠・把握・真理を持つ認識。'),
 ('daß selbst in Ansehung seiner Gesetzgebung ',['r6ck','r6dq','h26ue'],'同じ元首の立法にまで及ぶ認識内容への取り立て。'),
 ('es ohne Gefahr sei, ',['r6dm','r6dp','r6dr'],'同じ全許可方針に由来する公共的な損失の危険不在。'),
 ('seinen Unterthanen zu erlauben, ',['r6bo','r6dk','r37c'],'同じ元首の全臣民について三対象への積極的許可と反対要求不在。'),
 ('von ihrer eigenen Vernunft öffentlichen Gebrauch zu machen, ',['r6da','r6db','r6dd'],'本人の理解力を用いる立法についての一般の公的理性使用。'),
 ('und ihre Gedanken über eine bessere Abfassung derselben, ',['r6cq','r6cu','r6cw','r6dg'],'同じ立法のよりよい全定式についての本人の思想の全候補。'),
 ('sogar mit einer freimüthigen Kritik der schon gegebenen, ',['r6co','r6cz','r6c3','r6dj','h26uf'],'同じ既存法への、自己の評価を意図的に隠さない率直な批判を伴う思想提示への強い追加。'),
 ('der Welt öffentlich vorzulegen; ',['r53q','r6cv','r6c5'],'同じ学識者が自分の声として世界読者へ公的に提示する内容。'),
 ('davon wir ein glänzendes Beispiel haben, ',['r6eh','r6ed','r6d6','h26uh'],'同じあり方と許可方針が実現した、指定公衆に利用可能な際立つ例。'),
 ('wodurch noch kein Monarch demjenigen vorging, ',['r6ea','r6d7','h26ui','h26m3'],'同じ実例のあり方について、現在までこの君主を上回る全君主の例がない。時間的な最初にはしない。'),
 ('welchen wir verehren.',['r6ec','h26nu','h26m3'],'同じ指定公衆が、同じ先行のフリードリヒへの敬意を保持する。'))
def reading_record():
    u=unit();cursor=390;clauses=[]
    for fragment,ns,reading in FRAGMENTS:
        assert u['text'][cursor:cursor+len(fragment)]==fragment,(cursor,fragment)
        assert all(n in catalog().entries for n in ns),ns
        clauses.append(dict(range=[cursor,cursor+len(fragment)],text=fragment,definitions=ns,reading=reading));cursor+=len(fragment)
    assert cursor==905 and sum(not c.isspace() for c in u['text'][390:])==444
    return dict(status='legislative_freedom_sentence_reviewed_under_explicit_reading',reviewer='assistant_review',document=FULL,meaning_basis=BASIS,
      source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[390,cursor],text=u['text'][390:cursor]),selection=selection_binding(catalog(),[118]),
      clauses=clauses,interpretation=LIMITS,unresolved=[],decision='equivalent_under_stated_reading_for_legislative_freedom_sentence',
      whole_sentence_semantically_verified=True,whole_unit_semantically_verified=False,newly_reviewed_sentence_characters=444,semantic_equivalence_automatically_proved=False,
      holistic_review=[r for _,_,r in FRAGMENTS]+['14断片と全文を再読し、一般条件と実在例の区別、全臣民・三対象・同じ法の参照、認識の内容と談話の作用範囲を確認した。未処理語句はなく、原刊の綴りと句読法を保存する。'],
      source_sha256={p:digest((ROOT/p).read_bytes()) for p in (FULL,CORE,BASIS,ANNOTATIONS,DOC,INVENTORY,SOURCE,*PRIORS)})

PARAGRAPH_REASONS=[
 '固定u0016全905文字・780非空白文字を二文と原刊492–493頁の照合v2で確認する。空白一文字を除く全位置を文別範囲で重複なく覆い、数式はない。',
 '第一文の重点設定と二理由、第二文の一般条件と実例について、否定・全称・存在・条件・許可・認識・比較・現在までの時間範囲を保持する。',
 '第一文jeneは宗教的未成熟、第二文die erstereは啓蒙である。同じ元首・臣民・法・定式・思考態度・判断を束縛し、実例は前に名指した同じ君主へ接続する。',
 '両文を同じ著者に帰属し、第一文の説明・理由・追加・並列、第二文の対照・領域拡張・取り立て・実例・比較観点の提示を保存する。引用内容は提示時に実行しない。',
 '啓蒙や全臣民の成功、一般条件の全対象での政策実施、唯一の最初又は唯一の最大、未来の優越例の不存在、全世界の敬意を補わない。未評価を不存在へ変えない。',
 '能力、自己帰責、後見、論述の重点、害と不名誉、思考態度、法と全定式、思想、批判、許可、安全性、認識、実例、敬意と質的比較は固定した意味規約と合成へ結ぶ。原語の綴りだけを意味にしない。',
 '文別の通読判断・局所検査・一次資料照合を固定し、既存18全単位判断と第一文の依存一致を検査する。検査通過を自動的な意味同一性へ換算しない。',
 '宗教への重点と理由から、啓蒙を後押しする元首の立法にも及ぶ認識、同じ現在の実例へ進む全体を再読した。採用解釈の下で未処理の内容・照応・談話作用はない。',
]
def paragraph_record():
    u=unit();first=read(FIRST);second=read(READING)
    return dict(status='ninth_paragraph_reviewed_under_explicit_reading',reviewer='assistant_review',document=FULL,meaning_basis=BASIS,
      source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],text=u['text']),selection=selection_binding(catalog(),[117,118]),
      sentence_readings=[dict(record=p,source=r['source'],selection=r['selection']) for p,r in ((FIRST,first),(READING,second))],
      interpretation=first['interpretation']+LIMITS+['旧文別記録の第二文未完という記述は記録時の進捗であり、今回の未解決点ではない。'],
      requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,PARAGRAPH_REASONS,strict=True)],
      decision='equivalent_under_stated_reading',unresolved=[],source_nonblank_characters=780,inherited_sentence_characters=336,newly_reviewed_sentence_characters=444,
      semantic_equivalence_automatically_proved=False,no_independent_review=True,
      source_sha256={p:digest((ROOT/p).read_bytes()) for p in (FULL,BASIS,ANNOTATIONS,DOC,INVENTORY,SOURCE,FIRST,READING,*PRIORS)})
@lru_cache(None)
def paragraph_checks():
    u=unit();covered=set();count=0
    for p in (FIRST,READING):
        row=read(p);a,b=row['source']['range'];assert row['source']['text']==u['text'][a:b] and row['source']['unit_sha256']==u['text_sha256']
        assert row['whole_sentence_semantically_verified'] and not row['unresolved'] and not covered.intersection(range(a,b))
        covered.update(range(a,b));count+=sum(not c.isspace() for c in u['text'][a:b])
        assert row['selection']==selection_binding(catalog(),[x['index'] for x in row['selection']['statements']])
    assert len(u['text'])==905 and count==780 and all(i in covered for i,c in enumerate(u['text']) if not c.isspace())
    assert read(PARAGRAPH)==paragraph_record()
    for n,(span,_) in NODE_INFO.items():assert 390<=span[0]<span[1]<=905
    return dict(whole_paragraph_characters=905,whole_paragraph_nonblank_characters=780,inherited_sentence_characters=336,new_sentence_characters=444,
      all_nonblank_positions_covered=True,no_double_counting=True,first_sentence_unchanged=True)
@lru_cache(None)
def structure_checks():
    c=catalog();old=parent();lib=dependency();assert c.document['statements'][:118]==old.document['statements'] and len(c.document['statements'])==119
    assert all(c.entries[n]==e for n,e in old.entries.items())
    for n,e in lib.entries.items():
        if n in c.entries:assert c.entries[n]['declaration']==e['declaration'] and c.entries[n]['meaning_ja']==e['meaning_ja']
    reviews=load_reviews(ROOT,INDEX)['works']['kant-1784'];assert len(reviews)==18
    for row in reviews:assert row['selection']==selection_binding(c,[s['index'] for s in row['selection']['statements']])
    for p in (*PRIORS,SOURCE,FIRST):validate_hashes(ROOT,read(p)['source_sha256'])
    validate_hashes(ROOT,read(BASIS)['import_source_sha256']);load_annotations(ROOT,BASIS,ANNOTATIONS)
    assert read(ANNOTATIONS)['entries']==read('data/religious-emphasis-sentence-identifiers-v1.json')['entries']
    assert read(READING)==reading_record()
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b,p
    core=parse((ROOT/CORE).read_text(encoding='utf-8'))
    for notation in ('compact','full'):
        t=format_graph(core,notation);assert parse(t)==parse(transcribe(t,alphabet='v2'))==core
    ranks={};t=format_graph(core,'compact')
    for n in MEANINGS:
        for rank,label in enumerate(('','b','c','d','e','f','g')):
            try:parse(t+'q[e[r '+label+'[p '+n+']][r '+label+'[p '+n+']]].')
            except ValueError as e:assert 'Quoted evaluation' in str(e),str(e)
            else:ranks[n]=rank;break
    assert ranks['r6ei']==5 and ranks['r6eg']==4,ranks
    return dict(preserved_statements=118,added_statements=1,preserved_whole_unit_reviews=18,new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),
      minimum_quote_ranks=ranks,roundtrip_scope='new core compact/full/v2; inherited manuscript and meanings unchanged')
def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()));write_exact(ROOT/PARAGRAPH,encoded(paragraph_record()))
def build_report():
    results={}
    for n,f in (('content',content_checks),('focus',focus_checks),('discourse',discourse_checks),('paragraph',paragraph_checks),('structure',structure_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(build())|set(catalog().source_sha256)|{INDEX,READING,PARAGRAPH,DOC,INVENTORY,SOURCE,FIRST,*PRIORS,
      'scripts/compose_legislative_freedom_sentence.py','scripts/check_legislative_freedom_sentence.py','tests/test_legislative_freedom_sentence.py',
      'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/compose_prince_sentence.py','scripts/compose_royal_example.py','scripts/compose_enlightened_thinking.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py'}
    return dict(status='legislative_freedom_sentence_and_ninth_paragraph_checked',document=FULL,**results,
      alignment=dict(**read(READING)['source'],statements=[118],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
      whole_sentence_semantically_verified=True,whole_paragraph_semantically_reviewed=True,verified_full_units={'kant-1784':0,'einstein-1905':0},
      whole_unit_registration='separate_explicit_review_required',source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
def review():
    record=read(PARAGRAPH);pins=dict(catalog().source_sha256)
    for p in (PARAGRAPH,REPORT,READING,FIRST,SOURCE,*PRIORS):
        for n,h in {p:digest((ROOT/p).read_bytes()),**read(p).get('source_sha256',{})}.items():
            assert n not in pins or pins[n]==h,n;pins[n]=h
    for p in (FULL,BASIS,ANNOTATIONS,INVENTORY,DOC):pins[p]=digest((ROOT/p).read_bytes())
    validate_hashes(ROOT,pins)
    return dict(schema_version='noema-semantic-review-1',work='kant-1784',unit='kant-1784:u0016',reviewer='assistant_review',decision=record['decision'],
      document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=unit()['text_sha256'],text=unit()['text'],range=[0,905],math=[]),
      selection=record['selection'],interpretation=record['interpretation'],limits=['各文の明示解釈を継承したアシスタント判断。独立査読・自動同義証明・歴史的真理の実証ではない。','第十段落とEinsteinは未完。'],unresolved=[],
      requirements=record['requirements'],evidence=dict(source_reading=[PARAGRAPH,SOURCE,FIRST,READING],formal_checks=[REPORT,*PRIORS],semantic_reading=[DOC]),source_sha256=pins)
