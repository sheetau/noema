"""Replay all retained office-obedience semantic dependencies after recovery."""
import pytest
from scripts import check_kant_office_obedience_content_visible as content

CASES=[(group,function,key) for group,(_,_,functions) in content.GROUPS.items() for function,key in functions]

@pytest.mark.parametrize('group,function,key',CASES)
def test_retained_office_obedience_diagnostics(group,function,key):
    content.replay(group,function,key)


def test_whole_office_scope_preserves_current_background_and_fixed_people():
    content.whole_content_checks()
