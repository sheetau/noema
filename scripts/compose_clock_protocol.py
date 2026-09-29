"""Compose the checked mathematical library and physical reading relationships."""
from pathlib import Path
import json

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / 'examples/v011/einstein-clock-protocol.noema'
BASIS = ROOT / 'data/clock-protocol-basis-v1.json'


def compose():
    real = parse((ROOT / 'examples/v011/real-cuts.noema').read_text(encoding='utf-8'))
    physical = parse((ROOT / 'examples/v011/clock-protocol-extension.noema').read_text(encoding='utf-8'))
    # Coordinate definitions refer to the real library, so parse after concatenation.
    coordinate = (ROOT / 'examples/fragments/clock-coordinate.noema.inc').read_text(encoding='utf-8')
    math = parse(format_graph(real, 'compact') + coordinate)
    physical_primitives = [d for d in physical['declarations'] if d['kind'] == 'primitive']
    physical_definitions = [d for d in physical['declarations'] if d['kind'] == 'definition']
    math['declarations'] = physical_primitives + math['declarations'] + physical_definitions
    combined = format_graph(math, 'compact') + '''
d db[clocka a clockb a placea a placeb a depart a reflect a arrive a ray a frame a unit a
     first h[b] c middle h[b] c last h[b] c] c[
  w[k da[v clocka v clockb v placea v placeb v depart v reflect v arrive v ray v frame v unit v first v middle v last]][
    w[k ba[v first]][w[k ba[v middle]][w[k ba[v last]][k bi[v first v middle v last]]]]
  ]
].
'''
    return format_graph(parse(combined), 'compact') + '\n'


def composed_basis():
    basis = json.loads((ROOT / 'data/real-cuts-basis-v1.json').read_text(encoding='utf-8'))
    physical = json.loads((ROOT / 'data/clock-physical-basis-v1.json').read_text(encoding='utf-8'))
    basis.update(version='clock-protocol-basis-v1', document=TARGET.relative_to(ROOT).as_posix(), status='partial_physical_semantic_conventions')
    basis['primitives'] = physical['primitives'] + basis['primitives']
    basis['definitions'].update(physical['definitions'])
    basis['definitions'].update({
        'bj': '正の有理数scaleによる切断の拡大。q<scale*xとなる元xが元の切断にある場合にqを含める。scaleが0以下なら空の性質となり、実数の切断条件を満たさない。',
        'bk': '正の尺度変更の後に切断offsetを加え、時刻座標を変換する。新しい読み=scale*古い読み+offsetという規約。',
        'db': 'daの一往復の設定にあり、三つの読みが実数の切断で、往路と復路の差が等しいという条件。一回の条件の成立だけで全時刻の時計同期を主張しない。'})
    basis['unresolved'] = physical['unresolved'] + [
        '物理的な単位の間の換算関係と、尺度変換の係数との接続。',
        '原文と全体として同義であることの確認、および原刊画像との照合。',
        '一般の実数全域での座標変換の法則の機械的証明。今回の自動証明は指定した正の倍率と有理数を埋め込んだ読み・原点に限る。']
    audit_basis(parse(compose()), basis)
    return basis


def main():
    text = compose()
    for path, body in ((TARGET, text), (BASIS, json.dumps(composed_basis(), ensure_ascii=False, indent=2) + '\n')):
        if path.exists():
            if path.read_text(encoding='utf-8') != body:
                raise ValueError('Stored clock protocol or basis differs')
        else:
            with path.open('x', encoding='utf-8', newline='\n') as stream:
                stream.write(body)
    print('Clock protocol reproduced; source equivalence remains partial')


if __name__ == '__main__':
    main()
