"""Compose clock rates, elapsed readings and a quantified approximation error."""
from copy import deepcopy
import json
from pathlib import Path

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis

ROOT = Path(__file__).resolve().parents[1]
ALIASES = {'ca': 'ma', 'cb': 'mb', 'cc': 'mc', 'ce': 'me', 'ci': 'mi'}


def physical_definition():
    params = ('clock a first a last a place a lab a rest a scene d lengthunit a coordinateunit a dialunit a '
              'speed b light b beta b firstt b lastt b firsttau b lasttau b firstreading b lastreading b scale b offset b')
    clauses = ['u[e[v first][v last]]', 'k ma[v clock]', 'k mc[v clock v rest]',
               'k mb[v clock v place v rest]', 'k mb[v first v place v rest]', 'k mb[v last v place v rest]',
               'k mi[v coordinateunit]', 'k mi[v dialunit]', 'k pd[v lab v rest v scene]',
               'k pb[v lab v rest v scene v lengthunit v coordinateunit v speed]',
               'k pc[v lab v scene v lengthunit v coordinateunit v light]']
    for event in ('first', 'last'):
        clauses += [
            f'k pa[v {event} v lab v scene v lengthunit v coordinateunit v {event}t k ad[v speed v {event}t] n p a b n p a b]',
            f'k pa[v {event} v rest v scene v lengthunit v coordinateunit v {event}tau n p a b n p a b n p a b]',
            f'k me[v clock v {event} v rest v dialunit k bb[v {event}reading]]',
            f'k hk[v scale v offset v {event}tau v {event}reading]']
    clauses.append('k hd[v speed v light v beta v firstt v firsttau v lastt v lasttau]')
    body = clauses[-1]
    for clause in reversed(clauses[:-1]):
        body = 'w[' + clause + '][' + body + ']'
    return 'd hn[' + params + '] c[' + body + '].\n'


def composed():
    doc = parse((ROOT / 'examples/v011/einstein-moving-shapes.noema').read_text(encoding='utf-8'))
    physical = parse((ROOT / 'examples/v011/clock-protocol-extension.noema').read_text(encoding='utf-8'))
    for declaration in physical['declarations']:
        if declaration['kind'] == 'primitive' and declaration['name'] in ALIASES:
            item = deepcopy(declaration)
            item['name'] = ALIASES[item['name']]
            doc['declarations'].append(item)
    text = (format_graph(doc, 'compact') + '\n'
            + (ROOT / 'examples/fragments/moving-clocks.noema.inc').read_text(encoding='utf-8')
            + physical_definition())
    doc = parse(text)
    basis = json.loads((ROOT / 'data/moving-shapes-basis-v1.json').read_text(encoding='utf-8'))
    old = json.loads((ROOT / 'data/clock-physical-basis-v1.json').read_text(encoding='utf-8'))
    basis['version'] = 'moving-clocks-basis-v1'
    basis['document'] = 'examples/v011/einstein-moving-clocks.noema'
    for record in old['primitives']:
        if record['symbol'] in ALIASES:
            item = deepcopy(record)
            item['source_convention'] = 'clock-physical-basis-v1:' + item['symbol']
            item['symbol'] = ALIASES[item['symbol']]
            basis['primitives'].append(item)
    basis['definitions'].update({
        'ha': '光速未満の符号付き速度について、正の時計の進み率がrate²=1-(v/V)²を満たす。',
        'hb': '既存の正のβと、β*rate=1で結ばれる時計の進み率。',
        'hc': '動く座標系の空間原点にある出来事の四座標変換。静止系の位置x=v*t、y=z=0と、動く系の位置ξ=η=ζ=0を保持する。共通の座標原点時刻の設定である。',
        'hd': '同じ変換と原点世界線上の二つの出来事について、静止系で後者の時刻が厳密に後である条件。',
        'he': '非負の継続時間durationに対し、時計の経過elapsedがrate倍、遅れlostがduration-elapsedである。進み率はhaを満たす。',
        'hf': '正で1以下の進み率に対し、単位時間あたりの遅れが1-rateである。',
        'hg': '速度比の二乗s、正の進み率、単位時間の遅れ、s/2という近似と、その近似との差を同時に記述する。近似を等式で真の遅れと同一視しない。',
        'hh': 'sを(v/V)²へ結び付け、光速未満の範囲を保持する。',
        'hi': 'hhとhgを結び、原文の単位時間あたりの厳密値・二次近似・誤差を記述する。',
        'hj': '非負の継続時間を明示し、時計の経過・遅れ・近似した遅れ・近似誤差を同じ時間尺度へ換算する。',
        'hk': '正の尺度と任意の原点を持つ、座標時刻から時計の読みへの校正関係。',
        'hl': '実切断で、正のβの逆数を時計の進み率として指定する。',
        'hm': '実切断で、正で1以下の進み率と非負の継続時間から、経過と遅れを指定する。',
        'hn': '同じ時計が動く系の同じ場所に静止し、二つの出来事がその場所にあること、両座標系の読み、同じ時計・単位での指示、共通の尺度と原点による校正をhdへ結び付ける。物理的な世界線と時間尺度の一般定義は未完。'})
    basis['unresolved'] += [
        'ma/mb/mc/me/miは既存の時計・場所・静止・読み・単位の意味規約を衝突しない名前で再利用する。これらの物理的な一般定義は未完。',
        '同じ二出来事の校正条件だけから、時計が全時刻で理想的な時計として振る舞うとは結論しない。',
        'hnは共通の座標原点時刻の設定を用いるが、時計の指示の原点offsetと尺度scaleは明示して許す。別々の原点変更や単位の混在を無条件に相殺しない。',
        '折れ線・閉曲線に沿う運動、加速区間での時計の応答、地球上の時計の比較はまだ記述しない。',
        '実切断での進み率と差は記述したが、切断全域の法則と微分積分の機械的な証明は未完。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def main():
    text, basis = composed()
    for name, body in {basis['document']: text, 'data/moving-clocks-basis-v1.json': json.dumps(basis, ensure_ascii=False, indent=2) + '\n'}.items():
        path = ROOT / name
        if path.exists():
            if path.read_text(encoding='utf-8') != body:
                raise ValueError('Stored moving clocks differ: ' + name)
        else:
            with path.open('x', encoding='utf-8', newline='\n') as stream:
                stream.write(body)
    print('Clock rates, readings and approximation error composed')


if __name__ == '__main__':
    main()
