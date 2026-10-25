"""Record the whole closing claim about a complete expression of motion laws."""
from functools import lru_cache
from pathlib import Path
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
ROOT=Path(__file__).resolve().parents[1]
def read(path):return (ROOT/path).read_text(encoding='utf-8')
FULL='examples/v014/einstein-complete-motion-expression.noema';CORE='examples/v014/complete-motion-expression-core.noema'
BASIS='data/complete-motion-expression-basis-v1.json';ANNOTATIONS='data/complete-motion-expression-identifiers-v1.json'
SOURCE='data/einstein-complete-motion-expression-reading-v1.json';REPORT='reports/complete-motion-expression-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';DOC='docs/complete-motion-expression-v1.md'
REVIEW='data/einstein-complete-motion-expression-review-v1.json'
CLAUSES=(
 ('Diese drei Beziehungen ',['eun','esd','euo','eup','euu','euv','euw','eux','euy','evb','eiswm','eis3v','evc'],'既存の三つの異なる項目と全内容へ戻す。第二・第三項は全物理設定を保った法則図式として参照し、現在の値への特殊化が元の全文内容と一致する。第一項も比だけに縮めず全速度の条件と決定可能性を保つ。'),
 ('sind ein vollständiger Ausdruck für die Gesetze, ',['euz','eu2','eu3','eu4','eu5','eu6','eu7','eva'],'同じ校正背景に属する全候補運動で、三関係を満たすことと理論が許すことの双方向の一致として読む。反例を含む範囲を成功例だけに縮めず、不足と過剰を区別する。法則を短い数値式や現在の一運動の一致へ替えない。'),
 ('nach denen sich gemäß vorliegender Theorie ',['eiscv','eigj','eisoe','eis6w','eva','uh','evc'],'同じ論説の同じ理論規約と比較基準を指定する。理論による許容は独立した入力として三関係と比較し、著者の完全性の主張を物理的真理又は処理系による証明にしない。'),
 ('das Elektron bewegen muß.',['eisxh','ra','eu7','euz','eu2','eva','evd','eve'],'同じ電子のKでの運動に対する理論内の制約としてmußを読む。実際の運動の発生、義務や因果的強制を追加しない。第三項の最終表示の後、既存の謝辞の前の同じ著者・論説の総括として結ぶ。'),
)
@lru_cache(None)
def record():
    catalog=load_catalog(ROOT,BASIS);s=json.loads(read(SOURCE));basis=json.loads(read(BASIS))
    paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,'scripts/review_complete_motion_expression.py','tests/test_complete_motion_expression_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for path in (SOURCE,REPORT):
        e=json.loads(read(path));validate_hashes(ROOT,e['source_sha256']);merge_pins(pins,e['source_sha256'])
    selection=[445];offset=0;clauses=[]
    for text,symbols,reason in CLAUSES:
        assert s['text'][offset:offset+len(text)]==text,offset
        assert all(n in catalog.entries for n in symbols)
        clauses.append(dict(range=[offset,offset+len(text)],text=text,statements=selection,definitions=symbols,reason=reason));offset+=len(text)
    assert offset==len(s['text'])
    reasons=(
      '原刊921頁で第三項の半径表示の後、謝辞の前にある一文を視認した。Diese drei Beziehungen、vollständiger Ausdruck、Gesetze、gemäß vorliegender Theorie、同じ電子のbewegen mußまでを全文として再読し、四つの連続範囲へ対応させた。',
      '第一項の全条件・比・任意速度の決定と、第二項の全電位・積分・速度式、第三項の全加速度等号列・半径表示・条件付き書換えを保持する。各適用条件に合う全事例へ第二・第三項を展開し、理論の許容との必要・十分両方向の一致を合成する。',
      '同じ著者rd、論説eirf、総括eis6j、三項eis3x/eis4q/eis4u、理論eis3k/eigj、電子eisxh、系raを結ぶ。場・軌道・出来事・量・単位・記録は各過程内で共有し、第二項と第三項の別の設定を無条件に一つへ混ぜない。',
      '既出三関係への後方参照、各内容と順序の対応、理論相対的な完全性の著者主張を区別して接続する。第三項の表示から総括、既存謝辞への順序を保ち、引用の提示から三式や完全性の真理を実行しない。',
      '完全な表現は固定した背景と明示した適用条件における全候補の双方向一致という読み。mußは理論内の制約であり、実測・真理・義務・因果的強制ではない。各式の不適用、接線加速度、全速度、電荷の符号を保持し、成功した場合だけの範囲や全軌道の円を追加しない。',
      '既存の物理量・実場・微分・積分・測定・理論規約・許容関係を再利用する。追加した候補範囲の関係は対象・系・背景・候補を明示する一般的規約であり、三式や完全性を一基本記号へ格納しない。完全性自体は量化と含意の二方向から定義し、未知の範囲や許容を補完しない。',
      '全称束縛の各位置を小さな区別可能領域で診断し、適用条件と結論の引数共有、現在の元の全文内容への厳密な特殊化、双方向一致の真偽表、二種類の反例、範囲拡大・空範囲・未知入力を検査する。旧物理検査の証拠と旧445主張の保存も照合し、有限診断を全領域の証明にしない。',
      '全文と直前の三項・直後の謝辞を合わせて再読し、参照・三という数・全内容・法則の作用範囲・双方向の完全性・同じ理論と電子・mußの役割が揃うと判断した。明示した解釈の下でのアシスタントの意味判断であり、独立査読・歴史的真理・原文同義性の自動証明ではない。',
    )
    assert len(reasons)==len(REQUIREMENTS)
    return dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[]),selection=selection_binding(catalog,selection),source_order_statements=selection,clauses=clauses,interpretation=basis['limitations'],limits=['明示した解釈の下でのアシスタントによる全文判断。独立査読、歴史的事実又は原文同義性の自動証明ではない。','u0239の節見出しと最終完成監査を残す。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,reasons)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT],semantic_reading=[DOC]),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins)
def prepare():
    from scripts.audit_opening_scope import write_exact
    write_exact(ROOT/REVIEW,json.dumps(record(),ensure_ascii=False,indent=2)+'\n')
@lru_cache(None)
def build_report():
    r=record();catalog=load_catalog(ROOT,BASIS);inventory=json.loads(read(INVENTORY));active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY)
    assert json.loads(read(REVIEW))==r;validate_review(ROOT,REVIEW,'einstein-1905',active,catalog,inventory)
    pins=dict(r['source_sha256']);pins[REVIEW]=digest((ROOT/REVIEW).read_bytes())
    return dict(status='complete_motion_expression_whole_unit_reviewed',document=FULL,source_units={r['unit']:r['reviewed_prose_characters']},reviewed_math_elements=0,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':1},semantic_equivalence_automatically_proved=False,source_sha256=pins)
