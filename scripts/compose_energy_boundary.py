"""Express left divergence without an infinite real or a physical inference rule."""
from copy import deepcopy
import json
from noema.grammar import parse, format_graph
from noema.extraction import extract_document, extract_basis
from noema.meaning_basis import audit_basis
from scripts.compose_electron_power_law import ROOT, CUT, SCALAR
from scripts.compose_electron_axis_motion import DOMAIN
from scripts.compose_origin_clock import definition, v
from scripts.compose_limits import call as k, app, both, op, quant, lam, ZERO
from scripts.compose_situated_criticism import params, args

PARENT = 'examples/v014/einstein-electron-power-law.noema'
SOURCE = 'examples/v014/einstein-energy-boundary.noema'
LIBRARY = 'examples/v014/energy-boundary.noema'
CORE = 'examples/v014/energy-boundary-core.noema'
READING = 'data/energy-boundary-reading-v1.json'
PHYSICAL = [('light', CUT), ('particle', 'a'), ('frame', 'a'), ('context', 'd'),
            ('accessible', 'h[d d] c'), ('attainable', 'h[a a '+CUT+' d] c')]
RATIONAL = [(n, 'b') for n in ('light', 'mass', 'bound', 'level', 'radius')]


def definitions():
    zero, one = k('bb', ZERO), k('bb', 'n p b b')
    boundary, radius, point, bound = map(v, ('boundary', 'radius', 'point', 'bound'))
    domain, function = v('domain'), v('function')
    positive = lambda x: both(k('ba', x), k('bg', zero, x))
    text = definition('sesr', params([(n, CUT) for n in ('boundary', 'radius', 'point')]), both(
        k('ba', boundary), positive(radius), k('ba', point),
        k('bg', k('bf', boundary, radius), point), k('bg', point, boundary)))
    text += definition('sess', params([('domain', DOMAIN), ('boundary', CUT)]), both(k('ba', boundary),
        quant('f', 'radius', CUT, op('y', positive(radius), quant('g', 'point', CUT,
            both(k('sesr', boundary, radius, point), app(domain, point)))))))
    text += definition('sest', params([('domain', DOMAIN), ('function', SCALAR), ('boundary', CUT)]), both(
        k('sess', domain, boundary), k('sjo', domain, function),
        quant('f', 'bound', CUT, op('y', k('ba', bound), quant('g', 'radius', CUT, both(positive(radius),
            quant('f', 'point', CUT, op('y', both(k('sesr', boundary, radius, point), app(domain, point)),
                k('bg', bound, app(function, point))))))))))
    light, mass, speed = map(v, ('light', 'mass', 'speed'))
    mul = lambda a, b: k('shv', a, b)
    scale = mul(mass, mul(light, light))
    text += definition('sesu', params([(n, CUT) for n in ('light', 'mass', 'speed')]),
        mul(scale, k('bf', k('soy', light, speed), one)), CUT)
    speeds = lam('speed', CUT, both(k('ba', speed), k('bc', zero, speed), k('bg', speed, light)))
    energy = lam('speed', CUT, k('sesu', light, mass, speed))
    text += definition('sesv', params([('light', CUT), ('mass', CUT)]), both(positive(light), positive(mass),
        k('sest', speeds, energy, light)))
    nonnegative_bound = k('szi', k('bg', bound, zero), zero, bound)
    level = k('bd', one, mul(nonnegative_bound, k('sjd', scale)))
    delta = mul(light, k('sjd', mul(k('bb', 'n p c b'), mul(level, level))))
    text += definition('sesw', params([(n, CUT) for n in ('light', 'mass', 'bound')]), delta, CUT)
    text += definition('sesx', params([(n, CUT) for n in ('light', 'mass', 'bound', 'speed')]), both(
        positive(light), positive(mass), k('ba', bound), k('ba', speed), k('bc', zero, speed),
        k('sesr', light, k('sesw', light, mass, bound), speed), k('bg', bound, k('sesu', light, mass, speed))))
    # Polynomial equations expose the radius certificate without division.
    light, mass, bound, level, radius = args(RATIONAL)
    mul = lambda a, b: k('ad', a, b)
    sub = lambda a, b: k('ab', a, k('ac', b))
    text += definition('sesy', params(RATIONAL), both(
        k('aa', ZERO, light), k('aa', ZERO, mass), op('u', k('aa', bound, ZERO)),
        op('u', k('aa', level, 'n p b b')), k('aa', ZERO, radius),
        op('e', bound, mul(mul(mass, mul(light, light)), sub(level, 'n p b b'))),
        op('e', mul(mul('n p c b', mul(level, level)), radius), light)))
    extra = [(n, 'b') for n in ('speed', 'beta', 'energy')]
    text += definition('sesz', params(RATIONAL+extra), both(k('sesy', *args(RATIONAL)),
        k('serb', light, v('speed'), v('beta'), mass, v('energy')),
        k('aa', sub(light, radius), v('speed'))))

    light, particle, frame, context, accessible, attainable = args(PHYSICAL)
    speed, alternative = v('speed'), v('alternative')
    text += definition('seta', params(PHYSICAL+[('speed', CUT)]), both(
        positive(light), k('ba', speed), k('bg', light, speed),
        quant('g', 'alternative', 'd', app(accessible, context, alternative)),
        quant('f', 'alternative', 'd', op('y', app(accessible, context, alternative),
            op('u', app(attainable, particle, frame, speed, alternative))))))
    text += definition('setb', params(PHYSICAL), both(positive(light),
        quant('g', 'alternative', 'd', app(accessible, context, alternative)),
        quant('f', 'speed', CUT, op('y', both(k('ba', speed), k('bg', light, speed)),
            k('seta', *args(PHYSICAL), speed)))))
    text += definition('setc', '', 'b context['+k('sesv', k('tc'), k('zramu'))+']', 'e')
    text += definition('setd', '', 'b context['+k('setb', k('tc'), k('zramatter'), k('ra'), v('context'),
        k('zrjaccessible'), k('zrjattainable'))+']', 'e')
    return text


