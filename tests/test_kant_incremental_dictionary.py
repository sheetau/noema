from copy import deepcopy
import pytest
from scripts import kant_public_fragment as writing,kant_incremental_dictionary as document
from scripts.check_kant_incremental_dictionary import cases,checked,previous
from scripts.visible_syntax_geometry import from_svg


@pytest.mark.parametrize('index',range(len(cases())))
def test_unknown_names_and_dependencies_from_geometry(index):checked(index)


@pytest.mark.parametrize('index',range(len(previous.preserved_rows())))
def test_saved_statement_and_declaration_ink_still_decodes(index):previous.preserved(index)


def test_future_source_is_absent_and_learned_only_after_decoding():
    source=cases()[1][2];row=checked(1);reader=document.Reader()
    first,second=source['declarations']
    assert all(d['name'] not in reader.context.parts and d['name'] not in reader.context.words for d in source['declarations'])
    assert reader.read(from_svg(row['item_svgs'][0]))==first
    assert first['name'] in reader.context.words and second['name'] not in reader.context.words
    assert reader.read(from_svg(row['item_svgs'][1]))==second
    assert reader.read(from_svg(row['item_svgs'][2]))==source['statements'][0]


def test_forward_reference_fails_without_advancing_state():
    row=checked(1);reader=document.Reader();before=deepcopy(reader.document)
    with pytest.raises(ValueError):reader.read(from_svg(row['item_svgs'][1]))
    assert reader.document==before
    assert reader.read(from_svg(row['item_svgs'][0]))==cases()[1][2]['declarations'][0]


def test_duplicate_name_and_declaration_after_statement_are_rejected():
    row=checked(1);items=[from_svg(s) for s in row['item_svgs']]
    reader=document.Reader();reader.read(items[0])
    with pytest.raises(ValueError,match='Duplicate or imported'):reader.read(items[0])
    reader.read(items[1]);reader.read(items[2])
    with pytest.raises(ValueError,match='Declaration follows a statement'):reader.read(items[0])


def test_reader_can_start_without_target_spelling_signature_or_body():
    source=cases()[0][2]['declarations'][0]
    row=checked(0)
    assert writing.decode_declaration(from_svg(row['item_svgs'][0]))==source
    assert writing.table.__wrapped__()==writing.table()


@pytest.mark.parametrize('middle,error',[
    (['types_end'],'Empty full name'),
    (['type_number','types_end'],'Full name requires root components'),
    (['book'],'Missing full name end'),
])
def test_malformed_full_name_from_actual_ink(middle,error):
    from scripts.check_kant_statements import raw_svg
    book=previous.declarations.previous.call('book')['symbol']
    tokens=['primitive','full_name',*(book if t=='book' else t for t in middle)]
    with pytest.raises(ValueError,match=error):writing.decode_declaration(from_svg(raw_svg(tokens)))


def test_full_name_does_not_accept_a_hidden_branch():
    from scripts.check_kant_statements import raw_svg
    book=previous.declarations.previous.call('book')['symbol']
    tokens=['primitive','full_name',book,book,'types_end','types_end','type_individual']
    with pytest.raises(ValueError,match='Full name cannot carry branches'):
        writing.decode_declaration(from_svg(raw_svg(tokens,side_at=2,side_tokens=[book])))
