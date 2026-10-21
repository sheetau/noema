"""Check scoped supplements and review the complete cohort covenant sentence."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import Content
from noema.meaning_catalog import load_catalog
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.compose_cohort_covenant_denial import ROOT,FULL,CORE,BASIS,ANNOTATIONS,PRIMITIVES,MEANINGS,LIMITS,parent,dependency,build,closure,NAMES
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown,symbol
from scripts.check_covenant_nullity import normalized

INDEX='data/semantic-review-index-v182.json'
REPORT='reports/cohort-covenant-denial-v1.json'
READING='data/cohort-covenant-denial-reading-v1.json'
DOC='docs/cohort-covenant-denial-v1.md'
LEXICAL='data/cohort-covenant-denial-lexical-v1.json'
INVENTORY='artifacts/written-units-v1/kant-1784.json'
PRIORS=tuple('reports/'+n+'-v1.json' for n in ('covenant-nullity','epoch-undertakings','cognitive-correction','cognitive-acquisition','cohort-progress-options','necessary-cohort-state','cohort-covenant-purpose','cohort-normative-denial'))
SCENES=('reference','candidate','context','first','last')
EXTRA='r zone[] a.r ztwo[] a.'+''.join('r z'+s+'[] d.' for s in SCENES)
SEQ=('one','two','one','two','one','two')
LITERAL='l[a]['+' '.join('k z'+n+'[]' for n in SEQ)+']'

def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(roots,query,boundaries=(),extra=EXTRA):
    doc=deepcopy(catalog().document)
    for d in doc['declarations']:
        if d['name'] in boundaries:d.update(kind='primitive',parameters=[p['sort'] for p in d['parameters']]);d.pop('body')
    doc.update(declarations=closure(doc,roots),statements=[])
    return parse(format_graph(doc,'compact')+extra+query)
def run(doc,v,domain=('one','two')):return evaluate(doc,v,domain,SCENES,True)
def base(doc):
    v={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
    v.update(zone=lambda:'one',ztwo=lambda:'two',h26av=lambda:'reference',h26ar=lambda r:'context',h255n=lambda:'context')
    v.update({'z'+s:lambda s=s:s for s in SCENES});return v
def content(value):return Content(SCENES,tuple(value and p=='candidate' for p in SCENES))

@lru_cache(None)
def importance_checks():
    doc=fixture(('r5dj',),'q[t[k r5dj['+LITERAL+']][k zcandidate[]]].');rows={}
    def model(concern=True,high=True,variant='baseline'):
        v=base(doc);v['h26ad']=lambda item,r:variant!='empty' and(item,r)==('one','reference')
        def concerned(group,items,reference,point):
            assert tuple(items(x) for x in ('one','two'))==((False,False) if variant=='empty' else (True,False))
            return concern and(group,reference,point)==('one' if variant=='wrong_group' else 'two','context' if variant=='wrong_reference' else 'reference','first' if variant=='wrong_point' else 'candidate')
        v['h26az']=concerned
        v['h225q']=lambda code,bs,p:high and normalized((code,bs,p))==(('r5di',3),SEQ,'candidate')
        return v
    for concern,high in product((False,True),repeat=2):
        actual=run(doc,model(concern,high));assert actual==[concern and high];rows[str((concern,high))]=actual[0]
    contrasts={}
    for variant in ('empty','wrong_group','wrong_reference','wrong_point'):
        actual=run(doc,model(variant=variant));assert actual==[False];contrasts[variant]=actual[0]
    for n in ('h26ad','h26az','h225q'):
        v=model();v[n]=unknown
        try:run(doc,v)
        except ValueError as e:assert 'Unknown' in str(e)
        else:raise AssertionError(n)
    short=fixture(('r5dj',),'q[t[k r5dj[l[a][k zone[]]]][k zcandidate[]]].');v=model();v['h26az']=lambda *a:True;v['h225q']=lambda *a:True
    assert run(short,v)==[False]
    return dict(concern_and_high_degree=rows,same_cohort_and_full_nonempty_domain=contrasts,malformed_binding_rejected=True,unknown_rejected=True)

@lru_cache(None)
def supplement_checks():
    doc=fixture(('r5dk',),'q[t[k r5dk[]][k zcandidate[]]].',('r5dc','r5dj'));rows={}
    left=('one',)*6;right=('two',)*6
    for selected_left,selected_right,valued_left,valued_right in product((False,True),repeat=4):
        v=base(doc);v['r5dc']=lambda *a:(selected_left and a==(*left,'candidate')) or(selected_right and a==(*right,'candidate'))
        v['r5dj']=lambda bs:content((tuple(bs.items)==left and valued_left) or(tuple(bs.items)==right and valued_right))
        want=(not selected_left or valued_left) and (not selected_right or valued_right)
        actual=run(doc,v);assert actual==[want];rows[str((selected_left,selected_right,valued_left,valued_right))]=actual[0]
    return dict(same_scope_supplement_oracle=rows,importance_does_not_filter_main_scope=True,boundaries=['r5dc','r5dj'])

@lru_cache(None)
def progress_checks():
    roots=('r5dl','r5dm','r5dn');rows={}
    for variant in ('baseline','wrong_group','wrong_scope','wrong_assessment','wrong_candidate','wrong_first','wrong_last','short','long'):
        names=list(SEQ)
        if variant=='short':names.pop()
        if variant=='long':names.append('one')
        seq='l[a]['+' '.join('k z'+n+'[]' for n in names)+']'
        query=''.join('q[t[k '+n+'['+seq+' k zfirst[] k zlast[]]][k zcandidate[]]].' for n in roots)
        doc=fixture(roots,query,('r5co','r5ci','r5cr'));v=base(doc)
        expected=['two','reference','context','candidate','first','last']
        positions={'wrong_group':0,'wrong_scope':1,'wrong_assessment':2,'wrong_candidate':3,'wrong_first':4,'wrong_last':5}
        if variant in positions:expected[positions[variant]]='one' if variant=='wrong_group' else 'outside'
        v['r5co']=lambda *a:a==tuple(expected);v['r5ci']=lambda *a:a==tuple(expected)
        v['r5cr']=lambda *a:a==tuple(expected[:2]+expected[3:])
        actual=run(doc,v);want=[variant=='baseline']*3
        if variant=='wrong_assessment':want[2]=True
        assert actual==want,(variant,actual);rows[variant]=actual
    return dict(same_three_kinds_as_inability=rows,boundaries=['r5co','r5ci','r5cr'],assessment_not_spuriously_added_to_self_judgment=True)

@lru_cache(None)
def discourse_checks():
    doc=fixture(('r5do',),'q[k r5do[]].',extra='');nodes=('h257r','h26bd','h26be','h26bf','h26bg','h26bh','h26bi','h26bj')
    a='author';ctx='context';whole=('r5dh',3);family=lambda n:(n,0)
    expected={
        'h236i':{('h26bd',a,whole,ctx),('h26bf',a,('r5dk',3),ctx)},
        'h234k':{('h26bf',a,'h26bd',ctx)},
        'h26ba':{('h26bf',a,whole,family('r5df'),family('r5dj'),ctx)},
        'h26bb':{('h26bh',a,whole,family('r5df'),(family('r5dl'),family('r5dm')),family('r5dn'),ctx)},
        'h26bc':{('h26be',a,whole,family('r5df'),family('r5db'),ctx)},
        'ue':{(l,r,ctx) for l,r in (('h257r','h26bd'),('h26be','h26bg'),('h26bf','h26bi'),('h26bi','h26bj'),('h26bj','h26bh'))},
    }
    rows={}
    for variant in ('baseline',*expected,'wrong_author','wrong_context','merged_nodes','reordered_details','other_scope','missing_supplement','unknown'):
        v=base(doc);v.update({n:lambda n=n:n for n in nodes});v['wa']=lambda:'other' if variant=='wrong_author' else a
        for n,wanted in expected.items():v[n]=lambda *args,n=n,wanted=wanted:n!=variant and normalized(args) in wanted
        if variant=='wrong_context':v['h255n']=lambda:'reference'
        if variant=='merged_nodes':
            v['h26bd']=lambda:'h257r'
            for n in expected:v[n]=lambda *a:True
        if variant=='reordered_details':v['h26bb']=lambda *args:normalized(args)==('h26bh',a,whole,family('r5df'),(family('r5dm'),family('r5dl')),family('r5dn'),ctx)
        if variant=='other_scope':v['h26ba']=lambda *args:normalized(args)==('h26bf',a,whole,family('r5dg'),family('r5dj'),ctx)
        if variant=='missing_supplement':v['h236i']=lambda *args:normalized(args)==('h26bd',a,whole,ctx)
        if variant=='unknown':
            v['h26bb']=unknown
            try:run(doc,v,(*nodes,a,'other'))
            except ValueError as e:assert 'Unknown' in str(e)
            else:raise AssertionError('unknown discourse')
            continue
        actual=run(doc,v,(*nodes,a,'other'));assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
        for n in ('h26az','h225q','h7k','h7l','h26as','h26at','h26am'):assert v[n] is unknown
    return dict(scoped_presentation_and_closed_quotes=rows,quoted_truth_not_executed=True,unknown_rejected=True)

def reading_record():
    unit=next(u for u in read(INVENTORY)['units'] if u['id']=='kant-1784:u0013');cursor=713;clauses=[]
    for text,names,reading in (
        ('Ein Zeitalter ',['r5bx','r5dc','r5de'],'全履歴を覆う固定区分における先行時代の全生存者。任意の時代についての一般的な否認。'),
        ('kann sich nicht verbünden und darauf verschwören, ',['r5ca','r5c6','r5c7','r5da','r5db','r5dd','r5dh','h26bc'],'同じ当事者の同じ条項・共同目的への相互宣誓を結び、その形成への正当な資格を全候補について否認する。否定的な結束の提示は別に保持する。'),
        ('das folgende in einen Zustand zu setzen, ',['r5bx','r5cx','r5c2','r5c3','r5c4','r5c5'],'同じ区分の直後の集団を、同じ合意の実施によって同じ非空の条件項目の状態へ置く目的。形成時には成功を要求しない。'),
        ('darin es ihm unmöglich werden muß, ',['r5cv','r5cw','r5cy','r5cz','r5c2'],'後続時代内の状態成立と、同じ状態が成立する全比較候補での三種類の進展不能を結ぶ。元の経過だけの失敗や空候補で必然性を代用しない。'),
        ('seine ',['r5cl','r5co','r5ci','r5cr','r5di'],'認識と進展の主体を同じ後続集団へ保つ。先行当事者の認識へ替えない。'),
        ('(vornehmlich so sehr angelegentliche) ',['r5di','r5dj','r5dk','h26az','h225q','h26ba','h234k'],'同じ後代にとって認識事項が非常に切実であることを特に取り立てる括弧内補足。重要性で中心命題の対象範囲を狭めない。'),
        ('Erkenntnisse zu erweitern, ',['r5cl','r5cm','r5co','r5dl'],'同じ内容についての把握・真理・十分な根拠を伴う認識の新たな獲得と範囲の拡大。単なる語の追加や知識量の数値ではない。'),
        ('von Irrthümern zu reinigen, ',['r5ce','r5cf','r5cg','r5ci','r5dm'],'同じ偽の内容への受容を、本人の理由ある訂正を経てなくす。忘却・死亡・言い換えだけで代用しない。'),
        ('und überhaupt in der Aufklärung weiter zu schreiten.',['r5cr','r5cs','r5cw','r5dn','h26bb'],'同じ集団の通常の理由ある自己判断の新たな取得・広がり。前二者から啓蒙一般へ論述を広げ、三種類のどの進展も可能でない条件の内側に保つ。')):
        assert unit['text'][cursor:cursor+len(text)]==text
        clauses.append(dict(range=[cursor,cursor+len(text)],text=text,definitions=names,reading=reading));cursor+=len(text)
    assert cursor==1004
    page=read('data/covenant-question-reading-v1.json')['original_page'];assert digest((ROOT/page['path']).read_bytes())==page['sha256']
    return dict(status='cohort_covenant_denial_sentence_reviewed_under_explicit_reading',reviewer='assistant_review',document=FULL,meaning_basis=BASIS,
        source=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[713,1004],text=unit['text'][713:1004]),selection=selection_binding(catalog(),[99]),
        clauses=clauses,interpretation=LIMITS,unresolved=[],decision='equivalent_under_stated_reading_for_cohort_covenant_denial_sentence',
        whole_sentence_semantically_verified=True,whole_unit_semantically_verified=False,newly_reviewed_sentence_characters=sum(not c.isspace() for c in unit['text'][713:1004]),
        semantic_equivalence_automatically_proved=False,original_page=page|dict(visually_inspected=True),lexical_evidence=LEXICAL,
        holistic_review=[
            '原刊488頁で前文の無効性から次の人間本性への犯罪・子孫による拒否までを含めて再読した。時代は全生存者の集団、次の時代は同じ区分の直後として保持し、世代間で同一人が重なることを排除しない。',
            '同じ当事者の相互引受け・宣誓・共同目的採用と、その目的の因果的な達成内容を確認した。個人別条項の七位置と目的の六位置を区別し、未履行や未成功の合意を語れる。全員の署名・秘密性・誠実さ・代表権は追加していない。',
            '同じ後代が置かれる非空の条件項目の状態、合意による原因性、後続時代内の成立を確認した。状態が成立する全比較候補では同じ集団の全方法・結果・継続に進展がない。三種類の同時成功だけの否定や、実際の一経過だけの比較にはしていない。',
            '認識の獲得は内容の把握と真理と十分な根拠、訂正は偽の同じ内容からの理由ある転換、啓蒙進展は通常の理由ある自己判断の新しい取得として、それぞれ公開した意味規約と構成をたどった。後代集団の同一性、前後点、固定真偽評価と範囲を取り違えていない。',
            'kann nichtは正当な資格の否認として全候補にかける。候補を形成済み・目的達成済みのものへ選別せず、存在例のない一般否認から具体的実在や禁止要求を補わない。後続の理由付けは本判断に含めない。',
            'seineと括弧内は同じ後代の認識事項へ結ぶ。切実さと高程度、特にという焦点と括弧による補足を分け、認識全体を重要な一部へ縮めない。überhauptは個別二進展から一般的な啓蒙への提示であり、知識の増加から自立への論理的含意を追加しない。',
            '著者による中心命題と補足の提示、同じ範囲の否定的な結束の性格づけ、前文からの順序を閉じた内容へ結んだ。全文の各節を固定原文と対応させ、未処理の語句を単なるラベルや検査成功に置き換えていない。有限模型は接続の検査であり、自動同値性証明や原著者の規範判断の真理の証明ではない。'],
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in (FULL,BASIS,ANNOTATIONS,DOC,INVENTORY,LEXICAL,page['path'],*PRIORS)})

@lru_cache(None)
def structure_checks():
    old,new=parent(),catalog();assert new.document['statements'][:99]==old.document['statements'] and len(new.document['statements'])==100
    assert all(new.entries[n]==e for n,e in old.entries.items())
    for n,e in dependency().entries.items():assert new.entries[n]['declaration']==e['declaration'] and new.entries[n]['meaning_ja']==e['meaning_ja']
    reviews=load_reviews(ROOT,INDEX)['works']['kant-1784']
    for row in reviews:assert row['selection']==selection_binding(new,[s['index'] for s in row['selection']['statements']])
    for p,indices in (('data/covenant-question-reading-v1.json',[96,97]),('data/covenant-nullity-reading-v1.json',[98])):
        assert read(p)['selection']==selection_binding(new,indices)
    for p in PRIORS:validate_hashes(ROOT,read(p)['source_sha256'])
    assert read(READING)==reading_record()
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b,p
    for path in (FULL,CORE):
        doc=parse((ROOT/path).read_text(encoding='utf-8'))
        for notation in ('compact','full'):
            text=format_graph(doc,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    return dict(preserved_statements=99,added_statements=1,preserved_whole_unit_reviews=len(reviews),preserved_opening_sentence_characters=614,new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),roundtrips=True,new_reviewed_sentence_characters=250)

def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))

def build_report():
    results={}
    for n,f in [('importance',importance_checks),('supplement',supplement_checks),('progress',progress_checks),('discourse',discourse_checks),('structure',structure_checks)]:
        results[n]=f();print(n+' checked',flush=True)
    paths=set(build())|set(catalog().source_sha256)|{INDEX,READING,DOC,LEXICAL,INVENTORY,*PRIORS,read(READING)['original_page']['path'],
        'data/covenant-question-reading-v1.json','data/covenant-nullity-reading-v1.json','scripts/compose_cohort_covenant_denial.py','scripts/check_cohort_covenant_denial.py',
        'tests/test_cohort_covenant_denial.py','scripts/compose_cohort_covenant_purpose.py','scripts/check_covenant_nullity.py',
        'scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/compose_protected_remarks.py'}
    return dict(status='cohort_covenant_denial_sentence_under_explicit_reading',document=FULL,**results,
        alignment=dict(**read(READING)['source'],statements=[99],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=True,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
