"""Add a scoped recognizability presentation without changing world conditions."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog, _references
from noema.semantic_reviews import digest
from scripts.compose_falling_depiction import ROOT, closure

PARENT = 'examples/v016/kant-book-form.noema'
PARENT_BASIS = 'data/book-form-basis-v1.json'
FULL = 'examples/v016/kant-recognizable-consequence.noema'
CORE = 'examples/v016/recognizable-consequence-core.noema'
LIBRARY = 'examples/v016/scoped-recognizability.noema'
BASIS = 'data/recognizable-consequence-basis-v1.json'
ANNOTATIONS = 'data/recognizable-consequence-identifiers-v1.json'
MEANING = '提示者がこの箇所・文脈で、指定された仮定の下に置いた同じ人物についての帰結を、想定される受け手にも認めやすく、新しい争点として扱わずに済むものとして提示する。仮定と帰結の記述の人物引数は同じ位置を指す。提示上の扱いであり、仮定や帰結の現実の真理、論理的な必然性、読者全員の既知性・同意・理解、著者がその生活態度を推奨することは含意しない。'
MEANINGS = {
    'rqxq': '同じ箇所・提示者・文脈について、指定された仮定例の提示と、指定仮定の下で指定帰結を認めやすいものとして扱う提示を結ぶ。三つの記述の対応は呼出側で固定し、この一般形自体は条件文記述の構文解析や内容評価を行わない。',
    'hzwy': '三つの代行例を前件sv、努力なしの達成を後件sxとするsyの一人称仮定例の提示に、同じsvの下でsxを認めやすいものとして扱う提示を結ぶ。原文jaのこの箇所での働きの読解であり、帰結を現実の真理や共有知識の事実として追加しない。',
}


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


def build():
    old = parent(); doc = deepcopy(old.document)
    assert not {'hzwx', 'rqxq', 'hzwy'} & set(old.entries)
    statements = doc['statements']; doc['statements'] = []
    size = len(doc['declarations'])
    text = '''r hzwx[a a i[h[a] e] i[h[a] e] d] c.
d rqxq[node a author a conditional i[h[a] e] premise i[h[a] e] conclusion i[h[a] e] scene d presented h[a a i[h[a] e] d] c recognizable h[a a i[h[a] e] i[h[a] e] d] c] c[
 w[c[v presented][v node v author v conditional v scene]][c[v recognizable][v node v author v premise v conclusion v scene]]
].
d hzwy[] c[k rqxq[k s3[] k wa[] r[p sy] r[p sv] r[p sx] k wh[] p s4 p hzwx]].
s[k hzwy[]].'''
    doc = parse(format_graph(doc, 'compact') + text)
    doc['statements'] = statements + doc['statements']
    basis = dict(status='scoped_recognizability_presentation', document=FULL, parent=PARENT,
        inherited_meaning_basis=PARENT_BASIS,
        primitives={'hzwx': dict(parameters=doc['declarations'][size]['parameters'], result='truth',
            arguments=['node', 'presenter', 'premise_description', 'conclusion_description', 'context'], meaning_ja=MEANING)},
        definitions=MEANINGS,
        new_signatures={d['name']: {k: d[k] for k in ('parameters', 'result')} for d in doc['declarations'][size:]},
        limitations=['jaを仮定下で帰結を認めやすいものとして提示する働きと読む。実際に共有された知識の事実や、すべてのjaの用法を定義したとはしない。',
            '既存42文と全定義・意味規約は保持し、文42に提示条件を追加する。世界の状態や能力条件の修正ではない。',
            'この文の全語義、jaと反語・焦点・態度の相互関係、条件文と段落の全体確認は残る。'])
    core = deepcopy(doc); core['statements'] = [doc['statements'][i] for i in (4, 42)]
    core['declarations'] = closure(doc, _references(core['statements']))
    lib = deepcopy(doc); lib.update(declarations=closure(doc, ['rqxq']), statements=[])
    body = format_graph(doc, 'compact') + '\n'
    ann = json.loads((ROOT / 'data/book-form-identifiers-v1.json').read_text(encoding='utf-8'))
    ann.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    encoded = lambda obj: json.dumps(obj, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n', LIBRARY: format_graph(lib, 'compact') + '\n',
        BASIS: encoded(basis), ANNOTATIONS: encoded(ann)}


def main():
    from scripts.audit_opening_scope import write_exact
    for path, text in build().items():
        write_exact(ROOT / path, text)
    print('Scoped recognizability presentation composed', flush=True)


if __name__ == '__main__':
    main()
