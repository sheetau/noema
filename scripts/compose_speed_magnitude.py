"""Separate signed velocity components from a nonnegative speed magnitude."""
from copy import deepcopy
import json

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, CUT, definition, v
from scripts.compose_limits import call as k, app, op, both, quant as q

FUNCTION='h['+CUT+'] '+CUT
DOMAIN='h['+CUT+'] c'


def arithmetic_definitions(real=False):
    typ=CUT if real else 'b';zero=k('bb','n p a b') if real else 'n p a b';one=k('bb','n p b b') if real else 'n p b b'
    mul=lambda a,b:k('shv' if real else 'ad',a,b)
    add=lambda a,b:k('bd' if real else 'ab',a,b)
    sub=lambda a,b:k('bf',a,b) if real else add(a,k('ac',b))
    eq=lambda a,b:k('sca',a,b) if real else op('e',a,b)
    lt=lambda a,b:k('bg' if real else 'aa',a,b)
    sq=lambda a:mul(a,a)
    params=lambda names:' '.join(n+' '+typ for n in names.split())
    valid=lambda names:[k('ba',v(n)) for n in names.split()] if real else []
    magnitude,x,y=map(v,('magnitude','x','y'))
    norm='szn' if real else 'szk'
    text=definition(norm,params('magnitude x y'),both(*valid('magnitude x y'),op('u',lt(magnitude,zero)),eq(sq(magnitude),add(sq(x),sq(y)))))
    V,s,b,u,w,X,Y=map(v,('light','speed','beta','longitudinal','transverse','outx','outy'))
    text+=definition('szo' if real else 'szl',params('light speed beta longitudinal transverse outx outy'),
        k('syt' if real else 'syq',V,s,b,u,w,X,Y,zero,one))
    W,U=map(v,('movingmag','resultmag'))
    D=add(sq(V),mul(s,u));two=add(one,one)
    numerator=mul(sq(V),sub(mul(sq(V),add(add(sq(s),sq(W)),mul(two,mul(s,u)))),mul(sq(s),sq(w))))
    text+=definition('szp' if real else 'szm',params('light speed longitudinal transverse movingmag resultmag'),
        both(*valid('light speed longitudinal transverse movingmag resultmag'),lt(zero,V),lt(sq(s),sq(V)),
            k(norm,W,u,w),op('u',lt(U,zero)),op('u',eq(D,zero)),eq(mul(sq(D),sq(U)),numerator)))
    return text


PRIMITIVES=[
    ('zkj',DOMAIN,'選択した時刻の範囲。全実時刻の存在や測定可能性をこの参照だけから補わない。'),
    ('zkk',FUNCTION,'同じ点の静止系での縦座標を時刻から得る関数。szrで履歴の測定記録へ接続する。'),
    ('zkl',FUNCTION,'同じ点の静止系での横座標を時刻から得る関数。szrで履歴の測定記録へ接続する。'),
    ('zkm',CUT,'速度の大きさを記述する評価時刻。未指定の時刻を現在日時へ固定しない。'),
    ('zkn',CUT,'同じ評価時刻での縦座標の微分値。szqで同じ関数の微分へ接続する。'),
    ('zko',CUT,'同じ評価時刻での横座標の微分値。szqで同じ関数の微分へ接続する。'),
    ('zkp',CUT,'この評価時刻でUと記す静止系の非負の速さへの参照。符号付きの縦速度成分とは異なる。'),
    ('zkq',CUT,'wと記す動く系の非負の速さへの参照。二つの符号付き速度成分と区別する。'),
    ('zkr','a','Uの二乗を座標の時間微分の二乗和で指定する本文箇所。'),
    ('zks','a','wの二乗を動く系の二速度成分の二乗和で指定する本文箇所。'),
]


