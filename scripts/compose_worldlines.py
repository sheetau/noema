"""Bind real trajectories to object-event incidence and shared coordinate units."""
from copy import deepcopy
import json

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from scripts.compose_limits import ROOT, R, F, ZERO, v, call, app, op, both, quant, lam
from scripts.compose_curve_discourse import OBS

EXTRA = [('lengthunit', 'a'), ('context', 'd'), ('lengthaxis', 'a'), ('timeaxis', 'a'),
         ('lengthdim', 'h[a] b'), ('timedim', 'h[a] b'), ('lengthscale', 'b'), ('timescale', 'b'), ('dial', F)]


def define(name, params, body):
    return 'd ' + name + '[' + params + '] c[' + body + '].\n'


def universal(params, body):
    for name, sort in reversed(params):
        body = quant('f', name, sort, body)
    return body


def definitions():
    text = ('r tf[a a d a a ' + ' '.join([R] * 4) + '] c.\n'
            'r tg[a a d] c.\nr tj[a d a a ' + R + '] c.\nr tk[a d] c.\nr tl[a h[a] b b] c.\n')
    coords = ('time', 'x', 'y', 'z')
    location = 'event a frame a context d lengthunit a timeunit a '
    point = [v(n) for n in ('event', 'frame', 'context', 'lengthunit', 'timeunit', *coords)]
    text += define('sa', location + ' '.join(n + ' ' + R for n in coords),
                   both(*[call('ba', v(n)) for n in coords], call('tf', *point)))
    text += define('sb', 'object a ' + location + ' '.join(n + ' ' + R for n in coords),
                   both(call('tg', v('object'), v('event'), v('context')), call('sa', *point)))
    text += define('sc', 'clock a ' + location + ' '.join(n + ' ' + R for n in (*coords, 'reading')),
        both(call('ta', v('clock')), call('te', v('timeunit')), call('ba', v('reading')),
             call('sb', v('clock'), *point), call('tb', v('clock'), v('event'), v('frame'), v('timeunit'), v('reading'))))
    first = [v(n) for n in ('event', 'frame', 'context', 'lengthunit', 'timeunit', *coords)]
    second = [v(n) for n in ('event', 'frame', 'context', 'lengthunit', 'timeunit')] + [v('other' + n) for n in coords]
    consistency = op('y', both(call('sa', *first), call('sa', *second)), both(*[op('e', v(n), v('other' + n)) for n in coords]))
    text += define('sd', 'frame a context d lengthunit a timeunit a', universal(
        [('event', 'a')] + [(n, R) for n in coords] + [('other' + n, R) for n in coords], consistency))
    trajectory = [('object', 'a'), ('frame', 'a'), ('context', 'd'), ('lengthunit', 'a'), ('timeunit', 'a'),
                  ('lower', R), ('upper', R)] + [(n, F) for n in ('x', 'y', 'z')]
    point_at = [v(n) for n in ('object', 'event', 'frame', 'context', 'lengthunit', 'timeunit')] + [v('time')] + [app(v(n), v('time')) for n in ('x', 'y', 'z')]
    observed_at = [v(n) for n in ('object', 'event', 'frame', 'context', 'lengthunit', 'timeunit', 'time')] + [v('observed' + n) for n in ('x', 'y', 'z')]
    interval = call('lg', v('lower'), v('upper'), v('time'))
    domain = lam('time', R, interval)
    text += define('se', ' '.join(n + ' ' + t for n, t in trajectory), both(
        call('ba', v('lower')), call('ba', v('upper')), call('bg', v('lower'), v('upper')),
        *[call('la', domain, v(n)) for n in ('x', 'y', 'z')],
        call('sd', v('frame'), v('context'), v('lengthunit'), v('timeunit')),
        quant('f', 'time', R, op('y', interval, quant('g', 'event', 'a', call('sb', *point_at)))),
        universal([('event', 'a'), ('time', R)] + [('observed' + n, R) for n in ('x', 'y', 'z')],
            op('y', both(interval, call('sb', *observed_at)), both(*[op('e', v('observed' + n), app(v(n), v('time'))) for n in ('x', 'y', 'z')])))))
    text += define('sf', 'lengthunit a timeunit a lengthaxis a timeaxis a lengthdim h[a] b timedim h[a] b lengthscale b timescale b', both(
        op('u', op('e', v('lengthunit'), v('timeunit'))), op('u', op('e', v('lengthaxis'), v('timeaxis'))),
        call('dh', v('lengthaxis'), v('lengthdim')), call('dh', v('timeaxis'), v('timedim')),
        call('aa', ZERO, v('lengthscale')), call('aa', ZERO, v('timescale')),
        call('tl', v('lengthunit'), v('lengthdim'), v('lengthscale')), call('tl', v('timeunit'), v('timedim'), v('timescale'))))
    text += define('sn', 'clock a frame a context d timeunit a', universal([('event', 'a'), ('left', R), ('right', R)],
        op('y', both(call('tg', v('clock'), v('event'), v('context')), call('ba', v('left')), call('ba', v('right')),
                     call('tb', v('clock'), v('event'), v('frame'), v('timeunit'), v('left')),
                     call('tb', v('clock'), v('event'), v('frame'), v('timeunit'), v('right'))), op('e', v('left'), v('right')))))
    text += define('sg', ' '.join(n + ' ' + t for n, t in trajectory) + ' dial ' + F, both(
        call('ta', v('object')), call('te', v('timeunit')), call('sn', v('object'), v('frame'), v('context'), v('timeunit')),
        call('se', *(v(n) for n, _ in trajectory)), call('la', domain, v('dial')),
        universal([('event', 'a'), ('time', R)] + [('observed' + n, R) for n in ('x', 'y', 'z')],
            op('y', both(interval, call('sb', *observed_at)), call('tb', v('object'), v('event'), v('frame'), v('timeunit'), app(v('dial'), v('time')))))))
    # OBS calls its shared coordinate/dial time unit simply "unit".
    common = [v(n) for n in ('frame', 'context', 'lengthunit', 'unit', 'lower', 'upper')]
    moving = call('sg', v('clock'), *common, v('x'), v('y'), v('z'), v('dial'))
    stationary = call('sg', v('reference'), *common,
                       *[lam('time', R, app(v(n), v('lower'))) for n in ('x', 'y', 'z')], lam('time', R, v('time')))
    endpoints = []
    for event, time in (('first', 'lower'), ('last', 'upper')):
        for obj in ('clock', 'reference'):
            endpoints.append(call('sb', v(obj), v(event), v('frame'), v('context'), v('lengthunit'), v('unit'), v(time),
                                  *[app(v(n), v(time)) for n in ('x', 'y', 'z')]))
    text += define('sh', ' '.join(n + ' ' + t for n, t in OBS + EXTRA), both(
        call('qb', *(v(n) for n, _ in OBS)),
        call('sf', *(v(n) for n in ('lengthunit', 'unit', 'lengthaxis', 'timeaxis', 'lengthdim', 'timedim', 'lengthscale', 'timescale'))),
        call('tk', v('frame'), v('context')), call('tj', v('frame'), v('context'), v('lengthunit'), v('unit'), v('light')),
        moving, stationary, *endpoints, op('e', app(v('dial'), v('lower')), v('lower')),
        op('e', app(v('dial'), v('upper')), v('reading'))))
    # Concrete rational observations are valid real embeddings. They expose
    # the same bindings without pretending to enumerate every real cut.
    numbers = [call('bb', v(n)) for n in coords]
    text += define('sk', 'clock a ' + location + ' '.join(n + ' b' for n in (*coords, 'reading')), both(
        call('ta', v('clock')), call('te', v('timeunit')), call('tg', v('clock'), v('event'), v('context')),
        call('tf', *(v(n) for n in ('event', 'frame', 'context', 'lengthunit', 'timeunit')), *numbers),
        call('tb', v('clock'), v('event'), v('frame'), v('timeunit'), call('bb', v('reading')))))
    text += define('sl', 'frame a context d lengthunit a timeunit a lengthaxis a timeaxis a lengthdim h[a] b timedim h[a] b lengthscale b timescale b light b', both(
        call('sf', *(v(n) for n in ('lengthunit', 'timeunit', 'lengthaxis', 'timeaxis', 'lengthdim', 'timedim', 'lengthscale', 'timescale'))),
        call('tk', v('frame'), v('context')), call('aa', ZERO, v('light')),
        call('tj', v('frame'), v('context'), v('lengthunit'), v('timeunit'), call('bb', v('light')))))
    real_first = [v(n) for n in ('event', 'frame', 'context', 'lengthunit', 'timeunit')] + [call('bb', v(n)) for n in coords]
    real_second = [v(n) for n in ('event', 'frame', 'context', 'lengthunit', 'timeunit')] + [call('bb', v('other' + n)) for n in coords]
    text += define('sm', location + ' '.join(n + ' b' for n in coords) + ' ' + ' '.join('other' + n + ' b' for n in coords),
        op('y', both(call('tf', *real_first), call('tf', *real_second)), both(*[op('e', v(n), v('other' + n)) for n in coords])))
    text += define('so', 'clock a event a frame a context d timeunit a left b right b', op('y',
        both(call('tg', v('clock'), v('event'), v('context')),
             call('tb', v('clock'), v('event'), v('frame'), v('timeunit'), call('bb', v('left'))),
             call('tb', v('clock'), v('event'), v('frame'), v('timeunit'), call('bb', v('right')))), op('e', v('left'), v('right'))))
    return text


