from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.render import render
from noema.script import decode, encode
from scripts.check_state_convenience import alignment, attribution_checks, source_checks, state_checks
from scripts.compose_state_convenience import ROOT, generic_composed, source_composed


def test_convenience_requires_initial_state_and_state_preserving_success():
    rows = state_checks()['cases']
    assert len(rows) == 64
    assert any(row['easy_goal'] and not row['state_convenience'] for row in rows)
    assert all(not row['state_convenience'] for row in rows if not row['initial_state'] or not row['result_state'])
    assert sum(row['state_convenience'] for row in rows) == 1


def test_state_goal_and_low_burden_cannot_be_borrowed_from_different_methods():
    result = state_checks()['contrasts']
    assert result == {'split_state_and_goal': [False, True], 'split_burden_and_success': [False, False],
        'combined': [True, True], 'outside_outcomes': [False, False]}


def test_source_convenience_evaluates_real_state_definitions_without_preferences():
    result = source_checks()
    rows = result['cases']
    assert len(rows) == 13
    assert rows['baseline'] == {'state_at_case': True, 'state_at_result': True,
        'person_convenience': True, 'scoped_general_claim': True}
    assert rows['state_changes']['state_at_case'] and not rows['state_changes']['state_at_result']
    assert not rows['state_changes']['person_convenience']
    assert rows['empty_people']['person_convenience'] and not rows['empty_people']['scoped_general_claim']
    assert not rows['wrong_standard_context']['person_convenience']
    assert result['ordinary_baseline_agrees'] and not result['definitions_replaced_by_primitives']
    assert not result['liking_motive_or_choice_evaluated']


def test_author_attribution_keeps_convenience_between_explanation_and_examples():
    rows = attribution_checks()
    assert len(rows) == 7
    assert [name for name, row in rows.items() if row['statements'][-1]] == ['baseline']
    assert all(row['statements'][:5] == [True] * 5 for row in rows.values())
    assert all(not row['underlying_contents_evaluated'] for row in rows.values())


def test_four_sentence_alignment_is_partial_and_leaves_the_remaining_paragraph():
    source = alignment()
    assert source['all_nonblank_prefix_characters_assigned']
    assert len(source['segments']) == 4
    assert [s['definition'] for s in source['segments']] == ['mx', 'un', 'sy', 't3']
    assert all(s['status'] == 'partial_explicit_reading' for s in source['segments'])
    assert source['remaining_source_characters'] > 0 and not source['full_semantic_equivalence']


def test_state_convenience_basis_and_written_forms():
    for compose, counts in ((generic_composed, (0, 10)), (source_composed, (97, 129))):
        text, basis = compose()
        doc = parse(text)
        audit = audit_basis(doc, basis)
        assert (audit['primitive_count'], audit['definition_count']) == counts
        assert (ROOT / basis['document']).read_text(encoding='utf-8') == text
        for notation in ('full', 'compact'):
            canonical = format_graph(doc, notation)
            assert parse(canonical) == parse(decode(encode(canonical, 'v2'))) == doc
        assert '<svg' in render(text, alphabet='v2')
