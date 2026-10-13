"""Light-speed moving balls, simultaneous slices and conditional energy ratios."""
from copy import deepcopy
import json

from noema.extraction import extract_document, extract_basis
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, op, both
from scripts.compose_field_equations import CUT, REGION
from scripts.compose_wave_amplitudes import params, generic_composed as amplitude_generic

PARENT = 'examples/v014/einstein-wave-approximation.noema'
ZERO, ONE = 'n p a b', 'n p b b'
GEOMETRY = 'light ax ay az radius x y z time'
SLICE = 'light speed ax ay az radius x y z'
ENERGY = 'light speed ax power newpower volume newvolume conversion energy newenergy'


def rational_definitions():
    mul = lambda a, b: k('ad', a, b)
    sub = lambda a, b: k('ab', a, k('ac', b))
    sq = lambda a: mul(a, a)
    V, a, b, c, x, y, z, t = map(v, ('light', 'ax', 'ay', 'az', 'x', 'y', 'z', 'time'))
    beta, ratio = map(v, ('beta', 'ratio'))
    text = definition('sebd', params('light ax ay az x y z time', 'b'), k('seaa',
        *[sub(pos, mul(mul(V, direction), t)) for pos, direction in ((x, a), (y, b), (z, c))]), 'b')
    factor = k('sebf', beta, ratio, a)
    text += definition('sebe', params('beta ratio ax ay az x y z', 'b'), k('seaa',
        mul(factor, x), sub(y, mul(mul(mul(b, beta), ratio), x)),
        sub(z, mul(mul(mul(c, beta), ratio), x))), 'b')
    # Definitions may refer only to earlier declarations.
    factor_definition = definition('sebf', params('beta ratio ax', 'b'), mul(beta, sub(ONE, mul(a, ratio))), 'b')
    text = factor_definition + text
    volume, newvolume = map(v, ('volume', 'newvolume'))
    text += definition('sebg', params('beta ratio ax volume newvolume', 'b'), both(
        k('aa', sq(ratio), ONE), k('aa', ZERO, beta), op('e', mul(sq(beta), sub(ONE, sq(ratio))), ONE),
        op('u', k('aa', ONE, sq(a))), k('aa', ZERO, volume), k('aa', ZERO, newvolume),
        op('e', mul(factor, newvolume), volume)))
    D, p, newp, conversion, E, newE = map(v, ('factor', 'power', 'newpower', 'conversion', 'energy', 'newenergy'))
    text += definition('sebh', params('factor power newpower volume newvolume conversion energy newenergy', 'b'), both(
        *[k('aa', ZERO, value) for value in (D, p, newp, volume, newvolume, conversion, E, newE)],
        op('e', newp, mul(p, sq(D))), op('e', mul(D, newvolume), volume),
        op('e', mul(conversion, E), mul(p, volume)), op('e', mul(conversion, newE), mul(newp, newvolume))))
    return text


RATIONAL_MEANINGS = {
    'sebd': '光速度Vと方向三成分に沿って移る中心からの、有理数の位置の二乗距離。半径や単位方向の条件は呼出側で要求する。',
    'sebe': '新座標時刻零の断面における二乗距離。β(1−a r)x、y−bβr x、z−cβr xの二乗和。rは符号付き速度比。',
    'sebf': 'β(1−a r)という符号を保持した係数。波の周波数・振幅の係数および断面の線形写像の行列式に使う。',
    'sebg': '許容速度比と正のβ、方向余弦、正の二体積について、β(1−a r)S′=Sを要求する。一般の体積測度から導く定義ではない。',
    'sebh': '正の係数・二乗振幅・体積・エネルギー・共通換算係数について、二乗振幅が係数の二乗倍、体積が逆数倍、換算係数とエネルギーの積が二乗振幅と体積の積である。エネルギー比の結論を前提へ含めない。',
}


