"""Generalize current coordinate/clock bindings and complete translated trials."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_differential_step import ROOT,read
from scripts.compose_comoving_labels import TAU
from scripts.compose_comoving_time_task import proposed
from scripts.compose_material_relative_frame import define
from scripts.compose_moving_trip_geometry import TRIP,KINEMATICS,fields_args,zero
from scripts.compose_limits import R,v,call as k,app,op,both,quant as q

PARENT='examples/v014/einstein-differential-step.noema';PARENT_BASIS='data/differential-step-basis-v1.json'
FULL='examples/v014/einstein-translated-light-trial.noema';CORE='examples/v014/translated-light-trial-core.noema'
BASIS='data/translated-light-trial-basis-v1.json';ANNOTATIONS='data/translated-light-trial-identifiers-v1.json';INDEX=282
MEANINGS={
 'ei26':'指定した状況で同じ対象出来事に付与された現在のKとkの四座標をsguで結ぶ。eiyyの固定zb6を状況引数に一般化する。',
 'ei27':'指定系・状況で全対象出来事に現在のeiyxが付与する四座標の全範囲。eiyz/eiy2の状況固定を外すが任意の未観測四組へ拡張しない。',
 'ei3a':'同じ状況の全対象出来事でK/kの座標が存在し、値として一意であり、その全対応対が機能的なグラフを成す。現在eiy3の同じ規約を状況引数で使う。',
 'ei3b':'指定状況の同じ出来事の全座標対で、指定τ候補の補助座標x-vt,y,z,tにおける値がk時刻成分に一致する。状況の実際の相対速度と同じzb7を結び、ei3aの完全対応を保持する。',
 'ei3c':'指定状況のei3bと全k時計網eiyfを受け、全対象出来事・全K組・全局所k時計の表示が同じτ候補値であり、全有効表示値がその値に等しい場合に限りその表示に対応する。eizzの全指示条件を同じ状況で使う。',
 'ei3d':'現在eixtの初期計器、全測定、同じ並進と全期間平行軸、両物差しの条件を保持し、選択した履歴zcjだけを引数historyへ一般化する。historyが同じcontextを表すことを要求し、別の候補状況を固定された履歴へ押し込めない。',
 'ei3e':'現在ei2mの光速度適用範囲・幾何学的長さ・両端の現在のK局所表示・同じ出来事時刻を保持し、軸そのものに重なるzdwだけを、同じ軸に平行な支持線の全経路zefへ一般化する。',
 'ei3f':'現在ei2aの同じ二時計・二地点・光・三出来事・同じ全同期範囲への所属と局所表示を保持する往復。出発点のk原点への一致を課さず、全光路はk縦軸に平行な支持線上にある。原点の場合も排除しない。',
 'ei3g':'既存eitiの完全な二端点軌道・光往復軌道・同じ三出来事の出会い・真空・反射を保持し、全経路の横座標を指定した一定y,zへ平行移動する。横速度は零のままで、光の交点条件eithと縦速度は変更しない。',
 'ei3h':'同じ出来事の現在のK四座標から補助値x-vtを作り、指定した補助位置x′と横座標y,zに一致させる。横座標を零へ固定せず、三値は同じ組から取得する。',
 'ei3i':'指定試行の三出来事の現在のK四組に同じ候補τを適用し、実際のk時計読取値qi,qj,qkへ結ぶ。状況・光試行・出来事・座標を取り違えず、旧shdへ戻さない。',
 'ei3j':'任意の出発点と指定された正の縦方向間隔の同じ試行を、現在のk局所時計、両端静止、三出来事の補助位置(x′,x′+gap,x′)と一定y,z、同じ出発t、平行移動した完全なK軌道、両K光区間の現行原理と局所時計へ接続する。',
 'ei3k':'指定した試行・地点・補助位置・出発時刻・状況について、同じ全計器履歴、同じτの全出来事対応と全k指示、全K時計網と全光速度原理、二つの光区間と正の間隔を持つei3jが存在する条件。可能な選択や実行の帰属はまだ含めない。',
 'ei3l':'指定したk静止地点の同じK時点で、同じ代表履歴と位置測定ymが一致し、そのx-vt,y,zと時刻が指定値に一致する。全時区間のk静止とK並進を保持する。元設定の地点に時計が既にあることを新たに要求しない。',
}
LIMITS=[
 'u0058を全文へ接続するための意味依存群。著者主張と全単位判断は増やさず、可能な選択・注意喚起・全空間への帰結は次の統合に残す。',
 '現在の測定・時計・出来事の規約を使い、候補設定と任意の試行を引数に取る。固定された基準状況zb6、選択試行zdq、光区間zdx/zdy、履歴zcjを候補設定へ流用しない。同じK/k・単位・V・vとτ候補は保持する。',
 '出発点はk原点に限らず、原点の場合も許す。光路全体は対応縦軸に平行な支持線に置き、Kの一定横座標y,zは任意の有効値とする。縦方向の正の間隔と0<v<V、非退化な往復と三時刻順序は引き継ぐ。',
 '両端点と光の全時区間の履歴をeitf/seへ結び、同じ三出来事での出会いをsbへ結ぶ。真空・反射・幾何学的弧長・全光速度適用範囲を保持し、端点の数値だけで全経路を代用しない。',
 '現在の座標対応と全時計の指示の条件を候補状況でも過不足なく保つ。部分的な三指示だけを全τ条件としない。時計を置いていない元設定の地点へ、候補試行の局所表示が現実に既にあるという条件を加えない。',
 '元設定の地点と時刻は同じ代表軌道と測定から取得する。kに静止することとKの位置が一定であることを混同しない。座標原点の移動でτの数値や時刻尺度を変えず、任意の地点での微分係数を原点の固定係数へ替えない。',
 '可能な別設定が存在するという原文の主張や一般の物理的導出を、有限の例が証明したとはしない。全実時刻・全候補・全局所指示への量化を保ち、未知入力を受理する既定値を置かない。旧定義・判断・証拠は変更しない。',
]

def adapted_definitions():
    """Two exact adaptations preserve every unrelated conjunct and argument."""
    old=parse(read(PARENT));ds={d['name']:d for d in old['declarations']};out=[]
    for source,target in (('eixt','ei3d'),('ei2m','ei3e')):
        d=deepcopy(ds[source]);d['name']=target
        if source=='eixt':d['parameters'].append(dict(name='history',sort='individual'))
        def walk(node):
            if isinstance(node,list):return [walk(x) for x in node]
            if not isinstance(node,dict):return node
            if source=='eixt' and node.get('kind')=='call' and node.get('symbol')=='zcj':return dict(kind='variable',name='history')
            result={n:walk(x) for n,x in node.items()}
            if source=='ei2m' and result.get('symbol')=='zdw':result['symbol']='zef'
            return result
        d['body']=walk(d['body']);out.append(d)
    return out

def definitions():
    c=v('context');e=v('event');t=v('tuple');moving=k('zbm');rest=k('ra');lu=k('ta');tu=k('rb')
    side=lambda frame:'i[event a tuple a]['+k('eiyx',e,t,k(frame),c)+']'
    text=define('ei26',[('first','a'),('second','a'),('context','d')],k('sgu','p zc4',side('ra'),side('zbm'),v('first'),v('second')))
    text+=define('ei27',[('tuple','a'),('frame','a'),('context','d')],q('g','event','a',both(k('zc4',e),k('eiyx',e,t,v('frame'),c))))
    ranges=lambda frame:'i[tuple a]['+k('ei27',t,k(frame),c)+']'
    pairs='i[first a second a]['+k('ei26',v('first'),v('second'),c)+']'
    text+=define('ei3a',[('context','d')],both(k('sgv','p zc4',side('ra'),side('zbm'),'p shh'),k('sgw',ranges('ra'),ranges('zbm'),pairs,'p shh')))
    val=proposed(v('function'),v('first'))
    allpairs=q('f','first','a',q('f','second','a',op('y',both(k('ei27',v('first'),rest,c),k('ei27',v('second'),moving,c),k('ei26',v('first'),v('second'),c)),both(k('ba',val),k('sca',val,k('zc6',v('second'),k('zc7')))))))
    text+=define('ei3b',[('function',TAU),('context','d')],both(k('ei3a',c),k('ba',k('zb7')),k('sca',k('zb7'),k('zbi',rest,moving,lu,tu,c)),allpairs))
    at=both(k('zc4',e),k('eiyx',e,v('first'),rest,c),k('zcz',e,moving,c),k('zbz',moving,v('clock'),c),k('cb',v('clock'),v('place'),moving),k('cb',e,v('place'),moving))
    display=lambda value:k('eiyg',e,v('clock'),v('place'),moving,value,c)
    allreadings=op('y',at,both(display(val),q('f','reading',R,op('y',k('ba',v('reading')),op('z',display(v('reading')),k('sca',v('reading'),val))))))
    for n in reversed(('event','clock','place','first')):allreadings=q('f',n,'a',allreadings)
    text+=define('ei3c',[('function',TAU),('context','d')],both(k('ei3b',v('function'),c),k('eiyf',moving,c),allreadings))
    trial=v('trial');first=v('firstclock');second=v('secondclock');origin=k('qc',trial);mirror=k('qd',trial);ray=k('qh',trial);axis=k('zbo',moving,k('yn'),c)
    events=[k(n,trial) for n in ('qe','qf','qg')];readings=[k(n,trial) for n in ('qi','qj','qk')]
    rows=[k('qb',first,second,moving,tu,c,trial),op('u',op('e',first,second)),op('u',op('e',origin,mirror)),k('zbw',moving,axis,k('yn'),c),k('zbz',moving,first,c),k('zbz',moving,second,c),k('zcu',origin,moving,c),k('zcu',mirror,moving,c),k('da',first,second,origin,mirror,*events,ray,moving,tu,*readings),k('sde',ray,*events,moving,'p cf','p cg','p ch'),k('qo',first,second,moving,tu,c)]
    rows += [k('zef',ray,a,b,axis,moving,c) for a,b in zip(events,events[1:])]
    rows += [k('eiz7',event,clock,place,value,c) for event,clock,place,value in zip(events,(first,second,first),(origin,mirror,origin),readings)]
    rows += [k('bg',a,b) for a,b in zip(readings,readings[1:])]
    text+=define('ei3f',[(n,'a') for n in ('trial','firstclock','secondclock')]+[('context','d')],both(*rows))
    cf=[v(n) for n in ('frame','context','lengthunit','timeunit')]
    reflect=k('bd',k('bd',v('origin'),v('length')),k('shv',v('speed'),k('bf',v('middle'),v('first'))))
    arrive=k('bd',v('origin'),k('shv',v('speed'),k('bf',v('last'),v('first'))))
    trace=lambda obj,lo,hi,x,speed:k('eitf',v(obj),*cf,v(lo),v(hi),x,v('y'),v('z'),speed,zero(),zero())
    rows=[op('u',op('e',v('firstend'),v('lastend'))),k('eith',*fields_args(KINEMATICS)),k('eisb5',v('ray'),v('frame'),c),k('sde',*[v(n) for n in ('ray','depart','reflection','arrival','frame')],'p cf','p cg','p ch'),trace('firstend','first','last',v('origin'),v('speed')),trace('lastend','first','last',k('bd',v('origin'),v('length')),v('speed')),trace('ray','first','middle',v('origin'),v('light')),trace('ray','middle','last',reflect,k('bf',zero(),v('light')))]
    rows += [k('eisca',v('ray'),v(a),v(b),v('frame'),c) for a,b in (('depart','reflection'),('reflection','arrival'))]
    for endpoint,event,time,x in (('firstend','depart','first',v('origin')),('lastend','reflection','middle',reflect),('firstend','arrival','last',arrive)):
        rows += [k('sb',v(obj),v(event),*cf,v(time),x,v('y'),v('z')) for obj in (endpoint,'ray')]
    text+=define('ei3g',TRIP+[('y',R),('z',R)],both(*rows))
    spatial=[(n,R) for n in ('x','y','z','time')]
    text+=define('ei3h',[('event','a'),('tuple','a')]+spatial[:3]+[('context','d')],both(k('eiz5',e,t,v('x'),c),k('ba',v('y')),k('ba',v('z')),k('sca',k('zc6',t,k('yo')),v('y')),k('sca',k('zc6',t,k('yp')),v('z'))))
    rows=[]
    for event,reading in zip(events,readings):
        tup=k('zdz',event,rest,c);value=proposed(k('zd4'),tup)
        rows.extend((k('eiyx',event,tup,rest,c),k('ba',value),k('sca',value,reading)))
    text+=define('ei3i',[('trial','a'),('context','d')],both(*rows))
    gap=v('gap');x=v('x');y=v('y');z=v('z');tm=v('time')
    times=[k('sjh',event,c) for event in events];xs=[k('sji',event,c) for event in events]
    rows=[k('ei3f',trial,k('te',trial),k('tf',trial),c),op('e',origin,v('point')),k('eizm',origin,c),k('eizm',mirror,c),k('ei3i',trial,c),k('sbg',k('zb7')),k('sbg',gap),k('ba',tm),k('sca',times[0],tm)]
    rows += [k('ei3h',event,k('zdz',event,rest,c),xp,y,z,c) for event,xp in zip(events,(x,k('bd',x,gap),x))]
    rows += [k('ei3g',origin,mirror,ray,*events,rest,c,lu,tu,xs[0],gap,k('tc'),k('zb7'),*times,y,z),k('ei3e',v('outward'),ray,events[0],events[1],k('bf',xs[1],xs[0]),c),k('ei3e',v('returning'),ray,events[1],events[2],k('bf',xs[1],xs[2]),c)]
    detailed=[(n,'a') for n in ('trial','point','outward','returning')]+[('gap',R)]+spatial+[('context','d')]
    text+=define('ei3j',detailed,both(*rows))
    body=both(k('ei3d',c,v('history')),k('ei3c',k('zd4'),c),k('eiyf',rest,c),k('eios',k('tc'),c),k('ei3j',*[v(n) for n,_ in detailed]))
    for n,sort in reversed([('history','a'),('outward','a'),('returning','a'),('gap',R)]):body=q('g',n,sort,body)
    text+=define('ei3k',[(n,'a') for n in ('trial','point')]+spatial+[('context','d')],body)
    p=v('point');moment=v('moment');stamp=k('yl',moment,rest,tu,c)
    coords=[k('ym',p,moment,rest,lu,k(a),c) for a in ('yn','yo','yp')]
    matched=[k('ys',moment,c),k('zce',p,moment,rest,lu,c),k('zcf',moment,rest,tu,c),k('sca',stamp,tm),k('sca',k('sin',k('zb7'),coords[0],stamp),x),k('sca',coords[1],y),k('sca',coords[2],z)]
    matched += [k('sca',coord,app(k('eismh',p,rest,lu,tu,k(a),c),stamp)) for a,coord in zip(('yn','yo','yp'),coords)]
    text+=define('ei3l',[('point','a')]+spatial+[('context','d')],both(*(k('ba',v(n)) for n,_ in spatial),k('zdi',p,c),k('zcu',p,moving,c),k('x4',p,moving,c),k('eizm',p,c),q('g','moment','a',both(*matched))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX;doc=deepcopy(old);doc['statements']=[]
    assert not set(MEANINGS)&{d['name'] for d in old['declarations']}
    doc['declarations']+=adapted_definitions();doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']
    added=doc['declarations'][len(old['declarations']):]
    basis=dict(status='translated_current_light_trial_dependency',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[]).document
    ann=json.loads(read('data/differential-step-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
