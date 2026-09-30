"""Compose a husbandry role and bind its possessive figurative depiction."""
from copy import deepcopy
import json

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from scripts.compose_limits import ROOT
from scripts.compose_persistence import generic_composed as persistence


def definitions():
    def both(*terms):
        result = terms[-1]
        for term in reversed(terms[:-1]):
            result = f'w[{term}][{result}]'
        return result
    duration = both('c[v scope][v earlier]', 'c[v scope][v later]',
                    'c[v before][v earlier v later]')
    care = both('c[v keepers][v keeper]', 'c[v human][v keeper]',
                'c[v maintained][v keeper v being v point]',
                'c[v managed][v keeper v being v point]',
                'c[v purpose][v keeper v being v point]')
    body = both('c[v animal][v being]', 'u[c[v human][v being]]',
                'k tb[v history v scope v before]', f'g earlier d[g later d[{duration}]]',
                f'f point d[y[c[v scope][v point]][g keeper a[{care}]]]')
    return ('\nd rab[being a keepers h[a] c history h[d] c scope h[d] c before h[d d] c '
            'human h[a] c animal h[a] c maintained h[a a d] c managed h[a a d] c '
            f'purpose h[a a d] c] c[{body}].\n')


def generic_composed():
    text, basis = persistence()
    doc = parse(text + definitions())
    basis = deepcopy(basis)
    basis.update(version='husbandry-depiction-basis-v1', document='examples/v014/husbandry-depiction.noema')
    basis['definitions']['rab'] = '非人の動物について、同じ履歴内の間の抜けない非零期間の全範囲で、人である飼い手が維持管理・行動等の管理・その管理に結び付く利用目的を持つ。同じ時点の三関係を同じ飼い手と動物へ結ぶ。飼い手の交代を許す。'
    basis['unresolved'] += [
        '動物の分類、飼育の管理責任、利用目的は引数の意味規約で与える。この条件だけで動物の生物学的定義や飼育の歴史全体を構成したとはしない。',
        '飼育上の役割を構成する条件であり、家畜と愛玩動物、飼育下の野生動物、救護対象の境界は追加の目的・慣習の規約を要する。',
        '所有者であることと飼育する役割は別条件である。実際に給餌等が成功したこと、建物の中にいること、飼い手の全員が全時点で働くことは要求しない。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def source_composed():
    doc = parse((ROOT / 'examples/v014/kant-caused-conditions.noema').read_text(encoding='utf-8'))
    statements, doc['statements'] = doc['statements'], []
    text = format_graph(doc, 'compact') + definitions() + '''
r qd[a] c.r qe[a a d] c.r ql[a a d] c.r qm[a a d] c.r qn[a a d] c.
r qo[a d d] c.r qr[a d d] c.r qp[] a.
d qj[person a] e[b context[w[k aa[v person]][w[k dj[v person v context]][
 g guardian a[w[k hg[k mp[k db[]] v guardian]][w[k aa[v guardian]][k dc[v guardian v person v context]]]]
]]]].
d qk[being a] e[b context[w[k qn[k db[] v being v context]][
 k rab[v being i[keeper a][k hg[k mp[k db[]] v keeper]]
  i[point d][k qr[v being v context v point]] i[point d][k qo[v being v context v point]]
  p dd p aa p qd p qe p ql p qm]
]]].
d qq[] c[k qh[k qp[] k wa[] r[p qj] r[p qk] k wh[]]].
'''
    doc = parse(text)
    doc['statements'] = statements
    # A figurative annotation is an attribution, not an assertion of qj or qk.
    doc = parse(format_graph(doc, 'compact') + '\ns[k qq[]].\n')
    basis = deepcopy(json.loads((ROOT / 'data/kant-caused-conditions-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-husbandry-depiction-basis-v1', document='examples/v014/kant-husbandry-depiction.noema')
    basis['definitions']['rab'] = generic_composed()[1]['definitions']['rab']
    declarations = {d['name']: d for d in doc['declarations']}
    for name, args, meaning in (
        ('qd', ['being'], '動物に分類される生物である。人かどうかはaaで別に判定する。分類の生物学的な基礎説明は未完。'),
        ('qe', ['keeper', 'being', 'point'], 'この時点で、その飼い手がその生物の生存に必要な条件を継続的に管理する役割を担う。役割の不履行や一時的な給餌の不在を、役割の不在と同一視しない。'),
        ('ql', ['keeper', 'being', 'point'], '同じ飼い手が、その生物の行動・移動・生活条件を飼育のために管理する立場を持つ。単なる観察や一度だけの接触とは区別する。'),
        ('qm', ['keeper', 'being', 'point'], '同じ飼い手によるその生物の維持管理が、人間の生活のためにその生物の活動・産物等を利用する目的に結び付く。具体的な産物や目的達成は固定しない。'),
        ('qn', ['owner', 'being', 'context'], 'この描写でその生物がその所有主体に属するものとして位置付けられる。飼育担当者や場所の同一性だけからは導かない。所有制度や法的正当性の一般説明は未完。'),
        ('qo', ['being', 'context', 'point'], 'この生物の飼育役割をこの文脈で評価する期間。履歴内の非空で間の抜けない期間であることはtbで検査する。'),
        ('qr', ['being', 'context', 'point'], 'この生物について飼育役割を評価する同じ時間的履歴。別の描写世界や別個体の履歴と混ぜない。'),
        ('qp', [], '対象者たちを後見人たちの家畜として描写する談話箇所。')):
        d = declarations[name]
        basis['primitives'].append({'symbol': name, 'parameters': d['parameters'], 'result': d['result'],
            'arguments': args, 'meaning_ja': meaning})
    basis['definitions'].update({
        'qj': '現在の対象範囲djに属する人であり、同じ後見人集団の人である構成員がその人の監督の立場dcを持つという対象側の性質。動物分類や所有は含めない。',
        'qk': '同じ後見人集団に属するものとして描かれ、その集団内の飼い手たちが非人の動物を継続的に管理して生活に利用するという描写側の性質。各飼い手が個別の所有者であることは要求しない。',
        'qq': '著者がqjの対象をqkとして非字義的に提示する。所有主体と飼い手の集団を同じdbへ結び、対象と描写の内容は実行評価しない。'})
    basis['unresolved'] += generic_composed()[1]['unresolved'][-3:] + [
        'Hausviehを、人間の生活のために維持管理され利用される動物という飼育上の役割から部分的に構成した。分類や目的に関する境界事例と原文の評価的効果は未確定。',
        '飼育・帰属を描写側qkへ加え、対象者が文字通り動物であるという主張は追加していない。集団dbを所有主体とする読みであり、各後見人の単独所有・所有権の正当性を含めない。',
        'qqの新しい本文文は、既存qhと同じ比喩提示の帰属である。描写の事実認定や、家畜の語義全体の完成として数えない。',
        'ruhigの穏順さ、身体的な歩行器と閉じ込め、転倒・歩行、比喩の評価的効果、譲歩・焦点、原刊照合と全文の意味確認は残る。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def main():
    for compose, filename in ((generic_composed, 'data/husbandry-depiction-basis-v1.json'),
                              (source_composed, 'data/kant-husbandry-depiction-basis-v1.json')):
        text, basis = compose()
        for name, body in ((basis['document'], text), (filename, json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            path = ROOT / name
            if path.exists():
                if path.read_text(encoding='utf-8') != body:
                    raise ValueError('Stored husbandry depiction differs: ' + name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream:
                    stream.write(body)
    print('Sustained husbandry, ownership and nonliteral attribution composed')


if __name__ == '__main__':
    main()
