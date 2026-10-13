import json

import pytest

from noema.grammar import parse
from scripts.check_role_hierarchy import REPORT, build_report
from scripts.compose_role_hierarchy import ROOT, PARENT, source_composed


@pytest.fixture(scope='module')
def result():
    return build_report()


def test_all_three_role_relations_and_scoped_contrasts(result):
    rows = result['orders']
    assert rows['relations'] == 512
    assert rows['strict_partial_orders'] == 19
    assert rows['contrasts']['empty_scope'] == [True, False]
    assert rows['contrasts']['outside_cycle'] == [True, True]
    assert rows['contrasts']['missing_transitive_edge'] == [False, False]
    assert rows['contrasts']['transitive_edge_present'] == [True, True]
    assert rows['contrasts']['incomparable'] == [True, False]
    assert rows['contrasts']['cycle'] == [False, False]


def test_general_order_laws_and_false_totality_or_immediacy(result):
    laws = result['order_laws']
    assert [row['status'] for row in laws.values()] == ['valid'] * 4 + ['invalid'] * 2
    assert laws['all_roles_comparable']['countermodel_found']
    assert laws['only_immediate_superiors']['countermodel_found']


def test_people_with_several_roles_do_not_acquire_a_global_personal_rank(result):
    assert result['holders']['two_roles_for_same_holder'] == [True, True, False, False]
    assert result['holders']['personal_transitivity_not_inferred']
    assert result['holders']['self_superiority_excluded_even_with_ordered_held_roles']


def test_rank_issuance_and_duty_are_independent(result):
    rows = result['source']['cases']
    assert len(rows) == 8
    assert next(row['results'] for row in rows if row['states'] == [True, True, False]) == [True, True, False, True, False]
    assert next(row['results'] for row in rows if row['states'] == [False, True, True]) == [False, True, True, False, False]
    assert next(row['results'] for row in rows if row['states'] == [True, False, True]) == [True, False, True, False, False]


def test_person_role_organization_context_and_command_targets_are_bound(result):
    rows = result['source']['contrasts']
    assert len(rows) == 17
    assert rows['message_action'] == [True, False, True, False, False]
    assert rows['norm_issuer'] == [True, True, False, True,False]
    assert rows['same_person'] == [False] * 5
    for name in ('upper_holder', 'lower_holder', 'member_organization', 'member_context',
                 'holder_organization', 'holder_context', 'order_organization', 'order_context', 'same_role'):
        assert rows[name] == [False, True, True, False, False]


def test_knowledge_gaps_are_not_filled_and_core_agrees(result):
    assert result['source']['unknowns_refused']
    assert result['source']['issuance_without_known_duty']
    assert result['source']['standalone_agrees']


def test_parent_and_claims_preserved_without_new_source_primitives(result):
    text, basis = source_composed()
    doc = parse(text)
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    assert doc['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert doc['statements'] == parent['statements']
    audit = result['documents'][basis['document']]
    assert (audit['primitive_count'], audit['definition_count']) == (252, 517)
    assert result['new_primitives'] == result['new_source_assertions'] == 0
    assert result['sizes']['kant-role-hierarchy'] == {'characters': 83311, 'statements': 15}
    assert result['sizes']['role-hierarchy-core'] == {'characters': 2082, 'statements': 0}


def test_report_reproduces_without_promoting_source_coverage(result):
    assert result == json.loads(REPORT.read_text(encoding='utf-8'))
    assert result['roundtrips'] and result['parent_preserved']
    assert not result['alignment']['new_source_ranges']
    assert not result['alignment']['semantic_completion']
    assert result['verified_full_units'] == {'kant-1784': 0, 'einstein-1905': 0}
