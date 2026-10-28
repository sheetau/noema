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
from scripts import tenth_observables_reference_roles as roles


POTENTIAL = set('eis4'+c for c in 'ghijklmnop')
MAGNETIC = set('eis5'+c for c in 'abcdefghijklmnopqrs')
POTENTIAL_ARGS = ('eisxh ra context zrhdomain zrhcurve zrgstart eisxv zrhstartpoint '
    'zrhendpoint zrgposition eisxt zrivelocity zriacceleration zrgprofile tc eis2a '
    'zrgcharge zrgepisode zrgfield ta rb eis2b eis2c eis2d eis2e eis2f zrgunit '
    'eis2g eis2h eis2i eis2j eis2k eis2l eis2m eis2n eis2o zrgwithdrawn zrginitial '
    'zrfenergy zrgradiated eis4g eis4h eis4i eis4j eis4k eis4l eis4m eis4n eis4o eis4p').split()
MAGNETIC_ARGS = ('eisxh ra ta rb eis2b eis2c eis2d eis2e eis2f eis2g eis2h eis2i eis2j '
    'eis4m tc eisxt eis2a zrgcharge eis5a eis5b eis5c eis5d eis5e eis5f eis5g '
    'eis5h eis5i eis5j eis5k eis5l eis5m eis5n eis5o eis5p context eis5q eis5r eis5s ta eis2g').split()
NUMERIC_ROLES = sorted(POTENTIAL | MAGNETIC)
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
    potential = candidate in POTENTIAL
    arguments = POTENTIAL_ARGS if potential else MAGNETIC_ARGS
    witnesses = (POTENTIAL if potential else MAGNETIC) - {candidate}
    ordered = [name for name in arguments if name in witnesses]
    values = [var('candidate') if n == candidate else var('context') if n == 'context'
              else var('witness'+n) if n in witnesses else call(n) for n in arguments]
    body = call('er7' if potential else 'esp', *values)
    for n in reversed(ordered):
        body = dict(kind='exists', variable='witness'+n, sort=declarations[n]['result'], body=body)
    return dict(kind='definition', name='observedrole'+candidate, parameters=[
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
    assert len(binders) == (9 if candidate in POTENTIAL else 18)
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
    assert set(result) == POTENTIAL | MAGNETIC | {'eis35'}
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
    assert not graph['eis35']
    assert all(not graph[n] for n in POTENTIAL)
    assert all(graph[n] == {'eis4m'} for n in MAGNETIC)


def test_charge_record_retains_complete_background_and_every_argument():
    context=var('context');scale=var('scale');candidate=var('candidate')
    terms=[
        call('ek3n',*(call(n) for n in 'ta rb eis2b eis2c eis2g eis2h eis2i eis2j'.split()),context),
        call('ek3o',*(call(n) for n in 'eisxh ra eisxv eis2b eis2a'.split()),context),
        call('ek3u',call('eisxh'),call('ra'),call('eisxv'),candidate,call('eis2d'),scale,call('zrgcharge'),context),
        call('ba',call('tc')),
        call('bg',call('bb',dict(kind='number',numerator=0,denominator=1)),call('tc'))]
    body=terms[-1]
    for term in reversed(terms[:-1]):body=both(term,body)
    expected=dict(kind='definition',name='observedroleeis35',parameters=[
        dict(name='candidate',sort='individual'),dict(name='context',sort='situation')],
        result='truth',body=dict(kind='exists',variable='scale',sort='number',body=body))
    actual=normalize_document(interface(source(),actual_roles()['eis35']))
    assert actual==normalize_document(interface(source(),expected))

    # After the complete typed comparison, erase opaque sorts solely to probe
    # bindings. The real numerical and physical predicates remain in the source.
    def abstract(value):
        if value=='number':return 'individual'
        if isinstance(value,list):return [abstract(x) for x in value]
        if not isinstance(value,dict):return value
        if value.get('kind')=='number':
            assert value['numerator']==0 and value['denominator']==1
            return call('zero')
        if value.get('kind')=='function':return 'individual'
        return {k:abstract(v) for k,v in value.items()}
    document=abstract(actual)
    role=document['declarations'][-1];witness=role['body']['variable']
    role['body']['body']=both(dict(kind='equal',arguments=[var(witness),call('chosen')]),role['body']['body'])
    constants={d['name']:(lambda:'fixed') for d in document['declarations'] if not d['parameters']}
    for name,sort in [('candidate','individual'),('context','situation'),('chosen','individual'),('zero','individual')]:
        document['declarations'].insert(-1,dict(kind='primitive',name=name,parameters=[],result=sort))
        constants[name]=lambda name=name:name
    document['statements']=[dict(kind='ask',body=call(role['name'],call('candidate'),call('context')))]
    rows={'ek3n':('fixed',)*8+('context',), 'ek3o':('fixed',)*5+('context',),
          'ek3u':('fixed','fixed','fixed','candidate','fixed','chosen','fixed','context'),
          'ba':('fixed',), 'bg':('zero','fixed')}
    def evaluate(selected):
        handlers=constants|{n:(lambda *args,row=row:args==row) for n,row in selected.items()}
        handlers['bb']=lambda x:'zero' if x=='zero' else 'wrong'
        return evaluate_document(document,individuals=('fixed','chosen','candidate','zero','wrong'),
            situations=('context','wrongcontext'),primitives=handlers)[0]['value']
    assert evaluate(rows)
    checked=set()
    for name,row in rows.items():
        for slot,value in enumerate(row):
            wrong='wrongcontext' if value=='context' else 'wrong'
            assert not evaluate(rows|{name:row[:slot]+(wrong,)+row[slot+1:]}),(name,slot)
            checked.add((name,slot))
    assert len(checked)==26
    COUNTS['eis35']=dict(witnesses=1,argument_slots=26,cases=27,
        typed_body_compared=True,one_witness_at_a_time=True,full_real_domain_proof=False)
