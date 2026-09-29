"""Relative asymptotic error bounds and a clock's second-order source formula."""
from copy import deepcopy
import json

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from scripts.compose_limits import ROOT, R, F, D, ZERO, v, call, app, op, both, quant, lam


def define(name, params, result, body):
    return 'd ' + name + '[' + params + '] ' + result + '[' + body + '].\n'


def definitions():
    zero, one = call('bb', ZERO), call('bb', 'n p b b')
    half = call('bb', 'n p b c')
    lt = lambda a, b: call('aa', a, b)
    le = lambda a, b: op('u', lt(b, a))
    neg = lambda a: call('ac', a)
    sub = lambda a, b: call('ab', a, neg(b))
    bound = call('ad', v('constant'), v('scale'))
    text = define('oi', 'error b scale b constant b', 'c', both(le(ZERO, v('constant')),
        op('x', both(le(ZERO, v('scale')), le(neg(bound), v('error')), le(v('error'), bound)),
           both(lt(v('scale'), ZERO), le(bound, v('error')), le(v('error'), neg(bound))))))
    near = both(app(v('domain'), v('x')), op('u', op('e', v('x'), v('point'))), call('ka', v('x'), v('point'), v('delta')))
    params = 'domain h[b] c function h[b] b approximation h[b] b scale h[b] b point b'
    text += define('oa', params + ' constant b delta b', 'c', both(lt(ZERO, v('constant')), lt(ZERO, v('delta')),
        quant('f', 'x', 'b', op('y', near, call('oi', sub(app(v('function'), v('x')), app(v('approximation'), v('x'))),
                                                       app(v('scale'), v('x')), v('constant'))))))
    text += define('ob', params, 'c', both(call('kb', v('domain'), v('point')),
        quant('g', 'constant', 'b', quant('g', 'delta', 'b', call('oa', *(v(n) for n in ('domain', 'function', 'approximation', 'scale', 'point', 'constant', 'delta')))))))
    params = 'domain ' + D + ' function ' + F + ' approximation ' + F + ' scale ' + F + ' point ' + R
    near = both(call('ba', v('x')), app(v('domain'), v('x')), op('u', op('e', v('x'), v('point'))), call('lb', v('x'), v('point'), v('delta')))
    text += define('oc', params + ' constant ' + R + ' delta ' + R, 'c', both(
        *[call('la', v('domain'), v(n)) for n in ('function', 'approximation', 'scale')],
        *[call('ba', v(n)) for n in ('point', 'constant', 'delta')],
        call('bg', zero, v('constant')), call('bg', zero, v('delta')),
        quant('f', 'x', R, op('y', near,
            call('bc', call('cb', call('bf', app(v('function'), v('x')), app(v('approximation'), v('x')))),
                 call('cd', v('constant'), call('cb', app(v('scale'), v('x')))))))))
    text += define('od', params, 'c', both(call('lc', v('domain'), v('point')),
        quant('g', 'constant', R, quant('g', 'delta', R, call('oc', *(v(n) for n in ('domain', 'function', 'approximation', 'scale', 'point', 'constant', 'delta')))))))
    squared = call('cd', v('x'), v('x'))
    text += define('oe', 'x ' + R, R, call('bf', one, call('cj', call('bf', one, squared))))
    text += define('of', 'x ' + R, R, call('cd', half, squared))
    text += define('og', 'x ' + R, R, call('cd', squared, squared))
    domain = lam('x', R, both(call('ba', v('x')), call('bg', call('cb', v('x')), one)))
    text += define('oh', '', 'c', call('od', domain, 'p oe', 'p of', 'p og', zero))
    return text


def explanations():
    return {
        'oi': '有理数の誤差の絶対値が、非負の定数と比較尺度の絶対値の積以下である。尺度の符号を分けた不等式で表す。',
        'oa': '有理数領域の穿孔近傍で、関数と近似の誤差が指定された正の定数と比較尺度で抑えられる。定数と近傍幅はxごとには変更しない。',
        'ob': '定義域の集積点で、ある正の定数と近傍幅を選べばoaが全対象点で成立する。定義域に対するBig-O型の誤差条件。',
        'oc': '実切断領域で、関数・近似・比較尺度の値の妥当性を確認し、正の定数と正の穿孔近傍幅による誤差上限を要求する。',
        'od': '有効な実切断の集積点で、正の定数と近傍幅が存在してocを満たす漸近的な誤差条件。',
        'oe': '速度比xについての厳密な単位時間の遅れ1-sqrt(1-x²)の構成式。実数としての意味は|x|<1の定義域で用いる。',
        'of': '速度比xについて二次近似x²/2を作る。',
        'og': '速度比xの四乗を作る。',
        'oh': '|x|<1の実領域で、oeとofの誤差がx=0においてogのオーダーで抑えられるという内容。これを定義したこと自体を証明とは数えない。'}


