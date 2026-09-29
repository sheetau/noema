"""Bind low burden to the same successful method and preserve role targets."""
from copy import deepcopy
import json

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from scripts.compose_limits import ROOT
from scripts.compose_contextual_ability import generic_composed as ability


def definitions():
    return '''
d nd[actor a goal e context d available h[a a d] c outcomes h[a a d d] c selected h[a a d d] c cost h[a a d] b easy h[b] c] c[
 g plan a[w[c[v available][v actor v plan v context]][w[k xa[v actor v plan v context v outcomes v selected]][w[f end d[y[c[v selected][v actor v plan v context v end]][t[v goal][v end]]]][c[v easy][c[v cost][v actor v plan v context]]]]]]
].
'''


def generic_composed():
    text, basis = ability()
    doc = parse(text)
    doc['schema_version'] = doc['lexicon_version'] = '0.14'
    text = format_graph(parse(format_graph(doc, 'compact') + definitions()), 'compact') + '\n'
    basis = deepcopy(basis)
    basis.update(version='easy-roles-basis-v1', document='examples/v014/easy-roles.noema')
    basis['definitions']['nd'] = '実行できる同じ方法について、評価対象の結果が非空で想定結果の部分集合となり、全評価結果で目的を達成し、その方法の負担評価値が文脈の容易さの基準を満たす。成功する方法と負担の小さい別の方法を混ぜない。'
    basis['unresolved'] += ['負担の尺度と容易さの基準は引数で明示する。低負担の方法による達成可能性を記述し、現在の目的達成・制度的な許可・あらゆる意味での容易さを含めない。']
    audit_basis(parse(text), basis)
    return text, basis


def source_composed():
    doc = parse((ROOT / 'examples/v014/kant-motive-explanations.noema').read_text(encoding='utf-8'))
    statements, doc['statements'] = doc['statements'], []
    doc['declarations'] = [d for d in doc['declarations'] if d['name'] != 'mx']
    text = format_graph(doc, 'compact') + '\n' + definitions() + '''
r oa[a a d] c.r ob[a a a d] c.r oc[a a d] b.r oe[b d] c.r of[a a d] c.
d od[actor a target a] e[b scene[w[u[e[v actor][v target]]][g act a[w[k oa[v actor v act v scene]][k ob[v act v actor v target v scene]]]]]].
d og[actor a target a context d] c[k nd[v actor k od[v actor v target] v context p ae p af p ap p oc i[value b][k oe[v value v context]]]].
d oi[group a person a context d] c[w[k hg[k mp[v group] v person]][t[k kg[v person]][v context]]].
d oj[group a targets h[a] c context d] c[
 w[g target a[c[v targets][v target]]][w[g actor a[k of[v group v actor v context]]][
 f actor a[y[k of[v group v actor v context]][w[k aa[v actor]][f target a[y[c[v targets][v target]][w[k aa[v target]][w[u[e[v actor][v target]]][k og[v actor v target v context]]]]]]]
 ]]]
].
d ok[group a] e[b context[k oj[v group i[target a][k oi[v group v target v context]] v context]]].
d ol[group a context d] c[w[k mu[v group v context]][k na[v group k mt[] r[p ok] v context]]].
d mx[] e[b context[k ol[k mv[] v context]]].
'''
    doc = parse(text)
    doc['statements'] = statements[:1]
    text = format_graph(doc, 'compact') + '\ns[w[k uc[k mw[] k wa[] r[k mx[]] k wh[]]][k ue[k wg[] k mw[] k wh[]]]].\n'
    doc = parse(text)
    basis = deepcopy(json.loads((ROOT / 'data/kant-motive-explanations-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-easy-guardians-basis-v1', document='examples/v014/kant-easy-guardians.noema')
    basis['definitions']['nd'] = generic_composed()[1]['definitions']['nd']
    decls = {d['name']: d for d in doc['declarations']}
    for name, labels, meaning in (
        ('oa', ['actor', 'act', 'scene'], 'その行為を、その人自身が発意して行う。単に他者からその立場に任命されたという事実とは区別する。'),
        ('ob', ['act', 'actor', 'target', 'scene'], 'その行為で、actorがtargetの判断・行為を指図する立場を自分のものとして引き受ける、または称する。正当な権利、周囲の承認、法制度上の後見人という資格は別条件である。'),
        ('oc', ['actor', 'plan', 'context'], 'この人がこの方法を用いる際の負担の評価値。同じ方法の成功条件へ結び、尺度の解釈は文脈の前提として与える。'),
        ('oe', ['burden', 'context'], 'この文脈で、その負担評価値を「これほど容易」と扱う基準。固定した数値や単位は原文へ補わない。'),
        ('of', ['group', 'actor', 'context'], 'この集団に対する「他者」として文脈で評価する人の範囲。全人類を無条件に全称化しない。')):
        d = decls[name]
        basis['primitives'].append({'symbol': name, 'parameters': d['parameters'], 'result': d['result'], 'arguments': labels, 'meaning_ja': meaning})
    basis['definitions'].update({
        'od': '本人と異なる対象に対し、自ら発意した行為によって、その対象の判断・行為を指図する立場を自分のものとして引き受ける内容。',
        'og': '同じ行為者・対象について、odを評価範囲内で達成できる低負担の方法がある。現在その立場にあることや正当な権限は主張しない。',
        'oi': '既存の母集団に属し、先行する移行・譲歩・持続を含むkgに該当する人。直前の割合表現が数えた人々を対象範囲にする。',
        'oj': '対象範囲と文脈上の他者の範囲が共に非空で、全て人であり、各他者が各対象と異なっていて、その対象へのogが成立する。対象ごとに異なる方法を許し、集団全員への一括達成は要求しない。',
        'ok': '同じ集団内のoiを対象としてojが成立する内容。指示語の対象を無関係な人々へ置き換えない。',
        'ol': '既存の第一の結果msと第二の結果okのそれぞれについて、同じ二要因mtを原因説明へ採用する。',
        'mx': '同じ集団mvについて二つの結果を説明するolの内容。著者への帰属と前段落より後という本文順序を保つ。'})
    basis['unresolved'] += [generic_composed()[1]['unresolved'][-1],
        'Anderenの文脈上の範囲と、その範囲内で各対象へ容易に立場を引き受けられるという読解を明示した。一般的傾向や例外、複数対象への同時達成の読みとは区別し、唯一の語義とはしない。',
        '後見の歴史的・制度的な全意味、aufwerfenの評価的な響き、容易さの尺度と変化の含意は未確定。二つの結果の原因説明を接続したが、第一文の意味確認や段落全体の完成ではない。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def main():
    for compose, filename in ((generic_composed, 'data/easy-roles-basis-v1.json'),
                              (source_composed, 'data/kant-easy-guardians-basis-v1.json')):
        text, basis = compose()
        for name, body in {basis['document']: text, filename: json.dumps(basis, ensure_ascii=False, indent=2) + '\n'}.items():
            path = ROOT / name
            if path.exists():
                if path.read_text(encoding='utf-8') != body:
                    raise ValueError('Stored easy role differs: ' + name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream:
                    stream.write(body)
    print('Easy attainment, assumed authority and the second causal result connected')


if __name__ == '__main__':
    main()
