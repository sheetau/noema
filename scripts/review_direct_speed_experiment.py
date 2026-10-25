"""Record the whole reading of experimental comparison and the oscillating-field example."""
from functools import lru_cache
from pathlib import Path
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
ROOT=Path(__file__).resolve().parents[1]
def read(path):return (ROOT/path).read_text(encoding='utf-8')
FULL='examples/v014/einstein-direct-speed-experiment.noema';CORE='examples/v014/direct-speed-experiment-core.noema'
BASIS='data/direct-speed-experiment-basis-v1.json';ANNOTATIONS='data/direct-speed-experiment-identifiers-v1.json'
SOURCE='data/einstein-direct-speed-experiment-reading-v1.json';REPORT='reports/direct-speed-experiment-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';DOC='docs/direct-speed-experiment-v1.md'
REVIEW='data/einstein-direct-speed-experiment-u0268-review-v1.json'
CLAUSES=(
 ('Diese Beziehung ist der Prüfung durch das Experiment zugänglich, ',['erc','eq4','ero','erp','erq','erw','eis37','eiswm','uh'],'直前の同じAm/Ae=v/Vを指し、校正された二つの偏向応答からの復元候補と、同じ電子・K・実速さの独立直接測定値を、同じ可能過程で比較できると述べる。一致又は理論の真理を比較の前提へ置かず、結果が偽でも比較操作として成立する。'),
 ('da die Geschwindigkeit des Elektrons auch direkt, ',['epr','erm','ern','ero','err','erx','eis36','eis3r','eis3s','eis3u','eisij','zc'],'同じ実履歴の三座標時刻微分の非負ノルムを同じ速度単位へ結び、校正・物理的信号取得・因果的な記録利用から直接の値を得る。方法と校正が検査対象の比を前提にしない独立性を保ち、auchで比による決定への追加、daで実験検査可能性への著者の理由を述べる。'),
 ('z. B. mittels rasch oszillierender elektrischer und magnetischer Felder, ',['ejsn','ers','ert','eru','erv','ery','ekc2','lf','eis4a','eis4b','eir5','eisa5'],'同じ装置が実際の電場と磁場の時間変化を信号取得に用いる一例を、直接測定へ挿入する。局所使用区間で二場成分を連続な非定数波形へ結び、両者の最小正周期と上下変動、測定配置の時間尺度に対して短い周期を要求する。単なる場の存在、静的な二場、任意の正弦名又は方法名だけでは代用しない。'),
 ('gemessen werden kann.',['ero','err','eru','erv','erx','ery','erz','er2','er3'],'同じ電子の同じ速さを、直接法とその振動場の例で測定できるという可能性を閉じる。実施済み・唯一の方法・全ての装置の成功とはせず、同じ著者・論説への帰属と直前の比の表示からの本文順序を保持する。'),
)

