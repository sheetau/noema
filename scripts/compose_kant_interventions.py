"""An explicit model-relative reading, kept separate from the general draft."""
import json
from pathlib import Path

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis

ROOT = Path(__file__).resolve().parents[1]


def composed():
    doc = parse((ROOT / 'examples/v012/kant-questions.noema').read_text(encoding='utf-8'))
    library = parse((ROOT / 'examples/v012/binary-interventions.noema').read_text(encoding='utf-8'))
    adapter = parse(format_graph(library, 'compact') + '''
r mp[d] h[a h[a] c] c.
r mq[h[a] e d] h[h[a] c h[a] c] c.
d mb[factor a topic h[a] e scene d] c[k sm[k mp[v scene] v factor k mq[v topic v scene]]].
d mc[factor a topic h[a] e scene d] c[k sl[k mp[v scene] v factor k mq[v topic v scene]]].
''')
    doc['declarations'] = adapter['declarations'] + [d for d in doc['declarations'] if d['name'] not in ('mb', 'mc')]
    text = format_graph(doc, 'compact') + '\n'
    basis = json.loads((ROOT / 'data/kant-question-basis-v1.json').read_text(encoding='utf-8'))
    math = json.loads((ROOT / 'data/binary-interventions-basis-v1.json').read_text(encoding='utf-8'))
    basis['version'] = 'kant-intervention-basis-v1'
    basis['document'] = 'examples/v012/kant-interventions.noema'
    basis['status'] = 'explicit_binary_model_reading_not_equivalent_to_general_source_claim'
    state = {'kind': 'function', 'parameters': ['individual'], 'result': 'truth'}
    equations = {'kind': 'function', 'parameters': ['individual', state], 'result': 'truth'}
    order = {'kind': 'function', 'parameters': [state, state], 'result': 'truth'}
    topic = {'kind': 'function', 'parameters': ['individual'], 'result': 'content'}
    basis['primitives'] = [p for p in basis['primitives'] if p['symbol'] not in ('mb', 'mc')]
    basis['primitives'] += [
        {'symbol': 'mp', 'parameters': ['situation'], 'result': equations, 'arguments': ['context'],
         'meaning_ja': '文脈で仮定する二値の構造方程式。各対象を変数の識別子として、割当てからその変数の値を定める機構を返す。制限を指す変数の真は適用、偽は不適用とする。介入の両側で同じ機構と背景を使う。現実の機構への適合は別の未検証仮定。'},
        {'symbol': 'mq', 'parameters': [topic, 'situation'], 'result': order, 'arguments': ['process_property', 'context'],
         'meaning_ja': '指定した過程の性質と文脈に対する進行の厳密比較。第一の割当てに比べ第二の割当てで進行が上位なら真。非反射的・推移的な比較として解釈し、同じ外延の性質を区別しない。進行の尺度と現実の過程との接続は明示すべき仮定であり、この宣言だけで完成した定義としない。'}]
    basis['definitions'].update(math['definitions'])
    basis['definitions'].update({
        'mb': '指定した二値モデルと進行比較において、制限を適用した全解が、不適用の全解より下位である。両側の解の存在が必要。一般の妨害の全語義より強い、明示的なモデル内の読み。',
        'mc': '指定した二値モデルと進行比較において、制限を適用した全解が、不適用の全解より上位である。両側の解の存在が必要。一般の促進の全語義より強い、明示的なモデル内の読み。'})
    basis['unresolved'] = [u for u in basis['unresolved'] if not u.startswith('妨げる・促す・自由の制限')]
    basis['unresolved'] += math['unresolved'] + [
        'この文書は介入比較による一つの強い読みであり、元の原文と同義な完成訳へ昇格させない。元の一般的な質問草案を保持する。',
        'mpの方程式とmqの尺度を、カントの社会的・歴史的な議論に適合させるための変数選択と意味説明が未完成。',
        '自由の制限ma自体の定義、確率的傾向、妨害や促進の程度、推量・強調、回答との談話的接続が残る。']
    audit_basis(parse(text), basis)
    return text, basis


def main():
    text, basis = composed()
    for name, body in {basis['document']: text, 'data/kant-intervention-basis-v1.json': json.dumps(basis, ensure_ascii=False, indent=2) + '\n'}.items():
        path = ROOT / name
        if path.exists():
            if path.read_text(encoding='utf-8') != body:
                raise ValueError('Stored intervention reading differs: ' + name)
        else:
            with path.open('x', encoding='utf-8', newline='\n') as stream:
                stream.write(body)
    print('Kant model-relative intervention reading composed; general source meaning not completed')


if __name__ == '__main__':
    main()
