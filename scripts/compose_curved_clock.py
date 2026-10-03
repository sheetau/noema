"""Connect the explicitly assumed extension from polygons to smooth curves."""
from copy import deepcopy
import json

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_polygon_clock import ROOT, CUT, PATH, COMPARE as POLYGON_COMPARE, params, args
from scripts.compose_origin_clock import definition
from scripts.compose_limits import call as k, app, op, both, quant as q, lam

PHI='h['+CUT+'] '+CUT
v=lambda name:'v '+name
CURVE=[p for p in PATH if p[0] not in ('segments','start','end')]+[(name,PHI) for name in ('x','y','z','vx','vy','vz')]
COMPARE=CURVE+POLYGON_COMPARE[len(PATH):]


def continuity_declarations():
    aliases={'la':'sjo','lb':'sjp','le':'sxt','lf':'sxu','lg':'sxs'}
    def rename(node):
        if isinstance(node,list):return [rename(x) for x in node]
        if not isinstance(node,dict):return node
        result={key:rename(value) for key,value in node.items()}
        if result.get('symbol') in aliases:result['symbol']=aliases[result['symbol']]
        if result.get('kind')=='definition':result['name']=aliases.get(result['name'],result['name'])
        return result
    old=parse((ROOT/'examples/v011/limits.noema').read_text(encoding='utf-8'))
    return [rename(d) for d in old['declarations'] if d['name'] in ('le','lf','lg')]


