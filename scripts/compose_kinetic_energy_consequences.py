"""Connect energy divergence, physical exclusion and the material extension."""
from scripts.compose_electron_kinetic_work import *
from scripts.compose_material_velocity import TRACK
from scripts.compose_doppler_infinity import GRAPH

PARENT=FULL;PARENT_BASIS=BASIS;PARENT_ANNOTATIONS=ANNOTATIONS
FULL='examples/v014/einstein-kinetic-energy-consequences.noema'
CORE='examples/v014/kinetic-energy-consequences-core.noema'
BASIS='data/kinetic-energy-consequences-basis-v1.json'
ANNOTATIONS='data/kinetic-energy-consequences-identifiers-v1.json'
BASE=[(n,'a') for n in ('matter','frame','lengthunit','timeunit','massunit','forceunit','energyunit')]+[('context','d')]+[(n,'b') for n in ('lengthscale','timescale','massscale','forcescale','energyscale')]+[(n,R) for n in ('light','mass')]
TRACE=[('event','a'),('domain',DOMAIN),('curve',CURVE),('location',POINT)]+[(n,R) for n in ('ux','uy','uz')]
NUM=[('speed',R),('energy',R)]
SETTING=BASE+TRACE+NUM
BACKGROUND=[('view','a')]+BASE
WITNESSES=TRACE+[('alternative','d')]
MOTION=[(n,t) for n,t in BASE if n in ('matter','frame','lengthunit','timeunit','context')]+TRACE+[('speed',R)]
PRIMITIVES={
 'eis3l':([('node','a'),('author','a'),('earlier','i[e]'),('current','i[e]'),('aspect','i[h[a d] c]'),('document','a'),('context','d')], 'authorがnodeで、同じdocumentのearlierとcurrentを、同じ理論的見解と状況についてaspectが指定する観点で同様の結果として提示する比較。内容・観点・先後を保持し、同義性、同一の対象範囲、厳密な論理含意、先行する予告の証明完了、両内容の現実成立を含意しない。具体的な物理内容や数式は引用側で合成する。'),
}
REFERENCES={
 'eis3k':'同じ著者の同じ論説の理論構成eigjを指す見解。eiscvで論説と基準状況へ結び、都合のよい許容状況の一覧へ替えない。',
 'eis3m':'u0263第一文、Wがv=Vで無限に大きくなるという帰結の箇所。',
 'eis3n':'u0263第二文、超光速度の存在可能性を否定する箇所。',
 'eis3o':'u0263のダッシュ間、同じ著者の先行結果との同様性を挿入する箇所。',
 'eis3p':'u0264で同じ運動エネルギー表現をponderableな質量にも適用すべきとする箇所。',
 'eis3q':'u0264で上に述べた電荷付加の議論を理由として参照する箇所。',
}
MEANINGS={
 'epq':'有効な三速度成分の平方和が、有効な非負の速さの二乗と等しい三次元のノルム条件。負の枝又は一つの軸成分だけを速さにしない。',
 'epr':'同じ点状物体・系・校正された長さ時間単位・出来事の実曲線に、三つの座標時刻微分seocと非負ノルムepqを結ぶ。光速未満条件、有限beta、エネルギー公式をこの運動の意味に含めない。',
 'eps':'同じeprの実速度、正の低速慣性質量、整合した長さ時間質量力と仕事単位、同じ出来事の並進運動エネルギーを接続する。電荷、電場、無放射の軌道や運動エネルギー公式は適用事例の選択条件にしない。',
 'ept':'同じepsへ最右辺のW=μV²(beta−1)を適用する。前段の印刷された無μの中間積分sergを修正せず、ここでは著者が指す最右辺の表現sercだけを取り出す。',
 'epu':'同じ理論・電子・系・質量・光速・全単位尺度を固定し、許容された代替状況と一組の実履歴・出来事・三速度を存在量化してeptへ結ぶ、入力速さと出力エネルギーの関係。',
 'epv':'背景を固定した同じepuを速さ・エネルギーの二実数関係として返す。各点の履歴・時点は変えてよいが、質量又はエネルギー単位を変えて発散させない。',
 'epw':'同じepuに有限の速さとエネルギーの点が少なくとも一組あるという非空条件。',
 'epx':'同じ非空の物理的エネルギー関係が光速の左側の全正近傍に点を持ち、任意の有限上限に対し十分近い全ての出力がそれを超えるというekjtの発散。実数無限大や境界v=Vでの有限値を作らない。',
 'epy':'同じ理論が許す状況で、同じ正の低速質量の点状物体が同じ系・単位に対し指定速さで実際に動くことの可能性。実履歴・出来事・三速度・代替状況を一組で結ぶ。エネルギー値の存在やbetaの実数性を可能性の選択条件にしない。',
 'epz':'同じ理論の許容状況が非空であり、光速を厳密に超える全ての有効な速さについてepyが成立しないという物理的な存在不可能性。光速ちょうど、光そのもの、数式の定義域の不在と区別する。',
 'ep2':'同じ論説の見解に対し、現在の電子とKの超光速度の物理的排除epzを比較の観点として返す。',
 'ep3':'現在と同じ電子・K・質量・仕事単位を背景にしたエネルギー発散と、同じ論説の理論への対応を結ぶu0263第一文の内容。',
 'ep4':'同じ理論と同じ現在の電子についての超光速度の存在不可能性。発散から自動導出せず、別の内容として述べる。',
 'ep5':'同じepsの適用事例を共通尺度へ換算し、既存setfで同じエネルギー表現を述べる。エネルギー尺度を質量×速度尺度二乗へ整合させ、単位の違う裸の数値を等置しない。',
 'ep6':'全てのponderableな物質点の、同じ実速度・低速質量・校正単位・運動エネルギーを持つ光速未満の事例に、同じep5の表現を適用する内容。対象の電荷、中性、加速の実施や質量の厳密保存を新条件にしない。',
 'ep7':'先行の同じ電子の完全なエネルギー記述の設定から、同じ最右辺sercを取り出した内容。表現への照応用であり、無μの中間積分へμを加える訂正ではない。',
 'eqa':'エネルギーの発散を先行表現からの帰結として述べ、超光速の不可能性を別に述べ、先行運動学の適用留保と上限の予告への同様性をダッシュ内の挿入として提示する。',
 'eqb':'u0263全文のメッセージ。',
 'eqc':'u0263を同じ著者・論説へ帰属し、運動エネルギーの等号列の直後に置く。',
 'eqd':'同じエネルギー表現の物質点への適用を、先行の質量結果への添加として述べ、上の電荷付加の可能性eoiを理由として参照する。推論の必要性を命令にせず、付加による質量不変を補わない。',
 'eqe':'u0264全文のメッセージ。',
 'eqf':'u0264を同じ著者・論説へ帰属し、u0263の境界と不可能性に続ける。',
}
LIMITS=[
 '原刊920頁u0263–u0264を扱う。M0428=W、M0429=v=V。v=Vで無限大という表記は、同じ正の質量と光速度の有限な運動状態の関係においてvをVへ下から近づける発散として読む。無限大を実数又は実在する境界状態のエネルギー値にしない。',
 'エネルギー式は前段M0427の最右辺を指す。無μの中間積分を保持したまま、最右辺sercとその物理的な量の帰属を参照する。全印刷式が正しい又は積分計算が証明済みと認めることは、著者の帰結を記述する条件ではない。',
 '発散の背景は同じ現在の電子、K、低速慣性質量、光速、全単位と尺度である。履歴・出来事・三速度と許容状況は各有限点で変えられる。許容範囲は同じ理論の全範囲で、実測標本や大きいエネルギーだけを選ばない。非空性と全正近傍での接近、全出力の上限超過を保つ。',
 'Überlichtgeschwindigkeitenの存在可能性は、考察中の正の低速質量を持つ点状物体がKに対しVを超える速さで動く、同じ理論内の物理状態の可能性として読む。任意の三方向をノルムで扱い、光、位相速度や現代の別種の対象へ範囲を拡張しない。v=Vそのものの不可能性はこの文の超光速という語へ補わない。',
 '可能性の実現条件には校正された実軌道と三速度を使い、光速未満や有限beta、有限運動エネルギーの存在を先取りしない。エネルギー発散から不可能性を証明する一般規則は追加せず、二つを著者の主張として分ける。',
 'wie bei unseren früheren Resultatenは同じ著者の先行運動学、特に§4の超光速での適用留保と光速上限の予告ejhtへ照応する読みを採る。唯一の歴史的参照先又は全先行結果の同義性とはしない。共通点は同じ理論が超光速の物理的適用を許さないこと。ダッシュ内の比較を補足として保持し、予告が既に証明されていたと書き換えない。',
 'u0264のponderable Massenはu0260と同じ正の低速慣性質量を持つ点状物体の範囲と読む。最右辺の表現を全適格な光速未満の事例へ適用し、同じ三速度のノルム、出来事、仕事単位・尺度、実際の運動エネルギーを保持する。電荷又は中性の前提、静電場による加速実験の実施、付加後の質量の厳密不変は加えない。',
 'auch/ebensoは先行の質量結果に続く適用の添加、mußはこの論述での推論上の必要性と読む。dem oben angeführten Argument zufolgeはu0260の同じ物体への任意小電荷付加の可能性eoiを理由として参照する。可能性から公式への厳密な数学的証明や現代の粒子理論の真理とは分ける。',
 '旧430主張と旧意味・証拠を保存する。有限の数値・役割・引用・束縛検査及び既存発散証拠は、全実数域の解析、理論の現実的妥当性、原文同義性の自動証明ではない。',
]

