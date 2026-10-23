"""Compose current simultaneous length and full-point signed vector translation."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_transverse_endpoint_claim import ROOT,read
from scripts.compose_material_relative_frame import define
from scripts.compose_material_body_motion import FIELDS
from scripts.compose_rod_methods import history,coords,interval
from scripts.compose_limits import R,v,call as k,app,op,both,quant as q

PARENT='examples/v014/einstein-transverse-endpoint-claim.noema';PARENT_BASIS='data/transverse-endpoint-claim-basis-v1.json'
FULL='examples/v014/einstein-transverse-measured-length.noema';CORE='examples/v014/transverse-measured-length-core.noema'
BASIS='data/transverse-measured-length-basis-v1.json';ANNOTATIONS='data/transverse-measured-length-identifiers-v1.json'
PAIR=[(n,'a') for n in ('body','low','high','firstevent','lastevent','firstrecord','lastrecord','frame')]+[('context','d'),('length',R)]
BASE=[(n,'a') for n in ('body','low','high','frame')]+[('context','d')]
VECTOR=[(n,R) for n in ('vx','vy','vz')]
MEANINGS={
 'ejcx':'同じ棒の指定長軸の全履歴eipcと、同じ系の現在両端記録ejceを結ぶ。二端の異なる出来事の時刻値を等しくし、その同じ時刻の同じ履歴の軸長eipaをlengthとする。正の長さ・校正された三次元距離を要求し、時刻の異なる二記録や符号付き一成分差を長さとみなさない。',
 'ejcy':'同じ棒・二端・系・文脈について、指定時刻にejcxの現在両端記録が存在し、その同時刻距離がlengthである。出来事と記録の四位置を別々に量化し、名前の一意性は要求しない。',
 'ejcz':'正の時間幅を持つ同じ系の対象区間の全実数時刻に、同じ棒の現在両端記録と同じ正の測定長ejcyが存在する。測定済み一時刻だけ又は空虚な全称へ縮めない。長さは同じ系の測定座標から得る同時刻距離。',
 'ejc2':'現在の正速度側の同じ横棒のejcf、両端の現在二系記録と一般式ejcj、Kでの全時刻の測定長ejczを結び、その正の長さが同じl/φ(v)であるとする条件。距離は絶対値だが原文の結論は符号付き商に等しいため、この条件は正の枝を選ぶ。端点式だけからこの等式を自動導出したとはしない。',
 'ejc3':'同じ物体の非空の完全な全物質点履歴と計量を保持し、全成員の全順方向時刻対で各成分の変位を同じ符号付き速度成分と経過時間の積へeiohで結ぶ。三成分の零・負・斜方向を許す一般の一定並進。端点だけやX方向だけに限定しない。',
 'ejc4':'同じ棒・二端・系・文脈の全履歴、同じ三成分の全点並進ejc3、全時刻の現在測定長ejczを保持する。各時刻の実際の端差ベクトルと速度ベクトルを非零直交eiu6へ結ぶ。速度零、潰れた軸、平行な運動を横運動としない。',
 'ejc5':'相異なる測定系と固有静止系で同じ棒・二端・単位を保ち、固有系の正の時間幅・全点静止・剛性・正の固有長eipeと、測定系での全点三成分並進・横運動・現在測定長ejc4を結ぶ。方向比較の一つの物理設定の条件であり、設定間の同一性・完全な比較範囲や長さの不変性はまだ主張しない。',
}
LIMITS=[
 'u0101の測定長と方向一般の対称性のための依存群。著者の結論・物理的意味の提示・対称性の理由・正負比較・oderの同値書換え・全文判断はまだ追加しない。既存318主張と102単位の判断を保持する。',
 '長さは同じ系の同時刻の両端を、現在の時計と位置測定の規約により定めた座標から得る正のユークリッド距離と読む。eipa/eisddが校正計量、ejce/eiyxが現在の測定と世界線・履歴を保持する。特定の観測者による物差しの操作をこの文へ新たに要求せず、原文が省略した実験の実施報告を補わない。',
 '同じ端標識を長軸へeipcで割り当て、その完全な履歴と実際の現在記録へ結ぶ。前段の縦棒xi専用のeiqg、又は未接続のza/shd/zgjの旧条件を流用しない。幾何学的標識を必ず物質点と同一とはしない。',
 '一般測定長ejcx/ejczは軸方向や符号を限定しない。前段の表示の二端差がl/φ(v)なら幾何学的距離はl/|φ(v)|。原文が測定長をl/φ(v)と述べるejc2は、その符号付き商が正の長さであるという追加の向きの読みを明示し、端点代数だけから正のφが証明できたことにしない。',
 'ejc3/ejc4は三成分の符号付き速度を用い、反転だけでなく斜方向の横運動も表す。方向を表すラベルではなく、全成員の履歴と各時刻の自軸との直交へ結ぶ。比較設定の全範囲を作る際は同じ棒・固有形状・尺度・速度の大きさを保ち、長さが等しくなる設定だけを選別しない。',
 '固有系と測定系の時刻・区間端を等置しない。ここでは各設定の物理条件までであり、設定間の同じ物質点・形状の対応や運動方向・向きへの不変性は後続の合成課題。',
 '有限評価は現在両端測定と距離の本体、量化の引数接続、明示した時刻での全物質点の並進と直交を対照する。全実数域・全物理履歴・全方向の実現を有限標本で証明せず、未知座標を零へ補わない。',
]

def definitions():
    body=v('body');low=v('low');high=v('high');frame=v('frame');ctx=v('context');length=v('length');time=v('time')
    first=v('firstrecord');last=v('lastrecord');stamp=k('zc6',first,k('zc7'))
    text=define('ejcx',PAIR,both(k('eipc',*history(body,frame,ctx),low,high),op('u',op('e',v('firstevent'),v('lastevent'))),k('ejce',body,low,v('firstevent'),first,frame,ctx),k('ejce',body,high,v('lastevent'),last,frame,ctx),k('sca',stamp,k('zc6',last,k('zc7'))),k('eipa',low,high,stamp,*coords(body,frame,ctx),length)))
    witness=both(k('ejcx',*[v(n) for n,_ in PAIR]),k('sca',stamp,time))
    for n in reversed(('firstevent','lastevent','firstrecord','lastrecord')):witness=q('g',n,'a',witness)
    text+=define('ejcy',BASE+[('time',R),('length',R)],both(k('ba',time),witness))
    text+=define('ejcz',BASE+[('length',R)],both(k('sbg',length),k('bg',*interval(frame,ctx)),q('f','time',R,op('y',k('lg',*interval(frame,ctx),time),k('ejcy',body,low,high,frame,ctx,time,length)))))
    zero=k('bb','n p a b');rod=k('zgu');ends=[k('zgv'),k('zgw')];proper=k('zgz');speed=k('zb7');phi=app(k('spc'),speed)
    text+=define('ejc2',[('context','d'),('length',R)],both(k('ejcf',ctx),k('ejcj',rod,ends[0],zero,ctx),k('ejcj',rod,ends[1],proper,ctx),k('ejcz',rod,*ends,k('ra'),ctx,length),k('sca',length,k('srx',proper,phi))))
    at=lambda axis,point,t:app(app(v(axis),point),t)
    point=v('point');start=v('start');end=v('end')
    guard=both(app(v('members'),point),k('lg',v('lower'),v('upper'),start),k('lg',v('lower'),v('upper'),end),k('bc',start,end))
    motion=op('y',guard,both(*(k('eioh',v(velocity),start,end,at(axis,point,start),at(axis,point,end)) for axis,velocity in zip(('x','y','z'),('vx','vy','vz')))))
    for n,t in reversed([('point','a'),('start',R),('end',R)]):motion=q('f',n,t,motion)
    text+=define('ejc3',FIELDS+VECTOR,both(k('eiad',*[v(n) for n,_ in FIELDS]),k('eisdd',frame,v('lengthunit'),v('timeunit'),ctx),k('bg',v('lower'),v('upper')),*(k('ba',v(n)) for n,_ in VECTOR),motion))
    delta=[k('bf',app(app(fn,high),time),app(app(fn,low),time)) for fn in coords(body,frame,ctx)]
    transverse=q('f','time',R,op('y',k('lg',*interval(frame,ctx),time),k('eiu6',*[v(n) for n,_ in VECTOR],*delta)))
    text+=define('ejc4',BASE+VECTOR+[('length',R)],both(k('eipc',*history(body,frame,ctx),low,high),k('ejc3',*history(body,frame,ctx),*[v(n) for n,_ in VECTOR]),k('ejcz',*[v(n) for n,_ in BASE],length),transverse))
    rest=v('restframe')
    text+=define('ejc5',BASE+[('restframe','a'),('proper',R)]+VECTOR+[('length',R)],both(op('u',op('e',frame,rest)),k('bg',*interval(rest,ctx)),k('eipe',*history(body,rest,ctx),low,high,v('proper')),k('ejc4',*[v(n) for n,_ in BASE+VECTOR],length)))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==318;doc=deepcopy(old);doc['statements']=[]
    assert not set(MEANINGS)&{d['name'] for d in old['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']
    added=doc['declarations'][len(old['declarations']):]
    basis=dict(status='current_measured_length_and_general_transverse_motion_dependencies',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[]).document
    ann=json.loads(read('data/transverse-endpoint-claim-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
