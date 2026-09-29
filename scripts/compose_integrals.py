"""Tagged partitions and integrals, expressed with functions and finite folds."""
from copy import deepcopy
import json

from noema.grammar import format_graph, parse
from noema.language import convert
from noema.meaning_basis import audit_basis
from scripts.compose_limits import ROOT, R, F, ZERO, v, call, app, op, both, quant, lam

ONE, TWO = 'n p b b', 'n p c b'


def definition(name, parameters, result, body):
    return 'd ' + name + '[' + parameters + '] ' + result + '[' + body + '].\n'


def fold(sequence, initial, params, body):
    return 'q[' + sequence + '][' + initial + '][i[' + params + '][' + body + ']]'


def families(real=False):
    prefix, scalar = ('n', R) if real else ('m', 'b')
    cell = 'h[b] ' + scalar
    cells = 'j[' + cell + ']'
    function = 'h[' + scalar + '] ' + scalar
    zero = call('bb', ZERO) if real else ZERO
    valid = lambda x: call('ba', x) if real else op('e', x, x)
    lt = lambda x, y: call('bg' if real else 'aa', x, y)
    le = lambda x, y: call('bc', x, y) if real else op('u', call('aa', y, x))
    sub = lambda x, y: call('bf', x, y) if real else call('ab', x, call('ac', y))
    add = lambda x, y: call('bd' if real else 'ab', x, y)
    mul = lambda x, y: call('cd' if real else 'ad', x, y)
    neg = lambda x: call('be' if real else 'ac', x)
    left, right, tag = [app(v('cell'), index) for index in (ZERO, ONE, TWO)]
    cell_valid = both(valid(left), valid(right), valid(tag), lt(left, right), le(left, tag), le(tag, right))
    text = definition(prefix + 'a', 'cell ' + cell, 'c', cell_valid)
    all_valid = fold(v('partition'), op('e', ZERO, ZERO), 'state c cell ' + cell,
                     both(v('state'), call(prefix + 'a', v('cell'))))
    chain = app(fold(v('partition'), lam('point', scalar, op('e', v('point'), v('lower'))),
                     'state h[' + scalar + '] c cell ' + cell,
                     lam('point', scalar, both(app(v('state'), left), op('e', v('point'), right)))), v('upper'))
    text += definition(prefix + 'b', 'partition ' + cells + ' lower ' + scalar + ' upper ' + scalar, 'c',
        both(valid(v('lower')), valid(v('upper')), lt(v('lower'), v('upper')),
             call('aa', ZERO, 'd[' + v('partition') + ']'), all_valid, chain))
    text += definition(prefix + 'c', 'partition ' + cells + ' delta ' + scalar, 'c',
        both(valid(v('delta')), lt(zero, v('delta')),
             fold(v('partition'), op('e', ZERO, ZERO), 'state c cell ' + cell,
                  both(v('state'), call(prefix + 'a', v('cell')), lt(sub(right, left), v('delta'))))))
    text += definition(prefix + 'd', 'partition ' + cells + ' function ' + function, scalar,
        fold(v('partition'), zero, 'state ' + scalar + ' cell ' + cell,
             add(v('state'), mul(sub(right, left), app(v('function'), tag)))))
    positive = lambda x: both(valid(x), lt(zero, x))
    qualifies = both(call(prefix + 'b', v('partition'), v('lower'), v('upper')), call(prefix + 'c', v('partition'), v('delta')))
    # Admit only radii for which some partition exists, then require every
    # qualifying partition and every choice of tags to obey the same bound.
    approximation = quant('f', 'epsilon', scalar, op('y', positive(v('epsilon')),
        quant('g', 'delta', scalar, both(positive(v('delta')), quant('g', 'partition', cells, qualifies),
            quant('f', 'partition', cells, op('y', qualifies,
                call('lb' if real else 'ka', call(prefix + 'd', v('partition'), v('function')), v('value'), v('epsilon'))))))))
    conditions = [valid(v('lower')), valid(v('upper')), valid(v('value')), lt(v('lower'), v('upper'))]
    if real:
        conditions.append(call('la', lam('x', R, call('lg', v('lower'), v('upper'), v('x'))), v('function')))
    text += definition(prefix + 'e', 'lower ' + scalar + ' upper ' + scalar + ' function ' + function + ' value ' + scalar,
                       'c', both(*conditions, approximation))
    oriented = [valid(v('lower')), valid(v('upper')), valid(v('value'))]
    if real:
        oriented.append(call('la', lam('x', R, op('x', call('lg', v('lower'), v('upper'), v('x')),
                                                  call('lg', v('upper'), v('lower'), v('x')))), v('function')))
    text += definition(prefix + 'f', 'lower ' + scalar + ' upper ' + scalar + ' function ' + function + ' value ' + scalar,
        'c', both(*oriented,
                  op('x', both(op('e', v('lower'), v('upper')), op('e', v('value'), zero)),
                     op('x', call(prefix + 'e', v('lower'), v('upper'), v('function'), v('value')),
                        call(prefix + 'e', v('upper'), v('lower'), v('function'), neg(v('value')))))))
    return text


