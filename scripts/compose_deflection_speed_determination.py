"""Compose calibrated readouts and the complete deflection speed argument."""
from scripts.compose_electron_deflection_response import *
from scripts.compose_limits import F
from scripts.compose_material_acceleration import AT

PARENT=FULL;PARENT_BASIS=BASIS;PARENT_ANNOTATIONS=ANNOTATIONS
FULL='examples/v014/einstein-deflection-speed-determination.noema'
CORE='examples/v014/deflection-speed-determination-core.noema'
BASIS='data/deflection-speed-determination-basis-v1.json'
ANNOTATIONS='data/deflection-speed-determination-identifiers-v1.json'
QUANTITY=[(n,'a') for n in ('target','frame','event','unit')]+[('value',R),('context','d')]
QD='i[h[a a a a '+R+' d] c]';RULE='i[h['+' '.join([R]*3)+'] c]'
CAL=[('method','a'),('instrument','a'),('quantity',QD),('frame','a'),('unit','a'),('range',DOMAIN),('calibration',F),('context','d')]
ACQUIRE=[(n,'a') for n in ('observer','method','instrument','record','target')]+[('quantity',QD)]+[(n,'a') for n in ('frame','event','unit')]+[('signal',R),('context','d')]
READOUT=ACQUIRE+[('range',DOMAIN),('calibration',F),('value',R)]
DEVICE=[(n,'a') for n in ('method','instrument','record')]+[('range',DOMAIN),('calibration',F),('signal',R)]
CHANNELS=('electricacc','magneticacc','electricfield','magneticfield')
INSTRUMENTS=[(pre+n,t) for pre in CHANNELS for n,t in DEVICE]
MEASUREMENT=RESPONSE+[('observer','a'),('assessment','d'),('accelerationunit','a'),('accelerationscale','b')]+INSTRUMENTS+[('ratio',R),('recovered',R)]
MEASURE_WITNESSES=[(n,t) for n,t in MEASUREMENT if n not in dict(BACKGROUND)]
PRIMITIVES={
 'eis3r':(CAL,'同じmethodのinstrumentが、quantityで記述された物理量に対する応答と標準との比較によって校正されており、range内の読み取り信号をcalibrationで同じframeとunitの量数値へ変換するという物理的対応。単なる任意の数値関数、装置名又は既知の答えの埋込みとは区別する。量の具体的意味は引用する定義へ与える。実際の使用・成功した読み取り、全装置の校正、対象命題の真理は含意しない。理想化した測定尺度の値を使い、有限装置が任意実数の全桁を出力することは要求しない。'),
 'eis3s':(ACQUIRE,'observerが同じmethodとinstrumentを用い、targetの指定frame・event・unitにおけるquantityのための物理的な観測操作を行い、その読み取り信号signalをrecordに取得したこと。対象への測定結合、同じ出来事と量の選択、観測から記録への因果的な取得を含む。数値が合うだけ、仮定した結果記録、別の量の読み取り又は装置が存在するだけでは成立しない。校正・信号域・変換後の実際の量との一致は合成で別に要求する。'),
 'eis3t':([('observer','a'),('rule',RULE),('left',R),('right',R),('result',R),('context','d')],'observerが同じcontextで、引用した二入力一出力の算術関係ruleに従う計算操作を行い、与えられたleft/rightからresultを得たこと。規則の記述と入力順序を保持し、単に関係が成立すること、未実行の計算可能性又はあらゆる関係を解く万能手続きとは区別する。ここで使う絶対値の規格化、非零分母の除算、乗算は別の定義へ明示し、結果の正しさは数値関係を併せて要求する。'),
 'eis3u':([('observer','a'),('record','a'),('acquisition','d'),('assessment','d')],'同じobserverがacquisitionで取得した同じrecordが、同じ可能な実験過程の後続又は同じassessmentへ保存・伝達され、そこで利用できるという因果的な記録の対応。別々に可能な相容れない世界の結果を集める関係ではない。過程と取得の同一性を保持し、記録内容の正しさ・理論との一致は別に要求する。'),
 'eis3v':([('part','i[e]'),('whole','i[e]'),('ordinal','b'),('context','d')],'wholeとして記述された順序ある式又は内容のまとまりのordinal番目をpartの内容として取り出す構造的な対応。同じ対象・量・単位・条件を保持し、順序を単なる見た目や任意の数へ交換しない。部分又は全体の真理、導出の妥当性、相互の論理同値は含めない。'),
}
REFERENCES=dict(zip(('eis3w','eis3x','eis3y','eis3z','eis32','eis33','eis34','eis35'),(
 'u0265の実験で調べ得る運動特性の列挙を導入する箇所への参照。この導入自体の全文判断はまだ行わない。',
 'u0266の番号1の項全体を指す箇所。','u0266第一文で第二(A)から同じ強さの偏向条件を得る箇所。',
 'u0266第二文で同じ理論により任意の許容速度を偏向応答の比から決定できると述べる箇所。',
 'u0267のAm/Ae=v/Vの表示箇所。','u0266–u0267の磁気的な偏向応答を呼ぶ記号Am。','同じ電気的な偏向応答を呼ぶ記号Ae。',
 '同じ現在の電子の非零符号付き電荷と単位尺度を指定する基準記録。実測済みの標識ではない。')))