def composed():
    doc=parse((ROOT/'examples/v014/einstein-motion-question.noema').read_text(encoding='utf-8'))
    statements,doc['statements']=doc['statements'],[]
    text=format_graph(doc,'compact')+arithmetic_definitions()+arithmetic_definitions(True)
    for name,typ,_ in PRIMITIVES:text+='r '+name+'[] '+typ+'.\n'
    params='domain '+DOMAIN+' x '+FUNCTION+' y '+FUNCTION+' instant '+CUT+' vx '+CUT+' vy '+CUT+' magnitude '+CUT
    text+=definition('szq',params,both(k('sjs',v('domain'),v('x'),v('instant'),v('vx')),
        k('sjs',v('domain'),v('y'),v('instant'),v('vy')),k('szn',v('magnitude'),v('vx'),v('vy'))))
    event,record,setting=map(v,('event','record','setting'))
    coord=lambda axis:k('zc6',record,k(axis))
    selected=k('zka',v('point'),event,setting);chart=k('shd',event,record,v('frame'),setting)
    match=both(k('sha',record,'p ba'),app(v('domain'),coord('zc7')),
        k('sca',coord('yn'),app(v('x'),coord('zc7'))),k('sca',coord('yo'),app(v('y'),coord('zc7'))),
        k('sca',coord('yp'),k('bb','n p a b')))
    text+=definition('szr','point a frame a domain '+DOMAIN+' x '+FUNCTION+' y '+FUNCTION+' setting d',
        both(q('g','event','a',selected),q('f','event','a',op('y',selected,both(k('zc4',event),
            q('g','record','a',chart),q('f','record','a',op('y',chart,match)))))))
    text+=definition('szs','value '+CUT+' context d',both(
        k('szr',k('zkb'),k('ra'),k('zkj'),k('zkk'),k('zkl'),v('context')),
        k('szq',k('zkj'),k('zkk'),k('zkl'),k('zkm'),k('zkn'),k('zko'),v('value'))))
    text+=definition('szt','value '+CUT+' context d',both(k('syu',k('zkb'),k('zbm'),k('zkc'),k('zkd'),v('context')),
        k('szn',v('value'),k('zkc'),k('zkd'))))
    for name,reference in (('szu','zkp'),('szv','zkq')):
        text+=definition(name,'value '+CUT+' context d',both(k('ba',v('value')),k('ba',k(reference)),k('sca',v('value'),k(reference))))
    doc=parse(text);doc['statements']=statements
    doc=parse(format_graph(doc,'compact')+'s[k zb[k zkr[] k rd[] r[p szs] r[p szu] k zkf[] k ri[]]].\n'
        +'s[k zb[k zks[] k rd[] r[p szt] r[p szv] k zkf[] k ri[]]].\n')
    basis=deepcopy(json.loads((ROOT/'data/motion-question-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='speed-magnitude-basis-v1',document='examples/v014/einstein-speed-magnitude.noema')
    decls={d['name']:d for d in doc['declarations']}
    for name,_,meaning in PRIMITIVES:
        d=decls[name];basis['primitives'].append(dict(symbol=name,parameters=d['parameters'],result=d['result'],arguments=[],meaning_ja=meaning))
    basis['definitions'].update({
        'szk':'二つの符号付き成分の二乗和を二乗に持つ非負の大きさ。有理数の関係。零も許す。',
        'szl':'既存の有理数の平面運動式syqを単位時刻に適用し、変換後の二速度成分を条件で表す。実際の出来事が時刻1にあるとは主張しない。',
        'szm':'変換前後の大きさを結ぶ有理数の二乗式。D=V²+v*u≠0の下でD²U²=V²*(V²*(v²+W²+2v*u)-v²*w_y²)。方向の成分を消さず、負のDも許す。',
        'szn':'二つの有効な実速度成分の二乗和から非負の大きさを指定する関係。正の速さだけを扱う旧syhを変更せず、静止の場合も含める。',
        'szo':'実切断上の変換後の二速度成分。既存sytの正のbetaと非零分母の条件を保持する。',
        'szp':'実切断上の変換前後の非負の大きさの二乗関係。原刊M0257の角度式をまだ同義に記述したとは扱わない。',
        'szq':'同じ定義域・同じ評価時刻における二座標関数の相対微分値と、それらから得る非負の速さを接続する。',
        'szr':'同じ点の履歴の全出来事について、指定基準系の有効な全記録の時刻が定義域に属し、二座標関数の値に一致し、第三成分が零である。空の履歴と座標記録の欠落を除く。',
        'szs':'同じ点の静止系の平面内の履歴と、同じ時刻における同じ二関数の微分から速さの候補を得る方法。',
        'szt':'同じ点の動く系での等速運動の二成分から、速さの候補を得る方法。',
        'szu':'静止系の速さを表すUという参照の値と候補値の一致。意味本体にラテン文字の綴りを埋め込まない。',
        'szv':'動く系の速さを表すwという参照の値と候補値の一致。横成分だけをwと同一視しない。'})
    basis['unresolved'] += [
        'u0135末尾のWir setzenとu0136のM0252を部分記述した。非負の速さとして読む規約を明示する。二乗式だけなら負の枝も満たすため、その枝を区別する。',
        '相対微分sjsの定義を再利用するが、一般的な微分の存在、全実時刻にわたる履歴、測定と関数の全域的な一致の機械的証明は未完。',
        'szmとszpは先行する成分式からの補助的な代数関係。角度・逆正接・三角関数、原刊照合済みのM0257との接続、平行四辺形則の近似という論述は未記述のまま。',
        'M0252の原刊照合と原文の全意味一致確認は未完。原刊906頁の別の二数式の訂正を、この数式の照合済み証拠には流用しない。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def main():
    text,basis=composed()
    for relative,body in ((basis['document'],text),('data/speed-magnitude-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
        path=ROOT/relative
        if path.exists():
            if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored speed magnitude differs: '+relative)
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Nonnegative speed magnitudes and derivative bindings composed')


if __name__=='__main__':main()
