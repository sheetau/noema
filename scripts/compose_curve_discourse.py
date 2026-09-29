"""Attribute a curve-clock extension as an assumption, not an established law."""
from copy import deepcopy
import json

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from scripts.compose_limits import ROOT, R, F, ZERO, v, call, app, op, both, quant, lam
from scripts.compose_kant_discourse import discourse_basis

KIN = [('lower', R), ('upper', R), ('rate', F), ('light', R)] + [(name, F) for name in ('x', 'y', 'z', 'vx', 'vy', 'vz')]
OBS = KIN + [(name, 'a') for name in ('clock', 'reference', 'first', 'last', 'place', 'frame', 'unit')] + [('reading', R)]
ALIASES = {'ma': 'ta', 'me': 'tb', 'mc': 'tc', 'mb': 'td', 'mi': 'te'}


def conditional_basis():
    desc = {'kind': 'description', 'result': 'content'}
    records = []
    for symbol, meaning in (
        ('ug', '著者が指定の文章箇所で内容の記述を仮定として採用し、指定した推論範囲へ置く。内容の真理、信念、証明を含意しない。'),
        ('uh', '著者が指定の文章箇所で内容の記述を、指定した仮定の範囲内の主張として提示する。文書全体の無条件の断言へ昇格させない。')):
        records.append({'symbol': symbol, 'parameters': ['individual', 'individual', desc, 'individual', 'situation'],
                        'result': 'truth', 'arguments': ['node', 'author', 'content_description', 'scope', 'context'], 'meaning_ja': meaning})
    records.append({'symbol': 'ui', 'parameters': ['individual', 'individual', 'situation'], 'result': 'truth',
                    'arguments': ['author', 'node', 'context'],
                    'meaning_ja': '著者が指定箇所の内容を既に証明されたものとして扱う。著者による証明済みという位置付けであり、検査器が証明を確認したという関係ではない。'})
    return {'primitives': records, 'definitions': {
        'vd': '同じ著者・文脈・推論範囲の仮定と条件付き主張を別箇所へ結ぶ。著者が前者から後者を帰結として提示することと本文順序を要求する。内容の評価や論理的な妥当性判定は行わない。'},
        'unresolved': ['仮定採用・範囲内主張・証明済みの位置付けを現実の発話から同定する一般的方法と、基礎語への還元は未完。']}


def generic_composed():
    text = 'n:\n'
    for name in ('expository-discourse', 'conditional-discourse'):
        text += (ROOT / ('examples/fragments/' + name + '.noema.inc')).read_text(encoding='utf-8')
    doc = parse(text)
    basis = deepcopy(discourse_basis())
    extra = conditional_basis()
    basis.update(version='conditional-discourse-basis-v1', document='examples/v014/conditional-discourse.noema')
    basis['primitives'] += extra['primitives']
    basis['definitions'].update(extra['definitions'])
    basis['unresolved'] += extra['unresolved']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def definitions():
    def define(name, params, result, body):
        return 'd ' + name + '[' + ' '.join(n + ' ' + t for n, t in params) + '] ' + result + '[' + body + '].\n'
    def universal(params, body):
        for name, sort in reversed(params):
            body = quant('f', name, sort, body)
        return body
    zero, one = call('bb', ZERO), call('bb', 'n p b b')
    domain = lam('t', R, call('lg', v('lower'), v('upper'), v('t')))
    rate = app(v('rate'), v('t'))
    square = lambda x: call('cd', x, x)
    light2 = square(v('light'))
    speed2 = call('bd', square(app(v('vx'), v('t'))), call('bd', square(app(v('vy'), v('t'))), square(app(v('vz'), v('t')))))
    kinematic = both(call('ba', v('lower')), call('ba', v('upper')), call('bg', v('lower'), v('upper')),
        call('ba', v('light')), call('bg', zero, v('light')),
        call('lh', v('lower'), v('upper'), v('x'), v('y'), v('z')), call('lf', domain, v('rate')),
        quant('f', 't', R, op('y', app(domain, v('t')), both(
            call('bg', zero, rate), call('bc', rate, one),
            *[call('li', domain, v(axis), v('t'), app(v('v' + axis), v('t'))) for axis in ('x', 'y', 'z')],
            call('bg', speed2, light2), op('e', call('cd', light2, square(rate)), call('bf', light2, speed2))))))
    text = define('qa', KIN, 'c', kinematic)
    observations = both(call('qa', *(v(n) for n, _ in KIN)), call('ba', v('reading')),
        call('ta', v('clock')), call('ta', v('reference')), op('u', op('e', v('clock'), v('reference'))),
        op('u', op('e', v('first'), v('last'))), call('tc', v('reference'), v('frame')), call('te', v('unit')),
        *[call('td', v(obj), v('place'), v('frame')) for obj in ('reference', 'first', 'last')],
        call('tb', v('clock'), v('first'), v('frame'), v('unit'), v('lower')),
        call('tb', v('reference'), v('first'), v('frame'), v('unit'), v('lower')),
        call('tb', v('reference'), v('last'), v('frame'), v('unit'), v('upper')),
        call('tb', v('clock'), v('last'), v('frame'), v('unit'), v('reading')))
    text += define('qb', OBS, 'c', observations)
    # qb fixes endpoint observations and kinematics but deliberately does not
    # prescribe an elapsed reading. qc is the separately attributed adoption.
    premise = universal(OBS, op('y', call('qb', *(v(n) for n, _ in OBS)),
        call('ne', v('lower'), v('upper'), v('rate'), call('bf', v('reading'), v('lower')))))
    text += define('qc', [], 'e', 'b scene[' + premise + ']')
    constant = both(call('ba', v('speed')), call('ba', v('factor')), call('ca', v('speed')),
        call('bg', v('speed'), v('light')), call('bg', zero, v('factor')),
        op('e', call('cd', light2, square(v('factor'))), call('bf', light2, square(v('speed')))),
        quant('f', 't', R, op('y', app(domain, v('t')), op('e', speed2, square(v('speed'))))))
    conclusion = universal(OBS + [('speed', R), ('factor', R)], op('y', both(call('qb', *(v(n) for n, _ in OBS)), constant),
        op('e', call('bf', v('upper'), v('reading')),
           call('cd', call('bf', v('upper'), v('lower')), call('bf', one, v('factor'))))))
    text += define('qd', [], 'e', 'b scene[' + conclusion + ']')
    return text


