"""Separate persistence on a future tail from existence of an unending tail."""
from copy import deepcopy
import json

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from scripts.compose_limits import ROOT
from scripts.compose_persistence import generic_composed as persistence

PARENT = 'examples/v014/kant-relational-fetters.noema'
BASE = 'history h[d] c before h[d d] c anchor d'
ARGS = 'v history v before v anchor'


def definitions():
    return f'''
d rby[{BASE}] h[d] c[i[point d][w[c[v history][v point]][x[e[v point][v anchor]][c[v before][v anchor v point]]]]].
d rbz[{BASE}] c[w[k ta[v history v before]][w[c[v history][v anchor]][
 f point d[y[c[k rby[{ARGS}]][v point]][g later d[w[c[v history][v later]][c[v before][v point v later]]]]]
]]].
d rca[{BASE} state h[d] c] c[w[k ta[v history v before]][w[c[v history][v anchor]][
 f point d[y[c[k rby[{ARGS}]][v point]][c[v state][v point]]]
]]].
d rcb[{BASE} state h[d] c] c[w[k rbz[{ARGS}]][k rca[{ARGS} v state]]].
d rcc[{BASE} state h[d] c beyond h[b d] c] c[w[k rcb[{ARGS} v state]][
 f horizon b[g point d[w[c[k rby[{ARGS}]][v point]][c[v beyond][v horizon v point]]]]
]].
'''


