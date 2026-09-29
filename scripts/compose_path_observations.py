"""Connect finite interval conditions to shared events and clock readings."""
from copy import deepcopy
import json
from pathlib import Path

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis

ROOT = Path(__file__).resolve().parents[1]


def v(name):
    return 'v ' + name


def call(name, *args):
    return 'k ' + name + '[' + ' '.join(args) + ']'


def apply(name, arg):
    return 'c[' + v(name) + '][' + arg + ']'


def eq(left, right):
    return 'e[' + left + '][' + right + ']'


def both(clauses):
    body = clauses[-1]
    for clause in reversed(clauses[:-1]):
        body = 'w[' + clause + '][' + body + ']'
    return body


def difference(left, right):
    return call('ab', left, call('ac', right))


COMMON = [('clock', 'a'), ('frame', 'a'), ('scene', 'd'), ('lengthunit', 'a'),
          ('timeunit', 'a'), ('dialunit', 'a'), ('light', 'b'), ('scale', 'b')]
PATH = ([('segments', 'j[a]'), ('start', 'h[a] a'), ('end', 'h[a] a')]
        + COMMON + [('first', 'a'), ('last', 'a')]
        + [(name, 'h[a] b') for name in ('time', 'x', 'y', 'z', 'reading', 'speed', 'vx', 'vy', 'vz', 'rate')]
        + [(name, 'b') for name in ('total', 'elapsed', 'lost')])


def definition(name, params, clauses):
    return 'd ' + name + '[' + ' '.join(n + ' ' + t for n, t in params) + '] c[' + both(clauses) + '].\n'


def definitions():
    # Endpoint displacement and the ideal interval reading law are explicit
    # premises. Endpoint observations alone do not establish uniform motion.
    params = COMMON + [('first', 'a'), ('last', 'a')]
    params += [(name, 'b') for name in ('firstt', 'lastt', 'firstx', 'firsty', 'firstz',
                                      'lastx', 'lasty', 'lastz', 'firstreading', 'lastreading',
                                      'speed', 'vx', 'vy', 'vz', 'rate')]
    dt = difference(v('lastt'), v('firstt'))
    clauses = ['u[' + eq(v('first'), v('last')) + ']', call('ma', v('clock')),
               call('mi', v('timeunit')), call('mi', v('dialunit')),
               call('aa', 'n p a b', v('scale')), call('aa', v('firstt'), v('lastt')),
               call('pc', v('frame'), v('scene'), v('lengthunit'), v('timeunit'), v('light')),
               call('ha', v('speed'), v('light'), v('rate')),
               'u[' + call('aa', v('speed'), 'n p a b') + ']']
    norm = call('ab', call('ad', v('vx'), v('vx')),
                call('ab', call('ad', v('vy'), v('vy')), call('ad', v('vz'), v('vz'))))
    clauses.append(eq(call('ad', v('speed'), v('speed')), norm))
    for point in ('first', 'last'):
        clauses += [call('pa', v(point), v('frame'), v('scene'), v('lengthunit'), v('timeunit'),
                         v(point + 't'), *(v(point + axis) for axis in ('x', 'y', 'z'))),
                    call('me', v('clock'), v(point), v('frame'), v('dialunit'), call('bb', v(point + 'reading')))]
    for axis in ('x', 'y', 'z'):
        clauses.append(eq(difference(v('last' + axis), v('first' + axis)), call('ad', dt, v('v' + axis))))
    clauses.append(eq(difference(v('lastreading'), v('firstreading')),
                      call('ad', v('scale'), call('ad', dt, v('rate')))))
    text = definition('ja', params, clauses)
    endpoints = {p: apply(p, v('segment')) for p in ('start', 'end')}
    duration = 'i[segment a][' + difference(apply('time', endpoints['end']), apply('time', endpoints['start'])) + ']'
    interval_args = [v(n) for n, _ in COMMON] + [endpoints['start'], endpoints['end']]
    interval_args += [apply('time', endpoints[p]) for p in ('start', 'end')]
    interval_args += [apply(axis, endpoints[p]) for p in ('start', 'end') for axis in ('x', 'y', 'z')]
    interval_args += [apply('reading', endpoints[p]) for p in ('start', 'end')]
    interval_args += [apply(n, v('segment')) for n in ('speed', 'vx', 'vy', 'vz', 'rate')]
    text += definition('jb', PATH, [
        call('if', v('segments'), v('start'), v('end'), v('first'), v('last')),
        call('ia', v('segments'), 'i[segment a][' + call('ja', *interval_args) + ']'),
        call('ie', v('segments'), duration, v('speed'), v('light'), v('rate'), v('total'), v('elapsed'), v('lost'))])
    text += definition('jc', PATH, [call('jb', *(v(n) for n, _ in PATH)),
                                    *[eq(apply(axis, v('first')), apply(axis, v('last'))) for axis in ('x', 'y', 'z')]])
    comparison = PATH + [('reference', 'a'), ('place', 'a'), ('offset', 'b'),
                         ('referencefirst', 'b'), ('referencelast', 'b'), ('gap', 'b')]
    text += definition('jd', comparison, [
        call('jc', *(v(n) for n, _ in PATH)), 'u[' + eq(v('clock'), v('reference')) + ']',
        call('ma', v('reference')), call('mc', v('reference'), v('frame')),
        call('mb', v('reference'), v('place'), v('frame')),
        *[call('mb', v(event), v('place'), v('frame')) for event in ('first', 'last')],
        *[call('me', v('reference'), v(event), v('frame'), v('dialunit'), call('bb', v('reference' + event)))
          for event in ('first', 'last')],
        *[call('hk', v('scale'), v('offset'), apply('time', v(event)), v('reference' + event))
          for event in ('first', 'last')],
        eq(apply('reading', v('first')), v('referencefirst')),
        eq(v('gap'), difference(v('referencelast'), apply('reading', v('last'))))])
    return text


