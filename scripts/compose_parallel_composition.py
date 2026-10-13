"""Represent consecutive normalized boosts and their same-event composition."""
from copy import deepcopy
import json

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, CUT, definition, v
from scripts.compose_limits import call as k, op, both, quant as q


def definitions():
    names='light speed moving beta otherbeta x y z time xx yy zz tt xxx yyy zzz ttt'.split()
    V,s,w,b,c,*coords=map(v,names);first,middle,last=coords[:4],coords[4:8],coords[8:]
    one='n p b b'
    text=definition('s4j',' '.join(n+' b' for n in names),both(
        k('srb',V,s,b,one,*first,*middle),k('srb',V,w,c,one,*middle,*last)))
    # A coefficient relation, not an assertion that the result is already beta(U).
    B=v('combined');mul=lambda x,y:k('ad',x,y)
    text+=definition('s4k','light b speed b moving b beta b otherbeta b combined b',
        op('e',mul(mul(V,V),B),mul(mul(b,c),k('ab',mul(V,V),mul(s,w)))))
    first,middle,last=map(v,('first','middle','last'))
    normalized='i[speed '+CUT+']['+k('bb',one)+']'
    text+=definition('s4l','first a last a light '+CUT+' speed '+CUT,k('sre',first,last,V,s,normalized))
    text+=definition('s4m','first a middle a last a light '+CUT+' speed '+CUT+' moving '+CUT,
        both(k('s4l',first,middle,V,s),k('s4l',middle,last,V,w)))
    frames=list(map(v,('initial','intermediate','final')));event,setting=v('event'),v('setting')
    distinct=both(*(op('u',op('e',frames[i],frames[j])) for i,j in ((0,1),(0,2),(1,2))))
    text+=definition('s4n','initial a intermediate a final a event a first a middle a last a setting d',
        both(distinct,k('zc4',event),*(k('shd',event,rec,frame,setting) for rec,frame in zip((first,middle,last),frames))))
    tri=k('s4n',*frames,event,first,middle,last,setting)
    def records(mode,body):
        for name in reversed(('first','middle','last')):body=q(mode,name,'a',body)
        return body
    text+=definition('s4o','initial a intermediate a final a setting d relation h[a a a] c',
        both(distinct,q('g','event','a',k('zc4',event)),
            q('f','event','a',op('y',k('zc4',event),records('g',tri))),
            q('f','event','a',records('f',op('y',tri,'c[v relation][v first v middle v last]')))))
    return text


