"""Frame-bound energy questions with explicit volume, amplitude and unit premises."""
from copy import deepcopy
import json

from noema.extraction import extract_document, extract_basis
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, op, both
from scripts.compose_field_equations import CUT, REGION
from scripts.compose_wave_readings import MOTION, parameters
from scripts.compose_wave_amplitudes import params

PARENT = 'examples/v014/einstein-transported-contents.noema'
BOUND = 'h[a a ' + REGION + ' d] c'
NUMBERS = 'light speed ax ay az radius pi power newpower volume'.split()
INPUTS = [(n, 'a') for n in ('complex', 'oldframe', 'newframe', 'kind', 'unit')]
INPUTS += [('scale', 'b'), ('context', 'd'), ('assigned', BOUND), ('motion', MOTION)]
INPUTS += [(n, CUT) for n in NUMBERS]
REFERENCES = dict(zip(('complex', 'newframe', 'kind', 'unit', 'scale', 'assigned', 'motion', 'context', 'scope', 'node'),
                      ('zvaa', 'zvab', 'zvac', 'zvad', 'zvae', 'zvaf', 'zvag', 'zvah', 'zvai', 'zvaj')))
REFERENCES.update(dict(zip(NUMBERS, ('zvak', 'zval', 'zvam', 'zvan', 'zvao', 'zvap', 'zvaq', 'zvar', 'zvas', 'zvat'))))


def definitions():
    zero = k('bb', 'n p a b')
    mul = lambda x, y: k('shv', x, y)
    pi, power, volume, value = map(v, ('pi', 'power', 'volume', 'value'))
    converted = k('bj', v('scale'), value)
    text = definition('seha', params('pi power volume value', CUT) + ' scale b', both(
        k('sedi', pi), *[k('ba', x) for x in (power, volume, value)],
        k('bc', zero, power), k('bg', zero, volume), k('bc', zero, value), k('aa', 'n p a b', v('scale')),
        k('sca', mul(mul(k('bb', 'n p i b'), pi), converted), mul(power, volume))))
    V, speed, a, b, c, radius = map(v, ('light', 'speed', 'ax', 'ay', 'az', 'radius'))
    region = 'i[' + params('x y z time', CUT) + '][' + k('secc', V, a, b, c, radius, *map(v, ('x', 'y', 'z', 'time'))) + ']'
    newregion = k('s6m', V, speed, region)
    text += definition('sehb', parameters(INPUTS + [('value', CUT)]), both(
        k('cf', v('complex')), k('va', v('oldframe')), k('va', v('newframe')),
        op('u', op('e', v('oldframe'), v('newframe'))), k('s45', V, speed),
        app(v('motion'), v('oldframe'), v('newframe'), V, speed, v('context')),
        app(v('assigned'), v('complex'), v('oldframe'), region, v('context')),
        app(v('assigned'), v('complex'), v('newframe'), newregion, v('context')),
        k('zof', v('unit'), v('kind'), v('scale'), v('context')),
        k('seak', V, speed, a, power, v('newpower')),
        k('sedo', V, speed, a, b, c, radius, pi, volume),
        k('seha', pi, v('newpower'), volume, value, v('scale'))))
    text += definition('sehc', parameters(INPUTS),
        'j v[i[value ' + CUT + '][' + k('sehb', *(v(n) for n, _ in INPUTS), value) + ']]', 'g[' + CUT + ']')
    return text


MEANINGS = {
    'seha': '正の体積と単位尺度について、非負の二乗振幅powerと候補値valueが8*pi*(scale*value)=power*volumeを満たす。piは既存の積分による指定を使う。零振幅と零エネルギーを許し、比の分母を零にしない。',
    'sehb': '同じ光の対象に旧系の移動球の閉内部と新系での逆座標変換領域を割り当てる。二系の運動・量の種類と単位尺度・振幅変換・新系の同時断面の体積積分を固定し、その対象の新系でのエネルギー候補値をsehaで拘束する。記録や実測の存在を要求しない。',
    'sehc': 'sehbの対象・二系・文脈・単位・幾何と波の条件を固定し、実切断のエネルギー値を答えとする質問を作る。答えを計算して出力する手続きではなく、存在・一意性・既知性を断言しない。',
    'sehd': 'u0205で求める新系kにおけるエネルギー値の質問。静止系の球と同じ対象・変換領域を保持し、後続の振幅・体積の式を候補条件へ接続した明示的な解釈。',
}


