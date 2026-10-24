"""Prepare mean flux and a nonvacuous finite-boundary intensity limit."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_amplitude_specialization import ROOT,read
from scripts.compose_material_relative_frame import define,args
from scripts.compose_doppler_infinity import GRAPH,quantified
from scripts.compose_limits import R,F,v,call as k,app,op,both,quant as q,lam

PARENT='examples/v014/einstein-amplitude-specialization.noema';PARENT_BASIS='data/amplitude-specialization-basis-v1.json'
FULL='examples/v014/einstein-radiative-intensity.noema';CORE='examples/v014/radiative-intensity-core.noema'
BASIS='data/radiative-intensity-basis-v1.json';ANNOTATIONS='data/radiative-intensity-identifiers-v1.json'
FLUX=[(n,R) for n in ('coefficient','nx','ny','nz','ex','ey','ez','hx','hy','hz')]
AVERAGE=FLUX+[('profile',F)]+[(n,R) for n in ('lower','upper','integrated','intensity')]
PLANE=FLUX+[(n,R) for n in ('meansquare','amplitude','intensity')]
MEANINGS={
 'ekjf':'係数coefficientを掛けたn・(E×H)の実数式。法線の向きと電気・磁気三成分の外積順序を保つ、符号付きの面積当たりエネルギー流の候補式。物理的対応と単位は呼出側で指定する。',
 'ekjg':'同じ三成分係数と方向のekjfに、同じ時刻での共通波形profileの二乗を掛けた時間関数。EとHが同じprofileを持つモデルの瞬間流の候補。profileを常に正弦波や平均二乗1/2と仮定しない。',
 'ekjh':'有限の正長区間におけるekjgの実数Riemann積分integratedをsedeで結び、integrated=(upper−lower)*intensityとする平均流。方向は単位ベクトル、係数は正。平均の対象、積分値、区間と平均値を共有する。物理的測定記録や周期条件はここには含めない。',
 'ekji':'同じcoefficient,n,E,Hのekjfへ指定されたmeansquareを掛ける実数式。共通波形の二乗平均がmeansquareと別に確認された場合の平均流候補。',
 'ekjj':'単位法線、横電場とH=n×Eというseaj、同じ電場の非負振幅seal、正の変換係数、非負のmeansquareを保ち、intensityを同じekjiへ結ぶ平面波の数値条件。実在場や測定との対応は未追加。',
 'ekjk':'正面接近の旧余弦−1にした一般二乗振幅式ekiiへ、同じ正の変換係数と波形二乗平均を掛ける実数式。旧実数角φ=πと物理的接近の接続は呼出側の責務。',
 'ekjl':'incident*(light+speed)/(light−speed)という接近側の平均流候補。許容域は呼出側で0<speed<lightとする。後退側の逆比や振幅そのものの平方根比へ替えない。',
 'ekjm':'正のlight、0<speed<light、非負incident及びreceivedの下でreceived=ekjlとする二変数グラフの点条件。零incidentを許すが、その発散は含意しない。境界speed=lightの有限値を与えない。',
 'ekjn':'同じgraphの有効な有限実数点(input,output)が、有限boundaryの正のradius幅の厳密な左近傍sesrにある条件。',
 'ekjo':'同じboundary,radiusの左近傍に同じgraphの点がある。入力と出力を共に存在量化する。',
 'ekjp':'有効な有限boundaryの任意の正のradiusの左近傍ごとにekjoを要求する集積条件。空の関係や境界から離れた関係を発散と認めない。',
 'ekjq':'同じgraphの一点が指定左近傍にあるなら、その出力が同じboundを厳密に超えるという局所含意。',
 'ekjr':'有効なboundary,bound及び正のradiusを保持し、全input/outputでekjqを要求する。多価関係の都合のよい出力だけを選ばない。',
 'ekjs':'同じgraphとboundaryの指定boundに対して、ekjrを満たす正のradiusがある。radiusはboundに依存して選ぶ。',
 'ekjt':'同じgraphの左集積ekjpと、任意の有限boundごとのekjsを連言する有限左境界への正の発散。無限実数を追加せず、単一のradiusが全boundに通用するとも述べない。',
 'ekju':'正のlightとincidentに対し、light*incident/(2*(incident+max(bound,0)))という正の左近傍幅の候補。incidentが固定された正の入射平均流であるときに使う。',
 'ekjv':'正のlight,incidentと有限bound、0<speed<lightについて、ekjuの近傍内にある同じspeedでekjlがboundを超える局所証明条件。全実数の発散自体と区別する。',
 'ekjw':'同じlightとincidentを固定して、入力speedと出力receivedについてekjmを返す二実数関係。速度ごとに入射流を選び直さない。',
 'ekjx':'正のlightと正のincidentに対して、同じekjwがlightへの左側発散ekjtを満たすという数値的内容。光源・波・観測者・単位や仮定的な著者主張はまだ含まない。',
}
LIMITS=[
 'u0201のunendlich intensivを、局所平面波モデルの単位横断面積を通るエネルギー流の周期平均が非有界になるという読みへ接続するための数式群。今回は原始関係と著者主張を増やさず、全文判断も増やさない。',
 '方向付き流はκ n・(E×H)、共通波形p(t)ならκ n・(E0×H0)p(t)²、その平均は実数積分を区間長で割る。κは選んだ力・エネルギー・長さ・時間の単位への正の換算係数であり、SIのε0やGaussian単位の定数を無説明に代入しない。物理的役割と同じ単位系の対応は次の統合に残す。',
 '横波seajならn・(E0×H0)=|E0|²=A²となる。平均二乗mが確認されたとき平均流はκmA²。正弦の一周期でm=1/2であることを、この区間平均の定義だけから断定しない。位相率と周期が速度により変わることも保持して後で接続する。',
 '接近側は正速度+xに対し旧法線−x・旧角φ=π。先行の一般式のcosφ=−1から二乗比(1+r)/(1−r)となる。前文φ=0の後退側と混同しない。数値式を物理的な接近の完全な定義の代わりにしない。',
 '固定した正の入射平均流Iに対し0<v<VでI′=I(V+v)/(V−v)と読む。任意の有限上限ごとに十分小さい正の近傍幅を選び、全てのグラフの出力を検査する。空域、境界から離れた域、一つだけ大きい出力、零振幅を発散の証拠にしない。',
 '既存の負無限遠発散ekfmとは入力境界が異なるため、既存sesrとekffを再利用して有限左境界の関係的発散を構成する。有限標本で実数の全域量化を代用しない。',
 '残るのは、校正された同じ源・波・観測者・二系・単位と平均流の物理的対応、周期平均と共通の係数、旧角πによる接近、速度ごとに補助量を選べる同一背景の非空な関係、光速での反実仮想を境界として読む明示、展開済みの式からの帰結及び著者帰属、u0201全文判断。',
]

def definitions():
    zero=k('bb','n p a b');one=k('bb','n p b b');two=k('bb','n p c b')
    mul=lambda x,y:k('shv',x,y);add=lambda x,y:k('bd',x,y);sub=lambda x,y:k('bf',x,y)
    positive=lambda x:both(k('ba',x),k('bg',zero,x))
    coef,nx,ny,nz,ex,ey,ez,hx,hy,hz=args(FLUX)
    dot=add(mul(nx,sub(mul(ey,hz),mul(ez,hy))),add(mul(ny,sub(mul(ez,hx),mul(ex,hz))),mul(nz,sub(mul(ex,hy),mul(ey,hx)))))
    text=define('ekjf',FLUX,mul(coef,dot),R)
    profile=app(v('profile'),v('time'))
    text+=define('ekjg',FLUX+[('profile',F)],lam('time',R,mul(k('ekjf',*args(FLUX)),mul(profile,profile))),F)
    lo,hi,integrated,I=map(v,('lower','upper','integrated','intensity'))
    text+=define('ekjh',AVERAGE,both(*(k('ba',v(n)) for n,t in AVERAGE if t==R),positive(coef),k('sca',k('seag',nx,ny,nz),one),k('bg',lo,hi),k('sede',lo,hi,k('ekjg',*args(FLUX),v('profile')),integrated),k('sca',integrated,mul(sub(hi,lo),I))))
    text+=define('ekji',FLUX+[('meansquare',R)],mul(v('meansquare'),k('ekjf',*args(FLUX))),R)
    text+=define('ekjj',PLANE,both(positive(coef),k('ba',v('meansquare')),k('bc',zero,v('meansquare')),k('seaj',nx,ny,nz,ex,ey,ez,hx,hy,hz),k('seal',ex,ey,ez,v('amplitude')),k('ba',I),k('sca',I,k('ekji',*args(FLUX),v('meansquare')))))
    V,speed,incident,received=map(v,('light','speed','incident','received'))
    text+=define('ekjk',[(n,R) for n in ('light','speed','coefficient','meansquare','amplitude')],mul(mul(coef,v('meansquare')),k('ekii',V,speed,sub(zero,one),v('amplitude'))),R)
    text+=define('ekjl',[(n,R) for n in ('light','speed','incident')],mul(incident,mul(add(V,speed),k('sjd',sub(V,speed)))),R)
    text+=define('ekjm',[(n,R) for n in ('light','incident','speed','received')],both(k('ekev',V,speed),k('ba',incident),k('bc',zero,incident),k('ba',received),k('bc',zero,received),k('sca',received,k('ekjl',V,speed,incident))))
    g=[('graph',GRAPH)];boundary=[('boundary',R)];radius=[('radius',R)];bound=[('bound',R)];xy=[('input',R),('output',R)]
    G,B,d,M,x,y=map(v,('graph','boundary','radius','bound','input','output'))
    text+=define('ekjn',g+boundary+radius+xy,both(k('ekff',G,x,y),k('sesr',B,d,x)))
    text+=define('ekjo',g+boundary+radius,quantified('g',xy,k('ekjn',G,B,d,x,y)))
    text+=define('ekjp',g+boundary,both(k('ba',B),q('f','radius',R,op('y',positive(d),k('ekjo',G,B,d)))))
    text+=define('ekjq',g+boundary+bound+radius+xy,op('y',k('ekjn',G,B,d,x,y),k('bg',M,y)))
    text+=define('ekjr',g+boundary+bound+radius,both(k('ba',B),k('ba',M),positive(d),quantified('f',xy,k('ekjq',G,B,M,d,x,y))))
    text+=define('ekjs',g+boundary+bound,both(k('ba',B),k('ba',M),q('g','radius',R,k('ekjr',G,B,M,d))))
    text+=define('ekjt',g+boundary,both(k('ekjp',G,B),q('f','bound',R,op('y',k('ba',M),k('ekjs',G,B,M)))))
    maximum=k('szi',k('bg',M,zero),zero,M)
    text+=define('ekju',[(n,R) for n in ('light','incident','bound')],mul(mul(V,incident),k('sjd',mul(two,add(incident,maximum)))),R)
    text+=define('ekjv',[(n,R) for n in ('light','incident','bound','speed')],both(positive(V),positive(incident),k('ba',M),k('ekev',V,speed),k('sesr',V,k('ekju',V,incident,M),speed),k('bg',M,k('ekjl',V,speed,incident))))
    text+=define('ekjw',[('light',R),('incident',R)],'i[speed '+R+' received '+R+']['+k('ekjm',V,incident,speed,received)+']',GRAPH)
    text+=define('ekjx',[('light',R),('incident',R)],both(positive(V),positive(incident),k('ekjt',k('ekjw',V,incident),V)))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==383
    assert not set(MEANINGS)&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']
    added=doc['declarations'][len(old['declarations']):]
    basis=dict(status='mean_flux_and_finite_left_boundary_dependencies',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[]).document
    ann=json.loads(read('data/amplitude-specialization-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
