"""Bind both sides of a depicted plural reference without literal identity."""
from copy import deepcopy
from functools import lru_cache
import json

from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure
from scripts.compose_limits import v, call, app, op, both, quant, lam, definition

PARENT = 'examples/v016/kant-occasional-continuation.noema'
PARENT_BASIS = 'data/occasional-continuation-basis-v2.json'
FULL = 'examples/v016/kant-depicted-referents.noema'
CORE = 'examples/v016/depicted-referents-core.noema'
LIBRARY = 'examples/v016/paired-reference-ranges.noema'
BASIS = 'data/depicted-referents-basis-v1.json'
ANNOTATIONS = 'data/depicted-referents-identifiers-v1.json'
MEANINGS = {
    'r2gf': '二つの非空な指定範囲の全要素が、与えた対応関係に参加する。対応辺の両端も必ず各範囲に属する。片側だけの網羅、無対応の要素、範囲外への辺を認めない。単射・一対一・物理的同一性は要求せず、多対多を許す。',
    'r2gg': '非空の人物範囲の各人について、同じ人に属する二つの対象範囲と対応をr2gfで検査する。範囲外の人に属する選択や対応辺が一つでもあれば不整合とする。他人の対応を借りたり、都合の悪い選択を先に除いたりしない。',
    'r2gh': '第一文からの同じ提示文脈の人物範囲について、第四文の描写上の除去対象h2sと、第三文の種類記述r2fhを受ける指示対象hzzzmを、同じ人のhzzznによって両側とも網羅する。種類記述は引用のまま渡し、規定や表現の内容・現実の作用を実行しない。',
    'r2gi': '第三文r2geの同じ著者・主張・足枷の比喩・本文順序を保ち、同じ提示文脈でr2ghの指示対応を要求する。第四文から第三文への逆順も拒否する。描写上の時点で指示対象を選び直さない。',
    'r2gj': '既存h3bの除去と不確かな跳躍の条件的描写への帰属に、同じ先行比喩と両側の指示対応r2giを接続する。条件内容の実行や、除去から知的能力の獲得への推論は行わない。',
    'r2gk': '既存h4fの理由付き描写への帰属にも、条件文と同じr2giを接続する。理由節だけが別の除去対象・人物・先行箇所を使うことを許さない。知的活動の比喩の対象側はまだ構成し終えていない。',
}
PRIMITIVES = {
    'hzzzm': ('a a i b[h[a] e] a a d', 'c', ['antecedent', 'author', 'kind', 'person', 'target', 'scope'],
        '先行箇所の同じ著者・種類記述を受けて、この人物について、この提示文脈で指示される対象。引用された種類を受ける指示の解釈であり、対象の内容や作用の真理、現実の物理的実在を断言する関係ではない。未知の指示を任意の対象で埋めず、仮定内の後状態から選び直さない。'),
    'hzzzn': ('a a a a a a d', 'c', ['node', 'antecedent', 'author', 'person', 'depicted', 'target', 'scope'],
        'この箇所が同じ著者の先行比喩を受ける際の、同じ人物についての描写側の対象と指示対象の対応。この二つを物理的に同じ物とはしない。対応の解釈は提示文脈で固定し、除去の成否や仮定の後状態から有利な辺を選ばない。対応だけから状態・原因・能力の真理は導かない。'),
}
LIMITS = [
    '第四文のsieを、第三文で足枷として描いた規定・定型表現を受ける指示とする候補。人物範囲は第一文から続く提示文脈に固定する。現実の全人類に個々の足枷の所有を要求する命題ではない。',
    '複数形の指示には両側の対象範囲を明示する。一方を空にして成立させず、未対応の対象を黙って捨てない。一対一を要求せず、複数の描写対象と一つの概念対象の対応なども許す。原文が対応辺の本数を指定しているとはしない。',
    '指示対象と対応辺の認定は意味規約に従う解釈入力である。一般形はその整合性を検査するが、自然言語の代名詞を自動解決するものではなく、現実の参照解釈の正しさを形式検査だけで証明しない。',
    '規定・表現の使用をやめること、知的な課題への不確かな取り組み、不慣れの因果的説明を持つ対象側の条件文は未完。今回は既存の身体的描写を残して指示対応を接続する。本文の二つの帰属は同じ対応を使う。',
    'auch・dennoch・nur、最小の溝の尺度と指示、自由な運動の種類、第五文と段落全体の意味確認は残る。今回の接続で第四文の意味一致や新しい原文対応文字数は加えない。',
]


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


