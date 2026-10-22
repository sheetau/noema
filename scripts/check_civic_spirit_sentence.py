"""Check sentence-wide scope, contrast, anaphora and preserved reviews."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import Content
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.compose_civic_spirit_sentence import ROOT,FULL,CORE,BASIS,ANNOTATIONS,MEANINGS,PRIMITIVES,LIMITS,NODE_INFO,ORDER,parent,dependency,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown

DOC='docs/civic-spirit-sentence-v1.md';READING='data/civic-spirit-sentence-reading-v1.json'
INDEX='data/semantic-review-index-v205.json';INVENTORY='artifacts/written-units-v1/kant-1784.json';SOURCE='data/tenth-paragraph-source-reading-v1.json'
PRIORS=('reports/faculty-development-room-v1.json','reports/civic-regime-barriers-v1.json','reports/civic-advantage-appearance-v1.json','reports/civic-intellectual-options-v1.json','reports/whole-view-sentence-v1.json',
 'data/qualified-speech-sentence-reading-v1.json','data/whole-view-sentence-reading-v1.json')
DOMAIN=('a','b');SCENES=('reference','oldreference','now','other','context')
CONSTANTS=dict(community='b',lowerorder='a',higherorder='b',order='a',person='a',faculty='b',task='b',activity='b',point='now')
TRIPLE=('community','lowerorder','higherorder')

def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def unit():return next(u for u in read(INVENTORY)['units'] if u['id']=='kant-1784:u0017')
def z(n):return 'k z'+n+'[]'
def args(ns):return ' '.join(z(n) for n in ns)
def content(f):return Content(SCENES,tuple(f(t) for t in SCENES))
def atom(n):return dict(kind='call',symbol=n,arguments=[])
def desc(rank,body):return rank,json.dumps(body,sort_keys=True)
def code(n):return desc(5,atom(n))
def profile(n,rank=4):return desc(rank,dict(kind='function_ref',symbol=n))
def norm(xs):return tuple(desc(x.rank,json.loads(x.syntax)) if hasattr(x,'syntax') else x for x in xs)
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(roots,query,boundaries=()):
    d=deepcopy(catalog().document);d['statements']=[]
    for row in d['declarations']:
        if row['name'] in boundaries:row.update(kind='primitive',parameters=[p['sort'] for p in row['parameters']]);row.pop('body')
    d['declarations']=closure(d,roots)
    extra=''.join('r z'+n+'[] '+('a' if v in DOMAIN else 'd')+'.' for n,v in CONSTANTS.items())
    return parse(format_graph(d,'compact')+extra+query)
def model(d):
    v={r['name']:unknown for r in d['declarations'] if r['kind']=='primitive'}
    v.update({'z'+n:lambda v=v:v for n,v in CONSTANTS.items()})
    v.update(wa=lambda:'a',h26zj=lambda:'reference',h26zk=lambda:'context',h26km=lambda:'oldreference',h26kn=lambda r:'now' if r=='oldreference' else 'other',
      h26zi=lambda c,l,h,r:(c,l,h,r)==('b','a','b','reference'),aa=lambda p:p=='a',h237c=lambda p,c,r:(p,c,r)==('a','b','reference'),
      h26zb=lambda c,p,f,r:(c,p,f,r)==('b','a','b','reference'),ab=lambda f,p,t:(f,p,t)==('b','a','now'))
    return v
def run(d,v,domain=DOMAIN,memo=True):return evaluate(d,v,domain,SCENES,memo)
def rejects(d,v):
    try:run(d,v)
    except ValueError as e:assert 'Unknown' in str(e),str(e)
    else:raise AssertionError('Unknown accepted')

@lru_cache(None)
def content_checks():
    names=('r6ic','r6id','r6ie','r6if','r6ig')
    q=''.join('q[t[k '+n+'['+args(TRIPLE)+']]['+z('point')+']].' for n in names)
    d=fixture(names,q,('r6hs','r6hw','r6h7','r6ia'));base=model(d);rows=[]
    def values(flags):
        a,b,c,e=flags;v=dict(base)
        v['r6hs']=lambda o,comm,lo,hi,r:content(lambda t:a and(o,comm,lo,hi,r,t)==('a','b','a','b','reference','now'))
        for n,flag in (('r6hw',b),('r6h7',c),('r6ia',e)):
            v[n]=lambda *xs,flag=flag:flag and xs==('b','a','b','reference','now')
        return v
    for flags in product((False,True),repeat=4):
        v=values(flags);a,b,c,e=flags;want=[a,b,a and b,c and e,all(flags)]
        assert run(d,v)==want;rows.append(dict(parts=flags,values=want))
    for n in (*('z'+n for n in TRIPLE),'zpoint','wa','h26zj'):
        w=values((True,)*4);w[n]=lambda n=n:'other' if n in ('zpoint','h26zj') else ('b' if n in ('wa','zlowerorder') else 'a')
        got=run(d,w);assert not got[-1],(n,got)
    for n in ('r6hs','r6hw','r6h7','r6ia'):
        w=values((True,)*4);w[n]=unknown;rejects(d,w)
    # A single coherent model also realizes the native barrier AND development
    # bodies together. Task b is immediately possible only at low freedom;
    # task a is initially unfulfilled and becomes possible after development.
    from scripts.check_faculty_development_room import model as development_model,SCENES as development_scenes
    native=fixture(('r6ih',),'q[t[k r6ih[]]['+z('point')+']].',('r6hs','r6hf','r6fr'))
    v=development_model(native)
    v.update(wa=lambda:'a',h26zj=lambda:'reference',h26km=lambda:'reference',h26kn=lambda _: 'anchor',zpoint=lambda:'anchor',
      h26zi=lambda c,l,h,r:(c,l,h,r)==('b','a','b','reference'),
      r6hs=lambda *a:Content(development_scenes,tuple(a==('a','b','a','b','reference') and t=='anchor' for t in development_scenes)))
    assert evaluate(native,v,DOMAIN,development_scenes,True)==[True]
    # Break each actual side without altering the appearance boundary.
    w=dict(v);w['h26zf']=lambda *a:False
    assert evaluate(native,w,DOMAIN,development_scenes,True)==[False]
    w=dict(v);old=v['h26yw']
    w['h26yw']=w['h26yx']=lambda c,t,r,p,m,s,o:old(c,t,r,p,m,'end' if s=='w10' else s,o)
    assert evaluate(native,w,DOMAIN,development_scenes,True)==[False]
    return dict(truth_assignments=rows,same_three_objects_author_reference_and_point=True,
      native_r6hx_and_r6ib_join_all_parts=True,native_barrier_and_development_coexist_in_one_model=True,
      breaking_either_actual_side_rejects_whole_sentence=True,
      boundaries='Truth table: r6hs/r6hw/r6h7/r6ia. Coherent native integration: only r6hs appearance and r6hf/r6fr normative values; barrier, opportunity, causal intervention, ownership and development history bodies execute together. Lower appearance/norm bodies are pinned by prior reports.')

@lru_cache(None)
def scope_checks():
    q=''.join('q[t[k '+n+'[]]['+z('point')+']].' for n in ('r6ih','r6ij','r6ik'))
    d=fixture(('r6ih','r6ij','r6ik'),q,('r6ie','r6if','r6ig'));base=model(d);cases=(('a','a','b'),('b','a','b'));rows=[]
    def values(selected,left,right):
        v=dict(base);v['h26zi']=lambda c,l,h,r:r=='reference' and (c,l,h) in cases and selected[cases.index((c,l,h))]
        def part(vals,*xs):return content(lambda t:xs in cases and vals[cases.index(xs)] and t=='now')
        v['r6ie']=lambda *xs:part(left,*xs);v['r6if']=lambda *xs:part(right,*xs)
        v['r6ig']=lambda *xs:part(tuple(a and b for a,b in zip(left,right)),*xs)
        return v
    for selected,left,right in product(tuple(product((False,True),repeat=2)),repeat=3):
        v=values(selected,left,right);l=any(selected) and all(not s or a for s,a in zip(selected,left));r=any(selected) and all(not s or a for s,a in zip(selected,right))
        want=[l and r,l,r];assert run(d,v)==want;rows.append(dict(selected=selected,left=left,right=right,values=want))
    v=values((True,True),(True,True),(True,True));assert run(d,v)==[True]*3
    # Evaluation is the fixed textual present, not the enclosing query scene.
    w=dict(v);w['zpoint']=lambda:'other';assert run(d,w)==[True]*3
    for n in ('h26zj','h26kn','h26km'):
        w=dict(v);w[n]=lambda *a:'other';assert run(d,w)==[False]*3,n
    for n in ('h26zi','r6ig'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    return dict(two_case_scope_matrix=rows,nonempty_all_cases=True,outside_scope_not_silently_universalized=True,
      full_content_equals_same_left_and_right=True,fixed_actual_anchor_and_reference=True,
      boundary='r6ie/r6if/r6ig for independent scope truth tables; their composition is checked in content_checks and lower native bodies in pinned reports.')

@lru_cache(None)
def referent_checks():
    fields={'r6il':('community','order','person','activity'),'r6im':('community','person','task'),
      'r6in':('community','person'),'r6io':('community','person','faculty')}
    q=''.join('q[t[k '+n+'['+args(ns)+']]['+z('point')+']].' for n,ns in fields.items())
    d=fixture(tuple(fields),q,('r6hf','r6hi'));v=model(d)
    v['r6hf']=lambda *a:a==('b','a','a','b','reference','now')
    v['r6hi']=lambda *a:a==('b','a','b','reference','now');assert run(d,v)==[True]*4
    changes={}
    for n in ('community','order','person','activity','task','faculty','point'):
        w=dict(v);w['z'+n]=lambda n=n:'other' if n=='point' else ('b' if CONSTANTS[n]=='a' else 'a')
        got=run(d,w)
        expected=[n not in (*ns,'point') for ns in fields.values()]
        assert got==expected,(n,got,expected);changes[n]=got
    w=dict(v);w['h26zj']=lambda:'other';assert run(d,w)==[False]*4
    for name in ('unowned','outside_faculty_scope','nonmember','nonhuman'):
        w=dict(v);w[{'unowned':'ab','outside_faculty_scope':'h26zb','nonmember':'h237c','nonhuman':'aa'}[name]]=lambda *a:False
        assert run(d,w)==[True,True,False,False],name
    for n in ('r6hf','r6hi','h26zb','ab'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    return dict(argument_changes=changes,mental_civic_and_spirit_referents_distinct=True,
      same_native_membership_and_owned_faculty_relation=True,
      boundary='r6hf/r6hi only: their normative and reasoned-task bodies are unchanged and pinned in civic-intellectual-options.')

@lru_cache(None)
def discourse_checks():
    nodes=(*NODE_INFO,'h26yd');domain=(*nodes,'author','wrong')
    d=fixture(('r6ip',),'q[k r6ip[]].');v=model(d);v.update({n:lambda n=n:n for n in nodes});v['wa']=lambda:'author';whole=code('r6ih')
    rows={'h26ub':{(n,'author',code(c),'context') for n,c in (('h26zq','r6ih'),('h26zr','r6ij'),('h26zs','r6ik'))},
      'h26zl':{('h26zz','author',whole,profile('r6ii',0),profile('r6ic'),profile('r6id'),profile('r6ie'),'context')},
      'h26uc':{('h26z4','author',whole,code('r6ij'),code('r6ik'),'context')},
      'h26zm':{('h26z3','author',whole,'h26zt',profile('r6il'),'context')},
      'h26zn':{('h26zy','author',whole,'h26zv',profile('r6im'),'context')},
      'h26zo':{(n,'author',whole,'h26zw',profile('r6in'),'context') for n in ('h26z5','h26z7')},
      'h26zp':{('h27ab','author',whole,'h26zw',profile('r6in'),profile('r6io'),'context')},
      'ue':{(a,b,'context') for a,b in ORDER}}
    def values(expected):
        w=dict(v);w.update({n:lambda *a,allowed=rs:norm(a) in allowed for n,rs in expected.items()});return w
    assert run(d,values(rows),domain)==[True];mutations=0
    for n,rs in rows.items():
        for row in rs:
            for i in range(len(row)):
                changed=deepcopy(rows);changed[n].remove(row);bad=list(row);bad[i]='__mismatch__';changed[n].add(tuple(bad))
                assert run(d,values(changed),domain)==[False],(n,i);mutations+=1
    for a,b in ORDER:
        changed=deepcopy(rows);changed['ue'].add((b,a,'context'));assert run(d,values(changed),domain)==[False]
        w=values(rows);w[b]=lambda a=a:a;assert run(d,w,domain)==[False],(a,b)
    for n in rows:
        w=values(rows);w[n]=unknown
        try:run(d,w,domain)
        except ValueError as e:assert 'Unknown' in str(e),str(e)
        else:raise AssertionError(n)
    return dict(argument_mutations=mutations,all_five_anaphors_and_possession_bound=True,
      concessive_same_case_profiles_and_ordered_two_regime_contrast=True,
      same_whole_and_both_part_attribution=True,positive_order_reverse_absence_and_distinct_nodes=True,
      quoted_content_not_executed=True,unknown_rejected=True)

FRAGMENTS=(
 ('Ein größerer Grad bürgerlicher Freiheit ',['r6ii','r6hg','r6hf','r6il'],'固定した同じ共同体・市民的行為・役割・基準の許可集合で、比較する二制度の高い側を取る。文脈上の非空の全比較組へ一般化する。'),
 ('scheint ',['r6ic','r6hs','rro'],'非空の表面的情報の全候補で、同じ高い側の比較内容が成立する見かけ。現実の精神的利益を断言しない。'),
 ('der Freiheit des Geistes des Volks ',['r6im','r6in','r6hd','r6hi','r6hh'],'同じ民衆各人の自分の悟性による理由ある判断を、固定課題の全事項について達成できる機会。集団・人・課題を両側で保持する。'),
 ('vortheilhaft, ',['r6hn','r6hm','r6hl'],'同じ評価済みの精神的課題機会が高い側で真包含拡大することを、見かけの内容として置く。'),
 ('und setzt ',['r6ie','r6id','r6hu','r6hw'],'その同じ高い側が制度条件の因果比較で制限を生むことを、見かけと連言する。'),
 ('ihr ',['h26zn','r6im'],'先行する民衆の精神的自由への照応。市民的自由や別の民衆へ取り替えない。'),
 ('doch ',['h26zl','r6ic','r6id','r6ie'],'有利に見えることから制限を退ける見通しに反して、同じ範囲で実際の制限をなお提示する。論理矛盾は要求しない。'),
 ('unübersteigliche Schranken; ',['r6hv','rwx','r6hw'],'高い側の非空全介入解で指定課題は評価済みで達成不能となり、低い側の少なくとも一解では達成機会がある。元の方程式に適合する高い側の観測と現在の不能も確認する。'),
 ('ein Grad weniger von ',['r6hg','r6h7'],'同じ大小比較の低い側。数値一単位の差や異なる時刻への移行を補わない。'),
 ('jener ',['h26zm','r6il'],'先行する市民的自由を指し、精神的自由の減少と取り違えない。'),
 ('verschaft ',['r6h7','r6hu'],'現在の低い側と同じ側へ介入した非空全解で、同じ法秩序の下で発展の余地があるという条件付きの可能化。'),
 ('hingegen ',['h26uc','r6ij','r6ik'],'高い側の見かけと制限を合わせた内容と、低い側の発展機会を、同じ比較対象について対照的に提示する。'),
 ('diesem ',['h26zo','r6in'],'同じ民衆の精神を受け手として指す。先の市民的自由そのものを受け手にしない。'),
 ('Raum, ',['r6h5','r6h6','r6h7'],'同じ制度の下で能力を展開する方法があるという余地。抽象的可能性の用法として扱い、独立した物理的空間の存在を補わない。'),
 ('sich ',['h26zo','r6in'],'受け手と展開する精神を同じ対象へ結ぶ再帰。各人の本人の能力を別人の成功に替えない。'),
 ('nach allem ',['r6h6','h26zb','h26zc'],'非空の全成員それぞれの非空の全関連能力と、それぞれの固定した潜在的全課題を対象にする。'),
 ('seinen ',['h26zp','r6io','r6hy'],'同じ精神の働きを担う本人が所有し使用する能力への所有照応。abとacで発展目標にも所有と使用を保つ。'),
 ('Vermögen ',['r6io','h26zb','r6h5'],'自分の悟性による判断の働き・資源として区分する関連能力。全心理機能の唯一の理論や数値強度とはしない。'),
 ('auszubreiten.',['r6h3','r6h4','r6h6'],'時間履歴を通じて固定課題全体を行使できる状態へ達する機会。既に行使できる能力には維持を認め、全体には未達課題を求める。実際の発展や一つの同時計画は断言しない。'))
def reading_record():
    u=unit();cursor=467;clauses=[]
    for fragment,ns,reading in FRAGMENTS:
        assert u['text'][cursor:cursor+len(fragment)]==fragment,(cursor,fragment)
        assert all(n in catalog().entries for n in ns),ns
        clauses.append(dict(range=[cursor,cursor+len(fragment)],text=fragment,definitions=ns,reading=reading));cursor+=len(fragment)
    assert cursor==715 and sum(not c.isspace() for c in u['text'][467:cursor])==215
    return dict(status='civic_spirit_sentence_reviewed_under_explicit_reading',reviewer='assistant_review',document=FULL,meaning_basis=BASIS,
      source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[467,cursor],text=u['text'][467:cursor]),selection=selection_binding(catalog(),[121]),
      clauses=clauses,interpretation=LIMITS,unresolved=[],decision='equivalent_under_stated_reading_for_civic_spirit_sentence',
      whole_sentence_semantically_verified=True,whole_unit_semantically_verified=False,newly_reviewed_sentence_characters=215,semantic_equivalence_automatically_proved=False,
      holistic_review=[r for _,_,r in FRAGMENTS]+['第三文全体を19断片と合わせて通読した。同じ非空比較範囲・民衆・人・二制度・固定課題・能力を保持し、市民的自由と精神的自由、見かけと事実、制限と機会、度合いと時間順、全能力と各能力の厳密増加を区別した。五照応・二つの対照・全文と二側の帰属を確認した。抽象的な空間語の用法と採用した一般化範囲・強い到達条件を明示した。後続第四文と段落全体の通読は別に残る。'],
      source_sha256={p:digest((ROOT/p).read_bytes()) for p in (FULL,CORE,BASIS,ANNOTATIONS,DOC,INVENTORY,SOURCE,*PRIORS)})
@lru_cache(None)
def structure_checks():
    c=catalog();old=parent();assert c.document['statements'][:-1]==old.document['statements'] and len(c.document['statements'])==122
    for source in (old,dependency()):
        for n,e in source.entries.items():
            if n in c.entries:assert c.entries[n]['declaration']==e['declaration'] and c.entries[n]['meaning_ja']==e['meaning_ja'],n
    reviews=load_reviews(ROOT,INDEX)['works']['kant-1784'];assert len(reviews)==19
    for row in reviews:assert row['selection']==selection_binding(c,[s['index'] for s in row['selection']['statements']])
    for p,i in (('data/qualified-speech-sentence-reading-v1.json',119),('data/whole-view-sentence-reading-v1.json',120)):
        assert read(p)['selection']==selection_binding(c,[i])
    for p in (*PRIORS,SOURCE):validate_hashes(ROOT,read(p)['source_sha256'])
    validate_hashes(ROOT,read(BASIS)['import_source_sha256']);load_annotations(ROOT,BASIS,ANNOTATIONS)
    assert read(ANNOTATIONS)['entries']==read('data/whole-view-sentence-identifiers-v1.json')['entries']
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
    expected={n:3 if n in ('r6ic','r6ie','r6ig','r6ih','r6ij','r6ip') else 0 for n in MEANINGS}
    assert ranks==expected,ranks
    return dict(preserved_statements=121,added_statements=1,preserved_whole_unit_reviews=19,preserved_first_two_sentence_reviews=True,
      new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),minimum_quote_ranks=ranks,roundtrip_scope='new core compact/full/v2; inherited manuscript and meanings unchanged')
def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))
def build_report():
    results={}
    for n,f in (('content',content_checks),('scope',scope_checks),('referents',referent_checks),('discourse',discourse_checks),('structure',structure_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(build())|set(catalog().source_sha256)|{INDEX,READING,DOC,INVENTORY,SOURCE,*PRIORS,
      'scripts/compose_civic_spirit_sentence.py','scripts/check_civic_spirit_sentence.py','tests/test_civic_spirit_sentence.py',
      'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/compose_prince_sentence.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/check_faculty_development_room.py'}
    return dict(status='civic_spirit_sentence_checked_under_explicit_reading',document=FULL,**results,
      alignment=dict(**read(READING)['source'],statements=[121],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
      whole_sentence_semantically_verified=True,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
      source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
