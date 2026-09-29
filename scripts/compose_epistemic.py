"""Compose description-sensitive attitudes and the still-undetermined phi draft."""
import json
from pathlib import Path

from noema.discourse import description_sort
from noema.grammar import parse, format_graph
from noema.language import convert
from noema.meaning_basis import audit_basis

ROOT = Path(__file__).resolve().parents[1]


def composed():
    fragment = (ROOT / 'examples/fragments/epistemic.noema.inc').read_text(encoding='utf-8')
    doc = parse('m:\n' + fragment)
    basis = {
        'version': 'epistemic-basis-v1', 'document': 'examples/v013/epistemic.noema',
        'primitives': [
            {'symbol': 'ra', 'parameters': ['individual', 'situation', 'situation'], 'result': 'truth',
             'arguments': ['agent', 'current_context', 'alternative'],
             'meaning_ja': '指定主体が指定文脈で排除していない候補状況。どの状況を候補にするかは解釈が明示する。反射性・推移性・対称性は自動で仮定しない。'},
            {'symbol': 'rb', 'parameters': ['individual', description_sort('content'), 'situation'], 'result': 'truth',
             'arguments': ['agent', 'description', 'context'],
             'meaning_ja': '主体がその文脈でこの記述を認識しているという明示的な関係。同じ命題内容を持つ別の記述を自動で認識したことにはしない。根拠の正当性や信頼性を意味しない。'}],
        'definitions': {
            'sa': '候補状況が少なくとも一つある。',
            'sb': '候補状況が空でなく、与えた命題内容が全候補で真となる。',
            'sc': '指定記述を明示的に評価して得た命題内容がsbを満たす。',
            'sd': '指定記述を認識しており、その内容が空でない全候補で真となる。実際の状況での真理はこれだけでは保証しない。',
            'se': '現在状況自体が候補に含まれ、sdを満たす。この条件は実際の真理を含むが、知識の一般的・十分な定義ではない。',
            'sf': '候補状況が空でなく、与えた命題内容が全候補で偽となる。',
            'sg': '候補が空でなく、真で決着も偽で決着もしていない。認識関係の欠如とは異なる。'},
        'unresolved': [
            '認識関係と候補状況を、証拠・推論・学習・記憶から構成する理論は未完。seをあらゆる文脈の知識の十分条件としない。',
            '式の記述は局所的な束縛変項名と有理数表記だけを正規化する。任意の意味上の同一視や自然言語の言い換えは行わない。',
            '引用対象は閉じた、脱引用を使わない式に限定する。se等の定義を隠して引用することも拒否する。知識についての知識を任意に引用する体系は未完。']}
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def einstein_composed():
    text, additions = composed()
    base = convert(parse((ROOT / 'examples/v011/einstein-coordinates.noema').read_text(encoding='utf-8')), '0.13')
    text = (format_graph(base, 'compact') + '\n' + text.split('\n', 1)[1]
            + (ROOT / 'examples/fragments/epistemic-phi.noema.inc').read_text(encoding='utf-8'))
    doc = parse(text)
    basis = json.loads((ROOT / 'data/coordinates-basis-v1.json').read_text(encoding='utf-8'))
    basis['version'] = 'einstein-epistemic-basis-v1'
    basis['document'] = 'examples/v013/einstein-epistemic.noema'
    basis['primitives'] += additions['primitives']
    basis['definitions'].update(additions['definitions'])
    basis['definitions'].update({
        'sq': '同じ主体・段階の二つの候補状況で、与えた速度におけるφ値が異なる。関数族familyの引数は状況、その結果は有理速度から有理値への関数。',
        'sp': 'ある有理速度でsqが成立し、候補の関数が少なくとも二通り残っている。これは関数の未決定性という読みであり、未知性全般の定義ではない。',
        'sr': '現在状況を含む全候補で、familyの関数が指定したNoema記述の関数と全有理速度にわたり一致する。式を認識していることや証明したことは含まない。',
        'su': '指定状況におけるfamilyのφを既存の非退化座標条件ehへ渡す。φ=1は補わず、原点定数・速度・単位の数値規約を保持する。'})
    basis['unresolved'] += additions['unresolved'] + [
        'vorläufigの段階依存をhereで区別するが、後続の導出によって候補が減ることをまだ本文の証明と接続していない。',
        'familyは同じ座標系・単位の規約を保持する局所的なパラメータ。単位変更や実切断の関数全域の未知性まで扱ったものではない。',
        '数学的に答えが一つでも本人が認識していない場合と、候補関数が複数ある場合は異なる。spだけで原文のunbekanntを完全に表したとはしない。',
        '有限検査でsqの具体的な速度は確認できるが、sp/srの全有理数の探索・比較は拒否する。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def main():
    for function, name in ((composed, 'data/epistemic-basis-v1.json'),
                           (einstein_composed, 'data/einstein-epistemic-basis-v1.json')):
        text, basis = function()
        for filename, body in {basis['document']: text, name: json.dumps(basis, ensure_ascii=False, indent=2) + '\n'}.items():
            path = ROOT / filename
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists():
                if path.read_text(encoding='utf-8') != body:
                    raise ValueError('Stored epistemic draft differs: ' + filename)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream:
                    stream.write(body)
    print('Descriptions, explicit awareness and phi alternatives composed')


if __name__ == '__main__':
    main()
