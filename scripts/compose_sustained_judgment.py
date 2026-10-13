"""Connect a scoped exercise of independent judgment to the gait depiction."""
from copy import deepcopy
import json

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from scripts.compose_limits import ROOT, v, app, op, both, quant, call, definition
from scripts.compose_persistence import generic_composed as persistence

PARENT = 'examples/v014/kant-controlled-gait.noema'


def definitions():
    invoke = lambda name, *args: app(v(name), *(v(arg) for arg in args))
    judged = invoke('judgments', 'person', 'judgment', 'point')
    independent = op('u', quant('g', 'other', 'a', both(
        op('u', op('e', v('other'), v('person'))), invoke('guidance', 'other', 'person', 'judgment', 'point'))))
    reasoned = quant('g', 'matter', 'a', both(invoke('matters', 'judgment', 'matter', 'point'),
        quant('g', 'reason', 'a', both(invoke('reasons', 'judgment', 'reason', 'point'),
            invoke('support', 'reason', 'judgment', 'point')))))
    owned_use = quant('g', 'faculty', 'a', both(invoke('owned', 'faculty', 'person', 'point'),
        invoke('use', 'person', 'faculty', 'judgment', 'point')))
    judgment = definition('rcr', 'person a judgment a point d owned h[a a d] c use h[a a a d] c '
        'judgments h[a a d] c matters h[a a d] c reasons h[a a d] c support h[a a d] c guidance h[a a a d] c',
        both(judged, owned_use, reasoned, independent))
    phase = lambda point: invoke('scope', point)
    member = lambda: invoke('parts', 'judgment', 'episode', 'point')
    performed = lambda: invoke('judgments', 'person', 'judgment', 'point')
    end_witness = quant('g', 'judgment', 'a', both(invoke('parts', 'judgment', 'episode', 'last'),
        invoke('judgments', 'person', 'judgment', 'last')))
    episode = definition('rcs', 'history h[d] c before h[d d] c scope h[d] c person a episode a last d '
        'occurs h[a d] c parts h[a a d] c judgments h[a a d] c adequate h[a a d] c',
        both(call('tb', v('history'), v('scope'), v('before')), phase('last'),
            quant('g', 'earlier', 'd', both(phase('earlier'), invoke('before', 'earlier', 'last'),
                quant('g', 'judgment', 'a', both(invoke('parts', 'judgment', 'episode', 'earlier'),
                    invoke('judgments', 'person', 'judgment', 'earlier'))))),
            invoke('occurs', 'episode', 'last'), end_witness,
            quant('f', 'point', 'd', op('y', phase('point'), both(
                op('x', op('e', v('point'), v('last')), invoke('before', 'point', 'last')),
                quant('f', 'judgment', 'a', op('y', both(member(), performed()),
                    invoke('adequate', 'person', 'judgment', 'point'))))))))
    return judgment + episode


MEANINGS = {
    'rcr': '同じ人・判断・状況に、本人の理解力の所有とその使用、対象についての判断、同じ判断で用いた理由とその支持を要求する。本人と異なる者によるその判断への指導がない。理由や理解力を別の判断から借りて条件を満たさない。',
    'rcs': '同じ履歴の空でない連続範囲に完了点とそれ以前の点があり、全点が完了点以前である。活動が完了点で生起し、その本人が完了点とそれ以前の少なくとも一時点で活動の一部として判断する。その範囲中、本人が同じ活動の一部として行う全判断が指定の条件を満たす。判断のない準備時点を許し、全点で同じ判断や理由を維持することは求めない。',
}
LIMITS = [
    'parts・scopeは同じ活動の全ての部分・全過程を尽くす意味規約であり、不適切な判断を都合よく外す根拠ではない。有限の観測点だけではその完全性を証明できない。',
    '理由の支持基準、理解力とその使用、指導、判断活動の構成は引数の意味規約に依存する。全ての知的活動を判断へ還元せず、理由のある判断の活動だけを扱う。',
    '全ての実際の判断に条件を課す構成で、外乱に対する頑健性、将来の技能、無誤謬性、確信の強さの必要十分条件ではない。対話・助言・情報の受領そのものを禁止しない。',
]