MEANINGS = {
    'sesr': '有限の実切断boundaryに対する、正のradius幅の左側の厳密な近傍。境界そのものと左端は含めない。',
    'sess': '任意に小さい左側近傍ごとにdomainの点が存在する。空の定義域や、境界から離れた範囲による空虚な発散認定を防ぐ。',
    'sest': '左側の集積点で、任意の有限の上限boundに対し、十分近い全ての定義域内の点でfunctionの値がboundを超えるという正の無限大への発散。無限大を実切断として追加しない。',
    'sesu': '正の質量・光速度および0以上で光速未満の速度に対する運動エネルギー候補mass*light^2*(beta-1)。呼出側が適用範囲を保持する。',
    'sesv': 'sesuが速度を光速へ下から近づけたときに発散するという内容。光速そのもので有限値を与えることや、超光速の物理的実現性を意味しない。',
    'sesw': '正のlightとmassについて、R=1+max(bound,0)/(mass*light^2)としたときの正の近傍幅light/(2*R^2)。全ての有限上限に依存して幅を選ぶ候補。',
    'sesx': '指定された一つの非負速度がseswの近傍内にあり、その運動エネルギー候補が同じboundを超える局所条件。全近傍内の全称命題とは区別する。',
    'sesy': '非負boundとR>=1について、bound=mass*light^2*(R-1)、2*R^2*radius=lightとする正の有理数の近傍幅の証明用条件。',
    'sesz': 'sesy、既存serbのエネルギー・正規化式、速度が光速のradius以内にある条件を同じ値で結ぶ有理数の証明前件。',
    'seta': '同じ物体・基準系の指定された超光速度が、基準文脈から許容されるどの物理的な状況でも実現しないという条件。許容状況は空でないことを要求する。',
    'setb': '指定の物体・基準系について、全ての光速を超える速さがsetaを満たす。速度の実数全域と、物理的に許容された状況の範囲を区別する。',
    'setc': 'u0263前半を、同じVとmuのエネルギー関数の左側発散として読む部分内容。原文のv=Vという表記を境界への接近として解釈する。',
    'setd': 'u0263後半の超光速度に存在可能性がないという主張を、同じ電子・Kと明示した物理的可能性の範囲で読む部分内容。数学的発散から自動で導出しない。',
}
LIMITS = [
    '原刊のv=Vで無限大という表記を、0<=v<Vのエネルギー関数の左側発散として読む。境界値へ実数の無限大を代入しない。',
    '有理係数の一般的な代数検査と、有理数を埋め込んだ局所モデルの評価を行う。実切断の全ての上限・近傍・速度に対する極限の機械的証明は未完。',
    '発散だけから超光速の存在不可能性は証明されない。可能な物理状況と速さの帰属の基礎説明、および数学と物理の接続は残る。',
    'u0263のalsoによる理由接続、以前の結果との比較、物理的な範囲の完全性、全体の意味一致は未記述または未確認。',
]


