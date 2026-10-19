"""Bind credited and required consideration before comparing their values."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog, _references
from noema.semantic_reviews import digest
from scripts.compose_falling_depiction import ROOT, closure

PARENT = 'examples/v016/kant-appointed-roles.noema'
PARENT_BASIS = 'data/appointed-roles-basis-v1.json'
FULL = 'examples/v016/kant-sufficient-payment.noema'
CORE = 'examples/v016/sufficient-payment-core.noema'
LIBRARY = 'examples/v016/sufficient-consideration.noema'
BASIS = 'data/sufficient-payment-basis-v1.json'
ANNOTATIONS = 'data/sufficient-payment-identifiers-v1.json'
PRIMITIVES = {
    'hzxj': (['transfer', 'payer', 'receiver', 'task_description', 'scene'], '同じ移転について、この支払う人から受け手への、記述された仕事の対価として算入される価値の有理数量。その取引文脈で必要対価hzxkと共通の単位・換算基準を使う。所持金全体、名目額、別の仕事への算入額とは分ける。移転の生起や媒体の受容は別条件である。金銭評価と算入の制度上の事実を入力とし、未知の額を0で補わない。'),
    'hzxk': (['payer', 'receiver', 'task_description', 'scene'], '同じ支払う人・受け手・仕事の取引条件において、その仕事を対価面で賄うために必要な移転価値の有理数量。hzxjと同じ尺度を用い、移転直前の条件・既払分に対する必要額を表し、支払後の残高0へすり替えない。単なる部分払いの額ではなく、この仕事を賄える条件に必要な額である。既知の無償条件は0と書けるが未知の条件とは区別する。価格の正当性やサービスの履行は含まない。'),
}
MEANINGS = {
    'rqxz': '同じ支払う人・受け手・仕事・評価状況について必要額が正であり、その同じ移転について算入される対価額が必要額以上である。額は同一尺度で与える。移転、受容、対価との結合は別条件に分け、ここだけから支払いの生起を推論しない。',
    'rqya': '旧toの、理解力を用いる仕事への対価となる移転が存在する内容を保存する。部分的な対価も含み、必要額を満たしたことは要求しない。',
    'to': '本人から別の受け手への同じ移転がrfの対価条件を満たし、かつ同じ受け手・仕事bm・状況でrqxzの必要対価を賄う内容。通貨・必要額の具体的な値は入力へ残し、原文に固定金額を補わない。単なる部分払いと、その仕事を対価面で賄う支払いを分ける。',
}


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


def build():
    old = parent(); doc = deepcopy(old.document)
    assert not (set(PRIMITIVES) | {'rqxz', 'rqya'}) & set(old.entries)
    at = next(i for i, d in enumerate(doc['declarations']) if d['name'] == 'to')
    prefix = deepcopy(doc); prefix.update(declarations=doc['declarations'][:at], statements=[])
    saved = deepcopy(old.entries['to']['declaration']); saved['name'] = 'rqya'
    prefix['declarations'].append(saved)
    text = '''r hzxj[a a a i[h[a] e] d] b.r hzxk[a a i[h[a] e] d] b.
d rqxz[payer a receiver a transfer a task i[h[a] e] scene d credit h[a a a i[h[a] e] d] b required h[a a i[h[a] e] d] b less h[b b] c] c[
 w[c[v less][n p a b c[v required][v payer v receiver v task v scene]]][
 u[c[v less][c[v credit][v transfer v payer v receiver v task v scene] c[v required][v payer v receiver v task v scene]]]]
].
d to[person a] e[b scene[g receiver a[g transfer a[g medium a[
 w[k rf[v person v receiver v transfer v medium r[p bm] v scene p ti p tj p tk]][
 k rqxz[v person v receiver v transfer r[p bm] v scene p hzxj p hzxk p hc]]
]]]]].'''
    parsed = parse(format_graph(prefix, 'compact') + text)
    doc['declarations'] = parsed['declarations'] + doc['declarations'][at + 1:]
    doc = parse(format_graph(doc, 'compact'))
    basis = dict(status='required_consideration_connected', document=FULL,
        revises_document=PARENT, revises_meaning_basis=PARENT_BASIS,
        primitives={}, definitions={}, predecessor_source_sha256=old.source_sha256,
        limitations=['対価額が同一尺度の有理数で表せる取引の読み。全ての交換制度や非数量的な履行条件をこれだけで定義したとはしない。',
            '必要額と算入額の制度上の意味を明示した基本関係に残す。本文から金額を推測する翻訳機ではない。',
            '正の必要対価がある支払いと無償の提供を分ける。旧toをrqyaとして保存する。',
            '支払いの一文・第二段落・二作品全文の意味確認は未完。'],
        unresolved=[dict(basis=r['basis'], historical_caveats=r['caveats']) for r in old.lineage])
    for d in doc['declarations']:
        n = d['name']
        if d['kind'] == 'primitive':
            labels, meaning = PRIMITIVES[n] if n in PRIMITIVES else (old.entries[n]['arguments'], old.entries[n]['meaning_ja'])
            basis['primitives'][n] = dict(parameters=d['parameters'], result=d['result'], arguments=labels, meaning_ja=meaning)
        else:
            basis['definitions'][n] = MEANINGS[n] if n in MEANINGS else old.entries[n]['meaning_ja']
    core = deepcopy(doc); core['statements'] = [doc['statements'][5]]
    core['declarations'] = closure(doc, _references(core['statements']))
    lib = deepcopy(doc); lib.update(declarations=closure(doc, ['rqxz']), statements=[])
    body = format_graph(doc, 'compact') + '\n'
    ann = json.loads((ROOT / 'data/appointed-roles-identifiers-v1.json').read_text(encoding='utf-8'))
    ann.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    enc = lambda x: json.dumps(x, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n', LIBRARY: format_graph(lib, 'compact') + '\n',
        BASIS: enc(basis), ANNOTATIONS: enc(ann)}


def main():
    from scripts.audit_opening_scope import write_exact
    for p, s in build().items():
        write_exact(ROOT / p, s)
    print('Sufficient consideration composed', flush=True)


if __name__ == '__main__':
    main()
