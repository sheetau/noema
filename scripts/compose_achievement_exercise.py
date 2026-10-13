"""Join achieved change and exercised activity on one anchored history."""
from copy import deepcopy
import json

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from scripts.compose_limits import ROOT, v, app, op, both, definition, call
from scripts.compose_persistence import generic_composed as persistence

PARENT = 'examples/v014/kant-sustained-judgment.noema'


def definitions():
    params = ('history h[d] c before h[d d] c person a attained d completed d anchor d '
        'achievement h[a d d] c exercise h[a d d] c')
    member = lambda name: app(v('history'), v(name))
    at_most = lambda first, last: op('x', op('e', v(first), v(last)), app(v('before'), v(first), v(last)))
    return definition('rct', params, both(call('ta', v('history'), v('before')),
        member('attained'), member('completed'), member('anchor'),
        at_most('attained', 'completed'), at_most('completed', 'anchor'),
        app(v('achievement'), v('person'), v('attained'), v('anchor')),
        app(v('exercise'), v('person'), v('completed'), v('anchor'))))


MEANING = '同じ順序付き履歴に達成時点・活動完了点・基準時が属し、達成時点≦活動完了点≦基準時である。同じ人・同じ基準時に、指定時点での達成と活動完了が共に成立する。達成や活動の内部条件は引数の関係で定める。同時の完了を許し、時間順から因果を導かない。'
LIMITS = [
    'achievementとexerciseは、この同じhistory・beforeで評価した出来事を渡す意味規約である。一般形は関係の内部を検査しない。原文側では双方を同じia・ic・本人・基準時へ接続する。',
    '二つの完了点の順序を要求する構成であり、活動の開始が達成後であること、達成状態が間の全点で保持されること、同じ活動が達成を生じさせたこと、将来の再現性は導かない。',
    '達成と活動は一人について存在する別々の証拠でよい。同じ過程であることや異なる過程であることは要求しない。省略された時間関係を原文の唯一の読みとして固定する根拠にはしない。',
]


def generic_composed():
    text, parent = persistence()
    doc = parse(text)
    doc['declarations'] = [row for row in doc['declarations'] if row['name'] == 'ta']
    doc['statements'] = []
    doc = parse(format_graph(doc, 'compact') + definitions())
    basis = {'version': 'achievement-exercise-basis-v1', 'document': 'examples/v014/achievement-exercise.noema',
        'primitives': [], 'definitions': {'ta': parent['definitions']['ta'], 'rct': MEANING}, 'unresolved': LIMITS}
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def source_composed():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    statements, doc['statements'] = doc['statements'], []
    extra = '''
d h5h[person a attained d anchor d] c[g process a[g earlier d[k h4p[v person v process v earlier v attained v anchor]]]].
d h5i[person a completed d anchor d] c[g episode a[k h5d[v person v episode v completed v anchor]]].
d h5j[person a attained d completed d anchor d] c[
 k rct[i[point d][k ia[v person v anchor v point]] i[first d last d][k ic[v first v last v anchor]]
  v person v attained v completed v anchor p h5h p h5i]
].
d h5k[person a] e[b anchor[g attained d[g completed d[k h5j[v person v attained v completed v anchor]]]]].
d h5l[person a] e[b anchor[
 k jb[v person k h4q[v person] r[p h4q] k h5k[v person] v anchor
  i[subject a description i[h[a] e] context d alternative d][k ke[k wa[] v subject v description v context v alternative]]]
]].
'''
    doc = parse(format_graph(doc, 'compact') + definitions() + extra)
    doc['statements'] = statements
    basis = deepcopy(json.loads((ROOT / 'data/kant-sustained-judgment-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-achievement-exercise-basis-v1', document='examples/v014/kant-achievement-exercise.noema')
    basis['definitions'].update({
        'rct': MEANING,
        'h5h': '同じ本人・基準文脈で、指定達成点を終点とする自己活動による自立への変化h4pが存在する。達成点を後続の活動との接続のために公開する。',
        'h5i': '同じ本人・基準文脈で、指定完了点を持つ継続した独立判断の活動h5dが存在する。開始点や全過程の条件はh5dに保持する。',
        'h5j': 'h5hの自立達成とh5iの知的活動を、同じ本人のiaの履歴・icの順序でrctへ接続する。達成時点≦活動完了点≦基準時である。',
        'h5k': '同じ本人にh5jを満たす達成点と活動完了点があるという内容。過去のどこかに二つの経験があるだけではなく、完了点の時間順を要求する。',
        'h5l': '現実の基準文脈では同じ人のh4qとh5kが成立する一方、著者の視点でh4qを認めた通常予想の候補ではh4qが成立してh5kが成立しないというjbの譲歩候補。空の候補、前提を満たさない候補、結論も成立する候補では認定しない。'})
    basis['unresolved'] += LIMITS + [
        '完了点の順序は、自立を得て知的に進むという明示的な解釈である。原文の並列だけから厳密な非重複や因果は主張できないため、活動全体が達成後に始まる条件は加えない。',
        'h5lの前提は自己活動による自立達成h4q、結論はその時点以後に完了する知的活動を持つh5kとした。通常予想の候補は現実の過去時点とは別の比較状況であり、同じ人の達成経験を保持するが、同一の過程個体まで固定しない。',
        'jbの全候補で不成立という条件はdennochの一つの操作化であり、期待の確率・強さ・正当性や自然言語の全用法を尽くさない。候補の欠落や未評価を偽として埋めない。',
        '身体的な歩行の真理は接続していない。先行版h5gの比喩帰属と、h5k・h5lの対象側の条件を分ける。比喩の対応の全意味、知的安定性、自立の基礎定義は未完。',
        'この版では少数者の本文主張を追加しない。h4r・h4sは自立達成だけを数える旧候補なので、h5kへ無条件に流用しない。対象者の評価の完全性と存在含意、Daherの推論、全文の意味一致確認は残る。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def main():
    for builder, stem in ((generic_composed, 'achievement-exercise'), (source_composed, 'kant-achievement-exercise')):
        text, basis = builder()
        for path, body in ((ROOT / basis['document'], text), (ROOT / ('data/' + stem + '-basis-v1.json'),
                json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            if path.exists():
                if path.read_text(encoding='utf-8') != body:
                    raise ValueError('Stored achievement exercise differs')
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream:
                    stream.write(body)
    print('Achievement and exercised judgment joined with a nonliteral concession candidate')


if __name__ == '__main__':
    main()
