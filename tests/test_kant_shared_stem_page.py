from scripts.check_kant_shared_stem_page import checked


def test_actual_statement_keeps_shared_argument_structure():
    row=checked(0)
    assert row['circles']==row['previous_circles']
    assert row['branches']>=row['previous_branches']
    assert row['multiple_owners']>=1 and row['maximum_sides']>=2
    assert row['branch_limits']==[] and row['unbranched_paths']==[]
