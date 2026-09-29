from pathlib import Path

import pytest

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.render import render
from noema.script import encode, decode
from scripts.compose_kant_discourse import composed, generic_composed
from scripts.check_kant_discourse import discourse_checks, imperative_checks, generic_checks, source_alignment


def test_author_order_and_argument_edges_do_not_endorse_the_source():
    cases = discourse_checks()
    assert len(cases) == 14
    assert cases['baseline']['actual']
    assert all(not row['actual'] for label, row in cases.items() if label != 'baseline')
    assert all(not row['underlying_contents_evaluated'] for row in cases.values())
    assert cases['baseline']['observed']['inferences'] == [['first', 'second', 'third', 'latin', 'german']]
    result = generic_checks()
    assert result['false_math_claim_attributed_without_endorsement'] == [
        {'kind': 'assert', 'value': True}, {'kind': 'ask', 'value': False}]
    assert result['empty_premises_rejected'] and result['self_premise_rejected']


def test_german_imperative_does_not_add_an_unstated_guidance_ban():
    cases = imperative_checks()
    assert cases['own_faculty_use_can_be_guided']['actual']
    assert not cases['independent_use_fails_under_guidance']['actual']
    assert cases['german_directive_uses_literal_goal']['actual']
    assert not cases['old_directive_added_an_extra_condition']['actual']
    assert cases['directive_is_not_assertion']['actual']
    assert cases['quoted_forms_remain_distinct']['actual']
    assert cases['latin_uses_selected_contextual_gloss']['actual']


def test_all_six_ranges_have_a_draft_without_claiming_semantic_completion():
    if not Path('artifacts/written-units-v1/kant-1784.json').exists():
        pytest.skip('Source artifact is prepared separately')
    alignment = source_alignment()
    assert len(alignment['segments']) == 6
    assert all(s['status'] == 'partial' for s in alignment['segments'])
    assert alignment['all_nonblank_source_characters_accounted_for']
    assert not alignment['complete_semantic_translation_verified']
    assert alignment['segments'][3]['reading'] == 'contextual_german_gloss_not_independent_latin_translation'


def test_composed_definitions_and_bodies_survive_all_written_forms():
    for compose, counts in ((generic_composed, (6, 3)), (composed, (28, 19))):
        text, basis = compose()
        doc = parse(text)
        audit = audit_basis(doc, basis)
        assert (audit['primitive_count'], audit['definition_count']) == counts
        for notation in ('full', 'compact'):
            canonical = format_graph(doc, notation)
            assert parse(canonical) == parse(decode(encode(canonical, 'v2'))) == doc
        assert '<svg' in render(text, alphabet='v2')
        assert not audit['semantic_equivalence_to_source_proven']
    assert len(doc['statements']) == 1
    assert doc['statements'][0]['body']['symbol'] == 'cp'