MEANINGS={
 'eqs':'同じ対象・系・出来事の横座標加速度の数値を指定加速度単位へ結ぶ一般的な量の意味。校正履歴とseppの実二階微分、長さ時間と加速度単位の正の尺度A T²=Lを存在量化して共有する。量のラベルや見かけの曲率だけで代用しない。',
 'eqt':'同じ対象の指定出来事・系・単位の電場y成分という量。ejsnの物理的場規約、単位付きの同じ四位置、同じ電場の評価を共有する。電子への力qYそのものとは分ける。',
 'equ':'同じ対象の指定出来事・系・単位の磁場z成分という量。eqtと同じ仕方で実磁場と単位を結び、磁気力−qvN/Vそのものとは分ける。',
 'eqv':'同じ量記述・方法・装置・単位の物理的校正eis3rと、同じ対象・出来事の信号取得eis3sを合わせ、信号域とcalibration(signal)=valueを要求する。仮定上の数値記録だけを測定成功にしない。',
 'eqw':'有効な符号付き加速度と正の場成分から、絶対値を場成分で割った非負応答を指定する算術関係。二乗等式と符号で負枝を除く。',
 'eqx':'有効な二実数と非零分母について、left/right=resultという商の算術関係。',
 'eqy':'有効な二実数について、left*right=resultという積の算術関係。',
 'eqz':'同じ背景の許容された電場単独・磁場単独の二つの物理試行eqh。第二(A)や比の成立を測定の対象条件へ先取りしない。',
 'eq2':'同じeqzの二実横加速度と正のY,NにAe,Amの規格化を結ぶ。旧eqmから第二(A)を前提にする部分を外した、観測の対象となる物理的な応答。',
 'eq3':'同じ長さ時間と指定加速度単位の正の尺度がA T²=Lを満たす。二階座標微分の数値を別尺度の加速度へ無換算で交換しない。',
 'eq4':'同じ物理応答eq2について、四つの量の校正された信号取得、同じ観測者への記録の持越し、二応答の規格化・比・速度への乗算を一つの許容された評価状況へ結ぶ。数値取得からの計算を含むが、復元値と元の速さの一致はこの測定構成の前提にしない。',
 'eq5':'同じ背景の一つの指定速さについて、eq4の全試行・四観測・同じ観測者と評価・計算結果が存在し、その復元値が同じ元の速さと一致するという決定可能性。別々の相容れない試行をまとめず、基準状況での実施済みを主張しない。',
 'eq6':'同じ現在の電子・K・電荷・低速質量と校正単位の基準を、正の電荷尺度とともに固定する。許容速度の範囲は正の同じVに対して定める。',
 'eq7':'同じ論説の理論と一つの基準電荷尺度を固定し、0≤v<Vの全ての有効な速さについてeq5の同じ電子の速度決定が可能であるという内容。低速近似又は測定済み標本だけに縮めず、零速度も理想的な局所応答の読みで含む。',
 'era':'同じ基準を持つ現在の電子の全ての物理試行eqhに第二(A)のsetkを適用する閉じた内容。先行三式elkの第二行を指すための投影であり、他の二行や共動系の横質量を混ぜない。',
 'erb':'同じ基準の全二試行eqzについて、非負のY,NがVY=vNなら二つの横加速度の大きさが等しいという内容。両場を同時に与える第三試行をこの原文条件へ追加しない。',
 'erc':'同じ基準を持つ全物理応答eq2について、正のAeと非負のAmの比がv/Vになるという数式内容。表示単位だけを取り出しても同じ電子・場・履歴・単位の意味へ接続する。',
 'erd':'同じ原文の比ercを使って任意速度の決定eq7を行うという理由接続で用いる、比と決定可能性のまとまり。測定可能性を比の数式だけから処理系が証明したとはしない。',
 'ere':'u0266全文の第一項番号、第二(A)への照応と帰結、二偏向の同じ強さ、同じ理論下の任意速度の決定、比の式への前方参照とAm/Aeの命名を保持する。',
 'erf':'現在の電子の同じ物理応答eq2における磁気側の値を記号Amへ対応させる命名規則。',
 'erg':'現在の電子の同じ物理応答eq2における電気側の値を記号Aeへ対応させる命名規則。',
 'erh':'u0266全文のメッセージ。','eri':'u0266を同じ著者・論説へ帰属し、列挙導入後の第一項に置く。',
 'erj':'同じ比ercをu0267の式表示と著者の主張として提示する。','erk':'u0267全文のメッセージ。','erl':'u0267を同じ著者・論説へ帰属し、u0266の式への前方参照に続ける。',
}
LIMITS=[
 '原刊920頁u0266全文とu0267のM0436を扱う。Y,Nは場成分、vは同じKの瞬間速さで、第二(A)の横成分を使う。Ablenkbarkeitは同じ校正の局所横加速度の大きさを正の場成分で規格化した応答と読む。有限距離の変位や曲率を無条件に同一視しない。',
 '測定は具体的な物理量の記述、装置の物理的な校正、同じ対象・出来事の信号取得、取得記録の因果的な保存、数値変換と算術操作から構成する。校正と取得は一般的な物理入力であり、無説明の測定ラベル・任意関数・仮定された数値だけでは代用しない。原文が装置の回路や操作細目を明記したとは扱わない。',
 '加速度は同じ長さ時間の実二階微分、電場・磁場は同じ指定点の物理的二場である。四読取りは同じ電子・速度・質量・電荷・単位の別試行でよいが、同じ観測者が同じ可能過程で記録を利用できることを要求する。相容れない別世界で独立に可能な結果だけを合成しない。',
 '任意速度は同じ理論の0≤v<Vの全範囲で、低速近似へ限定しない。零速度には局所加速度の理想測定という読みを適用し、静止電子が通過型装置を通るという追加主張はしない。有限測定器による全実数の全桁出力や誤差零の現実実験を完成条件にしない。',
 '測定構成eq4に第二(A)、比の真理又は復元値と実速度の一致を前件として埋め込まない。一致は決定成功eq5、全速度でのその可能性は著者主張eq7で要求する。数式から装置の実現を自動導出しない。後続u0268での独立した直接測定との比較にこの区別を残す。',
 '先行の三式(A)の第二行をeraとして指定し、同じ強さの条件と速度決定を著者の理由として接続する。Man ersieht alsoは観測者全員の現実の認識ではなく論述上の帰結提示と読む。Am/Aeの順序、正の分母とVの既出の同一性を保つ。',
 '旧432主張と判断・意味・証拠を保存する。u0265の列挙導入自体、u0268の独立直接測定と高速振動場の例はこの二単位の判断に含めない。局所有限検査は物理法則・全実数域・原文同義性の自動証明ではない。',
]