def composed():
    text = (ROOT / 'examples/v014/integrals.noema').read_text(encoding='utf-8')
    basis = deepcopy(json.loads((ROOT / 'data/integrals-basis-v1.json').read_text(encoding='utf-8')))
    old_doc = parse((ROOT / 'examples/v014/einstein-path-observations.noema').read_text(encoding='utf-8'))
    old_basis = json.loads((ROOT / 'data/path-observations-basis-v1.json').read_text(encoding='utf-8'))
    doc = parse(text)
    for declaration in old_doc['declarations']:
        if declaration['kind'] == 'primitive' and declaration['name'] in ALIASES:
            item = deepcopy(declaration)
            item['name'] = ALIASES[item['name']]
            doc['declarations'].append(item)
    for record in old_basis['primitives']:
        if record['symbol'] in ALIASES:
            item = deepcopy(record)
            item['source_symbol'] = item['symbol']
            item['symbol'] = ALIASES[item['symbol']]
            basis['primitives'].append(item)
    text = format_graph(doc, 'compact') + '\n' + definitions()
    for name in ('expository-discourse', 'conditional-discourse'):
        text += (ROOT / ('examples/fragments/' + name + '.noema.inc')).read_text(encoding='utf-8')
    for name in ('wa', 'wb', 'wc', 'wd', 'we'):
        text += 'r ' + name + '[] a.\n'
    text += ('r wf[] d.\n'
             's[k ui[k wa[] k wb[] k wf[]]].\n'
             's[k ue[k wb[] k wc[] k wf[]]].\n'
             's[k vd[k wa[] k wf[] k we[] k wc[] k wd[] r[k qc[]] r[k qd[]]]].\n')
    doc = parse(text)
    generic = generic_composed()[1]
    basis.update(version='curve-discourse-basis-v1', document='examples/v014/einstein-curve-discourse.noema')
    basis['primitives'] += generic['primitives']
    basis['definitions'].update(generic['definitions'])
    basis['definitions'].update({
        'qa': '連続な進み率、微分可能な閉曲線、光速と速度成分の関係を指定する。時計の経過が積分と一致する条件は含まない。',
        'qb': 'qaと同じ場所の二時計の出発・帰着の指示を併記する。静止時計を共通の時刻尺度として、出発時の指示一致を要求する。移動時計の帰着指示は積分値へ固定しない。曲線と実際の世界線の全時刻の観測接続は未完。',
        'qc': 'qbに当てはまる各ケースで、移動時計の指示差が進み率の積分に等しい、という拡張を採用する内容。qbの定義にこの法則を埋め込まない。',
        'qd': 'qbと一定の速度の大きさ、正の進み率の係数について、帰還後の指示差が区間時間*(1-係数)に等しいという厳密なモデル帰結。原文M0241の二次近似そのものではない。'})
    for name, label in zip(('wa', 'wb', 'wc', 'wd', 'we'), ('著者', '先行する折れ線の結果の箇所', '曲線への拡張を仮定する箇所', '帰還時計の帰結の箇所', '仮定の推論範囲'), strict=True):
        basis['primitives'].append({'symbol': name, 'parameters': [], 'result': 'individual', 'arguments': [],
                                    'meaning_ja': 'この文書の' + label + 'を指す局所参照。参照そのものを内容の翻訳と数えない。'})
    basis['primitives'].append({'symbol': 'wf', 'parameters': [], 'result': 'situation', 'arguments': [], 'meaning_ja': 'この段落を提示する文脈。'})
    basis['unresolved'] += generic['unresolved'] + [
        '先行する折れ線の証明内容はwbから本文へ完全には接続していない。uiは原文での証明済みという位置付けだけを表す。',
        'qcはモデルに対する拡張の草案である。曲線と実時計の世界線の結合、長さ単位、光速度の観測、全時刻の物理的意味は未完。',
        'qdはモデルの厳密式で、原文M0241の近似式と高次項の扱いをまだ結んでいない。原文全文と同義とは判定しない。',
        '地球上の時計の比較と、全前提から帰結を導く実切断の積分定理の機械的証明は未完。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def main():
    for compose, filename in ((generic_composed, 'data/conditional-discourse-basis-v1.json'),
                              (composed, 'data/curve-discourse-basis-v1.json')):
        text, basis = compose()
        for name, body in {basis['document']: text, filename: json.dumps(basis, ensure_ascii=False, indent=2) + '\n'}.items():
            path = ROOT / name
            if path.exists():
                if path.read_text(encoding='utf-8') != body:
                    raise ValueError('Stored conditional discourse differs: ' + name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream:
                    stream.write(body)
    print('Scoped source assumptions composed; neither attribution nor a model is a physical proof')


if __name__ == '__main__':
    main()
