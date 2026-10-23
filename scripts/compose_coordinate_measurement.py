"""Bind signed coordinates to one calibrated ruler and its actual procedure."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_axis_projection import ROOT,read,PHYSICAL,args
from scripts.compose_material_relative_frame import define
from scripts.compose_rod_methods import history,interval
from scripts.compose_limits import R,v,call as k,op,both,quant as q

PARENT='examples/v014/einstein-axis-projection.noema';PARENT_BASIS='data/axis-projection-basis-v1.json'
FULL='examples/v014/einstein-coordinate-measurement.noema';CORE='examples/v014/coordinate-measurement-core.noema'
BASIS='data/coordinate-measurement-basis-v1.json';ANNOTATIONS='data/coordinate-measurement-identifiers-v1.json'
PROCEDURE=[(n,'a') for n in ('observer','method','first','last','frame','unit')]+[('length',R),('context','d')]
USE=[(n,'a') for n in ('ruler','method','frame')]+[('context','d')]
READING=[(n,'a') for n in ('observer','method','ruler','first','last','frame')]+[('length',R),('context','d')]
MEASURE=PHYSICAL+[(n,'a') for n in ('observer','method','ruler')]+[('value',R),('length',R)]
SPECIFIC=PHYSICAL+[(n,'a') for n in ('observer','method')]+[('value',R),('length',R)]
CANDIDATE=[('place','a'),('frame','a'),('role','a'),('value',R),('context','d')]
PRIMITIVES={
 'eisnc':(PROCEDURE,'observerがmethodの長さ比較・移し取り・必要な分割という操作を同じcontextで実行し、同じframeのfirstとlastの距離をunitでlengthとして得る。単なる数値候補、校正済みの方法が存在するだけの状態、別の方法の結果と区別する。使う物差しの全範囲は既存eisejで指定し、個々の道具の校正・剛性・配置・同じ物差しによる読取りxh及び幾何学的距離は合成側で要求する。始点と終点が同じ位置の場合の零距離も含む。'),
}
MEANINGS={
 'eixc':'有効な非負の距離lengthと有効な符号付き値valueの平方が等しい。絶対値を新演算にせず、正・負・零の座標を同じ非負距離へ結ぶ。',
 'eixd':'指定の物差しを同じ方法で使う唯一の道具とし、全道具範囲eisejを個体一致の双条件で限定する。型・系・単位・正の使用区間、同じ全成員履歴の静止と剛性、同じ方法・系・単位・期間での校正eisefを要求する。静止期間はこの測定配置の期間である。',
 'eixe':'同じ観測者・方法・物差し・二地点・系・単位・非負距離について、方法の実行eisnc、同じ道具による読取りxh、空間距離th、eixdの校正と物理履歴を結ぶ。校正可能性や幾何数値の一致だけで実測を認定しない。',
 'eixf':'同じ軸・原点・方向標識・対象地点・射影点・系・役割の全期間の符号付き距離eixbを、同じ原点から同じ射影点へのeixeの実測とeixcの絶対値へ結ぶ。原点に射影される点も扱い、測定距離を負値にしない。',
 'eixg':'eixfへその系に与えた同じ物差しを渡し、物差しの配備zbxと初期個体の同一性、現在と初期の同じ原点・同じ役割の軸、現行の方向標識を要求する。別の道具や別の役割で同じ数値を得ても代用しない。',
 'eixh':'同じ地点・系・役割・有効な符号付き値について、射影点、観測者、方法、非負距離が存在しeixgを満たす。射影候補zcvの一つに限定せず、物理的射影と実測を満たす全候補を認める。',
 'eixi':'zcyで選ぶ同じ地点・系・役割・長さ単位の座標がeixhを満たし、あらゆるeixhの実数値候補と値が一致する。測定方法・観測者・射影点の個体同一性を要求せず、異なる値の候補を隠さない。',
}
LIMITS=[
 'u0045第一文の測定依存群であり、270本文主張と既存の判断を維持する。全空間・全三成分・両系の思考設定、時計配置点の時刻設定とu0045全体の意味判断は次に接続する。',
 'このcontextは一つの静止した測定配置の全期間である。物差しの再配置を含む全操作期間や全空間測定の全期間に一つのeipwを要求する定義として使わない。次の統合では、同じ空間配置・対象・軸・尺度を保持する測定配置ごとの文脈を結ぶ必要がある。',
 '方法の実行と道具の範囲を新しい一般的関係eisncと既存eisejで接続する。校正した任意の方法を、別の方法によるxh読取りの説明に流用しない。新関係は全文の真偽・三成分の存在・一意性を一入力に隠さない。',
 '理想的に校正された物差しとEuclid幾何の長さ比較として読む。任意の実数を有限回で全桁計算できることや現実の機器の無限精度を要求しない。実際の測定操作は意味規約付き入力で、有限検査を実測証拠とはしない。',
 '射影点は物差し又は軸の物質成員に限定しない。軸の支持直線上の幾何点として前段eixbで確認する。零値は非負距離へ含み、符号は全正方向記録と実座標から決める。',
 '原文の同じ初期計器を維持するが、初期と運動後の長さ値、両系の座標値、両系の正方向が同一であることは加えない。全候補の一意性は値に関する条件であり、各測定手順が唯一であるとはしない。',
 '存在量化の結合は小さい有限域で各位置を識別し、実数量化の本体を別に検査する。完全履歴と全実数候補は有限評価を拒否し、未知の入力を偽又は零に補わない。',
]

def definitions():
    text='r eisnc['+' '.join(t for _,t in PROCEDURE)+'] c.\n'
    zero=k('bb','n p a b');length=v('length');value=v('value');c=v('context');f=v('frame');r=v('ruler');method=v('method')
    text+=define('eixc',[('length',R),('value',R)],both(k('ba',length),k('ba',value),k('bc',zero,length),k('sca',k('shv',length,length),k('shv',value,value))))
    exact=q('f','tool','a',op('z',k('eisej',v('tool'),method,c),op('e',v('tool'),r)))
    text+=define('eixd',USE,both(k('xc',r),k('va',f),k('ti',k('ta')),k('ci',k('rb')),k('bg',*interval(f,c)),k('eisej',r,method,c),exact,k('eipw',r,f,c),k('eigy',*history(r,f,c)),k('eisef',r,method,f,k('ta'),k('rb'),*interval(f,c),c)))
    reading=[v(n) for n in ('observer','ruler','first','last','frame')]+[k('ta'),length,c]
    procedure=[v(n) for n in ('observer','method','first','last','frame')]+[k('ta'),length,c]
    text+=define('eixe',READING,both(k('xb',v('observer')),k('eixd',r,method,f,c),k('ba',length),k('bc',zero,length),k('eisnc',*procedure),k('xh',*reading),k('th',v('first'),v('last'),f,k('ta'),length)))
    text+=define('eixf',MEASURE,both(k('eixb',*args(PHYSICAL),value),k('eixc',length,value),k('eixe',v('observer'),method,r,v('origin'),v('projection'),f,length,c)))
    ruler=k('zby',f,c);origin=k('zbn',f,c);axis=k('zbo',f,v('role'),c)
    text+=define('eixg',SPECIFIC,both(k('eixf',*args(PHYSICAL),v('observer'),method,ruler,value,length),k('zbx',f,ruler,c),op('e',ruler,k('zby',f,k('zb4'))),op('e',v('origin'),origin),op('e',origin,k('zbn',f,k('zb4'))),op('e',v('axis'),axis),op('e',axis,k('zbo',f,v('role'),k('zb4'))),op('e',v('guide'),k('eismu',axis,f,c))))
    supplied=[axis,origin,k('eismu',axis,f,c),v('place'),v('projection'),f,v('role'),c,v('observer'),method,value,length]
    body=k('eixg',*supplied)
    for n,t in reversed([('projection','a'),('observer','a'),('method','a'),('length',R)]):body=q('g',n,t,body)
    text+=define('eixh',CANDIDATE,both(k('ba',value),body))
    selected=k('zcy',v('place'),f,v('role'),k('ta'),c)
    text+=define('eixi',[(n,t) for n,t in CANDIDATE if n!='value'],both(k('eixh',v('place'),f,v('role'),selected,c),q('f','value',R,op('y',k('eixh',*args(CANDIDATE)),k('sca',value,selected)))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==270;doc=deepcopy(old);doc['statements']=[]
    assert not (set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in old['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='calibrated_signed_coordinate_measurement_dependency',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[]).document
    ann=json.loads(read('data/axis-projection-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
