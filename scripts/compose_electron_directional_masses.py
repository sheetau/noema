"""Integrate the mass inquiry, force example and conditional two-mass result."""
from scripts.compose_electron_force_measurement import *

PARENT='examples/v014/einstein-electron-force-measurement.noema'
PARENT_BASIS='data/electron-force-measurement-basis-v1.json'
FULL='examples/v014/einstein-electron-directional-masses.noema'
CORE='examples/v014/electron-directional-masses-core.noema'
BASIS='data/electron-directional-masses-basis-v1.json'
ANNOTATIONS='data/electron-directional-masses-identifiers-v1.json'
INDICES=(423,424,425)
ALL=CONVENTION+COEFFICIENTS
EXTRA_MASS=[('forcerecord','a'),('force',POINT),('accelerationunit','a'),('accelerationscale','b')]
code=lambda fields,result:'i[h['+' '.join(t for n,t in fields)+'] '+result+']'
PRIMITIVES={
 'eisyu':([('node','a'),('author','a'),('anchor','a'),('prior','i[e]'),('condition',code(CONVENTION,'c')),('question',code(CONVENTION,'g['+R+' '+R+']')),('scope','a'),('context','d')], '同じ先行anchorのpriorを受け、authorがnodeでconditionの下のquestionを問う提示。同じ46設定を条件と質問へ同順で渡し、二実数の候補の外側で固定する一般的な型付き質問族の提示である。具体的対象・数量・条件は引用した規則で合成する。解の存在・一意性・既知性、条件の現実成立、引用の実行を要求しない。'),
 'eisyv':([('node','a'),('author','a'),('scope','a'),('context','d')], 'authorがnodeで扱う問いの立て方を、scopeの主題について当該の議論の背景で通例となっている考察の仕方に沿わせるという論述上の位置付け。全ての人の同意、慣例の正しさ、問いの答え又は現代でも同じ慣例が続くことを主張しない。具体的な問いや物理的定義は別に結ぶ。'),
 'eisyw':([('node','a'),('author','a'),('designation','a'),('referent','a'),('document','a'),('context','d')], 'authorがnodeで、既に限定されたreferentをdocument内ではdesignationという呼称で、その限定を毎回付けずに端的に呼ぶという命名規約の採用。指示対象の限定を解除せず、一般の同名対象へ拡張しない。採用の条件、対象の意味、実際の成立は外側の合成条件に置く。'),
 'eisyx':([('designation','a'),('axes','j[a]'),('setting',code(ALL,'c')),('selector',code(ALL,R)),('document','a'),('scope','a'),('context','d')], '同じdocument・scopeでdesignationという数量呼称を、閉じたsettingを満たす同じ48役割からselectorが取る実数へ対応させ、その係数を適用する成分役割を順序付きaxesで指定する。物理対象・系・単位・運動と各軸の幾何的関係・係数の適用式はsettingに合成する。語の綴りだけで量の意味を与えず、別設定の値へ交換しない。値の存在、引用規則の真理や測定済みを含意しない。'),
}
REFERENCES={
 'eisyy':'u0252第一文の、通常の考え方に沿って動く電子の縦横質量を問う箇所。',
 'eisyz':'u0254冒頭のund bemerken zunächst以下の、同じ瞬間共動系の機械力三成分をまず指摘する箇所。',
 'eisy2':'u0254の括弧内、この力を同じ系に静止するばね秤で例えば測り得るという挿入例示の箇所。',
 'eisy3':'u0254 Wenn wir nunからu0258までの、呼称と数値規約を採れば二質量を得る条件付き導出の箇所。',
 'eisy4':'u0255 Massenzahl × Beschleunigungszahl = Kraftzahlの表示箇所。',
 'eisy5':'u0257の縦質量の名称と分数表示の箇所。',
 'eisy6':'u0258の横質量の名称と分数表示の箇所。',
 'eisy7':'u0254のdie auf das Elektron wirkende Kraftという、同じ瞬間共動系での力を無修飾に呼ぶ呼称。',
 'eisza':'u0252とu0257のlongitudinale Masseという、選択した運動軸成分の質量係数の呼称。',
 'eiszb':'u0252とu0258のtransversale Masseという、運動軸に直交する二成分の共通質量係数の呼称。',
}
MEANINGS={
 'emh':'同じV=tcとv=eisxtの1−(v/V)²。適用域は先行のV>0、0≤v<V。',
 'emi':'emhの非負平方根cj。物理設定の亜光速条件で正となる分母で、負の平方根を採らない。',
 'emj':'同じCONVENTIONと二係数についてemfを保持し、縦=μ/(sqrt(1−(v/V)²))³と横=μ/(1−(v/V)²)を実数の積・逆数・平方根で明記する。',
 'emk':'同じ設定のforcerecordを著者が電子に働く力と端的に呼ぶ命名規約。物理的なkの限定はemcに保ち、Kの力へ読み替えない。',
 'eml':'同じ規約emc・呼称emk・実三成分の質量数値×加速度数値=力数値sephと全六実数の係数同定sepiを結ぶ、採用した二質量の条件。',
 'emm':'同じ採用条件emlなら、平方根を含む具体的な二質量emjであるという条件文。零加速度の一例からの同定に替えない。',
 'emn':'同じ全共動設定・力記録・二単位役割・二係数についてemmを述べる閉じた条件付き結論。',
 'emo':'同じ全設定でemcと呼称emkを採れば、実三成分に適用する具体的な二質量emjの組が存在するという閉じた結論。既知の値の存在は質問自体には入れず導出側で述べる。',
 'emp':'同じ全設定でemlとして採った縦係数を、μ/(sqrt(1−(v/V)²))³に結ぶ表示内容。',
 'emq':'同じ全設定でemlとして採った横係数を、μ/(1−(v/V)²)に結ぶ表示内容。',
 'emr':'同じemc規約とsepiの係数を採るなら、同じKの実三加速度とkの力三成分にsephの数値法則を保持するという内容。表示u0255を三成分に展開し、全ての独立三数値の積が等しいとはしない。',
 'ems':'同じ全emc設定について、そのforcerecordにemkの端的な呼称を採る内容。後の条件付き提示の前件に置き、無条件の一般命名を主張しない。',
 'emt':'端的な呼称emsと数値法則の保持emrを合わせる条件内容。kの力・Kの加速度・整合する単位は各emcで同じ設定に共有する。',
 'emu':'先行の同じ三行六等号eluと、今回採用する呼称・数値規約emtを結ぶ導出の前提内容。',
 'emv':'同じ設定の二係数候補emdから縦の値を取る射影。',
 'emw':'同じ設定の二係数候補emdから横の値を取る射影。',
 'emx':'縦の呼称を同じemdのx成分係数、横の呼称を同じemdのy,z共通係数へ結ぶ表記規約。Kでの速度(v,0,0)と直交校正軸をemcのek63が保つ。',
 'emy':'著者が先行(A)を受け、同じemc設定でemeの二係数を問う提示、通例の考え方に沿う位置付け、縦横の名称と本文順序を合わせる。',
 'emz':'縦横の質量を問う提示emyのメッセージ。',
 'em2':'同じ著者・論説へ問いを帰属し、前の(A)と後の書換え導入の間へ置く主張423。',
 'em3':'著者が六等号の後でまず同じkの力emaを指摘し、その同じ力に対するばね秤の可能測定embを括弧内の一例として補足する。',
 'em4':'力の三成分の指摘と、同じ系のばね秤の可能な例示を伝えるメッセージ。',
 'em5':'力の指摘と括弧内の例示を著者・論説へ帰属し、六等号の後へ置く主張424。',
 'em6':'呼称と数値法則を保持する条件の下で、先行六等号から二質量の結論emn/emoを得ると提示する。加速度をKで測る選択はemcへ保持し、数値法則の表示、二分数表示、名称、前方・後方の照応と順序を結ぶ。',
 'em7':'条件付きの規約採用と二質量表示em6のメッセージ。',
 'ena':'同じ著者・論説へ条件付き導出を帰属し、力の説明・括弧例示に続ける主張425。',
}
LIMITS=[
 '原刊918–919頁と固定u0252、u0254–u0258の全文を同じ一群で読む。u0252第二文とu0253の六等号は旧主張422を共有する。u0259以降の別定義・理論比較はここに含めない。',
 '問いの縦横質量は、直後に明示されるkの力とKの加速度の規約で求める二係数として遡って読む。問いの段階で答えの存在・既知性を主張しない。Wirは同じ著者の論述主体。通例は当時の考察の仕方という背景で、現代の普遍的定義ではない。',
 'zunächstは六等号の後にまず力を指摘し、括弧の測定例、条件付き質量の導出へ進む説明順として保持する。ばね秤は例えば採り得る一方法で、実際に測定したとも唯一の方法とも読まない。物理的な校正・可能性・同じ力の共有は既存el2–embに残す。',
 '条件は、同じ共動系の力を端的に力と呼び、質量数値×加速度数値=力数値を保持し、加速度をKで測ること。emcの量単位と尺度を維持する。eisywは呼称を採る行為であり、物理的な限定を取り払う行為ではない。',
 '縦は瞬間速度(v,0,0)を持つKのx軸、横はその直交するy/z成分の共通係数。先行の直交校正と同じ物理配置を継承する。v=0では選択済みの軸に対する共通のμとして読む。横を現代の別の力の定義によるμβへ直さない。',
 '質量は同じ全六実数の成分関係の係数として同定し、現在の実加速度と実力にもその関係を要求する。全加速度の物理的な実現や実験済みを要求しない。零加速度の一点一致を同定根拠にしない。',
 '二分数の平方根は非負の根。V>0、0≤v<V、μ>0と整合単位を保つ。正のβの定義とμβ³/μβ²から同じ値を表す。一般実数体の解析定理と原文同義性は有限診断で証明したとはしない。',
 '旧423主張・全意味規約・判断・証拠を保持する。新基本関係四つは型付き質問提示・慣行への準拠・端的な命名・型付き量の名称という再利用できる関係であり、電子の物理や原文一文の真理は合成側に置く。',
]

