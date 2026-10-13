from noema.grammar import parse
from noema.meaning_basis import audit_basis
from scripts.check_scoped_counts import finite_checks, source_checks, alignment
from scripts.compose_scoped_counts import ROOT, PARENT, generic_composed, source_composed


def test_population_is_complete_nonempty_unique_and_order_independent():
    rows = finite_checks()
    assert rows['scope_cases'] == 320
    assert rows['threshold_and_permutation_cases'] == 576
    for name in ('omitted_eligible_person', 'selected_only_sample', 'out_of_scope_person', 'duplicate', 'bad_indicator'):
        assert rows['contrasts'][name] == [False] * 3
    assert rows['unknown_property_refused']


def test_zero_qualifiers_strict_boundary_and_absolute_count_are_distinct():
    rows = finite_checks()['contrasts']
    assert rows['zero_qualifiers'] == [True, True, False]
    assert rows['at_upper_boundary'] == [True, False, False]
    assert rows['all_of_small_scope'] == [True, True, True]


def test_source_person_scope_property_and_bound_share_the_context():
    rows = source_checks()
    assert len(rows) == 11
    assert rows['baseline'] == [True, True]
    assert rows['zero'] == [True, False]
    assert rows['wrong_property_context'] == [True, False]
    assert rows['population_size_bound'] == [True, True]
    assert [name for name, result in rows.items() if result[1]] == ['baseline', 'population_size_bound']


def test_only_quantity_fragment_is_aligned_and_success_property_is_still_pending():
    row = alignment()
    assert row['source'] == 'nur Wenige'
    assert not row['full_semantic_equivalence']
    assert 'successful independent work on the mind and secure gait as the counted property' in row['remaining']


def test_existing_source_is_preserved_without_a_new_asserted_conclusion():
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    for builder, expected in ((generic_composed, (4, 11)), (source_composed, (215, 330))):
        text, basis = builder()
        doc = parse(text)
        audit = audit_basis(doc, basis)
        assert (audit['primitive_count'], audit['definition_count']) == expected
        assert (ROOT / basis['document']).read_text(encoding='utf-8') == text
    assert doc['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert doc['statements'] == parent['statements']
