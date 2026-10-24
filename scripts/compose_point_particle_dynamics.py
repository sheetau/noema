"""Connect a charged point trajectory, low-speed inertia and the local rest law."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_limits import ROOT,R,v,call as k,app,op,both,quant as q
from scripts.compose_material_relative_frame import define
from scripts.compose_material_velocity import TRACK,DOMAIN,CURVE,POINT,ROLES,coord,valid
from scripts.compose_material_acceleration import AT,PROFILES,ACCEL
from scripts.compose_vacuum_field_domain import FIELDS,CHART
from scripts.compose_field_equations import FIELD,REGION
from scripts.compose_doppler_infinity import quantified
from scripts.compose_relativity_conjecture import content

def read(path):return (ROOT/path).read_text(encoding='utf-8')
PARENT='examples/v014/einstein-charge-constancy-claim.noema';PARENT_BASIS='data/charge-constancy-claim-basis-v1.json'
FULL='examples/v014/einstein-point-particle-dynamics.noema';CORE='examples/v014/point-particle-dynamics-core.noema'
BASIS='data/point-particle-dynamics-basis-v1.json';ANNOTATIONS='data/point-particle-dynamics-identifiers-v1.json'
UNITS=[(n,'a') for n in ('lengthunit','timeunit','massunit','forceunit')]+[(n,'b') for n in ('lengthscale','timescale','massscale','forcescale')]+[('context','d')]
MASS=[(n,'a') for n in ('matter','frame','event','massunit')]+[('mass',R),('context','d')]
HISTORY=TRACK+[('lengthunit','a'),('timeunit','a'),('region',REGION)]
KINEMATIC=AT+[('lengthunit','a'),('timeunit','a'),('region',REGION)]
REST=[('point',POINT)]+PROFILES
SCALAR=[(n,R) for n in ('mass','charge','acceleration','electric')]
VECTOR=[('mass',R),('charge',R),('point',POINT),('electricfield',FIELD)]+ACCEL
CHARGE=[(n,'a') for n in ('matter','frame','event','chargerecord','chargeunit')]+[('chargescale','b'),('charge',R),('context','d')]
SETTING=FIELDS+[('matter','a'),('event','a'),('domain',DOMAIN),('curve',CURVE),('point',POINT)]+PROFILES+ACCEL+[(n,'a') for n in ('chargerecord','massunit')]+[('chargescale','b'),('charge',R),('mass',R)]+[(n,'b') for n in ('lengthscale','timescale','massscale','forcescale')]
CASES=[(n,t) for n,t in SETTING if n not in ('frame','context','electricconversion')]
ZERO=k('bb','n p a b');ONE=k('bb','n p b b')
PRIMITIVES={
 'eisww':(MASS,'同じmatterのeventでの物理的状態について、低速域の慣性を質量単位massunitで数値massとして記述する帰属。低速は基準frameでの速度が光速度に比べ十分小さく、機械的な作用に対する運動変化の係数が速度に依存しない近似へ帰着する領域と読む。その係数は同じ機械的作用と座標時刻の加速度の尺度により比較される慣性の量であり、電気量、重力による重量、移動時の縦横の係数又は電磁場エネルギーそのものとは別である。正値と単位の整合は合成で要求する。現在の速度が実際に低速であること、特定の粒子種、特定の電気力の運動法則、実測済み、相対論的な質量公式はこの帰属自体に含めない。'),
}
MEANINGS={
 'ek3n':'同じ文脈の長さ・時間・質量・力の四単位を、既存ejwbの正の尺度と次元指数へ結ぶ。力の尺度Fと質量M・長さL・時間TはF T²=M Lを満たし、数値の二階座標時刻微分に質量を掛けると同じ力単位になる。単に単位名が一致するという条件ではない。',
 'ek3o':'同じ対象・系・出来事・質量単位の低速慣性質量をeiswwへ結び、正の有効実数とする。現時点の速度が小さいこと又はその粒子の全運動が等速であることを要求しない。',
 'ek3p':'同じ物質点の非空で完全な座標時刻履歴seobを保ち、同じ校正座標系・長さ時間単位をejslで固定する。領域内の全実時刻で曲線の位置は同じ電磁場領域に属し、その時刻の同じ対象の全座標出来事にeisqdの明示単位を要求する。成功した一点だけに校正を限定しない。',
 'ek3q':'同じ単位付きの全履歴ek3pとseppを結び、指定した同じ出来事・四座標で三つの座標加速度を実際の座標時刻二階微分として与える。固有時の微分、独立に選んだ速度関数、別粒子又は別時点の加速度へ替えない。',
 'ek3r':'指定点の同じ座標時刻で三つの速度関数の値が全て有効な零である。ek3qと結んで瞬間静止を表し、近傍全体の静止又は加速度零を追加しない。単独で物理的な履歴の存在を断言する定義ではない。',
 'ek3s':'有効な正のmassと符号付きcharge、acceleration、electricに対するmass×acceleration=charge×electricの一成分の数式。電荷で割らず、零・負の電荷と任意の加速度符号を扱う。物理的な値の帰属は別に接続する。',
 'ek3t':'相異なる三空間軸のそれぞれについて、同じ四座標で同じ電場を評価した成分と対応する座標加速度にek3sを適用する。時刻軸を第四の運動式へ追加せず、場の原点値や大きさだけで代用しない。',
 'ek3u':'同じ対象を点状の電気量担体eisqcとして扱い、その同じ系・出来事・電荷単位・正の尺度にsbw2で指定された有効な非零の符号付き電荷を結ぶ。正の電荷又は現代の負電子の値へ固定せず、全時間の電荷不変をこの局所の帰属に追加しない。',
 'ek3v':'同じ設定の校正された二場ejsn、整合した力・質量・座標単位ek3n、低速慣性質量ek3o、単位付き二階履歴ek3q、点状担体の電荷ek3uを結ぶ。電荷×電場と力の換算は1であり、数値式に隠れた換算係数を作らない。真空、無磁場、放射不在又は運動方程式を設定の前提にしない。',
 'ek3w':'同じ設定で、同じ三速度が当該瞬間に零なら、その同じ場所と時刻の電場三成分・同じ電荷と低速慣性質量・同じ座標加速度がek3tを満たすという局所的な条件付き運動法則。近傍全体の静止を要求せず、非静止時にもこの三式を無条件適用しない。',
 'ek3x':'K=raの同じ評価点で、全ての設定引数に対しek3vならek3wを要求する閉じた内容。u0240–u0243の物理的依存候補であり、著者の仮定・その限定・命名・直後の時間部分・表示式と意味説明・第十節見出しの全文統合はまだ行わない。',
}
LIMITS=[
 '原刊917頁u0240–u0243の同じ粒子の点状理想化、電荷、瞬間静止、三つの二階座標時刻微分、同じ位置の電場、低速時の質量に必要な依存群。旧413主張を保持し、新主張と全単位の意味判断は追加しない。',
 '低速慣性質量は機械的作用に対する運動変化の係数の低速域の値という一般的な物理入力として明示する。その同じ値の正性・単位・対象・出来事を合成へ接続する。μを電荷、移動時の縦横係数又は名前だけの定数にしない。物理的な校正操作や一般の力学を有限検査で証明したとはしない。',
 '履歴は選択した非空の局所時間領域について完全であり、評価時刻の両側近傍をseppが要求する。場の領域はその局所履歴を含めばよく、全宇宙又は全生涯を含む必要はない。明示単位を全対象出来事で共有し、時刻座標を別のパラメーターへ交換しない。',
 '点粒子は既存eisqcの電気量を一つの位置へ集中させる理想化として読む。古典的な対象であり、現代の電子の固定電荷、量子性、内部構造又は点電荷自己場の正則性を補わない。場割当は指定位置で有効な既存の二場として扱い、その場の発生源又は自己作用の理論を導入しない。',
 '長さL・時間T・質量M・力Fの尺度は正の有理数として既存の乗法単位規約を使い、F T²=M Lと電気的換算1で印刷式の無係数の形を与える。特定のSI又はCGSの数値を原文へ足さず、複数の整合した尺度を許す。',
 '同じ出来事の電荷は非零の符号付き量という帯電の読み。数式ek3s自体は零電荷も扱うが、物理的設定では非零とする。この量を全期間固定された電荷へ自動的に拡張しない。',
 '静止は指定時刻の三速度零であり、三加速度零ではない。右の直後の時間部分を有限な静止期間へ替えない。in dem nächsten Zeitteilchenの初期運動の意味は、この局所式へ結ぶ後続の時間的提示で明示する必要があり、今回の局所式だけで全文を判断しない。',
 'nur folgendesという運動法則への仮定の限定、folgendesの前方参照、Elektronの以下の命名、μとx,y,zの意味説明、§10の緩い加速と動力学の主題、著者への帰属は未統合。既存の第九節の担体モデルを点粒子や無放射へ無条件に流用しない。',
 '有限モデルは数値・対象・単位・場所・履歴・三軸と条件の結合を検査する。二階微分の解析的多項式診断と、全時間量化のネイティブな拒否を維持し、連続体全域、物理法則又は原文同義性の自動証明にしない。',
]

def args(fields,**replace):return [replace.get(n,v(n)) for n,t in fields]

def definitions():
    text='r eisww['+' '.join(t for n,t in MASS)+'] c.\n'
    profiles=[('lengthunit',(1,0,0),'lengthscale'),('timeunit',(0,0,1),'timescale'),('massunit',(0,1,0),'massscale'),('forceunit',(1,1,-2),'forcescale')]
    rat=lambda x:'n '+('u' if x<0 else 'p')+' '+{0:'a',1:'b',2:'c'}[abs(x)]+' b'
    body=[k('ejwb',v(unit),*(rat(x) for x in dims),v(scale),v('context')) for unit,dims,scale in profiles]
    body.append(op('e',k('ad',v('forcescale'),k('ad',v('timescale'),v('timescale'))),k('ad',v('massscale'),v('lengthscale'))))
    text+=define('ek3n',UNITS,both(*body))
    text+=define('ek3o',MASS,both(k('ba',v('mass')),k('bg',ZERO,v('mass')),k('eisww',*args(MASS))))
    time=v('time');point=app(v('curve'),time)
    selected=both(k('ba',time),app(v('domain'),time))
    record=k('seoa',*args(TRACK),v('event'),time)
    calibrated=k('eisqd',v('matter'),v('frame'),v('event'),v('lengthunit'),v('timeunit'),point,v('context'))
    each=q('f','time',R,op('y',selected,both(k('ejsj',point,v('region')),q('f','event','a',op('y',record,calibrated)))))
    text+=define('ek3p',HISTORY,both(k('ejsl',*args(CHART)),k('seob',*args(TRACK)),each))
    text+=define('ek3q',KINEMATIC,both(k('ek3p',*args(HISTORY)),k('sepp',*args(AT))))
    moment=coord(v('point'),ROLES[3]);speeds=[app(v(n),moment) for n,t in PROFILES]
    text+=define('ek3r',REST,both(*(both(k('ba',x),k('sca',x,ZERO)) for x in speeds)))
    text+=define('ek3s',SCALAR,both(*(k('ba',v(n)) for n,t in SCALAR),k('bg',ZERO,v('mass')),k('sca',k('shv',v('mass'),v('acceleration')),k('shv',v('charge'),v('electric')))))
    roles=[op('u',op('e',k(a),k(b))) for i,a in enumerate(ROLES) for b in ROLES[i+1:]]
    text+=define('ek3t',VECTOR,both(*roles,valid(v('point')),*(k('ek3s',v('mass'),v('charge'),v(acc),app(app(v('electricfield'),k(axis)),*(coord(v('point'),a) for a in ROLES))) for axis,(acc,t) in zip(ROLES[:3],ACCEL))))
    reading=k('sbw2',v('chargerecord'),v('matter'),k('zor'),v('frame'),v('event'),v('chargeunit'),v('chargescale'),v('charge'),v('context'),'p zof','p zog')
    text+=define('ek3u',CHARGE,both(k('eisqc',v('matter'),v('context')),reading,op('u',k('sca',v('charge'),ZERO))))
    text+=define('ek3v',SETTING,both(k('ejsn',*args(FIELDS)),k('sca',v('electricconversion'),ONE),k('ek3n',*args(UNITS)),k('ek3o',*args(MASS)),k('ek3q',*args(KINEMATIC)),k('ek3u',*args(CHARGE))))
    text+=define('ek3w',SETTING,op('y',k('ek3r',*args(REST)),k('ek3t',*args(VECTOR))))
    # Avoid capture of the source content's evaluation point by the four-coordinate binder.
    text+=content('ek3x',quantified('f',[(('location' if n=='point' else n),t) for n,t in CASES],op('y',k('ek3v',*args(SETTING,frame=k('ra'),context=v('point'),electricconversion=ONE,point=v('location'))),k('ek3w',*args(SETTING,frame=k('ra'),context=v('point'),electricconversion=ONE,point=v('location'))))))
    return text

@lru_cache(None)
def build():
    old=parse(read(PARENT));assert len(old['statements'])==413
    assert not(set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']
    added=doc['declarations'][len(old['declarations']):]
    prim={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,t in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='charged_point_particle_local_dynamics_dependency',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=prim,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[]).document
    ann=json.loads(read('data/charge-constancy-claim-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode()))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