def fixed(fields,**replace):
    return [replace.get(n,{'view':k('eis3k'),'context':v('point')}.get(n,k(FIXED[n]) if n in FIXED else v(n))) for n,t in fields]

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] c.\n' for n,(fs,_) in PRIMITIVES.items())+''.join('r '+n+'[] a.\n' for n in REFERENCES)
    zero=k('bb','n p a b');one=k('bb','n p b b');s=v('speed');E=v('energy');ctx=v('context');view=v('view')
    text+=define('epq',[(n,R) for n in ('ux','uy','uz','speed')],both(*(k('ba',v(n)) for n in ('ux','uy','uz','speed')),k('bc',zero,s),k('sca',k('shv',s,s),k('seag',v('ux'),v('uy'),v('uz')))))
    whole='i[x '+R+' y '+R+' z '+R+' time '+R+']['+both(*(k('ba',v(n)) for n in ('x','y','z','time')))+']'
    motion=both(k('eiszn',v('matter'),ctx),k('ejsl',v('frame'),v('lengthunit'),v('timeunit'),ctx),k('ek3p',v('matter'),v('frame'),ctx,v('domain'),v('curve'),v('lengthunit'),v('timeunit'),whole),k('eisqd',v('matter'),v('frame'),v('event'),v('lengthunit'),v('timeunit'),v('location'),ctx),k('seoc',v('matter'),v('frame'),ctx,v('domain'),v('curve'),v('event'),v('location'),v('ux'),v('uy'),v('uz')),k('epq',v('ux'),v('uy'),v('uz'),s))
    text+=define('epr',MOTION,motion)
    energy=k('eiszt',v('matter'),v('frame'),v('event'),v('energyunit'),E,ctx)
    units=both(k('ek3n',*args(UNITS)),k('ejwb',v('energyunit'),'n p c b','n p b b','n u c b',v('energyscale'),ctx),op('e',v('energyscale'),k('ad',v('forcescale'),v('lengthscale'))),k('eiszw',v('frame'),v('lengthunit'),v('forceunit'),v('energyunit'),ctx))
    text+=define('eps',SETTING,both(k('epr',*args(MOTION)),k('ek3o',*args(MASS)),units,k('ba',v('light')),k('bg',zero,v('light')),k('ba',E),energy))
    formula=k('serc',v('light'),s,k('soy',v('light'),s),v('mass'),E)
    text+=define('ept',SETTING,both(k('eps',*args(SETTING)),formula))
    alternate=[v('alternative') if n=='context' else v(n) for n,t in SETTING]
    text+=define('epu',BACKGROUND+NUM,quantified('g',WITNESSES,both(k('eisoe',view,ctx,v('alternative')),k('ept',*alternate))))
    text+=define('epv',BACKGROUND,'i[speed '+R+' energy '+R+']['+k('epu',*args(BACKGROUND),s,E)+']',GRAPH)
    text+=define('epw',BACKGROUND,quantified('g',NUM,k('epu',*args(BACKGROUND),s,E)))
    text+=define('epx',BACKGROUND,both(k('epw',*args(BACKGROUND)),k('ekjt',k('epv',*args(BACKGROUND)),v('light'))))
    possible=both(k('eisoe',view,ctx,v('alternative')),k('epr',*[v('alternative') if n=='context' else v(n) for n,t in MOTION]),k('ek3o',*[v('alternative') if n=='context' else v(n) for n,t in MASS]))
    text+=define('epy',BACKGROUND+[('speed',R)],quantified('g',WITNESSES,possible))
    accessible=quantified('g',[('alternative','d')],k('eisoe',view,ctx,v('alternative')))
    text+=define('epz',BACKGROUND,both(k('ba',v('light')),k('bg',zero,v('light')),accessible,quantified('f',[('speed',R)],op('y',both(k('ba',s),k('bg',v('light'),s)),op('u',k('epy',*args(BACKGROUND),s))))))
    text+=define('ep2',[('view','a'),('context','d')],k('epz',*fixed(BACKGROUND,view=view,context=ctx)))
    p=v('point');theory=k('eiscv',k('eis3k'),k('eirf'),quote('eigj'),p)
    text+=content('ep3',both(theory,k('epx',*fixed(BACKGROUND))))
    text+=content('ep4',both(theory,k('epw',*fixed(BACKGROUND)),k('epz',*fixed(BACKGROUND))))
    speedscale=k('shv',k('bb',v('lengthscale')),k('sjd',k('bb',v('timescale'))))
    text+=define('ep5',SETTING,both(k('eps',*args(SETTING)),k('setf',v('light'),s,k('soy',v('light'),s),v('mass'),E,k('bb',v('massscale')),speedscale,k('bb',v('energyscale')))))
    fields=[(n,t) for n,t in SETTING if n not in ('frame','lengthunit','timeunit','light','context')]
    fixed_material=[{'frame':k('ra'),'lengthunit':k('ta'),'timeunit':k('rb'),'light':k('tc'),'context':p}.get(n,v(n)) for n,t in SETTING]
    text+=content('ep6',quantified('f',fields,op('y',both(k('eoc',v('matter'),p),k('eps',*fixed_material),k('bg',s,k('tc'))),k('ep5',*fixed_material))))
    # This projection retains the physical assumptions, and only selects the final expression.
    text+=content('ep7',both(op('t',k('epg'),p),k('serc',k('tc'),k('eisxt'),k('soy',k('tc'),k('eisxt')),k('eis2a'),k('zrfenergy'))))
    who=k('rd');paper=k('eirf');scope=k('eisxg')
    compare=both(k('eiswm',k('eis3o'),who,k('zia'),quote('ejht'),paper,p),k('eis3l',k('eis3o'),who,quote('ejht'),quote('ep4'),'r[p ep2]',paper,p))
    text+=content('eqa',both(k('uh',k('eis3m'),who,quote('ep3'),scope,p),k('zc',k('eis3m'),who,quote('ep7'),quote('ep3'),scope,p),k('eiswm',k('eis3m'),who,k('eis3h'),quote('eph'),paper,p),k('uh',k('eis3n'),who,quote('ep4'),scope,p),compare,k('eisa5',k('eis3o'),who,quote('ep4'),quote('eqg'),p),k('ue',k('eis3m'),k('eis3n'),p)))
    return text,compare

