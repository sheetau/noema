"""Define relative limits, continuity and closed curves using existing syntax."""
from copy import deepcopy
import json
from pathlib import Path

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis

ROOT = Path(__file__).resolve().parents[1]
R, D, F = 'h[b] c', 'h[h[b] c] c', 'h[h[b] c] h[b] c'
ZERO = 'n p a b'


def v(name):
    return 'v ' + name


def call(name, *args):
    return 'k ' + name + '[' + ' '.join(args) + ']'


def app(function, *args):
    return 'c[' + function + '][' + ' '.join(args) + ']'


def op(name, *args):
    return name + ''.join('[' + arg + ']' for arg in args)


def both(*args):
    return args[0] if len(args) == 1 else op('w', args[0], both(*args[1:]))


def quant(marker, name, sort, body):
    return marker + ' ' + name + ' ' + sort + '[' + body + ']'


def lam(name, sort, body):
    return 'i[' + name + ' ' + sort + '][' + body + ']'


def definition(name, parameters, body):
    return 'd ' + name + '[' + parameters + '] c[' + body + '].\n'


def definitions():
    # Rational-domain forms are useful in their own right and permit exact
    # affine quantifier tests. They are not a discretization of real cuts.
    sub = lambda x, y: call('ab', x, call('ac', y))
    lt = lambda x, y: call('aa', x, y)
    inside = lambda x: app(v('domain'), x)
    fn = lambda x: app(v('function'), x)
    point, value, epsilon, delta, x = [v(n) for n in ('point', 'value', 'epsilon', 'delta', 'x')]
    text = definition('ka', 'left b right b radius b', both(lt(ZERO, v('radius')),
        lt(sub(v('left'), v('right')), v('radius')), lt(sub(v('right'), v('left')), v('radius'))))
    text += definition('kb', 'domain h[b] c point b', quant('f', 'epsilon', 'b', op('y', lt(ZERO, epsilon),
        quant('g', 'x', 'b', both(inside(x), op('u', op('e', x, point)), call('ka', x, point, epsilon))))))
    limit = quant('f', 'epsilon', 'b', op('y', lt(ZERO, epsilon), quant('g', 'delta', 'b', both(
        lt(ZERO, delta), quant('f', 'x', 'b', op('y', both(inside(x), op('u', op('e', x, point)), call('ka', x, point, delta)),
            call('ka', fn(x), value, epsilon)))))))
    text += definition('kc', 'domain h[b] c function h[b] b point b value b', both(call('kb', v('domain'), point), limit))
    continuous = quant('f', 'epsilon', 'b', op('y', lt(ZERO, epsilon), quant('g', 'delta', 'b', both(
        lt(ZERO, delta), quant('f', 'x', 'b', op('y', both(inside(x), call('ka', x, point, delta)),
            call('ka', fn(x), fn(point), epsilon)))))))
    text += definition('kd', 'domain h[b] c function h[b] b point b', both(inside(point), continuous))
    text += definition('ke', 'domain h[b] c function h[b] b', quant('f', 'point', 'b',
        op('y', inside(point), call('kd', v('domain'), v('function'), point))))
    text += definition('kf', 'lower b upper b x b', both(op('u', lt(x, v('lower'))), op('u', lt(v('upper'), x))))
    interval = lam('t', 'b', call('kf', v('lower'), v('upper'), v('t')))
    text += definition('kg', 'lower b upper b x h[b] b y h[b] b z h[b] b', both(
        lt(v('lower'), v('upper')),
        *[call('ke', interval, v(axis)) for axis in ('x', 'y', 'z')],
        *[op('e', app(v(axis), v('lower')), app(v(axis), v('upper'))) for axis in ('x', 'y', 'z')]))
    # Real-domain forms quantify every candidate cut and explicitly guard
    # validity; a predicate on Q is not automatically a real number.
    valid = lambda a: call('ba', a)
    positive = lambda a: both(valid(a), call('bg', call('bb', ZERO), a))
    real_input = lambda a: both(valid(a), inside(a))
    text += definition('la', 'domain ' + D + ' function ' + F, quant('f', 'x', R,
        op('y', real_input(x), valid(fn(x)))))
    text += definition('lb', 'left ' + R + ' right ' + R + ' radius ' + R, both(
        valid(v('left')), valid(v('right')), positive(v('radius')),
        call('bg', v('left'), call('bd', v('right'), v('radius'))),
        call('bg', v('right'), call('bd', v('left'), v('radius')))))
    text += definition('lc', 'domain ' + D + ' point ' + R, both(valid(point),
        quant('f', 'epsilon', R, op('y', positive(epsilon), quant('g', 'x', R,
            both(real_input(x), op('u', op('e', x, point)), call('lb', x, point, epsilon)))))))
    real_limit = quant('f', 'epsilon', R, op('y', positive(epsilon), quant('g', 'delta', R, both(
        positive(delta), quant('f', 'x', R, op('y', both(real_input(x), op('u', op('e', x, point)), call('lb', x, point, delta)),
            call('lb', fn(x), value, epsilon)))))))
    text += definition('ld', 'domain ' + D + ' function ' + F + ' point ' + R + ' value ' + R,
        both(call('la', v('domain'), v('function')), valid(value), call('lc', v('domain'), point), real_limit))
    real_continuous = quant('f', 'epsilon', R, op('y', positive(epsilon), quant('g', 'delta', R, both(
        positive(delta), quant('f', 'x', R, op('y', both(real_input(x), call('lb', x, point, delta)),
            call('lb', fn(x), fn(point), epsilon)))))))
    text += definition('le', 'domain ' + D + ' function ' + F + ' point ' + R,
        both(call('la', v('domain'), v('function')), real_input(point), real_continuous))
    text += definition('lf', 'domain ' + D + ' function ' + F, both(call('la', v('domain'), v('function')),
        quant('f', 'point', R, op('y', real_input(point), call('le', v('domain'), v('function'), point)))))
    text += definition('lg', 'lower ' + R + ' upper ' + R + ' x ' + R,
        both(valid(v('lower')), valid(v('upper')), valid(x), call('bc', v('lower'), x), call('bc', x, v('upper'))))
    interval = lam('t', R, call('lg', v('lower'), v('upper'), v('t')))
    text += definition('lh', 'lower ' + R + ' upper ' + R + ' x ' + F + ' y ' + F + ' z ' + F, both(
        valid(v('lower')), valid(v('upper')), call('bg', v('lower'), v('upper')),
        *[call('lf', interval, v(axis)) for axis in ('x', 'y', 'z')],
        *[op('e', app(v(axis), v('lower')), app(v(axis), v('upper'))) for axis in ('x', 'y', 'z')]))
    punctured = lam('t', R, both(app(v('domain'), v('t')), op('u', op('e', v('t'), point))))
    quotient = lam('t', R, call('cd', call('bf', fn(v('t')), fn(point)), call('cg', call('bf', v('t'), point))))
    text += definition('li', 'domain ' + D + ' function ' + F + ' point ' + R + ' derivative ' + R, both(
        call('la', v('domain'), v('function')), real_input(point),
        call('ld', punctured, quotient, point, v('derivative'))))
    return text