def definitions():
    text = families() + families(real=True)
    # Exact polynomial interpolation makes a three-field record writable in
    # Noema, without new primitives or a partial field lookup operation.
    sub = lambda x, y: call('ab', x, call('ac', y))
    mul = lambda x, y: call('ad', x, y)
    index = v('index')
    weights = [mul('n p b c', mul(sub(index, ONE), sub(index, TWO))),
               call('ac', mul(index, sub(index, TWO))), mul('n p b c', mul(index, sub(index, ONE)))]
    fields = ('left', 'right', 'tag')
    terms = [mul(v(field), weight) for field, weight in zip(fields, weights, strict=True)]
    text += definition('mg', 'left b right b tag b', 'h[b] b',
                       lam('index', 'b', call('ab', terms[0], call('ab', terms[1], terms[2]))))
    terms = [call('cd', v(field), call('bb', weight)) for field, weight in zip(fields, weights, strict=True)]
    text += definition('ni', ' '.join(field + ' ' + R for field in fields), 'h[b] ' + R,
                       lam('index', 'b', call('bd', terms[0], call('bd', terms[1], terms[2]))))
    domain = lam('t', R, call('lg', v('lower'), v('upper'), v('t')))
    rate = app(v('rate'), v('t'))
    zero, one = call('bb', ZERO), call('bb', ONE)
    params = 'lower ' + R + ' upper ' + R + ' rate ' + F + ' elapsed ' + R + ' lost ' + R
    text += definition('ng', params, 'c', both(
        call('ba', v('lower')), call('ba', v('upper')), call('bg', v('lower'), v('upper')),
        call('lf', domain, v('rate')), call('ba', v('elapsed')), call('ba', v('lost')),
        quant('f', 't', R, op('y', app(domain, v('t')), both(call('bg', zero, rate), call('bc', rate, one)))),
        call('ne', v('lower'), v('upper'), v('rate'), v('elapsed')),
        op('e', v('lost'), call('bf', call('bf', v('upper'), v('lower')), v('elapsed')))))
    params += ' light ' + R + ' ' + ' '.join(name + ' ' + F for name in ('x', 'y', 'z', 'vx', 'vy', 'vz'))
    light2 = call('cd', v('light'), v('light'))
    squares = [call('cd', app(v('v' + axis), v('t')), app(v('v' + axis), v('t'))) for axis in ('x', 'y', 'z')]
    speed2 = call('bd', squares[0], call('bd', squares[1], squares[2]))
    text += definition('nh', params, 'c', both(
        call('ng', v('lower'), v('upper'), v('rate'), v('elapsed'), v('lost')),
        call('ba', v('light')), call('bg', zero, v('light')),
        call('lh', v('lower'), v('upper'), v('x'), v('y'), v('z')),
        quant('f', 't', R, op('y', app(domain, v('t')), both(
            *[call('li', domain, v(axis), v('t'), app(v('v' + axis), v('t'))) for axis in ('x', 'y', 'z')],
            call('bg', speed2, light2),
            op('e', call('cd', light2, call('cd', rate, rate)), call('bf', light2, speed2)))))))
    return text


