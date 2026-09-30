from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_training_frame import (
    alignment, assembly_checks, attribution_checks, bodily_checks, depiction_checks,
    generic_checks, paragraph_review, source_checks,
)
from scripts.compose_training_frame import ROOT, generic_composed, source_composed


def test_supporting_training_structure_needs_all_six_conditions():
    rows = generic_checks()
    assert len(rows) == 64
    assert sum(row['accepted'] for row in rows) == 1


def test_structural_connection_is_symmetric_and_cannot_borrow_foreign_members():
    report = assembly_checks()
    assert len(report['graphs']) == 8 and sum(row['accepted'] for row in report['graphs']) == 4
    assert len(report['scope']) == 8
    assert [key for key, value in report['scope'].items() if value] == [
        'permuted', 'reversed_connections', 'duplicate_member']


def test_intended_users_and_learning_goal_do_not_assert_children_or_success():
    rows = source_checks()
    assert len(rows) == 15
    assert [name for name, valid in rows.items() if valid] == [
        'baseline', 'children_and_activity_false', 'children_and_activity_true']


def test_independent_bodily_activity_excludes_support_only_for_the_same_act():
    assert bodily_checks() == {'baseline': True, 'supported': False, 'no_movement': False,
                              'other_act_supported': True, 'other_person_supported': True}


def test_configured_apparatus_is_the_same_device_as_the_confinement_depiction():
    rows = depiction_checks()
    assert len(rows) == 5
    assert [name for name, valid in rows.items() if valid] == ['baseline']
    frames = attribution_checks()
    assert [name for name, row in frames.items() if row['framed']] == ['baseline']
    assert all(not row['bodily_activity_evaluated'] for row in frames.values())


def test_configuration_and_purpose_are_not_full_historical_meaning_confirmation():
    review = paragraph_review()
    assert not review['semantic_completion'] and review['not_a_complete_obligation_inventory']
    assert all(row['status'] == 'open' for row in review['current_obligations'])
    assert not alignment()['full_semantic_equivalence']
    assert parse(source_composed()[0])['statements'] == parse(
        (ROOT / 'examples/v014/kant-confinement.noema').read_text(encoding='utf-8'))['statements']


def test_training_frame_basis_and_original_alphabet_roundtrip():
    for compose, counts in ((generic_composed, (0, 7)), (source_composed, (174, 217))):
        text, basis = compose()
        doc = parse(text)
        audit = audit_basis(doc, basis)
        assert (audit['primitive_count'], audit['definition_count']) == counts
        assert (ROOT / basis['document']).read_text(encoding='utf-8') == text
        for notation in ('full', 'compact'):
            form = format_graph(doc, notation)
            assert parse(form) == parse(decode(encode(form, 'v2'))) == doc
