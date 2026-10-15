from itertools import product

import pytest

from scripts.check_disclosure_actions import values


@pytest.mark.parametrize('first,second,deliver1,deliver2,permit,oppose', list(product((False, True), repeat=6)))
def test_same_composed_action_can_be_permitted_without_being_performed(first, second, deliver1, deliver2, permit, oppose):
    performed = first and not second and deliver1 and deliver2
    assert values(candidate=(first, second), delivered=(deliver1, deliver2), permission=permit, opposed=oppose) == [
        permit and not oppose, performed, performed, True]


@pytest.mark.parametrize('variant', ('other_person', 'other_subject', 'other_criterion', 'wrong_polarity',
    'wrong_message', 'other_activity', 'other_principal'))
def test_constructed_action_keeps_the_original_assessment_bindings(variant):
    assert values(variant=variant) == [True, False, False, True]


@pytest.mark.parametrize('variant', ('wrong_target', 'wrong_role'))
def test_permission_for_another_description_or_role_does_not_transfer(variant):
    assert values(variant=variant) == [False, True, True, True]


@pytest.mark.parametrize('records,scope,critical,expected', [
    ((), (), True, False), ((), (), False, False),
    (('first',), ('first', 'second'), True, False),
    (('first', 'second'), ('first',), True, False),
    (('first',), ('first',), True, False),
    (('first',), ('first',), False, True),
    (('second',), ('second',), True, True),
    (('second', 'first'), ('first', 'second'), True, True),
    (('first', 'second', 'first'), ('first', 'second'), True, True),
    (('first', 'second', 'outside'), ('first', 'second'), True, False),
])
def test_same_record_codes_control_the_scope_and_all_assessment_items(records, scope, critical, expected):
    assert values(records=records, scope=scope, critical=critical) == [True, expected, expected, True]


@pytest.mark.parametrize('first,second,critical', list(product((False, True), repeat=3)))
def test_mixed_and_positive_assessments_preserve_the_optional_negative_condition(first, second, critical):
    expected = not critical or not (first and second)
    assert values(signs=(first, second), candidate=(first, second), critical=critical) == [True, expected, expected, True]


@pytest.mark.parametrize('first,second', list(product((False, True), repeat=2)))
def test_actual_truth_does_not_decide_the_speakers_assessment(first, second):
    assert values(actual=(first, second)) == [True] * 4


@pytest.mark.parametrize('variant,message', [
    ('unknown_truth', 'Unknown criterion evaluation'),
    ('unknown_scope', 'Unknown disclosure scope'),
    ('unknown_candidates', 'Unknown judgment candidates'),
    ('unknown_presentation', 'Unknown public presentation'),
    ('unknown_record', 'Unknown judgment record'),
])
def test_permission_and_quotation_do_not_evaluate_unknown_action_conditions(variant, message):
    assert values(variant=variant, indices=(0, 3)) == [True, True]
    with pytest.raises(ValueError, match=message):
        values(variant=variant, indices=(1,))


def test_unknown_selector_cannot_be_replaced_by_an_invented_description():
    with pytest.raises(ValueError, match='Unknown assessment selector'):
        values(variant='unknown_selector', indices=(0,))


def test_pure_memoization_does_not_change_the_interpretation():
    assert values(memoize=False) == values() == [True] * 4
