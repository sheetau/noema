"""Bind a positive longitudinal ray to the same origin and full two-frame paths."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_frame_light_law import ROOT,read
from scripts.compose_material_relative_frame import define
from scripts.compose_limits import v,call as k,op,both

PARENT='examples/v014/einstein-frame-light-law.noema';PARENT_BASIS='data/frame-light-law-basis-v1.json'
FULL='examples/v014/einstein-origin-light-ray.noema';CORE='examples/v014/origin-light-ray-core.noema'
BASIS='data/origin-light-ray-basis-v1.json';ANNOTATIONS='data/origin-light-ray-identifiers-v1.json';INDEX=289
MEANINGS={
 'ei46':'現在の同じk原点出来事の両時刻零とK補助三座標零ei4kを保持し、その同じk四座標組の三空間ラベルも零にする。前段の時刻原点と別の空間原点選択を、この光線の出発出来事へ結ぶ。',
 'ei47':'指定系で同じ光が時刻零・空間原点から正の縦方向へ進む非退化な一区間。現在の局所時計・両端四座標・幾何学的光路長ei44を保ち、放出が同じ始出来事であること、正の終時刻と縦座標、横成分零、軸に沿う全経路、全区間の一定速度Vの三軌道eitfと両端の出会いsbを結ぶ。',
 'ei5a':'K/kの同じ光・源・放出・始終出来事を測る現在の二記録ei45に、同じ原点規約ei4lとその始出来事ei46、両系の全縦光軌道ei47、両端での同じτの表示対応snfと未定φ(v)の全時間式smjを結ぶ。両系の時刻と距離の数値は異なってよい。',
}
LIMITS=[
 'u0065–u0068の正のξ方向へ放出する光と二つの表示式を現在の本文へ接続する物理依存群。著者主張と全文判断は増やさない。二原理の適用、容易さ、二式の帰結と書換えの帰属は残る。',
 '原文u0065はτ=0で正のξ方向への放出を指定する。ξ=Vτと直前の原点規約を合わせ、同じk原点からの放出として読む。これは単独の時刻条件だけから全空間零が従うという主張ではなく、この光線に使う原点の選択である。',
 '前段ei4lと同じ現在二座標組を用い、ei46でその始出来事のk空間ラベルを零に合わせる。両系の原点が全時刻で一致することや、一般のt=τを追加しない。',
 '各系で正の縦軸上を進む同じ光の全区間を、始位置零・三速度成分(V,0,0)のeitf/seと両端のsbへ結ぶ。これは先行の全区間光速度原理をこの直線伝播設定に適用する明示的な運動学的読みであり、原理の自動証明ではない。',
 '光路長は同じ系の幾何学的弧長で、選んだ零点から正の縦方向へ進む場合に終点縦座標へ一致させる。曲線や逆方向にこの等置を一般化しない。V-vを運動系の光速として使わない。',
 '同じτ候補と同じφ(v)を全対応・全時計指示・全実数四入力の時間式へ結ぶ。二つの端点だけでその全条件を代用せず、kの局所時刻をKの時刻へ置き換えない。',
 'この光線上の条件は光線外の全座標変換を決定しない。有限の関数指紋・有理代入・境界の対照例を、全実数の軌道や一般物理的導出の証明とはしない。旧定義・判断・証拠は保存する。',
]

def definitions():
    zero=k('bb','n p a b');ctx=v('context');event=v('event');first=v('first');second=v('second')
    text=define('ei46',[('event','a'),('first','a'),('second','a'),('context','d')],both(k('ei4k',event,first,second,ctx),*(k('sca',k('zc6',second,k(a)),zero) for a in ('yn','yo','yp'))))
    seg=v('segment');frame=v('frame');ray=k('wf',seg);depart=k('wi',seg);end=k('wj',seg);axis=k('zbo',frame,k('yn'),ctx)
    coord=lambda e,a:k('snd',e,frame,k(a),ctx)
    t=coord(end,'zc7');xyz=[coord(end,a) for a in ('yn','yo','yp')];cf=[frame,ctx,k('ta'),k('rb')]
    rows=[k('ei44',seg,ray,depart,end,k('wq',seg),frame,k('tc'),ctx),op('u',op('e',depart,end)),op('e',k('wh',seg),depart),k('sbg',k('tc')),k('sbg',t),k('sbg',xyz[0])]
    rows += [k('sca',coord(depart,a),zero) for a in ('yn','yo','yp','zc7')]
    rows += [k('sca',x,zero) for x in xyz[1:]]
    rows += [k('sca',k('wq',seg),xyz[0]),k('zbw',frame,axis,k('yn'),ctx),k('zdw',ray,depart,end,axis,frame,ctx),k('eitf',ray,*cf,zero,t,zero,zero,zero,k('tc'),zero,zero),k('sb',ray,depart,*cf,zero,zero,zero,zero),k('sb',ray,end,*cf,t,*xyz)]
    text+=define('ei47',[('segment','a'),('frame','a'),('context','d')],both(*rows))
    rest=v('rest');moving=v('moving');depart=k('wi',moving);end=k('wj',moving)
    rows=[k('ei45',rest,moving,ctx),k('ei4l',ctx),k('ei46',depart,k('zdz',depart,k('ra'),ctx),k('zdz',depart,k('zbm'),ctx),ctx),k('ei47',rest,k('ra'),ctx),k('ei47',moving,k('zbm'),ctx),k('snf',depart,ctx),k('snf',end,ctx),k('smj',k('zd4'),k('zeq'),k('tc'),k('zb7'))]
    text+=define('ei5a',[('rest','a'),('moving','a'),('context','d')],both(*rows))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX;doc=deepcopy(old);doc['statements']=[]
    assert not set(MEANINGS)&{d['name'] for d in old['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']
    added=doc['declarations'][len(old['declarations']):]
    basis=dict(status='same_origin_positive_longitudinal_light_dependency',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS)+['sng','snh'],statement_indices=[]).document
    ann=json.loads(read('data/frame-light-law-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
