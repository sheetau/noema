"""Attribute the Doppler consequence to one source model and receiving observer."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_distant_direction_geometry import ROOT,read,SETTING as PRIOR
from scripts.compose_wave_cycle_frequency import HARMONIC
from scripts.compose_wave_transform_application import FAMILY,transformed
from scripts.compose_wave_display import PHASE
from scripts.compose_field_equations import POINT,TAU
from scripts.compose_material_relative_frame import define,args
from scripts.compose_relativity_conjecture import content
from scripts.compose_two_postulates import quote
from scripts.compose_electromotive_wording import bind
from scripts.compose_limits import R,F,D,v,call as k,app,op,both,quant as q

PARENT='examples/v014/einstein-distant-direction-geometry.noema';PARENT_BASIS='data/distant-direction-geometry-basis-v1.json'
FULL='examples/v014/einstein-observed-doppler.noema';CORE='examples/v014/observed-doppler-core.noema'
BASIS='data/observed-doppler-basis-v1.json';ANNOTATIONS='data/observed-doppler-identifiers-v1.json';INDICES=[370,371]
CURVE='h['+R+'] '+POINT;MODELS='h['+R+'] '+CURVE;PHASES='h['+R+'] '+F
DIR=[(n,R) for n in ('ax','ay','az')]
XYZ=[(n,F) for n in ('x','y','z')]
MODEL=[('object','a'),('frame','a'),('lengthunit','a'),('timeunit','a'),('models',MODELS),('parameters',D),('scope','a'),('context','d')]
PHYSICAL_PHASE=[(n,'a') for n in ('subject','wave','process','frame','lengthunit','timeunit')]+[('models',MODELS),('phases',PHASES),('parameters',D),('lower',R),('upper',R),('received','c'),('scope','a'),('context','d')]
SOURCE_CYCLE=HARMONIC+[(n,R) for n in ('light','rate','ax','ay','az','period','frequency','distance')]
SOURCE_FIELDS=[(n,'a') for n in ('source','wave','process','frame','lengthunit','timeunit','scope')]+[('context','d')]+HARMONIC+[(n,R) for n in ('light','rate','ax','ay','az','period','frequency','lower','upper')]
RECEIVER=[(n,'a') for n in ('observer','wave','process','frame','lengthunit','timeunit','scope')]+[('context','d')]+HARMONIC+[('phase',TAU)]+XYZ+[(n,R) for n in ('rate','offset','period','frequency','lower','upper')]
MAPPING=[(n,R) for n in ('light','speed','oldlower','oldupper')]+[('old'+n,F) for n in ('x','y','z')]+XYZ+[('time',R)]
EXTRA=[('oldobslower',R),('oldobsupper',R)]+[('oldobs'+n,F) for n in ('x','y','z')]+[('oldoffset',R),('newoffset',R)]
SETTING=PRIOR+EXTRA
VARIABLES=[(n,t) for n,t in SETTING if n not in ('frame','scope','context','light')]
TRUE=op('e','n p a b','n p a b');FALSE=op('u',TRUE)
PRIMITIVES={
 'eissk':(MODEL,'同じobjectの空間的な位置と時刻を、同じframe・長さ時間単位・scopeで解釈する理想化モデル族がmodelsである。parametersが許すパラメータの各値で、modelsが与える四座標曲線はその対象を表す配置として読む。これは対象の同一性とモデルの物理的役割の対応であり、一つの対象が全モデルの全位置へ同時に実在する条件ではない。静止、遠さ、極限、速度、パラメータの正値は曲線と合成条件で指定する。実際の物体の点状性、全粒子の停止、モデルの実験的実現又は模型だけから物理法則を導けることを含意しない。'),
 'eissl':(PHYSICAL_PHASE,'同じsubject・wave・processについて、同じ系と単位のmodelsに沿う周期的な放射成分の位相を、同じparametersのモデルごとにphasesとして解釈する物理的な対応。receivedが偽ならsubjectによる放射の位相、真ならsubjectがその波を受け取る位相を、そのsubjectの当該系の局所時計時刻で表す。lowerからupperの範囲で同じscopeの周期的成分を採用する理想化であり、単なる数値関数の一致、別の波の放射、装置表示の任意の繰返しとは区別する。位相原点は周期数を変えないが、同じモデル・過程・時計の対応は保持する。正弦・最小周期・周期数の数値・静止・速度は合成側で検査し、この関係自体にドップラー式やその正当性を含めない。現実の測定実施、意識的な色の知覚、無限精度の測定又は近似誤差からの位相の一意推定は要求しない。'),
 'eissm':([], 'u0188のAus der Gleichung für ω′ folgt:からdurch die Gleichung gegeben:までの、光源と観測者の条件付き帰結を提示する箇所。'),
 'eissn':([], 'u0189=M0333の、同じ光源と観測者のν′を与える表示式の箇所。'),
 'eisso':([], '直前u0186=M0327の第一式ω′=ωβ(1−av/V)を参照する命題項目。四つの式のうち位相率の式であり、方向余弦の式を代用しない。'),
}
MEANINGS={
 'ekdv':'距離パラメータごとにekdiの同じ静止曲線を返す源のモデル族。三方向成分を族全体で固定する。',
 'ekdw':'同じ旧位相ekbfを、ekdvの各距離に対応する源曲線へ適用した位相の族。局所の実際の場を源位置まで外挿する主張ではなく、周期的な理想化の位相原点をそろえる構成。',
 'ekdx':'指定した同じ三位置関数と時刻から四座標曲線を作り、パラメータには依存しないモデル族にする。各パラメータで別の観測者の経路へ替えない。',
 'ekdy':'同じ四座標位相をekdxの同じ経路へ適用するekdaを、パラメータに依存しない位相族にする。',
 'ekdz':'モデルのパラメータの全許容範囲を正の有効実数とする。有限の成功例だけを選ぶ範囲ではない。',
 'ekd2':'同じ単位方向と正の距離について、源配置−R*n上の位相率ω、位相原点ωR/V、同じ正弦・余弦・一周期・放射周期数をekc7へ結ぶ。Rごとに周期数を選び直さない。',
 'ekd3':'同じ源・波・過程・K・単位に、ekdvの位置モデル、ekdwの放射位相、全正距離、方向の極限ekdm及び全距離でのekd2を結ぶ。Kに静止する曲線族の無限遠という理想化であり、単一の有限な源位置を無限大と同一視しない。',
 'ekd4':'同じ観測者・波・過程・系・単位の経路と受信位相をeissk/eisslへ帰属し、局所区間全時刻のekdcと同じ位相原点を持つ最小周期ekc7から、受信周期数を定める。短い区間で一周期の実測が済んだという意味ではない。',
 'ekd5':'新系の同じ三位置と時刻から四座標を作り、同じVと−vの逆Lorentz写像で得る旧時刻が旧観測区間に入り、旧経路の三位置と一致する点条件。新旧の同じ数値時刻を無条件に同一視しない。',
 'ekd6':'同じ観測者のKにおける正X速度vの完全な物理履歴eivu、旧経路上の位相率ω(1−av/V)、新観測区間の全時刻のekd5を合わせる。kに静止する観測者の同一性は先行ekclから保持する。',
 'ekd7':'先行ekclの同じ波・場・近似・観測者に、源の静止モデルと放射周期数、同じ観測者のK運動とk受信周期数、同じ実数角を結ぶ全59役割の条件。ν′のドップラー等式ekea自体は条件へ含めない。',
 'ekea':'同じ59役割のうちV,v,ν,cosφ,ν′を使い、ν′がekdrの印刷式に等しいという数値的な帰結。物理的な役割と適用域はekd7へ分離する。',
 'ekeb':'K、V、第七節、評価状況を固定し、残る55役割の全割当についてekd7ならekeaと述べる条件内容。前提と帰結で別の波・源・観測者・周期数を存在選択し直さない。',
 'ekec':'先行ekclの同じ37証人の設定の中で、ω′をsdn2で与え、その値をωβ(1−av/V)の明示形へ結ぶ内容。M0327第一式への参照用であり、引用した先行法則を現実の真理へ変えない。',
 'eked':'著者が同じ第七節で先行のω′の式ekecから条件付きのekebを帰結として提示し、参照項目eissoと先のパラメータ表示eissjを結ぶ。コロンから同じν′の表示への説明・順序を保持する。',
 'ekee':'光源と観測者の条件付き帰結ekedを述べるメッセージ。',
 'ekef':'u0188の帰結提示を同じ著者・論説へ帰属し、直前の四パラメータの補足に続ける。',
 'ekeg':'u0189の表示項目を同じ条件付き内容ekebへ結ぶ。式を無条件の実験事実へ替えない。',
 'ekeh':'同じドップラー表示ekegを述べるメッセージ。',
 'ekei':'u0189の表示を同じ著者・論説へ帰属し、u0188のコロンに続く箇所として保持する。',
}
LIMITS=[
 'u0188–u0189を原刊911頁の条件付き帰結と表示として読む。源に静止するK、正X方向の速さvで動く同じ観測者、その共動kの局所時刻による受信周期数を使う。φは源から観測者へ向かう線と速度の0からpiまでの角でありcosφ=aとなる。',
 'unendlich fernは、先行の源と波の役割を保持した理想化モデル族−R*nの方向極限として読む。一つの実在対象が全Rの位置に同時にあること、実数の無限座標、源の点状性を要求しない。各モデルの源曲線がKで静止し、その意味役割をeisskが指定する。',
 'wahrgenommenは同じ観測者が受け取る周期的な放射成分の周期数と読む。eisslは位相の物理的な放射・受信役割を指定する一般関係であり、周期数の数学条件やドップラー式は含めない。現実の測定済み、視覚器官の応答又は意識的な色の判断へ限定しない。',
 '源の放射位相はモデル族におけるω(t+R/V)として位相原点を合わせる。これは源での実際の電磁場が局所の近似場に厳密一致するという外挿ではない。観測者の位相は同じ変換後位相を経路へ適用し、その局所時計時刻の率と周期へ結ぶ。',
 'νとν′は同じ一周期2*piと時間単位に結ばれた周期数で、ωや時間周期と同じ値にはしない。位相の物理的な同定を条件に明示し、場の成分誤差上限だけから周期数を一意に推定しない。既存の近似誤差と用途上の十分性を保持する。',
 '単位方向、V>0、0<v<Vは先行の標準配置と数式の適用域を使う。零速度の任意の角の割当を追加しない。各周期は数学的な正弦表示の最小正周期であり、局所観測区間が一周期以上あるという追加条件にはしない。',
 '条件内容ekebは同じ55役割への全称条件であり、ν′の印刷等式を条件へ含めてから結論として繰り返す構成ではない。新しい物理仮説の証明、全実数域の機械証明、現実の源・観測実験の存在を著者帰属だけから認定しない。',
 '二つの新しい一般関係は対象と配置モデル族、及び同じ放射成分の位相の物理的解釈に限る。源の静止・遠距離極限・観測者の速度・角度・周期数・等式・条件・著者提示を原始語へ圧縮しない。u0178の主題、u0190以降の原理名・特殊例・光行差は別に残る。',
]

def oldphase():return k('ekbf',*args(PHASE))
def newphase():return transformed(k('zb7'))[-1]
def model_curve(xyz,time):
    spatial=k('ekbe',*(app(x,time) for x in xyz))
    return 'i[axis a]['+k('szi',op('e',v('axis'),k('zc7')),time,app(spatial,v('axis')))+']'

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+('c' if fs else 'a')+'.\n' for n,(fs,_) in PRIMITIVES.items())
    zero=k('bb','n p a b');one=k('bb','n p b b');time=v('time');distance=v('distance');n=args(DIR);V=v('light');rate=v('rate');ctx=v('context');scope=v('scope')
    text+=define('ekdv',DIR,'i[distance '+R+']['+k('ekdi',*n,distance)+']',MODELS)
    sourcecurve=app(k('ekdi',*n,distance),time);sourcephase=app(oldphase(),*(app(sourcecurve,k(a)) for a in ('yn','yo','yp','zc7')))
    text+=define('ekdw',PHASE,'i[distance '+R+'][i[time '+R+']['+sourcephase+']]',PHASES)
    text+=define('ekdx',XYZ,'i[distance '+R+'][i[time '+R+']['+model_curve(args(XYZ),time)+']]',MODELS)
    text+=define('ekdy',[('phase',TAU)]+XYZ,'i[distance '+R+']['+k('ekda',v('phase'),*args(XYZ))+']',PHASES)
    text+=define('ekdz',[],'i[distance '+R+']['+both(k('ba',distance),k('bg',zero,distance))+']',D)
    sourceoffset=k('shv',rate,k('shv',distance,k('sjd',V)))
    text+=define('ekd2',SOURCE_CYCLE,both(k('sdl2',V,zero,rate,*n),app(k('ekdz'),distance),k('ekc7',*args(HARMONIC),rate,sourceoffset,v('period'),v('frequency'))))
    srcmodel=k('ekdv',*n);srcphases=k('ekdw',*args(PHASE));parameters=k('ekdz')
    sourcebinding=k('eissk',v('source'),v('frame'),v('lengthunit'),v('timeunit'),srcmodel,parameters,scope,ctx)
    sourcecycle=k('eissl',*[v(x) for x in ('source','wave','process','frame','lengthunit','timeunit')],srcmodel,srcphases,parameters,v('lower'),v('upper'),FALSE,scope,ctx)
    text+=define('ekd3',SOURCE_FIELDS,both(k('bg',v('lower'),v('upper')),sourcebinding,sourcecycle,k('ekdm',*n),q('f','distance',R,op('y',app(parameters,distance),k('ekd2',*args(SOURCE_CYCLE))))))
    obsmodel=k('ekdx',*args(XYZ));obsphases=k('ekdy',v('phase'),*args(XYZ))
    observerbinding=k('eissk',v('observer'),v('frame'),v('lengthunit'),v('timeunit'),obsmodel,parameters,scope,ctx)
    reception=k('eissl',*[v(x) for x in ('observer','wave','process','frame','lengthunit','timeunit')],obsmodel,obsphases,parameters,v('lower'),v('upper'),TRUE,scope,ctx)
    text+=define('ekd4',RECEIVER,both(observerbinding,reception,k('ekdc',v('phase'),*args(XYZ),v('lower'),v('upper'),rate,v('offset')),k('ekc7',*args(HARMONIC),rate,v('offset'),v('period'),v('frequency'))))
    newpoint=model_curve(args(XYZ),time);inverse=k('s46',V,k('bf',zero,v('speed')),newpoint);oldtime=app(inverse,k('zc7'))
    text+=define('ekd5',MAPPING,both(*(k('ba',x) for x in [time,oldtime]),k('lg',v('oldlower'),v('oldupper'),oldtime),*(k('sca',app(v('old'+axis),oldtime),app(inverse,k(role))) for axis,role in zip(('x','y','z'),('yn','yo','yp')))))
    speed=k('zb7');oldxyz=[v('oldobs'+x) for x in ('x','y','z')];newxyz=[v('obs'+x) for x in ('x','y','z')]
    motion=k('eivu',v('observer'),v('frame'),ctx,v('lengthunit'),v('timeunit'),v('oldobslower'),v('oldobsupper'),*oldxyz,speed)
    oldtrace=k('ekdc',oldphase(),*oldxyz,v('oldobslower'),v('oldobsupper'),k('shv',rate,k('sdm2',V,speed,v('ax'))),v('oldoffset'))
    inside=both(k('ba',time),k('lg',v('obslower'),v('obsupper'),time))
    mapping=k('ekd5',V,speed,v('oldobslower'),v('oldobsupper'),*oldxyz,*newxyz,time)
    text+=define('ekd6',SETTING,both(motion,oldtrace,q('f','time',R,op('y',inside,mapping))))
    sourceargs={'period':v('oldperiod')}
    receiverargs={'frame':k('zbm'),'phase':newphase(),'x':v('obsx'),'y':v('obsy'),'z':v('obsz'),'rate':k('sdn2',V,speed,rate,v('ax')),'offset':v('newoffset'),'period':v('newperiod'),'frequency':v('newfrequency'),'lower':v('obslower'),'upper':v('obsupper')}
    geometry=[v(x) for x in ('ax','ay','az')]+[speed]+[v(x) for x in ('anglecos','anglesin','ratio','principal','pi','angle')]
    text+=define('ekd7',SETTING,both(k('ekcl',*args(FAMILY)),k('ekd3',*[sourceargs.get(x,v(x)) for x,t in SOURCE_FIELDS]),k('ekd4',*[receiverargs.get(x,v(x)) for x,t in RECEIVER]),k('ekd6',*args(SETTING)),k('ekdq',*geometry)))
    text+=define('ekea',SETTING,k('sca',v('newfrequency'),k('ekdr',V,speed,v('frequency'),v('anglecos'))))
    fixed={'frame':k('ra'),'scope':k('eisrx'),'context':v('point'),'light':k('tc')};actual=[fixed.get(x,v(x)) for x,t in SETTING]
    conditional=op('y',k('ekd7',*actual),k('ekea',*actual))
    for name,t in reversed(VARIABLES):conditional=q('f',name,t,conditional)
    text+=content('ekeb',conditional)
    priorvars=[(x,t) for x,t in FAMILY if x not in fixed]
    expanded=k('shv',rate,k('shv',k('soy',V,speed),k('sdm2',V,speed,v('ax'))))
    angular=both(k('ekcl',*[fixed.get(x,v(x)) for x,t in FAMILY]),k('sca',k('sdn2',k('tc'),speed,rate,v('ax')),expanded.replace(v('light'),k('tc'))))
    text+=content('ekec',bind(priorvars,angular))
    node=k('eissm');display=k('eissn');prior=k('eisso');author=k('rd');section=k('eisrx');p=v('point')
    text+=content('eked',both(k('eisox',prior,quote('ekec'),p),k('zc',node,author,quote('ekec'),quote('ekeb'),section,p),k('ue',prior,node,p),k('uf',author,node,display,p),k('ue',node,display,p)))
    text+=content('ekeg',k('eisox',display,quote('ekeb'),p))
    for shown,message,statement,item,previous in [('eked','ekee','ekef','eissm','eissj'),('ekeg','ekeh','ekei','eissn','eissm')]:
        text+='d '+message+'[] f[j s[k '+shown+'[]]].\n'
        text+=define(statement,[],both(k('eir3',k(item),author,k('eirf'),quote(message),k('ri')),k('ue',k(previous),k(item),k('ri')),op('u',op('e',k(previous),k(item)))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==370
    assert not(set(PRIMITIVES)|set(MEANINGS))&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol=n,arguments=[])) for n in ('ekef','ekei')]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,t in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='same_source_model_observer_and_conditional_doppler_consequence',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=INDICES).document
    ann=json.loads(read('data/distant-direction-geometry-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
