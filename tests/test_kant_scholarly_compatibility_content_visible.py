"""Replay all retained scholarly-compatibility semantic dependencies after recovery."""
import pytest
from scripts import check_kant_scholarly_compatibility_content_visible as content

CASES=[(group,function,key) for group,(_,_,functions) in content.GROUPS.items() for function,key in functions]

@pytest.mark.parametrize('group,function,key',CASES)
def test_retained_scholarly_compatibility_diagnostics(group,function,key):
    content.replay(group,function,key)


def test_each_of_nine_binders_over_two_values_with_others_instantiated():
    content.slotwise_binding_checks()


def test_native_conditional_and_focus_bodies_preserve_same_people_and_method():
    content.whole_content_checks()
