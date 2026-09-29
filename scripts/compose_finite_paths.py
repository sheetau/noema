"""Finite ordered path arithmetic with explicit per-segment ideal-clock premises."""
from copy import deepcopy
import json
from pathlib import Path

from noema.grammar import format_graph, parse
from noema.language import convert
from noema.meaning_basis import audit_basis

ROOT = Path(__file__).resolve().parents[1]


def composed():
    original = parse((ROOT / 'examples/v011/einstein-moving-clocks.noema').read_text(encoding='utf-8'))
    doc = convert(original, '0.14')
    text = (format_graph(doc, 'compact') + '\n'
            + (ROOT / 'examples/fragments/finite-paths.noema.inc').read_text(encoding='utf-8'))
    doc = parse(text)
    basis = deepcopy(json.loads((ROOT / 'data/moving-clocks-basis-v1.json').read_text(encoding='utf-8')))
    basis['version'] = 'finite-paths-basis-v1'
    basis['document'] = 'examples/v014/einstein-finite-paths.noema'
    basis['definitions'].update({
        'ia': '順序付き有限列の各出現について性質が真である。空列では真。同じ区間名が複数回現れれば各出現を処理する。',
        'ib': '有限列の各出現に与えた有理数値を、先頭から加算する。空列の合計は0。',
        'ic': '区間ごとの継続時間と進み率の積を加算する。入力値そのものの物理的な妥当性は主張しない。',
        'id': '列が空でなく、全区間の継続時間が正で、同じ正の光速に対して各速度と正の進み率がhaを満たす。',
        'ie': 'idの条件のもとで、全継続時間、区間の時間と進み率の積の和、両者の差を指定する。加速点での時計応答を導出する定義ではない。',
        'if': '最初の区間の始点が指定した出発点で、各区間の終点が次の始点と等しく、最後の終点が指定した到着点である。空列は出発点と到着点が等しい場合だけ成立。',
        'ig': '同じ出発点へ戻る接続した有限列が、ieの正の区間時間と時計の合計条件を満たす。幾何学的な速度・長さや加速点での時計の法則までは指定しない。',
        'ih': '列のすべての出現に対して、与えた数値関数が共通値に等しい。空列では真。'})
    basis['unresolved'].append(
        '今回の有限列は折れ線経路の接続と時間集計の部分草案である。旧版の未解決欄は継承した記録として保つ。'
        '速度と幾何学的な変位の結合、同じ時計・基準系・時間単位・連続した指示、'
        '加速点で区間法則を採用する根拠、滑らかな曲線への極限、地球上の時計は未完。')
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def main():
    text, basis = composed()
    for relative, body in {basis['document']: text,
                           'data/finite-paths-basis-v1.json': json.dumps(basis, ensure_ascii=False, indent=2) + '\n'}.items():
        path = ROOT / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            if path.read_text(encoding='utf-8') != body:
                raise ValueError('Stored finite path document differs: ' + relative)
        else:
            with path.open('x', encoding='utf-8', newline='\n') as stream:
                stream.write(body)
    print('Finite paths composed; no claim of acceleration physics or full source coverage')


if __name__ == '__main__':
    main()
