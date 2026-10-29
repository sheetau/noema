"""Retained finite contrasts use current recovered bodies and explicit controls."""
import pytest
from scripts import check_kant_public_reversal_content_visible as content


@pytest.mark.parametrize('group,function,key',[
    (group,function,key) for group,(_,_,functions) in content.GROUPS.items() for function,key in functions])
def test_retained_diagnostic(group,function,key):
    content.replay(group,function,key)


def test_recovered_conditional_attachment_certificate():
    content.attachment_certificate()
