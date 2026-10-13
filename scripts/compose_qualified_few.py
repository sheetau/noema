"""Count actual achievers separately from the author's defeated expectations."""
from copy import deepcopy
import json

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from scripts.compose_limits import ROOT
from scripts.compose_scoped_counts import generic_composed as counts

PARENT = 'examples/v014/kant-achievement-exercise.noema'


def definitions():
    return '''
d rcu[population j[a] property h[a] c complete h[a] c] c[
 q[v population][e[n p a b][n p a b]][i[valid c person a][w[v valid][x[c[v property][v person]][c[v complete][v person]]]]]
].
d rcv[population j[a] scope h[a] c property h[a] c complete h[a] c upper b] c[
 w[k rcu[v population v property v complete]][k rcn[v population v scope v property v upper]]
].
d rcw[population j[a] scope h[a] c property h[a] c complete h[a] c upper b] c[
 w[k rcu[v population v property v complete]][k rco[v population v scope v property v upper]]
].
'''


MEANINGS = {
    'rcu': '列に載る全対象について、数える性質の肯定例があるか、否定を評価するために指定した完全性条件を満たす。列の外の対象はここでは評価せず、範囲との完全な一致は別途rcmで要求する。空列ではこの条件だけは成立する。',
    'rcv': 'rcuの評価条件と、rcnの全対象の正確な列挙・正の上限未満の人数条件を合わせる。数える性質の真偽を、別の期待や評価条件との論理積に置き換えない。該当者ゼロを許す。',
    'rcw': 'rcvと同じ評価条件に、該当者が少なくとも一人いるrcoの人数条件を合わせる。評価不足の対象を成功者から除いて少数に見せない。',
}
LIMITS = [
    'propertyとcompleteは完全な解釈で与える。completeが数える性質の否定評価に十分であることは呼出側の意味規約であり、未知の事実を偽として返してよい規則ではない。',
    'rcuは肯定例による十分性と否定評価に必要な条件を分ける。ただし有限評価器は純粋な全域的解釈を前提とし、Pythonの未定義なコールバックを短絡評価で隠す機構ではない。',
    '全対象の列挙・上限の文脈的妥当性・述語解釈の完全性は現実について別途確認する。有限例で全人類の経験を調べたことにはならない。',
]


