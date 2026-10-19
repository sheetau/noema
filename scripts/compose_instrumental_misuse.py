"""Bind unexamined expression use, misuse and its causal act in one relation."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure

PARENT = 'examples/v016/kant-confirmed-incapacity.noema'
PARENT_BASIS = 'data/confirmed-incapacity-basis-v1.json'
FULL = 'examples/v016/kant-instrumental-misuse.noema'
CORE = 'examples/v016/instrumental-misuse-core.noema'
BASIS = 'data/instrumental-misuse-basis-v1.json'
ANNOTATIONS = 'data/instrumental-misuse-identifiers-v1.json'
MEANINGS = {
    'r2ep': '同じ本人が同じ対象を同じ活動で使い、その対象をその活動へ適用することを吟味する本人の判断が、同じ文脈にはない。使用・判断・対象・吟味の四関係を引数とする一般形。固定した一項の式への具体化、無意識、能力欠如、誤用、過去や将来の判断不在は要求しない。',
    'r2eq': '同じ対象・本人・自然的能力・活動・基準について、表現を吟味せず使うr2ep、同じ能力の同じ活動での誤用hn2、活動の生起、同じ活動から同じ本人のh26への結果生成、およびその結果の成立を結ぶ。別の行為の誤用や原因を借りない。',
    'r2er': '規定または定型表現h27である同じ対象と同じ本人に、r2eqを満たす能力と使用活動があるという対象側の部分関係。各条件に別々の活動を存在させて結合しない。',
    'r2es': '対象と利用者の二位置を、厳密に二要素の列からr2erへ渡す。足枷の描写側と同じ位置対応を保つ。',
    'r2et': '第三文の同じ箇所で、機械的な使用と誤用を同じ因果的活動へ接続した対象側r2esを、既存の身体的な足枷h2bで描く帰属。対象側や身体側の実際の成立を、この帰属から導かない。',
}
LIMITS = [
    'mechanischenを、この活動で表現の適用を本人が吟味しないという既存の部分的な読みとして接続する。一項の式の具体化を機械的使用の必須条件にせず、規定の使用にも同じ一般構成を使えるようにする。物理的な機械、無意識、反復の全語義は未完。',
    '語句ごとの独立した存在条件を一つの同じ本人・能力・活動へ結ぶ。合理的使用から誤用への言い直しho2は保持し、合理的使用の単純な否定を誤用にせず、正の評価だけでは新しい対象側を満たさない。',
    '対象の分類h27は既存の規定hd2と定型表現h22を使う。規定の制定・拘束性、定型表現の任意の型・引数数の基礎説明、二種類の一般化と列挙の作用範囲は未完である。',
    'h26の指定された将来範囲内の持続を継承する。これを無期限の持続やimmerwährendenの語義全体と同一視しない。使用がなくても永久に未成熟であるという法則や、必ずその生涯で脱出できないという原文判断は追加しない。',
    '実際の結果生成g3と結果の成立を要求する部分的な対象関係であり、一般的な道具の目的・性向・潜在的な働き全体を定義したものではない。どの因果・持続の読みが第三文全体に適するかは引き続き検討する。',
    '原文全体の意味一致は未確認。今回の対応は既存範囲の機械的使用・誤用と足枷を同じ活動へ接続する記録であり、接続詞や持続句を新たに対応済みへ数えない。',
]


@lru_cache(None)
def parent(): return load_catalog(ROOT, PARENT_BASIS)


def build():
    old = parent(); doc = deepcopy(old.document)
    assert not set(MEANINGS) & set(old.entries)
    size = len(doc['declarations']); statements = doc['statements']; doc['statements'] = []
    doc = parse(format_graph(doc, 'compact') + '''
d r2ep[person a object a act a point d use h[a a a d] c judgments h[a a d] c matters h[a a d] c examines h[a a d] c] c[
 w[c[v use][v person v object v act v point]][u[g judgment a[w[c[v judgments][v person v judgment v point]][w[c[v matters][v judgment v object v point]][c[v examines][v judgment v act v point]]]]]]
].
d r2eq[object a person a faculty a act a point d] c[
 w[k r2ep[v person v object v act v point p hx2 p fa p fb p hz2]][w[t[k hn2[v person v faculty v act]][v point]][w[k dg[v act v point]][w[k g3[v act v person r[p h26] v point]][t[k h26[v person]][v point]]]]]
].
d r2er[object a person a] e[b point[w[t[k h27[v object]][v point]][g faculty a[g act a[k r2eq[v object v person v faculty v act v point]]]]]].
d r2es[participants j[a]] e[k rbv[p r2er v participants]].
d r2et[] c[k rbu[k h2d[] k wa[] r[p r2es] r[p h2b] k wh[]]].
''')
    assert len(statements) == 54 and statements[52]['body']['symbol'] == 'h2c'
    assert statements[10]['body']['symbol'] == 'ho2' and statements[53]['body']['symbol'] == 'h3b'
    statements[52] = dict(kind='assert', body=dict(kind='call', symbol='r2et', arguments=[]))
    doc['statements'] = statements; doc = parse(format_graph(doc, 'compact'))
    core = deepcopy(doc); core.update(declarations=closure(doc, ['r2et']), statements=doc['statements'][52:53])
    added = doc['declarations'][size:]; assert len(added) == 5
    basis = dict(status='mechanical_use_and_misuse_bound_to_same_causal_act_candidate', document=FULL,
        parent=PARENT, inherited_meaning_basis=PARENT_BASIS, primitives={}, definitions=MEANINGS,
        new_signatures={d['name']: {k: d[k] for k in ('parameters', 'result')} for d in added}, limitations=LIMITS)
    body = format_graph(doc, 'compact') + '\n'
    annotations = json.loads((ROOT / 'data/confirmed-incapacity-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    encode = lambda x: json.dumps(x, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n', BASIS: encode(basis), ANNOTATIONS: encode(annotations)}


if __name__ == '__main__':
    from scripts.audit_opening_scope import write_exact
    for path, body in build().items(): write_exact(ROOT / path, body)
    print('Five definitions; mechanical use and misuse share the causal activity', flush=True)
