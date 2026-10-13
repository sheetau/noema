from noema.grammar import parse
from noema.meaning_basis import audit_basis
from scripts.check_conditional_release import (
    minimum_checks, minimum_laws, release_checks, source_checks, attribution_checks, alignment,
)
from scripts.compose_conditional_release import ROOT, PARENT, generic_composed, source_composed


def test_contextual_minima_allow_ties_but_reject_empty_or_incoherent_comparisons():
    result = minimum_checks()
    assert result['relations'] == 512
    assert result['total_preorders'] == 13
    assert result['models_with_tied_minima'] > 0
    assert result['empty_scope'] == [False] * 4


def test_minimum_is_unique_only_up_to_rank_not_individual_identity():
    rows = minimum_laws()
    assert sum(row['status'] == 'valid' for row in rows.values()) == 3
    assert rows['minimum_is_a_unique_individual']['countermodel_found']


def test_release_needs_the_same_person_process_object_and_actual_state_change():
    report = release_checks()
    assert len(report['cases']) == 64
    assert sum(row['result'][0] for row in report['cases']) == 1
    assert len(report['bindings']) == 17
    assert not any(row[0] for row in report['bindings'].values())


def test_hypothetical_release_keeps_one_anchored_minimum_referent_among_possible_ties():
    rows = source_checks()
    assert len(rows) == 15
    assert rows['baseline'] == [True, True, True]
    assert rows['selected_tie_has_no_jump'] == [True, False, False]
    assert rows['unselected_tie_has_no_jump'] == [True, True, True]
    assert rows['wider_ditch_only'] == [True, False, False]
    assert rows['still_bound'] == [False, True, False]
    assert rows['no_hypothetical_cases'] == [True, True, False]
    assert [key for key, value in rows.items() if value[-1]] == ['baseline', 'unselected_tie_has_no_jump']


def test_attribution_does_not_execute_or_assert_the_hypothetical_events():
    report = attribution_checks()
    assert report['hypothetical_content_unexecuted']
    assert [key for key, value in report['cases'].items() if value[0]] == ['baseline']


def test_source_alignment_excludes_the_unwritten_because_clause():
    row = alignment()
    assert row['source'].startswith('Wer sie auch abwürfe')
    assert row['source'].endswith('Sprung thun')
    assert 'weil' not in row['source']
    assert not row['full_semantic_equivalence']
    assert 'because of unfamiliar free movement' in row['remaining']


def test_source_basis_and_prior_content_are_preserved():
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    for builder, counts in ((generic_composed, (0, 9)), (source_composed, (205, 299))):
        text, basis = builder()
        doc = parse(text)
        audit = audit_basis(doc, basis)
        assert (audit['primitive_count'], audit['definition_count']) == counts
        assert (ROOT / basis['document']).read_text(encoding='utf-8') == text
    assert doc['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert doc['statements'][:-1] == parent['statements']
    assert doc['statements'][-1]['body']['symbol'] == 'h3b'
