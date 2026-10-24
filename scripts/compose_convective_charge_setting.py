"""Connect regional signed charge, material velocity and the source curl laws."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_limits import ROOT,R,v,call as k,app,op,both,quant as q,lam
from scripts.compose_material_relative_frame import define
from scripts.compose_field_equations import POINT,REGION,FIELD,JET,TAU,ROLES
from scripts.compose_local_density import BALL,PROFILE
from scripts.compose_additive_charge import DOMAIN as SETS,TOTAL
from scripts.compose_material_velocity import DOMAIN,CURVE
from scripts.compose_vacuum_field_domain import FIELDS as FIELD_SETTING
from scripts.compose_doppler_infinity import quantified

def read(path):return (ROOT/path).read_text(encoding='utf-8')
PARENT='examples/v014/einstein-eighth-section-heading.noema';PARENT_BASIS='data/eighth-section-heading-basis-v1.json'
FULL='examples/v014/einstein-convective-charge-setting.noema';CORE='examples/v014/convective-charge-setting-core.noema'
BASIS='data/convective-charge-setting-basis-v1.json';ANNOTATIONS='data/convective-charge-setting-identifiers-v1.json'
CHART=[('frame','a'),('lengthunit','a'),('timeunit','a'),('context','d')]
AMOUNT=[('distribution','a'),('kind','a'),('frame','a'),('event','a'),('time',R),('region',BALL),('lengthunit','a'),('timeunit','a'),('quantityunit','a'),('amount',R),('context','d')]
REGIONAL_TOTAL=[('distribution','a'),('frame','a'),('event','a'),('point',POINT),('context','d'),('lengthunit','a'),('timeunit','a'),('chargeunit','a'),('sets',SETS),('total',TOTAL)]
PROFILES=[('pi',R),('upper',R),('charge',PROFILE),('volume',PROFILE),('average',PROFILE)]
LOCAL=REGIONAL_TOTAL+PROFILES+[('density',R)]
NORMAL=LOCAL+[('normalized',R)]
TRACK=[('matter','a'),('frame','a'),('context','d'),('domain',DOMAIN),('curve',CURVE),('lengthunit','a'),('timeunit','a')]
VELOCITY=[('distribution','a')]+TRACK+[('event','a'),('point',POINT),('velocity',POINT)]
SETTING=FIELD_SETTING+[('light',R),('distribution','a'),('pi',R),('densityfield',TAU),('chargefield',TAU),('velocityfield',FIELD)]
WITNESSES=[('event','a'),('sets',SETS),('total',TOTAL)]+PROFILES[1:]+[('electricjet',JET),('magneticjet',JET)]
COUPLED=SETTING+[('point',POINT)]+WITNESSES
SUPPORT=[('distribution','a')]+CHART+[('point',POINT),('normalized',R)]
FLOW=[('distribution','a')]+CHART+[('region',REGION),('velocityfield',FIELD)]
PRIMITIVES={
 'eisvx':(AMOUNT,'同じdistributionとして物理的に同定した分布が、frameのeventにおける座標時刻timeの空間領域regionに保有するkindの符号付き総量を、同じ長さ・時刻・量単位とcontextでamountへ結ぶ。regionはその同時刻断面上の領域述語として解釈し、同じ物理領域の異なる点表現で総量を変えない。eventとtimeの対応及び単位は同じ座標規約に従う。単なる任意の加法的関数、領域を横切る通過量、物質点一個の保有量、時刻差分とは区別する。量の種類が既存zorなら、電気的作用の強さと二極性を表す加法的な電気量として、eirmと同じ符号・尺度の物理的規約を用いる。正負の相殺を許し、零量から空間領域や担体の不在を導かない。量の同定と単位校正を含む基礎的帰属であり、実測済みや保存則の成立を含意しない。有限な総量を持つ適用領域だけで成立する。'),
}
MEANINGS={
 'ekxe':'同じ分布・系・出来事・四座標時刻・長さ時間電荷単位で、同時刻断面の領域族と符号付き有限加法的総量を構成し、その領域族の全領域の値を電気量zorの物理的保有量eisvxへ結ぶ。点表現の違いによる所属差をseowで排除する。',
 'ekxf':'ekxeの同じ総量について、0<半径<upperの全同時刻開球を定義域へ含め、各球の総量をcharge、実際のpiによる体積をvolumeへ結び、その比averageの零半径極限seojを電荷密度densityとする。物質点の存在を密度の定義条件にはしない。',
 'ekxg':'ekxfの同じ局所電荷密度を、同じpiを使うsemlの4pi倍の規格化値normalizedへ結ぶ。負値と零を許し、normalizedを電荷密度や球の総量そのものとしない。',
 'ekxh':'同じ物質点の全座標時刻履歴seobを保持し、定義域内の全有効時刻で同じ出来事・四座標を明示した長さ時間単位のeisqdへも結ぶ。ある一点だけの単位一致で履歴全体の単位を済ませない。',
 'ekxi':'同じ分布の成員zqnについて、単位付き履歴ekxh、その出来事の位置、二側の内点における三座標時刻微分seocを、同じvelocityの三成分へ結ぶ。代表的な別担体、固有時微分、絶対速度の名前で代用しない。',
 'ekxj':'同じ校正済み二場・領域・単位ejsnと地点で、電荷密度場と規格化密度場の値をekxgへ結び、同じ密度値と流速場の値・21偏微分を原刊M0383のsemhへ渡す。場単位と球の電荷単位を共有し、物質不在や変換後の印刷形を追加しない。',
 'ekxk':'有効な規格化密度が非零なら、その同じ地点・系・明示単位で同じ分布に属する担体と出来事が存在する。零密度では担体の有無を決めず、存在を要求しない。密度場だけを自由な数値関数として物質から切り離さない。',
 'ekxl':'同じ分布に属する全担体・出来事・有効領域内四座標の位置割当に対し、同じ流速場の値をekxiの実際の座標時刻速度へ結ぶ履歴が存在する。全成員を同じ一価の流速場へ結び、一つの成功する代表点だけへ縮めない。',
 'ekxm':'非空の指定四座標領域の全有効点で、同じ分布・二場・密度場・流速場・校正単位にekxjを満たす局所証人を要求し、非零密度の担体支持ekxkと全担体の速度ekxlを結ぶ対流を伴う原系の場の設定。全実数・全関数域を有限観測列へ置換しない。',
}
LIMITS=[
 '第九節u0228–u0232の意味依存群を構成する。現在の408主張、旧定義・意味規約・既存判断を変更せず、この段階では本文の著者提示又は全単位意味確認数を増やさない。次に小さい剛体・イオン/電子・電荷の不変な付着・Lorentzの電気力学と光学の電磁的基礎・出発点とwhere説明を統合する。',
 '密度は同時刻の球平均の局所極限という既存の読みを用いる。密度が有限に存在する古典的な連続体記述であり、点電荷の特異点まで有限密度へ変えない。任意の可算加法的測度や全形状の縮小領域との一致を、この定義だけから主張しない。',
 '電荷保有量は一般の量種付き物理入力eisvx、有限加法性はseor、座標表現不変性はseow、密度の極限はseojで分ける。任意の真偽コールバックや加法性だけで電荷と同定しない。物理的単位・極性は同じeirmの規約へ接続する。',
 '既存zqnを選んだ分布の成員関係として再使用する。全成員の所在と軌跡を量化し、密度非零で支持を要求する。密度零は空間の不在・担体の不在・速度零を意味しない。異符号が同じ速度で共存する相殺は許すが、異なる速度を持つ種の流れを合計密度と単一速度の積へ無断でまとめない。',
 '物質点の全履歴の座標単位をeisqdへ接続する。履歴内点の二側微分はseocから再使用する。任意の加速度や変形を等速並進へ制限せず、剛性・小ささ・不変な電荷付着・電荷保存則はこの層の前提に混ぜない。',
 '原系M0383の六式とM0384の電気側発散を使い、磁気側発散零を補わない。物質を含むので真空ejsoを使わずejsnを使う。後続M0389の磁気側の1/V欠落をsemfへ保存したまま、今回の原系へ混ぜない。',
 '有限検査では数値本体、局所引数の同一性、各束縛位置、二点の全域診断を分ける。全関数域と全実数域を列挙できない場合の拒否を保持し、有限対照を密度の存在又は原文同義性の証明にしない。',
]

def args(fields,**replace):return [replace.get(n,v(n)) for n,t in fields]
def at(fn,point=None):return app(fn,*(app(v('point') if point is None else point,k(a)) for a in ROLES))
def velocity(point=None):return lam('axis','a',at(app(v('velocityfield'),v('axis')),point))
def definitions():
    text='r eisvx['+' '.join(t for n,t in AMOUNT)+'] c.\n'
    time=app(v('point'),k('zc7'));universe=lam('probe',POINT,k('seot',v('probe'),time));region=v('part')
    valid=both(*(k('ba',app(v('point'),k(a))) for a in ROLES))
    measured=k('eisvx',v('distribution'),k('zor'),v('frame'),v('event'),time,region,v('lengthunit'),v('timeunit'),v('chargeunit'),app(v('total'),region),v('context'))
    text+=define('ekxe',REGIONAL_TOTAL,both(valid,k('ejsl',*args(CHART)),k('seow',universe,v('sets')),k('seor',universe,v('sets'),v('total')),q('f','part',BALL,op('y',app(v('sets'),region),measured))))
    radius=v('radius');ball=lam('probe',POINT,k('seog',v('point'),radius,v('probe')))
    inside=both(k('ba',radius),k('bg',k('bb','n p a b'),radius),k('bg',radius,v('upper')))
    body=both(app(v('sets'),ball),k('sca',app(v('total'),ball),app(v('charge'),radius)),k('sedm',radius,v('pi'),app(v('volume'),radius)))
    text+=define('ekxf',LOCAL,both(k('ekxe',*args(REGIONAL_TOTAL)),k('sedi',v('pi')),k('seoj',*[v(n) for n in ('upper','charge','volume','average','density')]),q('f','radius',R,op('y',inside,body))))
    text+=define('ekxg',NORMAL,both(k('ekxf',*args(LOCAL)),k('seml',v('pi'),v('normalized'),v('density'))))
    track=args(TRACK[:5]);moment=v('moment');curvepoint=app(v('curve'),moment)
    position=lambda point:k('eisqd',v('matter'),v('frame'),v('event'),v('lengthunit'),v('timeunit'),point,v('context'))
    linked=both(k('seoa',*track,v('event'),moment),position(curvepoint))
    text+=define('ekxh',TRACK,both(k('ejsl',*args(CHART)),k('seob',*track),q('f','moment',R,op('y',both(k('ba',moment),app(v('domain'),moment)),q('g','event','a',linked)))))
    member=app(k('zqn'),v('matter'),v('distribution'),v('context'))
    text+=define('ekxi',VELOCITY,both(member,k('ekxh',*args(TRACK)),position(v('point')),k('seoc',*track,v('event'),v('point'),*(app(v('velocity'),k(a)) for a in ROLES[:3]))))
    local=args(NORMAL,density=at(v('chargefield')),normalized=at(v('densityfield')))
    equations=k('semh',v('electricfield'),v('magneticfield'),v('region'),v('point'),v('light'),at(v('densityfield')),velocity(),v('electricjet'),v('magneticjet'))
    text+=define('ekxj',COUPLED,both(k('ejsn',*args(FIELD_SETTING)),k('ejsj',v('point'),v('region')),k('ekxg',*local),equations))
    support=quantified('g',[('matter','a'),('event','a')],both(member,k('zpb',v('matter'),v('frame'),v('event'),v('point'),v('context')),position(v('point'))))
    text+=define('ekxk',SUPPORT,both(k('ba',v('normalized')),op('y',op('u',k('sca',v('normalized'),k('bb','n p a b'))),support)))
    selected=both(member,k('zpb',v('matter'),v('frame'),v('event'),v('point'),v('context')),k('ejsj',v('point'),v('region')))
    proof=quantified('g',[('domain',DOMAIN),('curve',CURVE)],k('ekxi',*args(VELOCITY,velocity=velocity())))
    text+=define('ekxl',FLOW,quantified('f',[('matter','a'),('event','a'),('point',POINT)],op('y',selected,proof)))
    inside=k('ejsj',v('point'),v('region'))
    witnesses=quantified('g',WITNESSES,k('ekxj',*args(COUPLED)))
    pointlaw=both(witnesses,k('ekxk',*args(SUPPORT,normalized=at(v('densityfield')))))
    text+=define('ekxm',SETTING,both(k('ejsn',*args(FIELD_SETTING)),q('g','point',POINT,inside),
        q('f','point',POINT,op('y',inside,pointlaw)),k('ekxl',*args(FLOW))))
    return text

@lru_cache(None)
def build():
    old=parse(read(PARENT));assert len(old['statements'])==408
    assert not(set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']
    added=doc['declarations'][len(old['declarations']):]
    prim={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,t in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='convective_charge_physical_setting_dependency',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=prim,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[]).document
    ann=json.loads(read('data/eighth-section-heading-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode()))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
