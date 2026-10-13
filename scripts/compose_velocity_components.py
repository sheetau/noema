"""Compose constant planar motion and its boost using existing arithmetic."""
from copy import deepcopy
import json

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, CUT, definition, v
from scripts.compose_limits import call as k, op, both, quant as q


def equations(real=False):
    names=('longitudinal','transverse','x','y','z','time')
    u,w,x,y,z,t=map(v,names)
    V,s,b=map(v,('light','speed','beta'))
    zero=k('bb','n p a b') if real else 'n p a b'
    mul=lambda a,b:k('shv' if real else 'ad',a,b)
    add=lambda a,b:k('bd' if real else 'ab',a,b)
    eq=lambda a,b:k('sca',a,b) if real else op('e',a,b)
    typ=CUT if real else 'b'
    params=lambda ns:' '.join(n+' '+typ for n in ns)
    valid=lambda ns:[k('ba',v(n)) for n in ns] if real else []
    text=definition('syr' if real else 'syp',params(names),both(*valid(names),eq(x,mul(u,t)),eq(y,mul(w,t)),eq(z,zero)))
    denominator=add(mul(V,V),mul(s,u))
    if real:text+=definition('sys',params(('light','speed','longitudinal')),denominator,CUT)
    allnames=('light','speed','beta')+names
    text+=definition('syt' if real else 'syq',params(allnames),both(*valid(allnames),
        k('srd' if real else 'sra',V,s,b),op('u',eq(denominator,zero)),
        eq(mul(denominator,x),mul(mul(V,V),mul(add(u,s),t))),
        eq(mul(mul(b,denominator),y),mul(mul(V,V),mul(w,t))),eq(z,zero)))
    return text


PRIMITIVES=[
    ('zka','a a d','c',['point','event','setting'],'指定する点状の運動対象の履歴に属する出来事。座標値や運動法則をこの関係だけから補わない。点状の対象と出来事の物理的な実現の説明は未完。'),
    ('zkb','','a',[],'§5冒頭で運動を考察する一つの点を指す。'),
    ('zkc','',CUT,[],'その点の動く基準系での縦方向速度成分。同じ値を全出来事で用いる定数。正負を限定しない。'),
    ('zkd','',CUT,[],'その点の動く基準系での横方向速度成分。同じ値を全出来事で用いる定数。正負を限定しない。'),
    ('zke','','d',[],'§5冒頭の平面内での等速運動を扱う設定。'),
    ('zkf','','a',[],'§5冒頭の運動を仮定し変換する議論の適用範囲。'),
    ('zkg','','a',[],'動く系での運動方程式と成分の定数性を指定する本文箇所。'),
    ('zkh','','a',[],'§3の変換式を代入して静止系での運動方程式を得る本文箇所。'),
]


