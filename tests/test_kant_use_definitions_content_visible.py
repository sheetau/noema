"""Replay all retained use-definitions semantic dependencies after recovery."""
import pytest
from scripts import check_kant_use_definitions_content_visible as content

CASES=[(group,function,key) for group,(_,_,functions) in content.GROUPS.items() for function,key in functions]

@pytest.mark.parametrize('group,function,key',CASES)
def test_retained_use_definitions_diagnostics(group,function,key):
    content.replay(group,function,key)
