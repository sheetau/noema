"""Bind the same light law to each frame's current clocks and selected events."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_affine_time_claim import ROOT,read
from scripts.compose_material_relative_frame import define
from scripts.compose_limits import R,v,call as k,op,both,quant as q

PARENT='examples/v014/einstein-affine-time-claim.noema';PARENT_BASIS='data/affine-time-claim-basis-v1.json'
FULL='examples/v014/einstein-frame-light-law.noema';CORE='examples/v014/frame-light-law-core.noema'
BASIS='data/frame-light-law-basis-v1.json';ANNOTATIONS='data/frame-light-law-identifiers-v1.json';INDEX=289
MEANINGS={
 'ei42':'指定系の同じ光区間について、放出元の静止又は運動の排他的分類と、両端の現在の局所時計表示・一意な出来事時刻・系内時点を結ぶ。K専用の参照時計や時刻取得を運動系へ流用しない。',
 'ei43':'指定系の全真空光区間に同じ一つの速度を与える既存eifxと、同じ系の現在の全配備時計網eiyfを結ぶ。全選択区間でei42を要求し、非空の完全な全区間範囲と幾何学的光路長を保持する。',
 'ei44':'選択した同じ光・始終出来事・幾何学的光路長を、指定系の光速度適用範囲とその系の参照時計によるeifw、現在の局所表示ei42、両端の現在四座標eiyxへ結ぶ。単独の選択区間だけで全体法則を代用しない。',
 'ei45':'Kとkの異なる二記録が同じ光・放出元・放出出来事・始終出来事を測ることを保持し、各系の別の局所時計・光路長・現在四座標へ結ぶ。両系の全区間法則ei43に同じVを渡し、同じτの全対応と全k指示ei3cを保つ。両系の時刻値や光路長の数値一致は要求しない。',
}
LIMITS=[
 'u0065–u0068の現在の本文接続に必要な全区間光速度と二系の測定の依存群。著者主張と全単位判断は増やさない。二原理からの帰属、求め方の容易さ、正のξ方向の全軌道と原点放出、二表示式の本文接続は残る。',
 'eifw/eifxの同じ光・源・放出・真空・幾何学的弧長・単位校正・非空の全適用区間を再利用する。光源の運動と時計の静止を交換せず、同じ源がKでは静止・kでは運動と分類されることを許す。',
 '各系のzbhと現在eiyf/eiyg/eiyi/eiyjを使う。K専用のrc、eing、sjhをkへ流用しない。Kへ戻す場合も以前のeiosとの無条件の論理同値は主張せず、現在の時計網への追加接続を明示する。',
 '速度の一般引数を持つei43/ei44と、同じV=tcを両系へ渡すei45を区別する。相対速度V-vをkで測る光速へ置き換えず、同じ出来事の二系の時刻や距離の数値を等置しない。',
 'ei42は全適用区間の時刻を、ei44は選択区間両端の現在四座標を結ぶ。全宇宙の全光出来事に現在の座標記録が実際に存在すると追加しない。測定範囲と条件の完全性は明示した入力に従う。',
 'ei45は同じ伝播を二系で記録する条件であり、共通原点からの放出や正の縦軸方向、全軌道の速度成分、ξ=Vτをまだ含めない。光線上の式を一般座標変換に拡張する根拠にも使わない。',
 '有限検査は同じ参照先・全区間範囲・個別の数値・現在の局所時計への接続を調べる。全物理的モデルの実現や二原理からの一般的導出の自動証明ではない。新規原始語は追加せず、旧判断と証拠を保存する。',
]

def definitions():
    seg=v('segment');frame=v('frame');ctx=v('context');speed=v('speed');at=lambda n:k(n,seg)
    rows=[k('saz',at('wf'),at('wg'),at('wh'),frame,ctx,'p wb','p wc','p wd','p we')]
    for e,cl,pl,val in (('wi','wk','wm','wo'),('wj','wl','wn','wp')):
        rows += [k('eiyg',at(e),at(cl),at(pl),frame,at(val),ctx),k('eiyi',at(e),at(pl),frame,ctx),k('eiyj',at(e),frame,ctx),k('sca',at(val),k('zbe',at(e),frame,k('rb'),ctx))]
    text=define('ei42',[('segment','a'),('frame','a'),('context','d')],both(*rows))
    selected=k('eiscd',seg,frame,k('ta'),k('rb'),ctx)
    text+=define('ei43',[('frame','a'),('speed',R),('context','d')],both(k('eifx',frame,speed,ctx),k('eiyf',frame,ctx),q('f','segment','a',op('y',selected,k('ei42',seg,frame,ctx)))))
    rows=[selected,k('eifw',seg,frame,k('zbh',frame,ctx),speed,ctx),k('ei42',seg,frame,ctx),op('e',at('wf'),v('ray')),op('e',at('wi'),v('first')),op('e',at('wj'),v('last')),k('ba',v('path')),k('sca',at('wq'),v('path'))]
    for e,val in (('first','wo'),('last','wp')):
        tup=k('zdz',v(e),frame,ctx)
        rows += [k('eiyx',v(e),tup,frame,ctx),k('sca',at(val),k('zc6',tup,k('zc7')))]
    fields=[(n,'a') for n in ('segment','ray','first','last')]+[('path',R),('frame','a'),('speed',R),('context','d')]
    text+=define('ei44',fields,both(*rows))
    a=v('rest');b=v('moving');rows=[op('u',op('e',a,b)),op('u',op('e',k('ra'),k('zbm'))),k('ei3c',k('zd4'),ctx)]
    rows += [op('e',k(n,a),k(n,b)) for n in ('wf','wg','wh','wi','wj')]
    for s,f in ((a,k('ra')),(b,k('zbm'))):
        rows += [k('ei43',f,k('tc'),ctx),k('ei44',s,k('wf',b),k('wi',b),k('wj',b),k('wq',s),f,k('tc'),ctx)]
    text+=define('ei45',[('rest','a'),('moving','a'),('context','d')],both(*rows))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX;doc=deepcopy(old);doc['statements']=[]
    assert not set(MEANINGS)&{d['name'] for d in old['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']
    added=doc['declarations'][len(old['declarations']):]
    basis=dict(status='current_frame_light_law_dependency',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[]).document
    ann=json.loads(read('data/affine-time-claim-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
