"""Current-only components and explicit whole-connection query instances."""
import pytest
from scripts import check_kant_clerical_public_freedom_content_visible as content
CASES=[(g,f,k) for g,(_,_,fs) in content.GROUPS.items() for f,k in fs]
@pytest.mark.parametrize('group,function,key',CASES)
def test_retained_diagnostics(group,function,key):content.replay(group,function,key)
def test_owned_review_and_goodwill():content.qualification_checks()
def test_exact_review_pair():content.review_binding_checks()
def test_all_communication_candidates_and_periods():content.mission_scope_checks()
def test_freedom_and_calling_are_independent():content.mission_independence_checks()
def test_each_adapter_position_and_exact_lengths():content.adapter_binding_checks()
def test_every_outer_case_binder():content.outer_binding_checks()
def test_required_unknown_inputs_are_refused():content.selected_unknown_checks()
def test_actual_case_items_public_candidates_and_norms_connected():content.whole_connection_checks()
