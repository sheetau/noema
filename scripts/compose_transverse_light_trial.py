"""Bind transverse roundtrips to current clocks and complete diagonal K paths."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_arbitrary_start_claim import ROOT,read
from scripts.compose_material_relative_frame import define
from scripts.compose_moving_trip_geometry import TRIP,KINEMATICS,fields_args,zero
from scripts.compose_limits import R,v,call as k,op,both,quant as q

PARENT='examples/v014/einstein-arbitrary-start-claim.noema';PARENT_BASIS='data/arbitrary-start-claim-basis-v1.json'
FULL='examples/v014/einstein-transverse-light-trial.noema';CORE='examples/v014/transverse-light-trial-core.noema'
BASIS='data/transverse-light-trial-basis-v1.json';ANNOTATIONS='data/transverse-light-trial-identifiers-v1.json';INDEX=284
MEANINGS={
 'ei3w':'現在ei3fの二時計・同じ光・三出来事・全同期範囲・局所表示を保持し、kでの完全な平行支持線の軸を引数axisへ一般化する。指定軸は相異なる横軸yo又はypであり、縦軸ynを受理しない。',
 'ei3x':'現在ei2mの全光速度適用範囲・同じ光と出来事・幾何学的経路長・両端の現在K局所表示と一意時刻を保持し、K縦軸上という制限だけを外す。実際の全軌道はei3zで別に接続し、kの横軸平行性をKへ移さない。',
 'ei3y':'同じ正の横距離、光の全速さV、0≤v<V、正の横成分w=√(V²-v²)と三時刻について、往路・復路の横移動量wΔtが同じ距離に等しいことを要求する。既存eitgとskzを再利用し、Vとwを交換しない。',
 'ei3z':'同じ二端点・光・三出来事の真空往復について、Kの完全な四軌道と六つの出会いを結ぶ。両端は縦速度v、光は往復とも縦速度vと選択横軸の成分±wを持つ。非選択横座標は一定で、反射と帰着のK縦位置は時間に応じて移動する。',
 'ei32':'指定した横軸の同じ光試行・地点・補助座標・K出発時刻を、現在のk時計往復ei3w、両端の共動、同じτの三読取り、現在のK座標、完全なK軌道ei3zと両光区間ei3xへ結ぶ。補助x-vtは一定、選択横座標は出発値・出発値+gap・出発値である。',
 'ei33':'指定試行・横軸・地点・補助座標・K出発時刻・候補設定について、現在の全計器履歴・全τ対応と全k指示・全K時計網・全光速度原理を保つei32の履歴、二区間、正の横距離と横成分が存在する。試行の可能選択・全範囲と微分の帰結は別に接続する。',
}
LIMITS=[
 'u0059–u0061を現在の本文へ接続するための横方向の物理依存群。著者主張と全単位判断は増やさず、全候補範囲・局所微分・類似推論と注意喚起・原刊との全文判断は次の統合に残す。',
 'kの相異なる横軸yo/ypに平行な全光路と、Kの斜めの全光路を区別する。Kの全光速はV、縦成分はv、選択横成分は往路+w・復路-wであり、w=√(V²-v²)>0とする。Vを横速度に置き換えない。',
 '原点・時刻・非選択横座標を零へ固定しない。横距離は正で、同じ試行の往路と復路で等しい。一般数値定義はv=0を比較例として許すが、現在の本文の試行は既出v>0を保持する。',
 'ei3xは縦軸上という二条件だけを外し、全区間範囲、幾何学的な光路長、現在のK配備時計の表示・一意な時刻・系内時点を保持する。ei32では両経路長をVと同じ二経過時間の積へ結ぶ。光の軌道はei3zの全seと出会いsbで別に要求する。',
 '同じ候補τはei3cの全対応と全k時計指示を満たし、三出来事の値はei3iで実際の読取りへ結ぶ。三つの読取りだけを全候補条件の代わりにしない。現在の地点・時刻と全履歴を保持し、旧sio/shd/sgp/sbcへ戻さない。',
 '平方根と速度三成分の条件は既存skzの意味を再利用する。有限の有理例と関数指紋は引数・向き・接続を調べる検査であり、全実数平方根の法則、全経路や物理的導出の証明にはしない。未知の切断・軌道・測定を既定値で埋めない。',
]

def transverse(axis):
    return both(op('x',op('e',axis,k('yo')),op('e',axis,k('yp'))),*(op('u',op('e',k(a),k(b))) for a,b in (('yn','yo'),('yn','yp'),('yo','yp'))))

def conjuncts(body):
    if body['kind']=='and':return [x for n in body['arguments'] for x in conjuncts(n)]
    return [body]

def adapted_definitions():
    ds={d['name']:d for d in parse(read(PARENT))['declarations']}
    d=deepcopy(ds['ei3f']);d['name']='ei3w';d['parameters'].append(dict(name='axis',sort='individual'))
    def walk(n):
        if isinstance(n,list):return [walk(x) for x in n]
        if not isinstance(n,dict):return n
        if n.get('kind')=='call' and n.get('symbol')=='yn':return dict(kind='variable',name='axis')
        return {k:walk(x) for k,x in n.items()}
    d['body']=walk(d['body']);out=[d]
    # Add the axis guard via the ordinary parser to avoid hand-written AST sorts.
    guard=parse('n:r yn[] a.r yo[] a.r yp[] a.'+define('jtransverse',[('axis','a')],transverse(v('axis'))))['declarations'][-1]
    name=guard['parameters'][0]['name']
    def rename(n):
        if isinstance(n,list):return [rename(x) for x in n]
        if not isinstance(n,dict):return n
        if n.get('kind')=='variable' and n['name']==name:return dict(kind='variable',name='axis')
        return {k:rename(x) for k,x in n.items()}
    d['body']=dict(kind='and',arguments=[rename(guard['body']),d['body']])
    d=deepcopy(ds['ei2m']);d['name']='ei3x'
    rows=conjuncts(d['body']);removed=[r for r in rows if r.get('symbol') in ('zbw','zdw')];assert len(removed)==2
    rows=[r for r in rows if r not in removed];body=rows[-1]
    for row in reversed(rows[:-1]):body=dict(kind='and',arguments=[row,body])
    d['body']=body;out.append(d);return out

def definitions():
    dt=k('bf',v('middle'),v('first'));back=k('bf',v('last'),v('middle'));w=v('transverse')
    text=define('ei3y',KINEMATICS+[('transverse',R)],both(k('eitg',*fields_args(KINEMATICS)),k('skz',v('light'),v('speed'),w),k('sca',k('shv',w,dt),v('length')),k('sca',k('shv',w,back),v('length'))))
    cf=[v(n) for n in ('frame','context','lengthunit','timeunit')];ctx=v('context');axis=v('axis')
    reflectx=k('bd',v('origin'),k('shv',v('speed'),dt));arrivex=k('bd',v('origin'),k('shv',v('speed'),k('bf',v('last'),v('first'))))
    rows=[transverse(axis),op('u',op('e',v('firstend'),v('lastend'))),k('ei3y',*fields_args(KINEMATICS),w),k('eisb5',v('ray'),v('frame'),ctx),k('sde',*[v(n) for n in ('ray','depart','reflection','arrival','frame')],'p cf','p cg','p ch')]
    rows += [k('eisca',v('ray'),v(a),v(b),v('frame'),ctx) for a,b in (('depart','reflection'),('reflection','arrival'))]
    for selected,role in (('y','yo'),('z','yp')):
        y,z=v('y'),v('z');my=k('bd',y,v('length')) if selected=='y' else y;mz=k('bd',z,v('length')) if selected=='z' else z
        velocity=[w if a==selected else zero() for a in ('y','z')]
        negative=[k('bf',zero(),w) if a==selected else zero() for a in ('y','z')]
        trace=lambda obj,lo,hi,x,yy,zz,vy,vz:k('eitf',v(obj),*cf,v(lo),v(hi),x,yy,zz,v('speed'),vy,vz)
        branch=[trace('firstend','first','last',v('origin'),y,z,zero(),zero()),trace('lastend','first','last',v('origin'),my,mz,zero(),zero()),trace('ray','first','middle',v('origin'),y,z,*velocity),trace('ray','middle','last',reflectx,my,mz,*negative)]
        for endpoint,event,time,x,yy,zz in (('firstend','depart','first',v('origin'),y,z),('lastend','reflection','middle',reflectx,my,mz),('firstend','arrival','last',arrivex,y,z)):
            branch += [k('sb',v(obj),v(event),*cf,v(time),x,yy,zz) for obj in (endpoint,'ray')]
        rows.append(op('y',op('e',axis,k(role)),both(*branch)))
    text+=define('ei3z',TRIP+[('y',R),('z',R),('transverse',R),('axis','a')],both(*rows))
    trial=v('trial');point=v('point');gap=v('gap');x=v('x');y=v('y');z=v('z');tm=v('time');rest=k('ra')
    origin=k('qc',trial);mirror=k('qd',trial);ray=k('qh',trial);events=[k(n,trial) for n in ('qe','qf','qg')];times=[k('sjh',e,ctx) for e in events]
    rows=[transverse(axis),k('ei3w',trial,k('te',trial),k('tf',trial),ctx,axis),op('e',origin,point),k('eizm',origin,ctx),k('eizm',mirror,ctx),k('ei3i',trial,ctx),k('sbg',k('zb7')),k('sbg',gap),k('ba',tm),k('sca',times[0],tm)]
    for e in (events[0],events[2]):rows.append(k('ei3h',e,k('zdz',e,rest,ctx),x,y,z,ctx))
    for role,yy,zz in (('yo',k('bd',y,gap),z),('yp',y,k('bd',z,gap))):rows.append(op('y',op('e',axis,k(role)),k('ei3h',events[1],k('zdz',events[1],rest,ctx),x,yy,zz,ctx)))
    rows.append(k('ei3z',origin,mirror,ray,*events,rest,ctx,k('ta'),k('rb'),k('sji',events[0],ctx),gap,k('tc'),k('zb7'),*times,y,z,w,axis))
    for seg,first,last,lo,hi in zip(('outward','returning'),events,events[1:],times,times[1:]):rows.append(k('ei3x',v(seg),ray,first,last,k('shv',k('tc'),k('bf',hi,lo)),ctx))
    spatial=[(n,R) for n in ('x','y','z','time')]
    detailed=[(n,'a') for n in ('trial','axis','point','outward','returning')]+[('gap',R),('transverse',R)]+spatial+[('context','d')]
    text+=define('ei32',detailed,both(*rows))
    body=both(k('ei3d',ctx,v('history')),k('ei3c',k('zd4'),ctx),k('eiyf',rest,ctx),k('eios',k('tc'),ctx),k('ei32',*fields_args(detailed)))
    for n,sort in reversed([('history','a'),('outward','a'),('returning','a'),('gap',R),('transverse',R)]):body=q('g',n,sort,body)
    text+=define('ei33',[(n,'a') for n in ('trial','axis','point')]+spatial+[('context','d')],body)
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX;doc=deepcopy(old);doc['statements']=[]
    assert not set(MEANINGS)&{d['name'] for d in old['declarations']}
    doc['declarations']+=adapted_definitions();doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']
    added=doc['declarations'][len(old['declarations']):]
    basis=dict(status='current_transverse_light_trial_dependency',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[]).document
    ann=json.loads(read('data/arbitrary-start-claim-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
