"""Replay all retained public-purpose-mechanism semantic dependencies after recovery."""
import pytest
from scripts import check_kant_public_purpose_mechanism_content_visible as content

CASES=[(group,function,key) for group,(_,_,functions) in content.GROUPS.items() for function,key in functions]

@pytest.mark.parametrize('group,function,key',CASES)
def test_retained_public_purpose_mechanism_diagnostics(group,function,key):
    content.replay(group,function,key)


def test_whole_institutional_content_and_actual_means_are_connected():
    content.whole_content_checks()
