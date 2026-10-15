from itertools import product

import pytest

from noema.constructed import parse
from scripts.compose_focused_permission import ROOT, PARENT, SOURCE, CORE, build
from scripts.check_focused_permission import values, attribution, source_invariants


@pytest.mark.parametrize('selected,ranked,person_valid,activity_valid,permission', list(product((False, True), repeat=5)))
def test_scalar_background_and_current_permission_remain_independent(selected, ranked, person_valid, activity_valid, permission):
    background = not selected or ranked and person_valid and activity_valid
    assert values(selected, ranked, person_valid, activity_valid, permission, indices=(0, 1, 2, 3)) == [
        True, background, True, permission and person_valid and activity_valid]


@pytest.mark.parametrize('variant', ('ruler_viewpoint', 'wrong_context', 'reversed_ranking'))
def test_source_background_keeps_the_author_context_and_comparison_direction(variant):
    assert values(variant=variant) == [True, False, True]


def test_background_does_not_assert_that_either_permission_is_currently_granted():
    # Normative relations and actual actions raise if called in this interpretation.
    assert values() == [True, True, True]


def test_unknown_scalar_relation_is_not_needed_to_construct_or_negate_the_package():
    assert values(variant='unknown_ranking', indices=(0, 2)) == [True, True]
    with pytest.raises(ValueError, match='Unknown source ranking'):
        values(variant='unknown_ranking', indices=(1,))


def test_current_permission_can_be_evaluated_without_the_ranking():
    assert values(variant='unknown_ranking', permission=True, indices=(3,)) == [True]


def test_closed_reference_construction_is_separate_from_resolving_the_reference():
    assert values(variant='unknown_reference', indices=(0, 2)) == [True, True]
    with pytest.raises(ValueError, match='Unknown closed person reference'):
        values(variant='unknown_reference', indices=(1,))


@pytest.mark.parametrize('reported,backgrounded', list(product((False, True), repeat=2)))
def test_source_attribution_keeps_both_records_without_evaluating_either_content(reported, backgrounded):
    for path in (SOURCE, CORE):
        assert attribution(parse((ROOT / path).read_text(encoding='utf-8')), reported, backgrounded) == (reported and backgrounded)


@pytest.mark.parametrize('variant', ('other_node', 'other_author', 'other_foreground_scope', 'other_background_scope',
                                  'other_context', 'old_foreground', 'other_background'))
def test_a_background_attached_to_another_claim_or_scope_does_not_transfer(variant):
    assert attribution(parse((ROOT / CORE).read_text(encoding='utf-8')), variant=variant) is False


def test_cache_does_not_change_reference_binding_or_scalar_background():
    assert values(memoize=False) == values() == [True, True, True]


def test_source_preservation_frame_identity_and_reproduction():
    source_invariants(*(parse((ROOT / path).read_text(encoding='utf-8')) for path in (PARENT, SOURCE)))
    assert all((ROOT / path).read_text(encoding='utf-8') == text for path, text in build().items())
