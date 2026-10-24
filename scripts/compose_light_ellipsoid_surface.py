"""Describe the same moving radiation boundary as an affine ellipsoid surface."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_portion_energy_inquiry import ROOT,read,SETTING
from scripts.compose_light_region_slices import GEOMETRY,XYZ,POINT
from scripts.compose_equal_volume_supposition import FIXED
from scripts.compose_material_relative_frame import define,args
from scripts.compose_relativity_conjecture import content
from scripts.compose_two_postulates import quote
from scripts.compose_doppler_infinity import quantified
from scripts.compose_limits import R,v,call as k,app,op,both

PARENT='examples/v014/einstein-portion-energy-inquiry.noema';PARENT_BASIS='data/portion-energy-inquiry-basis-v1.json'
FULL='examples/v014/einstein-light-ellipsoid-surface.noema';CORE='examples/v014/light-ellipsoid-surface-core.noema'
BASIS='data/light-ellipsoid-surface-basis-v1.json';ANNOTATIONS='data/light-ellipsoid-surface-identifiers-v1.json';INDEX=390
TRIANGLE=[(n,R) for n in ('factor','sheary','shearz')]
CENTER=[(n,R) for n in ('cx','cy','cz')]
ELLIPSOID=TRIANGLE+[('radius',R)]+CENTER
COORDS=XYZ+[('time',R)]
VARIABLES=[(n,t) for n,t in SETTING if n not in FIXED]
PRIMITIVES={
 'eistu':([], 'u0206の、同じ球面を動く系で見た楕円体面として述べ、τ=0の式を導入するコロンまでの箇所。'),
 'eistv':([], 'u0207=M0359の、前の同じ球面の新系時刻τ=0の方程式を表示する箇所。'),
}
MEANINGS={
 'ekoi':'三位置に対する三角線形写像L(x,y,z)=(factor*x,y−sheary*x,z−shearz*x)。非空間成分は零とし、時刻成分の変換とは区別する。',
 'ekoj':'factorが正の場合のekoiの逆写像(u,v,w)↦(u/factor,v+sheary*u/factor,w+shearz*u/factor)。許容性は利用側で要求する。',
 'ekok':'有効な三係数と位置・正のfactorについて、ekoiとekojを両順序で合成すると各三成分が元へ戻る条件。三角写像の可逆性を特定軸だけで代用しない。',
 'ekol':'有効な正のfactorと半径、三係数・中心・位置について、L(position−center)の三平方和がradius²に等しいという面。可逆な線形写像による正半径球面の逆像を楕円体面とする一般的な幾何学の構成。閉内部又は中身を持つ物体とは区別する。',
 'ekom':'同じV/vと波面方向について、新系時刻timeの球面像の中心を、逆Lorentz変換後の三つの時間項を消すLの逆像として構成する。旧系の中心を同じ数値の新系位置として転記しない。',
 'ekon':'同じ有効四座標における実際の逆Lorentz球面secdへの所属と、同じ時刻の中心ekom・正の三角係数によるekolへの所属が双方向に一致することと、同じ三角写像の両順序の位置復元を結ぶ。球面上の正例だけを比較しない。',
 'ekoo':'許容速度・正半径・単位波面方向のeklzと正のDについて、全有効四座標でekonを要求する。動く系で見る面が全時刻で平行移動する同じ楕円体面であるという構成。τ=0だけ又は有限標本へ縮めない。',
 'ekop':'印刷された(βξ−aβ(v/V)ξ)²+(η−bβ(v/V)ξ)²+(ζ−cβ(v/V)ξ)²の左辺を構成する。第一項も差として明示し、全三成分の符号と二乗を保つ。',
 'ekoq':'有効な三位置とeklzの下で、τ=0の実際の逆Lorentz球面seceへの所属と、ekop=R²という印刷式が双方向に一致する条件。原点や面上だけの一致ではない。',
 'ekor':'同じ幾何条件の全有効三位置についてekoqを要求し、新系時刻零の球面を表示式で過不足なく表す。旧系時刻零を同時に要求しない。',
 'ekos':'前の質問と同じ68設定のうちK,V,波範囲,同じ部分,状況を固定し、残る63役割でekn7なら同じ幾何のekooとなるという内容。放射部分と無関係な単独の図形へ替えない。',
 'ekot':'同じ63役割・同じekn7の下で、同じ球面のτ=0の表示式ekorを述べる内容。両内容の半径・方向・V/vと参照範囲を共有する。',
 'ekou':'著者による楕円体面の主張uhと、τ=0の式の表示eisox、コロンによる表示導入ufと順序ue、先の同じ光の部分の質問への後方参照eisraを保つ。原文にない導出済み・自明性を追加しない。',
 'ekov':'同じ面の楕円体としての記述と零時刻方程式の提示ekouを述べるメッセージ。',
 'ekow':'u0206–u0207の一続きの文を同じ著者・論説へ帰属し、前のエネルギー質問に続ける。',
}
LIMITS=[
 '原刊913頁のu0206–u0207を一文として読む。M0358はτ=0、M0359は三つの差の二乗和=R²であり、保存MathMLと原刊の対応を確認する。ξ,η,ζは既出k=zbmの三位置である。',
 '楕円体面は可逆な線形写像による正半径球面の像という一般的な幾何学の意味で構成する。Lの行列式はD>0であり、LᵀLの二次形式は正定値となる。主軸の直交対角化や半軸値を別途求めたとはしない。せん断項を落として座標軸に沿う回転楕円体へ替えない。',
 '形状の説明は新系の任意時刻で保持し、表示式だけをτ=0へ限定する。中心は一般に新系で動く。原刊はτ=0の表示を選んでおり、新旧時刻零が同じ出来事集合であるとはしない。',
 '正の半径と可逆性により面は非空・閉・有界で、面とその内部の区別を保つ。球の特殊形を楕円体から排除せず、零相対速度も許容する。厳密な光速以上はeklzが拒否する。全実数の位相的性質や主軸定理を自動証明したという記録ではない。',
 '前のekn7の同じ物理部分・波・校正単位・領域履歴と初期部分輸送を引き継ぐ。今回の図形式を物理対象の同一性又は無流出入の代用にしない。球面は物質的な剛体殻や光速で静止する慣性観測者ではない。',
 'im bewegten System betrachtetは同じ対象のk座標による同時形状として読む。著者による考察の視点であり光学的な写真像や網膜像ではない。著者の形状主張・式の提示と、その数学的又は物理的真理の証明を分ける。',
 '有理切断の対照と多項式補題、無限域の有限評価拒否、原文の通読判断はそれぞれの範囲を保持する。後続u0208–u0209のS/S′命名と体積比、以後の総量比は今回の完成範囲へ含めない。',
]

def triangle():
    V=v('light');speed=v('speed');one=k('bb','n p b b');beta=k('soy',V,speed);ratio=k('shv',speed,k('sjd',V))
    return [k('sdn2',V,speed,one,v('ax')),*[k('shv',v(n),k('shv',beta,ratio)) for n in ('ay','az')]]

def definitions():
    text=''.join('r '+n+'[] a.\n' for n in PRIMITIVES);zero=k('bb','n p a b');mul=lambda a,b:k('shv',a,b);axes=('yn','yo','yp')
    xyz=args(XYZ);factor,sy,sz=args(TRIANGLE);x,y,z=xyz
    text+=define('ekoi',TRIANGLE+XYZ,k('ekbe',mul(factor,x),k('bf',y,mul(sy,x)),k('bf',z,mul(sz,x))),POINT)
    ix=mul(x,k('sjd',factor));text+=define('ekoj',TRIANGLE+XYZ,k('ekbe',ix,k('bd',y,mul(sy,ix)),k('bd',z,mul(sz,ix))),POINT)
    first=k('ekoi',*args(TRIANGLE),*xyz);second=k('ekoj',*args(TRIANGLE),*xyz)
    compositions=[k('ekoj',*args(TRIANGLE),*[app(first,k(a)) for a in axes]),k('ekoi',*args(TRIANGLE),*[app(second,k(a)) for a in axes])]
    text+=define('ekok',TRIANGLE+XYZ,both(*(k('ba',a) for a in args(TRIANGLE+XYZ)),k('bg',zero,factor),*(k('sca',app(p,k(a)),x) for p in compositions for a,x in zip(axes,xyz))))
    shifted=[k('bf',x,c) for x,c in zip(xyz,args(CENTER))];point=k('ekoi',*args(TRIANGLE),*shifted);norm=k('seag',*[app(point,k(a)) for a in axes])
    text+=define('ekol',ELLIPSOID+XYZ,both(*(k('ba',a) for a in args(ELLIPSOID+XYZ)),k('bg',zero,factor),k('bg',zero,v('radius')),k('sca',norm,mul(v('radius'),v('radius')))))
    V=v('light');speed=v('speed');time=v('time');beta=k('soy',V,speed);tri=triangle()
    target=[mul(mul(beta,k('bf',mul(V,v('ax')),speed)),time),*[mul(mul(mul(V,v(n)),beta),time) for n in ('ay','az')]]
    text+=define('ekom',GEOMETRY+[('time',R)],k('ekoj',*tri,*target),POINT)
    center=k('ekom',*args(GEOMETRY),time);centers=[app(center,k(a)) for a in axes]
    actual=app(k('secd',*args(GEOMETRY)),*args(COORDS));shape=k('ekol',*tri,v('radius'),*centers,*xyz)
    text+=define('ekon',GEOMETRY+COORDS,both(k('eklz',*args(GEOMETRY)),*(k('ba',a) for a in args(COORDS)),k('ekok',*tri,*[k('bf',x,c) for x,c in zip(xyz,centers)]),op('z',actual,shape)))
    valid=both(*(k('ba',a) for a in args(COORDS)))
    text+=define('ekoo',GEOMETRY,both(k('eklz',*args(GEOMETRY)),k('bg',zero,tri[0]),quantified('f',COORDS,op('y',valid,k('ekon',*args(GEOMETRY+COORDS))))))
    ratio=mul(speed,k('sjd',V));first=mul(beta,x);terms=[k('bf',first,mul(mul(mul(v('ax'),beta),ratio),x)),*[k('bf',pos,mul(mul(mul(v(n),beta),ratio),x)) for n,pos in [('ay',y),('az',z)]]]
    text+=define('ekop',GEOMETRY+XYZ,k('seag',*terms),R)
    equation=k('sca',k('ekop',*args(GEOMETRY+XYZ)),mul(v('radius'),v('radius')))
    text+=define('ekoq',GEOMETRY+XYZ,both(k('eklz',*args(GEOMETRY)),*(k('ba',a) for a in xyz),op('z',k('sece',*args(GEOMETRY+XYZ)),equation)))
    text+=define('ekor',GEOMETRY,both(k('eklz',*args(GEOMETRY)),quantified('f',XYZ,op('y',both(*(k('ba',a) for a in xyz)),k('ekoq',*args(GEOMETRY+XYZ))))))
    setting=[FIXED.get(n,v(n)) for n,t in SETTING];geometry=[FIXED.get(n,v(n)) for n,t in GEOMETRY]
    for name,target in [('ekos','ekoo'),('ekot','ekor')]:text+=content(name,quantified('f',VARIABLES,op('y',k('ekn7',*setting),k(target,*geometry))))
    p=v('point');author=k('rd');node=k('eistu');display=k('eistv');scope=k('eistk')
    text+=content('ekou',both(k('uh',node,author,quote('ekos'),scope,p),k('eisox',display,quote('ekot'),p),k('uf',author,node,display,p),k('ue',node,display,p),k('eisra',node,author,k('eirf'),k('eistt'),quote('ekod'),quote('ekos'),scope,p)))
    text+='d ekov[] f[j s[k ekou[]]].\n'
    text+=define('ekow',[],both(k('eir3',node,author,k('eirf'),quote('ekov'),k('ri')),k('ue',k('eistt'),node,k('ri')),op('u',op('e',k('eistt'),node)),op('u',op('e',node,display))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX
    assert not (set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='ekow',arguments=[]))]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='same_radiation_boundary_as_ellipsoid_and_zero_time_equation',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[INDEX]).document
    ann=json.loads(read('data/portion-energy-inquiry-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
