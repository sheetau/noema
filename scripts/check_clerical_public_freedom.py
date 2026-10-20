"""Check the complete scholarly-freedom sentence and its explicit reading."""
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
from scripts.compose_clerical_public_freedom import ROOT,FULL,CORE,BASIS,ANNOTATIONS,NAMES,PRIMITIVES,MEANINGS,LIMITS,parent,dependencies,build,closure
from scripts.check_scholarly_mission import model as mission_model,BOUNDARIES,TIMES
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown,symbol

INDEX='data/semantic-review-index-v171.json'
REPORT='reports/clerical-public-freedom-v1.json'
AUDIT='data/clerical-public-freedom-reading-v1.json'
DOC='docs/clerical-public-freedom-v1.md'
INVENTORY='artifacts/written-units-v1/kant-1784.json'
EVIDENCE='data/officer-example-evidence-v1.json'
IMAGE='artifacts/officer-example-v1/page-486.jpg'
LEXICAL='data/reviewed-thoughts-lexical-v1.json'
PRIOR=tuple('reports/'+n+'-v1.json' for n in ('clerical-obligation','reviewed-thoughts','creed-opinions','reform-proposals','scholarly-mission'))
DOMAIN=('x','y')
DISCOURSE=('author','prior','sentence','freedom','calling','other')


def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)


@lru_cache(None)
def fixture(target='r37o',boundaries=('r35t',*BOUNDARIES)):
    doc=deepcopy(catalog().document)
    for d in doc['declarations']:
        if d['name'] in boundaries:
            d.update(kind='primitive',parameters=[p['sort'] for p in d['parameters']]);d.pop('body')
    doc.update(declarations=closure(doc,[target]),statements=[])
    query='k '+target+'[]'
    if target!='r37q':query='t['+query+'][k zpoint[]]'
    return parse(format_graph(doc,'compact')+'r zpoint[] d.q['+query+'].')


