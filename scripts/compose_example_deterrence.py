"""Distinguish examples, fear, all contemplated attempts and usual deterrence."""
from copy import deepcopy
import json

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from scripts.compose_limits import ROOT
from scripts.compose_finite_ratios import generic_composed as ratios


def definitions():
    return '''
d r6[person a scope h[a] c context d relation h[a a d] c] c[
 w[g item a[c[v scope][v item]]][f item a[y[c[v scope][v item]][c[v relation][v person v item v context]]]]
].
d r7[cases j[a] eligible h[a] c property h[a] c criterion h[b] c] c[
 w[k pd[v cases v eligible v property v criterion]][k hc[n p b c k pb[v cases v property]]]
].
'''


def generic_composed():
    text, basis = ratios()
    doc = parse(text + definitions())
    basis = deepcopy(basis)
    basis.update(version='example-deterrence-basis-v1', document='examples/v014/example-deterrence.noema')
    basis['definitions'].update({
        'r6': '指定した対象範囲が非空で、その全項について、同じ人物・文脈に指定関係が成立する。該当項がない場合を成功と数えない。',
        'r7': '重複のない非空の適格事例列について、性質が成り立つ割合が過半数で、文脈の基準も満たす。全例での成立は要求しない。'})
    basis['unresolved'] += [
        'r7は有限の等重み事例による通常性の明示的な読みである。自然言語の一般的な通常性、無限母集団や確率分布の理論を確立したものではない。',
        '事例の選定・網羅性・代表性と基準の根拠は呼出側で保持する。成功例だけを集めた列から、通常そうなるという現実の結論を導かない。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def source_composed():
    doc = parse((ROOT / 'examples/v014/kant-experience-acquisition.noema').read_text(encoding='utf-8'))
    statements, doc['statements'] = doc['statements'], []
    text = format_graph(doc, 'compact') + definitions() + '''
r gd[a] a.r ge[a] a.r gg[a a d] c.r gj[a d] c.r gk[d] j[a].r gl[b d] c.
r go[a] d.r gp[a i[h[a] e] d] c.r g2[] a.
d gq[person a act a context d] c[w[k ma[v person v act v context]][w[
 k dd[v context k go[v act]]
][k gp[v act r[p bb] v context]]]].
d gr[case a] e[b context[w[k gg[k gd[v case] k ge[v case] v context]][w[
 k dd[k f7[k ge[v case]] v context]
][g experiencer a[w[k aa[v experiencer]][k fg[v experiencer k ge[v case] k f7[k ge[v case]]]]]]]]].
d gs[case a] e[b context[w[u[k al[k gd[v case] k bb[k gd[v case]] v context]]][
 g act a[w[k gq[k gd[v case] v act v context]][k mc[k gd[v case] v act v context]]]
]]].
d gt[case a] e[b context[k r6[k gd[v case] i[act a][k gq[k gd[v case] v act v context]] v context
 i[person a act a point d][w[k mc[v person v act v point]][w[k md[v person v act v point]][
  k me[v person v act r[p mc] v point]
 ]]]
]]].
d gu[case a] e[b context[w[t[k gr[v case]][v context]][w[t[k gs[v case]][v context]][
 k ea[v case r[p gr] v case r[p gs] v context]
]]]].
d gv[case a] e[b context[w[t[k gr[v case]][v context]][w[t[k gt[v case]][v context]][
 k ea[v case r[p gr] v case r[p gt] v context]
]]]].
d gw[case a context d] c[w[k gj[v case v context]][w[k aa[k gd[v case]]][w[k dj[k gd[v case] v context]][t[k gr[v case]][v context]]]]].
d gx[] e[b context[w[k hr[k gk[v context] v context]][w[
 k r7[k gk[v context] i[case a][k gw[v case v context]] i[case a][t[k gv[v case]][v context]]
  i[ratio b][k gl[v ratio v context]]]
][q[k gk[v context]][e[n p a b][n p a b]][i[valid c case a][w[v valid][t[k gu[v case]][v context]]]]]
]]].
d gy[] c[w[k uc[k g2[] k wa[] r[k gx[]] k wh[]]][k ue[k fv[] k g2[] k wh[]]]].
'''
    doc = parse(text)
    doc['statements'] = statements
    basis = deepcopy(json.loads((ROOT / 'data/kant-experience-acquisition-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-example-deterrence-basis-v1', document='examples/v014/kant-example-deterrence.noema')
    generic = generic_composed()[1]
    basis['definitions'].update({name: generic['definitions'][name] for name in ('r6', 'r7')})
    declarations = {d['name']: d for d in doc['declarations']}
    for name, labels, meaning in (
        ('gd', ['case'], '評価事例で、例を知って反応する対象者。失敗した本人と同一とは限らない。'),
        ('ge', ['case'], '評価事例で対象者に示される一つの経験行為。世の中にそれしか例がないという唯一性は主張しない。'),
        ('gg', ['person', 'example', 'context'], 'この人が、この経験行為の例をこの文脈で知覚・伝聞等により認識している。本人が経験したことや直接目撃したことは要求しない。'),
        ('gj', ['case', 'context'], '通常性の評価範囲に属する事例である。回避が成立したかどうかによって選び直さないという意味規約を持つ。'),
        ('gk', ['context'], 'この文脈で通常性を評価する事例の有限列。重複・適格性・非空性・網羅性は別に検査する。'),
        ('gl', ['ratio', 'context'], 'この文脈で、gemeiniglichの通常性に必要な割合の基準。具体値を原文へ固定しない。過半数はr7の別条件である。'),
        ('go', ['act'], '考慮している行為の予定・想定時点。実行済みの時点ではない。'),
        ('gp', ['act', 'task_description', 'context'], 'この文脈で考慮する行為が、記述された活動を試みることに当たる。実際に試みたことや、実行可能であることは含まない。'),
        ('g2', [], '例による萎縮と、その後の試みを通常思いとどまらせることを述べる談話箇所。')):
        d = declarations[name]
        basis['primitives'].append({'symbol': name, 'parameters': d['parameters'], 'result': d['result'],
            'arguments': labels, 'meaning_ja': meaning})
    basis['definitions'].update({
        'gq': 'この人について現在問題となる行為のうち、現在より後に想定され、同じ自立的な活動bbの試みに当たるもの。予定と実行を分ける。',
        'gr': '対象者が認識した一つの例が先行し、ある人による同じ自立的活動の不成功経験fgである。経験者と対象者を別に結び、無関係な失敗例を混ぜない。',
        'gs': '対象者には同じ目的bbへ行動する勇気が十分でなく、少なくとも一つの後続する試みに害への恐れがある。恐れと実際の危険・能力不足は分ける。schüchternの一つの部分的な読み。',
        'gt': '非空の後続する試みgqの全てについて、同じ本人が害を恐れ、行為を避け、その恐れを回避理由として採用する。単なる未実行や外部からの妨害とは区別する。',
        'gu': '同じ事例でgrとgsが成立し、その例を萎縮の原因説明へ採用する。前後や同時成立だけから原因を断定しない。',
        'gv': '同じ事例でgrとgtが成立し、その例を回避の原因説明へ採用する。全ての可能な状況で必ず避けるという保証ではない。',
        'gw': '事例が評価範囲gjに属し、対象者は人で現在のdjに属し、同じ文脈でgrの例の条件が成立する。成功結果だけを適格事例としない。',
        'gx': '網羅性を明示した非空・重複なしの適格事例列でguが成立し、gvの割合が過半数と文脈基準を満たす。評価事例の中に回避しない例外を許す。',
        'gy': 'gxの部分解釈を著者へ帰属させ、先行する学習の見込みfvとの本文順を保持する。gxの実行評価や譲歩の期待構造はこの関係に含めない。'})
    basis['unresolved'] += generic['unresolved'][-2:] + [
        'ein Beispielを一つの認識された不成功例、schüchternを害への恐れと目標に向かう勇気の不足として読む。報告された架空例、恐れの増加量、恥ずかしさ等を含む語義全体は未確定。',
        '通常性を有限事例内の割合で操作化し、無修飾の萎縮は指定した同じ評価事例で成立すると読む。一般文の唯一の意味ではなく、事例の代表性と現実の頻度を証明しない。',
        'allen ferneren Versuchenの全称は、この文脈で問題となる後続の自立的活動の試みgqへ作用する。考えられる宇宙全体の全行為や、本人が一生行動しないことは主張しない。',
        '例を原因に採用した説明と、介入効果を証明した因果機構は異なる。allein・dochの譲歩と焦点、文字通りの転倒・歩行と比喩、認知変化、原刊照合と全文の意味確認は残る。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def main():
    for compose, filename in ((generic_composed, 'data/example-deterrence-basis-v1.json'),
                              (source_composed, 'data/kant-example-deterrence-basis-v1.json')):
        text, basis = compose()
        for name, body in ((basis['document'], text), (filename, json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            path = ROOT / name
            if path.exists():
                if path.read_text(encoding='utf-8') != body:
                    raise ValueError('Stored example deterrence differs: ' + name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream:
                    stream.write(body)
    print('Examples, timidity, scoped avoidance and exception-tolerant deterrence composed')


if __name__ == '__main__':
    main()
