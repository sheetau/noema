"""Persistent membership and explicit parallel transport, without a photon ontology."""
from copy import deepcopy
import json

from noema.extraction import extract_document, extract_basis
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, op, both, quant
from scripts.compose_field_equations import CUT, POINT, ROLES
from scripts.compose_field_transform import point_expression
from scripts.compose_wave_amplitudes import params
from scripts.compose_light_complex import generic_composed as ball_generic

PARENT = 'examples/v014/einstein-partition-bounds.noema'
ZERO, ONE = 'n p a b', 'n p b b'
GEOMETRY = 'light ax ay az radius ox oy oz'
FAMILY = 'labels h[a] c origins h[a] ' + POINT


def shared_definitions():
    scope, members, period, start, end, item, time = map(v, 'scope members period start end item time'.split())
    text = definition('sefa', 'scope h[a] c members h[a a] c start a end a',
        quant('f', 'item', 'a', op('y', app(scope, item), op('z', app(members, item, start), app(members, item, end)))))
    text += definition('sefb', 'scope h[a] c members h[a a] c period h[a] c start a', both(
        app(period, start), quant('f', 'time', 'a', op('y', app(period, time), k('sefa', scope, members, start, time)))))
    return text


def rational_definitions():
    mul = lambda x, y: k('ad', x, y)
    text = definition('sefc', params('light direction offset time', 'b'),
        k('ab', v('offset'), mul(mul(v('light'), v('direction')), v('time'))), 'b')
    text += definition('sefd', params('current density velocity', 'b'),
        k('ab', v('current'), k('ac', mul(v('density'), v('velocity')))), 'b')
    incoming, outgoing = map(v, ('incoming', 'outgoing'))
    nonnegative = both(op('u', k('aa', incoming, ZERO)), op('u', k('aa', outgoing, ZERO)))
    text += definition('sefe', params('incoming outgoing', 'b'), both(nonnegative, op('e', incoming, outgoing)))
    text += definition('seff', params('incoming outgoing', 'b'), both(op('e', incoming, ZERO), op('e', outgoing, ZERO)))
    return text


SHARED_MEANINGS = {
    'sefa': '指定した対象範囲内で、二時点の所属が各対象ごとに一致する。対象数の一致だけとは区別する。時点間の持続は含まない。',
    'sefb': '基準時点が指定した期間に属し、その期間の全時点で各対象の所属が基準時点と一致する。空の期間を拒否する。期間の連続性・順序・対象の実在は引数の解釈として別途必要。',
}
RATIONAL_MEANINGS = {
    'sefc': '初期位置成分offsetにlight*direction*timeを加えた有理数の等速経路の成分。',
    'sefd': '有理数の流れの成分currentから、密度densityと境界速度velocityの積を引いた相対成分。',
    'sefe': '非負の流入量と流出量が等しく、差し引きが零である。どちらの量も零とは限らない。',
    'seff': '流入量と流出量がともに零である。経路や時間区間から量を計算する定義ではない。',
}


