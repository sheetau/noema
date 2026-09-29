"""Compose distinct avoidance motives and list their explanatory contribution."""
from copy import deepcopy
import json

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from scripts.compose_limits import ROOT


def definitions(include_primitive=True):
    return ('r ea[a i[h[a] e] a i[h[a] e] d] c.\n' if include_primitive else '') + '''
d na[subject a factors j[i[h[a] e]] effect i[h[a] e] scene d] c[
 w[u[e[d[v factors]][n p a b]]][q[v factors][e[n p a b][n p a b]][i[valid c factor i[h[a] e]][w[v valid][k ea[v subject v factor v subject v effect v scene]]]]]
].
d nb[person a scene d options h[a a d] c factor h[a a d] c description i[h[a a d] c] avoids h[a a d] c reason h[a a i[h[a a d] c] d] c] c[
 g act a[w[c[v options][v person v act v scene]][w[c[v factor][v person v act v scene]][w[c[v avoids][v person v act v scene]][c[v reason][v person v act v description v scene]]]]]
].
d nc[person a episode h[a d] c context d scope h[a d d] c] c[
 w[g scene d[c[v scope][v person v context v scene]]][f scene d[y[c[v scope][v person v context v scene]][c[v episode][v person v scene]]]]
].
'''


def generic_composed():
    text = format_graph(parse('n:\n' + definitions()), 'compact') + '\n'
    original = json.loads((ROOT / 'data/described-explanations-basis-v1.json').read_text(encoding='utf-8'))
    basis = {'version': 'motive-explanations-basis-v1', 'document': 'examples/v014/motive-explanations.noema',
        'primitives': deepcopy(original['primitives']), 'definitions': {
            'na': '要因記述の列が空でなく、各要因が同じ対象と結果の原因説明へ採用される。要因の真理、相互作用、最小性、これだけが原因であることは主張しない。',
            'nb': 'その人に関係する行為のうち、指定した要因が成立し、本人が行為を避け、その要因の記述が回避の理由として採用される行為が存在する。行為・本人・状況を全条件で共有する。',
            'nc': '指定した人物と文脈で評価対象の機会が空でなく、全ての評価機会で指定したエピソード条件が成立する。評価範囲を超える普遍的な性格判断は含まない。'},
        'unresolved': ['原因説明への採用は実在の因果機構や介入効果の証明ではない。列は各要因への採用を要求する読みであり、要因の連言だけを一体の原因にすることとは異なる。',
            '行為の選定、要因の内容と記述の対応、評価機会の選択と代表性は呼出側の前提である。動機や性格の一般理論を確立したものではない。']}
    audit_basis(parse(text), basis)
    return text, basis


