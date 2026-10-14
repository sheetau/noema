import json

import pytest

from noema.grammar import parse
from scripts.check_office_associations import REPORT, build_report
from scripts.compose_office_associations import ROOT, PARENT


@pytest.fixture(scope='module')
def result(): return build_report()


def test_membership_and_commissioned_task_qualification_are_distinct(result):
    assert len(result['generic']['cases']) == 16
    for row in result['generic']['cases']:
        assert row['results'] == [row['bits'][0], all(row['bits']), all(row['bits'])]


def test_role_and_principal_records_cannot_be_combined_across_tasks_or_contexts(result):
    for name in ('split_role', 'split_principal', 'split_time', 'task_alias'):
        assert result['generic']['contrasts'][name] == [True, False, False]
    assert result['generic']['contrasts']['alternative_role'] == [True, False, True]


def test_populated_association_excludes_empty_singleton_and_self_membership(result):
    for name in ('empty', 'one_member', 'other_group', 'self_member'):
        assert result['generic']['contrasts'][name] == [False, True, False]


def test_members_may_serve_different_institutions(result):
    assert result['source']['cases']['baseline'] == [True, True, True]
    assert result['source']['cases']['same_principal'] == [True, True, True]
    assert result['source']['distinct_principals_allowed']


def test_contract_cannot_drop_a_qualified_but_uncommitted_member(result):
    assert result['generic']['contrasts']['extra_qualified'] == [True, True, True]
    assert result['source']['cases']['extra_qualified'] == [True, True, False]
    assert result['source']['cases']['past_members'] == [True, True, True]
    assert result['source']['cases']['outside_proponent'] == [True, False, False]
    assert result['source']['parties_share_membership'] and result['source']['membership_fixed_at_anchor']


def test_other_professional_domains_reuse_the_schema_without_a_noun_id(result):
    assert result['cross_domain']['cases'] == {'so': [True, False], 'sq': [False, True]}
    assert result['cross_domain']['new_noun_primitives'] == 0
    assert result['cross_domain']['whole_clergy_or_medical_profession_not_claimed']


def test_task_performance_is_not_inferred_and_unknown_membership_is_not_empty(result):
    assert result['generic']['task_not_executed'] and result['generic']['unknown_relations_refused']
    assert result['source']['actual_tasks_not_required']
    assert result['source']['closed_roundtrips']
    assert result['generic']['standalone_agrees'] and result['source']['standalone_agrees']


def test_parent_and_interpretive_status_are_preserved(result):
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    doc = parse((ROOT / 'examples/v014/kant-office-associations.noema').read_text(encoding='utf-8'))
    assert doc['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert len(doc['declarations']) == len(parent['declarations']) + 7
    assert doc['statements'] == parent['statements'] and len(doc['statements']) == 15
    assert result['new_primitives'] == result['new_author_statements'] == 0
    assert result['alignment']['segments'][0]['text'] == 'Gesellschaft von Geistlichen'
    assert not result['alignment']['semantic_completion']
    assert result['verified_full_units'] == {'kant-1784': 0, 'einstein-1905': 0}
    assert result == json.loads(REPORT.read_text(encoding='utf-8'))
