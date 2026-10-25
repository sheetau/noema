"""Connect the axial energy argument while preserving the printed integral."""
from scripts.compose_material_mass_claim import *
from scripts.compose_electron_power_law import ALL as POWER,LOCAL as POWER_LOCAL,PROFILES as ENERGY_PROFILES
from scripts.compose_electron_axis_motion import ALL as MOTION
from scripts.compose_point_particle_dynamics import HISTORY,FIELDS,CHARGE,MASS,UNITS
from scripts.compose_electric_action import FIELDS as ACTION
from scripts.compose_electron_energy_balance import BASE as ENERGY_BASE,VALUES

PARENT=FULL;PARENT_BASIS=BASIS;PARENT_ANNOTATIONS=ANNOTATIONS
FULL='examples/v014/einstein-electron-kinetic-work.noema'
CORE='examples/v014/electron-kinetic-work-core.noema'
BASIS='data/electron-kinetic-work-basis-v1.json'
ANNOTATIONS='data/electron-kinetic-work-identifiers-v1.json'
SETTING=POWER+[(n,'a') for n in ('episode','field','lengthunit','timeunit','massunit','forceunit','chargeunit','electricunit','magneticunit','energyunit')]+[(n,'b') for n in ('lengthscale','timescale','massscale','forcescale','energyscale')]+[('electricfield',FIELD),('magneticfield',FIELD),('region',REGION),('slowbound',R)]
ALL=SETTING+VALUES
KINETIC=[('matter','a'),('frame','a'),('event','a'),('unit','a'),('value',R),('context','d')]
WITHDRAWAL=ENERGY_BASE[:-1]+[('value',R),('context','d')]
RADIATION=[(n,'a') for n in ('episode','particle','frame','start','end','unit')]+[('value',R),('context','d')]
PRIMITIVES={
 'eiszt':(KINETIC,'同じ物体の指定出来事での、基準系に相対的な並進運動に帰属するエネルギーを共通の仕事単位unitでvalueとする物理的対応。内部状態を保って当該系で静止へ移すとき機械的仕事として交換できる運動の寄与という意味を採り、静止時のこの寄与を零とする。内部エネルギー・静止エネルギー・放射量そのものと区別する。特定の速度公式、実測又は制動の実施は含めない。'),
 'eiszu':(WITHDRAWAL,'同じ開始・終了で区切ったepisodeにおいて、同じframeでfieldからparticleへ渡した仕事に対応する場のエネルギーの取り出しをunitでvalueとする物理的帰属。場のエネルギーは物質への仕事と他の形態との交換収支によって同定する。単なる場の強さや場の全貯蔵量とは区別する。数値積分、他の受け取り手の不存在、粒子の運動エネルギーとの等値は別に合成する。'),
 'eiszv':(RADIATION,'同じparticleから同じepisodeの開始・終了間に外向きの電磁放射として失われるエネルギーを同じframeと仕事単位unitでvalueとする物理的帰属。局所の力の数値や任意の損失ではなく、物質から離れて伝播する電磁的なエネルギー移転を指す。零も許すが、緩い加速からの零、特定放射則、実験済みは含めない。'),
 'eiszw':([(n,'a') for n in ('frame','lengthunit','forceunit','energyunit')]+[('context','d')],'指定系の校正された長さと有向の機械的力を使う仕事の単位をenergyunitとする物理的対応。力とその方向への変位の積の積分で仕事を比較し、他形態とのエネルギー交換にも同じ単位を使う。単位尺度の積は合成で要求する。単位名だけの一致又は任意数値へのエネルギーという命名ではない。'),
 'eiszx':([(n,'a') for n in ('frame','lengthunit','timeunit')]+[('bound',R),('scope','a'),('context','d')],'同じ系と長さ・時間の校正で、scopeの理想化した議論において加速度の大きさを緩いと評価する比較基準がboundであるという文脈依存の程度規約。数値の正性と実際の加速度の全区間での上限条件は合成する。普遍的な閾値、速度が小さいこと、厳密な無放射、特定の放射則をこの程度規約に含めない。'),
 'eiszy':([('node','a'),('author','a'),('question','i[g['+R+']]'),('scope','a'),('context','d')],'authorがnodeで同じscopeのquestionが求める量をこれから決定するという論述上の取組を告げる。候補の意味は引用した質問で与える。単に疑問を発したこと、既知の答え、計算又は実験の完了を含意しない。'),
 'eiszz':([('field','a'),('frame','a'),('electricfield',FIELD),('region',REGION),('context','d')],'個体として参照するfieldの、同じframeとregionにおける電気的成分モデルがelectricfieldであるという対象と数量モデルの対応。物理的な場の割当・単位・試験電荷による意味、静的性質は別に要求する。別の場のエネルギー又は同じ数値だけの関数へ交換しない。'),
}
# Existing episode/axis/value names are rebound to the current electron by definitions.
FIXED={'matter':'eisxh','frame':'ra','domain':'zrhdomain','curve':'zrhcurve','start':'zrgstart','end':'eisxv','startpoint':'zrhstartpoint','endpoint':'zrhendpoint','finalposition':'zrgposition','finalspeed':'eisxt','velocity':'zrivelocity','acceleration':'zriacceleration','profile':'zrgprofile','light':'tc','charge':'zrgcharge','episode':'zrgepisode','field':'zrgfield','energyunit':'zrgunit','withdrawn':'zrgwithdrawn','initial':'zrginitial','final':'zrfenergy','radiated':'zrgradiated','lengthunit':'ta','timeunit':'rb'}
NEW_VALUES={}
for i,(name,typ) in enumerate((x for x in ALL if x[0] not in FIXED and x[0]!='context')):
    symbol='eis2'+chr(ord('a')+i);FIXED[name]=symbol;NEW_VALUES[symbol]=(typ,'u0261–u0262の同じ設定における'+name+'。具体的な物理的役割・単位・同一性はeor–eo5で接続する。')