def generic_composed():
    text, basis = persistence()
    doc = parse(text + definitions())
    basis = deepcopy(basis)
    basis.update(version='sustained-judgment-basis-v1', document='examples/v014/sustained-judgment.noema')
    basis['definitions'].update(MEANINGS)
    basis['unresolved'] += LIMITS
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def source_composed():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    statements, doc['statements'] = doc['statements'], []
    extra = '''r h5a[a d d] c.r h5b[a a d] c.r h5f[] a.
d h5c[person a judgment a point d] c[k rcr[v person v judgment v point p ab p ac p fa p fb p fc p fd p ad]].
d h5d[person a episode a last d anchor d] c[
 w[k aa[v person]][w[k ia[v person v anchor v anchor]][w[x[e[v last][v anchor]][k ic[v last v anchor v anchor]]][
 k rcs[i[point d][k ia[v person v anchor v point]] i[first d final d][k ic[v first v final v anchor]]
  i[point d][k h5a[v episode v last v point]] v person v episode v last p dg p h5b p fa p h5c]
 ]]]
].
d h5e[person a] e[b anchor[g episode a[g last d[k h5d[v person v episode v last v anchor]]]]].
d h5g[] c[k qh[k h5f[] k wa[] r[p h5e] r[p h4z] k wh[]]].
'''
    doc = parse(format_graph(doc, 'compact') + definitions() + extra)
    doc['statements'] = statements + [{'kind': 'assert', 'body': {'kind': 'call', 'symbol': 'h5g', 'arguments': []}}]
    basis = deepcopy(json.loads((ROOT / 'data/kant-controlled-gait-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-sustained-judgment-basis-v1', document='examples/v014/kant-sustained-judgment.noema')
    decls = {d['name']: d for d in doc['declarations']}
    for name, arguments, meaning in (
        ('h5a', ['episode', 'last', 'point'], 'この完了点で記述する同じ知的活動の全過程の範囲に入る状況。失敗した判断の時点を選択的に除かない。準備や判断の間の時点も含む。'),
        ('h5b', ['judgment', 'episode', 'point'], 'この状況で、この判断が同じ知的活動を構成する部分である。単に同時に行われる別の活動の判断とは区別する。活動の個体化と部分関係の基礎は未完。'),
        ('h5f', [], '第三段落末で知的活動を確かな歩みによって描写する談話箇所。身体活動の個体や判断の個体ではない。')):
        d = decls[name]
        basis['primitives'].append({'symbol': name, 'parameters': d['parameters'], 'result': d['result'],
            'arguments': arguments, 'meaning_ja': meaning})
    basis['definitions'].update(MEANINGS)
    basis['definitions'].update({
        'h5c': '既存のab・ac・fa・fb・fc・fd・adを同じ判断に結び、自分の理解力を使った、用いた理由に支持される、他者による指導のない判断をrcrで記述する。',
        'h5d': '同じ本人の基準文脈の実際の履歴で基準時までに完了した知的活動がrcsを満たす。各判断にh5cを課すが、準備時点に判断が存在することや身体的な歩行は求めない。',
        'h5e': '本人にh5dの知的活動があるという比喩の対象側の候補内容。知的自立へ移行したh4qの歴史とは独立であり、過去の達成から自動的に導かない。',
        'h5g': '著者が知的活動h5eを身体的な歩行h4zで非字義的に提示するという解釈上の帰属。既存qhで同じ人の二つの異なる記述を対応させる。両内容の実行、真理値一致、両活動の同一性は要求しない。'})
    basis['unresolved'] += LIMITS + [
        'h5eはsicheren Gangの対象側を、活動内で独立した理由ある判断を維持することとして読む明示的な候補である。原文が判断ごとの理由条件を列挙したわけではなく、確信・技能・安定性の全語義を定義し終えたものでもない。',
        'h5gの比喩帰属だけを追加する。自立達成と知的活動の時間的な接続、dennochの期待対比、Daherの推論、少数者の全文主張への接続は未完。',
        '親文書の「比喩の対象側が未記述」という記録は歴史的な課題である。この版で候補内容と引用の対応を追加したが、原文との意味一致確認は依然未完。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def main():
    for builder, stem in ((generic_composed, 'sustained-judgment'), (source_composed, 'kant-sustained-judgment')):
        text, basis = builder()
        for path, body in ((ROOT / basis['document'], text), (ROOT / ('data/' + stem + '-basis-v1.json'),
                json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            if path.exists():
                if path.read_text(encoding='utf-8') != body:
                    raise ValueError('Stored sustained judgment differs')
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream:
                    stream.write(body)
    print('Scoped independent judgment and quoted gait depiction composed')


if __name__ == '__main__':
    main()
