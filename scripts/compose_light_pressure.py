"""Energy flux, signed work and pressure without dividing by zero velocity."""
from copy import deepcopy
import json

from noema.extraction import extract_document, extract_basis
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, op, both
from scripts.compose_field_equations import CUT
from scripts.compose_wave_amplitudes import params
from scripts.compose_mirror_reflection import generic_composed as reflection_document

PARENT = 'examples/v014/einstein-mirror-reflection.noema'
BASE = 'light speed amplitude ax conversion'
REFLECT = 'light speed amplitude ax finalamplitude finalax conversion'
FLUX = REFLECT+' incoming outgoing'
WORK = 'speed incoming outgoing pressure work'
ALL = FLUX+' pressure work'
LEADING = 'amplitude ax conversion leading'


def definitions(real=False):
    sort = CUT if real else 'b'
    domain, reflection, flux, work, pressure, balance, leading = (
        ('sekh', 'seki', 'sekj', 'sekk', 'sekl', 'sekm', 'sekn') if real else
        ('seka', 'sekb', 'sekc', 'sekd', 'seke', 'sekf', 'sekg'))
    zero, one, two = ('n p a b', 'n p b b', 'n p c b')
    if real: zero, one, two = (k('bb', n) for n in (zero, one, two))
    mul = lambda a, b: k('shv' if real else 'ad', a, b)
    add = lambda a, b: k('bd' if real else 'ab', a, b)
    sub = lambda a, b: k('bf', a, b) if real else add(a, k('ac', b))
    eq = lambda a, b: k('sca', a, b) if real else op('e', a, b)
    lt = lambda a, b: k('bg' if real else 'aa', a, b)
    le = lambda a, b: op('u', lt(b, a))
    sq = lambda x: mul(x, x)
    valid = lambda fields: [k('ba', v(n)) for n in fields.split()] if real else []
    invoke = lambda fn, fields: k(fn, *map(v, fields.split()))
    V, speed, A, a, B, b, C, incoming, outgoing, P, W, P0 = map(v,
        'light speed amplitude ax finalamplitude finalax conversion incoming outgoing pressure work leading'.split())
    denominator = sub(sq(V), sq(speed))
    numerator = add(sub(sq(V), mul(two, mul(mul(speed, V), a))), sq(speed))
    entering, leaving = sub(mul(V, a), speed), sub(speed, mul(V, b))
    text = definition(domain, params(BASE, sort), both(*valid(BASE),
        lt(zero, V), lt(sq(speed), sq(V)), le(sq(a), one), le(zero, A), lt(zero, C)))
    text += definition(reflection, params(REFLECT, sort), both(invoke(domain, BASE), *valid('finalamplitude finalax'),
        le(zero, B), le(sq(b), one), eq(mul(denominator, B), mul(A, numerator)),
        eq(mul(numerator, b), sub(mul(two, mul(speed, V)), mul(add(sq(V), sq(speed)), a)))))
    text += definition(flux, params(FLUX, sort), both(invoke(domain, BASE), *valid('finalamplitude finalax incoming outgoing'),
        le(zero, B), le(sq(b), one), le(zero, entering), le(zero, leaving), le(zero, incoming), le(zero, outgoing),
        eq(mul(C, incoming), mul(sq(A), entering)), eq(mul(C, outgoing), mul(sq(B), leaving))))
    text += definition(work, params(WORK, sort), both(*valid(WORK), le(zero, incoming), le(zero, outgoing), le(zero, P),
        eq(W, sub(incoming, outgoing)), eq(W, mul(P, speed))))
    text += definition(pressure, params(BASE+' pressure', sort), both(invoke(domain, BASE), *valid('pressure'), le(zero, P),
        eq(mul(mul(C, denominator), P), mul(two, mul(sq(A), sq(entering))))))
    text += definition(balance, params(ALL, sort), both(invoke(reflection, REFLECT), invoke(flux, FLUX), invoke(work, WORK)))
    text += definition(leading, params(LEADING, sort), both(*valid(LEADING), le(zero, A), le(sq(a), one),
        lt(zero, C), le(zero, P0), eq(mul(C, P0), mul(two, mul(sq(A), sq(a))))))
    return text