def generic_composed():
    text, basis = persistence()
    doc = parse(text + definitions())
    basis = deepcopy(basis)
    basis.update(version='unending-persistence-basis-v1', document='examples/v014/unending-persistence.noema')
    basis['definitions'].update({
        'rby': '同じ履歴のうち、基準時そのものか、それより後の状況の範囲。順序の妥当性はrbz・rcaで別に要求する。',
        'rbz': '履歴が非空の厳密な全順序を持ち基準時を含み、その基準時以降のどの状況にも同じ履歴内でさらに後の状況がある。最後の状況を持つ履歴は満たさない。',
        'rca': '履歴が非空の厳密な全順序を持ち基準時を含み、基準時以降の履歴の全状況で状態が成立する。履歴に終点があっても成立でき、空の後続範囲での空虚な成功は基準時の包含で防ぐ。',
        'rcb': 'rbzとrcaがともに成立する。基準時以降に終点がなく、その範囲の全状況で状態が続く。終点の有無が未確認であることや、指定された有限期間の観測とは区別する。',
        'rcc': 'rcbに加え、どんな有理数の時間限界にも、それを越える同じ履歴の将来の状況がある。beyondは同じ原点・単位の時間座標を、その有理数の限界が厳密に下回るという関係として与える。'})
    basis['unresolved'] += [
        '履歴と先行関係の完全さは解釈の前提である。rbzは順序上の最後の点がないことを要求するが、時間の数値的な長さ、発散、時間粒度や物理的な寿命を定義しない。',
        '最後の点がないことと、外部の数値時刻に対して上に非有界であることは違う。例えば上端を含まない有限長の時間区間もrbzを満たしうる。無限の数値的な持続には追加の尺度条件が必要。',
        '有限評価器へ渡した状況集合を全履歴と解釈した場合、rbzとrcbは必ず偽になる。これはその有限モデルの結果であり、現実の持続の否定でも、言語の表現不能でもない。',
        '有限の観測記録がいつまでも拡張できそうなこと、将来を知らないこと、通常の傾向、反事実的な継続や必然性は、rcb自体には含めない。']
    basis['unresolved'].append('rccのbeyondは実数時刻の下側切断を表す関係として使えるが、切断の妥当性、時間順序との整合、原点・単位は呼出側の意味規約で与える。任意の真偽関数を実時間の測定とみなさない。有理数の全領域への量化を有限の限界値で代用しない。')
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def source_composed():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    statements, doc['statements'] = doc['statements'], []
    extra = '''
d h2k[person a] e[b context[k rca[i[point d][k ia[v person v context v point]]
 i[first d second d][k ic[v first v second v context]] v context i[point d][t[k bf[v person]][v point]]]]].
d h2l[person a] e[b context[k rcb[i[point d][k ia[v person v context v point]]
 i[first d second d][k ic[v first v second v context]] v context i[point d][t[k bf[v person]][v point]]]]].
d h2m[person a beyond h[b d] c] e[b context[k rcc[i[point d][k ia[v person v context v point]]
 i[first d second d][k ic[v first v second v context]] v context i[point d][t[k bf[v person]][v point]] v beyond]]].
'''
    doc = parse(format_graph(doc, 'compact') + definitions() + extra)
    doc['statements'] = statements
    basis = deepcopy(json.loads((ROOT / 'data/kant-relational-fetters-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-unending-persistence-basis-v1', document='examples/v014/kant-unending-persistence.noema')
    generic = generic_composed()[1]
    basis['definitions'].update({name: generic['definitions'][name] for name in ('rby', 'rbz', 'rca', 'rcb', 'rcc')})
    basis['definitions'].update({
        'h2k': '同じ人物の同じ履歴において基準時以降の全状況で依存状態bfが続く。h26の選んだ評価区間と違い、履歴の残部全体を要求するが、履歴に最後の状況があっても成立できる。',
        'h2l': 'h2kの持続に加えて、同じ履歴の基準時以降のどの状況にもさらに後の状況がある。順序上の終点のない持続という強い候補であり、カントがこれを文字どおり主張したとは確定していない。',
        'h2m': 'h2lの持続に加え、明示した同じ時間座標のどんな有理数の限界より先にも状況がある。時間尺度の引数を要求する候補であり、個人の寿命について本文に主張を足さない。'})
    basis['unresolved'] += generic['unresolved'][-5:] + [
        'h26・h2k・h2lの違いを明示するための定義追加であり、immerwährendenの採用訳や新しい本文の主張・原文範囲は追加しない。有限の生涯や修辞的な強調を、個人の無限の寿命へ変換しない。',
        'h2lだけでは数値的に無限の持続時間を保証しない。h2mに必要な時間尺度を原文から補わず、どの強さを採用するかは持続を強める原文の語義の検討とともに残る。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def witnesses_composed():
    doc = parse('''n:
r aa[b b] c.
d wa[scope h[b] c] c[w[g point b[c[v scope][v point]]][
 f point b[y[c[v scope][v point]][g later b[w[c[v scope][v later]][k aa[v point v later]]]]]
]].
d wb[scope h[b] c] c[f horizon b[g point b[w[c[v scope][v point]][k aa[v horizon v point]]]]].
d wc[point b] c[w[u[k aa[v point n p a b]]][k aa[v point n p b b]]].
d wd[point b] c[u[k aa[v point n p a b]]].
s[k wa[p wc]].s[u[k wb[p wc]]].s[k wa[p wd]].s[k wb[p wd]].
''')
    d = doc['declarations'][0]
    basis = {'version': 'rational-tail-witnesses-basis-v1', 'document': 'examples/v014/rational-tail-witnesses.noema',
        'primitives': [{'symbol': 'aa', 'parameters': d['parameters'], 'result': d['result'],
            'arguments': ['left', 'right'], 'meaning_ja': '有理数についての通常の厳密な大小関係。leftがrightより小さい。'}],
        'definitions': {
            'wa': '有理数の範囲が非空で、その各点より大きい点が同じ範囲にある。最大の点がないという条件。',
            'wb': 'どんな有理数の限界にも、それより大きい点が範囲にある。上に非有界である条件。',
            'wc': '0以上1未満の有理数の範囲。上端1を含まない。',
            'wd': '0以上の有理数の範囲。'},
        'unresolved': ['数の範囲についての正確な具体例であり、状況型を数型へ暗黙に読み替える証明ではない。現実の時間や人の生涯がこのいずれかのモデルに従うという主張もない。']}
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def main():
    for builder, stem in ((generic_composed, 'unending-persistence'), (source_composed, 'kant-unending-persistence'),
            (witnesses_composed, 'rational-tail-witnesses')):
        text, basis = builder()
        for path, body in ((ROOT / basis['document'], text), (ROOT / ('data/' + stem + '-basis-v1.json'),
                json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            if path.exists():
                if path.read_text(encoding='utf-8') != body:
                    raise ValueError('Stored unending persistence differs')
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream:
                    stream.write(body)
    print('Future-tail persistence and absence of a final point composed separately')


if __name__ == '__main__':
    main()