def composed():
    base = (ROOT / 'examples/v011/limits.noema').read_text(encoding='utf-8')
    doc = parse(base + definitions())
    basis = deepcopy(json.loads((ROOT / 'data/limits-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='asymptotics-basis-v1', document='examples/v011/asymptotics.noema')
    basis['definitions'].update(explanations())
    basis['unresolved'] += ['誤差条件の定義とその証明を区別する。実切断の全域でohが成立することの機械的証明は未完。',
                            '近づく点・定義域・比較尺度を明示したBig-O型を扱う。確率的誤差、測定精度、任意の漸近展開の全体系ではない。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def source_composed():
    base = parse((ROOT / 'examples/v014/einstein-curve-discourse.noema').read_text(encoding='utf-8'))
    statements, base['statements'] = base['statements'], []
    doc = parse(format_graph(base, 'compact') + '\n' + definitions())
    zero, one = call('bb', ZERO), call('bb', 'n p b b')
    half, eighth = call('bb', 'n p b c'), call('bb', 'n p b i')
    square = lambda a: call('cd', a, a)
    ratio = call('cd', v('speed'), call('cg', v('light')))
    ratio2, ratio4 = square(ratio), square(square(ratio))
    body = both(*[call('ba', v(n)) for n in ('speed', 'light', 'factor', 'duration', 'gap', 'approximation', 'error')],
        call('ca', v('speed')), call('bg', v('speed'), v('light')), call('bg', zero, v('light')),
        call('bg', zero, v('factor')), call('ca', v('duration')),
        op('e', call('cd', square(v('light')), square(v('factor'))), call('bf', square(v('light')), square(v('speed')))),
        op('e', v('gap'), call('cd', v('duration'), call('bf', one, v('factor')))),
        op('e', v('approximation'), call('cd', half, call('cd', v('duration'), ratio2))),
        op('e', v('error'), call('bf', v('gap'), v('approximation'))),
        call('bc', call('cd', eighth, call('cd', v('duration'), ratio4)), v('error')),
        call('bc', v('error'), call('cd', half, call('cd', v('duration'), ratio4))))
    text = format_graph(doc, 'compact') + '\n' + define('qe', ' '.join(n + ' ' + R for n in ('speed', 'light', 'factor', 'duration', 'gap', 'approximation', 'error')), 'c', body)
    doc = parse(text)
    # Preserve the exact same quantified observation and constant-speed
    # antecedent. Replace only the consequent with an explicit remainder.
    old = deepcopy(next(d for d in doc['declarations'] if d['name'] == 'qd'))
    old['name'] = 'qf'
    matrix = old['body']['body']
    variables = []
    while matrix['kind'] == 'forall':
        variables.append(matrix['variable'])
        matrix = matrix['body']
    if matrix['kind'] != 'implies':
        raise ValueError('Unexpected source claim structure')
    from scripts.compose_curve_discourse import OBS
    names = dict(zip([n for n, _ in OBS] + ['speed', 'factor'], variables, strict=True))
    var = lambda n: {'kind': 'variable', 'name': names[n]}
    c = lambda symbol, *args: {'kind': 'call', 'symbol': symbol, 'arguments': list(args)}
    approximate, error = 'approximatevalue', 'errorvalue'
    consequent = c('qe', var('speed'), var('light'), var('factor'), c('bf', var('upper'), var('lower')),
                   c('bf', var('upper'), var('reading')), {'kind': 'variable', 'name': approximate}, {'kind': 'variable', 'name': error})
    cut = {'kind': 'function', 'parameters': ['number'], 'result': 'truth'}
    for name in (error, approximate):
        consequent = {'kind': 'exists', 'variable': name, 'sort': cut, 'body': consequent}
    matrix['arguments'][1] = consequent
    doc['declarations'].append(old)
    # This is the authored conditional conclusion, not an unconditional claim.
    result_description = statements[-1]['body']['arguments'][-1]
    if result_description != {'kind': 'quote', 'body': {'kind': 'call', 'symbol': 'qd', 'arguments': []}}:
        raise ValueError('Unexpected source conclusion description')
    result_description['body']['symbol'] = 'qf'
    doc['statements'] = statements
    basis = deepcopy(json.loads((ROOT / 'data/curve-discourse-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='curve-approximation-basis-v1', document='examples/v014/einstein-curve-approximation.noema')
    basis['definitions'].update(explanations())
    basis['definitions'].update({
        'qe': '光速未満の一定速度について、厳密な指示差、二次近似、残差を区別する。残差はT*(v/V)^4/8以上、T*(v/V)^4/2以下という明示した評価を採る。この定数の境界は原文の逐語的な記述ではなく、高次項の省略を説明する数学的な補足である。',
        'qf': 'qdと同じ観測・一定速度の前提の下で、qeを満たす近似値と誤差が存在するという内容。仮定範囲内の帰結に置き、厳密値と近似値を等置しない。'})
    basis['unresolved'] += ['二次近似の式と四次の残差を今回接続した。継承した未解決欄は以前の草案の記録として保持する。',
                            '四次誤差の上界は区間時間Tを固定した評価であり、Tを速度に依存させる場合の一様な評価とは主張しない。',
                            '全実切断での近似評価の機械的証明、世界線・観測・単位、前の折れ線の証明内容、地球上の推論は未完。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def main():
    for compose, filename in ((composed, 'data/asymptotics-basis-v1.json'),
                              (source_composed, 'data/curve-approximation-basis-v1.json')):
        text, basis = compose()
        for name, body in {basis['document']: text, filename: json.dumps(basis, ensure_ascii=False, indent=2) + '\n'}.items():
            path = ROOT / name
            if path.exists():
                if path.read_text(encoding='utf-8') != body:
                    raise ValueError('Stored asymptotics differ: ' + name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream:
                    stream.write(body)
    print('Asymptotic errors and the source second-order clock term are separate from exact equality')


if __name__ == '__main__':
    main()
