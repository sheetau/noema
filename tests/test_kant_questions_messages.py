import pytest
from scripts import kant_public_fragment as writing
from scripts.check_kant_questions_messages import cases,checked,preserved_rows,preserved,malformed,sequences
from scripts.visible_syntax_geometry import from_svg,to_svg


@pytest.mark.parametrize('index',range(len(cases())))
def test_new_expressions_keep_their_native_scope_and_arguments(index):checked(index)


@pytest.mark.parametrize('index',range(len(preserved_rows())))
def test_existing_ink_keeps_its_exact_reading(index):preserved(index)


@pytest.mark.parametrize('key',list(malformed()))
def test_bad_question_or_message_is_rejected_from_actual_ink(key):
    tokens,message=malformed()[key]
    with pytest.raises(ValueError,match=message):
        writing.decode(list(reversed(from_svg(sequences.raw_svg(tokens)))))


def test_question_signature_rejects_an_extra_answer_branch():
    book=sequences.numbers.components()[0][0]
    q0=malformed()['extra-answer'][0][:-1]
    with pytest.raises(ValueError,match='Too many branches for the visible question type'):
        writing.decode(from_svg(sequences.raw_svg(q0,side_at=0,side_tokens=[book])))


def test_message_forces_and_answer_order_are_not_layout_variants():
    by_key={key:i for i,(key,_,_) in enumerate(cases())}
    assert len({checked(by_key[key])['svg'] for key in writing.MESSAGE_FORCES})==3
    assert checked(by_key['two-answers'])['svg']!=checked(by_key['exchanged-answers'])['svg']
    source=cases()[by_key['mixed-answers']][2]
    serial=writing.compile_statement(source,branch=False)
    assert writing.decode(from_svg(to_svg(serial['shapes'])))==source


def test_unknown_force_is_not_coerced_and_shape_lookup_is_unambiguous():
    with pytest.raises(ValueError,match='Unknown message force'):
        writing.split(dict(kind='message',force='guess',content={}))
    assert writing.table.__wrapped__()==writing.table()
