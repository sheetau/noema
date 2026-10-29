"""Retain possibility, pace, witness and discourse diagnostics after recovery."""
import pytest
from scripts import check_kant_public_slow_attainment_content_visible as content

@pytest.mark.parametrize('function,key',content.GROUPS['attainment'][2])
def test_retained_attainment_diagnostics(function,key):
    content.replay('attainment',function,key)
