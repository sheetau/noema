from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_husbandry_depiction import (
    alignment, attribution_checks, binding_checks, generic_checks, paragraph_review,
    source_checks, target_checks,
)
from scripts.compose_husbandry_depiction import ROOT, generic_composed, source_composed


def test_husbandry_needs_animal_classification_and_all_three_bound_roles():
    rows = generic_checks()
    assert len(rows) == 32
    accepted = [row for row in rows if row['accepted']]
    assert accepted == [{'animal': True, 'human': False, 'roles': [True, True, True], 'accepted': True}]


def test_sustained_husbandry_allows_rotation_but_not_gaps_or_split_role_bindings():
    rows = binding_checks()
    assert len(rows) == 12
    assert [name for name, accepted in rows.items() if accepted] == ['baseline', 'rotating_keepers']


def test_possessive_depiction_does_not_assert_that_the_target_is_an_animal():
    rows = source_checks()
    assert len(rows) == 15
    assert rows['actual_human'] == {'target': True, 'depiction': False, 'framing': True}
    assert rows['baseline'] == {'target': False, 'depiction': True, 'framing': True}
    assert [name for name, row in rows.items() if row['depiction']] == ['baseline', 'rotating_keepers']
    assert all(row['framing'] for row in rows.values())


def test_literal_target_binds_the_same_guardian_group_and_current_population():
    rows = target_checks()
    assert len(rows) == 5
    assert [name for name, accepted in rows.items() if accepted] == ['baseline']


def test_new_assertion_checks_attribution_without_executing_either_description():
    rows = attribution_checks()
    assert len(rows) == 7
    assert [name for name, row in rows.items() if row['assertion']] == ['baseline']
    assert all(not row['contents_evaluated'] for row in rows.values())
    review = paragraph_review()
    assert not review['semantic_completion'] and review['not_a_complete_obligation_inventory']
    assert all(row['status'] == 'open' for row in review['current_obligations'])
    assert next(row for row in review['current_obligations'] if row['id'] == 'livestock_possession')['progress_ja']
    assert not alignment()['full_semantic_equivalence']


def test_husbandry_basis_and_independent_alphabet_roundtrip():
    for compose, counts in ((generic_composed, (0, 5)), (source_composed, (153, 202))):
        text, basis = compose()
        doc = parse(text)
        audit = audit_basis(doc, basis)
        assert (audit['primitive_count'], audit['definition_count']) == counts
        assert (ROOT / basis['document']).read_text(encoding='utf-8') == text
        for notation in ('compact', 'full'):
            form = format_graph(doc, notation)
            assert parse(form) == parse(decode(encode(form, 'v2'))) == doc
