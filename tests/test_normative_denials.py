import json

import pytest

from noema.grammar import parse
from scripts.check_normative_denials import REPORT, build_report
from scripts.compose_normative_denials import ROOT, PARENT


@pytest.fixture(scope='module')
def result(): return build_report()


def test_permission_absence_prohibition_and_conflict_are_distinct(result):
    assert len(result['generic']['cases']) == 32
    for row in result['generic']['cases']:
        valid, permit, forbid, require, polarity = row['bits']
        assert row['results'] == [valid and not permit, valid and forbid, valid and (not permit or forbid)]


def test_power_absence_is_guarded_by_valid_arguments_and_owner(result):
    for row in result['generic']['power_cases']:
        power = not row['prior'] and row['subsequent'] and row['controlled'] and row['recognized']
        assert row['results'] == [not power, power]
    assert all(row == [False, False] for row in result['generic']['invalid_power_inputs'].values())


def test_undertaking_can_be_forbidden_and_still_have_a_normative_effect(result):
    assert len(result['source']['cases']) == 32
    for row in result['source']['cases']:
        permit, forbid, controlled, recognized, effect = row['bits']
        power = controlled and recognized
        assert row['results'] == [not permit, forbid, not permit or forbid, not power, not (power and effect), power, power and effect]
    forbidden = next(r for r in result['source']['cases'] if r['bits'] == [False, True, True, True, True])
    assert forbidden['results'] == [True, True, True, False, False, True, True]


def test_same_agreement_is_the_source_of_the_proposed_norm_change(result):
    assert result['source']['contrasts']['other_agreement'] == [False, False, False, True, True, False, False]
    assert result['source']['same_agreement_for_norm_effect']


def test_collective_adapter_preserves_single_owner_and_undertaking_content(result):
    assert result['source']['adapter'] == {'oldgroup': [True], 'newgroup': [False], 'empty': [False], 'oldgroup,newgroup': [False]}
    for name in ('extra_binding', 'empty_binding'):
        assert result['source']['contrasts'][name] == [False] * 7
    assert result['source']['contrasts']['wrong_owner'][3:] == [False] * 4


def test_unknown_norms_cannot_be_reported_absent_but_targets_need_not_execute(result):
    assert result['generic']['unknown_relations_refused']
    assert result['source']['unknown_norms_refused']
    assert result['source']['unknown_undertaking_not_executed']
    assert result['source']['same_undertaking_for_norm_and_power']
    assert result['source']['closed_roundtrips']


def test_parent_and_unresolved_source_interpretation_are_preserved(result):
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    child = parse((ROOT / 'examples/v014/kant-normative-denials.noema').read_text(encoding='utf-8'))
    assert child['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert len(child['declarations']) == len(parent['declarations']) + 10
    assert child['statements'] == parent['statements'] and len(child['statements']) == 15
    assert result['new_primitives'] == result['new_author_statements'] == 0
    assert not result['alignment']['semantic_completion']
    assert result['verified_full_units'] == {'kant-1784': 0, 'einstein-1905': 0}
    assert result == json.loads(REPORT.read_text(encoding='utf-8'))
