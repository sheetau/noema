"""Bind a presentation's senders, recipients, subjects and message description."""
from copy import deepcopy
import json

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from scripts.compose_limits import ROOT


def definitions():
    return '''
d r2[senders h[a] c audience h[a] c subject h[a] a description i[h[a] f] context d occurs h[a d] c presents h[a a d] c conveys h[a a a i[h[a] f] d] c] c[
 w[g sender a[c[v senders][v sender]]][w[g recipient a[c[v audience][v recipient]]][
  g act a[w[c[v occurs][v act v context]][w[
   f sender a[y[c[v senders][v sender]][c[v presents][v sender v act v context]]]
  ][f recipient a[y[c[v audience][v recipient]][
   c[v conveys][v act v recipient c[v subject][v recipient] v description v context]
  ]]]]
 ]]]
].
d r3[context d before h[d d] c prerequisite h[d] c] c[
 g earlier d[w[u[e[v earlier][v context]]][w[c[v before][v earlier v context]][c[v prerequisite][v earlier]]]]
].
'''


def generic_composed():
    doc = parse('n:\n' + definitions())
    basis = {'version': 'directed-presentations-basis-v1',
        'document': 'examples/v014/directed-presentations.noema', 'primitives': [],
        'definitions': {
            'r2': '非空の提示者群と受け手群について、実際に生じる同じ提示行為で、各提示者が示す側となり、各受け手に、その受け手へ対応付けられた対象についての同じ発話記述を提示する。記述の内容は実行評価しない。',
            'r3': '現在とは異なる先行状況があり、同じ先行状況が時間的な前後関係と指定前提の両方を満たす。前提が現在や無関係な後続状況で成立するだけでは足りない。'},
        'unresolved': [
            'r2の一つの提示行為は部分行為を持ち得る。各提示者が各受け手に個別に発話したことや、受け手が理解・受容したことは含まない。',
            '発話の記述は対象から発話への閉じた関数を指す。受け手と対象の対応は引数で明示する。提示したことから内容の真理や立証、強制、話者の誠実さを推論しない。',
            '示す側の役割、記述の提示、時間の前後は引数の意味規約であり、伝達媒体・証拠の十分性・時刻の具体値を確定しない。']}
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def source_composed():
    doc = parse((ROOT / 'examples/v014/kant-scoped-interventions.noema').read_text(encoding='utf-8'))
    statements, doc['statements'] = doc['statements'], []
    text = format_graph(doc, 'compact') + definitions() + '''
r f2[a a a i[h[a] f] d] c.r f3[a a d] c.r f4[a d d] c.
d et[person a] e[b context[k rl[v person r[p up] v context p uq p ur]]].
d eu[person a] e[b context[k rc[v person p ej p et i[scene d][k f4[v person v context v scene]]]]].
d ev[person a] f[j s[k eu[v person]]].
d e2[person a] e[b context[k re[v person p ej i[scene d][k f4[v person v context v scene]]]]].
d ew[group a] e[b context[
 w[k hi[k mp[v group] p aa]][w[k hi[k mp[k mv[]] p aa]][
  k r2[i[sender a][k hg[k mp[v group] v sender]] i[recipient a][k dj[v recipient v context]]
   i[recipient a][v recipient] r[p ev] v context p dg p f3 p f2]
 ]]
]].
d ex[group a] e[b context[w[t[k ew[v group]][v context]][
 k r3[v context p dd i[earlier d][w[g person a[k dj[v person v context]]][
  f person a[y[k dj[v person v context]][t[k er[v group v person]][v earlier]]]
 ]]]
]]].
d e3[person a] e[b context[w[t[k et[v person]][v context]][u[t[k uw[v person]][v context]]]]].
d e4[] e[b context[w[g person a[k dj[v person v context]]][
 f person a[y[k dj[v person v context]][t[k e3[v person]][v context]]]
]]].
'''
    doc = parse(text)
    doc['statements'] = statements
    basis = deepcopy(json.loads((ROOT / 'data/kant-scoped-interventions-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-directed-presentations-basis-v1',
                 document='examples/v014/kant-directed-presentations.noema')
    basis['definitions'].update(generic_composed()[1]['definitions'])
    decls = {d['name']: d for d in doc['declarations']}
    for name, args, meaning in (
        ('f2', ['act', 'recipient', 'subject', 'message_description', 'context'], 'この提示行為で、この受け手へ、指定対象について記述された発話を示す。発話記述の関数の引数をsubjectへ対応付ける。内容の真理や証明、受け手の理解や同意を意味しない。'),
        ('f3', ['sender', 'act', 'context'], 'この人が同じ提示行為で示す側の当事者となる。単なる同席者や受け手としての参加とは区別する。'),
        ('f4', ['person', 'context', 'case'], 'この人物と文脈において、自立を試みる場合の危険という条件を評価する仮定状況の範囲。実際に試みたという履歴ではなく、前文の信念候補u2とも区別する。')):
        declaration = decls[name]
        basis['primitives'].append({'symbol': name, 'parameters': declaration['parameters'],
            'result': declaration['result'], 'arguments': args, 'meaning_ja': meaning})
    basis['definitions'].update({
        'et': '自立の状態upへ向かう場合の可能な結果に、本人への不利益がある。非常に高いという程度utは要求せず、実際に不利益が起きたこととも分ける。',
        'eu': '指定された非空の仮定範囲で、同じ人物が自立した活動を試みるejなら、その人にetの危険があるという条件。実際の試みや実際の危険は断定しない。',
        'ev': 'euを主張として示す発話の対象。作成しただけでは発話を実行しない。',
        'e2': 'euを評価する同じ範囲に、前件ejが成立する場合が少なくとも一つある。条件euの真理と、適用する場合の存在を分ける補助条件。',
        'ew': '同じ後見人群が、先行文の同じ対象範囲djへ、本人自身についてのevを同じ提示行為で示す。受け手と警告の対象を取り違えず、記述された内容は実行評価しない。',
        'ex': 'ewの提示より前に、今回の提示対象と同じ人々全員について、同じ後見人群によるerの制約が成立する状況がある。対象範囲は提示時の文脈に固定する。erを採用する明示的なモデル内の読みである。',
        'e3': '同じ本人と活動について不利益の可能性etはあるが、先行する非常に高い危険の基準uwは満たさない。危険がないこと、他者が危険を信じていないこととは異なる。',
        'e4': '先行する同じ対象範囲djが非空で、その全員についてe3が成立する内容。「それほど大きくない」のsoを先行の高危険度基準へ対応させる部分的な読み。'})
    basis['unresolved'] += generic_composed()[1]['unresolved'] + [
        '条件付きの危険を示す行為とその前後を接続した。zeigenの証拠提示としての意味、危険の実在を含む読み、媒体や受け手の認識変化は未確定である。',
        'allein gehenを、既存の自立した理解力の使用とその試みへ対応させる対象側の解釈である。実際に一人で歩くという描写、家畜・歩行器、先行する認知的変化は未記述。',
        '条件euが全候補で前件偽のために成立する場合も区別する。e2で適用例の存在を別に確認できるが、その存在を原文へ無条件に追加しない。',
        '非常に高い危険度をetへ追加せず、後続の「それほど大きくない」をe3・e4へ接続した。soの程度基準が先行uwに一致する読みを明示するが、唯一の解釈としては確定しない。学習・萎縮・譲歩・焦点の記述は残る。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def main():
    for compose, filename in ((generic_composed, 'data/directed-presentations-basis-v1.json'),
                              (source_composed, 'data/kant-directed-presentations-basis-v1.json')):
        text, basis = compose()
        for name, body in ((basis['document'], text), (filename, json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            path = ROOT / name
            if path.exists():
                if path.read_text(encoding='utf-8') != body:
                    raise ValueError('Stored directed presentation differs: ' + name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream:
                    stream.write(body)
    print('Directed message presentation and prior constraint connected without endorsement')


if __name__ == '__main__':
    main()
