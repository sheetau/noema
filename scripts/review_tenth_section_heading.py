"""Record the complete final section heading under the stated physical reading."""
from functools import lru_cache
from pathlib import Path
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
ROOT=Path(__file__).resolve().parents[1]
def read(path):return (ROOT/path).read_text(encoding='utf-8')
FULL='examples/v014/einstein-tenth-section-heading.noema';CORE='examples/v014/tenth-section-heading-core.noema'
BASIS='data/tenth-section-heading-basis-v1.json';ANNOTATIONS='data/tenth-section-heading-identifiers-v1.json'
SOURCE='data/einstein-tenth-section-heading-reading-v1.json';REPORT='reports/tenth-section-heading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';DOC='docs/tenth-section-heading-v1.md'
REVIEW='data/einstein-tenth-section-heading-review-v1.json'
CLAUSES=(
 ('§ 10. ',['eisdv','eihq','eisxm','eisxg','eispb','evl'],'同じ第二部に直接属する深さ2、表示番号10の節見出し。箇所と節区分を分け、第九節の定理末尾から見出し、粒子設定の導入への順序を保つ。'),
 ('Dynamik des ',['eisth','evj','elm','evk','eisdw'],'物理的な粒子設定と、同じ対象の作用・慣性・運動変化を結ぶ法則の定式化を対象とする研究主題。法則の真理、実例の存在、導出や実測の完了を見出しから断言しない。'),
 ('(langsam beschleunigten) ',['ek3p','sepo','eiszx','evf','evg','evh','evi'],'括弧内の限定を同じ電子の同じ校正された履歴へ掛ける。全対象時刻の実三加速度の大きさが、全区間外で指定した正の文脈的基準より小さいという読み。速度の小ささ、各成分別の上限、無放射、x軸だけの運動へ替えない。'),
 ('Elektrons.',['eisxh','eisxi','ek34','evi','evj','evk'],'直後に仮定的に導入して以後Elektronと呼ぶ同じ点状荷電粒子。非零の符号付き電荷、低速慣性質量、場、実軌道と単位を既存規約へ結び、現代の固定負電荷や量子粒子種を補わない。'),
)
@lru_cache(None)
def record():
    catalog=load_catalog(ROOT,BASIS);s=json.loads(read(SOURCE));basis=json.loads(read(BASIS))
    paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,'scripts/review_tenth_section_heading.py','tests/test_tenth_section_heading_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for path in (SOURCE,REPORT):
        e=json.loads(read(path));validate_hashes(ROOT,e['source_sha256']);merge_pins(pins,e['source_sha256'])
    selection=[446];offset=0;clauses=[]
    for text,symbols,reason in CLAUSES:
        assert s['text'][offset:offset+len(text)]==text,offset
        assert all(n in catalog.entries for n in symbols)
        clauses.append(dict(range=[offset,offset+len(text)],text=text,statements=selection,definitions=symbols,reason=reason));offset+=len(text)
    assert offset==len(s['text'])
    reasons=(
      '原刊917頁で第九節の定理末尾と点状粒子の導入の間にある§ 10. Dynamik des (langsam beschleunigten) Elektrons.を視認した。番号、動力学の主題、括弧内の加速の限定、電子を一つの見出しとして再読し、四つの連続範囲へ対応させた。',
      '同じ粒子の物理設定と運動法則の定式化を、研究の主題として結ぶ。緩い加速は完全な非空履歴、同じ校正時刻、三座標の実二階微分、独立した正の程度基準、三成分の二乗和の厳しい上限へ合成する。',
      '見出しeisxm、節eisxg、第二部eispb、論説eirf、直前のeiswv、直後のeisxa、同じ電子eisxhとKを共有する。粒子の設定と括弧の加速を同じ軌道・時間領域・三速度関数・単位へ接続し、別の対象や時点を混ぜない。',
      '番号付き見出しによる区分と主題の案内として保持し、物理命題の断言や実験命令にしない。設定と検討する定式化は引用の中に置き、見出しの成立から引用内容の真理や現実の実例を実行しない。',
      'langsamは加速度の大きさの文脈的な小ささとして読み、低速、無放射、普遍的閾値又は軌道に都合のよい後付け上限としない。全区間・三次元の意味を保持し、直線や円、現在の現代的電子の電荷値を付加しない。',
      '物理的な粒子・場・質量・電荷・履歴・微分・程度基準・研究主題・見出し階層を既存定義から再利用する。新しい原始関係はなく、主題名や原語の綴り、全文専用の基本記号で意味を代用しない。',
      '三加速度の合成と境界・符号、実多項式の一階・二階微分、全時刻と各加速度、全設定の束縛、校正・同じ履歴・程度基準の必要性、引用の非実行、番号・階層・前後順序を対照する。有限の束縛診断を全関数域の検証にせず、既存証拠と旧446主張を保存する。',
      '前後の本文を含めて見出し全体を再読し、§10の区分、動力学の主題、同じ電子、括弧内の緩い加速の限定と提示役割が揃うと判断した。明示した解釈の下でのアシスタントの意味判断であり、独立査読・歴史的真理・原文同義性の自動証明ではない。二作品全体の最終完成監査は別に行う。',
    )
    assert len(reasons)==len(REQUIREMENTS)
    return dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[]),selection=selection_binding(catalog,selection),source_order_statements=selection,clauses=clauses,interpretation=basis['limitations'],limits=['明示した解釈の下でのアシスタントによる全文判断。独立査読、歴史的事実又は原文同義性の自動証明ではない。','二作品全体の最終完成監査は別に行う。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,reasons)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT],semantic_reading=[DOC]),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins)
def prepare():
    from scripts.audit_opening_scope import write_exact
    write_exact(ROOT/REVIEW,json.dumps(record(),ensure_ascii=False,indent=2)+'\n')
@lru_cache(None)
def build_report():
    r=record();catalog=load_catalog(ROOT,BASIS);inventory=json.loads(read(INVENTORY));active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY)
    assert json.loads(read(REVIEW))==r;validate_review(ROOT,REVIEW,'einstein-1905',active,catalog,inventory)
    pins=dict(r['source_sha256']);pins[REVIEW]=digest((ROOT/REVIEW).read_bytes())
    return dict(status='tenth_section_heading_whole_unit_reviewed',document=FULL,source_units={r['unit']:r['reviewed_prose_characters']},reviewed_math_elements=0,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':1},semantic_equivalence_automatically_proved=False,source_sha256=pins)
