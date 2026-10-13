"""Extract closed definition dependencies without rewriting their syntax."""
from copy import deepcopy
from dataclasses import dataclass

from .discourse import normalize_document
from .meaning_basis import audit_basis
from .semantics import require


def _references(value):
    """Include references under quotations, folds and nested statements."""
    result = set()
    if isinstance(value, dict):
        if value.get('kind') in ('call', 'function_ref'):
            result.add(value['symbol'])
        for child in value.values():
            result.update(_references(child))
    elif isinstance(value, list):
        for child in value:
            result.update(_references(child))
    return result


@dataclass
class ExtractedDocument:
    document: dict
    roots: list
    statement_indices: list
    retained_symbols: list
    removed_symbols: list


def extract_document(document, *, roots=(), statement_indices=None):
    """Keep requested symbols, statements and their transitive references.

    By default ALL statements survive. Passing [] explicitly extracts a
    definitions-only library. Selected statements retain source order, even
    if indices are supplied in another order. Repeated source statements are
    preserved; repeated indices are rejected. Names, quoted bodies, aliases,
    statement scopes and the edition remain unchanged. No input is mutated.
    An empty result is rejected by the language's existing document rules.
    """
    doc = normalize_document(document)
    require(isinstance(roots, (list, tuple)) and all(isinstance(s, str) for s in roots),
            'Roots must be a list or tuple of symbol names')
    declarations = {d['name']: d for d in doc['declarations']}
    require(set(roots) <= set(declarations), 'Unknown extraction root')
    if statement_indices is None:
        indices = list(range(len(doc['statements'])))
    else:
        require(isinstance(statement_indices, (list, tuple)), 'Statement indices must be a list or tuple')
        require(all(type(i) is int and 0 <= i < len(doc['statements']) for i in statement_indices),
                'Invalid statement index')
        require(len(set(statement_indices)) == len(statement_indices), 'Duplicate statement index')
        indices = sorted(statement_indices)
    statements = [doc['statements'][i] for i in indices]
    pending = set(roots) | _references(statements)
    retained = set()
    while pending:
        symbol = pending.pop()
        if symbol in retained:
            continue
        retained.add(symbol)
        pending.update(_references(declarations[symbol]) - retained)
    selected = {**deepcopy(doc), 'declarations': [deepcopy(d) for d in doc['declarations'] if d['name'] in retained],
                'statements': deepcopy(statements)}
    selected = normalize_document(selected)
    # Normalization must not turn extraction into substitution or rewriting.
    require(selected['declarations'] == [d for d in doc['declarations'] if d['name'] in retained]
            and selected['statements'] == statements, 'Extraction changed retained syntax')
    return ExtractedDocument(selected, sorted(set(roots)), indices,
        [d['name'] for d in doc['declarations'] if d['name'] in retained],
        [d['name'] for d in doc['declarations'] if d['name'] not in retained])


def extract_basis(document, basis, extraction, *, version, document_path):
    """Project meaning entries; retain all caveats without copying stale maps.

    Linkage maps and other source-specific metadata are not reinterpreted as
    belonging to the new document. Their source location remains explicit.
    """
    audit_basis(document, basis)
    require(isinstance(extraction, ExtractedDocument), 'Expected an extracted document')
    checked = extract_document(document, roots=extraction.roots, statement_indices=extraction.statement_indices)
    require(checked == extraction, 'Extraction does not match source')
    require(isinstance(version, str) and version.strip(), 'Missing extracted basis version')
    require(isinstance(document_path, str) and document_path.strip(), 'Missing extracted document path')
    kept = set(extraction.retained_symbols)
    result = {'version': version, 'document': document_path,
        'primitives': [deepcopy(row) for row in basis['primitives'] if row['symbol'] in kept],
        'definitions': {name: meaning for name, meaning in basis['definitions'].items() if name in kept},
        'unresolved': deepcopy(basis.get('unresolved', [])),
        'extraction_source': {'basis_version': basis.get('version'), 'document': basis.get('document'),
            'roots': extraction.roots[:], 'statement_indices': extraction.statement_indices[:],
            'metadata_policy': 'Meaning entries are projected; all source caveats are retained. Other source metadata is not copied.'}}
    audit_basis(extraction.document, result)
    return result
