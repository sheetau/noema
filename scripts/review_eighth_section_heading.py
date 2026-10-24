"""Record the whole eighth heading under the explicit two-topic reading."""
from functools import lru_cache
from pathlib import Path
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
ROOT=Path(__file__).resolve().parents[1]
def read(path):return (ROOT/path).read_text(encoding='utf-8')
FULL='examples/v014/einstein-eighth-section-heading.noema';CORE='examples/v014/eighth-section-heading-core.noema'
BASIS='data/eighth-section-heading-basis-v1.json';ANNOTATIONS='data/eighth-section-heading-identifiers-v1.json'
SOURCE='data/einstein-eighth-section-heading-reading-v1.json';REPORT='reports/eighth-section-heading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';DOC='docs/eighth-section-heading-v1.md'
REVIEW='data/einstein-eighth-section-heading-u0202-review-v1.json'
REASONS=(
 'u0202全体103非空白文字を原刊913頁上端の見出しと照合した。§8、光線のエネルギーの変換、句点、完全鏡に及ぼされる放射圧の理論という二項を保持する。数式要素はなく、本文の密度説明へ進む前の一つの見出しである。',
 '第一項は同じ光の部分のK/kにおける二つの平均総エネルギーの対応ekw7を変換規則の主題ekxaへ結ぶ。第二項は完全鏡の同じ面部分に光が及ぼす法線力の平均圧力の設定ekugと検討する法則ekufを理論主題ekxbへ結ぶ。ekxcは両方を同じ研究で扱い、いずれかだけで見出しを代用しない。',
 'エネルギーの旧新値・旧新系・同じ部分・波・単位・文脈を一組の64証人で共有する。両系の同時断面と全領域の平均・積分は既存ekmiを保ち、密度、振幅、別の光の部分へ取り替えない。鏡側は同じ光の相互作用が同じ物質的面部分へ及ぼす力を使い、作用方向を逆転させない。',
 '第二部eispbの深さ2・番号8の既存区分eistkを案内するeihqの見出しとし、本文の物理法則を著者が真と断言するメッセージへ変換しない。前の第七節末尾、今回の見出し、次の密度説明の順序と箇所の区別を保持する。範囲はu0202–u0226、次の見出しu0227で閉じる。',
 'Theorieは第二項を導くと読み、第一項は値表現の変換規則と条件の主題として読む。光の平均総量と代表モデル、完全鏡の理想化は本文に採用済みの明示した読みを継承する。全ての光の形状を球面又は平面波に制限する断言、変換式や圧力式の真理・全域性・導出成功・実験実施を見出しから補わない。零エネルギーを比のために排除しない。',
 '源・波・部分・場・校正単位・平均・積分、鏡と反射の境界・損失・光の力・法線平均圧力は既存定義で説明する。新しい一般関係eisvvはeismrと同種の変換研究を実数値の対応へ型付けしたもので、特定の光や原文の一項全体を語義へ収納しない。eisthとeihqを再使用し、追加するもう一つの原始個体は見出し箇所への参照だけである。',
 '64束縛位置と公開された二値・二系・文脈を個別に診断し、同じ研究での二主題、設定と式の引用の区別、階層・番号・前後順序を対照する。全実数・全関数の有限評価は拒否し、下位の物理構成は固定した検査証拠を再利用する。既存407主張・意味規約・識別表記の保存も確認する。テスト通過を意味同義性の自動判定とはしない。',
 '原刊の見出しを、前節末尾及び続くエネルギー変換と鏡の放射圧の本文へ結んで読み直した。明示した平均総量と完全鏡の理想化の下で、二主題、変換、理論、作用を受ける対象、提示の役割、番号・階層・範囲を欠落なく記述したと判断する。引用された本文の物理理論の正しさを認定した判断ではない。',
)

@lru_cache(None)
def record():
    catalog=load_catalog(ROOT,BASIS);source=json.loads(read(SOURCE));s=source['segments'][0];basis=json.loads(read(BASIS))
    paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,'scripts/review_eighth_section_heading.py','tests/test_eighth_section_heading_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    assert len(REASONS)==len(REQUIREMENTS)
    return dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[]),selection=selection_binding(catalog,[407]),clauses=[dict(range=s['range'],text=s['text'],statements=[407],definitions=list(basis['definitions']),reason=REASONS[1])],interpretation=basis['limitations'],limits=['明示した読みの下でのアシスタントによる全単位判断であり、独立査読又は意味同義性の自動証明ではない。','見出しは研究主題を案内する。引用する設定の実在、原式の物理的正しさ又は理論の完成を認定しない。','第九節以降と二作品全体は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT],semantic_reading=[DOC]),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins)

def prepare():
    from scripts.audit_opening_scope import write_exact
    write_exact(ROOT/REVIEW,json.dumps(record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    r=record();assert json.loads(read(REVIEW))==r
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY)
    validate_review(ROOT,REVIEW,'einstein-1905',active,load_catalog(ROOT,BASIS),json.loads(read(INVENTORY)))
    return dict(status='eighth_section_heading_whole_unit_reviewed',document=FULL,source_units={r['unit']:r['reviewed_prose_characters']},whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':1},semantic_equivalence_automatically_proved=False,source_sha256=r['source_sha256']|{REVIEW:digest((ROOT/REVIEW).read_bytes())})
