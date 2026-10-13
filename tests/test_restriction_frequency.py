import json

import pytest

from noema.grammar import parse
from noema.meaning_basis import audit_basis
from scripts.check_restriction_frequency import REPORT, build_report
from scripts.compose_restriction_frequency import ROOT, PARENT, source_composed


@pytest.fixture(scope='module')
def result():
    return build_report()


def test_weighted_frequency_requires_complete_classification_and_exact_ratio(result):
    assert result['finite']['state_weight_ratio_cases'] == 464
    assert result['finite']['unknown_classification_refused']
    rows = result['finite']['contrasts']
    assert rows['unclassified_hit'] == rows['unclassified_miss'] == [False, False]
    assert rows['no_hits'] == [True, False]
    assert rows['all_hits'] == [True, True]


def test_scope_cannot_omit_duplicate_or_add_points(result):
    rows = result['finite']['contrasts']
    assert rows['reordered'] == [True, False]
    for name in ('omitted_middle', 'duplicate', 'empty', 'extra_point'):
        assert rows[name] == [False, False]
    # A different explicit scope may be valid; that does not justify its source reading.
    assert rows['narrowed_scope'] == [True, True]


def test_weights_are_positive_and_uniform_rescaling_or_mass_preserving_splits_agree(result):
    rows = result['finite']['contrasts']
    for name in ('zero_weight', 'negative_weight', 'negative_ratio', 'ratio_over_one', 'bad_indicator', 'split_without_preserving_mass'):
        assert rows[name] == [False, False]
    for name in ('weighted_half', 'uniform_weight_scaling', 'fractional_weight_scaling',
            'split_hit_preserving_mass', 'split_miss_preserving_mass'):
        assert rows[name] == [True, True]


def test_activity_degree_and_temporal_frequency_have_independent_criteria(result):
    rows = result['source']['degree_frequency_cases']
    assert len(rows) == 27
    assert all(row['results'][1] for row in rows)
    assert sum(row['results'][0] for row in rows) == 20
    contrasts = result['source']['contrasts']
    assert contrasts['stricter_degree'] == contrasts['stricter_frequency'] == [False, True]
    assert contrasts['weighted_frequency'] == [True, True]
    assert contrasts['wrong_frequency'] == [False, False]


def test_a_missing_or_wrong_inner_degree_cannot_become_a_nonqualifying_time(result):
    rows = result['source']['contrasts']
    for name in ('unclassified_middle', 'conflicting_middle', 'wrong_middle_degree', 'missing_middle_activity'):
        assert rows[name] == [False, False]
    assert result['source']['unknown_inner_norm_refused']
    assert result['source']['execution_and_author_permissions_guarded']


def test_same_period_is_nonempty_ordered_and_complete_at_the_anchor(result):
    rows = result['source']['contrasts']
    for name in ('missing_middle_point', 'empty_scope', 'empty_history', 'scope_outside', 'gap',
            'cyclic_order', 'wrong_frame', 'zero_middle_weight'):
        assert rows[name] == [False, False]
    assert rows['other_context_scope'] == [True, True]


def test_composition_preserves_prior_claims_without_new_primitives():
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    text, basis = source_composed()
    doc = parse(text)
    audit = audit_basis(doc, basis)
    assert (audit['primitive_count'], audit['definition_count']) == (250, 459)
    assert doc['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert doc['statements'] == parent['statements']
    assert len(doc['statements']) == 15
    assert (ROOT / basis['document']).read_text(encoding='utf-8') == text


def test_saved_report_reproduces_without_certifying_original_frequency_semantics(result):
    assert result == json.loads(REPORT.read_text(encoding='utf-8'))
    assert result['new_primitives'] == result['new_source_assertions'] == 0
    assert result['roundtrips'] and result['parent_preserved']
    assert result['alignment']['semantic_completion'] is False
    assert result['verified_full_units'] == {'kant-1784': 0, 'einstein-1905': 0}
