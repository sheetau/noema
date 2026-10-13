"""Keep restriction degree separate from finite weighted temporal frequency."""
from copy import deepcopy
import json

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from scripts.compose_limits import ROOT
from scripts.compose_proportions import generic_composed as proportions

PARENT = 'examples/v014/kant-restriction-degree.noema'


def definitions():
    return '''
d rd3[points j[d] point d] c[
 q[v points][u[e[n p a b][n p a b]]][i[found c item d][x[v found][e[v item][v point]]]]
].
d rd4[points j[d] property h[d] c weight h[d] b] b[
 q[v points][n p a b][i[total b point d][k ha[v total k hb[c[v weight][v point] k hd[c[v property][v point]]]]]]
].
d rd5[points j[d] scope h[d] c classified h[d] c weight h[d] b] c[
 w[k he[]][w[k hc[n p a b d[v points]]][f point d[
  w[z[c[v scope][v point]][k rd3[v points v point]]][
   w[u[k hc[n p b b k rd4[v points i[item d][e[v item][v point]] i[item d][n p b b]]]]][
    y[c[v scope][v point]][w[c[v classified][v point]][k hc[n p a b c[v weight][v point]]]]
   ]
  ]
 ]]]
].
d rd6[points j[d] scope h[d] c classified h[d] c property h[d] c weight h[d] b ratio b] c[
 w[k rd5[v points v scope v classified v weight]][w[u[k hc[v ratio n p a b]]][w[u[k hc[n p b b v ratio]]][
  e[k hb[v ratio k rd4[v points i[point d][e[n p a b][n p a b]] v weight]]][k rd4[v points v property v weight]]
 ]]]
].
d rd7[points j[d] scope h[d] c classified h[d] c property h[d] c weight h[d] b ratio b criterion h[b] c] c[
 w[k rd6[v points v scope v classified v property v weight v ratio]][c[v criterion][v ratio]]
].
'''


MEANINGS = {
    'rd3': '状況が指定の有限列に現れる。',
    'rd4': '列の各状況について、指定性質の指示関数と重みの積を加算する。生の合計であり、重複・重み・範囲の正当性はrd5で検査する。',
    'rd5': '指示関数の規約を満たし、非空の列が対象範囲の全状況を過不足なく重複なしで列挙し、全対象が分類済みで、全対象の重みが厳密に正である。',
    'rd6': 'rd5を満たす同じ範囲で、0以上1以下の比率と全重みの積が、指定性質を満たす重みの合計に等しい。',
    'rd7': 'rd6の正確な比率が、別に指定した頻度評価の基準を満たす。活動内の制限の程度を測る基準とは区別する。',
}
LIMITS = [
    '有限の評価機会・状況に正の有理数重みを与える候補尺度である。全て1なら機会数の比率になる。重みを継続時間として読むには、各状況が代表する重複しない時間区間、その完全性、同じ区間内の状態の保持を別に確かめる必要がある。',
    '単なる観測点の数や標本の比率を現実の全期間の頻度・連続時間の測度と同一視しない。重みと対象範囲は結果を見て選び直さず、比較対象間で固定する。',
    '同じ状態の評価機会を分ける場合、合計重みを保てば割合を保てる。別状態への分割や重みの変更は同じ測定とはしない。検査した有限例を全分割の一般証明には数えない。',
    '範囲内で分類済み条件が偽なら比率の主張は不成立になる。分類を評価できなければ未知を偽とせず評価を拒否する。範囲外の未評価入力も現行評価器の式評価順によって参照され得る。',
]


def generic_composed():
    text, basis = proportions()
    doc = parse(text + definitions())
    basis = deepcopy(basis)
    basis.update(version='restriction-frequency-basis-v1', document='examples/v014/restriction-frequency.noema')
    basis['definitions'].update(MEANINGS)
    basis['unresolved'] += LIMITS
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def source_composed():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    statements, doc['statements'] = doc['statements'], []
    extra = definitions() + '''
d h75[source a person a role a population j[a] ratio b context d] c[
 k h74[v source v person v role v population v ratio i[value b][e[n p a b][n p a b]] v context]
].
d h76[source a person a role a frame a populations h[d] j[a] degrees h[d] b degreecriterion h[b] c points j[d] weight h[d] b frequency b frequencycriterion h[b] c anchor d] c[
 w[k tb[i[point d][k h7q[v frame v anchor v point]] i[point d][k h7r[v frame v anchor v point]] i[first d last d][k ic[v first v last v anchor]]]][
  k rd7[v points i[point d][k h7r[v frame v anchor v point]]
   i[point d][k h75[v source v person v role c[v populations][v point] c[v degrees][v point] v point]]
   i[point d][k h74[v source v person v role c[v populations][v point] c[v degrees][v point] v degreecriterion v point]]
   v weight v frequency v frequencycriterion]
 ]
].
'''
    doc = parse(format_graph(doc, 'compact') + extra)
    doc['statements'] = statements
    basis = deepcopy(json.loads((ROOT / 'data/kant-restriction-degree-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-restriction-frequency-basis-v1', document='examples/v014/kant-restriction-frequency.noema')
    basis['definitions'].update(MEANINGS)
    basis['definitions'].update({
        'h75': '私的活動の範囲・全対象の規範分類・禁止割合をh74で検査し、程度の大小の基準を問わず、その割合が正しいことを確認する。程度基準を満たさない場合と分類が欠ける場合を分けるための条件。',
        'h76': '同じ期間枠と評価文脈で、非空・一つの時間的経過内・間の抜けない範囲を全列挙する。各点で私的活動全体の禁止割合h75が正しく評価済みで、指定の程度基準を満たす点の重み付き割合が、指定値と頻度基準を満たす。内側の程度基準と外側の頻度基準は別々である。',
    })
    basis['unresolved'] += LIMITS + [
        '程度が基準未満の時点を数えないことと、未分類や衝突の時点を黙って不成立として数えることを分ける。後者では全期間の頻度を確定しない。',
        '各時点の活動一覧は同じ人・立場・規範出所で評価する。時点間で活動種類が変わることは許すが、活動の粒度・制度の対応と程度基準の比較可能性は呼出側で確認する。',
        'öftersの候補となる実際の制度状態の頻度であり、頻繁な制限を許可する規範と、各時点で制限を許可する規範はまだこの定義へ接続していない。原文がその頻度で実際に制限しているという主張を追加しない。',
        '原文の頻度・程度の唯一の読み、継続時間や反復回数との関係、進歩を妨げないという留保、全文の意味一致は未完。',
    ]
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def main():
    for builder, stem in ((generic_composed, 'restriction-frequency'), (source_composed, 'kant-restriction-frequency')):
        text, basis = builder()
        for name, body in ((basis['document'], text), ('data/' + stem + '-basis-v1.json', json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            path = ROOT / name
            if path.exists():
                if path.read_text(encoding='utf-8') != body:
                    raise ValueError('Stored restriction frequency differs: ' + name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream:
                    stream.write(body)
    print('Separate degree and frequency criteria composed with explicit positive weights')


if __name__ == '__main__':
    main()
