"""Represent strict shortfalls, the substituted quotient and quantified bounds."""
from copy import deepcopy
import json

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, CUT, definition, v
from scripts.compose_limits import call as k, op, both, quant as q


def definitions():
    V,a,g,h,U,s,w=map(v,('limit','amount','gap','othergap','result','speed','moving'))
    text=''
    for real,name in ((False,'s3n'),(True,'s3o')):
        typ=CUT if real else 'b';zero=k('bb','n p a b') if real else 'n p a b'
        lt=lambda x,y:k('bg' if real else 'aa',x,y)
        sub=lambda x,y:k('bf',x,y) if real else k('ab',x,k('ac',y))
        eq=lambda x,y:k('sca',x,y) if real else op('e',x,y)
        valid=[k('ba',x) for x in (V,a,g)] if real else []
        text+=definition(name,'limit '+typ+' amount '+typ+' gap '+typ,
            both(*valid,lt(zero,V),lt(zero,g),lt(g,V),eq(a,sub(V,g))))
    zero='n p a b';mul=lambda x,y:k('ad',x,y);add=lambda x,y:k('ab',x,y);sub=lambda x,y:add(x,k('ac',y))
    A=sub(sub(add(V,V),g),h);D=add(mul(V,A),mul(g,h))
    text+=definition('s3p','limit b gap b othergap b result b',both(k('s3n',V,sub(V,g),g),k('s3n',V,sub(V,h),h),
        op('u',op('e',D,zero)),op('e',mul(D,U),mul(mul(V,V),A))))
    zero=k('bb',zero);mul=lambda x,y:k('shv',x,y);add=lambda x,y:k('bd',x,y);sub=lambda x,y:k('bf',x,y)
    A=sub(sub(add(V,V),g),h);den=add(A,mul(mul(g,h),k('sjd',V)))
    text+=definition('s3q','limit '+CUT+' gap '+CUT+' othergap '+CUT,mul(mul(V,A),k('sjt',den)),CUT)
    text+=definition('s3r','limit '+CUT+' gap '+CUT+' othergap '+CUT+' result '+CUT,
        both(k('s3o',V,sub(V,g),g),k('s3o',V,sub(V,h),h),k('ba',U),op('u',k('sca',den,zero)),k('sca',U,k('s3q',V,g,h))))
    text+=definition('s3s','limit '+CUT+' amount '+CUT,both(k('ba',V),k('ba',a),k('bg',zero,V),op('u',k('bg',a,zero)),k('bg',a,V)))
    text+=definition('s3t','limit '+CUT+' speed '+CUT+' moving '+CUT,both(k('s3s',V,s),k('s3s',V,w)))
    result=k('s3j',V,s,w)
    text+=definition('s3u','limit '+CUT+' speed '+CUT+' moving '+CUT,
        op('y',k('s3t',V,s,w),both(k('s3g',V,s,w,result),k('s3s',V,result))))
    text+=definition('s3v','limit '+CUT,both(k('ba',V),k('bg',zero,V),
        q('f','speed',CUT,q('f','moving',CUT,k('s3u',V,s,w)))))
    return text


