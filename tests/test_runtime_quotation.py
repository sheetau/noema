from pathlib import Path

import pytest

from noema.ranked import parse
from noema.ranked_semantics import evaluate_document as previous_evaluate
from noema.guarded_ranked_semantics import evaluate_document, QuestionValue, SequenceValue
from noema.semantics import SemanticError
from scripts.check_runtime_quotation import CHAIN, TRUE, ROUTES, route_document


def values(doc, primitives, **options):
    return [r['value'] for r in evaluate_document(doc, individuals=('alice', 'bob'),
        situations=('now',), primitives=primitives, **options)]


@pytest.mark.parametrize('route', ROUTES)
@pytest.mark.parametrize('ceiling', range(3))
@pytest.mark.parametrize('target', (None, 0, 1, 2))
def test_latent_evaluation_routes_obey_ceiling_and_keep_allowed_cases(route, ceiling, target):
    doc = route_document(route, ceiling, target)
    calls = []
    model = {'touch': lambda: calls.append(True) is None}
    if route == 'callback':
        model['bridge'] = lambda fn: fn()
    if target is None or target < ceiling:
        assert values(doc, model) == [True]
        assert calls == ([] if target is None else [True])
    else:
        with pytest.raises(SemanticError, match='Runtime quotation ceiling'):
            values(doc, model)
        assert calls == []


def test_previous_acceptance_is_reproduced_and_successor_rejects_it():
    doc = route_document('apply', 0, 1)
    model = {'touch': lambda: True}
    assert previous_evaluate(doc, individuals=('alice',), situations=('now',), primitives=model)[0]['value'] is True
    with pytest.raises(SemanticError, match='Runtime quotation ceiling'):
        values(doc, model)


@pytest.mark.parametrize('definitions,expressions', [(False, False), (True, False), (False, True), (True, True)])
def test_warm_caches_do_not_erase_the_evaluation_context(definitions, expressions):
    text = CHAIN + 'd probe[] c[s[k aa[]]].'
    text += 'd template[] i[h[h[] c] c][r[i[fn h[] c][c[v fn][]]]].'
    text += 'q[k probe[]].q[c[s[k template[]]][p probe]].'
    calls = []
    with pytest.raises(SemanticError, match='Runtime quotation ceiling'):
        values(parse(text), {'touch': lambda: calls.append(True) is None},
            memoize_definitions=definitions, memoize_expressions=expressions)
    # The unrestricted first statement ran; the restricted second one did not.
    assert calls == [True]


@pytest.mark.parametrize('container', ('function', 'question', 'sequence', 'nested_sequence'))
def test_preexisting_values_returned_by_primitives_retain_ceiling_after_escape(container):
    function_sort = '{"kind":"function","parameters":[],"result":"truth"}'
    sort, body, use = {
        'function': ('h[] c', 'k supply[]', 'c[s[k template[]]][]'),
        'question': ('g[]', 'k supply[]', 'h[s[k template[]]][]'),
        'sequence': ('j[h[] c]', 'k supply[]', 'q[s[k template[]]][' + TRUE + '][i[state c item h[] c][c[v item][]]]'),
        'nested_sequence': ('j[j[h[] c]]', 'k supply[]', 'q[s[k template[]]][' + TRUE + '][i[state c inner j[h[] c]][q[v inner][v state][i[prior c item h[] c][c[v item][]]]]]'),
    }[container]
    text = CHAIN + 'r register[h[] c] c.r supply[] ' + sort + '.'
    text += 'd run[] h[] c[i[][s[k ab[]]]].d template[] i[' + sort + '][r[' + body + ']].'
    text += 'q[k register[k run[]]].q[' + use + '].'
    stored = []; calls = []
    def supply():
        fn = stored[0]
        if container == 'function':
            return fn
        if container == 'question':
            return QuestionValue(fn)
        sequence = SequenceValue((fn,), function_sort)
        if container == 'sequence':
            return sequence
        return SequenceValue((sequence,), '{"element":' + function_sort + ',"kind":"sequence"}')
    model = {'touch': lambda: calls.append(True) is None,
             'register': lambda fn: stored.append(fn) is None, 'supply': supply}
    with pytest.raises(SemanticError, match='Runtime quotation ceiling'):
        values(parse(text), model)
    assert calls == []


