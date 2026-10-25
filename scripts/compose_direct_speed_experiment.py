"""Connect an independent speed measurement, a real comparison and oscillating fields."""
from scripts.compose_deflection_speed_determination import *
from scripts.compose_kinetic_energy_consequences import MOTION
from scripts.compose_field_transform import point_expression

PARENT=FULL;PARENT_BASIS=BASIS;PARENT_ANNOTATIONS=ANNOTATIONS
FULL='examples/v014/einstein-direct-speed-experiment.noema';CORE='examples/v014/direct-speed-experiment-core.noema'
BASIS='data/direct-speed-experiment-basis-v1.json';ANNOTATIONS='data/direct-speed-experiment-identifiers-v1.json'
SPEED_UNITS=[('lengthscale','b'),('timescale','b'),('speedunit','a'),('speedscale','b'),('context','d')]
DETAIL=[('event','a'),('scene','d'),('speedunit','a'),('speedscale','b')]+DEVICE
DIRECT=BACKGROUND+[('observer','a'),('assessment','d')]+DETAIL
COMPARED=MEASUREMENT+[('direct'+n,t) for n,t in DETAIL]+[('agrees','c')]
OSCILLATION=[('profile',F)]+[(n,R) for n in ('period','center','positive','negative','lower','upper')]
EXTRA=[(n,t) for n,t in FIELDS if n not in dict(DIRECT)]+[(n,R) for n in ('x','y','z','lower','upper','threshold')]+[(pre+n,t) for pre in ('electric','magnetic') for n,t in OSCILLATION if n not in ('lower','upper')]
EXAMPLE=DIRECT+EXTRA
COUPLING=ACQUIRE+[(n,t) for n,t in FIELDS if n not in dict(ACQUIRE)]+[(n,R) for n in ('lower','upper','x','y','z')]
PRIMITIVES={
 'eis36':([('method','a'),('claim','i[e]'),('context','d')],'methodによる量の算出とその校正が、検査対象claimの成立又はその同値な再表現を算出前提に用いないという手続き上の独立性。同じ方法名であるかでは判定せず、装置の校正にも答えの先取りを許さない。他の全物理法則からの独立性、誤差源の統計的独立性、実行済みや正確性は含めない。具体的な量・装置・取得・算出値は合成側で指定する。'),
 'eis37':([('observer','a'),('claim','i[e]'),('left',R),('right',R),('agrees','c'),('context','d')],'observerが同じcontextでclaimを実験的に調べるため、同じ尺度で比較すべき二量left/rightの一致を調べ、agreesという判定を得る実際の比較操作。二量がどこから得られたか、対象・単位の対応、独立性、判定の数値的正しさは合成側で要求する。単に二数が等しいという事実、未実行の検証計画、普遍法則の証明や実験の成功と同一視しない。'),
 'eis4a':(COUPLING,'observerがmethod/instrumentを使ってtargetの指定event・frame・quantity・unitの信号signalをrecordへ取得する操作に、同じ領域のelectricfieldとmagneticfieldの時間変化を物理的に用いる対応。二場と粒子又は検出系との結合が、時刻情報を取得信号へ反映する測定過程の一部となる。場が付近に存在するだけ、無関係な発振器の表示又は任意の数値関数では成立しない。lower/upperは同じ時間単位の使用区間。x,y,zはその操作で時間変化を利用する局所部位の同じ長さ単位の座標であり、別の場所の速い変動を流用しない。具体的な周期・速さ・校正と独立性は外側に合成し、特定の回路、粒子飛行距離、偏向比の正しさをこの関係へ埋め込まない。'),
 'eis4b':([('method','a'),('frame','a'),('timeunit','a'),('threshold',R),('context','d')],'同じmethodの時間情報を識別する測定配置・応答の時間尺度を背景に、「速い振動」と呼ぶ周期の上限thresholdを同じframe/timeunitで定める文脈上の比較基準。採用する場の周期から逆算して都合よく選ぶ値ではなく、対象となる操作と時間分解の条件に基づく基準である。普遍的な数値境界、単なる非零の振動数、校正の成功又は電磁波の放射を意味しない。'),
}
REFERENCES={
 'eis4c':'u0268全文、直前の比を実験で調べられるという主張と理由の箇所。',
 'eis4d':'u0268のda以下、同じ電子の速度を独立に直接測定できるという理由の箇所。',
 'eis4e':'u0268のz.B.以下、高速に振動する電場と磁場を用いる測定の挿入例示。',
}
MEANINGS={
 'erm':'対象・系・出来事の実速さを指定速度単位の量へ結ぶ。校正された実履歴の三つの座標時刻微分と非負ノルムeprを使い、速度単位の尺度U T=Lを共有する。場による偏向比を速さそのものの定義へ用いない。',
 'ern':'正の長さ時間尺度と速度単位の次元(1,0,−1)を、U T=Lという数値尺度の条件へ結ぶ。',
 'ero':'同じ電子・系・実速さについて、理論が許す測定状況のermをeqvの校正・取得へ結ぶ。方法と校正が比ercを前提にしないこと、同じ観測者がその記録を同じ評価段階で利用できることを要求する。',
 'erp':'偏向側の測定・計算eq4と同じ運動条件の独立直接測定eroを、同じ観測者・評価段階・速度尺度へ共有し、復元値と直接値の比較操作と正しい真偽判定を結ぶ。一致を前提にせず、実験で検査できることと実験が理論を支持することを分ける。',
 'erq':'同じ背景でerpの全測定・算術・直接法・比較判定が一つの可能過程として存在すること。実験済み又は判定が真であることを意味しない。',
 'err':'同じ背景についてeroの直接測定が可能であること。偏向側の測定記録の存在や、比較結果の一致は条件に入れない。',
 'ers':'同じ連続な実数値の周期波形について最小正周期を要求し、使用区間内の一周期内に中心の上下を取る時刻を持たせる。定数場、整数倍周期、一方の極値だけ、全時間の実際の使用と区別する。',
 'ert':'同じ使用区間の同じ空間点で、実電場y成分と実磁場z成分がそれぞれ指定波形に一致し、その四位置が物理場の領域内にあるという点条件。場の二成分を取り違えず、他の成分を無条件に零とはしない。',
 'eru':'同じ直接測定eroの装置・信号・記録で物理的二場を用い、両波形の周期・上下変動・連続性・全使用時刻の実場対応、同じ文脈の速さ基準を満たす例。放射波や平面波、同一周波数、特定回路の設計までは補わない。',
 'erv':'同じ背景についてeruの振動場を用いる直接測定が一つの可能過程として存在する。一つの例であり、直接法の全てをこの装置へ限定しない。',
 'erw':'同じ現在の電子・K・速さ・質量・電荷・整合単位と理論を固定し、erqによる偏向比の実験的検査の可能性を述べる閉じた内容。',
 'erx':'同じ現在の背景で、偏向比を算出前提にしない直接速度測定errの可能性を述べる内容。',
 'ery':'同じ現在の背景で、速く振動する電場と磁場を用いる直接測定ervの可能性を述べる例示内容。',
 'erz':'u0268のDiese Beziehungを直前の同じ比ercへ戻し、比較の可能性・直接測定という理由・auchによる追加・z.B.の挿入例示を同じ著者と論説へ結ぶ。',
 'er2':'u0268全文のメッセージ。','er3':'u0268を同じ著者・論説へ帰属し、比の表示u0267の後に置く。',
}
LIMITS=[
 '原刊920頁u0268全文を扱う。直前のAm/Ae=v/Vを実験で調べること、同じ電子の速度を直接にも測れるという理由、速く振動する電場と磁場による一例を省略しない。u0265の列挙導入は別途残る。',
 '直接測定は実三速度の非負ノルムという同じ量を、校正と物理的な取得から得ることであり、検査対象の比を算出又は校正の前提にしない。全物理理論から独立した裸の観察とは読まない。',
 '同じ現在の電子・K・速さ・単位を固定し、別の測定状況を許すが、同じ可能過程で同じ観測者が記録を利用できる条件を保つ。電気側・磁気側・直接側の数値を無関係な電子や異なる速度から寄せ集めない。',
 '理想的な量尺度における数値の一致を比較する読み。現実の有限精度の実験を実施済み又は誤差零とせず、比較可能性から支持・普遍的証明・正しい比を自動認定しない。旧草案の任意の誤差区間の重なりへ縮めない。',
 '振動は連続で非定数の周期的な上下変動として読む。測定に使う局所区間で実二場へ対応し、数学的な波形の全周期性と現実の全時刻の場を区別する。電場y成分と磁場z成分という標準配置を一例の具体化として採り、全ての方法へ強制しない。',
 'raschは測定配置の時間情報・応答尺度に基づく文脈上の周期閾値との比較とする。二場を同じ周波数・位相・振幅・正弦又は平面放射波へ限定せず、使用による時刻情報の物理的な信号への結合を要求する。原文が特定装置の回路又は飛行距離を記したとはしない。',
 '本文434主張・旧判断・意味・証拠を保持する。検査の数値例、各束縛位置の有限診断、著者の理由提示は、全実数・物理的実現又は原文同義性の自動証明ではない。',
]

