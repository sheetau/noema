"""Review the two squared-speed definitions as the complete unit u0136."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_velocity_magnitude_claim import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,INDICES,LIMITS
from scripts.check_velocity_magnitude_claim import DOC,SOURCE,INVENTORY,PRIORS,DEPENDENCIES,source_record

REPORT='reports/velocity-magnitude-claim-v1.json'
REVIEW='data/einstein-velocity-magnitude-u0136-review-v1.json'

@lru_cache(None)
def record():
    catalog=load_catalog(ROOT,BASIS);s=source_record()['segments'][2]
    assert s['unit']=='einstein-1905:u0136' and s['text']=='[M0252]' and s['range']==[0,7]
    indices=[INDICES[1]];symbols=['ejoh','ejoi','ejoj','ejok','ejol','ejop','ejoq','ejom','ejoo','szn','szq','sjs','ejny','ejmv','ejmu','eismh','eislo','zb']
    assert all(n in catalog.entries for n in symbols)
    reasons=(
        '固定u0136の全範囲[M0252]を原刊905頁で照合した。先行のWir setzen:、表示された二行U²=(dx/dt)²+(dy/dt)²とw²=wξ²+wη²、後続のundと角度の導入を続けて読んだ。二微分の分母は同じdt、wの二添字はξ/ηである。固定MathMLと画像のハッシュを記録する。',
        '二式を共に定義導入として保持する。UはKの同じ点の二座標の同じ時刻における実微分の二乗和から得る非負の速さ、wはkの同じ点の二定速度成分の二乗和から得る非負の速さである。平方・加法・二つの等号・符号付き成分・零を保持し、Uとwやwと横成分を等置しない。',
        '点zkb、K/k、現在状況zb6と同じ長さ・時間尺度ta/rbを共有する。ejnyは現在の全両系履歴・実際の定速度・厳密な合成成分を接続する。ejohはその点の実際の座標関数eismhをその系の全期間と同じ時刻で微分する。ejojは同じ二定数zkc/zkdのk運動を使い、U/wの表記をejop/ejoqと値zkp/zkqへ結ぶ。',
        'Wir setzenに続く二式を、著者による二つの数量の命名・定義導入zbとして読む。方法側ejoi/ejojと値側ejok/ejolを区別し、同じ著者・第五節・提示文脈へ渡す。二式の順序とU/wの表記規則も保持する。定義を引用して述べたことから測定や微分の実行済みを要求しない。',
        '速さの非負性は明示した読みであり、二乗式だけなら負の枝も可能なことを隠さない。零の速さと負の成分を許し、点の光速上限を追加しない。先行の平面等速運動の全期間で同じ値を用い、任意の加速運動へ一般化しない。閉区間端では既存相対微分の片側の読みを許す。後続の角度の枝や零速度での角の存在をこの二式へ追加しない。',
        '数値ノルムsznと二微分の接続szqは既存の本体と意味を保ち、現在の座標規約・局所時計・物差し・世界線・全期間へ接続した。旧版の部分的な履歴に戻さず、原語の文字だけで速さや微分を代用しない。新しい表記個体はUとwの識別のためで、その数量としての役割は合成側に記述する。',
        '符号・零・非負ノルム、二つの導関数、実際の座標関数と同じ時刻・期間、物体・系・尺度・状況、全時刻に共有する二成分、表記と定義の全引数を検査した。全実数の微分・量化は有限評価を拒否する。以前の全履歴と変換の証拠もハッシュで保持する。検査通過を一般定理、物理的真理、意味同値の自動証明とはしない。',
        '導入のコロンから二式、次のundまでを通読した。U²の二微分とw²の二成分を、それぞれの同じ運動と表記に結び、二式の全関係と定義提示を、非負の速さという明示した解釈の下で欠落なく記述したと判断する。u0135全体とu0137–u0139の角度に関する部分には未処理項目があるため、この判断の範囲へ含めない。',
    )
    assert len(reasons)==len(REQUIREMENTS)
    paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,*PRIORS,*DEPENDENCIES,'scripts/review_velocity_magnitude_claim.py','tests/test_velocity_magnitude_claim_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT,*DEPENDENCIES):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    return dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[{k:m[k] for k in ('id','sha256')} for m in s['math']]),selection=selection_binding(catalog,indices),source_order_statements=indices,clauses=[dict(range=s['range'],text=s['text'],definitions=symbols,reason='同じ点のKの二座標の時間微分からU、kの二定速度成分からwを非負の速さとして得る二式を、同じ著者の定義導入と表記規則へ接続した。')],interpretation=LIMITS,limits=['明示した解釈の下でのアシスタントの通読判断であり、独立査読・全可能解釈の包含・意味同値の自動証明ではない。','u0135の全体、u0137以降、二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,reasons)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC]),reviewed_prose_characters=0,source_sha256=pins)


def prepare():
    from scripts.audit_opening_scope import write_exact
    write_exact(ROOT/REVIEW,json.dumps(record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    r=record();assert json.loads(read(REVIEW))==r
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY)
    validate_review(ROOT,REVIEW,'einstein-1905',active,load_catalog(ROOT,BASIS),json.loads(read(INVENTORY)))
    return dict(status='both_current_squared_speed_definitions_whole_unit_reviewed',document=FULL,source_units={r['unit']:0},reviewed_math_elements=2,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':1},semantic_equivalence_automatically_proved=False,source_sha256=r['source_sha256']|{REVIEW:digest((ROOT/REVIEW).read_bytes())})
