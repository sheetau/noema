"""Whole typed projections, quotation dependencies and small binding checks."""
from copy import deepcopy
from functools import lru_cache
import pytest
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import evaluate_document
from noema.meaning_catalog import _references
from scripts.check_manuscript_context import catalogs
from scripts import tenth_closing_reference_roles as roles


def var(n): return dict(kind='variable', name=n)
def call(n, *args): return dict(kind='call', symbol=n, arguments=list(args))
def both(*args):
    result = args[-1]
    for arg in reversed(args[:-1]): result = dict(kind='and', arguments=[arg, result])
    return result
def quote(n): return dict(kind='quote', body=call(n))
def number(n): return dict(kind='number', numerator=n, denominator=1)


@lru_cache(None)
def source(): return catalogs()['einstein-1905'].document


@lru_cache(None)
def actual(): return roles.build_roles(source())


def replace(node, variables, calls):
    # Independent expected projection: normalized source names are disjoint
    # from these descriptive test names. Only its outer context is supplied.
    if isinstance(node, list): return [replace(x, variables, calls) for x in node]
    if not isinstance(node, dict): return node
    if node.get('kind') == 'variable' and node['name'] in variables:
        return deepcopy(variables[node['name']])
    if node.get('kind') == 'call' and node['symbol'] in calls:
        assert not node['arguments']
        return deepcopy(calls[node['symbol']])
    return {k: replace(v, variables, calls) for k, v in node.items()}


def expected(candidate):
    declarations = {d['name']: d for d in source()['declarations']}
    ctx = var('context')
    def content(name):
        node = declarations[name]['body']; assert node['kind'] == 'content'
        return replace(node['body'], {node['variable']: ctx}, {})
    def tuple_call(name, names):
        return call(name, *(ctx if n == 'context' else call(n) for n in names.split()))
    def distinct(a, b): return dict(kind='not', arguments=[dict(kind='equal', arguments=[call(a), call(b)])])
    peers = (candidate,); extra = []
    if candidate in ('zrqwork', 'eis6k'):
        peers = ('zrqwork', 'eis6k')
        body = both(tuple_call('eis5v', 'zrqwork eis6k context'), tuple_call('eis5w', 'eirf eis6k context'))
    elif candidate == 'zrqperson':
        body = both(tuple_call('eis5t', 'rd zrqperson context'), tuple_call('eis5u', 'rd zrqperson context'),
            tuple_call('eira', 'eis6i context'), distinct('eis6l', 'zrqperson'),
            tuple_call('eirb', 'eis6i eis6l zrqperson context'))
    elif candidate == 'eis6t':
        body = both(tuple_call('eira', 'eis6m context'), distinct('eis6s', 'eis6t'),
            tuple_call('eirb', 'eis6m eis6s eis6t context'), tuple_call('eis6c', 'eis6m eirf eis6t context'))
    elif candidate in ('eis6o', 'eis6p', 'eis6q'):
        peers = ('eis6o', 'eis6p', 'eis6q')
        body = call('etw', *[call(n) for n in peers], number(1905), number(5), ctx)
    elif candidate == 'eis6r':
        body = call('etx', *[call(n) for n in ('eis6o','eis6p','eis6q','eis6r')],
            number(1905), number(5), number(29), ctx,
            *[dict(kind='function_ref', symbol=n) for n in ('eis5z','eis6a','eis6b')])
    elif candidate == 'eis6u': body = content('et3')
    elif candidate in ('zrrhistory', 'zrrscope', 'zrroccasions'):
        peers = ('zrrhistory', 'zrrscope', 'zrroccasions')
        body = tuple_call('eis5y', 'rd zrqwork zrrhistory zrrscope zrroccasions context')
    elif candidate == 'zrrbefore': body = tuple_call('sewm', 'zrrhistory zrrbefore')
    elif candidate == 'zrrworking':
        body = tuple_call('sewq', 'rd zrqwork context zrrhistory zrrscope zrrbefore zrrworking')
    elif candidate in ('zrqoccurs','zrqperforms','zrqproduces','zrquses','zrqstandard','zrqmeets'):
        peers = ('zrqoccurs','zrqperforms','zrqproduces','zrquses','zrqstandard','zrqmeets')
        d = declarations['etm']; extra = [('input', 'individual')]
        assert [p['sort'] for p in d['parameters']] == ['individual']*4+['situation']
        values = [call('rd'), call('zrqperson'), var('input'), call('zrqwork'), ctx]
        body = replace(d['body'], dict(zip([p['name'] for p in d['parameters']], values, strict=True)), {})
    elif candidate in ('zrqjudgments','zrqmatters','zrqlinked','zrqcandidates'):
        peers = ('zrqjudgments','zrqmatters','zrqlinked','zrqcandidates'); body = content('etq')
    elif candidate in ('zrraims','zrrgoalfor'):
        peers = ('zrraims','zrrgoalfor')
        body = call('sewt', call('zrqperson'), call('rd'), call('zrqwork'), quote('sewv'), ctx,
            *[call(n) for n in ('zrrhistory','zrrscope','zrrbefore','zrroccasions','zrqoccurs',
                                'zrqperforms','zrraims','zrrgoalfor','zrrworking')])
    elif candidate == 'zrqscope': body = content('ett')
    else: raise AssertionError(candidate)
    replacements = {n: var('candidate' if n == candidate else 'witness'+n) for n in peers}
    body = replace(body, {}, replacements)
    binders = [('witness'+n, declarations[n]['result']) for n in peers if n != candidate]+extra
    for name, sort in reversed(binders): body = dict(kind='exists', variable=name, sort=sort, body=body)
    return dict(kind='definition', name='closingrole'+candidate, parameters=[
        dict(name='candidate', sort=declarations[candidate]['result']), dict(name='context', sort='situation')],
        result='truth', body=body)


