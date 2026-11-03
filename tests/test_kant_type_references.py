import pytest
from scripts import kant_scoped_types as types,kant_public_fragment as writing
from scripts.check_kant_type_references import cases,checked,type_cases,preserved_rows,preserved,declarations
from scripts.visible_syntax_geometry import from_svg


@pytest.mark.parametrize('index',range(len(cases())))
def test_contracted_declaration_from_actual_ink(index):checked(index)


@pytest.mark.parametrize('index',range(len(preserved_rows())))
def test_old_expanded_ink_keeps_exact_reading(index):preserved(index)


@pytest.mark.parametrize('key,values',type_cases())
def test_expanded_and_contracted_types_end_at_same_boundary(key,values):
    for references in (False,True):
        stream=iter(types.type_list_tokens(values,references=references)+['type_truth','not'])
        assert types.read_type_list(lambda:next(stream))==values
        assert types.read_type(lambda:next(stream))=='truth'
        assert next(stream)=='not'
    if key=='base-unchanged':assert types.type_list_tokens(values)==['type_individual','type_individual','types_end']


@pytest.mark.parametrize('tokens,message',[
    (['bound0','types_end'],'Unbound visible type reference'),
    (['type_sequence','bound0','types_end'],'Unbound visible type reference'),
    (['type_number','bound1','types_end'],'Unbound visible type reference'),
    (['type_number','type_truth','bound_shift','bound0','types_end'],'Invalid visible type reference tail'),
    (['type_function','type_number','types_end','type_truth','bound1','types_end'],'Unbound visible type reference'),
    (['quote_raise','bound0','types_end'],'rank marker'),
])
def test_invalid_reference_from_actual_ink(tokens,message):
    book=declarations.previous.call('book')['symbol']
    raw=['primitive',book,*tokens,'type_truth']
    with pytest.raises(ValueError,match=message):
        writing.decode_declaration(from_svg(declarations.previous.raw_svg(raw)))


def test_a_new_header_cannot_read_the_previous_headers_types():
    stream=iter(['type_number','types_end','bound0'])
    assert types.read_type_list(lambda:next(stream))==['number']
    with pytest.raises(ValueError,match='Unbound visible type reference'):types.read_type(lambda:next(stream))


def test_expansion_is_bounded_before_copying_repeated_types():
    # Each complete function includes two copies of the previous type. Only
    # a short input is needed to exceed 4096 expanded nodes.
    tokens=['type_number']
    for _ in range(14):tokens+=['type_function','bound0','types_end','bound0']
    stream=iter(tokens+['types_end'])
    with pytest.raises(ValueError,match='Expanded type header exceeds node budget'):
        types.read_type_list(lambda:next(stream))


def test_references_cannot_hide_excessive_expanded_depth():
    # The first type reaches depth 128 with only 129 nodes. Wrapping its
    # reference once exceeds depth without reaching the separate size limit.
    stream=iter(['type_sequence']*128+['type_number','type_sequence','bound0','types_end'])
    with pytest.raises(ValueError,match='Type nesting outside'):types.read_type_list(lambda:next(stream))
