"""Extend the preserved cut library with products, partial operations and beta."""
import json
from pathlib import Path

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis

ROOT = Path(__file__).resolve().parents[1]


def composed():
    text = (ROOT / 'examples/v011/real-cuts.noema').read_text(encoding='utf-8')
    text += (ROOT / 'examples/fragments/real-products.noema.inc').read_text(encoding='utf-8')
    doc = parse(text)
    basis = json.loads((ROOT / 'data/real-cuts-basis-v1.json').read_text(encoding='utf-8'))
    basis['version'] = 'real-products-basis-v1'
    basis['document'] = 'examples/v011/real-products.noema'
    basis['definitions'].update({
        'ca': '切断が0以上であるという順序条件。切断の妥当性は単独では検査しない。',
        'cb': '有効な切断に対する絶対値の構成式。非負なら元の切断、負なら符号反転を用いる。',
        'cc': '非負の有効な二切断の積の構成式。負の有理数、または正の切断要素x,yの積より小さい有理数を含む。非負入力という前提を持つ内部式。',
        'cd': '有効な二切断の符号付きの積の構成式。絶対値同士の積を作り、符号が異なる場合は符号反転する。',
        'ce': 'left,right,resultが全て有効な切断で、resultがcdの構成式と外延的に同じであるという乗算関係。',
        'cf': '正の有効な切断の逆数の構成式。q<0、または切断外の正の上側値uがありq*u<1となるqを含む。正数入力という前提を持つ内部式。',
        'cg': '非零の有効な切断の符号付き逆数の構成式。正数にはcf、負数には符号反転・cf・符号反転を適用する。',
        'ch': '入力と結果が有効な切断、入力が非零、結果がcgと同じという逆数関係。零には成立する結果がない。',
        'ci': '分子・分母・結果が有効な切断、分母が非零、結果が分子と分母の逆数の積であるという除算関係。',
        'cj': '非負の有効な切断の非負平方根の構成式。q<0またはqの二乗が入力切断に入る場合にqを含む。定義域外では平方根とは解釈しない内部式。',
        'ck': '入力と結果が有効な切断、入力が非負、結果がcjと同じという平方根関係。負数には成立する結果がない。',
        'cl': '正のlight、絶対値がlightより小さいspeedについて、ratio=speed/light、root=非負平方根(1-ratio*ratio)、factor=1/rootを満たす実切断の関係。原文βの数式の部分記述。',
        'cm': '有理数座標についてlight>0、speedの二乗<lightの二乗、factor>0、factorの二乗*(lightの二乗-speedの二乗)=lightの二乗を表す代数的検査条件。clとの切断上の同値性は機械的には未証明。'})
    basis['unresolved'] = [
        '全ての有効な実切断について、積・逆数・平方根の構成が正当な切断となることと実数体の一般法則の機械的証明。定義の数学的理由は文書に記録する。',
        '原文の速度と係数を物理量・基準系・単位へ接続し、前後の変換式とともに原文の意味を確認する作業。',
        '偏微分・連続性・積分など、後続の式に必要な理論。',
        '有限標本で有理数・実数の全域を代用しない。非線形で量化が混在する式は、実数上の解だけから有理数の真偽を判定しない。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def main():
    text, basis = composed()
    for name, body in {basis['document']: text, 'data/real-products-basis-v1.json': json.dumps(basis, ensure_ascii=False, indent=2) + '\n'}.items():
        path = ROOT / name
        if path.exists():
            if path.read_text(encoding='utf-8') != body:
                raise ValueError('Stored real products differ: ' + name)
        else:
            with path.open('x', encoding='utf-8', newline='\n') as stream:
                stream.write(body)
    print('Real products, partial inverse/root and beta relation composed')


if __name__ == '__main__':
    main()
