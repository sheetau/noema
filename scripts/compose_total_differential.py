"""Define finite-dimensional total differentiability from a uniform remainder."""
from copy import deepcopy
import json

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, op, both, quant as q
from scripts.compose_field_equations import CUT, TAU, POINT, REGION, FIELD, JET, ROLES

PARENT='examples/v014/einstein-field-constraints.noema'
FUNCTION='h['+POINT+'] '+CUT
DOMAIN='h['+POINT+'] c'
CORE=tuple('s7'+letter for letter in 'qrstuvwx')


def definitions():
    zero=k('bb','n p a b');axes=v('axes');point=v('point');increment=v('increment');gradient=v('gradient')
    fold=lambda initial,params,body:'q['+axes+']['+initial+'][i['+params+']['+body+']]'
    text=definition('s7q','axes j[a] vector '+POINT,fold(zero,'value '+CUT+' axis a',k('bd',v('value'),k('shu',app(v('vector'),v('axis'))))),CUT)
    text+=definition('s7r','axes j[a] gradient '+POINT+' increment '+POINT,fold(zero,'value '+CUT+' axis a',
        k('bd',v('value'),k('shv',app(gradient,v('axis')),app(increment,v('axis'))))),CUT)
    member=fold('u[e[n p a b][n p a b]]','seen c item a',op('x',v('seen'),op('e',v('item'),v('axis'))))
    text+=definition('s7s','axes j[a] first '+POINT+' second '+POINT,'i[axis a]['+k('szi',member,k('bd',app(v('first'),v('axis')),app(v('second'),v('axis'))),zero)+']',POINT)
    text+=definition('s7t','axes j[a] point '+POINT,k('s7s',axes,point,'i[axis a]['+zero+']'),POINT)
    projected=k('s7t',axes,point);shifted=k('s7s',axes,point,increment);size=k('s7q',axes,increment)
    valid=lambda vector:k('shn',axes,vector,'p ba')
    positive=lambda value:both(k('ba',value),k('bg',zero,value))
    function=v('function');domain=v('domain');value=app(function,shifted);base=app(function,projected)
    ball=op('y',both(valid(increment),k('bg',size,v('radius'))),both(app(domain,shifted),k('ba',value)))
    args='axes j[a] function '+FUNCTION+' domain '+DOMAIN+' point '+POINT
    text+=definition('s7u',args+' radius '+CUT,both(valid(point),positive(v('radius')),app(domain,projected),k('ba',base),q('f','increment',POINT,ball)))
    residual=k('bf',k('bf',value,base),k('s7r',axes,gradient,increment))
    remainderargs='axes j[a] function '+FUNCTION+' point '+POINT+' gradient '+POINT+' increment '+POINT
    text+=definition('s7v',remainderargs,residual,CUT)
    text+=definition('s7w',remainderargs+' epsilon '+CUT,both(valid(point),valid(gradient),valid(increment),positive(v('epsilon')),
        k('ba',base),k('ba',value),k('bg',zero,size),k('bg',k('shu',residual),k('shv',v('epsilon'),size))))
    nearby=both(valid(increment),k('bg',zero,size),k('bg',size,v('delta')))
    bound=k('s7w',axes,function,point,gradient,increment,v('epsilon'))
    uniform=q('f','epsilon',CUT,op('y',positive(v('epsilon')),q('g','delta',CUT,both(positive(v('delta')),
        k('bc',v('delta'),v('radius')),q('f','increment',POINT,op('y',nearby,bound))))))
    text+=definition('s7x',args+' gradient '+POINT,both(valid(gradient),q('g','radius',CUT,
        both(k('s7u',axes,function,domain,point,v('radius')),uniform))))
    coords=[app(v('vector'),k(role)) for role in ROLES]
    for name,typ,result in (('s7y',TAU,FUNCTION),('s7z',REGION,DOMAIN)):
        text+=definition(name,'function '+typ,'i[vector '+POINT+']['+app(function,*coords)+']',result)
    fieldargs='electric '+FIELD+' magnetic '+FIELD+' region '+REGION+' point '+POINT+' electricjet '+JET+' magneticjet '+JET
    totals=[k('s7x',k('shx'),k('s7y',app(v(field),k(role))),k('s7z',v('region')),point,
        'i[axis a]['+app(v(jet),k(role),v('axis'))+']') for field,jet in (('electric','electricjet'),('magnetic','magneticjet')) for role in ROLES[:3]]
    text+=definition('s74',fieldargs,both(*totals))
    text+=definition('s75',fieldargs,both(k('s74',v('electric'),v('magnetic'),v('region'),point,v('electricjet'),v('magneticjet')),
        k('s6s',v('electric'),v('magnetic'),v('region'),point,v('electricjet'),v('magneticjet'))))
    V,s=v('light'),v('speed');oldpoint=k('s46',V,k('bf',zero,s),point)
    premise=both(k('s45',V,s),k('s75',v('electric'),v('magnetic'),v('region'),oldpoint,v('electricjet'),v('magneticjet')))
    conclusion=k('s75',k('s6k',V,s,v('electric'),v('magnetic')),k('s6l',V,s,v('electric'),v('magnetic')),
        k('s6m',V,s,v('region')),point,k('s6u',V,s,v('electricjet'),v('magneticjet')),k('s6v',V,s,v('electricjet'),v('magneticjet')))
    text+=definition('s76',fieldargs+' light '+CUT+' speed '+CUT,op('y',premise,conclusion))
    return text