def composed():
    doc = parse((ROOT / 'examples/v014/einstein-curve-approximation.noema').read_text(encoding='utf-8'))
    statements, doc['statements'] = doc['statements'], []
    basis = deepcopy(json.loads((ROOT / 'data/curve-approximation-basis-v1.json').read_text(encoding='utf-8')))
    quantities = parse((ROOT / 'examples/v011/quantities.noema').read_text(encoding='utf-8'))
    quantity_basis = json.loads((ROOT / 'data/quantities-basis-v1.json').read_text(encoding='utf-8'))
    for d in quantities['declarations']:
        if d['name'] in ('da', 'db', 'dc', 'dd', 'de', 'df', 'dg', 'dh'):
            doc['declarations'].append(deepcopy(d))
            basis['definitions'][d['name']] = quantity_basis['definitions'][d['name']]
    doc = parse(format_graph(doc, 'compact') + '\n' + definitions())
    extra_types = parse('n:r extra[' + ' '.join(t for _, t in EXTRA) + '] c.')['declarations'][0]['parameters']
    for source, target in (('qc', 'qi'), ('qf', 'qj')):
        item = deepcopy(next(d for d in doc['declarations'] if d['name'] == source))
        item['name'] = target
        extra_names = ['world' + name for name, _ in EXTRA]
        def attach(node):
            if isinstance(node, list):
                for child in node:
                    attach(child)
            elif isinstance(node, dict):
                if node.get('kind') == 'call' and node.get('symbol') == 'qb':
                    node['symbol'] = 'sh'
                    node['arguments'] += [{'kind': 'variable', 'name': name} for name in extra_names]
                else:
                    for child in node.values():
                        attach(child)
        attach(item['body']['body'])
        for name, sort in reversed(list(zip(extra_names, extra_types, strict=True))):
            item['body']['body'] = {'kind': 'forall', 'variable': name, 'sort': sort, 'body': item['body']['body']}
        doc['declarations'].append(item)
    old_args = statements[-1]['body']['arguments']
    if old_args[-2]['body']['symbol'] != 'qc' or old_args[-1]['body']['symbol'] != 'qf':
        raise ValueError('Unexpected source scoped descriptions')
    old_args[-2]['body']['symbol'], old_args[-1]['body']['symbol'] = 'qi', 'qj'
    doc['statements'] = statements
    parsed = parse(format_graph(doc, 'compact'))
    declarations = {d['name']: d for d in parsed['declarations']}
    records = (
        ('tf', ['event', 'frame', 'context', 'length_unit', 'time_unit', 'time', 'x', 'y', 'z'],
         '指定文脈の同じ出来事に、指定基準系と長さ・時間単位で実数の時空座標を割り当てる関係。有効な切断に対する実数版であり、座標の存在や同一性は別の条件で検査する。'),
        ('tg', ['object', 'event', 'context'], '指定文脈で、出来事が対象の世界線に属するという物理的な対応。座標の一致だけから別の対象の出来事へ取り替えない。'),
        ('tj', ['frame', 'context', 'length_unit', 'time_unit', 'light_speed'], '指定文脈・基準系・単位比における光速度の実数の読み。別の系でも同じ値になることを、この関係だけでは断定しない。'),
        ('tk', ['frame', 'context'], '指定文脈で基準系を慣性系として採用する物理的な条件。任意の加速座標系へ時計の式を無条件に適用しない。'))
    for name, labels, meaning in records:
        basis['primitives'].append({'symbol': name, 'parameters': declarations[name]['parameters'], 'result': 'truth',
                                    'arguments': labels, 'meaning_ja': meaning})
    previous = json.loads((ROOT / 'data/path-observations-basis-v1.json').read_text(encoding='utf-8'))
    record = deepcopy(next(r for r in previous['primitives'] if r['symbol'] == 'pe'))
    record.update(symbol='tl', source_convention='path-observations-basis-v1:pe')
    basis['primitives'].append(record)
    basis.update(version='worldlines-basis-v1', document='examples/v014/einstein-worldlines.noema')
    basis['definitions'].update({
        'sa': '有効な実切断で記述した四座標が、同じ出来事・基準系・文脈・単位の座標関係tfを満たす。',
        'sb': 'saの出来事が、同じ文脈で指定した対象の世界線に属する。',
        'sc': 'sbの時計について同じ時間単位での有効な実数の指示がある。',
        'sd': '同じ出来事・基準系・文脈・長さ単位・時間単位では、有効な四座標の割当てが一意である。',
        'se': '同じ対象の実時間区間の全時刻に曲線の出来事が存在し、逆にその区間の対象の観測は全て曲線に一致する。sdを含み、存在する一部の点だけで全経路を代用しない。',
        'sf': '異なる長さ・時間の基底軸と単位について、既存の次元定義dh、正の単位尺度、単位の次元・尺度の意味規約を一致させる。',
        'sg': 'seの時計の各出来事の指示が、同じ時間単位と与えた指示関数に対応する。進み率の積分法則は含まない。',
        'sh': 'qbに、両時計の全区間の世界線・指示、出発と帰着の特定出来事、慣性系、光速度の読み、長さと時間単位の次元と尺度を接続する。',
        'sk': '有理数の四座標と指示を実切断へ埋め込んだ、一つの時計の出来事の対応。有限検査では指定した有理数埋込みのみを比較する。',
        'sl': 'sfと慣性系の条件に、有理数から実切断へ埋め込んだ正の光速度の読みを結ぶ。',
        'sm': '有理数埋込みで指定した二つの四座標が同じ出来事に割り当てられた場合、それらが同じ値であることを要求する。sdの一対に対する検査例で、全域の代用ではない。',
        'sn': '同じ時計・出来事・基準系・時間単位では、有効な実数の指示が一意である。対象との対応は指定文脈で確認する。',
        'so': 'snについて、有理数埋込みの二つの指示の一対を検査する。読みの存在自体は別の条件である。',
        'qi': 'qcの観測前提qbをshへ拡張した仮定の内容。積分法則を世界線の定義から導いたことにはしない。',
        'qj': 'qfの観測前提qbをshへ拡張した、仮定範囲内の近似と残差の帰結。'})
    basis['unresolved'] += ['数学的な曲線と全区間の物理的な対応条件を今回追加した。継承した未解決欄は以前の草案の記録として保持する。',
        'tf/tg/tj/tkは観測・対象との対応・光速度・慣性系の意味規約であり、その物理的実現や理論全体への還元は未完。',
        '全実数時刻に対応する出来事の存在を述べる。有限個の出来事を持つ検査用モデルで連続経路全体を確認したとはしない。',
        '光速度の系間不変性、時計の機構と加速応答、先行の証明の全内容、地球上の比較と原文全文の意味確認は未完。']
    audit_basis(parsed, basis)
    return format_graph(parsed, 'compact') + '\n', basis


def main():
    text, basis = composed()
    for relative, body in {basis['document']: text, 'data/worldlines-basis-v1.json': json.dumps(basis, ensure_ascii=False, indent=2) + '\n'}.items():
        path = ROOT / relative
        if path.exists():
            if path.read_text(encoding='utf-8') != body:
                raise ValueError('Stored worldlines differ: ' + relative)
        else:
            with path.open('x', encoding='utf-8', newline='\n') as stream:
                stream.write(body)
    print('Whole-interval object, coordinate and unit bindings composed; finite samples are not full worldlines')


if __name__ == '__main__':
    main()
