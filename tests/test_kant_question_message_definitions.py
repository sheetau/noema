import pytest
from scripts.check_kant_question_message_definitions import checked,ORIGINALS,expression_inventory


@pytest.mark.parametrize('index',range(len(ORIGINALS)))
def test_saved_definition_keeps_its_exact_body_and_scope(index):checked(index)


def test_native_expression_inventory_has_no_unhandled_writer_branch():
    row=expression_inventory()
    assert row['native_expression_kinds']==row['writer_expression_kinds']
    assert {'iff','question','answer_matches','message','message_content'}<=set(row['native_expression_kinds'])


def test_saved_definitions_contain_the_expected_new_constructors():
    assert set().union(*(set(checked(i)['new_constructors']) for i in range(len(ORIGINALS))))=={'iff','question','message'}
