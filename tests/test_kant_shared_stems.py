import pytest
from scripts.check_kant_shared_stems import cases,checked


@pytest.mark.parametrize('index',range(len(cases())))
def test_actual_stems_keep_native_syntax_and_existing_branches(index):checked(index)


@pytest.mark.parametrize('key',['function-definition-body','content-siblings'])
def test_single_sides_share_a_stem_and_reduce_the_long_connection(key):
    row=checked(next(i for i,(name,_,_) in enumerate(cases()) if name==key))
    assert row['maximum_sides']==1 and row['branches']==3
    assert row['ink']['stem_junctions']>row['previous_ink']['stem_junctions']
    assert row['ink']['line_length']<row['previous_ink']['line_length']
    assert row['ink']['excursion']<row['previous_ink']['excursion']
    assert row['width']<row['previous_width']
    assert row['branch_limits']==[] and row['unbranched_paths']==[]