def direct_values(prefix=''):
    return [v(prefix+n) if n in dict(DETAIL) else v(n) for n,t in DIRECT]
def acquisition():
    return dict(observer=v('observer'),method=v('method'),instrument=v('instrument'),record=v('record'),target=v('matter'),quantity='r[p erm]',frame=v('frame'),event=v('event'),unit=v('speedunit'),signal=v('signal'),context=v('scene'))
def definitions():
    text=''.join('r '+n+'['+' '.join(t for n,t in fs)+'] c.\n' for n,(fs,m) in PRIMITIVES.items())+''.join('r '+n+'[] a.\n' for n in REFERENCES)
    zero=k('bb',rat(0));ctx=v('context');speed=v('speed')
    unit=both(k('ejwb',v('speedunit'),rat(1),rat(0),rat(-1),v('speedscale'),ctx),k('aa',rat(0),v('lengthscale')),k('aa',rat(0),v('timescale')),op('e',k('ad',v('speedscale'),v('timescale')),v('lengthscale')))
    # A first-derivative quantity; acceleration is not needed by the direct method.
    ws=[(n,t) for n,t in MOTION if n not in ('matter','frame','event','speed','context')]+[(n,'b') for n in ('lengthscale','timescale','speedscale')]
    vals={n:v(n) for n,t in MOTION}|dict(matter=v('target'),speed=v('value'))
    quantityunit=unit.replace(v('speedunit'),v('unit'))
    text+=define('erm',QUANTITY,quantified('g',ws,both(k('epr',*[vals[n] for n,t in MOTION]),quantityunit,k('ejwb',v('lengthunit'),rat(1),rat(0),rat(0),v('lengthscale'),ctx),k('ejwb',v('timeunit'),rat(0),rat(0),rat(1),v('timescale'),ctx))))
    text+=define('ern',SPEED_UNITS,unit)
    av=acquisition();rv=av|{n:v(n) for n in ('range','calibration')}|dict(value=speed)
    text+=define('ero',DIRECT,both(k('eisoe',v('view'),ctx,v('scene')),k('eisoe',v('view'),ctx,v('assessment')),k('ern',v('lengthscale'),v('timescale'),v('speedunit'),v('speedscale'),v('scene')),k('erm',v('matter'),v('frame'),v('event'),v('speedunit'),speed,v('scene')),k('eqv',*[rv[n] for n,t in READOUT]),k('eis36',v('method'),quote('erc'),v('scene')),k('eis3u',v('observer'),v('record'),v('scene'),v('assessment'))))
    text+=define('erp',COMPARED,both(k('eq4',*args(MEASUREMENT)),k('ero',*direct_values('direct')),k('eis37',v('observer'),quote('erc'),v('recovered'),speed,v('agrees'),v('assessment')),op('z',v('agrees'),k('sca',v('recovered'),speed))))
    for name,fields,target in [('erq',COMPARED,'erp'),('err',DIRECT,'ero')]:text+=define(name,BACKGROUND,quantified('g',[(n,t) for n,t in fields if n not in dict(BACKGROUND)],k(target,*args(fields))))
    whole='i[time '+R+']['+k('ba',v('time'))+']'
    text+=define('ers',OSCILLATION,both(*(k('ba',v(n)) for n,t in OSCILLATION if t==R),k('ekc2',v('profile'),v('profile'),v('period')),k('lf',whole,v('profile')),k('bc',k('bd',v('lower'),v('period')),v('upper')),k('lg',v('lower'),k('bd',v('lower'),v('period')),v('positive')),k('lg',v('lower'),k('bd',v('lower'),v('period')),v('negative')),k('bg',v('center'),app(v('profile'),v('positive'))),k('bg',app(v('profile'),v('negative')),v('center'))))
    coords=[v(n) for n in ('x','y','z','time')]
    point=point_expression(coords)
    text+=define('ert',EXAMPLE+[('time',R)],both(k('ejsj',point,v('region')),*(k('sca',app(app(v(pre+'field'),k(axis)),*coords),app(v(pre+'profile'),v('time'))) for pre,axis in [('electric',ROLES[1]),('magnetic',ROLES[2])])) )
    fieldvals={n:v(n) for n,t in FIELDS}|dict(context=v('scene'))
    coupling=av|fieldvals|{n:v(n) for n in ('lower','upper','x','y','z')}
    oscillations=[k('ers',*[v(n) if n in ('lower','upper') else v(pre+n) for n,t in OSCILLATION]) for pre in ('electric','magnetic')]
    inside=both(k('ba',v('time')),k('lg',v('lower'),v('upper'),v('time')))
    text+=define('eru',EXAMPLE,both(k('ero',*args(DIRECT)),k('ejsn',*[fieldvals[n] for n,t in FIELDS]),*(k('ba',v(n)) for n in ('x','y','z','lower','upper','threshold')),k('bg',v('lower'),v('upper')),k('bg',zero,v('threshold')),k('eis4b',v('method'),v('frame'),v('timeunit'),v('threshold'),v('scene')),*oscillations,*(k('bg',v(pre+'period'),v('threshold')) for pre in ('electric','magnetic')),q('f','time',R,op('y',inside,k('ert',*args(EXAMPLE),v('time')))),k('eis4a',*[coupling[n] for n,t in COUPLING])) )
    text+=define('erv',BACKGROUND,quantified('g',[(n,t) for n,t in EXAMPLE if n not in dict(BACKGROUND)],k('eru',*args(EXAMPLE))))
    p=v('point');theory=k('eiscv',k('eis3k'),k('eirf'),quote('eigj'),p)
    actual=current(BACKGROUND,speed=k('eisxt'))
    for name,target in [('erw','erq'),('erx','err'),('ery','erv')]:text+=content(name,both(theory,q('g','chargescale','b',both(k('eq6',v('chargescale'),p),k('s45',k('tc'),k('eisxt')),k('bc',zero,k('eisxt')),k(target,*actual)))))
    who=k('rd');paper=k('eirf');section=k('eisxg');node=k('eis4c');reason=k('eis4d');example=k('eis4e')
    text+=content('erz',both(k('eiswm',node,who,k('eis32'),quote('erc'),paper,p),k('uh',node,who,quote('erw'),section,p),k('uh',reason,who,quote('erx'),section,p),k('zc',node,who,quote('erx'),quote('erw'),section,p),k('eisij',reason,who,quote('eq7'),quote('erx'),paper,p),k('eir5',example,who,reason,quote('ery'),p),k('eisa5',example,who,quote('erx'),quote('ery'),p),k('uh',example,who,quote('ery'),section,p),k('ue',node,reason,p)))
    text+='d er2[] f[j s[k erz[]]].\n';text+=define('er3',[],both(k('eir3',node,who,paper,quote('er2'),k('ri')),k('ue',k('eis32'),node,k('ri'))))
    return text

@lru_cache(None)
def build():
    old=parse(read(PARENT));assert len(old['statements'])==434
    assert not(set(MEANINGS)|set(PRIMITIVES)|set(REFERENCES))&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='er3',arguments=[]))]
    added=doc['declarations'][len(old['declarations']):]
    prim={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,t in PRIMITIVES[d['name']][0]] if d['name'] in PRIMITIVES else [],meaning_ja=PRIMITIVES[d['name']][1] if d['name'] in PRIMITIVES else REFERENCES[d['name']]) for d in added if d['kind']=='primitive'}
    basis=dict(status='independent_direct_speed_comparison_and_oscillating_field_example',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=prim,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[434]).document
    ann=json.loads(read(PARENT_ANNOTATIONS));ann.update(document=FULL,document_sha256=digest(body.encode()))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
