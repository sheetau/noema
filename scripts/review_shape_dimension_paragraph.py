"""Whole reading of dimensional contraction, planar limit and physical caveat."""
from functools import lru_cache
import json,re
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_speed_boundary_forecast import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,LIMITS
from scripts.check_speed_boundary_forecast import DOC,SOURCE,INVENTORY,PRIOR,DEPENDENCIES

REPORT='reports/speed-boundary-forecast-v1.json'
REVIEW='data/einstein-shape-dimension-u0116-review-v1.json'
SOURCES=('data/einstein-directional-contraction-source-reading-v1.json','data/einstein-planar-shape-limit-source-reading-v1.json',SOURCE)
DOCS=('docs/directional-contraction-claim-v1.md','docs/planar-shape-limit-v1.md',DOC)
CLAUSES=(
 ('Während also die [M0201]- und [M0202]-Dimension der Kugel ',['ejgr','ejgu','ejg2','ejgz'],'先の球について、横二方向Y,Zの不変と次の縦方向の対照、先行結果からの帰結という提示を保持する。'),
 ('(also auch jedes starren Körpers von beliebiger Gestalt) ',['ejgp','ejgt','ejgm','ejg2'],'同じ剛体の全物質点を持つ任意形状へ一般化する。射影の有限幅を寸法と読み、穴や非連結部分を除かない。'),
 ('durch die Bewegung nicht modifiziert erscheinen, ',['ejgq','ejgr','ejgl'],'静止側とKの全対象時刻の実際の二横幅の存在と等しさを述べる。両系の同時刻面を等置せず、光学像にはしない。'),
 ('erscheint die [M0203]-Dimension im Verhältnis [M0204] verkürzt, ',['ejgs','ejgq','stw','ejgv'],'縦X幅は静止幅に√(1−(v/V)²)を掛けた値となる。比1対平方根の向き、正幅の厳密な縮小と零幅の保持を区別する。'),
 ('also um so stärker, je größer [M0205] ist. ',['ejgx','ejgy','ejg2','ejg4'],'同じ光速と正の元の幅について、許容速度vが大きいほど縮小後の幅が小さい。著者の帰結として提示し、加速履歴へ替えない。'),
 ('Für [M0206] schrumpfen alle bewegten Objekte ',['ejgp','ejhe','ejhf','ejhj'],'v=Vを同じ有限形状の光速未満からの極限と読む解釈を発話外に明示し、全適格物体に量化する。'),
 ('— vom „ruhenden“ System aus betrachtet — ',['ejgm','ejhd','ejhe'],'Kの全対象時刻の座標形状に接続する。前向き像と既存変換の逆代入の一致を光速未満で保持する。'),
 ('in flächenhafte Gebilde zusammen. ',['ejg5','ejg6','ejg7','ejha','ejhb','ejhc','ejhi'],'元形状の全点が一つの精度でVtの平面へ近づく。横射影の形を保持し、平面全体への充填や光速での有限βを補わない。'),
 ('Für Überlichtgeschwindigkeiten werden unsere Überlegungen sinnlos; ',['ejhk','ejhl','ejhm','eisof'],'同じ考察・同じ四式族の超光速への物理的適用が成立しないという留保。有限βの不存在だけでこの意味を代用しない。'),
 ('wir werden übrigens in den folgenden Betrachtungen finden, ',['ejhs','ejht','eisdb','eisog'],'同じ理論について後続の展開で明らかになるという補足的予告。現在の実証済み事実や前半からの論理的帰結へ替えない。'),
 ('daß die Lichtgeschwindigkeit in unserer Theorie physikalisch die Rolle der unendlich großen Geschwindigkeiten spielt.',['ejhn','ejho','ejhp','ejhq','ejhr','ejhv'],'物質的対象の物理的許容速度域における到達不能な上限Vと、全有限上限を超える比較速度の端に同じ役割を与える。同じ論説の理論、全許容状況と同じ全物質点を保持する。'),
)
REASONS=(
 '固定u0116全634文字を原刊903頁の三文へ照合し、M0201–M0206の軸、比の根号と二乗、速度、v=Vを再読した。第一文の括弧内の一般化、第二文の観測系の挿入、第三文の留保と補足的予告も対象に含む。',
 '同じ全物質点の任意形状と実際の幅から、横二不変、縦縮小、同じ元の幅の速度比較を構成した。第二文は全元位置の共通近傍での平面への接近と横射影を持つ。第三文は物理的適用不能と、理論が許す同じ物体の速度域の非到達の上限を別に構成する。',
 'K/k、同じ尺度、同じ光速Vと比較するv、同じ剛体と物質点、同じ考察・四式族・論説内の理論を保持する。理論についての一つの見解変数を留保と予告へ共有する。比較する速度族は同じ物体の加速履歴ではなく、静止形状・幅を固定した比較と許容状態の範囲である。',
 'Währendの対照、alsoの先行球と四式からの一般化と速度比較への帰結、著者への帰属と文順を保持する。第二文の下側極限の解釈注記を著者の発話と分ける。第三文のübrigensを補足として保持し、eisdbの後続への予告から現在の物理的真理や証明完了を導かない。',
 '寸法を有限射影幅、見え方を同時刻座標形状、v=Vを下側極限、無限大速度の物理的役割を物質的対象の到達不能な速度上限として読むことを明示する。任意形状を球や凸集合へ限定せず、光伝播を剛体の速度域へ入れず、無限大を実数値にしない。質量・エネルギー式や実施可能な加速装置を追加しない。',
 '既存の実切断、順序、平方根、全点の歴史、物質点の所属、形状射影と幅、引用・著者帰属・予告を再利用した。新しい物理的許容・適用・補足の関係は引数と否定の範囲を明示した一般関係であり、原文一文全体を名付けた原始述語ではない。上限と無限の端の共通役割は量化と近傍で合成する。',
 '既存の全形状・幅・速度比較・極限の検査に加え、同じ出来事の記録、φ=1、数式上と物理的な不成立の独立性、許容状況と全物質点の同一性、有限境界と無限の端、同じ理論と予告の引用を検査した。全実数量化は残し、有限対照・型検査と通読による判断を区別する。',
 '原刊の直前の回転楕円体と三半軸、u0116の全三文、直後の逆向きの観測についての文まで読み直した。明示した寸法・極限・物理的上限の読みの下で、量化、対照、程度、観測系、適用限界、同じ理論、予告という関係を欠落なく保持したと判断する。直後の逆向きの観測系への適用は別のu0117として残す。',
)

