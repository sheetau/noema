"""Reuse the printed-credit composition in Einstein's existing edition 0.14."""
from copy import deepcopy
import json
from pathlib import Path
from noema.grammar import parse, format_graph
from noema.constructed import parse as parse_constructed
from noema.extraction import extract_document
from noema.meaning_basis import audit_basis
from noema.semantic_reviews import digest

ROOT = Path(__file__).resolve().parents[1]
PARENT = 'examples/v014/einstein-density-origins.noema'
PARENT_BASIS = 'data/einstein-density-origins-basis-v1.json'
FULL = 'examples/v014/einstein-author-credit.noema'
CORE = 'examples/v014/einstein-author-credit-core.noema'
BASIS = 'data/einstein-author-credit-basis-v1.json'
ANNOTATIONS = 'data/einstein-author-credit-identifiers-v1.json'
LIBRARY = 'examples/v016/author-credit.noema'
LIBRARY_BASIS = 'data/author-credit-basis-v1.json'
INDEX = 206
PRIMITIVES = {
    'eira': (['activity', 'context'], '同じ文脈で指定された提示行為が成立する。物理的な印刷者や執筆者を指定しない。'),
    'eirb': (['activity', 'label', 'subject', 'context'], '同じ提示行為で名称を対象へ適用する。綴りの一致から対象の同一性を推論しない。'),
    'eirc': (['activity', 'document', 'author', 'context'], '指定文書のその提示行為が、同じ対象を文書の著者として表示する役割を持つ。表示の真実性、自筆性、提示者と著者の一致を含意しない。'),
    'eird': ([], 'u0002で使う名称個体。A. Einsteinという綴りは別添えの識別表記で保持し、人物rdそのものと区別する。'),
    'eire': ([], 'u0002のvon A. Einstein.という前付の著者表示における名称使用。紙面の印刷行為や自筆署名を特定するものではない。'),
    'eirf': ([], '今回記述する1905年の論説を指す文書個体。本文中の著者参照rdがこの文書の表示対象に結ばれる。'),
    'eirg': ([], '同じ論説の前付における著者表示の文脈。本文の推論範囲・物理的設定とは区別する。'),
}
MEANINGS = {
    'eiaa': '同じ名称使用が同じ文脈で成立し、同じ名称を同じ対象へ適用し、その同じ使用が指定文書の著者としてその対象を表示する。誰が実際に表示を行ったか、表示の真正性・自筆性は要求しない。',
    'eiab': '前付u0002の名称eirdを既存本文の著者参照rdへ適用し、その同じ表示eireが同じ論説eirfの著者表示であることを結ぶ。名称と人物を区別し、前付文脈eirgを固定する。実際の提示者を著者と同一視しない。',
}


def read(path):
    return (ROOT/path).read_text(encoding='utf-8')


def build():
    old = parse(read(PARENT)); doc = deepcopy(old)
    assert len(old['statements']) == INDEX
    names = {d['name'] for d in old['declarations']}
    assert not names.intersection(set(PRIMITIVES) | set(MEANINGS))
    generic = deepcopy(parse_constructed(read(LIBRARY))['declarations'][0])
    assert generic['name'] == 'rqqx'
    generic['name'] = 'eiaa'
    doc['statements'] = []; doc['declarations'].append(generic)
    additions = ('r eira[a d] c.r eirb[a a a d] c.r eirc[a a a d] c.'
        'r eird[] a.r eire[] a.r eirf[] a.r eirg[] d.'
        'd eiab[] c[w[u[e[k eird[]][k rd[]]]][k eiaa[k eire[] k eird[] k rd[] k eirf[] k eirg[] p eira p eirb p eirc]]].'
        's[k eiab[]].')
    doc = parse(format_graph(doc, 'compact') + additions)
    doc['statements'] = deepcopy(old['statements']) + doc['statements']
    basis = json.loads(read(PARENT_BASIS))
    basis.update(version='einstein-author-credit-basis-v1', document=FULL)
    basis['definitions'].update(MEANINGS)
    for d in doc['declarations']:
        if d['name'] in PRIMITIVES:
            labels, meaning = PRIMITIVES[d['name']]
            basis['primitives'].append(dict(symbol=d['name'], parameters=d['parameters'],
                result=d['result'], arguments=labels, meaning_ja=meaning))
    basis['unresolved'] += [
        'u0002の著者表示を本文のrdへ結んだ。表題の主題、導入段落の電磁現象と説明、残りの原文の全体判断は未完。',
        'rqqxの一般的な著者表示の合成をeiaaとして0.14へ移した。引用や階数を使わない本体・引数・意味規約を保持し、旧206主張を変更しない。']
    basis['author_credit_provenance'] = dict(generic_library=LIBRARY, generic_basis=LIBRARY_BASIS,
        old_symbol='rqqx', new_symbol='eiaa', original_statements_retained=INDEX)
    audit_basis(doc, basis)
    body = format_graph(doc, 'compact') + '\n'
    core = extract_document(doc, roots=[], statement_indices=[INDEX]).document
    annotations = dict(schema_version='noema-identifiers-1', document=FULL,
        document_sha256=digest(body.encode('utf-8')), entries=[dict(symbol='eird', role='designation',
        forms=[dict(text='A. Einstein', language='de', role='printed_identifying_form')])])
    return {FULL: body, CORE: format_graph(core, 'compact')+'\n',
        BASIS: json.dumps(basis, ensure_ascii=False, indent=2)+'\n',
        ANNOTATIONS: json.dumps(annotations, ensure_ascii=False, indent=2)+'\n'}


def main():
    from scripts.audit_opening_scope import write_exact
    for name, body in build().items():
        write_exact(ROOT/name, body)
    print('Einstein printed author credit connected; original 206 assertions retained')


if __name__ == '__main__':
    main()
