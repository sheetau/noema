"""Keep signed charge fixed on material portions and transport it with a small rigid body."""
from copy import deepcopy
from functools import lru_cache
import json,re
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_limits import ROOT,R,v,call as k,app,op,both,quant as q,lam
from scripts.compose_material_relative_frame import define
from scripts.compose_material_body_motion import FIELDS as HISTORY,FAMILY
from scripts.compose_field_equations import POINT,ROLES
from scripts.compose_local_density import BALL
from scripts.compose_additive_charge import sets
from scripts.compose_doppler_infinity import quantified

def read(path):return (ROOT/path).read_text(encoding='utf-8')
PARENT='examples/v014/einstein-convective-charge-setting.noema';PARENT_BASIS='data/convective-charge-setting-basis-v1.json'
FULL='examples/v014/einstein-attached-material-charge.noema';CORE='examples/v014/attached-material-charge-core.noema'
BASIS='data/attached-material-charge-basis-v1.json';ANNOTATIONS='data/attached-material-charge-identifiers-v1.json'
LABELS='h[a] c';PARTS='h['+LABELS+'] c';TOTAL='h['+LABELS+'] '+R
COORDS=[(axis,FAMILY) for axis in ('x','y','z')]
PULLBACK=[('members',LABELS)]+COORDS+[('time',R),('space',BALL)]
FIXED=HISTORY+[('distribution','a'),('chargeunit','a'),('parts',PARTS),('total',TOTAL)]
MATERIAL=FIXED+[('event','a'),('time',R),('part',LABELS)]
SPATIAL=FIXED+[('event','a'),('time',R),('space',BALL)]
SMALL=HISTORY+[('scope','a'),('threshold',R)]
PAIR=[('left','a'),('right','a'),('time',R),('threshold',R)]+COORDS
ALL=FIXED+[('scope','a'),('threshold',R)]
PHYSICAL=[('body','a'),('distribution','a'),('kind','a'),('frame','a'),('event','a'),('time',R),('part',LABELS),('lengthunit','a'),('timeunit','a'),('quantityunit','a'),('amount',R),('context','d')]
SCALE=[('scope','a'),('frame','a'),('lengthunit','a'),('threshold',R),('context','d')]
PRIMITIVES={
 'eisvy':(PHYSICAL,'同じbodyを構成して履歴を通じて追跡する物質点の集合partについて、その同じ物質部分に帰属するdistributionのkindの保有量が、frameのeventと座標時刻timeにおいてamountであるという物理的帰属。partは同じbodyの全物質点の範囲へ制限して解釈し、範囲外のラベルで部分を区別しない。空間に固定した箱や各時刻で別の物質へ付け替えた部分ではなく、同じ物質ラベルの部分を扱う。量の種類・長さ時刻量単位・contextを保持し、電気量zorではeirm/eisvxと同じ二極性と校正尺度を使う。単なる部分集合上の任意関数、空間的な共存、全体の量の偶然一致ではこの帰属を代用しない。量の値は各時刻で変わり得る基礎入力であり、不変性や剛性、量の非零、実測済み、保存則はこの関係単独から導かない。'),
 'eisvz':(SCALE,'scopeの対象を小さい空間的広がりとして扱う際に、同じframe・lengthunit・contextで用いる比較上限がthresholdであるという尺度規約。比較対象となる物理的配置や記述の分解尺度を先に固定し、個々の候補の大きさに合わせて成功するまで上限を増やさない。対象の実際の全点間距離がこの上限未満かは別の数値条件で要求する。単位の呼び名だけ、任意の有限上界、寸法の零や点状性を小ささの代用にしない。一般の文脈依存の空間サイズの比較であり、特定粒子種・特定数値・特定の波長比・全物理効果の無視可能性を含意しない。'),
}
MEANINGS={
 'ekxn':'指定した物質点の全範囲内で、全点の所属が一致する二つの物質部分。範囲外のラベルで部分を区別しない。既存seooの一般的な集合構成を個体ラベルへ適用する。',
 'ekxo':'指定した物質点範囲内で共通の成員がない二つの物質部分。',
 'ekxp':'空部分を含み、和と差で閉じ、同じ物質点範囲内で同じ部分を同様に受け入れる部分族。全ての部分の有限総量や可算加法性は要求しない。',
 'ekxq':'ekxpの物質部分族に与えられた符号付き有限加法的総量。空部分は零、同じ部分は同値、互いに素な二部分の和の量は二量の和。時刻や場所を引数にしない一つの関数だが、これだけでは実際の物質への量の帰属を意味しない。',
 'ekxr':'同じekxqの部分族に属する物質部分と、その有効な実数の総量を結ぶ。',
 'ekxs':'指定時刻の同じ三座標族でspaceに位置する、同じmembers内の物質点だけを選ぶ逆像。三成分と時刻を同じ物質点から構成する。空間に固定された部分を物質ラベルへ固定した部分と取り違えない。',
 'ekxt':'同じ物体・分布・系・出来事・時刻・単位の指定物質部分に対し、同じekxrの値を電気量zorの物理的保有量eisvyへ結ぶ。その時刻の量の帰属であり、一時刻だけで不変を認定しない。',
 'ekxu':'同じ空間領域の物質逆像ekxsにekxtを適用し、その同じ量を空間保有量eisvxへ結ぶ。空間領域に含まれる電荷は、同じ時刻にそこにある物質部分の電荷であり、別の全体量又は別時刻の量を流用しない。',
 'ekxv':'同じ非空の完全な物体履歴と校正座標に、同じ物質点全範囲を選んだ局所電荷分布zqn、全体を含む符号付き部分量関数ekxqを結ぶ。正長区間の全時刻で、同じ出来事の全適格物質部分にekxt、全適格空間逆像にekxuを要求する。同じ部分量関数を全時刻に共有し、総電荷だけの一定や内部での電荷交換を不変な付着として認めない。',
 'ekxw':'同じ二物質点の同時刻の有効な三座標を取り、正のthresholdについて距離二乗eigwがthresholdの二乗未満であるという局所寸法条件。距離の符号や座標差一成分だけで判定しない。',
 'ekxx':'同じ全物質点履歴の剛性eigyと、文脈で先に定めた小ささの尺度eisvzを共有する。正長区間の全点対・全時刻でekxwを要求する小さい剛体の条件。物体全体の静止、球形、三標識点、非零の寸法を補わない。',
 'ekxy':'同じ物体・評価系・尺度・全成員・全区間の座標族について、不変に付着した電荷分布ekxvと小さい剛体ekxxを同時に要求する。電荷の一定を剛性だけから推論せず、別物体の剛性や別区間の付着を組み合わせない。',
}
LIMITS=[
 'u0232第二文の条件に向けた依存群である。408主張・旧規約・既存判断を保持し、著者提示や全単位判断を追加しない。複数の小さい担体への分布の分解と前段ekxmとの対応、イオン/電子、Lorentz理論の電磁的基礎という条件付き位置付け、冒頭全体の本文統合が残る。',
 '不変な付着を、同じ物質部分の電荷が全時刻で一定であり、その物質の移動で空間分布が移るという読みで構成する。全体だけ一定でも内部で電荷が交換されれば受け入れない。固定部分量関数は仮定する内容の一部であり、Maxwell方程式又は相対性原理から保存を証明したとはしない。',
 'この層のdistributionは一つの物体に対応する局所成分である。複数のイオン/電子の全体を一個の剛体へ狭めない。前段の場の全分布との合成・分解は後続で明示する。物体の全成員には零電荷部分も含め、量の零から物質点や領域の不在を導かない。',
 '物体の全体部分を量の定義域に含める有限総量のモデルである。全ての任意部分集合や可算加法性は要求しない。空間への逆像が適格な全領域を扱い、都合のよい固定箱だけを選ばない。空間の箱を固定しても中の物質が変わるため、その箱の量の時間不変は要求しない。',
 '剛性は指定された評価系と同時性・尺度での全点対距離の不変という既存eigyを再利用する。これを全系同時の剛性、Born剛性、全担体が一つの静止慣性系を持つこと、任意加速の実現可能性へ強めない。本文適用時には各担体の評価系と場の系の対応を保持する。',
 '小ささは文脈の比較尺度と数値寸法の組合せである。原文に具体的な閾値や球形を補わず、点状性や任意の有限上界だけで小さいと認定しない。尺度規約の充足は物理的解釈であり、数値試験から尺度の妥当性を証明しない。',
 '有限検査は符号付き部分量、空間逆像、全部分・全時刻の接続、内部交換と空間流入出、全点対の寸法、同じ設定の共有を分ける。全実数時刻と全空間領域への量化は原文に残し、有限標本への暗黙置換を拒否する。',
]

