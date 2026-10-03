"""Bind arbitrary finite polygon legs to one clock and shared corner events."""
from copy import deepcopy
import json

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_clock_transfer import ROOT, CUT
from scripts.compose_origin_clock import definition
from scripts.compose_limits import call as k, app, op, both, quant as q, lam

v=lambda n:'v '+n
PATH=[('segments','j[a]'),('start','h[a] a'),('end','h[a] a'),('record','h[a] a'),
      ('reading','h[a] '+CUT),('clock','a'),('first','a'),('last','a'),('speed',CUT),('setting','d')]
COMPARE=PATH+[('reference','a'),('initialevent','a'),('initialrecord','a'),('referencestart',CUT),('referenceend',CUT),('initial','d')]
params=lambda items:' '.join(n+' '+s for n,s in items)
args=lambda items:[v(n) for n,_ in items]


def composed():
    doc=parse((ROOT/'examples/v014/einstein-clock-transfer.noema').read_text(encoding='utf-8'))
    statements,doc['statements']=doc['statements'],[]
    text=format_graph(doc,'compact')
    zero=k('bb','n p a b');frame=k('ra');unit=k('rb')
    eq=lambda a,b:k('sca',a,b);sub=lambda a,b:k('bf',a,b);mul=lambda a,b:k('shv',a,b)
    record=lambda event:app(v('record'),event)
    read=lambda event:app(v('reading'),event)
    coord=lambda rec,axis:k('zc6',rec,k(axis))
    duration=lambda first,last:sub(coord(record(last),'zc7'),coord(record(first),'zc7'))
    first,last=v('first'),v('last');rate=k('stw',k('tc'),v('speed'))
    a,b=app(v('start'),v('segment')),app(v('end'),v('segment'))
    # Same sequence laws as finite-paths, with separate symbols in this vocabulary.
    text+=definition('sxb','segments j[a] property h[a] c',op('q',v('segments'),op('e','n p a b','n p a b'),
        'i[state c segment a]['+both(v('state'),app(v('property'),v('segment')))+']'))
    text+=definition('sxc','segments j[a] start h[a] a end h[a] a first a last a',app(op('q',v('segments'),lam('point','a',op('e',v('point'),first)),
        'i[state h[a] c segment a]['+lam('point','a',both(app(v('state'),a),op('e',v('point'),b)))+']'),last))
    text+=definition('sxd','segments j[a] measure h[a] '+CUT,op('q',v('segments'),zero,
        'i[state '+CUT+' segment a]['+k('bd',v('state'),app(v('measure'),v('segment')))+']'),CUT)
    legparams='clock a first a last a record h[a] a reading h[a] '+CUT+' setting d'
    text+=definition('sxe',legparams,both(op('u',op('e',first,last)),
        *(k('swl',v('clock'),event,record(event),read(event),v('setting')) for event in (first,last))))
    text+=definition('sxf','first a last a record h[a] a reading h[a] '+CUT+' speed '+CUT,
        eq(sub(read(last),read(first)),mul(rate,duration(first,last))))
    binding=k('sxe',v('clock'),a,b,v('record'),v('reading'),v('setting'))
    text+=definition('sxg',params(PATH),both(k('aa','n p a b','d[v segments]'),
        k('sxc',v('segments'),v('start'),v('end'),first,last),k('xm',v('clock'),frame,v('setting')),
        k('sxb',v('segments'),lam('segment','a',both(binding,k('swo',record(a),record(b),v('speed')),
            k('swx',v('clock'),record(a),record(b),v('setting')))))))
    text+=definition('sxh',params(PATH),both(k('sxg',*args(PATH)),k('sxb',v('segments'),lam('segment','a',
        k('swq',v('clock'),record(a),record(b),v('setting'))))))
    text+=definition('sxi',params(PATH),k('sxb',v('segments'),lam('segment','a',
        k('sxf',a,b,v('record'),v('reading'),v('speed')))))
    text+=definition('sxj',params(PATH),k('sxd',v('segments'),lam('segment','a',duration(a,b))),CUT)
    text+=definition('sxk',params(PATH),k('sxd',v('segments'),lam('segment','a',sub(read(b),read(a)))),CUT)
    initialrecord=v('initialrecord');T=duration(first,last)
    text+=definition('sxl',params(COMPARE),both(op('u',op('e',v('clock'),v('reference'))),op('u',op('e',v('initial'),v('setting'))),
        k('x4',v('clock'),frame,v('initial')),k('x4',v('reference'),frame,v('initial')),k('x4',v('reference'),frame,v('setting')),
        k('qo',v('clock'),v('reference'),frame,unit,v('initial')),
        k('swl',v('clock'),first,record(first),read(first),v('initial')),
        k('swl',v('reference'),v('initialevent'),initialrecord,v('referencestart'),v('initial')),
        k('swl',v('reference'),last,record(last),v('referenceend'),v('setting')),
        eq(coord(record(first),'zc7'),coord(initialrecord,'zc7')),eq(read(first),v('referencestart')),
        *(eq(coord(initialrecord,axis),coord(record(last),axis)) for axis in ('yn','yo','yp')),
        q('g','place','a',both(k('zab',v('clock'),last,v('place'),frame,v('setting')),
            k('zab',v('reference'),last,v('place'),frame,v('setting')),k('cb',last,v('place'),frame)))))
    text+=definition('sxm',params(COMPARE),both(k('sxi',*args(PATH)),eq(sub(v('referenceend'),v('referencestart')),T)))
    gap=sub(v('referenceend'),read(last))
    text+=definition('sxn',params(COMPARE),both(k('bg',read(last),v('referenceend')),eq(gap,mul(T,sub(k('bb','n p b b'),rate)))))
    text+=definition('sxo',params(PATH),both(k('sbg',T),op('u',op('e',first,last)),
        *(eq(coord(record(first),axis),coord(record(last),axis)) for axis in ('yn','yo','yp'))))
    scale=v('scale');seconds=mul(scale,T)
    text+=definition('sxp',params(COMPARE),both(k('sxn',*args(COMPARE)),q('g','scale',CUT,
        both(k('svp',scale,v('setting')),k('swy',seconds)))))
    for name,closed in (('sxq',False),('sxr',True)):
        premise=both(k('sxh',*args(PATH)),k('sxl',*args(COMPARE)),k('sxm',*args(COMPARE)),
            q('g','scale',CUT,k('svp',scale,v('setting'))))
        if closed:premise=both(premise,k('sxo',*args(PATH)))
        body=op('y',premise,k('sxp',*args(COMPARE)))
        for n,s in reversed(COMPARE):body=q('f',n,s,body)
        text+=definition(name,'','b context['+body+']','e')
    text+='r zjb[] a.r zjc[] a.\n'
    doc=parse(text);doc['statements']=statements
    doc=parse(format_graph(doc,'compact')+'''
s[k uh[k zjb[] k rd[] r[k sxq[]] k rh[] k ri[]]].
s[k zdg[k zjb[] k rd[] r[k sxq[]] k rh[] k ri[]]].
s[k uh[k zjc[] k rd[] r[k sxr[]] k rh[] k ri[]]].
''')
    basis=deepcopy(json.loads((ROOT/'data/einstein-clock-transfer-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='polygon-clock-basis-v1',document='examples/v014/einstein-polygon-clock.noema')
    basis['definitions'].update({
        'sxb':'有限列の全出現で性質が成立する。空列なら真。',
        'sxc':'有限列の区間を同じ出来事で順に接続し、指定した出発・到着出来事を結ぶ。空列なら両者の同一性を要求する。',
        'sxd':'有限列の各出現に対応する実数切断の値を順次加算する。空列の値は零。入力の有効性は利用側で課す。',
        'sxe':'同じ時計の異なる二出来事の記録・指示・場所をswlで結ぶ。出来事から記録と指示への関数を経路全体で共有する。',
        'sxf':'指定した二出来事間の指示差が、共通速度の進み率と座標時間差の積になる理想的な区間法則。',
        'sxg':'非空の接続区間列で、同じ時計の全端点を結び、共通の正の速さと各区間の測定済み記録の直線等速条件を課す。全時刻の存在は含まない。',
        'sxh':'sxgに、全区間の全実時刻で時計の出来事と直線等速の記録が存在するswqを加える。',
        'sxi':'経路の全区間でsxfを採用する。角で同じ出来事と単一の指示関数を共有し、区間間の指示のリセットを許さない。加速の一般法則は導かない。',
        'sxj':'全区間の座標時間差の和。順序の正当性や同じ時計であることを単独では要求しない。',
        'sxk':'全区間の指示差の和。同じ指示関数の端点を用いる。',
        'sxl':'共通の初期設定での静止と同期、初期指示の一致、比較時計の終着位置への残留、到着の同じ出来事と場所での比較。帰還では初期の場所も一致できる。',
        'sxm':'同じ経路の全区間に理想指示法則を課し、静止時計の指示差は全座標時間差に等しいとする前提。',
        'sxn':'到着で移動時計が厳密に遅れ、指示差が全所要時間と共通速さの遅れ率の積である結論条件。前提の代わりには用いない。',
        'sxo':'正の全時間の後に、異なる出来事で同じ三座標位置へ帰還する条件。出発と帰着の出来事を同一視しない。',
        'sxp':'到着指示差の結論に、秒への有効な尺度と、固定した全所要時間に対する四次以上の近似誤差の留保を接続する。',
        'sxq':'任意の有限折れ線について、同じ時計と共通速さ、同期、全区間の指示法則を前提としてsxpを述べる内容。全列の成立を有限検査で認定しない。',
        'sxr':'sxqと同じ前提に位置への帰還を加えた条件付き内容。'})
    for name,meaning in (('zjb','折れ線でも同じ結果が成立すると著者が直ちに認める箇所。'),('zjc','出発と到着の場所が一致する場合も成立すると述べる箇所。')):
        basis['primitives'].append(dict(symbol=name,parameters=[],result='individual',arguments=[],meaning_ja=meaning))
    basis['unresolved'] += [
        'u0127の部分記述。共通の速さを前段から引き継ぐ読みである。各区間で速さを変える場合は別の加重和の式が必要。',
        '角での方向転換・発進・停止に追加の時計指示変化がないことをsxi/sxmの前提として明示する。加速中の機構を慣性時計から導出してはいない。',
        '全時刻の存在と全有限列の一般成立は有限標本で証明しない。時計・基準系・場所・同期・測定の基礎概念と原刊照合、原文との全意味一致は残る。',
        '連続曲線へ拡張する仮定の発話と地球上の時計への適用は後続の接続課題。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def main():
    text,basis=composed()
    for relative,body in ((basis['document'],text),('data/polygon-clock-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
        path=ROOT/relative
        if path.exists():
            if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored polygon differs: '+relative)
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Polygon clock with shared corner events composed')


if __name__=='__main__':main()
