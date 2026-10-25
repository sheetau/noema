"""Record the full reading of the material-point extension, independently of tests."""
from functools import lru_cache
from pathlib import Path
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
ROOT=Path(__file__).resolve().parents[1]
def read(path):return (ROOT/path).read_text(encoding='utf-8')
FULL='examples/v014/einstein-material-mass-claim.noema';CORE='examples/v014/material-mass-claim-core.noema'
BASIS='data/material-mass-claim-basis-v1.json';ANNOTATIONS='data/material-mass-claim-identifiers-v1.json'
SOURCE='data/einstein-material-mass-claim-reading-v1.json';REPORT='reports/material-mass-claim-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';DOC='docs/material-mass-claim-v1.md'
REVIEW='data/einstein-material-mass-claim-u0260-review-v1.json'
CLAUSES=(
 ('Wir bemerken, daß diese Resultate über die Masse auch für die ponderabeln materiellen Punkte gilt; ',['eoc','eoj','eok','eol','eom','eon','eoo','eiszn','eiszo','uh','eiswm','sepf','seph'],'著者が、先行二質量の結果を同じ規約で質量を持つ点状物体へ適用することを指摘する。正の低速慣性質量・単位・同じ履歴・共動系の力と元系の実加速度を接続し、最初から帯電又は中性という制限を置かない。'),
 ('denn ',['zc','eoo'],'後半の可能性を前半の適用拡張の理由として著者へ帰属する。電荷追加による質量の厳密不変や、数式の数学的証明を補わない。'),
 ('ein ponderabler materieller Punkt kann durch Zufügen einer beliebig kleinen elektrischen Ladung zu einem Elektron ',['eoc','eod','eoe','eof','eog','eoh','eoi','seqt','seqr','eirk','zrdpossible','zrdadded','sbw2'],'同じ物質点と電荷単位を固定して、任意の正の上限より絶対値が小さい非零の電荷を加える許容操作と可能な結果がある。元の電荷を含む加法的収支を保ち、結果は同じ点状荷電対象となる。実行済み、固定した小電荷、零への相殺、別物体への置換と区別する。'),
 ('(in unserem Sinne) ',['eoe','eisqc','eiszp','eoo'],'括弧内で、Elektronを同じ著者がu0240で採った点状荷電対象という意味に限定する。現代の特定の粒子種へ変わることや、新しい物体の生成へ替えない。'),
 ('gemacht werden.', ['eof','eog','eoh','eoi','eoo','eop','eoq'],'前述の付加によって同じ物質点がその分類を満たす可能性として文を閉じる。同じ著者・論説への全文帰属と、前段u0259からの本文順を保持する。'),
)

@lru_cache(None)
def record():
    catalog=load_catalog(ROOT,BASIS);s=json.loads(read(SOURCE));basis=json.loads(read(BASIS))
    paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,'scripts/review_material_mass_claim.py','tests/test_material_mass_claim_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for path in (SOURCE,REPORT):
        e=json.loads(read(path));validate_hashes(ROOT,e['source_sha256']);merge_pins(pins,e['source_sha256'])
    offset=0;clauses=[]
    for text,symbols,reason in CLAUSES:
        assert s['text'][offset:offset+len(text)]==text,offset
        assert all(n in catalog.entries for n in symbols)
        clauses.append(dict(range=[offset,offset+len(text)],text=text,statements=[427],definitions=symbols,reason=reason));offset+=len(text)
    assert offset==len(s['text'])
    reasons=(
     '固定u0260全文を原刊919頁の比較上の注意の次の段落と照合した。Wir bemerken、diese Resultate、auch、ponderabeln、denn、kann、Zufügen、beliebig kleinen、Elektron、括弧内in unserem Sinneと受動表現の終わりをすべて含む。',
     '関係と作用範囲はclausesに列挙した。先行の質量結果への照応、質量を持つ点状物体への適用、正の低速慣性質量、同じ力・加速度・単位と二系履歴、任意の正の上限、上限ごとの操作と可能結果の存在、加法的電荷収支、著者の呼称の意味限定と理由付けを分けて合成した。',
     '元と結果は同じ物体・単位を共有し、元の電荷は零と決めない。結果の電荷を同じ物体の物理的記録と点状担体へ結ぶ。質量の適用は同じ物質点・出来事・元と共動の二系・長さ時間単位・低速質量・速度を共有する。速度方向と直交二方向の係数は先行と同じsepf/sephで、別の質量規約へ交換しない。',
     'eooは質量結果の適用をuhで指摘し、eiswmで先行二質量へ照応する。後半をuhで述べ、zcで可能性から適用拡張への理由方向を保持する。eiszpで括弧内の呼称の意味を先行命名へ結ぶ。eop/eoqは全文メッセージを同じ著者・論説へ帰属し、本文順序を保つ。引用された物理内容を提示時に実行しない。',
     'ponderableは正の低速慣性質量を持つ点状の力学的物体として読む。重量測定、現代粒子種、中性という前提、電荷追加後の質量の厳密不変を加えない。任意小は全正有理上限とし、上限に依存する可能な操作を許すが、固定小電荷や有限標本へ縮めない。力は共動系、加速度は元系という先行規約を維持する。',
     'eisznは位置と慣性を持つ物体の点状力学モデル、eiszoは有向の機械的作用の物理的帰属という一般的意味規約である。電荷は既存の加法的な符号付き物理量とsbw2の記録へ結び、電子の分類はその非零電荷と既存eisqcで構成する。原文一文全体の真理を新原始記号にせず、数式・量化・可能性・帰属を合成する。',
     '検査は二係数と静止境界、正の単位尺度、同じ履歴・実速度・共動時点、正負の小電荷と元の電荷、相殺・置換・不可能結果、引用と理由方向、各存在束縛を扱う。全実時間の微分や全有理上限を有限評価で認定しない。物理的な適用拡張の妥当性と、著者がその理由を述べる内容の意味判断を区別する。旧427主張と根拠を保存する。',
     'u0260全文を先行の質量・比較規約と後続の運動エネルギー導入の間へ戻して再読した。質量を持つ点状物体への拡張、同じ物体への任意小電荷の付加可能性、著者がいう電子という限定、理由と断定の役割が揃うため、明示した解釈の下で全文を記述できたと判断する。アシスタントの判断であり独立査読又は自動同義性証明ではない。後続u0261以降は含めない。',
    )
    assert len(reasons)==len(REQUIREMENTS)
    return dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[]),selection=selection_binding(catalog,[427]),source_order_statements=[427],clauses=clauses,interpretation=basis['limitations'],limits=['明示した読みの下でのアシスタントによる全文判断。独立査読、物理的真理又は原文同義性の自動証明ではない。','後続の運動エネルギー、放射の限定、実験的関係は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,reasons)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT],semantic_reading=[DOC]),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins)

def prepare():
    from scripts.audit_opening_scope import write_exact
    write_exact(ROOT/REVIEW,json.dumps(record(),ensure_ascii=False,indent=2)+'\n')
@lru_cache(None)
def build_report():
    r=record();assert json.loads(read(REVIEW))==r
    catalog=load_catalog(ROOT,BASIS);inventory=json.loads(read(INVENTORY));active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY)
    validate_review(ROOT,REVIEW,'einstein-1905',active,catalog,inventory)
    return dict(status='whole_material_mass_extension_and_charge_reason_reviewed',document=FULL,source_units={r['unit']:r['reviewed_prose_characters']},whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':1},semantic_equivalence_automatically_proved=False,source_sha256=r['source_sha256']|{REVIEW:digest((ROOT/REVIEW).read_bytes())})