def source_composed():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    basis = deepcopy(json.loads((ROOT / 'data/einstein-transported-contents-basis-v1.json').read_text(encoding='utf-8')))
    statements, doc['statements'] = doc['statements'], []
    text = format_graph(doc, 'compact') + definitions()
    sorts = dict(INPUTS) | {'scope': 'a', 'node': 'a'}
    for role, symbol in REFERENCES.items():
        text += 'r ' + symbol + '[] ' + sorts[role] + '.'
    args = [k('ra' if role == 'oldframe' else REFERENCES[role]) for role, _ in INPUTS]
    text += definition('sehd', '', k('sehc', *args), 'g[' + CUT + ']')
    doc = parse(text); doc['statements'] = statements
    doc = parse(format_graph(doc, 'compact') + 's[' + k('zih', k(REFERENCES['node']), k('rd'), 'r[k sehd[]]',
        k(REFERENCES['scope']), k('ri')) + '].')
    basis.update(version='einstein-energy-questions-basis-v1', document='examples/v014/einstein-energy-questions.noema')
    basis['definitions'].update(MEANINGS)
    labels = {
        'complex': '移動球面に囲まれる同じ光の集合への局所参照。光子の個数や同一性を指定しない。',
        'newframe': 'u0205のkという基準系への局所参照。旧系とは別の座標系として考察する。',
        'kind': 'この計算でenergy=power*volume/(8*pi)として指定するエネルギー量の種類への局所参照。一般的な仕事・力との物理法則への接続は未完。',
        'unit': 'エネルギー候補値の単位への局所参照。原文にない特定の単位名を補わない。',
        'scale': 'この単位から8*piの式を採用した基準尺度への正の有理倍率。',
        'assigned': '同じ光の集合・基準系・領域・文脈の対応を与える関数への局所参照。対象の実在や物理的同一性は数値から導かず、明示したモデルの入力として残す。',
        'motion': '二系の標準配置・光速度・符号付き相対速度・文脈を対応させる関数への局所参照。',
        'context': '光の集合と二系を考察する物理的設定への局所参照。著者の発話文脈riとは区別する。',
        'scope': 'u0205の光エネルギーを求める考察範囲への局所参照。',
        'node': 'u0205で新系kに相対的なエネルギーを問う文章箇所への局所参照。',
    }
    for role in NUMBERS:
        labels[role] = 'この光の集合の計算に用いる' + {
            'light': '光速度V', 'speed': '符号付き系間速度v', 'ax': '光の単位方向のx成分a',
            'ay': '光の単位方向のy成分b', 'az': '光の単位方向のz成分c', 'radius': '旧系の移動球の半径R',
            'pi': '既存積分定義で指定するpi', 'power': '旧系の二乗振幅A²',
            'newpower': '新系の二乗振幅A′²', 'volume': '新系の時刻零における領域の体積S′'}[role] + 'への局所参照。候補条件で先行定義に接続する。'
    declarations = {d['name']: d for d in doc['declarations']}
    for role, symbol in REFERENCES.items():
        d = declarations[symbol]
        basis['primitives'].append(dict(symbol=symbol, parameters=d['parameters'], result=d['result'], arguments=[], meaning_ja=labels[role]))
    basis['unresolved'] += [
        'u0205のエネルギーの問いを、同じ対象・新系・単位を保持した実数値の質問に接続する。実測記録の存在や答えを知っていることを追加しない。',
        '候補条件には後続の振幅・体積・エネルギーの式を用いる。質問の提示そのものが、その式の証明や解の存在を意味するとはしない。',
        'assignedとmotionは明示したモデルの入力。光の集合と領域の物理的な帰属、力・仕事によるエネルギーの一般的説明、単位の実現は未完。',
        '8*piの規約を採用した一様なエネルギー密度のモデルである。波の瞬間的な電磁場からの導出や時間平均の定義はここでは完了していない。',
        '「同じ光の集合を包む」とする著者の帰結提示、言い換えを示すd.h.の談話関係は未完。全文の意味一致を認定しない。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def core_composed():
    text, basis = source_composed(); doc = parse(text)
    selected = extract_document(doc, roots=['seha', 'sehc', 'sehd'], statement_indices=[len(doc['statements'])-1])
    projected = extract_basis(doc, basis, selected, version='energy-questions-core-basis-v1',
        document_path='examples/v014/energy-questions-core.noema')
    return format_graph(selected.document, 'compact') + '\n', projected


BUILDERS = ((source_composed, 'einstein-energy-questions'), (core_composed, 'energy-questions-core'))


def main():
    for builder, stem in BUILDERS:
        text, basis = builder()
        for name, body in ((basis['document'], text), ('data/'+stem+'-basis-v1.json', json.dumps(basis, ensure_ascii=False, indent=2)+'\n')):
            path = ROOT / name
            if path.exists():
                if path.read_text(encoding='utf-8') != body:
                    raise ValueError('Stored energy question differs: '+name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream:
                    stream.write(body)
        print(stem, len(text), 'characters')


if __name__ == '__main__':
    main()
