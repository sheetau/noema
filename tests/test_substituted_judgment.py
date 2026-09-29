from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.render import render
from noema.script import decode, encode
from scripts.check_substituted_judgment import (
    attribution_checks, conditional_checks, effort_checks, provider_checks,
    source_alignment, source_checks, task_checks,
)
from scripts.compose_substituted_judgment import ROOT, generic_composed, source_composed


def test_effort_free_attainment_requires_one_successful_available_method():
    result = effort_checks()
    assert len(result['cases']) == 128
    assert result['contrasts'] == {'separate_methods': [False, True],
        'same_successful_method': [True, True], 'outside_outcomes': [False, False],
        'no_available_method': [False, False]}


def test_condition_truth_and_premise_applicability_are_separate():
    rows = conditional_checks()
    assert len(rows) == 64
    assert all(not row['conditional'] for row in rows if not row['cases'])
    assert any(row['conditional'] and not row['applicable'] for row in rows)
    assert any(not row['conditional'] and row['applicable'] for row in rows)


def test_provider_kind_access_and_described_task_bind_the_same_objects():
    rows = provider_checks()
    assert len(rows) == 7
    assert [key for key, row in rows.items() if row['accepted']] == ['baseline']
    assert all(not row['task_evaluated'] for row in rows.values())


def test_source_scenario_uses_real_definitions_and_can_share_provider_roles():
    result = source_checks()
    rows = result['cases']
    assert len(rows) == 14
    assert rows['baseline'] == rows['shared_human_provider'] == {
        'premise_in_case': True, 'result_in_case': True, 'applicable': True,
        'conditional': True, 'premise_in_actual_context': False}
    assert rows['wrong_task']['conditional'] and not rows['wrong_task']['applicable']
    assert not rows['own_effort']['conditional'] and rows['own_effort']['applicable']
    assert not result['task_contents_evaluated'] and not result['definitions_replaced_by_primitives']


def test_task_constituents_and_first_person_attribution_keep_their_scope():
    tasks, attribution = task_checks(), attribution_checks()
    assert len(tasks) == 9 and len(attribution) == 8
    assert tasks['baseline'] == [True] * 4
    assert tasks['wrong_actor'] == [False] * 4
    assert tasks['missing_moral'] == [False, True, True, True]
    assert [key for key, row in attribution.items() if row['statements'][-1]] == ['baseline']
    assert all(not row['underlying_scenario_evaluated'] for row in attribution.values())


def test_substituted_judgment_basis_written_forms_and_source_limits():
    for compose, counts in ((generic_composed, (0, 12)), (source_composed, (84, 115))):
        text, basis = compose()
        doc = parse(text)
        audit = audit_basis(doc, basis)
        assert (audit['primitive_count'], audit['definition_count']) == counts
        assert (ROOT / basis['document']).read_text(encoding='utf-8') == text
        for notation in ('full', 'compact'):
            canonical = format_graph(doc, notation)
            assert parse(canonical) == parse(decode(encode(canonical, 'v2'))) == doc
        assert '<svg' in render(text, alphabet='v2')
    alignment = source_alignment()
    assert alignment['end'] - alignment['start'] == len(alignment['source'])
    assert alignment['status'] == 'partial_explicit_reading'
    assert not alignment['full_semantic_equivalence']
