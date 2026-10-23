"""Review the auxiliary-coordinate and synchronized-time paragraph as a whole."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_comoving_time_task import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,INDEX,LIMITS
from scripts.check_comoving_time_task import DOC,SOURCE,INVENTORY,PRIOR,DEPENDENCIES,source_record

REPORT='reports/comoving-time-task-v1.json';REVIEW='data/einstein-comoving-time-task-review-v1.json'
CLAUSES=(
 ('Setzen wir [M0084], ',['sin','eizr','zdm'],'同じv,x,tでx′=x-vtと置く補助量の定義を、著者による導入として保持する。'),
 ('so ist klar, daß ',['eizr','uh','zdg'],'定義を置いた同じ設定で後続内容を主張し、明白だと提示する役割を保持する。'),
 ('einem im System [M0085] ruhenden Punkte ',['eizm','eizn','eizo','eizp'],'全配置点を同じk静止範囲へ結び、自系代表位置の完全な静止、同じK並進、同じ点・出来事・各系の時点と測定値の接続を要求する。'),
 ('ein bestimmtes, von der Zeit unabhängiges Wertsystem [M0086] zukommt. ',['sih','sij','sil','eizp','eizq'],'全点・全時点で三値が利用でき、同じ点の全時点対でx′,y,zが一定であることを保持する。正の時間幅と全区間時刻の被覆を保ち、点同士の値の一致やξへの等置は加えない。'),
 ('Wir bestimmen zuerst [M0087] als Funktion von [M0088] und [M0089]. ',['eizu','eizv','eizw','zdn'],'まずτをx′,y,z,tの四引数関数として求める下位課題を、同じ出来事の現在の全座標対応に結ぶ。質問を解の発見済みへ替えない。'),
 ('Zu diesem Zwecke haben wir in Gleichungen auszudrücken, daß ',['eiz2','zdo'],'同じτ探索を目的とし、次の時計指示との一致条件を方程式で表す必要を保持する。具体式や導出成功を先取りしない。'),
 ('[M0090] nichts anderes ist als der Inbegriff der Angaben ',['eizz','eiyg','eiy3'],'同じ全比較出来事における全局所配備時計の指示と候補τの過不足ない値対応を保持する。全有効読取値を比較し、指示の欠落と余分な値を許さない。'),
 ('von im System [M0091] ruhenden Uhren, ',['eiyf','eiye','eiyg','eizz'],'初期から同じ全配備時計の集団と、その同じkにおける代表配置の静止・校正・局所表示を保持する。'),
 ('welche nach der im § 1 gegebenen Regel synchron gemacht worden sind.',['eiyf','qo','eiyo','eiz2','eislp'],'同じ全時計集団の共通参照と全対全試行の同期条件を使い、第一節の規則への本文参照を同じkの局所表示に結ぶ。'),
)
REASONS=(
 '固定原文u0048全437文字・314本文文字と8数式要素を原刊898頁で再照合した。三文を九つの連続範囲に分け、Setzenからworden sindまで欠落なく保持する。',
 '補助量定義、静止点の全時点不変性、明白さ、先に求める量、四引数関数の質問、同じ目的のため方程式で表す必要、時計指示全体との過不足ない一致、静止・同期条件を合成した。',
 '同じK,k、移動後設定、v、三軸、長さ・時間単位を引き継ぐ。点のymと各系ylを同じ代表位置・出来事・測定地点へ結び、候補関数は現在のeiy3/eiyz/eiy2/eiyyを使う。第一節の参照、同じτ探索と先行方程式探索の課題を保持する。',
 '第一文は著者の定義導入と明白さを伴う主張、第二文は最初の量の決定課題、第三文はそのための必要条件の提示である。引用から物理的真理や解の発見済みを導かず、三メッセージを同じ著者・論説・本文順序へ帰属する。',
 'x′=ξ、t=τ、全点へのK時計新設、時計内部の停止、異なる点の座標一致、未測定の全実数四組の実現、具体的なLorentz変換や光往復式を加えない。静止点の成功標本、端点、時計一台、候補値の存在だけへ全称条件を縮めない。',
 '対象は同じ座標配置と全比較区間・出来事であり、静止点・時計指示の全範囲を既存規約へ結ぶ。Inbegriffはその範囲の局所表示全体、nichts anderesは全有効値についての同値条件として読む。新規原始関係はなく、17定義で既存の数値演算、履歴、測定、時計、引用と課題を合成する。',
 '原刊・固定本文・先行判断・数値核・時計同期・履歴の証拠を保持し、今回の接続対照と分離して扱う。二値域での存在結合と明示した実数型射影を使った全称構造検査は、無限域の物理的真理や同義性の証明ではない。元の無限域を有限評価しないことも確認する。',
 '前段の座標対応と一様性、後続の光往復の設定を含めて三文を通読した。補助量と運動系座標を区別し、同じ比較範囲の全静止点と同期時計の指示全体という明示した読みの下で、意味内容・提示役割・指示対象・目的・順序を欠落なく記述したと判断する。',
)

@lru_cache(None)
def record():
    source=source_record();catalog=load_catalog(ROOT,BASIS);clauses=[];offset=0
    for text,symbols,reason in CLAUSES:
        assert source['text'][offset:offset+len(text)]==text
        assert all(n in catalog.entries for n in symbols)
        clauses.append(dict(range=[offset,offset+len(text)],text=text,definitions=symbols,reason=reason));offset+=len(text)
    assert offset==437
    paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,PRIOR,*DEPENDENCIES,'scripts/review_comoving_time_task.py','tests/test_comoving_time_task_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT,*DEPENDENCIES):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    return dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=source['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=source['unit_sha256'],text=source['text'],range=source['range'],math=[{k:m[k] for k in ('id','sha256')} for m in source['math']]),selection=selection_binding(catalog,list(range(INDEX,INDEX+3))),source_order_statements=list(range(INDEX,INDEX+3)),clauses=clauses,interpretation=LIMITS,limits=['明示した解釈の下でのアシスタントの通読判断。独立査読、全実数上の物理的定理、同義性の自動証明ではない。','具体的なτの変換式とu0049以降、二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC]),reviewed_prose_characters=314,source_sha256=pins)

def prepare():
    from scripts.audit_opening_scope import write_exact
    write_exact(ROOT/REVIEW,json.dumps(record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    rec=record();assert json.loads(read(REVIEW))==rec
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY)
    validate_review(ROOT,REVIEW,'einstein-1905',active,load_catalog(ROOT,BASIS),json.loads(read(INVENTORY)))
    return dict(status='auxiliary_invariance_and_synchronized_time_three_sentences_reviewed',document=FULL,source_units={'einstein-1905:u0048':314},whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':1},general_physical_invariance_proved=False,concrete_tau_transformation_derived=False,semantic_equivalence_automatically_proved=False,source_sha256=rec['source_sha256']|{REVIEW:digest((ROOT/REVIEW).read_bytes())})