@lru_cache(None)
def record():
    catalog=load_catalog(ROOT,BASIS);inv=json.loads(read(INVENTORY));u=inv['units'][115];assert u['id']=='einstein-1905:u0116'
    paths={FULL,CORE,BASIS,ANNOTATIONS,*SOURCES,REPORT,INVENTORY,*DOCS,PRIOR,*DEPENDENCIES,'scripts/review_shape_dimension_paragraph.py','tests/test_shape_dimension_paragraph_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (*SOURCES,REPORT,*DEPENDENCIES):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    math=[]
    for p in SOURCES:
        for s in json.loads(read(p))['segments']:
            assert s['unit_sha256']==u['text_sha256'] and u['text'][s['range'][0]:s['range'][1]]==s['text']
            math.extend({k:m[k] for k in ('id','sha256')} for m in s['math'])
    assert [m['id'] for m in math]==[f'M{i:04d}' for i in range(201,207)]
    clauses=[];offset=0
    for text,symbols,reason in CLAUSES:
        assert u['text'][offset:offset+len(text)]==text and all(n in catalog.entries for n in symbols)
        clauses.append(dict(range=[offset,offset+len(text)],text=text,definitions=symbols,reason=reason));offset+=len(text)
    assert offset==len(u['text'])==634 and len(REASONS)==len(REQUIREMENTS)
    interpretations=[
      '第一文の寸法は同じ物体の占有形状の軸射影の有限幅。任意形状に球の内部充填や凸性を要求せず、静止側の基準時刻とKの全対象時刻の幅を比較する。',
      '第一文の比1:√(1−(v/V)²)は静止時対運動時。速度の程度比較は同じ光速と正の元の幅を固定し、加速履歴とはしない。',
      '第二文のv=Vは光速未満の形状族の下側極限として読む。横射影をVt平面へ置き、同じ有限形状の全元位置が各固定K時刻で一つの精度に共通して近づく。著者帰属とは別のejhjで解釈を注記する。',
      *LIMITS[1:],
    ]
    return dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=u['id'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=u['text_sha256'],text=u['text'],range=[0,len(u['text'])],math=math),selection=selection_binding(catalog,[332,333,334,335]),source_order_statements=[332,333,334,335],clauses=clauses,interpretation=interpretations,limits=['有限幅・同時刻の座標形状・下側極限・物質的対象の到達不能な上限という明示した読みの下でのアシスタントによる通読判断。全ての可能な解釈の包含、独立査読、一般の意味同値や物理的真理の自動証明ではない。','u0117以降と二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS)],evidence=dict(source_reading=list(SOURCES),formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=list(DOCS)),reviewed_prose_characters=len(re.sub(r'\s|\[M\d+\]','',u['text'])),source_sha256=pins)

def prepare():
    from scripts.audit_opening_scope import write_exact
    write_exact(ROOT/REVIEW,json.dumps(record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    r=record();assert json.loads(read(REVIEW))==r
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY)
    validate_review(ROOT,REVIEW,'einstein-1905',active,load_catalog(ROOT,BASIS),json.loads(read(INVENTORY)))
    return dict(status='shape_dimension_limit_and_caveat_whole_paragraph_reviewed',document=FULL,source_units={r['unit']:r['reviewed_prose_characters']},reviewed_math_elements=6,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':1},semantic_equivalence_automatically_proved=False,source_sha256=r['source_sha256']|{REVIEW:digest((ROOT/REVIEW).read_bytes())})
