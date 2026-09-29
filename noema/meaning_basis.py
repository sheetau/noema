"""Match a document's semantic conventions to its declared signatures.

This audits explanatory documentation, not truth or grounding in the world.
"""
from .discourse import normalize_document, definition_audit
from .semantics import require


def audit_basis(document, basis):
    doc = normalize_document(document)
    require(isinstance(basis, dict) and isinstance(basis.get('primitives'), list), 'Invalid semantic basis')
    records = basis['primitives']
    require(all(isinstance(r, dict) and isinstance(r.get('symbol'), str) for r in records), 'Invalid basis entry')
    lookup = {r['symbol']: r for r in records}
    require(len(lookup) == len(records), 'Duplicate basis symbol')
    primitives = [d for d in doc['declarations'] if d['kind'] == 'primitive']
    definitions = [d for d in doc['declarations'] if d['kind'] == 'definition']
    require(set(lookup) == {d['name'] for d in primitives}, 'Basis and primitive inventory differ')
    for d in primitives:
        r = lookup[d['name']]
        require(r.get('parameters') == d['parameters'] and r.get('result') == d['result'], 'Basis signature differs')
        require(isinstance(r.get('arguments'), list) and len(r['arguments']) == len(d['parameters'])
                and all(isinstance(a, str) and a for a in r['arguments'])
                and len(set(r['arguments'])) == len(r['arguments']), 'Invalid argument labels')
        require(isinstance(r.get('meaning_ja'), str) and r['meaning_ja'].strip(), 'Missing meaning convention')
    require(isinstance(basis.get('definitions'), dict) and set(basis['definitions']) == {d['name'] for d in definitions},
            'Basis and defined vocabulary differ')
    require(all(isinstance(v, str) and v.strip() for v in basis['definitions'].values()), 'Missing definition explanation')
    return {'primitive_count': len(primitives), 'definition_count': len(definitions),
            'signature_and_documentation_coverage': True, 'definition_dependencies': definition_audit(doc),
            'semantic_equivalence_to_source_proven': False}
