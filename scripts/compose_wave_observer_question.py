"""Construct a stationary observer's inquiry with fixed wave and field roles."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_wave_display import ROOT,read,FIELD,REGION
from scripts.compose_vacuum_field_domain import FIELDS as CALIBRATION
from scripts.compose_material_relative_frame import define,args
from scripts.compose_limits import R,F,v,call as k,app,op,both,quant as q

PARENT='examples/v014/einstein-wave-display.noema';PARENT_BASIS='data/wave-display-basis-v1.json'
FULL='examples/v014/einstein-wave-observer-question.noema';CORE='examples/v014/wave-observer-question-core.noema'
BASIS='data/wave-observer-question-basis-v1.json';ANNOTATIONS='data/wave-observer-question-identifiers-v1.json'
OBSERVER=[('observer','a'),('frame','a'),('context','d'),('lengthunit','a'),('timeunit','a'),('lower',R),('upper',R)]+[(n,F) for n in ('x','y','z')]
TRACE=[(n,F) for n in ('x','y','z')]+[('region',REGION),('time',R)]
LOCATION=OBSERVER+[('region',REGION)]
INVESTIGATION=LOCATION+[('wave','a'),('process','a')]
QUESTION=INVESTIGATION+[(n,'a') for n in ('chargeunit','electricunit','magneticunit','forceunit')]+[(n,R) for n in ('electricconversion','magneticconversion')]
ANSWERS=[('electricfield',FIELD),('magneticfield',FIELD)]
PRIMITIVES={
 'eissd':([('observer','a'),('wave','a'),('process','a'),('frame','a'),('region',REGION),('context','d')],'observerが同じ物理的な波waveに属する過程processを、frameの座標とregionの範囲で調べるという対象と調査の対応。数値関数の偶然の一致を波の同一性とせず、別の波又は別の過程の調査を混ぜない。調査はその系における電磁的な性質を確かめる活動として読み、成功した測定記録・答えの既知性・特定の装置・全点の実測済みを要求しない。静止、領域への位置付け、候補場の物理的校正はそれぞれ別に合成する。仮定の内部へ置いた場合に現実の実験実施を含意しない。'),
}
MEANINGS={
 'ekbu':'同じ観測者・系・単位・文脈・正の時間区間について、観測者の役割xb/x4を、三つの代表位置関数の全区間静止eit2へ結ぶ。端点だけの一致、系で座標記述できること、身体内部の全物質点の停止へ置換しない。',
 'ekbv':'同じ三つの代表位置関数を同じtimeで評価し、その三位置と時刻が全て有効実数で指定regionに入ることを述べる。三空間軸と時刻の順序を保つ点ごとの条件。',
 'ekbw':'ekbuの同じ静止観測者の代表位置が、指定した閉時間区間の全有効時刻にekbvで同じ領域に属する。局所調査区間を正の長さで領域内に取る読みであり、変換された領域を新系の矩形領域に取り替えない。',
 'ekbx':'同じekbwの観測者が、同じ系・領域・文脈で同じ波に属する過程を調べるeissdを満たすという条件。調査の条件そのものを問いの提示や実測結果にしない。',
 'ekby':'調査条件ekbxを保持し、二つの答え候補を同じ過程の同じ系・領域の電場と磁場としてeispnへ結び、ejsnの座標・単位・力との換算規約で物理的に同定する。任意の数値関数、別の波の場、既存の別節の固定場を候補の代用にしない。',
 'ekbz':'先に指定した観測者・波・過程・系・領域・位置関数・区間・単位を質問の外側で固定し、電場と磁場の関数対を答えとする質問を作る。候補ごとに別の源や波を存在選択し直さず、存在・一意性・発見済みを断言しない。著者による質問提示は別に必要である。',
}
LIMITS=[
 'u0182の前半に必要な依存定義群。本文366主張と既存の意味判断を保持し、この追加だけでu0182又は第一文を記述済みとはしない。先行の同じ波の仮定とkへの束縛、著者によるWir fragenの提示、後半の変換適用は未完。',
 'Beschaffenheitは同じ物理的な波の電場・磁場の時空関数の記述を求める問いとして準備する。これらは実際の物理場の候補であり、先行の近似表現のsin式と自動的に同一視しない。後続で近似的な答えを与える場合は、表現場と物理場及び十分性の規約を別に維持する必要がある。',
 '観測者の静止は、校正された同じ系の同じ代表位置が全区間で一定であることとする。調査区間を変換後領域内に正の長さで選べる局所的な理想化を採る。原文の全時間・全空間への追加仮定ではなく、源の静止や観測者の全構成粒子の停止を要求しない。',
 '質問の答え型は電場・磁場の関数対であり、単位を固定して初めて物理的な性質となる。関数の領域外の延長は問う性質に含めず、点ごとの実測記録、測定成功、答えの存在・一意性、著者の既知性を追加しない。',
 '今回の定義は任意のframeを引数に取る。本文へ適用する際にKとk、同じ相対運動、同じ物理的な過程と先行の波、変換領域s6m、同じ単位・換算を接続しなければならない。古い第六節の固定された別の場znl/znmを現在の波へ流用しない。',
 '有限検査では全履歴を入力境界として明示した静止の診断、点ごとの座標、二値時刻域での全位置量化、候補二場と同じ固定質問引数の対応を別に確認する。全実数時刻・全関数の列挙拒否を保持し、有限例から現実の調査や原文同義性を認定しない。',
]

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] c.\n' for n,(fs,_) in PRIMITIVES.items())
    text+=define('ekbu',OBSERVER,both(k('xb',v('observer')),k('x4',v('observer'),v('frame'),v('context')),k('eit2',*args(OBSERVER))))
    coordinates=[app(v(n),v('time')) for n in ('x','y','z')]+[v('time')]
    text+=define('ekbv',TRACE,both(*(k('ba',x) for x in coordinates),app(v('region'),*coordinates)))
    inside=both(k('ba',v('time')),k('lg',v('time'),v('lower'),v('upper')))
    text+=define('ekbw',LOCATION,both(k('ekbu',*args(OBSERVER)),q('f','time',R,op('y',inside,k('ekbv',*args(TRACE))))))
    text+=define('ekbx',INVESTIGATION,both(k('ekbw',*args(LOCATION)),k('eissd',*[v(n) for n in ('observer','wave','process','frame','region','context')])))
    text+=define('ekby',QUESTION+ANSWERS,both(k('ekbx',*args(INVESTIGATION)),k('ejsn',*args(CALIBRATION)),k('eispn',*[v(n) for n in ('process','frame','electricfield','magneticfield','region','context')])))
    text+=define('ekbz',QUESTION,'j v[i['+' '.join(n+' '+t for n,t in ANSWERS)+']['+k('ekby',*args(QUESTION+ANSWERS))+']]', 'g['+FIELD+' '+FIELD+']')
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==366
    assert not(set(PRIMITIVES)|set(MEANINGS))&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,t in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='stationary_observer_and_field_pair_question_dependencies',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[]).document
    ann=json.loads(read('data/wave-display-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
