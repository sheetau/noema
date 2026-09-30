from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.render import render
from noema.script import encode, decode
from scripts.check_caused_conditions import (
    alignment, generic_checks, paragraph_review, source_checks, temporal_checks,
)
from scripts.compose_caused_conditions import ROOT, generic_composed, source_composed


def test_caused_condition_requires_state_event_shared_agents_and_result_relation():
    rows = generic_checks()
    assert len(rows) == 64
    accepted = [row for row in rows if row['caused_condition']]
    assert len(accepted) == 2
    assert {row['prior_state'] for row in accepted} == {False, True}
    assert all(row['state'] and row['occurs'] and all(row['agents']) and row['cause'] for row in accepted)


def test_understanding_result_is_not_merely_present_or_replaced_with_dependency():
    rows = source_checks()
    assert len(rows) == 11
    assert [name for name, row in rows.items() if row['caused_condition']] == ['baseline', 'already_insufficient']
    assert rows['no_causation']['result_condition']
    assert rows['split_agents']['result_condition']
    assert rows['dependency_instead_of_understanding']['result_condition']
    assert rows['already_insufficient']['prior_condition']
    assert not rows['baseline']['prior_condition']


def test_same_current_recipients_link_causative_prefix_prevention_and_warning():
    rows = temporal_checks()
    assert len(rows) == 6
    assert [name for name, row in rows.items() if row['prefix_then_warning']] == ['baseline', 'already_insufficient']
    assert rows['no_warning']['ordered_prefix']
    assert all(not row['earlier_selection'] for row in rows.values())


def test_new_source_span_and_paragraph_review_do_not_promote_partial_meaning():
    row, review = alignment(), paragraph_review()
    assert row['status'] == 'partial_explicit_reading' and not row['full_semantic_equivalence']
    assert not review['semantic_completion'] and review['not_a_complete_obligation_inventory']
    assert all(item['status'] == 'open' for item in review['current_obligations'])
    prior = parse((ROOT / 'examples/v014/kant-example-deterrence.noema').read_text(encoding='utf-8'))
    assert parse(source_composed()[0])['statements'] == prior['statements']


def test_caused_condition_basis_and_original_alphabet_roundtrip():
    for compose, counts in ((generic_composed, (0, 1)), (source_composed, (145, 198))):
        text, basis = compose()
        doc = parse(text)
        audit = audit_basis(doc, basis)
        assert (audit['primitive_count'], audit['definition_count']) == counts
        assert (ROOT / basis['document']).read_text(encoding='utf-8') == text
        for notation in ('full', 'compact'):
            form = format_graph(doc, notation)
            assert parse(form) == parse(decode(encode(form, 'v2'))) == doc
        assert '<svg' in render(text, alphabet='v2')