def generic_composed():
    text, basis = amplitude_generic()
    doc = parse(text + rational_definitions())
    basis = deepcopy(basis)
    basis.update(version='light-complex-basis-v1', document='examples/v014/light-complex.noema')
    basis['definitions'].update(RATIONAL_MEANINGS)
    basis['unresolved'] += ['体積とエネルギーの法則は明示した条件である。測度・空間積分・物理的エネルギー・換算係数8πの構成は未完。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def definitions():
    text = rational_definitions()
    zero, one = k('bb', ZERO), k('bb', ONE)
    mul = lambda a, b: k('shv', a, b)
    sq = lambda a: mul(a, a)
    V, a, b, c, R, x, y, z, t = map(v, GEOMETRY.split())
    s = v('speed')
    text += definition('seca', params('light ax ay az x y z time', CUT), k('seag',
        *[k('bf', pos, mul(mul(V, direction), t)) for pos, direction in ((x, a), (y, b), (z, c))]), CUT)
    guards = both(*[k('ba', v(n)) for n in GEOMETRY.split()], k('bg', zero, V), k('bg', zero, R),
        k('sca', k('seag', a, b, c), one))
    distance = k('seca', V, a, b, c, x, y, z, t)
    for name, comparison in (('secb', 'sca'), ('secc', 'bc')):
        text += definition(name, params(GEOMETRY, CUT), both(guards, k(comparison, distance, sq(R))))
    coords = list(map(v, ('x', 'y', 'z', 'time')))
    boundary = 'i[' + params('x y z time', CUT) + '][' + k('secb', V, a, b, c, R, *coords) + ']'
    text += definition('secd', params('light speed ax ay az radius', CUT), k('s6m', V, s, boundary), REGION)
    text += definition('sece', params(SLICE, CUT), both(k('s45', V, s),
        app(k('secd', V, s, a, b, c, R), x, y, z, zero)))
    beta = k('soy', V, s)
    ratio = mul(s, k('sjd', V))
    D = k('sdn2', V, s, one, a)
    text += definition('secf', params('light speed ax ay az x y z', CUT), k('seag',
        mul(D, x), k('bf', y, mul(mul(mul(b, beta), ratio), x)),
        k('bf', z, mul(mul(mul(c, beta), ratio), x))), CUT)
    text += definition('secg', params(SLICE, CUT), both(
        *[k('ba', v(n)) for n in SLICE.split()], k('s45', V, s), k('bg', zero, R),
        k('sca', k('seag', a, b, c), one), k('sca', k('secf', V, s, a, b, c, x, y, z), sq(R))))
    volume, newvolume = map(v, ('volume', 'newvolume'))
    ratio_guards = both(k('s45', V, s), k('ba', a), k('bc', sq(a), one))
    text += definition('sech', params('light speed ax volume newvolume', CUT), both(ratio_guards,
        k('ba', volume), k('ba', newvolume), k('bg', zero, volume), k('bg', zero, newvolume),
        k('sca', mul(D, newvolume), volume)))
    p, newp, conversion, E, newE = map(v, ('power', 'newpower', 'conversion', 'energy', 'newenergy'))
    text += definition('seci', params(ENERGY, CUT), both(k('seak', V, s, a, p, newp),
        k('sech', V, s, a, volume, newvolume),
        *[both(k('ba', value), k('bg', zero, value)) for value in (p, newp, conversion, E, newE)],
        k('sca', mul(conversion, E), mul(p, volume)), k('sca', mul(conversion, newE), mul(newp, newvolume))))
    text += definition('secj', params('light speed ax energy newenergy', CUT), both(ratio_guards,
        *[both(k('ba', value), k('bg', zero, value)) for value in (E, newE)], k('sca', newE, mul(D, E))))
    rate, newrate = map(v, ('rate', 'newrate'))
    text += definition('seck', params('light speed ax energy newenergy rate newrate', CUT), both(
        k('secj', V, s, a, E, newE), *[both(k('ba', value), k('bg', zero, value)) for value in (rate, newrate)],
        k('sca', newrate, k('sdn2', V, s, rate, a))))
    text += definition('secl', params('light speed energy newenergy', CUT), both(k('secj', V, s, one, E, newE),
        k('sca', newE, k('sdr2', V, s, E))))
    return text


MEANINGS = {
    'seca': '実切断の光速度と単位方向に沿って移る中心からの二乗距離を構成する。',
    'secb': '有効な実切断、正の光速度・半径、単位方向を要求し、光速度で移る球の表面を四座標で指定する。光やエネルギーの所属は含めない。',
    'secc': 'secbと同じ移動球の閉じた内部。境界を含み、表面だけの条件と区別する。',
    'secd': '同じ移動球面を、既存の逆ローレンツ座標変換によって新しい四座標の領域として構成する。許容速度は利用側で要求する。',
    'sece': '許容速度でsecdの新座標時刻を零へ固定した同時断面。旧座標時刻を零へ固定する操作とは区別する。',
    'secf': '新座標時刻零での二乗距離を、β(1−av/V)x、y−bβ(v/V)x、z−cβ(v/V)xの二乗和として構成する。',
    'secg': '有効な実切断・単位方向・正の半径・許容速度のもとで、secfが半径の二乗に等しい楕円体表面。seceとの対応は別途検査する。',
    'sech': '正の体積S,S′について、周波数係数D=β(1−av/V)とS′の積がSに等しい。測度を構成した証明ではなく体積比の明示的な条件。',
    'seci': '同じV,v,aで、既存の二乗振幅変換seak、体積比sech、正の共通換算係数CによるCE=A²SとCE′=A′²S′を要求する。E′=DEを条件に含めない。',
    'secj': '同じ許容速度と方向余弦に対し、二つの正のエネルギー値がE′=β(1−av/V)Eを満たす。比の分母が零となる零エネルギーは対象外。',
    'seck': '同じ速度・方向余弦を用い、正のエネルギーと周波数が同じD倍になる。観測者・光の集合の同一性の説明は別途必要。',
    'secl': '前向き平行方向a=1での正のエネルギー比を、既存の正の平方根の表現へ結ぶ。負の枝を許さない。',
}


def source_composed():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    basis = deepcopy(json.loads((ROOT / 'data/einstein-wave-approximation-basis-v1.json').read_text(encoding='utf-8')))
    statements, doc['statements'] = doc['statements'], []
    doc = parse(format_graph(doc, 'compact') + definitions())
    doc['statements'] = statements
    basis.update(version='einstein-light-complex-basis-v1', document='examples/v014/einstein-light-complex.noema')
    basis['definitions'].update(RATIONAL_MEANINGS)
    basis['definitions'].update(MEANINGS)
    basis['unresolved'] += [
        '原刊913–914頁の球面・楕円体断面・体積比・エネルギー比の式へ部分接続する。図形だけから、境界をエネルギーが横切らないことや同じ光の集合を包むことは導かない。',
        '球と楕円体の体積測度、線形変換下の体積則、空間積分、光エネルギーと二乗振幅の物理法則および換算係数8πの構成は未完。Cは正の共通係数として残し、8πを定義済みとはしない。',
        '正のエネルギーについて比を扱う。零振幅自体は既存seakで許されるが、0/0のエネルギー比は認定しない。エネルギー比と周波数比の一致は、同じ速度・方向を共有する値の条件である。',
        '観測者・単位・基準系・同じ光の集合への物理的帰属、相対性原理の適用と著者の推論の談話は未完。既存173件の著者主張を保持し、未記述の主張を追加しない。',
        '有理数の代数的検証と登録した有理数切断の具体例を、実数全域の演算法則・体積法則の証明や原文の全文意味一致と同一視しない。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def core_composed():
    text, basis = source_composed()
    doc = parse(text)
    selected = extract_document(doc, roots=['sece', 'secg', 'secc', 'seci', 'seck', 'secl'], statement_indices=[])
    projected = extract_basis(doc, basis, selected, version='light-complex-core-basis-v1', document_path='examples/v014/light-complex-core.noema')
    return format_graph(selected.document, 'compact') + '\n', projected


BUILDERS = ((generic_composed, 'light-complex'), (source_composed, 'einstein-light-complex'), (core_composed, 'light-complex-core'))


def main():
    for builder, stem in BUILDERS:
        text, basis = builder()
        for name, body in ((basis['document'], text), ('data/' + stem + '-basis-v1.json', json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            path = ROOT / name
            if path.exists():
                if path.read_text(encoding='utf-8') != body:
                    raise ValueError('Stored light complex differs: ' + name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream:
                    stream.write(body)
        print(stem, len(text), 'characters')


if __name__ == '__main__':
    main()