def composed():
    base = convert(parse((ROOT / 'examples/v011/limits.noema').read_text(encoding='utf-8')), '0.14')
    doc = parse(format_graph(base, 'compact') + '\n' + definitions())
    basis = deepcopy(json.loads((ROOT / 'data/limits-basis-v1.json').read_text(encoding='utf-8')))
    basis['version'] = 'integrals-basis-v1'
    basis['document'] = 'examples/v014/integrals.noema'
    meanings = {
        'a': '一つのタグ付き区間の左右端と代表点の妥当性。左端より右端が大きく、代表点は両端を含む区間内にある。',
        'b': '空でない順序付き区間列が、指定した下端から上端へ、隙間や重複なく接続するタグ付き分割。',
        'c': '正のdeltaを指定し、各区間が妥当でその幅がdeltaより厳密に小さい。空列はこの条件だけなら成立するが、積分ではbも要求する。',
        'd': '各代表点での関数値に区間幅を掛け、先頭から加算した式。空列では0。分割や関数の妥当性は呼出し側の条件である。',
        'e': '下端より上端が大きい区間の積分関係。任意の正の精度で正の細かさを選び、その細かさの分割が実際に存在し、全てのその分割と代表点で和が指定値へ近づく。',
        'f': '向き付きの積分関係。等しい両端では値0、逆向きでは正方向の積分の符号を反転する。'}
    for prefix, domain in (('m', '有理数領域。'), ('n', '有効な実切断の領域。')):
        for suffix, meaning in meanings.items():
            basis['definitions'][prefix + suffix] = domain + meaning
    basis['definitions'].update({
        'mg': '三つの有理数から区間レコードを作る。0,1,2でそれぞれ左端、右端、代表点となる二次多項式で、他の入力にも値を持つ。補間は欄の実装にだけ使い、曲線や積分の近似ではない。',
        'ni': '三つの実切断から区間レコードを作る。mgと同じ有理数の係数を実数へ埋め込んだ線形結合で、0,1,2でそれぞれ指定切断と一致する構成。一般の切断上の一致の機械的証明は未完。',
        'ng': '正の長さの実時間区間で、連続かつ正で1以下の進み率の積分を経過とし、区間時間との差を遅れとする。時計の機構や観測の存在は断定しない。',
        'nh': 'ngと連続閉曲線を結び、各時刻の三速度成分を座標の相対微分で指定し、正の光速未満という条件と進み率の式を課す。この曲線上の理想時計の法則を採用した条件であり、加速の物理的な導出ではない。'})
    basis['unresolved'] += [
        'タグ付き区間は関数型のレコードとして、0番を左端、1番を右端、2番を代表点とする。他の入力での値はこの表現では参照しない。数字は構造上の欄番号であって個別概念の意味の置換表ではない。',
        '全分割を有限個で代用しない。具体的な有限和の検査や多項式の性質は、積分全域の機械的な証明ではない。',
        'nhは連続な進み率と各時刻での微分を要求する限定した曲線モデルである。角のある折れ線、より一般の可積分な速度、原文の滑らかさの全解釈を同一視しない。',
        '曲線の実際の時計・測定・単位への接続、仮定としての著者の発話、地球上の比較、実切断の微積分法則の機械的証明は未完。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def main():
    text, basis = composed()
    for relative, body in {basis['document']: text,
                           'data/integrals-basis-v1.json': json.dumps(basis, ensure_ascii=False, indent=2) + '\n'}.items():
        path = ROOT / relative
        if path.exists():
            if path.read_text(encoding='utf-8') != body:
                raise ValueError('Stored integrals differ: ' + relative)
        else:
            with path.open('x', encoding='utf-8', newline='\n') as stream:
                stream.write(body)
    print('Tagged partitions and integral relations composed without new primitives')


if __name__ == '__main__':
    main()
