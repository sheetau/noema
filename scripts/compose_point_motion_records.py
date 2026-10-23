"""Bind a point's constant velocity to complete current coordinate histories."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_curve_earth_claim import ROOT,read
from scripts.compose_origin_clock_question import tracks
from scripts.compose_clock_transfer_records import stamp,sub,mul,eq
from scripts.compose_rod_methods import interval
from scripts.compose_solid_sphere_geometry import args,bind
from scripts.compose_material_relative_frame import define
from scripts.compose_relativity_conjecture import content
from scripts.compose_limits import R,v,call as k,app,op,both,quant as q

PARENT='examples/v014/einstein-curve-earth-claim.noema';PARENT_BASIS='data/curve-earth-claim-basis-v1.json'
FULL='examples/v014/einstein-point-motion-records.noema';CORE='examples/v014/point-motion-records-core.noema'
BASIS='data/point-motion-records-basis-v1.json';ANNOTATIONS='data/point-motion-records-identifiers-v1.json'
LOCAL=[(n,'a') for n in ('object','event','record','place','frame')]+[('context','d')]
VELOCITY=[('object','a'),('frame','a')]+[(n,R) for n in ('vx','vy','vz')]+[('context','d')]
PLANAR=[('object','a'),('frame','a'),('longitudinal',R),('transverse',R),('context','d')]
MEANINGS={
 'ejms':'同じ運動対象の同じ出来事・四座標記録・場所・系・文脈に、現在の物差しと局所時計の付与eiywと世界線の帰属sbを結ぶ。代表位置の三関数を同じ記録時刻で評価し、全対象期間内の記録の三座標と一致させる。',
 'ejmt':'同じ対象・系・実時刻についてejmsの同じ出来事・記録・場所が存在する。時刻と場所を別々の証人から取らず、指定時刻をその記録の時刻へ一致させる。',
 'ejmu':'同じ対象・系・校正尺度・正の全期間について、代表位置の完全なse履歴を保持する。現在の世界線出来事の全記録候補をejmsへ接続し、全実時刻にejmtの現在記録を要求する。点の運動は同じ対象位置を一つの三座標の世界線として追う運動学的理想化であり、質量や物質種を指定しない。',
 'ejmv':'ejmuの完全な現在履歴について、同じ三つの有効な実速度成分を全実時刻で共有し、下端からの三位置の変化が成分と経過時間の積に一致する。初期位置は任意で、各成分は負・零・正を許し、対象の速度上限を加えない。',
 'ejmw':'同じ対象のejmvによる縦・横・零の三定速度と、全期間の下端における既存syrの三式を結ぶ。これにより全時刻でξ=wξτ、η=wητ、ζ=0となる。原点を通る位置定数を省かず、下端時刻を零に固定しない。',
 'ejmx':'既出の同じK/kの全原点・軸・物差し・時計配置と正X並進eivzに、同じ点zkbがkで二定数zkc/zkdによる平面運動ejmwをする設定を結ぶ。系の速度vと点の二速度成分を取り違えず、§3の対象と規約を継承する。',
 'ejmy':'§5冒頭の同じ点の平面運動を、既出のK/kの現在の比較状況zb6で指定する内容。旧zkeの独立した部分設定を現在の座標規約へ接続せずに採用することはしない。本文の仮定採用と記号説明の発話は後続。',
 'ejmz':'同じ対象の同じ系・期間における現在記録の全範囲。ejmsを満たす同じ出来事と場所の存在を要求する。方程式が成立した記録だけを選ばず、後続の運動方程式の問いや速度合成へ渡す。',
}
LIMITS=[
 '原刊905頁のu0130–u0132を一つの設定文として計画する。系kがKのX方向へ既出の一定速度vで動き、点のk座標はξ=wξτ、η=wητ、ζ=0、wξとwηは定数である。今回はその完全な現在履歴と三成分の依存群で、見出しu0129と仮定提示・記号説明・全単位判断は未完。',
 'Punktは同じ位置対象を各時刻に一つの三座標で追う運動学的な点として読む。世界線への出来事の帰属、座標の一意性、全実時刻の存在、現在の物差しと局所時計の付与を合成する。電荷・質量・微視的な物質種や、拡がる物体の内部全点の運動は追加しない。',
 '一般の定速度ejmvは任意の初期位置と符号付きの三成分を許す。原文の原点を通る平面の三式はejmwで別に課す。同じ成分を全時刻に用い、点の静止という退化例や光速以上の成分値を先回りして除外しない。',
 'K/kは§3と同じ比較設定zb6・尺度ta/rbへ接続する。Kとkの時刻値や同時刻面を等置しない。längs der X-Achseは既出の正X方向の全配置の等速並進として読み、新たな原点の再設定や追加の時計同期操作を導入しない。',
 '全期間は各系のeisls/eisltによる正の対象期間であり、動く点が都合よく等速に見える標本だけを取らない。代表位置seと現在記録の存在は区別し、全実数量化を有限の記録一覧へ置き換えない。',
 '一般の速度成分は位置差と時間差の比例として構成する。前後で異なる成分値を選ぶこと、端点だけで一致する寄り道、別の対象・系・単位・記録時刻の混合を対照検査する。有限検査は連続体上の全称や微分の一般証明ではない。',
 '旧数値核syr、現在の測定eiyw、全位置se、系の配置eivzをそのまま再利用し、新規基本記号は追加しない。u0133以降の課題提示・座標変換の適用・結果の運動式は後続に残す。',
]

def definitions():
    obj=v('object');ev=v('event');rec=v('record');pl=v('place');frame=v('frame');ctx=v('context');t=stamp(rec);lo,hi=interval(frame,ctx);fs=tracks(obj,frame,ctx);at=lambda time:[app(f,time) for f in fs]
    current=both(k('zzbv',obj,ev,ctx),k('eiyw',ev,rec,pl,frame,ctx),k('lg',lo,hi,t))
    text=define('ejms',LOCAL,both(current,k('sb',obj,ev,frame,ctx,k('ta'),k('rb'),t,*at(t)),*(eq(k('zc6',rec,k(a)),x) for a,x in zip(('yn','yo','yp'),at(t)))))
    text+=define('ejmt',[('object','a'),('frame','a'),('time',R),('context','d')],both(k('ba',v('time')),bind(('event','record','place'),'a','g',both(k('ejms',*args(LOCAL)),eq(t,v('time'))))))
    every=bind(('event','record','place'),'a','f',op('y',current,k('ejms',*args(LOCAL))))
    coverage=q('f','time',R,op('y',k('lg',lo,hi,v('time')),k('ejmt',obj,frame,v('time'),ctx)))
    text+=define('ejmu',[('object','a'),('frame','a'),('context','d')],both(k('eisdd',frame,k('ta'),k('rb'),ctx),k('bg',lo,hi),k('se',obj,frame,ctx,k('ta'),k('rb'),lo,hi,*fs),every,coverage))
    time=v('time');components=[v('v'+a) for a in ('x','y','z')]
    affine=both(*(eq(x,k('bd',base,mul(velocity,sub(time,lo)))) for x,base,velocity in zip(at(time),at(lo),components)))
    text+=define('ejmv',VELOCITY,both(k('ejmu',obj,frame,ctx),*(k('ba',x) for x in components),q('f','time',R,op('y',k('lg',lo,hi,time),affine))))
    u=v('longitudinal');w=v('transverse');zero=k('bb','n p a b')
    text+=define('ejmw',PLANAR,both(k('ejmv',obj,frame,u,w,zero,ctx),k('syr',u,w,*at(lo),lo)))
    text+=define('ejmx',[('context','d')],both(k('eivz',ctx),k('ejmw',k('zkb'),k('zbm'),k('zkc'),k('zkd'),ctx)))
    text+=content('ejmy',k('ejmx',k('zb6')))
    text+=define('ejmz',[('object','a'),('record','a'),('frame','a'),('context','d')],bind(('event','place'),'a','g',k('ejms',*args(LOCAL))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==350;doc=deepcopy(old);doc['statements']=[]
    assert not set(MEANINGS)&{d['name'] for d in old['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements'];added=doc['declarations'][len(old['declarations']):]
    basis=dict(status='complete_current_point_motion_and_planar_constant_components_dependency',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[]).document
    ann=json.loads(read('data/curve-earth-claim-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
