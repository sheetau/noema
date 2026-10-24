"""Record the complete reading of the short charge-constancy theorem note."""
from functools import lru_cache
from pathlib import Path
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
ROOT=Path(__file__).resolve().parents[1]
def read(path):return (ROOT/path).read_text(encoding='utf-8')
FULL='examples/v014/einstein-charge-constancy-claim.noema';CORE='examples/v014/charge-constancy-claim-core.noema'
BASIS='data/charge-constancy-claim-basis-v1.json';ANNOTATIONS='data/charge-constancy-claim-identifiers-v1.json'
SOURCE='data/einstein-charge-constancy-reading-v1.json';REPORT='reports/charge-constancy-claim-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';DOC='docs/charge-constancy-claim-v1.md'
REVIEW='data/einstein-charge-constancy-u0238-review-v1.json'
CLAUSES=(
 ('Es möge noch kurz bemerkt werden, daß ',['ek3i','eiswt','eisws','eiswu','eiswv'],'前文への追加を控えめな注記として提示し、その導入から定理末尾までを短い扱いとする。許可の取得済み、命令、内容の不確実性とはしない。'),
 ('aus den entwickelten Gleichungen ',['ek3e','ekzc','ekz7','ek2j','eiswm'],'先行の原系式と変換式を、直前に同定された新速度の意味で受け直す。同じ出発内容を容易な導出の前提へ結び、先行箇所への照応を保つ。'),
 ('leicht der folgende wichtige Satz gefolgert werden kann: ',['ek3f','ek3g','ek3h','s2y','zlw','zlx','zla','zlb','zlc','eiswr','ek3j','uf'],'同じ後続の定理を、利用可能な方法による非空有限の許容手順で容易に導けるとする。重要さは同じ定理の評価であり、容易さや真理とは別。コロンが予告した同じ定理へ接続する。'),
 ('Bewegt sich ein elektrisch geladener Körper beliebig im Raume ',['ek3d','ek3b','ek23','ek25','eiad','eiag'],'持続的な同じ全物質点の帯電物体の任意運動を全設定への量化で記述する。全体の剛性・等速・一様密度・全部分の固定電荷に狭めない。帯電は随伴側の正味総電荷が非零という明示した読み。'),
 ('und ändert sich hierbei seine Ladung nicht, ',['ek3c','ek24','ek22','eisvy'],'同じ全物体の実際の全量が、同じ随伴側区間の任意二時刻で等しいという前件。密度、代表点の電荷、端点だけの一致へ替えない。'),
 ('von einem mit dem Körper bewegten Koordinatensystem aus betrachtet, ',['ek26','ek27','ek3a','sb'],'同じ追跡点へ原点を付けた随伴系からの記述。完全な全物体履歴を保持し、全体の共通静止慣性系は要求しない。同じ追跡点の出来事で比較期間を両方向に対応させる。'),
 ('so bleibt seine Ladung auch — ',['ek3c','ek24','ek3d'],'前件の時間不変から、同じ全量のK側での時間不変を条件付きで述べる。auchは一定性をKにも加える。系間の数値電荷の等値を定理へ足さない。'),
 ('von dem „ruhenden“ System [M0393] aus betrachtet — ',['ek3j','eismz','eiseb','ra','ek23','ek27'],'M0393のKと先行の引用符付き静止系の呼称を同じraへ固定する。Kの時計・単位・同時切片で全体電荷を扱い、絶対静止を含めない。'),
 ('konstant.',['ek24','ek3c','ek3k','ek3l','ek3m','uh','eir3'],'同じK側の全区間における一定性を結論とし、導入と一続きの主張を同じ著者・論説へ帰属させる。著者が述べたことと検証器が証明したことを区別する。'),
)

