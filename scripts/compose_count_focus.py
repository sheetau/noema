"""Represent count alternatives without equating exclusion with surprise."""
from copy import deepcopy
import json

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from scripts.compose_limits import ROOT

PARENT = 'examples/v014/kant-qualified-few.noema'


def definitions():
    return '''
d rcx[population j[a]] j[b][q[v population][l[b][n p a b]][i[counts j[b] person a][m[v counts][l[b][d[v counts]]]]]].
d rcy[counts j[b] selected h[b] c alternative h[b] c] c[
 q[v counts][e[n p a b][n p a b]][i[valid c count b][w[v valid][y[c[v selected][v count]][c[v alternative][v count]]]]]
].
d rcz[counts j[b] selected h[b] c alternatives j[h[b] c] actual b] c[
 w[q[v counts][u[e[n p a b][n p a b]]][i[found c count b][x[v found][e[v count][v actual]]]]][
 w[c[v selected][v actual]][w[u[e[d[v alternatives]][n p a b]]][
  q[v alternatives][e[n p a b][n p a b]][i[valid c alternative h[b] c][w[v valid][
   y[u[k rcy[v counts v selected v alternative]]][u[c[v alternative][v actual]]]
  ]]]
 ]]]
].
'''


MEANINGS = {
    'rcx': '列の長さNから、取り得る人数0,1,...,Nの全てを一回ずつ昇順に生成する。各段で現在の人数列の長さを次の数として付け加える。元の対象列の重複や範囲の完全性は別途検査する。',
    'rcy': '指定した人数列の全要素について、選んだ数量条件が成立するなら比較条件も成立する。列が完全な人数領域であるという条件の下での含意であり、一時点の実測人数だけで条件の強弱を判断しない。空列では全称条件は空虚に成立する。',
    'rcz': '実際の人数が指定人数列に属して選んだ数量条件を満たし、比較条件の列は空でない。各比較条件について、選んだ条件からrcyの意味で従わないなら実際の人数では不成立である。従う弱い条件・同値な条件は排除しない。期待・確率・話者の驚きは条件に含めない。',
}
LIMITS = [
    'rczは明示した数量の代替条件についての排除条件であり、焦点の自然言語上の適切さ、比較条件の選定根拠、前提と断言の区分、onlyやnurの全用法を定義したものではない。',
    '全比較条件が弱い条件や同値条件だけの場合、実際の数量条件以上の排除効果は生じない。恒偽の比較条件も、この検査だけでは文脈的に不適切だと判定できない。',
    'rcyは渡した人数領域に相対的である。原文側ではrcxによって0から母集団の人数までを全て含める。有限評価例は任意の列長についての帰納証明ではない。',
]


def generic_composed():
    doc = parse('n:\n' + definitions())
    basis = {'version': 'count-focus-basis-v1', 'document': 'examples/v014/count-focus.noema',
        'primitives': [], 'definitions': MEANINGS, 'unresolved': LIMITS}
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def source_composed():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    statements, doc['statements'] = doc['statements'], []
    extra = '''r h5v[b d] j[h[b] c].
d h5w[population j[a] context d] c[w[k h5o[v population v context]][
 k rcz[k rcx[v population] i[count b][w[k hc[n p a b v count]][k hc[v count k h4h[d[v population] v context]]]]
  k h5v[d[v population] v context] k hf[v population i[person a][t[k h5k[v person]][v context]]]]
]].
d h5x[population j[a]] e[b context[w[k h5w[v population v context]][k h5p[v population v context]]]].
d h5y[] e[b context[g population j[a][t[k h5x[v population]][v context]]]].
d h5z[] c[w[k uc[k h5t[] k wa[] r[k h5y[]] k wh[]]][w[
 k ud[k wa[] i[node a][x[e[v node][k h3a[]]][e[v node][k h3s[]]]] k h5t[] k wh[]]
][k ue[k h3s[] k h5t[] k wh[]]]]].
'''
    doc = parse(format_graph(doc, 'compact') + definitions() + extra)
    if statements[-1] != {'kind': 'assert', 'body': {'kind': 'call', 'symbol': 'h5u', 'arguments': []}}:
        raise ValueError('Unexpected conclusion attribution in parent')
    doc['statements'] = statements[:-1] + [{'kind': 'assert', 'body': {'kind': 'call', 'symbol': 'h5z', 'arguments': []}}]
    basis = deepcopy(json.loads((ROOT / 'data/kant-qualified-few-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-count-focus-basis-v1', document='examples/v014/kant-count-focus.noema')
    decl = next(row for row in doc['declarations'] if row['name'] == 'h5v')
    basis['primitives'].append({'symbol': 'h5v', 'parameters': decl['parameters'], 'result': decl['result'],
        'arguments': ['population_size', 'context'],
        'meaning_ja': 'この母集団の全人数と基準文脈で、数量の焦点に関連する比較条件の列。各要素は人数を受けて真偽を返す同じ型の条件であり、人数以外の性質や対象者は変更しない。予想する状況keとは異なり、確率や驚きは表さない。条件の選定根拠は解釈上の前提。'})
    basis['definitions'].update(MEANINGS)
    basis['definitions'].update({
        'h5w': '実際の人数条件h5oを保持し、同じ対象列について生成した0からNの人数領域で、0より大きく同じh4hの上限未満という条件から従わないh5vの比較条件を、実際の人数では排除する。母集団・数える性質h5k・文脈・上限を固定して数量条件だけを比較する。',
        'h5x': '数量の排除h5wと、実際の該当者への譲歩h5pを共に持つ内容。数量の比較条件と、達成後の活動についての期待候補を別の引数・関係として保持する。',
        'h5y': '全対象を過不足なく含む有限列が存在してh5xが成立する結論候補。実際の人数・評価条件・存在含意を保持して、数量代替条件の排除を加える。',
        'h5z': 'h5yの数量焦点を持つ結論を同じ著者・結論箇所へ帰属させ、先行版と同じ根拠集合と本文順序を保持する。旧h5uの本文主張を置き換えるが、旧定義と文書は残す。'})
    basis['unresolved'] += LIMITS + [
        'nur Wenigeに数量代替条件の排除を接続した解釈候補である。各比較条件はNoemaの人数述語として与え、対訳語や固定の人数辞書からは生成しない。原文の比較条件を一意に確定していない。',
        'h4hの具体的な数値や、h5vの条件列を原文から復元したわけではない。全員が絶対人数として少数に入る場合もh5oは引き続き許し、数量比較による追加条件は別に評価する。',
        '同じ文脈では実際の人数だけが既知でも、比較条件の0からNにおける真偽を全て評価できなければ排除判定は未完である。未評価の条件を偽にする規則は追加しない。',
        '数量比較と譲歩、前提・断言の区分、焦点位置・韻律、nurの評価的意味、Daherの根拠範囲、基礎概念と原文の意味一致確認は残る。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def main():
    for builder, stem in ((generic_composed, 'count-focus'), (source_composed, 'kant-count-focus')):
        text, basis = builder()
        for path, body in ((ROOT / basis['document'], text), (ROOT / ('data/' + stem + '-basis-v1.json'),
                json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            if path.exists():
                if path.read_text(encoding='utf-8') != body:
                    raise ValueError('Stored count focus differs')
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream:
                    stream.write(body)
    print('Count-domain implication and exclusion added without imposing surprise')


if __name__ == '__main__':
    main()
