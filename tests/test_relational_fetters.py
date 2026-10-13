from noema.grammar import parse
from noema.meaning_basis import audit_basis
from scripts.check_relational_fetters import (
    pair_checks, bodily_checks, persistence_checks, attribution_checks, framing_checks, category_refusal, alignment,
)
from scripts.compose_relational_fetters import ROOT, PARENT, generic_composed, source_composed


def test_participant_positions_and_arity_are_preserved_across_pair_lifting():
    report = pair_checks()
    assert len(report['cases']) == 6
    assert [row['participants'] for row in report['cases'] if row['result'][0]] == [('zb', 'zc')]
    assert report['same_individual_can_fill_two_roles']


def test_physical_fetter_requires_same_object_limb_person_and_movement():
    report = bodily_checks()
    assert len(report['cases']) == 16
    assert sum(row['result'][0] for row in report['cases']) == 1
    assert len(report['bindings']) == 15
    assert not any(row[0] for row in report['bindings'].values())


def test_persistence_requires_every_intermediate_point_and_does_not_assert_forever():
    rows = persistence_checks()
    assert len(rows) == 10
    assert [name for name, result in rows.items() if result[0]] == ['baseline', 'loss_outside_scope']
    assert rows['scope_includes_prior_time'] == [False]


def test_attribution_preserves_direction_author_and_context_without_execution():
    report = attribution_checks()
    assert report['all_content_primitives_guarded_against_execution']
    assert [key for key, value in report['cases'].items() if value[0]] == ['baseline']


def test_relational_metaphor_does_not_entail_target_or_depiction_truth():
    rows = framing_checks()
    assert len(rows) == 8
    assert any(not row['target'] and not row['depiction'] and row['framed'] for row in rows)
    assert all(not row['result'][-1] for row in rows)


def test_unbounded_description_domain_is_not_replaced_by_examples():
    assert category_refusal()['refused']


def test_alignment_does_not_count_unresolved_unending_duration():
    row = alignment()
    assert row['source'] == 'Fußschellen'
    assert 'strength of immerwährenden' in row['remaining']
    assert not row['full_semantic_equivalence']


def test_source_preserves_prior_declarations_and_adds_only_metaphor_attribution():
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    for builder, counts in ((generic_composed, (1, 3)), (source_composed, (194, 282))):
        text, basis = builder()
        doc = parse(text)
        audit = audit_basis(doc, basis)
        assert (audit['primitive_count'], audit['definition_count']) == counts
        assert (ROOT / basis['document']).read_text(encoding='utf-8') == text
    assert doc['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert doc['statements'][:-1] == parent['statements']
    assert doc['statements'][-1]['body']['symbol'] == 'h2c'
