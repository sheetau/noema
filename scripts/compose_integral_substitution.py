"""State oriented substitution and its two applications to electron work."""
from copy import deepcopy
import json

from noema.grammar import parse, format_graph
from noema.extraction import extract_document, extract_basis
from noema.meaning_basis import audit_basis
from scripts.compose_electron_power_law import ROOT, CUT, SCALAR, ALL
from scripts.compose_electron_axis_motion import ROLES, coord
from scripts.compose_origin_clock import definition, v
from scripts.compose_limits import call as k, app, both, op, quant, lam, ZERO
from scripts.compose_situated_criticism import params, args

PARENT = 'examples/v014/einstein-electron-power-law.noema'
LIBRARY = 'examples/v014/integral-substitution.noema'
BASIS = 'data/integral-substitution-basis-v1.json'
BOUNDS = [(n, CUT) for n in ('lower', 'upper', 'rangelower', 'rangeupper')]
FUNCTIONS = [(n, SCALAR) for n in ('transform', 'rate', 'integrand')]
FIELDS = BOUNDS + FUNCTIONS
RANGES = [(n, CUT) for n in ('positionlower', 'positionupper', 'speedlower', 'speedupper')]


def interval(lower, upper):
    return lam('point', CUT, k('sxs', lower, upper, v('point')))


def definitions():
    lower, upper, rlo, rhi = args(BOUNDS)
    transform, rate, integrand = args(FUNCTIONS)
    time, value = v('time'), v('value')
    inside = interval(lower, upper)
    outer = interval(rlo, rhi)
    # Unit charge reuses the existing signed integral, including equal bounds.
    text = definition('sesi', params([('lower', CUT), ('upper', CUT), ('integrand', SCALAR), ('value', CUT)]),
        k('sero', lower, upper, k('bb', 'n p b b'), value, integrand))
    text += definition('sesj', params(FIELDS + [('time', CUT)]), both(
        k('ba', app(transform, time)), k('ba', app(rate, time)),
        k('sxs', rlo, rhi, app(transform, time)),
        k('sjs', inside, transform, time, app(rate, time))))
    text += definition('sesk', params(FIELDS), both(
        *[k('ba', x) for x in args(BOUNDS)], k('bg', lower, upper), k('bg', rlo, rhi),
        k('sxu', inside, transform), k('sxu', inside, rate), k('sxu', outer, integrand),
        quant('f', 'time', CUT, op('y', k('sxs', lower, upper, time), k('sesj', *args(FIELDS), time)))))
    text += definition('sesl', params(FUNCTIONS), lam('time', CUT,
        k('shv', app(integrand, app(transform, time)), app(rate, time))), SCALAR)
    before = k('sesi', app(transform, lower), app(transform, upper), integrand, value)
    after = k('sesi', lower, upper, k('sesl', *args(FUNCTIONS)), value)
    text += definition('sesm', params(FIELDS + [('value', CUT)]), both(before, after))
    text += definition('sesn', params(FIELDS), op('y', k('sesk', *args(FIELDS)), both(
        quant('g', 'value', CUT, both(k('ba', value), k('sesm', *args(FIELDS), value))),
        quant('f', 'value', CUT, op('y', k('ba', value), op('z', before, after))))))

    # Two changes of variable share one time interval and the existing motion.
    start = coord(v('startpoint'), ROLES[3]); end = coord(v('endpoint'), ROLES[3])
    position = lam('time', CUT, coord(app(v('curve'), time), ROLES[0]))
    force = lam('position', CUT, k('shv', v('charge'), app(v('profile'), v('position'))))
    energy_rate = lam('speed', CUT, k('sere', v('light'), v('mass'), v('speed')))
    spatial = [start, end, v('positionlower'), v('positionupper'), position, v('velocity'), force]
    velocity = [start, end, v('speedlower'), v('speedupper'), v('velocity'), v('acceleration'), energy_rate]
    text += definition('seso', params(ALL + RANGES), both(k('sesf', *args(ALL)),
        k('sesk', *spatial), k('sesk', *velocity),
        # The square root integrand must stay strictly within its domain.
        k('bg', k('be', v('light')), v('speedlower')), k('bg', v('speedupper'), v('light'))))
    work = k('sesi', app(position, start), app(position, end), force, value)
    kinetic = k('sesi', app(v('velocity'), start), app(v('velocity'), end), energy_rate, value)
    text += definition('sesp', params(ALL + RANGES), op('y', k('seso', *args(ALL + RANGES)), both(
        k('sesn', *spatial), k('sesn', *velocity),
        quant('g', 'value', CUT, both(k('ba', value), work, kinetic)),
        quant('f', 'value', CUT, op('y', k('ba', value), op('z', work, kinetic))))))
    fixed = [k('zramatter'), k('ra'), v('context'), k('zrhdomain'), k('zrhcurve'), k('zrgstart'), k('zraevent'),
        k('zrhstartpoint'), k('zrhendpoint'), k('zrgposition'), k('zb7'), k('zrivelocity'), k('zriacceleration'),
        k('zrgprofile'), k('tc'), k('zramu'), k('zrgcharge')]
    text += definition('sesq', params(RANGES), 'b context[' + both(
        't[' + k('sesh') + '][' + v('context') + ']',
        k('seso', *fixed, *args(RANGES)), k('sesp', *fixed, *args(RANGES))) + ']', 'e')
    return text


