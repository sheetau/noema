"""Record the complete reading of the second experimental relation."""
from functools import lru_cache
from pathlib import Path
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
ROOT=Path(__file__).resolve().parents[1]
def read(path):return (ROOT/path).read_text(encoding='utf-8')
FULL='examples/v014/einstein-traversed-potential.noema';CORE='examples/v014/traversed-potential-core.noema'
BASIS='data/traversed-potential-basis-v1.json';ANNOTATIONS='data/traversed-potential-identifiers-v1.json'
SOURCE='data/einstein-traversed-potential-reading-v1.json';REPORT='reports/traversed-potential-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';DOC='docs/traversed-potential-v1.md'
REVIEWS=['data/einstein-traversed-potential-u0269-review-v1.json','data/einstein-traversed-potential-u0270-review-v1.json']
CLAUSES=(
 (
  ('2. ',['eislk','esf'],'同じ実験的性質の列挙の第二項として位置を明示する。列挙導入u0265の参照先は保持するが、その全文を今回完了したとはしない。'),
  ('Aus der Ableitung für die kinetische Energie des Elektrons folgt, ',['ep7','ese','eiswm','zc','esf'],'同じ電子について先行する初期静止・仕事・無放射・閉収支・第一(A)と最右辺の運動エネルギー表現へ照応し、仕事/電荷としての電位差から後の関係を導く著者の理由を示す。先行中間積分のμ欠落を補正しない。'),
  ('daß zwischen der durchlaufenen Potentialdifferenz und der erlangten Geschwindigkeit [M0437] des Elektrons ',['serw','eou','er4','er5','er6','er7','esa','esb','esc','esd'],'同じ原点・初速零からの電子の全実軌道、実静電場、非零符号付き電荷・低速質量・終端速度vを接続する。通過電位差は全経路を含む区間の電位関数から得る初期値−終端値で、同じ仕事/電荷と長さ時間・速度の単位へ校正する。別電子・任意数値・端点だけの電位へ替えない。'),
  ('die Beziehung gelten muß:',['esd','ese','esf','esg','esi','uh','zc','uf'],'その設定の下で表示の関係が成立すべきだという推論上の必要性を、著者の主張と理由からの帰結として保持し、コロンで次の表示へつなぐ。電子への規範的命令、実験済み又は処理系が証明した事実とはしない。'),
 ),
 (
  ('[M0438]',['er4','er6','er7','esa','esb','esc','esd','esh','esj','esk','esl','seuw','seut','seur','eisox','eisnw','uh'],'P＝∫X dx＝(μ/ε)V²{1/√(1−(v/V)²)−1}の全表示。Pの呼称と同じ通過電位差、実場の向き付き積分、同じμ・ε・V・獲得速度vの平方根を含む右辺を接続する。積分は直前の原点から同じ終位置までと読む。両等号、電荷の符号、非単位質量、光速未満の非負速度、Pの単位を保持し、著者・論説と第二項導入に結ぶ。'),
 ),
)

