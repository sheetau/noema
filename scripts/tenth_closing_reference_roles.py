"""Typed candidate descriptions for the acknowledgment and date notices.

Descriptions retain complete source conditions. Opaque reference lookup does
not assert them, establish a unique referent or execute quoted claims.
"""
from copy import deepcopy

WORK = ('zrqwork', 'eis6k')
CALENDAR = ('eis6o', 'eis6p', 'eis6q')
COVERAGE = ('zrrhistory', 'zrrscope', 'zrroccasions')
ACTIVITY = ('zrqoccurs', 'zrqperforms', 'zrqproduces', 'zrquses', 'zrqstandard', 'zrqmeets')
JUDGING = ('zrqjudgments', 'zrqmatters', 'zrqlinked', 'zrqcandidates')
PURPOSE = ('zrraims', 'zrrgoalfor')
GROUPS = (WORK, ('zrqperson',), ('eis6t',), CALENDAR, ('eis6r',),
          ('eis6u',), COVERAGE, ('zrrbefore',), ('zrrworking',), ACTIVITY,
          JUDGING, PURPOSE, ('zrqscope',))
CANDIDATES = tuple(n for group in GROUPS for n in group)


def var(name): return dict(kind='variable', name=name)
def call(name, *args): return dict(kind='call', symbol=name, arguments=list(args))
def both(*args):
    if len(args) < 2: raise ValueError('Conjunction needs at least two arguments')
    return dict(kind='and', arguments=[args[0], args[1] if len(args) == 2 else both(*args[1:])])


def walk(node):
    if isinstance(node, list):
        for value in node: yield from walk(value)
    elif isinstance(node, dict):
        yield node
        for value in node.values(): yield from walk(value)


def substitute(node, variables=None, references=None):
    """Replace free variables and closed calls, respecting every source binder.

The caller uses fresh names; reject accidental capture instead of silently
changing a source binding. Quotation nodes are retained as quotation nodes.
"""
    variables = {} if variables is None else variables
    references = {} if references is None else references
    if isinstance(node, list):
        return [substitute(x, variables, references) for x in node]
    if not isinstance(node, dict): return node
    if node.get('kind') == 'variable' and node['name'] in variables:
        return deepcopy(variables[node['name']])
    if node.get('kind') == 'call' and node['symbol'] in references:
        if node['arguments']: raise ValueError('Candidate reference is no longer closed')
        return deepcopy(references[node['symbol']])
    bound = set()
    if node.get('kind') in {'exists', 'forall', 'content'}:
        bound.add(node['variable'])
    if node.get('kind') == 'lambda':
        bound.update(p['name'] for p in node['parameters'])
    active = {n: value for n, value in variables.items() if n not in bound}
    inserted = {x['name'] for value in [*active.values(), *references.values()]
                for x in walk(value) if x.get('kind') == 'variable'}
    if bound & inserted: raise ValueError('Candidate substitution would capture a variable')
    return {k: substitute(v, active if k == 'body' else variables, references)
            for k, v in node.items()}