def interface(role):
    lookup = {d['name']: d for d in source()['declarations']}; declarations = []
    for name in sorted(_references(role['body'])):
        d = lookup[name]
        params = [p['sort'] for p in d['parameters']] if d['kind'] == 'definition' else d['parameters']
        declarations.append(dict(kind='primitive', name=name, parameters=deepcopy(params), result=deepcopy(d['result'])))
    return dict(schema_version='0.16', lexicon_version='0.16', declarations=declarations+[deepcopy(role)], statements=[])


@pytest.mark.parametrize('candidate', roles.CANDIDATES)
def test_complete_typed_projection(candidate):
    assert normalize_document(interface(actual()[candidate])) == normalize_document(interface(expected(candidate)))


TUPLE_ROLES = ('zrqwork','eis6k','eis6o','eis6p','eis6q','eis6r',
               'zrrhistory','zrrscope','zrroccasions','zrrbefore','zrrworking','zrraims','zrrgoalfor')


@pytest.mark.parametrize('candidate', TUPLE_ROLES)
def test_every_tuple_slot_and_each_witness_binding(candidate):
    # The preceding whole typed comparison preserves numbers, quotations and
    # function sorts. Here only the binding structure is abstracted to two
    # individuals; this is not a proof over the original function domains.
    role = normalize_document(interface(actual()[candidate]))['declarations'][-1]
    body = role['body']; binders = []
    while body['kind'] == 'exists':
        binders.append(body['variable']); body = body['body']
    atoms = body['arguments'] if body['kind'] == 'and' else [body]
    assert all(a['kind'] == 'call' for a in atoms)
    seen_slots = set(); seen_binders = set()
    context = role['parameters'][1]['name']; candidate_variable = role['parameters'][0]['name']
    for selected in [None, *binders]:
        env = {candidate_variable: 'fixed', context: 'context'}
        env.update({b: 'chosen' if b == selected else 'fixed' for b in binders})
        rows = {a['symbol']: tuple(env[x['name']] if x['kind'] == 'variable' else 'fixed'
                                  for x in a['arguments']) for a in atoms}
        abstract = []
        for a in atoms:
            args = [deepcopy(x) if x['kind'] == 'variable' else call('fixed') for x in a['arguments']]
            abstract.append(call(a['symbol'], *args))
        body = both(*abstract) if len(abstract) > 1 else abstract[0]
        body = replace(body, {b: call('fixed') for b in binders if b != selected}, {})
        if selected is not None:
            body = dict(kind='exists', variable=selected, sort='individual', body=both(
                dict(kind='equal', arguments=[var(selected), call('chosen')]), body))
        d = deepcopy(role); d['body'] = body; d['parameters'][0]['sort'] = 'individual'
        declarations = [dict(kind='primitive', name=a['symbol'],
            parameters=['situation' if x == var(context) else 'individual' for x in a['arguments']],
            result='truth') for a in atoms]
        declarations += [dict(kind='primitive', name=n, parameters=[], result=t)
                         for n, t in [('fixed','individual'), ('chosen','individual'), ('context','situation')]]
        document = dict(schema_version='0.16', lexicon_version='0.16', declarations=declarations+[d],
            statements=[dict(kind='ask', body=call(d['name'], call('fixed'), call('context')))])
        def evaluate(expected_rows):
            handlers = {n: (lambda n=n: n) for n in ('fixed','chosen','context')}
            handlers.update({n: (lambda *args, row=row: args == row) for n, row in expected_rows.items()})
            return evaluate_document(document, individuals=('fixed','chosen'),
                situations=('context','othercontext'), primitives=handlers)[0]['value']
        assert evaluate(rows)
        for name, row in rows.items():
            for slot, value in enumerate(row):
                if selected is not None and value != 'chosen': continue
                wrong = 'othercontext' if value == 'context' else 'fixed' if value == 'chosen' else 'chosen'
                assert not evaluate(rows | {name: row[:slot]+(wrong,)+row[slot+1:]})
                seen_slots.add((name, slot))
                if selected is not None: seen_binders.add(selected)
    assert seen_slots == {(a['symbol'], i) for a in atoms for i in range(len(a['arguments']))}
    assert seen_binders == set(binders)


