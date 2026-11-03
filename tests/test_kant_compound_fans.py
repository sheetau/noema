import pytest

from scripts.check_kant_compound_fans import cases,checked


@pytest.mark.parametrize('index',range(len(cases())))
def test_compound_words_keep_multiple_branches_without_reduction(index):
    row=checked(index)
    expected=7 if row['key']=='seven-branches' else 2 if row['key'] in ('give-compounds','quoted-compounds') else 3
    assert row['maximum_sides']==expected
    assert row['multiple_owners']>=1
    assert row['branch_limits']==[] and row['unbranched_paths']==[]
    if row['key']=='nested-compounds':assert row['max_branch_depth']>=2
