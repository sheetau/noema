"""Record the complete reading of Einstein's ninth-section conformity conclusion."""
from functools import lru_cache
from pathlib import Path
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
ROOT=Path(__file__).resolve().parents[1]
def read(path):return (ROOT/path).read_text(encoding='utf-8')
FULL='examples/v014/einstein-convective-relativity-claim.noema';CORE='examples/v014/convective-relativity-claim-core.noema'
BASIS='data/convective-relativity-claim-basis-v1.json';ANNOTATIONS='data/convective-relativity-claim-identifiers-v1.json'
SOURCE='data/einstein-convective-relativity-reading-v1.json';REPORT='reports/convective-relativity-claim-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';DOC='docs/convective-relativity-claim-v1.md'
REVIEW='data/einstein-convective-relativity-u0237-review-v1.json'
CLAUSES=(
 ('Da — ',['ek2v','ek2t','ek2w','zc'],'新速度の同定を、直前の変換と併せて結論の理由とする。単なる同時成立へ替えない。'),
 ('wie aus dem Additionstheorem der Geschwindigkeiten (§ 5) folgt — ',['ek2s','ejnp','ejpc','eisoq','ek2v','eisov','zc'],'第五節の成分変換と同じ速度合成則を根拠として、同定が従うと述べる挿入。三成分と速さを同一視しない。'),
 ('der Vektor ([M0391]) nichts anderes ist als die Geschwindigkeit der elektrischen Massen ',['ek2j','ek2i','ek2h','ek2f','ek2g','ekzu','ekxl','ekxi','ekxh','seoc'],'直前の同じ三成分を同じ電荷分布の物質成員の実速度へ同定する。全成員・全対象記録の両方向対応と、単位付きの同じ履歴の実微分を保持する。'),
 ('im System [M0392] gemessen, ',['zbm','ek2i','eiscc','ekxl','ekzu','s6m'],'測る系は同じk。新座標時刻・単位・新逆像領域を使い、元の時刻や固有時、速度の大きさだけへ替えない。'),
 ('so ist damit gezeigt, daß ',['ek2t','ek2u','ek2w','zc','ui'],'同じ変換と同定から後続の条件付き適合が示されたという著者の結論と証明済みの位置付けを保つ。検証器の証明認定ではない。'),
 ('unter Zugrundelegung unserer kinematischen Prinzipien ',['ek2r','eifj','eify','ek2u','ug','uh','rd'],'同じ著者の二原理を基礎とする限定。原理の内容とその採用行為を区別し、原理の現実成立や読者全員の同意を加えない。'),
 ('die elektrodynamische Grundlage der Lorentzschen Theorie der Elektrodynamik bewegter Körper ',['ek2n','ekyv','eiswa','eisdi','eisv5','ekyo','ek2l','ekyq','eiswp','eiswm','ekyx'],'先行の同じLorentz理論が採る具体的な条件付き電気力学の基礎を指す。同じ内容を一法則へ結び、理論全体の未記述の全法則へ拡張しない。'),
 ('dem Relativitätsprinzip entspricht.',['ek2q','ek2p','ek2o','eiff','eife','eifd','sar','eifi','eisch','eifj'],'指定した同じ基礎法則が、原理の完全な共通法則体系に入るという読み。全適格系での法則成立、全候補履歴の全対応記述での適合保存、絶対静止に対応する特性の否定を保つ。'),
)

