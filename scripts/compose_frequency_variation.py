"""Compose frequency over independently selected comparison situations."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure

SOURCE = 'examples/v016/kant-recognized-example.noema'
SOURCE_BASIS = 'data/recognized-example-basis-v1.json'
LIBRARY = 'examples/v016/frequency-under-variation.noema'
BASIS = 'data/frequency-under-variation-basis-v1.json'
MEANING = '同じ基準に固定した比較範囲と通常性順序について、非空の極小比較状況すべてで、その状況の過不足ない非空・重複なしの適格事例列に応答が過半数かつ基準文脈の割合条件を満たす。状況の選択と状況内の頻度を二段階で評価し、基準状況の観測だけや一事例の成功と同一視しない。'
LIMITS = [
    '一般的性向を通常候補での全称条件へ、頻度を事例の割合へ分け、二つを組み合わせる構成である。自然言語の全一般文や全頻度副詞を単一の条件で定義したとはしない。',
    '比較範囲と通常性順序は応答の結果で選び直さない。候補は実際に生起した履歴に限定しないが、どの変化を許すかは利用者が説明する必要がある。',
    '事例は比較状況ごとに違ってよい。割合の判定基準は同じ基準文脈を保ち、失敗する状況だけ閾値を緩めない。通常候補間の事例を合算しない。',
    '各状況の事例列は有限・等重みである。無限母集団の測度、連続確率分布、観測から反事実的な傾向を推定する方法は実装していない。',
    'カントの現行本文・帰属・意味判断は変更しない。現行hzudにこの条件が含意されないことを検証し、直接採用に必要な比較範囲・語義・無修飾の萎縮の量化を未解決として明記する。',
]


@lru_cache(None)
def catalog():
    return load_catalog(ROOT, SOURCE_BASIS)


def definition():
    return '''
d r2bd[anchor d scenes h[d d] c preferred h[d d d] c population h[d] j[a] eligible h[a d] c response h[a d] c criterion h[b d] c complete h[j[a] d] c] c[
 k rqt4[i[scene d][c[v scenes][v anchor v scene]]
 i[first d second d][c[v preferred][v anchor v first v second]]
 i[scene d][w[c[v complete][c[v population][v scene] v scene]][
 k r7[c[v population][v scene] i[item a][c[v eligible][v item v scene]]
 i[item a][c[v response][v item v scene]] i[ratio b][c[v criterion][v ratio v anchor]]]
]]]
].
'''


def document(roots=('r7', 'rqt4')):
    old = catalog(); assert 'r2bd' not in old.entries
    d = deepcopy(old.document)
    d.update(declarations=closure(d, roots), statements=[])
    return parse(format_graph(d, 'compact') + definition())


def build():
    d = document(); old = catalog(); primitives = []; meanings = {}
    for row in d['declarations']:
        n = row['name']
        if row['kind'] == 'definition':
            meanings[n] = MEANING if n == 'r2bd' else old.entries[n]['meaning_ja']
        else:
            e = old.entries[n]
            primitives.append(dict(symbol=n, parameters=row['parameters'], result=row['result'],
                arguments=e['arguments'], meaning_ja=e['meaning_ja']))
    basis = dict(status='frequency_under_contextual_variation_not_source_replacement', document=LIBRARY,
        primitives=primitives, definitions=meanings, limitations=LIMITS,
        origin_sha256={SOURCE: digest((ROOT/SOURCE).read_bytes()), SOURCE_BASIS: digest((ROOT/SOURCE_BASIS).read_bytes())})
    return {LIBRARY: format_graph(d, 'compact')+'\n', BASIS: json.dumps(basis, ensure_ascii=False, indent=2)+'\n'}


def main():
    from scripts.audit_opening_scope import write_exact
    for path, body in build().items():
        write_exact(ROOT/path, body)
    print('Frequency and comparison-situation quantification composed without changing the manuscript', flush=True)


if __name__ == '__main__':
    main()
