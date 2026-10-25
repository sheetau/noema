"""Connect the traversed potential drop to the same electron energy process."""
from scripts.compose_direct_speed_experiment import *
from scripts import compose_electron_kinetic_work as energy

PARENT=FULL;PARENT_BASIS=BASIS;PARENT_ANNOTATIONS=ANNOTATIONS
FULL='examples/v014/einstein-traversed-potential.noema';CORE='examples/v014/traversed-potential-core.noema'
BASIS='data/traversed-potential-basis-v1.json';ANNOTATIONS='data/traversed-potential-identifiers-v1.json'
EXTRA=[('potential',F),('left',R),('right',R),('drop',R),('potentialunit','a'),('potentialscale','b'),('chargescale','b'),('chargerecord','a'),('speedunit','a'),('speedscale','b')]
SETTING=energy.SETTING+EXTRA
ALL=energy.ALL+EXTRA
NUMERIC=[(n,R) for n in ('light','speed','mass','charge','drop')]
PRIMITIVES={
 'eis4f':([(n,'a') for n in ('frame','energyunit','chargeunit','potentialunit')]+[('context','d')],'指定系のpotentialunitを、同じenergyunitの仕事を同じchargeunitの符号付き電荷で割る電位の差の物理的単位とする校正対応。単位電荷に対する仕事の比較を意味し、単位名だけの一致ではない。尺度の正性と積の整合、実際の場・軌道・電荷・電位関数・値は合成側で要求する。特定のエネルギー公式、電荷の正号、実測、全空間での電位の存在を含めない。'),
}
NEW_VALUES={
 'eis4g':(F,'同じ軸上の静電場に対する電位関数。値は同じ電荷当たりの仕事単位で、加法定数を固定しない。'),
 'eis4h':(R,'原点・終位置と全実軌道を含む軸上区間の左端。'),
 'eis4i':(R,'同じ電位区間の右端。'),
 'eis4j':(R,'同じ静止からの過程で通過した符号付き電位降下P。'),
 'eis4k':('a','同じ仕事と符号付き電荷に校正された電位単位。'),
 'eis4l':('b','同じ電位単位の正の尺度。'),
 'eis4m':('b','同じ電荷単位の正の尺度。'),
 'eis4n':('a','同じ電子の終端出来事での電荷記録。'),
 'eis4o':('a','同じ長さ時間校正に対応する速度単位。'),
 'eis4p':('b','同じ速度単位の正の尺度。'),
}
FIXED=energy.FIXED|dict(zip((n for n,t in EXTRA),NEW_VALUES))|{'speed':'eisxt'}
REFERENCES={'eis4q':'u0269、列挙の第二項で運動エネルギーの導出から電位差と獲得速度の関係を導く箇所。','eis4r':'u0270、M0438の電位差・場の積分・速度式の表示。','eis4s':'M0438で同じ通過電位差を呼ぶ記号P。'}
MEANINGS={
 'er4':'同じ終端電子の非零電荷の校正を電位の仕事/電荷単位へ結び、正の尺度でPunit Qunit=Wunit、Uunit Tunit=Lunitを保つ。既存eorの機械単位と共用する。',
 'er5':'指定電位区間の一点xでは、同じ実電場の領域に開始時刻の(x,0,0,t)が属する。時間独立性eosと合わせ、単なる任意の数値プロファイルで電位を代用しない。',
 'er6':'零と同じ終位置、全実軌道のxを含む閉区間上で、電位差を全二点の向き付き場積分seuwへ結ぶ。その区間の全点を同じ実電場に対応させる。往復運動も排除せず、端点だけで内部の誤った電位を隠さない。',
 'er7':'同じ電子・系・実軌道・初速零・実静電場・符号付き電荷・低速質量をeouへ結び、電位単位・全軌道上の電位・仕事=電荷×降下を同じ取り出し量へ接続する。運動エネルギーの速度式はここに仮定しない。',
 'esa':'正の光速度・低速質量、非零の符号付き電荷、非負で光速未満の獲得速度について、seurの関係と印刷されたμ/ε V²(1/sqrt(1−(v/V)²)−1)を同じPへ結ぶ。絶対電荷又はμ=1へ替えず、二重の逆数と平方根を保持する。',
 'esb':'同じ現在の過程にer7を適用した、実際に通過した電位差と場の積分・仕事の内容。',
 'esc':'同じ現在のV・v・μ・ε・Pのesaによる速度関係。',
 'esd':'M0438のP=積分Xdx=速度式の全等号を、同じ電位と電子の過程で接続した内容。',
 'ese':'既存ep7の同じ運動エネルギー導出の前提と右端のエネルギー式に、通過電位の仕事/電荷対応esbを加えた導出の読解。印刷M0427の中間項へμを補正せず、そこを物理前提にも使わない。',
 'esf':'u0269の第二項という位置、同じ電子の運動エネルギーの導出への照応、folgtとmußの推論上の主張、直後表示への接続。',
 'esg':'u0269の全文メッセージ。','esh':'同じ電子の同じ過程で通過した電位差というPの量内容。表示の数値式をその量の意味へ先取りしない。',
 'esi':'u0269を同じ著者・論説へ帰属し、直接速度測定の記述の後に置く。',
 'esj':'u0270のPの呼称と、同じ過程の両等号の表示及び著者主張。',
 'esk':'u0270の全文メッセージ。','esl':'u0270を同じ著者・論説へ帰属し、第二項の導入に続ける。',
}
LIMITS=[
 '原刊920–921頁u0269–u0270を、前段の静止・原点からの軸上静電加速と同じ電子・過程の第二項として読む。上下端が印刷されない積分はその両端の定積分。任意の初速や時間変動する場への無条件拡張ではない。',
 'Pは初期電位から終端電位を引く符号付き降下。負電荷の加速ではPも負であり、電荷の絶対値を使わない。電位の加法定数は自由。閉区間は全実軌道を含み、単調運動又は両端間だけの領域へ限定しない。',
 '同じ領域内の静的な軸方向場を採り、電位関数の全二点差を同じ場の向き付き積分へ結ぶ。三次元全空間の経路独立性、任意の静電場の電位存在定理、微積分基本定理の一般的機械証明はここで主張しない。',
 '同じ仕事・電荷・長さ時間の校正と正の尺度を要求する。数値だけのP、別の電子の電荷・質量・軌道、別単位の速度の混入を認めない。運動エネルギーと仕事の等置は前段の初期零・無放射・閉収支という明示した理想化の下にある。',
 'folgtとmußはその導出から関係が成立すべきだという著者の推論上の必要性。規範的義務、実験済み又は無条件の物理的真理としない。先行M0427のμを欠く中間積分は旧本文に保存し、この正しい別の印刷式で遡って訂正しない。',
 '旧435主張・定義・判断・証拠を保持する。有限検査と多項式モデル、著者の理由提示を全実数上の証明又は原文との同義性の自動認定へ置き換えない。列挙導入u0265と第三項以降は別途残る。',
]
def actual(fields,**replace):return [replace.get(n,v('point') if n=='context' else k(FIXED[n])) for n,t in fields]
def interval(x):return both(k('ba',x),k('bc',v('left'),x),k('bc',x,v('right')))
def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] c.\n' for n,(fs,_) in PRIMITIVES.items())+''.join('r '+n+'[] '+t+'.\n' for n,(t,_) in NEW_VALUES.items())+''.join('r '+n+'[] a.\n' for n in REFERENCES)
    zero=k('bb',rat(0));one=k('bb',rat(1));ctx=v('context');x=v('x');t=v('moment')
    fields={n:v(n) for n,t in ALL}|dict(event=v('end'))
    units=both(k('ek3u',*[fields[n] for n,t in energy.CHARGE]),k('eis4f',*[v(n) for n in ('frame','energyunit','chargeunit','potentialunit','context')]),k('aa',rat(0),v('potentialscale')),k('aa',rat(0),v('chargescale')),op('e',k('ad',v('potentialscale'),v('chargescale')),v('energyscale')),k('ern',*[v(n) for n,t in SPEED_UNITS]))
    text+=define('er4',SETTING,units)
    text+=define('er5',SETTING+[('x',R)],op('y',interval(x),app(v('region'),x,zero,zero,coord(v('startpoint'),ROLES[3]))))
    potentialdomain='i[x '+R+']['+interval(x)+']'
    lower=coord(v('startpoint'),ROLES[3]);upper=coord(v('endpoint'),ROLES[3])
    timeinside=both(k('ba',t),k('sxs',lower,upper,t))
    text+=define('er6',SETTING,both(k('ba',v('left')),k('ba',v('right')),interval(zero),interval(v('finalposition')),k('seuw',potentialdomain,v('potential'),v('profile'),zero,v('finalposition'),v('drop')),q('f','x',R,k('er5',*args(SETTING),x)),q('f','moment',R,op('y',timeinside,interval(coord(app(v('curve'),t),ROLES[0]))))))
    text+=define('er7',ALL,both(k('eou',*args(energy.SETTING)),k('er4',*args(SETTING)),k('er6',*args(SETTING)),k('seut',zero,v('finalposition'),v('profile'),v('drop'),v('charge'),v('withdrawn'))))
    V=v('light');speed=v('speed');mass=v('mass');charge=v('charge');drop=v('drop');ratio=k('shv',speed,k('sjd',V));radicand=k('bf',one,k('shv',ratio,ratio))
    rhs=k('shv',k('shv',mass,k('sjd',charge)),k('shv',k('shv',V,V),k('bf',k('sjd',k('cj',radicand)),one)))
    text+=define('esa',NUMERIC,both(k('seur',V,speed,k('soy',V,speed),mass,charge,drop),k('sca',drop,rhs)))
    ev=lambda n:op('t',k(n),v('point'))
    text+=content('esb',k('er7',*actual(ALL)))
    text+=content('esc',k('esa',*actual(NUMERIC,speed=k('eisxt'))))
    text+=content('esd',both(ev('esb'),ev('esc')))
    text+=content('ese',both(ev('ep7'),ev('esb')))
    p=v('point');who=k('rd');paper=k('eirf');section=k('eisxg');node=k('eis4q');display=k('eis4r')
    text+=content('esf',both(k('eislk',node,k('eis3w'),rat(2),paper,p),k('eiswm',node,who,k('eis3h'),quote('ep7'),paper,p),k('zc',node,who,quote('ese'),quote('esd'),section,p),k('uh',node,who,quote('esd'),section,p),k('uf',who,node,display,p)))
    text+='d esg[] f[j s[k esf[]]].\n'
    text+=define('esh',[('matter','a'),('value',R),('context','d')],both(op('e',v('matter'),k('eisxh')),k('er7',*actual(ALL,drop=v('value'),context=ctx))))
    text+=define('esi',[],both(k('eir3',node,who,paper,quote('esg'),k('ri')),k('ue',k('eis4c'),node,k('ri'))))
    text+=content('esj',both(k('eisox',display,quote('esd'),p),k('uh',display,who,quote('esd'),section,p),k('eisnw',display,who,k('eis4s'),'r[p esh]',paper,p)))
    text+='d esk[] f[j s[k esj[]]].\n'
    text+=define('esl',[],both(k('eir3',display,who,paper,quote('esk'),k('ri')),k('ue',node,display,k('ri'))))
    return text

@lru_cache(None)
def build():
    old=parse(read(PARENT));assert len(old['statements'])==435
    assert not(set(MEANINGS)|set(PRIMITIVES)|set(REFERENCES)|set(NEW_VALUES))&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol=n,arguments=[])) for n in ('esi','esl')]
    added=doc['declarations'][len(old['declarations']):]
    prim={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,t in PRIMITIVES[d['name']][0]] if d['name'] in PRIMITIVES else [],meaning_ja=PRIMITIVES[d['name']][1] if d['name'] in PRIMITIVES else NEW_VALUES[d['name']][1] if d['name'] in NEW_VALUES else REFERENCES[d['name']]) for d in added if d['kind']=='primitive'}
    basis=dict(status='traversed_potential_and_acquired_speed_connected',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=prim,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[435,436]).document
    ann=json.loads(read(PARENT_ANNOTATIONS));ann.update(document=FULL,document_sha256=digest(body.encode()))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