REFERENCES=dict(zip(('eis3a','eis3b','eis3c','eis3d','eis3e','eis3f','eis3g','eis3h','eis3i'),('運動エネルギーを決定するという導入。','原点初速零の軸上運動から仕事へ進む条件文。','緩い加速と放射しないという設定。','同じ場の取り出しを運動エネルギーへ等置する推論。','全運動区間で第一(A)を使う参照。','M0425の仕事積分表示。','M0426の運動エネルギーWという呼称。','M0427の印刷された等号列。','同じ設定で無放射を緩い加速の帰結として扱う箇所。')))
REFERENCES['eis3j']='M0426–M0427で運動エネルギーを呼ぶ記号W。'
MEANINGS={
 'eor':'同じ軸上の実履歴、全時刻の校正座標、正の整合単位と同じ物理的な二場を保持し、場の個体参照とエネルギーの仕事単位を接続する。質量・電荷・作用はeotで結び、運動方程式や無放射はまだ要求しない。',
 'eos':'同じ領域の全有効四座標で電場を(profile(x),0,0)とする静的な軸方向場のモデル。profileは時刻に依存しない同じ関数で、領域の任意の点の三成分を比較する。',
 'eot':'同じ実曲線上の一時刻の出来事と電荷・電気力記録を一組で取り、既存eibsの電気的作用qE、非零電荷と低速質量の帰属を同じ粒子・場・単位へ接続する。電荷と低速質量の数値は全区間で共有する。',
 'eou':'同じeor/eosの設定に、全運動区間の各実時刻についてeotの実際の電気的作用の帰属を要求する。別の粒子の静電場、端点だけの確認、数値だけの力では代用しない。',
 'eov':'同じ曲線xの座標時刻微分をvelocity、その微分をaccelerationとする一時刻の接続。端点にも両側近傍を要求する。第一(A)の力学的等式はこの定義には入れない。',
 'eow':'同じ正の文脈的比較基準を全区間の外で固定し、全運動時刻の実加速度eovの絶対値がその基準より小さいという緩い加速。速度が小さいことや単に加速度を任意の大きい数で抑えることへ替えない。',
 'eox':'同じ過程・電子・場・K・両端と仕事単位に、初期と終端の運動エネルギー、場からの取り出し、外向き放射量の四値を物理的に帰属させる。',
 'eoy':'同じ場から取り出した量に、原点0から同じ終位置までの符号付き仕事積分seroを結ぶ。積分内の電荷・静電場プロファイルは軌道の作用と同じもの。',
 'eoz':'同じeowの緩い加速と、同じ過程の放射量零という二つの設定を合わせる。両者の普遍的な含意や実際の放射理論を証明したとしない。',
 'eo2':'同じ四値の帰属に、他の移転・内部変化を含めない収支設定、初期運動エネルギー零と放射零、withdrawn=final-initial+radiatedを結ぶ。この簡略収支は本文の等置で採用する明示読解。',
 'eo3':'同じ取り出しと終端の運動エネルギーの物理的帰属を保ち、両者の数値を等置する。無放射や収支を等式から逆推定しない。',
 'eo4':'同じ軌道・電荷・質量・静電場と各時刻の実微分を共有し、全運動区間に第一(A)の縦方向式sesfを適用する。betaを終端値へ固定しない。',
 'eo5':'同じ終端運動エネルギーWを、同じ位置仕事積分と、印刷通りの無質量係数の速度積分及びμV²(beta−1)へ等置する。sergを使い、補正候補serhへ交換しない。',
 'eo6':'同じ電子・K・終端・仕事単位に帰属する運動エネルギーを答え候補とする実数質問。解の既知性や式を先に候補条件へ入れない。',
 'eo7':'同じ現在の電子と明示単位に対する、原点初速零の軸上運動と静電力の条件内容。',
 'epa':'同じ運動条件なら同じ取り出したエネルギーが仕事積分で与えられるという条件文。',
 'epb':'同じ設定の緩い加速という内容。',
 'epc':'同じ過程の放射量零という内容。',
 'epd':'同じ緩い加速・無放射と簡略収支の設定を合わせた、エネルギー等置への前提内容。',
 'epe':'同じ場の取り出しと同じ電子の終端運動エネルギーが等しいという内容。',
 'epf':'同じ全運動区間での第一(A)の適用内容。',
 'epg':'同じ仕事式・収支設定・第一(A)を合わせた、印刷された等号列への著者の前提内容。',
 'eph':'同じ電子・場・軌道・単位・四つのエネルギー帰属、緩い加速と無放射・簡略収支・第一(A)という同じepgの前提を保持したM0427の等号列の内容。数式単位だけの選択からも物理的な前提と無放射の限定をたどれる。',
 'epi':'決定の取組、条件付きの自明性、緩い加速を採る設定、そこからの無放射、仕事と運動エネルギーの必然的等置、先行第一(A)への全過程の照応、したがって次の式を得るという全文の提示。',
 'epj':'u0261の全文メッセージ。',
 'epk':'u0261を同じ著者・論説へ帰属し、u0260の物質点への拡張に続ける。',
 'epl':'M0427の同じ原文保存内容を数式表示として提示する。',
 'epm':'u0262の数式提示のメッセージ。',
 'epn':'u0262を同じ著者・論説へ帰属し、u0261の前方参照の直後へ置く。',
 'epo':'同じ電子・K・終端・単位に帰属する実数値を記号Wへ対応させる規則。別の物体のエネルギーや表示の個体へ数値を交換しない。',
 'epp':'M0425に対応する、同じ場から取り出した量が同じ過程の位置仕事積分であるという内容。運動条件を含む条件文epaとは区別する。',
}
LIMITS=[
 '原刊919–920頁のu0261全文とu0262のM0427を一群として読む。X-AchseのXは座標軸、elektrostatische Kraft XのXは先行節と同じ単位電荷当たりの電気的力（電場成分）。電子への力はεXであり、X自体をεXに取り替えない。',
 '同じ現在の電子eisxh、K、原点初速零の全軸上履歴、同じ非零符号付き電荷と正の低速慣性質量、正の整合単位を使う。終端vは非負でV未満とする既存sergの読みであり、軸の正方向を選んだ速さ。全時刻のbetaはその時刻の速度の関数で、初速零で割らない。',
 '静電場は考察領域で時間独立の軸方向電場(profile(x),0,0)として読む。磁場を零にせず、電気的仕事の寄与を取り出す。閉じた簡略エネルギー収支により他の仕事・内部変化を数えないという限定を明示する。実際の場の源、自己場の正則化や放射則を補わない。',
 'langsamは同じ座標時刻加速度が議論で採用した小ささの比較基準に収まるという程度の読み。原文は閾値を指定しないため値を創作せず、速度が小さい又は加速度厳密零とはしない。sollとmögeはこの議論で採る設定、infolgedessenは著者の理由付けとして記述し、緩い加速なら厳密無放射という処理系の定理にはしない。',
 '静止時の運動エネルギーを零とする規約、同じ仕事単位、他の移転・内部変化を除いた収支を明示して等置を読む。mußはこの設定での推論上の必然性であり、電子への規範的義務ではない。Wirは著者の論述上の一人称複数で、共同著者又は読者全員の行為を追加しない。',
 'M0425とM0427最初の位置積分には上下端が印刷されていない。直前の原点から終位置までの過程を指す定積分として解釈し、任意の積分定数は加えない。仕事積分はseroの向き付き定義を使う。',
 '原刊920頁とMathMLのM0427はともに中間項∫0^v β³v dvにμを含まない。sergを保存し、μを含めるserhや質量を1に置く補正を著者へ帰属しない。βは積分内で変数vに依存する。右端だけでなくWと位置積分を含む全等号列を接続する。',
 'Man erhält daherと第一(A)への参照は著者の推論として保存する。印刷式の不整合を、前提からの数学的導出に成功したものとして扱わない。一般の積分変数変換や微積分基本定理の機械的証明を本文記述の完成条件に追加しない。既存の補正候補・解析依存・反例は保持する。',
 '旧428主張と証拠を変更しない。有限検査は数値・単位・役割・引用・束縛と境界の診断で、全実数域の解析、物理的真理、意味同義性を自動証明しない。後続u0263以降は今回含めない。',
]