def args(fields,**replace):return [replace.get(n,v(n)) for n,t in fields]
def coord(axis,label,time):return app(app(v(axis),label),time)
def definitions():
    text=''.join('r '+n+'['+' '.join(t for n,t in fs)+'] c.\n' for n,(fs,m) in PRIMITIVES.items())
    rename=dict(zip(('seoo','seop','seoq','seor','seos'),('ekxn','ekxo','ekxp','ekxq','ekxr')))
    text+=re.sub(r'\b(seoo|seop|seoq|seor|seos)\b',lambda m:rename[m[0]],sets('a'))
    p=v('label');time=v('time');axis=v('axis')
    component=k('bb','n p a b')
    for role,value in reversed(list(zip(ROLES,[coord(a,p,time) for a in ('x','y','z')]+[time]))):component=k('szi',op('e',axis,k(role)),value,component)
    location=lam('axis','a',component)
    text+=define('ekxs',PULLBACK,lam('label','a',both(app(v('members'),p),app(v('space'),location))),LABELS)
    amount=app(v('total'),v('part'))
    physical=k('eisvy',v('body'),v('distribution'),k('zor'),v('frame'),v('event'),time,v('part'),v('lengthunit'),v('timeunit'),v('chargeunit'),amount,v('context'))
    text+=define('ekxt',MATERIAL,both(k('lg',v('lower'),v('upper'),time),k('ekxr',v('members'),v('parts'),v('total'),v('part'),amount),physical))
    preimage=k('ekxs',*args(PULLBACK));value=app(v('total'),preimage)
    text+=define('ekxu',SPATIAL,both(k('ekxt',*args(MATERIAL,part=preimage)),k('eisvx',v('distribution'),k('zor'),v('frame'),v('event'),time,v('space'),v('lengthunit'),v('timeunit'),v('chargeunit'),value,v('context'))))
    allparts=q('f','part',LABELS,op('y',app(v('parts'),v('part')),k('ekxt',*args(MATERIAL))))
    allspaces=q('f','space',BALL,op('y',app(v('parts'),preimage),k('ekxu',*args(SPATIAL))))
    history=q('f','time',R,op('y',k('lg',v('lower'),v('upper'),time),q('g','event','a',both(allparts,allspaces))))
    membership=q('f','label','a',op('z',app(v('members'),p),app(k('zqn'),p,v('distribution'),v('context'))))
    text+=define('ekxv',FIXED,both(k('eiad',*args(HISTORY)),k('ejsl',*[v(n) for n in ('frame','lengthunit','timeunit','context')]),k('bg',v('lower'),v('upper')),membership,app(v('parts'),v('members')),k('ekxq',v('members'),v('parts'),v('total')),history))
    valid=[k('ba',v(n)) for n in ('time','threshold')]+[k('ba',coord(a,v(p),time)) for p in ('left','right') for a in ('x','y','z')]
    text+=define('ekxw',PAIR,both(*valid,k('bg',k('bb','n p a b'),v('threshold')),k('bg',k('eigw',v('left'),v('right'),time,*args(COORDS)),k('shv',v('threshold'),v('threshold')))))
    selected=both(app(v('members'),v('left')),app(v('members'),v('right')),k('lg',v('lower'),v('upper'),time))
    small=quantified('f',[('left','a'),('right','a'),('time',R)],op('y',selected,k('ekxw',*args(PAIR))))
    text+=define('ekxx',SMALL,both(k('eigy',*args(HISTORY)),k('bg',v('lower'),v('upper')),k('ba',v('threshold')),k('bg',k('bb','n p a b'),v('threshold')),k('eisvz',*args(SCALE)),small))
    text+=define('ekxy',ALL,both(k('ekxv',*args(FIXED)),k('ekxx',*args(SMALL))))
    return text

@lru_cache(None)
def build():
    old=parse(read(PARENT));assert len(old['statements'])==408
    assert not(set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']
    added=doc['declarations'][len(old['declarations']):]
    prim={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,t in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='fixed_material_portion_charge_and_small_rigid_body_dependency',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=prim,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[]).document
    ann=json.loads(read('data/convective-charge-setting-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode()))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
