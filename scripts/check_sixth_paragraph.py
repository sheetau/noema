"""Review the complete sixth paragraph without changing its twelve assertions."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest,selection_binding,validate_hashes,REQUIREMENTS
from scripts.compose_grounded_step import ROOT
from scripts.check_fifth_paragraph import calls,named

FULL='examples/v016/kant-royal-intervention-sentence.noema'
BASIS='data/royal-intervention-sentence-basis-v1.json'
ANNOTATIONS='data/royal-intervention-sentence-identifiers-v1.json'
INDEX='data/semantic-review-index-v191.json'
INVENTORY='artifacts/written-units-v1/kant-1784.json'
PARAGRAPH='data/sixth-paragraph-reading-v1.json'
REVIEW='data/sixth-paragraph-review-v1.json'
REPORT='reports/sixth-paragraph-v1.json'
DOC='docs/sixth-paragraph-v1.md'
STEMS=('covenant-question','covenant-nullity','cohort-covenant-denial','posterity-rights','legislative-touchstone',
    'provisional-order-sentence','fixed-compact-sentence','personal-renunciation-sentence','monarchical-sentence',
    'monarchical-religion-sentence','royal-intervention-sentence')
SENTENCES=tuple('data/'+n+'-reading-v1.json' for n in STEMS)
PRIORS=tuple('reports/'+n+'-v1.json' for n in STEMS)
IMAGES=('artifacts/spiritual-guardians-v1/page-488.jpg','artifacts/law-enactment-v1/page-489.jpg',
    'artifacts/personal-enlightenment-v1/page-490.jpg','artifacts/royal-writing-oversight-v1/page-491.jpg')
ROOTS=('r472','r473','r5bv','r5do','r5eh','r5e4','r5hw','r5kj','r5ma','r5mv','r5o4','r5sa')
NODES=('h255s','h255t','h257r','h26bd','h26bx','h26co','h26ei','h26fi','h26gd','h26gw','h26h5','h26jn')
LIMITS=[
    '11件の文別判断に含まれる十二文の採用解釈を保持する。各記録の「後続は未完」は作成時の進捗であり、今回の意味条件ではない。全4,155文字・3,549非空白文字を一つの段落として通読し、文別の合算だけで判断しない。',
    '冒頭の団体は教会会議又はClassisだけに限定しない。呼称の敬称と自己呼称は同じ名称形式へ結ぶ。不変の信条への相互宣誓・全成員への後見・成員を媒介とする全人民への後見・永続化は同じ共同目的であり、その成功を断言しない。',
    '資格の全面的否認、契約の全規範的帰結への無効性、最高権力等の確認があっても無効という譲歩を区別する。現実の形成不能や契約の不存在、確認済みの歴史的事件へ替えない。',
    '先行時代と次の時代、全後代の人々、同じ企て・本性・使命・進展・決議を保持する。認識獲得・訂正・自己判断の進展を異なる構成として扱う。前後時代の成員重複を排除せず、後代を血縁だけに限定しない。',
    '人間本性への侵害と後代による拒否の積極的許可、決議の無権限な採択と不遜な評価を分ける。原文の根拠提示を論理的妥当性の証明にせず、許可から全員の実際の拒否又は全手段の無限定な許可を導かない。',
    '立法の試金石は全検討範囲で一般の採択可能性と同じ人民による自己賦課可能性の同値と読む。この明示した判定基準を、現実の全員一致又は特定君主への権限授与に置換しない。',
    '暫定秩序は同じ人民・法・導入活動・制度・期間と全市民を保つ。最初の十分な到達点という操作的読解と比較モデルを明記した文別判断を継承する。現実の必然的到達、全法案の一括許容、全市民個別の全知識は補わない。',
    '同じ暫定秩序の下で公的批評の自由、洞察の公開と確証、共同提案、改革側の保護と維持意向側への非妨害を結ぶ。王座と洞察の表現を身体的な椅子又は抽象物の発声へ替えない。反対に持続的な問い直し禁止の合意は一人生涯内でも不許可とする。',
    '期間を不毛にする因果的帰結と後代への害の推量を分ける。期間の字義的消失や全員の個別被害を加えない。本人の一時的延期の許容を、全有限期間への許可や本人・後代の放棄への許可へ広げない。',
    '同じ人民と君主の決定範囲、人民意志の規範的な統合、立法権威の必要な根拠を保持する。市民的秩序の監督と宗教的な必要性の代決を区別し、所管外と強制的妨害を防ぐ積極的な職責をともに残す。',
    '最終文の威厳は公的地位の尊重に関わる側面、最高の見識は君主自身の評価と読む。内容審査と好意的描写への批判的距離、格言の字義と宗教的認識への適用、宗教的専制支援の不相応な権能使用を区別する。比較の全対応対を結果で選別しない。',
    '全十二文で著者帰属・疑問と自己回答・仮定・譲歩・理由・比喩・対照・強調・引用の作用域を保つ。引用された内容の真理と現実の発言・政策実施を分ける。有限検査と境界接続、原刊照合、通読判断は別の証拠であり、独立査読又は自動同値証明ではない。',
]
REASONS=[
    '固定原文u0013の全4,155文字・3,549非空白文字を原刊488–491頁で通読した。11文別記録に含まれる十二文が非空白位置を重複なく覆い、文間の未選択位置は空白だけである。数式はない。',
    '相互宣誓への資格の問いと否認、契約の無効性と譲歩、後代の進展を妨げる拘束、本性への侵害と拒否資格、立法の試金石、暫定秩序と持続的固定の対照、本人の延期と放棄、人民と君主、所管と職責、最終の介入批判を一つの議論として確認した。量化・否定・条件・様相・程度・時間・因果を保持する。',
    '同じ団体・合意・目的・成員・人民、先行時代と次代・後代、本性と使命、法と制度・期間、共同提案と会衆、個人と後代の啓蒙、君主と最高職・同じ臣民の理解を各照応先に結ぶ。全十二文は第六段落の提示文脈h255nを共有する。',
    '否定疑問とその同じ内容への全面的回答、法の試金石を置く問い、条件付き主張・目的・根拠・譲歩・思案・推量・見立て・皮肉・ラテン語引用を区別する。原刊の疑問符と大文字を固定転記と照合し、別の版へ書き換えない。',
    '永久的後見の達成や現在の合意の存在を補わない。暫定秩序の保持を永久固定へ替えず、推量を中心内容への無条件連言にせず、延期から放棄許可を導かない。市民的秩序の監督と知的内容への統治的介入を区別し、規範的許容から履行や成功を導かない。',
    '公開した意味規約と合成定義で、資格・義務・無効性・目的・因果・認識・進展・権利・主体と制度・期間・役割・引用・程度を追跡する。原語の綴りや一文専用の真偽記号で代用しない。解釈範囲・評価基準・比較場面の完全な供給は解釈入力の責任として保持する。',
    '原刊四頁、各文の全語句対応と読解、局所報告、現行本文の依存意味と識別表記の一致を別々に確認して保存する。旧判断を変更せず、今回の全段落判断に必要な選択と理由を新記録へ残す。',
    '段落を通読し、将来の公的問い直しと進展を閉ざす合意の否認から、暫定秩序の条件、本人の自由と後代の権利、君主の権限の限界と介入批判へ至る論旨を確認した。明示した読解の下で未処理の語句又は文間参照はない。次段落の啓蒙時代の現状判断は混入していない。',
]

def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
def unit():return next(u for u in read(INVENTORY)['units'] if u['id']=='kant-1784:u0013')
def rows():return [dict(record=p,source=read(p)['source'],selection=read(p)['selection']) for p in SENTENCES]
def indices():return list(range(96,108))
def merge_pins(paths):
    pins=dict(catalog().source_sha256)
    for p in paths:
        for name,sha in {p:digest((ROOT/p).read_bytes()),**read(p).get('source_sha256',{})}.items():
            assert name not in pins or pins[name]==sha,name
            pins[name]=sha
    return pins

def paragraph_reading():
    source=unit();paths={FULL,BASIS,ANNOTATIONS,INVENTORY,DOC,*SENTENCES,*IMAGES}
    return dict(status='sixth_paragraph_reviewed_under_explicit_reading',reviewer='assistant_review',document=FULL,meaning_basis=BASIS,
        source=dict(unit=source['id'],unit_sha256=source['text_sha256'],range=[0,len(source['text'])],text=source['text']),
        selection=selection_binding(catalog(),indices()),sentence_readings=rows(),interpretation=LIMITS,
        requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS,strict=True)],
        decision='equivalent_under_stated_reading',unresolved=[],source_nonblank_characters=3549,
        inherited_sentence_characters=3549,additional_punctuation_characters=0,
        semantic_equivalence_automatically_proved=False,no_independent_review=True,
        facsimile=dict(artifacts=list(IMAGES),pages=[488,489,490,491],visually_collated=True,
            differences='長いs、行末分綴、改頁の送り語を照合。立法試金石は原刊489頁の疑問符を保持し、AAの句点へ変更しない。490頁のseinenと大文字Grammaticosを固定転記で保持する。'),
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})

@lru_cache(None)
def coverage_checks():
    source=unit();covered=set();count=0
    for row in rows():
        record=read(row['record']);s=row['source'];a,b=s['range']
        assert s['unit']==source['id'] and s['unit_sha256']==source['text_sha256']
        assert s['text']==source['text'][a:b] and record['whole_sentence_semantically_verified']
        assert not record.get('unresolved') and not covered.intersection(range(a,b))
        covered.update(range(a,b));count+=sum(not c.isspace() for c in s['text'])
    assert count==3549 and len(source['text'])==4155
    assert all(i in covered for i,c in enumerate(source['text']) if not c.isspace())
    assert sum(not c.isspace() for c in source['text'])==count
    assert digest(source['text'].encode('utf-8'))==source['text_sha256']
    assert read(PARAGRAPH)==paragraph_reading()
    return dict(sentence_records=11,source_sentences=12,whole_paragraph_nonblank_characters=3549,
        inherited_nonblank_characters=3549,additional_characters=0,all_nonblank_positions_covered=True,no_double_counting=True)

@lru_cache(None)
def transition_checks():
    c=catalog();ctx=named('h255n');a=named('wa');previous='h254d';edges=[]
    for i,(root,node) in enumerate(zip(ROOTS,NODES,strict=True),96):
        assert c.document['statements'][i]['body']==dict(kind='call',symbol=root,arguments=[])
        d=c.entries[root]['declaration'];edge=[named(previous),named(node),ctx]
        assert any(x['arguments']==edge for x in calls(d,'ue')),(root,previous,node)
        for x in calls(d,'ue'):assert x['arguments'][-1]==ctx
        for x in calls(d,'h236i'):assert x['arguments'][1]==a and x['arguments'][-1]==ctx
        assert 'h255n' in selection_binding(c,[i])['dependencies']
        edges.append([previous,node]);previous=node
    answer=c.entries['r473']['declaration']
    assert any(x['arguments']==[a,named('h255s'),named('h255t'),ctx] for x in calls(answer,'hzcs'))
    assert any(x['arguments'][1:4]==[a,named('h255s'),named('h255t')] and x['arguments'][-1]==ctx for x in calls(answer,'h236m'))
    # Later discussion uses the same monarch/office and personal religious domain,
    # while legislative standing and public dignity retain distinct relations.
    prevdeps=set(selection_binding(c,[106])['dependencies']);lastdeps=set(selection_binding(c,[107])['dependencies'])
    assert {'r2uj','r2ui','h234f','r5ni','h26g7'}<=prevdeps&lastdeps
    assert 'h26io' in lastdeps and 'r5mv' not in lastdeps
    assert read(SENTENCES[-1])['quotation']['literal']!='r5ry'
    return dict(all_sentence_order_edges=edges,same_paragraph_presentation_context=True,same_question_and_self_answer=True,
        monarch_office_subjects_and_religious_domain_preserved=True,no_new_language_relations=True)

@lru_cache(None)
def preservation_checks():
    c=catalog();assert len(c.document['statements'])==108
    selected=[]
    for row in rows():
        idx=[x['index'] for x in row['selection']['statements']];selected.extend(idx)
        assert row['selection']==selection_binding(c,idx),row['record']
    assert selected==indices()
    prior=load_reviews(ROOT,INDEX)['works']['kant-1784'];assert len(prior)==15
    for row in prior:assert row['selection']==selection_binding(c,[x['index'] for x in row['selection']['statements']])
    pins=merge_pins([*SENTENCES,*PRIORS,PARAGRAPH]);validate_hashes(ROOT,pins)
    return dict(preserved_whole_unit_reviews=15,unchanged_sentence_bindings=11,unchanged_local_reports=len(PRIORS),
        no_manuscript_or_language_changes=True,hash_pinned_files=len(pins),paragraph_statements=indices())

def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    write_exact(ROOT/PARAGRAPH,encoded(paragraph_reading()))

def build_report():
    results={}
    for n,fn in [('coverage',coverage_checks),('transitions',transition_checks),('preservation',preservation_checks)]:
        results[n]=fn();print(n+' checked',flush=True)
    paths=set(merge_pins([*SENTENCES,*PRIORS,PARAGRAPH]))|{DOC,INDEX,PARAGRAPH,INVENTORY,FULL,BASIS,ANNOTATIONS,*IMAGES,
        'scripts/check_sixth_paragraph.py','scripts/check_fifth_paragraph.py','tests/test_sixth_paragraph.py'}
    return dict(status='sixth_paragraph_explicit_reading_checked',document=FULL,**results,
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
    return dict(schema_version='noema-semantic-review-1',work='kant-1784',unit='kant-1784:u0013',reviewer='assistant_review',
        decision=record['decision'],document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,
        source=dict(inventory=INVENTORY,unit_sha256=unit()['text_sha256'],text=unit()['text'],range=[0,len(unit()['text'])],math=[]),
        selection=record['selection'],interpretation=record['interpretation'],
        limits=['明示した読みの下でのアシスタント判断。独立査読・自動同値証明ではなく、各文の解釈上の限界を継承する。',
            '全歴史的含意の同時復元でも原著者の主張の真理の証明でもない。',
            '第七段落以降とアインシュタイン論文は未完。'],unresolved=[],requirements=record['requirements'],evidence=evidence,source_sha256=pins)