def base(doc):
    v={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
    v.update(h232v=lambda:'reference',zpoint=lambda:'late');return v


def native_model(doc,variant='baseline',bits=(True,False,True)):
    v=base(doc);v.update(mission_model(variant,bits))
    v.update(h232v=lambda:'reference',r35t=lambda *args:variant!='no_case' and args==('x',)*9+('reference',),
        h247d=lambda person,ref:'y' if variant=='wrong_scholar' else person,
        cd=lambda role,ref:variant!='not_scholarly' and (role,ref)==('x','reference'))
    return v


@lru_cache(None)
def native_checks():
    rows={}
    for variant in ('baseline','one_banned','one_unpermitted','wrong_scholar','not_scholarly','no_execution','no_case'):
        doc=fixture();v=native_model(doc,variant)
        # The task's realization, truth of opinions and improvements stay unknown.
        for n in ('r36y','r367','h7q','h7r','ic'):v[n]=unknown
        actual=evaluate(doc,v,DOMAIN,TIMES,True)
        assert actual==[variant in ('baseline','no_execution','no_case')],(variant,actual);rows[variant]=actual[0]
    table=[]
    for allowed,called in product((False,True),repeat=2):
        values=[]
        for target in ('r37m','r37n','r37o'):
            doc=fixture(target);values+=evaluate(doc,native_model(doc,bits=(allowed,False,called)),DOMAIN,TIMES,True)
        assert values==[allowed,called,allowed and called],(allowed,called,values)
        table.append(dict(allowed=allowed,called=called,results=values))
    return dict(contrasts=rows,independent_clauses=table,native_norms_and_full_communication_scope=True,
        quoted_mission_not_executed=True,boundaries=['r35t clerical case',*BOUNDARIES],boundary_evidence=list(PRIOR))


@lru_cache(None)
def scope_checks():
    doc=fixture('r37o',('r35t','r37j','r37k'));rows={}
    for position in range(9):
        selected=tuple('y' if i==position else 'x' for i in range(9))
        person,role,church,congregation,students,members,creed,subject,standard=selected
        expected=(person,person,church,creed,subject,'reference')
        for fail in ('none','freedom','calling'):
            v=base(doc);seen=set();forwarded=set()
            def cases(*args):seen.add(args);return args==(*selected,'reference')
            def content(kind):
                def result(*args):
                    forwarded.add(args)
                    return Content(TIMES,tuple(args==expected and fail!=kind for _ in TIMES))
                return result
            v.update(r35t=cases,h247d=lambda p,ref:p,cd=lambda *args:True,r37j=content('freedom'),r37k=content('calling'))
            actual=evaluate(doc,v,DOMAIN,TIMES,True)
            assert actual==[fail=='none'] and seen=={(*xs,'reference') for xs in product(DOMAIN,repeat=9)},(position,fail,actual)
            assert expected in forwarded
            rows[NAMES[position]+'_'+fail]=actual[0]
    return dict(contrasts=rows,all_nine_prior_case_fields_quantified=True,
        same_person_church_creed_subject_and_person_bound_scholar=True,
        boundary='r37j/k are typed here and evaluated natively in native_checks; prior r35t meaning is pinned.')


def discourse_model(doc,variant='baseline'):
    v=base(doc);v.update(h247e=lambda:'sentence',h247f=lambda:'freedom',h247g=lambda:'calling',h246q=lambda:'prior',
        wa=lambda:'author',h232o=lambda:'reference')
    def claim(node,author,code,ctx):
        expected={'sentence':'r37o','freedom':'r37m','calling':'r37n'}
        if variant=='swapped_contents':expected.update(freedom='r37n',calling='r37m')
        return node in expected and (author,symbol(code),code.rank,ctx)==('other' if variant=='wrong_author' else 'author',
            expected[node],3,'late' if variant=='wrong_context' else 'reference') and not(variant=='missing_calling' and node=='calling')
    def focus(node,author,firstnode,first,secondnode,second,background,ctx):
        return variant!='no_focus' and (node,author,firstnode,symbol(first),first.rank,secondnode,symbol(second),second.rank,symbol(background),background.rank,ctx)==(
            'sentence','author','freedom','r37m',3,'calling','r37n',3,'r37o' if variant=='wrong_background' else 'r37p',3,'reference')
    def contrast(node,author,prior,left,current,right,dimension,ctx):
        return variant!='no_contrast' and (node,author,prior,symbol(left),left.rank,current,symbol(right),right.rank,symbol(dimension),ctx)==(
            'sentence','author','prior','r37m' if variant=='wrong_prior_content' else 'r36k',3,'sentence','r37o',3,
            'r36k' if variant=='wrong_dimension' else 'r2zg','reference')
    def order(first,last,ctx):
        pairs={('prior','sentence'),('freedom','calling')}
        if variant=='wrong_predecessor':pairs.remove(('prior','sentence'))
        if variant=='reversed_addition':pairs.remove(('freedom','calling'))
        return (first,last) in pairs and ctx=='reference'
    v.update(h236i=claim,h245k=focus,h236k=contrast,ue=order);return v


@lru_cache(None)
def discourse_checks():
    doc=fixture('r37q',());rows={}
    for variant in ('baseline','swapped_contents','wrong_author','wrong_context','missing_calling','no_focus','wrong_background',
        'no_contrast','wrong_prior_content','wrong_dimension','wrong_predecessor','reversed_addition'):
        actual=evaluate(doc,discourse_model(doc,variant),DISCOURSE,TIMES,True)
        assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
    v=discourse_model(doc);v.update(h247g=lambda:'freedom',h236i=lambda *args:True,h245k=lambda *args:True,h236k=lambda *args:True,ue=lambda *args:True)
    assert evaluate(doc,v,DISCOURSE,TIMES,True)==[False]
    expect=fixture('r37p',());table=[]
    for bits in product((False,True),repeat=4):
        v=base(expect);v['wa']=lambda:'author'
        def compare(author,left,right,ref):
            assert (author,left.rank,right.rank,ref)==('author',2,2,'reference')
            return dict(zip((('r37m','r37m'),('r37n','r37n'),('r37m','r37n'),('r37n','r37m')),bits))[(symbol(left),symbol(right))]
        v['h245j']=compare;actual=evaluate(expect,v,DISCOURSE,TIMES,True)
        assert actual==[bits==(True,True,True,False)],(bits,actual);table.append(dict(inputs=bits,value=actual[0]))
    return dict(contrasts=rows,expectation_table=table,distinct_clause_nodes=True,exact_prior_contrast_and_added_focus=True,
        expectation_background_not_mixed_into_world_content=True,quoted_world_and_background_not_executed_by_attribution=True)


@lru_cache(None)
def unknown_checks():
    rows=[]
    for target,names,fn,domain in [('r37o',('r35t','h247d','cd','h245c','h237z'),native_model,DOMAIN),
        ('r37q',('h236i','h245k','h236k','ue'),discourse_model,DISCOURSE)]:
        doc=fixture(target,() if target=='r37q' else ('r35t',*BOUNDARIES))
        for n in names:
            v=fn(doc);v[n]=unknown
            try:evaluate(doc,v,domain,TIMES,True)
            except ValueError as error:assert 'Unknown' in str(error),str(error)
            else:raise AssertionError(n)
            rows.append(n)
    return dict(unknown_relations_rejected=rows)


def reading():
    unit=next(u for u in read(INVENTORY)['units'] if u['id']=='kant-1784:u0012')
    parts=[
        ('Aber ',['h236k','r2zg','r37q'],'直前の職務制約を撤回せず、同じ本人の公的な学識者の立場との対照を提示する。'),
        ('als Gelehrter ',['h247d','cd','r2zi','r37m','r37n'],'同じ本人の学識者としての公的理性使用の立場を、職務上の役割とは別に保持する。'),
        ('hat er volle Freiheit, ',['r35t','r37c','r37d','r37e','r37j','r37m'],'同じ聖職者の全対象の全伝達候補について積極的許可と反対要求の不在を述べる。'),
        ('ja sogar den Beruf dazu, ',['r37h','r37i','r37k','r37n','r37p','h245k'],'同じ公的伝達への課題を自由に加える。各対象を期間内のいずれかの時機に伝える方針で、全案の採用ではない。'),
        ('alle seine ',['r36m','r36v','r37h','r37j'],'同じ本人の資格ある全見解を扱い、許可済み・実行済みのものだけへ絞らない。'),
        ('sorgfältig geprüften ',['r36n','r36o','r36p','r36q'],'同じ内容の吟味を基準点以前に一応終え、固定した全関連事項へ本人が注意を配る。真理や無謬性を要求しない。'),
        ('und wohlmeinenden ',['rqyn','r36r','r36s'],'同じ見解判断が他者の利益をそれ自体求める目的を持つ。受益の成功や他の動機の不在ではない。'),
        ('Gedanken ',['r36m','r36w'],'本人の見解内容とその同じ判断を表す伝達。単なる他人の引用とは区別する。'),
        ('über das Fehlerhafte in jenem Symbol, ',['r35t','r326','h243x','r36u','r36v'],'先行する同じ信条について、備えるべき条件の不足を論点とする。欠点の実在を別に断言しない。'),
        ('und Vorschläge ',['h246z','r364','r365','r37e','r37g'],'本人の提案を第二の伝達対象に加える。採用を検討に付す内容を保持し、吟味・善意の修飾は見解側に置く。'),
        ('wegen besserer Einrichtung ',['h246w','h246x','h246y','r36z','r362'],'現行構成と候補を固定基準で厳密に比較し、改善と実施を提案の引用内容として結ぶ。'),
        ('des Religions- und Kirchenwesens, ',['h246v','r363','r364'],'同じ教会の宗教的な教え・実践と教会の制度・組織・運営の領域を保持する。'),
        ('dem Publikum mitzutheilen.',['r36x','r36y','r366','r367','r37a','r37b','r37f','r37g'],'双方に共有される全読者世界への同じ内容の伝達。全宛先へ提示するが受領・理解・賛同は要求しない。'),
    ]
    cursor,clauses=3186,[]
    for text,names,meaning in parts:
        assert unit['text'][cursor:cursor+len(text)]==text,(cursor,text)
        clauses.append(dict(range=[cursor,cursor+len(text)],text=text,definitions=names,reading=meaning));cursor+=len(text)
    assert cursor==3452
    text=unit['text'][3186:3452];count=sum(not c.isspace() for c in text);assert count==230
    page=next(p for p in read(EVIDENCE)['pages'] if p['page']==486)
    assert digest((ROOT/IMAGE).read_bytes())==page['sha256']
    return dict(status='clerical_public_freedom_sentence_reviewed_under_explicit_reading',reviewer='assistant_review',document=FULL,meaning_basis=BASIS,
        source=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[3186,3452],text=text),selection=selection_binding(catalog(),[87]),
        clauses=clauses,interpretation=LIMITS,unresolved=[],decision='equivalent_under_stated_reading_for_scholarly_freedom_calling_and_contrast',
        whole_sentence_semantically_verified=True,whole_unit_semantically_verified=False,newly_reviewed_sentence_characters=count,
        preserved_reviewed_sentence_characters=2728,paragraph_reviewed_sentence_characters=2958,semantic_equivalence_automatically_proved=False,
        holistic_review=[
            '原刊486頁の前の職務教示義務、Aberからmitzutheilenまで、次の良心への負担の文を目視通読し、今回の全依存構成と照合した。文の連続した全範囲を上の対応で覆う。',
            '先行の同じ聖職者・教会・信条・主題を共有し、学識者の立場を本人と固定基準から一つに参照する。職務の教示や信条内容の真理を、公的な伝達資格の条件に移さない。',
            '本人の見解・吟味・注意・善意・欠点の論点を別々に保持し、検討済みと真であること、善意と成功した利益を区別した。',
            '改善提案は規則・手続・役割関係の構成を対象とし、比較元・候補・領域・評価基準を採用提案と伝達に共有する。比較の真理や候補の実施は提案内容内に置き、資格や伝達では実行しない。',
            '全資格見解と全提案の全伝達候補への自由と、全項目を期間内にいずれかの方法で伝える使命を区別する。原文にない日時・締切や全案の採用は補わない。',
            '自由節と使命節はいずれも共有不定詞句を受ける。慎重な吟味と善意はGedankenを修飾する読みを明示し、提案側へ追加しない。',
            'ja sogarの追加焦点と期待背景を世界内容から分け、Aberを直前の職務制約との対照として保持する。先行義務を撤回せず、自由・使命・実行を相互に導出しない。',
            '全文と両節は段階3で帰属し、同じ範囲・順序と段階2の期待比較を保持する。帰属検査で引用した規範・伝達・期待背景の真理を要求しない。有限検査と明示解釈の通読判断を区別する。'],
        original_page=page,source_sha256={p:digest((ROOT/p).read_bytes()) for p in (FULL,BASIS,ANNOTATIONS,DOC,INVENTORY,EVIDENCE,IMAGE,LEXICAL,*PRIOR)})


