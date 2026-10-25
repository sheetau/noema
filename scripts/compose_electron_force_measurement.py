"""Connect the current comoving force, a spring measurement and mass convention."""
from scripts.compose_electron_mass_rewrite import *
from scripts.compose_electric_action import FIELDS as ACTION
from scripts.compose_limits import F

PARENT='examples/v014/einstein-electron-mass-rewrite.noema'
PARENT_BASIS='data/electron-mass-rewrite-basis-v1.json'
FULL='examples/v014/einstein-electron-force-measurement.noema'
CORE='examples/v014/electron-force-measurement-core.noema'
BASIS='data/electron-force-measurement-basis-v1.json'
ANNOTATIONS='data/electron-force-measurement-identifiers-v1.json'
FORCE=PAIR+[('forcerecord','a'),('force',POINT)]
TARGET=[(n,'a') for n in ('matter','forcerecord','frame','event','forceunit','lengthunit')]+[('force',POINT),('context','d')]
CALIBRATION=[('range',DOMAIN),('response',F)]
GAUGE=[(n,'a') for n in ('instrument','element','frame','axis','lengthunit','forceunit')]+CALIBRATION+[('context','d')]
TRIAL=TARGET+[('instrument','a'),('element','a'),('axis','a'),('operation','a'),('alternative','d')]+CALIBRATION+[('deflection',R)]
WITNESSES=[('operation','a'),('alternative','d')]+CALIBRATION+[('deflection',R)]
CONVENTION=FORCE+[('accelerationunit','a'),('accelerationscale','b')]
COEFFICIENTS=[('longitudinal',R),('transverse',R)]
PRIMITIVES={
 'eisyr':([('element','a'),('frame','a'),('axis','a'),('lengthunit','a'),('forceunit','a')]+CALIBRATION+[('context','d')], 'elementの指定軸方向の可逆的な弾性変形について、無荷重配置からの符号付き変位をlengthunitで読むとき、range内の変位δに対する復元力の同じforceunitでの有向成分が−response(δ)であるという物理的応答。指定系の静的な釣合いにおける外から加える成分はresponse(δ)となる。弾性は荷重を除けば基準配置へ戻る復元作用として採り、単なる数値関数や不可逆な変形に替えない。線形Hooke則、全変位域、理想測定の実施済み、対象に働く他の力の不在は含めない。'),
 'eisys':(GAUGE, 'instrumentがelementの指定軸方向の変位を、同じlengthunitの無荷重基準から読み取る機構と、同じrange・responseによってその読みをforceunitの数値へ換算する校正された目盛りを備えるという装置の対応。弾性体への荷重の与え方と表示機構の対応を保持し、名前が秤であることや任意の表示関数で代用しない。elementの弾性応答、装置の静止、実際の使用、特定対象の測定の成功は別に要求する。'),
 'eisyt':([(n,'a') for n in ('operation','instrument','element','matter','forcerecord','frame','event','forceunit','lengthunit','axis')]+[('deflection',R),('source','d'),('alternative','d')], 'sourceで同じmatter・frame・event・forceunitに帰属するforcerecordの指定軸の機械的作用を比較対象としたoperationが、alternativeでinstrumentの同じelementへの等価な有向荷重として伝達又は静的に比較され、同じlengthunitの変位deflectionとして読み取られる対応。対象記録、軸、単位、無荷重基準を保ち、別の力や大きさだけの比較に交換しない。比較は当該の力の寄与を釣合いで同定する理想試行を許し、sourceの粒子軌道全体をalternativeでも保つこと、sourceで装置を実際に接続済みであること、力の数値が目盛りと一致すること、物理的に可能な試行であることは別条件にする。'),
}
MEANINGS={
 'ely':'同じPAIRの共動設定ek63に、同じk・電子・出来事・電荷記録・全単位のeibsを結ぶ。同じ新点ek5iでの実電場を三成分ベクトルへ構成し、指定したforcerecordとforceをεE′の電気的な機械的作用の記録へ結ぶ。瞬間静止する系の電磁的な力として用い、支持力を含む合力へ替えない。',
 'elz':'零を含む変位範囲においてresponseの値が全て有効で、response(0)=0、範囲内の異なる二変位に対して厳密単調増加するという校正曲線の数値条件。正の線形剛性に限定せず、零の一例や二点だけで全域の校正を認定しない。',
 'el2':'同じ装置の異なる弾性要素を部分zjgとして結び、同じ系・軸・二単位・変位域・応答曲線の物理的な復元作用eisyr、校正目盛りeisys、数値的校正elzと、装置の当該系への静止x4を合わせる。',
 'el3':'同じ元の力記録・対象・系・時点・単位を固定し、同じ操作の物理的に可能な結果zrdpossibleでel2の静止した装置とeisytの機械的比較を要求する。その実数変位が校正域に入り、同じresponseの値が指定したforceの同じ軸成分と等しい。成功した実際の測定又は元の粒子の全軌道を結果へ複製する主張ではない。',
 'el4':'同じinstrumentとelementを三成分の測定へ共有する。各軸についてel3を満たす操作・可能結果・校正域・曲線・変位が存在し、向きを変えた別の試行を許す。三軸を同時に同じ配置で測ることや三つの別装置を要求しない。',
 'el5':'同じ力の三成分をel4の仕方で測り得る一つの装置と弾性要素が存在する。ばね秤は可能な方法の一つであり、全ての測定法又は唯一の方法を尽くす定義にはしない。',
 'el6':'同じ電子・同じkの物理的な力elyと、その同じ力記録・三成分・単位・元状況を用いたばね秤での測定可能性el5を合わせる。装置の静止は結果状況のkであり、電子がKに静止する条件を足さない。',
 'el7':'同じPAIRについてel6を満たす力記録とベクトルが存在する。力の同定と測定可能性を別々の力の証人に分けない。',
 'ema':'同じ全共動設定ek63で、同じ実電場に由来する力記録とベクトルelyが存在するという、u0254第一文の物理的内容の候補。本文への提示と全単位判断は未追加。',
 'emb':'同じ全共動設定ek63でel7の力とばね秤測定の可能性を述べる閉じた内容。本文の括弧・例えばという例示・先行式への照応・全単位判断は次の統合へ残す。',
 'emc':'同じkの力elyを保ち、加速度単位を長さ/時間²の次元と正の尺度Aへ結ぶ。A T²=LかつM A=Fを要求し、同じ対象・出来事で力をk、加速度をKで測るzraconventionを指定する。加速度数値は既存のKの実二階微分と同じで、単位の換算を省略しない。',
 'emd':'emcの同じ物理設定に対する二質量係数の候補。現在の三加速度・同じ力の数値がsephを満たし、全六実数に対する係数恒等条件sepiを要求する。零加速度の一例だけで任意係数を正解にせず、全数値の実験的実現を要求しない。',
 'eme':'同じCONVENTIONの割当を答え候補の外側で固定してemdの縦横二実数を同時に問う質問。候補ごとに電子・速度・出来事・単位・規約・力を選び直さない。答えの存在、既知性又は著者の問いの提示は構成からは主張しない。',
 'emf':'emcの同じ物理設定と同じ実三成分のsephに、縦μβ³・横μβ²のsepfを結ぶ結論候補。現代の別の力の定義による横μβへ修正しない。',
 'emg':'同じ物理規約emcの下で、全六実数の係数同定emdと具体係数emfが同値になるという条件文。一般の実数体の定理や原文同義性を有限診断から認定しない。',
}
LIMITS=[
 'u0252第一文とu0254–u0258を統合するための物理的な依存群。既存423主張と255全単位判断を保持し、新しい全文判断は追加しない。力の同定、測定可能性、測定規約と係数の問いを同じ電子へ結ぶ。',
 '原刊919頁のponderomotorische Kraftを、共動系で瞬間静止する同じ電子への局所的な電磁的機械作用として読む。eibsの電気的寄与を使い、支持力を含む合力をεE′としない。実際のkの場・新点・電荷記録・量単位を共有する。',
 'ばね秤は可逆な弾性変形と復元作用、変位の読取り、力への校正目盛りを持つ装置として構成する。十分な範囲の一価で厳密単調な校正を採る。Hookeの線形則、特定材料、測定の無限精度又は実施済みは原文へ加えない。',
 'couldの可能性は既存zrdpossibleによる物理的な可能結果の存在として読む。各成分を同じ装置と弾性要素の別の向き・試行で測ることを許す。三方向の同時測定、任意の装置の成功、全試行結果での保証を要求しない。',
 '測定の比較対象は元状況の同じ力の寄与である。結果状況ではその作用を等価な機械的荷重として比較し、元の電子の加速軌道全体は要求しない。ばねの支持作用で電子を静止させた仮想配置と、元の自由な運動の矛盾を作らない。原文はこの比較の物理的可能性を主張するのであって、処理系が実験で立証するものではない。',
 '力・質量・座標の整合単位は先行ek3nを保ち、加速度単位を派生尺度A=L/T²として明示する。単位換算と、kの力/Kの加速度という物理的定義の選択を区別する。',
 '質量の候補は係数恒等条件sepiと現在の実三成分をともに満たすものとする。全数値を実際に観測したとはしない。X軸が瞬間速度方向で、Y/Zがその直交平面である先行配置を保持し、v=0では選択済みの軸と共通のμへの極限として読む。',
 '通常の考え方への沿い方、縦横という命名と幾何の説明、最初に注目するという談話順、例えばという例示、力の無修飾の呼称、条件付き規約採用、平方根の分母を持つ二表示式、著者帰属と一群の全文判断は未統合。数値や依存定義だけで完成件数を増やさない。',
]

