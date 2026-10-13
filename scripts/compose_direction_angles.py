"""Represent planar angles by unit-circle coordinates and keep inverse branches explicit."""
from copy import deepcopy
import json

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, CUT, definition, v
from scripts.compose_limits import call as k, app, op, both

ANGLE='h[c] '+CUT


def definitions(real=False):
    typ=CUT if real else 'b';zero=k('bb','n p a b') if real else 'n p a b';one=k('bb','n p b b') if real else 'n p b b'
    names=('s2c','s2d','s2e','s2f','s2g','s2h') if real else ('szw','szx','szy','szz','s2a','s2b')
    circle,direction,inverse,principal,oriented,unsigned=names
    mul=lambda a,b:k('shv' if real else 'ad',a,b);add=lambda a,b:k('bd' if real else 'ab',a,b)
    sub=lambda a,b:k('bf',a,b) if real else add(a,k('ac',b))
    eq=lambda a,b:k('sca',a,b) if real else op('e',a,b)
    lt=lambda a,b:k('bg' if real else 'aa',a,b);sq=lambda a:mul(a,a)
    params=lambda ns:' '.join(n+' '+typ for n in ns.split())
    valid=lambda ns:[k('ba',v(n)) for n in ns.split()] if real else []
    c,s=map(v,('cosine','sine'));x,y,r=map(v,('x','y','radius'))
    text=definition(circle,params('cosine sine'),both(*valid('cosine sine'),eq(add(sq(c),sq(s)),one)))
    text+=definition(direction,params('x y radius cosine sine'),both(*valid('x y radius'),lt(zero,r),k(circle,c,s),eq(x,mul(r,c)),eq(y,mul(r,s))))
    text+=definition(inverse,params('x y cosine sine'),both(*valid('x y'),op('u',eq(x,zero)),k(circle,c,s),op('u',eq(c,zero)),eq(mul(x,s),mul(y,c))))
    text+=definition(principal,params('x y cosine sine'),both(k(inverse,x,y,c,s),lt(zero,c)))
    a,b,R=map(v,('otherx','othery','otherradius'));length=mul(r,R)
    dot=add(mul(x,a),mul(y,b));cross=sub(mul(x,b),mul(y,a))
    common=both(*valid('x y radius otherx othery otherradius'),k('szn' if real else 'szk',r,x,y),
        k('szn' if real else 'szk',R,a,b),lt(zero,r),lt(zero,R),k(circle,c,s),eq(mul(length,c),dot))
    args=params('x y radius otherx othery otherradius cosine sine')
    text+=definition(oriented,args,both(common,eq(mul(length,s),cross)))
    text+=definition(unsigned,args,both(common,op('u',lt(s,zero)),eq(sq(mul(length,s)),sq(cross))))
    return text


