"""A declared, standard-relative macroscopic reading of a conductor."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_charge_transport_capacity import ROOT,read,HISTORY,PROFILES
from scripts.compose_material_relative_frame import define,args
from scripts.compose_limits import R,v,call as k,app,op,both,quant as q,ZERO

PARENT='examples/v014/einstein-electric-response.noema'
PARENT_BASIS='data/electric-response-basis-v1.json'
FULL='examples/v014/einstein-conductor-reading.noema'
CORE='examples/v014/conductor-reading-core.noema'
BASIS='data/conductor-reading-basis-v1.json'
ANNOTATIONS='data/conductor-reading-identifiers-v1.json'
WINDOW=[(n,R) for n in ('lower','upper','start','end','threshold','minimumspan')]
RESPONSE=HISTORY+[('threshold',R),('minimumspan',R)]
WITNESS=RESPONSE+[('section','a'),('orientation','a'),('start',R),('end',R)]
STANDARD=[('standard','a'),('body','a'),('source','d'),('timeunit','a'),('quantityunit','a'),('threshold',R),('minimumspan',R)]
TRIAL=STANDARD+[('operation','a'),('alternative','d')]+[(n,t) for n,t in HISTORY if n not in ('body','context','timeunit','quantityunit')]
CAPACITY=STANDARD+PROFILES
ATTRIBUTION=[('standard','a'),('operation','a'),('source','d')]+HISTORY
MEANINGS={
 'eice':'有効な実数で与えた履歴区間内に、正の最小持続時間以上の長さを持つ非退化な応答区間を指定する。率の閾値と最小持続時間は正とし、零閾値で任意の漏れを、零時間で瞬間値を成功にしない。数値基準の物理的な適切さはeirpが別に指定する。',
 'eicf':'同じ物体の完全な電流履歴eibfの、全断面範囲内の同じ有向断面について、eiceの応答区間の全実時刻で電流の絶対値が指定閾値を超える。端点や標本だけを持続としない。一つの試行が示す応答であり、全断面・全時刻・全試行の成功とはしない。',
 'eicg':'同じ物体・系・文脈・単位・完全な電流履歴と、固定された正の閾値・最小時間について、eicfを満たす断面と向きと応答区間が存在する。短い一過性応答、閾値以下の漏れ、区間外の値は成功にならない。',
 'eich':'同じ物体・元状況にあらかじめ適用する基準eirp、その基準に属する電気的試行eirq、物質を保持する許容性eirk、同じ試行の可能な結果zrdpossibleを結ぶ。その結果の同じ全電流履歴が試行に由来する応答であるeirrと、eicgの持続条件を要求する。元状況に現に電流が流れることや試行の実施済みを要求しない。',
 'eici':'同じ基準・物体・元状況・単位・閾値・最小時間の下で、eichを満たす試行と可能結果が存在する。履歴の六関数族を同じ元状況・操作・結果で選ぶ。通常の条件で材料を変えず有意な電荷輸送を持続させられる物体、という導体の文脈依存の読みに用いる。特定担体の剛体内軌跡、電子種、Ohm則、二値因果モデルの全解保証を語義に加えない。',
}
PRIMITIVES={
 'eirp':(STANDARD,'指定した評価基準が、この元状況の同じ物体と量・時間単位に適用され、輸送率の閾値と最小持続時間を定める。作用の許容範囲、尺度、過渡応答を除く評価時間、通常の輸送と無視する漏れの区別を結果を見る前に固定するという文脈上の基準設定。成功例に合わせた閾値の引下げや試行後の分類変更を許さない。これは物体が成功するという分類ではなく、評価の物理的・実用的な基準の帰属である。単一の普遍的数値境界を意味しない。'),
 'eirq':([('standard','a'),('body','a'),('operation','a'),('source','d')],'同じ評価基準の下で、この操作が同じ物体の電荷輸送を調べる通常の電気的な駆動・接続の試行に属する。作用の強さ、準備・待ち時間、温度・相・接触・幾何学的尺度を基準の許容範囲に保つ。材料の破壊・変質や別物体の混入による通過を試行種類へ含めず、許容性自体はeirkとも照合する。電場・電位差等の電気的作用を加える役割であり、単なる外力による物体全体の運搬や偶発的な熱揺らぎの選別とは区別する。成功は含意しない。'),
 'eirr':(ATTRIBUTION,'同じ基準・操作・元状況について、結果文脈の同じ物体・系・単位・区間・全断面に割り当てた累積輸送量と率の履歴が、その試行によって現れる物理的な輸送応答であるという帰属。単なる共存や時間的先行から認定せず、無関係な既存電流を成功へ混入しないための背景と応答の分離を基準に従って保つ。零又は弱い応答もこの帰属を持ち得る。閾値超過・持続・物理的可能性・導体の分類は合成側で別に要求する。一般的な物理的応答の基礎関係として採り、微視的な因果機構の導出や実験の実施を意味しない。'),
}
LIMITS=[
 '導入u0003のLeiterを、通常の条件で材料を変えず有意な電荷輸送を持続できる物体として読むための基準付き語義構成である。量・尺度・試行範囲に相対的で、物質を一つの普遍的閾値で二分する定理ではない。',
 'eirp/eirq/eirrは基準の帰属、試行の種類、物理的応答への帰属という基礎規約である。数値や有限試験の成功からそれらの適切さを自動認定しない。説明のない「導体」原始記号や原語の綴りで判定を代用しない。',
 '語義を成立させる試行は、本文の磁石と導体が動く二場合とは別の可能な性質評価である。本文で現に流れる電流へ正の下限・一方向の持続・一定の駆動を追加しない。評価試行と原文中の現象の文脈を区別して適用する。',
 '特定の点状担体を全区間追跡できること、参照物体の剛性、線形Ohm則、電流がない側との強い二値対照は導体の必要条件にしない。過去の補助定義は、その条件が適切な説明を表すために保持する。',
 '原文の具体的な解釈文脈・基準と語義の結合、磁石・電磁相互作用、二場合の物理的比較条件、起電力・エネルギー、著者への帰属と全文判断は未完。原文207主張と著者表示判断を保持する。',
]

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fields)+'] c.\n' for n,(fields,_) in PRIMITIVES.items())
    zero=k('bb',ZERO)
    text+=define('eice',WINDOW,both(*(k('ba',v(n)) for n,_ in WINDOW),
        k('bg',zero,v('threshold')),k('bg',zero,v('minimumspan')),k('bg',v('start'),v('end')),
        k('lg',v('lower'),v('upper'),v('start')),k('lg',v('lower'),v('upper'),v('end')),
        k('bc',v('minimumspan'),k('bf',v('end'),v('start')))))
    rate=app(app(v('current'),v('section'),v('orientation')),v('time'))
    text+=define('eicf',WITNESS,both(k('eibf',*args(HISTORY)),k('eice',*args(WINDOW)),app(v('sections'),v('section'),v('orientation')),
        q('f','time',R,op('y',k('lg',v('start'),v('end'),v('time')),k('eibk',rate,v('threshold'))))))
    text+=define('eicg',RESPONSE,q('g','section','a',q('g','orientation','a',q('g','start',R,q('g','end',R,k('eicf',*args(WITNESS)))))))
    result=[v('alternative') if n=='context' else v(n) for n,_ in HISTORY]
    text+=define('eich',TRIAL,both(k('zm',v('body')),k('eirp',*args(STANDARD)),
        k('eirq',*[v(n) for n in ('standard','body','operation','source')]),k('eirk',v('body'),v('operation'),v('source')),
        app(k('zrdpossible'),*[v(n) for n in ('operation','body','source','alternative')]),
        k('eirr',v('standard'),v('operation'),v('source'),*result),k('eicg',*result,v('threshold'),v('minimumspan'))))
    names={n for n,_ in PROFILES}
    selected=[app(v(n),v('source'),v('operation'),v('alternative')) if n in names else v(n) for n,_ in TRIAL]
    text+=define('eici',CAPACITY,q('g','operation','a',q('g','alternative','d',k('eich',*selected))))
    return text

def build():
    old=parse(read(PARENT));doc=deepcopy(old);doc['statements']=[]
    assert not (set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in doc['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='standard_relative_conductor_reading',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,
        primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[]).document
    ann=json.loads(read('data/electric-response-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}

if __name__=='__main__':
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    print('Standard-relative conductor reading composed')