def target_values():
    values={n:v(n) for n,t in TARGET};values['frame']=k('eisxy');return values

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] c.\n' for n,(fs,_) in PRIMITIVES.items())
    values=new_values();point=values['point'];electric=k('ekbe',*[app(app(values['electricfield'],k(axis)),*[coord(point,a) for a in ROLES]) for axis in ROLES[:3]])
    values.update(carrier=v('matter'),forcerecord=v('forcerecord'),fieldunit=v('electricunit'),force=v('force'),electric=electric,conversion=ONE)
    text+=define('ely',FORCE,both(k('ek63',*args(PAIR)),k('eibs',*[values[n] for n,t in ACTION])))
    delta=v('delta');other=v('other');response=lambda d:app(v('response'),d);inside=lambda d:both(k('ba',d),app(v('range'),d))
    calibrated=both(app(v('range'),ZERO),k('sca',response(ZERO),ZERO),q('f','delta',R,op('y',inside(delta),k('ba',response(delta)))),q('f','delta',R,q('f','other',R,op('y',both(inside(delta),inside(other),k('bg',delta,other)),k('bg',response(delta),response(other))))))
    text+=define('elz',CALIBRATION,calibrated)
    text+=define('el2',GAUGE,both(op('u',op('e',v('instrument'),v('element'))),k('zjg',v('element'),v('instrument'),v('context')),k('eisyr',*[v(n) for n,t in PRIMITIVES['eisyr'][0]]),k('eisys',*args(GAUGE)),k('elz',*args(CALIBRATION)),k('x4',v('instrument'),v('frame'),v('context'))))
    measured={n:v(n) for n,t in GAUGE};measured['context']=v('alternative')
    trial={n:v(n) for n,t in PRIMITIVES['eisyt'][0]};trial['source']=v('context')
    text+=define('el3',TRIAL,both(app(k('zrdpossible'),v('operation'),v('matter'),v('context'),v('alternative')),k('el2',*[measured[n] for n,t in GAUGE]),k('eisyt',*[trial[n] for n,t in PRIMITIVES['eisyt'][0]]),inside(v('deflection')),k('ba',app(v('force'),v('axis'))),k('sca',response(v('deflection')),app(v('force'),v('axis')))))
    measurements=[]
    for axis in ROLES[:3]:measurements.append(quantified('g',WITNESSES,k('el3',*[k(axis) if n=='axis' else v(n) for n,t in TRIAL])))
    text+=define('el4',TARGET+[('instrument','a'),('element','a')],both(*measurements))
    text+=define('el5',TARGET,q('g','instrument','a',q('g','element','a',k('el4',*args(TARGET),v('instrument'),v('element')))))
    text+=define('el6',FORCE,both(k('ely',*args(FORCE)),k('el5',*[target_values()[n] for n,t in TARGET])))
    text+=define('el7',PAIR,q('g','forcerecord','a',q('g','force',POINT,k('el6',*args(FORCE)))))
    actual=shared()+[v('forcerecord'),v('force')]
    text+=content('ema',quantified('f',BOUND,op('y',k('ek63',*shared()),q('g','forcerecord','a',q('g','force',POINT,k('ely',*actual))))))
    text+=content('emb',quantified('f',BOUND,op('y',k('ek63',*shared()),k('el7',*shared()))))
    rat=lambda n:'n '+('u' if n<0 else 'p')+' '+{0:'a',1:'b',2:'c'}[abs(n)]+' b'
    units=both(k('ejwb',v('accelerationunit'),rat(1),rat(0),rat(-2),v('accelerationscale'),v('context')),op('e',k('ad',v('accelerationscale'),k('ad',v('timescale'),v('timescale'))),v('lengthscale')),op('e',k('ad',v('massscale'),v('accelerationscale')),v('forcescale')))
    text+=define('emc',CONVENTION,both(k('ely',*args(FORCE)),units,k('zraconvention',v('matter'),k('eisxy'),k('ra'),v('event'),v('forceunit'),v('accelerationunit'),v('context'))))
    factors=[k('tc'),k('eisxt'),k('soy',k('tc'),k('eisxt')),v('mass'),*args(COEFFICIENTS)]
    components=k('seph',*args(COEFFICIENTS),*args(ACCEL),*[app(v('force'),k(a)) for a in ROLES[:3]])
    for name,numeric in [('emd','sepi'),('emf','sepf')]:text+=define(name,CONVENTION+COEFFICIENTS,both(k('emc',*args(CONVENTION)),components,k(numeric,*factors)))
    text+=define('eme',CONVENTION,'j v[i['+' '.join(n+' '+t for n,t in COEFFICIENTS)+']['+k('emd',*args(CONVENTION+COEFFICIENTS))+']]','g['+' '.join(t for n,t in COEFFICIENTS)+']')
    text+=define('emg',CONVENTION+COEFFICIENTS,op('y',k('emc',*args(CONVENTION)),op('z',k('emd',*args(CONVENTION+COEFFICIENTS)),k('emf',*args(CONVENTION+COEFFICIENTS)))))
    return text

@lru_cache(None)
def build():
    old=parse(read(PARENT));assert len(old['statements'])==423
    assert not(set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']
    added=doc['declarations'][len(old['declarations']):]
    prim={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,t in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='same_electron_force_spring_measurement_and_mass_candidates',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=prim,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[]).document
    ann=json.loads(read('data/electron-mass-rewrite-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode()))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
