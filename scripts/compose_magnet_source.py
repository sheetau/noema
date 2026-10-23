"""Connect an active material magnet, its source fields and both comparison cases."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_magnetic_action import ROOT,read
from scripts.compose_conductor_cases import PREMISE as CONDUCTOR_PREMISE,FIELDS as CONDUCTOR_FIELDS,conclusion
from scripts.compose_field_equations import FIELD,REGION,POINT,ROLES
from scripts.compose_rest_force import AXES
from scripts.compose_material_relative_frame import define,args
from scripts.compose_limits import R,v,call as k,app,op,both,quant as q,ZERO

PARENT='examples/v014/einstein-magnetic-action.noema'
PARENT_BASIS='data/magnetic-action-basis-v1.json'
FULL='examples/v014/einstein-magnet-source.noema'
CORE='examples/v014/magnet-source-core.noema'
BASIS='data/magnet-source-basis-v1.json'
ANNOTATIONS='data/magnet-source-identifiers-v1.json'
SOURCE=[('body','a'),('frame','a'),('context','d')]+[(n,'a') for n in ('lengthunit','timeunit','electricunit','magneticunit','sourcecondition')]+[('electricfield',FIELD),('magneticfield',FIELD),('region',REGION)]
WITNESS=SOURCE+[('point',POINT),('magnetic',POINT)]
CONFIGURATION=[('body','a'),('context','d'),('sourcecondition','a')]
LOCAL=[(n,t) for n,t in SOURCE if n not in ('body','lengthunit','timeunit')]
CASES=[('left','a'),('lengthunit','a'),('timeunit','a')]+[(case+n,t) for case in ('first','second') for n,t in LOCAL]
EXTRA=[(case+n,t) for case in ('first','second') for n,t in LOCAL if n not in ('frame','context')]
PREMISE=CONDUCTOR_PREMISE+EXTRA
FIELDS=CONDUCTOR_FIELDS+EXTRA
MEANINGS={
 'eicq':'幾何学的な物体zmについて、同じ文脈・発生源条件の内部磁気源配置eirxと、その物体に由来する二成分場eirwを結ぶ。系・長さ時間単位・場単位・領域を共有し、物体の物質占有外にある有効な四座標で磁気側場をscb2により評価して、少なくとも一空間成分が非零である証人を要求する。単に外部磁場の中に物体があるだけでは成立しない。',
 'eicr':'eicqを満たす物体外の一点と磁気側場の三成分値が存在する、活動中の磁気源としての磁石の読み。点や場値を個体名へ固定しない。採用する例示範囲は外部に磁場を持つ磁石であり、完全遮蔽された配置や停止中の装置まで網羅する辞書的な分類ではない。内部の源配置・物理的帰属・非零な外部場をそれぞれ保持する。',
 'eics':'同じ左側物体と長さ・時間単位を、第一・第二の各評価系・文脈のeicrへ結ぶ。二場合の場関数・発生源条件・領域は別でよい。磁石の同一性から二系の電場や磁場の成分値が同じとは要求しない。',
 'eict':'導体と比較準備を含む既存eickへ、同じ左側物体が両場合で活動中の磁気源であるeicsを追加した比較前件。相対運動と運動/静止役割、導体の能力、物理的な準備を保持する。場や電流の一致を前件へ含めない。',
 'eicu':'磁石・導体を接続したeictの比較前件から、同じ右側物体の全断面電流履歴一致eibiへの条件内容。条件の物理的真理を処理系が導出するものではない。',
 'eicv':'eictの比較前件とeibiの電流一致を共に満たす二場合の内容。前件不成立でeicuだけが真の場合を、前件も満たす例として扱わない。現実に二試行を実施済みとは主張しない。',
}
PRIMITIVES={
 'eirw':(SOURCE,'指定物体の物質内の電荷・電流・磁気モーメントの状態を発生源として帰属した電気側・磁気側の成分場を、指定系・文脈・長さ時間単位・場単位・領域・発生源条件で与える。発生源条件は採用する初期/境界条件と、他の発生源・自由場からこの寄与を分ける規約を固定する。同じ場所に物体と場が共存するという意味ではない。場は電荷への電気的作用と速度依存の磁気的作用を定める物理量として読み、数値関数の名から帰属を推定しない。この寄与を全発生源を合わせた場と同一視せず、原文への適用時にその扱いを明示する。帰属の基本規約であり、場の方程式を解いた証明や実験実施を内包しない。'),
 'eirx':(CONFIGURATION,'指定物体が、その文脈と発生源条件の下で、物体に対して保持される磁化又は内部の電流配置による磁気源として作動する物理的な状態。磁化は物質内の磁気モーメントの巨視的な配置、内部電流は物体に対する電荷の循環・輸送として読む。外部磁場を通過するだけ、又は正味電荷を持つ物体の共通並進だけとは区別する。永久磁石の磁化と作動中の電磁石の電流のいずれも許し、鉄・棒形状・原子の古典的回転・永久性を一律の必要条件にしない。外部の非零場はこの記号で認定せず、合成で要求する。'),
}
LIMITS=[
 '磁石はこの導入で比較する活動中の外部磁気源として読む。数値的な強さの閾値や特定の材料を原文へ補わず、電源を切った装置や完全遮蔽した配置の一般分類まで同じ述語で主張しない。',
 'eirwは物体に帰属する場の寄与であり、導体や他の源の場も含む全場とは区別する。後続の相互作用では、どの寄与がどの力・電流へ関与するかを接続する必要がある。',
 '二場合の物理的な内部準備の対応は既存eirsが扱う。評価系を変えた場の成分や源条件のラベルの同一性をそれに代用しない。',
 '外部の一点の非零は場の存在の証人であり、周囲の全領域の形、全点での非零、力の非零、相互作用による電流の生成を意味しない。',
 '旧207主張と著者表示判断を保持する。例示の呼びかけ、通常の理解への帰属、電場・起電力・エネルギーの各内容と導入全体の判断は未完である。',
]

def case_args(case):
    return [v('left' if n=='body' else n if n in ('lengthunit','timeunit') else case+n) for n,_ in SOURCE]

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fields)+'] c.\n' for n,(fields,_) in PRIMITIVES.items())
    coords=[app(v('point'),k(n)) for n in ROLES]
    nonzero=[op('u',k('sca',app(v('magnetic'),k(n)),k('bb',ZERO))) for n in ROLES[:3]]
    text+=define('eicq',WITNESS,both(k('zm',v('body')),k('eirx',*args(CONFIGURATION)),k('eirw',*args(SOURCE)),
        op('u',op('e',v('lengthunit'),v('timeunit'))),
        k('znn',v('frame'),v('electricfield'),v('magneticfield'),v('region'),v('context')),
        k('eirn',v('frame'),v('electricfield'),v('electricunit'),v('context')),
        k('eirn',v('frame'),v('magneticfield'),v('magneticunit'),v('context')),
        app(v('region'),*coords),k('scb2',AXES,v('magneticfield'),v('point'),v('magnetic')),
        op('u',k('eiro',*[v(n) for n in ('body','frame','context','lengthunit','timeunit')],*coords)),
        op('x',nonzero[0],op('x',nonzero[1],nonzero[2]))))
    text+=define('eicr',SOURCE,q('g','point',POINT,q('g','magnetic',POINT,k('eicq',*args(WITNESS)))))
    text+=define('eics',CASES,both(*(k('eicr',*case_args(case)) for case in ('first','second'))))
    text+=define('eict',PREMISE,both(k('eick',*args(CONDUCTOR_PREMISE)),k('eics',*args(CASES))))
    text+=define('eicu',FIELDS,op('y',k('eict',*args(PREMISE)),conclusion()))
    text+=define('eicv',FIELDS,both(k('eict',*args(PREMISE)),conclusion()))
    return text

def build():
    old=parse(read(PARENT));doc=deepcopy(old);doc['statements']=[]
    assert not (set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in doc['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='magnet_source_and_case_connection',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,
        primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[]).document
    ann=json.loads(read('data/magnetic-action-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}

if __name__=='__main__':
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    print('Magnet source and comparison cases composed')
