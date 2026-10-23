"""Compose a physical applicability caveat and an unattained-boundary forecast."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_planar_shape_limit import ROOT,read
from scripts.compose_ether_dispensability import VIEW,VIEW_CODE
from scripts.compose_material_shape_dimensions import SETTING
from scripts.compose_solid_sphere_geometry import bind
from scripts.compose_shape_contraction import SHAPE
from scripts.compose_rod_methods import history
from scripts.compose_material_relative_frame import define
from scripts.compose_relativity_conjecture import content
from scripts.compose_two_postulates import quote
from scripts.compose_limits import R,v,call as k,app,op,both,quant as q

PARENT='examples/v014/einstein-planar-shape-limit.noema';PARENT_BASIS='data/planar-shape-limit-basis-v1.json'
FULL='examples/v014/einstein-speed-boundary-forecast.noema';CORE='examples/v014/speed-boundary-forecast-core.noema'
BASIS='data/speed-boundary-forecast-basis-v1.json';ANNOTATIONS='data/speed-boundary-forecast-identifiers-v1.json';INDEX=335
DOMAIN='h['+R+'] c';NEAR='h['+R+' '+R+'] c';FAMILY='i[h['+R+'] e]'
PRIMITIVES={
 'eisoe':([('view','a'),('base','d'),('alternative','d')],'alternativeが、viewという同じ理論的な記述規約においてbaseから比較する物理的に許容された状況である。単なる論理的無矛盾や数式の定義域とは分ける。理論の許容範囲全体への関係であり、実験済みの状況一覧や所望の値を持つ状況だけを選ばない。対象の同一性・全物質点・尺度・実際の量の値は合成側で結ぶ。'),
 'eisof':([('view','a'),('considerations','i[e]'),('family',FAMILY),('parameter',R),('reference','d')],'同じviewの下で、considerationsという考察をfamilyのparameterへの適用として解釈する際に、量・測定・対象への参照を保持した意味ある物理的適用がある。型が合うこと、文字列を評価できること、式の真理だけを適用の成立としない。閉じたfamilyはどの数値を動かすかを固定し、他の考察への適用に交換しない。否定はその範囲での適用の不成立であり、言語一般の無意味や全ての理論の否定ではない。'),
 'eisog':([('node','a'),('author','a'),('topic','a'),('primary',VIEW_CODE),('addition',VIEW_CODE),('scope','a'),('reference','d')],'authorがnodeで、同じtopicについてprimaryを述べるのに付随してadditionを補足的に提示する談話関係。両記述は同じtopicとreferenceへ適用する型を持つ。本筋への付記という位置付けを保ち、因果的な帰結・論理的必要性・単なる同時発生とはしない。引用した内容の真理や既に立証済みであることはこの関係から導かない。'),
 'eisoh':([], 'u0116第三文の後半、同じ理論での光速の物理的役割を後続で示すという補足的な予告の箇所。'),
}
MEANINGS={
 'ejhk':'指定速度を引数として、同じ現在のK/kで測った同じ出来事の全対応四記録にφ=1の四式sreを要求する内容族。対応記録の非空性も保持し、適用限界を述べる際にどの速度とどの式の族を問題にするかを固定する。',
 'ejhl':'同じ任意形状の三軸寸法ejgtと、面状化の明示した極限ejhfを合わせた、ここまでの物理的考察の内容。別の論説や後続で未提示の主張へ参照を替えない。',
 'ejhm':'同じ見解について、全ての有効な超光速度には有限のβでsrdを満たす候補がなく、かつ同じ考察ejhlを同じ四式族ejhkへ適用する意味ある物理的解釈eisofがないと述べる。後者を前者から自動推論せず共に主張する。',
 'ejhn':'指定領域と近傍族について、領域が非空で、全ての正の近傍指定に領域内の点があり、一方で各領域内の点はある近傍から外れるという非到達の端の役割。有限の上限への接近と全有限上限を超える増大に共通して適用する。無限大を実数の値として加えない。',
 'ejho':'同じ理論・同じ物体・基準文脈について、許容された代替状況で同じ全物質点が同じKと尺度の下に全点並進する正の速度の範囲。全物質点の所属を基準状況と双方向に保ち、別物体や測定済み標本へ替えない。',
 'ejhp':'同じ物体の物理的に許容された速度範囲ejhoが、全値で同じ正の光速Vより小さく、V直下の全正近傍でejhnの非到達の端の役割を持つ。有限βや単なる数値写像だけで物理的範囲を認定しない。',
 'ejhq':'有効な非負の比較速度の領域に対し、指定した全ての正の有限上限を超える近傍を使ったejhnの役割。無限に大きい速度を、全有限上限を超える端の記述として表し、実在する無限大速度の物体や実切断を要求しない。',
 'ejhr':'同じ論説の理論構成を表す見解について、非負速度の無限の端ejhqと同じ非到達の端の役割が、有限寸法の全適格物体の許容速度の光速境界ejhpにあるという内容。§4の物質的対象の範囲における物理的な上限の読み。',
 'ejhs':'同じ理論的見解についてejhrが後続の論説展開で明らかになるとeisdbで予告する。現在の成立をここで実行せず、願望や既に完了した実証へ替えない。',
 'ejht':'同じ著者の同じ論説の見解を一つに束縛し、超光速での適用の留保ejhmと、同じ見解についての予告ejhsを述べ、後者をübrigensに対応する補足として位置付ける第三文の内容。',
 'ejhu':'u0116第三文の留保と補足的予告ejhtを述べるメッセージ。',
 'ejhv':'第三文を同じ著者・論説へ帰属し、面状化を述べた第二文の後に置く。',
}
LIMITS=[
 'u0116第三文[391,634)を対象とする。超光速でわれわれの考察が意味を失うという留保と、同じ理論で光速が無限大速度の物理的役割を果たすことを後続で示すという補足的予告を分けて接続する。',
 'sinnlosは、同じ物理的考察を同じ四式族へ超光速で適用する解釈が成立しないという読み。実数の有限βがないという数値的条件とこの適用上の留保を共に述べ、数式の不成立だけから物理的不能や言語全体の無意味を導かない。',
 'physikalisch die Rolleは、§4の有限寸法を持つ物質的対象の、理論が許す有限な運動状態における到達不能な上限の役割として読む。光そのものがVで伝わることを否定せず、光・電磁場をこの剛体の許容状態の集合へ混ぜない。',
 '無限に大きい比較速度は全有限上限を超える端を指し、無限大を実数や実在する物体の速度にしない。同じ非到達の端の型ejhnを、物理的速度域のV直下の近傍と、非負比較速度域の全有限上限より上の近傍へ適用する。単なる再パラメータ化から物理的役割を導かない。',
 '許容された物理状況は理論の範囲全体への入力であり、有限の観測例から完全性を推定しない。許容域が非空で境界へ任意に近づけること、境界以上に状態がないことを予告の内容に含める。加速の実施や利用可能な実験装置の存在は加えない。',
 '同じ理論は先行eigjの論説内の理論構成とeiscvで同定する。未来の展開を指す既存eisdbを使い、予告内容の現実の成立や証明完了は要求しない。予告先を後続u0263だけへ限定せず、u0263のエネルギー式や質量条件をこの文へ補わない。',
 'übrigensは同じ見解についての補足的な提示として保持し、前半の数式上の留保から後半の物理的役割が論理的に証明されたという因果関係を付けない。第一人称複数は著者の論述を指すと読み、新たな共著者集団を補わない。',
 '新しい基本関係は理論的に許容される状況、記述の物理的適用、同じ主題への補足提示という一般的な関係である。速度域・上限・近傍・全物質点・同じ式族・参照・引用と予告は合成側で構成する。検査成功は意味同値や物理的真理の自動証明ではない。',
]

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+('a' if not fs else 'c')+'.\n' for n,(fs,_) in PRIMITIVES.items())
    speed=v('speed');light=k('tc');zero=k('bb','n p a b');view=v('view');ref=v('reference');event=v('event');first=v('first');second=v('second')
    pair=both(k('eiyx',event,first,k('ra'),k('zb6')),k('eiyx',event,second,k('zbm'),k('zb6')))
    one='i[value '+R+']['+k('bb','n p b b')+']'
    rules=both(bind(('event','first','second'),'a','g',pair),bind(('event','first','second'),'a','f',op('y',pair,k('sre',first,second,light,speed,one))))
    text+='d ejhk[speed '+R+'] e[b point['+rules+']].\n'
    text+=content('ejhl',both(*(op('t',k(n),v('point')) for n in ('ejgt','ejhf'))))
    impossible=q('f','beta',R,op('y',k('ba',v('beta')),op('u',k('srd',light,speed,v('beta')))))
    inapplicable=op('u',k('eisof',view,quote('ejhl'),'r[p ejhk]',speed,ref))
    text+=define('ejhm',VIEW,q('f','speed',R,op('y',both(k('ba',speed),k('bg',light,speed)),both(impossible,inapplicable))))
    member=lambda x:both(k('ba',x),app(v('domain'),x))
    nonempty=q('g','point',R,member(v('point')))
    approach=q('f','scale',R,op('y',k('sbg',v('scale')),q('g','sample',R,both(member(v('sample')),app(v('near'),v('scale'),v('sample'))))))
    excluded=q('f','inside',R,op('y',member(v('inside')),q('g','away',R,both(k('sbg',v('away')),op('u',app(v('near'),v('away'),v('inside')))))))
    text+=define('ejhn',[('domain',DOMAIN),('near',NEAR)],both(nonempty,approach,excluded))
    body=v('body');base=v('base');alt=v('alternative')
    same=q('f','point','a',op('z',k('eirh',body,v('point'),base),k('eirh',body,v('point'),alt)))
    allowed=q('g','alternative','d',both(k('eisoe',view,base,alt),same,k('eipf',*history(body,k('ra'),alt),speed)))
    text+=define('ejho',[('view','a'),('body','a'),('base','d')],'i[speed '+R+']['+both(k('sbg',speed),allowed)+']',DOMAIN)
    domain=k('ejho',view,body,base);near='i[scale '+R+' speed '+R+']['+both(k('sbg',v('scale')),k('ba',speed),k('bg',k('bf',light,v('scale')),speed),k('bg',speed,light))+']'
    text+=define('ejhp',[('view','a'),('body','a'),('base','d')],both(k('sbg',light),k('ejhn',domain,near),q('f','speed',R,op('y',both(k('ba',speed),app(domain,speed)),k('bg',speed,light)))))
    unbounded='i[speed '+R+']['+both(k('ba',speed),k('bc',zero,speed))+']'
    above='i[scale '+R+' speed '+R+']['+both(k('sbg',v('scale')),k('ba',speed),k('bg',v('scale'),speed))+']'
    text+=define('ejhq',[],k('ejhn',unbounded,above))
    theory=k('eiscv',view,k('eirf'),quote('eigj'),ref)
    physical=q('f','body','a',q('f','shape',SHAPE,op('y',k('ejgp',body,v('shape'),k('zb6')),k('ejhp',view,body,k('zb6')))))
    text+=define('ejhr',VIEW,both(theory,k('ejhq'),physical))
    text+=define('ejhs',VIEW,k('eisdb',view,'r[p ejhr]',k('eirf'),ref))
    whole=q('g','view','a',both(k('eiscv',view,k('eirf'),quote('eigj'),v('point')),k('ejhm',view,v('point')),k('ejhs',view,v('point')),k('eisog',k('eisoh'),k('rd'),view,'r[p ejhm]','r[p ejhs]',k('eisn5'),v('point'))))
    text+=content('ejht',whole);text+='d ejhu[] f[j s[k ejht[]]].\n'
    text+=define('ejhv',[],both(k('eir3',k('zia'),k('rd'),k('eirf'),quote('ejhu'),k('ri')),k('ue',k('zh7'),k('zia'),k('ri')),op('u',op('e',k('zh7'),k('zia')))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX;doc=deepcopy(old);doc['statements']=[]
    assert not (set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in old['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='ejhv',arguments=[]))];added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='superluminal_applicability_and_physical_boundary_forecast',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[INDEX]).document
    ann=json.loads(read('data/planar-shape-limit-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
