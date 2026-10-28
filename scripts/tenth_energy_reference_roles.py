"""Closed reference descriptions for the shared electron-energy setting.

These descriptions identify candidates; separate lookups neither establish a
common witness nor assert the original energy argument. Its joint body must
still be connected and checked unchanged.
"""
from copy import deepcopy


PHYSICAL = frozenset(
    ['eis2'+c for c in 'abcdefghijklmno'] +
    ['zrgcharge', 'zrgfield', 'zrgposition', 'zrgprofile', 'zrgstart',
     'zrgunit', 'zrhcurve', 'zrhdomain', 'zrhendpoint', 'zrhstartpoint',
     'zriacceleration', 'zrivelocity'])
VALUES = frozenset(('zrfenergy', 'zrgwithdrawn', 'zrginitial', 'zrgradiated'))


def _variable(name):
    return dict(kind='variable', name=name)


def _call(name, *arguments):
    return dict(kind='call', symbol=name, arguments=list(arguments))


def _letters(index):
    result = ''
    while True:
        result = chr(97 + index % 26) + result
        index = index // 26 - 1
        if index < 0:
            return result


def build_roles(document):
    """Project the reviewed source tuples, preserving every original type."""
    source = {d['name']: d for d in document['declarations']}

    def content_arguments(name, predicate):
        body = source[name]['body']
        if (body['kind'] != 'content' or body['body']['kind'] != 'call'
                or body['body']['symbol'] != predicate):
            raise ValueError('Energy source content changed: ' + name)
        return body['variable'], deepcopy(body['body']['arguments'])

    context, setting = content_arguments('eo7', 'eou')
    other_context, all_args = content_arguments('epe', 'eo3')
    if (context != other_context or all_args[:len(setting)] != setting
            or source['eou']['parameters'] != source['eow']['parameters']
            or len(setting) != len(source['eou']['parameters'])
            or len(all_args) != len(source['eox']['parameters'])):
        raise ValueError('Energy source tuples no longer agree')
    local = PHYSICAL | VALUES | {'zrgepisode'}
    setting_names = {n['symbol'] for n in setting if n['kind'] == 'call'}
    all_names = {n['symbol'] for n in all_args if n['kind'] == 'call'}
    if (setting_names & local != PHYSICAL | {'zrgepisode'}
            or all_names & local != local):
        raise ValueError('Energy source reference inventory changed')
    roles = {}

    def project(candidate, predicates, arguments, peers):
        order = [n['symbol'] for n in arguments if n['kind'] == 'call'
                 and n['symbol'] in peers and n['symbol'] != candidate]
        if len(order) != len(set(order)):
            raise ValueError('Repeated energy witness in source tuple')
        bound = {name: 'energypeer'+_letters(i) for i, name in enumerate(order)}
        actual = []
        for node in arguments:
            if node['kind'] == 'variable' and node['name'] == context:
                actual.append(_variable('energycontext'))
            elif node['kind'] == 'call' and not node['arguments']:
                name = node['symbol']
                actual.append(_variable('energycandidate') if name == candidate else
                              _variable(bound[name]) if name in bound else deepcopy(node))
            else:
                raise ValueError('Unexpected energy tuple argument')
        if _variable('energycandidate') not in actual:
            raise ValueError('Energy candidate missing from source tuple')
        calls = [_call(name, *deepcopy(actual)) for name in predicates]
        body = calls[0] if len(calls) == 1 else dict(kind='and', arguments=calls)
        for name in reversed(order):
            body = dict(kind='exists', variable=bound[name],
                        sort=deepcopy(source[name]['result']), body=body)
        roles[candidate] = dict(kind='definition', name='energyrole'+candidate,
            parameters=[dict(name='energycandidate', sort=deepcopy(source[candidate]['result'])),
                        dict(name='energycontext', sort='situation')],
            result='truth', body=body)

    for name in sorted(PHYSICAL):
        project(name, ('eou', 'eow'), setting, PHYSICAL | {'zrgepisode'})
    # eou/eow do not constrain their episode parameter. Energy attribution does.
    project('zrgepisode', ('eox',), all_args, VALUES)
    for name in sorted(VALUES):
        project(name, ('eox',), all_args, VALUES)
    roles['eis3k'] = dict(kind='definition', name='energyroleeis3k', parameters=[
        dict(name='energycandidate', sort='individual'),
        dict(name='energycontext', sort='situation')], result='truth',
        body=_call('eiscv', _variable('energycandidate'), _call('eirf'),
                   dict(kind='quote', body=_call('eigj')), _variable('energycontext')))
    return roles


def build_report():
    """Check roles against full source bodies, independently of finite models."""
    import hashlib
    import json
    from pathlib import Path
    from noema.constructed_discourse import normalize_document
    from noema.extraction import extract_document
    from noema.meaning_catalog import _references
    from scripts.check_manuscript_context import catalogs
    root = Path(__file__).resolve().parents[1]
    catalog = catalogs()['einstein-1905']
    source = {d['name']: d for d in catalog.document['declarations']}
    roles = build_roles(catalog.document)
    graph = {}; dependencies = set()
    for name, declaration in roles.items():
        seen = set(); pending = list(_references(declaration['body']))
        while pending:
            symbol = pending.pop()
            if symbol in seen:
                continue
            seen.add(symbol)
            pending.extend(_references(source[symbol].get('body')) - seen)
        if name in seen:
            raise ValueError('Self-referential energy role: ' + name)
        graph[name] = sorted(seen & set(roles))
        dependencies.update(seen)
    if (any(graph[n] for n in PHYSICAL) or graph['eis3k']
            or not set(graph['zrgepisode']) <= PHYSICAL
            or any(not set(graph[n]) <= PHYSICAL | {'zrgepisode'} for n in VALUES)):
        raise ValueError('Unexpected energy role dependency')
    document = extract_document(catalog.document, roots=sorted(dependencies), statement_indices=[]).document
    document['declarations'] += list(roles.values())
    normalize_document(document)
    paths = set(catalog.source_sha256) | {catalog.document_path, 'data/work-state.json',
        'scripts/tenth_energy_reference_roles.py', 'tests/test_tenth_energy_reference_roles.py',
        'noema/constructed_discourse.py', 'noema/constructed_semantics.py',
        'noema/extraction.py', 'noema/meaning_catalog.py', 'scripts/check_manuscript_context.py'}
    return dict(schema='noema-tenth-energy-reference-roles-1',
        status='closed_typed_roles_checked_against_full_source_dependencies',
        roles=len(roles), physical_setting_roles=len(PHYSICAL), energy_value_roles=len(VALUES),
        role_dependency_graph=graph, normalized_source_closure=True,
        definition_sha256={n: hashlib.sha256(json.dumps(d, sort_keys=True, separators=(',', ':')).encode('utf-8')).hexdigest()
                           for n, d in sorted(roles.items())},
        actual_svg_decoding_performed=False, document_integration_credit=0,
        limitations=['Descriptions do not prove candidate existence, uniqueness or joint consistency.',
                    'Finite binding diagnostics do not prove physical laws over real/function domains.',
                    'The complete source argument must still be connected and decoded from SVG.'],
        source_sha256={p: hashlib.sha256((root/p).read_bytes()).hexdigest() for p in sorted(paths)})
