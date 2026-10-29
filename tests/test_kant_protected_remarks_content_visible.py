"""Retained diagnostics, witnessed command bindings and protected remarks."""
import pytest
from scripts import check_kant_protected_remarks_content_visible as content
CASES=[(group,function,key) for group,(_,_,functions) in content.GROUPS.items() for function,key in functions]
@pytest.mark.parametrize('group,function,key',CASES)
def test_retained_protected_remarks_diagnostics(group,function,key):
    content.replay(group,function,key)
def test_prior_command_witnesses_are_bound_one_slot_at_a_time():
    content.prior_binding_checks()
def test_nine_conditional_arguments_are_bound_one_slot_at_a_time():
    content.slotwise_binding_checks()
def test_witnessed_native_scope_and_all_regulator_protections():
    content.whole_content_checks()
