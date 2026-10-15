"""Structural evidence for a manually reviewed source passage.

Reachability includes quoted syntax. It never certifies semantic equivalence,
execution, or that a parameterized template has been instantiated.
"""
from collections import deque
from copy import deepcopy
from hashlib import sha256
from .extraction import _references


def require(condition, message):
    if not condition: raise ValueError(message)


def audit(document, source_unit, review):
    """Validate a partitioned review and record reproducible dependency paths.

    The caller supplies an already parsed/typed document. A passage partition
    establishes that its text was considered, not that it was translated.
    Review decisions remain human-readable open obligations.
    """
    text = source_unit['text']
    digest = sha256(text.encode('utf-8')).hexdigest()
    require(digest == source_unit['text_sha256'] == review['source_sha256'], 'Source hash differs')
    require(source_unit['id'] == review['unit'], 'Source unit differs')
    require(review['semantic_completion'] is False, 'This audit cannot certify completion')
    require(review['counts_as_translated_coverage'] is False, 'Review partition is not translation coverage')
    start, end = review['passage_range']
    require(type(start) is int and type(end) is int and 0 <= start < end <= len(text), 'Invalid passage range')
    lookup = {d['name']: d for d in document['declarations']}
    require(len(lookup) == len(document['declarations']), 'Duplicate declaration')
    dependencies = {name: sorted(_references(d)) for name, d in lookup.items()}
    require(all(set(refs) <= lookup.keys() for refs in dependencies.values()), 'Unknown declaration dependency')
    indices = review['statement_indices']
    require(isinstance(indices, list) and indices and len(set(indices)) == len(indices), 'Invalid statement selection')
    require(all(type(i) is int and 0 <= i < len(document['statements']) for i in indices), 'Invalid statement index')

    def paths(selected):
        found = {}
        pending = deque()
        for index in sorted(selected):
            for symbol in sorted(_references(document['statements'][index])):
                require(symbol in lookup, 'Unknown statement dependency')
                pending.append((symbol, {'statement_index': index, 'symbols': [symbol]}))
        while pending:
            symbol, path = pending.popleft()
            if symbol in found: continue
            found[symbol] = path
            for child in dependencies[symbol]:
                pending.append((child, {'statement_index': path['statement_index'], 'symbols': path['symbols'] + [child]}))
        return found

    selected_paths = paths(indices)
    all_paths = paths(range(len(document['statements'])))
    cursor = start
    seen = set()
    rows = []
    for entry in review['obligations']:
        require(isinstance(entry['id'], str) and entry['id'] and entry['id'] not in seen, 'Duplicate or empty obligation ID')
        seen.add(entry['id'])
        a, b = entry['range']
        require(type(a) is int and type(b) is int and a == cursor and a < b <= end, 'Review partition gap or overlap')
        require(entry['source'] == text[a:b], 'Source excerpt differs')
        require(entry['decision'] == 'open' and bool(entry['remaining'].strip()), 'Missing open review decision')
        roots = entry['candidate_roots']
        require(isinstance(roots, list) and all(isinstance(s, str) for s in roots) and len(set(roots)) == len(roots), 'Invalid candidate roots')
        require(set(roots) <= lookup.keys(), 'Unknown candidate root')
        findings = []
        for root in roots:
            findings.append({'symbol': root, 'kind': lookup[root]['kind'],
                'selected_statement_path': deepcopy(selected_paths.get(root)),
                'any_statement_path': deepcopy(all_paths.get(root))})
        rows.append({**deepcopy(entry), 'structural_evidence': findings,
            'unconnected_candidate_roots': [r for r in roots if r not in selected_paths],
            'has_recorded_candidate': bool(roots)})
        cursor = b
    require(rows and cursor == end, 'Review partition is incomplete')

    templates = []
    for template in review['templates']:
        name = template['symbol']
        require(name in lookup and lookup[name]['kind'] == 'definition', 'Unknown template definition')
        roles = template['parameter_roles']
        params = lookup[name]['parameters']
        require(len(roles) == len(params) and all(isinstance(r, str) and r.strip() for r in roles), 'Template parameter roles differ')
        sites = []
        def visit(value, owner, path):
            if isinstance(value, dict):
                if value.get('kind') == 'quote' and value.get('body') == {'kind': 'function_ref', 'symbol': name}:
                    sites.append({'owner': owner, 'path': path, 'rank': value.get('rank', 0)})
                for key, child in sorted(value.items()): visit(child, owner, path + '/' + key)
            elif isinstance(value, list):
                for i, child in enumerate(value): visit(child, owner, path + '/' + str(i))
        for owner in sorted(selected_paths): visit(lookup[owner], owner, '')
        for index in sorted(indices): visit(document['statements'][index], 'statement:' + str(index), '')
        templates.append({'symbol': name, 'selected_statement_path': deepcopy(selected_paths.get(name)),
            'literal_function_quote_sites': sites,
            'parameters': [{'index': i, 'role': roles[i], 'sort': deepcopy(p['sort'])} for i, p in enumerate(params)],
            'interpretation': 'A function-reference quote describes the parameterized definition; it does not bind these parameters.'})
    return {'status': 'structural_review_with_open_semantic_obligations', 'unit': source_unit['id'],
        'passage_range': [start, end], 'source_sha256': digest, 'statement_indices': sorted(indices),
        'obligations': rows, 'templates': templates, 'semantic_completion': False,
        'counts_as_translated_coverage': False,
        'limits': [
            'Paths include quotations and code syntax; reachability is not execution or source equivalence.',
            'No path to a named candidate does not exclude another equivalent expression or dynamic argument binding.',
            'The passage partition records review scope only; it adds no translated characters or verified source units.',
            'Candidate roots, semantic obligations and parameter-role explanations are reviewed inputs, not inferred semantics.']}