RATIONAL_MEANINGS = {
    'seka': '正の光速度、光速未満の符号付き速度、非負の振幅、絶対値1以下の方向余弦、正の密度換算係数という有理数の定義域。',
    'sekb': '同じV,vについて、前版の三段階から得る振幅と縦方向余弦の閉じた式を分母を払って表す。振動数はエネルギー収支に使わず、原刊M0376の不整合な振動数式も取り込まない。',
    'sekc': '同じ系の単位面積・単位時間に対応する入出エネルギー値を、C*incoming=A²(Va−v)、C*outgoing=B²(v−Vb)で拘束する。両側の相対法線速度を非負とし、掠める境界と零振幅も許す。',
    'sekd': '非負の入出エネルギー値と圧力について、符号付き仕事率work=incoming−outgoing=pressure*speedを要求する。速度や仕事率を非負とは要求せず、零速度で圧力を除算して決めない。',
    'seke': '同じ定義域でC*(V²−v²)*P=2*A²*(Va−v)²を満たす非負の圧力。零速度にも値を定めるが、仕事の式だけから零速度で導けたことにはしない。',
    'sekf': '同じ振幅・方向・速度・換算係数・入出エネルギー・圧力・仕事率を、反射sekb、流入出sekc、仕事sekdに共有させる。圧力の閉じた式sekeを前提に含めない。',
    'sekg': '非負の振幅と絶対値1以下の方向余弦に対し、C*leading=2*A²*a²を満たす非負の値。原文の最初の近似として示す速度零の項であり、非零速度で厳密値と等置しない。',
}
MEANINGS = {
    'sekh': 'sekaの定義域を有効な実切断で表す。密度換算係数は正で、光速と同一視しない。',
    'seki': 'sekbの振幅・方向の反射変換を実切断の等式として表す。三段階と結ぶ有理数の代数検査は、実切断全域の証明とは分ける。',
    'sekj': 'sekcの同じ面積・時間規約における入出エネルギーを実切断で表す。相対法線速度の零は境界であり、実際に光が到着したと断言しない。',
    'sekk': '入出エネルギーの差と圧力・速度の積を、同じ符号付き仕事率へ結ぶ実切断の条件。',
    'sekl': '正の光速度と係数、許容速度について、光圧の閉じた式を実切断で表す。速度零でも式の値はある。',
    'sekm': '実切断の反射・入出エネルギー・仕事の条件を同じ引数で接続する。仕事の式では零速度の圧力が未決定となることを保持する。',
    'sekn': 'C*leading=2*A²*a²という速度零の項を実切断で表す。近似と厳密値の識別に使う。',
    'seko': '既存の積分によるpiの指定を要求し、係数C=8*piとしてsekmのエネルギー収支へ接続する。任意の正の係数をpiと認定しない。',
    'sekp': '同じpiの指定とC=8*piにより、seklの光圧式へ接続する。圧力の量の種類・装置・単位実現は別途必要。',
    'sekq': '同じpiの指定とC=8*piにより、seknの速度零の近似項へ接続する。原文の経験・他理論との一致を自動的に補わない。',
}


def generic_composed():
    text, basis = reflection_document(); basis = deepcopy(basis)
    doc = parse(text+definitions())
    basis.update(version='light-pressure-basis-v1', document='examples/v014/light-pressure.noema')
    basis['definitions'].update(RATIONAL_MEANINGS)
    basis['unresolved'] += ['Cは任意の正の係数として扱う有理数のモデル。原刊の8*piは実切断の草案に接続する。零速度の圧力を仕事から除算して導かず、近似の項を厳密式と区別する。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact')+'\n', basis


def source_composed():
    doc = parse((ROOT/PARENT).read_text(encoding='utf-8'))
    basis = deepcopy(json.loads((ROOT/'data/einstein-mirror-reflection-basis-v1.json').read_text(encoding='utf-8')))
    statements, doc['statements'] = doc['statements'], []
    text = format_graph(doc, 'compact')+definitions()+definitions(True)
    coefficient = k('shv', k('bb', 'n p i b'), v('pi'))
    for name, base, fields in (('seko', 'sekm', ALL), ('sekp', 'sekl', BASE+' pressure'), ('sekq', 'sekn', LEADING)):
        text += definition(name, params(fields.replace('conversion', 'pi'), CUT), both(k('sedi', v('pi')),
            k(base, *(coefficient if n == 'conversion' else v(n) for n in fields.split()))))
    doc = parse(text); doc['statements'] = statements
    basis.update(version='einstein-light-pressure-basis-v1', document='examples/v014/einstein-light-pressure.noema')
    basis['definitions'].update(RATIONAL_MEANINGS); basis['definitions'].update(MEANINGS)
    basis['unresolved'] += [
        'u0222–u0225の入出エネルギー・仕事・光圧・近似式を部分記述する。単位面積と単位時間について同じ規約で正規化した量の値として扱い、面積・時間の測定や物体への帰属を補わない。',
        '反射の振幅と方向は前版の三段階から得るものを使う。原刊M0376最右辺の振動数の不整合は、圧力を合わせるために消去も同一視もしない。',
        '仕事の式から圧力を一意に導く際にはv≠0が必要。静止時はこの式だけでは圧力を定められない。閉じた圧力式の静止値を、運動量移転や連続性から物理的に正当化する接続は未完。',
        '特定の面への流入出についてVa−vとv−Vbを非負にする。等号は掠める境界で、光の到着の断言ではない。鏡の実体、接触出来事、完全反射の場の境界条件は未完。',
        '速度零の項を近似として分離し、有理数の許容域で誤差の上界を検査する。実切断全域の極限・連続性の証明、経験と他理論との一致、原文の自明さや導出の談話は未完。',
    ]
    audit_basis(doc, basis)
    return format_graph(doc, 'compact')+'\n', basis


def core_composed():
    text, basis = source_composed(); doc = parse(text)
    selected = extract_document(doc, roots=['seko', 'sekp', 'sekq'], statement_indices=[])
    projected = extract_basis(doc, basis, selected, version='light-pressure-core-basis-v1', document_path='examples/v014/light-pressure-core.noema')
    return format_graph(selected.document, 'compact')+'\n', projected


BUILDERS = ((generic_composed, 'light-pressure'), (source_composed, 'einstein-light-pressure'), (core_composed, 'light-pressure-core'))


def main():
    for builder, stem in BUILDERS:
        text, basis = builder()
        for name, body in ((basis['document'], text), ('data/'+stem+'-basis-v1.json', json.dumps(basis, ensure_ascii=False, indent=2)+'\n')):
            path = ROOT/name
            if path.exists():
                if path.read_text(encoding='utf-8') != body: raise ValueError('Stored pressure differs: '+name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream: stream.write(body)
        print(stem, len(text), 'characters')


if __name__ == '__main__': main()
