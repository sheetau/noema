"""Whole readings of the axial work argument and the printed energy chain."""
from functools import lru_cache
from pathlib import Path
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
ROOT=Path(__file__).resolve().parents[1]
def read(path):return (ROOT/path).read_text(encoding='utf-8')
FULL='examples/v014/einstein-electron-kinetic-work.noema';CORE='examples/v014/electron-kinetic-work-core.noema'
BASIS='data/electron-kinetic-work-basis-v1.json';ANNOTATIONS='data/electron-kinetic-work-identifiers-v1.json'
SOURCE='data/einstein-electron-kinetic-work-reading-v1.json';REPORT='reports/electron-kinetic-work-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';DOC='docs/electron-kinetic-work-v1.md'
REVIEWS=['data/einstein-electron-kinetic-work-u0261-review-v1.json','data/einstein-electron-kinetic-work-u0262-review-v1.json']
CLAUSES=(
 ('Wir bestimmen die kinetische Energie des Elektrons. ',['eiszy','eo6','eiszt','epi'],'著者が同じ電子の運動エネルギーをこれから決定すると告げる。答えを先取りせず、当該系の静止で零とする並進運動の寄与を候補とする。'),
 ('Bewegt sich ein Elektron vom Koordinatenursprung des Systems [M0422] aus mit der Anfangsgeschwindigkeit 0 beständig auf der [M0423]-Achse unter der Wirkung einer elektrostatischen Kraft [M0424] , ',['eor','eos','eot','eou','eo7','serw','ek3p','ejsn','eibs'],'同じ電子がKの原点で初速零から全区間X軸上を動くという条件。静的な電場Xと電子へのεXの電気的作用を同じ場・電荷・実履歴・校正単位に結ぶ。'),
 ('so ist klar, daß die dem elektrostatischen Felde entzogene Energie den Wert [M0425] hat. ',['epa','epp','eoy','sero','eiszu','eiszw','zdg','eisox','epi'],'その条件なら場から取り出すエネルギーが同じ0から終位置までの仕事積分で与えられることを著者が明らかと述べる。上下端は直前の過程から補う明示読解であり、印刷してあるとはしない。'),
 ('Da das Elektron langsam beschleunigt sein soll und infolgedessen keine Energie in Form von Strahlung abgeben möge, ',['eov','eow','eoz','epb','epc','eiszx','eiszv','ug','zc','epi'],'同じ座標時刻の実加速度が文脈の小ささの基準に収まる設定と、放射による損失を零とする設定を分ける。soll/mögeの採用とinfolgedessenの著者の理由付けを残す。緩い加速から厳密無放射を処理系の定理にしない。'),
 ('so muß die dem elektrostatischen Felde entzogene Energie gleich der Bewegungsenergie [M0426] des Elektrons gesetzt werden. ',['eox','eo2','eo3','epd','epe','epo','eiszt','eiszu','eisnw','serm','sern','zc','uh'],'同じ仕事単位と両端のエネルギーを共有し、静止時零・無放射・他の移転と内部変化を除いた簡略収支の下で、取り出しと終端運動エネルギーWを等置すべきという推論を述べる。初期零か無放射の片方だけでは等置しない。'),
 ('Man erhält daher, indem man beachtet, daß während des ganzen betrachteten Bewegungsvorganges die erste der Gleichungen (A) gilt:', ['eo4','sesf','sese','sesb','epf','epg','eph','epi','epj','epk','eiswm','zc'],'第一(A)が同じ全運動過程で成り立つという参照を、各時刻の実速度・実加速度・同じ場と電荷へ結ぶ。そのことと前の仕事・収支設定から、したがって直後の式を得るという著者の推論を提示する。印刷式の厳密導出を成功と認めず、前方参照と同じ著者への全文帰属を保つ。'),
)

