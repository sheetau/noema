"""Represent phase, Doppler factors and aberrated direction components."""
from copy import deepcopy
import json

from noema.extraction import extract_document, extract_basis
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, op, both
from scripts.compose_field_equations import CUT

PARENT = 'examples/v014/einstein-auxiliary-terms.noema'
ZERO = 'n p a b'
ONE = 'n p b b'
CZ = k('bb', ZERO)
CO = k('bb', ONE)


def rational_definitions():
    add = lambda a,b:k('ab',a,b)
    mul = lambda a,b:k('ad',a,b)
    sub = lambda a,b:add(a,k('ac',b))
    square = lambda a:mul(a,a)
    r,b,a,y,z = map(v, ('ratio','beta','ax','ay','az'))
    domain = both(k('aa',square(r),ONE), k('aa',ZERO,b),
        op('e',mul(square(b),sub(ONE,square(r))),ONE),
        op('e',add(square(a),add(square(y),square(z))),ONE))
    text = definition('sdh2','ratio b beta b ax b ay b az b',domain)
    w,wp,ap,bp,cp = map(v,('rate','shifted','dx','dy','dz'))
    denominator = sub(ONE,mul(a,r))
    text += definition('sdi2','ratio b beta b rate b ax b ay b az b shifted b dx b dy b dz b',both(
        k('sdh2',r,b,a,y,z), k('aa',ZERO,w),
        op('e',wp,mul(w,mul(b,denominator))),
        op('e',mul(denominator,ap),sub(a,r)),
        op('e',mul(mul(b,denominator),bp),y),
        op('e',mul(mul(b,denominator),cp),z)))
    V,t,x,py,pz,phase=map(v,('light','time','x','y','z','phase'))
    dot=add(mul(a,x),add(mul(y,py),mul(z,pz)))
    text += definition('sdj2','light b rate b ax b ay b az b time b x b y b z b phase b',both(
        k('aa',ZERO,V),op('e',mul(V,phase),mul(w,sub(mul(V,t),dot)))))
    text += definition('sdk2','ratio b rate b shifted b',both(k('aa',square(r),ONE),k('aa',ZERO,w),
        k('aa',ZERO,wp),op('e',mul(square(wp),add(ONE,r)),mul(square(w),sub(ONE,r)))))
    return text


RATIONAL_MEANINGS = {
    'sdh2': '無次元の符号付き速度比の絶対値が1未満、βは正でβ²(1−比²)=1、三つの方向余弦の二乗和は1という有理数の条件。',
    'sdi2': 'sdh2と正の周波数を前提に、変換後の周波数と三つの方向余弦の四式を分母を払って表す。周波数には角周波数と通常の周波数を同一尺度で混ぜない。',
    'sdj2': '光速度が正のとき、位相Φ=ω(t−(ax+by+cz)/V)を、分母Vを払った有理数の等式で表す。場の正弦波形や光源の実在は含まない。',
    'sdk2': '正の周波数と正の変換後周波数を要求し、平行方向の比が√((1−比)/(1＋比))となる条件を平方の等式で表す。負の平方根の枝を認めない。',
}


def generic_composed():
    doc=parse('n:r aa[b b] c.r ab[b b] b.r ac[b] b.r ad[b b] b.'+rational_definitions())
    labels={'aa':'有理数の厳密な小なり。','ab':'有理数の加算。','ac':'有理数の加法逆元。','ad':'有理数の乗算。'}
    basis={'version':'wave-directions-basis-v1','document':'examples/v014/wave-directions.noema',
        'primitives':[{'symbol':d['name'],'parameters':d['parameters'],'result':d['result'],
            'arguments':['value'] if d['name']=='ac' else ['left','right'],'meaning_ja':labels[d['name']]}
            for d in doc['declarations'] if d['kind']=='primitive'],
        'definitions':RATIONAL_MEANINGS,
        'unresolved':['有理数の代数的条件であり、実数演算の一般法則や、光源・観測者・波の測定との接続の証明ではない。']}
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def definitions():
    mul=lambda a,b:k('shv',a,b)
    sub=lambda a,b:k('bf',a,b)
    add=lambda a,b:k('bd',a,b)
    V,s,w,a,b,c=map(v,('light','speed','rate','ax','ay','az'))
    params=' '.join(n+' '+CUT for n in ('light','speed','rate','ax','ay','az'))
    square=lambda a:mul(a,a)
    text=rational_definitions()
    text+=definition('sdl2',params,both(*(k('ba',x) for x in (V,s,w,a,b,c)),k('s45',V,s),
        k('bg',CZ,w),k('sca',add(square(a),add(square(b),square(c))),CO)))
    ratio=mul(s,k('sjd',V))
    denominator=sub(CO,mul(a,ratio))
    text+=definition('sdm2','light '+CUT+' speed '+CUT+' ax '+CUT,denominator,CUT)
    den=k('sdm2',V,s,a)
    factor=mul(k('soy',V,s),den)
    text+=definition('sdn2','light '+CUT+' speed '+CUT+' rate '+CUT+' ax '+CUT,mul(w,factor),CUT)
    text+=definition('sdo2','light '+CUT+' speed '+CUT+' ax '+CUT,mul(sub(a,ratio),k('sjd',den)),CUT)
    text+=definition('sdp2','light '+CUT+' speed '+CUT+' ax '+CUT+' transverse '+CUT,
        mul(v('transverse'),k('sjd',factor)),CUT)
    outputs=tuple(map(v,('shifted','dx','dy','dz')))
    expected=(k('sdn2',V,s,w,a),k('sdo2',V,s,a),k('sdp2',V,s,a,b),k('sdp2',V,s,a,c))
    text+=definition('sdq2',params+' '+' '.join(n+' '+CUT for n in ('shifted','dx','dy','dz')),both(
        k('sdl2',V,s,w,a,b,c),*(k('ba',x) for x in outputs),
        *(k('sca',x,y) for x,y in zip(outputs,expected))))
    longitudinal=mul(w,k('sky',mul(sub(CO,ratio),k('sjd',add(CO,ratio)))))
    text+=definition('sdr2','light '+CUT+' speed '+CUT+' rate '+CUT,longitudinal,CUT)
    t,x,y,z=map(v,('time','x','y','z'))
    dot=add(mul(a,x),add(mul(b,y),mul(c,z)))
    text+=definition('sds2',' '.join(n+' '+CUT for n in ('light','rate','ax','ay','az','time','x','y','z')),
        mul(w,sub(t,mul(dot,k('sjd',V)))),CUT)
    return text


