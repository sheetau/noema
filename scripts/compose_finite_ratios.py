"""Eliminate the unique ratio witness for a guarded finite population."""
from copy import deepcopy
import json

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from scripts.compose_limits import ROOT
from scripts.compose_proportions import generic_composed as proportions


def definitions():
    return '''
r pa[b b] b.
d pb[population j[a] property h[a] c] b[k pa[k hf[v population v property] d[v population]]].
d pc[population j[a] property h[a] c] c[k hj[v population v property k pb[v population v property]]].
d pd[population j[a] domain h[a] c property h[a] c criterion h[b] c] c[
 k hk[v population v domain v property v criterion k pb[v population v property]]
].
'''


def additions(doc):
    d = next(d for d in doc['declarations'] if d['name'] == 'pa')
    return {'primitives': [{'symbol': 'pa', 'parameters': d['parameters'], 'result': d['result'],
        'arguments': ['numerator', 'denominator'],
        'meaning_ja': '非零の分母では有理数の正確な商を返す補助関数。分母0の場合だけ戻り値を0と規約する全域化であり、通常の除算が0除算を許すという主張ではない。空集団の割合は別のhj条件で必ず拒否する。'}],
        'definitions': {
            'pb': '有限列の性質を満たす出現数を列長で割った候補値。重複・空列・対象の型を検査する前の値であり、単独では有効な割合とは呼ばない。',
            'pc': '計算した候補値pbに既存hjを適用し、非空性・重複の不在・指示関数の規約・比率の範囲・人数との等式を検査する。',
            'pd': '計算した候補値pbに既存hkを適用し、母集団の種類と文脈的な比率基準も要求する。全有理数の候補リストを探索する処理ではない。'}}


def generic_composed():
    text, basis = proportions()
    doc = parse(text + definitions())
    basis = deepcopy(basis)
    basis.update(version='finite-ratios-basis-v1', document='examples/v014/finite-ratios.noema')
    extra = additions(doc)
    basis['primitives'] += extra['primitives']
    basis['definitions'].update(extra['definitions'])
    basis['unresolved'] += ['等価性は有理数の演算と指示関数の意味規約の下で成立する。任意の誤った除算実装について旧量化と一致するという保証ではない。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def source_composed():
    doc = parse((ROOT / 'examples/v014/kant-easy-guardians.noema').read_text(encoding='utf-8'))
    base = deepcopy(doc)
    base['declarations'], base['statements'] = [], []
    for d in doc['declarations']:
        if d['name'] == 'hq':
            text = format_graph(base, 'compact') + '\n' + definitions() + '''
d hq[population j[a] property h[a] e] e[
 b scene[w[k hr[v population v scene]][
  k pd[v population p aa i[person a][t[c[v property][v person]][v scene]] i[ratio b][k hs[v ratio v scene]]]
 ]]
].
'''
            base = parse(text)
        else:
            base['declarations'].append(deepcopy(d))
    base['statements'] = doc['statements']
    text = format_graph(base, 'compact') + '\n'
    basis = deepcopy(json.loads((ROOT / 'data/kant-easy-guardians-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-finite-ratio-basis-v1', document='examples/v014/kant-finite-ratio.noema')
    extra = additions(base)
    basis['primitives'] += extra['primitives']
    basis['definitions'].update(extra['definitions'])
    basis['definitions']['hq'] = '有限母集団の人数から比率を直接計算し、既存の型・非空性・重複・文脈基準と母集団の完全性を検査する。正しい演算規約の下で旧版の唯一の比率の存在条件と同値であり、無限の有理数領域を有限候補で代用しない。'
    basis['unresolved'] += [
        '過去のhqの全有理数量化に関する実行拒否は、この版では一意な比率の直接計算へ置き換えた。旧文書と検査記録は変更しない。Noema一般の有理数量化を有限列挙へ置換する機能ではない。',
        '計算可能になったことは、現実の母集団、本文の解釈、原因の実在、論文全文の意味確認の証明ではない。']
    audit_basis(parse(text), basis)
    return text, basis


def main():
    for compose, filename in ((generic_composed, 'data/finite-ratios-basis-v1.json'),
                              (source_composed, 'data/kant-finite-ratio-basis-v1.json')):
        text, basis = compose()
        for name, body in {basis['document']: text, filename: json.dumps(basis, ensure_ascii=False, indent=2) + '\n'}.items():
            path = ROOT / name
            if path.exists():
                if path.read_text(encoding='utf-8') != body:
                    raise ValueError('Stored finite ratio differs: ' + name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream:
                    stream.write(body)
    print('Unique finite ratios computed directly; invalid populations remain rejected')


if __name__ == '__main__':
    main()