@lru_cache(None)
def records():
    catalog=load_catalog(ROOT,BASIS);source=json.loads(read(SOURCE));basis=json.loads(read(BASIS))
    paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,'scripts/review_electron_kinetic_work.py','tests/test_electron_kinetic_work_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for path in (SOURCE,REPORT):
        e=json.loads(read(path));validate_hashes(ROOT,e['source_sha256']);merge_pins(pins,e['source_sha256'])
    output=[]
    for i,s in enumerate(source['units']):
        selection=[428] if i==0 else [429];offset=0;clauses=[]
        definitions=CLAUSES if i==0 else (('[M0427]',['eo5','eph','epl','epm','epn','eiszt','sero','serg','serc','serf','serd','sere','eisox','uh'],'W、同じεXの位置積分、質量係数を印刷していない0からvまでのβ³vの速度積分、μV²(β−1)の全四項を等置する同じ内容を著者の式として提示する。βは積分変数の関数であり、正の平方根に対応する正規化を保持する。'),)
        for text,symbols,reason in definitions:
            assert s['text'][offset:offset+len(text)]==text,offset
            assert all(n in catalog.entries for n in symbols)
            clauses.append(dict(range=[offset,offset+len(text)],text=text,statements=selection,definitions=symbols,reason=reason));offset+=len(text)
        assert offset==len(s['text'])
        reasons=(
         ('固定u0261の四文全体を原刊919–920頁と照合した。M0422=K、M0423=軸のX、M0424=静電的なX、M0425=∫εXdx、M0426=Wを保持する。' if i==0 else '固定u0262のM0427全体を原刊920頁と照合した。Wから始まる三つの等号、位置積分、下端0・上端vの速度積分、βの三乗、μVの二乗と正の根号を含む最右辺を保持する。'),
         '各句の関係はclausesに記した。実履歴、原点、初速零、全区間軸上、静的電場と作用、各時刻の実微分、程度基準、エネルギーの同じ帰属、仕事積分、設定と収支・等置、第一(A)と直後の積分列を合成した。端点だけで全区間を認定しない。',
         '同じ電子eisxh、K、開始zrgstartと終端eisxv、同じ曲線、電荷・低速質量・場・仕事単位を共有する。各時刻のβと最終vを区別する。旧草案のzramatterやzb7を無条件に現正本へ流用しない。Xという軸記号と電場成分、Wという数値の呼称と数式表示の個体を取り違えない。',
         ('第一文の決定の取組をeiszy、第二文の条件と自明性をepa/zdg、第三文の採用をug・理由と等置をzc/uh、Wの呼称をeisnwで保持する。第四文の全過程の第一(A)へのeiswmと、したがって直後のephを得るというzc、本文順序・同じ著者へのeir3を結ぶ。' if i==0 else '同じephをeisoxとuhで印刷された数式表示として提示し、u0261末尾のしたがって・第一(A)の参照に続ける。引用された等号列の数値的成立や導出成功を表示の実行条件に含めない。'),
         'langsamの閾値は創作せず、座標加速度についての文脈的な程度とする。soll/mögeは設定、infolgedessenは著者の理由であり物理定理ではない。静止で零の並進運動エネルギーと他の移転・内部変化を除く簡略収支を明示する。位置積分の暗黙の両端は直前の過程から読む。非負の終端速度を使う原文保存sergの読解を明示し、μを中間積分へ補わない。',
         '新たな基本関係は物理的エネルギーの三帰属、仕事単位、文脈的な程度基準、場の個体と成分モデルの対応、これから量を決定するという取組の提示である。対象・単位・時刻を引数にし、具体的な数式や因果・軌道・原文一文の真理を原始記号に隠さない。既存の物理的電気力eibsと校正・微分・積分・収支を合成する。',
         '局所検査は同じ単位尺度、静的電場の三成分、実有理関数履歴の微分、四つのエネルギー帰属、零初期量・零放射、印刷sergへの接続、引用と理由方向、全時刻量化と各作用記録の束縛を診断する。既存の固定した解析・電気力・軌道・収支・積分列の証拠を再利用する。全実時間と全分割を有限標本で証明せず、未知入力を拒否する。',
         ('u0261全文をu0260の物質点への拡張とu0262の積分表示の間へ戻して通読した。決定の導入、条件付きの自明な仕事、緩い加速と無放射の設定、等置、全過程での第一(A)、したがって次の式という全ての論述役割が揃うと判断する。' if i==0 else 'u0262の全四項を直前の仕事・収支設定・第一(A)からの推論と、後続の光速境界の段落の間へ戻して通読した。印刷されたμの欠落を保存したまま、同じ電子・場・単位・過程の式として全体を記述できたと判断する。')+'明示した読みの下でのアシスタント判断であり、独立査読、物理的真理又は同義性の自動証明ではない。',
        )
        assert len(reasons)==len(REQUIREMENTS)
        output.append(dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[{k:m[k] for k in ('id','sha256')} for m in s['math']]),selection=selection_binding(catalog,selection),source_order_statements=selection,clauses=clauses,interpretation=basis['limitations'],limits=['明示した解釈の下でのアシスタントによる全文判断。独立査読、物理的真理又は同義性の自動証明ではない。','中間積分のμ欠落は原文のまま保持する。後続u0263以降の光速境界・実験的関係は含めない。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,reasons)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT],semantic_reading=[DOC]),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins))
    return output

def prepare():
    from scripts.audit_opening_scope import write_exact
    for path,r in zip(REVIEWS,records()):write_exact(ROOT/path,json.dumps(r,ensure_ascii=False,indent=2)+'\n')
@lru_cache(None)
def build_report():
    rows=records();catalog=load_catalog(ROOT,BASIS);inventory=json.loads(read(INVENTORY));active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY)
    pins=dict(rows[0]['source_sha256'])
    for path,r in zip(REVIEWS,rows):
        assert json.loads(read(path))==r;validate_review(ROOT,path,'einstein-1905',active,catalog,inventory);pins[path]=digest((ROOT/path).read_bytes())
    return dict(status='axial_electric_work_argument_and_printed_chain_whole_units_reviewed',document=FULL,source_units={r['unit']:r['reviewed_prose_characters'] for r in rows},reviewed_math_elements=6,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':2},semantic_equivalence_automatically_proved=False,source_sha256=pins)
