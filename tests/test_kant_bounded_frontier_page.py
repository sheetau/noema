from scripts.check_kant_bounded_frontier_page import checked


def test_actual_statement_preserves_structure_without_increasing_excursion():
    row=checked(0)
    assert row['circles']==row['previous_circles']==39
    assert row['branches']>=row['previous_branches']==4
    assert row['multiple_owners']>=1 and row['maximum_sides']>=2
    assert row['branch_limits']==[] and row['unbranched_paths']==[]
    assert row['ink']['excursion']<=row['previous_ink']['excursion']