MEANINGS={
    's7q':'指定した有限軸列について成分の絶対値を加えたL1ノルム。軸列の非空性・重複排除と値の有効性は呼出側のshnで要求する。',
    's7r':'同じ有限軸列の勾配成分と変位成分の積を加えた一次項。',
    's7s':'二つのベクトルを指定軸で成分ごとに加え、指定軸以外は零にする。評価する関数へ未指定成分を持ち込まない。',
    's7t':'指定軸の値だけを残し、それ以外を零にした基準点。',
    's7u':'指定点を含む正半径のL1開球が領域に入り、その球の全点で関数値が有効な実数となる局所条件。空の領域や片側だけの点列で代用しない。',
    's7v':'関数の増分から、同じ勾配による一次項を引いた剰余。',
    's7w':'指定した非零変位について、剰余の絶対値がepsilonと変位ノルムの積より厳密に小さい条件。点・勾配・変位・関数値・epsilonの有効性も要求する。',
    's7x':'関数が局所開球で定義され、任意の正のepsilonに対し一つの正のdeltaが存在し、その球内の全ての非零変位でs7wを満たすという全微分可能性。同時に複数軸を動かす変位を含む。',
    's7y':'四引数のスカラー関数を四座標ベクトルを受け取る関数へ変換する。同じx,y,z,tの順を保つ。',
    's7z':'同じ四座標の領域を、ベクトルを受け取る条件へ変換する。',
    's74':'同じ二場・領域・点と六つの勾配について、全六成分の四変数の全微分可能性を要求する。',
    's75':'全微分可能性s74と、同じ24値が各軸の実際の偏微分であるs6sを共に明示する。両者を機械的に同値と認定したとはしない。',
    's76':'許容速度で、逆変換先の旧点におけるs75から、新点の変換した二場が数値変換した勾配でs75を満たすという連鎖律の条件付き命題。一般の実切断上の証明は未完。',
}


def composed():
    doc=parse((ROOT/PARENT).read_text(encoding='utf-8'));statements,doc['statements']=doc['statements'],[]
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=statements
    basis=deepcopy(json.loads((ROOT/'data/einstein-field-constraints-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='einstein-total-differential-basis-v1',document='examples/v014/einstein-total-differential.noema')
    basis['definitions'].update(MEANINGS)
    basis['unresolved'] += [
        '連鎖律に必要な局所正則性を説明する数学的な解釈注記として追加した。原文の新しい範囲を完成扱いにせず、著者への帰属文も変更しない。',
        '全微分可能性と各偏微分の存在を区別した。s76は一般の実切断で表した連鎖律の命題だが、全実数上の証明、逆写像の近傍評価、測定・単位・真空の意味との接続は未完。',
        'epsilonごとの一様なdelta、全変位の量化、局所開球の条件を、有限個の検査点に置き換えない。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def generic_composed():
    # Keep a reusable definition library with only its actual dependencies.
    text,basis=composed();doc=parse(text);byname={d['name']:d for d in doc['declarations']};needed=set(CORE)
    def references(node):
        if isinstance(node,list):return set().union(*(references(n) for n in node)) if node else set()
        if not isinstance(node,dict):return set()
        found={node['symbol']} if node.get('symbol') in byname else set()
        return found|set().union(*(references(n) for n in node.values()))
    todo=list(needed)
    while todo:
        for name in references(byname[todo.pop()])-needed:needed.add(name);todo.append(name)
    doc['declarations']=[d for d in doc['declarations'] if d['name'] in needed];doc['statements']=[]
    basis=dict(version='total-differential-basis-v1',document='examples/v014/total-differential.noema',
        primitives=[p for p in basis['primitives'] if p['symbol'] in needed],
        definitions={name:meaning for name,meaning in basis['definitions'].items() if name in needed},
        unresolved=['有限軸列で定義した実数値関数の局所条件であり、全実切断について連鎖律を証明したものではない。依存する既存の数・有限列の意味規約は元の規約を保持する。'])
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def main():
    for builder,name in ((generic_composed,'total-differential'),(composed,'einstein-total-differential')):
        text,basis=builder()
        for filename,body in ((basis['document'],text),('data/'+name+'-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/filename
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored total differential differs: '+filename)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Finite-dimensional uniform linear approximation composed')


if __name__=='__main__':main()