def test_caught_failure_restores_context_and_does_not_poison_unrestricted_function():
    text = CHAIN + 'r check[h[] c h[] c] c.d run[] h[] c[i[][s[k ab[]]]].'
    text += 'd identity[] i[h[h[] c] h[] c][r[i[fn h[] c][v fn]]].'
    text += 'q[k check[c[s[k identity[]]][k run[]] k run[]]].'
    calls = []
    def check(limited, original):
        with pytest.raises(SemanticError, match='Runtime quotation ceiling'):
            limited()
        assert calls == []
        return original()
    assert values(parse(text), {'touch': lambda: calls.append(True) is None, 'check': check}) == [True]
    assert calls == [True]


@pytest.mark.parametrize('route', ('function_value', 'callback_invocation', 'nested_interpretation'))
def test_another_interpretation_cannot_reset_the_current_ceiling(route):
    stored = []; calls = []
    source = parse(CHAIN + 'r save[h[] c] c.q[k save[i[][s[k ab[]]]]].')
    source_model = {'touch': lambda: calls.append(True) is None, 'save': lambda fn: stored.append(fn) is None}
    assert values(source, source_model) == [True]
    if route == 'function_value':
        target = parse('o:r supply[] h[] c.d template[] i[h[] c][r[k supply[]]].q[c[s[k template[]]][]].')
        model = {'supply': lambda: stored[0]}
    else:
        target = parse('o:r check[] c.d template[] i[c][r[k check[]]].q[s[k template[]]].')
        nested = parse(CHAIN + 'q[s[k ab[]]].')
        model = {'check': stored[0] if route == 'callback_invocation' else
                 lambda: values(nested, {'touch': lambda: calls.append(True) is None})[0]}
    with pytest.raises(SemanticError, match='Runtime quotation ceiling'):
        values(target, model)
    assert calls == []
    # Both the foreign closure and a fresh evaluation still work outside it.
    assert stored[0]() is True
    assert calls == [True]


def test_independent_threads_do_not_share_an_active_ceiling():
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event
    entered, release = Event(), Event()
    low = parse('o:r check[] c.d quoted[] i[c][r[k check[]]].q[s[k quoted[]]].')
    high = parse(CHAIN + 'q[s[k ac[]]].')
    def hold():
        entered.set()
        assert release.wait(5), 'Second interpretation did not finish'
        return True
    with ThreadPoolExecutor(max_workers=1) as pool:
        pending = pool.submit(values, low, {'check': hold})
        try:
            assert entered.wait(5), 'First interpretation did not start'
            assert values(high, {'touch': lambda: True}) == [True]
        finally:
            release.set()
        assert pending.result(timeout=5) == [True]


@pytest.mark.parametrize('alice,bob', [(False, False), (False, True), (True, False), (True, True)])
def test_person_specific_descriptions_still_work_and_attribution_does_not_execute(alice, bob):
    doc = parse(Path('examples/v015/person-dependent-reports.noema').read_text(encoding='utf-8'))
    stored = {}; calls = []
    def register(first, second):
        stored.update(alice=first, bob=second)
        return True
    def attributed(description):
        assert calls == []
        return description.rank == 1
    def selected(person):
        calls.append(person)
        return stored[person]
    model = dict(register=register, attributed=attributed, selected=selected, anchor=lambda: 'now',
        satisfied=lambda person, context: alice if person == 'alice' else not bob,
        frustrated=lambda person, context: bob if person == 'bob' else not alice)
    assert values(doc, model) == [True, True, alice and bob]


def test_closed_kant_quote_is_not_executed():
    doc = parse(Path('examples/v015/kant-nonrestriction-description.noema').read_text(encoding='utf-8'))
    def forbidden(*args):
        raise AssertionError('Quoted predicate executed')
    model = {d['name']: forbidden for d in doc['declarations'] if d['kind'] == 'primitive'}
    assert values(doc, model) == [True]
