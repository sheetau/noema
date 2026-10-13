"""Connect unit-circle angles to the reviewed velocity-composition expression."""
from copy import deepcopy
import json

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, CUT, definition, v
from scripts.compose_limits import call as k, app, op, both


def definitions():
    V,s,W,c,h,r,U=map(v,('light','speed','moving','cosine','sine','radical','result'))
    zero='n p a b';one='n p b b';two='n p c b'
    mul=lambda a,b:k('ad',a,b);add=lambda a,b:k('ab',a,b);sq=lambda a:mul(a,a)
    sub=lambda a,b:add(a,k('ac',b));eq=lambda a,b:op('e',a,b);lt=lambda a,b:k('aa',a,b)
    params=lambda ns:' '.join(n+' b' for n in ns.split())
    core='light speed moving cosine sine'
    numerator=sub(mul(sq(V),add(add(sq(s),sq(W)),mul(two,mul(mul(s,W),c)))),mul(mul(sq(s),sq(W)),sq(h)))
    D=add(sq(V),mul(mul(s,W),c))
    common=both(lt(zero,V),op('u',lt(W,zero)),k('szw',c,h))
    text=definition('s2n',params(core+' radical'),both(common,op('u',lt(r,zero)),eq(mul(sq(V),sq(r)),numerator)))
    text+=definition('s2o',params(core+' radical result'),both(k('s2n',V,s,W,c,h,r),op('u',eq(D,zero)),eq(mul(D,U),mul(sq(V),r))))
    text+=definition('s2p',params(core+' result'),both(common,lt(sq(s),sq(V)),op('u',lt(U,zero)),op('u',eq(D,zero)),eq(mul(sq(D),sq(U)),mul(sq(V),numerator))))
    for real,name in ((False,'s2q'),(True,'s2u')):
        typ=CUT if real else 'b';u,y=map(v,('longitudinal','transverse'))
        product=lambda a,b:k('shv' if real else 'ad',a,b)
        equal=lambda a,b:k('sca',a,b) if real else op('e',a,b)
        text+=definition(name,' '.join(n+' '+typ for n in 'longitudinal transverse moving cosine sine'.split()),
            both(k('szn' if real else 'szk',W,u,y),k('s2c' if real else 'szw',c,h),
                equal(u,product(W,c)),equal(product(y,y),product(product(W,W),product(h,h)))))
    mul=lambda a,b:k('shv',a,b);add=lambda a,b:k('bd',a,b);sq=lambda a:mul(a,a)
    sub=lambda a,b:k('bf',a,b);eq=lambda a,b:k('sca',a,b);lt=lambda a,b:k('bg',a,b)
    zero=k('bb',zero);one=k('bb',one);two=k('bb',two)
    params=lambda ns:' '.join(n+' '+CUT for n in ns.split())
    # Positive reciprocal is used only for V; the outer quotient is signed.
    divided=mul(mul(mul(s,W),h),k('sjd',V))
    radicand=sub(add(add(sq(s),sq(W)),mul(two,mul(mul(s,W),c))),sq(divided))
    denominator=add(one,mul(mul(mul(s,W),c),k('sjd',sq(V))))
    text+=definition('s2r',params(core),radicand,CUT)
    text+=definition('s2s',params('light speed moving cosine'),denominator,CUT)
    args=(V,s,W,c,h);rad=k('s2r',*args);den=k('s2s',V,s,W,c)
    text+=definition('s2t',params(core+' result'),both(
        *(k('ba',v(n)) for n in (core+' result').split()),lt(zero,V),op('u',lt(W,zero)),k('s2c',c,h),
        op('u',lt(rad,zero)),op('u',eq(den,zero)),eq(U,mul(k('sky',rad),k('sjt',den)))))
    return text


