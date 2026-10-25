"""Bind the two transverse responses to calibrated trials of the same electron."""
from scripts.compose_kinetic_energy_consequences import *
from scripts.compose_point_particle_dynamics import KINEMATIC,UNITS,MASS,CHARGE,FIELDS
from scripts.compose_electric_action import FIELDS as ELECTRIC
from scripts.compose_magnetic_action import FIELDS as MAGNETIC
from scripts.compose_material_acceleration import PROFILES,ACCEL

PARENT=FULL;PARENT_BASIS=BASIS;PARENT_ANNOTATIONS=ANNOTATIONS
FULL='examples/v014/einstein-electron-deflection-response.noema'
CORE='examples/v014/electron-deflection-response-core.noema'
BASIS='data/electron-deflection-response-basis-v1.json'
ANNOTATIONS='data/electron-deflection-response-identifiers-v1.json'
SHARED=[(n,'a') for n in ('matter','frame','lengthunit','timeunit','massunit','forceunit','chargeunit','electricunit','magneticunit')]+[(n,'b') for n in ('lengthscale','timescale','massscale','forcescale','chargescale')]+[(n,R) for n in ('light','speed','mass','charge')]
TRACE=[('event','a'),('scene','d'),('domain',DOMAIN),('curve',CURVE),('location',POINT)]+PROFILES+ACCEL+[(n,FIELD) for n in ('electricfield','magneticfield')]+[('region',REGION)]+[(n,'a') for n in ('chargerecord','electricrecord','magneticrecord')]
STRENGTHS=[('electricstrength',R),('magneticstrength',R)]
COEFFICIENTS=[('electricresponse',R),('magneticresponse',R)]
BACKGROUND=SHARED+[('view','a'),('context','d')]
CASE=SHARED+TRACE+STRENGTHS
prefixed=lambda prefix:[(prefix+n,t) for n,t in TRACE]
PAIR=BACKGROUND+prefixed('electric')+prefixed('magnetic')+STRENGTHS
TRIPLE=PAIR+prefixed('combined')
RESPONSE=PAIR+COEFFICIENTS
POSSIBLE=BACKGROUND+STRENGTHS+COEFFICIENTS
WITNESSES=prefixed('electric')+prefixed('magnetic')
MEANINGS={
 'eqh':'同じ電子・系・出来事の正の低速質量と非零符号付き電荷、校正された全履歴と実二階微分、整合単位、実二場と二つの力の寄与を結ぶ横偏向の試行。指定点の速度は(v,0,0)、電場は(0,Y,0)、磁場は(0,0,N)。場成分のY,Nを電子への力そのものへ替えず、電気力qYと磁気力−qvN/Vを別の記録へ結ぶ。運動方程式を前提へ混ぜない。',
 'eqi':'同じeqhの実際の横加速度に、第二(A)のsetkを適用する。係数はKの場に対するμβで、共動系の力についての横質量μβ²とは別である。',
 'eqj':'同じ電子・系・速さ・低速質量・電荷・全単位を固定し、同じ見解が許す電場単独と磁場単独の二状況でeqiを要求する。二つの履歴・出来事・場・記録は各試行内で共有し、同一の実現状況や同じ全軌道を要求しない。',
 'eqk':'eqjの二試行と同じ背景・Y,Nを共有する、両場を同時に与えた第三の許容試行のeqiを合わせる。別の速度又は別の荷電粒子の反応を比較しない。',
 'eql':'同じ三試行eqkで非負のY,NがVY=vNを満たすと、二つの横加速度は逆向きで大きさが等しく、両場の横加速度は零になるという条件文。原文第一項を接続する依存候補であり、著者への帰属又は全速度の実験可能性ではない。',
 'eqm':'同じeqjの二つの実横加速度の大きさを、それぞれの正の場成分で割った正のAeと非負のAmへ結ぶ。長さ・時間と二場の単位は共通背景に固定され、任意の幾何係数を置いて比だけを合わせない。数値を読み取る測定装置や測定の可能性は別に必要。',
 'eqn':'同じ実応答eqmと、同じV,v,Ae,Amの比setsを合わせる。分母Aeの正性を保ち、異なる試行の速度・単位を混ぜない。',
 'eqo':'同じ実応答eqmならAm/Ae=v/Vであるという条件文。二つの(A)と正の規格化からの依存候補であり、原文の推論・法則の提示や実測済みの主張ではない。',
 'eqp':'同じ実応答eqmを固定した上で、V Am/Aeという数値を復元速度候補recoveredへ結ぶ。Ae=0を許さず、元の速さとの一致や全速度での測定可能性はこの候補の構成から自動認定しない。',
 'eqq':'同じ背景・二場強度・二応答係数に対し、eqmへ結び付く二つの完全な試行の証人が存在する。各試行の出来事・物理状況・履歴・場・記録を一組にして量化する。実測の記録や数値読み取り装置の存在には替えない。',
 'eqr':'同じ具体的な二試行と応答係数を外で固定し、eqpの復元速度候補を問う実数質問。答えの既知性や実験実施を含めない。',
}
LIMITS=[
 'u0266–u0267の第二(A)、電気的Y・磁気的Nによる横偏向とAm/Ae=v/Vを統合する依存群。旧432主張と全文判断267件を保存し、この段階では新たな全文判断又は著者主張を追加しない。',
 '先行(A)と同じKで瞬間速度を(v,0,0)とする標準配置を使う。Y,Nは単位電荷の電気的作用と速度依存の磁気的作用を定める場成分であり、電子への二つの機械的寄与qY,−qvN/Vとは分ける。局所点で他成分零とし、全空間で一様な場又は有限期間の等加速を補わない。',
 'Ablenkbarkeitを同じ状態の横座標加速度の大きさの場成分単位当たりの応答として読む候補。実際の校正履歴と二階微分に接続し、共通の任意gainは導入しない。スクリーン上の有限変位や曲率の無条件な同一視はせず、それらを使う場合の幾何・時間条件は別に必要。',
 '比較される試行は同じ理論の全許容状況に属する別状況でよい。電子・系・速さ・低速質量・電荷・長さ時間質量力電荷と二場単位を外側で共有する。試行があること、全速度で試行できること、結果を観測して速度を知れることを分ける。',
 '場強度による規格化ではY,N>0、Ae>0、Am>=0を要求する。零速度では磁気側の応答零という数値関係を含むが、静止粒子の通過型装置で測定できると追加しない。釣合条件と(A)の数式自体は零の場も扱い、電荷の正負による向きの反転を保持する。',
 'ejsnの物理的な場規約で電気換算1・磁気換算1/Vを固定し、ek3nのF T²=M Lを満たす同じ単位を使う。SIの裸の場数値をそのまま比較せず、単位変更時は帰属と換算条件も一緒に変える。',
 'u0265の列挙予告、u0266の第二式からの著者の理由・任意速度での決定可能性、u0267の式表示とAm/Aeの指示、u0268の独立直接測定と振動場の例は全文統合へ残る。有限数値・束縛・役割検査を全実数域又は原文同義性の証明へ替えない。',
]

