"""Construct the same transformed quantities for the ninth-section displays."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_limits import ROOT,R,v,call as k,app,op,both,quant as q,lam
from scripts.compose_material_relative_frame import define
from scripts.compose_convective_foundation_reading import GLOBAL
from scripts.compose_convective_charge_setting import FIELD_SETTING,at,args
from scripts.compose_field_equations import FIELD,TAU,POINT,JET,REGION,ROLES
from scripts.compose_field_transform import point_expression
from scripts.compose_doppler_infinity import quantified

def read(path):return (ROOT/path).read_text(encoding='utf-8')
PARENT='examples/v014/einstein-ninth-section-opening.noema';PARENT_BASIS='data/ninth-section-opening-basis-v1.json'
FULL='examples/v014/einstein-convective-transformed-quantities.noema';CORE='examples/v014/convective-transformed-quantities-core.noema'
BASIS='data/convective-transformed-quantities-basis-v1.json';ANNOTATIONS='data/convective-transformed-quantities-identifiers-v1.json'
KINEMATICS=[('light',R),('speed',R),('velocity',POINT)]
LOCAL=KINEMATICS+[('density',R)]
SETTING=GLOBAL+[('speed',R)]
AT_POINT=SETTING+[('point',POINT)]
WITH_JET=AT_POINT+[('newelectricjet',JET)]
MEANINGS={
 'ekzr':'同じV・系の速度v・元の三速度についてD=V²−v uxを構成する。非零性や有効性を値の構成だけで保証しない。',
 'ekzs':'同じDからV²(ux−v)/D、V²uy/(βD)、V²uz/(βD)を構成した三成分。βはsoyの正の枝、逆数は符号を保つsjtを用いる。第四の物理的速度を導入せず、他の個体役割への延長は零とする。適用域はekzwで別に指定する。',
 'ekzt':'同じ元の規格化密度とuxを用いてβDρ/V²を構成する。三速度と別のDやβへ取り替えず、ρが零又は負でも除算しない。',
 'ekzu':'新しい四座標を同じV・速度−vのs46で元の四座標へ写し、その点の元の流速にekzsを適用した三成分場。元の同じ数値座標で評価せず、引数変更と速度成分の変換を両方行う。新系での物理的速度との同定はまだ含めない。',
 'ekzv':'ekzuと同じ逆座標写像で元の密度・流速を評価してekztを適用したスカラー場。新系での物理的電荷密度や電気側発散との一致は、この関数を作るだけでは断言しない。',
 'ekzw':'元の有効な三速度と密度、s45の正のVと|v|<V、非零Dを要求する局所適用域。D>0や物質速度の絶対値<Vを追加しない。',
 'ekzx':'第九節の同じ原系解釈ekyzに、K/kの正逆の全座標規約eisqt、同じ速度単位、同じ旧領域の全有効点のekzwを結ぶ。さらに同じ単位・分布側の二場からs6k/s6lで構成した場を、s6mの新領域でejsnの物理的な場へ対応させる。これを第三・六節の変換則を使う設定とし、方程式、変換した密度・速度の新系での物理的同定、剛体付着を条件に含めない。',
 'ekzy':'同じ新座標地点から逆変換した旧地点でρ・三速度を取り、ekzu/ekzvの同じ新値とsoyのβをsentの五等式へ渡す。新電場は同じs6k、領域は同じs6m、三対角偏微分は同じ新地点の実際のs5tである。',
 'ekzz':'同じ設定から構成した二場・新領域・新密度・三速度について、全新有効点で18偏微分s5uと印刷形semfの六回転式が成立する。磁気側に印刷されていない1/Vを足さない。電気側発散は別のekz2へ分ける。',
 'ekz2':'同じ新領域が非空で、その全有効点に同じekzyを満たす新電場の微分表が存在する。三つの新速度、同じρ′の発散と変換の五等式を共有し、六式・旧側微分・磁気側微分の存在を余分に要求しない。',
}
LIMITS=[
 '次の一続きの原文u0233–u0236へ接続する依存群。先に元の物理的規約、二系の座標対応、変換された場の物理的意味、同じ新座標上の速度・密度関数、二つの式の表示内容を構成する。著者の仮定・第三/六節への参照・導出提示・wobei及び全単位判断は次に結ぶ。今回だけで完成件数を増やさない。',
 '原系のGLOBAL型を保ち、speedだけを追加する。担体パケット13引数は継承したインターフェースであり、今回の解釈条件も式もそこへ制約を追加しない。新しい原始関係・参照定数・本文主張は追加しない。',
 '新しい速度・密度は元の物理量から実際の演算で構成した関数である。次文u0237の新系で測った速度との同定を今回の前提へ置かず、u0238の任意運動での総電荷不変も仮定しない。新密度の発散との一致はekzyの要求であり、関数定義の副作用ではない。',
 '元の領域を同じ逆写像の逆像s6mへ変える。分母が零の点を都合よく新領域から削除せず、元の対象領域全体で式が定義されることを明示的な適用条件とする。Dの符号を制限せず、零密度でも三速度を保持する。',
 '二系の原点・軸・時計・単位と全座標範囲は正逆のeisqtへ接続する。同じ数値の四組や一つの出来事の成功で系全体の対応を代用しない。新場のejsnは第六節の物理的場変換を現在の場へ用いる前提で、真空条件・物質不在・磁気側発散零を補わない。',
 '原刊916頁M0389磁気側の1/V欠落をsemfに保存する。印刷形の記述と物理的導出の正しさは別であり、既存の反例や旧検査を修正しない。M0390の五等式は既存sentを再利用する。',
 '有限対照は実数の有理埋込み、非対称な標本場、独立した微分表と接続引数に限る。全実数・全関数域の列挙拒否を維持し、関数の数値試験を一般的な連鎖律・物理法則・原文同義性の証明にしない。',
]

def transformed_fields():return [k(n,v('light'),v('speed'),v('electricfield'),v('magneticfield')) for n in ('s6k','s6l')]
def newregion():return k('s6m',v('light'),v('speed'),v('region'))
def inverse(point):return k('s46',v('light'),k('be',v('speed')),point)
def flow(field,point):return lam('axis','a',at(app(field,v('axis')),point))
def local(point):return [v('light'),v('speed'),flow(v('velocityfield'),point),at(v('densityfield'),point)]

def definitions():
    V,s,u=v('light'),v('speed'),v('velocity');zero=k('bb','n p a b');mul=lambda a,b:k('shv',a,b)
    square=mul(V,V);D=k('ekzr',*args(KINEMATICS));beta=k('soy',V,s)
    text=define('ekzr',KINEMATICS,k('bf',square,mul(s,app(u,k('yn')))),R)
    values=[mul(mul(square,k('bf',app(u,k('yn')),s)),k('sjt',D))]
    values += [mul(mul(square,app(u,k(a))),k('sjt',mul(beta,D))) for a in ROLES[1:3]]
    value=zero
    for a,x in reversed(list(zip(ROLES[:3],values))):value=k('szi',op('e',v('axis'),k(a)),x,value)
    text+=define('ekzs',KINEMATICS,lam('axis','a',value),POINT)
    text+=define('ekzt',LOCAL,mul(mul(mul(beta,D),v('density')),k('sjt',square)),R)
    coords=[(n,R) for n in ('x','y','z','time')];p=point_expression(args(coords));old=inverse(p)
    forms={n:k(sym,*local(old)[:width]) for n,sym,width in [('velocity','ekzs',3),('density','ekzt',4)]}
    scalar=lambda body:'i['+' '.join(n+' '+t for n,t in coords)+']['+body+']'
    text+=define('ekzu',SETTING,lam('axis','a',scalar(app(forms['velocity'],v('axis')))),FIELD)
    text+=define('ekzv',SETTING,scalar(forms['density']),TAU)
    text+=define('ekzw',LOCAL,both(k('s45',V,s),k('ba',v('density')),*(k('ba',app(u,k(a))) for a in ROLES[:3]),op('u',k('sca',D,zero))))
    point=v('point');inside=k('ejsj',point,v('region'));forward=lam('place',POINT,k('s46',V,s,v('place')));back=lam('place',POINT,inverse(v('place')))
    charts=[k('eisqt',k(a),k(b),v('lengthunit'),v('timeunit'),mapping,v('context')) for a,b,mapping in [('ra','zbm',forward),('zbm','ra',back)]]
    newargs=args(FIELD_SETTING,frame=k('zbm'),region=newregion(),electricfield=transformed_fields()[0],magneticfield=transformed_fields()[1])
    text+=define('ekzx',SETTING,both(k('ekyz',*args(GLOBAL)),k('s45',V,s),*charts,k('eiscc',k('zbm'),v('lengthunit'),v('timeunit'),k('tb'),v('context')),k('ejsn',*newargs),q('f','point',POINT,op('y',inside,k('ekzw',*local(point))))))
    old=inverse(point);newdensity=at(k('ekzv',*args(SETTING)),point);newvelocity=flow(k('ekzu',*args(SETTING)),point)
    original=local(old);flowargs=[V,s,beta,original[3]]+[app(original[2],k(a)) for a in ROLES[:3]]+[newdensity]+[app(newvelocity,k(a)) for a in ROLES[:3]]
    text+=define('ekzy',WITH_JET,k('sent',*flowargs,v('newelectricjet'),transformed_fields()[0],newregion(),point))
    inside=k('ejsj',point,newregion());jets=[('newelectricjet',JET),('newmagneticjet',JET)]
    curls=both(k('s5u',*transformed_fields(),newregion(),point,*args(jets)),k('semf',V,newdensity,newvelocity,*args(jets)))
    for name,fs,body in [('ekzz',jets,curls),('ekz2',jets[:1],k('ekzy',*args(WITH_JET)))]:
        text+=define(name,SETTING,both(q('g','point',POINT,inside),q('f','point',POINT,op('y',inside,quantified('g',fs,body)))))
    return text

@lru_cache(None)
def build():
    old=parse(read(PARENT));assert len(old['statements'])==410
    assert not set(MEANINGS)&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']
    added=doc['declarations'][len(old['declarations']):]
    basis=dict(status='shared_transformed_velocity_density_and_printed_equations',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[]).document
    ann=json.loads(read('data/ninth-section-opening-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode()))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
