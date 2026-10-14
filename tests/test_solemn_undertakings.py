import json

import pytest

from noema.grammar import parse
from scripts.check_solemn_undertakings import REPORT, build_report
from scripts.compose_solemn_undertakings import ROOT, PARENT


@pytest.fixture(scope='module')
def result(): return build_report()


def test_conditional_appeal_is_not_an_assertion_of_breach_or_response(result):
    assert len(result['conditionals']) == 4
    for row in result['conditionals']:
        assert row['results'] == [row['target'] or row['response'], False]


def test_all_five_action_components_are_required(result):
    assert len(result['actions']) == 32
    for row in result['actions']: assert row['results'] == [all(row['bits'])]


@pytest.mark.parametrize('section', ['generic', 'source'])
def test_every_party_needs_solemnity_and_appeal_in_the_same_act(result, section):
    assert len(result[section]['cases']) == 16
    for row in result[section]['cases']:
        expected = [all(row['bits'])] * 2
        if section == 'generic': expected.insert(0, row['bits'][0] and row['bits'][2])
        assert row['results'] == expected
    for name in ('authority_alias', 'formula_alias', 'wrong_bindings', 'ceremony_act', 'appeal_person', 'appeal_act', 'appeal_time', 'separate_witness'):
        assert not any(result[section]['contrasts'][name])
    assert result[section]['contrasts']['matching_alternative'] == ([False, True, True] if section == 'generic' else [True, True])


def test_purpose_uses_the_undertaking_witness_and_does_not_require_achievement(result):
    assert len(result['purposes']) == 8
    for row in result['purposes']:
        formed = row['first'] and row['second']
        assert row['results'] == [formed, formed and row['aimed']]
    assert result['source']['contrasts']['goal_alias'] == [True, False]


def test_represented_authority_policy_and_response_are_not_executed(result):
    for section in ('generic', 'source'):
        assert result[section]['underlying_truth_not_executed']
        assert result[section]['unknown_appeal_refused']
        assert result[section]['standalone_agrees']
        assert result[section]['closed_roundtrips']


def test_parent_and_partial_interpretation_status_are_preserved(result):
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    doc = parse((ROOT / 'examples/v014/kant-solemn-undertakings.noema').read_text(encoding='utf-8'))
    assert doc['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert len(doc['declarations']) == len(parent['declarations']) + 7
    assert doc['statements'] == parent['statements'] and len(doc['statements']) == 15
    assert result['new_primitives'] == result['new_author_statements'] == 0
    assert result['alignment']['segments'][0]['text'] == 'eidlich'
    assert not result['alignment']['semantic_completion']
    assert result['verified_full_units'] == {'kant-1784': 0, 'einstein-1905': 0}
    assert result == json.loads(REPORT.read_text(encoding='utf-8'))