def composed():
    doc=parse((ROOT/'examples/v014/einstein-earth-clocks.noema').read_text(encoding='utf-8'))
    statements,doc['statements']=doc['statements'],[]
    text=format_graph(doc,'compact')+equations()+equations(True)
    for name,params,result,_,_ in PRIMITIVES:text+='r '+name+'['+params+'] '+result+'.\n'
    coord=lambda record,axis:k('zc6',record,k(axis))
    coordinates=lambda record:[coord(record,axis) for axis in ('yn','yo','yp','zc7')]
    point,event,record,setting=map(v,('point','event','record','setting'))
    selected=k('zka',point,event,setting)
    def graph(frame,formula):
        chart=k('shd',event,record,frame,setting)
        return both(q('g','event','a',selected),q('f','event','a',op('y',selected,both(k('zc4',event),
            q('g','record','a',chart),q('f','record','a',op('y',chart,both(k('sha',record,'p ba'),formula)))))))
    u,w=map(v,('longitudinal','transverse'))
    text+=definition('syu','point a frame a longitudinal '+CUT+' transverse '+CUT+' setting d',
        both(k('ba',u),k('ba',w),graph(v('frame'),k('syr',u,w,*coordinates(record)))))
    V,s,b=map(v,('light','speed','beta'))
    text+=definition('syv','point a frame a light '+CUT+' speed '+CUT+' beta '+CUT+' longitudinal '+CUT+' transverse '+CUT+' setting d',
        graph(v('frame'),k('syt',V,s,b,u,w,*coordinates(record))))
    V,s,u,w=k('tc'),k('zb7'),k('zkc'),k('zkd');b=k('soy',V,s);setting=k('zke')
    text+=definition('syw','',both(op('u',op('e',k('ra'),k('zbm'))),
        k('zgj',k('zbm'),k('ra'),k('zbo',k('ra'),k('yn'),setting),s,k('ta'),k('rb'),setting),
        k('syu',k('zkb'),k('zbm'),u,w,setting)))
    first,second=map(v,('first','second'))
    selected=k('zka',k('zkb'),event,setting)
    chart=lambda rec,frame:k('shd',event,rec,k(frame),setting)
    text+=definition('syx','',both(q('g','event','a',selected),q('f','event','a',op('y',selected,
        both(q('g','first','a',chart(first,'ra')),q('g','second','a',chart(second,'zbm')),
            q('f','first','a',q('f','second','a',op('y',both(chart(first,'ra'),chart(second,'zbm')),k('ssn',first,second)))))))))
    text+=definition('syy','','b context['+both(k('syw'),k('syx'),k('srd',V,s,b),
        op('u',k('sca',k('sys',V,s,u),k('bb','n p a b'))))+']','e')
    text+=definition('syz','','b context['+k('syv',k('zkb'),k('ra'),V,s,b,u,w,setting)+']','e')
    text+=definition('sza','','b context['+k('syw')+']','e')
    doc=parse(text);doc['statements']=statements
    doc=parse(format_graph(doc,'compact')+'s[k ug[k zkg[] k rd[] r[k sza[]] k zkf[] k ri[]]].\n'
        +'s[k zc[k zkh[] k rd[] r[k syy[]] r[k syz[]] k zkf[] k ri[]]].\n')
    basis=deepcopy(json.loads((ROOT/'data/earth-clocks-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='velocity-components-basis-v1',document='examples/v014/einstein-velocity-components.noema')
    decls={d['name']:d for d in doc['declarations']}
    for name,_,_,labels,meaning in PRIMITIVES:
        d=decls[name];basis['primitives'].append(dict(symbol=name,parameters=d['parameters'],result=d['result'],arguments=labels,meaning_ja=meaning))
    basis['definitions'].update({
        'syp':'原点を通る平面内の等速運動x=u*t,y=w*t,z=0の有理数条件。時間ごとの速度再選択を含まない。',
        'syq':'有理数の速度合成後の運動方程式。D=V²+v*u≠0、D*x=V²*(u+v)*t、beta*D*y=V²*w*t、z=0。betaの正の枝と許容速度を保持する。',
        'syr':'実切断で表す平面内の等速運動。全引数の有効性とx=u*t,y=w*t,z=0を要求する。',
        'sys':'速度合成式の分母をV²倍した値V²+v*u。値を定義するだけでは非零性を保証しない。',
        'syt':'実切断上の変換後の運動方程式。正のbetaと非零の分母を明示し、正負の速度成分を許す。分母を払った等式で除算の定義域を保つ。',
        'syu':'指定点の履歴の全出来事に同じ二つの速度成分を使い、指定基準系の全座標記録がsyrを満たす。空の履歴と座標の欠落を除く。全実時刻の出来事の存在は別の課題。',
        'syv':'指定点の履歴の全出来事について、指定基準系での全座標記録がsytを満たす。別の点や別の出来事の座標を代用しない。',
        'syw':'異なる二基準系の縦軸に沿う相対運動と、動く系での指定点の平面内の等速運動を結ぶ設定。',
        'syx':'同じ点の同じ出来事に対する両基準系の記録が存在し、全記録対が係数1の既存四座標変換ssnを満たす。',
        'syy':'元の運動と同じ出来事の座標変換、許容速度と非零分母を合わせた代入の前提内容。',
        'syz':'静止系での同じ点の変換後の運動を表す内容。',
        'sza':'動く系での運動を仮定として指定する内容。現実の出来事の断言と区別する。'})
    basis['unresolved'] += [
        'u0130〜u0134の部分草案。u0133冒頭の「運動を求める」課題提示、§5見出し、後続の近似・速度の大きさ・角度はこの追加に含めない。',
        '点状の対象・出来事・測定・基準系の物理的な基礎関係と、全実時刻にわたる履歴の存在の説明は未完。有限の具体例で無限時間の運動を証明しない。',
        '非零分母は商を運動方程式として読むための明示した条件。点の速度に光速未満という条件を原文に先回りして補わず、負の分母も許す。',
        '有理数多項式の代入検査は実切断上の一般的な体の法則の機械的証明ではない。原刊照合と原文の全意味一致確認は未完。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def main():
    text,basis=composed()
    for relative,body in ((basis['document'],text),('data/velocity-components-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
        path=ROOT/relative
        if path.exists():
            if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored velocity components differ: '+relative)
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Planar motion and transformed velocity components composed')


if __name__=='__main__':main()
