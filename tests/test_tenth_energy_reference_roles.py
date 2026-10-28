"""Typed source projections and finite, one-witness binding diagnostics.

Opaque physical/function types are erased only after comparing the entire
typed role. These diagnostics do not prove the underlying physical laws.
"""
from copy import deepcopy
from functools import lru_cache
import json
import pytest
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import evaluate_document
from noema.meaning_catalog import _references
from scripts.check_manuscript_context import catalogs
from scripts import tenth_energy_reference_roles as roles


SETTING = ('eisxh ra context zrhdomain zrhcurve zrgstart eisxv zrhstartpoint '
           'zrhendpoint zrgposition eisxt zrivelocity zriacceleration zrgprofile '
           'tc eis2a zrgcharge zrgepisode zrgfield ta rb eis2b eis2c eis2d eis2e '
           'eis2f zrgunit eis2g eis2h eis2i eis2j eis2k eis2l eis2m eis2n eis2o').split()
ALL = SETTING + ['zrgwithdrawn', 'zrginitial', 'zrfenergy', 'zrgradiated']
PHYSICAL = set(SETTING) - {'eisxh', 'ra', 'context', 'eisxv', 'eisxt', 'tc', 'ta', 'rb', 'zrgepisode'}
VALUES = {'zrfenergy', 'zrgwithdrawn', 'zrginitial', 'zrgradiated'}
NUMERIC_ROLES = sorted(PHYSICAL | VALUES | {'zrgepisode'})
COUNTS = {}


def var(name): return dict(kind='variable', name=name)
def call(name, *args): return dict(kind='call', symbol=name, arguments=list(args))
def both(*args): return dict(kind='and', arguments=list(args))


@lru_cache(None)
def source():
    return catalogs()['einstein-1905'].document


@lru_cache(None)
def actual_roles():
    return roles.build_roles(source())


def interface(document, role):
    declarations = {d['name']: d for d in document['declarations']}
    result = []
    for name in sorted(_references(role['body'])):
        d = declarations[name]
        parameters = [p['sort'] for p in d['parameters']] if d['kind'] == 'definition' else d['parameters']
        result.append(dict(kind='primitive', name=name, parameters=deepcopy(parameters), result=deepcopy(d['result'])))
    return dict(schema_version='0.16', lexicon_version='0.16', declarations=result+[deepcopy(role)], statements=[])


def expected_role(candidate):
    """Literal reviewed argument positions, independent of source-content traversal."""
    declarations = {d['name']: d for d in source()['declarations']}
    physical = candidate in PHYSICAL
    arguments = SETTING if physical else ALL
    witnesses = ((PHYSICAL | {'zrgepisode'}) if physical else VALUES) - {candidate}
    ordered = [name for name in arguments if name in witnesses]
    values = [var('candidate') if n == candidate else var('context') if n == 'context'
              else var('witness'+n) if n in witnesses else call(n) for n in arguments]
    body = both(call('eou', *values), call('eow', *deepcopy(values))) if physical else call('eox', *values)
    for n in reversed(ordered):
        body = dict(kind='exists', variable='witness'+n, sort=declarations[n]['result'], body=body)
    return dict(kind='definition', name='energyrole'+candidate, parameters=[
        dict(name='candidate', sort=declarations[candidate]['result']),
        dict(name='context', sort='situation')], result='truth', body=body)


def substitute(node, bindings):
    if isinstance(node, list): return [substitute(x, bindings) for x in node]
    if not isinstance(node, dict): return node
    if node.get('kind') == 'variable' and node['name'] in bindings:
        return deepcopy(bindings[node['name']])
    return {k: substitute(x, bindings) for k, x in node.items()}


