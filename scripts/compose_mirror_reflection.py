"""Keep staged mirror reflection and the discrepant printed formula distinct."""
from copy import deepcopy
import json

from noema.extraction import extract_document, extract_basis
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, op, both
from scripts.compose_field_equations import CUT, REGION
from scripts.compose_wave_amplitudes import params
from scripts.compose_wave_directions import generic_composed as arithmetic_document

PARENT = 'examples/v014/einstein-shared-light-law.noema'
STAGES = 'amplitude ax rate firstamplitude firstax firstrate secondamplitude secondax secondrate finalamplitude finalax finalrate'
PAIR = 'amplitude ax rate finalamplitude finalax finalrate'


def wave_definitions(real=False):
    sort = CUT if real else 'b'
    names = ('sejg', 'sejh', 'seji', 'sejj', 'sejk', 'sejl') if real else ('seja', 'sejb', 'sejc', 'sejd', 'seje', 'sejf')
    domain, boost, reflect, chain, derived, printed = names
    zero, one, two = ('n p a b', 'n p b b', 'n p c b')
    if real: zero, one, two = (k('bb', n) for n in (zero, one, two))
    mul = lambda a, b: k('shv' if real else 'ad', a, b)
    add = lambda a, b: k('bd' if real else 'ab', a, b)
    neg = lambda a: k('be' if real else 'ac', a)
    sub = lambda a, b: k('bf', a, b) if real else add(a, neg(b))
    eq = lambda a, b: k('sca', a, b) if real else op('e', a, b)
    lt = lambda a, b: k('bg' if real else 'aa', a, b)
    le = lambda a, b: op('u', lt(b, a))
    sq = lambda a: mul(a, a)
    speednames = 'light speed' if real else 'ratio beta'
    V, speed, a, A, rate = map(v, ('light', 'speed', 'ax', 'amplitude', 'rate'))
    r = mul(speed, k('sjd', V)) if real else v('ratio')
    beta = k('soy', V, speed) if real else v('beta')
    valid = lambda fields: [k('ba', v(n)) for n in fields.split()] if real else []
    speed_domain = k('s45', V, speed) if real else lt(sq(r), one)
    extra = [] if real else [lt(zero, beta), eq(mul(sq(beta), sub(one, sq(r))), one)]
    text = definition(domain, params(speednames+' ax', sort), both(
        *valid(speednames+' ax'), speed_domain, le(sq(a), one), *extra))
    B, b, freq = map(v, ('finalamplitude', 'finalax', 'finalrate'))
    value_guards = lambda: both(*valid(PAIR), le(zero, A), le(zero, B), lt(zero, rate), lt(zero, freq),
        le(sq(a), one), le(sq(b), one))
    factor = mul(beta, sub(one, mul(r, a)))
    text += definition(boost, params(speednames+' '+PAIR, sort), both(
        k(domain, *(v(n) for n in (speednames+' ax').split())), value_guards(),
        eq(B, mul(A, factor)), eq(mul(sub(one, mul(r, a)), b), sub(a, r)), eq(freq, mul(rate, factor))))
    text += definition(reflect, params(PAIR, sort), both(value_guards(), eq(B, A), eq(b, neg(a)), eq(freq, rate)))
    first = [v(n) for n in 'firstamplitude firstax firstrate'.split()]
    second = [v(n) for n in 'secondamplitude secondax secondrate'.split()]
    original = [A, a, rate]; final = [B, b, freq]
    forward = [V, speed] if real else [r, beta]
    inverse = [V, neg(speed)] if real else [neg(r), beta]
    text += definition(chain, params(speednames+' '+STAGES, sort), both(
        k(boost, *forward, *original, *first), k(reflect, *first, *second), k(boost, *inverse, *second, *final)))
    numerator = add(sub(one, mul(two, mul(r, a))), sq(r))
    denominator = sub(one, sq(r))
    closed_speed = 'light speed' if real else 'ratio'
    for name, frequency_denominator in ((derived, denominator), (printed, sq(sub(one, r)))):
        text += definition(name, params(closed_speed+' '+PAIR, sort), both(*valid(closed_speed), speed_domain,
            value_guards(), eq(mul(denominator, B), mul(A, numerator)),
            eq(mul(numerator, b), sub(mul(two, r), mul(add(one, sq(r)), a))),
            eq(mul(frequency_denominator, freq), mul(rate, numerator))))
    return text


