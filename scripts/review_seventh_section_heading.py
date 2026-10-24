"""Record the seventh heading under a shared theoretical-topic reading."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_seventh_section_heading import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,INDEX,LIMITS
from scripts.check_seventh_section_heading import DOC,SOURCE,INVENTORY,DEPENDENCIES,source_record

REPORT='reports/seventh-section-heading-v1.json'
REVIEW='data/einstein-seventh-section-heading-u0178-review-v1.json'
REASONS=(
 'u0178全文を固定転記及び原刊910頁で照合した。§7、Theorie、Doppelerschen Prinzips、und der Aberrationを保つ。見出しの印字を本文の既存呼称と同じ個体の別表記として残す。',
 'ekktは同じ研究と状況にドップラー側ekkrと光行差側ekksを連言する。ドップラーの物理設定ekkpと定式化eke2、光行差の設定ekkqと定式化ekhcを別々に引用し、理論的な説明・条件・原理との関係・導出を扱う主題へ結ぶ。Theorieの射程を片方へ限定しない。',
 '論説eirf、第二部eispb、既存第七節eisrx、固定系ra、光速度tc及び状況riを共有する。設定の56又は61役割を一つの証人群に結び、源・波・観測者・二系・単位・周期数・法線・角を別対象へ取り替えない。呼称ekkvは本文のeisssを返し、eiss3は本文で命名された同じ光行差の内容へ結ぶ。',
 'ekkuはeihqによって深さ2・番号7・第二部に属する節の主題として提示する。直前の第六節末尾と次の波の仮定への順序を保持し、u0201まで、次の同階層のu0202直前までを区分とする。設定や物理法則の真理を断言するメッセージにはしない。',
 'settingsとaccountを分ける一般関係eisthは同じ論点を扱う研究の案内であり、引用の真理や理論の完成、実例の現実成立、実証済みを要求しない。全称法則を設定の条件へ加えない。光行差の角の基準線は本文で採用済みの同時刻の源と観測者の結線であり、印刷式との既知の不整合を解消するための暗黙の訂正をしない。',
 'ドップラーは放射と受信の周期数を同じ波及び相対運動へ結び、光行差は変換後法線・光線方向・旧新の実数角へ結ぶ。原語の名だけを主題の意味に代用しない。新しい一般関係は設定記述と検討する定式化を引数に取る研究主題の規約で、特定の源や式を一つの原始語へまとめていない。',
 '56及び61証人を二値域の各位置で診断し、引用の設定と式の取り違え、別研究・別状況、片方の欠落、同じ名前、節番号・親・階層・前後順序を対照する。実際の速度域は別に評価し、下位の波・観測・角の本体は固定済みの検査証拠へ参照する。無限の設定を有限に列挙せず、旧384主張・意味規約・識別表記を保持する。',
 '見出し全体を第六節の末尾及び第七節冒頭とともに再読した。接続済みの本文におけるドップラー原理と光行差の理論を同じ研究主題として案内する読みの下で、二主題・範囲・参照・提示の役割を欠落なく記述したと判断する。本文の法則が真であることや二つの研究分野の網羅をこの判断から導かない。',
)

@lru_cache(None)
def record():
    catalog=load_catalog(ROOT,BASIS)
    paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,*DEPENDENCIES,'scripts/review_seventh_section_heading.py','tests/test_seventh_section_heading_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT,*DEPENDENCIES):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    s=source_record()['segments'][0]
    symbols=['ekku','eihq','eisdv','eisdw','ekkt','ekkr','ekks','eisth','ekkp','ekkq','ekev','eket','ekgy','eke2','ekhc','eisch','ekkv','eisss','eiss3']
    assert len(REASONS)==len(REQUIREMENTS) and all(n in catalog.entries for n in symbols)
    return dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[]),selection=selection_binding(catalog,[INDEX]),source_order_statements=[INDEX],clauses=[dict(range=s['range'],text=s['text'],definitions=symbols,reason=REASONS[1])],interpretation=LIMITS,limits=['原文全体と提示の役割を照合したアシスタントによる判断。独立査読や意味同値の自動証明ではない。','理論は同じ二つの物理的主題の研究として読む。引用した設定の実在、印刷式の真理、説明や導出の成功は見出しから認定しない。','u0202以降と二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC]),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins)

def prepare():
    from scripts.audit_opening_scope import write_exact
    write_exact(ROOT/REVIEW,json.dumps(record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    r=record();assert json.loads(read(REVIEW))==r
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY)
    validate_review(ROOT,REVIEW,'einstein-1905',active,load_catalog(ROOT,BASIS),json.loads(read(INVENTORY)))
    pins=r['source_sha256']|{REVIEW:digest((ROOT/REVIEW).read_bytes())}
    return dict(status='seventh_section_heading_whole_unit_reviewed',document=FULL,source_units={r['unit']:r['reviewed_prose_characters']},reviewed_math_elements=0,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':1},semantic_equivalence_automatically_proved=False,source_sha256=pins)
