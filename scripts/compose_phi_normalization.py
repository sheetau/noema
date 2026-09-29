"""Compose explicit reciprocity, rod-length symmetry and sign conditions."""
import json
from pathlib import Path

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis

ROOT = Path(__file__).resolve().parents[1]


def composed():
    text = (ROOT / 'examples/v011/einstein-coordinates.noema').read_text(encoding='utf-8')
    text += (ROOT / 'examples/fragments/phi-normalization.noema.inc').read_text(encoding='utf-8')
    doc = parse(text)
    basis = json.loads((ROOT / 'data/coordinates-basis-v1.json').read_text(encoding='utf-8'))
    basis['version'] = 'phi-normalization-basis-v1'
    basis['document'] = 'examples/v011/einstein-phi-normalization.noema'
    basis['definitions'].update({
        'fa': '正負の速度でのφ値の積が1であるという往復条件。速度反転による関数値の同一性は含まない。',
        'fb': '正負の速度でのφ値が等しいという対称条件。',
        'fc': '同じ棒の固有長と正負の運動で測る横方向の長さが正で、φ値との積が固有長になり、二つの測定長が等しい。原文の長さl/φを正の長さとして読む符号規約を明示する。',
        'fd': '往復条件fa、対称条件fb、正のφ値を合わせる。三条件を暗黙に混同しない。',
        'fe': '往復条件と、同じ正の棒の長さに関する対称条件fcを合わせる。',
        'ff': '入力の四座標に共通の倍率を掛けた結果が、出力四座標である。',
        'fg': '共通原点・原点時刻の設定で、速度speedの変換と逆速度の変換を続けて適用する。二方向のβの一致はcmの正の枝と速度反転対称性による。φの二値は独立した引数。',
        'fh': 'φが1と定まった場合の四座標変換。前提を満たさないφを自動で1にする操作ではない。',
        'fi': '実切断で、二つの有効なφ値が相反的かつ等しく、正であるという条件。切断の乗法cdと順序bgを参照する。',
        'fj': '実切断で、同じ正の棒の長さ、二つの正の測定長、往復条件と長さの対称条件を記述する。',
        'fk': 'φが非零で、動く座標系ではξ=0、η=proper、ζ=0となる棒の端点を、静止系の座標と四式で結ぶ。proper=0の場合はもう一方の端点にも使える。',
        'fm': '同じ関数φのspeedと逆速度での値にfdを適用する。二つの独立した関数を使わない。',
        'fn': '実切断の速度と、その符号反転での同じ関数の値にfiを適用する。',
        'fo': '正の光速度と、絶対値がそれより小さい全有理速度についてfmを要求する。有限個の速度だけで全域と扱わない。'})
    basis['unresolved'] += [
        '原文のKとK′が相対的に静止することだけから、共通の単位・原点・軸方向まで一致する恒等変換を導くことはしない。恒等性を採用する物理的設定の説明は別に必要。',
        '原文のl/φを正の長さとする規約をfc/feで明示した。絶対値l/|φ|だけならφ=-1も除外できず、軸の向きや連続性など追加の条件が必要となる。',
        'φの点ごとの代数的制約を検証する。全速度・全出来事への適用範囲、原文の棒・軸・慣性系の設定への帰属と一般的定義は未完。',
        'fi/fjは実切断での記述。切断の一般法則からφ=1を導く機械的証明を今回完成させたものではない。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def main():
    text, basis = composed()
    for name, body in {basis['document']: text, 'data/phi-normalization-basis-v1.json': json.dumps(basis, ensure_ascii=False, indent=2) + '\n'}.items():
        path = ROOT / name
        if path.exists():
            if path.read_text(encoding='utf-8') != body:
                raise ValueError('Stored phi normalization differs: ' + name)
        else:
            with path.open('x', encoding='utf-8', newline='\n') as stream:
                stream.write(body)
    print('Reciprocity, transverse lengths and phi sign conditions composed')


if __name__ == '__main__':
    main()
