"""Bind spatial affine rows to current rays and an actual moving-origin event."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_transverse_ray_claim import ROOT,read
from scripts.compose_homogeneous_coordinates import MATRIX,VECTOR
from scripts.compose_comoving_labels import TAU
from scripts.compose_material_relative_frame import define
from scripts.compose_material_axes import interval
from scripts.compose_limits import R,v,call as k,app,op,both,quant as q

PARENT='examples/v014/einstein-transverse-ray-claim.noema';PARENT_BASIS='data/transverse-ray-claim-basis-v1.json'
FULL='examples/v014/einstein-spatial-affine-calibration.noema';CORE='examples/v014/spatial-affine-calibration-core.noema'
BASIS='data/spatial-affine-calibration-basis-v1.json';ANNOTATIONS='data/spatial-affine-calibration-identifiers-v1.json';INDEX=300
MEANINGS={
 'ei6y':'空間三役割のいずれかについて、一つの行列の同じ役割行と定数ベクトルの同じ成分を取り出し、候補関数を全有効実数四入力でそのアフィン式smdへ結ぶ。係数を入力ごとに選び直さず、時間役割を空間行として扱わない。',
 'ei6z':'同じ現在変換のアフィン条件eizfと全入力延長ei6yを保持し、全現在座標対の同じ出来事対応eiyyについて候補関数の値がkの指定空間成分に一致することを要求する。測定範囲と全実数延長を区別する。',
 'ei62':'一つの対象出来事に現在のK/k両四座標eiyxを結び、指定空間候補のK四入力での値を同じk座標成分へ一致させる。具体的な光線や原点の端点を、同じ行列行の候補関数へ接続する。',
 'ei63':'同じk原点の零点出来事と、後の正のK時刻にある原点の対象出来事を現在の両座標へ結ぶ。原点の全k静止・K並進eizm、零から当該時刻までの全一次軌道と出会い、現在の代表軌道、Kでの(v*t,0,0)、kでの三座標零を保持する。任意の単位時刻に出来事があるとは要求しない。',
 'ei64':'同じ空間候補の値を、零点、正の原点時刻、独立した正の三光線到達時刻の五点へ結ぶ数値的較正条件。光のK座標は(V*T,0,0,T)、(v*T,w*T,0,T)、(v*T,0,w*T,T)であり、対応するk成分は同じa,V,vの縦・横式である。五点一致だけではアフィン性を意味しない。',
 'ei65':'現在の縦光線ei5y、両横光線ei6eと同じ原点出来事ei63を、一つの現在アフィン行列・定数ベクトルへ結ぶ。各空間候補zfhはその同じ行の全入力延長と全現在対応を満たし、実際の五出来事の測定と、各々の正の到達時刻を使うei64の五点条件を満たす。',
 'ei66':'同じ現在設定について、全測定範囲と三本の光線に共通する行列・定数ベクトル、および正時刻の原点出来事が存在してei65を満たすという追加の十分条件。一般四式を述べる著者の推論への解釈前提であり、原文が全条件を逐一述べたとはしない。',
}
LIMITS=[
 'u0081–u0084の全座標式へ進むための依存群。著者主張と全単位意味判断をまだ増やさず、係数の再表示、四式・βの提示と原刊との全文判断を次の統合へ残す。',
 '先行のlinearの読みを保持し、空間三候補を同じ現在eizfの行列行・定数成分によるアフィン式で全実数入力へ延長する。未測定の全四組が現実の出来事として実現するとは要求しない。',
 '三本の光線だけでは空間アフィン行を決められないため、同じk原点が後の正時刻にも空間ラベル零を持つ条件を明示する。原点は同じ全履歴eizm、現在eiyxと実際の出会いへ結び、別の点や単に数値を補った出来事へ交換しない。',
 '原点の時刻と各光線の到達時刻は独立な正値であり、1にも同じ時刻にも固定しない。原点の実際の時刻は現在のK運動区間内に置く。原文に明記されない測定選択と五点の十分性は解釈上の追加条件として記録する。',
 '五点の候補関数値は、実際の両系測定と数値較正の双方へ同じ関数を渡して結ぶ。五点で合う非線形関数を排除する役割は別の全入力アフィン条件ei6yに持たせる。',
 '同じa=zeq(v)を使い、縦光線のξと横光線のη/ζを流用せず、Kの各到達時刻と対応する座標を使う。後段φ=spcへの再表示は別であり、a=1を先取りしない。',
 '全入力量化・関数の存在量化は有限評価を拒否する。有限の関数指紋・有理数の較正補題と現在依存の結合検査は、一般実数体の定理や物理的導出・原文との同義性の自動証明ではない。旧判断・定義・証拠を保存する。',
]
SPATIAL=('yn','yo','yp')
ROLES=(*SPATIAL,'zc7')
CALIBRATION=[('function',TAU),('role','a')]+[(n,R) for n in ('light','speed','scale','origintime','xtime','ytime','ztime')]

def selected(role):return op('x',op('e',role,k('yn')),k('soa',role))

def definitions():
    fn=v('function');role=v('role');matrix=v('matrix');offset=v('offset');zero=k('bb','n p a b');ctx=v('context')
    coefficients=[app(matrix,role,k(a)) for a in ROLES]+[app(offset,role)]
    fields=[('function',TAU),('role','a'),('matrix',MATRIX),('offset',VECTOR)]
    text=define('ei6y',fields,both(selected(role),*(k('ba',x) for x in coefficients),k('smd',fn,*coefficients)))
    first=v('first');second=v('second');args=[k('zc6',first,k(a)) for a in ROLES]
    result=app(fn,*args)
    correspondence=q('f','first','a',q('f','second','a',op('y',k('eiyy',first,second),both(k('ba',result),k('sca',result,k('zc6',second,role))))))
    text+=define('ei6z',fields,both(k('eizf',matrix,offset),k('ei6y',fn,role,matrix,offset),correspondence))
    event=v('event');K=k('ra');ks=k('zbm');first=k('zdz',event,K,ctx);second=k('zdz',event,ks,ctx)
    args=[k('zc6',first,k(a)) for a in ROLES];result=app(fn,*args)
    text+=define('ei62',[('function',TAU),('role','a'),('event','a'),('context','d')],both(selected(role),k('zc4',event),k('eiyx',event,first,K,ctx),k('eiyx',event,second,ks,ctx),*(k('ba',x) for x in args),k('ba',result),k('ba',k('zc6',second,role)),k('sca',result,k('zc6',second,role))))
    depart=v('depart');origin=k('zbn',ks,ctx);speed=k('zb7');time=k('snd',event,K,k('zc7'),ctx);lu=k('ta');tu=k('rb')
    tracks=[k('eismh',origin,K,lu,tu,k(a),ctx) for a in SPATIAL]
    rows=[k('eivx',ctx),k('zbv',ks,origin,ctx),k('eizm',origin,ctx),k('ei46',depart,k('zdz',depart,K,ctx),k('zdz',depart,ks,ctx),ctx),k('zc4',event),op('u',op('e',depart,event)),k('eiyx',event,first,K,ctx),k('eiyx',event,second,ks,ctx),k('cb',event,origin,ks),k('sbg',time),k('lg',*interval(K,ctx),zero),k('lg',*interval(K,ctx),time)]
    position=[k('shv',speed,time),zero,zero]
    rows += [k('sca',k('zc6',first,k(a)),x) for a,x in zip(SPATIAL,position)]
    rows += [k('sca',k('zc6',second,k(a)),zero) for a in SPATIAL]
    rows += [k('eitf',origin,K,ctx,lu,tu,zero,time,zero,zero,zero,speed,zero,zero),k('sb',origin,depart,K,ctx,lu,tu,zero,zero,zero,zero),k('sb',origin,event,K,ctx,lu,tu,time,*position)]
    rows += [k('sca',app(f,zero),zero) for f in tracks]
    rows += [k('sca',app(f,time),x) for f,x in zip(tracks,position)]
    text+=define('ei63',[('depart','a'),('event','a'),('context','d')],both(*rows))
    V=v('light');speed=v('speed');a=v('scale');w=k('sle',V,speed)
    times=[v(n) for n in ('origintime','xtime','ytime','ztime')];to,tx,ty,tz=times
    points=[(zero,zero,zero,zero),(k('shv',speed,to),zero,zero,to),(k('shv',V,tx),zero,zero,tx),(k('shv',speed,ty),k('shv',w,ty),zero,ty),(k('shv',speed,tz),zero,k('shv',w,tz),tz)]
    values=[app(fn,*p) for p in points]
    expected=[k('snb',V,speed,a,k('shv',k('sna',V,speed),tx)),k('shv',a,k('shv',V,ty)),k('shv',a,k('shv',V,tz))]
    rows=[selected(role),k('skz',V,speed,w),k('ba',a),*(k('sbg',t) for t in times),*(k('ba',x) for x in values),k('sca',values[0],zero),k('sca',values[1],zero)]
    for axis,value,target in zip(SPATIAL,values[2:],expected):
        rows += [op('y',op('e',role,k(axis)),k('sca',value,target)),op('y',op('u',op('e',role,k(axis))),k('sca',value,zero))]
    text+=define('ei64',CALIBRATION,both(*rows))
    origin_event=v('originevent');ctx=k('zb6');depart=k('wi',k('zey'));ends=[k('wj',k('zey')),k('wj',k('zfb',k('yo'))),k('wj',k('zfb',k('yp')))]
    rows=[k('eizf',matrix,offset),k('ei5y',k('zez'),k('zey'),ctx),k('ei6e',k('yo'),ctx),k('ei6e',k('yp'),ctx),k('ei63',depart,origin_event,ctx)]
    times=[k('snd',e,K,k('zc7'),ctx) for e in (origin_event,*ends)]
    for axis in SPATIAL:
        fn=k('zfh',k(axis));rows.append(k('ei6z',fn,k(axis),matrix,offset))
        rows += [k('ei62',fn,k(axis),e,ctx) for e in (depart,origin_event,*ends)]
        rows.append(k('ei64',fn,k(axis),k('tc'),k('zb7'),app(k('zeq'),k('zb7')),*times))
    text+=define('ei65',[('matrix',MATRIX),('offset',VECTOR),('originevent','a')],both(*rows))
    body=k('ei65',matrix,offset,origin_event)
    for n,t in reversed([('matrix',MATRIX),('offset',VECTOR),('originevent','a')]):body=q('g',n,t,body)
    text+='d ei66[] e[b point['+body+']].\n'
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX;doc=deepcopy(old);doc['statements']=[]
    assert not set(MEANINGS)&{d['name'] for d in old['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']
    added=doc['declarations'][len(old['declarations']):]
    basis=dict(status='current_spatial_affine_rows_and_actual_ray_calibration',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[]).document
    ann=json.loads(read('data/transverse-ray-claim-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
