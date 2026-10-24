"""Integrate the phase-averaged density of one physical radiation portion."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_light_region_slices import ROOT,read,LOCATION,VOLUMES,GEOMETRY,OLD,XYZ
from scripts.compose_density_relativity import BASE
from scripts.compose_radiative_density import DENSITY,DENSITY_MODEL,PHYSICAL,HARMONIC
from scripts.compose_wave_transform_application import transformed
from scripts.compose_field_equations import REGION,TAU
from scripts.compose_material_relative_frame import define,args
from scripts.compose_limits import R,F,v,call as k,app,op,both,lam,quant as q

PARENT='examples/v014/einstein-light-region-slices.noema';PARENT_BASIS='data/light-region-slices-basis-v1.json'
FULL='examples/v014/einstein-mean-light-energy.noema';CORE='examples/v014/mean-light-energy-core.noema'
BASIS='data/mean-light-energy-basis-v1.json';ANNOTATIONS='data/mean-light-energy-identifiers-v1.json'
PROFILE=DENSITY+[('sine',F),('offset',R)]
MEAN=PROFILE+[('cycle',R),('density',R)]
SPATIAL=DENSITY+[('sine',F),('phase',TAU),('cycle',R),('density',R),('region',REGION),('portionregion',REGION),('time',R)]
FRAME=DENSITY_MODEL+[('portion','a'),('portionregion',REGION),('cosine',F),('pi',R),('cycle',R),('time',R),('density',R)]
INTEGRAL=[(n,R) for n in ('radius','pi','factor','density','energy')]
INTEGRALS=INTEGRAL+[('volume',R)]
TOTAL=BASE+[('portion','a')]+[(n,R) for n in ('radius','volume','newvolume','energy','newenergy')]
ARITHMETIC=[(n,R) for n in ('pi','amplitude','newamplitude','volume','newvolume','energy','newenergy')]
MEANINGS={
 'ekma':'同じ密度係数ekkwと正弦について、位相原点offsetへ独立な位相変数thetaを加えたK*sin(offset+theta)²を返す。時間の進行や領域の移動をthetaと同一視しない。',
 'ekmb':'正の位相一周期cycleの0からcycleまでekmaを積分し、その値がcycle*densityであるという位相平均。正のVと係数、非負の平均密度、有効な位相原点を要求する。正弦・周期の同定は利用側で別に要求する。',
 'ekmc':'指定時刻と有効な三空間座標がportionregionに属するなら、同じ点が密度モデルのregionにも属し、同じphaseのその点の値を位相原点としてekmbが成立する。部分の外では密度一致を要求せず、一つの基準点だけの平均を全領域へ転用しない。',
 'ekmd':'有効な指定時刻の全ての有効な三空間座標にekmcを要求する。領域を固定した各点の位相平均が同じdensityである、一様平均の条件。実数全域を有限標本に変更しない。',
 'ekme':'同じwave/process/frame/単位/考察範囲に属する瞬間密度モデルekkzと放射部分の領域割当eistm、同じ正弦余弦・pi・最小位相一周期ekc3、同じ時刻断面での全点平均ekmdを結ぶ。一様な平均モデルとしての物理的帰属であり、部分の内部生成消滅や保存を主張しない。',
 'ekmf':'正のRとfactor、積分で定めるpi及び非負密度について、−R/factorからR/factorまでdensity*pi*(R²−factor²*x²)を積分した値がenergyである。球・楕円体断面の一様平均密度を空間積分する。体積の既知値との積を前件にしない。',
 'ekmg':'ekmfの同じ区間・断面多項式で、密度を掛けない積分値を正のvolumeへ結ぶ。二積分が同じ領域を扱い、energy=volume*densityは別の帰結候補ekmhへ置く。',
 'ekmh':'有効な正の体積と非負の密度・総量についてenergy=density*volumeという関係。単独で物理的な帰属や空間積分の存在を認定しない。',
 'ekmi':'先行の同じ70役割で、校正された波の基礎設定と旧新の周期平均密度、同じ光の部分・二系の同時体積を保持し、各時刻零断面全点の位相平均及びその重み付き空間積分を二つの総エネルギーへ結ぶ。旧系factor=1、新系factor=β(1−av/V)、両系の平均密度はそれぞれのekleを使う。総量と密度を区別し、総量比を前提にしない。',
 'ekmj':'ekmiと同じ70役割の旧新の総エネルギーが、それぞれ同じ振幅・piからの平均密度と同時体積の積であるという帰結候補。物理的前件と空間積分の構成はekmiへ分ける。',
 'ekmk':'同じpiと旧新振幅に対して、旧振幅・旧総量が正、新側は非負、二体積が正であり、各総量がそれぞれのekle平均密度と体積の積であるという代数的前件。二体積を等しいともLorentz体積比に従うともここでは仮定しない。',
 'ekml':'同じ非零の旧振幅・旧総量及び非負の新側についてE′*A²=E*A′²を要求する。分母が正なのでE′/E=A′²/A²と同値な、除算しない比の記述。0/0を成功としない。',
 'ekmm':'ekmkの平均密度と総量の条件に、正の二体積の等しさekl6を加えるなら、同じ値の比ekmlとなるという代数的な条件規則。実際の体積変換式を前件に入れず、任意の比の二振幅で同体積の仮定を検査できる。著者の反実仮想の発話やその帰属はまだ追加しない。',
}
LIMITS=[
 'u0203第二文の同体積の条件文とu0205のエネルギーの問いへ必要な依存群。前版386主張・既存の通読判断を保持し、新しい原文一文全体の意味判断は追加しない。',
 'A²/(8*pi)を先行版と同じ周期平均密度として読む。ここで総量を与える際は、同じ点・同じ領域を固定し正弦の位相原点を一周期ずらした平均を採る。この位相平均は正弦の周期平均に一致する標準的な解析の読みで、必要な全点の積分等式を明示する。特定位相の有限球の瞬間エネルギー又は移動境界を追う時間平均とは区別する。',
 '全点の位相平均は、同じ部分の時刻断面が密度モデルの領域内にあることとともに要求する。局所近似の適用範囲の外へ自動的に外挿せず、その仮定が満たせる半径・時刻範囲で使う。eistmによる全領域履歴の割当は領域を指示するためであり、全時刻で密度法則を適用したという主張ではない。',
 '一様な平均モデルでは、各点の平均密度の空間積分を平均総エネルギーと定義する。有限有界領域の連続な正弦モデルの下で瞬間総量の位相平均との一致を標準的な積分の線形性・順序交換として読む。Noemaでは先に局所平均を定め、その平均を同じ断面多項式で積分する手順を明示し、積分交換定理の全実数上の自動証明とはしない。',
 '物理的なエネルギーの意味と単位はeistj/ekkz/eisteの仕事・交換収支へ、どの光の部分かはeistmへ既に接続している。新しい文全体を原始関係に格納せず、一般関係の追加はない。球と楕円体の断面積の幾何学的な読みは前版sedpを引き継ぐ。',
 '同体積の代数規則ekmmは、同じ平均密度の説明と仮定した二体積を共有する。実際の幾何が強制する体積比を同時に仮定して前件を空にする構成は避ける。ただし原文のEs wäre ... wenn ...とdaherの談話上の提示、同じ対象を保つ仮定の作用域、後続の一般的な体積不一致は次の本文統合で必要である。',
 '零振幅・零平均密度・零総エネルギーを物理的モデルからは排除しない。比を述べるekmk/ekmlでは旧側の分母を正に限定する。有限切断モデルや多項式補題は、全実数域の積分の存在一意性、物理法則又は原文の意味同義性の自動証明ではない。',
]

def definitions():
    z=k('bb','n p a b');o=k('bb','n p b b');mul=lambda a,b:k('shv',a,b)
    positive=lambda x:both(k('ba',x),k('bg',z,x));nonnegative=lambda x:both(k('ba',x),k('bc',z,x))
    p=app(v('sine'),k('bd',v('offset'),v('theta')))
    text=define('ekma',PROFILE,lam('theta',R,mul(k('ekkw',*args(DENSITY)),mul(p,p))),F)
    text+=define('ekmb',MEAN,both(*(k('ba',v(n)) for n,t in DENSITY),positive(v('coefficient')),positive(v('light')),positive(v('cycle')),k('ba',v('offset')),nonnegative(v('density')),k('sede',z,v('cycle'),k('ekma',*args(PROFILE)),mul(v('cycle'),v('density')))))
    coords=[*args(XYZ),v('time')];offset=app(v('phase'),*coords)
    mean=[offset if n=='offset' else v(n) for n,t in MEAN]
    text+=define('ekmc',SPATIAL+XYZ,op('y',both(*(k('ba',x) for x in coords),app(v('portionregion'),*coords)),both(app(v('region'),*coords),k('ekmb',*mean))))
    body=k('ekmc',*args(SPATIAL),*args(XYZ))
    for n,t in reversed(XYZ):body=q('f',n,t,body)
    text+=define('ekmd',SPATIAL,both(k('ba',v('time')),body))
    loc={n:v(n) for n,t in FRAME}|{'region':v('portionregion')}
    text+=define('ekme',FRAME,both(k('ekkz',*args(DENSITY_MODEL)),k('eistm',*[loc[n] for n,t in LOCATION]),k('ekc3',*args(HARMONIC)),k('ekmd',*args(SPATIAL))))
    radius=v('radius');factor=v('factor');rho=v('density');energy=v('energy');volume=v('volume');width=mul(radius,k('sjd',factor))
    area=lam('x',R,k('sedl',v('pi'),radius,mul(factor,v('x'))))
    weighted=lam('x',R,mul(rho,app(area,v('x'))))
    text+=define('ekmf',INTEGRAL,both(positive(radius),positive(factor),k('sedi',v('pi')),nonnegative(rho),nonnegative(energy),k('sede',k('be',width),width,weighted,energy)))
    text+=define('ekmg',INTEGRALS,both(k('ekmf',*args(INTEGRAL)),positive(volume),k('sede',k('be',width),width,area,volume)))
    text+=define('ekmh',[(n,R) for n in ('volume','density','energy')],both(positive(volume),nonnegative(rho),nonnegative(energy),k('sca',energy,mul(volume,rho))))
    V=v('light');speed=v('speed');newamps,shifted,_,phase=transformed(speed)
    oldphase=k('ekbf',V,v('rate'),v('ax'),v('ay'),v('az'));oldregion=k('ekau',v('space'),v('lower'),v('upper'));newregion=k('eken',speed,v('space'),v('lower'),v('upper'),V)
    regions=[k('eklw',*args(OLD)),k('eklx',*args(GEOMETRY))];D=k('sdn2',V,speed,o,v('ax'))
    pair={n:v(n) for n,t in TOTAL}|dict(newframe=k('zbm'),scope=k('eistk'))
    conditions=[k('eklp',*args(BASE)),k('eklg',*args(BASE)),k('eklh',*args(BASE)),k('ekl4',*[pair[n] for n,t in VOLUMES])]
    rows=[(v('frame'),oldphase,[v(n) for n in ('ex','ey','ez','hx','hy','hz')],oldregion,regions[0],v('amplitude'),o,v('energy'),v('volume')),(k('zbm'),phase,newamps,newregion,regions[1],v('newamplitude'),D,v('newenergy'),v('newvolume'))]
    for frame,p,coefficients,region,portionregion,amp,factor,E,S in rows:
        rho=k('ekle',v('pi'),amp)
        overrides=dict(frame=frame,phase=p,region=region,portionregion=portionregion,scope=k('eistk'),time=z,density=rho,**dict(zip(('ex','ey','ez','hx','hy','hz'),coefficients)))
        conditions.append(k('ekme',*[overrides.get(n,v(n)) for n,t in FRAME]))
        conditions.append(k('ekmg',radius,v('pi'),factor,rho,E,S))
    text+=define('ekmi',TOTAL,both(*conditions))
    text+=define('ekmj',TOTAL,both(*[k('ekmh',v(S),k('ekle',v('pi'),v(A)),v(E)) for S,A,E in [('volume','amplitude','energy'),('newvolume','newamplitude','newenergy')]]))
    guard=both(k('sedi',v('pi')),positive(v('amplitude')),nonnegative(v('newamplitude')),positive(v('energy')),nonnegative(v('newenergy')))
    text+=define('ekmk',ARITHMETIC,both(guard,*[k('ekmh',v(S),k('ekle',v('pi'),v(A)),v(E)) for S,A,E in [('volume','amplitude','energy'),('newvolume','newamplitude','newenergy')]]))
    ratio_fields=[(n,R) for n in ('amplitude','newamplitude','energy','newenergy')]
    text+=define('ekml',ratio_fields,both(positive(v('amplitude')),nonnegative(v('newamplitude')),positive(v('energy')),nonnegative(v('newenergy')),k('sca',mul(v('newenergy'),mul(v('amplitude'),v('amplitude'))),mul(v('energy'),mul(v('newamplitude'),v('newamplitude'))))))
    text+=define('ekmm',ARITHMETIC,op('y',both(k('ekmk',*args(ARITHMETIC)),k('ekl6',v('volume'),v('newvolume'))),k('ekml',*args(ratio_fields))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==386
    assert not set(MEANINGS)&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']
    added=doc['declarations'][len(old['declarations']):]
    basis=dict(status='phase_mean_density_spatial_energy_and_equal_volume_rule_dependencies',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[]).document
    ann=json.loads(read('data/light-region-slices-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
