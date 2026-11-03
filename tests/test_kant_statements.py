import pytest
from scripts import kant_public_fragment as writing
from scripts.check_kant_statements import cases,checked,preserved_rows,preserved,malformed,raw_svg
from scripts.visible_syntax_geometry import from_svg


@pytest.mark.parametrize('index',range(len(cases())))
def test_statement_force_and_scope_from_actual_ink(index):checked(index)


@pytest.mark.parametrize('index',range(len(preserved_rows())))
def test_saved_expressions_keep_exact_native_reading(index):preserved(index)


@pytest.mark.parametrize('key',list(malformed()))
def test_malformed_statement_from_actual_ink(key):
    tokens,message=malformed()[key]
    with pytest.raises(ValueError,match=message):
        writing.decode(from_svg(raw_svg(tokens)))


@pytest.mark.parametrize('where',(0,8))
def test_assumption_head_and_end_cannot_carry_a_hidden_child(where):
    tokens=malformed()['empty-assumption'][0]
    truth=tokens[1:-1]
    # An inner end has a following main continuation, making the attached
    # expression an actual second arm rather than merely a trailing word.
    tokens=['suppose',*truth,'suppose',*truth,*truth,'types_end',*truth,'types_end']
    with pytest.raises(ValueError,match='Statement head/end cannot carry a branch'):
        writing.decode(from_svg(raw_svg(tokens,side_at=where,side_tokens=truth)))


def test_an_expression_after_the_outer_end_is_not_silently_consumed():
    tokens=malformed()['empty-assumption'][0]
    truth=tokens[1:-1]
    tokens=['suppose',*truth,*truth,'types_end']
    with pytest.raises(ValueError,match='Trailing visible words'):
        writing.decode(from_svg(raw_svg(tokens,side_at=5,side_tokens=truth)))


def test_no_universal_statement_head_and_forces_are_distinct():
    by_key={k:s for k,_,s in cases()}
    assert writing.events(by_key['assert'])[0]['token']==by_key['assert']['body']['symbol']
    assert writing.events(by_key['ask-question'])[0]['token']=='question'
    assert writing.events(by_key['perform-direct'])[0]['token']=='message_direct'
    assert writing.events(by_key['ask-truth'])[0]['token']=='ask_truth'
    assert checked(0)['svg']!=checked(1)['svg']
    assert writing.table.__wrapped__()==writing.table()


def test_wrong_native_force_is_not_silently_replaced():
    source=dict(cases()[2][2],kind='assert')
    with pytest.raises(ValueError,match='Statement body has wrong sort'):writing.events(source)
