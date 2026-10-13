"""Connect an actual agent's work to an attained change, without eternal success."""
from copy import deepcopy
import json

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from scripts.compose_limits import ROOT, v, app, op, both, call, definition
from scripts.compose_transitions import generic_composed as transitions

PARENT = 'examples/v014/kant-scoped-counts.noema'


def definitions():
    params = ('history h[d] c before h[d d] c person a process a earlier d later d prior e goal e description i[h[a] e] '
        'changes h[a d d] c affected h[a a d d] c occurs h[a d] c agent h[a a d] c work h[a a d] c produces h[a a i[h[a] e] d] c')
    return definition('rcp', params, both(
        call('tg', *[v(n) for n in ('history', 'before', 'process', 'earlier', 'later', 'changes')]),
        app(v('affected'), *[v(n) for n in ('person', 'process', 'earlier', 'later')]),
        op('t', v('prior'), v('earlier')), op('u', op('t', v('prior'), v('later'))),
        op('u', op('t', v('goal'), v('earlier'))), op('t', v('goal'), v('later')),
        app(v('occurs'), v('process'), v('later')),
        app(v('agent'), v('person'), v('process'), v('later')),
        app(v('work'), v('person'), v('process'), v('later')),
        app(v('produces'), v('process'), v('person'), v('description'), v('later'))))


