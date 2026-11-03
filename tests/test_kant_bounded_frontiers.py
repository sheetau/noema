import pytest
from scripts.check_kant_bounded_frontiers import cases,checked


@pytest.mark.parametrize('index',range(len(cases())))
def test_actual_frontiers_keep_native_syntax_and_existing_branches(index):
    row=checked(index)
    if not row['identical_svg']:
        assert row['ink']['excursion']<row['previous_ink']['excursion']


@pytest.mark.parametrize('key',['content-outward','function-definition-body','content-siblings'])
def test_long_arch_is_reduced_without_dropping_its_branch(key):
    row=checked(next(i for i,(name,_,_) in enumerate(cases()) if name==key))
    assert row['frontier_yields']>0
    assert row['ink']['excursion']<row['previous_ink']['excursion']
    assert row['branch_limits']==[] and row['unbranched_paths']==[]


def test_atomic_control_matches_saved_ink_and_large_atomic_case_is_reused():
    by_key={key:i for i,(key,_,_) in enumerate(cases())}
    control=checked(by_key['fans-four-compounds'])
    large=checked(by_key['fans-seven-branches'])
    assert control['scheduling_scope']==large['scheduling_scope']=='atomic-branches'
    assert control['action']=='redrawn-control' and control['identical_svg']
    assert large['action']=='reused-svg' and large['identical_svg']


def test_no_height_improvement_preserves_the_old_quoted_placement():
    row=checked(next(i for i,(name,_,_) in enumerate(cases()) if name=='content-quoted'))
    assert row['frontier_window_rejected'] and row['identical_svg']
