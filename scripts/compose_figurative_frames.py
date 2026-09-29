"""Keep a figurative depiction separate from the content it presents."""
from copy import deepcopy
import json

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from scripts.compose_limits import ROOT


def definitions():
    return '''
r qa[a a i[h[a] e] i[h[a] e] d] c.
d qh[node a author a target i[h[a] e] depiction i[h[a] e] context d] c[
 w[u[e[v target][v depiction]]][k qa[v node v author v target v depiction v context]]
].
d qi[node a author a target i[h[a] e] depiction i[h[a] e] content e context d] c[
 w[k qh[v node v author v target v depiction v context]][t[v content][v context]]
].
'''


def generic_composed():
    doc = parse('n:\n' + definitions())
    declaration = doc['declarations'][0]
    basis = {'version': 'figurative-frames-basis-v1', 'document': 'examples/v014/figurative-frames.noema',
        'primitives': [{'symbol': 'qa', 'parameters': declaration['parameters'], 'result': declaration['result'],
            'arguments': ['node', 'author', 'target_description', 'depiction_description', 'context'],
            'meaning_ja': 'その文脈の談話節点で、著者が対象の性質記述を、別の性質記述を用いた非字義的な描写として提示する。二つの記述の人物引数を対応させる。描写を現実の出来事として断言することや、両内容の真偽の同一性は含まない。'}],
        'definitions': {
            'qh': '対象と描写の記述が異なり、qaの非字義的な提示関係がある。どちらの記述の内容も実行評価しない。',
            'qi': 'qhに加えて、明示的に渡した対象内容が現在文脈で成立する。描写内容の成立は要求しない。内容と記述の対応は呼出側で保持する。'},
        'unresolved': ['これは二つの異なる性質記述を明示する形式であり、比喩を自動発見したり、描写から適切な対象の意味を推論したりする処理ではない。',
            '対応をqaの意味規約で与える。比喩の全理論、評価的効果、複数の読みを一意に解決する基準は含まない。']}
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def source_composed():
    doc = parse((ROOT / 'examples/v014/kant-finite-ratio.noema').read_text(encoding='utf-8'))
    statements, doc['statements'] = doc['statements'], []
    text = format_graph(doc, 'compact') + '\n' + definitions() + '''
r qb[] a.r qc[a a i[h[a] e] d] c.
d qf[person a] e[b point[u[t[k kl[v person]][v point]]]].
d qg[person a] e[b context[g point d[
 w[k tf[i[scene d][k ia[v person v context v scene]] i[scene d][k ib[v person v context v scene]]
  i[earlier d later d][k ic[v earlier v later v context]] v point i[earlier d later d][k kd[v earlier v later v context]]]][
  k qc[k qb[] v person r[p qf] v point]
 ]
]]].
'''
    doc = parse(text)
    doc['statements'] = statements
    text = format_graph(doc, 'compact') + '\ns[k qh[k mw[] k wa[] r[p kf] r[p qg] k wh[]]].\n'
    doc = parse(text)
    basis = deepcopy(json.loads((ROOT / 'data/kant-finite-ratio-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-nature-depiction-basis-v1', document='examples/v014/kant-nature-depiction.noema')
    generic = generic_composed()[1]
    basis['primitives'] += generic['primitives']
    basis['definitions'].update(generic['definitions'])
    decls = {d['name']: d for d in doc['declarations']}
    for name, labels, meaning in (
        ('qb', [], 'この表現で自然を指す対象。個体型で参照することは、人間であること・意思を持つこと・実際に発話することを意味しない。自然という概念の一般的な構成は未完。'),
        ('qc', ['declarer', 'person', 'status_description', 'point'], 'その状況において、第一の対象が、その人を記述された地位・条件を満たすものとして宣告するという描写内容。宣告の正当性や、宣告によって実際に地位が生じることは別条件。')):
        d = decls[name]
        basis['primitives'].append({'symbol': name, 'parameters': d['parameters'], 'result': d['result'], 'arguments': labels, 'meaning_ja': meaning})
    basis['definitions'].update({
        'qf': '自然的な発達上の依存により他者の指導を必要とするklの状態ではないという内容。実際に誰からも指導されないこととは同一視しない。',
        'qg': '同じ人物の履歴内で、生涯の評価範囲より十分前に、自然qbがその人をqfの状態にあると宣告した、という描写内容。本文はこの描写の字義的な真理を断言せず、kfを提示する比喩として参照する。'})
    basis['unresolved'] += generic['unresolved'] + [
        '既存の自然的成熟への移行kfと、宣告としての描写qgを異なる記述として結び付けた。元の原因説明や割合の真偽条件へ、自然の発話を追加していない。',
        'freisprechenの歴史的な義務からの解放という用法は参考にしたが、この資料だけでカントの読みが一意に確定するとはしない。参照記録はfigurative-reading-review-v1.jsonに保存する。',
        '自然という対象・宣告の一般的な意味、比喩の評価的効果、ラテン語、原因の意味、残る本文と原刊確認は未完。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def main():
    for compose, filename in ((generic_composed, 'data/figurative-frames-basis-v1.json'),
                              (source_composed, 'data/kant-nature-depiction-basis-v1.json')):
        text, basis = compose()
        for name, body in {basis['document']: text, filename: json.dumps(basis, ensure_ascii=False, indent=2) + '\n'}.items():
            path = ROOT / name
            if path.exists():
                if path.read_text(encoding='utf-8') != body:
                    raise ValueError('Stored figurative frame differs: ' + name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream:
                    stream.write(body)
    print('Figurative declaration linked to natural maturation without asserting literal speech')


if __name__ == '__main__':
    main()