def generic_composed():
    text, basis = counts()
    doc = parse(text + definitions())
    basis = deepcopy(basis)
    basis.update(version='qualified-few-basis-v1', document='examples/v014/qualified-few.noema')
    basis['definitions'].update(MEANINGS)
    basis['unresolved'] += LIMITS
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def source_composed():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    statements, doc['statements'] = doc['statements'], []
    extra = '''r h5t[] a.
d h5m[population j[a] context d] c[k rcu[v population i[person a][t[k h5k[v person]][v context]] i[person a][k h4t[v person v context]]]].
d h5n[population j[a] context d] c[w[k h5m[v population v context]][k h4j[v population p h5k v context]]].
d h5o[population j[a] context d] c[w[k h5m[v population v context]][k h4k[v population p h5k v context]]].
d h5p[population j[a] context d] c[q[v population][e[n p a b][n p a b]][
 i[valid c person a][w[v valid][y[t[k h5k[v person]][v context]][t[k h5l[v person]][v context]]]]
]].
d h5q[population j[a]] e[b context[k h5o[v population v context]]].
d h5r[population j[a]] e[b context[w[k h5o[v population v context]][k h5p[v population v context]]]].
d h5s[] e[b context[g population j[a][t[k h5r[v population]][v context]]]].
d h5u[] c[w[k uc[k h5t[] k wa[] r[k h5s[]] k wh[]]][w[
 k ud[k wa[] i[node a][x[e[v node][k h3a[]]][e[v node][k h3s[]]]] k h5t[] k wh[]]
][k ue[k h3s[] k h5t[] k wh[]]]]].
'''
    doc = parse(format_graph(doc, 'compact') + definitions() + extra)
    doc['statements'] = statements + [{'kind': 'assert', 'body': {'kind': 'call', 'symbol': 'h5u', 'arguments': []}}]
    basis = deepcopy(json.loads((ROOT / 'data/kant-achievement-exercise-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-qualified-few-basis-v1', document='examples/v014/kant-qualified-few.noema')
    decl = next(d for d in doc['declarations'] if d['name'] == 'h5t')
    basis['primitives'].append({'symbol': 'h5t', 'parameters': decl['parameters'], 'result': decl['result'], 'arguments': [],
        'meaning_ja': '第三段落末の、自己活動による自立と確かな知的活動を持つ少数者についての結論箇所。人や出来事の個体ではなく談話上の参照先。'})
    basis['definitions'].update(MEANINGS)
    basis['definitions'].update({
        'h5m': '全列挙の各対象について、今回数えるh5kの肯定例があるか、基準時までの能力評価が整合するh4tを要求する。h4qだけの肯定でh5kの否定側の評価不足を許す旧h4uとは区別する。',
        'h5n': 'h5mの評価条件の下、同じ文脈でh5kを満たす人をh4jで数え、正の上限未満を要求する。ゼロ人を許す比較用候補。',
        'h5o': 'h5mの評価条件の下、同じ文脈でh5kを満たす人が少なくとも一人いて、h4kの上限未満である。期待との対比h5lではなく実際の達成・活動h5kを数える。',
        'h5p': '列に含むh5kの該当者全員に、同じ文脈でh5lの期待との対比がある。誰を人数に数えるかは変更しない。全列挙の正しさと存在はh5oに接続したとき別途要求する。',
        'h5q': 'h5oの存在を伴う人数条件だけの内容。期待の候補をまだ評価していなくても、完全な実際の性質解釈と評価条件の下で独立に扱える。',
        'h5r': 'h5oの実際の人数条件とh5pの譲歩の提示条件を分けて同時に要求する。期待条件を満たさない人を数える対象から取り除くことはしない。',
        'h5s': '指定文脈の対象者全員を過不足なく含む有限列があり、h5rを満たすという第三段落末の結論の候補内容。有限列全域への存在量化を使い、一つの都合のよい標本では代用しない。',
        'h5u': '著者がh5sを結論箇所h5tで提示し、直前の条件付き描写h3aとその理由h3sを根拠側として帰結に置き、h3sの後に結論を置くという帰属。引用内容の実行、論理的導出の妥当性、現実の人数はこの帰属から推論しない。'})
    basis['unresolved'] += LIMITS + [
        '本文ではgiebt esを存在を伴う読みとしてh5oを採用し、ゼロを許すh5nも保持した。原文の存在含意・nurの焦点・具体的な上限の適切さを確定したものではない。',
        'h5mは能力の結果範囲の評価不足に対する構造的な検査である。判断の理由・指導・活動範囲・現実の履歴・因果等の全知識を保証するものではなく、それらは完全な解釈を与える契約のままである。',
        'h5pは実際の該当者について譲歩を分配する一つの読みである。期待の強さ・選定理由、集合全体にかかる別の譲歩の読みは未完。期待の評価不足を人数の減少には使わない。',
        'Daherの根拠側は直前の条件付き描写とその理由へ接続した明示的な候補であり、段落全体への指示範囲を唯一に確定しない。udは著者の推論提示を表すだけで、身体的な条件文から人数条件の論理的含意を証明しない。',
        'h5sの任意の有限列への存在量化を有限評価器は実行しない。具体的な全列挙でh5rを検査し、全文主張の帰属は引用を実行しない設定で検査する。全有限列の機械的証明や原文との意味一致確認とは区別する。',
        '基礎概念、自立・精神への働きかけ・安定した知的活動の全語義、比喩、前段落からの論述接続、原刊照合と全文の意味一致確認は未完。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def main():
    for builder, stem in ((generic_composed, 'qualified-few'), (source_composed, 'kant-qualified-few')):
        text, basis = builder()
        for path, body in ((ROOT / basis['document'], text), (ROOT / ('data/' + stem + '-basis-v1.json'),
                json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            if path.exists():
                if path.read_text(encoding='utf-8') != body:
                    raise ValueError('Stored qualified few differs')
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream:
                    stream.write(body)
    print('Actual qualifying people counted separately from concession and inferred conclusion attribution')


if __name__ == '__main__':
    main()
