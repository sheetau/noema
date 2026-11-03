import pytest
from scripts.check_kant_single_branch_routes import cases,checked


@pytest.mark.parametrize('index',range(len(cases())))
def test_routes_preserve_exact_syntax_tokens_and_successful_placements(index):
    checked(index)


def test_existing_higher_order_definition_keeps_its_nested_application():
    index=next(i for i,(key,_,_) in enumerate(cases()) if key=='function-definition-body')
    row=checked(index)
    assert row['branches']==3 and row['max_branch_depth']==2
    assert row['branch_limits']==[] and row['unbranched_paths']==[]
