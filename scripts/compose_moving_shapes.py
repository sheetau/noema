"""Compose a world tube, a frame's time slice, and the moving sphere equations."""
import json
from pathlib import Path

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis

ROOT = Path(__file__).resolve().parents[1]


def composed():
    text = (ROOT / 'examples/v011/einstein-phi-normalization.noema').read_text(encoding='utf-8')
    text += (ROOT / 'examples/fragments/moving-shapes.noema.inc').read_text(encoding='utf-8')
    doc = parse(text)
    basis = json.loads((ROOT / 'data/phi-normalization-basis-v1.json').read_text(encoding='utf-8'))
    basis['version'] = 'moving-shapes-basis-v1'
    basis['document'] = 'examples/v011/einstein-moving-shapes.noema'
    basis['definitions'].update({
        'ga': '正の半径の球面を、その中心からの三つの座標で記述する。球の内部まで含む条件ではない。',
        'gb': '正のβと許容速度の条件cmを保ち、β(x-vt)、y、zが半径radiusの球面ga上にある条件。中心の移動と各時刻の形を同じ式で記述する。',
        'gc': '正のβについて、βx、y、zが球面ga上にある楕円体の表面条件。原点時刻の断面に使う。',
        'gd': '正の半径とβに対し、正の縦半軸はβとの積が半径となり、二つの横半軸は半径そのものである。直径との混同を避け、軸上の中心から正の交点までの距離を表す。',
        'ge': '正の半径・光速度、光速未満の速度と正の縦半軸について、V²a²=R²(V²-v²)となる条件。βを消去した代数的な半軸の条件。',
        'gg': '球面の各点を全時刻で同じ位置に置く、四座標上の成立条件。静止した球面の世界管の数学的な記述。',
        'gh': 'gbを時刻と位置を引数とする関数にしたもの。',
        'gi': '任意の四座標上の成立条件について、その座標系の一つの時刻を固定した三次元の断面を作る。',
        'gj': '任意の二時刻で全位置の成立条件が一致する。与えた座標系での形状の時間不変性であり、全座標系での静止や物質の剛性を意味しない。',
        'gl': '異なる二つの出来事に、同じ座標系・文脈・長さ単位・時間単位・時刻を用いて位置を割り当てる。',
        'gm': 'glの二出来事が、同じ明示した出来事集合にも属する。物体表面に属するという解釈は集合の与え方で明示する。',
        'gn': '実切断の正の半径と三位置による球面条件。有効な切断を要求する。',
        'go': '実切断のβと速度の条件を保持し、符号付きの中心移動を反映した球面の世界管を記述する。',
        'gp': '実切断で、正の縦半軸と二つの横半軸をβ・半径に結び付ける。',
        'gq': '一つの出来事に明示的に割り当てた四座標が、与えた世界管の条件を満たす。別の出来事の座標で代用しない。',
        'gr': '同じ座標系・文脈・単位・時刻で読んだ二つの出来事が、同じ世界管の幾何条件も満たす。',
        'gs': '二つの出来事が同じ物体等の出来事集合に属し、同時刻の読みと与えた世界管の形状条件が一致する。集合への所属と単なる座標上の一致は分ける。'})
    basis['unresolved'] += [
        '時間を固定した断面は座標系に依存する。異なる系で同時刻に選ぶ表面の出来事が同じ集合だとは仮定しない。',
        '世界管や時間不変の球面を数学的に記述しただけで、物質の剛性・構成・加速に対する応答を定義したとはしない。',
        '物体表面への出来事の所属はgmの集合引数に明示する。物体同一性や表面の物理的な一般定義は未完。',
        '光速ちょうどの有限β・正の縦半軸は定義域外。原文の極限の説明を、光速の物体について正則な変換が存在するという主張へ置き換えない。',
        '実切断の球面・半軸条件は記述したが、切断演算の一般法則による機械的な証明は未完。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def main():
    text, basis = composed()
    for name, body in {basis['document']: text, 'data/moving-shapes-basis-v1.json': json.dumps(basis, ensure_ascii=False, indent=2) + '\n'}.items():
        path = ROOT / name
        if path.exists():
            if path.read_text(encoding='utf-8') != body:
                raise ValueError('Stored moving shape differs: ' + name)
        else:
            with path.open('x', encoding='utf-8', newline='\n') as stream:
                stream.write(body)
    print('Moving sphere, simultaneous slices and frame-bound observations composed')


if __name__ == '__main__':
    main()
