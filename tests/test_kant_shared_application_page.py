from scripts.check_kant_shared_application_page import checked


def test_actual_shared_conjunction_keeps_argument_branches():
    row=checked(0)
    assert row['multiple_owners']>=1 and row['maximum_sides']>=2
    assert row['branches']>=4
    assert row['branch_limits']==[] and row['unbranched_paths']==[]
    assert row['svg_changed']
