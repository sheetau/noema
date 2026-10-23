"""Review the complete coordinate-correspondence and equation-task sentence."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_event_coordinate_task import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,INDEX,LIMITS
from scripts.check_event_coordinate_task import DOC,SOURCE,INVENTORY,PRIOR,DEPENDENCIES,source_record

REPORT='reports/event-coordinate-task-v1.json';REVIEW='data/einstein-event-coordinate-task-review-v1.json'
CLAUSES=(
 ('Zu jedem Wertsystem [M0081], ',['eiyz','eiy3','sgv','sgw','sha','eiy6'],'有効な静止系の四座標の全範囲を対象とし、x,y,z,tの三位置・時刻の役割を既出の規則へ結ぶ。有限標本や任意の実数四組へ範囲を替えない。'),
 ('welches Ort und Zeit eines Ereignisses im ruhenden System vollkommen bestimmt, ',['eiyu','eiyv','eiyw','eiyx','shl','eixu','eiyi','eiyj'],'同じ出来事の場所を三つの測定値の全候補から唯一に特定し、同じ場所の一意な時計時刻と系内時点の値へ第四成分を結ぶ。出来事個体の唯一性は要求しない。'),
 ('gehört ein jenes Ereignis relativ zum System [M0082] festlegendes Wert System [M0083], ',['eiyy','eiy2','eiy3','sgu','sgv','sgw','eiy6'],'同じ一つの出来事を同じ移動系kで指定するξ,η,ζ,τの存在と値としての一意な対応を保持する。別出来事の組合せ、全系共通の値、逆方向の一意性へ替えない。'),
 ('und es ist nun die Aufgabe zu lösen, ',['eiy7','eiza','eizb','zdc'],'現在の論述段階で解く課題として提示する役割を、先行の対応主張と同じ設定・著者へ結ぶ。発見済みの報告ではない。'),
 ('das diese Größen verknüpfende Gleichungssystem zu finden.',['eiy4','eiy5','sgx','sgy','sgz'],'同じ二組の量の対応と方程式列の解集合が過不足なく一致する条件を質問の答え条件にする。具体式・線形性・導出や解法は先取りしない。'),
)
REASONS=(
 '固定原文u0046の全289文字・227本文文字とM0081〜M0083を原刊898頁の一文へ照合した。Wert Systemの分かち書き以外に内容を変える差はなく、全文を連続した五範囲として保持する。',
 'Zu jedemの全範囲、場所と時刻の完全な特定、同じ出来事への二系の対応、四値の存在と一意性、今求める方程式系の課題、量と式の解集合の対応を列挙して合成した。',
 '静止系raと先行zcgでkと命名したzbm、同じ移動後設定zb6、三軸と時間の四役割、全比較出来事zc4を保持する。空間測定eixuと時計時刻eiyi、tのeiwtとτのeiymに結び、同じ出来事を二系で追跡する。',
 '前半は第三節の思考設定の範囲内での対応の主張、後半はその対応を結ぶ方程式を見いだす課題の提示である。著者帰属と本文順序を保ち、質問を解答済みの断言や外部の読者への実行命令に替えない。',
 '同じ場所・時刻の別出来事や同値の別記録を許し、時計のない地点への時刻拡張、任意実数四組の実現、逆方向の一意性、線形性・具体変換式・解の発見済みを追加しない。場所の一意性は全測定空間の条件として扱い、候補を成功例へ狭めない。',
 '三位置値は実際の測定と一意値、第四値は同じ場所の配備時計と全対応時点へ結ぶ。場所特定・全対象の対応・方程式列とその解集合・質問の条件は既存の量化と定義で合成し、新しい原始記号は追加していない。',
 '固定原文と原刊保存物、前段の空間・時刻の証拠、測定値・場所・時刻の結合、全対象対応、方程式の不足・余分な解、提示と引用の有限対照検査を保存する。有限例は一般の座標幾何・物理変換や意味同義性の自動証明ではない。',
 '前段の同じ空間と時計の設定、後段u0047の線形性という別主張に照らして一文全体を再読した。全有効な四座標が同じ出来事を両系で指定し、その対応の方程式を今求めるという明示した読みの下で、範囲・照応・特定条件・課題の役割を欠落なく記述したと判断する。',
)

@lru_cache(None)
def record():
    source=source_record();catalog=load_catalog(ROOT,BASIS);clauses=[];offset=0
    for text,symbols,reason in CLAUSES:
        assert source['text'][offset:offset+len(text)]==text
        assert all(n in catalog.entries for n in symbols)
        clauses.append(dict(range=[offset,offset+len(text)],text=text,definitions=symbols,reason=reason));offset+=len(text)
    assert offset==289
    paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,PRIOR,*DEPENDENCIES,'scripts/review_event_coordinate_task.py','tests/test_event_coordinate_task_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT,*DEPENDENCIES):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    return dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=source['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=source['unit_sha256'],text=source['text'],range=source['range'],math=[{k:m[k] for k in ('id','sha256')} for m in source['math']]),selection=selection_binding(catalog,[INDEX]),source_order_statements=[INDEX],clauses=clauses,interpretation=LIMITS,limits=['明示した解釈の下でのアシスタントの通読判断。独立査読、一般の座標幾何や物理変換、同義性の自動証明ではない。','u0047以降と二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC]),reviewed_prose_characters=227,source_sha256=pins)

def prepare():
    from scripts.audit_opening_scope import write_exact
    write_exact(ROOT/REVIEW,json.dumps(record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    rec=record();assert json.loads(read(REVIEW))==rec
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY)
    validate_review(ROOT,REVIEW,'einstein-1905',active,load_catalog(ROOT,BASIS),json.loads(read(INVENTORY)))
    return dict(status='same_event_coordinate_correspondence_and_equation_task_whole_unit_reviewed',document=FULL,source_units={'einstein-1905:u0046':227},whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':1},semantic_equivalence_automatically_proved=False,source_sha256=rec['source_sha256']|{REVIEW:digest((ROOT/REVIEW).read_bytes())})
