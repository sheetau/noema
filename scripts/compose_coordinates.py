"""Compose the source's four coordinate equations and explicit observations."""
import json
from pathlib import Path

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis

ROOT = Path(__file__).resolve().parents[1]


def composed():
    text = (ROOT / 'examples/v011/quantities.noema').read_text(encoding='utf-8')
    for fragment in ('coordinate-transform', 'coordinate-observations'):
        text += (ROOT / ('examples/fragments/' + fragment + '.noema.inc')).read_text(encoding='utf-8')
    doc = parse(text)
    basis = json.loads((ROOT / 'data/quantities-basis-v1.json').read_text(encoding='utf-8'))
    basis['version'] = 'coordinates-basis-v1'
    basis['document'] = 'examples/v011/einstein-coordinates.noema'
    dim = {'kind': 'function', 'parameters': ['individual'], 'result': 'number'}
    phi = {'kind': 'function', 'parameters': ['number'], 'result': 'number'}
    records = [
        ('pa', ['individual', 'individual', 'situation', 'individual', 'individual'] + ['number'] * 4,
         ['event', 'frame', 'context', 'length_unit', 'time_unit', 'time', 'x', 'y', 'z'],
         '指定文脈で、同じ出来事に指定基準系の時空座標を割り当てる関係。時刻は時間単位、三位置座標は長さ単位の読み。読みがない場合に座標を補わない。測定・座標系・出来事の一般的な定義は未完。'),
        ('pb', ['individual', 'individual', 'situation', 'individual', 'individual', 'number'],
         ['from_frame', 'to_frame', 'context', 'length_unit', 'time_unit', 'speed'],
         'to_frameがfrom_frameに対して正負付きの速度speedで動く関係。向きはfrom_frameのx軸、数値単位はlength_unit/time_unit。順序の逆転を暗黙に同一視しない。'),
        ('pc', ['individual', 'situation', 'individual', 'individual', 'number'],
         ['frame', 'context', 'length_unit', 'time_unit', 'light_speed'],
         '指定基準系と文脈における光速度の読み。単位はlength_unit/time_unit。変換後にも同じ速度になることをこの基本関係だけで前提にしない。'),
        ('pd', ['individual', 'individual', 'situation'], ['from_frame', 'to_frame', 'context'],
         '二つの慣性座標系の軸が標準の平行配置にあり、相対運動がx軸に沿うという設定。共通の原点やφ=1はこの関係から補わない。慣性系や方向の物理的な定義は未完。'),
        ('pe', ['individual', dim, 'number'], ['unit', 'dimension', 'scale'],
         '単位が指定次元と正の有理数の基準尺度を持つという意味規約。宣言した単位の実現や校正を説明したことにはしない。'),
        ('pf', ['individual', 'individual', 'situation', 'individual', 'individual', phi] + ['number'] * 4,
         ['from_frame', 'to_frame', 'context', 'length_unit', 'time_unit', 'phi', 'time_offset', 'x_offset', 'y_offset', 'z_offset'],
         '指定した二座標系・文脈・単位表記に対して、未確定な速度の関数φと四つの原点定数を変換のパラメータとして採用する関係。φの引数はlength_unit/time_unitでの速度の読み、原点定数は対応する座標単位の読み。φを自動的に1、原点定数を0にはしない。解釈は関数の外延に従う。')]
    basis['primitives'] += [{'symbol': s, 'parameters': p, 'result': 'truth', 'arguments': a, 'meaning_ja': m} for s, p, a, m in records]
    basis['definitions'].update({
        'ea': '有理数について原文M0135の四式とβ条件cmを合わせる。時間式はlightが正なので分母を払ってlight²*tau=phi*beta*(light²*t−speed*x)とする。φ値は任意の引数であり1とはしない。',
        'eb': '速度を引数に取る関数φを明示し、そのspeedでの値をeaに渡す。',
        'ec': '出力座標からそれぞれの原点定数を引いてebを適用する。四つの定数は独立した引数であり、時空座標へ一律に同じ定数を足す規約ではない。',
        'ed': '実切断について四式を記述する。各切断が有効で、βがclを満たすことを要求する。',
        'ee': '実切断の速度から実切断のφ値を得る関数を明示してedを適用する。',
        'ef': '実切断の四つの原点定数を明示してeeを適用する。原点定数自体も有効な切断でなければならない。',
        'eh': '有理数の座標変換として、ecに加えφ(speed)が非零であることを要求する。式が全ての出来事を一点へ潰す退化を座標変換とは数えない。',
        'eg': '同一の出来事・文脈について、二基準系の座標の読み、相対速度、光速度、標準配置、明示した単位と次元、φと原点定数のパラメータ、非退化の四式を結び付ける。全出来事に成り立つ変換であるという全称命題は別に必要。'})
    basis['unresolved'] += [
        '原文M0135の四式とu0085の関数・原点定数の部分記述であり、導出の談話や、後にφ=1を示す議論は未記述。',
        '慣性系、標準配置、測定、出来事、単位の実現と変換パラメータを共通の基礎概念から定義する作業。',
        'egの観測との接続は有理数の読みだけ。実数の式ed/ee/efとの観測接続と一般法則の機械的証明は未完。',
        '一出来事の座標の整合だけから、全出来事の変換や慣性系の全域的な座標の一意性を結論しない。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def main():
    text, basis = composed()
    for name, body in {basis['document']: text, 'data/coordinates-basis-v1.json': json.dumps(basis, ensure_ascii=False, indent=2) + '\n'}.items():
        path = ROOT / name
        if path.exists():
            if path.read_text(encoding='utf-8') != body:
                raise ValueError('Stored coordinates differ: ' + name)
        else:
            with path.open('x', encoding='utf-8', newline='\n') as stream:
                stream.write(body)
    print('Four coordinate equations, phi, origins and observations composed')


if __name__ == '__main__':
    main()