@lru_cache(None)
def records():
    catalog=load_catalog(ROOT,BASIS);source=json.loads(read(SOURCE));basis=json.loads(read(BASIS))
    paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,'scripts/review_traversed_potential.py','tests/test_traversed_potential_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for path in (SOURCE,REPORT):
        e=json.loads(read(path));validate_hashes(ROOT,e['source_sha256']);merge_pins(pins,e['source_sha256'])
    output=[]
    for i,s in enumerate(source['units']):
        selection=[435+i];offset=0;clauses=[]
        for text,symbols,reason in CLAUSES[i]:
            assert s['text'][offset:offset+len(text)]==text,offset
            assert all(n in catalog.entries for n in symbols)
            clauses.append(dict(range=[offset,offset+len(text)],text=text,statements=selection,definitions=symbols,reason=reason));offset+=len(text)
        assert offset==len(s['text'])
        reasons=(
         ('原刊920–921頁のu0269を改頁をまたいで照合した。2、Aus der Ableitung、für die kinetische Energie des Elektrons、folgt、zwischen、durchlaufenen Potentialdifferenz、erlangten Geschwindigkeit v des Elektrons、Beziehung、gelten mußとコロンを全て保持する。' if i==0 else '原刊921頁のu0270をMathML M0438と照合した。P、二つの等号、上下端が印刷されない∫X dx、μ/ε、V²、1/√(1−(v/V)²)−1と括弧を保持する。μは右辺に印刷されており、εの絶対値でも単位電荷でもない。'),
         '既存eouが校正された実軌道・物理的静電場・初期静止・非零電荷・低速質量を構成し、er4–er7が全通過区間の電位と同じ仕事/電荷へ結ぶ。seuwの全二点の電位差、seutの同じ場の仕事積分、esaの既存seur及び印刷右辺をesdで合成する。eseは同じ運動エネルギー導出の内容と仕事/電荷の対応を理由へまとめる。',
         '電子・K・場・過程・始終出来事・全軌道・終端速度v・ε・低速質量μ・Vを同じ固定束へ渡す。仕事、長さ時間、電荷、電位、速度の校正と正の尺度を共有し、Punit Qunit=Wunit及びUunit Tunit=Lunitを満たす。通過区間は原点と終位置だけでなく途中の全x位置を含み、別の場の数値や他の電子の電荷を流用しない。',
         'eislkで第二項、eiswmで同じ電子の運動エネルギー導出へ照応し、zcとuhでfolgtとmußの推論上の必要性を著者の理由と主張に分ける。ufでコロンから表示へ、eisoxとeisnwで全式表示とPの呼称へ接続する。eir3とueで著者・同じ論説・前項からの順序を保ち、引用した物理内容を提示の検査時に実行しない。',
         '前段の原点初速零の軸上静電加速、緩い加速・無放射・閉収支の理想化を継承する明示読解。Pは初期電位−終端電位、積分はその両端、電位の加法定数は自由で負電荷を許す。全軌道を含む閉区間上の電位として読み、三次元全空間の経路独立性・時間変動場・任意初速への普遍公式は補わない。印刷M0427のμ欠落をこの新しい表示で訂正しない。',
         '新基本関係eis4fは同じ物理的仕事と符号付き電荷による電位単位の校正だけを担う。実場、全域の電位、差と積分、仕事の線形性、同じ電子と獲得速度、単位尺度、平方根と非零条件、著者の理由・列挙・表示は既存及び新しい合成に分ける。一文又は式全体を未説明の原始記号へ置き換えない。',
         '数値検査は正負電荷・非単位質量・静止・誤った降下を扱い、右辺の平方根と逆数も実評価する。単位と過程の引数、内部点の実場、途中の軌道逸脱、既存の全多項式係数による電位検査、全実数量化拒否、引用の非実行を確認する。前の435主張と意味規約・判断選択を保持し、有限診断を全実数の解析又は物理的真理の証明に変換しない。',
         ('u0269を前項の直接速度測定と後の表示式の間へ戻して再読した。第二項、どの導出に基づき、どの電子が通過した電位差と獲得速度の関係が成立すべきかが、同じ実場・軌道・量・単位と著者の推論で揃った。' if i==0 else 'u0270を第二項の導入と第三項の曲率半径の間で再読した。Pの呼称、同じ場の向き付き積分、同じμ/ε・V・vの右辺、両等号、物理的量と単位及び著者の表示が揃った。')+'明示した解釈の下で全文を記述できたと判断する。アシスタントの意味判断であり、独立査読・物理的真理・同義性の自動証明ではない。',
        )
        assert len(reasons)==len(REQUIREMENTS)
        output.append(dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[{k:m[k] for k in ('id','sha256')} for m in s['math']]),selection=selection_binding(catalog,selection),source_order_statements=selection,clauses=clauses,interpretation=basis['limitations'],limits=['明示した解釈の下でのアシスタントによる全文判断。独立査読、物理的真理又は原文同義性の自動証明ではない。','u0265の列挙導入とu0271以降は別途残る。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,reasons)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT],semantic_reading=[DOC]),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins))
    return output

def prepare():
    from scripts.audit_opening_scope import write_exact
    for path,r in zip(REVIEWS,records()):write_exact(ROOT/path,json.dumps(r,ensure_ascii=False,indent=2)+'\n')
@lru_cache(None)
def build_report():
    rows=records();catalog=load_catalog(ROOT,BASIS);inventory=json.loads(read(INVENTORY));active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY);pins=dict(rows[0]['source_sha256'])
    for path,r in zip(REVIEWS,rows):
        assert json.loads(read(path))==r;validate_review(ROOT,path,'einstein-1905',active,catalog,inventory);pins[path]=digest((ROOT/path).read_bytes())
    return dict(status='traversed_potential_whole_units_reviewed',document=FULL,source_units={r['unit']:r['reviewed_prose_characters'] for r in rows},reviewed_math_elements=2,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':2},semantic_equivalence_automatically_proved=False,source_sha256=pins)
