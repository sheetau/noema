"""Recovered teaching policy, same-case obligation and appointment explanation."""
import pytest
from scripts import check_kant_clerical_obligation_content_visible as content
CASES=[(group,function,key) for group,(_,_,functions) in content.GROUPS.items() for function,key in functions]
@pytest.mark.parametrize('group,function,key',CASES)
def test_retained_clerical_obligation_diagnostics(group,function,key):
    content.replay(group,function,key)
def test_every_case_binder_is_connected(): content.slotwise_binding_checks()
def test_policy_binding_preserves_each_slot_and_exact_length(): content.policy_binding_checks()
def test_same_policy_and_past_appointment_witnesses(): content.appointment_checks()
def test_current_case_and_both_independent_clauses_connected(): content.whole_content_checks()
def test_selected_unknown_inputs_refused(): content.selected_unknown_checks()
