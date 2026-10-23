"""Connect both transverse ray calculations to current complete paths."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_longitudinal_elimination import ROOT,read
from scripts.compose_material_relative_frame import define
from scripts.compose_two_postulates import quote
from scripts.compose_relativity_conjecture import content
from scripts.compose_limits import R,v,call as k,op,both

PARENT='examples/v014/einstein-longitudinal-elimination.noema';PARENT_BASIS='data/longitudinal-elimination-basis-v1.json'
FULL='examples/v014/einstein-transverse-ray-claim.noema';CORE='examples/v014/transverse-ray-claim-core.noema'
BASIS='data/transverse-ray-claim-basis-v1.json';ANNOTATIONS='data/transverse-ray-claim-identifiers-v1.json';INDEX=295
MEANINGS={
 'ei6c':'指定系の同じ光区間ei44を、時刻零・位置零から進む完全な直線軌道eitf/seと両端の出会いsbへ結ぶ。横軸は相異なるyo又はyp、指定横速度は正、縦速度は非負とする。横座標は正、非選択横座標は零で、光路長は正の三変位平方和の平方根である。Kの斜めの光路長を横距離だけへ縮めない。',
 'ei6d':'同じ横軸について現在のK/k二区間ei45、同じ零原点ei4l/ei46、Kの速度成分(v,w)とkの(0,V)の全光路ei6cを結ぶ。w=√(V²−v²)>0、kでの軸上全光路、両端のτ対応と全τ式、同じK到達出来事のx′=0を保持する。',
 'ei6e':'同じ設定の指定横軸の二記録zfa/zfbを現在の全光線条件ei6dへ渡す。他軸の記録や到達値を流用しない。',
 'ei6f':'両横軸の現在の光線条件ei6eを同じ設定で考察する内容。一方だけでは満たさない。',
 'ei6g':'y方向の同じ現在光線の前提内容。ηの式と時刻条件の共通前提である。',
 'ei6h':'y方向の同じ光線の前提、同じ到達出来事のη=Vτとτ代入式soe、tとx′の値sofを結ぶ計算前提。',
 'ei6i':'z方向の同じ光線の前提と、その到達出来事の時刻・x′条件sofを結ぶ。η側の距離や時刻を流用しない。',
 'ei6j':'同じ著者が両横軸の光線を考察し、先の縦方向の計算ze6と同様の推論として提示する内容。',
 'ei6k':'両横軸の考察と類推ei6jを断定の伝達形式にする。',
 'ei6l':'両横軸の考察を同じ著者・論説へ帰属し、縦方向の時間消去からの順序を保つ。',
 'ei6m':'現在のy方向の光線条件ei6gから、同じη=Vτとτ代入式solを得るという著者の帰結提示。',
 'ei6n':'ηの第一表示ei6mを断定の伝達形式にする。',
 'ei6o':'ηの第一表示を同じ著者・論説へ帰属し、両横軸の考察に続ける。',
 'ei6p':'その同じy方向光線の前提から、t=y/√(V²−v²)とx′=0の併記somを提示する。wobeiは同じ導出に伴う条件の補足として読む。',
 'ei6q':'y方向の時刻と補助座標条件ei6pを断定の伝達形式にする。',
 'ei6r':'同じy方向の時刻条件を同じ著者・論説へ帰属し、ηの第一表示に続ける。',
 'ei6s':'同じy光線の式と時刻条件ei6hによってsolをsooへ書き換え、η=aVy/√(V²−v²)を得る提示。',
 'ei6t':'ηの時間消去ei6sを断定の伝達形式にする。',
 'ei6u':'ηの時間消去を同じ著者・論説へ帰属し、直前の時刻条件からの順序を保つ。',
 'ei6v':'同じz方向光線とその時刻条件ei6iからsoqのζの式を得る提示。直前のη導出との類推を明示し、undの並列を同じ二軸考察へ結ぶ。',
 'ei6w':'ζの類推結果ei6vを断定の伝達形式にする。',
 'ei6x':'ζの結果を同じ著者・論説へ帰属し、ηの時間消去に続ける。',
}
LIMITS=[
 'u0073–u0080を、直前の原点放出と正方向の設定を両横軸へ適用する類推として読む。原点は両系の時刻零・位置零で一致する選択であり、以後の全時刻での原点一致やt=τを要求しない。',
 'Kでは全速さV、縦成分v、選択横成分w=√(V²−v²)の直線、kでは同じ光が選択横軸に沿って速さVで進む。先行の直線伝播・相対運動の読みを保持し、この成分分解を原理から自動証明したとはしない。',
 '各光線の全区間を現在の時計・四座標・光速度範囲と結ぶ。端点の平方和だけで曲がる光路を受理せず、全eitf/seの条件を保持する。未知の履歴や測定は有限例で補わない。',
 'yとzは別の光線・到達出来事・距離・時刻を選べる。同じV,v,φを共有するが、一方の到達測定を他方へ転用しない。kの座標はη/ζ、Kの距離はy/zであり、これらを等置しない。',
 'Auf analoge Weiseとundは先の縦方向、及び同じ横二軸の導出への類推・並列として読む。wobeiは同じyの計算に伴う二条件、alsoはその値を入れる帰結である。著者の提示を実行履歴や形式証明と同一視しない。',
 '既存soe/sof/sogとsol/som/soo/soqの実切断による数式を再利用し、aは未定φ(v)のまま保持する。原文に明記されたy条件をzでも同形に用いるという省略補完を明示し、光線外の一般変換はここで確定しない。',
 '数値核のv=0や任意係数の例と現在の正のvの物理設定を区別する。全実数軌道は有限評価を拒否する。有理多項式補題・有限関数指紋・引数の対照検査は、一般実数体や物理的導出・意味同値の自動証明ではない。',
]
GROUPS=(('ei6j','ei6k','ei6l','zfg','ze6'),('ei6m','ei6n','ei6o','zfc','zfg'),('ei6p','ei6q','ei6r','zfd','zfc'),('ei6s','ei6t','ei6u','zfe','zfd'),('ei6v','ei6w','ei6x','zff','zfe'))
SELECTIONS=((295,),(295,296),(296,297),(296,297),(296,297,298),(296,297,298),(295,298,299),(295,298,299))

def definitions():
    seg=v('segment');frame=v('frame');axis=v('axis');ctx=v('context');zero=k('bb','n p a b')
    depart=k('wi',seg);end=k('wj',seg);ray=k('wf',seg);V=k('tc');speed=k('zb7');w=k('sle',V,speed)
    coord=lambda e,role:k('snd',e,frame,role,ctx)
    time=coord(end,k('zc7'));xyz=[coord(end,k(a)) for a in ('yn','yo','yp')]
    cf=[frame,ctx,k('ta'),k('rb')]
    rows=[k('soa',axis),k('ei44',seg,ray,depart,end,k('wq',seg),frame,V,ctx),op('u',op('e',depart,end)),op('e',k('wh',seg),depart),k('ba',v('longitudinal')),k('bc',zero,v('longitudinal')),k('sbg',v('transverse')),k('sbg',time),k('sbg',coord(end,axis)),k('sbg',k('wq',seg))]
    rows += [k('sca',coord(depart,k(a)),zero) for a in ('yn','yo','yp','zc7')]
    rows += [k('sca',xyz[0],k('shv',v('longitudinal'),time)),k('sca',coord(end,axis),k('shv',v('transverse'),time)),k('sca',k('shv',k('wq',seg),k('wq',seg)),k('bd',k('shv',xyz[0],xyz[0]),k('bd',k('shv',xyz[1],xyz[1]),k('shv',xyz[2],xyz[2]))))]
    for role in ('yo','yp'):
        velocity=[v('transverse') if a==role else zero for a in ('yo','yp')]
        other=k('yp' if role=='yo' else 'yo')
        rows.append(op('y',op('e',axis,k(role)),both(k('sca',coord(end,other),zero),k('eitf',ray,*cf,zero,time,zero,zero,zero,v('longitudinal'),*velocity))))
    rows += [k('sb',ray,depart,*cf,zero,zero,zero,zero),k('sb',ray,end,*cf,time,*xyz)]
    text=define('ei6c',[('segment','a'),('frame','a'),('axis','a'),('longitudinal',R),('transverse',R),('context','d')],both(*rows))
    rest=v('rest');moving=v('moving');depart=k('wi',moving);end=k('wj',moving);K=k('ra');ks=k('zbm')
    line=k('zbo',ks,axis,ctx)
    rows=[k('soa',axis),k('ei45',rest,moving,ctx),k('ei4l',ctx),k('ei46',depart,k('zdz',depart,K,ctx),k('zdz',depart,ks,ctx),ctx),k('sbg',speed),k('skz',V,speed,w),k('ei6c',rest,K,axis,speed,w,ctx),k('ei6c',moving,ks,axis,zero,V,ctx),k('zbw',ks,line,axis,ctx),k('zdw',k('wf',moving),depart,end,line,ks,ctx),k('snf',depart,ctx),k('snf',end,ctx),k('smj',k('zd4'),k('zeq'),V,speed),k('sca',k('sne',end,ctx),zero)]
    text+=define('ei6d',[('rest','a'),('moving','a'),('axis','a'),('context','d')],both(*rows))
    text+=define('ei6e',[('axis','a'),('context','d')],k('ei6d',k('zfa',axis),k('zfb',axis),axis,ctx))
    ctx=k('zb6');end=lambda a:k('wj',k('zfb',k(a)))
    text+=content('ei6f',both(k('ei6e',k('yo'),ctx),k('ei6e',k('yp'),ctx)))
    text+=content('ei6g',k('ei6e',k('yo'),ctx))
    text+=content('ei6h',both(k('ei6e',k('yo'),ctx),k('soe',end('yo'),k('yo'),ctx),k('sof',end('yo'),k('yo'),ctx)))
    text+=content('ei6i',both(k('ei6e',k('yp'),ctx),k('sof',end('yp'),k('yp'),ctx)))
    author=k('rd');section=k('eisms');point=v('point')
    text+=content('ei6j',both(k('ug',k('zfg'),author,quote('ei6f'),section,point),k('zep',k('zfg'),author,k('ze6'),section,point)))
    text+=content('ei6m',k('zc',k('zfc'),author,quote('ei6g'),quote('sol'),section,point))
    text+=content('ei6p',k('zc',k('zfd'),author,quote('ei6g'),quote('som'),section,point))
    text+=content('ei6s',k('zd3',k('zfe'),author,quote('ei6h'),quote('sol'),quote('soo'),section,point))
    text+=content('ei6v',both(k('zc',k('zff'),author,quote('ei6i'),quote('soq'),section,point),k('zep',k('zff'),author,k('zfe'),section,point)))
    for body,message,attribution,node,previous in GROUPS:
        text+='d '+message+'[] f[j s[k '+body+'[]]].\n'
        text+=define(attribution,[],both(k('eir3',k(node),author,k('eirf'),quote(message),k('ri')),k('ue',k(previous),k(node),k('ri')),op('u',op('e',k(previous),k(node)))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX;doc=deepcopy(old);doc['statements']=[]
    assert not set(MEANINGS)&{d['name'] for d in old['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol=g[2],arguments=[])) for g in GROUPS]
    added=doc['declarations'][len(old['declarations']):]
    basis=dict(status='both_current_transverse_ray_calculations_connected',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=list(range(INDEX,INDEX+len(GROUPS)))).document
    ann=json.loads(read('data/longitudinal-elimination-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