@lru_cache(None)
def record():
    catalog=load_catalog(ROOT,BASIS);source=json.loads(read(SOURCE));basis=json.loads(read(BASIS));s=source['units'][0]
    paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,'scripts/review_direct_speed_experiment.py','tests/test_direct_speed_experiment_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for path in (SOURCE,REPORT):
        e=json.loads(read(path));validate_hashes(ROOT,e['source_sha256']);merge_pins(pins,e['source_sha256'])
    selection=[434];offset=0;clauses=[]
    for text,symbols,reason in CLAUSES:
        assert s['text'][offset:offset+len(text)]==text,offset
        assert all(n in catalog.entries for n in symbols)
        clauses.append(dict(range=[offset,offset+len(text)],text=text,statements=selection,definitions=symbols,reason=reason));offset+=len(text)
    assert offset==len(s['text'])
    reasons=(
     '固定u0268全文を原刊920頁で、直前のAm/Ae=v/Vと次の番号2の間へ戻して照合した。Diese Beziehung、Prüfung durch das Experiment、zugänglich、da、同じElektronのGeschwindigkeit、auch direkt、z.B.、mittels、rasch、oszillierender、elektrischer und magnetischer Felder、gemessen werden kannを保持する。',
     '速さは校正された実軌道の三速度ノルムとして構成し、直接法の校正と取得をその量へ結ぶ。比による復元と独立直接値を同じ観測者が同じ可能過程で比較する。実験可能性、直接測定可能性、振動場の一例、著者による理由の提示を分け、比較結果の一致は要求しない。',
     '対象は同じ現在の電子、K、瞬間速さ、質量、電荷、長さ時間及び場の単位である。速度単位U T=Lと実ノルムを共有する。三測定が別の状況でも、取得記録は同じ観測者の一つの評価段階で利用できる。Diese Beziehungは直前の同じ比ercへ戻し、直接法がその比と同値な式を校正にも算出にも使わないことを要求する。',
     'uhで比較と直接法の可能性を著者主張として分け、zcでdaの理由、eisijでauchの追加を保持する。eir5とeisa5は振動場法の例示と挿入であり、唯一の方法への限定ではない。eir3とueで同じ著者・論説・直前表示からの順序を保持し、引用された実験の実行又は成功へ変換しない。',
     '理想的な量尺度での数値比較として読む。原文にない任意誤差区間の重なり、実験済み、理論支持又は普遍的な証明を足さない。振動は連続で非定数の周期的上下変動とし、標準配置の電場y成分・磁場z成分を一例の具体化に用いる。二場が同じ周波数・位相・振幅である条件、放射波・平面波、特定回路や飛行距離は補わない。速さの基準は測定配置の時間尺度に対する文脈的な比較として明示する。',
     '追加基本関係は、方法と校正の計算前提の独立性、二量を照合する実行操作、時間変化する物理場から同じ取得信号への結合、測定配置の時間尺度による比較基準である。速さの意味、単位換算、校正・信号取得・記録の因果共有、最小周期・連続性・上下変動、全使用時刻、可能性と提示は既存又は新しい合成定義に残す。全文を一つの原始記号へ圧縮しない。',
     '検査は量と単位、校正・取得・独立性・記録の同一性、真偽双方の比較、実二場の成分と使用区間、二つの周期と閾値、物理的結合、全存在位置、引用・理由・例示を対照する。周期波形の有限診断は現実の測定又は全実数の周期性の証明ではない。実数・関数の全域量化は有限評価を拒否し、旧証拠と既存定義を保持する。',
     'u0268全文を直前の偏向比による速度決定と次の実験的性質の列挙項の間で再読した。何をどの独立した量と比較するか、その可能性を支える直接法、時間変化する実二場による測定の一例と速さ、同じ対象・単位・記録・著者の理由と挿入が揃い、明示した理想測定と振動場の読みで全文を記述したと判断する。これはアシスタントの意味判断であり、独立査読、物理的真理又は同義性の自動証明ではない。',
    )
    assert len(reasons)==len(REQUIREMENTS)
    return dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[]),selection=selection_binding(catalog,selection),source_order_statements=selection,clauses=clauses,interpretation=basis['limitations'],limits=['明示した解釈の下でのアシスタントによる全文判断。独立査読、実験による理論検証又は原文同義性の自動証明ではない。','u0265の列挙導入とu0269以降の残りの性質は別途残る。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,reasons)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT],semantic_reading=[DOC]),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins)

def prepare():
    from scripts.audit_opening_scope import write_exact
    write_exact(ROOT/REVIEW,json.dumps(record(),ensure_ascii=False,indent=2)+'\n')
@lru_cache(None)
def build_report():
    r=record();catalog=load_catalog(ROOT,BASIS);inventory=json.loads(read(INVENTORY));active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY);pins=dict(r['source_sha256'])
    assert json.loads(read(REVIEW))==r;validate_review(ROOT,REVIEW,'einstein-1905',active,catalog,inventory);pins[REVIEW]=digest((ROOT/REVIEW).read_bytes())
    return dict(status='direct_speed_experiment_whole_unit_reviewed',document=FULL,source_units={r['unit']:r['reviewed_prose_characters']},reviewed_math_elements=0,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':1},semantic_equivalence_automatically_proved=False,source_sha256=pins)