@lru_cache(None)
def structure_checks():
    old,new=parent(),catalog()
    assert new.document['statements'][:87]==old.document['statements'] and len(new.document['statements'])==88
    assert all(new.entries[n]==e for n,e in old.entries.items())
    for lib in dependencies():
        for n,e in lib.entries.items():assert new.entries[n]['declaration']==e['declaration'] and new.entries[n]['meaning_ja']==e['meaning_ja'],n
    reviews=load_reviews(ROOT,INDEX)['works']['kant-1784']
    for row in reviews:assert row['selection']==selection_binding(new,[s['index'] for s in row['selection']['statements']])
    for path in PRIOR:validate_hashes(ROOT,read(path)['source_sha256'])
    prior=read('data/clerical-obligation-reading-v1.json')
    assert prior['selection']==selection_binding(new,[86]);validate_hashes(ROOT,prior['source_sha256'])
    validate_hashes(ROOT,{r['raw_archive']:r['raw_sha256'] for r in read(LEXICAL)['sources']})
    assert read(AUDIT)==reading()
    for path,body in build().items():assert (ROOT/path).read_text(encoding='utf-8')==body,path
    for path in (FULL,CORE):
        doc=parse((ROOT/path).read_text(encoding='utf-8'))
        for notation in ('compact','full'):
            text=format_graph(doc,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    return dict(preserved_statements=87,added_statements=1,preserved_whole_unit_reviews=len(reviews),new_definitions=len(MEANINGS),
        new_primitives=len(PRIMITIVES),new_reviewed_sentence_characters=230,roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for path,body in build().items():write_exact(ROOT/path,body)
    write_exact(ROOT/AUDIT,encoded(reading()))


def build_report():
    results={}
    for name,fn in [('native',native_checks),('scope',scope_checks),('discourse',discourse_checks),('unknown',unknown_checks),('structure',structure_checks)]:
        results[name]=fn();print(name+' checked',flush=True)
    paths=set(build())|set(catalog().source_sha256)|{INDEX,AUDIT,DOC,INVENTORY,EVIDENCE,IMAGE,LEXICAL,*PRIOR,
        'data/clerical-obligation-reading-v1.json','scripts/compose_clerical_public_freedom.py','scripts/check_clerical_public_freedom.py',
        'tests/test_clerical_public_freedom.py','scripts/check_scholarly_mission.py','scripts/compose_civic_example.py',
        'scripts/compose_confessional_teaching.py','scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py',
        'scripts/check_pastoral_roles.py','scripts/check_motive_causes.py'}
    return dict(status='clerical_scholarly_freedom_calling_and_contrast',document=FULL,**results,
        alignment=dict(**read(AUDIT)['source'],statements=[87],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=True,whole_unit_semantically_verified=False,
        verified_full_units={'kant-1784':0,'einstein-1905':0},source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
