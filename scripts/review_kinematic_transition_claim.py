"""Record the whole-unit reading of the kinematic summary and transition."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_kinematic_transition_claim import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,LIMITS
from scripts.check_kinematic_transition_claim import DOC,SOURCE,INVENTORY,PRIORS,DEPENDENCIES,source_record

REPORT='reports/kinematic-transition-claim-v1.json'
REVIEW='data/einstein-kinematic-transition-u0150-review-v1.json'
REASONS=(
 'u0150全文を原刊907頁で照合した。Wir haben nun、für uns notwendigen Sätze、unseren zwei Prinzipien entsprechenden Kinematik、hergeleitetと、und gehen dazu überからderen Anwendung in der Elektrodynamik zu zeigenまでを、一文の総括と移行として読んだ。前の群の記述と次の部見出しを混ぜない。',
 '前半ejr7は、現在の同じ課題に必要な非空の全命題が、同じ運動学体系に属し、同じ閉じた内容の論証を第一部で提示済みという総括である。後半ejsbは同じ必要命題群を前提に用いる電気力学の体系の構成例を示す目標であり、ejsdがその課題に移る提示を保持する。',
 'Wir/unsは同じ著者rd、必要性と移行は同じ課題zm7、総括の範囲は第一部znb、運動学体系はzncに固定する。二原理は現在のeion/eiotを参照する。derenは同じri段階の必要項目とeisoxの内容を引き継ぎ、目標の適用段階に別の必要項目や内容を選び直さない。',
 'uhによる導出済みの総括と、znhによる目標に取り組む課題開始を分ける。nunは第一部末の現在riと読み、完了した論証提示の段階と応用目標の評価段階を区別する。帰属eir3と順序ueにより、群の提示から総括、同じ文の移行へ続く論述を保持する。引用された内容や目標は帰属から実行しない。',
 '必要は次の応用課題に相対的な読み、対応するは同じ二原理を前提にした運動学という読み、応用は同じ命題群の共同利用という読みを明示した。体系全体との論理同値、全運動学定理の有限一覧、各命題に独立の一例、現在の目標達成、現在は一例もないという否定を補わない。',
 '運動学はeiscm/eihnから物体・位置・時刻・配置変化へ、電気力学はeig4/eie5から電荷輸送・電気作用・磁気作用へ接続する。eisoxによる閉じた内容、zfrによる論証提示、ztによる同じ内容の前提使用、zngによる体系の構成例の提示を合成した。旧zm6の未割当写像やznfの未説明な応用を使わず、新たな基本記号も加えない。',
 '非空の全必要項目、同じ内容・著者・課題・範囲・基準段階、現在の二原理と分野、同じ応用体系とその提示を局所対照で確認した。全閉記述の量化は有限評価器で拒否され、二記述の代入検査を一般の全域証明にしない。全必要命題の実際の導出・応用や著者の論証の健全性は、文の意味記述とは分ける。',
 '一文全体を通読し、必要命題の総括、二原理と運動学、同じ命題群の照応、電気力学への共同利用、現在の課題開始と将来に評価する目標まで確認した。明示した課題相対性・導出の基礎・共同利用という読みの下で、全体を欠落なく記述したと判断する。独立査読や意味同値の自動証明ではない。',
)


@lru_cache(None)
def record():
    catalog=load_catalog(ROOT,BASIS)
    paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,*PRIORS,*DEPENDENCIES,'scripts/review_kinematic_transition_claim.py','tests/test_kinematic_transition_claim_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT,*DEPENDENCIES):
        e=json.loads(read(p));validate_hashes(ROOT,e['source_sha256']);merge_pins(pins,e['source_sha256'])
    s=source_record()['segments'][0]
    symbols=['ejrz','ejr2','ejr3','ejr4','ejr5','ejr6','ejr7','ejsa','ejsb','ejsc','ejsd','ejsg','ejsh','eion','eiot','eihn','eie5','eisox','zfr','zna','zt','zng','znh']
    assert len(REASONS)==len(REQUIREMENTS) and all(n in catalog.entries for n in symbols)
    return dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[]),selection=selection_binding(catalog,[150,151]),source_order_statements=[150,151],clauses=[dict(range=s['range'],text=s['text'],definitions=symbols,reason=REASONS[1])],interpretation=LIMITS,limits=['課題相対的な必要性、二原理を導出の基礎にする運動学、必要命題群を前提にした電気力学の構成例の提示という明示した読みの下でのアシスタントの判断。独立査読・唯一の歴史的語義・意味同値の自動証明ではない。','全必要命題の実在する内容・論証提示・応用を処理系が実証したことにはしない。全閉記述の量化を有限代入で置き換えたのは検査用の診断だけで、正本は全域を保持する。','u0151以降と二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC]),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins)


def prepare():
    from scripts.audit_opening_scope import write_exact
    write_exact(ROOT/REVIEW,json.dumps(record(),ensure_ascii=False,indent=2)+'\n')


@lru_cache(None)
def build_report():
    r=record();assert json.loads(read(REVIEW))==r
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY)
    validate_review(ROOT,REVIEW,'einstein-1905',active,load_catalog(ROOT,BASIS),json.loads(read(INVENTORY)))
    pins=r['source_sha256']|{REVIEW:digest((ROOT/REVIEW).read_bytes())}
    return dict(status='kinematic_summary_and_collective_application_whole_unit_reviewed',document=FULL,source_units={r['unit']:r['reviewed_prose_characters']},reviewed_math_elements=0,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':1},all_prior_derivations_and_future_applications_empirically_verified=False,semantic_equivalence_automatically_proved=False,source_sha256=pins)
