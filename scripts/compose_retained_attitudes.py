"""Reuse actual change and persistence for a newly acquired attitude."""
from copy import deepcopy
import json

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from scripts.compose_limits import ROOT
from scripts.compose_transitions import generic_composed as transitions

PARENT = 'examples/v014/kant-attempt-history.noema'


def definitions():
    return '''
d raf[history h[d] c before h[d d] c person a property h[a] e process a earlier d later d anchor d changes h[a d d] c affected h[a a d d] c] c[
 w[k th[v history v before v process v earlier v later v changes c[v property][v person]]][w[
  c[v affected][v person v process v earlier v later]
 ][w[c[v history][v anchor]][w[x[e[v later][v anchor]][c[v before][v later v anchor]]][
  f point d[y[w[c[v history][v point]][w[
   x[e[v later][v point]][c[v before][v later v point]]
  ][x[e[v point][v anchor]][c[v before][v point v anchor]]]]][t[c[v property][v person]][v point]]]
 ]]]]
].
'''


def generic_composed():
    text, previous = transitions()
    doc = parse(text)
    doc['declarations'] = [d for d in doc['declarations'] if d['name'] in ('ta', 'tg', 'th')]
    doc['statements'] = []
    doc = parse(format_graph(doc, 'compact') + definitions())
    basis = {'version': 'retained-attitudes-basis-v1', 'document': 'examples/v014/retained-attitudes.noema',
        'primitives': [], 'definitions': {name: previous['definitions'][name] for name in ('ta', 'tg', 'th')},
        'unresolved': [
            '指定された一つの履歴における取得と後の持続を表す。唯一の取得、過程内の連続性、原因の説明、未来の永続性は含めない。',
            '状態の偽は意味上の偽であり、記録の欠落ではない。履歴の実世界への接続と網羅性は別途必要である。',
            '状態の性質と変化過程の関係は引数で与える。態度以外の状態にも適用できるが、特定の機構を発見する手続きではない。']}
    basis['definitions']['raf'] = '同じ本人・性質・履歴の中で、実際の一つの過程が性質の不成立から成立への変化を結び、本人がその変化を受ける。その後端から基準状況まで性質が持続する。基準状況が履歴外、後端より前、途中で性質が失われた場合は成立しない。'
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def source_composed():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    statements, doc['statements'] = doc['statements'], []
    doc = parse(format_graph(doc, 'compact') + definitions() + '''
d h7[person a] e[b point[k id[v person r[p bf] v point]]].
d ha2[person a] e[b anchor[w[t[k bf[v person]][v anchor]][g process a[g earlier d[g later d[
 k raf[i[point d][k ia[v person v anchor v point]] i[first d second d][k ic[v first v second v anchor]]
  v person p h7 v process v earlier v later v anchor p ag p la]
]]]]]].
d hb2[person a] e[b context[w[t[k bf[v person]][v context]][t[k uy[v person]][v context]]]].
d hc2[person a] e[b context[w[t[k hb2[v person]][v context]][w[
 t[k ha2[v person]][v context]
][t[k h5[v person]][v context]]]]].
''')
    doc['statements'] = statements
    basis = deepcopy(json.loads((ROOT / 'data/kant-attempt-history-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-retained-attitudes-basis-v1', document='examples/v014/kant-retained-attitudes.noema')
    basis['definitions']['raf'] = generic_composed()[1]['definitions']['raf']
    basis['definitions'].update({
        'h7': '本人が既存の未成熟bfの記述に該当する自分の状態を好ましく受け入れている。idを再利用し、好ましさの成立だけからその状態の真理や能力を推定しない。',
        'ha2': '本人は現在bfにあり、同じ本人についてh7が不成立から成立する過程を経て、その後から現在までh7が持続している。lieb gewonnenの取得を、単なる現在の好みと区別する部分的な読み。',
        'hb2': '現在未成熟bfにある本人にとって、自立的な使用能力upへ向かう活動の負担uyが成立する。実際の離脱、達成方法の存在、自責的な原因bdは付け加えない。',
        'hc2': '第三段落の部分的な接続。同じ本人と文脈でhb2の困難、ha2の取得して持続する好み、h5の現在の能力不足と過去の許容不在による説明を結ぶ。愛着を能力不足の別の原因として補わない。'})
    basis['unresolved'] += generic_composed()[1]['unresolved'] + [
        'liebの情緒的な愛着はidの好ましい受容だけでは尽くさない。sogarの強調、ほとんど本性となったという修飾、自然や習慣の一般説明も未完である。',
        '取得を、不成立の前状態から成立への実際の過程と、その後の持続で読む。原文が唯一の開始瞬間や連続的な心理変化を特定したとはしない。',
        'schwerは既存uyの活動負担による部分的な読みである。全手段が困難であること、成功不可能、低負担手段の単なる不在と同一視しない。',
        '本人の現在の未成熟bfを保持するが、原因の自責性bdは要求しない。一般化jeden einzelnen Menschen、alsoの推論、自己による作業の機構と程度はまだ接続しない。',
        'hc2は同じ本人の条件を結ぶ候補であり、新たな無条件の本文主張ではない。第三段落の全文意味確認は未完。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def main():
    for builder, name in ((generic_composed, 'retained-attitudes'), (source_composed, 'kant-retained-attitudes')):
        text, basis = builder()
        for path, body in ((ROOT / basis['document'], text),
                (ROOT / ('data/' + name + '-basis-v1.json'), json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            if path.exists():
                if path.read_text(encoding='utf-8') != body:
                    raise ValueError('Stored retained attitude differs: ' + str(path))
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream:
                    stream.write(body)
    print('Acquired attitude, persistence and difficult activity composed without new primitives')


if __name__ == '__main__':
    main()