def generic_composed():
    text, parent = transitions()
    doc = parse(text)
    doc['declarations'] = [d for d in doc['declarations'] if d['name'] in ('ta', 'tg')]
    doc['statements'] = []
    doc = parse(format_graph(doc, 'compact') + definitions())
    basis = {'version': 'self-achievement-basis-v1', 'document': 'examples/v014/self-achievement.noema', 'primitives': [],
        'definitions': {name: parent['definitions'][name] for name in ('ta', 'tg')},
        'unresolved': [
            '前状態・目標・活動内容と結果生成関係は引数で与える。descriptionは同じ本人へのgoalの記述であるという接続規約を呼出側で保持する。順序だけから因果を導かない。',
            '変化過程を本人の活動過程へ同定する粒度の構成であり、途中の全ての部分活動や認知機構を記述し終えたものではない。後端で活動の生起を記録するが、瞬間的な作業とは限らない。',
            '本人の関与は要求するが、他者の援助や他の原因を排除しない。意図・負担の量・方法の合理性・後の永続性・他場面での再現性を追加しない。']}
    basis['definitions']['rcp'] = '同じ履歴の前後を結ぶ同じ過程が本人に作用し、前状態は成立から不成立へ、目標は不成立から成立へ変わる。本人が関与するその同じ活動過程が指定した作業であり、同じ本人に記述された目標を生じさせる。単なる後状態や無関係な作業の共存では成立しない。'
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def source_composed():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    statements, doc['statements'] = doc['statements'], []
    extra = '''r h4m[a a d] c.r h4n[a a a d] c.
d h4l[person a] e[b point[w[t[k fo[v person]][v point]][t[k up[v person]][v point]]]].
d h4o[person a act a point d] c[g part a[w[k h4m[v part v person v point]][k h4n[v person v part v act v point]]]].
d h4p[person a process a earlier d later d anchor d] c[
 w[k ia[v person v anchor v anchor]][w[x[e[v later][v anchor]][k ic[v later v anchor v anchor]]][
  k rcp[i[point d][k ia[v person v anchor v point]] i[first d last d][k ic[v first v last v anchor]]
   v person v process v earlier v later k bf[v person] k h4l[v person] r[p h4l] p ag p la p dg p df p h4o p g3]
 ]]
].
d h4q[person a] e[b anchor[g process a[g earlier d[g later d[k h4p[v person v process v earlier v later v anchor]]]]]].
d h4t[person a anchor d] c[w[k ia[v person v anchor v anchor]][w[
 k ta[i[point d][k ia[v person v anchor v point]] i[first d last d][k ic[v first v last v anchor]]]
][f point d[y[w[k ia[v person v anchor v point]][x[e[v point][v anchor]][k ic[v point v anchor v anchor]]]][t[k fo[v person]][v point]]]]]].
d h4u[context d] c[f person a[y[w[k aa[v person]][k h4i[v person v context]]][x[t[k h4q[v person]][v context]][k h4t[v person v context]]]]].
d h4r[population j[a] context d] c[w[k h4u[v context]][k h4j[v population p h4q v context]]].
d h4s[population j[a] context d] c[w[k h4u[v context]][k h4k[v population p h4q v context]]].
'''
    doc = parse(format_graph(doc, 'compact') + definitions() + extra)
    doc['statements'] = statements
    basis = deepcopy(json.loads((ROOT / 'data/kant-scoped-counts-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-self-achievement-basis-v1', document='examples/v014/kant-self-achievement.noema')
    generic = generic_composed()[1]
    basis['definitions']['rcp'] = generic['definitions']['rcp']
    decls = {d['name']: d for d in doc['declarations']}
    for name, arguments, meaning in (
        ('h4m', ['part', 'person', 'point'], 'この人の精神的な営みを構成する、考え方・判断の習慣・認知的な働きなどの一部分。物理的な脳器官や任意の所有物とは区別する。Geistの全語義と精神の構成理論は未完。'),
        ('h4n', ['person', 'part', 'act', 'point'], '本人がこの活動で、その精神的な部分のあり方を吟味し、組み直すように働きかける。改善の成功や自立の達成は含意せず、単なる既存の能力の使用とも区別する。活動内部の方法・努力量・反復は未確定。')):
        d = decls[name]
        basis['primitives'].append({'symbol': name, 'parameters': d['parameters'], 'result': d['result'],
            'arguments': arguments, 'meaning_ja': meaning})
    basis['definitions'].update({
        'h4l': '本人について、全利用可能方法の評価範囲が整合するfoと、他者の指導なしで自分の理解力を使う達成方法を持つupがともに成立する。bfの単なる否定ではなく、肯定的な達成方法を要求する。',
        'h4o': '本人の精神的な部分h4mがあり、同じ本人が同じ活動でその同じ部分へh4nの働きかけを行う。他人の精神への作業を混ぜない。',
        'h4p': '本人の実際の同じ履歴で、基準時までに、本人の精神への働きかけによるrcpの過程があり、bfからh4lへ変わった。結果生成は既存g3へ接続する。未来の成功を完了済みとして数えない。',
        'h4q': '基準時までにh4pを満たす過程があるという、達成経験を持つ人の候補。現在も能力を保つこと、同じことを常にできること、確かな歩みの条件はまだ要求しない。',
        'h4t': '本人の同じ順序付き履歴に基準時が属し、その基準時までの全状況で、能力評価の整合性foが成立する。評価対象の欠落を過去の不成功として数えることを防ぐ条件。未来の評価までは要求しない。',
        'h4u': 'この基準文脈の全対象者について、有効な成功例h4qを既に持つか、h4tの全履歴の能力評価条件を要求する。肯定には有効な一例で足り、成功例のない対象者の評価欠落を不成功へ変換しない。',
        'h4r': 'h4uの評価条件の下で、この文脈の全対象者についてh4qを持つ人数をh4jの上限条件へ接続した候補。該当者がゼロの場合も許す。',
        'h4s': 'h4uの評価条件の下で、同じ全対象者とh4qについて、少なくとも一人いるh4kの上限条件へ接続した候補。原文の確かな歩みを追加していないので、原文の最終的な少数者の主張ではない。'})
    basis['unresolved'] += generic['unresolved'] + [
        'denen es gelungen istからUnmündigkeit heraus zu wikkelnまでの部分的な達成条件。精神の自己形成、成功の機構・程度、努力の全語義、身体的な解放の比喩は未完。',
        'h4lは既存の能力評価に依存する。評価する方法と結果の選び方が現実に正当かは別途必要であり、抽象的な成功判定器だけで原文の自立を完全に説明したとはしない。',
        'h4t・h4uは宣言された履歴と利用可能方法の評価範囲の整合性を検査する。現実の全履歴・全方法・自己活動・結果生成の知識が完全であることの証明ではなく、未観測の出来事を偽にしてよい規則でもない。',
        '後続の確かな歩みとdennochの譲歩が未接続なので、h4r・h4sをカントの少数者の主張として帰属させない。現在の不保持が過去の成功を消すという条件も加えない。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def main():
    for builder, stem in ((generic_composed, 'self-achievement'), (source_composed, 'kant-self-achievement')):
        text, basis = builder()
        for path, body in ((ROOT / basis['document'], text), (ROOT / ('data/' + stem + '-basis-v1.json'),
                json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            if path.exists():
                if path.read_text(encoding='utf-8') != body:
                    raise ValueError('Stored self achievement differs')
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream:
                    stream.write(body)
    print('Actual self work, attained change and historical achievers composed')


if __name__ == '__main__':
    main()
