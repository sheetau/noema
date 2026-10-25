"""Rewrite (A) as six equalities in the same two-frame physical setting."""
from scripts.compose_electron_transformed_dynamics import *

PARENT='examples/v014/einstein-electron-transformed-dynamics.noema'
PARENT_BASIS='data/electron-transformed-dynamics-basis-v1.json'
FULL='examples/v014/einstein-electron-mass-rewrite.noema'
CORE='examples/v014/electron-mass-rewrite-core.noema'
BASIS='data/electron-mass-rewrite-basis-v1.json'
ANNOTATIONS='data/electron-mass-rewrite-identifiers-v1.json'
INDEX=422
REFERENCES={
 'eisyp':'u0252第二文Wir schreiben die Gleichungen (A) in der Formという、先行の同じ三式を書き換えて提示する箇所。質量を問う第一文とは区別する。',
 'eisyq':'u0253のM0417、三行の各二等号による書換え式の表示箇所。',
}
MEANINGS={
 'elq':'同じKの実電磁場の同じ指定四点で、μβ³ax=εX、μβ²ay=εβ(Y−vN/V)、μβ²az=εβ(Z+vM/V)という三行の最初の等号を構成する。正のμとV、0≤v<V、正のβ、有効な各数値を保持する。',
 'elr':'同じPAIRの旧指定点とその実座標写像ek5iによる新点において、εX=εX′、εβ(Y−vN/V)=εY′、εβ(Z+vM/V)=εZ′という各行の第二等号を構成する。新電場は独立した実場newelectricであり、変換混合をその定義として代入しない。電荷を両辺に保持し、ε=0から場の等値を逆推論しない。',
 'els':'同じPAIRに対する三行六等号elq/elrと、先行式(A)のKにおける右側初期変化ek74を共有する。実微分・同じ電子・単位・両系の対応は適用設定ek63へ結び、任意の独立した六数値へ置き換えない。',
 'elt':'同じ共動物理設定ek63と先行の場・座標変換ek66の下で、式(A)の初期三式elbと書換えのelsが同値であるという条件文。変換式又は運動式を前件なしで恒真にしない。',
 'elu':'先行式(A)と同じ全共動設定ek63に対し、同じ六等号と初期変化elsを述べる閉じた表示内容。新旧の証人を別々に選ばず、同じ38束縛と評価文脈を共有する。',
 'elv':'著者が同じ先行の変換内容ek7sの下で、ラベル(A)の指すelkをeluへ同値に書き換えて提示する。前の式への照応、(A)のラベル、六等号の表示、説明と本文順序を保持し、質量の問い又は力の測定規約をここで断定しない。',
 'elw':'u0252第二文とu0253の書換え導入・表示elvを伝える断定的メッセージ。',
 'elx':'同じ著者・論説へelwを帰属し、先行(A)の表示に続ける主張422。',
}
LIMITS=[
 'u0252第二文とu0253の三行M0417を原刊919頁へ照合する。u0252第一文の通常の考え方に沿った縦横質量の問いは、後続の力・加速度の規約とともに残し、u0252全体を判断済みにはしない。',
 '同じ電子eisxh・出来事eisxv・K=ra・k=eisxy・瞬間速さeisxt・V=tc・低速慣性質量μ・符号付き電荷ε・全単位尺度を先行PAIRから継承する。Kの瞬間速度(v,0,0)、両原点、実二階微分をek63に保持する。',
 '各行を最初の等号と第二等号に分ける。縦のμβ³、横のμβ²、右辺の横β、v/V、Yの負号とZの正号を保持する。現代の別の横質量μβへ修正しない。',
 '右端のX′,Y′,Z′は同じkの独立した実電場を、同じ出来事の新四点で評価した値である。旧点の数値を新系へそのまま渡さず、ek5iで対応させる。書換えに必要な既出変換と表示式を区別する。',
 '既出の小tの初期運動の読みとKのo(Δt)を維持する。加速度を有限時間の一定値にせず、kのτ微分とKのt微分を混同しない。',
 '表示式は力の数値候補εE′を含むが、この段階で物理的な力の同定、ばね秤の測定可能性、質量という呼称や係数の一意決定を完成扱いしない。零加速度の一例から質量を同定しない。',
 '検査では独立に各等号を破る数値と場、同じ引数接続、全38束縛、引用の作用範囲を対照する。保持した軌道の実二階微分は先行検査を再利用する。全実数・全関数域の有限認定や原文同義性の自動証明とはしない。',
 '旧422主張・旧意味規約・証拠を保持する。新しい基本記号は本文二箇所への参照だけであり、数式・量化・条件付き書換え・表示は既存概念から合成する。',
]

