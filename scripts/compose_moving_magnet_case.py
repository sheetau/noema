"""Compose the first conventional explanation of the induction example."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_interaction_example import ROOT,read,FIELDS as EXAMPLE
from scripts.compose_material_body_motion import FIELDS as MOTION,FAMILY as TRAJECTORIES
from scripts.compose_current_distribution import HISTORY,SCOPE,FAMILY
from scripts.compose_electric_response import FIELDS as LOCAL_ACTION
from scripts.compose_field_equations import POINT,ROLES
from scripts.compose_material_relative_frame import define,args
from scripts.compose_limits import R,F,v,call as k,app,op,both,quant as q,ZERO

PARENT='examples/v014/einstein-observable-contrast.noema'
PARENT_BASIS='data/observable-contrast-basis-v1.json'
FULL='examples/v014/einstein-moving-magnet-case.noema'
CORE='examples/v014/moving-magnet-case-core.noema'
BASIS='data/moving-magnet-case-basis-v1.json'
ANNOTATIONS='data/moving-magnet-case-identifiers-v1.json'
INDEX=209
AXES='l[a][k yn[] k yo[] k yp[]]'
BASE=EXAMPLE+[('lower',R),('upper',R)]+[(side+'members','h[a] c') for side in ('left','right')]+[(side+axis,TRAJECTORIES) for side in ('left','right') for axis in ('x','y','z')]+[('reference','d')]
RESULT=[('energyunit','a'),('energy',F),('sections',SCOPE),('cumulative',FAMILY),('current',FAMILY),('point',POINT),('electric',POINT),('section','a'),('orientation','a'),('time',R)]
FIELDS=BASE+RESULT
NEIGHBOR=[(n,t) for n,t in BASE if n in ('left','frame','context','lengthunit','timeunit','lower','upper','region')]
PRODUCTION=[(n,t) for n,t in BASE if n in ('process','left','frame','context','electricunit','electricfield','region')]
ELIGIBILITY=[(n,t) for n,t in BASE if n in ('process','left','right','frame','context','reference')]
ENERGY=[(n,t) for n,t in BASE if n in ('frame','context','lengthunit','timeunit','electricunit','electricfield','region')]+[('energyunit','a'),('time',R),('value',R)]
ENERGY_HISTORY=[(n,t) for n,t in ENERGY if n not in ('time','value')]+[('lower',R),('upper',R),('energy',F)]
CURRENT_POINT=HISTORY+[('section','a'),('orientation','a'),('time',R)]
COVER=MOTION+[('region',next(t for n,t in EXAMPLE if n=='region'))]
FIELD_POINT=[(n,t) for n,t in FIELDS if n in ('electricfield','region','point','electric')]
SCHEMA='i[h['+' '.join(t for _,t in LOCAL_ACTION)+'] c]'
RESPONSE=[(n,t) for n,t in FIELDS if n in ('process','right','frame','context','lengthunit','timeunit','electricunit','electricfield','magneticfield','region','chargeunit','lower','upper','sections','cumulative','current')]+[('local_action',SCHEMA)]
PRIMITIVES={
 'eisal':(NEIGHBOR,'指定系・文脈・長さ時間単位・区間で、このregionはleftの物質占有の周囲として選んだ空間的範囲を各時刻に与える。物体外に広がり物体を取り囲む近傍の範囲であり、任意の遠い一点や単なる名前ではない。範囲の広さは場を記述する設定で固定し、球形・一定半径・有限体積・全点での非零場を一律に要求しない。物体の運動に伴う領域の変化を許す。場や電流の生成、他物体の包含はこの基礎的な空間帰属とは別に要求する。'),
 'eisam':(PRODUCTION,'同じprocessでleftを発生源として扱う状態と運動の下で、指定系・状況・単位・範囲のelectricfieldが物理的に生じているという生成への帰属。数値場が指定されているだけ、既存の無関係な外場との共存だけから認定しない。entstehtをこの過程に伴う場の生成と読むための一般的な源と場の関係で、全空間の電場が直前まで厳密に零だったこと、スイッチ投入、遅延時間の特定を要求しない。磁石の種類・運動静止・非零場の証人は合成で別に要求する。'),
 'eisan':(ENERGY,'同じ系・状況・座標単位・領域で記述するelectricfieldの電気的な場の状態に、指定時刻のエネルギー量valueをenergyunitで帰属する。量は場から物質への仕事や他のエネルギー形態との交換の収支で扱う物理的量で、単位は力とその方向の変位の積による仕事の基準へ整合させる。場の領域全体に対応する量であり、都合のよい一点の値、磁石の機械的運動エネルギー、磁気側まで合わせた全エネルギーへ替えない。場が零の状態を電気的な場エネルギーの零基準とする。数値関数の名札や実測記録の存在だけからこの帰属を認めない。特定の単位系の密度公式、時間一定性、保存則の導出はこの帰属自体には含めない。'),
 'eisao':(RESPONSE,'同じprocess・系・状況において、指定した電気側の場がright内の可動電荷への電気的作用を通じ、指定の全断面の輸送量・電流履歴を物理的応答として生むという帰属。単なる共存や時間的先行ではなく、源からの電気的な駆動と導体の応答を同じ物理的説明の機構として扱う。生成に関与する局所作用と輸送の記録は渡された閉じたlocal_action型に従い、同じright・frame・context・座標単位・chargeunit・electricunit・二場・region・区間・断面範囲・履歴を共有する。該当する担体の位置はrightの物質領域内で、場評価点・時刻・作用・断面の輸送への接続を欠かさない。応答全体への帰属であり一つの担体の一力だけを全体の説明に代用しない。他の原因の併存や零交差を許し、場を除けば全可能状態で必ず電流が消えるという必要性、刺激以外を全て二値化したモデル、微視的機構の証明、実験実施を要求しない。履歴の妥当性・非零の電流・周囲にある導体部分の空間対応は合成で別に要求する。'),
 'eisap':(ELIGIBILITY,'同じ例process・二物体について、この系・状況がreferenceで考える配置・回路・準備・記述尺度の下で許容する事例である。単に現に観測済みの組や結果が成功した事例だけを選ばず、同じ例を条件文として考える全候補範囲を定める。運動と静止、場の生成、エネルギー、電流生成はこの範囲の条件へ先取りしない。'),
 'eisaq':([], '固定原文einstein-1905:u0003[550,770)の、磁石運動・導体静止の場合を電場とそのエネルギーおよび電流生成で説明する一文の箇所。'),
}
MEANINGS={
 'eidm':'同じ例の許容事例eisapと磁石・導体・結合設定eic2を保ち、同じ系・状況・区間の磁石の運動eiagと導体の静止eiahを結ぶ条件文の前件。生成する場・エネルギー・電流を前件へ入れない。',
 'eidn':'同じ物体の全物質点・全区間履歴eiadの下で、全成員の全区間内時刻の座標が指定region内にある。選んだ一点だけを導体の部分の全範囲とせず、物質点の同一性と座標・時刻を保つ。',
 'eido':'有効な四座標が指定領域にあり、同じ電気側場の評価scb2が与える三成分の少なくとも一つが非零である証人。負の場も許し、全点での非零とはしない。',
 'eidp':'指定時刻とエネルギー値が有効な実数で、値が非負であり、同じ場・領域・単位への物理的エネルギー帰属eisanを持つ。数値の妥当性だけからエネルギーと認めない。',
 'eidq':'正の長さの全時刻区間で、同じ場・領域・エネルギー単位とenergy関数の各値へeidpを要求する。あるエネルギー値を持つという読みであり、全時刻で同じ値だという追加条件はない。',
 'eidr':'妥当な全断面電流履歴の指定断面・向き・区間内時刻で、同じ符号付き電流の絶対値が零を超える。正方向限定や任意の観測閾値を補わず、他時刻での零交差を許す。',
 'eids':'同じ源の場が磁石周囲で生じること、全導体部分のその領域への包含、非零の電場の証人、場エネルギーの全時刻帰属、同じ導体の電流履歴と非零の電流の証人、および局所作用型eicaに従う物理的生成への帰属を結ぶ。',
 'eidt':'eidmの磁石運動・導体静止の条件なら、エネルギー単位と履歴、全断面の電流履歴、場と電流の証人が存在してeidsを満たすという条件。個別の数値・場の一様性・定常性・常時非零を原文へ補わない。',
 'eidu':'同じ二物体と例について、referenceで許容する全候補の設定にeidtを課す条件内容。具体的な実験を実施した主張や一標本の確認とはしない。',
 'eidv':'前二文の同じ磁石eisaa・導体eisab・例eisacを保つ、第一の場合の条件的説明の閉じた内容。',
 'eidw':'同じ論説の通常の理解eisahの下でeidvの説明が採られるというeisaiの帰属。後二文は先行する通常の理解の具体化として読み、帰属時に物理内容を実行しない。',
 'eidx':'第一の場合の説明への帰属eidwを主張の力で提示するメッセージ。例への呼びかけの指示や、物理実験の成功報告へ取り替えない。',
 'eidy':'同じ著者・論説がeidxをこの一文で提示し、既存ufで先行する対照文を説明するnämlichの談話関係と本文順序を結ぶ。説明の論理的十分性や物理的真理を帰属から導かない。',
}
LIMITS=[
 '通常の理解による二説明の第一の場合として読む。原文の文頭条件は同じ評価系の磁石運動・導体静止であり、絶対運動ではない。',
 '原文の例のマクロな物体・材料と回路の準備を保つ。場の領域はこの例の導体部分を含む磁石周囲の記述範囲であり、全宇宙・任意の配置への無条件な物理定理へ拡張しない。',
 'entstehtはこの源の過程に伴う場の生成、gewisser Energiewertは各時刻で定まる場エネルギーとして読む。原文にない初期の完全な零場、定常性、密度公式、特定単位系は補わない。',
 '電流生成は同じ場の電気的作用に基づく物理的な応答帰属として読む。既存eicdの全介入解で応答が反転する強い因果対照へ狭めない。基本的な物理帰属の意味規約を明示し、微視的法則の導出は翻訳の要件としない。',
 '一文の意味判断と全段落の完了を分ける。第一文と逆の場合の一文および段落全体の通読判断は別に残る。',
]

def motion(side):return [v(side if n=='body' else side+n if n in ('members','x','y','z') else n) for n,_ in MOTION]
def history():return [v('right' if n=='body' else 'chargeunit' if n=='quantityunit' else n) for n,_ in HISTORY]
def energy_args():return [v(n) if n not in ('time','value') else v('instant') if n=='time' else app(v('energy'),v('instant')) for n,_ in ENERGY]

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+('a' if not fs else 'c')+'.\n' for n,(fs,_) in PRIMITIVES.items())
    text+=define('eidm',BASE,both(k('eisap',*args(ELIGIBILITY)),k('eic2',*args(EXAMPLE)),k('eiag',*motion('left')),k('eiah',*motion('right'))))
    coords=[app(app(v(axis),v('member')),v('instant')) for axis in ('x','y','z')]
    inside=app(v('region'),*coords,v('instant'))
    text+=define('eidn',COVER,both(k('eiad',*args(MOTION)),q('f','member','a',q('f','instant',R,op('y',both(app(v('members'),v('member')),k('lg',v('lower'),v('upper'),v('instant'))),inside)))))
    coords=[app(v('point'),k(n)) for n in ROLES]
    nonzero=[op('u',k('sca',app(v('electric'),k(n)),k('bb',ZERO))) for n in ROLES[:3]]
    text+=define('eido',FIELD_POINT,both(app(v('region'),*coords),k('scb2',AXES,v('electricfield'),v('point'),v('electric')),op('x',nonzero[0],op('x',*nonzero[1:]))))
    text+=define('eidp',ENERGY,both(k('zzba',v('time')),k('zzba',v('value')),op('u',k('zzbg',v('value'),k('bb',ZERO))),k('eisan',*args(ENERGY))))
    text+=define('eidq',ENERGY_HISTORY,both(k('zzbg',v('lower'),v('upper')),q('f','instant',R,op('y',k('lg',v('lower'),v('upper'),v('instant')),k('eidp',*energy_args())))))
    current=app(app(v('current'),v('section'),v('orientation')),v('time'))
    text+=define('eidr',CURRENT_POINT,both(k('eibf',*args(HISTORY)),app(v('sections'),v('section'),v('orientation')),k('lg',v('lower'),v('upper'),v('time')),k('eibk',current,k('bb',ZERO))))
    text+=define('eids',FIELDS,both(k('eisal',*args(NEIGHBOR)),k('eisam',*args(PRODUCTION)),k('eidn',*motion('right'),v('region')),
        k('eido',*args(FIELD_POINT)),k('lg',v('lower'),v('upper'),app(v('point'),k('zc7'))),k('eidq',*args(ENERGY_HISTORY)),k('eidr',*history(),v('section'),v('orientation'),v('time')),
        k('eisao',*args(RESPONSE[:-1]),'r[p eica]')))
    result=k('eids',*args(FIELDS))
    for n,t in reversed(RESULT):result=q('g',n,t,result)
    text+=define('eidt',BASE,op('y',k('eidm',*args(BASE)),result))
    content=k('eidt',*[v('point' if n=='reference' else n) for n,_ in BASE])
    for n,t in reversed(BASE):
        if n not in ('left','right','process','reference'):content=q('f',n,t,content)
    text+='d eidu[left a right a process a] e[b point['+content+']].\n'
    text+='d eidv[] e[k eidu[k eisaa[] k eisab[] k eisac[]]].\n'
    text+='d eidw[] e[b point['+both(k('eisah',k('eisak'),k('eirf'),v('point')),k('eisai',k('eisak'),'r[k eidv[]]',v('point')))+']].\n'
    text+='d eidx[] f[j s[k eidw[]]].\n'
    text+=define('eidy',[],both(k('eir3',k('eisaq'),k('rd'),k('eirf'),'r[k eidx[]]',k('ri')),k('uf',k('rd'),k('eisaj'),k('eisaq'),k('ri')),k('ue',k('eisaj'),k('eisaq'),k('ri')),op('u',op('e',k('eisaj'),k('eisaq')))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX;doc=deepcopy(old);doc['statements']=[]
    assert not(set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in doc['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='eidy',arguments=[]))]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='moving_magnet_case_under_usual_account',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=[],statement_indices=[INDEX]).document
    ann=json.loads(read('data/observable-contrast-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}

if __name__=='__main__':
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    print('Moving-magnet explanation appended')