def generic_composed():
    text, basis = ball_generic()
    basis = deepcopy(basis)
    doc = parse(text + shared_definitions() + rational_definitions())
    basis.update(version='transported-contents-basis-v1', document='examples/v014/transported-contents.noema')
    basis['definitions'].update(SHARED_MEANINGS | RATIONAL_MEANINGS)
    basis['unresolved'] += ['期間と対象範囲は明示的な引数。流入・流出の数値と個体の所属は独立しており、光やエネルギーの物理的実体を定義したとはしない。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def definitions():
    text = shared_definitions() + rational_definitions()
    mul = lambda x, y: k('shv', x, y)
    zero, one = k('bb', ZERO), k('bb', ONE)
    V, a, b, c, R, ox, oy, oz = map(v, GEOMETRY.split())
    t = v('time')
    text += definition('sega', params('light direction offset time', CUT),
        k('bd', v('offset'), mul(mul(V, v('direction')), t)), CUT)
    coords = [k('sega', V, axis, offset, t) for axis, offset in zip((a, b, c), (ox, oy, oz))]
    text += definition('segb', params('light ax ay az ox oy oz time', CUT), point_expression([*coords, t]), POINT)
    args = [V, a, b, c, R, ox, oy, oz]
    point = k('segb', V, a, b, c, ox, oy, oz, t)
    for name, original in (('segc', 'secc'), ('segd', 'secb')):
        text += definition(name, params(GEOMETRY + ' time', CUT), both(
            *[k('ba', v(n)) for n in (GEOMETRY + ' time').split()],
            k(original, V, a, b, c, R, *[app(point, k(role)) for role in ROLES])))
    text += definition('sege', params(GEOMETRY, CUT), both(
        *[k('ba', v(n)) for n in GEOMETRY.split()], k('bg', zero, V), k('bg', zero, R),
        k('sca', k('seag', a, b, c), one)))
    text += definition('segf', params(GEOMETRY + ' time', CUT), both(k('sege', *args), k('ba', t),
        *[op('z', k(name, *args, zero), k(name, *args, t)) for name in ('segc', 'segd')]))
    text += definition('segg', params(GEOMETRY, CUT), both(k('sege', *args),
        quant('f', 'time', CUT, op('y', k('ba', t), k('segf', *args, t)))))
    label, labels, origins = map(v, ('label', 'labels', 'origins'))
    offsets = [app(app(origins, label), k(role)) for role in ROLES[:3]]
    text += definition('segh', FAMILY + ' ' + params('light ax ay az radius time', CUT) + ' label a', both(
        app(labels, label), k('segc', V, a, b, c, R, *offsets, t)))
    text += definition('segi', FAMILY + ' ' + params('light ax ay az radius', CUT),
        quant('f', 'label', 'a', op('y', app(labels, label), k('segg', V, a, b, c, R, *offsets))))
    density = v('density')
    text += definition('segj', params('light ax ay az density jx jy jz', CUT), both(
        *[k('ba', v(n)) for n in 'light ax ay az density jx jy jz'.split()],
        k('bg', zero, V), k('sca', k('seag', a, b, c), one), k('bc', zero, density),
        *[k('sca', k('bf', v(current), mul(density, mul(V, direction))), zero)
          for current, direction in zip(('jx', 'jy', 'jz'), (a, b, c))]))
    return text


MEANINGS = {
    'sega': '実切断の等速経路の一成分。初期位置から光速度と方向の積だけ単位時間ごとに移動する。入力の有効性は呼出側で要求する。',
    'segb': '三つの初期位置と時刻から四座標を構成する。全対象に同じ速度ベクトルを用いる。',
    'segc': '有効な初期位置と時刻について、segbの点が既存の移動球の閉内部seccに属する。',
    'segd': '同じ点が既存の移動球面secbに属する。閉内部と球面を区別する。',
    'sege': '有効な初期位置、正の光速度と半径、単位方向を要求する。',
    'segf': '妥当な等速経路について、指定時刻と零時刻で閉内部への所属と球面への所属がそれぞれ一致する。二時刻だけの条件。',
    'segg': '妥当な等速経路の閉内部・球面への所属が全ての有効な実時刻で零時刻と一致する。有限個の時点の一致で代用しない。',
    'segh': 'ラベルの対象範囲と初期位置の関数を用い、指定時刻に同じ移動球の閉内部にいるラベルを選ぶ。範囲外のラベルを含めない。初期位置関数の時刻成分は使用しない。',
    'segi': '対象範囲の各ラベルの初期位置についてseggを要求する。空の対象範囲では真。ラベルと位置の対応は固定したモデルであり、物理的な光の構成要素や生成・消滅を定義したものではない。',
    'segj': '非負の密度と流れの三成分について、移動球の速度V*nに対する相対流れj−density*V*nが各成分で零である。境界積分の差し引きが零という条件より強い点ごとの条件。電磁場の物理法則やエネルギー保存則から導いたとはしない。',
}


def source_composed():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    basis = deepcopy(json.loads((ROOT / 'data/einstein-partition-bounds-basis-v1.json').read_text(encoding='utf-8')))
    statements, doc['statements'] = doc['statements'], []
    doc = parse(format_graph(doc, 'compact') + definitions())
    doc['statements'] = statements
    basis.update(version='einstein-transported-contents-basis-v1', document='examples/v014/einstein-transported-contents.noema')
    basis['definitions'].update(SHARED_MEANINGS | RATIONAL_MEANINGS | MEANINGS)
    basis['unresolved'] += [
        'u0205の持続する同じ光の集合を、固定ラベルの等速輸送モデルとして部分記述する。光子の実在・同一性を仮定しない。ラベルの物理的帰属、生成・消滅や吸収・放出の排除、電磁場とエネルギー密度・流れとの法則は未完。',
        '相対流れが点ごとに零であること、移動球の所属が全時刻で不変であること、非負の流入・流出が等しいことを別の条件とする。相互の物理的な同値性を無条件に主張しない。',
        '有理数の等式検証と有理数を埋め込んだ切断の具体例を、全実切断の法則の機械的証明とはしない。著者の「したがって」の談話と後続のエネルギーを問う発話への接続は未完。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def core_composed():
    text, basis = source_composed()
    doc = parse(text)
    selected = extract_document(doc, roots=['sefa', 'sefb', 'segf', 'segg', 'segh', 'segi', 'segj'], statement_indices=[])
    projected = extract_basis(doc, basis, selected, version='transported-contents-core-basis-v1',
        document_path='examples/v014/transported-contents-core.noema')
    return format_graph(selected.document, 'compact') + '\n', projected


BUILDERS = ((generic_composed, 'transported-contents'), (source_composed, 'einstein-transported-contents'),
            (core_composed, 'transported-contents-core'))


def main():
    for builder, stem in BUILDERS:
        text, basis = builder()
        for name, body in ((basis['document'], text), ('data/' + stem + '-basis-v1.json', json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            path = ROOT / name
            if path.exists():
                if path.read_text(encoding='utf-8') != body:
                    raise ValueError('Stored transport definition differs: ' + name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream:
                    stream.write(body)
        print(stem, len(text), 'characters')


if __name__ == '__main__':
    main()