def composed():
    doc=parse((ROOT/'examples/v014/einstein-axial-composition.noema').read_text(encoding='utf-8'))
    statements,doc['statements']=doc['statements'],[]
    text=format_graph(doc,'compact')+definitions()
    text+='r zlg[] '+CUT+'.r zlh[] '+CUT+'.r zli[] a.r zlj[] a.r zlk[] a.r zll[] a.\n'
    V,g,h,U,s,w=map(k,('tc','zlg','zlh','zkp','zb7','zkq'))
    text+=definition('s3w','','b context['+k('s3v',V)+']','e')
    text+=definition('s3x','','b context['+both(k('s3o',V,s,g),k('s3o',V,w,h))+']','e')
    text+=definition('s3y','','b context['+both(k('s3r',V,g,h,U),k('bg',U,V))+']','e')
    text+=definition('s3z','','b context['+both('t[k s3x[]][v context]','t[k s3l[]][v context]')+']','e')
    x,y=map(v,('speed','moving'));result=k('s3j',V,x,y);zero=k('bb','n p a b')
    text+=definition('s4a','','b context['+both(k('ba',V),k('bg',zero,V),
        q('f','speed',CUT,q('f','moving',CUT,op('y',k('s3t',V,x,y),k('s3g',V,x,y,result)))))+']','e')
    doc=parse(text);doc['statements']=statements
    doc=parse(format_graph(doc,'compact')+'''
s[k zc[k zli[] k rd[] r[k s4a[]] r[k s3w[]] k zkf[] k ri[]]].
s[k ug[k zlj[] k rd[] r[k s3x[]] k zlk[] k ri[]]].
s[k zc[k zll[] k rd[] r[k s3z[]] r[k s3y[]] k zlk[] k ri[]]].
s[k zfr[k zll[] k rd[] r[k s3w[]] k ri[] k zkf[]]].
''')
    basis=deepcopy(json.loads((ROOT/'data/axial-composition-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='speed-deficits-basis-v1',document='examples/v014/einstein-speed-deficits.noema')
    decls={d['name']:d for d in doc['declarations']}
    for name,meaning in (
        ('zlg','vをV−κと記すときのκへの参照。正性・上限・同じvとの接続はs3xで要求する。'),
        ('zlh','wをV−λと記すときのλへの参照。正性・上限・同じwとの接続はs3xで要求する。'),
        ('zli','光速未満の二速度から光速未満の速度が得られると述べる本文箇所。'),
        ('zlj','κとλを導入し、その正性と上限を指定する本文箇所。'),
        ('zlk','κ・λによる置き換えと変形を行う局所的な論証範囲。'),
        ('zll','置き換え後の商と光速より小さいことを示し、先行する主張の論証として提示する箇所。')):
        d=decls[name];basis['primitives'].append(dict(symbol=name,parameters=d['parameters'],result=d['result'],arguments=[],meaning_ja=meaning))
    basis['definitions'].update({
        's3n':'有理数で、正の上限Vからの不足gが0<g<Vを満たし、量a=V−gとなる。速度に限らない不足の関係。a=0やa=Vは含めない。',
        's3o':'有効な実切断でのs3nと同じ不足の関係。量が0となる境界まで不足の上限を緩めない。',
        's3p':'0<κ,λ<Vの下でD=V*(2V−κ−λ)+κλ、D≠0、D*U=V²*(2V−κ−λ)となる有理数の商。U<Vはこの定義へ結論として埋め込まない。',
        's3q':'実切断でV*(2V−κ−λ)/(2V−κ−λ+κλ/V)を構成する。定義域はs3rで要求する。',
        's3r':'0<κ,λ<V、有効な結果、非零分母の下で、結果がs3qの値となる実切断の関係。厳密な上限不等式は別に記述する。',
        's3s':'有効な実数についてV>0かつ0≤a<V。零を含み、上限そのものは含めない。',
        's3t':'同じVについて二つの入力速度がs3sの範囲に入る。正負の符号付き速度全体へ無断に範囲を広げない。',
        's3u':'s3tを満たす入力なら、既存の一次元式で構成した値が合成関係を満たし、同じVのs3sの範囲に入る。単なる結果の全称条件だけにして、結果の不在で空虚に成立させない。',
        's3v':'正の有効なVに対し、任意の二実切断入力でs3uが成立するという全称条件。有限標本への量化ではない。',
        's3w':'光速度tcに関するs3vの内容。「常に」を選んだ二速度だけの検査へ縮めない。',
        's3x':'同じ光速度・既存のv・wと、それぞれのκ・λをs3oで結んだ置き換えの内容。',
        's3y':'同じUがκ・λによる商を満たし、さらに厳密にVより小さいというM0271の内容。',
        's3z':'既存の一次元合成式s3lと同じ変数へ結ばれた置き換えs3xを合わせた前提内容。',
        's4a':'非負で光速未満の任意の入力について、M0263の式から構成した値が同じ合成関係を満たす、という式の一般形への参照内容。個別の速度対だけから一般主張を推論しない。'})
    basis['unresolved'] += [
        'u0143とM0271の部分記述。前段の同方向の式に続く速さの主張として、一般条件を0≤v,w<Vと読む。任意方向での速度合成の全主張へ拡張しない。',
        '原文の不足の条件0<κ,λ<Vは0<v,w<Vだけを表す。零速度は一般主張には含めるが、不足を用いる同じ論証へ黙って含めず、別の境界例として検査する。',
        'nämlichを、後続の式を先行する主張の論証として提示する帰属で接続した。提示の事実と論証の妥当性を区別し、全実切断の証明済みとはしない。',
        '原刊906頁の数式と条件句を照合した。歴史的な速度の意味と方向規約、全実切断の体・順序の法則、後続の光速度の不変性、原文全体の意味一致確認は未完。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def main():
    text,basis=composed()
    for name,body in ((basis['document'],text),('data/speed-deficits-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
        path=ROOT/name
        if path.exists():
            if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored speed deficits differ: '+name)
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Strict shortfalls, substituted quotient and universally stated speed bound composed')


if __name__=='__main__':main()
