"""Record a whole-unit reading of the introduction to the three properties."""
from functools import lru_cache
from pathlib import Path
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
ROOT=Path(__file__).resolve().parents[1]
def read(path):return (ROOT/path).read_text(encoding='utf-8')
FULL='examples/v014/einstein-experimental-list-opening.noema';CORE='examples/v014/experimental-list-opening-core.noema'
BASIS='data/experimental-list-opening-basis-v1.json';ANNOTATIONS='data/experimental-list-opening-identifiers-v1.json'
SOURCE='data/einstein-experimental-list-opening-reading-v1.json';REPORT='reports/experimental-list-opening-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';DOC='docs/experimental-list-opening-v1.md'
REVIEW='data/einstein-experimental-list-opening-review-v1.json'
CLAUSES=(
 ('Wir wollen nun ',['eum','eis6v','eur'],'同じ著者が現在の論述段階から列挙に移る意向・取組を表明する。一人称複数を共同著者にせず、既に完了した列挙や特定日時を補わない。'),
 ('die aus dem Gleichungssystem (A) resultierenden, ',['elk','euq','eup','eiswm','eis3v','zc'],'同じ先行(A)を第一の構成部分とする適用前提から、同じ三性質を得るという著者の帰結提示。各項の校正背景・初速零・無放射・閉収支・局所磁気設定を保持し、それらを(A)自体からの帰結としない。'),
 ('dem Experimente zugänglichen Eigenschaften der Bewegung des Elektrons ',['eun','esd','euo','eul','erw','euj','euk','et7','eua','euf','eug','uh'],'同じ電子の運動について後続する三項の全内容を参照する。各項の量の独立した測定・校正・取得と、同じ可能過程での記録共有・予測との比較を要求し、実験での一致や実施済みを補わない。'),
 ('aufzählen.',['eum','eislk','eur','eus','eut'],'既存の第一・第二・第三項と各内容を同じ順序で対応させ、同じ著者・論説に帰属する。物質点への拡張の後、第一項の前という本文の位置も保持する。'),
)

@lru_cache(None)
def record():
    catalog=load_catalog(ROOT,BASIS);s=json.loads(read(SOURCE));basis=json.loads(read(BASIS))
    paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,'scripts/review_experimental_list_opening.py','tests/test_experimental_list_opening_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for path in (SOURCE,REPORT):
        e=json.loads(read(path));validate_hashes(ROOT,e['source_sha256']);merge_pins(pins,e['source_sha256'])
    selection=[444];offset=0;clauses=[]
    for text,symbols,reason in CLAUSES:
        assert s['text'][offset:offset+len(text)]==text,offset
        assert all(n in catalog.entries for n in symbols)
        clauses.append(dict(range=[offset,offset+len(text)],text=text,statements=selection,definitions=symbols,reason=reason));offset+=len(text)
    assert offset==len(s['text'])
    reasons=(
      '原刊920頁を直前の物質点への拡張と直後の番号1を含めて確認した。Wir wollen nun、同じ(A)からの帰結、実験へのアクセス、同じ電子の運動の性質、列挙する取組までを一文として再読し、原文全文を四つの連続範囲に対応させた。',
      '列挙の取組は一般的な非空・同長の項目列と内容列へ合成する。第一項の偏向条件・比・任意許容速度の決定、第二項の実電位区間と速度式、第三項の加速度等号列・半径式・条件付き書換えを既存の全内容から参照する。',
      '著者rd、論説eirf、導入eis3w、既存三項eis3x/eis4q/eis4u、同じ(A)のeisym/elkを結ぶ。各項の電子・K・理論・単位・時点・適用条件と測定記録を保存し、別の対象や別の電位過程の値を混ぜない。',
      '現在からの列挙への移行、項目の順序と内容との対応、(A)への照応、適用前提からの帰結という著者の提示、全三項の実験可能性の主張を分けて合わせる。引用内容を実行して数学的成功や物理的真理を補わない。',
      'Wirは同じ著者、wollenは論述上の意向・取組、nunは現在の段階への移行として読む。実験へのアクセスは独立した測定と比較の可能性であり、個別の歴史的装置・実施済み・支持や一致を要求しない。各項の明示した物理条件を適用範囲として保持する。',
      '数式・物理量・校正・取得・独立性・記録共有・比較は既存関係を再利用する。追加した列挙の意向は任意の項数と内容を引数にする一般的関係であり、三つの物理式やこの全文を一基本記号へ隠さない。未知入力の拒否を保持する。',
      '局所検査で全三内容と適用条件の欠落、項目と内容の順序、著者・論説・根拠の取り違え、引用の非実行を区別する。測定依存群は公式を測定前提へ入れず、一致と不一致、実幾何量と予測量、全束縛位置を区別する。検査成功とは別に全文の意味を判断する。',
      '全文と前後を再読し、列挙への移行、三性質の全内容、(A)からの帰結の提示、各項への実験的アクセス、照応と順序が揃うと判断した。明示した解釈の下でのアシスタントの意味判断であり、独立査読・歴史的真理・同義性の自動証明ではない。',
    )
    assert len(reasons)==len(REQUIREMENTS)
    return dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[]),selection=selection_binding(catalog,selection),source_order_statements=selection,clauses=clauses,interpretation=basis['limitations'],limits=['明示した解釈の下でのアシスタントによる全文判断。独立査読、歴史的事実又は原文同義性の自動証明ではない。','u0239とu0275は別途判断する。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,reasons)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT],semantic_reading=[DOC]),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins)

def prepare():
    from scripts.audit_opening_scope import write_exact
    write_exact(ROOT/REVIEW,json.dumps(record(),ensure_ascii=False,indent=2)+'\n')
@lru_cache(None)
def build_report():
    r=record();catalog=load_catalog(ROOT,BASIS);inventory=json.loads(read(INVENTORY));active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY)
    assert json.loads(read(REVIEW))==r;validate_review(ROOT,REVIEW,'einstein-1905',active,catalog,inventory)
    pins=dict(r['source_sha256']);pins[REVIEW]=digest((ROOT/REVIEW).read_bytes())
    return dict(status='experimental_list_opening_whole_unit_reviewed',document=FULL,source_units={r['unit']:r['reviewed_prose_characters']},reviewed_math_elements=0,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':1},semantic_equivalence_automatically_proved=False,source_sha256=pins)