def test_expanded_quote_graph_is_acyclic_and_source_unchanged():
    before = deepcopy(source()); built = roles.build_roles(source())
    assert source() == before
    graph, deps = roles.dependency_graph(source(), built)
    assert len(graph) == 27
    assert set(graph['zrqscope']) == set(roles.CANDIDATES)-set(roles.CALENDAR)-{'eis6r','eis6u','eis6t','zrqscope'}
    assert set(graph['eis6u']) == {'eis6o','eis6p','eis6q','eis6r'}
    assert 'sewv' in deps and 'zrradvances' in deps and 'eto' in deps
    assert 'sewb' not in deps  # Keep the source's static criterion specialization.
    for n in roles.PURPOSE:
        assert any(x == quote('sewv') for x in roles.walk(built[n]['body']))
        assert not any(x.get('kind') == 'evaluate' for x in roles.walk(built[n]['body']))
    for n in roles.JUDGING:
        assert sum(x == quote('eto') for x in roles.walk(built[n]['body'])) == 2


def test_substitution_respects_shadowing_and_rejects_capture():
    node = dict(kind='exists', variable='outer', sort='individual', body=var('outer'))
    assert roles.substitute(node, {'outer': call('rd')}) == node
    capture = dict(kind='exists', variable='closingcandidate', sort='individual', body=call('zrqperson'))
    with pytest.raises(ValueError, match='capture'):
        roles.substitute(capture, references={'zrqperson': var('closingcandidate')})
    with pytest.raises(ValueError, match='no longer closed'):
        roles.substitute(call('zrqperson', call('rd')), references={'zrqperson': var('closingcandidate')})
