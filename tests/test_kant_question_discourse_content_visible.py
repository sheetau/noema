"""Replay all retained question-discourse semantic dependencies after recovery."""
import pytest
from scripts import check_kant_question_discourse_content_visible as content

CASES=[(group,function,key) for group,(_,_,functions) in content.GROUPS.items() for function,key in functions]

@pytest.mark.parametrize('group,function,key',CASES)
def test_retained_question_discourse_diagnostics(group,function,key):
    content.replay(group,function,key)
