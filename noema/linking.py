"""Explicit, capture-free linking for definition-language documents.

Sharing is opt-in and checks structural identity after reference relocation.
The caller must establish that shared primitive conventions really agree.
Equal bodies do not make independently named descriptions interchangeable.
"""
from copy import deepcopy
from dataclasses import dataclass

from .discourse import name, normalize_document
from .grammar import number_word
from .semantics import require


def relocate(value, symbols):
    """Relocate global references, including those inside descriptions.

    This is an AST-fragment operation; callers validate complete documents.
    Bound variables, argument labels, and type syntax are never renamed.
    """
    if isinstance(value, list):
        return [relocate(item, symbols) for item in value]
    if not isinstance(value, dict):
        return value
    result = {key: relocate(item, symbols) for key, item in value.items()}
    if value.get('kind') in ('call', 'function_ref'):
        require(value['symbol'] in symbols, 'Missing relocation for global symbol')
        result['symbol'] = symbols[value['symbol']]
    if value.get('kind') in ('primitive', 'definition'):
        require(value['name'] in symbols, 'Missing relocation for declaration')
        result['name'] = symbols[value['name']]
    return result


@dataclass
class LinkedDocuments:
    document: dict
    symbols: dict
    statements: dict


def link_documents(documents, *, shared=None):
    """Link an ordered mapping of labels to documents of the same edition.

    shared[label][local_name] = (earlier_label, earlier_name) explicitly
    identifies a common declaration. Its relocated definition/signature must
    be identical. Each source's map is injective, preserving distinct local
    descriptions. Statements retain order and multiplicity without evaluation.
    No input is mutated; relocation and statement maps allow exact projection.
    """
    require(isinstance(documents, dict) and documents, 'Provide an ordered nonempty document mapping')
    require(all(isinstance(label, str) and label for label in documents), 'Invalid document label')
    shared = {} if shared is None else shared
    require(isinstance(shared, dict) and set(shared) <= set(documents), 'Unknown sharing source')
    normalized = {label: normalize_document(doc) for label, doc in documents.items()}
    first = next(iter(normalized.values()))
    require(all(doc['schema_version'] == first['schema_version'] for doc in normalized.values()),
            'Linking requires the same edition; upgrade explicitly first')
    reserved = {d['name'] for doc in normalized.values() for d in doc['declarations']}
    output = {**deepcopy(first), 'declarations': [], 'statements': []}
    symbols, statements, declarations = {}, {}, {}
    fresh_index = 0
    for label, doc in normalized.items():
        requests = shared.get(label, {})
        local_names = {d['name'] for d in doc['declarations']}
        require(isinstance(requests, dict) and set(requests) <= local_names, 'Unknown local sharing symbol')
        mapping = {}
        occupied = set(declarations)
        for declaration in doc['declarations']:
            original = declaration['name']
            if original in requests:
                target = requests[original]
                require(isinstance(target, (list, tuple)) and len(target) == 2
                        and all(isinstance(v, str) for v in target), 'Invalid sharing target')
                owner, symbol = target
                require(owner in symbols and symbol in symbols[owner], 'Sharing target must belong to an earlier source')
                chosen = symbols[owner][symbol]
            elif original not in occupied:
                chosen = original
            else:
                while True:
                    chosen = 'zz' + number_word(fresh_index)
                    fresh_index += 1
                    if chosen not in reserved and chosen not in occupied:
                        break
            name(chosen)
            require(chosen not in mapping.values(), 'Sharing would collapse distinct local descriptions')
            mapping[original] = chosen
            occupied.add(chosen)
        for declaration in doc['declarations']:
            moved = relocate(declaration, mapping)
            if declaration['name'] in requests:
                require(moved == declarations[moved['name']], 'Shared declaration differs after relocation')
            else:
                output['declarations'].append(moved)
                declarations[moved['name']] = moved
        offset = len(output['statements'])
        output['statements'].extend(relocate(doc['statements'], mapping))
        statements[label] = list(range(offset, len(output['statements'])))
        symbols[label] = mapping
    return LinkedDocuments(normalize_document(output), symbols, statements)


def project_document(linked, source, *, document=None):
    """Recover one normalized source; reject broken maps or cross-source refs."""
    require(isinstance(linked, LinkedDocuments) and source in linked.symbols, 'Unknown linked source')
    doc = normalize_document(linked.document if document is None else document)
    mapping = linked.symbols[source]
    require(len(set(mapping.values())) == len(mapping), 'Non-injective source map')
    declarations = {d['name']: d for d in doc['declarations']}
    require(set(mapping.values()) <= set(declarations), 'Linked declaration missing')
    reverse = {new: old for old, new in mapping.items()}
    indices = linked.statements[source]
    require(all(type(index) is int and 0 <= index < len(doc['statements']) for index in indices), 'Invalid statement map')
    result = {**doc,
        'declarations': [relocate(declarations[new], reverse) for new in mapping.values()],
        'statements': [relocate(doc['statements'][index], reverse) for index in indices]}
    return normalize_document(result)
