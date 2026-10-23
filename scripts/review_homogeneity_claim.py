"""Review the source's first homogeneity-based requirement on the coordinate task."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_homogeneity_claim import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,INDEX,LIMITS
from scripts.check_homogeneity_claim import DOC,SOURCE,INVENTORY,PRIOR,DEPENDENCIES,source_record

REPORT='reports/homogeneity-claim-v1.json';REVIEW='data/einstein-homogeneity-claim-review-v1.json'
CLAUSES=(
 ('Zunächst ',['eizi','eizl'],'同じ方程式探索課題の最初の主要検討段階として、その所属と他の全主要段階への先行を保持する。'),
 ('ist klar, ',['eizj','zdg'],'同じ線形性の内容についての著者による明白さの提示であり、処理系の自明性認定ではない。'),
 ('daß die Gleichungen linear sein müssen ',['eizd','eizf','eizg','eizj','sht','zdh'],'同じ座標対応を表す変換が全入力に共通する行列と定数を持つというアフィン形を、先行課題への必要条件として保持する。'),
 ('wegen der Homogenitätseigenschaften, ',['eize','shs','shr','eizj','zc'],'全対象の同じ変位の比較が出発点に依存しないことを理由に、同じアフィン形が従わなければならないという著者の理由づけを保持する。'),
 ('welche wir Raum und Zeit beilegen.',['eizc','eizd','eize','eizh'],'空間三方向と時間の四変位を同じ計器規約の場所・局所時刻へ結び、その比較規則に特権的な出発点がないという読みの一様性を著者の採用内容にする。'),
)
REASONS=(
 '固定原文u0047の全129文字・112本文文字を原刊898頁と照合した。数式置換要素はなく、linearの強調を含む一文全体を連続した五範囲で保持する。',
 '最初という順序、明白さの提示、同じ方程式のアフィン形、課題への必要条件、一様性からの理由の向き、空間と時間への著者の性質帰属を列挙して接続した。',
 '前段の同じ二系・移動後設定・長さと時間の単位・四役割を保持する。全入力域は現行のeiyzの測定済み四座標、変換は同じ出来事のeiyyに適合させ、必要条件を同じ方程式探索箇所zdbへ結ぶ。',
 '一様性は著者が同じ思考設定に採る規約、必要性と明白さは著者による提示として記述する。引用内容の実験的真理、一般的導出の検証、解の発見済みを述べたことにしない。',
 '原点一致・零定数、入力ごとに変わる係数、原文にない連続性、全物理法則の一様性一般、任意の同値な数式表記までの一次性を追加しない。零変位・一地点・一つの方向だけの条件へ弱めず、全有効入力対と全許容四変位を保つ。',
 '一様性は現在の実測地点と局所時計に結んだ座標比較の出発点独立性として明示する。アフィン形は全入力に共通する行列と原点定数を全称・存在量化で合成する。唯一の新規原始関係は一般的な課題の主要段階への所属であり、最初・必要性・物理内容を一語へ押し込まない。',
 '原刊保存物、固定原文、先行座標対応の判断、既存の数値・正規化・有理多項式の証拠を保持した。今回の有限対照と明示した型射影は全実数の標本認定に使わず、元の無限関数域の拒否を確認する。一様性から一般実数上のアフィン性への逆向きの証明は行っていない。',
 '先行する方程式探索と後続する具体的な変数設定に照らして一文全体を再読した。この運動学の座標比較の一様性と原点定数を許すlinearという明示した読みの下で、著者の性質帰属、理由、必要性、明白さ、まずという役割を欠落なく記述したと判断する。',
)

@lru_cache(None)
def record():
    source=source_record();catalog=load_catalog(ROOT,BASIS);clauses=[];offset=0
    for text,symbols,reason in CLAUSES:
        assert source['text'][offset:offset+len(text)]==text
        assert all(n in catalog.entries for n in symbols)
        clauses.append(dict(range=[offset,offset+len(text)],text=text,definitions=symbols,reason=reason));offset+=len(text)
    assert offset==129
    paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,PRIOR,*DEPENDENCIES,'scripts/review_homogeneity_claim.py','tests/test_homogeneity_claim_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT,*DEPENDENCIES):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    return dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=source['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=source['unit_sha256'],text=source['text'],range=source['range'],math=[]),selection=selection_binding(catalog,[INDEX]),source_order_statements=[INDEX],clauses=clauses,interpretation=LIMITS,limits=['明示した解釈の下でのアシスタントの通読判断。独立査読、一様性からの一般的導出や物理的真理、同義性の自動証明ではない。','u0048以降と二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC]),reviewed_prose_characters=112,source_sha256=pins)

def prepare():
    from scripts.audit_opening_scope import write_exact
    write_exact(ROOT/REVIEW,json.dumps(record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    rec=record();assert json.loads(read(REVIEW))==rec
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY)
    validate_review(ROOT,REVIEW,'einstein-1905',active,load_catalog(ROOT,BASIS),json.loads(read(INVENTORY)))
    return dict(status='homogeneity_affine_necessity_and_first_step_whole_unit_reviewed',document=FULL,source_units={'einstein-1905:u0047':112},whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':1},homogeneity_implies_general_real_affinity_proved=False,semantic_equivalence_automatically_proved=False,source_sha256=rec['source_sha256']|{REVIEW:digest((ROOT/REVIEW).read_bytes())})
