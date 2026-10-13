import json

import pytest

from noema.grammar import parse
from scripts.check_action_conformity import REPORT, build_report
from scripts.compose_action_conformity import ROOT, PARENT, source_composed


@pytest.fixture(scope='module')
def result():
    return build_report()


def test_opposed_requirements_cannot_be_satisfied(result):
    cases = result['local']['cases']
    assert len(cases) == 8
    assert all(not row['conforms'] for row in cases if row['states'][:2] == [True, True])
    assert all(row['conforms'] for row in cases if row['states'][:2] == [False, False])


def test_unpaid_action_permission_and_conformity_are_independent(result):
    rows = result['source']['cases']
    assert len(rows) == 64
    for row in rows:
        ban, required, quality, paid, spoken, allowed = row['states']
        conforms = (not ban or not spoken) and (not required or quality)
        assert row['results'] == [not paid, allowed, conforms, conforms,
            spoken and conforms, not spoken or conforms, spoken]
    assert result['source']['standalone_agrees']


def test_missing_scope_cannot_certify_all_requirements(result):
    rows = result['source']['contrasts']
    for name in ('missing_banning_source', 'missing_positive_property',
                 'equal_value_alias_is_not_the_required_description', 'empty_scope_with_unlisted_requirement'):
        assert rows[name][2:6] == [True, False, False, False]
    assert rows['duplicate_descriptions'][2:6] == [True, True, True, True]
    assert rows['no_requirement_for_this_action'] == [True, False, True, True, True, True, True]


def test_conditional_conformity_does_not_assert_its_antecedent(result):
    assert result['source']['contrasts']['inactive_antecedent_with_nonconformity'] == [
        True, False, False, False, False, True, False]
    assert result['source']['unknown_action_property_refused']


def test_coverage_body_is_exercised_separately_from_source_fixture_oracle(result):
    coverage = result['coverage']
    assert coverage['norm_and_scope_cases'] == 1296
    assert 0 < coverage['accepted_cases'] < 1296
    assert coverage['body_evaluated_without_coverage_oracle']
    assert coverage['description_contents_not_executed']
    assert not coverage['full_description_domain_verified']
    assert result['source']['scope_coverage_abstracted_to_the_explicit_normative_table']


def test_unbounded_description_domain_is_not_silently_sampled(result):
    assert len(result['limits']['unbounded_quantification_refusals']) == 2
    assert all('Cannot finitely quantify the description domain' in message
        for message in result['limits']['unbounded_quantification_refusals'])
    assert result['limits']['coverage_can_be_quoted_without_execution']
    assert set(result['limits']['quotations_with_disquotation_refused']) == {'rfe', 'rff', 'rfg', 'rfi'}


def test_parent_preserved_without_new_primitives_or_author_claims(result):
    text, basis = source_composed()
    doc = parse(text)
    parent = parse((ROOT/PARENT).read_text(encoding='utf-8'))
    assert doc['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert len(doc['declarations']) - len(parent['declarations']) == 10
    assert doc['statements'] == parent['statements']
    assert len(doc['statements']) == 15
    assert result['new_primitives'] == result['new_author_statements'] == 0
    assert result['documents'][basis['document']]['primitive_count'] == 252


def test_source_mapping_remains_a_partial_operational_interpretation(result):
    assert result['alignment']['segments'][0]['status'] == 'partial'
    assert result['alignment']['source_claim_not_reduced_to_positive_permission']
    assert not result['alignment']['semantic_completion']
    assert result['verified_full_units'] == {'kant-1784': 0, 'einstein-1905': 0}


def test_reproducible_report_and_alphabet_roundtrip(result):
    assert result == json.loads(REPORT.read_text(encoding='utf-8'))
    assert result['parent_preserved'] and result['roundtrips']