def composed():
    original = (ROOT / 'examples/v014/einstein-finite-paths.noema').read_text(encoding='utf-8')
    doc = parse(original + definitions())
    basis = deepcopy(json.loads((ROOT / 'data/finite-paths-basis-v1.json').read_text(encoding='utf-8')))
    basis['version'] = 'path-observations-basis-v1'
    basis['document'] = 'examples/v014/einstein-path-observations.noema'
    basis['definitions'].update({
        'ja': '同じ時計・基準系・文脈・単位で二出来事の座標と指示を結ぶ。正の時間差、速度ベクトルと変位、速度の大きさと進み率、正の共通指示尺度による区間指示差を条件として課す。端点観測から途中の等速性や加速点の時計応答を導くものではない。',
        'jb': '有限列の境目で同じ出来事を共有し、同じ出来事には同じ時刻・位置・指示の関数値を用いる。全区間のjaと、ieの経過合計を結ぶ。全継続時間や指示差の望ましい結論を追加条件として先取りしない。',
        'jc': 'jbを満たし、出発と帰着の三位置座標が等しい。場所への帰還を出来事の同一性と混同しない。',
        'jd': 'jcの帰還時に同じ場所の別の静止時計と比較する。出発時の指示一致、基準時計の共通尺度・原点による二指示、帰還時の指示差を指定する。途中の全時刻での静止や理想的な指示は基本関係・校正条件の解釈として与える。'})
    basis['unresolved'].append(
        '今回は共通の有理数座標と指示、同一出来事での接続を追加した。区間の指示法則は明示した前提であり、'
        '端点座標のみから等速運動を証明しない。時計の物理的な機構、慣性系、加速点での応答、'
        '実数一般・曲線の極限・地球上の比較は未完。読みの切断を検査する具体例は有限個の有理数埋込みだけを対象とする。')
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def main():
    text, basis = composed()
    for relative, body in {basis['document']: text,
                           'data/path-observations-basis-v1.json': json.dumps(basis, ensure_ascii=False, indent=2) + '\n'}.items():
        path = ROOT / relative
        if path.exists():
            if path.read_text(encoding='utf-8') != body:
                raise ValueError('Stored observation document differs: ' + relative)
        else:
            with path.open('x', encoding='utf-8', newline='\n') as stream:
                stream.write(body)
    print('Shared clock, events and units connected; interval law remains an explicit premise')


if __name__ == '__main__':
    main()
