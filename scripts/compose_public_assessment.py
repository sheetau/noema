"""Compose criterion failures and a publication intended for others' assessment."""
from copy import deepcopy
import json

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from scripts.compose_limits import ROOT

PARENT = 'examples/v014/kant-protected-speech.noema'


def definitions():
    return '''
d ret[subject a criteria j[h[a] e]] e[b context[
 q[v criteria][u[e[n p a b][n p a b]]][i[failed c criterion h[a] e][
  x[v failed][u[t[c[v criterion][v subject]][v context]]]
 ]]
]].
d reu[criteria j[h[a] e]] h[a] f[i[subject a][j s[k ret[v subject v criteria]]]].
d rev[criteria j[h[a] e]] h[a] f[i[subject a][j q[k ret[v subject v criteria]]]].
'''


MEANINGS = {
    'ret': '対象について、指定した達成条件の有限列の少なくとも一つがその状況で不成立であるという内容。満たすべき条件からの不足という限定した欠陥の捉え方。空列は欠陥ありとしない。',
    'reu': '同じ条件列についてretの不足があることを述べる主張の発話を、対象から返す。発話を作ることは、その内容の真理や話者の信念を認定することではない。',
    'rev': '同じ条件列についてretの不足があるか尋ねる質問の発話を、対象から返す。同じ内容を使う主張reuとは発話の働きが異なる。',
}
LIMITS = [
    '条件は既存のNoemaで定義した対象から内容への関数を列で渡す。文字列の語彙表や欠陥という基本記号で代用せず、対象・条件の組合せによって拡張する。',
    '条件列の採用が適切であること、列が必要な条件を尽くすこと、未達が道徳的非難に当たることはこの定義からは従わない。達成条件による欠陥の一つの操作的な読みであり、語義の全てではない。',
    '重複・順序を変えても不足の有無は変わらないが、条件列の記述自体の同一性は別である。条件を追加すれば、以前は不足なしだった対象が不足ありになる場合がある。',
    '条件の評価が未知なら評価を拒否し、不足または充足へ補わない。有限解釈器は全条件を評価するため、既に不足が判明した場合にも別条件が未知なら拒否する。',
]


def generic_composed():
    doc = parse('n:\n' + definitions())
    basis = {'version': 'criterion-failures-basis-v1', 'document': 'examples/v014/criterion-failures.noema',
             'primitives': [], 'definitions': MEANINGS, 'unresolved': LIMITS}
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def source_composed():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    basis = deepcopy(json.loads((ROOT / 'data/kant-protected-speech-basis-v1.json').read_text(encoding='utf-8')))
    statements, doc['statements'] = doc['statements'], []
    extra = definitions() + '''
r hzu[a a i[e] d] c.
r hzv[a a i[h[a] f] d] c.
d hzw[person a judgment a subject a description i[h[a] f] context d] c[
 w[k fa[v person v judgment v context]][w[k fb[v judgment v subject v context]][
  k hzv[v judgment v subject v description v context]
 ]]
].
d hzx[audience a subject a description i[h[a] f]] e[b context[
 g person a[w[k h6t[v audience v person v context]][g judgment a[
  k hzw[v person v judgment v subject v description v context]
 ]]]
]].
d hzy[person a activity a role a audience a channel a subject a description i[h[a] f] goal i[e] context d] c[
 w[k h6v[v person v activity v role v audience v channel v subject v description v context]][
  k hzu[v person v activity v goal v context]
 ]
].
'''
    doc = parse(format_graph(doc, 'compact') + extra)
    doc['statements'] = statements
    basis.update(version='kant-public-assessment-basis-v1', document='examples/v014/kant-public-assessment.noema')
    decls = {d['name']: d for d in doc['declarations']}
    for name, arguments, meaning in (
        ('hzu', ['actor', 'activity', 'goal_description', 'context'], '本人がその活動の計画・遂行で目指す目的内容の記述。活動自体の実行、目的の真理・達成、実現可能性は要求しない。目的の形成や意図の一般理論は未完。'),
        ('hzv', ['judgment', 'subject', 'message_description', 'context'], 'この判断が、この対象について指定された発話記述の内容を検討・評価する判断である。単に同じ話題の別内容を判断したことでは足りない。賛否・判断の正しさ・発話の真理を含まない。')):
        row = decls[name]
        basis['primitives'].append({'symbol': name, 'parameters': row['parameters'], 'result': row['result'],
            'arguments': arguments, 'meaning_ja': meaning})
    basis['definitions'].update(MEANINGS)
    basis['definitions'].update({
        'hzw': '同じ本人による実際の判断行為faを、対象fbと発話記述hzvへ結ぶ。別人の判断や、同じ話題の別の発話への判断を混ぜない。',
        'hzx': '指定の受け手群の少なくとも一人が、同じ対象と発話記述についてhzwの判断を行うという内容。全員の判断、賛同、正しい結論、発話の受領を要求しない。',
        'hzy': '同じ公的活動・受け手群・経路・対象・発話記述についてh6vが成立し、その本人が同じ活動で指定目的を目指す。公衆による判断の目的には、対応するhzxの閉じた記述を渡す。',
    })
    basis['unresolved'] += LIMITS + [
        '原文の軍務の欠陥への注記を、明示した条件の不充足を述べる発話として部分的に構成する。軍務の概念、具体的な評価条件、注記の議論・証拠・提案を尽くした記述は残る。',
        '公衆の判断へ示す目的をhzxの閉じた記述で与える読みを検査する。少なくとも一人の判断を目標内容とする部分的な読みであり、実際の全員の判断や賛同を要求する意味へ強めない。',
        'hzyは任意の目的記述を受け取る。検査作例でのみ、hzxの受け手群・対象・発話をh6vの同じ引数へ明示的に対応させる。別のgoalを渡すと別の目的になる。',
        'hzxの受け手群は、各評価状況における同じ集団のh6tによる構成員である。全状況で成員が固定していることは仮定しない。',
        '意図と判断対象の二つの基本関係を追加した。特定の言葉の置換表ではなく別分野にも使える意味規約だが、その認知過程の構成的説明と原文との完全な意味一致は未完。',
        '実際の提示・受領・理解・判断・真理は別条件である。目的や予定された公的活動を記述するだけで、それらが起きたとはしない。既存15件の本文主張を保持する。',
    ]
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def main():
    for builder, stem in ((generic_composed, 'criterion-failures'), (source_composed, 'kant-public-assessment')):
        text, basis = builder()
        for name, body in ((basis['document'], text), ('data/' + stem + '-basis-v1.json', json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            path = ROOT / name
            if path.exists():
                if path.read_text(encoding='utf-8') != body:
                    raise ValueError('Stored public assessment differs: ' + name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream:
                    stream.write(body)
    print('Criterion failures and a purpose of public assessment composed')


if __name__ == '__main__':
    main()