def mass_args():return shared()+[v(n) for n,t in EXTRA_MASS]
def mass_content(name,body,coefficients=False):
    return content(name,quantified('f',BOUND+EXTRA_MASS+(COEFFICIENTS if coefficients else []),body))

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] c.\n' for n,(fs,_) in PRIMITIVES.items())+''.join('r '+n+'[] a.\n' for n in REFERENCES)
    ratio=k('shv',k('eisxt'),k('sjd',k('tc')))
    text+=define('emh',[],k('bf',ONE,k('shv',ratio,ratio)),R)
    text+=define('emi',[],k('cj',k('emh')),R)
    root=k('emi');L=k('shv',v('mass'),k('sjd',k('shv',k('shv',root,root),root)));T=k('shv',v('mass'),k('sjd',k('emh')))
    text+=define('emj',ALL,both(k('emf',*args(ALL)),k('sca',v('longitudinal'),L),k('sca',v('transverse'),T)))
    text+=define('emk',CONVENTION,k('eisyw',k('eisy3'),k('rd'),k('eisy7'),v('forcerecord'),k('eirf'),v('context')))
    text+=define('eml',ALL,both(k('emd',*args(ALL)),k('emk',*args(CONVENTION))))
    text+=define('emm',ALL,op('y',k('eml',*args(ALL)),k('emj',*args(ALL))))
    actual=mass_args();allactual=actual+args(COEFFICIENTS)
    text+=mass_content('emn',k('emm',*allactual),True)
    text+=mass_content('emo',op('y',both(k('emc',*actual),k('emk',*actual)),quantified('g',COEFFICIENTS,k('emj',*allactual))))
    for name,which,value in [('emp','longitudinal',L),('emq','transverse',T)]:text+=mass_content(name,op('y',k('eml',*allactual),k('sca',v(which),value)),True)
    factors=[k('tc'),k('eisxt'),k('soy',k('tc'),k('eisxt')),v('mass'),*args(COEFFICIENTS)]
    components=k('seph',*args(COEFFICIENTS),*args(ACCEL),*[app(v('force'),k(a)) for a in ROLES[:3]])
    text+=mass_content('emr',op('y',both(k('emc',*actual),k('sepi',*factors)),components),True)
    text+=mass_content('ems',op('y',k('emc',*actual),k('emk',*actual)))
    text+=content('emt',both(op('t',k('ems'),v('point')),op('t',k('emr'),v('point'))))
    text+=content('emu',both(op('t',k('elu'),v('point')),op('t',k('emt'),v('point'))))
    text+=define('emv',ALL,v('longitudinal'),R)+define('emw',ALL,v('transverse'),R)
    p=v('point');who=k('rd');paper=k('eirf');scope=k('eisxg')
    text+=content('emx',both(k('eisyx',k('eisza'),'l[a][k yn[]]','r[p emd]','r[p emv]',paper,scope,p),k('eisyx',k('eiszb'),'l[a][k yo[] k yp[]]','r[p emd]','r[p emw]',paper,scope,p)))
    text+=content('emy',both(k('eisyu',k('eisyy'),who,k('eisym'),quote('elk'),'r[p emc]','r[p eme]',scope,p),k('eisyv',k('eisyy'),who,scope,p),op('t',k('emx'),p)))
    text+='d emz[] f[j s[k emy[]]].\n'
    text+=define('em2',[],both(k('eir3',k('eisyy'),who,paper,quote('emz'),k('ri')),k('ue',k('eisym'),k('eisyy'),k('ri')),k('ue',k('eisyy'),k('eisyp'),k('ri'))))
    text+=content('em3',both(k('uh',k('eisyz'),who,quote('ema'),scope,p),k('eiswm',k('eisyz'),who,k('eisyq'),quote('elu'),paper,p),k('eir5',k('eisy2'),who,k('eisyz'),quote('emb'),p),k('eisa5',k('eisy2'),who,quote('ema'),quote('emb'),p),k('uh',k('eisy2'),who,quote('emb'),scope,p),k('ue',k('eisyz'),k('eisy2'),p),k('ue',k('eisy2'),k('eisy3'),p)))
    text+='d em4[] f[j s[k em3[]]].\n'
    text+=define('em5',[],both(k('eir3',k('eisyz'),who,paper,quote('em4'),k('ri')),k('ue',k('eisyq'),k('eisyz'),k('ri'))))
    conclusion=both(op('t',k('emn'),p),op('t',k('emo'),p))
    # A closed content for the joint conclusion, without executing it in the presentation.
    text+=content('enb',conclusion)
    text+=content('enc',op('y',op('t',k('emt'),p),op('t',k('enb'),p)))
    text+=content('em6',both(k('uh',k('eisy3'),who,quote('enc'),scope,p),k('zc',k('eisy3'),who,quote('emu'),quote('enb'),scope,p),k('eiswm',k('eisy3'),who,k('eisyq'),quote('elu'),paper,p),k('eisd4',k('eisy3'),who,k('eisnb'),k('ra'),paper,p),k('eisox',k('eisy4'),quote('emr'),p),k('eisox',k('eisy5'),quote('emp'),p),k('eisox',k('eisy6'),quote('emq'),p),op('t',k('emx'),p),k('uf',who,k('eisy3'),k('eisy5'),p),k('uf',who,k('eisy3'),k('eisy6'),p),k('ue',k('eisy3'),k('eisy4'),p),k('ue',k('eisy4'),k('eisy5'),p),k('ue',k('eisy5'),k('eisy6'),p)))
    text+='d em7[] f[j s[k em6[]]].\n'
    text+=define('ena',[],both(k('eir3',k('eisy3'),who,paper,quote('em7'),k('ri')),k('ue',k('eisy2'),k('eisy3'),k('ri'))))
    return text

