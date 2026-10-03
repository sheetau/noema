"""Compose separated initial synchronization and a co-located arrival comparison."""
from copy import deepcopy
import json

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, CUT, definition
from scripts.compose_limits import call as k, app, op, both, quant as q, lam

v=lambda name:'v '+name
COMMON=[(name,'a') for name in ('movingclock','reference','placea','placeb','departure','initialreference','arrival','firstrecord','initialrecord','lastrecord')]
COMMON += [(name,CUT) for name in ('movingstart','referencestart','movingend','referenceend')]+[('initial','d'),('motion','d')]
CONSTANTS=dict(zip([n for n,_ in COMMON],('zie','zip','ziq','zir','zis','zit','ziu','ziv','ziw','zix','ziy','ziz','zi2','zi3','zi4','zi5')))


def rational_definitions():
    T,f,A,B,C,D=map(v,('duration','rate','movingstart','referencestart','movingend','referenceend'))
    sub=lambda a,b:k('ab',a,k('ac',b));eq=lambda a,b:op('e',a,b)
    return definition('swj','duration b rate b movingstart b referencestart b movingend b referenceend b',both(
        k('aa','n p a b',T),k('aa','n p a b',f),op('u',k('aa','n p b b',f)),eq(A,B),
        eq(sub(C,A),k('ad',f,T)),eq(sub(D,B),T)))


MEANINGS={'swj':'正の経過時間について、二時計の初期の同時指示が等しく、一方の指示差がrate倍、静止側の指示差が経過時間と等しい有理数の比較前提。'}