def definitions():
    text=''.join('r '+n+'[] a.\n' for n in REFERENCES)
    beta=k('soy',k('tc'),k('eisxt'));square=k('shv',beta,beta);cube=k('shv',square,beta)
    point=v('point');coordinates=[coord(point,a) for a in ROLES]
    E=[app(app(v('electricfield'),k(a)),*coordinates) for a in ROLES[:3]]
    B=[app(app(v('magneticfield'),k(a)),*coordinates) for a in ROLES[:3]]
    ratio=k('shv',k('eisxt'),k('sjd',k('tc')))
    mixed=(E[0],k('shv',beta,k('bf',E[1],k('shv',ratio,B[2]))),k('shv',beta,k('bd',E[2],k('shv',ratio,B[1]))))
    middle=[k('shv',v('charge'),x) for x in mixed]
    left=[k('shv',k('shv',v('mass'),power),v(n)) for (n,t),power in zip(ACCEL,(cube,square,square))]
    domain=both(k('s45',k('tc'),k('eisxt')),k('bc',ZERO,k('eisxt')),valid(point),*(k('ba',x) for x in [v('charge'),*E,*B]))
    text+=define('elq',SETTING,both(domain,k('ba',v('mass')),k('bg',ZERO,v('mass')),*(k('ba',x) for x in args(ACCEL)),*(k('sca',l,m) for l,m in zip(left,middle))))
    newpoint=k('ek5i',k('tc'),k('eisxt'),k('eisxz'),point)
    newE=[app(app(v('newelectric'),k(a)),*[coord(newpoint,b) for b in ROLES]) for a in ROLES[:3]]
    text+=define('elr',PAIR,both(domain,valid(newpoint),*(k('ba',x) for x in newE),*(k('sca',m,k('shv',v('charge'),n)) for m,n in zip(middle,newE))))
    text+=define('els',PAIR,both(k('elq',*args(SETTING)),k('elr',*args(PAIR)),k('ek74',*args(SETTING))))
    text+=define('elt',PAIR,op('y',both(k('ek63',*args(PAIR)),k('ek66',*args(PAIR))),op('z',k('elb',*args(SETTING)),k('els',*args(PAIR)))))
    text+=content('elu',quantified('f',BOUND,op('y',k('ek63',*shared()),k('els',*shared()))))
    p=v('point');who=k('rd');paper=k('eirf');scope=k('eisxg');intro=k('eisyp');display=k('eisyq')
    text+=content('elv',both(k('zd3',intro,who,quote('ek7s'),quote('elk'),quote('elu'),scope,p),k('eiswm',intro,who,k('eisym'),quote('elk'),paper,p),k('eisch',k('eisyo'),quote('elk'),scope,p),k('eisox',display,quote('elu'),p),k('uf',who,intro,display,p),k('ue',intro,display,p),op('u',op('e',intro,display))))
    text+='d elw[] f[j s[k elv[]]].\n'
    text+=define('elx',[],both(k('eir3',intro,who,paper,quote('elw'),k('ri')),k('ue',k('eisym'),intro,k('ri')),op('u',op('e',k('eisym'),intro))))
    return text

@lru_cache(None)
def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX
    assert not(set(MEANINGS)|set(REFERENCES))&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='elx',arguments=[]))]
    added=doc['declarations'][len(old['declarations']):]
    prim={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[],meaning_ja=REFERENCES[d['name']]) for d in added if d['kind']=='primitive'}
    basis=dict(status='same_electron_six_equalities_mass_rewrite',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=prim,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[INDEX]).document
    ann=json.loads(read('data/electron-transformed-dynamics-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode()))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