def actual(fields,**replace):
    return [replace.get(n,v('point') if n=='context' else k(FIXED[n])) for n,t in fields]

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] c.\n' for n,(fs,_) in PRIMITIVES.items())
    text+=''.join('r '+n+'[] '+t+'.\n' for n,(t,_) in NEW_VALUES.items())+''.join('r '+n+'[] a.\n' for n in REFERENCES)
    zero=k('bb','n p a b');one=k('bb','n p b b');ctx=v('context')
    fs={n:v(n) for n,t in SETTING};fs.update(electricconversion=one,magneticconversion=k('sjd',v('light')))
    units=[k('ek3n',*args(UNITS)),k('ejwb',v('energyunit'),'n p c b','n p b b','n u c b',v('energyscale'),ctx),op('e',v('energyscale'),k('ad',v('forcescale'),v('lengthscale'))),k('eiszw',v('frame'),v('lengthunit'),v('forceunit'),v('energyunit'),ctx)]
    text+=define('eor',SETTING,both(k('serw',*args(MOTION)),k('ek3p',*args(HISTORY)),k('ejsn',*[fs[n] for n,t in FIELDS]),k('eiszz',v('field'),v('frame'),v('electricfield'),v('region'),ctx),*units))
    coords=[(n,R) for n in ('x','y','z','time')];xyz=args(coords)
    inside=both(*(k('ba',x) for x in xyz),app(v('region'),*xyz))
    eq=both(*(k('sca',app(app(v('electricfield'),k(axis)),*xyz),app(v('profile'),v('x')) if i==0 else zero) for i,axis in enumerate(ROLES[:3])))
    text+=define('eos',SETTING,quantified('f',coords,op('y',inside,eq)))
    moment=v('moment');location=app(v('curve'),moment);x=coord(location,ROLES[0]);electric=k('ekbe',app(v('profile'),x),zero,zero);force=k('ekbe',k('shv',v('charge'),app(v('profile'),x)),zero,zero)
    witnesses=[('event','a'),('chargerecord','a'),('forcerecord','a'),('chargescale','b')]
    ac=fs|{n:v(n) for n,t in witnesses}|dict(carrier=v('matter'),fieldunit=v('electricunit'),point=location,electric=electric,force=force,conversion=one)
    text+=define('eot',SETTING+[('moment',R)],quantified('g',witnesses,both(k('eibs',*[ac[n] for n,t in ACTION]),k('ek3u',*[ac[n] for n,t in CHARGE]),k('ek3o',*[ac[n] for n,t in MASS]))))
    lower=coord(v('startpoint'),ROLES[3]);upper=coord(v('endpoint'),ROLES[3]);inside=both(k('ba',moment),k('sxs',lower,upper,moment))
    each=lambda body:quantified('f',[('moment',R)],op('y',inside,body))
    text+=define('eou',SETTING,both(k('eor',*args(SETTING)),k('eos',*args(SETTING)),each(k('eot',*args(SETTING),moment))))
    coordinate=lam('time',R,coord(app(v('curve'),v('time')),ROLES[0]))
    text+=define('eov',SETTING+[('moment',R)],both(k('senz',v('domain'),moment),k('sjs',v('domain'),coordinate,moment,app(v('velocity'),moment)),k('sjs',v('domain'),v('velocity'),moment,app(v('acceleration'),moment))))
    bound=v('slowbound');acc=app(v('acceleration'),moment)
    text+=define('eow',SETTING,both(k('ba',bound),k('bg',zero,bound),k('eiszx',v('frame'),v('lengthunit'),v('timeunit'),bound,k('eisxg'),ctx),each(both(k('eov',*args(SETTING),moment),k('ba',acc),k('bg',k('bf',zero,bound),acc),k('bg',acc,bound)))))
    base={n:v(n) for n,t in ALL}|dict(particle=v('matter'),unit=v('energyunit'))
    kinetic=lambda event,value:k('eiszt',v('matter'),v('frame'),v(event),v('energyunit'),v(value),ctx)
    wd=lambda val:k('eiszu',*[base[n] for n,t in WITHDRAWAL if n!='value' and n!='context'],v(val),ctx)
    rad=lambda val:k('eiszv',*[base[n] for n,t in RADIATION if n!='value' and n!='context'],v(val),ctx)
    text+=define('eox',ALL,both(*(k('ba',v(n)) for n,t in VALUES),kinetic('start','initial'),kinetic('end','final'),wd('withdrawn'),rad('radiated')))
    text+=define('eoy',ALL,both(wd('withdrawn'),k('sero',zero,v('finalposition'),v('charge'),v('withdrawn'),v('profile'))))
    text+=define('eoz',ALL,both(k('eow',*args(SETTING)),rad('radiated'),k('sca',v('radiated'),zero)))
    text+=define('eo2',ALL,both(k('eox',*args(ALL)),app(k('zrgclosed'),*[base[n] for n,t in ENERGY_BASE]),k('serm',*args(VALUES))))
    text+=define('eo3',ALL,both(k('eox',*args(ALL)),k('sern',*args(VALUES))))
    text+=define('eo4',SETTING,k('sesf',*args(POWER)))
    text+=define('eo5',ALL,both(kinetic('end','final'),k('sero',zero,v('finalposition'),v('charge'),v('final'),v('profile')),k('serg',v('light'),v('mass'),v('finalspeed'),v('final'))))
    # The question captures the current setting outside the answer variable.
    text+=define('eo6',[],'j v[i[value '+R+']['+k('eiszt',k('eisxh'),k('ra'),k('eisxv'),k('zrgunit'),v('value'),k('ri'))+']]','g['+R+']')
    text+=define('epo',[('matter','a'),('value',R),('context','d')],both(op('e',v('matter'),k('eisxh')),k('eiszt',v('matter'),k('ra'),k('eisxv'),k('zrgunit'),v('value'),ctx)))
    ev=lambda n:op('t',k(n),v('point'))
    text+=content('eo7',k('eou',*actual(SETTING)))
    text+=content('epp',k('eoy',*actual(ALL)))
    text+=content('epa',op('y',ev('eo7'),ev('epp')))
    text+=content('epb',k('eow',*actual(SETTING)))
    text+=content('epc',both(k('eiszv',*[actual(ALL)[[n for n,t in ALL].index(n)] for n in ('episode','matter','frame','start','end','energyunit')],k('zrgradiated'),v('point')),k('sca',k('zrgradiated'),zero)))
    text+=content('epd',both(ev('eo7'),k('eoz',*actual(ALL)),k('eo2',*actual(ALL))))
    text+=content('epe',k('eo3',*actual(ALL)))
    text+=content('epf',k('eo4',*actual(SETTING)))
    text+=content('epg',both(ev('epd'),ev('epf'),k('eoy',*actual(ALL))))
    text+=content('eph',both(ev('epg'),k('eo5',*actual(ALL))))
    who=k('rd');paper=k('eirf');scope=k('eisxg');p=v('point')
    text+=content('epi',both(k('eiszy',k('eis3a'),who,quote('eo6'),scope,p),k('zdg',k('eis3b'),who,quote('epa'),scope,p),k('eisox',k('eis3f'),quote('epp'),p),k('ug',k('eis3c'),who,quote('epb'),scope,p),k('ug',k('eis3i'),who,quote('epc'),scope,p),k('zc',k('eis3i'),who,quote('epb'),quote('epc'),scope,p),k('zc',k('eis3d'),who,quote('epd'),quote('epe'),scope,p),k('uh',k('eis3d'),who,quote('epe'),scope,p),k('eisnw',k('eis3g'),who,k('eis3j'),'r[p epo]',paper,p),k('uh',k('eis3e'),who,quote('epf'),scope,p),k('eiswm',k('eis3e'),who,k('eisym'),quote('elk'),paper,p),k('zc',k('eis3h'),who,quote('epg'),quote('eph'),scope,p),*(k('ue',k(a),k(b),p) for a,b in zip(('eis3a','eis3b','eis3c','eis3d','eis3e'),('eis3b','eis3c','eis3d','eis3e','eis3h')))))
    text+='d epj[] f[j s[k epi[]]].\n'
    text+=define('epk',[],both(k('eir3',k('eis3a'),who,paper,quote('epj'),k('ri')),k('ue',k('eiszq'),k('eis3a'),k('ri'))))
    text+=content('epl',both(k('eisox',k('eis3h'),quote('eph'),p),k('uh',k('eis3h'),who,quote('eph'),scope,p)))
    text+='d epm[] f[j s[k epl[]]].\n'
    text+=define('epn',[],both(k('eir3',k('eis3h'),who,paper,quote('epm'),k('ri')),k('ue',k('eis3e'),k('eis3h'),k('ri'))))
    return text

@lru_cache(None)
def build():
    old=parse(read(PARENT));assert len(old['statements'])==428
    assert not(set(MEANINGS)|set(PRIMITIVES)|set(REFERENCES)|set(NEW_VALUES))&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions())
    doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol=n,arguments=[])) for n in ('epk','epn')]
    added=doc['declarations'][len(old['declarations']):]
    prim={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,t in PRIMITIVES[d['name']][0]] if d['name'] in PRIMITIVES else [],meaning_ja=PRIMITIVES[d['name']][1] if d['name'] in PRIMITIVES else NEW_VALUES[d['name']][1] if d['name'] in NEW_VALUES else REFERENCES[d['name']]) for d in added if d['kind']=='primitive'}
    basis=dict(status='axial_electric_work_and_printed_kinetic_energy_argument',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=prim,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[428,429]).document
    ann=json.loads(read(PARENT_ANNOTATIONS));ann.update(document=FULL,document_sha256=digest(body.encode()))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