def composed():
    base = (ROOT / 'examples/v011/real-products.noema').read_text(encoding='utf-8')
    doc = parse(base + definitions())
    basis = deepcopy(json.loads((ROOT / 'data/real-products-basis-v1.json').read_text(encoding='utf-8')))
    basis['version'] = 'limits-basis-v1'
    basis['document'] = 'examples/v011/limits.noema'
    basis['definitions'].update({
        'ka': '有理数の二値の距離が指定した正の半径より厳密に小さい。両向きの差の不等式で定義する。',
        'kb': '有理数領域で、どの正の半径内にも指定点とは異なる定義域の点が存在する集積条件。',
        'kc': '有理数領域で、指定点が集積点であり、任意の正の精度に対して近傍半径を選び、その穿孔近傍内の定義域で関数値が目標値へ近づく。',
        'kd': '有理数領域の定義域内の点における相対的な連続性。孤立点でも成立し得る。',
        'ke': '有理数領域の定義域の全点におけるkd。',
        'kf': '有理数xが指定した閉区間の中にある。下端が上端より大きければ空となる。',
        'kg': '正の長さの有理数パラメータ区間で三成分が連続し、両端の値が一致する。有理数領域に限定した検証用の曲線で、実数全域の曲線の代用ではない。',
        'la': '有効な実切断のうち指定定義域の全入力で、関数値も有効な実切断である。',
        'lb': '有効な実切断の二値が、指定された有効で正の半径より互いに近い。加算と厳密な順序で定義する。',
        'lc': '有効な実切断の指定点が、定義域の有効な実切断からなる集合の集積点である。',
        'ld': '実切断上でlaとlcを満たす関数の、穿孔近傍を使う相対的な極限。目標値も有効な実切断である。',
        'le': '実切断上でlaを満たす関数の、定義域内の有効な点における相対的な連続性。',
        'lf': '実切断上でlaを満たす関数の、定義域の全有効点における連続性。',
        'lg': '有効な三実切断について、xが下端以上かつ上端以下である閉区間の関係。',
        'lh': '正の長さの実パラメータ閉区間で、三つの実座標関数が連続し、両端の位置が一致する閉曲線。自己交差や停止、角の存在は除外しない。',
        'li': '定義域内の有効な点において、非零の入力差に対する差商のld極限が指定値になる微分関係。定義域に対する相対的な導関数であり、端点では片側の条件になり得る。'})
    basis['unresolved'] += [
        '有理数領域の線形な具体例の検証を、実数全域の連続性や完全性の証明として流用しない。',
        'lhは位相的な連続閉曲線であり、原文の曲がった曲線についての滑らかさの程度や物理的な運動を全て定義したものではない。',
        '差商を除く点を明示したが、実切断での微分法則や微積分学の一般定理の機械的証明は未完。',
        '折れ線列から曲線への収束、速度と時計指示の積分、加速の前提、著者が仮定する発話との接続は未完。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def main():
    text, basis = composed()
    for relative, body in {basis['document']: text,
                           'data/limits-basis-v1.json': json.dumps(basis, ensure_ascii=False, indent=2) + '\n'}.items():
        path = ROOT / relative
        if path.exists():
            if path.read_text(encoding='utf-8') != body:
                raise ValueError('Stored limits differ: ' + relative)
        else:
            with path.open('x', encoding='utf-8', newline='\n') as stream:
                stream.write(body)
    print('Relative limits, continuity and real closed curves defined using existing syntax')


if __name__ == '__main__':
    main()