@pytest.mark.parametrize('candidate', NUMERIC_ROLES)
def test_typed_roles_and_every_argument_and_witness(candidate):
    expected = normalize_document(interface(source(), expected_role(candidate)))
    actual = normalize_document(interface(source(), actual_roles()[candidate]))
    assert actual == expected, ('Complete typed role differs', candidate)
    role = actual['declarations'][-1]
    binders = []; leaf = role['body']
    while leaf['kind'] == 'exists':
        binders.append(leaf['variable']); leaf = leaf['body']
    assert len(binders) == (27 if candidate in PHYSICAL else 4 if candidate == 'zrgepisode' else 3)
    predicates = leaf['arguments'] if leaf['kind'] == 'and' else [leaf]
    cases = 0; checked_slots = set(); checked_witnesses = set()
    # One witness varies over a small guarded domain; all others are instantiated.
    for selected in [None, *binders]:
        env = {role['parameters'][0]['name']: 'candidate', role['parameters'][1]['name']: 'context'}
        env.update({n: 'chosen' if n == selected else 'fixed' for n in binders})
        expected_rows = {p['symbol']: tuple(env[a['name']] if a['kind'] == 'variable' else 'fixed'
                                          for a in p['arguments']) for p in predicates}
        body = substitute(leaf, {n: call('fixed') for n in binders if n != selected})
        if selected is not None:
            body = dict(kind='exists', variable=selected, sort='individual', body=both(
                dict(kind='equal', arguments=[var(selected), call('chosen')]), body))
        diagnostic = deepcopy(role); diagnostic['body'] = body
        diagnostic['parameters'][0]['sort'] = 'individual'
        declarations = deepcopy(actual['declarations'][:-1])
        for d in declarations:
            d['parameters'] = ['situation' if t == 'situation' else 'individual' for t in d['parameters']]
            if not d['parameters']: d['result'] = 'individual'
        constants = {d['name']: (lambda: 'fixed') for d in declarations if not d['parameters']}
        for name, sort in [('fixed','individual'), ('chosen','individual'), ('candidate','individual'), ('context','situation')]:
            declarations.append(dict(kind='primitive', name=name, parameters=[], result=sort))
            constants[name] = lambda name=name: name
        document = dict(schema_version='0.16', lexicon_version='0.16', declarations=declarations+[diagnostic],
                        statements=[dict(kind='ask', body=call(role['name'], call('candidate'), call('context')))])

        def evaluate(rows):
            handlers = constants | {name: (lambda *args, row=row: args == row) for name, row in rows.items()}
            return evaluate_document(document, individuals=('fixed','chosen','candidate','wrong'),
                situations=('context','wrongcontext'), primitives=handlers)[0]['value']

        assert evaluate(expected_rows); cases += 1
        for predicate, row in expected_rows.items():
            slots = range(len(row)) if selected is None else [i for i, value in enumerate(row) if value == 'chosen']
            for slot in slots:
                replacement = 'wrongcontext' if row[slot] == 'context' else 'wrong'
                changed = row[:slot] + (replacement,) + row[slot+1:]
                assert not evaluate(expected_rows | {predicate: changed}), (candidate, selected, predicate, slot)
                cases += 1; checked_slots.add((predicate, slot))
                if selected is not None: checked_witnesses.add(selected)
        if selected is not None: assert selected in checked_witnesses
    assert checked_slots == {(p['symbol'], i) for p in predicates for i in range(len(p['arguments']))}
    assert checked_witnesses == set(binders)
    COUNTS[candidate] = dict(witnesses=len(binders), argument_slots=len(checked_slots), cases=cases,
        typed_body_compared=True, one_witness_at_a_time=True, full_real_domain_proof=False)


def test_reference_graph_has_no_self_reference_or_cycle_and_source_is_unchanged():
    before = deepcopy(source()); result = roles.build_roles(source())
    assert source() == before
    assert set(result) == PHYSICAL | VALUES | {'zrgepisode','eis3k'}
    declarations = {d['name']: d for d in source()['declarations']}
    graph = {}
    for name, role in result.items():
        pending = list(_references(role['body'])); seen = set()
        while pending:
            symbol = pending.pop()
            if symbol in seen: continue
            seen.add(symbol); pending.extend(_references(declarations[symbol].get('body')) - seen)
        assert name not in seen
        graph[name] = seen & set(result)
    assert all(not graph[n] for n in PHYSICAL)
    assert graph['zrgepisode'] <= PHYSICAL
    assert all(graph[n] <= PHYSICAL | {'zrgepisode'} for n in VALUES)
    assert not graph['eis3k']


def test_theory_view_preserves_quotation_without_executing_it():
    role = actual_roles()['eis3k']
    assert role['body'] == call('eiscv', var('energycandidate'), call('eirf'),
        dict(kind='quote', body=call('eigj')), var('energycontext'))
    document = interface(source(), role)
    document['declarations'] += [dict(kind='primitive', name=n, parameters=[], result=t)
        for n,t in [('candidate','individual'),('context','situation')]]
    document['statements'] = [dict(kind='ask', body=call(role['name'],call('candidate'),call('context')))]
    def forbidden(): raise AssertionError('Quoted theory content executed')
    def predicate(candidate, paper, description, context):
        return (candidate == 'view' and paper == 'paper' and context == 'world'
                and json.loads(description.syntax) == call('eigj'))
    handlers = dict(candidate=lambda:'view', context=lambda:'world', eirf=lambda:'paper',
                    eigj=forbidden, eiscv=predicate)
    assert evaluate_document(document, individuals=('view','paper'), situations=('world',), primitives=handlers)[0]['value']