MEANINGS['enb']='同じ条件付きの全係数結論emnと、同じ規約での二係数の存在結論emoを合わせる。提示が引用する結論の内容で、引用の実行は要求しない。'
MEANINGS['enc']='呼称・数値法則の保持emtを前件、同じ二係数の結論enbを後件に持つ内容。著者はこの条件文を述べ、規約を採らない別定義の値をここで排除しない。'

@lru_cache(None)
def build():
    old=parse(read(PARENT));assert len(old['statements'])==423
    assert not(set(MEANINGS)|set(PRIMITIVES)|set(REFERENCES))&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol=n,arguments=[])) for n in ('em2','em5','ena')]
    added=doc['declarations'][len(old['declarations']):]
    prim={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,t in PRIMITIVES[d['name']][0]] if d['name'] in PRIMITIVES else [],meaning_ja=PRIMITIVES[d['name']][1] if d['name'] in PRIMITIVES else REFERENCES[d['name']]) for d in added if d['kind']=='primitive'}
    basis=dict(status='directional_mass_question_force_example_and_conditional_result',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=prim,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=list(INDICES)).document
    ann=json.loads(read('data/electron-force-measurement-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode()))
    for symbol,label in [('eisy7','die auf das Elektron wirkende Kraft'),('eisza','Longitudinale Masse'),('eiszb','Transversale Masse')]:ann['entries'].append(dict(symbol=symbol,role='designation',forms=[dict(text=label,language='de',role='printed_identifying_form')]))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
