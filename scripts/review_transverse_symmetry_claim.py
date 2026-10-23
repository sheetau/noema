"""Whole reading of measured phi meaning, spatial symmetry and the signed rewrite."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_transverse_symmetry_claim import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,LIMITS
from scripts.check_transverse_symmetry_claim import DOC,SOURCE,INVENTORY,PRIOR,DEPENDENCIES,source_record

REPORT='reports/transverse-symmetry-claim-v1.json'
REVIEWS=tuple(f'data/einstein-transverse-symmetry-u{n:04d}-review-v1.json' for n in (101,102,103,104))
CLAUSES=(
 (
  ('Die Länge des Stabes, in [M0181] gemessen, ist also [M0182]; ',['ejdk','ejdl','ejc2','ejcz','ejdm'],'同じ棒をKで同時刻測定した正の距離がl/φ(v)であると、直前の両端式から結論する。'),
  ('damit ist die Bedeutung der Funktion [M0183] gegeben. ',['ejdm','zhf','spc'],'その同じ測定内容によって同じφの物理的意味が与えられると述べる。'),
  ('Aus Symmetriegründen ist nun einleuchtend, ',['ejdo','eisn2','zdg'],'この段階で、後続する同じ不変性を空間的対称性を理由に明らかだと提示する。'),
  ('daß die im ruhenden System gemessene Länge eines bestimmten Stabes, welcher senkrecht zu seiner Achse bewegt ist, ',['ejda','ejc5','ejc6','ejcz','ejdn'],'同じ特定の棒・固有形状を保ち、自軸へ垂直に動く棒の静止系での現在測定長を指す。'),
  ('nur von der Geschwindigkeit, nicht aber von der Richtung und dem Sinne der Bewegung abhängig sein kann. ',['ejdc','ejdd','ejde','ejdn'],'同じ速度の大きさなら長さが等しく、方向と向きへの依存がないという全比較範囲の主張。'),
  ('Es ändert sich also die im ruhenden System gemessene Länge des bewegten Stabes nicht, wenn [M0184] mit [M0185] vertauscht wird. ',['ejdf','ejdg','ejdh','ejdq','ejdr','ejds'],'同じ棒を同じKから見る二設定でvを−vへ交換しても、その測定長は変わらないと結論する。'),
  ('Hieraus folgt:',['ejdu','ejdi'],'その同じ二測定長の不変から次の二分数の等値が従うと提示する。'),
 ),
 (('[M0186]',['ejdi','srx','ejdr','ejdu'],'同じ正のlと同じφの正負値についてl/φ(v)=l/φ(−v)を提示し、コンマで後続の書換えへつなぐ。'),),
 (('oder',['ejdt','ejdv','zd3'],'同じ二設定の条件の下で二分数の等値をφの二値の等値へ同値に書き換える。'),),
 (('[M0187].',['ssk','ejdt','ejdv'],'同じφ(v)とφ(−v)が等しいという式と句点。φ=1とは区別する。'),),
)
REASONS=(
 (
  '固定u0101の全518文字・非空白本文405文字とM0181–M0185を原刊902頁へ照合した。Die Längeから四文目のHieraus folgtのコロンまで通読し、後続M0186へつながる範囲を確認した。',
  'Kで測った同じ棒の長さの帰結、同じ測定によるφの物理的意味、対称性を理由とする明白さ、特定の横棒の速度の大きさだけへの依存、方向・向きからの独立、正負交換での長さ不変と次の式への帰結を分けて構成した。',
  '棒zgu、二端zgv/zgw、固有長zgz、測定系ra、固有系zbm、速度zb7、同じ正規化後spcを前段と共有する。静止系という呼び方は測定するKを指し、動く棒をKへ静止させない。正負交換は同じK/kの別設定で、系の交換ではない。',
  'alsoとHieraus folgtは同じ著者の帰結zc、damitは同じ内容による物理解釈zhf、対称性の理由はeisn2、einleuchtendはzdg、一般不変性の採用はuhで保持する。nunはこの論述段階への移行であり物理時刻ではない。全て同じ著者・論説・第三節と本文順序へ結ぶ。',
  '正の測定距離と符号付き商l/φ(v)の一致が選ぶ向きの読みを明示し、端点代数だけから正値性が証明されたことにはしない。方向一般は非零光速未満の理想的比較設定群で保ち、加速・実験による全設定の現実化を加えない。候補を等長設定だけにせず、他の独立な条件を変えた場合まで無条件に同じ値とする読みへ広げない。',
  '測定長は現行記録と同時刻二端距離、同じ棒は全物質点と固有点対距離、速度は全系と全物質点の共通三成分、方向不変性は全適格設定・同速時の長さの等値へ合成する。新しいeisn2は具体的な棒・数式を埋め込まない汎用の空間的対称性による理由帰属である。',
  '原刊・固定本文・意味規約の通読に、固有形状の本体、異なる長さが候補に残ること、全方向の存在条件の例化、正負の現在記録、帰属・引用・書換えの対照を合わせる。全実数域の有限評価は拒否し、全物理的対称性の真理を検査成功から認定しない。',
  '測定長の第一文から対称性の第二文、正負交換の第三文、次の式を導く第四文まで再読した。正の同時刻距離、同じ固有形状の理想的比較群、対称性と結論の著者帰属という明示した読みの下で、関係・参照・範囲・提示を欠落なく保持したと判断する。',
 ),
 (
  '固定u0102のM0186を原刊902頁へ照合した。左右ともlを分子、同じφのv及び−vでの値を分母とする分数であり、保存MathMLの分数構造と末尾コンマを確認した。',
  '二つの商をsrxで別々に構成し、ejdiでその値の等値を述べる。左の正速度と右の負速度を区別し、測定長の候補名だけの等値や、lとφの積の等値へ替えない。',
  '左右のlは同じ棒の同じ正の固有長zgz、φは同じspc、引数は同じzb7とその符号反転である。実際の測定内容は前提ejdr/ejdp/ejdhで現在記録と二設定へ結ぶ。',
  'u0101末のHieraus folgtに続く著者の帰結であり、ejduが同じ二測定長の不変からejdiを提示する。コンマに続くoderと次のφの等値は後続の書換えとして保持する。',
  '非零φを保ち、商を絶対値へ変更しない。二分数が等しいだけで各φ=1や全対称性の実証を結論しない。一般距離と符号付き商の一致という読みは先行する測定条件に明示している。',
  '既存srxの正の分母φ²による商と実切断の値同値を用いる。左右の同じ関数の異なる引数を実際に適用し、この表示式専用の未説明の原始語へ置き換えない。',
  '原刊の分数線・引数・等号の確認と、正負の非零φについて商の等値を評価する対照を併記する。数値核の有限例は全実数体の機械的証明又は全文の意味判断の自動生成ではない。',
  '直前のHieraus folgt、左右の分数とコンマ、後続oderまで続けて再読した。同じ二測定から導かれる二商の等値という読みで、式と提示上の役割を欠落なく保持したと判断する。',
 ),
 (
  '固定u0103の全4文字oderを原刊902頁の二分数の等値とφの二値の等値の間で照合した。',
  '同じ二設定の条件の下で、二商の等値と二つのφの等値が同値であるejdtを構成し、ejdvが同じ内容の書換えとして提示する。片方向の含意や任意選択へ縮めない。',
  '書換え元はM0186のejdi、書換え先はM0187のssk、条件は同じ正のl・非零φ・現在二測定のejdpである。相反積や次のφ=1への書換えにしない。',
  '著者が同じ議論で別の等価な形を述べ直すというzd3と、その同値内容を採用するuhで保持する。新しい実験結果、排他的な二択又は二式の単なる列挙ではない。',
  '前提の非零φと正のlを落とさず、分母零の式を有効としない。二つのφが等しいことから1になるという後続の推論をこの語へ加えない。',
  '既存の条件・双条件の論理演算と、閉じた内容の書換え提示zd3を合成する。oder一語専用の原始意味は増やさない。',
  '原刊上の接続位置を通読し、双条件の真理表と非零係数での二式の本体評価、書換えの条件・元・先・著者・範囲の取り違えを検査した。',
  '二分数の等値からoder、次のφの等値まで再読した。同じ測定条件下の同値な述べ直しという役割を欠落なく保持したと判断する。',
 ),
 (
  '固定u0104のM0187と句点を原刊902頁へ照合した。左はφ(v)、右はφ(−v)で、同じ関数の二値を等号で結ぶ。',
  '同じspcの正負引数の有効な二値が等しいsskを述べる。値の積1、各値1、符号付き速度そのものの等値とは区別する。',
  'φは前の測定長の解釈と同じ正規化後関数であり、vは同じzb7である。正負設定のK/k・棒・尺度を保持し、逆向きだけ別の関数を使わない。',
  '直前のoderによる同値書換えの到着内容として、同じ著者・論説へejdv/ejd7で帰属する。句点でこの書換えを閉じ、次の相反積との合成は別の文に残す。',
  '純粋な二値の一致は非単位値でも成立することを保持する。測定側の正値条件と純粋数式の適用範囲を混同せず、この式だけでφ=1が証明されたとしない。',
  '既存sskの実切断による二値等値を意味規約ごと再利用し、現在二設定と二分数の等値への接続だけを新しく合成する。',
  '原刊式・句点の通読に、異なる非零値、同じ非単位値、負の同値を含む数値核と、二分数からの条件付き同値の検査を併記する。全実数・全物理状況の真理の認定とは区別する。',
  'oderから同じφの二値の等号と句点まで再読した。同じ正負速度の二測定に基づく同値な書換えという読みの下で、式・参照・提示を欠落なく保持したと判断する。',
 ),
)

@lru_cache(None)
def records():
    catalog=load_catalog(ROOT,BASIS);paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,PRIOR,*DEPENDENCIES,'scripts/review_transverse_symmetry_claim.py','tests/test_transverse_symmetry_claim_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT,*DEPENDENCIES):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    out=[];selections=([318,319,320,321],[321],[322],[322])
    for i,s in enumerate(source_record()['segments']):
        clauses=[];offset=0
        for text,symbols,reason in CLAUSES[i]:
            assert s['text'][offset:offset+len(text)]==text and all(n in catalog.entries for n in symbols)
            clauses.append(dict(range=[offset,offset+len(text)],text=text,definitions=symbols,reason=reason));offset+=len(text)
        assert offset==len(s['text']) and len(REASONS[i])==len(REQUIREMENTS)
        selection=selections[i]
        out.append(dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[{k:m[k] for k in ('id','sha256')} for m in s['math']]),selection=selection_binding(catalog,selection),source_order_statements=selection,clauses=clauses,interpretation=LIMITS,limits=['正の同時刻距離と符号付き商の一致、同じ固有形状の理想的全方向比較群、対称性と推論の著者帰属という明示した読みの下でのアシスタントの通読判断。独立査読、全物理的導出、意味同値の自動証明ではない。','u0105以降と二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS[i])],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC]),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins))
    return out

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,r in zip(REVIEWS,records()):write_exact(ROOT/p,json.dumps(r,ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY);catalog=load_catalog(ROOT,BASIS);inv=json.loads(read(INVENTORY));pins={}
    for p,r in zip(REVIEWS,records()):
        assert json.loads(read(p))==r
        validate_review(ROOT,p,'einstein-1905',active,catalog,inv);merge_pins(pins,r['source_sha256']);pins[p]=digest((ROOT/p).read_bytes())
    return dict(status='measured_phi_meaning_and_symmetry_whole_units_reviewed',document=FULL,source_units={r['unit']:r['reviewed_prose_characters'] for r in records()},reviewed_math_elements=7,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':4},semantic_equivalence_automatically_proved=False,source_sha256=pins)
