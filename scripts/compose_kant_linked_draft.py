"""Join diverged Kant drafts using their verified common ancestor."""
from copy import deepcopy
import json
import re

from noema.grammar import format_graph, parse
from noema.linking import link_documents
from noema.meaning_basis import audit_basis
from scripts.compose_limits import ROOT

SOURCES = {'current': 'kant-retained-attitudes', 'confinement': 'kant-confinement-onset'}
ANCESTOR = 'kant-caused-conditions'


def read_pair(stem):
    doc = parse((ROOT / ('examples/v014/' + stem + '.noema')).read_text(encoding='utf-8'))
    basis = json.loads((ROOT / ('data/' + stem + '-basis-v1.json')).read_text(encoding='utf-8'))
    audit_basis(doc, basis)
    return doc, basis


def linkage():
    ancestor, common_basis = read_pair(ANCESTOR)
    pairs = {label: read_pair(stem) for label, stem in SOURCES.items()}
    common_names = {d['name'] for d in ancestor['declarations']}
    for doc, basis in pairs.values():
        if doc['declarations'][:len(ancestor['declarations'])] != ancestor['declarations']:
            raise ValueError('Common declarations changed; sharing requires review')
        if doc['statements'][:len(ancestor['statements'])] != ancestor['statements']:
            raise ValueError('Common statements changed; prefix removal requires review')
        primitive_basis = {row['symbol']: row for row in basis['primitives']}
        if any(primitive_basis[row['symbol']] != row for row in common_basis['primitives']):
            raise ValueError('Common primitive conventions changed')
        if any(basis['definitions'][name] != explanation for name, explanation in common_basis['definitions'].items()):
            raise ValueError('Common definition explanations changed')
    inputs = {label: deepcopy(pair[0]) for label, pair in pairs.items()}
    # This exact inherited prefix is already present in current, not a general
    # deduplication of repeated assertions, utterances or equal descriptions.
    inputs['confinement']['statements'] = inputs['confinement']['statements'][len(ancestor['statements']):]
    linked = link_documents(inputs, shared={'confinement': {name: ('current', name) for name in common_names}})
    return linked, pairs, ancestor


def source_composed():
    linked, pairs, ancestor = linkage()
    basis = deepcopy(pairs['current'][1])
    basis.update(version='kant-linked-draft-basis-v1', document='examples/v014/kant-linked-draft.noema')
    common = {d['name'] for d in ancestor['declarations']}
    mapping = linked.symbols['confinement']
    changed = {old: new for old, new in mapping.items() if old != new}

    def explanation(text):
        # These reviewed convention texts use these tokens as Noema names.
        return re.sub(r'(?<![a-z2-7])[a-z2-7]+(?![a-z2-7])', lambda match: changed.get(match[0], match[0]), text)

    for row in pairs['confinement'][1]['primitives']:
        if row['symbol'] not in common:
            moved = deepcopy(row)
            moved['symbol'] = mapping[row['symbol']]
            moved['meaning_ja'] = explanation(row['meaning_ja'])
            basis['primitives'].append(moved)
    for old, meaning in pairs['confinement'][1]['definitions'].items():
        if old not in common:
            basis['definitions'][mapping[old]] = explanation(meaning)
    basis['unresolved'] += [explanation(text) for text in pairs['confinement'][1]['unresolved'] if text not in pairs['current'][1]['unresolved']]
    basis['unresolved'].append('分岐した草案を参照を保って結合した文書であり、二枝の内容の現実的な整合性や原文の全文意味一致を証明したものではない。未記述箇所と基本概念の説明は残る。')
    basis['linkage'] = {'sources': SOURCES, 'ancestor': ANCESTOR, 'symbols': linked.symbols,
        'omitted_exact_common_statement_prefix': len(ancestor['statements']),
        'statement_maps': linked.statements, 'independent_same_spelling_is_not_shared': True}
    audit_basis(linked.document, basis)
    return format_graph(linked.document, 'compact') + '\n', basis


def main():
    text, basis = source_composed()
    for path, body in ((ROOT / basis['document'], text), (ROOT / 'data/kant-linked-draft-basis-v1.json',
            json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
        if path.exists():
            if path.read_text(encoding='utf-8') != body:
                raise ValueError('Stored linked Kant draft differs')
        else:
            with path.open('x', encoding='utf-8', newline='\n') as stream:
                stream.write(body)
    print('Kant branches linked with explicit ancestry and relocated descriptions')


if __name__ == '__main__':
    main()