def composed():
    doc=parse((ROOT/'examples/v014/einstein-direction-angles.noema').read_text(encoding='utf-8'))
    statements,doc['statements']=doc['statements'],[]
    text=format_graph(doc,'compact')+definitions()+'r zkw[] a.\n'
    truth='e[n p a b][n p a b]';cosine=app(k('zkt'),truth);sine=app(k('zkt'),op('u',truth))
    text+=definition('s2v','','b context['+both(k('syw'),k('szt',k('zkq'),k('zke')),k('szs',k('zkp'),k('zke')),
        k('s2t',k('tc'),k('zb7'),k('zkq'),cosine,sine,k('zkp')))+']','e')
    doc=parse(text);doc['statements']=statements
    doc=parse(format_graph(doc,'compact')+'s[k uh[k zkw[] k rd[] r[k s2v[]] k zkf[] k ri[]]].\n')
    basis=deepcopy(json.loads((ROOT/'data/direction-angles-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='angle-composition-basis-v1',document='examples/v014/einstein-angle-composition.noema')
    d=next(d for d in doc['declarations'] if d['name']=='zkw')
    basis['primitives'].append(dict(symbol='zkw',parameters=d['parameters'],result=d['result'],arguments=[],
        meaning_ja='原刊906頁の角度を含む速度合成式M0257の本文箇所。分母の余弦を訂正記録へ接続する。'))
    basis['definitions'].update({
        's2n':'正のV、非負のw、単位円の二成分c,sについて、非負の平方根rをV²r²=V²(v²+w²+2vwc)−v²w²s²で指定する有理数の関係。',
        's2o':'s2nの非負平方根を使う式。D=V²+vwc≠0の下でDU=V²rを要求する。Dの符号を二乗で消さず、式単独では負のUも排除しない。',
        's2p':'角の二成分を使った非負の速さの二乗関係。|v|<VとD≠0を要求する。分母が負の場合、s2oの式とは同じ条件にならない。',
        's2q':'有理数の速度成分と角の二成分の接続。縦成分=w*c、横成分の二乗=w²*s²と非負ノルムを要求する。横の向きの符号は拘束しない。',
        's2r':'実切断の被開平数(v²+w²+2vwc)−(vws/V)²の構成式。V>0などの定義域はs2tで要求する。',
        's2s':'実切断の分母1+vwc/V²の構成式。V>0と分母非零はs2tで要求する。',
        's2t':'有効な実切断、V>0、w≥0、単位円条件、非負の被開平数と非零分母の下で、U=非負平方根(s2r)/s2sを表す。外側は既存の符号付き逆数を使い、分母の絶対値への置換はしない。',
        's2u':'実切断の成分と角の接続。縦成分=w*c、横成分の二乗=w²*s²を保つ。負の基準系速度での向きなしの角との同一視はしない。',
        's2v':'同じ点の運動、動く系の速さw、静止系の微分から得た非負の速さUを、角を含む原刊の式へ接続した部分的な内容。前後の議論と角の規約が未完のため全意味一致とはしない。'})
    basis['unresolved'] += [
        'M0257を保存済みの訂正層へ明示的に接続した。原データのsinを黙って変更せず、訂正後のcosを使う。',
        '非負の平方根を非零の符号付き分母で割る式を保持する。負の分母では非負の速さの二乗式と一致しない。原文の暗黙の適用範囲は未確定。',
        '成分から角への接続は縦成分=w*cos、横成分の二乗=w²*sin²。負の基準系速度で既存の向きなしの角を用いる場合、縦成分の符号が一致しないことがある。',
        '前後の計算の容易さの評価、速度二つの対称性への注目、近似の論述、全実切断上の体・平方根の定理、原文全体の意味一致確認は未完。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def main():
    text,basis=composed()
    for relative,body in ((basis['document'],text),('data/angle-composition-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
        path=ROOT/relative
        if path.exists():
            if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored angle composition differs: '+relative)
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Reviewed angle composition with explicit root and signed denominator composed')


if __name__=='__main__':main()
