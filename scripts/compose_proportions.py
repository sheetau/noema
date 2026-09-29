"""Count finite populations and keep contextual large shares distinct from most."""
from copy import deepcopy
import json

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from scripts.compose_limits import ROOT


def definitions():
    return '''
r ha[b b] b.r hb[b b] b.r hc[b b] c.r hd[c] b.
d he[] c[f value c[w[y[v value][e[k hd[v value]][n p b b]]][y[u[v value]][e[k hd[v value]][n p a b]]]]].
d hf[population j[a] property h[a] c] b[
 q[v population][n p a b][i[count b person a][k ha[v count k hd[c[v property][v person]]]]]
].
d hg[population j[a] person a] c[
 q[v population][u[e[n p a b][n p a b]]][i[found c item a][x[v found][e[v item][v person]]]]
].
d hh[population j[a]] c[
 f person a[u[k hc[n p b b k hf[v population i[item a][e[v person][v item]]]]]]
].
d hi[population j[a] domain h[a] c] c[
 w[k hh[v population]][q[v population][e[n p a b][n p a b]][i[valid c person a][w[v valid][c[v domain][v person]]]]]
].
d hj[population j[a] property h[a] c ratio b] c[
 w[k he[]][w[k hh[v population]][w[k hc[n p a b d[v population]]][
  w[u[k hc[v ratio n p a b]]][w[u[k hc[n p b b v ratio]]][
   e[k hb[v ratio d[v population]]][k hf[v population v property]]
  ]]
 ]]]
].
d hk[population j[a] domain h[a] c property h[a] c criterion h[b] c ratio b] c[
 w[k hi[v population v domain]][w[k hj[v population v property v ratio]][c[v criterion][v ratio]]]
].
d hl[population j[a] property h[a] c ratio b] c[
 w[k hj[v population v property v ratio]][k hc[n p b c v ratio]]
].
'''


def generic_composed():
    doc = parse('n:\n' + definitions())
    declarations = {d['name']: d for d in doc['declarations']}
    records = (
        ('ha', ['left', 'right'], '有理数の通常の加算。'),
        ('hb', ['left', 'right'], '有理数の通常の乗算。'),
        ('hc', ['left', 'right'], '有理数の厳密な大小比較。第一引数が第二引数より小さい。'),
        ('hd', ['condition'], '真理値の数値指示関数。真を1、偽を0とする。この全条件をheでも記述し、割合の検査時に要求する。'))
    basis = {'version': 'proportions-basis-v1', 'document': 'examples/v014/proportions.noema',
        'primitives': [{'symbol': s, 'parameters': declarations[s]['parameters'], 'result': declarations[s]['result'],
                        'arguments': a, 'meaning_ja': m} for s, a, m in records],
        'definitions': {
            'he': '真理値の両方について指示関数hdの値を制約する。真なら1、偽なら0である。',
            'hf': '列の各出現について性質の真偽を指示関数で数え、加算する。重複を自動削除しない生の出現数であり、人数として使う条件は別に検査する。',
            'hg': '個体が列のいずれかの位置に現れる。',
            'hh': '各個体の出現数が1を超えない。指示関数と加算・比較の意味規約の下で重複を拒否する。',
            'hi': '重複がなく、列の各個体が指定した母集団の種類に属する。対象の全列挙や非空性はこの条件だけでは主張しない。',
            'hj': 'heを満たし、母集団が空でなく重複もなく、0以上1以下の比率と全人数との積が性質を満たす人数に等しい。',
            'hk': 'hi・hjを満たす母集団の比率が、指定した文脈的な評価基準を満たす。',
            'hl': 'hjの比率が厳密に1/2より大きい。文脈的な大きさの評価とは別の過半数条件。'},
        'unresolved': ['母集団が評価対象を過不足なく列挙していることは、この有限列と型検査だけからは分からない。',
                       '文脈的な大きさの基準を定める方法、無限集団の測度や標本から母集団を推定する統計は含めない。']}
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def source_composed():
    doc = parse((ROOT / 'examples/v014/kant-quoted-group.noema').read_text(encoding='utf-8'))
    statements, doc['statements'] = doc['statements'], []
    text = format_graph(doc, 'compact') + '\n' + definitions() + '''
r hr[j[a] d] c.r hs[b d] c.
d hn[population j[a] property h[a] e ratio b scene d] c[
 w[k hr[v population v scene]][
  k hk[v population p aa i[person a][t[c[v property][v person]][v scene]] i[value b][k hs[v value v scene]] v ratio]
 ]
].
d hq[population j[a] property h[a] e] e[
 b scene[g ratio b[k hn[v population v property v ratio v scene]]]
].
'''
    doc = parse(text)
    doc['statements'] = statements
    text = format_graph(doc, 'compact') + '\n'
    basis = deepcopy(json.loads((ROOT / 'data/kant-quoted-group-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-large-share-basis-v1', document='examples/v014/kant-large-share.noema')
    generic = generic_composed()[1]
    basis['primitives'] += generic['primitives']
    basis['definitions'].update(generic['definitions'])
    declarations = {d['name']: d for d in doc['declarations']}
    for symbol, labels, meaning in (
        ('hr', ['population', 'context'], '列がこの文脈で割合を評価する母集団を過不足なく列挙するという前提。調査標本を母集団の全体と無条件に同一視しない。'),
        ('hs', ['ratio', 'context'], 'その文脈で比率を「これほど大きい割合」と評価する基準。一定の数値や過半数には固定せず、文脈の比較基準として明示する。')):
        basis['primitives'].append({'symbol': symbol, 'parameters': declarations[symbol]['parameters'],
            'result': 'truth', 'arguments': labels, 'meaning_ja': meaning})
    basis['definitions'].update({
        'hn': '文脈の母集団hrが重複のない人々aaからなり、指定した性質の比率が正確で、その文脈の大きさの基準hsを満たす。',
        'hq': '「人々のこれほど大きい割合が、指定した性質に該当する」という量化表現。比率を具体値に固定せず存在量化し、性質を引数として残す。'})
    basis['unresolved'] += generic['unresolved'] + [
        'u0009のein so großer Theil der Menschenという量化部分への草案。後続する生涯・好んで留まること・自然による解放・原因説明はhqの性質引数へまだ接続していない。',
        'hrとhsは文脈上の母集団と比較基準への明示的な前提である。原文が具体的な人数・比率・閾値を指定したとはしない。',
        'hqの全有理数にわたる存在量化を有限の候補リストで代用しない。有限検査ではhnへ比率を明示して条件を確認する。']
    audit_basis(parse(text), basis)
    return text, basis


def main():
    for compose, filename in ((generic_composed, 'data/proportions-basis-v1.json'),
                              (source_composed, 'data/kant-large-share-basis-v1.json')):
        text, basis = compose()
        for name, body in {basis['document']: text, filename: json.dumps(basis, ensure_ascii=False, indent=2) + '\n'}.items():
            path = ROOT / name
            if path.exists():
                if path.read_text(encoding='utf-8') != body:
                    raise ValueError('Stored proportion document differs: ' + name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream:
                    stream.write(body)
    print('Finite proportions composed; contextual large share is not fixed to a majority')


if __name__ == '__main__':
    main()
