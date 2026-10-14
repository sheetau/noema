"""Audit structural references from manuscript statements into their vocabulary.

This includes quotations: a quoted formula is part of what a statement refers
to, even though it is not executed. Reachability is neither truth nor source
equivalence, and cannot resolve functions supplied by external interpretations.
"""
from collections import deque
from .discourse import normalize_document
from .semantics import require


def referenced_symbols(value):
    result = set()
    if isinstance(value, dict):
        if value.get('kind') in ('call', 'function_ref'):
            result.add(value['symbol'])
        for child in value.values():
            result.update(referenced_symbols(child))
    elif isinstance(value, list):
        for child in value:
            result.update(referenced_symbols(child))
    return result


def audit_integration(document):
    doc = normalize_document(document)
    declarations = {d['name']: d for d in doc['declarations']}
    direct, closures = {}, {}
    # The language checker has already rejected forward/circular definitions.
    for name, declaration in declarations.items():
        direct[name] = referenced_symbols(declaration.get('body', {}))
        closures[name] = {name}.union(*(closures[ref] for ref in direct[name]))
    statements, used = [], set()
    for index, statement in enumerate(doc['statements']):
        roots = referenced_symbols(statement)
        reachable = set().union(*(closures[ref] for ref in roots))
        used.update(reachable)
        statements.append(dict(index=index, kind=statement['kind'], direct_symbols=sorted(roots),
            reachable_symbols=sorted(reachable),
            primitive_symbols=sorted(s for s in reachable if declarations[s]['kind'] == 'primitive')))
    return dict(statement_count=len(statements), declaration_count=len(declarations),
        definition_count=sum(d['kind'] == 'definition' for d in declarations.values()),
        primitive_count=sum(d['kind'] == 'primitive' for d in declarations.values()),
        statements=statements, statement_reachable_symbols=sorted(used),
        unreferenced_definitions=[s for s, d in declarations.items() if d['kind'] == 'definition' and s not in used],
        direct_definition_references={s: sorted(refs) for s, refs in direct.items() if declarations[s]['kind'] == 'definition'},
        quoted_references_included=True, structural_audit_only=True, semantic_equivalence_verified=False)


def dependency_path(document, statement_index, target):
    """Return a shortest structural reference path, or None if not referenced."""
    doc = normalize_document(document)
    require(type(statement_index) is int and 0 <= statement_index < len(doc['statements']), 'Invalid statement index')
    declarations = {d['name']: d for d in doc['declarations']}
    require(isinstance(target, str) and target in declarations, 'Unknown integration target')
    pending = deque((name, [name]) for name in sorted(referenced_symbols(doc['statements'][statement_index])))
    visited = set()
    while pending:
        name, path = pending.popleft()
        if name in visited: continue
        visited.add(name)
        if name == target: return path
        pending.extend((ref, path + [ref]) for ref in sorted(referenced_symbols(declarations[name].get('body', {}))) if ref not in visited)
    return None