def source_composed():
    doc=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    basis=deepcopy(json.loads((ROOT/'data/einstein-auxiliary-terms-basis-v1.json').read_text(encoding='utf-8')))
    statements,doc['statements']=doc['statements'],[]
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=statements
    basis.update(version='einstein-wave-directions-basis-v1',document='examples/v014/einstein-wave-directions.noema')
    basis['definitions'].update(RATIONAL_MEANINGS)
    basis['definitions'].update({
        'sdl2':'有効な実切断の光速度・符号付き速度・正の周波数・三方向余弦を要求する。速度は光速未満、方向余弦の二乗和は1。',
        'sdm2':'1−a v/Vという分母。sdl2の範囲では正となる代数的な条件を別に検証する。',
        'sdn2':'ωβ(1−a v/V)による周波数の変換値。通常の周波数νも同じ倍率を使えるが、ωとνそのものを同一の値にはしない。',
        'sdo2':'(a−v/V)/(1−a v/V)による縦方向余弦の変換値。分母の正値が必要。角度そのものとその余弦を同一視しない。',
        'sdp2':'横方向の余弦をβ(1−a v/V)で割った値。二つの横軸へそれぞれ同じ式を適用する。',
        'sdq2':'sdl2を満たす同じ入力に対する、変換後の周波数と三方向余弦がsdn2/sdo2/sdp2と一致する。別入力の成分を混ぜない。',
        'sdr2':'a=1の平行方向におけるν√((1−v/V)/(1＋v/V))の正の枝の値。正のV、光速未満の速度、正のνを利用側で要求する。',
        'sds2':'実数切断で、同じ周波数・三方向余弦・四座標から位相ω(t−(ax+by+cz)/V)を構成する。正のVと有効な入力は利用側の条件である。',
    })
    basis['unresolved'] += [
        '第7節の位相、周波数、方向余弦、ドップラー式、光行差と特殊例へ数学的に部分対応する。角度の余弦と光源・観測者を結ぶ幾何学、遠方光源・近似平面波・観測の具体的な対応は未記述。',
        'ωは位相の角周波数、νは通常の周波数として区別する。同じ変換倍率を持つが、両者の比例定数や周期を定義し終えたわけではない。',
        'M0320のうち位相の部分に対応する。正弦波形、六つの振幅、M0325の変換後の場、振幅変換はこの草案に含めない。',
        '有理数の多項式条件の一般的な補助検査と、構成した有理数切断の具体例を区別する。下側切断で定義した実数体・平方根の全域的な法則の機械的証明ではない。',
        '値を作る関数sdm2〜sdp2/sdr2/sds2は、単独では引数の物理的・数学的な許容性を認定しない。適用時に明示した定義域を要求する。',
        '原文の導出の談話、光源の方向と波の進行方向の符号、角度の幾何学、光源や波の基礎概念、全文の意味一致は未完。既存173件の本文主張を保持し、新たな著者主張は追加しない。',
    ]
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def core_composed():
    text,basis=source_composed();doc=parse(text)
    selected=extract_document(doc,roots=['sdq2','sdr2','sds2'],statement_indices=[])
    projected=extract_basis(doc,basis,selected,version='wave-directions-core-basis-v1',
        document_path='examples/v014/wave-directions-core.noema')
    return format_graph(selected.document,'compact')+'\n',projected


def main():
    for builder,stem in ((generic_composed,'wave-directions'),(source_composed,'einstein-wave-directions'),(core_composed,'wave-directions-core')):
        text,basis=builder()
        for name,body in ((basis['document'],text),('data/'+stem+'-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/name
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored wave directions differ: '+name)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(stem,len(text),'characters')


if __name__=='__main__':main()
