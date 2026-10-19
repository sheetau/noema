"""Bind a recognized example to an earlier experience without merging its observers."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog, _references
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure

PARENT = 'examples/v016/kant-walking-acquisition.noema'
PARENT_BASIS = 'data/walking-acquisition-basis-v1.json'
FULL = 'examples/v016/kant-recognized-example.noema'
CORE = 'examples/v016/recognized-example-core.noema'
LIBRARY = 'examples/v016/recognized-prior-experience.noema'
BASIS = 'data/recognized-example-basis-v1.json'
ANNOTATIONS = 'data/recognized-example-identifiers-v1.json'
MEANINGS = {
    'r2ba': '指定した対象者が同じ例を現在の文脈で認識し、その例の時点が先行し、指定範囲のある経験者について同じ例・時点の経験条件が成立する。対象者と経験者の同一性、直接目撃、例の唯一性は要求しない。認識・時点・先行・経験者範囲・経験内容を引数にする一般構成。',
    'r2bb': '同じ事例の対象者gdが例geを認識し、その先行する例について、ある人が補助なしの足移動を試みて転倒したという既存hzumの身体的経験が成立する。認識した例と別の転倒を混ぜない。',
    'r2bc': '後続の萎縮節g2において、同じ事例の知的な不成功例を認識する内容grを、転倒例を認識する内容r2bbで非字義的に提示する。学習節fvの別の提示から自動的には継承せず、この節への帰属を明示する。両内容の真偽一致や身体転倒の実在は断言しない。',
}
LIMITS = [
    'ein Beispiel von der Artを直前の転倒経験の種類を受ける例として読む。例を知ることには伝聞を含め、本人の転倒や直接目撃へ限定しない。唯一の歴史的読解を証明するものではない。',
    '身体側は既採用のhzumによる転倒の読みを継ぐ。別人の経験を知る場合も、本人の経験を知る場合も許す。知的側と身体側で同じ例索引を使うのは描写の対応であり、現実の出来事の同一性ではない。',
    '一般構成は経験内容と経験者の範囲を引数にする。新しい語別の基本関係や実行文法は追加しない。旧grの内容は変更しない。',
    '架空の例、通常性の有限等重み事例による読み、schüchternの程度と語義、würden・wohl・endlichの作用範囲、末尾一文と段落全体の意味判断は残る。',
]


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


def additions():
    return '''
d r2ba[observer a example a anchor d people h[a] c recognizes h[a a d] c point h[a] d before h[d d] c experience h[a a d] c] c[
 w[c[v recognizes][v observer v example v anchor]][w[c[v before][c[v point][v example] v anchor]][
 g person a[w[c[v people][v person]][c[v experience][v person v example c[v point][v example]]]]
]]].
d r2bb[case a] e[b scene[k r2ba[k gd[v case] k ge[v case] v scene p aa p gg p f7 p dd
 i[person a example a point d][t[k hzum[v person v example]][v point]]]]].
d r2bc[] c[k qh[k g2[] k wa[] r[p gr] r[p r2bb] k wh[]]].
'''


def build():
    old = parent(); doc = deepcopy(old.document)
    statements = doc['statements']; doc['statements'] = []
    size = len(doc['declarations'])
    assert not set(MEANINGS) & set(old.entries)
    doc = parse(format_graph(doc, 'compact') + additions() + 's[k r2bc[]].')
    doc['statements'] = statements + doc['statements']
    doc = parse(format_graph(doc, 'compact'))
    core = deepcopy(doc); core['statements'] = doc['statements'][-1:]
    core['declarations'] = closure(doc, _references(core['statements']))
    library = deepcopy(doc); library.update(declarations=closure(doc, ['r2ba']), statements=[])
    added = doc['declarations'][size:]
    assert len(added) == 3 and all(d['kind'] == 'definition' for d in added)
    basis = dict(status='recognized_prior_fall_depiction_connected', document=FULL, library=LIBRARY,
        parent=PARENT, inherited_meaning_basis=PARENT_BASIS, primitives={}, definitions=MEANINGS,
        new_signatures={d['name']: {k: d[k] for k in ('parameters', 'result')} for d in added}, limitations=LIMITS)
    body = format_graph(doc, 'compact') + '\n'
    ann = json.loads((ROOT/'data/walking-acquisition-identifiers-v1.json').read_text(encoding='utf-8'))
    ann.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    enc = lambda value: json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact')+'\n',
        LIBRARY: format_graph(library, 'compact')+'\n', BASIS: enc(basis), ANNOTATIONS: enc(ann)}


def main():
    from scripts.audit_opening_scope import write_exact
    for path, body in build().items():
        write_exact(ROOT/path, body)
    print('Recognized example composed: three definitions, zero primitives, 52 statements', flush=True)


if __name__ == '__main__':
    main()
