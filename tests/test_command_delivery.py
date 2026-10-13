import json

import pytest

from noema.grammar import parse
from scripts.check_command_delivery import REPORT, build_report
from scripts.compose_command_delivery import ROOT, PARENT, source_composed


@pytest.fixture(scope='module')
def result():
    return build_report()


def test_directive_retains_force_actor_action_and_content_at_each_scene(result):
    rows = result['finite']
    assert len(rows) == 4
    assert all(row['results'] == [True, True, True] for row in rows)


def test_issuance_receipt_duty_and_execution_are_independent(result):
    rows = result['source']['cases']
    assert len(rows) == 64
    for row in rows:
        occurs, presents, conveys, received, required, done = row['states']
        issued = occurs and presents and conveys
        assert row['results'] == [issued, issued and received, required,
            issued and required, issued and required and not done, done]
    unnoticed = next(row for row in rows if row['states'] == [True, True, True, False, True, False])
    assert unnoticed['results'] == [True, False, True, True, True, False]
    no_duty = next(row for row in rows if row['states'] == [True, True, True, True, False, False])
    assert no_duty['results'] == [True, True, False, False, False, False]


def test_wrong_targets_do_not_transfer_receipt_or_norms(result):
    rows = result['source']['contrasts']
    assert len(rows) == 20
    assert rows['message_other_actor'] == rows['message_alias'] == [False, False, True, False, False, False]
    for name, observed in rows.items():
        if name.startswith('receipt_'):
            assert observed == [True, False, True, True, True, False]
        if name.startswith('norm_') or name == 'no_office':
            assert observed == [True, True, False, False, False, False]


def test_unknown_stages_are_not_filled_in_and_standalone_library_agrees(result):
    assert result['source']['unknown_stages_refused']
    assert result['source']['issuance_and_duty_do_not_require_receipt_or_performance']
    assert result['source']['same_results_in_standalone_core']
    assert result['sizes']['command-delivery-core'] == {'characters': 1345, 'statements': 0}


def test_parent_claims_are_preserved_without_new_primitives(result):
    text, basis = source_composed()
    doc = parse(text)
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    assert doc['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert doc['statements'] == parent['statements']
    assert len(doc['statements']) == 15
    audit = result['documents'][basis['document']]
    assert (audit['primitive_count'], audit['definition_count']) == (252, 511)
    core = result['documents']['examples/v014/command-delivery-core.noema']
    assert (core['primitive_count'], core['definition_count']) == (8, 10)
    assert result['new_primitives'] == result['new_source_assertions'] == 0


def test_saved_report_reproduces_without_certifying_authority_or_source_equivalence(result):
    assert result == json.loads(REPORT.read_text(encoding='utf-8'))
    assert result['roundtrips'] and result['parent_preserved']
    assert result['alignment']['new_source_ranges']
    assert not result['alignment']['semantic_completion']
    assert result['verified_full_units'] == {'kant-1784': 0, 'einstein-1905': 0}