@lru_cache(None)
def records():
    catalog=load_catalog(ROOT,BASIS);s=json.loads(read(SOURCE));basis=json.loads(read(BASIS))
    paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,'scripts/review_charge_constancy_claim.py','tests/test_charge_constancy_claim_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    clauses=[];offset=0
    for text,symbols,reason in CLAUSES:
        assert s['text'][offset:offset+len(text)]==text,(offset,text)
        assert all(n in catalog.entries for n in symbols)
        clauses.append(dict(range=[offset,offset+len(text)],text=text,statements=[412],definitions=symbols,reason=reason));offset+=len(text)
    assert offset==len(s['text']) and s['unit']=='einstein-1905:u0238'
    reasons=(
      '固定u0238の全文とM0393を原刊917頁の第九節末尾へ照合した。導入、コロン、条件付き定理、引用符と二つの挿入ダッシュ、K、末尾の一定性までを同じ一単位として固定した。後続の第十節見出しは含めない。',
      '同じ持続的物体の任意運動、帯電、随伴側の実際の全体電荷履歴と時間不変、K側の時間不変への条件をek3dへ合成した。その同じ定理への容易な導出可能性と重要性、簡潔な追加の注記という提示をek3eからek3mで統合する。任意運動を一つの定速Lorentz写像に狭めない。',
      '物体、全成員、分布、追跡点、固定単位、各系の全量履歴を同じ設定に束縛する。期間は同じ追跡点の出来事で双方向に対応させる。developed equationsの原系式ekzcと変換式ekz7を同じ新速度同定ek2jで受け直し、同じ出発内容から同じek3dへ至る手順を要求する。引用符付き静止系はeisebとra、著者はrd、論説はeirf、節はeisv6である。',
      'Es mögeの控えめな提示、nochの追加、kurzの扱いの短さ、leicht ... kannの容易な導出可能性、重要な同じ定理という評価、folgendeとコロンの前方参照を別々に表す。uhとeir3で同じ内容の著者の主張を記述し、方法の実行済みやuiによる証明完了へ替えない。auchは同じ一定性をK側にも加える条件の向きへ結ぶ。',
      '有限区間は任意の正長区間へ量化した過程の読みであり、一個の数値例や特定の運動へ限定しない。持続的な固定成員の物体と、同じ物体の追跡点へ原点を随伴する座標系を明示的に採る。原文にない原点規約を印字された事実とはせず、物質の生成消滅や開放系の成員変更を含むとは主張しない。この読みで加速・回転・変形・内部電荷移動を許し、共通静止慣性系、全部分の電荷一定、局所保存則、数値総電荷の系間等値を補わない。',
      '時間不変は全時刻対の同じ量の等値、全量は同じ物質部分に対する加法的な電気量の保有、随伴性は完全な履歴と同じ追跡点の原点への固定として構成済み。容易さは既存s2yの手順接続と同じ列の低負担で合成する。三つの新一般関係は内容の重要性、提示範囲の短さ、控えめな追加の注記に限り、物理定理そのものを原始関係へ収納しない。',
      '前段の全体電荷の履歴、欠落や余分な記録、同じ追跡点の双方向対応、任意設定の全束縛位置の検査を固定した証拠として引き継ぐ。新検査は非空手順列の接続、負担、利用可能性、同じ前提・結論・文脈、独立な重要性評価、短い範囲と本文参照を対照する。引用内容を実行できなくても提示は記述でき、未知入力は拒否する。有限診断は全連続体や原文同義性の自動証明ではない。',
      '原刊第九節の最後の一文を、直前の式・速度の同定・前の結論とともに再読した。簡潔な追加の注記として、展開済み方程式から容易に導ける重要な定理を予告し、任意運動する同じ帯電物体の随伴系での一定性をKでの一定性へ結ぶ全内容を保持したと判断する。随伴系・持続的物体・比較期間の規約は明示した読みとして扱う。原刊の磁気側1/V欠落は修正せず、著者の導出の一般的な健全性を認定する判断とはしない。',
    )
    assert len(reasons)==len(REQUIREMENTS)
    return [dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[{k:m[k] for k in ('id','sha256')} for m in s['math']]),selection=selection_binding(catalog,[412]),source_order_statements=[412],clauses=clauses,interpretation=basis['limitations'],limits=['明示した読みの下でのアシスタントによる全単位判断。独立査読や原文同義性の自動証明ではない。','持続的な同じ物体・同じ追跡点に随伴する系・対応する任意の正長有限期間という解釈を採用した。物理的結論の一般的な証明ではない。','二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,reasons)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT],semantic_reading=[DOC]),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins)]

def prepare():
    from scripts.audit_opening_scope import write_exact
    write_exact(ROOT/REVIEW,json.dumps(records()[0],ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    catalog=load_catalog(ROOT,BASIS);inventory=json.loads(read(INVENTORY));active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY)
    r=records()[0];assert json.loads(read(REVIEW))==r;validate_review(ROOT,REVIEW,'einstein-1905',active,catalog,inventory)
    pins=dict(r['source_sha256']);pins[REVIEW]=digest((ROOT/REVIEW).read_bytes())
    return dict(status='charge_constancy_whole_unit_reviewed',document=FULL,source_units={r['unit']:r['reviewed_prose_characters']},reviewed_math_elements=1,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':1},semantic_equivalence_automatically_proved=False,source_sha256=pins)
