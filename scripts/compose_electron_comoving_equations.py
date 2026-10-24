"""Connect initial rest equations, chosen origins, and the seven transformations."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_limits import ROOT,R,v,call as k,app,op,both,quant as q,lam
from scripts.compose_material_relative_frame import define
from scripts.compose_point_particle_dynamics import SETTING,PROFILES,ACCEL,REST,VECTOR,args,coord,ROLES,ZERO,ONE
from scripts.compose_electron_rest_law_claim import FUTURE
from scripts.compose_material_velocity import POINT,DOMAIN,CURVE,valid,equalpoints
from scripts.compose_field_equations import FIELD,REGION
from scripts.compose_doppler_infinity import quantified
from scripts.compose_relativity_conjecture import content
from scripts.compose_two_postulates import quote

def read(path):return (ROOT/path).read_text(encoding='utf-8')
PARENT='examples/v014/einstein-electron-coordinate-claim.noema';PARENT_BASIS='data/electron-coordinate-claim-basis-v1.json'
FULL='examples/v014/einstein-electron-comoving-equations.noema';CORE='examples/v014/electron-comoving-equations-core.noema'
BASIS='data/electron-comoving-equations-basis-v1.json';ANNOTATIONS='data/electron-comoving-equations-identifiers-v1.json';INDICES=(419,420)
EXTRA=[('newrecord','a'),('newelectric',FIELD),('newmagnetic',FIELD)]+[('new'+n,t) for n,t in PROFILES+ACCEL]
PAIR=SETTING+EXTRA
ATPOINT=PAIR+[('location',POINT)]
MIX=[('light',R),('speed',R),('offset',POINT),('electric',FIELD),('magnetic',FIELD)]
REMAINDER=[('velocity',PROFILES[0][1]),('initial',R),('acceleration',R)]
SMALL=[('domain',DOMAIN)]+REMAINDER
REFERENCES={
 'eisx6':'u0246–u0249の同じ共動系kの座標時刻τの表記。原刊918頁の括弧と記号一覧を採り、電子テキストM0406のtとM0409のτ脱落との違いを照合記録に保つ。',
 'eisx7':'同じ共動系での同じ電子の座標ξ,η,ζの順序付き表記。値と軸順は同じ物理設定から射影する。',
 'eisya':'同じ共動系での電場第一成分X′の表記。座標ξ又はKのXと同一視しない。',
 'eisyb':'同じ共動系での電場第二成分Y′の表記。',
 'eisyc':'同じ共動系での電場第三成分Z′の表記。',
 'eisyd':'u0246の既出の仮定と相対性原理から直後の三式を明白として導入する箇所。',
 'eisye':'u0247の同じ共動系での三運動方程式M0408の表示箇所。',
 'eisyf':'u0248第一文のwobeiによる同じ共動系の記号説明箇所。',
 'eisyg':'u0248第二文の両系の原点の対応を追加で指定する箇所。',
 'eisyh':'u0248第二文で第三節と第六節の変換式の適用を述べる箇所。',
 'eisyi':'u0249の時空四式と電場三式M0413の表示箇所。',
 'eisyj':'u0249で用いる同じVとvに対する正の係数βの表記。以前の具体的な系間速度を流用せずsoy(tc,eisxt)へ結ぶ。',
 'eisyk':'u0249で用いる同じ正の光速度Vの表記。値は既存tcへ結ぶ。',
}
MEANINGS={
 'ek6x':'指定した旧二場の電気側混合s6iを、同じ原点ずれを保つ逆写像ek5jで引き戻した新座標の電場関数。実測場との同定は別条件であり、ここでは関数を構成する。',
 'ek6y':'同じ原点ずれを持つ逆写像ek5jによる旧場領域の逆像。新旧の座標を数値のまま同一視しない。',
 'ek6z':'u0245と同じKの設定・共動系・出来事・両履歴・瞬間静止を保持し、独立に指定した新電磁二場・電荷記録・三速度関数・三加速度を同じkのek3vへ結ぶ。電荷・低速慣性質量・全単位尺度は共有する。新三式と場変換の真理は前提に含めない。',
 'ek62':'選んだ同じkの未指定だった四原点ずれeisxzの全成分が零であるという追加条件。Kの四原点に対するkの四原点の選択を表す。',
 'ek63':'同じ両系の物理設定ek6zに、後から追加する同じkの四原点選択ek62を結ぶ。指定出来事は両系で時刻零・空間原点となる。',
 'ek64':'独立に指定したkの実際の電場が、同じ旧二場を混合・逆変換したek6xと新領域全体で一致する。単一時点への数値一致や新電場の定義による循環ではない。',
 'ek65':'同じ旧領域の一点で、実際の座標対応ek5iによる新四座標がs46の四式を満たし、新電場の三値が同じ旧点の(X,β(Y−vN/V),β(Z+vM/V))となる。七式の左右と同じ出来事を共有する。',
 'ek66':'同じ物理的な両系の設定について、新領域全体の電場同定ek64と、旧領域の全有効四点での七変換式ek65を述べる。電子の原点一箇所だけに限定しない。',
 'ek7a':'同じ速度関数の初期一次式に対する残差を、初期からの時間差で割った関数。初期値と加速度を同じ時刻に固定し、穿孔した右側領域で用いる。',
 'ek7b':'同じ初期時刻が元の時間域の両側内点であり、正の時間差から近づくek7aの極限が零となる。直後の速度変化がaΔτ+o(Δτ)であるという読み。有限区間の厳密な一次式や誤差ゼロを要求しない。',
 'ek7c':'同じkの実二階微分と実電場に三式μa=εEを課し、同じ三速度の右微分ek32と初期一次式の剰余ek7bを合わせる。加速度や電場が全時間一定とはしない。',
 'ek7d':'表記に用いるkの物理設定。ek3vと同じ電子・出来事・kを固定し、指定点を同じ自由な四原点ずれに結ぶ。量を別の系や出来事から採らない。',
 'ek7e':'同じ設定の新座標時刻τの射影。',
 'ek7f':'同じ設定の同じ場所と時刻での新電場第一成分の射影。',
 'ek7g':'同じ設定の同じ場所と時刻での新電場第二成分の射影。',
 'ek7h':'同じ設定の同じ場所と時刻での新電場第三成分の射影。',
 'ek7i':'既存の正の根の規約soyによる、同じtcと瞬間速度eisxtの係数β。',
 'ek7j':'同じ光速度tcを返す量の射影。',
 'ek7k':'ξ,η,ζ、τ、新電場三成分、同じμとε、βとV、kの表記を物理設定と各射影へ結ぶ。原刊の七つの記号一覧を保持する。',
 'ek7l':'同じ評価状況に、両系の物理設定と追加の原点選択ek63を持つ共同証人があるという設定内容。運動三式と電場変換は存在の前提にはしない。',
 'ek7m':'同じ原点選択をした物理設定の存在ek7lと、その全設定で同じkの初期三式ek7cが成立するという内容。未知の加速度を初めから運動式で定義しない。',
 'ek7n':'前の同じ静止時の法則ek35、同じ相対性原理eifj、u0245の同じ共動配置の瞬間静止ek6rを、後続で明示する原点設定ek7lの下で一つの推論の前提内容にまとめる。引用された前提の真理の証明とは区別する。',
 'ek7o':'著者が同じ前提ek7nから同じkの初期三式ek7mが従うと述べ、その同じ内容を明白として提示する。上の仮定への照応、相対性原理の呼称、式表示と本文順序を結ぶ。',
 'ek7p':'三運動式への導入と表示ek7oを伝える断定的メッセージ。',
 'ek7q':'u0246–u0247の導入と三式を同じ著者・論説へ帰属し、前の瞬間静止の文に続ける主張419。',
 'ek7r':'wobeiの記号説明を同じ表示三式へ接続し、同じkでの数量と座標の意味を指定する。',
 'ek7s':'同じ原点を選ぶ両系の全物理設定ek63に対し、同じ全域の七変換式ek66を要求する内容。新電場が変換関数へ同定されることを帰結側に保持する。',
 'ek7t':'同じ著者が四原点の対応を追加で仮定として採用し、u0245の同じ座標選択を引き継ぐと提示する。新しい別のkへの変更ではない。',
 'ek7u':'第三節の最終座標変換と第六節の最終場変換の参照を保ち、同じ追加設定ek7lから全変換の適用ek73を述べ、そこから表示する七式ek7sを導く提示。全適用と表示の範囲を区別し、旧節の具体的なkや速度を現在の設定へ代入しない。',
 'ek7v':'記号説明、追加の原点選択、変換の適用と七式の表示を本文順序と各箇所の区別を保って統合する。',
 'ek7w':'u0248–u0249の説明・追加設定・変換を伝える断定的メッセージ。',
 'ek7x':'同じ著者・論説へu0248–u0249を帰属し、直前の三運動式に続ける主張420。',
 'ek7y':'同じ旧二場の磁気側混合s6jを、同じ原点ずれを保つ逆写像ek5jで引き戻した新座標の磁場関数。第六節の全変換の適用に用い、七式の表示には追加しない。',
 'ek7z':'独立に指定したkの実磁場が、同じ旧二場の磁気側混合と逆変換によるek7yと新領域全体で一致する。',
 'ek72':'同じ設定での全時空・電場変換ek66と磁場変換ek7zを結ぶ、第三節と第六節の変換全体の適用内容。表示する七式と区別する。',
 'ek73':'同じ原点を選ぶ両系の全物理設定に対し、第三節と第六節の全変換ek72が成り立つという内容。続く七式だけに適用範囲を縮めない。',
}
LIMITS=[
 'u0246–u0249を原刊918頁の一続きの導入・三式・記号説明・原点選択・七式として読む。電子テキストM0406はtだが原刊はτ、M0409はτを落としているが原刊はξ,η,ζ,τ,X′,Y′,Z′である。固定原文とMathMLを変更せず、ここでは原刊のτを採ると明示する。',
 '直後・小さいτは、u0248の原点選択の下で同じ出来事から正の時間差で近づく初期運動として読む。三式の加速度はその時点の実二階微分で、速度の初期一次式の剰余をo(Δτ)で保持する。有限時間区間全体に三式を厳密適用する読み、有限の最小時間粒、全区間の静止や一定加速度は採らない。',
 '同じ電子eisxh・出来事eisxv・瞬間速さeisxt・k=eisxy・局所新履歴eisx2/eisx3をu0245から引き継ぐ。新電磁二場と電荷記録・三速度関数・三加速度は共同の証人として独立に選び、実際の物理的帰属と微分をek3vで要求する。Kに固定されたek34/ek4pをkの設定へ流用しない。',
 '同じ符号付き非零電荷、低速慣性質量、整合した長さ・時間・質量・力・電磁単位と尺度を両系で共有するという原文の無係数の式の読み。μを移動時の縦横の質量又は電気量に替えず、今のKでの速度を低速に制限しない。',
 'u0248の追加選択によって初めて同じkの四原点ずれを全て零にする。u0246の小τはこの後続の明示選択と一群で解釈する。u0245の旧主張や規約の自由な原点ずれは変更しない。',
 '新電場は独立した物理場であり、変換関数として最初から定義しない。μa=εEと新電場の変換一致は帰結側に置く。場の変換は新領域全体、七式は旧領域の全有効四点を扱い、電子が置かれた原点一箇所だけに縮めない。',
 'M0413は時空四式と電気側三式だけを表示する。一方、直前の第三節と第六節の変換が成り立つという主張は磁場三式を含む全適用ek73として保持し、そこから七式ek7sを取り出す。未表示の磁場三式を表示内容へ追加せず、全適用からは落とさない。βは正の1/√(1−v²/V²)、V=tc>0、0≤v<Vである。',
 '上の仮定は同じek35、相対性原理は同じeifj、第三節の最終四式はejeh、第六節の最終場変換はejvmを参照する。後二者は原節への参照であり、その具体的な旧k=zbmや速度zb7を現在のk,vへ代用しない。原理からの帰結は著者に帰属する推論zcとして保持し、処理系が物理的真理を証明したとはしない。',
 '後続u0250以降のKへの変換とu0244の法則の答えへの接続、第十節見出しの緩い加速はまだ別の作業である。検査成功と全文の意味判断を区別する。',
]
BOUND=[(('oldpoint' if n=='point' else n),t) for n,t in PAIR if n not in ('frame','context','electricconversion','event')]
def shared():return args(PAIR,frame=k('ra'),context=v('point'),electricconversion=ONE,point=v('oldpoint'),event=k('eisxv'))
def new_values():
    result=dict(frame=k('eisxy'),region=k('ek6y',k('tc'),k('eisxt'),k('eisxz'),v('region')),electricfield=v('newelectric'),magneticfield=v('newmagnetic'),chargerecord=v('newrecord'),domain=k('eisx2'),curve=k('eisx3'),point=k('ek5i',k('tc'),k('eisxt'),k('eisxz'),v('point')))
    result.update({n:v('new'+n) for n,t in PROFILES+ACCEL});return dict(zip((n for n,t in SETTING),args(SETTING,**result)))
def new_args(fields):return [new_values()[n] for n,t in fields]

def definitions():
    text=''.join('r '+n+'[] a.\n' for n in REFERENCES)
    inverse=lam('location',POINT,k('ek5j',v('light'),v('speed'),v('offset'),v('location')))
    text+=define('ek6x',MIX,k('s6h',k('s6i',v('light'),v('speed'),v('electric'),v('magnetic')),inverse),FIELD)
    text+=define('ek7y',MIX,k('s6h',k('s6j',v('light'),v('speed'),v('electric'),v('magnetic')),inverse),FIELD)
    text+=define('ek6y',MIX[:3]+[('region',REGION)],k('s6g',v('region'),inverse),REGION)
    text+=define('ek6z',PAIR,both(k('ek6n',*args(SETTING)),k('ek6o',*args(SETTING)),k('ek3v',*new_args(SETTING)),k('ek3r',*new_args(REST))))
    text+=define('ek62',[],both(*(k('sca',coord(k('eisxz'),a),ZERO) for a in ROLES)))
    text+=define('ek63',PAIR,both(k('ek6z',*args(PAIR)),k('ek62')))
    transformed=k('ek6x',k('tc'),k('eisxt'),k('eisxz'),v('electricfield'),v('magneticfield'))
    text+=define('ek64',PAIR,k('ejs3',v('newelectric'),transformed,new_values()['region']))
    location=v('location');mapped=k('ek5i',k('tc'),k('eisxt'),k('eisxz'),location)
    electric=k('s6i',k('tc'),k('eisxt'),v('electricfield'),v('magneticfield'))
    text+=define('ek65',ATPOINT,both(equalpoints(mapped,k('s46',k('tc'),k('eisxt'),location)),*(k('sca',app(app(v('newelectric'),k(a)),*(coord(mapped,b) for b in ROLES)),app(app(electric,k(a)),*(coord(location,b) for b in ROLES))) for a in ROLES[:3])))
    text+=define('ek66',PAIR,both(k('ek64',*args(PAIR)),q('f','location',POINT,op('y',k('ejsj',location,v('region')),k('ek65',*args(ATPOINT))))))
    text+=define('ek7z',PAIR,k('ejs3',v('newmagnetic'),k('ek7y',k('tc'),k('eisxt'),k('eisxz'),v('electricfield'),v('magneticfield')),new_values()['region']))
    text+=define('ek72',PAIR,both(k('ek66',*args(PAIR)),k('ek7z',*args(PAIR))))
    moment=v('time');initial=v('initial');delta=k('bf',moment,initial)
    residual=k('bf',k('bf',app(v('velocity'),moment),app(v('velocity'),initial)),k('shv',v('acceleration'),delta))
    text+=define('ek7a',REMAINDER,lam('time',R,k('shv',residual,k('sjd',delta))),PROFILES[0][1])
    positive=lam('time',R,both(k('ba',moment),app(v('domain'),moment),k('bg',initial,moment)))
    text+=define('ek7b',SMALL,both(k('senz',v('domain'),initial),k('ba',v('acceleration')),k('sjr',positive,k('ek7a',*args(REMAINDER)),initial,ZERO)))
    nv=new_values();tau=coord(nv['point'],ROLES[3])
    text+=define('ek7c',PAIR,both(k('ek3t',*new_args(VECTOR)),k('ek32',*new_args(FUTURE)),*(k('ek7b',nv['domain'],nv[n],tau,nv[a]) for (n,t),(a,s) in zip(PROFILES,ACCEL))))
    text+=define('ek7d',SETTING,both(k('ek3v',*args(SETTING)),op('e',v('frame'),k('eisxy')),op('e',v('matter'),k('eisxh')),op('e',v('event'),k('eisxv')),equalpoints(v('point'),k('eisxz'))))
    text+=define('ek7e',SETTING,coord(v('point'),ROLES[3]),R)
    for name,axis in zip(('ek7f','ek7g','ek7h'),ROLES[:3]):text+=define(name,SETTING,app(app(v('electricfield'),k(axis)),*(coord(v('point'),a) for a in ROLES)),R)
    text+=define('ek7i',SETTING,k('soy',k('tc'),k('eisxt')),R)
    text+=define('ek7j',SETTING,k('tc'),R)
    p=v('point');who=k('rd');paper=k('eirf');scope=k('eisxg');intro=k('eisyd');display=k('eisye');explain=k('eisyf');origin=k('eisyg');transform=k('eisyh');shown=k('eisyi')
    scalar=[('eisx6','ek7e'),('eisya','ek7f'),('eisyb','ek7g'),('eisyc','ek7h'),('eisxj','ek37'),('eisxl','ek4b'),('eisyj','ek7i'),('eisyk','ek7j')]
    text+=content('ek7k',both(*(k('eiswy',k(n),'r[p ek7d]','r[p '+selector+']',paper,scope,p) for n,selector in scalar),k('eiswz',k('eisx7'),'l[a][k yn[] k yo[] k yp[]]','r[p ek7d]','r[p ek4a]',paper,scope,p),k('eisd4',explain,who,k('eisx4'),k('eisxy'),paper,p)))
    text+=content('ek7l',quantified('g',BOUND,k('ek63',*shared())))
    text+=content('ek7m',both(op('t',k('ek7l'),p),quantified('f',BOUND,op('y',k('ek63',*shared()),k('ek7c',*shared())))))
    text+=content('ek7n',both(*(op('t',k(n),p) for n in ('ek35','eifj','ek6r','ek7l'))))
    text+=content('ek7o',both(k('zc',intro,who,quote('ek7n'),quote('ek7m'),scope,p),k('uh',intro,who,quote('ek7m'),scope,p),k('zdg',intro,who,quote('ek7m'),scope,p),k('eisra',intro,who,paper,k('eisxc'),quote('ek4f'),quote('ek7n'),scope,p),k('eisch',k('eiscg'),quote('eifj'),scope,p),k('eisox',display,quote('ek7m'),p),k('uf',who,intro,display,p),k('ue',intro,display,p),op('u',op('e',intro,display))))
    text+='d ek7p[] f[j s[k ek7o[]]].\n'
    text+=define('ek7q',[],both(k('eir3',intro,who,paper,quote('ek7p'),k('ri')),k('ue',k('eisxx'),intro,k('ri')),op('u',op('e',k('eisxx'),intro))))
    text+=content('ek7r',both(op('t',k('ek7k'),p),k('uf',who,explain,display,p),k('ue',display,explain,p)))
    text+=content('ek7s',quantified('f',BOUND,op('y',k('ek63',*shared()),k('ek66',*shared()))))
    text+=content('ek73',quantified('f',BOUND,op('y',k('ek63',*shared()),k('ek72',*shared()))))
    text+=content('ek7t',both(k('ug',origin,who,quote('ek7l'),scope,p),k('eisra',origin,who,paper,k('eisxw'),quote('ek6k'),quote('ek7l'),scope,p)))
    text+=content('ek7u',both(k('zc',transform,who,quote('ek7l'),quote('ek73'),scope,p),k('uh',transform,who,quote('ek73'),scope,p),k('zc',transform,who,quote('ek73'),quote('ek7s'),scope,p),k('uh',transform,who,quote('ek7s'),scope,p),k('eisov',transform,who,k('eisms'),quote('ejeh'),paper,p),k('eisov',transform,who,k('zno'),quote('ejvm'),paper,p),k('eisox',shown,quote('ek7s'),p),k('uf',who,transform,shown,p)))
    nodes=('eisyf','eisyg','eisyh','eisyi')
    text+=content('ek7v',both(*(op('t',k(n),p) for n in ('ek7r','ek7t','ek7u')),*(k('ue',k(a),k(b),p) for a,b in zip(nodes,nodes[1:])),*(op('u',op('e',k(a),k(b))) for i,a in enumerate(nodes) for b in nodes[i+1:])))
    text+='d ek7w[] f[j s[k ek7v[]]].\n'
    text+=define('ek7x',[],both(k('eir3',explain,who,paper,quote('ek7w'),k('ri')),k('ue',display,explain,k('ri')),op('u',op('e',display,explain))))
    return text

@lru_cache(None)
def build():
    old=parse(read(PARENT));assert len(old['statements'])==419
    assert not(set(MEANINGS)|set(REFERENCES))&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol=n,arguments=[])) for n in ('ek7q','ek7x')]
    added=doc['declarations'][len(old['declarations']):]
    prim={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[],meaning_ja=REFERENCES[d['name']]) for d in added if d['kind']=='primitive'}
    basis=dict(status='same_comoving_initial_dynamics_origins_and_seven_transformations',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=prim,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=list(INDICES)).document
    ann=json.loads(read('data/electron-coordinate-claim-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode()))
    ann['entries'] += [dict(symbol=n,role='designation',forms=[dict(text=s,language='de',role='printed_identifying_form')]) for n,s in [('eisx6','τ'),('eisx7','(ξ,η,ζ)'),('eisya','X′'),('eisyb','Y′'),('eisyc','Z′'),('eisyj','β'),('eisyk','V')]]
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
