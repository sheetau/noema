from copy import deepcopy
import pytest
from scripts import kant_public_fragment as writing
from scripts.check_kant_declarations import cases,checked,inputs,preserved_rows,preserved,malformed,previous,reader_without_target
from scripts.kant_lexical_context import LexicalContext,use_context
from scripts.visible_syntax_geometry import from_svg


@pytest.mark.parametrize('index',range(len(cases())))
def test_declaration_without_target_body_or_signature(index):checked(index)


@pytest.mark.parametrize('index',range(len(preserved_rows())))
def test_saved_statement_still_decodes(index):preserved(index)


@pytest.mark.parametrize('key',list(malformed()))
def test_invalid_declaration_from_ink(key):
    tokens,message=malformed()[key]
    with pytest.raises(ValueError,match=message):
        writing.decode_declaration(from_svg(previous.raw_svg(tokens)))


@pytest.mark.parametrize('where,match',[(0,'Statement head/end'),(1,'Declaration name'),(2,'Type header')])
def test_declaration_header_rejects_attached_arguments(where,match):
    book=previous.call('book')['symbol']
    tokens=['primitive',book,'types_end','type_individual']
    with pytest.raises(ValueError,match=match):
        writing.decode_declaration(from_svg(previous.raw_svg(tokens,side_at=where,side_tokens=[book])))


def test_definition_cannot_hide_a_wrong_result_type():
    _,_,source,published=inputs()[4]
    wrong=dict(source,result='truth')
    with pytest.raises(ValueError,match='Definition result sort mismatch'):
        writing.compile_declaration(wrong,lexicon=LexicalContext.from_published(published))


def test_statement_and_declaration_entry_points_are_distinct():
    source=cases()[0][2]
    with pytest.raises(ValueError,match='Expected a statement'):writing.compile_statement(source)
    with pytest.raises(ValueError,match='Declaration head inside an expression'):
        writing.decode(from_svg(checked(0)['svg']),lexicon=LexicalContext.from_published(inputs()[0][3]))
    with pytest.raises(ValueError,match='Expected a visible declaration head'):
        writing.decode_declaration(from_svg(previous.checked(0)['svg']))


def test_exchanged_body_is_read_from_ink_not_restored_from_dictionary():
    _,_,original,published=inputs()[5]
    altered=inputs()[6][2]
    assert original!=altered and checked(5)['svg']!=checked(6)['svg']
    assert writing.decode_declaration(from_svg(checked(6)['svg']),lexicon=LexicalContext.from_published(published))==altered
    assert writing.table.__wrapped__()==writing.table()
