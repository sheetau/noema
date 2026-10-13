from noema.grammar import parse
from noema.meaning_basis import audit_basis
from scripts.check_sustained_judgment import (
    judgment_checks, general_laws, episode_laws, source_checks, attribution_checks, alignment,
)
from scripts.compose_sustained_judgment import ROOT, PARENT, generic_composed, source_composed


def test_independent_judgment_binds_the_used_faculty_and_supported_reason():
    result = judgment_checks()
    assert result['truth_cases'] == 128
    assert result['accepted_truth_cases'] == 1
    rows = result['binding_cases']
    assert [name for name, row in rows.items() if row == [True]] == ['self_guidance', 'other_guided_judgment']


def test_owned_use_and_supported_reason_are_necessary_but_individually_insufficient():
    rows = general_laws()
    assert sum(row['status'] == 'valid' for row in rows.values()) == 4
    assert rows['own_use_alone_suffices']['countermodel_found']
    assert rows['supported_reason_alone_suffices']['countermodel_found']


def test_good_endpoint_does_not_erase_bad_judgments_earlier_in_the_episode():
    rows = episode_laws()
    assert sum(row['status'] == 'valid' for row in rows.values()) == 3
    assert rows['good_endpoint_alone_is_enough']['countermodel_found']


def test_native_episode_allows_preparation_and_revision_but_checks_its_whole_scope():
    result = source_checks()
    rows = result['cases']
    assert len(rows) == 23
    assert rows['baseline'] == rows['reasons_change'] == rows['foreign_judgment_guided'] == [True, True]
    assert rows['middle_unsupported'] == rows['middle_guided'] == rows['omitted_middle'] == [False, False]
    assert rows['future_completion'] == [False, False]
    assert rows['no_earlier_judgment'] == [False, False]
    assert result['gait_and_achievement_primitives_guarded_against_execution']


def test_attributing_the_metaphor_never_executes_either_description():
    result = attribution_checks()
    assert len(result['cases']) == 7
    assert [name for name, row in result['cases'].items() if row == [True]] == ['baseline']
    assert result['all_content_primitives_guarded_against_execution']


def test_new_reading_does_not_claim_semantic_equivalence_or_new_source_extent():
    row = alignment()
    assert row['source'] == 'einen sicheren Gang zu thun'
    assert not row['full_semantic_equivalence']
    assert 'temporal connection to self-achievement' in row['remaining']


def test_existing_claims_are_preserved_and_only_figurative_attribution_is_added():
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    for builder, expected in ((generic_composed, (0, 6)), (source_composed, (223, 348))):
        text, basis = builder()
        doc = parse(text)
        audit = audit_basis(doc, basis)
        assert (audit['primitive_count'], audit['definition_count']) == expected
        assert (ROOT / basis['document']).read_text(encoding='utf-8') == text
    assert doc['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert doc['statements'][:-1] == parent['statements']
    assert doc['statements'][-1]['body']['symbol'] == 'h5g'
    assert len(doc['statements']) == 14