def composed():
    doc=parse((ROOT/'examples/v014/einstein-polygon-clock.noema').read_text(encoding='utf-8'))
    statements,doc['statements']=doc['statements'],[]
    doc['declarations']+=continuity_declarations();text=format_graph(doc,'compact')
    frame=k('ra');unit=k('rb');zero=k('bb','n p a b')
    eq=lambda a,b:k('sca',a,b);mul=lambda a,b:k('shv',a,b)
    record=lambda event:app(v('record'),event)
    coord=lambda rec,axis:k('zc6',rec,k(axis))
    first,last=v('first'),v('last');lo=coord(record(first),'zc7');hi=coord(record(last),'zc7')
    inside=lambda time:k('sxs',lo,hi,time)
    domain=lam('time',CUT,inside(v('time')))
    speed2=mul(v('speed'),v('speed'))
    velocity2=k('bd',mul(v('vx'),v('vx')),k('bd',mul(v('vy'),v('vy')),mul(v('vz'),v('vz'))))
    text+=definition('syh',' '.join(name+' '+CUT for name in ('speed','vx','vy','vz')),
        both(k('sbg',v('speed')),*(k('ba',v(name)) for name in ('vx','vy','vz')),eq(velocity2,speed2)))
    text+=definition('sxv',params(CURVE),both(k('sha',record(first),'p ba'),k('sha',record(last),'p ba'),k('bg',lo,hi),
        k('sbg',v('speed')),k('srd',k('tc'),v('speed'),k('soy',k('tc'),v('speed'))),
        *(k('sxu',domain,v(name)) for name in ('x','y','z','vx','vy','vz')),
        q('f','time',CUT,op('y',inside(v('time')),both(
            *(k('sjs',domain,v(axis),v('time'),app(v('v'+axis),v('time'))) for axis in ('x','y','z')),
            k('syh',v('speed'),*(app(v('v'+axis),v('time')) for axis in ('x','y','z'))))))))
    # Bind the curve to measured records before making any elapsed-clock law.
    pointparams=CURVE+[('event','a'),('observed','a')]
    time=coord(v('observed'),'zc7')
    text+=definition('sxw',params(pointparams),both(k('swl',v('clock'),v('event'),v('observed'),app(v('reading'),v('event')),v('setting')),
        k('sha',record(v('event')),'p ba'),k('shh',v('observed'),record(v('event'))),inside(time),
        *(eq(coord(v('observed'),axis),app(v(component),time)) for axis,component in (('yn','x'),('yo','y'),('yp','z')))))
    incidence=both(k('zc4',v('event')),k('sha',v('observed'),'p ba'),k('shd',v('event'),v('observed'),frame,v('setting')),
        q('g','place','a',both(k('zab',v('clock'),v('event'),v('place'),frame,v('setting')),k('cb',v('event'),v('place'),frame))))
    text+=definition('sxx',params(CURVE),both(k('ca',v('clock')),k('ci',unit),k('bg',lo,hi),
        q('f','event','a',q('f','observed','a',op('y',both(incidence,inside(time)),k('sxw',*args(CURVE),v('event'),v('observed')))))))
    # Every real time needs an event, and each reading at that event must agree.
    coverage=q('f','time',CUT,op('y',inside(v('time')),q('g','event','a',q('g','observed','a',
        both(k('sxw',*args(CURVE),v('event'),v('observed')),eq(time,v('time')))))))
    unique=q('f','event','a',q('f','observed','a',op('y',both(incidence,inside(time)),q('f','value',CUT,
        op('y',both(k('ba',v('value')),k('ce',v('clock'),v('event'),frame,unit,v('value'))),eq(v('value'),app(v('reading'),v('event'))))))))
    text+=definition('sxy',params(CURVE),both(k('sxx',*args(CURVE)),coverage,unique))
    text+=definition('sxz',params(CURVE),both(op('u',op('e',first,last)),k('xm',v('clock'),frame,v('setting')),
        *(k('sxw',*args(CURVE),event,record(event)) for event in (first,last))))
    # The old endpoint comparison and gap definitions do not use segment data.
    def adapter(items):
        unused={'segments':'l[a][]','start':lam('ignored','a',first),'end':lam('ignored','a',last)}
        return [unused.get(n,v(n)) for n,_ in items]
    oldpath=adapter(PATH);oldcompare=adapter(POLYGON_COMPARE)
    text+=definition('sya',params(COMPARE),both(k('sxv',*args(CURVE)),k('sxy',*args(CURVE)),k('sxz',*args(CURVE)),
        k('sxl',*oldcompare),q('g','scale',CUT,k('svp',v('scale'),v('setting')))))
    text+=definition('syc',params(CURVE),k('sxo',*oldpath))
    text+=definition('syf',params(COMPARE),k('sxp',*oldcompare))
    for symbol,closed in (('syg',False),('syd',True)):
        premise=k('sya',*args(COMPARE))
        if closed:premise=both(premise,k('syc',*args(CURVE)))
        body=op('y',premise,k('syf',*args(COMPARE)))
        for name,sort in reversed(COMPARE):body=q('f',name,sort,body)
        text+=definition(symbol,'','b context['+body+']','e')
    text+=definition('syb','','b context['+op('y','t[k sxq[]][v context]','t[k syg[]][v context]')+']','e')
    text+=definition('sye','','b context['+both('t[k sxq[]][v context]','t[k syb[]][v context]')+']','e')
    text+='r ui[a a d] c.r zjd[] a.r zje[] a.r zjf[] a.\n'
    doc=parse(text);doc['statements']=statements
    doc=parse(format_graph(doc,'compact')+'''
s[k ui[k rd[] k zjb[] k ri[]]].
s[k ug[k zje[] k rd[] r[k syb[]] k zjd[] k ri[]]].
s[k uh[k zjf[] k rd[] r[k syd[]] k zjd[] k ri[]]].
s[k zc[k zjf[] k rd[] r[k sye[]] r[k syd[]] k zjd[] k ri[]]].
''')
    basis=deepcopy(json.loads((ROOT/'data/polygon-clock-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='curved-clock-basis-v1',document='examples/v014/einstein-curved-clock.noema')
    basis['definitions'].update({
        'sxs':'既存lgの記号を置換した閉区間への所属。両端と入力が有効な実切断であり、入力は下端以上・上端以下である。',
        'sxt':'既存leを再利用する定義域に相対的な連続性。全ての正の精度に対して近傍を選び、その近傍内の全入力を検査する。',
        'sxu':'既存lfを再利用する定義域の全点での連続性。有限標本で認定しない。',
        'syh':'三つの有効な速度成分の平方和が、指定した共通の正の速さの平方に一致する。向きの固定、微分との一致、全時刻の成立は別条件である。',
        'sxv':'端点記録が定める正の時間区間で、三座標と三速度成分が連続であり、速度が座標の相対微分に等しく、大きさが共通の正の光速未満の速さに一致するC1の曲線モデル。指示の進み率の法則は含まない。',
        'sxw':'同じ時計の測定記録と指示を、出来事からの候補記録・指示関数と結ぶ。記録の同一性は四成分の値で比較し、三位置がその時刻の曲線の値と一致する。',
        'sxx':'区間内の測定済みの全出来事と記録でsxwを要求する部分条件。途中の全時刻の存在は含まない。',
        'sxy':'sxxに加え、全実時刻に時計の出来事と記録が存在し、同じ出来事の有効な指示は全て同じ候補指示に一致する。',
        'sxz':'出発と帰着は異なる出来事であり、両端の時計・曲線・記録・指示が同じ設定に結ばれる。',
        'sya':'C1の曲線、全時間の時計の対応、端点、初期同期と比較時計の残留、秒への尺度をまとめた観測設定。遅れの式を設定の定義へ埋め込まない。',
        'syc':'曲線の両端が正の経過時間後に同じ位置へ戻る。sxoの端点条件を再利用し、空の区間列を実際の運動経路と主張するものではない。',
        'syf':'sxpの同じ到着差と近似留保を曲線の端点に適用する。共通の時間単位と秒への換算を保持する。',
        'syg':'曲線の観測設定が成立すれば、同じ到着差と近似留保が成立するという全ケースの内容。',
        'syb':'前段の折れ線の結果sxqが成立すれば、それを曲線へ拡張したsygも成立する、という仮定の内容。引用された先行結果への参照だけでなく、その内容を条件部に使う。',
        'syd':'sygの設定に位置への帰還を加えた全ケースについての条件付き帰結。',
        'sye':'前段の折れ線の結果sxqと、曲線への拡張仮定sybを合わせた推論前提。'})
    old=json.loads((ROOT/'data/conditional-discourse-basis-v1.json').read_text(encoding='utf-8'))
    basis['primitives'].append(deepcopy(next(p for p in old['primitives'] if p['symbol']=='ui')))
    for name,meaning in (('zjd','曲線への拡張仮定を採用する推論範囲。'),('zje','折れ線の結果を曲線へ拡張すると仮定する箇所。'),('zjf','その範囲内で閉曲線の帰還時計の帰結を提示する箇所。')):
        basis['primitives'].append(dict(symbol=name,parameters=[],result='individual',arguments=[],meaning_ja=meaning))
    basis['unresolved'] += [
        'u0128の地球上の時計の比較より前を部分記述した。連続して曲がる経路を、時間区間上のC1座標と連続した速度によるモデルで読む。両端の微分は片側であり、繰返し周回の速度の周期性までは要求しない。',
        '曲線の遅れの法則はsybで仮定として採用する。C1幾何、有限観測、前段の慣性系の式だけから加速時計の応答を証明していない。',
        '物理的主張の真偽の証明と、その主張・仮定をNoemaで記述できることは別の課題である。未証明であることだけを言語の表現不能とは扱わない。',
        '全実時刻の存在、C1条件、全曲線についての成立を有限標本で認定しない。原刊照合と原文との全意味一致、基礎概念の説明は未完。',
        '地球の赤道と極の時計の比較とその条件は後続の接続課題。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def main():
    text,basis=composed()
    for relative,body in ((basis['document'],text),('data/curved-clock-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
        path=ROOT/relative
        if path.exists():
            if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored curved clock differs: '+relative)
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Curve extension assumption connected to polygon content')


if __name__=='__main__':main()
