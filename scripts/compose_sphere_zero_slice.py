"""Express the same material surface on K's zero-time slice."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_sphere_setting import ROOT,read
from scripts.compose_solid_sphere_geometry import bind
from scripts.compose_rod_methods import interval
from scripts.compose_material_relative_frame import define
from scripts.compose_two_postulates import quote
from scripts.compose_relativity_conjecture import content
from scripts.compose_limits import R,v,call as k,app,op,both,quant as q

PARENT='examples/v014/einstein-sphere-setting.noema';PARENT_BASIS='data/sphere-setting-basis-v1.json'
FULL='examples/v014/einstein-sphere-zero-slice.noema';CORE='examples/v014/sphere-zero-slice-core.noema'
BASIS='data/sphere-zero-slice-basis-v1.json';ANNOTATIONS='data/sphere-zero-slice-identifiers-v1.json';INDEX=330
MEANINGS={
 'ejfr':'同じKの現在出来事記録eiyxが、そのKの対象期間内で時刻t=0を持つ条件。空間座標や表面への適合で候補を先に絞らない。kの時刻τには零を要求しない。',
 'ejfs':'ejfrの全現在K零時刻記録について、同じ物体の独立な境界ejfaへの所属と、出来事・記録を受け取る指定criterionが双方向に一致する。少なくとも一つのK零時刻の境界記録を要求する汎用の断面記述。',
 'ejft':'同じKのt=0の断面上で、同じ出来事のkの現在記録があり、そのk自身の対象区間内で同じ物体の境界と元の球面式sszを満たすことを表面の条件として使う。比較元を全k時刻面のままにせず、対象出来事をKの零断面へ合わせる。',
 'ejfu':'同じKのt=0の全適格記録について、同じ物体の物質境界とstfのx²/(√(1−(v/V)²))²+y²+z²=R²を双方向に結ぶ。平方根の外の二乗、元の半径、横二成分を保つ。',
 'ejfv':'同じ球の全物質点の設定ejff、元のkの表面式ejfh、既に得た現在の最終四式ejehを合わせた、Kでの表現への前提内容。新たなφや旧shdの対応は使わない。',
 'ejfw':'同じ球・半径・設定の表面を、Kのt=0の出来事におけるk記録で表すejftの内容。現在の一つの出来事を二系で追う。',
 'ejfx':'同じ球・半径・設定のK零時刻断面をKの三位置とstfで表すejfuの内容。後続の半軸の結論はまだ追加しない。',
 'ejfy':'著者が同じ前提ejfvの下で、同じ零断面のk座標による表現ejfwをK座標によるejfxへ書き換えて示す。ausgedrücktとzur Zeit t=0の両方を保持し、全時空表面と一断面を同一視しない。',
 'ejfz':'Kの零時刻断面への表現の書換えejfyを述べるメッセージ。',
 'ejf2':'u0112のコロンからu0113の式を同じ著者・論説へ帰属し、元のkの球面式に続ける。注本文のインベントリ末尾を本文の先行箇所にしない。',
}
LIMITS=[
 'u0112–u0113を原刊903頁へ照合する。dieser Oberflächeは直前の同じ物体zhwの境界を指す。閉球連続体という前の明示した読みと、同じ半径zhx・速度zb7・光速tc・K/kを保持する。',
 '対象はKのt=0という一つの同時刻断面である。比較元ejftも同じK零断面の出来事を選び、その同じ出来事のk記録を用いる。k側のτ=0は要求せず、全k時刻の球面記述を一つのK断面と論理的に同一視しない。',
 '期間は各系の座標規約に従う。扱うK零断面の表面記録がkの対象期間にも属する範囲として読む。これは対象区間の選択であり、二系の区間端や時刻値の一致ではない。表面に対応するk記録が欠ければejftを真としない。K側では零時刻の全適格記録を扱い、表面の正例だけへ選別しない。',
 'ejfsは独立な占有領域の境界と指定式の双方向の一致を全記録に課し、非空の表面記録を要求する。全物質点の履歴・形状・記録存在はejffから保つ。任意の実数四組が測定済みであることや、有限標本が全連続体を尽くすことは追加しない。',
 'M0199の分母は(√(1−(v/V)²))²であり、√を消してからさらに二重に二乗する誤りを避ける。横のy²,z²へ縮小係数を掛けず、右辺は同じR²である。stfは同じβ・速度・光速の許容域とt=0を保持する。',
 'ausgedrücktは既出の最終四式を用いて同じ表面をK座標で表す提示としてzd3へ接続する。著者の書換えの帰属と、処理系による代数的・物理的証明を区別する。新しい変換法則や同時性の規約を導入しない。',
 '有限検査は現在の出来事と二記録、両方向の表面一致、t=0の選択、実切断の有理境界例を点検する。保存された旧多項式証拠は数値核の関係を支えるが、旧zhu/shdの物質境界・座標解釈を現行の根拠として復活させない。',
 '続くu0114–u0115の回転楕円体という形状分類と三半軸、u0116以降の一般形状への帰結は別の後続の主張として残す。',
]

def definitions():
    event=v('event');record=v('record');body=v('body');ctx=v('context');radius=v('radius');K=k('ra');moving=k('zbm');zero=k('bb','n p a b')
    stamp=lambda r:k('zc6',r,k('zc7'))
    fields=[('event','a'),('record','a'),('context','d')]
    text=define('ejfr',fields,both(k('eiyx',event,record,K,ctx),k('lg',*interval(K,ctx),stamp(record)),k('sca',stamp(record),zero)))
    selected=k('ejfr',event,record,ctx);surface=k('ejfa',body,event,record,K,ctx)
    witness=bind(('event','record'),'a','g',both(selected,surface))
    every=bind(('event','record'),'a','f',op('y',selected,op('z',surface,app(app(v('criterion'),event),record))))
    text+=define('ejfs',[('body','a'),('context','d'),('criterion','h[a] h[a] c')],both(witness,every))
    second=v('second');original=q('g','second','a',both(k('eiyx',event,second,moving,ctx),k('lg',*interval(moving,ctx),stamp(second)),k('ejfa',body,event,second,moving,ctx),k('ssz',second,radius)))
    fields=[('body','a'),('radius',R),('context','d')]
    for name,criterion in (('ejft',original),('ejfu',k('stf',record,radius))):
        text+=define(name,fields,both(k('sbg',radius),k('ejfs',body,ctx,'i[event a][i[record a]['+criterion+']]')))
    point=v('point');text+=content('ejfv',both(*(op('t',k(n),point) for n in ('ejff','ejfh','ejeh'))))
    for name,target in (('ejfw','ejft'),('ejfx','ejfu')):text+=content(name,k(target,k('zhw'),k('zhx'),k('zb6')))
    text+=content('ejfy',k('zd3',k('zh2'),k('rd'),quote('ejfv'),quote('ejfw'),quote('ejfx'),k('eisn5'),point))
    text+='d ejfz[] f[j s[k ejfy[]]].\n'
    text+=define('ejf2',[],both(k('eir3',k('zh2'),k('rd'),k('eirf'),quote('ejfz'),k('ri')),k('ue',k('eisn6'),k('zh2'),k('ri')),op('u',op('e',k('eisn6'),k('zh2')))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX;doc=deepcopy(old);doc['statements']=[]
    assert not set(MEANINGS)&{d['name'] for d in old['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='ejf2',arguments=[]))]
    added=doc['declarations'][len(old['declarations']):]
    basis=dict(status='same_surface_expressed_on_current_K_zero_time_slice',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[INDEX]).document
    ann=json.loads(read('data/sphere-setting-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
