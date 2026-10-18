"""Use the explicit author/use convention for the active honorific statement."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_falling_depiction import ROOT, closure

PARENT = 'examples/v016/kant-periodical-profile.noema'
PARENT_BASIS = 'data/periodical-profile-basis-v1.json'
FULL = 'examples/v016/kant-designation-order.noema'
CORE = 'examples/v016/designation-order-core.noema'
BASIS = 'data/designation-order-basis-v1.json'
ANNOTATIONS = 'data/designation-order-identifiers-v1.json'
MEANING = '既存の丁寧な名称使用hzlrを保持し、著者wa・使用箇所hzlpの順で、同じ人物の記述hzmbと男性分類の記述hzmcを一般関係hzwhへ渡す。呼称内での描写の使用を述べ、本人の実際の属性を補わない。著者・箇所の順が規約と食い違っていた旧版hzmdの接続先を修正した定義。'


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


def build():
    old = parent()
    doc = deepcopy(old.document)
    general = next(d for d in doc['declarations'] if d['name'] == 'hzwh')
    doc['declarations'].remove(general)
    at = next(i for i, d in enumerate(doc['declarations']) if d['name'] == 'hzmd')
    doc['declarations'].insert(at, general)
    honorific = doc['declarations'][at + 1]
    argument = honorific['body']['arguments'][1]['arguments'][-1]
    assert argument == {'kind': 'function_ref', 'symbol': 'du'}
    argument['symbol'] = 'hzwh'
    doc = parse(format_graph(doc, 'compact'))
    core = deepcopy(doc)
    core['declarations'] = closure(doc, ['hzmd', 'hzwg'])
    core['statements'] = [doc['statements'][26], doc['statements'][41]]
    primitives, definitions = {}, {}
    for d in doc['declarations']:
        n = d['name']
        if d['kind'] == 'primitive':
            primitives[n] = {k: deepcopy(old.entries[n][k]) for k in ('arguments', 'meaning_ja')}
            primitives[n].update(parameters=d['parameters'], result=d['result'])
        else:
            definitions[n] = MEANING if n == 'hzmd' else old.entries[n]['meaning_ja']
    basis = dict(status='explicit_author_use_order_for_honorific_and_periodical_descriptions',
        document=FULL, revises_document=PARENT, revises_meaning_basis=PARENT_BASIS,
        primitives=primitives, definitions=definitions,
        revision=dict(changed_definition='hzmd', reordered_primitive='hzwh', new_symbols=[]),
        predecessor_source_sha256=old.source_sha256,
        limitations=['旧duの引数名とhzmdの呼び出し順の食い違いを、現行辞書のhzmdの定義自体で解消する。',
            '過去のファイルを書き換えず、新しい本文と完全な意味規約を保存する。hzwhは前方参照を避けるためhzmdの直前へ移す。',
            '新しい基本関係・局所参照は追加しない。既存hzwhの著者・箇所・対象記述・性質記述・文脈の順に統一する。',
            '敬称について採用した読みは変えず、実際の性別・身分・内心の敬意を補わない。',
            '本文42文の構文は保持し、文26の参照先hzmdだけを改訂する。十単位604文字の判断は参照先の実質的な不変を検査して新しい来歴に結び直す。',
            '偶発性・内容対応・著者注全体の意味確認は残る。'],
        unresolved=[dict(basis=row['basis'], historical_caveats=row['caveats']) for row in old.lineage])
    body = format_graph(doc, 'compact') + '\n'
    annotations = json.loads((ROOT / 'data/periodical-profile-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    encoded = lambda obj: json.dumps(obj, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n', BASIS: encoded(basis), ANNOTATIONS: encoded(annotations)}


def main():
    for name, body in build().items():
        p = ROOT / name
        if p.exists():
            assert p.read_text(encoding='utf-8') == body, name
        else:
            with p.open('x', encoding='utf-8', newline='\n') as stream:
                stream.write(body)
    print('Honorific and periodical descriptions use the explicit author/use order', flush=True)


if __name__ == '__main__':
    main()
