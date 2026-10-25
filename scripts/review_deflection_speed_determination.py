"""Record complete readings of the deflection argument and ratio display."""
from functools import lru_cache
from pathlib import Path
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
ROOT=Path(__file__).resolve().parents[1]
def read(path):return (ROOT/path).read_text(encoding='utf-8')
FULL='examples/v014/einstein-deflection-speed-determination.noema';CORE='examples/v014/deflection-speed-determination-core.noema'
BASIS='data/deflection-speed-determination-basis-v1.json';ANNOTATIONS='data/deflection-speed-determination-identifiers-v1.json'
SOURCE='data/einstein-deflection-speed-determination-reading-v1.json';REPORT='reports/deflection-speed-determination-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';DOC='docs/deflection-speed-determination-v1.md'
REVIEWS=['data/einstein-deflection-speed-determination-u0266-review-v1.json','data/einstein-deflection-speed-determination-u0267-review-v1.json']
CLAUSES=(
 (
  ('1. ',['eislk','ere','eri'],'先行の実験的性質の列挙導入に対する第一項とし、同じ著者・論説へ帰属する。導入自体の全文判断とは区別する。'),
  ('Aus der zweiten Gleichung des Systems (A) folgt, daß ',['elk','era','eis3v','eiswm','zc','ere'],'同じ三式(A)の第二行を、同じ電子・単位・系の横成分として取り出し、後続の偏向条件への著者の理由付けを述べる。式の引用を実行したことや処理系による導出としない。'),
  ('eine elektrische Kraft [M0430] und eine magnetische Kraft [M0431] dann gleich stark ablenkend wirken auf ein mit der Geschwindigkeit [M0432] bewegtes Elektron, wenn [M0433]. ',['eqh','eqz','eq6','erb','setk','seto','uh'],'Y,Nを先行の物理的な電場y成分・磁場z成分と読み、同じ電子・K・v・低速質量・電荷・校正単位の二試行で、VY=vNなら実横加速度の大きさが等しいと述べる。磁気側の符号を保持し、第三の両場試行の実行を余計な前提にしない。'),
  ('Man ersieht also, daß die Ermittelung der Geschwindigkeit des Elektrons aus dem Verhältnis der magnetischen Ablenkbarkeit [M0434] und der elektrischen Ablenkbarkeit [M0435] ',['eqs','eqt','equ','eqv','eqw','eqx','eqy','eq2','eq3','eq4','eq5','erc','erf','erg','ere'],'同じ電子への磁気・電気の局所横加速度を正の場成分で規格化したAm,Aeを名付ける。各量を校正装置で取得し、同じ観測者が因果的に共有する記録から規格化・Am/Ae・V倍を計算し、復元値が元の速度と一致するという決定を述べる。alsoは前の偏向条件からの論述上の帰結であり、現実の全員の認識ではない。'),
  ('nach unserer Theorie für beliebige Geschwindigkeiten möglich ist ',['eiscv','eisoe','eis3u','eq5','eq6','eq7','ere'],'同じ理論と基準電荷尺度を固定した0≤v<Vの全ての有効な速度について、一つの可能過程に属する測定・評価・正しい復元が存在するという著者の主張。測定済み標本又は低速近似への限定、別世界の記録の寄せ集め、現実で実施済みという追加主張を避ける。'),
  ('durch Anwendung des Gesetzes:',['eqx','eqy','eis3t','erc','ere','uf','ue'],'直後の同じAm/Ae=v/Vを適用し、V倍して速度を求める計算と、式表示への前方参照を保持する。比の等式だけで測定器の実現を自動証明したとはしない。'),
 ),
 (
  ('[M0436]',['eqh','eqz','eq2','eq6','erc','sets','erj','erk','erl','eisox','uh'],'同じ電子・K・速度・低速質量・電荷・単位の実二試行の規格化応答にAm/Ae=v/Vを適用する。正の分母Ae、非負Am、正のVと光速未満のv、比の入力順序を保持する。直前の第一項が適用すると述べた法則の表示と著者主張として提示する。'),
 ),
)