def case_args(prefix,electric,magnetic):
    return [electric if n=='electricstrength' else magnetic if n=='magneticstrength' else v(prefix+n) if n in dict(TRACE) else v(n) for n,t in CASE]

def definitions():
    zero=k('bb','n p a b');one=k('bb','n p b b');ctx=v('scene');loc=v('location');V=v('light');speed=v('speed');charge=v('charge');Y=v('electricstrength');N=v('magneticstrength')
    vec=lambda x,y,z:k('ekbe',x,y,z)
    electric=vec(zero,Y,zero);magnetic=vec(zero,zero,N);velocity=vec(speed,zero,zero)
    values={n:v(n) for n,t in CASE}|dict(context=ctx,point=loc,carrier=v('matter'),electricconversion=one,magneticconversion=k('sjd',V))
    physical=[k('ejsn',*[values[n] for n,t in FIELDS]),k('ek3n',*[values[n] for n,t in UNITS]),k('ek3o',*[values[n] for n,t in MASS]),k('ek3u',*[values[n] for n,t in CHARGE]),k('ek3q',*[values[n] for n,t in KINEMATIC]),k('eisqd',v('matter'),v('frame'),v('event'),v('lengthunit'),v('timeunit'),loc,ctx)]
    moment=coord(loc,ROLES[3]);physical += [k('s45',V,speed),k('bc',zero,speed)]
    physical += [k('sca',app(v(n),moment),value) for (n,t),value in zip(PROFILES,(speed,zero,zero))]
    ea=values|dict(forcerecord=v('electricrecord'),fieldunit=v('electricunit'),electric=electric,force=vec(zero,k('shv',charge,Y),zero),conversion=one)
    ma=values|dict(forcerecord=v('magneticrecord'),magnetic=magnetic,velocity=velocity,force=vec(zero,k('bf',zero,k('shv',charge,k('shv',speed,k('shv',N,k('sjd',V))))),zero),conversion=k('sjd',V))
    physical += [k('eibs',*[ea[n] for n,t in ELECTRIC]),k('eico',*[ma[n] for n,t in MAGNETIC])]
    # Keep the actual field values explicit even when an action relation is abstracted in a role test.
    coords=[coord(loc,a) for a in ROLES]
    physical += [k('sca',app(app(v(field),k(axis)),*coords),value) for field,vals in [('electricfield',(zero,Y,zero)),('magneticfield',(zero,zero,N))] for axis,value in zip(ROLES[:3],vals)]
    text=define('eqh',CASE,both(*physical))
    numeric=k('setk',V,speed,k('soy',V,speed),v('mass'),charge,Y,N,v('ay'))
    text+=define('eqi',CASE,both(k('eqh',*args(CASE)),numeric))
    access=lambda pre:k('eisoe',v('view'),v('context'),v(pre+'scene'))
    pair=both(access('electric'),access('magnetic'),k('eqi',*case_args('electric',Y,zero)),k('eqi',*case_args('magnetic',zero,N)))
    text+=define('eqj',PAIR,pair)
    text+=define('eqk',TRIPLE,both(k('eqj',*args(PAIR)),access('combined'),k('eqi',*case_args('combined',Y,N))))
    square=lambda value:k('shv',value,value)
    equal=both(k('sca',square(v('electricay')),square(v('magneticay'))),k('sca',v('electricay'),k('bf',zero,v('magneticay'))),k('sca',v('combineday'),zero))
    text+=define('eql',TRIPLE,op('y',both(k('eqk',*args(TRIPLE)),k('seto',V,speed,Y,N)),equal))
    Ae=v('electricresponse');Am=v('magneticresponse')
    response=both(k('eqj',*args(PAIR)),*(k('ba',x) for x in (Y,N,Ae,Am)),*(k('bg',zero,x) for x in (Y,N,Ae)),k('bc',zero,Am),k('sca',square(k('shv',Ae,Y)),square(v('electricay'))),k('sca',square(k('shv',Am,N)),square(v('magneticay'))))
    text+=define('eqm',RESPONSE,response)
    ratio=k('sets',V,speed,Ae,Am)
    text+=define('eqn',RESPONSE,both(k('eqm',*args(RESPONSE)),ratio))
    text+=define('eqo',RESPONSE,op('y',k('eqm',*args(RESPONSE)),ratio))
    text+=define('eqp',RESPONSE+[('recovered',R)],both(k('eqm',*args(RESPONSE)),k('ba',v('recovered')),k('sca',v('recovered'),k('sett',V,Ae,Am))))
    text+=define('eqq',POSSIBLE,quantified('g',WITNESSES,k('eqm',*args(RESPONSE))))
    text+=define('eqr',RESPONSE,'j v[i[recovered '+R+']['+k('eqp',*args(RESPONSE),v('recovered'))+']]','g['+R+']')
    return text

@lru_cache(None)
def build():
    old=parse(read(PARENT));assert len(old['statements'])==432
    assert not set(MEANINGS)&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']
    added=doc['declarations'][len(old['declarations']):]
    basis=dict(status='physical_transverse_trial_and_response_dependency',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[]).document
    ann=json.loads(read(PARENT_ANNOTATIONS));ann.update(document=FULL,document_sha256=digest(body.encode()))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
