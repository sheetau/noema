"""Bind energy-flow models and hypothetical approach to the same radiation."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_radiative_intensity import ROOT,read,FLUX
from scripts.compose_doppler_specialization import EXTENDED
from scripts.compose_observed_amplitude import SETTING as AMPLITUDE
from scripts.compose_wave_cycle_frequency import HARMONIC,TIMEWAVE
from scripts.compose_wave_transform_application import transformed
from scripts.compose_field_equations import FIELD,REGION,TAU
from scripts.compose_material_relative_frame import define,args
from scripts.compose_relativity_conjecture import content,evaluate
from scripts.compose_two_postulates import quote
from scripts.compose_doppler_infinity import GRAPH,quantified
from scripts.compose_limits import R,F,v,call as k,app,op,both,lam

PARENT='examples/v014/einstein-radiative-intensity.noema';PARENT_BASIS='data/radiative-intensity-basis-v1.json'
FULL='examples/v014/einstein-observed-intensity.noema';CORE='examples/v014/observed-intensity-core.noema'
BASIS='data/observed-intensity-basis-v1.json';ANNOTATIONS='data/observed-intensity-identifiers-v1.json';INDEX=383
COEFFICIENT=[(n,'a') for n in ('frame','lengthunit','timeunit','forceunit','electricunit','magneticunit','energyunit')]+[('coefficient',R),('context','d')]
FLOW=[(n,'a') for n in ('wave','process','frame','lengthunit','timeunit','energyunit')]+[('region',REGION),('flux',FIELD),('scope','a'),('context','d')]
MODEL=[(n,'a') for n in ('wave','process','frame','lengthunit','timeunit','forceunit','electricunit','magneticunit','energyunit','scope')]+[('context','d'),('coefficient',R),('sine',F),('phase',TAU)]+[(n,R) for n in ('ex','ey','ez','hx','hy','hz')]+[('region',REGION)]
VECTOR=[('coefficient',R),('sine',F),('phase',TAU)]+[(n,R) for n in ('ex','ey','ez','hx','hy','hz')]
AVERAGE=FLUX+TIMEWAVE+[('intensity',R)]
SETTING=EXTENDED+[('amplitude',R),('newamplitude',R),('energyunit','a')]+[(n,R) for n in ('coefficient','incident','received')]
VARIABLES=[(n,t) for n,t in SETTING if n not in ('frame','light','scope','context')]
VARYING={'newamplitude','newperiod','newfrequency','obslower','obsupper','obsx','obsy','obsz','oldobslower','oldobsupper','oldobsx','oldobsy','oldobsz','oldoffset','newoffset'}
BACKGROUND=[('view','a')]+[(n,t) for n,t in SETTING if n not in VARYING|{'speed','received'}]
WITNESSES=[(n,t) for n,t in SETTING if n in VARYING]+[('alternative','d')]
BACKGROUND_VARIABLES=[(n,t) for n,t in BACKGROUND if n not in ('frame','light','scope','context')]
TRUE=op('e','n p a b','n p a b');FALSE=op('u',TRUE)
PRIMITIVES={
 'eiste':(COEFFICIENT,'同じframeの校正された直交空間軸と指定単位について、電気・磁気の場成分の外積を、energyunit/(timeunit*lengthunit²)で表す電磁エネルギー流へ換算する正の係数がcoefficientであるという単位と物理的量の対応。エネルギーは場から物質への仕事及び他形態との交換収支で扱い、energyunitはforceunitとその方向の変位の積の仕事基準に整合する。外積の数式、波や局所モデルへの適用、平均、速度依存及び発散は別に合成する。任意の無次元定数をエネルギーと呼ぶだけの規約、単位系を混ぜた数値の同一視、測定実施の認定ではない。'),
 'eistf':(FLOW,'同じwaveのprocessについて、同じframe・長さ時間及びエネルギー単位・regionで、fluxが電磁エネルギーの面積当たり時間当たりの移転を表すベクトル場モデルとしてscopeの考察に採用されるという物理的対応。成分は各正の空間軸に垂直な面をその正方向へ横切る符号付きの流である。数値関数だけからこの役割を認めず、場の作用と仕事・エネルギー交換の説明へ結ぶ。理想化モデルであり、実際の流の無限精度の測定記録又はモデルの全領域外への物理的外挿ではない。既存の場の誤差上限だけから十分性を自動推論しない。具体的な成分・方向・平均・観測者・境界をこの関係へ隠さない。'),
 'eistg':([], 'u0201のEs folgtからerscheinen müßteまで、光速で接近する観測者への無限強度を展開済みの式からの仮定的帰結として述べる箇所。'),
}
MEANINGS={
 'ekjy':'同じ実数時間関数profileを同じtimeで二度評価した値の積を返す二乗時間関数。',
 'ekjz':'同じ正弦・余弦・pi・一周期・位相率・位相原点・周期数のekc7と、0から同じperiodまでの正弦時間関数の二乗積分=period/2を結ぶ。周期平均の解析条件を明示し、任意波形や有限観測区間の平均を1/2と認定しない。',
 'ekka':'同じ係数、正弦、四座標位相、六係数から、各空間軸のκ(E×H)sin²Φというベクトル場を構成する。三つの向きにekjfを適用し、非空間役割の拡張成分は零。',
 'ekkb':'同じ波・過程・系・単位・範囲・状況について正の換算係数eisteを保持し、同じekkaのベクトル場をeistfのエネルギー流モデルへ結ぶ。係数、単位、二場又は位相を枝ごとに選び直さない。',
 'ekkc':'同じ一周期のekjzに、同じ方向・六係数・位相率・原点・周期・強度の積分平均ekjhを結ぶ。積分量はperiod*intensityであり、時間周期の異なる二系へ同じ積分値を流用しない。',
 'ekkd':'同じ66設定の波・放射源・観測者・K/k・局所近似・校正・旧新振幅を保持し、旧角πと旧法線−xの正面接近、両系の横波、同じエネルギー単位・換算係数・流モデル、各系の周期平均を結ぶ。旧系の基準静止点での正のincidentと、新系の同じ受信経路のreceivedを区別する。',
 'ekke':'同じ66設定のekkdと、先行表示の同じ電気側二乗振幅比ekijを合わせた、展開済みの式に適合する有限速度の設定。既存ekibの一般適用条件は書き換えない。',
 'ekkf':'同じviewと基準contextから許容されるalternativeの下で、同じ背景・speed・receivedをekkeへ結ぶ一点条件。物理的な設定のcontextだけをalternativeへ一貫して渡し、異なる速度を同じ現実状況の同時運動としない。',
 'ekkg':'同じ背景を固定したspeed/receivedの関係。速度で変わる周期・新振幅・受信軌跡・位相原点と代替状況を同じ16証人として存在量化する。入射場、源・波・観測者、単位、旧振幅、入射平均流を選び直さない。',
 'ekkh':'同じ背景を固定してekkgを入力speed・出力receivedの二実数関係として返す。',
 'ekki':'同じ背景のekkgに有限速度と有限受信強度の一組があるという非空条件。',
 'ekkj':'同じ論説の理論的見解と同じ背景の非空な有限設定ごとに、同じ受信強度の関係がVへの左側発散ekjtを満たすという内容。näherteとmüßteを理論内の代替設定の非到達境界についての帰結と読む。現実の光速観測者や実数の無限強度を要求しない。',
 'ekkk':'同じ66設定の残る62全称役割について、ekkdなら先行の同じ二乗振幅比ekijと述べる。新しい強度と接近の明示読解を伴う適用形であり、別の波の一般式へ参照を切り替えない。',
 'ekkl':'先行の同じ波の変換式とパラメータ指定ekco、一般二乗振幅比ekikを同じ評価点で合わせた、展開済みの式への参照内容。',
 'ekkm':'同じ強度と接近を明示したekkkとして先行振幅式を説明し、同じ展開済みの式ekklから境界内容ekkjが従うという著者の提示と仮定範囲内の主張を結ぶ。物理的な証明成功を帰属時に要求しない。',
 'ekkn':'u0201の強度の境界帰結と式からの提示ekkmを述べるメッセージ。',
 'ekko':'u0201を同じ著者・論説へ帰属し、直前の二乗振幅の特殊表示に続ける。',
}
LIMITS=[
 'u0201のM0348=Vを保持し、光速で接近する仮定と無限に強く現れる帰結を、同じ理論の有限速度0<v<Vの代替設定がVへ近づく境界として読む。光速での観測者静止系を実在させたり、既存の有限変換にv=Vを代入したりしない。これは採用する境界読解であり唯一の歴史的意図の確定ではない。',
 'intensivは同じ観測者の系で同じ波が運ぶエネルギーの単位横断面積・単位時間当たりの周期平均と読む。明るさの心理的感覚、装置の飽和、振幅の数値そのもの、総エネルギーとは区別する。エネルギーを仕事と交換収支、単位を力と変位の積へ結び、ベクトル流・方向・正弦二乗・周期積分を合成する。',
 '同じ非零の伝播する真空光の局所平面波という読みのため、当文の強度評価ではseajの横波とH=n×Eを明示する。先行の一般振幅の著者主張を横波だけへ書き換えず、その非横波反例も保持する。Maxwell方程式から横波を導く一般的な機械証明をこの意味判断の成功と混同しない。',
 '旧基準静止点の周期平均をincident、新系の同じ観測者に沿う局所位相の周期平均をreceivedとする。位相の周期平均には局所表現の数学的一周期を使い、有限の物理観測区間に一周期が収まることや実測を補わない。共通正弦の二乗平均1/2を積分条件として確認し、原点の違いと二系の周期の違いを保つ。',
 '同じ正の換算係数とエネルギー単位を二系の校正へ結び、波のエネルギー流モデルとしての採用を別の物理的対応にする。以前の周波数・方向・振幅に関する誤差十分性を、エネルギー流へ無断拡張しない。モデルを現実の厳密場や全空間全時間の実測へ置き換えない。',
 '正の+x速度で接近する配置は旧法線−x、旧実数角π。源の−R*n配置は+x側となり、同じ観測者の+x運動が接近になる。受信の新角φ′について前段に保存した結線角と印刷式の不整合を修正せず、ここで別のφ′を導入しない。',
 '同じ源・波・過程・観測者、旧場・旧振幅・入射平均流、系と単位及び局所領域を背景に固定する。各速度の補助周期・軌跡・位相原点・新振幅と理論内の代替状況は存在量化する。同時に一人が相反する速度で現実に運動するとはしない。候補はeisoeの理論全範囲であり、大きい出力だけを選ばない。',
 '正のincidentを要求する。零放射に無限強度を結論する読みは採らない。非空の有限設定を前件に、境界へ任意に近い非空な設定と近傍内の全出力の上限超過を共に主張する。実数の無限値や、一つの大きい標本を結論にしない。',
 'Es folgt aus den entwickelten Gleichungenは先行変換表示・一般振幅比への参照と著者の帰結提示で保持する。näherte/müßteは代替設定における境界への仮定的な帰結であり、現在の実験の報告、観測者への規範的命令、物理的真理又は引用の自動証明とはしない。',
]

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+('c' if fs else 'a')+'.\n' for n,(fs,_) in PRIMITIVES.items())
    zero=k('bb','n p a b');one=k('bb','n p b b');half=k('bb','n p b c');mul=lambda x,y:k('shv',x,y)
    positive=lambda x:both(k('ba',x),k('bg',zero,x))
    text+=define('ekjy',[('profile',F)],lam('time',R,mul(app(v('profile'),v('time')),app(v('profile'),v('time')))),F)
    timeprofile=k('ekc5',v('sine'),v('rate'),v('offset'));period=v('period')
    text+=define('ekjz',TIMEWAVE,both(k('ekc7',*args(TIMEWAVE)),k('sede',zero,period,k('ekjy',timeprofile),mul(period,half))))
    coords=[v(n) for n in ('x','y','z','time')];wave=app(v('sine'),app(v('phase'),*coords))
    amps=[v(n) for n in ('ex','ey','ez','hx','hy','hz')];basis=((one,zero,zero),(zero,one,zero),(zero,zero,one))
    vector=k('ekbe',*(mul(k('ekjf',v('coefficient'),*direction,*amps),mul(wave,wave)) for direction in basis))
    field='i[axis a][i['+' '.join(n+' '+R for n in ('x','y','z','time'))+']['+app(vector,v('axis'))+']]'
    text+=define('ekka',VECTOR,field,FIELD)
    physical={n:v(n) for n,t in MODEL};physical['flux']=k('ekka',*args(VECTOR))
    text+=define('ekkb',MODEL,both(positive(v('coefficient')),k('eiste',*args(COEFFICIENT)),k('eistf',*[physical[n] for n,t in FLOW])))
    text+=define('ekkc',AVERAGE,both(k('ekjz',*args(TIMEWAVE)),k('ekjh',*args(FLUX),timeprofile,zero,period,mul(period,v('intensity')),v('intensity'))))
    V,speed,coef=map(v,('light','speed','coefficient'));newamps,shifted,_,phase=transformed(speed)
    oldphase=k('ekbf',V,v('rate'),v('ax'),v('ay'),v('az'))
    oldregion=k('ekau',v('space'),v('lower'),v('upper'));newregion=k('eken',speed,v('space'),v('lower'),v('upper'),V)
    ampactual=[FALSE if n=='magneticside' else v(n) for n,t in AMPLITUDE]
    models=[]
    for frame,p,coefficients,region in ((v('frame'),oldphase,amps,oldregion),(k('zbm'),phase,newamps,newregion)):
        replacements=dict(frame=frame,phase=p,region=region,**dict(zip(('ex','ey','ez','hx','hy','hz'),coefficients)))
        models.append(k('ekkb',*[replacements.get(n,v(n)) for n,t in MODEL]))
    averages=[]
    for direction,coefficients,rate,offset,p,f,I in (([v(n) for n in ('ax','ay','az')],amps,v('rate'),zero,v('oldperiod'),v('frequency'),v('incident')),(shifted[1:],newamps,shifted[0],v('newoffset'),v('newperiod'),v('newfrequency'),v('received'))):
        averages.append(k('ekkc',coef,*direction,*coefficients,*args(HARMONIC),rate,offset,p,f,I))
    text+=define('ekkd',SETTING,both(k('eket',*args(EXTENDED)),k('ekev',V,speed),k('ekia',*ampactual),positive(v('incident')),k('ba',v('received')),k('bc',zero,v('received')),k('sca',v('angle'),v('pi')),k('sca',v('ax'),k('bf',zero,one)),k('sca',v('ay'),zero),k('sca',v('az'),zero),k('seaj',*[v(n) for n in ('ax','ay','az')],*amps),k('seaj',*shifted[1:],*newamps),*models,*averages))
    text+=define('ekke',SETTING,both(k('ekkd',*args(SETTING)),k('ekij',*ampactual)))
    point=BACKGROUND+[('speed',R),('received',R)]+WITNESSES
    actual=[v('alternative') if n=='context' else v(n) for n,t in SETTING]
    text+=define('ekkf',point,both(k('eisoe',v('view'),v('context'),v('alternative')),k('ekke',*actual)))
    text+=define('ekkg',BACKGROUND+[('speed',R),('received',R)],quantified('g',WITNESSES,k('ekkf',*args(point))))
    text+=define('ekkh',BACKGROUND,'i[speed '+R+' received '+R+']['+k('ekkg',*args(BACKGROUND),speed,v('received'))+']',GRAPH)
    text+=define('ekki',BACKGROUND,quantified('g',[('speed',R),('received',R)],k('ekkg',*args(BACKGROUND),speed,v('received'))))
    fixed={'frame':k('ra'),'light':k('tc'),'scope':k('eisrx'),'context':v('point')};bg=[fixed.get(n,v(n)) for n,t in BACKGROUND]
    theory=k('eiscv',v('view'),k('eirf'),quote('eigj'),v('point'))
    text+=content('ekkj',quantified('f',BACKGROUND_VARIABLES,op('y',both(theory,k('ekki',*bg)),k('ekjt',k('ekkh',*bg),k('tc')))))
    st=[fixed.get(n,v(n)) for n,t in SETTING];aa=[FALSE if n=='magneticside' else fixed.get(n,v(n)) for n,t in AMPLITUDE]
    text+=content('ekkk',quantified('f',VARIABLES,op('y',k('ekkd',*st),k('ekij',*aa))))
    text+=content('ekkl',both(evaluate('ekco'),evaluate('ekik')))
    p=v('point');node=k('eistg');author=k('rd');scope=k('eisrx')
    text+=content('ekkm',both(k('eissb',node,k('eiss6'),author,quote('ekik'),quote('ekkk'),scope,p),k('zc',node,author,quote('ekkl'),quote('ekkj'),scope,p),k('uh',node,author,quote('ekkj'),scope,p)))
    text+='d ekkn[] f[j s[k ekkm[]]].\n'
    text+=define('ekko',[],both(k('eir3',node,author,k('eirf'),quote('ekkn'),k('ri')),k('ue',k('eistd'),node,k('ri')),op('u',op('e',k('eistd'),node))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX
    assert not(set(PRIMITIVES)|set(MEANINGS))&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='ekko',arguments=[]))]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,t in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='same_radiation_energy_flow_and_hypothetical_light_speed_boundary',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[INDEX]).document
    ann=json.loads(read('data/radiative-intensity-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