def generic_composed():
    doc=parse((ROOT/'examples/v014/clock-delay.noema').read_text(encoding='utf-8')+rational_definitions())
    basis=deepcopy(json.loads((ROOT/'data/clock-delay-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='clock-transfer-basis-v1',document='examples/v014/clock-transfer.noema')
    basis['definitions'].update(MEANINGS)
    basis['unresolved']+=['初期の同時指示の一致と、到着時の同じ場所での指示差を区別する。途中での設定変更や加速の効果は指示法則の前提として別に扱う。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def source_composed():
    doc=parse((ROOT/'examples/v014/einstein-clock-delay.noema').read_text(encoding='utf-8'))
    statements,doc['statements']=doc['statements'],[]
    text=format_graph(doc,'compact')+rational_definitions()
    params=' '.join(name+' '+sort for name,sort in COMMON);args=[v(n) for n,_ in COMMON]
    z=k('bb','n p a b');one=k('bb','n p b b');V=k('tc');speed=k('zb7');frame=k('ra');unit=k('rb')
    mul=lambda a,b:k('shv',a,b);sub=lambda a,b:k('bf',a,b);eq=lambda a,b:k('sca',a,b);sq=lambda a:mul(a,a)
    coord=lambda record,axis:k('zc6',record,k(axis))
    dt=lambda first,last:sub(coord(last,'zc7'),coord(first,'zc7'))
    first,last=v('firstrecord'),v('lastrecord');T=dt(first,last)
    for name,sort in COMMON:
        symbol=CONSTANTS[name]
        if symbol!='zie':text+='r '+symbol+'[] '+sort+'.\n'
    text+='r zi6[] a.r zi7[] a.r zja[] a.\n'
    text+=definition('swl','clock a event a record a reading '+CUT+' setting d',both(k('ca',v('clock')),k('ci',unit),k('zc4',v('event')),
        k('shd',v('event'),v('record'),frame,v('setting')),k('sha',v('record'),'p ba'),k('ba',v('reading')),
        k('ce',v('clock'),v('event'),frame,unit,v('reading')),q('g','place','a',both(k('zab',v('clock'),v('event'),v('place'),frame,v('setting')),k('cb',v('event'),v('place'),frame)))))
    reads=[('movingclock','departure','firstrecord','movingstart','initial'),('reference','initialreference','initialrecord','referencestart','initial'),
           ('movingclock','departure','firstrecord','movingstart','motion'),('movingclock','arrival','lastrecord','movingend','motion'),('reference','arrival','lastrecord','referenceend','motion')]
    placements=[('movingclock','departure','placea','initial'),('reference','initialreference','placeb','initial'),
        ('movingclock','departure','placea','motion'),('movingclock','arrival','placeb','motion'),('reference','arrival','placeb','motion')]
    text+=definition('swm',params,both(
        *(op('u',op('e',v(a),v(b))) for a,b in (('movingclock','reference'),('placea','placeb'),('departure','initialreference'),('departure','arrival'),('initialreference','arrival'),('initial','motion'))),
        k('x4',v('movingclock'),frame,v('initial')),k('x4',v('reference'),frame,v('initial')),k('x4',v('reference'),frame,v('motion')),
        k('xm',v('movingclock'),frame,v('motion')),k('qo',v('movingclock'),v('reference'),frame,unit,v('initial')),
        *(k('swl',*(v(n) for n in row)) for row in reads),
        *(k('zab',v(clock),v(event),v(place),frame,v(ctx)) for clock,event,place,ctx in placements),
        eq(coord(first,'zc7'),coord(v('initialrecord'),'zc7')),k('bg',coord(first,'zc7'),coord(last,'zc7')),
        *(eq(coord(v('initialrecord'),axis),coord(last,axis)) for axis in ('yn','yo','yp')),
        eq(v('movingstart'),v('referencestart'))))
    displacement=[sub(coord(last,axis),coord(first,axis)) for axis in ('yn','yo','yp')]
    text+=definition('swo','firstrecord a lastrecord a speed '+CUT,both(k('sha',first,'p ba'),k('sha',last,'p ba'),k('sbg',v('speed')),
        k('srd',V,v('speed'),k('soy',V,v('speed'))),k('sbg',T),
        eq(k('bd',sq(displacement[0]),k('bd',sq(displacement[1]),sq(displacement[2]))),mul(sq(v('speed')),sq(T)))))
    record=v('record');elapsed=dt(first,record)
    line=both(k('sha',record,'p ba'),k('sha',first,'p ba'),k('sha',last,'p ba'),k('sbg',T),
        k('bc',z,elapsed),k('bc',elapsed,T),*(eq(mul(sub(coord(record,axis),coord(first,axis)),T),mul(displacement[i],elapsed)) for i,axis in enumerate(('yn','yo','yp'))))
    text+=definition('swp','record a firstrecord a lastrecord a',line)
    # Complete time coverage is explicit; finite endpoint tests do not certify it.
    incidence=both(k('zc4',v('event')),k('shd',v('event'),record,frame,v('setting')),k('sha',record,'p ba'),
        q('g','place','a',both(k('zab',v('clock'),v('event'),v('place'),frame,v('setting')),k('cb',v('event'),v('place'),frame))))
    within=lambda t:both(k('ba',t),k('bc',coord(first,'zc7'),t),k('bc',t,coord(last,'zc7')))
    everyrecord=q('f','event','a',q('f','record','a',op('y',both(incidence,within(coord(record,'zc7'))),k('swp',record,first,last))))
    coverage=q('f','time',CUT,op('y',within(v('time')),q('g','event','a',q('g','record','a',both(incidence,eq(coord(record,'zc7'),v('time')),k('swp',record,first,last))))))
    text+=definition('swx','clock a firstrecord a lastrecord a setting d',both(k('ca',v('clock')),k('sha',first,'p ba'),k('sha',last,'p ba'),k('sbg',T),everyrecord))
    text+=definition('swq','clock a firstrecord a lastrecord a setting d',both(k('swx',v('clock'),first,last,v('setting')),coverage))
    text+=definition('swr',params,both(k('swm',*args),k('swo',first,last,speed),
        eq(sub(v('movingend'),v('movingstart')),mul(k('svm'),T)),eq(sub(v('referenceend'),v('referencestart')),T)))
    constants=[k(CONSTANTS[n]) for n,_ in COMMON]
    text+=definition('sws','','b context['+both(k('swm',*constants),k('swo',k('ziv'),k('zix'),speed),k('swq',k('zie'),k('ziv'),k('zix'),k('zi5')))+']','e')
    text+=definition('swt','','b context['+k('swr',*constants)+']','e')
    text+=definition('swu','','b context['+both('t[k sws[]][v context]','t[k swt[]][v context]')+']','e')
    duration=dt(k('ziv'),k('zix'));gap=sub(k('zi3'),k('zi2'))
    text+=definition('swv','','b context['+both(k('bg',k('zi2'),k('zi3')),eq(gap,mul(duration,k('svt'))))+']','e')
    # For each fixed travel duration, retain the fourth-order qualification.
    ratio=v('ratio');domain=lam('ratio',CUT,both(k('ba',ratio),k('bg',sq(ratio),one)))
    text+=definition('swy','duration '+CUT,both(k('sbg',v('duration')),k('svy',domain,
        lam('ratio',CUT,mul(v('duration'),k('svz',ratio))),lam('ratio',CUT,mul(v('duration'),k('swa',ratio))),'p swb',z)))
    scale=v('scale');seconds=mul(scale,duration);gapseconds=mul(scale,gap);estimate=mul(seconds,k('svu'));error=sub(gapseconds,estimate)
    text+=definition('swk','scale '+CUT+' duration '+CUT+' gap '+CUT+' approximation '+CUT+' error '+CUT,both(k('svp',scale,k('zi5')),
        *(k('ba',v(n)) for n in ('duration','gap','approximation','error')),
        eq(v('duration'),seconds),eq(v('gap'),gapseconds),eq(v('approximation'),estimate),eq(v('error'),error)))
    text+=definition('sww','','b context['+both('t[k swv[]][v context]',q('g','scale',CUT,both(
        k('swk',scale,seconds,gapseconds,estimate,error),k('swy',seconds))))+']','e')
    text+=definition('sxa','scale '+CUT,both(k('svp',scale,k('zi5')),
        k('svr',*(k(n) for n in ('tc','zb7','svm','svt','svu','svv'))),
        k('bc',mul(seconds,mul(k('bb','n p b i'),k('swb',k('sje',speed,V)))),error),
        k('bc',error,mul(seconds,mul(k('bb','n p b c'),k('swb',k('sje',speed,V)))))))
    text+=definition('swz','','b context['+both(k('svr',*(k(n) for n in ('tc','zb7','svm','svt','svu','svv'))),
        q('f','scale',CUT,op('y',k('svp',scale,k('zi5')),k('sxa',scale))))+']','e')
    # Named attribution preserves the author's conditional and the added idealization.
    doc=parse(text);doc['statements']=statements
    doc=parse(format_graph(doc,'compact')+'''
s[k ug[k zi6[] k rd[] r[k sws[]] k rh[] k ri[]]].
s[k zfl[k zja[] k rd[] r[k sws[]] r[k swt[]] k rh[] k ri[]]].
s[k zc[k zi7[] k rd[] r[k swu[]] r[k sww[]] k rh[] k ri[]]].
''')
    basis=deepcopy(json.loads((ROOT/'data/einstein-clock-delay-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='einstein-clock-transfer-basis-v1',document='examples/v014/einstein-clock-transfer.noema')
    basis['definitions'].update(MEANINGS|{
        'swl':'同じ時計・出来事・観測系・時間単位の指示と測定済みの座標記録を、出来事と時計の共通場所に結ぶ。',
        'swm':'異なる二時計とA/B、出発・Bでの初期読み・到着の三出来事を結ぶ。初期の両時計の静止と同期、初期二出来事の同時性と指示一致、静止時計のBへの残留、到着時の同じ場所での比較を要求する。',
        'swo':'正の速さと正の所要時間について、三次元の端点変位の長さの二乗が速さと時間の積の二乗に等しい。方向をX軸に固定しない。途中の経路はこの条件だけでは確定しない。',
        'swp':'指定記録が端点間の時間内にあり、各空間成分が時間について線形補間される。直線上にあるだけでなく一様な進行を要求する。',
        'swq':'同じ時計の全ての測定済み出来事が区間内でswpを満たし、区間内の全実時刻にその時計の出来事と記録が存在する連続時間の直線等速運動条件。',
        'swx':'区間内で測定済みの同じ時計の全出来事についてswpを検査する部分条件。全時刻の記録の存在はswqで別に要求する。',
        'swr':'swmとswoに、移動時計の指示差がf*T、静止時計の指示差がTという二つの区間法則を加えた理想化。発進・停止・設定変更で追加の指示変化がないことを含む前提。',
        'sws':'同じ二時計の初期同期、三出来事と場所、正の速さ、連続時間の直線移送という設定内容。',
        'swt':'同じ移送でswrの二つの指示法則を採用する追加解釈の内容。',
        'swu':'移送の設定と二時計の指示法則を合わせた推論前提。',
        'swv':'到着時に静止時計の指示が厳密に大きく、両指示差が所要時間と遅れ率の積である内容。',
        'swy':'正の固定した所要時間に対して、総遅れの二次近似誤差が速度比の四乗のオーダーになる条件。時間が速度に依存する族の一様な評価ではない。',
        'swk':'同じ到着時指示差と所要時間を共通尺度で秒へ換算し、総遅れ・二次近似・残差を結ぶ。',
        'sww':'到着時の厳密な指示差を秒と二次近似へ結び、固定所要時間での四次以上の留保を保持する内容。',
        'swz':'同じ到着時の残差について、所要時間を掛けた四次の具体的な上下限という補足条件。原文の数値係数そのものとはしない。',
        'sxa':'指定した秒への換算尺度が有効であり、同じ到着時の実際の指示差の二次近似残差が所要時間を掛けた四次の上下限を満たす条件。'})
    decls={d['name']:d for d in doc['declarations']}
    meanings={
        'zip':'Bに初めから留まる比較用の時計。','ziq':'出発地点A。','zir':'到着地点B。',
        'zis':'移動時計がAから出発する出来事。','zit':'出発と同時刻にBで静止時計の初期指示を読む出来事。','ziu':'移動時計がBへ到着し両時計を比較する同じ出来事。',
        'ziv':'Aでの出発の観測系の座標記録。','ziw':'Bでの初期読みの観測系の座標記録。','zix':'Bでの到着の観測系の座標記録。',
        'ziy':'出発時の移動時計の指示。','ziz':'同じ初期時刻にBで読む静止時計の指示。','zi2':'到着時の移動時計の指示。','zi3':'同じ到着出来事での静止時計の指示。',
        'zi4':'移送前に二時計がKに静止して同期する設定。','zi5':'AからBへ移送し静止時計をBに残す設定。',
        'zi6':'初期同期と直線移送の条件を仮定する箇所。','zi7':'到着時の指示差と二次近似の帰結を述べる箇所。','zja':'移動時計と静止時計の区間指示法則を理想化として明示する箇所。'}
    for name,meaning in meanings.items():
        d=decls[name];basis['primitives'].append(dict(symbol=name,parameters=d['parameters'],result=d['result'],arguments=[],meaning_ja=meaning))
    basis['unresolved']+=[
        'u0126の部分記述。eigentümlicheという帰結への評価、原刊照合と原文の意味一致は未完。',
        'swqの全時刻での存在は有限の記録から証明しない。端点の変位だけで一様な直線運動とは判定しない。',
        '静止時計のBへの残留と初期の両時計の静止は文脈別の物理的関係で与える。初期の同時性と到着時の同一出来事を区別する。',
        'swrは発進と停止で追加の指示変化を生じない区間法則を明示する。原点時計の慣性運動だけから加速中の挙動を証明したことにはしない。',
        '四次の留保は所要時間を固定した評価。経路の距離を固定して速度を変え、所要時間も変える場合の誤差はT*(v/V)^4として扱い、無条件にO(v^4)とはしない。',
        '折れ線・帰還・曲線・地球上の時計への適用は後続の本文として未接続。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def main():
    for compose,name in ((generic_composed,'clock-transfer'),(source_composed,'einstein-clock-transfer')):
        text,basis=compose()
        for relative,body in ((basis['document'],text),('data/'+name+'-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/relative
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored clock transfer differs: '+relative)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Separated initial synchronization and co-located arrival clocks composed')


if __name__=='__main__':main()
