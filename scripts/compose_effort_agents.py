"""Distinguish the method's beneficiary from the agent bearing its effort."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog, _references
from noema.semantic_reviews import digest
from scripts.compose_falling_depiction import ROOT, closure

PARENT = 'examples/v016/kant-recognizable-consequence.noema'
PARENT_BASIS = 'data/recognizable-consequence-basis-v1.json'
FULL = 'examples/v016/kant-effort-agents.noema'
CORE = 'examples/v016/effort-agents-core.noema'
LIBRARY = 'examples/v016/agent-scoped-effort.noema'
BASIS = 'data/effort-agents-basis-v1.json'
ANNOTATIONS = 'data/effort-agents-identifiers-v1.json'
EFFORT = '指定された本人の目的に関する同じ方法で、開始から結果へ至る経路に、指定された実施者の文脈上問題となる努力が要る。本人と実施者を別引数にし、他人のための方法・別方法・別の開始や結果での努力を混ぜない。経路を評価する条件であり、その方法を現実に選択・実行した事実、結果時点だけの努力、全ての活動の禁止や不可能性を意味しない。'
MEANINGS = {
    'rqxr': '同じ本人・方法・開始・結果について、指定範囲内の少なくとも一人がその経路で問題となる努力を要する。実施者の範囲が空なら成立しない。本人だけ、他者だけ、任意の指定集団を分けて照合できる。範囲外の実施者の努力を混ぜない。',
    'sk': '本人のための同じ方法・開始・結果について、努力を担う実施者も同じ本人であるというhzwzの特殊化。本人がその経路で問題となる努力を要することを述べる。本人の努力がない場合も他者の努力を否定せず、方法の現実の実行・本人の不実行・努力不能は含意しない。',
}


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


def build():
    old = parent(); doc = deepcopy(old.document)
    assert not {'hzwz', 'rqxr'} & set(old.entries)
    at = next(i for i, d in enumerate(doc['declarations']) if d['name'] == 'sk')
    assert doc['declarations'][at]['kind'] == 'primitive'
    prefix = deepcopy(doc); prefix.update(declarations=doc['declarations'][:at], statements=[])
    text = '''r hzwz[a a a d d] c.
d rqxr[person a method a start d end d agents h[a] c effort h[a a a d d] c] c[
 g agent a[w[c[v agents][v agent]][c[v effort][v agent v person v method v start v end]]]
].
d sk[person a method a start d end d] c[k hzwz[v person v person v method v start v end]].'''
    parsed = parse(format_graph(prefix, 'compact') + text)
    doc['declarations'] = parsed['declarations'] + doc['declarations'][at + 1:]
    doc = parse(format_graph(doc, 'compact'))
    basis = dict(status='effort_agent_and_method_beneficiary_separated', document=FULL,
        revises_document=PARENT, revises_meaning_basis=PARENT_BASIS, primitives={}, definitions={},
        predecessor_source_sha256=old.source_sha256,
        limitations=['旧skの本人の努力という条件を、本人と実施者を同一にする構成へ移す。他者の努力を必須条件として追加しない。',
            '努力の種類と目的、方法・結果の評価範囲は文脈に依存する。原文にない労力の数値や具体的な履歴を補わない。',
            'selbstのこの箇所での本人への結合を説明する。程度焦点など全用法や、本文の反語的効果を定義したとはしない。',
            '条件文・第二段落全体と二作品全文の意味確認は未完。'],
        unresolved=[dict(basis=r['basis'], historical_caveats=r['caveats']) for r in old.lineage])
    for d in doc['declarations']:
        n = d['name']
        if d['kind'] == 'primitive':
            labels, meaning = (['effort_agent', 'method_beneficiary', 'method', 'start', 'end'], EFFORT) if n == 'hzwz' else (old.entries[n]['arguments'], old.entries[n]['meaning_ja'])
            basis['primitives'][n] = dict(parameters=d['parameters'], result=d['result'], arguments=labels, meaning_ja=meaning)
        else:
            basis['definitions'][n] = MEANINGS[n] if n in MEANINGS else old.entries[n]['meaning_ja']
    core = deepcopy(doc); core['statements'] = [doc['statements'][i] for i in (4, 42)]
    core['declarations'] = closure(doc, _references(core['statements']))
    lib = deepcopy(doc); lib.update(declarations=closure(doc, ['rqxr']), statements=[])
    body = format_graph(doc, 'compact') + '\n'
    ann = json.loads((ROOT / 'data/recognizable-consequence-identifiers-v1.json').read_text(encoding='utf-8'))
    ann.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    enc = lambda x: json.dumps(x, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n', LIBRARY: format_graph(lib, 'compact') + '\n',
        BASIS: enc(basis), ANNOTATIONS: enc(ann)}


def main():
    from scripts.audit_opening_scope import write_exact
    for p, s in build().items():
        write_exact(ROOT / p, s)
    print('Effort agents separated from method beneficiaries', flush=True)


if __name__ == '__main__':
    main()