def all_definitions():
    text,compare=definitions()
    # eqg must precede the presentation that quotes it.
    marker='d eqa';at=text.index(marker);text=text[:at]+content('eqg',compare)+text[at:]
    p=v('point');who=k('rd');paper=k('eirf');scope=k('eisxg')
    text+='d eqb[] f[j s[k eqa[]]].\n'
    text+=define('eqc',[],both(k('eir3',k('eis3m'),who,paper,quote('eqb'),k('ri')),k('ue',k('eis3h'),k('eis3m'),k('ri'))))
    text+=content('eqd',both(k('uh',k('eis3p'),who,quote('ep6'),scope,p),k('eisij',k('eis3p'),who,quote('eon'),quote('ep6'),paper,p),k('eiswm',k('eis3p'),who,k('eis3h'),quote('ep7'),paper,p),k('eiswm',k('eis3q'),who,k('eiszr'),quote('eoi'),paper,p),k('zc',k('eis3q'),who,quote('eoi'),quote('ep6'),scope,p)))
    text+='d eqe[] f[j s[k eqd[]]].\n'
    text+=define('eqf',[],both(k('eir3',k('eis3p'),who,paper,quote('eqe'),k('ri')),k('ue',k('eis3n'),k('eis3p'),k('ri'))))
    return text
MEANINGS['eqg']='ダッシュ内の同様性の比較と同じ先行箇所への照応を一つにまとめた挿入内容。主節の不可能性と引用・挿入の作用範囲を保つ。'

@lru_cache(None)
def build():
    old=parse(read(PARENT));assert len(old['statements'])==430
    assert not(set(MEANINGS)|set(PRIMITIVES)|set(REFERENCES))&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+all_definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol=n,arguments=[])) for n in ('eqc','eqf')]
    added=doc['declarations'][len(old['declarations']):]
    prim={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,t in PRIMITIVES[d['name']][0]] if d['name'] in PRIMITIVES else [],meaning_ja=PRIMITIVES[d['name']][1] if d['name'] in PRIMITIVES else REFERENCES[d['name']]) for d in added if d['kind']=='primitive'}
    basis=dict(status='physical_energy_boundary_and_ponderable_mass_extension',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=prim,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[430,431]).document
    ann=json.loads(read(PARENT_ANNOTATIONS));ann.update(document=FULL,document_sha256=digest(body.encode()))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
