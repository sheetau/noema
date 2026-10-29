"""Recovered opinion contents, normative scopes and whole conditional connections."""
import pytest
from scripts import check_kant_public_civic_opinion_content_visible as content
CASES=[(group,function,key) for group,(_,_,functions) in content.GROUPS.items() for function,key in functions]
@pytest.mark.parametrize('group,function,key',CASES)
def test_retained_public_civic_opinion_diagnostics(group,function,key):
    content.replay(group,function,key)
def test_every_outer_case_and_public_expression_binder_is_connected():
    content.slotwise_binding_checks()
def test_same_citizen_expression_and_all_three_duty_forms_are_connected():
    content.whole_content_checks()