def composed():
    doc=parse((ROOT/'examples/v014/einstein-speed-magnitude.noema').read_text(encoding='utf-8'))
    statements,doc['statements']=doc['statements'],[]
    text=format_graph(doc,'compact')+definitions()+definitions(True)
    truth='e[n p a b][n p a b]';false='u['+truth+']'
    text+=definition('s2i','cosine '+CUT+' sine '+CUT,'i[choice c]['+k('szi',v('choice'),v('cosine'),v('sine'))+']',ANGLE)
    text+=definition('s2j','angle '+ANGLE,k('s2c',app(v('angle'),truth),app(v('angle'),false)))
    text+='r zkt[] '+ANGLE+'.r zku[] a.r zkv[] a.\n'
    cosine=app(k('zkt'),truth);sine=app(k('zkt'),false);speed=k('zb7');zero=k('bb','n p a b')
    common=both(k('syw'),k('szt',k('zkq'),k('zke')))
    text+=definition('s2k','','b context['+both(common,k('s2e',k('zkc'),k('zkd'),cosine,sine))+']','e')
    text+=definition('s2l','','b context['+both(common,k('s2f',k('zkc'),k('zkd'),cosine,sine))+']','e')
    text+=definition('s2m','','b context['+both(common,k('s2h',speed,zero,k('sky',k('shv',speed,speed)),k('zkc'),k('zkd'),k('zkq'),cosine,sine))+']','e')
    doc=parse(text);doc['statements']=statements
    # The inverse relation leaves the historical branch convention unresolved.
    # The principal-value alternative is defined but not attributed to Einstein.
    doc=parse(format_graph(doc,'compact')+'s[k uh[k zku[] k rd[] r[k s2k[]] k zkf[] k ri[]]].\n'
        +'s[k uh[k zkv[] k rd[] r[k s2m[]] k zkf[] k ri[]]].\n')
    basis=deepcopy(json.loads((ROOT/'data/speed-magnitude-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='direction-angles-basis-v1',document='examples/v014/einstein-direction-angles.noema')
    decls={d['name']:d for d in doc['declarations']}
    for name,meaning in (
        ('zkt','αを単位円上の座標対で指す。真の引数で余弦成分、偽で正弦成分を返す。周回数やラジアンの実数値はこの参照に含めない。'),
        ('zku','二速度成分の比の逆正接でαを指定する本文箇所。'),
        ('zkv','αを二つの速度の間の角と解釈する本文箇所。')):
        d=decls[name];basis['primitives'].append(dict(symbol=name,parameters=d['parameters'],result=d['result'],arguments=[],meaning_ja=meaning))
    meanings=[
        '単位円上の二成分c,sの条件c²+s²=1。',
        '正の大きさrと二成分x,yについてx=r*c,y=r*sとなる向き。零ベクトルには向きを割り当てない。',
        '分母xが非零の比y/xの逆正接の関係を単位円上で表す。c≠0とx*s=y*cを要求する。反対向きの二候補をこの関係だけでは区別しない。',
        '比y/xの逆正接を右半円c>0へ制限した主値の候補条件。正負の成分から直接得る向きとは一般に異なる。',
        '二つの非零ベクトルの向き付きの角。余弦を内積、正弦を有向面積と、二つの大きさの積へ接続する。',
        '二つの非零ベクトルの向きなしの角。内積の余弦を保持し、正弦を非負とする。向き付きの符号を保存する定義とは別である。']
    for names,prefix in ((('szw','szx','szy','szz','s2a','s2b'),'有理数による'),(('s2c','s2d','s2e','s2f','s2g','s2h'),'実切断による')):
        basis['definitions'].update({name:prefix+meaning for name,meaning in zip(names,meanings)})
    basis['definitions'].update({
        's2i':'既存の二切断の選択sziを使い、二成分から一つの角の座標対を関数として構成する。型だけでは単位円条件を満たすとはしない。',
        's2j':'関数として渡された角の二成分が単位円条件を満たす。',
        's2k':'既存の点の運動と速さに結び、αが成分比の逆正接関係を満たすという部分的な読み。原文の枝の選択はまだ確定しない。',
        's2l':'同じ記述で逆正接を主値へ制限する代替的な内容。著者がこの規約を採用したとは断言しない。',
        's2m':'同じαを、基準系の符号付き縦速度と動く点の速度の間の向きなしの角として接続した部分的な読み。双方の非零性を要求する。'})
    basis['unresolved'] += [
        'u0138のM0253とu0139前半の部分記述。逆正接の関係と主値を分離した。枝を未確定のまま残すs2kは原文の全意味を確定した訳ではない。',
        '単位円の座標対は一周を法とする角を表す。ラジアンや度の実数測度、周回数を含む角、三角関数の解析的構成との接続は未完。',
        '逆正接の主値と二速度の向きなしの角は、負の縦成分・負の横成分・負の基準系速度で一致しない場合がある。原文の軸と符号・枝の規約をこれから照合する。',
        '縦成分零では比y/xを定義せず、零速度にはベクトル間の角を自動で割り当てない。後続の速度合成式の適用や極限とは別の条件である。',
        'u0137の接続語、u0139後半の計算への移行、M0257の角度式、近似の論述、原刊照合と原文の全意味確認は未完。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def main():
    text,basis=composed()
    for relative,body in ((basis['document'],text),('data/direction-angles-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
        path=ROOT/relative
        if path.exists():
            if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored angles differ: '+relative)
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Unit-circle directions, inverse branches and velocity angles composed')


if __name__=='__main__':main()
