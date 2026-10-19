"""Keep precedence over an interval distinct from distance to a reference time."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_falling_depiction import ROOT, closure

PARENT = 'examples/v016/kant-evaluated-motives.noema'
PARENT_BASIS = 'data/evaluated-motives-basis-v1.json'
FULL = 'examples/v016/kant-relative-past.noema'
CORE = 'examples/v016/relative-past-core.noema'
LIBRARY = 'examples/v016/prior-interval-reference.noema'
BASIS = 'data/relative-past-basis-v1.json'
ANNOTATIONS = 'data/relative-past-identifiers-v1.json'
MEANINGS = {
    'rqxe': '指定点が同じ順序付き履歴の非空で間の抜けない範囲の全てに先行し、同じ履歴内の基準点にも先行し、その指定点から基準点への経過が与えた距離基準を満たす。範囲の各点まで十分な時間が経過したことは要求しない。先行範囲と距離の基準点を別引数で保持する。',
    'km': '同じ本人の履歴で、klかつkcでない状態からkcへ、その本人を対象とする過程ag・laが移す。後状態は生涯の評価範囲の全てに先行する。とうの昔という経過の基準kdは後状態から内容の基準状況contextまでに課す。範囲の開始点まで長い待機期間があったことは追加しない。',
    'qg': '同じ本人の履歴で、生涯の評価範囲より前に、自然qbがその人をqfの状態にあると宣告したという描写。とうの昔という距離は宣告時点から内容の基準状況contextまでで判定し、範囲の全時点までには要求しない。本文ではkfを提示する非字義的な描写として帰属し、自然の現実の発話や状態の実現を断言しない。',
}


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


def build():
    old = parent();assert 'rqxe' not in old.entries
    doc = deepcopy(old.document)
    at = next(i for i, d in enumerate(doc['declarations']) if d['name'] == 'km')
    prefix = deepcopy(doc);prefix.update(declarations=doc['declarations'][:at], statements=[])
    generic = '''d rqxe[history h[d] c extent h[d] c before h[d d] c point d reference d distant h[d d] c] c[
 w[k te[v history v extent v before v point]][w[c[v history][v reference]][
  w[c[v before][v point v reference]][c[v distant][v point v reference]]
 ]]
].'''
    parsed = parse(format_graph(prefix, 'compact') + generic)
    doc['declarations'] = parsed['declarations'] + doc['declarations'][at:]
    for d in doc['declarations']:
        if d['name'] not in ('km', 'qg'):continue
        anchor = d['parameters'][-1]['name'] if d['name'] == 'km' else d['body']['variable']
        count = []
        def revise(node):
            if isinstance(node, dict):
                if node.get('kind') == 'call' and node['symbol'] == 'tf':
                    node['symbol'] = 'rqxe'
                    node['arguments'].insert(4, dict(kind='variable', name=anchor));count.append(1)
                for child in node.values():revise(child)
            elif isinstance(node, list):
                for child in node:revise(child)
        revise(d['body']);assert len(count) == 1
    doc = parse(format_graph(doc, 'compact'))
    basis = dict(status='prior_interval_and_reference_relative_distance', document=FULL,
        revises_document=PARENT, revises_meaning_basis=PARENT_BASIS,
        primitives={}, definitions={}, predecessor_source_sha256=old.source_sha256,
        limitations=[
            '原文のlängstを内容の評価基準時点からの距離として読む。afterに対応する範囲への先行は別に保持する。数値的な年数は補わない。',
            '基準点を履歴内に要求するので、単なる本文位置を時間上の点の代わりに渡さない。本文帰属の文脈と引用内容を評価する時間的状況は同一とは限らない。',
            '自然的成熟の構成、ラテン語の用法、態度と生涯、後見の容易さの範囲、第一文・第二段落の全体レビューは残る。',
            '従来のtfは全範囲の各点までの経過を述べる用途に保持する。一般言語で無効にする変更ではない。'],
        unresolved=[dict(basis=r['basis'], historical_caveats=r['caveats']) for r in old.lineage])
    for d in doc['declarations']:
        n = d['name']
        if d['kind'] == 'primitive':
            basis['primitives'][n] = dict(parameters=d['parameters'], result=d['result'],
                arguments=old.entries[n]['arguments'], meaning_ja=old.entries[n]['meaning_ja'])
        else:
            basis['definitions'][n] = MEANINGS[n] if n in MEANINGS else old.entries[n]['meaning_ja']
    core = deepcopy(doc);core['statements'] = [doc['statements'][i] for i in (2, 3)]
    core['declarations'] = closure(doc, ['uc', 'mw', 'wa', 'mx', 'wh', 'ue', 'wg', 'qh', 'kf', 'qg'])
    library = deepcopy(doc);library.update(declarations=closure(doc, ['rqxe', 'tf']), statements=[])
    body = format_graph(doc, 'compact') + '\n'
    ann = json.loads((ROOT / 'data/evaluated-motives-identifiers-v1.json').read_text(encoding='utf-8'))
    ann.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    enc = lambda obj: json.dumps(obj, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n', LIBRARY: format_graph(library, 'compact') + '\n',
        BASIS: enc(basis), ANNOTATIONS: enc(ann)}


def main():
    for name, body in build().items():
        p = ROOT / name
        if p.exists():assert p.read_text(encoding='utf-8') == body, name
        else:
            with p.open('x', encoding='utf-8', newline='\n') as stream:stream.write(body)
    print('Reference-relative past connected without new primitives', flush=True)


if __name__ == '__main__':main()