def rat(n):return 'n '+('u' if n<0 else 'p')+' '+{0:'a',1:'b',2:'c'}[abs(n)]+' b'
def current(fields,**replace):
    special={'speed':v('speed'),'chargescale':v('chargescale'),'view':k('eis3k'),'context':v('point')}
    return [replace.get(n,special.get(n,k(FIXED[n]) if n in dict(SHARED) and n in FIXED else v(n))) for n,t in fields]
def read_arguments(channel,quantity,value,unit):
    pre='electric' if channel.startswith('electric') else 'magnetic'
    supplied={n:v(channel+n) for n,t in DEVICE}|dict(observer=v('observer'),target=v('matter'),quantity='r[p '+quantity+']',frame=v('frame'),event=v(pre+'event'),unit=unit,context=v(pre+'scene'),value=value)
    return [supplied[n] for n,t in READOUT]

def definitions():
    text=''.join('r '+n+'['+' '.join(t for n,t in fs)+'] c.\n' for n,(fs,m) in PRIMITIVES.items())+''.join('r '+n+'[] a.\n' for n in REFERENCES)
    zero=k('bb',rat(0));one=k('bb',rat(1));ctx=v('context');sq=lambda x:k('shv',x,x)
    # Canonical scalar quantity descriptions, shared by calibration and acquisition.
    accfields=[(n,t) for n,t in KINEMATIC if n not in ('matter','frame','event','context','ay','region')]+[(n,'b') for n in ('lengthscale','timescale','accelerationscale')]
    whole='i[x '+R+' y '+R+' z '+R+' time '+R+']['+both(*(k('ba',v(n)) for n in ('x','y','z','time')))+']'
    vals={n:v(n) for n,t in KINEMATIC}|dict(matter=v('target'),ay=v('value'),region=whole)
    units=both(k('ejwb',v('unit'),rat(1),rat(0),rat(-2),v('accelerationscale'),ctx),k('ejwb',v('lengthunit'),rat(1),rat(0),rat(0),v('lengthscale'),ctx),k('ejwb',v('timeunit'),rat(0),rat(0),rat(1),v('timescale'),ctx),op('e',k('ad',v('accelerationscale'),k('ad',v('timescale'),v('timescale'))),v('lengthscale')))
    text+=define('eqs',QUANTITY,quantified('g',accfields,both(k('ek3q',*[vals[n] for n,t in KINEMATIC]),units)))
    for name,unit,field,axis in [('eqt','electricunit','electricfield',ROLES[1]),('equ','magneticunit','magneticfield',ROLES[2])]:
        witnesses=[(n,t) for n,t in FIELDS if n not in ('frame','context',unit)]+[('location',POINT)]
        fields={n:v(n) for n,t in FIELDS}|{unit:v('unit')};loc=v('location')
        body=both(k('ba',v('value')),k('ejsn',*[fields[n] for n,t in FIELDS]),k('eisqd',v('target'),v('frame'),v('event'),v('lengthunit'),v('timeunit'),loc,ctx),k('ejsj',loc,v('region')),k('sca',app(app(v(field),k(axis)),*(coord(loc,a) for a in ROLES)),v('value')))
        text+=define(name,QUANTITY,quantified('g',witnesses,body))
    text+=define('eqv',READOUT,both(k('eis3r',*args(CAL)),k('eis3s',*args(ACQUIRE)),k('ba',v('signal')),app(v('range'),v('signal')),k('ba',v('value')),k('sca',app(v('calibration'),v('signal')),v('value'))))
    scalar=[(n,R) for n in ('left','right','result')];left=v('left');right=v('right');result=v('result');valids=[k('ba',x) for x in (left,right,result)]
    text+=define('eqw',scalar,both(*valids,k('bg',zero,right),k('bc',zero,result),k('sca',sq(left),sq(k('shv',right,result)))))
    text+=define('eqx',scalar,both(*valids,op('u',k('sca',right,zero)),k('sca',left,k('shv',right,result))))
    text+=define('eqy',scalar,both(*valids,k('sca',k('shv',left,right),result)))
    Y=v('electricstrength');N=v('magneticstrength');Ae=v('electricresponse');Am=v('magneticresponse');V=v('light');speed=v('speed')
    physicalpair=both(k('eisoe',v('view'),ctx,v('electricscene')),k('eisoe',v('view'),ctx,v('magneticscene')),k('eqh',*case_args('electric',Y,zero)),k('eqh',*case_args('magnetic',zero,N)))
    text+=define('eqz',PAIR,physicalpair)
    text+=define('eq2',RESPONSE,both(k('eqz',*args(PAIR)),k('eqw',v('electricay'),Y,Ae),k('eqw',v('magneticay'),N,Am),k('bg',zero,Ae)))
    unitfields=[('lengthscale','b'),('timescale','b'),('accelerationunit','a'),('accelerationscale','b'),('context','d')]
    text+=define('eq3',unitfields,both(k('ejwb',v('accelerationunit'),rat(1),rat(0),rat(-2),v('accelerationscale'),ctx),k('aa',rat(0),v('lengthscale')),k('aa',rat(0),v('timescale')),op('e',k('ad',v('accelerationscale'),k('ad',v('timescale'),v('timescale'))),v('lengthscale'))))
    clauses=[k('eq2',*args(RESPONSE)),k('eisoe',v('view'),ctx,v('assessment'))]
    for pre in ('electric','magnetic'):clauses.append(k('eq3',v('lengthscale'),v('timescale'),v('accelerationunit'),v('accelerationscale'),v(pre+'scene')))
    specs=[('electricacc','eqs',v('electricay'),v('accelerationunit')),('magneticacc','eqs',v('magneticay'),v('accelerationunit')),('electricfield','eqt',Y,v('electricunit')),('magneticfield','equ',N,v('magneticunit'))]
    for channel,quantity,value,unit in specs:
        pre='electric' if channel.startswith('electric') else 'magnetic'
        clauses += [k(quantity,v('matter'),v('frame'),v(pre+'event'),unit,value,v(pre+'scene')),k('eqv',*read_arguments(channel,quantity,value,unit)),k('eis3u',v('observer'),v(channel+'record'),v(pre+'scene'),v('assessment'))]
    for rule,x,y,z in [('eqw',v('electricay'),Y,Ae),('eqw',v('magneticay'),N,Am),('eqx',Am,Ae,v('ratio')),('eqy',V,v('ratio'),v('recovered'))]:clauses += [k(rule,x,y,z),k('eis3t',v('observer'),'r[p '+rule+']',x,y,z,v('assessment'))]
    text+=define('eq4',MEASUREMENT,both(*clauses))
    text+=define('eq5',BACKGROUND,quantified('g',MEASURE_WITNESSES,both(k('eq4',*args(MEASUREMENT)),k('sca',v('recovered'),speed))))
    base={'matter':k('eisxh'),'frame':k('ra'),'event':k('eisxv'),'chargerecord':k('eis35'),'chargescale':v('chargescale'),'context':ctx}|{n:k(FIXED[n]) for n,t in SHARED if n in FIXED}
    text+=define('eq6',[('chargescale','b'),('context','d')],both(k('ek3n',*[base[n] for n,t in UNITS]),k('ek3o',*[base[n] for n,t in MASS]),k('ek3u',*[base[n] for n,t in CHARGE]),k('ba',k('tc')),k('bg',zero,k('tc'))))
    p=v('point');theory=k('eiscv',k('eis3k'),k('eirf'),quote('eigj'),p)
    scope=lambda body:both(theory,quantified('g',[('chargescale','b')],both(k('eq6',v('chargescale'),p),body)))
    allowed=both(k('ba',speed),k('bc',zero,speed),k('bg',speed,k('tc')))
    text+=content('eq7',scope(quantified('f',[('speed',R)],op('y',allowed,k('eq5',*current(BACKGROUND))))))
    casebound=[('speed',R)]+TRACE+STRENGTHS
    law=k('setk',k('tc'),speed,k('soy',k('tc'),speed),k('eis2a'),k('zrgcharge'),Y,N,v('ay'))
    # The accessibility guard retains the same theory in the source projection.
    antecedent=both(k('eisoe',k('eis3k'),p,v('scene')),k('eqh',*current(CASE)))
    text+=content('era',scope(quantified('f',casebound,op('y',antecedent,law))))
    pairbound=[('speed',R)]+WITNESSES+STRENGTHS
    equal=k('sca',sq(v('electricay')),sq(v('magneticay')))
    text+=content('erb',scope(quantified('f',pairbound,op('y',both(k('eqz',*current(PAIR)),k('seto',k('tc'),speed,Y,N)),equal))))
    responsebound=pairbound+COEFFICIENTS
    text+=content('erc',scope(quantified('f',responsebound,op('y',k('eq2',*current(RESPONSE)),k('sets',k('tc'),speed,Ae,Am)))))
    text+=content('erd',both(op('t',k('erc'),p),op('t',k('eq7'),p)))
    for name,selected in [('erf','magneticresponse'),('erg','electricresponse')]:
        fields=[('chargescale','b')]+[(n,t) for n,t in responsebound if n!=selected]
        vals=current(RESPONSE,context=ctx,**{selected:v('value')})
        text+=define(name,[('matter','a'),('value',R),('context','d')],both(op('e',v('matter'),k('eisxh')),quantified('g',fields,both(k('eq6',v('chargescale'),ctx),k('eq2',*vals)))))
    who=k('rd');paper=k('eirf');section=k('eisxg');node=k('eis3x');reason=k('eis3y');det=k('eis3z');display=k('eis32')
    text+=content('ere',both(k('eislk',node,k('eis3w'),rat(1),paper,p),k('eis3v',quote('era'),quote('elk'),rat(2),p),k('eiswm',reason,who,k('eisym'),quote('elk'),paper,p),k('zc',reason,who,quote('era'),quote('erb'),section,p),k('uh',reason,who,quote('erb'),section,p),k('zc',det,who,quote('erb'),quote('eq7'),section,p),k('zc',det,who,quote('erc'),quote('eq7'),section,p),k('uh',det,who,quote('eq7'),section,p),k('eisnw',det,who,k('eis33'),'r[p erf]',paper,p),k('eisnw',det,who,k('eis34'),'r[p erg]',paper,p),k('uf',who,det,display,p),k('ue',reason,det,p),k('ue',det,display,p)))
    text+='d erh[] f[j s[k ere[]]].\n'
    text+=define('eri',[],both(k('eir3',node,who,paper,quote('erh'),k('ri')),k('ue',k('eis3w'),node,k('ri'))))
    text+=content('erj',both(k('eisox',display,quote('erc'),p),k('uh',display,who,quote('erc'),section,p)))
    text+='d erk[] f[j s[k erj[]]].\n'
    text+=define('erl',[],both(k('eir3',display,who,paper,quote('erk'),k('ri')),k('ue',node,display,k('ri'))))
    return text

@lru_cache(None)
def build():
    old=parse(read(PARENT));assert len(old['statements'])==432
    assert not(set(MEANINGS)|set(PRIMITIVES)|set(REFERENCES))&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol=n,arguments=[])) for n in ('eri','erl')]
    added=doc['declarations'][len(old['declarations']):]
    prim={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,t in PRIMITIVES[d['name']][0]] if d['name'] in PRIMITIVES else [],meaning_ja=PRIMITIVES[d['name']][1] if d['name'] in PRIMITIVES else REFERENCES[d['name']]) for d in added if d['kind']=='primitive'}
    basis=dict(status='calibrated_deflection_readouts_and_all_speed_determination',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=prim,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[432,433]).document
    ann=json.loads(read(PARENT_ANNOTATIONS));ann.update(document=FULL,document_sha256=digest(body.encode()))
    for symbol,form in [('eis33','A_m'),('eis34','A_e')]:ann['entries'].append(dict(symbol=symbol,role='designation',forms=[dict(text=form,language='de',role='printed_identifying_form')]))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
