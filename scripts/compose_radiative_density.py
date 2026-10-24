"""Bind radiative density, cycle means and flux relative to moving boundaries."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_seventh_section_heading import ROOT,read
from scripts.compose_observed_intensity import MODEL,COEFFICIENT,VECTOR,FLOW,EXTENDED,AMPLITUDE,HARMONIC,TIMEWAVE,FALSE
from scripts.compose_wave_transform_application import transformed
from scripts.compose_field_equations import FIELD,REGION,TAU
from scripts.compose_material_relative_frame import define,args
from scripts.compose_limits import R,F,v,call as k,app,op,both,lam

PARENT='examples/v014/einstein-seventh-section-heading.noema';PARENT_BASIS='data/seventh-section-heading-basis-v1.json'
FULL='examples/v014/einstein-radiative-density.noema';CORE='examples/v014/radiative-density-core.noema'
BASIS='data/radiative-density-basis-v1.json';ANNOTATIONS='data/radiative-density-identifiers-v1.json'
DENSITY=[(n,R) for n in ('coefficient','light','ex','ey','ez','hx','hy','hz')]
SCALAR=DENSITY+[('sine',F),('phase',TAU)]
DENSITY_MODEL=MODEL+[('light',R)]
PHYSICAL=[(n,'a') for n in ('wave','process','frame','lengthunit','timeunit','energyunit')]+[('region',REGION),('densityfield',TAU),('scope','a'),('context','d')]
AVERAGE=DENSITY+[('profile',F)]+[(n,R) for n in ('lower','upper','integrated','density')]
CYCLE=DENSITY+TIMEWAVE+[('density',R)]
PLANE=[(n,R) for n in ('coefficient','light','pi','nx','ny','nz','ex','ey','ez','hx','hy','hz','amplitude','density')]
MOVING=[('flux',FIELD),('densityfield',TAU),('velocity',FIELD)]
TRANSPORT=SCALAR+[(n,R) for n in ('nx','ny','nz')]
SETTING=EXTENDED+[(n,R) for n in ('amplitude','newamplitude')]+[('energyunit','a')]+[(n,R) for n in ('coefficient','density','newdensity')]
PRIMITIVES={
 'eistj':(PHYSICAL,'同じwaveのprocessについて、同じframe・長さ時間及びエネルギー単位・regionで、densityfieldが各同時刻の空間の単位体積当たり電磁エネルギーを表すスカラー場モデルとしてscopeの考察に採用されるという物理的対応。体積単位は同じ校正された直交空間軸のlengthunitの三乗、エネルギーは場から物質への仕事及び他形態との交換収支で扱い、energyunitは同じ力とその方向の変位の積の仕事基準に整合する。数値関数だけから物理的役割を認めず、観測実施や現実の厳密場への無限精度の一致を要求しない。平均、具体的な場の二乗式、三次元積分、選んだ境界の運動、対象の同一性や保存則は別に合成し、この関係だけから認定しない。'),
}
MEANINGS={
 'ekkw':'κ/(2V)を同じ電気三係数と磁気三係数の二乗和へ掛けた、共通波形を掛ける前のエネルギー密度係数。Vの正値と物理単位の対応は呼出側で要求する。',
 'ekkx':'同じekkwへ同じ時間profileの二乗を掛ける瞬間密度の時間関数。波形の二乗平均を初めから1/2にしない。',
 'ekky':'同じ係数・光速度・六係数・正弦・四座標位相からekkw*sin²Φという密度スカラー場を構成する。',
 'ekkz':'同じ波・過程・系・単位・領域・範囲・状況について正のVとκ及び既存eisteの校正を保持し、同じekkyをeistjの密度場モデルへ結ぶ。流のモデルだけから密度の物理的対応を推論しない。',
 'ekk2':'有効で正のVとκ、既存の積分で指定したpiについて4*pi*κ=Vを要求する。原文の電磁単位規約に合わせる条件であり、任意の単位系でκの数値を同じとしない。',
 'ekk3':'有限の正長区間の同じ瞬間密度ekkxのRiemann積分integratedと、integrated=(upper−lower)*densityを結ぶ平均密度。六係数は有効な実数、Vとκは正、平均密度は非負とする。',
 'ekk4':'同じ正弦・余弦・pi・周期・位相率・原点・周期数のekjzと、同じ0からperiodまでの積分平均ekk3を結ぶ。積分値はperiod*density。各系の周期を共有し直さない。',
 'ekk5':'同じ横波条件seajと非負電気振幅seal、原文単位係数ekk2についてdensity=ekkw/2を要求する周期平均の数値条件。位相平均の解析条件はekk4で別に結ぶ。',
 'ekk6':'同じ流fluxから、同じdensityfieldと同じ境界の局所velocityの積を成分ごとに引いたベクトル場。動く面に相対的な流の候補を同じ座標時刻で構成する。',
 'ekk7':'同じVと方向nx,ny,nzのV*nを、各空間軸で一定の速度ベクトル場として返す。非空間役割の拡張成分は零。特定の面への帰属や軌跡は別に要求する。',
 'ekla':'同じκ,V,六係数,正弦,位相のエネルギー流ekkaと密度ekkyについて、同じV*nで動く面への相対流ekk6を構成する。境界が光速度で動くことを、観測者静止系のv=Vへ置き換えない。',
 'eklb':'同じ66役割の物理的な波・二系・校正・近似・位相・周期・旧新振幅に、両系の横波、同じ原文単位係数、両系の密度モデルとそれぞれの周期平均を結ぶ。正面接近の角や非零密度を追加せず、u0201の境界主張を前提へ輸入しない。',
 'eklc':'同じpi・旧振幅・旧周期平均密度についてsedrの8*pi*density=amplitude²を述べる数値的帰結。物理的適用条件はeklbに分離する。',
 'ekld':'同じpi・新振幅・新周期平均密度についてsedrの8*pi*newdensity=newamplitude²を述べる数値的帰結。旧密度を新密度へ流用しない。',
}
LIMITS=[
 '原刊913頁のu0203–u0205を一続きとして読み、まず密度・平均・動く境界に相対的な流という依存群を構成する。今回は著者主張を追加せず、全単位意味判断を増やさない。',
 'A²/(8pi)は同じ真空横波の電気又は等しい磁気振幅による周期平均密度として読む。瞬間密度はκ/(2V)(E0²+H0²)sin²Φであり、横波かつκ=V/(4pi)ならA²*sin²Φ/(4pi)。平均二乗1/2は同じ正弦の周期積分へ結ぶ。この平均読解は明示した理想化で、原文に時間平均という語が印字されているとはしない。',
 '新系について省略されたpro Volumeneinheitを、同じ文の前半及び後続の体積との積との照応から補い、A′²/(8pi)も平均密度と読む。総エネルギーや単位時間・単位面積の強度と同一視しない。',
 '密度の物理的役割は同じ仕事・エネルギー交換と単位へ結ぶ。eistjは領域上のモデルへの対応であり、具体式・平均・面の運動・同じ光の集合を原始関係の中へ隠さない。両系の周期はそれぞれの位相率と観測経路の原点を保つ。',
 '境界速度wに対する流はJ−u*wである。横波でJ=V*n*u、w=V*nなら点ごとに零となる。表面の法線を波の法線と同一視せず、成分ごとに零な相対流はどの表面法線への射影でも零になる。この局所計算だけでは球面の同一性、全時刻の領域、閉じた光の集合又は総量保存を認定しない。',
 '既存の一般振幅主張・非横波の反例・光行差の結線角と印刷式の不整合は保持する。今回の密度の読みでは横波を明示し、過去の条件を遡及変更しない。',
 '有理数piの検査標本は積分境界を差し替える診断であり円周率そのものではない。関数と積分の未知入力は拒否する。有限検査及び分母を払った有理多項式補題は、全実数上の積分・物理法則・原文との意味同義性の自動証明ではない。',
 '残るのはu0203第一文の相対性原理への根拠付けと著者帰属、同体積ならという反実仮想と実際の体積不一致、同じ波の集合・同時断面・球面運動・局所無流出入からの帰結、u0205の言換えと新系エネルギーの問い、u0202の節主題及び後続本文。',
]

def definitions():
    text=''.join('r '+n+'['+' '.join(t for n,t in fields)+'] c.\n' for n,(fields,meaning) in PRIMITIVES.items())
    zero=k('bb','n p a b');one=k('bb','n p b b');two=k('bb','n p c b');four=k('bb','n p e b');half=k('bb','n p b c')
    mul=lambda x,y:k('shv',x,y);positive=lambda x:both(k('ba',x),k('bg',zero,x))
    V=v('light');coef=v('coefficient');amps=[v(n) for n in ('ex','ey','ez','hx','hy','hz')]
    value=mul(mul(coef,k('sjd',mul(two,V))),k('bd',k('seag',*amps[:3]),k('seag',*amps[3:])))
    text+=define('ekkw',DENSITY,value,R)
    p=app(v('profile'),v('time'))
    text+=define('ekkx',DENSITY+[('profile',F)],lam('time',R,mul(k('ekkw',*args(DENSITY)),mul(p,p))),F)
    coords=[v(n) for n in ('x','y','z','time')];p=app(v('sine'),app(v('phase'),*coords))
    scalar='i['+' '.join(n+' '+R for n in ('x','y','z','time'))+']['+mul(k('ekkw',*args(DENSITY)),mul(p,p))+']'
    text+=define('ekky',SCALAR,scalar,TAU)
    actual={n:v(n) for n,t in DENSITY_MODEL}|{'densityfield':k('ekky',*args(SCALAR))}
    text+=define('ekkz',DENSITY_MODEL,both(positive(V),positive(coef),k('eiste',*args(COEFFICIENT)),k('eistj',*[actual[n] for n,t in PHYSICAL])))
    text+=define('ekk2',[(n,R) for n in ('coefficient','light','pi')],both(positive(V),positive(coef),k('sedi',v('pi')),k('sca',mul(mul(four,v('pi')),coef),V)))
    lo,hi,integrated,rho=map(v,('lower','upper','integrated','density'))
    text+=define('ekk3',AVERAGE,both(*(k('ba',v(n)) for n,t in AVERAGE if t==R),positive(V),positive(coef),k('bg',lo,hi),k('bc',zero,rho),k('sede',lo,hi,k('ekkx',*args(DENSITY),v('profile')),integrated),k('sca',integrated,mul(k('bf',hi,lo),rho))))
    profile=k('ekc5',v('sine'),v('rate'),v('offset'));period=v('period')
    text+=define('ekk4',CYCLE,both(k('ekjz',*args(TIMEWAVE)),k('ekk3',*args(DENSITY),profile,zero,period,mul(period,rho),rho)))
    direction=[v(n) for n in ('nx','ny','nz')]
    text+=define('ekk5',PLANE,both(k('ekk2',coef,V,v('pi')),k('seaj',*direction,*amps),k('seal',*amps[:3],v('amplitude')),k('ba',rho),k('sca',rho,mul(half,k('ekkw',*args(DENSITY))))))
    relative=k('bf',app(app(v('flux'),v('axis')),*coords),mul(app(v('densityfield'),*coords),app(app(v('velocity'),v('axis')),*coords)))
    text+=define('ekk6',MOVING,'i[axis a][i['+' '.join(n+' '+R for n in ('x','y','z','time'))+']['+relative+']]',FIELD)
    constant=app(k('ekbe',*(mul(V,x) for x in direction)),v('axis'))
    text+=define('ekk7',[('light',R)]+[(n,R) for n in ('nx','ny','nz')],'i[axis a][i['+' '.join(n+' '+R for n in ('x','y','z','time'))+']['+constant+']]',FIELD)
    text+=define('ekla',TRANSPORT,k('ekk6',k('ekka',*args(VECTOR)),k('ekky',*args(SCALAR)),k('ekk7',V,*direction)),FIELD)
    speed=v('speed');newamps,shifted,_,phase=transformed(speed)
    oldphase=k('ekbf',V,v('rate'),v('ax'),v('ay'),v('az'));oldregion=k('ekau',v('space'),v('lower'),v('upper'));newregion=k('eken',speed,v('space'),v('lower'),v('upper'),V)
    models=[];averages=[]
    for frame,p,coefficients,region in ((v('frame'),oldphase,amps,oldregion),(k('zbm'),phase,newamps,newregion)):
        replacements=dict(frame=frame,phase=p,region=region,**dict(zip(('ex','ey','ez','hx','hy','hz'),coefficients)))
        models.append(k('ekkz',*[replacements.get(n,v(n)) for n,t in DENSITY_MODEL]))
    for coefficients,rate,offset,p,f,density in ((amps,v('rate'),zero,v('oldperiod'),v('frequency'),rho),(newamps,shifted[0],v('newoffset'),v('newperiod'),v('newfrequency'),v('newdensity'))):
        averages.append(k('ekk4',coef,V,*coefficients,*args(HARMONIC),rate,offset,p,f,density))
    ampactual=[FALSE if n=='magneticside' else v(n) for n,t in AMPLITUDE]
    text+=define('eklb',SETTING,both(k('eket',*args(EXTENDED)),k('ekev',V,speed),k('ekia',*ampactual),k('ekk2',coef,V,v('pi')),k('seaj',*[v(n) for n in ('ax','ay','az')],*amps),k('seaj',*shifted[1:],*newamps),*models,*averages))
    text+=define('eklc',SETTING,k('sedr',v('pi'),mul(v('amplitude'),v('amplitude')),rho))
    text+=define('ekld',SETTING,k('sedr',v('pi'),mul(v('newamplitude'),v('newamplitude')),v('newdensity')))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==385
    assert not (set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,t in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='radiative_density_cycle_and_moving_boundary_dependencies',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[]).document
    ann=json.loads(read('data/seventh-section-heading-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
