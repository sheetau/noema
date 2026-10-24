"""Give the point-charge calibration physical units and directed force records."""
from copy import deepcopy
from fractions import Fraction
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_vacuum_field_domain import ROOT,read
from scripts.compose_material_relative_frame import define
from scripts.compose_relativity_conjecture import content,evaluate
from scripts.compose_two_postulates import quote
from scripts.compose_field_equations import POINT,ROLES
from scripts.compose_rest_force import AXES
from scripts.compose_limits import R,v,call as k,app,op,both
from scripts.check_moving_light_trip import literal

PARENT='examples/v014/einstein-field-symmetry-conclusion.noema';PARENT_BASIS='data/field-symmetry-conclusion-basis-v1.json'
FULL='examples/v014/einstein-point-charge-calibration.noema';CORE='examples/v014/point-charge-calibration-core.noema'
BASIS='data/point-charge-calibration-basis-v1.json';ANNOTATIONS='data/point-charge-calibration-identifiers-v1.json';INDEX=163
PROFILE=[('unit','a'),('length','b'),('mass','b'),('time','b'),('scale','b'),('context','d')]
POSITION=[('body','a'),('frame','a'),('event','a'),('lengthunit','a'),('timeunit','a'),('point',POINT),('context','d')]
FORCE=[(n,'a') for n in ('record','trial','source','target','frame','event','unit')]+[('force',POINT),('context','d')]
PRIMITIVES={
 'eisqb':(PROFILE,'同じ文脈でunitの量種と尺度を、長さ・質量・時間の独立した基準によって定める単位規約。length/mass/timeはそれぞれの次元指数で、unitの一単位は基準のm^length kg^mass s^timeのscale倍である。基準の長さは校正された物差しによる距離、時間は校正された時計の経過、質量は機械的作用に対する慣性の量として同定する。基準名だけの文字列比較ではなく、同じ基準へ比較・移換できる尺度の指定である。正の尺度は合成側で要求する。原点の移動、対数量、単位変更による物理量の変化は含まない。本文の歴史的なcm/Dynを比較するための基準であり、現代の特定の標準器や定義定数を原著に追加しない。'),
 'eisqc':([('body','a'),('context','d')],'bodyは同じ文脈で、電気的作用の強さと極性を担う電気量を一つの位置へ集中させて記述する点状担体の理想化である。内部の空間的な広がりと多極構造をこの記述で分解せず、電荷と位置を同じ対象に帰属させる。座標点そのものや電気量という数値を物体と同一視しない。対象の位置・量の値・単位・作用は別に接続する。現代の特定粒子種、点電荷の実在や自己場の正則性、試行の実行を主張しない。'),
 'eisqd':(POSITION,'同じbodyのeventにおける位置と時刻を、frameの明示した長さ・時間単位でpointの四座標へ対応させる物理的な位置割当。三座標はその長さ単位、時刻はその時間単位を用いる。同じ出来事を別単位で記述する場合は数値を換算し、別系の数値座標を等置しない。電気量の校正では同じ試行で比較する対象の電荷位置を追跡し、別の物体の点や別時点の位置を混ぜない。点状理想化は別のeisqcで要求し、位置割当だけから対象の内部構造を消去しない。実測済みを意味しない。'),
 'eisqe':(FORCE,'recordが同じtrialで、sourceからtargetへ、frameのeventにおいて働く電気的な機械力の寄与を、unitの三成分forceとして記述するという作用の帰属。力は同じ状態での運動量変化への寄与又はそれを釣り合わせる機械的作用として同定する基礎量である。作用する側と受ける側を区別し、重力や支持力を加えた合力、逆向きの反作用、source自身に働く力を代入しない。電気量の極性・尺度と同じ物理的規約を用いるが、数値比例だけではこの帰属を認定しない。仮定上の結果も許し、実行済みの標識ではない。'),
 'eisqf':([], 'u0173の校正で比較する第二対象zomについて、同じK・出来事・電気量単位で値1を指定する結果記録。'),
 'eisqg':([], '同じ校正試行の第一対象zolのKにおける四座標。長さはcm、時間は秒として位置割当へ結ぶ。',POINT),
 'eisqh':([], '同じ校正試行の第二対象zomのKにおける四座標。第一対象と同時刻で距離1 cmを要求する。',POINT),
 'eisqi':([], '同じ校正で第一対象から第二対象へ働く電気的な力の三成分。単位Dyn、三成分の大きさ1を要求するが方向は原文にない値で固定しない。',POINT),
 'eisqj':([], 'u0173第二文のd. h.以下で、電気量1の仮定を距離1 cm・力1 Dynの作用で説明する箇所。'),
}
MEANINGS={
 'ejwb':'正の有理尺度と三次元指数を同じ物理的単位規約eisqbへ結ぶ。単位名や数値の一致だけで校正を済ませない。',
 'ejwc':'同じ文脈のcmは長さの1/100 m、Dynは質量×長さ/時間²の1/100000 kg m/s²、秒は時間の基準尺度1とする。Dynの尺度は1 g×1 cm/s²の換算と一致する。',
 'ejwd':'二つの有効な四座標の時刻が一致し、三空間成分の差の平方和が非負の距離の平方になる。各入力を同じ長さ単位で使う。同じ座標点を排除せず、非零距離は適用側で与える。',
 'ejwe':'三つの異なる空間軸の有効な力成分について、平方和が非負の大きさの平方になる。向きを特定せず、大きさだけを使う校正と後続の力ベクトルの等値を区別する。',
 'ejwf':'同じ第一対象zolを点状電気量として扱い、Kの同じ出来事・単位zouで値1の記録sbz2を与える仮定内容。実測済みや現代の粒子の実在を含意しない。',
 'ejwg':'第一対象の値1の記録と、同じ系・出来事・量種・単位・尺度で第二対象にも値1を指定する別記録を結ぶ。二対象を区別し、未説明の同じ量という一つの判定だけで代用しない。',
 'ejwh':'同じ単位規約、点状の第一対象と同じ量の別対象、同じ試行・出来事、第一対象のKへの静止を保持し、同じcm/秒の二位置の同時刻距離1と、第一対象から第二対象への力のDynでの大きさ1を結ぶ校正仮定。距離と力の結果記録、力の向きと受け手、三成分と大きさを区別する。第二対象の静止を追加しない。',
 'ejwi':'同じ著者が電気量1のejwfを仮定し、d. h.以下の作用による校正ejwhも仮定として提示して説明する。両内容を処理系が事実として実行せず、単独の一試行が単位定義の一般的必要十分条件だとも主張しない。',
 'ejwj':'点状電気量1の仮定と作用による校正説明ejwiを述べるメッセージ。',
 'ejwk':'u0173第二文の校正の仮定と説明を同じ著者・論説へ帰属させる。旧文163だけを置き換える。段落の他の五文の完成は別に必要。',
}
LIMITS=[
 'u0173六文のうち第二文の物理的な校正の依存内容を先に完成させる。段落の解釈導入、相対性原理による二系の同じ電気量、静止・瞬間静止での力との同定、二つの言い表しへの導入と段落全体の判断は残る。',
 '電気量は電気的作用の強さと二極性を表す符号付き量。ここでは同じ正の単位を二対象に使い値1を指定する。慣性質量や電荷の数値を物体そのものにしない。点状の理想化を要求するのは原文で指定された第一対象であり、第二対象の静止や内部構造は補わない。',
 '校正の点はcm/秒の単位を明示した同じKの二位置。後続の場の四座標候補zpj/zpkと数値で同一視しない。距離は同じ校正時刻の三次元の直線距離として読み、別時点や光の経路長へ替えない。',
 'Dynを1 g cm/s²という機械力の単位として、独立した長さ・質量・時間の次元と正の尺度へ結ぶ。m/kg/sは比較基準であり、原著に現代のSI法制や定義定数を導入しない。電気量の単位zouはこの同じ静電的な作用による校正に属し、別の単位を使って数値だけ1にしない。',
 '第一対象がKに静止するという旧x4の意味を保持する。親のsby2に一時あったxmとの誤接続は後継版で訂正済みであり、旧証拠を書き換えない。今回は新たな校正内容を同じ物理的な位置と力へ結ぶ。',
 '仮定された結果記録であり、測定や試行の実行を要請しない。距離と力の一般的な物理的同定規約を明示し、実験装置の全構成やクーロン則の一般証明を原文へ追加しない。',
 '旧文163のみを置換し、他357主張・既判断・旧意味規約を保存する。全文意味確認数は増やさない。',
]

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in spec[0])+'] '+('c' if spec[0] else spec[2] if len(spec)>2 else 'a')+'.\n' for n,spec in PRIMITIVES.items())
    zero=k('bb','n p a b');one=k('bb','n p b b');p=v('point');ctx=v('context')
    text+=define('ejwb',PROFILE,both(k('aa','n p a b',v('scale')),k('eisqb',*[v(n) for n,_ in PROFILE])))
    text+=content('ejwc',both(k('ejwb',k('zos'),literal(1),literal(0),literal(0),literal(Fraction(1,100)),p),k('ejwb',k('zot'),literal(1),literal(1),literal(-2),literal(Fraction(1,100000)),p),k('ejwb',k('zik'),literal(0),literal(0),literal(1),literal(1),p)))
    def squared_sum(xs):
        out=zero
        for x in xs:out=k('bd',out,k('shv',x,x))
        return out
    first,second=v('first'),v('second');coords=lambda point:[app(point,k(n)) for n in ROLES]
    text+=define('ejwd',[('first',POINT),('second',POINT),('distance',R)],both(k('shn',k('shx'),first,'p ba'),k('shn',k('shx'),second,'p ba'),k('ba',v('distance')),k('bc',zero,v('distance')),k('sca',coords(first)[3],coords(second)[3]),k('sca',squared_sum([k('bf',a,b) for a,b in zip(coords(first)[:3],coords(second)[:3])]),k('shv',v('distance'),v('distance')))))
    text+=define('ejwe',[('force',POINT),('magnitude',R)],both(k('shn',AXES,v('force'),'p ba'),k('ba',v('magnitude')),k('bc',zero,v('magnitude')),k('sca',squared_sum(coords(v('force'))[:3]),k('shv',v('magnitude'),v('magnitude')))))
    text+=content('ejwf',both(k('eisqc',k('zol'),p),evaluate('sbz2')))
    reading=lambda record,target,kind,unit:k('sbw2',k(record),k(target),k(kind),k('ra'),k('zoo'),k(unit),'n p b b',one,p,'p zof','p zog')
    text+=content('ejwg',both(evaluate('ejwf'),op('u',op('e',k('zol'),k('zom'))),reading('eisqf','zom','zor','zou')))
    positions=[k('eisqd',k(body),k('ra'),k('zoo'),k('zos'),k('zik'),k(point),p) for body,point in [('zol','eisqg'),('zom','eisqh')]]
    text+=content('ejwh',both(evaluate('ejwc'),evaluate('ejwg'),k('va',k('ra')),k('zoh',k('zon'),k('zol'),k('zom'),k('ra'),k('zoo'),p),k('x4',k('zol'),k('ra'),p),*positions,k('ejwd',k('eisqg'),k('eisqh'),one),reading('zov','zon','zop','zos'),reading('zow','zon','zoq','zot'),op('u',op('e',k('zop'),k('zoq'))),k('eisqe',k('zow'),k('zon'),k('zol'),k('zom'),k('ra'),k('zoo'),k('zot'),k('eisqi'),p),k('eirl',k('zow'),k('zom'),k('ra'),k('zoo'),p),k('zof',k('zot'),k('zpn'),'n p b b',p),k('zpc',k('zow'),k('zom'),k('zpn'),k('ra'),k('zoo'),k('zot'),k('eisqi'),p),k('ejwe',k('eisqi'),one)))
    a=k('rd');scope=k('zno')
    text+=content('ejwi',both(k('ug',k('zoy'),a,quote('ejwf'),scope,p),k('ug',k('eisqj'),a,quote('ejwh'),scope,p),k('uf',a,k('zoy'),k('eisqj'),p),k('ue',k('zoy'),k('eisqj'),p),op('u',op('e',k('zoy'),k('eisqj')))))
    text+='d ejwj[] f[j s[k ejwi[]]].\n'
    text+=define('ejwk',[],k('eir3',k('zoy'),a,k('eirf'),quote('ejwj'),k('ri')))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==358
    assert not(set(PRIMITIVES)|set(MEANINGS))&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=deepcopy(old['statements']);doc['statements'][INDEX]=dict(kind='assert',body=dict(kind='call',symbol='ejwk',arguments=[]))
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='physical_point_charge_calibration_dependency',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[INDEX]).document
    ann=json.loads(read('data/field-symmetry-conclusion-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
