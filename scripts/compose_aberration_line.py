"""Keep the simultaneous source-observer line distinct from the boost axis."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_doppler_specialization import ROOT,read,EXTENDED
from scripts.compose_observed_doppler import MODELS
from scripts.compose_field_equations import POINT
from scripts.compose_material_relative_frame import define,args
from scripts.compose_relativity_conjecture import content
from scripts.compose_limits import R,v,call as k,app,op,both,quant as q

PARENT='examples/v014/einstein-doppler-infinity.noema';PARENT_BASIS='data/doppler-infinity-basis-v1.json'
FULL='examples/v014/einstein-aberration-line.noema';CORE='examples/v014/aberration-line-core.noema'
BASIS='data/aberration-line-basis-v1.json';ANNOTATIONS='data/aberration-line-identifiers-v1.json'
GEOMETRY=[(n,R) for n in ('light','speed','ax','ay','az')]
POSITION=[(n,R) for n in ('px','py','pz')]
POINT_FIELDS=GEOMETRY+[('distance',R),('time',R)]
DISPLACEMENT=GEOMETRY+POSITION+[('distance',R),('time',R)]
PAIR=[(n,R) for n in ('nx','ny','nz','lx','ly','lz','cosine','sine')]
MEASURE=[(n,R) for n in ('ratio','principal','pi','angle')]
NEW_ANGLE=[(n,R) for n in ('newanglecos','newanglesin','newratio','newprincipal','newangle')]
SETTING=EXTENDED+NEW_ANGLE
VARIABLES=[(n,t) for n,t in SETTING if n not in ('frame','scope','context','light')]
AXES=('yn','yo','yp');ALL_AXES=AXES+('zc7',)
MEANINGS={
 'ekfz':'正の光速度、光速未満の符号付き速度、有限な単位旧方向を要求する数値的な配置条件。sdl2の位相率を1にして再使用するが、実際の波の位相率を1へ変更しない。',
 'ekga':'旧系で静止する源−R*nをLorentz変換し、新系の同じ時刻τを引数にした四座標。縦位置は−R*a/γ−v*τ、横位置は−R*bと−R*c、時刻はτ。旧時刻t=τを代入した非同時な位置ではない。',
 'ekgb':'新系の同時刻の結線に沿う非正規化方向(a/γ,b,c)の長さ。波面法線の変換値や縦軸との角ではない。',
 'ekgc':'(a/γ,b,c)を同じ正の長さekgbで正規化した、源から観測者へ向く同時刻結線の遠距離方向。源と観測者を交換しない。',
 'ekgd':'同じ旧波面法線の単位方向をsdo2/sdp2で変換した新波面法線の三成分。結線のekgcとは別に構成する。',
 'ekge':'二つの有効な三次元単位方向の内積をcosineに等置し、単位円と非負sineを要求する向きなし角の成分条件。第二方向を速度又は座標軸へ置き換えない。',
 'ekgf':'ekgeの同じ二方向と同じ円成分をejotへ渡し、0からpiの実数角へ結ぶ。角の測度と余弦の値を区別し、直角・反対向きも保持する。',
 'ekgg':'新時刻τに対応する静止源の旧時刻τ/γ−v*R*a/V²。静止源の旧縦位置−R*aを時間変換の逆解へ入れる。',
 'ekgh':'同じ距離Rと新時刻τについて、旧源曲線ekdiをekggの旧時刻で評価してs46で変換すると、ekgaの全四成分へ一致すること。許容速度・正距離・有限時刻を保持する。',
 'ekgi':'全正距離の各モデルについてekgaの同じ新時刻曲線を返すモデル族。物理的な源との同一性はekgnのeisskへ結ぶ。',
 'ekgj':'指定された新時刻での有限な観測者位置からekgaの同時刻の源位置を引いた三変位。光の放出時刻の源位置又は観測者から源への逆向きとは区別する。',
 'ekgk':'同じ観測者位置と新時刻に対し、縦成分だけへv*τを加えた有限の位置ベクトル。新系の源の並進を、遠距離極限の有限な基点へ移す。',
 'ekgl':'同じ新同時刻の変位ekgjがekgk+R*ekgb*ekgcに全空間成分で一致する。正の距離・長さを保持し、既存の−ρ*n源の極限へρ=R*ekgbで接続するための尺度変更。',
 'ekgm':'同じ尺度変更ekglの下で、距離ρ=R*ekgbと位置ekgkを既存ekdjへ渡し、実際の同時刻結線がekgcへ成分ごとにepsilon以内で近いことを要求する。',
 'ekgn':'同じ65役割で既存eketの源・波・系・観測者・位相・周期・旧角条件を保ち、源を同じLorentz変換後の曲線族ekgiへeisskで帰属し、同時刻結線方向ekgcの既存全位置極限ekdmと、その方向から新波面法線ekgdへの実数角ekgfを結ぶ。印刷された光行差等式を前件へ含めない。',
 'ekgo':'同じ設定のnewanglecosが(cosφ−v/V)/(1−(v/V)cosφ)に等しいというM0340の数値内容。oldanglecosは先行の旧角anglecosであり、結線の新角を先にa′と等置しない。',
 'ekgp':'K・V・第七節・評価状況を固定し、残る61役割の全割当でekgnならekgoを述べる条件内容。本文への著者帰属・φ′という表記の導入・式の書換え提示は次の統合に残す。',
 'ekgq':'同じ許容数値配置の新波面法線ekgdと新同時刻結線ekgcの間の実数角。物理的な同じ波への結合ekgnを局所診断する数値核。',
 'ekgr':'同じ許容配置での1/(γ*ekgb)。新波面法線と同時刻結線の内積に対応する比較値であり、印刷された(a−v/V)/(1−av/V)をこの値へ修正しない。',
 'ekgs':'同じ源の新同時刻結線に沿う、正規化前の三成分(a/γ,b,c)。長さをまだ割らず、平方根が有理数でない場合も座標と内積の役割を別に確認できる。',
}
LIMITS=[
 'u0193の固定原文と原刊912頁は、移動系の波面法線（光線方向）と結線「光源―観測者」の間の角と記す。今回の採用読解は、この結線を同じ移動系の同時刻の源から観測者への向きとする。速度方向又は+x軸へ無断で置換しない。',
 '源は先行のK静止モデル−R*nであり、新系での同時刻τを固定して旧時刻を解き直す。源をkでも静止させず、旧新の数値時刻を同一視しない。各モデルの位置と物理的な同じ源をeisskで結び、全距離で同時に実在すると解釈しない。',
 'R→+∞における新同時刻結線は(a/γ,b,c)の正規化方向であり、新波面法線の(a−v/V,b/γ,c/γ)/(1−av/V)とは一般に異なる。有限な観測者位置と時刻を先に固定し、距離を増やす。全時刻・全空間で一様という追加主張はしない。',
 '方向成分の限界と同じ物理設定への対応を準備する。実数の平方根、逆数、Lorentz写像、単位円、内積、積分による角、既存の遠距離極限を合成し、新しい一般基本関係を追加しない。',
 'この字義的な結線読解では、例えばV=5,v=3,旧方向(0,1,0)の新法線は(−3/5,4/5,0)、結線方向は(0,1,0)であり、角の余弦4/5と表示式の−3/5は一致しない。本文の誤植を確定したものではなく、印字と採用解釈の不整合を隠さず記録する。',
 'u0193のNennt manによるφ′の命名・Wellennormale (Strahlrichtung)の同一方向の提示・a′の式の書換え・コロン、及びu0194の表示帰属は未接続。旧375主張と全単位判断を保持し、新しい全単位判断はまだ追加しない。',
 '有限の有理数切断モデル、量化の各位置、座標対応の対照は一般実数体の機械証明や歴史的意図の証明ではない。未知の平方根・逆数・積分を成功値で補わず、全実数域を有限評価へ縮めない。',
]

def components(fn):return [app(fn,k(a)) for a in AXES]

def definitions():
    zero=k('bb','n p a b');one=k('bb','n p b b');V=v('light');speed=v('speed');distance=v('distance');time=v('time');n=[v(a) for a in ('ax','ay','az')]
    gamma=k('soy',V,speed);inverse=k('sjd',gamma);neg=lambda x:k('bf',zero,x);mul=lambda x,y:k('shv',x,y)
    text=define('ekfz',GEOMETRY,k('sdl2',V,speed,one,*n))
    source=[k('bf',neg(mul(distance,mul(n[0],inverse))),mul(speed,time)),neg(mul(distance,n[1])),neg(mul(distance,n[2]))]
    spatial=k('ekbe',*source)
    text+=define('ekga',POINT_FIELDS,'i[axis a]['+k('szi',op('e',v('axis'),k('zc7')),time,app(spatial,v('axis')))+']',POINT)
    longitudinal=mul(n[0],inverse)
    text+=define('ekgs',GEOMETRY,k('ekbe',longitudinal,n[1],n[2]),POINT)
    rawline=components(k('ekgs',*args(GEOMETRY)));length=k('sky',k('seag',*rawline))
    text+=define('ekgb',GEOMETRY,length,R)
    text+=define('ekgc',GEOMETRY,k('ekbe',*(mul(x,k('sjd',k('ekgb',*args(GEOMETRY)))) for x in rawline)),POINT)
    text+=define('ekgd',GEOMETRY,k('ekbe',k('sdo2',V,speed,n[0]),*(k('sdp2',V,speed,n[0],x) for x in n[1:])),POINT)
    left=[v(x) for x in ('nx','ny','nz')];right=[v(x) for x in ('lx','ly','lz')];co=v('cosine');si=v('sine')
    text+=define('ekge',PAIR,both(*(k('ba',v(x)) for x,t in PAIR),k('sca',k('seag',*left),one),k('sca',k('seag',*right),one),k('s2c',co,si),k('bc',zero,si),k('sca',co,k('seah',*left,*right))))
    text+=define('ekgf',PAIR+MEASURE,both(k('ekge',*args(PAIR)),k('ejot',co,si,*args(MEASURE))))
    oldtime=k('bf',mul(time,inverse),mul(mul(speed,distance),mul(n[0],k('sjd',mul(V,V)))))
    text+=define('ekgg',POINT_FIELDS,oldtime,R)
    oldpoint=app(k('ekdi',*n,distance),k('ekgg',*args(POINT_FIELDS)));mapped=k('s46',V,speed,oldpoint);newpoint=k('ekga',*args(POINT_FIELDS))
    admissible=both(k('ekfz',*args(GEOMETRY)),k('ba',distance),k('bg',zero,distance),k('ba',time))
    text+=define('ekgh',POINT_FIELDS,both(admissible,*(k('sca',app(mapped,k(a)),app(newpoint,k(a))) for a in ALL_AXES)))
    text+=define('ekgi',GEOMETRY,'i[distance '+R+'][i[time '+R+']['+newpoint+']]',MODELS)
    text+=define('ekgj',DISPLACEMENT,k('ekbe',*(k('bf',v(p),app(newpoint,k(a))) for p,a in zip(('px','py','pz'),AXES))),POINT)
    text+=define('ekgk',GEOMETRY+POSITION+[('time',R)],k('ekbe',k('bd',v('px'),mul(speed,time)),v('py'),v('pz')),POINT)
    line=components(k('ekgc',*args(GEOMETRY)));normal=components(k('ekgd',*args(GEOMETRY)));shift=components(k('ekgk',*args(GEOMETRY+POSITION+[('time',R)])))
    rho=mul(distance,k('ekgb',*args(GEOMETRY)));d=components(k('ekgj',*args(DISPLACEMENT)))
    text+=define('ekgl',DISPLACEMENT,both(admissible,*(k('ba',v(p)) for p,t in POSITION),k('bg',zero,k('ekgb',*args(GEOMETRY))),*(k('sca',a,k('bd',p,mul(rho,b))) for a,p,b in zip(d,shift,line))))
    text+=define('ekgm',DISPLACEMENT+[('epsilon',R)],both(k('ekgl',*args(DISPLACEMENT)),k('ekdj',*line,*shift,rho,v('epsilon'))))
    circle=[v(x) for x in ('newanglecos','newanglesin','newratio','newprincipal','pi','newangle')]
    text+=define('ekgn',SETTING,both(k('eket',*args(EXTENDED)),k('eissk',v('source'),k('zbm'),v('lengthunit'),v('timeunit'),k('ekgi',*args(GEOMETRY)),k('ekdz'),v('scope'),v('context')),k('ekdm',*line),k('ekgf',*normal,*line,*circle)))
    text+=define('ekgo',SETTING,k('sca',v('newanglecos'),k('sdo2',V,speed,v('anglecos'))))
    fixed={'frame':k('ra'),'light':k('tc'),'scope':k('eisrx'),'context':v('point')};actual=[fixed.get(n,v(n)) for n,t in SETTING]
    body=op('y',k('ekgn',*actual),k('ekgo',*actual))
    for n,t in reversed(VARIABLES):body=q('f',n,t,body)
    text+=content('ekgp',body)
    text+=define('ekgq',GEOMETRY+[('newanglecos',R),('newanglesin',R),('newratio',R),('newprincipal',R),('pi',R),('newangle',R)],both(k('ekfz',*args(GEOMETRY)),k('ekgf',*normal,*line,*circle)))
    text+=define('ekgr',GEOMETRY,k('sjd',mul(gamma,k('ekgb',*args(GEOMETRY)))),R)
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==375
    assert not set(MEANINGS)&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']
    added=doc['declarations'][len(old['declarations']):]
    basis=dict(status='simultaneous_connecting_line_and_aberrated_wave_normal_dependencies',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[]).document
    ann=json.loads(read('data/doppler-infinity-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
