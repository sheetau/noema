"""Connect K-time relative propagation and substitution on the same light ray."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_spatial_method_claim import ROOT,read
from scripts.compose_material_relative_frame import define
from scripts.compose_material_axes import interval
from scripts.compose_moving_trip_geometry import linear
from scripts.compose_two_postulates import quote
from scripts.compose_relativity_conjecture import content
from scripts.compose_limits import R,F,v,call as k,app,op,both,quant as q
from scripts.compose_public_first_sentence import PRIMITIVES as CONTRAST

PARENT='examples/v014/einstein-spatial-method-claim.noema';PARENT_BASIS='data/spatial-method-claim-basis-v1.json'
FULL='examples/v014/einstein-longitudinal-elimination.noema';CORE='examples/v014/longitudinal-elimination-core.noema'
BASIS='data/longitudinal-elimination-basis-v1.json';ANNOTATIONS='data/longitudinal-elimination-identifiers-v1.json';INDEX=293
FIELDS=[('first',R),('second',R),('speed',R),('target',F),('reference',F)]
PRIMITIVES={'eisnp':([('node','a'),('presenter','a'),('first_node','a'),('first_content','i[e]'),('second_node','a'),('second_content','i[e]'),('common_dimension','i[h[a] e]'),('context','d')],CONTRAST['h222q'][2])}
MEANINGS={
 'ei5w':'同じ二時刻でtargetとreferenceの位置の差を取り、その差の増分が同じ速度と経過時間の積に一致するeiohへ結ぶ。二対象の位置、時刻、速度の有効性を保持し、距離の絶対値や別々の時計の時間差へ替えない。',
 'ei5x':'正の幅の同じ時間区間の全時刻対にei5wを要求し、同じ二軌道の相対位置が指定した一定速度で変化することを表す。端点二点だけの平均速度ではない。',
 'ei5y':'現在の同じ二区間ei5aと同じk原点を保持し、その原点の全設定内の静止・K並進eizm、同じ放出出来事とK時刻零、光線と共通のK区間での原点軌道を結ぶ。両一次軌道の相対速度はV−vであり、現在原点の同時刻位置v*tと光の終点位置から得る差が同じ補助x′に一致する。',
 'ei5z':'選択した同じ光の二区間zez/zeyについて、K時刻で測るk原点との相対速度・補助位置ei5yを述べる内容。',
 'ei52':'同じ光のkでの測定とKで測る原点との相対運動を対照して提示し、ei5zを述べ、そこからx′/(V−v)=tを得るという著者の帰結を接続する。',
 'ei53':'原点との相対速度とK時刻の式ei52を述べるメッセージ。',
 'ei54':'u0069–u0070の相対速度とtの式を同じ著者・論説へ帰属し、先行ξのτ代入表示に続ける。',
 'ei55':'同じ光線のK相対速度条件ei5yと、その同じ到達出来事のsniによるt=x′/(V−v)、先行する同じτ代入式snhを合わせる。',
 'ei56':'同じ前提ei55の下で、先行するξの式snsを、tを消去したsnuへ書き換えて得るという著者の提示。',
 'ei57':'tの代入による縦座標の結果ei56を述べるメッセージ。',
 'ei6a':'u0071–u0072の代入と結果式を同じ著者・論説へ帰属し、同じtの値を得る箇所に続ける。',
 'ei6b':'同じK/kの選択区間のいずれかであり、両記録が同じ光・放出・始終出来事を測るei45を満たすという性質。kでのVとKでの原点に対するV−vを、同じ光線区間の測り方という共通観点で対照するために引用する。',
}
LIMITS=[
 'u0069は原刊899頁から900頁へ続く文。Nun ... aberは、同じ光をkで測るVから、Kの時刻でk原点に対して測るV−vへ観点を移す対照として読む。以前の光速原理の撤回や論理的矛盾ではない。',
 '対照は既存Kantのh222qの同じ基本規約を、0.14の閉じた引用型に合わせたeisnpで再使用する。特定の接続語や物理式専用の意味規約は加えない。',
 '同じk原点の全設定内の代表履歴と、この光線のK時刻0からtまでの一次軌道を結ぶ。全区間の相対変位を使い、原点の静止、V−vをτで測る速度、x′=ξを仮定しない。',
 '原点放出・空間零点と両時刻零は先行ei5aの明示的な読みを継承する。原点は同じ放出出来事に位置するが、後の光の到達出来事に原点もあるとは要求しない。同時刻の原点位置を使う。',
 '現在の設定は正のvを含み、光線条件はv<Vを保持する。t>0、V−v>0の範囲で割る。数値核はv=0も比較できるが、今回の物理設定を静止系対へ変更しない。',
 'Setzen wir ... einは、この同じtの値を先行するξの式へ代入して結果を得るという著者の計算提示として読む。実際の計算行為の履歴・実行日時・読者の参加を補わない。',
 '既存sni/sntとsnj/snuの同じ到達出来事・V,v,a=φ(v),x′を再利用する。aを1や最終確定係数へ固定しない。光線上の一致だけから全空間の座標変換を決定せず、横方向の光線はu0073以降に残す。',
 '一般実数域の量化は有限評価を拒否する。一次軌道の有限指紋、同じ時計・原点の結合、既存の有理多項式補題と数値代入は限定された証拠であり、一般実数体・物理法則・原文との同義性の自動証明ではない。',
]
GROUPS=(('ei52','ei53','ei54','ze5','ze4'),('ei56','ei57','ei6a','ze6','ze5'))

def definitions():
    text='r eisnp['+' '.join(t for _,t in PRIMITIVES['eisnp'][0])+'] c.\n'
    delta=lambda t:k('bf',app(v('target'),t),app(v('reference'),t))
    text+=define('ei5w',FIELDS,both(*(k('ba',app(v(f),v(t))) for f in ('target','reference') for t in ('first','second')),k('eioh',v('speed'),v('first'),v('second'),delta(v('first')),delta(v('second')))))
    allpairs=q('f','first',R,q('f','second',R,op('y',both(k('lg',v('lower'),v('upper'),v('first')),k('lg',v('lower'),v('upper'),v('second'))),k('ei5w',*[v(n) for n,_ in FIELDS]))))
    text+=define('ei5x',[('lower',R),('upper',R)]+FIELDS[2:],both(k('ba',v('lower')),k('ba',v('upper')),k('ba',v('speed')),k('bg',v('lower'),v('upper')),allpairs))
    rest=v('rest');moving=v('moving');ctx=v('context');K=k('ra');ks=k('zbm');lu=k('ta');tu=k('rb');zero=k('bb','n p a b')
    origin=k('zbn',ks,ctx);depart=k('wi',rest);end=k('wj',rest);time=k('snd',end,K,k('zc7'),ctx);x=k('snd',end,K,k('yn'),ctx)
    tracks=[k('eismh',origin,K,lu,tu,k(a),ctx) for a in ('yn','yo','yp')]
    relative=k('sna',k('tc'),k('zb7'))
    rows=[k('ei5a',rest,moving,ctx),k('eivx',ctx),k('zbv',ks,origin,ctx),k('eizm',origin,ctx),k('lg',*interval(K,ctx),zero),k('lg',*interval(K,ctx),time),k('sb',origin,depart,K,ctx,lu,tu,zero,zero,zero,zero),k('eitf',origin,K,ctx,lu,tu,zero,time,zero,zero,zero,k('zb7'),zero,zero)]
    rows += [k('sca',app(fn,zero),zero) for fn in tracks]
    rows += [k('sca',app(fn,time),position) for fn,position in zip(tracks,[k('shv',k('zb7'),time),zero,zero])]
    rows += [k('ei5x',zero,time,relative,linear(zero,zero,k('tc')),linear(zero,zero,k('zb7'))),k('sbg',relative),k('sca',k('sne',end,ctx),k('bf',x,app(tracks[0],time)))]
    text+=define('ei5y',[('rest','a'),('moving','a'),('context','d')],both(*rows))
    text+=content('ei5z',k('ei5y',k('zez'),k('zey'),k('zb6')))
    text+='d ei6b[segment a] e[b point['+both(op('x',op('e',v('segment'),k('zez')),op('e',v('segment'),k('zey'))),k('ei45',k('zez'),k('zey'),k('zb6')))+']].\n'
    text+=content('ei52',both(k('eisnp',k('ze5'),k('rd'),k('ze2'),quote('ei5e'),k('ze5'),quote('ei5z'),'r[p ei6b]',v('point')),k('uh',k('ze5'),k('rd'),quote('ei5z'),k('eisms'),v('point')),k('zc',k('ze5'),k('rd'),quote('ei5z'),quote('snt'),k('eisms'),v('point'))))
    end=k('wj',k('zey'));ctx=k('zb6')
    text+=content('ei55',both(k('ei5y',k('zez'),k('zey'),ctx),k('sni',end,ctx),k('snh',end,ctx)))
    text+=content('ei56',k('zd3',k('ze6'),k('rd'),quote('ei55'),quote('sns'),quote('snu'),k('eisms'),v('point')))
    for body,message,author,node,previous in GROUPS:
        text+='d '+message+'[] f[j s[k '+body+'[]]].\n'
        text+=define(author,[],both(k('eir3',k(node),k('rd'),k('eirf'),quote(message),k('ri')),k('ue',k(previous),k(node),k('ri')),op('u',op('e',k(previous),k(node)))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX;doc=deepcopy(old);doc['statements']=[]
    assert not (set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in old['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol=g[2],arguments=[])) for g in GROUPS]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='same_K_time_relative_light_motion_and_longitudinal_elimination',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=list(range(INDEX,INDEX+2))).document
    ann=json.loads(read('data/spatial-method-claim-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
