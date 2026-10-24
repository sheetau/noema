"""Keep one radiation portion across calibrated simultaneous volume slices."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_density_unit_scope import ROOT,read
from scripts.compose_field_equations import REGION,POINT
from scripts.compose_material_relative_frame import define,args
from scripts.compose_limits import R,v,call as k,app,op,both

PARENT='examples/v014/einstein-density-unit-scope.noema';PARENT_BASIS='data/density-unit-scope-basis-v1.json'
FULL='examples/v014/einstein-light-region-slices.noema';CORE='examples/v014/light-region-slices-core.noema'
BASIS='data/light-region-slices-basis-v1.json';ANNOTATIONS='data/light-region-slices-identifiers-v1.json'
GEOMETRY=[(n,R) for n in ('light','speed','ax','ay','az','radius')]
OLD=[(n,t) for n,t in GEOMETRY if n!='speed']
XYZ=[(n,R) for n in ('x','y','z')];SPACE='h['+' '.join(t for n,t in XYZ)+'] c'
LOCATION=[(n,'a') for n in ('portion','wave','process','frame','lengthunit','timeunit')]+[('region',REGION),('scope','a'),('context','d')]
PAIR=[(n,'a') for n in ('portion','wave','process','frame','newframe','lengthunit','timeunit','scope')]+[('context','d')]+GEOMETRY
VOLUMES=PAIR+[(n,R) for n in ('pi','volume','newvolume')]
PRIMITIVES={
 'eistm':(LOCATION,'同じwaveのprocessから選んだportionという放射の部分系について、frameの校正された長さ時間単位によるregionを、その空間的な範囲の全時刻履歴としてscopeのモデルに割り当てる。単なる名前や任意のラベル集合ではなく、同じ電磁的な過程のどの部分を追うかを固定する物理的な部分系と座標領域の対応である。波全体と選んだ部分を区別し、無関係な波、別の部分、外接領域の余分な空間を取り替えない。領域はその部分の包絡する占有範囲であり、正弦場の瞬間的な節を穴にしない。光子の個数・粒子存在論や実測済みは要求しない。この割当自体は仮定としても使え、指定領域の運動式、別系との座標対応、流入出の不存在、内部生成消滅の不存在、同じ内容を保つという保存法則、エネルギー値は別に合成する。'),
}
MEANINGS={
 'eklw':'同じV・単位方向三成分・正の半径で、seccの光速度並進する閉球内部を四座標領域として返す。球面だけのsecbと区別する。',
 'eklx':'eklwの同じ閉内部を、同じV/vの逆Lorentz変換s6mで新座標の四次元領域へ写す。領域を別の球へ選び直さない。',
 'ekly':'指定したregionの時刻引数をtimeに固定して三空間座標の性質を返す。どちらの系のregionかを呼出側で保ち、旧時刻と新時刻を同一視しない。',
 'eklz':'有効な実数のV/v・三方向・R、許容速度s45、正の半径と単位方向を要求する共通の幾何条件。零速度及び符号付き速度を許し、光速以上を拒否する。',
 'ekl2':'eklzの条件の下で、secfの新時刻零の二乗距離がR²以下である閉楕円体内部。既存secgの表面を含み、体積を表面だけに割り当てない。',
 'ekl3':'同じ放射部分・波・過程・考察範囲を両系の閉内部eklw/eklxへ帰属し、同じ出来事の標準Lorentz座標写像をeisqtで同じ長さ時間単位へ校正する。両系は異なる座標系であり、数値領域だけから物理的な対象同一性を結論しない。部分の全時刻モデルへの割当はここでは仮定であり、無流出入による保存の証明ではない。',
 'ekl4':'ekl3の同じ対象と座標設定へ、同じR・piの球と新時刻零の楕円体内部の体積積分sedpを結ぶ。両体積の単位は同じlengthunitの三乗。旧新の同時断面を別々に取り、等体積又は比を条件へ先取りしない。',
 'ekl5':'ekl4と同じV/v/aに対する正の二体積がsechのD*S′=Sを満たすという帰結候補。体積積分からの一般的な変数変換の自動証明とは区別する。',
 'ekl6':'指定した有効で正の二体積が等しいという条件。エネルギー比を追加せず、零体積の退化例を除く。',
 'ekl7':'指定した有効で正の二体積が異なるという条件。全ての非零相対速度・方向で成立するとはしない。',
}
LIMITS=[
 'u0203の同体積の条件、u0204の移動球面、u0205の同じ光の集合と新系の問いへ必要な、対象・領域・同時断面・体積の依存群である。今回の386著者主張は全て保持し、新しい文全体の意味判断は行わない。',
 'eistmは放射の部分系と完全な領域履歴の物理的なモデル割当である。従来のsegiによる任意のラベル集合の幾何的不変だけからこの割当を導かない。部分系の指定と、それが閉じていて同じ内容を保つことを分ける。',
 '球と楕円体の体積は既存sedm/sedoの断面積積分として読む。円板断面の中心の平行移動は面積を変えないというユークリッド幾何の解釈を継承する。有限検査の積分境界は全実数上の積分の証明ではなく、piの有理標本も円周率そのものではない。',
 'v/V=3/5、方向(1/3,2/3,2/3)は単位方向でD=(5/4)*(1−(1/3)*(3/5))=1となる。非零速度でも等体積の特殊例がある。u0203のDies ist jedoch nicht der Fallは後続の方向依存式と合わせて、一般には等体積でないという読みを検討する必要がある。全ての方向で不等という文字通りの強い読みはこの例と両立しない。今回はその読解を原文全体の判断に確定しない。',
 '残る接続は、同じ周期又は位相平均モデルでの総エネルギーと平均密度×体積、同体積ならという反実仮想の提示、局所相対流零と球面の全時刻の運動・内部生成消滅の条件からの同じ光の集合、著者のthereforeとd.h.及び質問である。瞬間の有限球のエネルギーを無説明に周期平均へ替えない。',
]

def definitions():
    text=''.join('r '+n+'['+' '.join(t for n,t in fs)+'] c.\n' for n,(fs,m) in PRIMITIVES.items())
    zero=k('bb','n p a b');one=k('bb','n p b b');mul=lambda x,y:k('shv',x,y)
    V,s,a,b,c,radius=map(v,[n for n,t in GEOMETRY]);coords=XYZ+[('time',R)]
    body='i['+' '.join(n+' '+t for n,t in coords)+']['+k('secc',*args(OLD),*args(coords))+']'
    text+=define('eklw',OLD,body,REGION)
    text+=define('eklx',GEOMETRY,k('s6m',V,s,k('eklw',*args(OLD))),REGION)
    text+=define('ekly',[('region',REGION),('time',R)],'i['+' '.join(n+' '+t for n,t in XYZ)+']['+app(v('region'),*args(XYZ),v('time'))+']',SPACE)
    text+=define('eklz',GEOMETRY,both(*(k('ba',v(n)) for n,t in GEOMETRY),k('s45',V,s),k('bg',zero,radius),k('sca',k('seag',a,b,c),one)))
    text+=define('ekl2',GEOMETRY+XYZ,both(k('eklz',*args(GEOMETRY)),*(k('ba',v(n)) for n,t in XYZ),k('bc',k('secf',V,s,a,b,c,*args(XYZ)),mul(radius,radius))))
    mapping='i[point '+POINT+']['+k('s46',V,s,v('point'))+']'
    conditions=[k('eklz',*args(GEOMETRY)),k('va',v('frame')),k('va',v('newframe')),op('u',op('e',v('frame'),v('newframe'))),k('eisqt',v('frame'),v('newframe'),v('lengthunit'),v('timeunit'),mapping,v('context'))]
    for frame,region in [(v('frame'),k('eklw',*args(OLD))),(v('newframe'),k('eklx',*args(GEOMETRY)))]:
        values={n:v(n) for n,t in PAIR}|dict(frame=frame,region=region)
        conditions.append(k('eistm',*[values[n] for n,t in LOCATION]))
    text+=define('ekl3',PAIR,both(*conditions))
    text+=define('ekl4',VOLUMES,both(k('ekl3',*args(PAIR)),k('sedp',*args(GEOMETRY),v('pi'),v('volume'),v('newvolume'))))
    text+=define('ekl5',VOLUMES,k('sech',V,s,a,v('volume'),v('newvolume')))
    for name,equal in [('ekl6',True),('ekl7',False)]:
        eq=k('sca',v('volume'),v('newvolume'))
        text+=define(name,[(n,R) for n in ('volume','newvolume')],both(*(both(k('ba',v(n)),k('bg',zero,v(n))) for n in ('volume','newvolume')),eq if equal else op('u',eq)))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==386
    assert not (set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,t in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='physical_portion_and_simultaneous_volume_dependencies',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[]).document
    ann=json.loads(read('data/density-unit-scope-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
