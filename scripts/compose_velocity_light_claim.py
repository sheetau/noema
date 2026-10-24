"""Present a light-speed specialization without a light-speed frame."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_velocity_deficit_claim import ROOT,read
from scripts.compose_material_relative_frame import define
from scripts.compose_relativity_conjecture import content
from scripts.compose_two_postulates import quote
from scripts.compose_limits import R,v,call as k,op,both,quant as q

PARENT='examples/v014/einstein-velocity-deficit-claim.noema';PARENT_BASIS='data/velocity-deficit-claim-basis-v1.json'
FULL='examples/v014/einstein-velocity-light-claim.noema';CORE='examples/v014/velocity-light-claim-core.noema'
BASIS='data/velocity-light-claim-basis-v1.json';ANNOTATIONS='data/velocity-light-claim-identifiers-v1.json';INDICES=(143,144)
MEANINGS={
 'ejqg':'正の光速度lightを用いる原刊の商(light+other)/(1+other/light)の実切断構成。分母と外側の除算を明示し、定義域はejqhで要求する。',
 'ejqh':'有効な実数light/other/result、正のlight、非零の1+other/lightの下でresultがejqgの値と等しい。結果がlightと等しいという第二の等号や、相手が光速未満という条件はこの商関係と分ける。',
 'ejqi':'0≤other<lightなら、同じ一次元合成式s3j(light,light,other)から構成した結果が原刊の簡約商ejqhを満たし、かつlightに等しい。式の一方の数値入力をlightに置き、実際の系速度をlightにする条件は加えない。',
 'ejqj':'同じ光速度tcに対し、任意の実入力otherについてejqiが成立するという表示式の一般内容。原刊の局所的なwは光速未満の合成相手、Uはその同じ合成の結果という束縛された役割として読む。既出の点の固定値zkq/zkpを無条件に代入しない。',
 'ejqk':'同じ現在の点・K/k・取得ejpaを保ち、点が正方向に光速度tcで動くこと、合成相手otherが0≤other<tcかつ実際の系速度zb7であることを要求する適用条件。点の速さzkq=tcを課し、zb7=tcは課さない。',
 'ejql':'同じ光速度の点の適用条件ejqkの下で、結果候補resultが同じ点のKでの実際の座標微分から得る速さejoiである。候補を演算結果へ等置する前の物理的な取得である。',
 'ejqm':'同じ取得ejqlに対して、物理的な入力順のs3g(tc,other,tc,result)、数値入力を交換したs4d(tc,other,result)、原刊の簡約商ejqh、result=tcを合わせる。入力の交換を系や観測上の役割の同一視へ替えない。',
 'ejqt':'現在状況zb6の同じ光速度の点と光速未満の系速度について、全てのother/result候補で、実際の速さ取得ejqlが成立すれば同じ値の交換前後の式と原刊の等式ejqmが成立するという適用内容。光速度の点や新たな光速の系が実在するという存在主張はしない。',
 'ejqu':'原刊表示式の数値的な一般内容ejqjと、同じ現在の速度の取得規則への条件付き適用ejqtを合わせる。零の合成相手は一般式に含むが、既存の正の相対運動に零方向を新設しない。',
 'ejqn':'同じ著者・第五節がzlmで、同じ一次元式に光速度を入れた一般形s4iから、全光速未満入力について光速度が不動点であるs4gを得ると提示する。',
 'ejqo':'同じ著者・第五節がzlnで、この場合の同じ特殊化s4iから、U=原刊の簡約商=Vというejquを得ると提示する。コロンと表示式を同じ帰結へ結ぶ。',
 'ejqp':'光速度が変化し得ないという帰結提示ejqnを述べるメッセージ。',
 'ejqq':'この場合の表示式への帰結提示ejqoを述べるメッセージ。',
 'ejqr':'光速度の不動点への帰結を同じ著者・論説へ帰属し、前の不足量による説明zllからzlmへの続きfernerを本文順序として保持する。',
 'ejqs':'同じ場合の表示式を得る提示を同じ著者・論説へ帰属し、zlmから表示式zlnへの本文順序と箇所の区別を保つ。',
}
LIMITS=[
 'u0145の二文とu0146/M0273を原刊906頁に照合する。光速度と光速未満の速度の合成、変化し得ないという全称的な不変性、fernerによる続き、この場合に得るという提示、コロン後の二つの等号を保持する。',
 '前の同方向の速度合成則の数式上の帰結として読む。光速未満の範囲は既存の0≤w<Vを保ち、符号付きの広い代数領域や任意方向へ無断に拡張しない。nicht geändert werden kannは全ての許容入力で同じ合成操作がVを保つという読みで、話者の知識・技術的能力の主張へ替えない。',
 '表示式のwはこの特殊化の合成相手、Uはその同じ合成結果の局所的な変数として束縛する。前段の実際の点の値zkq/zkpを無条件に流用しない。同じs3g/s3jの数値入力交換を用い、物理的な適用では点のk速度がV、系速度が光速未満の相手となる対応を明示する。',
 '適用条件は同じ点・両系・尺度・全現在履歴・座標微分と非負ノルムをejpa/ejoiへ結ぶ。点側の速さzkq=tcを置き、実際の系速度zb7=tcは置かない。光速の座標系やそのローレンツ係数を許容しない。適用の含意から、その場合の実在や前提の成立を導かない。',
 '元の正の相対運動はそのまま保つ。一方、式の一般的な0≤w<Vには零を含め、光速度に零を合成する境界も記述する。零速度に方向を与えたり、現在の物理設定を零速度へ拡張したりしない。',
 '固定電子転記M0273の分母1+w/vは原刊の1+w/Vと異なる。data/written-math-corrections-v1.jsonの既存訂正層を明示し、元のMathMLとハッシュは変更しない。簡約した商の本体もejqg/ejqhで明示する。',
 '商の成立とU=Vを別の関係として保持する。代数上はw≠−Vでも不変となるが、それを原文の光速未満の範囲へ混ぜない。w=−Vは分母零であり、U=Vだけでは商を成立させない。',
 '有限の対照・原刊訂正・既存の有理多項式証拠・全実数量化の列挙拒否と意味判断を区別する。新たな原始述語は追加せず、旧文143/144以外の354主張と過去の証拠を保存する。u0147以降とs5mの旧前提への接続は未完。',
]

def definitions():
    V,w,U=map(v,('light','other','result'));zero=k('bb','n p a b');one=k('bb','n p b b')
    den=k('bd',one,k('shv',w,k('sjd',V)))
    text=define('ejqg',[('light',R),('other',R)],k('shv',k('bd',V,w),k('sjt',den)),R)
    text+=define('ejqh',[('light',R),('other',R),('result',R)],both(*(k('ba',x) for x in (V,w,U)),k('bg',zero,V),op('u',k('sca',den,zero)),k('sca',U,k('ejqg',V,w))))
    result=k('s3j',V,V,w)
    text+=define('ejqi',[('light',R),('other',R)],op('y',k('s3s',V,w),both(k('ejqh',V,w,result),k('sca',result,V))))
    light=k('tc');ctx=v('context');point=v('point');ev=lambda n:'t['+k(n)+']['+point+']'
    text+=content('ejqj',both(k('ba',light),k('bg',zero,light),q('f','other',R,k('ejqi',light,w))))
    text+=define('ejqk',[('other',R),('context','d')],both(k('ejpa',ctx),k('s3i',k('zkc'),k('zkd'),k('zkq')),k('sca',k('zkq'),light),k('s3s',light,w),k('bg',zero,w),k('sca',w,k('zb7'))))
    text+=define('ejql',[('other',R),('result',R),('context','d')],both(k('ejqk',w,ctx),k('ejoi',U,ctx)))
    text+=define('ejqm',[('other',R),('result',R),('context','d')],both(k('ejql',w,U,ctx),k('s3g',light,w,light,U),k('s4d',light,w,U),k('ejqh',light,w,U),k('sca',U,light)))
    text+=content('ejqt',q('f','other',R,q('f','result',R,op('y',k('ejql',w,U,k('zb6')),k('ejqm',w,U,k('zb6'))))))
    text+=content('ejqu',both(ev('ejqj'),ev('ejqt')))
    author=k('rd');scope=k('eisoq')
    text+=content('ejqn',k('zc',k('zlm'),author,quote('s4i'),quote('s4g'),scope,point))
    text+=content('ejqo',k('zc',k('zln'),author,quote('s4i'),quote('ejqu'),scope,point))
    for name,body in (('ejqp','ejqn'),('ejqq','ejqo')):text+='d '+name+'[] f[j s[k '+body+'[]]].\n'
    for name,node,message,previous in (('ejqr','zlm','ejqp','zll'),('ejqs','zln','ejqq','zlm')):
        text+=define(name,[],both(k('eir3',k(node),author,k('eirf'),quote(message),k('ri')),k('ue',k(previous),k(node),k('ri')),op('u',op('e',k(previous),k(node)))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==356;doc=deepcopy(old);doc['statements']=[]
    assert not set(MEANINGS)&{d['name'] for d in old['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=deepcopy(old['statements'])
    for i,n in zip(INDICES,('ejqr','ejqs')):doc['statements'][i]=dict(kind='assert',body=dict(kind='call',symbol=n,arguments=[]))
    added=doc['declarations'][len(old['declarations']):]
    basis=dict(status='light_speed_specialization_and_same_point_application',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},replaced_partial_statements=list(INDICES),limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=list(INDICES)).document
    ann=json.loads(read('data/velocity-deficit-claim-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
