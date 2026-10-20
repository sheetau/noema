"""Separate the fifth sentence's count from its concessive background."""
from copy import deepcopy
from functools import lru_cache
import json

from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure
from scripts.compose_scalar_backgrounds import PAIR

PARENT = 'examples/v016/kant-fourth-sentence.noema'
PARENT_BASIS = 'data/fourth-sentence-basis-v1.json'
FULL = 'examples/v016/kant-fifth-sentence-scope.noema'
CORE = 'examples/v016/fifth-sentence-scope-core.noema'
BASIS = 'data/fifth-sentence-scope-basis-v1.json'
ANNOTATIONS = 'data/fifth-sentence-scope-identifiers-v1.json'
MEANINGS = {
    'r2iz': '同じ人の自立達成h4qを認めた著者waの通常予想keが非空で、全候補ではh4qが成立し、達成と確かな知的活動を結ぶh5kが成立しないというjaの背景。現実側での達成や成功者数はこの背景だけでは要求しない。',
    'r2ja': '指定された列の各人について、同じ文脈で実際の達成と知的活動h5kを持つ人に限りr2izの譲歩背景を要求する。背景の成立を人数に数える条件へ加えず、非該当者に譲歩を要求しない。全列挙と評価条件は呼出側で検査する。',
    'r2jb': '指定された同じ対象列についてh5wの存在を伴う少数者数と数量代替の排除を前景内容にする。h5kの達成・活動、h4tの評価条件、対象範囲、上限、数量の比較条件を保持し、予想keは実行しない。',
    'r2jc': '指定対象列がこの文脈の人aaかつ範囲h4iの全員を重複なく尽くし、h5mの評価条件を満たし、該当者にr2jaの背景が成立する内容。少数者数、正の成功者数、数量代替の排除は背景側へ重複させない。',
    'r2jd': '対象全域を表す有限列が存在し、前景r2jbが成立する内容。任意の有限列への量化であり、有限評価用の候補列への置換ではない。',
    'r2je': '対象全域を表す有限列が存在し、背景r2jcが成立する内容。前景と同じaa・h4i・h5k・h4t・文脈を用いるため、別の成功者集合を選ぶことはできない。列の順序の一致や同じ列個体は要求しない。',
    'r2jf': '閉じた前景r2jdと背景r2jeを既存rstの対にする。前景を否定しても背景の記述はそのまま残り、対を作るだけでは内容を実行しない。',
    'r2jg': '第五文の結論箇所h5tでr2jfの数量前景と譲歩背景を同じ著者wa・文脈whへrqtvで帰属する。背景の範囲h222dを区別し、直前の条件付き描写h3aとその理由h3sからこの結論を提示するud、および理由から結論への本文順序ueを保持する。論理的導出や人数の真理は主張しない。',
}
REFERENCE = '固定原文kant-1784:u0010の第五文末、und dennoch einen sicheren Gang zu thun.の文字範囲。譲歩背景の範囲への参照であり、身体描写・知的活動の全意味の確認済みを表す基本関係ではない。'
LIMITS = [
    '第五文の作用範囲の改善であり、一文全体または第三段落全体の意味確認ではない。',
    'giebt esは一人以上いる読み、nur Wenigeは同じ母集団での正の上限未満と数量代替排除、dennochは実際の該当者に分配する背景として読む。数値上限・比較条件・予想候補は文脈上の解釈入力であり、原文へ固定値を補わない。',
    'Daherの根拠を直前の第四文の主節と理由へ限定する明示的な読みを採る。段落の先頭までを直接の根拠集合に含める別の読みを唯一に排除するものではない。',
    'jaは全ての通常予想候補で前提成立・帰結不成立を要求する操作化。確率の程度、韻律、nurやdennochの全用法を定義するものではない。',
    '現実のh5kがh4qを含む接続を保持する。旧h5pのjbを背景jaへ分離したことで、実際の成功者の譲歩条件が失われないことを構造と境界検査で確認する。',
    '自己形成h4m・h4n、確かな知的活動h5c・h5dと身体歩行h4z、解放の比喩、自己活動の因果が並列された二つの成果に及ぶ範囲の原文確認が残る。先行の合成と検査を再利用し、検査成功だけでこれらの意味判断を済ませない。',
    '有限評価器は両辺を評価するため、非該当者の未定義コールバックを短絡で隠せることを保証しない。未知入力は偽へ補わず、任意の有限列全域への量化を有限候補で代用しない。',
]


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


def additions():
    return '''
r h222d[] a.
d r2iz[person a] e[b point[k ja[v person k h4q[v person] r[p h4q] k h5k[v person] v point
 i[subject a premise i[h[a] e] context d alternative d][k ke[k wa[] v subject v premise v context v alternative]]]]].
d r2ja[population j[a] context d] c[q[v population][e[n p a b][n p a b]][
 i[valid c person a][w[v valid][y[t[k h5k[v person]][v context]][t[k r2iz[v person]][v context]]]]]].
d r2jb[population j[a]] e[b context[k h5w[v population v context]]].
d r2jc[population j[a]] e[b context[w[
 k rcm[v population i[person a][w[k aa[v person]][k h4i[v person v context]]]]
 ][w[k h5m[v population v context]][k r2ja[v population v context]]]]].
d r2jd[] e[b context[g population j[a][t[k r2jb[v population]][v context]]]].
d r2je[] e[b context[g population j[a][t[k r2jc[v population]][v context]]]].
d r2jf[] ''' + PAIR + '''[k rst[r c[k r2jd[]] r c[k r2je[]]]].
d r2jg[] c[w[k rqtv[k h5t[] k wa[] k r2jf[] k h5t[] k h222d[] k wh[]]][w[
 k ud[k wa[] i[node a][x[e[v node][k h3a[]]][e[v node][k h3s[]]]] k h5t[] k wh[]]
 ][k ue[k h3s[] k h5t[] k wh[]]]]].
'''


def build():
    old = parent()
    doc = deepcopy(old.document)
    statements, doc['statements'] = doc['statements'], []
    assert not (set(MEANINGS) | {'h222d'}) & set(old.entries)
    doc = parse(format_graph(doc, 'compact') + additions())
    assert statements[15]['body']['symbol'] == 'h5z'
    statements[15] = dict(kind='assert', body=dict(kind='call', symbol='r2jg', arguments=[]))
    doc['statements'] = statements
    core = deepcopy(doc)
    core.update(declarations=closure(doc, ['r2jg', 'rsw', 'rsx', 'rsy']),
                statements=[statements[15]])
    added = doc['declarations'][len(old.document['declarations']):]
    basis = dict(status='fifth_sentence_count_and_concessive_scope_partial',
                 document=FULL, parent=PARENT, inherited_meaning_basis=PARENT_BASIS,
                 definitions=MEANINGS,
                 primitives={'h222d': dict(parameters=[], result='individual',
                                           arguments=[], meaning_ja=REFERENCE)},
                 new_signatures={d['name']: {k: d[k] for k in ('parameters', 'result')}
                                 for d in added},
                 limitations=LIMITS)
    body = format_graph(doc, 'compact') + '\n'
    annotations = json.loads((ROOT / 'data/fourth-sentence-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    encode = lambda value: json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n',
            BASIS: encode(basis), ANNOTATIONS: encode(annotations)}
