"""Present unchanged transverse dimensions, axial contraction and speed ordering."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_material_shape_dimensions import ROOT,read,SETTING,WIDTHS
from scripts.compose_solid_sphere_geometry import args,bind
from scripts.compose_shape_contraction import SHAPE
from scripts.compose_rod_methods import interval
from scripts.compose_material_relative_frame import define
from scripts.compose_relativity_conjecture import content
from scripts.compose_two_postulates import quote
from scripts.compose_limits import R,v,call as k,app,op,both,quant as q

PARENT='examples/v014/einstein-material-shape-dimensions.noema';PARENT_BASIS='data/material-shape-dimensions-basis-v1.json'
FULL='examples/v014/einstein-directional-contraction-claim.noema';CORE='examples/v014/directional-contraction-claim-core.noema'
BASIS='data/directional-contraction-claim-basis-v1.json';ANNOTATIONS='data/directional-contraction-claim-identifiers-v1.json';INDEX=332
PRIMITIVES={'eisob':'u0116第一文のYとZの寸法が運動で変わらないという対照の第一側の箇所。','eisoc':'u0116第一文のX寸法が指定比で縮むという対照の第二側の箇所。'}
MEANINGS={
 'ejgp':'任意形状の同じ物体の運動設定ejgjに、静止系の基準時刻で三軸の有限幅が存在することを結ぶ。形状は任意のまま、ここでいう寸法を持つ有限な対象の比較範囲を明示する。',
 'ejgq':'同じ物体の指定軸に非負の有限静止幅が存在し、Kの全対象時刻に非負の実際の幅が存在する。縦軸なら静止幅に√(1−(v/V)²)を掛けた値、横軸なら同じ値とし、正の縦幅は厳密に短くなる。比1対係数の向きを保つ。',
 'ejgr':'同じ物体についてYとZの両方の寸法が全対象時刻に不変となるejgq。片方の横方向だけにしない。',
 'ejgs':'同じ物体についてX寸法が全対象時刻に指定比で縮小するejgq。時刻零だけに限らず、正の静止幅の厳密な縮小と零幅の保存を区別する。',
 'ejgt':'全物体・全任意形状について、有限寸法の運動設定ejgpから、全時刻の実際の変換形状ejgmと、存在する横二幅・縦幅の関係ejgr/ejgsが従うという内容。',
 'ejgu':'同じ全物体・全任意形状の範囲で横二寸法の不変ejgrを述べる内容。対照の第一側。',
 'ejgv':'同じ全物体・全任意形状の範囲で縦寸法の縮小ejgsを述べる内容。対照の第二側。',
 'ejgw':'指定軸について、同じ有限寸法の運動設定にある全物体の静止側とK側の寸法を比べる内容。横と縦の対照を同じ寸法への運動の効果という観点へ結ぶ。',
 'ejgx':'同じ正の有限静止幅・正の光速に対する二つの許容された非負速度を比較し、第二の速度が大きければ第二の縮小後の幅が厳密に小さいという条件付き関係。物体の異なる元の大きさや加速過程を比較しない。',
 'ejgy':'同じ光速で全ての静止幅・二速度にejgxを要求する内容。速度が大きいほど縮小が強いという比較を、同じ元の幅の下で一般的に述べる。',
 'ejgz':'先行する一般の球形剛体の回転楕円体と半軸ejgb、同じ現在の最終四式ejehを合わせ、任意形状の寸法へ進む著者の先行内容とする。',
 'ejg2':'著者が先の球と変換から任意形状の三軸寸法ejgtを帰結として示し、横二不変ejguと縦縮小ejgvを同じ観点で対照し、同じ関係から速さによる比較ejgyを結論する提示。',
 'ejg3':'u0116第一文の帰結・横縦の対照・速度による比較ejg2を述べるメッセージ。',
 'ejg4':'同じ第一文を著者・論説へ帰属し、直前の球形剛体の回転楕円体と三半軸の箇所に続ける。後の光速極限と留保の文はまだ含めない。',
}
LIMITS=[
 'u0116の冒頭から第一文末ist.まで[0,270)とM0201–M0205を原刊903頁へ照合する。段落後半の二文とM0206は別に残し、全単位完成には数えない。',
 'Dimensionは同じ物体の占有集合の座標軸への射影の有限幅と読む。任意形状に球の内部充填や凸性・連結性を要求しない。有限な静止三幅を持つ対象を明示した範囲とし、その範囲から運動時の幅の存在も結論の内側で要求する。',
 '同じ静止幅を全K時刻の実際の幅へ結び、横二方向では同値、縦方向では静止幅対運動幅が1対√(1−(v/V)²)となる。向きを逆にして伸長させず、半軸から直径への変更によって比を変えない。',
 '既存の0<v<Vの正X並進・平行軸・同じ尺度の比較設定を継承する。正の縦寸法には厳密な縮小、零寸法には零の保存を要求する。er scheinenはKの同時刻座標からの寸法として読み、光の遅延による画像の錯覚とはしない。',
 'je größer vは、同じ光速と同じ正の静止寸法の下で、許容された非負速度の大小を比べる。異なる大きさの物体同士、速度の向きの順序、同じ物体の加速履歴や時間に沿った縮小過程へ替えない。',
 'Währendは横二方向と縦方向への運動の効果の対照、二つのalsoは先の球と四式からの一般化及び縮小比からの速度比較という著者の帰結として保持する。既存eisnpとzcを再利用し、処理系の一般的な物理証明として提示しない。',
 '全物体・形状関数・時刻・幅・速度の量化は有限例へ置換しない。有限対照と引数検査、既存の多項式・上限下限の証拠、原文の通読判断を分ける。光速極限、超光速での議論の意味、後続の物理的役割の予告は未完。',
]

def definitions():
    text=''.join('r '+n+'[] a.\n' for n in PRIMITIVES)
    body=v('body');shape=v('shape');ctx=v('context');axis=v('axis');time=v('time');proper=v('proper');observed=v('observed');K=k('ra');moving=k('zbm');zero=k('bb','n p a b')
    resttime=interval(moving,ctx)[0]
    widths=args(WIDTHS[:3])
    finite=bind(tuple(n for n,_ in WIDTHS[:3]),R,'g',both(*(k('ejgl',body,moving,ctx,resttime,k(a),w) for a,w in zip(('yn','yo','yp'),widths))))
    text+=define('ejgp',SETTING,both(k('ejgj',*args(SETTING)),finite))
    axial=op('e',axis,k('yn'));transverse=op('x',op('e',axis,k('yo')),op('e',axis,k('yp')))
    smaller=op('y',k('sbg',proper),k('bg',observed,proper))
    longitudinal=both(k('sca',observed,k('shv',proper,k('stw',k('tc'),k('zb7')))),smaller)
    value=both(k('ba',observed),k('bc',zero,observed),k('ejgl',body,K,ctx,time,axis,observed),op('y',axial,longitudinal),op('y',transverse,k('sca',observed,proper)))
    every=q('f','time',R,op('y',k('lg',*interval(K,ctx),time),q('g','observed',R,value)))
    text+=define('ejgq',[('body','a'),('axis','a'),('context','d')],both(op('x',axial,transverse),q('g','proper',R,both(k('ba',proper),k('bc',zero,proper),k('ejgl',body,moving,ctx,resttime,axis,proper),every))))
    text+=define('ejgr',[('body','a'),('context','d')],both(*(k('ejgq',body,k(a),ctx) for a in ('yo','yp'))))
    text+=define('ejgs',[('body','a'),('context','d')],k('ejgq',body,k('yn'),ctx))
    def general(result):return q('f','body','a',q('f','shape',SHAPE,op('y',k('ejgp',body,shape,k('zb6')),result)))
    text+=content('ejgt',general(both(k('ejgm',body,shape,k('zb6')),k('ejgr',body,k('zb6')),k('ejgs',body,k('zb6')))))
    text+=content('ejgu',general(k('ejgr',body,k('zb6'))));text+=content('ejgv',general(k('ejgs',body,k('zb6'))))
    text+='d ejgw[axis a] e[b point['+general(k('ejgq',body,axis,k('zb6')))+']].\n'
    light=v('light');speed=v('speed');other=v('other')
    admissible=both(k('sbg',light),k('sbg',proper),k('ba',speed),k('ba',other),k('bc',zero,speed),k('bg',speed,other),*(k('srd',light,s,k('soy',light,s)) for s in (speed,other)))
    comparison=k('bg',k('shv',proper,k('stw',light,other)),k('shv',proper,k('stw',light,speed)))
    text+=define('ejgx',[(n,R) for n in ('light','proper','speed','other')],op('y',admissible,comparison))
    text+=content('ejgy',bind(('proper','speed','other'),R,'f',k('ejgx',k('tc'),proper,speed,other)))
    text+=content('ejgz',both(*(op('t',k(n),v('point')) for n in ('ejgb','ejeh'))))
    clauses=[k('zc',k('zh6'),k('rd'),quote('ejgz'),quote('ejgt'),k('eisn5'),v('point'))]
    clauses.extend(k('uh',k(node),k('rd'),quote(claim),k('eisn5'),v('point')) for node,claim in (('eisob','ejgu'),('eisoc','ejgv')))
    clauses.extend([k('eisnp',k('zh6'),k('rd'),k('eisob'),quote('ejgu'),k('eisoc'),quote('ejgv'),'r[p ejgw]',v('point')),k('zc',k('zic'),k('rd'),quote('ejgt'),quote('ejgy'),k('eisn5'),v('point'))])
    text+=content('ejg2',both(*clauses));text+='d ejg3[] f[j s[k ejg2[]]].\n'
    text+=define('ejg4',[],both(k('eir3',k('zh6'),k('rd'),k('eirf'),quote('ejg3'),k('ri')),k('ue',k('zh3'),k('zh6'),k('ri')),op('u',op('e',k('zh3'),k('zh6')))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX;doc=deepcopy(old);doc['statements']=[]
    assert not (set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in old['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='ejg4',arguments=[]))];added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[],meaning_ja=PRIMITIVES[d['name']]) for d in added if d['kind']=='primitive'}
    basis=dict(status='directional_dimensions_and_speed_order_author_claim',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[INDEX]).document
    ann=json.loads(read('data/material-shape-dimensions-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
