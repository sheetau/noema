"""Preserve a presented sufficiency restriction independently of its truth."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog, _references
from noema.semantic_reviews import digest
from scripts.compose_falling_depiction import ROOT, closure

PARENT = 'examples/v016/kant-sufficient-payment.noema'
PARENT_BASIS = 'data/sufficient-payment-basis-v1.json'
FULL = 'examples/v016/kant-payment-reading.noema'
CORE = 'examples/v016/payment-reading-core.noema'
BASIS = 'data/payment-reading-basis-v1.json'
ANNOTATIONS = 'data/payment-reading-identifiers-v1.json'
MEANING = '提示者が同じ箇所・文脈で、指定された人物についての前件を、指定帰結に足りる条件として取り立て、それ以上の追加要件を求めないという限定を提示する。両記述の人物引数は同じ位置を指す。背景として固定した文脈の条件を取り払わず、他の達成手段や別の十分条件の存在も否定しない。前件が必要条件であること、前件・帰結の現実の真理、内容の論理的な妥当性、提示者の推奨は含意しない。語形ではなく条件の提示上の扱いを表す基本関係である。'
DEFINITION_MEANING = 't3の一人称仮定例を提示する同じ箇所・著者・文脈で、支払能力tpだけで本人の思考なしの達成tqに足りると限定して提示する。原文nurの条件提示の読みを保持し、支払えなければ必ず思考が必要だという逆方向の条件は追加しない。t3内の将来の引受けの見込みは同じ仮定に従属したままである。'


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


def build():
    old = parent(); doc = deepcopy(old.document)
    assert not {'hzxl', 'hzxm'} & set(old.entries)
    statements = doc['statements']; doc['statements'] = []; size = len(doc['declarations'])
    text = '''r hzxl[a a i[h[a] e] i[h[a] e] d] c.
d hzxm[] c[w[k s4[k t4[] k wa[] r[p t3] k wh[]]][k hzxl[k t4[] k wa[] r[p tp] r[p tq] k wh[]]]].
s[k hzxm[]].'''
    doc = parse(format_graph(doc, 'compact') + text)
    doc['statements'] = statements + doc['statements']
    basis = dict(status='payment_sentence_with_presented_sufficiency', document=FULL, parent=PARENT,
        inherited_meaning_basis=PARENT_BASIS,
        primitives={'hzxl': dict(parameters=doc['declarations'][size]['parameters'], result='truth',
            arguments=['node', 'presenter', 'premise_description', 'conclusion_description', 'context'], meaning_ja=MEANING)},
        definitions={'hzxm': DEFINITION_MEANING},
        new_signatures={d['name']: {k: d[k] for k in ('parameters', 'result')} for d in doc['declarations'][size:]},
        limitations=['条件だけで足りるという提示を、通常の条件文の提示から区別する。nurの全用法を一括して定義するものではない。',
            '既存43文と全定義・意味規約を保持し、文43に提示条件を追加する。真偽の条件を必要十分条件へ変更しない。',
            '意味の対応判断は明示したこの一文の読解に限る。第二段落全体と二作品全文の意味確認は未完。'])
    core = deepcopy(doc); core['statements'] = [doc['statements'][i] for i in (5, 43)]
    core['declarations'] = closure(doc, _references(core['statements']))
    body = format_graph(doc, 'compact') + '\n'
    ann = json.loads((ROOT / 'data/sufficient-payment-identifiers-v1.json').read_text(encoding='utf-8'))
    ann.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    enc = lambda x: json.dumps(x, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n', BASIS: enc(basis), ANNOTATIONS: enc(ann)}


def main():
    from scripts.audit_opening_scope import write_exact
    for path, text in build().items(): write_exact(ROOT / path, text)
    print('Presented sufficiency composed', flush=True)


if __name__ == '__main__':
    main()
