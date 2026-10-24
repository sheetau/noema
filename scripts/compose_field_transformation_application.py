"""Apply the final coordinate transformation to the same electromagnetic process."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_vacuum_field_domain import ROOT,read
from scripts.compose_field_equations import FIELD,REGION,ROLES,POINT
from scripts.compose_material_relative_frame import define
from scripts.compose_solid_sphere_geometry import bind
from scripts.compose_relativity_conjecture import content,evaluate
from scripts.compose_two_postulates import quote
from scripts.compose_limits import R,v,call as k,app,op,both,quant as q

PARENT='examples/v014/einstein-vacuum-equation-assumption.noema'
PARENT_BASIS='data/vacuum-equation-assumption-basis-v1.json'
FULL='examples/v014/einstein-field-transformation-application.noema'
CORE='examples/v014/field-transformation-application-core.noema'
BASIS='data/field-transformation-application-basis-v1.json'
ANNOTATIONS='data/field-transformation-application-identifiers-v1.json';INDEX=153
PRIMITIVES={
 'eispn':([('process','a'),('frame','a'),('electric',FIELD),('magnetic',FIELD),('region',REGION),('context','d')], '同じprocessの電磁的な事象・場の変化と作用を、frameの座標で指定したregionにおけるelectric/magneticの二成分場により記述するという物理的な帰属。過程は単一の事象又は文脈で一緒に扱う過程群でよく、光だけや一個の荷電粒子に限定しない。どの出来事が属するかは別の所属関係、場の物理的な意味と単位は既存規約へ結ぶ。この帰属だけでは場の方程式、変換則、実験の実施や別系での測定値を認定しない。数値関数が一致する無関係な過程を取り替えず、指定した過程の記述全体を都合のよい成功例へ縮めない。'),
 'eispo':([('event','a'),('process','a'),('context','d')], 'eventがcontextで記述する同じprocessの事象の全範囲に属する。別の過程の同時刻の事象や、変換式の成否で選別した観測だけとは区別する。文脈で対象とする全事象を指定する所属関係であり、各出来事の座標記録、場の値、測定の成功は別に接続する。未知の所属を偽と補わない。'),
 'eispp':([], '第六節で現在の二場znl/znmと領域znkを用いて記述する電磁過程群への参照。内容はeig3/eispnと同じ所属出来事・二系の座標へ別に結び、未説明の名称だけで過程の意味を代用しない。'),
 'eispq':([], 'u0157–u0158のM0291/M0292を合わせた変換後の六式の表示箇所。原刊907頁の四式と908頁の二式を一つの表示群として扱う。'),
 'eispr':([], 'u0159のwobeiとu0160のM0293で、直前の変換式に用いる同じβを指定する補足箇所。第三節の先行βの導入箇所とは別である。'),
}
MEANINGS={
 'ejte':'同じ過程がeig3の電磁過程であり、現在のK・二場・領域によって記述されるeispnを満たす。同じ文脈の場・単位の規約ejsyを共有する。',
 'ejtf':'同じ過程に属する一つの出来事と、一方の系の四座標記録を同じ状況のeiyxへ結ぶ。場の式や変換式が成立することを所属の選別条件に使わない。',
 'ejtg':'同じ過程に属する一つの出来事が、指定されたK記録とk記録を共に持つ。二つの別の出来事を片側ずつ合わせない。',
 'ejth':'現在の比較設定zb6で同じ電磁過程・場の規約と二系の全配置の運動eivzを共有する。所属出来事の範囲は非空で、全所属出来事に両系の記録が存在する。',
 'ejti':'指定された同じK/k記録対に係数1のssnを適用し、旧座標が新座標への速度−vのs46と全四成分で一致すること、同じ旧領域とその逆像への所属を結ぶ。全四値の有効性と正のVの定義域を保持する。',
 'ejtj':'ejthの同じ過程・範囲の全ての同一出来事記録対について、第三節の同じ現在の記録範囲と対応eiyz/eiy2/eiyyに属し、ejtiの同じ逆写像で場の引数を変更できることを要求する。',
 'ejtk':'直前の真空の六式の仮定ejs6を現在の比較設定zb6へ適用し、第三節の最終変換ejehと同じ電磁過程の記録・逆写像ejtjを合わせた、原文の書換えに用いる前提内容。発散条件は足さない。',
 'ejtl':'著者が同じ前提ejtkの下で直前の仮定ejs6を変換後の六式s6oへ書き換えると提示する。第三節で展開した最終変換ejehと、そこで導入した両系の座標・移動系の表記規約eiy6を同じ論説から参照する。',
 'ejtm':'著者が同じ範囲で、直前の変換式で用いるβを既存spqの同じ正の根の規約により指定する補足内容。',
 'ejtn':'変換を適用して式を得るejtl、表示群とs6oの内容対応、wobei以下のβの補足ejtmを、一つの文の順序と説明関係へ結ぶ。',
 'ejto':'u0156–u0160の変換の適用・六式・βの補足ejtnを述べるメッセージ。',
 'ejtp':'同じ著者と論説へ一文を帰属し、直前の仮定の成分説明eispmからの順序を保持する。旧文153の部分的な導出提示を置き換える。',
}
LIMITS=[
 'u0156–u0160を原刊907–908頁で一続きの文として読む。第三節の変換の適用、同じ電磁過程をそこで導入した速度vの系へ関係付ける操作、六式を得るという提示、wobeiとβまでを保持する。',
 '現在の過程群eisppを同じ二場・領域の物理的な記述へ結び、所属する全出来事を扱う。各出来事に両系の座標があり、同じ出来事の全記録対へ変換を適用する。式が成功する標本だけの範囲、別過程の記録、全実数四組の実測済みへ替えない。',
 '比較設定は既出zb6、K/kはra/zbm、速度vはzb7、Vはtcである。直前の仮定内容ejs6を同じ設定に適用する。先行第三節の最終四式ejehと、同じ移動系を含む表記規約eiy6を参照し、途中のφ付きの式を最終変換として流用しない。',
 '場の成分混合と引数の逆変換を分け、同じ速度−vの写像を両場と領域に使う。新座標を未変換の旧座標として代入せず、同じ出来事の四座標と全成分で結ぶ。現在の物理設定の正のvを保持し、負の速度は逆写像の演算に用いる。',
 '表示された混合成分は旧場の式の新変数による表現である。移動系での独立した物理的な力の定義や測定場への同定はu0161以降で扱い、ここでは同一視しない。',
 '六式はs6k/s6lの混合と逆写像、s6mの領域、s5yの六回転式を再利用する。βは既出spqの正の1/√(1−(v/V)²)で、同じV,vを保つ。改頁や式の配置は別の法則を追加しない。',
 '六回転式だけからは変換後の六式を一般に導けないという既存反例を保持する。真空の語から発散条件や全微分の仮定を黙って追加せず、zd3は著者の導出・書換え提示の帰属として扱う。有限例も原著者の一般的な導出の証明ではない。',
 '新しい基本関係は、同じ過程の二場による記述の帰属と、全所属出来事の指定である。残る三基本記号は過程群と二箇所の参照。物理的な語彙、座標測定、系の運動、式の計算、著者の提示は既存定義から構成する。',
 '旧文153以外の357主張と旧版・旧証拠・既判断を保持する。全実数や全関数域の有限列挙拒否を維持し、原文全体の意味判断は局所検査から分ける。',
]


def coordinates(record):return 'i[role a]['+k('zc6',record,v('role'))+']'


def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+('c' if fs else 'a')+'.\n' for n,(fs,_) in PRIMITIVES.items())
    process=v('process');ctx=v('context');event=v('event');lab=v('lab');own=v('own');pc=[('process','a'),('context','d')]
    text+=define('ejte',pc,both(k('eig3',process,ctx),k('eispn',process,k('ra'),k('znl'),k('znm'),k('znk'),ctx),k('ejsy',ctx)))
    text+=define('ejtf',[('process','a'),('event','a'),('tuple','a'),('frame','a'),('context','d')],both(k('eispo',event,process,ctx),k('eiyx',event,v('tuple'),v('frame'),ctx)))
    text+=define('ejtg',[('process','a'),('lab','a'),('own','a'),('context','d')],q('g','event','a',both(k('ejtf',process,event,lab,k('ra'),ctx),k('ejtf',process,event,own,k('zbm'),ctx))))
    member=k('eispo',event,process,ctx)
    complete=both(*(q('g','tuple','a',k('ejtf',process,event,v('tuple'),k(frame),ctx)) for frame in ('ra','zbm')))
    text+=define('ejth',pc,both(op('e',ctx,k('zb6')),k('ejte',process,ctx),k('eivz',ctx),q('g','event','a',member),q('f','event','a',op('y',member,complete))))
    V=k('tc');speed=k('zb7');negative=k('bf',k('bb','n p a b'),speed);old=coordinates(lab);new=coordinates(own)
    inverse=k('s46',V,negative,new);region=k('s6m',V,speed,k('znk'))
    comparisons=[k('sca',k('zc6',lab,k(a)),app(inverse,k(a))) for a in ROLES]
    text+=define('ejti',[('lab','a'),('own','a')],both(k('s45',V,speed),k('ssn',lab,own),k('ejsj',old,k('znk')),k('ejsj',new,region),*comparisons))
    selected=k('ejtg',process,lab,own,ctx)
    body=both(k('eiyz',lab),k('eiy2',own),k('eiyy',lab,own),k('ejti',lab,own))
    text+=define('ejtj',pc,both(k('ejth',process,ctx),bind(('lab','own'),'a','f',op('y',selected,body))))
    text+=content('ejtk',both(op('t',k('ejs6'),k('zb6')),evaluate('ejeh'),k('ejtj',k('eispp'),k('zb6'))))
    point=v('point');node=k('znq');author=k('rd');scope=k('zno')
    text+=content('ejtl',both(k('zd3',node,author,quote('ejtk'),quote('ejs6'),quote('s6o'),scope,point),*(k('eisov',node,author,k('eisms'),quote(n),k('eirf'),point) for n in ('ejeh','eiy6'))))
    text+=content('ejtm',k('uh',k('eispr'),author,quote('spq'),scope,point))
    nodes=('znq','eispq','eispr')
    text+=content('ejtn',both(evaluate('ejtl'),evaluate('ejtm'),k('eisox',k('eispq'),quote('s6o'),point),*(k('uf',author,k(a),k(b),point) for a,b in zip(nodes,nodes[1:])),*(k('ue',k(a),k(b),point) for a,b in zip(nodes,nodes[1:])),*(op('u',op('e',k(a),k(b))) for i,a in enumerate(nodes) for b in nodes[i+1:])))
    text+='d ejto[] f[j s[k ejtn[]]].\n'
    text+=define('ejtp',[],both(k('eir3',node,author,k('eirf'),quote('ejto'),k('ri')),k('ue',k('eispm'),node,k('ri')),op('u',op('e',k('eispm'),node))))
    return text


def build():
    old=parse(read(PARENT));assert len(old['statements'])==358
    assert not(set(PRIMITIVES)|set(MEANINGS))&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions())
    doc['statements']=deepcopy(old['statements']);doc['statements'][INDEX]=dict(kind='assert',body=dict(kind='call',symbol='ejtp',arguments=[]))
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='same_electromagnetic_process_final_transformation_and_beta',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[INDEX]).document
    ann=json.loads(read('data/vacuum-equation-assumption-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
