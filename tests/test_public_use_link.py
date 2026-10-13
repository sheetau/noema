import json

import pytest

from noema.grammar import parse
from noema.meaning_basis import audit_basis
from scripts.check_public_use_link import REPORT, build_report
from scripts.compose_public_use_link import ROOT, source_composed


@pytest.fixture(scope='module')
def result():
    return build_report()


def test_complete_current_and_old_role_documents_are_recoverable(result):
    projection = result['projections']
    assert projection['both_complete_original_documents_recovered']
    assert projection['roles_edition_restored_to'] == '0.11'
    assert projection['shared_declarations'] == 0
    assert projection['original_statement_count'] == 15
    mapping = projection['independent_role_symbols']
    assert len(mapping) == len(set(mapping.values())) == 24
    assert mapping['aa'] != 'aa'


def test_all_original_normative_and_role_models_match_after_relocation(result):
    rows = result['replayed']
    assert rows['original_and_linked_evaluation_pairs'] == 29
    assert len(rows['normative_cases']) == 12
    assert len(rows['role_cases']) == 17
    assert rows['legacy_modules_restored_after_replay']
    assert len(rows['current_access']['cases']) == 25
    assert rows['current_access']['unassessed_permission_refused']


def test_the_two_reader_scopes_must_match_and_be_nonempty(result):
    assert result['scope_equality_cases'] == 16
    for name in ('missing_reader', 'extra_reader', 'empty_scopes'):
        assert result['bridges']['cases'][name] == [False] * 5


def test_reader_and_writer_permissions_are_independent_even_for_the_same_authority(result):
    rows = result['bridges']['cases']
    assert rows['reader_permission_only'] == [True, True, True, False, False]
    assert rows['writer_permission_only'] == [True, False, False, True, False]
    assert rows['writer_conflict'] == rows['wrong_writer_role'] == [True, True, True, False, False]


def test_classification_permission_access_and_actual_performance_are_separate(result):
    rows = result['bridges']['cases']
    assert rows['baseline'] == [True, True, True, True, False]
    assert rows['actual_performance'] == [True] * 5
    assert rows['no_reader_means'] == [True, True, False, True, False]


def test_another_public_audience_or_another_publication_cannot_supply_the_bridge(result):
    rows = result['bridges']['cases']
    assert len(rows) == 19
    for name in ('other_public_audience', 'not_public_audience', 'not_reason_use', 'not_scholarly_role',
            'wrong_activity_role', 'wrong_activity_channel', 'wrong_activity_subject',
            'wrong_activity_description', 'wrong_activity_context'):
        assert rows[name] == [False] * 5
    assert result['bridges']['message_truth_and_understanding_guarded']


def test_integration_preserves_claims_without_declaring_publicity_complete():
    text, basis = source_composed()
    doc = parse(text)
    audit = audit_basis(doc, basis)
    assert (audit['primitive_count'], audit['definition_count']) == (244, 414)
    assert len(doc['statements']) == 15
    assert (ROOT / basis['document']).read_text(encoding='utf-8') == text
    assert basis['role_linkage']['shared_declarations'] == []


def test_saved_report_is_reproduced_without_adding_source_coverage(result):
    assert result == json.loads(REPORT.read_text(encoding='utf-8'))
    assert len(result['alignment']['segments']) == 4
    assert not result['alignment']['new_source_ranges']
    assert not result['alignment']['semantic_completion']
    assert result['verified_full_units'] == {'kant-1784': 0, 'einstein-1905': 0}
