from copy import deepcopy
from functools import lru_cache

import pytest

from noema.extraction import extract_document
from noema.grammar import parse
from noema.integration_audit import dependency_path
from scripts.compose_density_interpretation import ROOT, PARENT, INDEX, SOURCE, BINDINGS, LOCAL, source_composed, core_composed, review_packet
from scripts.check_density_interpretation import structural_checks, attribution_checks, conditional_contrasts, CONNECTED


@lru_cache(maxsize=1)
def documents():
    return parse(source_composed()[0]), parse((ROOT / PARENT).read_text(encoding='utf-8'))


@lru_cache(maxsize=1)
def contrasts():
    return conditional_contrasts()


def test_real_authored_quote_now_reaches_explanations_without_new_definitions():
    doc, parent = documents()
    result = structural_checks(doc, parent)
    assert all(result['dependency_paths'][s] for s in CONNECTED)
    assert len(doc['statements']) == len(parent['statements']) == 175
    assert doc['statements'][:INDEX] == parent['statements'][:INDEX]
    assert doc['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert len(LOCAL) == 11
    assert all(d['kind'] == 'primitive' for d in doc['declarations'][len(parent['declarations']):])
    assert dependency_path(doc, INDEX, 'zqd') is None


def test_standalone_artifact_keeps_actual_revised_statement():
    doc, _ = documents()
    core = parse(core_composed()[0])
    assert core == extract_document(doc, statement_indices=[INDEX]).document
    assert len(core['statements']) == 1
    assert core['statements'][0] == doc['statements'][INDEX]


@pytest.mark.parametrize('change', ['old_quote', 'distribution', 'unit_swap', 'author', 'old_definition', 'earlier_statement'])
def test_incorrect_integration_or_unannounced_historical_edits_fail(change):
    original, parent = documents()
    doc = deepcopy(original)
    args = doc['statements'][INDEX]['body']['arguments']
    quote = args[-1]['body']
    if change == 'old_quote':
        args[-1] = deepcopy(parent['statements'][INDEX]['body']['arguments'][-1])
    elif change == 'distribution':
        quote['arguments'][1] = dict(kind='call', symbol='rd', arguments=[])
    elif change == 'unit_swap':
        quote['arguments'][3], quote['arguments'][4] = quote['arguments'][4], quote['arguments'][3]
    elif change == 'author':
        args[1] = deepcopy(args[0])
    elif change == 'old_definition':
        next(d for d in doc['declarations'] if d['name'] == 'seof')['body']['symbol'] = 'senw'
    else:
        doc['statements'][0]['kind'] = 'ask'
    with pytest.raises(ValueError):
        structural_checks(doc, parent)


def test_authored_attribution_does_not_evaluate_physics_or_substitute_quotes():
    doc, parent = documents()
    result = attribution_checks(doc, parent)
    assert len(result['cases']) == 8
    assert len(result['discourse_contrasts']) == 5
    assert len(result['quoted_argument_contrasts']) == len(SOURCE) == 14
    assert result['physical_content_not_executed']
    assert result['old_quote_not_substituted']


def test_missing_explanation_can_hide_a_failed_source_case():
    row = contrasts()['lost_case']
    assert row['old_assignment'] == [True, True]
    assert row['new_assignment'] == [False, True]
    assert row['other_premises'] and not row['formula_witness']
    assert row['results'] == [False, True]


def test_new_explanation_can_admit_a_previously_absent_case():
    assert contrasts()['added_case']['results'] == [True, False]


def test_sufficient_assignment_agreement_requires_pi_condition_too():
    rows = contrasts()['cases']
    assert len(rows) == 128
    matching = [r for r in rows if r['old_assignment'] == r['new_assignment'] and r['pi']]
    assert len(matching) == 16
    assert all(r['results'][0] == r['results'][1] for r in matching)
    assert any(r['old_assignment'] == r['new_assignment'] and not r['pi'] and r['results'] == [True, False] for r in rows)
    assert not contrasts()['real_histories_or_source_equivalence_proven']


def test_review_does_not_promote_connection_to_source_equivalence():
    packet = review_packet()
    checks = {c['id']: c for c in packet['checks']}
    assert checks['meaning_expansion_in_statement']['status'] == 'connected_in_revised_reading'
    assert checks['interpretation_conservativity']['status'] == 'open'
    assert checks['concept_grounding']['status'] == 'open'
    assert checks['whole_unit_decision']['status'] == 'open'
    assert not packet['semantic_completion']
    assert not packet['equivalence_to_previous_reading_proven']
    assert packet['fixed_bindings'] == BINDINGS
