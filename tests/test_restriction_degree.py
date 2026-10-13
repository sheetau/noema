import json

import pytest

from noema.grammar import parse
from noema.meaning_basis import audit_basis
from scripts.check_restriction_degree import REPORT, build_report
from scripts.compose_restriction_degree import ROOT, PARENT, source_composed


@pytest.fixture(scope='module')
def result():
    return build_report()


def test_missing_permission_is_not_prohibition_or_a_resolved_classification(result):
    rows = result['classification']['truth_table']
    assert len(rows) == 32
    for row in rows:
        if not any(row[key] for key in ('required_positive', 'required_negative', 'allowed_positive', 'allowed_negative')):
            assert row['results'] == [False, False, False]
    assert result['classification']['execution_always_guarded']


def test_both_permissions_are_choices_but_opposed_requirements_are_conflicts(result):
    for row in result['classification']['truth_table']:
        if row['allowed_positive'] and row['allowed_negative']:
            conflict = row['required_positive'] or row['required_negative']
            assert row['results'] == [conflict, False, not conflict]
        if row['required_positive'] and row['required_negative']:
            assert row['results'] == [True, False, False]


def test_unknown_and_conflicting_activities_cannot_be_counted_as_banned(result):
    rows = result['source']['state_and_ratio_cases']
    assert len(rows) == 48
    assert sum(row['result'] for row in rows) == 3
    for row in rows:
        if any(state in ('unclassified', 'conflict') for state in row['states']):
            assert row['result'] is False
    assert result['source']['unknown_norm_refused']


def test_scope_omissions_duplicates_and_empty_populations_are_rejected(result):
    rows = result['source']['contrasts']
    assert rows['reordered']
    for name in ('missing_permitted_activity', 'missing_banned_activity', 'duplicate', 'empty',
            'out_of_scope', 'unlisted_scope_member', 'bad_indicator'):
        assert rows[name] is False


def test_ratio_criterion_and_activity_granularity_are_not_silently_fixed(result):
    rows = result['source']['contrasts']
    assert rows['all_permitted_zero'] and rows['all_banned_one']
    for name in ('negative_ratio', 'ratio_over_one', 'strict_boundary', 'stricter_context'):
        assert rows[name] is False
    assert rows['narrowed_scope'] and rows['banned_class_split']
    assert rows['permitted_class_split'] is False
    assert result['source']['scope_narrowing_requires_independent_source_justification']


def test_normative_identity_and_entrusted_office_are_preserved(result):
    for name in ('source', 'person', 'role', 'description', 'context', 'wrong_office'):
        assert result['source']['contrasts'][name] is False
    assert result['source']['actual_execution_and_author_meta_norms_guarded']


def test_reuse_adds_no_primitives_and_preserves_all_existing_claims():
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    text, basis = source_composed()
    doc = parse(text)
    audit = audit_basis(doc, basis)
    assert (audit['primitive_count'], audit['definition_count']) == (250, 452)
    assert doc['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert doc['statements'] == parent['statements']
    assert len(doc['statements']) == 15
    assert (ROOT / basis['document']).read_text(encoding='utf-8') == text


def test_reproducible_report_keeps_partial_measure_separate_from_source_equivalence(result):
    assert result == json.loads(REPORT.read_text(encoding='utf-8'))
    assert result['new_primitives'] == result['new_source_assertions'] == 0
    assert result['roundtrips'] and result['parent_preserved']
    assert not result['alignment']['semantic_completion']
    assert result['verified_full_units'] == {'kant-1784': 0, 'einstein-1905': 0}
