from itertools import product

import pytest

from scripts.check_scalar_backgrounds import values, permission_values, EDGES
from scripts.compose_scalar_backgrounds import ROOT, build


@pytest.mark.parametrize('focus,first,second,additive,ranked', list(product((False, True), repeat=5)))
def test_background_failure_is_not_the_negation_of_the_foreground(focus, first, second, additive, ranked):
    background = ranked and (not additive or first or second)
    result = values((focus, first, second), additive, edges=EDGES if ranked else ((0, 1),))
    assert result == [background, focus, background, not focus,
        dict(force='ask', values=[focus, not focus]), True, True, True]


@pytest.mark.parametrize('alternatives,expected', [
    ((), False), (('focus',), False), (('focus', 'one'), False),
    (('one',), True), (('one', 'one'), True), (('two', 'one'), True),
])
def test_comparison_scope_is_nonempty_excludes_the_focus_and_does_not_count_duplicates(alternatives, expected):
    assert values(alternatives=alternatives, additive=False)[:4] == [expected, True, expected, False]


@pytest.mark.parametrize('edges,expected', [
    (EDGES, True), (((0, 1), (1, 2)), False),
    (EDGES + ((1, 0),), False), (EDGES + ((0, 0),), False),
])
def test_strict_partial_ranking_rejects_cycles_and_missing_transitive_edges(edges, expected):
    assert values(edges=edges, order_only=True) == [expected]


@pytest.mark.parametrize('variant', ('wrong_observer', 'wrong_context'))
def test_a_ranking_from_another_perspective_or_context_cannot_supply_the_background(variant):
    assert values(variant=variant)[:4] == [False, True, False, False]


def test_the_same_truth_under_another_description_does_not_transfer_the_ranking():
    assert values(alternatives=('alias',), edges=((0, 1),))[:4] == [False, True, False, False]
    assert values(alternatives=('alias',), edges=((0, 3),))[:4] == [True, True, True, False]


def test_scalar_only_background_does_not_require_any_alternative_to_be_true():
    assert values((True, False, False), additive=False)[:4] == [True, True, True, False]
    assert values((True, False, False), additive=True)[:4] == [False, True, False, False]


def test_scalar_only_background_does_not_execute_alternative_contents():
    assert values(additive=False, variant='unknown_alternative', indices=(0, 2)) == [True, True]
    with pytest.raises(ValueError, match='Unknown alternative truth'):
        values(additive=True, variant='unknown_alternative', indices=(0,))


def test_background_does_not_require_knowing_the_foreground_truth():
    assert values(variant='unknown_focus', indices=(0, 2)) == [True, True]
    with pytest.raises(ValueError, match='Unknown foreground truth'):
        values(variant='unknown_focus', indices=(1,))


def test_foreground_does_not_require_a_known_or_satisfied_scalar_background():
    assert values(variant='unknown_ranking', indices=(1, 3)) == [True, False]
    with pytest.raises(ValueError, match='Unknown scalar ranking'):
        values(variant='unknown_ranking', indices=(0,))


@pytest.mark.parametrize('variant', ('unknown_focus', 'unknown_alternative', 'unknown_ranking'))
def test_negation_and_question_construction_preserve_codes_without_executing_contents(variant):
    assert values(variant=variant, indices=(5, 6, 7)) == [True] * 3


def test_cached_and_uncached_interpretations_agree():
    assert values(memoize=False) == values()


def test_saved_noema_can_be_reproduced_without_a_model():
    assert all((ROOT / path).read_text(encoding='utf-8') == text for path, text in build().items())


@pytest.mark.parametrize('plain,compound,ranked,oppose_plain,oppose_compound', list(product((False, True), repeat=5)))
def test_alternative_permissions_use_one_frame_and_keep_background_separate(plain, compound, ranked, oppose_plain, oppose_compound):
    foreground = compound and not oppose_compound
    assert permission_values(plain, compound, ranked, oppose_plain, oppose_compound) == [
        ranked and plain and not oppose_plain, foreground, not foreground, True]


@pytest.mark.parametrize('variant', ('wrong_ruler', 'wrong_person', 'wrong_role', 'wrong_act'))
def test_both_permissions_keep_the_same_ruler_person_role_and_activity(variant):
    assert permission_values(variant=variant) == [False, False, True, True]


def test_ranking_another_frame_does_not_change_the_permission_itself():
    assert permission_values(variant='different_frame') == [False, True, False, True]


def test_permission_projection_does_not_need_the_ranking():
    assert permission_values(variant='unknown_ranking', indices=(1, 2, 3)) == [True, False, True]
    with pytest.raises(ValueError, match='Unknown permission ranking'):
        permission_values(variant='unknown_ranking', indices=(0,))


def test_background_uses_the_alternative_permission_without_executing_the_foreground():
    assert permission_values(variant='unknown_compound', indices=(0, 3)) == [True, True]
    with pytest.raises(ValueError, match='Unknown compound permission'):
        permission_values(variant='unknown_compound', indices=(1,))
