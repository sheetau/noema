"""Compose graded adverse prospects and non-factive, description-sensitive judgments."""
from copy import deepcopy
import json

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from scripts.compose_limits import ROOT


def definitions():
    return '''
d rl[person a activity i[h[a] e] context d prospects h[a i[h[a] e] d d] c adverse h[a d] c] c[
 g outcome d[w[c[v prospects][v person v activity v context v outcome]][c[v adverse][v person v outcome]]]
].
d rm[person a activity i[h[a] e] context d prospects h[a i[h[a] e] d d] c adverse h[a d] c degree h[a i[h[a] e] d] a standard h[a d] c] c[
 w[k rl[v person v activity v context v prospects v adverse]][c[v standard][c[v degree][v person v activity v context] v context]]
].
d rn[person a property h[a] e context d candidates h[a d d] c] c[
 w[g scene d[c[v candidates][v person v context v scene]]][
  f scene d[y[c[v candidates][v person v context v scene]][t[c[v property][v person]][v scene]]]
 ]
].
'''


def generic_composed():
    doc = parse('n:\n' + definitions())
    basis = {'version': 'described-appraisals-basis-v1',
        'document': 'examples/v014/described-appraisals.noema', 'primitives': [],
        'definitions': {
            'rl': '本人が記述された活動を行う場合の可能な結果のうち、本人にとって不利益となるものがある。同じ本人・活動の記述・評価文脈・結果を結ぶ。現実の実行や不利益の発生は要求しない。',
            'rm': 'rlを満たし、同じ本人・活動・文脈の危険の程度が、その文脈の指定基準に入る。程度は個体型の尺度値であり、確率や損失額への数値化、特定の閾値を要求しない。',
            'rn': '本人と文脈について採用された判断候補が非空で、全候補において本人の性質が成立する。実際の文脈が候補に含まれることは要求しない。空の候補を肯定判断として扱わない。'},
        'unresolved': [
            '可能な結果、不利益、危険の程度と基準、判断候補の選定は引数による意味規約である。不利益の可能性だけから高危険度を導かない。尺度の算定法、確率、意思決定理論全体は未定義である。',
            'rnは候補による内容の評価条件であり、認識された記述を単独では保持しない。記述への認識・候補の選定と組み合わせる場合、同じ性質を明示的に渡す。論理的全知や矛盾した信念の一般理論ではない。']}
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def source_composed():
    doc = parse((ROOT / 'examples/v014/kant-state-convenience.noema').read_text(encoding='utf-8'))
    statements, doc['statements'] = doc['statements'], []
    text = format_graph(doc, 'compact') + definitions() + '''
r uq[a i[h[a] e] d d] c.r ur[a d] c.r us[a i[h[a] e] d] a.r ut[a d] c.
r uu[a i[h[a] e] d] b.r uv[b d] c.
r u2[a i[h[a] e] d d] c.r u3[a i[h[a] e] d] c.r u4[b d] c.
d up[person a] e[b scene[w[k aa[v person]][k xd[v person k bb[v person] v scene p ae p af p ap]]]].
d uw[person a] e[b context[k rm[v person r[p up] v context p uq p ur p us p ut]]].
d ux[person a] e[b context[w[k u3[v person r[p uw] v context]][
 k rn[v person p uw v context i[who a here d there d][k u2[v who r[p uw] v here v there]]]
]]].
d uy[person a] e[b context[k uv[k uu[v person r[p up] v context] v context]]].
d uz[person a] e[b context[w[t[k uy[v person]][v context]][t[k ux[v person]][v context]]]].
d u5[population j[a]] e[b context[
 w[k hr[v population v context]][
  w[k pd[v population p aa i[person a][t[k uz[v person]][v context]] i[ratio b][k u4[v ratio v context]]]][
   k hc[n p b c k pb[v population i[person a][t[k uz[v person]][v context]]]]
  ]
 ]
]].
'''
    doc = parse(text)
    doc['statements'] = statements
    basis = deepcopy(json.loads((ROOT / 'data/kant-state-convenience-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-described-appraisals-basis-v1',
                 document='examples/v014/kant-described-appraisals.noema')
    basis['definitions'].update(generic_composed()[1]['definitions'])
    decls = {d['name']: d for d in doc['declarations']}
    for name, args, meaning in (
        ('uq', ['person', 'goal_description', 'context', 'outcome'], '本人が記述された状態へ向かう活動をする場合に可能な結果。成功した結果だけに限定せず、失敗や途中の不利益を含め得る。現実に活動を実行したことは主張しない。'),
        ('ur', ['person', 'outcome'], 'その結果が本人に不利益をもたらすという関係。何を不利益と評価するかは意味規約に含め、恐れていることや実際に起きたことと区別する。'),
        ('us', ['person', 'goal_description', 'context'], '本人がその状態へ向かう活動について、文脈ごとの危険の程度を尺度上の値として与える。原文にない数値や損失と確率の積は補わない。'),
        ('ut', ['degree', 'context'], '指定文脈において危険の尺度値が「非常に」に相当する基準に入る。具体的な閾値や尺度算定法は未確定。'),
        ('uu', ['person', 'goal_description', 'context'], '本人が記述された状態へ向かう活動をする場合の負担。達成したことや実行済みであることを含まない。既存の個別方法の負担ocとは、活動全体への評価を区別する。'),
        ('uv', ['burden', 'context'], '指定文脈で負担が骨の折れる水準にあるという基準。個別の数値を原文へ補わない。'),
        ('u2', ['person', 'property_description', 'context', 'candidate'], '本人がその記述された性質を判断する際に採用する候補状況。記述ごとに範囲を保持し、著者が可能とする結果uqと同一視しない。'),
        ('u3', ['person', 'property_description', 'context'], '本人がこの性質の記述を認識し、判断の対象としている。同じ真理値を持つ別の記述へ自動的に置き換えない。これ単独では肯定判断や真実を含まない。'),
        ('u4', ['ratio', 'context'], 'その文脈で、割合が「はるかに最大の部分」に当たる程度の大きさを持つという基準。u5で厳密な過半数も別途要求し、単なる過半数をこの強い表現と同一視しない。')):
        declaration = decls[name]
        basis['primitives'].append({'symbol': name, 'parameters': declaration['parameters'],
            'result': declaration['result'], 'arguments': args, 'meaning_ja': meaning})
    basis['definitions'].update({
        'up': '人が自分の理解力を他者の指導なしで使えるという達成状態。既存のbbとxdを再利用する。自責的な未成熟bdからの実際の移行beを、将来に向かう活動へ誤って要求しない。',
        'uw': 'upの状態へ向かう活動について、本人に不利益な可能結果があり、その危険の程度が非常に高いという文脈基準に入る内容。',
        'ux': '本人がuwという記述を認識し、その記述について採用した非空の判断候補でuwが成立する。性質参照・引用・候補選択には同じuwを渡す。実際の文脈でuwが成立することは主張しない。',
        'uy': 'upへ向かう活動の負担が、その文脈で骨の折れる水準にある内容。活動の実行と達成を要求しない。',
        'uz': '同じ本人と文脈について、負担uyが成立し、高危険度だという判断uxがある。負担を著者の挿入説明として読む草案であり、高危険度自体は著者の事実主張にしない。',
        'u5': '文脈での人々の母集団が完全・非空・重複なしで、そのうちuzを満たす割合が過半数を超え、さらに強い程度の基準u4を満たす内容。後見人による働きかけや挿入された女性集団の範囲はまだ接続しない。'})
    basis['unresolved'] += generic_composed()[1]['unresolved'] + [
        'Schritt zur Mündigkeitを、自立的に理解力を使える状態へ向かう活動として部分記述した。段階としての一歩、習慣的な自立、活動の範囲、尺度の説明は残る。',
        '負担の挿入句を著者の説明として読む。人々自身による負担の判断も含む読みや、auchの追加・焦点の扱いは確定していない。',
        '女性全体を含むという挿入句、後見人がこの判断を生じさせる主節、gütigstの皮肉と後続の比喩は未記述。この従属節の内容だけを新たな著者の独立断言として追加しない。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def main():
    for compose, name in ((generic_composed, 'data/described-appraisals-basis-v1.json'),
                          (source_composed, 'data/kant-described-appraisals-basis-v1.json')):
        text, basis = compose()
        for filename, body in ((basis['document'], text), (name, json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            path = ROOT / filename
            if path.exists():
                if path.read_text(encoding='utf-8') != body:
                    raise ValueError('Stored described appraisal differs: ' + filename)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream:
                    stream.write(body)
    print('Adverse prospects and non-factive judgments composed')


if __name__ == '__main__':
    main()
