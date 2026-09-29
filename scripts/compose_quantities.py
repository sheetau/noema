"""Compose dimensions and units with the real arithmetic and beta relations."""
import json
from pathlib import Path

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis

ROOT = Path(__file__).resolve().parents[1]


def composed():
    text = (ROOT / 'examples/v011/real-products.noema').read_text(encoding='utf-8')
    text += (ROOT / 'examples/fragments/clock-coordinate.noema.inc').read_text(encoding='utf-8')
    text += (ROOT / 'examples/fragments/quantities.noema.inc').read_text(encoding='utf-8')
    doc = parse(text)
    basis = json.loads((ROOT / 'data/real-products-basis-v1.json').read_text(encoding='utf-8'))
    basis['version'] = 'quantities-basis-v1'
    basis['document'] = 'examples/v011/quantities.noema'
    basis['definitions'].update({
        'bj': '正の有理数scaleによる切断の拡大。scaleが0以下なら空集合となり、有効な切断を表さない。',
        'bk': '切断の正の尺度変更と原点offsetの加算。今回の乗法的な単位換算とは別の座標用演算。',
        'da': '全ての基底軸の指数が0である次元。無次元を表す。',
        'db': '次元の積。各基底軸の指数を加算する。',
        'dc': '次元の逆。各基底軸の指数の符号を反転する。',
        'dd': '次元の商。分子側から分母側の指数を減算する。',
        'de': '次元の有理数乗。各指数にpowerを掛ける。値そのものの冪乗が定義できることは別に検査する。',
        'df': '全ての基底軸で指数が等しいという次元の同一性。',
        'dg': '次元がdaと等しいという無次元条件。異なる無次元の量が同じ種類だとは推論しない。',
        'dh': '一つの基底軸の次元の特徴付け。その軸だけが指数1で、他の全ての軸は0。基本記号に名称を与えるだけで済ませない。',
        'di': '量の種類・次元が同じで、二つの単位尺度が正の有理数であるという換算の適合条件。',
        'dj': '有理数の二つの読みが同じ量を表すという換算関係。diの条件に加えて、読み*単位尺度が等しい。',
        'dk': '実切断の二つの読みが同じ量を表す換算関係。diの条件、両方の切断条件と、尺度を掛けた切断の同一性を要求する。',
        'ds': '三つの有理数の単位尺度が全て正。',
        'dl': '有理数の量の積。結果次元が入力次元の積で、基準単位へ換算した結果が入力値の積である。結果の量の種類を次元だけから決めない。',
        'dm': '有理数の量の商。結果次元が入力次元の商で、分母が非零、尺度換算した値が乗算による商の等式を満たす。',
        'dn': 'βの入力に使う次元条件。長さ軸と時間軸は異なり、長さ・時間はdhを満たす基底次元、二速度は同じ種類かつ長さ/時間の次元、係数は無次元である。',
        'dp': '速度・光速度・係数をそれぞれ正の尺度で基準単位へ換算し、cmの有理数のβ条件を適用する。',
        'do': 'dnの種類・次元条件とdpの数値条件を合わせた有理数のβ関係。',
        'dq': 'dnの種類・次元条件と正の尺度条件を満たし、実切断の各読みを基準単位へ換算してclを適用するβ関係。'})
    basis['unresolved'] += [
        '量の種類、長さ・時間の物理的な意味、単位の実現と観測・物体・出来事・基準系の関係は別の意味規約が必要。',
        '次元は任意の軸に対する有理数指数の関数としている。物理的に採用する有限の基底体系と量の種類は明示する必要がある。',
        '単位尺度は正の有理数に限る。無理数の尺度、アフィン量の原点移動、対数量の換算は今回のdj/dkでは扱わない。',
        '同じ種類・次元の二値であることは、同じ対象・出来事・基準系の測定であることを保証しない。本文の観測関係への接続は未完。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def main():
    text, basis = composed()
    for name, body in {basis['document']: text, 'data/quantities-basis-v1.json': json.dumps(basis, ensure_ascii=False, indent=2) + '\n'}.items():
        path = ROOT / name
        if path.exists():
            if path.read_text(encoding='utf-8') != body:
                raise ValueError('Stored quantities differ: ' + name)
        else:
            with path.open('x', encoding='utf-8', newline='\n') as stream:
                stream.write(body)
    print('Dimensions, rational unit scales and beta conditions composed')


if __name__ == '__main__':
    main()
