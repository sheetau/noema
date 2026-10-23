"""Connect comoving representative positions and complete moving-end light paths."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_carried_clock_synchrony import ROOT,read,record_args
from scripts.compose_rod_methods import coords,interval
from scripts.compose_material_relative_frame import define
from scripts.compose_limits import R,F,v,call as k,app,op,both,quant as q

PARENT='examples/v014/einstein-carried-clock-synchrony.noema';PARENT_BASIS='data/carried-clock-synchrony-basis-v1.json'
FULL='examples/v014/einstein-moving-trip-geometry.noema';CORE='examples/v014/moving-trip-geometry-core.noema'
BASIS='data/moving-trip-geometry-basis-v1.json';ANNOTATIONS='data/moving-trip-geometry-identifiers-v1.json'
TRACES=[(side+axis,F) for side in ('target','reference') for axis in ('x','y','z')]
KINEMATICS=[(n,R) for n in ('origin','length','light','speed','first','middle','last')]
TRIP=[(n,'a') for n in ('firstend','lastend','ray','depart','reflection','arrival','frame')]+[('context','d'),('lengthunit','a'),('timeunit','a')]+KINEMATICS
PRIMITIVES={
 'eismh':([('object','a'),('frame','a'),('lengthunit','a'),('timeunit','a'),('axis','a'),('context','d')], '指定した物理的な記述尺度でobjectの位置を代表する基準点について、同じframe・長さ単位・時間単位・contextのaxis成分を時刻の関数として取り出す。拡がりを持つ観測者では、その巨視的な配置を追う代表点であり、身体の全物質点や内部運動を同じ点に縮めない。未知の軌道を既定の零で埋めず、同じ対象の出来事への帰属と全区間の有効性はseで要求する。'),
}
MEANINGS={
 'eitd':'同じ二時刻におけるtargetとreferenceの三位置を有効な実切断として取り、referenceからtargetへの相対変位の各成分が二時刻で不変であることを要求する。距離だけの一致や絶対座標の一致にはしない。',
 'eite':'同じ基準系・単位・正の時間区間で二対象の代表位置の完全なse履歴を要求し、区間内の全時刻対でeitdの相対位置が不変である。相手が動いていることや近くにいることは別条件。内部機構を凍結する物体全体の静止とは分ける。',
 'eitf':'同じ対象・系・単位・区間について、始位置と一定の三速度成分から作った三つの一次時刻関数を完全なseへ渡す。端点だけの補間ではなく、全区間の出来事と座標への対応を要求する。',
 'eitg':'正の棒長、0以上で光速より小さい速度、時間順に並ぶ出発・反射・帰着と任意の有効な出発位置を持つ往復の数値領域。v=0は依存定義の比較例として許し、本文の正のybは別に保つ。',
 'eith':'同じeitgの数値を用い、往路の光の反射位置が動くB端の位置に等しく、復路の光の帰着位置が動くA端の位置に等しいという二つの交点条件。原点を零に固定しない。',
 'eiti':'同じ二端・光・三出来事の真空中の反射往復について、eithの交点、二端の等速軌道と往復の光の全se軌道、全出会いのsbを結ぶ。Aはこの試行でX方向の後端、Bは前端として読む。棒全体の剛性と測定は別に接続する。',
 'eitj':'既存zas/zat/zauの同じ三記録をA端出発・B端反射・A端帰着として選び、現行eiq2の出来事・現在位置・両表示・静止系時刻を結ぶ。異なる時計、時刻や記録の欄を混ぜない。',
 'eitk':'同じ運動する棒eipkと両時計の全区間の条件eiq4、三照合記録eitjを保持し、eitiの全往復を同じ静止系・単位・既出の速度ybと光速tcへ結ぶ。出発位置は同じA端の関数から取り、r_ABの候補zavを区間中の二端間隔として用いる。',
 'eitl':'観測者xbが同じ時計のそばzapで共に動くzaqという既存の役割を保ち、時計の取り付けeiqzと、その時計に対する観測者代表位置の全区間の共動eiteを結ぶ。近接だけや一時点の位置一致で共動を代用しない。',
 'eitm':'同じ棒の二時計のそばの異なる観測者をeitlで結び、両者が同じ三記録・光・試行の二時計へ第一節の中点判定biを適用する。適用を中点条件の成立や同期しているという判断へ変えない。',
}
LIMITS=[
 'u0036〜u0039とu0280の本文接続に必要な、共動観測者と全区間の光・棒端の軌道の依存群。本文の著者主張と意味確認済み単位は増やさない。二式の著者への帰属・注の内容と付着位置は後で接続する。',
 '観測者の共動は、時計に対する巨視的な代表位置が全区間で一定の相対変位を保つという理想化で読む。足・腕・眼・内部部品の全運動を禁止せず、身体全体を物質点へ同一視しない。近接zapはその文脈の局所観測に相応しい空間的な近さという物理的入力であり、原文にない数値の距離閾値は加えない。',
 'seへ渡す代表位置と端点の位置は同じra・ta・rbと運動区間を使う。時計は既にeiqzで同じ端点の全履歴に結び、未知の座標を静止や零へ補わない。共動だけから近接や実際の判定行為は推論しない。',
 '原刊の二式は正のvの向きに対し、出発するAを後端、反射するBを前端に取る読みとする。前の棒の幾何は端点順序を未固定として保存し、この光往復の配置でのみx_B(t_A)=x_A(t_A)+r_ABを要求する。',
 '真空の光はeisb5・eisca、同じ三出来事と反射はsde、全区間の軌道はse、端点と光の同じ出会いはsbで分けて記述する。放出・反射・帰着に対応する出来事を変えず、帰着を静止した出発位置へ戻ることとはしない。放出元の機構・反射面の微視的機構はこの理想化に追加しない。',
 'eitiは直線の往路・復路に一定の大きさVの速度を与えた運動学的な条件である。第二原理が真であることや、現実の全光路が実現することを証明しない。原理から二式を得るという著者の提示は後続の本文で別に帰属する。',
 '同じzavはこの段階では静止系の一定の端点間隔r_ABの候補として全軌道へ結ぶ。現行方法eip6による長さの測定と二式の本文提示への接続は残す。初期静止長ya、光の往復全長、任意の経路長へ交換しない。',
 '第一節の判定の引用biは三つの時計指示の中点条件を表す。zarの適用行為はその結果の肯定を要求しない。静止時計の全要件を含むqoを動く時計自身へ直接適用することとは区別する。',
 '有限検査は一次関数の係数、同じ三出来事・全履歴への結合、数値的交点と二式の関係、相対変位、引用された判定の非実行を調べる。全実時刻の量化と未知入力の拒否を保ち、有限標本を全履歴や原文との意味同値の証明にしない。',
]


def fields_args(fields):return [v(n) for n,_ in fields]
def zero():return k('bb','n p a b')
def linear(start,origin,speed):return 'i[time '+R+']['+k('bd',origin,k('shv',speed,k('bf',v('time'),start)))+']'
def defs():
    text='r eismh['+' '.join(t for _,t in PRIMITIVES['eismh'][0])+'] '+F+'.\n'
    position=lambda side,a,t:app(v(side+a),v(t))
    values=[position(side,a,t) for side in ('target','reference') for a in ('x','y','z') for t in ('first','second')]
    relative=lambda a,t:k('bf',position('target',a,t),position('reference',a,t))
    text+=define('eitd',[('first',R),('second',R)]+TRACES,both(k('ba',v('first')),k('ba',v('second')),*(k('ba',x) for x in values),*(k('sca',relative(a,'first'),relative(a,'second')) for a in ('x','y','z'))))
    shared=[v(n) for n in ('frame','context','lengthunit','timeunit','lower','upper')]
    pair=op('y',both(*(k('lg',v('lower'),v('upper'),v(t)) for t in ('first','second'))),k('eitd',v('first'),v('second'),*fields_args(TRACES)))
    fields=[('target','a'),('reference','a'),('frame','a'),('context','d'),('lengthunit','a'),('timeunit','a'),('lower',R),('upper',R)]+TRACES
    text+=define('eite',fields,both(op('u',op('e',v('target'),v('reference'))),k('bg',v('lower'),v('upper')),k('eisdd',v('frame'),v('lengthunit'),v('timeunit'),v('context')),*(k('se',v(s),*shared,*(v(s+a) for a in ('x','y','z'))) for s in ('target','reference')),q('f','first',R,q('f','second',R,pair))))
    fields=[('target','a'),('frame','a'),('context','d'),('lengthunit','a'),('timeunit','a'),('lower',R),('upper',R)]+[(n,R) for n in ('x','y','z','vx','vy','vz')]
    text+=define('eitf',fields,both(*(k('ba',v(n)) for n in ('x','y','z','vx','vy','vz')),k('se',v('target'),*shared,*(linear(v('lower'),v(a),v('v'+a)) for a in ('x','y','z')))))
    text+=define('eitg',KINEMATICS,both(*(k('ba',v(n)) for n,_ in KINEMATICS),k('sbg',v('length')),k('bc',zero(),v('speed')),k('bg',v('speed'),v('light')),k('bg',v('first'),v('middle')),k('bg',v('middle'),v('last'))))
    dt=k('bf',v('middle'),v('first'));back=k('bf',v('last'),v('middle'))
    reflect=k('bd',k('bd',v('origin'),v('length')),k('shv',v('speed'),dt))
    arrive=k('bd',v('origin'),k('shv',v('speed'),k('bf',v('last'),v('first'))))
    text+=define('eith',KINEMATICS,both(k('eitg',*fields_args(KINEMATICS)),k('sca',k('bd',v('origin'),k('shv',v('light'),dt)),reflect),k('sca',k('bf',reflect,k('shv',v('light'),back)),arrive)))
    cf=[v(n) for n in ('frame','context','lengthunit','timeunit')]
    trace=lambda obj,lo,hi,x,speed:k('eitf',v(obj),*cf,v(lo),v(hi),x,zero(),zero(),speed,zero(),zero())
    clauses=[op('u',op('e',v('firstend'),v('lastend'))),k('eith',*fields_args(KINEMATICS)),k('eisb5',v('ray'),v('frame'),v('context')),k('sde',*[v(n) for n in ('ray','depart','reflection','arrival','frame')],'p cf','p cg','p ch'),trace('firstend','first','last',v('origin'),v('speed')),trace('lastend','first','last',k('bd',v('origin'),v('length')),v('speed')),trace('ray','first','middle',v('origin'),v('light')),trace('ray','middle','last',reflect,k('bf',zero(),v('light')))]
    for start,end in (('depart','reflection'),('reflection','arrival')):clauses.append(k('eisca',v('ray'),v(start),v(end),v('frame'),v('context')))
    for endpoint,event,time,x in (('firstend','depart','first',v('origin')),('lastend','reflection','middle',reflect),('firstend','arrival','last',arrive)):
        for target in (endpoint,'ray'):clauses.append(k('sb',v(target),v(event),*cf,v(time),x,zero(),zero()))
    text+=define('eiti',TRIP,both(*clauses))
    c=v('context');records=(('zas','zaj','xn'),('zat','zak','xo'),('zau','zaj','xn'))
    text+=define('eitj',[('context','d')],both(*(both(k('zac',k(rec),k(clock),c),k('eiq2',k(clock),k(end),*record_args(k(rec)),c)) for rec,clock,end in records)))
    event=lambda rec:k('zad',k(rec));time=lambda rec:k('zah',k(rec))
    origin=app(app(coords(k('xi'),k('ra'),c)[0],k('xn')),time('zas'))
    text+=define('eitk',[('context','d')],both(k('eipk',c),k('eiq4',k('zaj'),k('xn'),c),k('eiq4',k('zak'),k('xo'),c),k('eitj',c),k('eiti',k('xn'),k('xo'),k('zax'),*(event(rec) for rec in ('zas','zat','zau')),k('ra'),c,k('ta'),k('rb'),origin,k('zav'),k('tc'),k('yb'),*(time(rec) for rec in ('zas','zat','zau')))))
    observer=v('observer');clock=v('clock');endpoint=v('endpoint')
    ofns=[k('eismh',observer,k('ra'),k('ta'),k('rb'),k(axis),c) for axis in ('yn','yo','yp')]
    cfns=[app(fn,endpoint) for fn in coords(k('xi'),k('ra'),c)]
    text+=define('eitl',[('observer','a'),('clock','a'),('endpoint','a'),('context','d')],both(k('xb',observer),k('zap',observer,clock,c),k('zaq',observer,clock,k('ra'),c),k('eiqz',clock,endpoint,c),k('eite',observer,clock,k('ra'),c,k('ta'),k('rb'),*interval(k('ra'),c),*ofns,*cfns)))
    clauses=[k('eitj',c),op('u',op('e',k('zay'),k('zaz'))),k('za4',k('zaw'),k('zax'),*(event(rec) for rec in ('zas','zat','zau')),k('ra'),c)]
    for observer,clock,end in (('zay','zaj','xn'),('zaz','zak','xo')):clauses.extend((k('eitl',k(observer),k(clock),k(end),c),k('zar',k(observer),k('zaj'),k('zak'),k('zaw'),'r[p bi]',c)))
    text+=define('eitm',[('context','d')],both(*clauses))
    return text


def build():
    old=parse(read(PARENT));assert len(old['statements'])==261;doc=deepcopy(old);doc['statements']=[]
    assert not(set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in doc['declarations']}
    doc=parse(format_graph(doc,'compact')+defs());doc['statements']=old['statements'];added=doc['declarations'][len(old['declarations']):]
    primitive=next(d for d in added if d['kind']=='primitive')
    basis=dict(status='comoving_observer_and_complete_moving_light_trip_dependency',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={'eismh':dict(parameters=primitive['parameters'],result=primitive['result'],arguments=[n for n,_ in PRIMITIVES['eismh'][0]],meaning_ja=PRIMITIVES['eismh'][1])},definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=['eitk','eitm'],statement_indices=[]).document
    ann=json.loads(read('data/carried-clock-synchrony-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