def definitions():
    source = lambda n: app(v('sources'), v(n))
    target = lambda n: app(v('targets'), v(n))
    edge = lambda a, b: app(v('mapping'), v(a), v(b))
    body = both(quant('g', 'left', 'a', source('left')), quant('g', 'right', 'a', target('right')),
        quant('f', 'left', 'a', op('y', source('left'), quant('g', 'right', 'a', both(target('right'), edge('left', 'right'))))),
        quant('f', 'right', 'a', op('y', target('right'), quant('g', 'left', 'a', both(source('left'), edge('left', 'right'))))),
        quant('f', 'left', 'a', quant('f', 'right', 'a', op('y', edge('left', 'right'), both(source('left'), target('right'))))))
    text = definition('r2gf', 'sources h[a] c targets h[a] c mapping h[a a] c', body)
    member = app(v('people'), v('person'))
    sources = lam('object', 'a', app(v('sources'), v('object'), v('person')))
    targets = lam('object', 'a', app(v('targets'), v('object'), v('person')))
    mapping = 'i[left a right a][c[v mapping][v left v right v person]]'
    absent = both(quant('f', 'object', 'a', op('u', app(v('sources'), v('object'), v('person')))),
        quant('f', 'object', 'a', op('u', app(v('targets'), v('object'), v('person')))),
        quant('f', 'left', 'a', quant('f', 'right', 'a', op('u', app(v('mapping'), v('left'), v('right'), v('person'))))))
    text += definition('r2gg', 'people h[a] c sources h[a a] c targets h[a a] c mapping h[a a a] c',
        both(quant('g', 'person', 'a', member), quant('f', 'person', 'a', both(
            op('y', member, call('r2gf', sources, targets, mapping)), op('y', op('u', member), absent)))))
    text += '''
d r2gh[scope d] c[k r2gg[
 i[person a][w[k aa[v person]][k hzzn[k hzzq[] v person v scope]]]
 i[object a person a][k h2s[v object v person v scope]]
 i[object a person a][k hzzzm[k h2d[] k wa[] r b[p r2fh] v person v object v scope]]
 i[left a right a person a][k hzzzn[k h3a[] k h2d[] k wa[] v person v left v right v scope]]
]].
d r2gi[] c[w[k r2ge[]][w[k r2gh[k wh[]]][u[k ue[k h3a[] k h2d[] k wh[]]]]]].
d r2gj[] c[w[k h3b[]][k r2gi[]]].
d r2gk[] c[w[k h4f[]][k r2gi[]]].
'''
    return text


def build():
    old = parent(); doc = deepcopy(old.document); statements = doc['statements']; doc['statements'] = []
    assert not (set(MEANINGS) | set(PRIMITIVES)) & set(old.entries)
    extra = ''.join('r ' + n + '[' + p + '] ' + result + '.' for n, (p, result, _, _) in PRIMITIVES.items())
    doc = parse(format_graph(doc, 'compact') + extra + definitions())
    assert len(statements) == 54 and statements[13]['body']['symbol'] == 'h4f' and statements[53]['body']['symbol'] == 'h3b'
    for index, name in ((13, 'r2gk'), (53, 'r2gj')):
        statements[index] = dict(kind='assert', body=dict(kind='call', symbol=name, arguments=[]))
    doc['statements'] = statements; doc = parse(format_graph(doc, 'compact'))
    core = deepcopy(doc); core.update(declarations=closure(doc, ['r2gk', 'r2gj']), statements=[statements[i] for i in (13, 53)])
    library = deepcopy(doc); library.update(declarations=closure(doc, ['r2gf', 'r2gg']), statements=[])
    added = doc['declarations'][len(old.document['declarations']):]; assert len(added) == 8
    decls = {d['name']: d for d in added}
    basis = dict(status='depicted_plural_reference_candidate', document=FULL, parent=PARENT, inherited_meaning_basis=PARENT_BASIS,
        definitions=MEANINGS, primitives={n: dict(parameters=decls[n]['parameters'], result=decls[n]['result'],
            arguments=labels, meaning_ja=meaning) for n, (_, _, labels, meaning) in PRIMITIVES.items()},
        new_signatures={d['name']: {k: d[k] for k in ('parameters', 'result')} for d in added}, limitations=LIMITS)
    body = format_graph(doc, 'compact') + '\n'
    annotations = json.loads((ROOT / 'data/occasional-continuation-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    encoded = lambda x: json.dumps(x, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n', LIBRARY: format_graph(library, 'compact') + '\n',
            BASIS: encoded(basis), ANNOTATIONS: encoded(annotations)}


if __name__ == '__main__':
    from scripts.audit_opening_scope import write_exact
    for path, body in build().items():
        write_exact(ROOT / path, body)
    print('Paired referent ranges connected to both fourth-sentence attributions', flush=True)
