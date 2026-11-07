"""Scoped negative claim and separately evaluated quoted arrangement."""
import pytest
from scripts import check_kant_clerical_conscience_content_visible as content
CASES=[(g,f,k) for g,(_,_,fs) in content.GROUPS.items() for f,k in fs]
@pytest.mark.parametrize('group,function,key',CASES)
def test_retained_diagnostics(group,function,key):content.replay(group,function,key)
def test_exact_arrangement_bindings_and_length():content.arrangement_binding_checks()
def test_each_outer_case_binder():content.outer_binding_checks()
def test_actual_same_policy_duty_and_appointment():content.appointment_checks()
def test_actual_case_negative_claim_and_unknown_refusal():content.whole_claim_checks()
def test_actual_quoted_arrangement_is_separate():content.whole_arrangement_checks()