def build():
    old = parse((ROOT/PARENT).read_text(encoding='utf-8')); doc = deepcopy(old); doc['statements'] = []
    values = {'zrjaccessible': ('h[d d] c', '同じ理論の適用範囲で基準文脈から物理的に許容される状況。数学的な関数の定義域とは別の関係。'),
              'zrjattainable': ('h[a a '+CUT+' d] c', '物体が基準系に対して指定の速さを持つ物理状態が、その状況で実現するという関係。'),
              'zrjlimitnode': ('a', 'u0263の無限大への増大を述べる箇所。'),
              'zrjpossiblenode': ('a', 'u0263の超光速度の存在不可能性を述べる箇所。'),
              'zrjscope': ('a', 'u0263の正の質量を持つ電子と同じ理論の適用範囲。')}
    additions = ''.join('r '+n+'[] '+sort+'.' for n, (sort, _) in values.items())+definitions()
    doc = parse(format_graph(doc, 'compact')+additions)
    claims = ''.join('s['+k('uh', k(node), k('rd'), 'r['+k(content)+']', k('zrjscope'), k('ri'))+'].'
                     for node, content in [('zrjlimitnode', 'setc'), ('zrjpossiblenode', 'setd')])
    doc['statements'] = old['statements']+parse(format_graph(doc, 'compact')+claims)['statements']
    basis = json.loads((ROOT/'data/einstein-electron-power-law-basis-v1.json').read_text(encoding='utf-8'))
    basis.update(version='einstein-energy-boundary-basis-v1', document=SOURCE)
    basis['definitions'].update(MEANINGS); basis['unresolved'] += LIMITS
    lookup = {d['name']: d for d in doc['declarations']}
    for name, (_, meaning) in values.items():
        d = lookup[name]; basis['primitives'].append(dict(symbol=name, parameters=d['parameters'], result=d['result'], arguments=[], meaning_ja=meaning))
    audit_basis(doc, basis)
    files = {SOURCE: format_graph(doc, 'compact')+'\n', 'data/einstein-energy-boundary-basis-v1.json': basis}
    for path, roots, indices in [(LIBRARY, list(MEANINGS)[:-2]+['sca'], []), (CORE, list(MEANINGS)+['sca'], [len(old['statements']), len(old['statements'])+1])]:
        selection = extract_document(doc, roots=roots, statement_indices=indices); stem = path.rsplit('/', 1)[1][:-6]
        files[path] = format_graph(selection.document, 'compact')+'\n'
        files['data/'+stem+'-basis-v1.json'] = extract_basis(doc, basis, selection, version=stem+'-basis-v1', document_path=path)
    return {p: body if isinstance(body, str) else json.dumps(body, ensure_ascii=False, indent=2)+'\n' for p, body in files.items()}


def main():
    for path, body in build().items():
        destination = ROOT/path
        if destination.exists(): assert destination.read_text(encoding='utf-8') == body, path
        else:
            with destination.open('x', encoding='utf-8', newline='\n') as stream: stream.write(body)
        print(path, len(body), flush=True)


if __name__ == '__main__': main()