def build_roles(document):
    source = {d['name']: d for d in document['declarations']}
    roles = {}
    # A reserved fresh namespace makes substitution independent of historical
    # normalizer variable names, while still detecting any future collision.
    if any(str(x.get('name', x.get('variable', ''))).startswith('closing')
           for d in source.values() for x in walk(d)):
        raise ValueError('Source now uses the reserved closing-role namespace')

    def content(name):
        node = source[name]['body']
        if source[name]['parameters'] or node['kind'] != 'content':
            raise ValueError('Expected closed source content: '+name)
        return substitute(node['body'], {node['variable']: var('closingcontext')})

    def unique(body, symbol):
        found = [x for x in walk(body) if x.get('kind') == 'call' and x['symbol'] == symbol]
        if len(found) != 1: raise ValueError('Expected one source call: '+symbol)
        return deepcopy(found[0])

    def project(peers, body, extra=()):
        for candidate in peers:
            witnesses = [n for n in peers if n != candidate]
            replacements = {candidate: var('closingcandidate')}
            replacements.update({n: var('closingpeer'+n) for n in witnesses})
            projected = substitute(body, references=replacements)
            if not any(x == var('closingcandidate') for x in walk(projected)):
                raise ValueError('Candidate does not occur: '+candidate)
            binders = [(n, source[n]['result']) for n in witnesses]
            binders = [('closingpeer'+n, t) for n, t in binders] + list(extra)
            for name, sort in reversed(binders):
                projected = dict(kind='exists', variable=name, sort=deepcopy(sort), body=projected)
            roles[candidate] = dict(kind='definition', name='closingrole'+candidate,
                parameters=[dict(name='closingcandidate', sort=deepcopy(source[candidate]['result'])),
                            dict(name='closingcontext', sort='situation')], result='truth', body=projected)

    research = content('etr'); acknowledgment = content('ett'); dateline = content('ety')
    project(WORK, both(unique(research, 'eis5v'), unique(research, 'eis5w')))
    project(('zrqperson',), both(unique(research, 'eis5t'), unique(research, 'eis5u'),
        unique(acknowledgment, 'eira'),
        dict(kind='not', arguments=[dict(kind='equal', arguments=[call('eis6l'), call('zrqperson')])]),
        unique(acknowledgment, 'eirb')))
    project(('eis6t',), both(unique(dateline, 'eira'),
        dict(kind='not', arguments=[dict(kind='equal', arguments=[call('eis6s'), call('eis6t')])]),
        unique(dateline, 'eirb'), unique(dateline, 'eis6c')))
    project(CALENDAR, unique(dateline, 'etw'))
    received = content('et3')
    project(('eis6r',), unique(received, 'etx'))
    project(('eis6u',), received)
    project(COVERAGE, unique(research, 'eis5y'))
    project(('zrrbefore',), call('sewm', call('zrrhistory'), call('zrrbefore')))
    temporal = source['etm']
    if [p['sort'] for p in temporal['parameters']] != ['individual']*4+['situation']:
        raise ValueError('Past contribution/current appraisal signature changed')
    actual = [call('rd'), call('zrqperson'), var('closinginput'), call('zrqwork'), var('closingcontext')]
    activity = substitute(temporal['body'], dict(zip([p['name'] for p in temporal['parameters']], actual, strict=True)))
    project(('zrrworking',), unique(activity, 'sewq'))
    project(ACTIVITY, activity, [('closinginput', 'individual')])
    project(JUDGING, content('etq'))
    project(PURPOSE, unique(content('sewx'), 'sewt'))
    project(('zrqscope',), acknowledgment)
    if tuple(roles) != CANDIDATES: raise ValueError('Closing role inventory changed')
    return roles


def dependency_graph(document, roles):
    """Expand source definitions, including those inside quotations."""
    from noema.meaning_catalog import _references
    source = {d['name']: d for d in document['declarations']}
    graph = {}; dependencies = set()
    order = {n: i for i, group in enumerate(GROUPS) for n in group}
    for name, role in roles.items():
        seen = set(); pending = list(_references(role['body']))
        while pending:
            symbol = pending.pop()
            if symbol in seen: continue
            seen.add(symbol)
            pending.extend(_references(source[symbol].get('body')) - seen)
        peers = seen & set(roles)
        if any(order[n] >= order[name] for n in peers):
            raise ValueError('Closing role is self-referential or points to a later group: '+name)
        graph[name] = sorted(peers); dependencies.update(seen)
    return graph, dependencies


def build_report():
    import hashlib, json
    from pathlib import Path
    from noema.constructed_discourse import normalize_document
    from noema.extraction import extract_document
    from scripts.check_manuscript_context import catalogs
    root = Path(__file__).resolve().parents[1]; catalog = catalogs()['einstein-1905']
    roles = build_roles(catalog.document)
    graph, dependencies = dependency_graph(catalog.document, roles)
    selected = extract_document(catalog.document, roots=sorted(dependencies), statement_indices=[]).document
    selected['declarations'] += list(roles.values())
    normalize_document(selected)
    paths = set(catalog.source_sha256) | {catalog.document_path, 'data/work-state.json',
        'scripts/tenth_closing_reference_roles.py', 'tests/test_tenth_closing_reference_roles.py',
        'noema/constructed_discourse.py', 'noema/constructed_semantics.py', 'noema/extraction.py',
        'noema/meaning_catalog.py', 'scripts/check_manuscript_context.py'}
    return dict(schema='noema-tenth-closing-reference-roles-1',
        status='closed_typed_roles_checked_against_full_source_dependencies', roles=len(roles),
        role_dependency_graph=graph, normalized_source_closure=True,
        definition_sha256={n: hashlib.sha256(json.dumps(d, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
                           for n, d in sorted(roles.items())},
        actual_svg_decoding_performed=False, document_integration_credit=0,
        limitations=['Descriptions do not establish existence, uniqueness or joint witnesses.',
            'Quotes remain nonfactive; work goals do not assert achievement.',
            'Calendar roles retain the explicit civil Gregorian reading.',
            'Source connection and actual visible decoding remain separate checks.'],
        source_sha256={p: hashlib.sha256((root/p).read_bytes()).hexdigest() for p in sorted(paths)})
