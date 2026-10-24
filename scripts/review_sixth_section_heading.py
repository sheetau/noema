"""Record the complete sixth-section heading under an explicit local-action reading."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_sixth_section_heading import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,INDEX,LIMITS
from scripts.check_sixth_section_heading import DOC,SOURCE,INVENTORY,PRIOR,DEPENDENCIES,source_record

REPORT='reports/sixth-section-heading-v1.json'
REVIEW='data/einstein-sixth-section-u0152-review-v1.json'
REASONS=(
 'u0152の二文全体を固定転記と原刊907頁画像で照合した。§6、真空のMaxwell-Hertz方程式の変換、磁場中の運動で現れる起電力の性質という二つの主題を保持する。後段u0173–u0176は局所的な起電力の読みの文脈とし、今回の確認済み範囲へ加算しない。',
 'ejswは同じ第二部の深さ2・番号6の見出しとしてejsvを案内する。ejsvは同じ研究と文脈にejstとejsuを結ぶ。前者は真空・同じ物理的な二場と単位・六回転式・既出Vの規約ejsqと座標対応eiu2、後者は単位試験電荷への同じ局所磁気作用ejsrの非零な場合ejssを研究対象へ渡す。',
 '論説eirf、第二部eispb、前の部見出しeispc、光速度tcと速度単位tb、同じ出来事の二系での対応eiu2を既存本文へ固定する。呼称eispf、節eispg、箇所eisphを分け、節全体u0152–u0177を冒頭仮定znoと同一視しない。式の一般規約と続く具体的な場znl/znm・領域znkへの仮定適用も分ける。',
 '二つの主題を引用するeisdwと番号付き区分eisdvによる見出しの提示として読む。場の式を現実に成立済みとする断言、変換の証明、性質の研究結果へ置き換えない。原刊の改行や太字は画像に残し、見出しの物理的条件へ追加しない。',
 '真空は式の適用領域へ課す。単位試験電荷がある事例へ同時に物質不在を強制しない。磁石・導体・閉回路の存在を一般の起電力へ要求せず、平行運動や静止での零作用も比較対象として許す。この節の六式を現代の発散条件込みの全理論と同一視せず、旧表現の一次近似を厳密な系間の力変換へ昇格しない。',
 '真空・場・単位・運動・局所駆動はejsp/eiscc/eico/eidz/eisarの合成へ分解し、力の記録、場の局所評価、同じ担体の実際の座標時刻速度と軌跡へ結ぶ。新しい二関係は閉じた内容規約を受け取る研究主題の役割だけを担い、物理内容を原語名のみに隠さない。三参照個体にも呼称・区分・箇所の規約を与える。',
 '全引数の結合、光速度と速度単位、正の単位電荷、局所駆動三成分、静止・平行運動、二主題と同一研究への接続、見出し階層・番号・順序を対照した。全実数領域・全軌跡の有限列挙は拒否し、検査での境界代入を正本へ持ち込まない。旧357主張と既存判断の依存内容も保持した。',
 '見出し全体を直前の部見出し・直後の仮定・後段の起電力の説明とともに再読した。真空の場の式の変換と、磁場中の運動による局所的な起電力の性格を扱う節題という明示した読みの下で、二主題・参照・範囲・提示の役割を欠落なく記述したと判断する。後段の一次近似・新表現・補助概念という結論はこの判断に含めない。',
)


@lru_cache(None)
def record():
    catalog=load_catalog(ROOT,BASIS)
    paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,PRIOR,*DEPENDENCIES,'scripts/review_sixth_section_heading.py','tests/test_sixth_section_heading_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT,*DEPENDENCIES):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    s=source_record()['segments'][0]
    symbols=['ejsw','eihq','eisdv','eisdw','ejsv','ejst','ejsu','ejsq','ejsp','eiscc','ejss','ejsr','eico','eidz','eisar','eiu2']
    assert len(REASONS)==len(REQUIREMENTS) and all(n in catalog.entries for n in symbols)
    return dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[]),selection=selection_binding(catalog,[INDEX]),source_order_statements=[INDEX],clauses=[dict(range=s['range'],text=s['text'],definitions=symbols,reason=REASONS[1])],interpretation=LIMITS,limits=['原文全体と提示の役割を照合したアシスタントによる判断。独立査読や意味同値の自動証明ではない。','起電力を局所的な単位試験電荷の作用として読む。見出しの引用対象を構成したことから本文の仮定、変換結果やその導出、起電力の性格についての結論を認定しない。','u0153以降と二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC]),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins)


def prepare():
    from scripts.audit_opening_scope import write_exact
    write_exact(ROOT/REVIEW,json.dumps(record(),ensure_ascii=False,indent=2)+'\n')


@lru_cache(None)
def build_report():
    r=record();assert json.loads(read(REVIEW))==r
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY)
    validate_review(ROOT,REVIEW,'einstein-1905',active,load_catalog(ROOT,BASIS),json.loads(read(INVENTORY)))
    pins=r['source_sha256']|{REVIEW:digest((ROOT/REVIEW).read_bytes())}
    return dict(status='sixth_section_heading_whole_unit_reviewed',document=FULL,source_units={r['unit']:r['reviewed_prose_characters']},reviewed_math_elements=0,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':1},semantic_equivalence_automatically_proved=False,source_sha256=pins)
