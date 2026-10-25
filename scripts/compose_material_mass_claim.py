"""Extend the mass result to ponderable points and explain the charge-addition reason."""
from scripts.compose_electron_convention_caution import *
from scripts.compose_point_particle_dynamics import MASS as INERTIA,UNITS
from scripts.compose_material_acceleration import AT
from scripts.compose_electron_comoving_history import HISTORY as TWOHISTORY

PARENT=FULL;PARENT_BASIS=BASIS;PARENT_ANNOTATIONS=ANNOTATIONS
FULL='examples/v014/einstein-material-mass-claim.noema'
CORE='examples/v014/material-mass-claim-core.noema'
BASIS='data/material-mass-claim-basis-v1.json'
ANNOTATIONS='data/material-mass-claim-identifiers-v1.json'
BASE=[('matter','a'),('unit','a'),('context','d')]
TRIAL=BASE+[('bound','b'),('operation','a'),('alternative','d')]
READING=[('frame','a'),('event','a'),('record','a'),('scale','b')]
MATERIAL=[(n,'a') for n in ('matter','frame','forceframe','event','lengthunit','timeunit','massunit','forceunit','accelerationunit')]+[('context','d')]+[(n,'b') for n in ('lengthscale','timescale','massscale','forcescale','accelerationscale')]+[(n,R) for n in ('mass','light','speed')]+[('offset',POINT),('domain',DOMAIN),('curve',CURVE),('newdomain',DOMAIN),('newcurve',CURVE),('point',POINT)]+PROFILES+ACCEL+[('forcerecord','a'),('force',POINT)]
PRIMITIVES={
 'eiszn':([('matter','a'),('context','d')], 'matterを同じ文脈の力学的記述で、慣性を担い位置を追跡できる物体の点状理想化として扱う。内部の広がり・形状・回転や多極構造を分解せず、機械的状態と作用を一つの代表位置へ帰属させる。座標点や数値自体を物体にせず、実際の幾何学的体積零、既に帯電していること、特定粒子種、特定の運動法則を含意しない。質量の値と正性、軌道と作用は別に接続する。'),
 'eiszo':([('record','a'),('matter','a'),('frame','a'),('event','a'),('context','d')], 'recordが同じmatterに当該frame・event・contextで働く有向の機械的作用の力を記述するという物理的な帰属。運動量変化への作用又はそれを釣り合わせる機械的作用との比較で同定し、数値ベクトルだけで力と認めない。電気的作用に限定せず、質量係数の特定の値、運動方程式の成立、実測済みは含めない。数値・単位・力と加速度の規約は別に結ぶ。'),
 'eiszp':([('node','a'),('author','a'),('designation','a'),('criterion','i[h[a a d] c]'),('anchor','a'),('document','a'),('scope','a'),('context','d')], 'authorがnodeでdesignationを、同じdocument・scopeの先行anchorで採った意味に従い、criterionが同じ対象・数量単位・状況について指定する分類の呼称として用いているという限定付きの語用。criterionは物理的対象と量の意味を合成して与える。名称だけで分類せず、他の用法や現代の粒子種の意味へ替えない。分類対象の実在、分類内容の現実成立又は新しい命名を含意しない。'),
}
REFERENCES={'eiszq':'u0260前半、先行の質量結果はponderableな物質点にも当てはまると指摘する箇所。','eiszr':'u0260後半、任意に小さい電荷の付加可能性をその理由に挙げる箇所。','eiszs':'u0260の括弧in unserem Sinneによる電子という呼称の意味限定の箇所。'}
MEANINGS={
 'eoc':'慣性を担う点状物体eisznであり、同じ文脈で校正された質量単位と正の低速慣性質量ek3oを持つというponderableな物質点の分類。最初から帯電又は中性と決めず、単なる対象リストzrdmaterialにしない。',
 'eod':'同じ点状物体・電荷単位・状況に、zrdchargeの値を同じ物体の電気量の記録sbw2で帰属させる。系・出来事・記録・正の尺度を一組で存在量化する。元の量は零でもよい。',
 'eoe':'同じeodの物理的電荷帰属に、電気量を一位置へ集中させるeisqcの点状担体と非零電荷を加える。本論文でいう電子の意味であり、特定の現代粒子種や固定の負電荷ではない。',
 'eof':'同じ対象・単位・元状況・上限・操作・結果について、既存seqtの小さい非零追加量・可能結果・加法的収支を保持し、対象の同一性を保つeirk、元の物理的電荷eod、結果の点状荷電対象eoeを接続する。',
 'eog':'指定した同じ正の上限について、eofを満たす操作と可能な結果が一組で存在する。実行済みや全結果での成功は要求しない。',
 'eoh':'同じ物体・単位・元状況を固定したまま、全ての正の有理上限についてeogが成立する。操作と結果は上限に依存してよい。有限標本又は固定した小電荷へ縮めない。',
 'eoi':'全てのponderableな物質点に、同じ正に校正された一つの電荷単位を全上限の外側で共有してeohの可能性があるという後半内容。元の対象の中性、電荷付加の実施、付加後の質量の厳密不変は加えない。',
 'eoj':'同じ物質点の長さ・時間・質量・力・加速度の整合した正の単位尺度、点状理想化と正の低速慣性質量を保持する。A T²=L、M A=Fにより元の質量式と同じ数値規約を用いる。',
 'eok':'同じ物質点の両系の完全な校正履歴ek5s、K側の実二階微分sepp、瞬間速度(speed,0,0)、対応する同じ出来事での共動系の実速度零を結ぶ。系の速度と物体の速度、元と新の座標時刻を取り違えず、電荷や場は要求しない。',
 'eol':'同じeoj/eokに、共動系の同じ機械的力記録・三成分と、力を共動系・加速度を元系で測る規約を結ぶ。電気的力だけに限定せず、力の数値が所望の質量式に合うことは選択条件に入れない。',
 'eom':'同じ物理設定eolの元系の三加速度と共動系の力に、先行と同じseph/sepfの二質量係数μ β³,μ β²を適用する。低速質量、単位、速度を同じ物質点へ帰属させ、零入力から任意の係数を認定しない。',
 'eon':'全ての同じ物質点の適用設定eolについて、eomの二係数が存在するという質量結果の適用拡張。電荷付加が質量を厳密に保存するという追加前提や、その可能性だけからの数学的証明を入れない。',
 'eoo':'著者が先行二質量の結果の拡張eonを指摘し、その理由として電荷付加の可能性eoiを述べる全文提示。先行結果への照応、dennの理由方向、in unserem Sinneの同じ呼称の意味限定、本文順序を保つ。',
 'eop':'物質点への適用と、任意に小さい電荷付加を理由とする全文のメッセージ。',
 'eoq':'u0260の全文を同じ著者・論説に帰属し、u0259の比較上の注意に続ける主張427。',
}
LIMITS=[
 '原刊919頁u0260全文。ponderableな物質点は、内部の広がりを分解しない力学的な点状物体で正の低速慣性質量を持つという読みを採る。重力測定や質量と重量の数値同一性を追加しない。対象を荷電粒子だけ又は中性物体だけに制限しない。',
 '質量結果は、同じ整合単位、瞬間速度方向と直交二方向、共動系の力と元系の座標時刻加速度という規約でのμβ³,μβ²を指す。先行の一般性を保つ軸選択に従い、個別物質点の速度をspeedとして扱う。kの力を現代の別の力定義へ替えず、横係数をμβへ直さない。',
 '付加の可能性は既存の物理的可能結果と加法的な符号付き電気量を使う。全ての正の有理上限を用いる任意小の表現は正の実上限にも正の有理下界がある性質に依拠し、有限例の列挙へ替えない。量の連続的可分性を現実の実験や現代の粒子理論で証明したとはしない。',
 '同じ物体と単位を保ち、元の電荷を含む加法的収支を使う。最初から中性とはせず、正負の追加を許し、結果で零への相殺を成功にしない。操作と結果は上限に依存してよいが、別物体への置換、任意の数値変更、実際に操作したこと又は全結果成功へ替えない。',
 'in unserem Sinneはu0240の点状荷電対象という著者の呼称に戻る。物理的に別種の粒子へ生成・変質する主張ではない。dennは可能性から質量結果への著者の理由付けであり、質量の連続性や電荷付加による慣性の厳密不変を新たに仮定して証明を完成させない。',
 '旧427主張と判断・証拠を保存する。有限検査は役割接続・対照例・束縛の診断であり、実数全域、微分、物理的可能性又は原文同義性を自動証明しない。後続の運動エネルギーu0261以降は別に扱う。',
]

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] c.\n' for n,(fs,_) in PRIMITIVES.items())+''.join('r '+n+'[] a.\n' for n in REFERENCES)
    rat=lambda x:'n '+('u' if x<0 else 'p')+' '+{0:'a',1:'b',2:'c'}[abs(x)]+' b'
    fields=[('frame','a'),('event','a'),('massunit','a'),('massscale','b'),('mass',R)]
    text+=define('eoc',[('matter','a'),('context','d')],both(k('eiszn',v('matter'),v('context')),quantified('g',fields,both(k('ek3o',*args(INERTIA)),k('ejwb',v('massunit'),rat(0),rat(1),rat(0),v('massscale'),v('context'))))))
    charge=lambda ctx:app(k('zrdcharge'),v('matter'),v('unit'),ctx)
    reading=k('sbw2',v('record'),v('matter'),k('zor'),v('frame'),v('event'),v('unit'),v('scale'),charge(v('context')),v('context'),'p zof','p zog')
    text+=define('eod',BASE,both(k('eiszn',v('matter'),v('context')),quantified('g',READING,reading)))
    text+=define('eoe',BASE,both(k('eod',*args(BASE)),k('eisqc',v('matter'),v('context')),op('u',k('sca',charge(v('context')),ZERO))))
    callbacks=['p eiszn']+[k('zrd'+n) for n in ('charge','amount','possible','added')]
    text+=define('eof',TRIAL,both(k('seqt',*args(TRIAL),*callbacks),k('eirk',v('operation'),v('matter'),v('context')),k('eod',*args(BASE)),k('eoe',v('matter'),v('unit'),v('alternative'))))
    text+=define('eog',BASE+[('bound','b')],quantified('g',TRIAL[-2:],k('eof',*args(TRIAL))))
    text+=define('eoh',BASE,quantified('f',[('bound','b')],op('y',k('aa',rat(0),v('bound')),k('eog',*args(BASE),v('bound')))))
    p=v('point');body=v('matter');unit=v('unit')
    text+=content('eoi',quantified('f',[('matter','a')],op('y',k('eoc',body,p),quantified('g',[('unit','a'),('scale','b')],both(k('zof',unit,k('zor'),v('scale'),p),k('aa',rat(0),v('scale')),k('eoh',body,unit,p))))))
    units=both(k('ek3n',*args(UNITS)),k('ejwb',v('accelerationunit'),rat(1),rat(0),rat(-2),v('accelerationscale'),v('context')),op('e',k('ad',v('accelerationscale'),k('ad',v('timescale'),v('timescale'))),v('lengthscale')),op('e',k('ad',v('massscale'),v('accelerationscale')),v('forcescale')))
    text+=define('eoj',MATERIAL,both(k('eiszn',body,v('context')),k('ek3o',*args(INERTIA)),units))
    hist={n:v(n) for n,t in TWOHISTORY};hist.update(first=v('frame'),second=v('forceframe'),olddomain=v('domain'),oldcurve=v('curve'))
    point=v('point');moment=coord(point,ROLES[3]);newpoint=k('ek5i',v('light'),v('speed'),v('offset'),point)
    text+=define('eok',MATERIAL,both(k('ek5s',*[hist[n] for n,t in TWOHISTORY]),k('sepp',*args(AT)),*(k('sca',app(v(n),moment),x) for (n,t),x in zip(PROFILES,(v('speed'),ZERO,ZERO))),k('seoc',body,v('forceframe'),v('context'),v('newdomain'),v('newcurve'),v('event'),newpoint,ZERO,ZERO,ZERO)))
    text+=define('eol',MATERIAL,both(k('eoj',*args(MATERIAL)),k('eok',*args(MATERIAL)),k('eiszo',v('forcerecord'),body,v('forceframe'),v('event'),v('context')),k('zpc',v('forcerecord'),body,k('zpn'),v('forceframe'),v('event'),v('forceunit'),v('force'),v('context')),k('zraconvention',body,v('forceframe'),v('frame'),v('event'),v('forceunit'),v('accelerationunit'),v('context'))))
    text+=define('eom',MATERIAL+COEFFICIENTS,both(k('eol',*args(MATERIAL)),k('seph',*args(COEFFICIENTS),*args(ACCEL),*[app(v('force'),k(a)) for a in ROLES[:3]]),k('sepf',v('light'),v('speed'),k('soy',v('light'),v('speed')),v('mass'),*args(COEFFICIENTS))))
    fields=[(('location' if n=='point' else n),t) for n,t in MATERIAL if n not in ('frame','context','light')]
    actual=[{'frame':k('ra'),'context':p,'light':k('tc'),'point':v('location')}.get(n,v(n)) for n,t in MATERIAL]
    text+=content('eon',quantified('f',fields,op('y',k('eol',*actual),quantified('g',COEFFICIENTS,k('eom',*actual,*args(COEFFICIENTS))))))
    who=k('rd');paper=k('eirf');scope=k('eisxg')
    text+=content('eoo',both(k('uh',k('eiszq'),who,quote('eon'),scope,p),k('eiswm',k('eiszq'),who,k('eisy3'),quote('enb'),paper,p),k('uh',k('eiszr'),who,quote('eoi'),scope,p),k('zc',k('eiszr'),who,quote('eoi'),quote('eon'),scope,p),k('eiszp',k('eiszs'),who,k('eisxi'),'r[p eoe]',k('eisxb'),paper,scope,p),k('ue',k('eiszq'),k('eiszr'),p),k('ue',k('eiszr'),k('eiszs'),p)))
    text+='d eop[] f[j s[k eoo[]]].\n'
    text+=define('eoq',[],both(k('eir3',k('eiszq'),who,paper,quote('eop'),k('ri')),k('ue',k('eiszm'),k('eiszq'),k('ri'))))
    return text

@lru_cache(None)
def build():
    old=parse(read(PARENT));assert len(old['statements'])==427
    assert not(set(MEANINGS)|set(PRIMITIVES)|set(REFERENCES))&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='eoq',arguments=[]))]
    added=doc['declarations'][len(old['declarations']):]
    prim={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,t in PRIMITIVES[d['name']][0]] if d['name'] in PRIMITIVES else [],meaning_ja=PRIMITIVES[d['name']][1] if d['name'] in PRIMITIVES else REFERENCES[d['name']]) for d in added if d['kind']=='primitive'}
    basis=dict(status='ponderable_point_mass_result_and_small_charge_reason',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=prim,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[427]).document
    ann=json.loads(read(PARENT_ANNOTATIONS));ann.update(document=FULL,document_sha256=digest(body.encode()))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