RATIONAL_MEANINGS = {
    'seja': '有理数の速度比の絶対値が1未満、正のβ、β²(1−比²)=1、方向余弦の絶対値が1以下という定義域。',
    'sejb': '同じ速度比とβにより、非負の振幅と正の振動数をβ(1−比*方向余弦)倍し、方向余弦を光行差の式で変換する有理数の条件。分母を払って記述する。',
    'sejc': '同じ静止系で振幅と振動数を保存し、縦方向余弦を反転する反射の数値条件。完全反射面の物理的性質は別に仮定する。',
    'sejd': '入射値を比rで変換し、その系でsejcを適用して、比−rで元の系へ戻す三段階。三つの中間量を共有し、別入力を混ぜない。',
    'seje': '三段階から得る閉じた有理数条件。振幅と振動数の係数は(1−2ra+r²)/(1−r²)、方向余弦は[2r−(1+r²)a]/(1−2ra+r²)。',
    'sejf': '原刊915頁M0376の最右辺を保持する有理数条件。振動数の分母だけが(1−r)²であり、sejeの1−r²と区別する。原刊の印刷を保持する記述で、三段階からの帰結とは認定しない。',
}
MEANINGS = {
    'sejg': '正の光速度V、|v|<V、有効な実切断、絶対値1以下の縦方向余弦という変換の定義域。',
    'sejh': 'sejbに対応する実切断の変換条件。速度比v/Vと既存の正のβを使い、振幅・振動数・縦方向余弦を同じ入力から変換する。',
    'seji': '非負の二振幅、正の二振動数、有効な二方向余弦について、振幅と振動数を保存し、縦成分を反転する。場の位相や偏光成分全体の境界条件を代用しない。',
    'sejj': '同じV,vで入射光を鏡の静止系へ変換し、sejiを適用し、速度−vで元へ戻す三段階の実切断条件。中間値を明示して保持する。',
    'sejk': '実切断の三段階から期待する閉じた式。振幅と振動数の分母を共に1−(v/V)²とする。sejlの原刊最右辺とは別の式として保持する。',
    'sejl': '原刊と電子テキストのM0376最右辺を、実切断で保持する条件。振動数の分母は(1−v/V)²である。原刊にも存在する不整合を転記訂正と呼ばず、導出結果sejkと別に記述する。',
    'sejm': '有効な四座標で、第一空間座標ξが零の平面。完全反射という物理的性質を含めない。',
    'sejn': '許容速度のもとで旧系のx=vtを満たす四座標領域。新系のξ=0に対応する動く平面の幾何。',
    'sejo': 'sejnの動く平面を既存の逆ローレンツ座標変換で新座標の領域へ移した条件。sejmとの一致を幾何学の検査で扱う。',
}


def generic_composed():
    text, basis = arithmetic_document(); basis = deepcopy(basis)
    doc = parse(text+wave_definitions())
    basis.update(version='mirror-reflection-basis-v1', document='examples/v014/mirror-reflection.noema')
    basis['definitions'].update(RATIONAL_MEANINGS)
    basis['unresolved'] += ['原刊最右辺と三段階の導出結果を別々に保持する。鏡・完全反射・光圧・エネルギー収支の物理的な説明と原文の談話は未完。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact')+'\n', basis


def source_composed():
    doc = parse((ROOT/PARENT).read_text(encoding='utf-8'))
    basis = deepcopy(json.loads((ROOT/'data/einstein-shared-light-law-basis-v1.json').read_text(encoding='utf-8')))
    statements, doc['statements'] = doc['statements'], []
    text = format_graph(doc, 'compact')+wave_definitions()+wave_definitions(True)
    coords = list(map(v, ('x', 'y', 'z', 'time')))
    zero = k('bb', 'n p a b'); V, speed = v('light'), v('speed')
    text += definition('sejm', params('x y z time', CUT), both(*(k('ba', x) for x in coords), k('sca', coords[0], zero)))
    text += definition('sejn', params('light speed x y z time', CUT), both(
        k('s45', V, speed), *(k('ba', x) for x in coords), k('sca', coords[0], k('shv', speed, coords[3]))))
    old = 'i['+params('x y z time', CUT)+']['+k('sejn', V, speed, *coords)+']'
    text += definition('sejo', params('light speed x y z time', CUT), both(k('s45', V, speed),
        app(k('s6m', V, speed, old), *coords)))
    doc = parse(text); doc['statements'] = statements
    basis.update(version='einstein-mirror-reflection-basis-v1', document='examples/v014/einstein-mirror-reflection.noema')
    basis['definitions'].update(RATIONAL_MEANINGS); basis['definitions'].update(MEANINGS)
    basis['unresolved'] += [
        '原刊914–915頁の鏡の座標面、入射値の変換、静止系の反射、元の系への逆変換を部分記述する。振幅は大きさとして非負、振動数は正とする。',
        'M0376の振動数の最右辺は原刊にも(1−v/V)²と印刷されている。直前の等式から導く1−(v/V)²とは区別し、原文を黙って修正しない。原刊の誤植と断定する歴史資料の確認ではなく、式の不整合の検査である。',
        '動く座標平面と物理的な鏡の同一性、完全反射の電磁的境界条件、入射・反射の光の所属、三段階の基準系・単位の帰属は未完。数値からこれらの物理関係を推定しない。',
        '数値変換は両符号の方向余弦に定義する。特定の側から鏡へ到達する条件Va−v>0や、接触の時刻・位置はまだ課さない。横方向・位相・偏光全体を記述し終えたとはしない。',
        '光圧と仕事・エネルギー収支、問いの提示、最後に得られるという導出の談話、原文との全文意味一致は未完。有理数の代数証明と有限の実切断解釈を、全実数の証明と区別する。',
    ]
    audit_basis(doc, basis)
    return format_graph(doc, 'compact')+'\n', basis


def core_composed():
    text, basis = source_composed(); doc = parse(text)
    selected = extract_document(doc, roots=['sejj', 'sejk', 'sejl', 'sejm', 'sejo'], statement_indices=[])
    projected = extract_basis(doc, basis, selected, version='mirror-reflection-core-basis-v1', document_path='examples/v014/mirror-reflection-core.noema')
    return format_graph(selected.document, 'compact')+'\n', projected


BUILDERS = ((generic_composed, 'mirror-reflection'), (source_composed, 'einstein-mirror-reflection'), (core_composed, 'mirror-reflection-core'))


def main():
    for builder, stem in BUILDERS:
        text, basis = builder()
        for name, body in ((basis['document'], text), ('data/'+stem+'-basis-v1.json', json.dumps(basis, ensure_ascii=False, indent=2)+'\n')):
            path = ROOT/name
            if path.exists():
                if path.read_text(encoding='utf-8') != body: raise ValueError('Stored reflection differs: '+name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream: stream.write(body)
        print(stem, len(text), 'characters')


if __name__ == '__main__': main()
