"""Review all four sentences and their shared reference in Kant's seventh paragraph."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest,selection_binding,validate_hashes,REQUIREMENTS
from scripts.compose_named_epoch_sentence import ROOT,FULL,BASIS,ANNOTATIONS
from scripts.check_fifth_paragraph import calls,named

INDEX='data/semantic-review-index-v195.json'
INVENTORY='artifacts/written-units-v1/kant-1784.json'
PARAGRAPH='data/seventh-paragraph-reading-v1.json';REVIEW='data/seventh-paragraph-review-v1.json'
REPORT='reports/seventh-paragraph-v1.json';DOC='docs/seventh-paragraph-v1.md'
STEMS=('present-epoch-sentence','present-shortfall-sentence','progress-indications-sentence','named-epoch-sentence')
SENTENCES=tuple('data/'+n+'-reading-v1.json' for n in STEMS)
PRIORS=tuple('reports/'+n+'-v1.json' for n in STEMS)
IMAGES=('artifacts/royal-writing-oversight-v1/page-491.jpg',)
ROOTS=('r5u7','r5vj','r5vr','r5vv');NODES=('h26la','h26lr','h26mj','h26m4')
LIMITS=[
 '四文の文別判断の解釈を保持する。各記録の後続未完という記載は作成時の進捗であり、今回の意味条件ではない。全778文字・662非空白文字を段落として通読した。次段落に述べる君主の具体的な義務・行為は含めない。',
 '第一文の条件付きの問いと回答は仮定的な論述であり、実際の口頭対話ではない。同じ現在の人々について、宗教的な自力行使能力の集団的到達を否定し、自由な取り組みの機会開放と離脱への障害漸減という進行を肯定する。',
 '第二文は同じ現在人口全体について、既存の能力と支援による能力獲得可能性のそれぞれが固定基準から大きく不足するという読み。全員が全く不能とはしない。可能性の評価と現実の能力、目標である確実で適切な行使と単なる本人の信念を分ける。',
 '第三文は同じ進行の両成分について明瞭な複数の徴候が話者側に利用可能であることを、不足と対照させる。全比較例での識別力という読みを継承する。徴候から対象の現実の真理を演繹せず、未知項目を偽とみなして評価済みにしない。',
 '場の開放という比喩の対象は、同じ人々が本人の宗教的な自力行使能力を目指して取り組める機会。一般的啓蒙と自己に帰責される未成熟からの離脱を説明関係に保つ。障害対象を質付き宗教能力そのものへ強めない。',
 '第四文は同じ進行の観点に限って、同じ現在の時代を啓蒙の時代と呼び、フリードリヒの時代と説明的に呼び換える。人物はフリードリヒ二世。原刊のFriederichsを保持し、百年の長さ・全在位期間との同一性・進展の独占的功績・数値的な在位年は追加しない。',
 '全四文で著者wa、提示文脈h26k7、現在集団h26kh、時代h26ki、固定基準h26kj、実際の例h26kmと現在h26knを共有する。能力の到達・不足と、進行・徴候・呼称をそれぞれの作用域で接続し、内容の引用段階を落とさない。',
 '原刊の通読、全語句対応、局所反例検査と既存証拠の依存一致は異なる根拠として保存する。明示した解釈の下でのアシスタント判断であり、独立査読・原文同値の自動証明・現実の歴史的主張の真理の証明ではない。',
]
REASONS=[
 '原刊491頁と固定転記u0014を全四文通読した。778文字・662非空白文字の全位置が四件の原文範囲で重複なく覆われ、文間は空白だけである。数式はない。',
 '条件付き問答、到達の否定と進行の肯定、現在能力と支援可能性の大きな不足、なおある徴候、観点を限定した二呼称を一つの議論として確認した。量化・否定・様相・程度・変化・識別力と提示作用域を保った。',
 'wir、die Menschen、ihnen、ihrer、dieses Zeitalterを同じ現在人口・時代へ結ぶ。dahinは質付き宗教能力、davonは開放と障害漸減の両側、In diesem Betrachtは同じ進行の観点。Friederichsは名称・人物・役職を分けて結ぶ。',
 '仮定された問いへの同じ回答、Neinとaber wohl、第二文の提示、Alleinと二つのdoch、場の非字義的描写、現在進行、二箇所の説明的なoder、davonとdiesesの照応、最終の限定的呼称を保持する。',
 '未到達を評価不足又は対象不在へ替えず、現実の能力と可能性を同一視しない。進行を達成又は無限の継続に強めず、徴候を真理保証にしない。実際の全人類の同意や単独の王の功績、百年間、在位年・具体的政策を補わない。',
 '能力・支援可能性・集団程度・新規の機会・離脱への障害とその漸減・比較上の識別力・時代の区間と在職の重なりを公開済みの構成で表した。表面の語句や文番号を内容の真理の代わりにしない。解釈入力の完全性の責任と有限評価の範囲を保持する。',
 '文別記録・各局所報告・原刊画像と補助一次資料を固定ハッシュで保存した。本文と意味規約を保持して旧16単位判断を引き継げることを確認し、今回の全段落判断は新規に記録する。',
 '問い、否定と肯定、不足の具体化、なおある進行の徴候、観点を限定した呼称という順序を全体として通読した。前後で人口・時代又は到達と進行の意味を交換していない。採用解釈の下で未処理の語句又は文間参照はない。',
]
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
def unit():return next(u for u in read(INVENTORY)['units'] if u['id']=='kant-1784:u0014')
def rows():return [dict(record=p,source=read(p)['source'],selection=read(p)['selection']) for p in SENTENCES]
def indices():return list(range(108,112))
def merge_pins(paths):
    pins=dict(catalog().source_sha256)
    for p in paths:
        for name,sha in {p:digest((ROOT/p).read_bytes()),**read(p).get('source_sha256',{})}.items():
            assert name not in pins or pins[name]==sha,name
            pins[name]=sha
    return pins
def paragraph_reading():
    u=unit();paths={FULL,BASIS,ANNOTATIONS,INVENTORY,DOC,*SENTENCES,*IMAGES}
    return dict(status='seventh_paragraph_reviewed_under_explicit_reading',reviewer='assistant_review',document=FULL,meaning_basis=BASIS,
        source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],text=u['text']),
        selection=selection_binding(catalog(),indices()),sentence_readings=rows(),interpretation=LIMITS,
        requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS,strict=True)],
        decision='equivalent_under_stated_reading',unresolved=[],source_nonblank_characters=662,
        inherited_sentence_characters=662,additional_punctuation_characters=0,
        semantic_equivalence_automatically_proved=False,no_independent_review=True,
        facsimile=dict(artifacts=list(IMAGES),pages=[491],visually_collated=True,
            differences='長いsと行末分綴を照合。原刊のFriederichsを保持し、AAのFriedrichsに変更しない。段落末と次段落のEin Fürstを区別する。'),
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
@lru_cache(None)
def coverage_checks():
    u=unit();covered=set();count=0
    for row in rows():
        record=read(row['record']);s=row['source'];a,b=s['range']
        assert s['unit']==u['id'] and s['unit_sha256']==u['text_sha256'] and s['text']==u['text'][a:b]
        assert record['whole_sentence_semantically_verified'] and not record.get('unresolved')
        assert not covered.intersection(range(a,b));covered.update(range(a,b));count+=sum(not c.isspace() for c in s['text'])
    assert count==662 and len(u['text'])==778
    assert all(i in covered for i,c in enumerate(u['text']) if not c.isspace())
    assert sum(not c.isspace() for c in u['text'])==count and digest(u['text'].encode('utf-8'))==u['text_sha256']
    assert read(PARAGRAPH)==paragraph_reading()
    return dict(sentence_records=4,source_sentences=4,whole_paragraph_nonblank_characters=662,
        inherited_nonblank_characters=662,additional_characters=0,all_nonblank_positions_covered=True,no_double_counting=True)
@lru_cache(None)
def transition_checks():
    c=catalog();ctx=named('h26k7');author=named('wa');previous='h26jn';edges=[]
    for i,(root,node) in enumerate(zip(ROOTS,NODES,strict=True),108):
        assert c.document['statements'][i]['body']==dict(kind='call',symbol=root,arguments=[])
        d=c.entries[root]['declaration'];edge=[named(previous),named(node),ctx]
        assert any(x['arguments']==edge for x in calls(d,'ue')),(root,previous,node)
        for x in calls(d,'ue'):assert x['arguments'][-1]==ctx
        for relation in ('h236i','h26me'):
            for x in calls(d,relation):assert x['arguments'][1]==author and x['arguments'][-1]==ctx
        deps=set(selection_binding(c,[i])['dependencies'])
        assert {'h26k7','wa','h26kh','h26ki','h26kj','h26km','h26kn'}<=deps
        edges.append([previous,node]);previous=node
    assert len(calls(c.entries['r5u4']['declaration'],'r5uo'))==1
    assert len(calls(c.entries['r5vp']['declaration'],'r5up'))==1
    assert calls(c.entries['r5u4']['declaration'],'r5ux')==calls(c.entries['r5vp']['declaration'],'r5ux')
    assert len(calls(c.entries['r5vs']['declaration'],'r5u4'))==1
    last=c.entries['r5vv']['declaration'];anaphor=calls(last,'h26m3')[0]['arguments']
    assert anaphor[2:4]==[named('h26la'),named('h26ki')]
    assert calls(last,'h26my')[0]['arguments'][-1]==ctx
    return dict(all_sentence_order_edges=edges,same_paragraph_presentation_context=True,
        same_population_epoch_reference_and_current=True,same_progress_for_answer_signs_and_final_aspect=True,no_new_language_relations=True)
@lru_cache(None)
def preservation_checks():
    c=catalog();assert len(c.document['statements'])==112;selected=[]
    for row in rows():
        idx=[x['index'] for x in row['selection']['statements']];selected.extend(idx)
        assert row['selection']==selection_binding(c,idx),row['record']
    assert selected==indices()
    prior=load_reviews(ROOT,INDEX)['works']['kant-1784'];assert len(prior)==16
    for row in prior:assert row['selection']==selection_binding(c,[x['index'] for x in row['selection']['statements']])
    pins=merge_pins([*SENTENCES,*PRIORS,PARAGRAPH]);validate_hashes(ROOT,pins)
    return dict(preserved_whole_unit_reviews=16,unchanged_sentence_bindings=4,unchanged_local_reports=4,
        no_manuscript_or_language_changes=True,hash_pinned_files=len(pins),paragraph_statements=indices())
def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    write_exact(ROOT/PARAGRAPH,encoded(paragraph_reading()))
def build_report():
    results={}
    for n,f in (('coverage',coverage_checks),('transitions',transition_checks),('preservation',preservation_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(merge_pins([*SENTENCES,*PRIORS,PARAGRAPH]))|{DOC,INDEX,PARAGRAPH,INVENTORY,FULL,BASIS,ANNOTATIONS,*IMAGES,
        'scripts/check_seventh_paragraph.py','scripts/check_fifth_paragraph.py','tests/test_seventh_paragraph.py'}
    return dict(status='seventh_paragraph_explicit_reading_checked',document=FULL,**results,
        alignment=dict(**read(PARAGRAPH)['source'],definitions=list(ROOTS),statements=indices(),status='explicit_interpretive_annotation'),
        whole_paragraph_semantically_reviewed=True,verified_full_units={'kant-1784':0,'einstein-1905':0},
        whole_unit_registration='separate_explicit_review_required',semantic_equivalence_automatically_proved=False,
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
def review():
    record=read(PARAGRAPH);validate_hashes(ROOT,read(REPORT)['source_sha256'])
    evidence=dict(source_reading=[PARAGRAPH,*SENTENCES],formal_checks=[REPORT,*PRIORS],semantic_reading=[DOC])
    pins=merge_pins([PARAGRAPH,REPORT,*SENTENCES,*PRIORS])
    for p in (FULL,BASIS,ANNOTATIONS,INVENTORY,DOC):pins[p]=digest((ROOT/p).read_bytes())
    validate_hashes(ROOT,pins)
    return dict(schema_version='noema-semantic-review-1',work='kant-1784',unit='kant-1784:u0014',reviewer='assistant_review',
        decision=record['decision'],document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,
        source=dict(inventory=INVENTORY,unit_sha256=unit()['text_sha256'],text=unit()['text'],range=[0,len(unit()['text'])],math=[]),
        selection=record['selection'],interpretation=record['interpretation'],
        limits=['各文の明示した解釈と限界を継承するアシスタント判断。独立査読・自動同値証明ではない。',
            '原著者の歴史的な主張の真理や、可能な全解釈を同時に再現したという主張ではない。',
            '第八段落以降とアインシュタイン論文は未完。'],unresolved=[],requirements=record['requirements'],evidence=evidence,source_sha256=pins)