def composed():
    doc=parse((ROOT/'examples/v014/einstein-light-invariance.noema').read_text(encoding='utf-8'))
    statements,doc['statements']=doc['statements'],[]
    text=format_graph(doc,'compact')+definitions()
    text+='r zlo[] a.r zlp[] d.r zlq[] a.r zlr[] a.r zls[] a.r zlt[] '+CUT+'.\n'
    V,s,w=k('tc'),k('zb7'),k('zlt');frames=[k(x) for x in ('ra','zbm','zlo')];setting=k('zlp')
    distinct=both(*(op('u',op('e',frames[i],frames[j])) for i,j in ((0,1),(0,2),(1,2))))
    motion=lambda moving,rest,speed:k('zgj',moving,rest,k('zbo',rest,k('yn'),setting),speed,k('ta'),k('rb'),setting)
    text+=definition('s4p','','b context['+both(distinct,motion(frames[1],frames[0],s),motion(frames[2],frames[1],w))+']','e')
    first,middle,last=map(v,('first','middle','last'))
    chain='i[first a middle a last a]['+k('s4m',first,middle,last,V,s,w)+']'
    direct='i[first a middle a last a]['+k('s4l',first,last,V,k('s3j',V,s,w))+']'
    for name,relation in (('s4q',chain),('s4r',direct)):
        text+=definition(name,'','b context['+k('s4o',*frames,setting,relation)+']','e')
    text+=definition('s4s','','b context['+both('t[k s4p[]][v context]','t[k s4q[]][v context]')+']','e')
    doc=parse(text);doc['statements']=statements
    doc=parse(format_graph(doc,'compact')+'''
s[k ug[k zlr[] k rd[] r[k s4p[]] k zlq[] k ri[]]].
s[k zc[k zls[] k rd[] r[k s4s[]] r[k s4r[]] k zlq[] k ri[]]].
''')
    basis=deepcopy(json.loads((ROOT/'data/light-invariance-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='parallel-composition-basis-v1',document='examples/v014/einstein-parallel-composition.noema')
    decls={d['name']:d for d in doc['declarations']}
    for name,meaning in (
        ('zlo','§5末尾で新たに導入する第三座標系k′。§3の逆速度による第三系や既存の点と同一視しない。'),
        ('zlp','§5末尾の二つの平行な座標変換を続けて適用する設定。'),
        ('zlq','第三系を導入して合成変換を考察する仮定範囲。'),
        ('zlr','第三系と、その原点の中間系の縦軸に沿う速度を設定する箇所。'),
        ('zls','二つの変換を合成して、速度の引数だけを置き換えた同形式の四式を得る箇所。'),
        ('zlt','第三系原点の、中間系に対する速度w。前の点運動の速さzkqとの同一性を字面だけから追加しない。')):
        d=decls[name];basis['primitives'].append(dict(symbol=name,parameters=d['parameters'],result=d['result'],arguments=[],meaning_ja=meaning))
    basis['definitions'].update({
        's4j':'同じ中間四座標を共有し、係数1の符号付き四座標変換srbをv、wで順に二回適用する有理数の関係。正のβと光速未満の速度条件は各適用で要求する。',
        's4k':'合成係数BについてV²B=β(v)β(w)(V²+vw)を指定する有理数の関係。それだけでBの正性や合成速度のβ条件を保証したとはしない。',
        's4l':'任意の光速度と符号付き速度で、係数を1とした既存sreの四座標式を二記録に適用する。ssnの固定された速度参照を変更しない。',
        's4m':'同じ中間記録を共有する二つのs4l。最後の時刻や横座標を省かない。',
        's4n':'互いに異なる三系で同じ出来事・設定を記述した三つの記録。別の出来事の中間記録を接続しない。',
        's4o':'非空の対象出来事の全域で三系の記録が存在し、対応する全三記録で指定する関係が成立する。複数の記録から都合のよい一つだけを選ばない。',
        's4p':'既存のKとkに加えた第三系k′が、kの縦軸に沿い速度wで平行並進する設定。Kに対するkの速度v、単位と設定も結ぶ。',
        's4q':'同じ対象出来事の全域で、Kからk、kからk′への二つの係数1の変換式を適用する内容。§3の原点・尺度の規約を採用した形であり、任意の原点ずれは含まない。',
        's4r':'同じ全三記録に対して、Kからk′への式を同じs4lにより記述し、速度引数へ(v+w)/(1+vw/V²)を与える。βの引数もこの値になる。',
        's4s':'第三系の設定s4pと二回の変換s4qを合わせた、合成の結論に対する前提内容。'})
    basis['unresolved'] += [
        'u0147の第二文からM0285とu0149冒頭のtrittまでの部分記述。冒頭の別の方法でも導出できたという可能性、後続の群という主張とその必然性はまだ記述しない。',
        '§3の係数1・零原点の四式を合成する。軸配置・共通尺度・原点時刻の校正を任意の相対運動だけから導かず、二つの式を前提として保持する。',
        '同じ出来事の三記録を全称的に結ぶが、全実数座標を実現する物理的な出来事が存在することの証明は含まない。',
        '原刊906頁の第三系導入とM0285を目視照合した。全実切断での体・平方根の法則、方向や原点に関する歴史的な規約、全文との意味一致確認は未完。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def main():
    text,basis=composed()
    for name,body in ((basis['document'],text),('data/parallel-composition-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
        path=ROOT/name
        if path.exists():
            if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored parallel composition differs: '+name)
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Consecutive normalized boosts and same-event composition composed')


if __name__=='__main__':main()