MEANINGS = {
    'sesi': '向きを持つ実切断の定積分。既存seroの電荷を1として再利用し、逆順では符号を反転し、両端一致では値零を要求する。',
    'sesj': '時間区間に相対的な変換関数の微分が同じrateであり、変換値が指定の外側区間に属するという一時刻の条件。',
    'sesk': '正の長さの時間区間と外側区間を指定し、変換関数とその微分の連続性、被積分関数の連続性、全時刻のsesjを要求する。単調性や微分の非零性は要求しない。',
    'sesl': 'integrand(transform(time))*rate(time)という変数変換後の被積分関数。微分の絶対値には置き換えない。',
    'sesm': '同じ値が、変換された両端間の積分と時間区間上の変換後の積分を同時に満たす。',
    'sesn': 'seskの条件から共通の積分値の存在と全実数候補についての同値を述べる変数変換の命題。記述した命題であり、全実切断に対する証明済み定理の登録ではない。',
    'seso': '同じ電子の軌道と全時刻の縦方向の式に、位置および速度についての二つの変数変換の正則性を加える。速度の外側区間は厳密に(-light,light)内に収める。',
    'sesp': 'sesoを前提とし、位置への変換と速度への変換、同じ仕事の値の存在と両積分の同値を述べる。質量を含む速度積分へ接続し、初速零での除算は行わない。',
    'sesq': '既存の本文の軌道・仕事・収支前提に、明示的に与えた位置と速度の範囲および変数変換の条件と命題を合わせた解釈候補。著者の追加発話としては帰属させない。',
}
LIMITS = [
    '全実切断の連続性・微分・積分の基本定理と変数変換の機械的証明は未完。sesn・sespを定義しただけで真とする規則は追加しない。',
    'sesqは正則性を追加した解釈候補であり、原文が全ての正則性仮定を明記したという主張ではない。原文対応範囲は増やさない。',
    '一般の関数を有限標本から多項式と推定しない。有理係数多項式の検査は、その明示的に登録した関数の解析的解釈に限る。',
    '原刊の質量係数を欠く中間積分と、質量を含む候補は引き続き区別する。物理的な静電力・単位・無放射の説明も残る。',
]


def build():
    parent = parse((ROOT/PARENT).read_text(encoding='utf-8'))
    doc = deepcopy(parent); doc['statements'] = []
    doc = parse(format_graph(doc, 'compact') + definitions())
    basis = json.loads((ROOT/'data/einstein-electron-power-law-basis-v1.json').read_text(encoding='utf-8'))
    basis['definitions'].update(MEANINGS); basis['unresolved'] += LIMITS
    selection = extract_document(doc, roots=list(MEANINGS), statement_indices=[])
    selected_basis = extract_basis(doc, basis, selection, version='integral-substitution-basis-v1', document_path=LIBRARY)
    audit_basis(selection.document, selected_basis)
    return {LIBRARY: format_graph(selection.document, 'compact')+'\n',
            BASIS: json.dumps(selected_basis, ensure_ascii=False, indent=2)+'\n'}


def main():
    for name, body in build().items():
        path = ROOT/name
        if path.exists():
            assert path.read_text(encoding='utf-8') == body, name
        else:
            with path.open('x', encoding='utf-8', newline='\n') as stream: stream.write(body)
        print(name, len(body), flush=True)


if __name__ == '__main__': main()
