"""Recovered civic obligations, possible consequences and quantified binding diagnostics."""
import pytest
from scripts import check_kant_civic_example_content_visible as content
CASES=[(group,function,key) for group,(_,_,functions) in content.GROUPS.items() for function,key in functions]
@pytest.mark.parametrize('group,function,key',CASES)
def test_retained_civic_diagnostics(group,function,key):
    content.replay(group,function,key)

def test_selected_sanction_unknowns():
    content.selected_sanction_unknown_checks()

def test_all_outer_case_and_criticism_detail_slots():
    content.slotwise_scope_checks()

def test_each_institutional_sanction_witness_slot():
    content.sanction_witness_binding_checks()

def test_current_case_criticism_permission_and_induction_connected():
    content.whole_content_checks()