@lru_cache(None)
def records():
    catalog=load_catalog(ROOT,BASIS);source=json.loads(read(SOURCE));basis=json.loads(read(BASIS))
    paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,'scripts/review_deflection_speed_determination.py','tests/test_deflection_speed_determination_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for path in (SOURCE,REPORT):
        e=json.loads(read(path));validate_hashes(ROOT,e['source_sha256']);merge_pins(pins,e['source_sha256'])
    output=[]
    for i,s in enumerate(source['units']):
        selection=[432+i];offset=0;clauses=[]
        for text,symbols,reason in CLAUSES[i]:
            assert s['text'][offset:offset+len(text)]==text,offset
            assert all(n in catalog.entries for n in symbols)
            clauses.append(dict(range=[offset,offset+len(text)],text=text,statements=selection,definitions=symbols,reason=reason));offset+=len(text)
        assert offset==len(s['text'])
        reasons=(
         ('固定u0266の二文を原刊920頁に照合した。番号1、第二(A)、Y,N,v、Y=N·v/V、gleich stark、Man ersieht also、Am,Ae、nach unserer Theorie、beliebige、möglich、Anwendung、末尾コロンを保持する。' if i==0 else '固定u0267の式表示全体を原刊920頁の第一項二文と後続の実験検証可能性の間で確認した。M0436の分子Am、分母Ae、等号、v/V、末尾の句点を保持し、式は同じ著者の主張として置く。'),
         ('実場と同じ電子への実横加速度、第二(A)の適用、二つの偏向の同じ大きさを共有背景で合成する。決定可能性は、物理量を指定した校正・信号取得・記録利用・算術操作・正しい復元の存在を、全速度の内側へ置く。計算があることと復元成功を分ける。' if i==0 else '全ての適格な二試行の実横加速度を正のY,Nで規格化してAe,Amとし、Am/Ae=v/Vを同じ物理背景へ結ぶ。両辺は同じv,V、正のAeを使い、単なる無所属の四数の等式で済ませない。'),
         '同じ電子、K、瞬間速度、低速質量、符号付き電荷、長さ時間と場の単位尺度を共有する。測定は同じ対象・出来事・量・単位を指定し、同じ観測者へ記録を渡す。AmとAeは同じ物理応答の値の命名であり、先行三式(A)の第二式と直後の表示への参照を固定する。',
         ('第一項番号、先行(A)への照応、第二式からの帰結、そこからの決定可能性という著者の論述を分ける。uh/zcで主張と理由、eisnwで名称、uf/ueで前方参照と順序、eir3で同じ著者・論説への帰属を保持する。' if i==0 else 'ercは数式内容、eisoxはその表示、uhは同じ著者による主張、eir3とueは同じ論説への帰属と直前項からの本文順序である。式を定義しただけに留めず、引用した理論内容の真理を検査モデルに自動実行させない。'),
         'Ablenkbarkeitを標準配置の局所横加速度の大きさ/正の場成分と明示して読む。有限距離変位・曲率、電子への力と場を混同しない。任意速度は同じ理論の0≤v<Vで、零速度は理想局所応答として含む。装置の細目、全桁出力、現実の誤差零、第三試行の実施、u0268の独立直接測定を追加しない。',
         '五つの一般的な基本関係は、物理標準に対する校正、因果的な信号取得、指定算術の実行、同じ可能過程での記録保存、順序ある内容の部分指定である。量・対象・規格化・比・単位・全速度量化は合成側にある。一文全体を原始記号にせず、校正の任意関数化又は名前だけの測定で代用しない。',
         '局所検査は符号・零速度・除算順序・単位換算、四チャネルの校正と取得、記録の因果共有、計算の接続、成功との区別、存在束縛と全速度量化、提示役割を扱う。各束縛位置の二値診断は大域的存在の証明ではない。実数・関数の本来の全量化は有限評価を拒否し、既存物理定義と第二(A)の固定証拠を保持する。',
         ('u0266全文を列挙導入u0265・先行(A)・比の表示u0267・後続の直接測定u0268と合わせて再読した。二つの偏向が同じ強さになる条件と、その比を用いる全速度での決定、同じ理論・電子・量・記録・数値操作、命名・理由・前方参照が揃い、明示した測定と応答の読みで全文を記述したと判断する。' if i==0 else 'u0267全文を直前の速度決定の結論と、直後の直接測定による検証可能性の理由の間へ戻して再読した。磁気/電気の順序、同じv/V、物理応答・適用範囲・表示と著者主張を保持し、明示した読みで式全体を記述したと判断する。')+'これはアシスタントの意味判断であり、独立査読、物理的真理又は同義性の自動証明ではない。',
        )
        assert len(reasons)==len(REQUIREMENTS)
        output.append(dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[{k:m[k] for k in ('id','sha256')} for m in s['math']]),selection=selection_binding(catalog,selection),source_order_statements=selection,clauses=clauses,interpretation=basis['limitations'],limits=['明示した解釈の下でのアシスタントによる全文判断。独立査読、物理的真理又は原文同義性の自動証明ではない。','u0265の列挙導入とu0268の直接測定・振動場の例は別途残る。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,reasons)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT],semantic_reading=[DOC]),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins))
    return output

def prepare():
    from scripts.audit_opening_scope import write_exact
    for path,r in zip(REVIEWS,records()):write_exact(ROOT/path,json.dumps(r,ensure_ascii=False,indent=2)+'\n')
@lru_cache(None)
def build_report():
    rows=records();catalog=load_catalog(ROOT,BASIS);inventory=json.loads(read(INVENTORY));active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY);pins=dict(rows[0]['source_sha256'])
    for path,r in zip(REVIEWS,rows):
        assert json.loads(read(path))==r;validate_review(ROOT,path,'einstein-1905',active,catalog,inventory);pins[path]=digest((ROOT/path).read_bytes())
    return dict(status='deflection_speed_argument_and_ratio_whole_units_reviewed',document=FULL,source_units={r['unit']:r['reviewed_prose_characters'] for r in rows},reviewed_math_elements=7,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':2},semantic_equivalence_automatically_proved=False,source_sha256=pins)