@lru_cache(None)
def records():
    catalog=load_catalog(ROOT,BASIS);s=json.loads(read(SOURCE));basis=json.loads(read(BASIS))
    paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,'scripts/review_convective_relativity_claim.py','tests/test_convective_relativity_claim_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    clauses=[];offset=0
    for text,symbols,reason in CLAUSES:
        assert s['text'][offset:offset+len(text)]==text,(offset,text)
        assert all(n in catalog.entries for n in symbols)
        clauses.append(dict(range=[offset,offset+len(text)],text=text,statements=[411],definitions=symbols,reason=reason));offset+=len(text)
    assert offset==len(s['text']) and s['unit']=='einstein-1905:u0237'
    reasons=(
      '固定u0237の全文とM0391/M0392を原刊917頁の先頭段落へ照合した。ドイツ語本文、MathML、原刊像をハッシュで固定し、直前の変換提示と後続の電荷不変の文を区別した。',
      '全新速度の物理的同定ek2j、第五節から従うという参照・推論、同定を理由とするDa ... so、直前の変換を含むdamit、示されたという位置付け、二原理を基礎とする条件、同じLorentz理論の基礎、相対性原理への適合を個別に構成して一文へ統合した。適合は同じ条件付き基礎法則を完全な共通法則体系へ含めるという明示した読みである。',
      '同じ電荷分布の物質・出来事と両系の単位付き記録を正逆座標写像で対応させ、新系kの実際の履歴の座標時刻微分へekzuを結ぶ。第五節は同じejnp/ejpc、原理は同じeifj/eify、Lorentz理論はeisv5、基礎の採用は同じekyo/ekyqである。一般化したek2lはKへ制限すると元の条件に一致する。基礎の法則個体は元の理論と共通体系で同じ個体に束縛する。',
      'eisovが先行の第五節を根拠として使う参照、zcが同定と適合への二つの導出提示、ugが著者自身の原理の採用、uhがその範囲の主張、uiが示されたという位置付けを保持する。eischは相対性原理の呼称を全内容へ固定し、eiswmは同じ先行基礎への照応、eir3は著者・論説への帰属、ueは先行五等式からの順序を保持する。引用を現実の真理へ脱引用しない。',
      '原理を基礎とする限定を条件付き内容と提示範囲の両方で保持する。共通体系はLorentz理論全体へ固定せず、この節の基礎法則を対象にする。全候補が法則適合するとは要求せず、不適合な候補の系間保存も扱う。旧印刷の磁気側1/V欠落、速度分母の符号と定義域を保存し、後続の電荷不変、流速の光速上限、全物体の共通静止系を補わない。',
      '実速度の意味は同じ物質・出来事・単位・履歴・座標時刻微分へ合成し、基礎法則は同じ物理的解釈条件と原系形の具体的方程式で与える。新一般関係eiswpは法則参照と条件付き内容との対応に限る。真理・適合・理論による採用は別々に合成し、相対性への文全体を原始関係に収納しない。共通体系の範囲と法則の成立・適合は既存の明示した規約を再利用する。',
      '同じ研究・法則・理論・文脈の結合、共通体系の完全性と両分野の非空性、全適格系での全法則の成立、全履歴の両側の記述存在と全対応対の適合保存を対照した。原理と結論の真偽を独立に変え、条件性を確認する。原始関係の未知入力を拒否し、引用内容が利用不能でも著者帰属を記述できる。有限標本は全連続体や原文同義性の自動証明ではない。',
      '原刊の一文を前の六式・五等式と先行Lorentz基礎へ戻して再読した。第五節の挿入、三成分の実速度への同定、kでの測定、Daとsoの向き、damitの参照、示されたという力、同じ著者の原理という限定、基礎と理論の区別、原理への適合を保持したと判断する。適合の意味は具体的な基礎法則を原理の完全な共通体系へ含める読解として明示した。著者の推論の数学的又は物理的な健全性を認定する判断ではない。',
    )
    assert len(reasons)==len(REQUIREMENTS)
    return [dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[{k:m[k] for k in ('id','sha256')} for m in s['math']]),selection=selection_binding(catalog,[411]),source_order_statements=[411],clauses=clauses,interpretation=basis['limitations'],limits=['明示した読みの下でのアシスタントによる全単位判断。独立査読や原文同義性の自動証明ではない。','著者の物理的結論と証明済みの提示を記述し、推論の一般的な健全性を認定しない。','二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,reasons)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT],semantic_reading=[DOC]),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins)]

def prepare():
    from scripts.audit_opening_scope import write_exact
    write_exact(ROOT/REVIEW,json.dumps(records()[0],ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    catalog=load_catalog(ROOT,BASIS);inventory=json.loads(read(INVENTORY));active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY)
    r=records()[0];assert json.loads(read(REVIEW))==r;validate_review(ROOT,REVIEW,'einstein-1905',active,catalog,inventory)
    pins=dict(r['source_sha256']);pins[REVIEW]=digest((ROOT/REVIEW).read_bytes())
    return dict(status='convective_relativity_whole_unit_reviewed',document=FULL,source_units={r['unit']:r['reviewed_prose_characters']},reviewed_math_elements=2,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':1},semantic_equivalence_automatically_proved=False,source_sha256=pins)
