"""Whole-unit reading of exchanged rest and observer roles in shape results."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_reciprocal_shape_results import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,INDEX,LIMITS
from scripts.check_reciprocal_shape_results import DOC,SOURCE,INVENTORY,PRIOR,DEPENDENCIES,source_record

REPORT='reports/reciprocal-shape-results-v1.json';REVIEW='data/einstein-reciprocal-shape-u0117-review-v1.json'
CLAUSES=(
 ('Es ist klar, ',['ejif','zdg'],'同じ帰結を著者が明白と提示する。処理系の自動証明や実験による確認へ替えない。'),
 ('daß die gleichen Resultate ',['ejid','ejie','ejh4','ejic','ejgy'],'一つの形状・三軸寸法・速さの比較・極限の規則を二つの観測方向に適用する。物体の個体名や位置・大きさの数値が同じという意味へ縮めない。'),
 ('von im „ruhenden“ System ruhenden Körpern gelten, ',['ejgi','ejhy','ejhz','ejid'],'Kで剛性・静止・任意形状を保つ同じ全物質点を取り、その有限な三軸幅と現在記録を結ぶ全適格物体の範囲を保持する。引用符付き静止系を絶対静止としない。'),
 ('welche von einem gleichförmig bewegten System aus betrachtet werden. ',['ejhx','ejii','eioj','ejh2','ejh3','ejh6','ejh7','ejia','ejib'],'kから見た全点並進は−vで、現在の四記録も観測系から静止系への順で結ぶ。各k時刻での形状・幅と負方向の極限平面を構成し、Kとkの同時刻面を等置しない。'),
 ('—',['ejih'],'この文の末尾と時計の議論への話題の区切りとして読む。新たな未記述の命題を補わず、著者帰属と前文からの文順を保持する。'),
)
REASONS=(
 '固定u0117を原刊903頁のEs ist klarからwerden. —まで、直前の球・任意形状・極限の段落と続く時計の導入とともに再読した。引用符付きruhenden、同じ結果、一様に動く系からの観測、文末の区切りを対象に含む。数式要素はこの単位にはない。',
 '全物質点の符号付き並進ejhx、同じ出来事の現在四記録ejii、静止側の完全な形状と有限三幅ejhz、観測側の全時刻の全占有形状と実際の三幅ejh4を構成した。負方向でも全位置の平面への極限ejiaと正則変換との一致ejibを同じ形状へ接続した。',
 '一つの共通規則ejidをk静止/K観測/+vとK静止/k観測/−vへ適用する。各適用内では同じ物体・物質点・形状・系・尺度・文脈・速度を保持し、二つの適用の物体は別々に量化する。同じ個体を二系に同時に静止させず、各系の対象時刻と現在記録を保持する。',
 'uhで同じ結果の内容を著者の主張として提示し、zdgで同じ内容の明白さを提示する。eir3で同じ論説と著者へ帰属し、ueで前の適用限界と予告に続ける。引用した内容の物理的真理や、処理系が一般証明を完了したことはこの帰属から導かない。',
 'die gleichen Resultateは既に得た物体の形状・寸法・程度と明示した極限に参照すると読む。後続で示すとの予告を現在の実証済み結果にせず、時計の結果も先取りしない。有限射影幅・同時刻座標・下側極限・既存の平行軸と共通尺度の読みを継承し、光学像や加速履歴を補わない。',
 '新しい基本記号は追加せず、全点履歴、順序、実切断の演算、現在の測定記録、完全な形状占有、軸射影幅、平方根、引用と談話関係を合成した。正速度専用の旧eipfを負速度に無理に流用せず、同じ三成分変位の数値核と全点履歴を符号付きで構成した。',
 '全成員の正負の並進、逆変換の四成分、静止系と観測系の区別、異なる時刻区間、三つの実際の幅、移動中心と正半軸、非連結形状、正負の極限平面、全物体の範囲、二方向で同じ規則を使うことを対照検査した。全実数量化は保持し、有限検査と意味判断を分ける。',
 '一文全体と前後を再読した。直前の幾何学的結果を同じ共通規則として両方向へ適用するという明示した読みの下で、静止する物体、一様に動く観測系、同じ帰結と著者の明白さの提示を欠落なく保持したと判断する。続くu0118の時計の設定と問いは別に残る。',
)

@lru_cache(None)
def record():
    catalog=load_catalog(ROOT,BASIS);s=source_record()['segments'][0]
    paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,PRIOR,*DEPENDENCIES,'scripts/review_reciprocal_shape_results.py','tests/test_reciprocal_shape_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT,*DEPENDENCIES):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    clauses=[];offset=0
    for text,symbols,reason in CLAUSES:
        assert s['text'][offset:offset+len(text)]==text and all(n in catalog.entries for n in symbols)
        clauses.append(dict(range=[offset,offset+len(text)],text=text,definitions=symbols,reason=reason));offset+=len(text)
    assert offset==len(s['text']) and len(REASONS)==len(REQUIREMENTS)
    return dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[]),selection=selection_binding(catalog,[INDEX]),source_order_statements=[INDEX],clauses=clauses,interpretation=LIMITS,limits=['直前の形状・三軸寸法・程度・明示した光速極限を指すという読みの下でのアシスタントによる通読判断。原文の全ての可能な読みの包含、独立査読、物理的真理や意味同値の自動証明ではない。','u0118以降と二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC]),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins)

def prepare():
    from scripts.audit_opening_scope import write_exact
    write_exact(ROOT/REVIEW,json.dumps(record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    r=record();assert json.loads(read(REVIEW))==r
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY)
    validate_review(ROOT,REVIEW,'einstein-1905',active,load_catalog(ROOT,BASIS),json.loads(read(INVENTORY)))
    return dict(status='reciprocal_body_shape_results_whole_unit_reviewed',document=FULL,source_units={r['unit']:r['reviewed_prose_characters']},reviewed_math_elements=0,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':1},semantic_equivalence_automatically_proved=False,source_sha256=r['source_sha256']|{REVIEW:digest((ROOT/REVIEW).read_bytes())})