def source_composed():
    doc = parse((ROOT / 'examples/v014/kant-release-transition.noema').read_text(encoding='utf-8'))
    statements, doc['statements'] = doc['statements'], []
    text = format_graph(doc, 'compact') + '\n' + definitions(False) + '''
r ma[a a d] c.r mb[a a d] c.r mc[a a d] c.r md[a a d] c.
r me[a a i[h[a a d] c] d] c.r mh[a d d] c.r mp[a] j[a].r mv[] a.r mw[] a.
d mf[person a scene d] c[k nb[v person v scene p ma p mb r[p mb] p md p me]].
d mg[person a scene d] c[k nb[v person v scene p ma p mc r[p mc] p md p me]].
d mj[person a] e[b context[k nc[v person p mf v context p mh]]].
d mk[person a] e[b context[k nc[v person p mg v context p mh]]].
d mq[group a] e[b context[g person a[w[k hg[k mp[v group] v person]][w[k aa[v person]][t[k mj[v person]][v context]]]]]].
d mr[group a] e[b context[g person a[w[k hg[k mp[v group] v person]][w[k aa[v person]][t[k mk[v person]][v context]]]]]].
d ms[group a] e[k kh[k mp[v group]]].
d mt[] j[i[h[a] e]][l[i[h[a] e]][r[p mq] r[p mr]]].
d mu[group a context d] c[k na[v group k mt[] r[p ms] v context]].
d mx[] e[b context[k mu[k mv[] v context]]].
'''
    doc = parse(text)
    doc['statements'] = statements
    text = format_graph(doc, 'compact') + '\ns[k uc[k mw[] k wa[] r[k mx[]] k wh[]]].\n'
    doc = parse(text)
    basis = deepcopy(json.loads((ROOT / 'data/kant-release-transition-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-motive-explanations-basis-v1', document='examples/v014/kant-motive-explanations.noema')
    basis['definitions'].update(generic_composed()[1]['definitions'])
    declarations = {d['name']: d for d in doc['declarations']}
    for name, labels, meaning in (
        ('ma', ['person', 'act', 'scene'], 'その人の行為選択を説明する際に、この状況で問題となる行為。実行済み・実行可能という条件とは別。'),
        ('mb', ['person', 'act', 'scene'], 'その人が、その行為に自分の努力・労力が要ると見込んでいる。実際の労力や能力不足とは区別する。'),
        ('mc', ['person', 'act', 'scene'], 'その人が、その行為による自分への害や危険を恐れている。客観的な危険の実在や程度を自動的に含まない。'),
        ('md', ['person', 'act', 'scene'], 'その人がその行為を行うことを避けている。単に未実行・実行不能であることとは区別する。'),
        ('me', ['person', 'act', 'factor_description', 'scene'], 'その人物・行為・状況について、記述された要因を行為回避の理由として採用する。実在の心理機構の証明とは別。'),
        ('mh', ['person', 'context', 'occasion'], 'その人の回避傾向をこの文脈で評価する対象の機会。単発の例から生涯の性格を断定しないための明示的な評価範囲。'),
        ('mp', ['group'], '説明対象の集団を構成する人々の列。集団という対象と列の対応を与え、割合の計算には既存の母集団条件も要求する。'),
        ('mv', [], 'この部分草案で説明対象とする集団。構成員の列はmpで与えられる。'),
        ('mw', [], '第二段落の原因説明を帰属させる談話節点。段落全体の完成を表す印ではない。')):
        d = declarations[name]
        basis['primitives'].append({'symbol': name, 'parameters': d['parameters'], 'result': d['result'], 'arguments': labels, 'meaning_ja': meaning})
    basis['definitions'].update({
        'mf': '問題となる行為で、労力を見込み、その行為を避け、労力の記述を回避理由として採用する例。',
        'mg': '問題となる行為で、害や危険を恐れ、その行為を避け、その恐れの記述を回避理由として採用する例。',
        'mj': '非空の評価機会全体でmfが成立する、労力を理由に避ける傾向の読解候補。',
        'mk': '非空の評価機会全体でmgが成立する、恐れを理由に避ける傾向の読解候補。',
        'mq': '説明対象の集団内に、mjに該当する人がいるという内容。全員や割合の大きさは主張しない。',
        'mr': '説明対象の集団内に、mkに該当する人がいるという内容。mqと同じ人であることを強制しない。',
        'ms': '同じ集団の列について、先行する移行と譲歩を含む既存khの割合の内容。',
        'mt': '原因として挙げる二つの要因mq・mrの記述の列。',
        'mu': '同じ集団の結果msについて、mtの二要因を原因説明へそれぞれ採用する。',
        'mx': '説明対象mvについてmuが成立するという内容。本文では、この内容の記述を著者へ帰属させる。'})
    basis['unresolved'] += generic_composed()[1]['unresolved'] + [
        'Faulheit・Feigheitを労力／恐れを理由にした回避傾向として構成する部分的な読解。程度、規範的評価、例外や傾向の確率的な意味はまだ含めていない。単なる決意不足・勇気不足の別名にはしていない。',
        '二要因をそれぞれ原因として挙げる読みを採る。要因が同じ個人に必ず共存することや、それぞれ単独で結果の十分条件となることは含めない。',
        '原文の後見人についての第二の結果は未接続。自然の比喩、語義の独立確認、原因の機構、段落の残部と原刊確認も残る。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def main():
    for compose, filename in ((generic_composed, 'data/motive-explanations-basis-v1.json'),
                              (source_composed, 'data/kant-motive-explanations-basis-v1.json')):
        text, basis = compose()
        for name, body in {basis['document']: text, filename: json.dumps(basis, ensure_ascii=False, indent=2) + '\n'}.items():
            path = ROOT / name
            if path.exists():
                if path.read_text(encoding='utf-8') != body:
                    raise ValueError('Stored motive explanation differs: ' + name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream:
                    stream.write(body)
    print('Distinct avoidance motives composed and attributed as causes of the population claim')


if __name__ == '__main__':
    main()
