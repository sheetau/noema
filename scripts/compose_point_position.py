"""Compose stationary material points and possible ruler-based Cartesian determination."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_rest_frame_introduction import ROOT,read
from scripts.compose_material_body_motion import FIELDS as BODY
from scripts.compose_material_relative_frame import define,ENAMES
from scripts.compose_two_postulates import quote
from scripts.compose_relativity_conjecture import content
from scripts.compose_limits import R,F,v,call as k,app,op,both,quant as q

PARENT='examples/v014/einstein-rest-frame-introduction.noema';PARENT_BASIS='data/rest-frame-introduction-basis-v1.json'
FULL='examples/v014/einstein-point-position.noema';CORE='examples/v014/point-position-core.noema'
BASIS='data/point-position-basis-v1.json';ANNOTATIONS='data/point-position-identifiers-v1.json';INDEX=223
HISTORY=[('point','a'),('frame','a'),('context','d'),('lengthunit','a'),('timeunit','a'),('lower',R),('upper',R)]+[(a,F) for a in ('x','y','z')]
GEOMETRY=[(n,R) for n in ('px','py','pz','ox','oy','oz',*ENAMES,'cx','cy','cz')]
USE=[('ruler','a'),('method','a'),('frame','a'),('unit','a'),('context','d')]
PRIMITIVES={
 'eisee':([('point','a'),('frame','a'),('lengthunit','a'),('timeunit','a'),('lower',R),('upper',R),('context','d')],'同じpointの位置と静止を論じるためにcontextで指定された、frame・長さ尺度・時間尺度と全対象期間であるという範囲規約。下限・上限は単なる任意の一瞬や静止して見える都合のよい標本ではなく、その設定で比較する非退化な全期間を指す。物質点の同一性と尺度を保持し、静止か否かを見てから期間を選ばない。履歴・静止の成立は別に要求する。'),
 'eisef':([('ruler','a'),('method','a'),('frame','a'),('unit','a'),('timeunit','a'),('lower',R),('upper',R),('context','d')],'rulerがmethodで長さを比較し移し取るために用いる目盛付きの物差しであり、frameの同じunitへ校正され、lowerからupperがその使用の全期間を覆うという対応。目盛の等しい差が同じ長さの差を表す尺度を定め、端点の一致・置き直し・必要な分割によって長さを比較する。数字を書いた任意の物体ではない。全期間の剛性はeigyで別に要求し、全ての物差しが同じ三次元形状や非共線三標識点を持つとは要求しない。'),
 'eiseg':([('record','a'),('point','a'),('frame','a'),('unit','a'),('context','d')],'recordが同じ物質点pointの位置をframeの原点と正規直交軸に対して記述する幾何記録である。成分0–2は点、3–5は原点の位置を一つの共通の補助Euclid空間表示とunitで表し、6–14は同じ表示での三単位軸、15–17はframeでの三つの符号付きCartesian座標を表す。補助表示の原点と回転は任意だが全成分で共通にし、物理的な点・原点・軸の対応と校正された長さを保持する。記録内の整合性は射影の式で別に確認する。測定前から点の座標を知っているという前提ではなく、可能な測定結果の物理的解釈を指定する。'),
 'eiseh':([('record','a'),('slot','b')],'同じ幾何記録のslotにある実数成分を返す。slotは0から17までの整数で、eisegの点・原点・三軸・出力三座標の順を保つ。それ以外の添字や未指定値を零で補わず未知として拒否する。返された切断の有効性や射影の整合性は別条件である。'),
 'eisei':([('method','a'),('point','a'),('frame','a'),('unit','a'),('record','a'),('context','d')],'methodの操作によって、同じframeの原点と軸に対するpointの位置を物差しで定め、結果をrecordとして得る。共通尺度での長さの比較・移し取り・分割と、直線・平行・直交のEuclid幾何学的作図を用い、原点から三直交軸方向への符号付き射影の長さから同じ点を再構成する。別々の点の測定値を混ぜず、位置決定と座標表現を同じ結果へ接続する。用いる物差しの全範囲はeisej、剛性と校正は別に確認する。この関係は操作が行われた設定での記述であり、現実での実施は可能性の引用から導かない。'),
 'eisej':([('ruler','a'),('method','a'),('context','d')],'rulerが同じmethodで用いる物差しの全範囲に属する。剛性や校正が確認できた道具だけを後から選ぶ標本ではない。一つの物差しを繰り返し用いる方法も許し、複数の物差しの現実の設置を必須にしない。使用道具があることと全道具の条件は別に合成する。'),
 'eisek':([('method','a'),('point','a'),('frame','a'),('unit','a'),('reference','d'),('setting','d')],'referenceの同じ静止物質点・frame・尺度と位置を保持した上で、methodによる位置決定を実行できる物理的・幾何学的に許容された設定settingである。理想的な剛体物差しと操作を用いる論説の記述尺度での実施可能性であり、無関係な世界で偶然同じ座標になることや単なる願望ではない。対象を移動・交換して測定容易な別位置へ変えること、隠れた単位変更を許さない。設定の許容性と、同じ方法が実際に位置決定の結果を与えることは別に要求する。現実に測定を行ったという主張ではない。'),
 'eisel':([], '固定原文einstein-1905:u0009の全一文。静止物質点の位置を剛体物差しとEuclid幾何学によって決定しCartesian座標で表せるという条件文の箇所。'),
}
MEANINGS={
 'eih6':'同じ物体の物質点としての対応、同じ系・尺度・全対象期間、既存seの完全な世界線履歴を要求し、区間内の全時刻対に三位置座標の一致を課す物質点の静止。空間点又は物体全体の静止で代用しない。',
 'eih7':'有効な点・原点・出力三座標と既存eiajの右手正規直交三軸について、三出力が点から原点への変位の各軸への射影eiamと値で一致する。共通のEuclid表示におけるCartesian座標の構成。負・零の座標も許す。',
 'eiia':'同じ物質点・系・文脈の対象期間と尺度及び三軌跡を保持したeih6の静止。全実数の区間履歴を存在量化して保持し、任意の一瞬や有限標本へ置き換えない。',
 'eiib':'同じ方法に使う同じ物差しについて、校正と全使用期間をeisefで指定し、その同じ系・尺度・期間の全成員履歴にeigyの剛性を要求する。',
 'eiic':'同じ点・系・長さ単位の幾何記録の物理的意味eisegと、全18成分におけるeih7の射影の整合性を結ぶ。数値の一致だけで別の対象の記録を代用しない。',
 'eiid':'同じ方法で同じ点の位置を決めて同じ幾何記録を得て、その記録のCartesian表現を確認する。使用する物差しが少なくとも一つあり、その全てに同じ方法・系・単位・文脈の剛性と校正eiibを要求する。',
 'eiie':'同じ点・系・尺度を保持する許容された実施設定があり、そこで同じ方法の位置決定とCartesian表現eiidが成り立つという可能性。参照点での実測済みを要求しない。',
 'eiif':'先行の同じ系raに対して静止する全物質点について、その同じ位置を物差しと幾何学で決めCartesian座標で表せるという条件内容。静止点が今ここに存在するという主張は追加しない。',
 'eiig':'全条件文eiifを主張するメッセージ。可能性を実際に測定した事実や命令へ替えない。',
 'eiih':'同じ著者・論説へeiigを帰属し、静止系の命名段落の後の別箇所として本文順序を保持する。',
}
LIMITS=[
 'materieller Punktは同じ物体を構成し履歴を通じ追跡する物質点又は点状の物体の理想化として読む。幾何学的な空間位置だけや物体全体の運動へ替えない。',
 '静止はこの記述で指定した全対象期間に同じ系で位置が変わらないこととする。対象期間を結果から恣意的に選ばず、端点だけの一致で途中の運動を隠さない。',
 'Euclid幾何学の方法は共通尺度の長さの比較・移し取り・分割と、直線・平行・直交による作図、三直交軸への射影と再構成として具体化する。一般の全幾何公理やLorentz変換の導出をこの一文の前提に加えない。',
 'Cartesian座標には任意に選んだ右手正規直交軸を使う規約を明示する。原文が唯一の向き・原点を指定したとせず、補助Euclid表示の原点・回転に依存して同じ点を変えない。',
 'kannは同じ静止点と位置・系・尺度を保持する許容設定で手順を実行できるという可能性と読む。測定済み、有限回で任意の実数を全桁算出する計算可能性、任意の現実の実機精度を要求しない。',
 '物理的な計測操作・校正・許容設定は意味規約を明示した入力である。幾何数値の局所検査を物理的な実測・全実数の列挙・同義性の自動証明に昇格させない。',
 'u0009の一文全体を記述する。次段落の運動の時間関数表示と時間・同時性の全説明は別に進める。',
]

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+(R if n=='eiseh' else 'a' if not fs else 'c')+'.\n' for n,(fs,_) in PRIMITIVES.items())
    membership=q('g','body','a',both(k('zm',v('body')),k('eirh',v('body'),v('point'),v('context'))))
    scope=k('eisee',*[v(n) for n in ('point','frame','lengthunit','timeunit','lower','upper','context')])
    equal=both(*(k('sca',app(v(a),v('first')),app(v(a),v('second'))) for a in ('x','y','z')))
    guard=both(k('lg',v('lower'),v('upper'),v('first')),k('lg',v('lower'),v('upper'),v('second')))
    text+=define('eih6',HISTORY,both(membership,scope,op('u',op('e',v('lengthunit'),v('timeunit'))),k('se',*[v(n) for n,_ in HISTORY]),q('f','first',R,q('f','second',R,op('y',guard,equal)))))
    valid=[k('ba',v(n)) for n,_ in GEOMETRY if n not in ENAMES]
    projections=[k('sca',v('c'+axis),k('eiam',*[v(n) for n in ('px','py','pz','ox','oy','oz',*(prefix+a for a in ('x','y','z')))])) for axis,prefix in zip(('x','y','z'),('u','v','w'))]
    text+=define('eih7',GEOMETRY,both(*valid,k('eiaj',*[v(n) for n in ENAMES]),*projections))
    body=k('eih6',*[v(n) for n,_ in HISTORY])
    for n,t in reversed(HISTORY[3:]):body=q('g',n,t,body)
    text+=define('eiia',HISTORY[:3],body)
    fields=[(n,t) for n,t in BODY if n not in ('body','frame','context','lengthunit')]
    rigid=k('eigy',*[v('ruler' if n=='body' else 'unit' if n=='lengthunit' else n) for n,_ in BODY])
    ruler=both(k('eisef',*[v(n) for n in ('ruler','method','frame','unit','timeunit','lower','upper','context')]),rigid)
    for n,t in reversed(fields):ruler=q('g',n,t,ruler)
    text+=define('eiib',USE,ruler)
    result=[('record','a'),('point','a'),('frame','a'),('unit','a'),('context','d')]
    text+=define('eiic',result,both(k('eiseg',*[v(n) for n,_ in result]),k('eih7',*[k('eiseh',v('record'),'n p '+number_word(i)+' b') for i in range(18)])))
    outcome=[('method','a'),('point','a'),('frame','a'),('unit','a'),('record','a'),('context','d')]
    selected=lambda r:k('eisej',r,v('method'),v('context'))
    text+=define('eiid',outcome,both(k('eisei',*[v(n) for n,_ in outcome]),k('eiic',*[v(n) for n,_ in result]),q('g','ruler','a',selected(v('ruler'))),q('f','ruler','a',op('y',selected(v('ruler')),k('eiib',*[v(n) for n,_ in USE])))))
    possible=both(k('eisek',*[v(n) for n in ('method','point','frame','unit','reference','setting')]),k('eiid',*[v(n) for n in ('method','point','frame','unit','record','setting')]))
    for n,t in reversed([('method','a'),('unit','a'),('record','a'),('setting','d')]):possible=q('g',n,t,possible)
    text+=define('eiie',[('point','a'),('frame','a'),('reference','d')],possible)
    text+=content('eiif',q('f','particle','a',op('y',k('eiia',v('particle'),k('ra'),v('point')),k('eiie',v('particle'),k('ra'),v('point')))))
    text+='d eiig[] f[j s[k eiif[]]].\n'
    text+=define('eiih',[],both(k('eir3',k('eisel'),k('rd'),k('eirf'),quote('eiig'),k('ri')),k('ue',k('eised'),k('eisel'),k('ri')),op('u',op('e',k('eised'),k('eisel')))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX;doc=deepcopy(old);doc['statements']=[]
    assert not(set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in doc['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='eiih',arguments=[]))]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='possible_ruler_based_cartesian_position_of_stationary_material_point',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=[],statement_indices=[INDEX]).document
    ann=json.loads(read('data/rest-frame-introduction-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
