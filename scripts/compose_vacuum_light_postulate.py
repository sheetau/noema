"""Bind a common light speed to complete vacuum propagation cases and local time."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_relativity_conjecture import ROOT,read
from scripts.compose_material_relative_frame import define
from scripts.compose_limits import R,v,call as k,op,both,quant as q

PARENT='examples/v014/einstein-relativity-conjecture.noema';PARENT_BASIS='data/relativity-conjecture-basis-v1.json'
FULL='examples/v014/einstein-vacuum-light-postulate.noema';CORE='examples/v014/vacuum-light-postulate-core.noema'
BASIS='data/vacuum-light-postulate-basis-v1.json';ANNOTATIONS='data/vacuum-light-postulate-identifiers-v1.json'
LOCAL=[('segment','a'),('frame','a'),('reference','a'),('speed',R),('context','d')]
FRAME=[('frame','a'),('speed',R),('context','d')]
PRIMITIVES={
 'eisb5':([('ray','a'),('frame','a'),('context','d')],'rayを、電気側・磁気側の場の変化とエネルギーの伝達を伴う電磁的な放射の伝播として巨視的に記述する。電荷・電流・場と物質への作用は既存eibs/eicoと同じ物理的区別を使う。光線はその伝播の経路を追跡する記述であって、物体の並進、音波、単なる静的な場の存在ではない。可視の波長だけや一つの偏光・波形へ狭めず、現代の光子模型や特定の媒体を必須としない。速度値はこの分類に含めない。'),
 'eisb6':([('segment','a'),('ray','a'),('emitter','a'),('emission','a'),('start','a'),('end','a'),('frame','a'),('lengthunit','a'),('timeunit','a'),('context','d')],'segmentの各参照が、指定物体emitterからemissionで放出された同じrayの伝播を、同じ系・単位・文脈で追う一つの区間の記録である。startは放出又はその後の同じ伝播上の出来事、endはそこから先の出来事である。emitterは同一物質部分と運動状態を持つ放出元の物体であり、rayや局所時計と取り違えない。対象を放出元の静止・等速・特定速度だけに限定しない。区間ごとの値を保持するため記録個体は系・単位・設定を含み、異なる系の値を同じ記録へ無条件に代入しない。実際の計器設置や観測済みという条件は要求せず、仮定上の伝播設定も扱う。'),
 'eisb7':([('frame','a'),('reference','a'),('timeunit','a'),('context','d')],'同じ系の位置ごとに静止する理想的な時計の読みを、同じ参照時計・時間単位へ結ぶ時刻付与規約が採用されている。時計は同じ反復過程・校正尺度に沿って経過を数値化する対象であり、ca/cb/cc/ci/ceはその時計、出来事との同所性、系に対する静止、単位、局所読みを指す。qoの光往復による同期条件を同じ規約で解釈し、同期の成立はsafの本体で別に要求する。仮定上の理想時計による座標時刻を許し、実機が全地点に設置済みとはしない。光源の運動や光線の時計を局所時計の静止と混同しない。'),
 'eisca':([('ray','a'),('start','a'),('end','a'),('frame','a'),('context','d')],'同じrayのstartからendまでの伝播経路の内部に物質的な伝播媒体を置かないという真空の条件。物質による屈折・遅延を持つ媒質内の伝播とは区別する。電磁場や光自身がないという条件ではなく、境界での放出元や受光物体の存在を排除しない。空間の一端だけの条件や、媒体を測っていないという情報不足では代用しない。'),
 'eiscb':([('segment','a'),('ray','a'),('start','a'),('end','a'),('frame','a'),('lengthunit','a'),('length',R),('context','d')],'同じ区間の同じrayが通る空間経路の長さが、指定系で校正した長さ単位でlengthであるという幾何学的な量の帰属。経路を順に細分した全ての有限折線長の上限としての弧長を採り、基準系の空間計量と同じ物質的な長さ尺度へ結ぶ。端点間距離を曲がった経路の長さに代用せず、屈折率を掛けた媒質の光学長とも区別する。経路の同一性・連続性・長さの存在を物理的入力として要求し、未知の軌跡から値を推測しない。折線上限の一般的計算をここで新たに実装したという意味ではない。'),
 'eiscc':([('frame','a'),('lengthunit','a'),('timeunit','a'),('speedunit','a'),('context','d')],'同じ系で空間の長さを静止した標準の尺度と比較し、時間をeisb7の理想時計の共通尺度で読むという単位の校正規約。指定速度単位はこの長さ単位を時間単位で割った単位で、数値の商への追加換算係数を要しない。各系で同じ物理的な単位規約を用い、座標名の一致だけで単位を同一視しない。長さと時間の尺度を混ぜず、特定のSI単位や数値を原文へ補わない。'),
 'eiscd':([('segment','a'),('frame','a'),('lengthunit','a'),('timeunit','a'),('context','d')],'この法則の適用範囲に属する、指定系・単位・文脈で記述する真空中の光の伝播区間の候補。放出元の運動状態、放出場所、方向、時刻、全部分区間を変えた仮定上の設定も範囲に含む。速度が所望の値になる記録だけを選ばず、観測済みの一覧や静止光源だけへ範囲を縮めない。各記録の物理的帰属・読みの妥当性・速度関係は別の条件で確認する。'),
 'eisce':([('frame','a'),('lengthunit','a'),('timeunit','a'),('context','d')],'eiscdがこの法則に必要な全光線・全方向・全時刻・全ての非零部分区間と、放出元の運動状態を変えた全設定を尽くしているという範囲の完全性。光源状態を固定した二標本だけでは足りず、結果が一致する候補だけの抜粋を認めない。有限検査や単位名から完全性を認定するものではない。'),
}
MEANINGS={
 'eifw':'同じ光線、放出元、放出と区間の二出来事、系と単位、真空、幾何学的な経路長を結び、同じ参照時計へ同期した両端の局所読みを既存safで与える。既存saxで正の経路長・経過時間・速度とlength=speed×elapsedを要求する。放出元の速度を足したり、往復距離の係数2を加えたりしない。',
 'eifx':'指定系の校正・時刻規約と完全な区間範囲の下で、既存sakにより非空の全適用区間へ同じ一つの速度を渡す。源の運動状態や時刻で速度値を選び直すことはできない。局所の時刻と物理的な帰属は各区間のeifwで要求する。',
 'eify':'力学方程式が成り立つ系があり、その全ての系でeifxの真空光伝播が同じ共通速度値tcを持つという内容。Vは既存の光速度参照tcであり、数値は指定しない。原文の常にという一般性を任意の適格系で読む明示的な解釈である。非慣性系・物質媒体内まで同じ座標速度を要求しない。',
}
LIMITS=[
 'u0004第二文の光伝播の仮定内部を構成する依存群。推測の前提化・命名・見かけ上の不整合・第二文全体の提示は別途接続する。本文の著者主張は追加しない。',
 '適格な慣性系を任意に選んでも同じ速度値を用いるという読みを採る。旧sbdのraだけへの固定を解除し、加速座標系の全てに等しい座標速度を課すことはしない。',
 '光・媒体のない伝播・源と区間・局所時刻・経路長・校正は物理的に意味付けされた基礎入力である。単なる語名から速度法則を認定せず、有限模型から物理的な全範囲や法則の真理を証明しない。',
 '光源運動からの独立性は、全運動状態を含む範囲に同じ速度を全称的に適用することで表す。静止・運動の二ラベルだけの比較や、一組の実験結果の一致ではない。',
 '理想時計・仮定上の光の設定を用い、全地点に実際の計器があるという余計な要求を加えない。幾何学的な弧長は基礎的な量の帰属として採り、一般的な弧長計算器の完成を主張しない。',
]

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] c.\n' for n,(fs,_) in PRIMITIVES.items())
    segment=v('segment');frame=v('frame');context=v('context');reference=v('reference');at=lambda name:k(name,segment)
    lengthunit=k('ta');timeunit=k('rb')
    conditions=[k('eisb5',at('wf'),frame,context),k('eisb6',segment,*[at(n) for n in ('wf','wg','wh','wi','wj')],frame,lengthunit,timeunit,context),
        k('eisca',at('wf'),at('wi'),at('wj'),frame,context),k('eiscb',segment,at('wf'),at('wi'),at('wj'),frame,lengthunit,at('wq'),context)]
    for event,clock,place,value in (('wi','wk','wm','wo'),('wj','wl','wn','wp')):
        conditions.append(k('saf',at(event),at(clock),at(place),reference,frame,timeunit,at(value),context,'p ca','p cb','p cc','p ci','p ce','p qo'))
    conditions.append(k('sax',at('wq'),at('wo'),at('wp'),v('speed')))
    text+=define('eifw',LOCAL,both(*conditions))
    reference=k('zbh',frame,context)
    selected='i[segment a]['+k('eiscd',segment,frame,lengthunit,timeunit,context)+']'
    measured='i[segment a value '+R+']['+k('eifw',segment,frame,reference,v('value'),context)+']'
    text+=define('eifx',FRAME,both(k('eisb7',frame,reference,timeunit,context),k('eiscc',frame,lengthunit,timeunit,k('tb'),context),k('eisce',frame,lengthunit,timeunit,context),k('sak',v('speed'),selected,measured)))
    qualifying=k('eifb',frame,v('point'))
    text+='d eify[] e[b point['+both(q('g','frame','a',qualifying),q('f','frame','a',op('y',qualifying,k('eifx',frame,k('tc'),v('point')))))+']].\n'
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==214;doc=deepcopy(old);doc['statements']=[]
    assert not(set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in doc['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='common_vacuum_light_speed_with_complete_emitter_scope',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=['eify'],statement_indices=[]).document
    ann=json.loads(read('data/relativity-conjecture-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
