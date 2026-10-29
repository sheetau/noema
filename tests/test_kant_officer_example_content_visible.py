"""Replay all retained officer-example semantic dependencies after recovery."""
import pytest
from scripts import check_kant_officer_example_content_visible as content

CASES=[(group,function,key) for group,(_,_,functions) in content.GROUPS.items() for function,key in functions]

@pytest.mark.parametrize('group,function,key',CASES)
def test_retained_officer_example_diagnostics(group,function,key):
    content.replay(group,function,key)


def test_each_of_ten_binders_over_two_values_with_others_instantiated():
    content.slotwise_binding_checks()


def test_native_conditional_preserves_command_duty_and_hypothetical_discussion():
    content.whole_content_checks()
