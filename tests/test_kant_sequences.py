import pytest
from scripts import kant_public_fragment as writing
from scripts.check_kant_sequences import cases,checked,preserved_rows,preserved,raw_svg,malformed,numbers
from scripts.visible_syntax_geometry import from_svg,to_svg


@pytest.mark.parametrize('index',range(len(cases())))
def test_sequence_ink_keeps_items_types_and_native_operations(index):checked(index)


@pytest.mark.parametrize('index',range(len(preserved_rows())))
def test_existing_nonnumeric_and_numeric_ink_keeps_its_reading(index):preserved(index)


@pytest.mark.parametrize('key',list(malformed()))
def test_malformed_sequence_ink_is_rejected_at_its_actual_boundary(key):
    tokens,message=malformed()[key]
    with pytest.raises(ValueError,match=message):writing.decode(list(reversed(from_svg(raw_svg(tokens)))))


@pytest.mark.parametrize('variant',['no-main-item','extra-side-expression','branch-on-end'])
def test_branches_cannot_hide_extra_items_or_close_the_main_list(variant):
    book=numbers.components()[0][0]
    empty=['sequence','type_individual','types_end']
    tokens=['equal',*empty,*empty];side_at=1;side=[book]
    if variant=='no-main-item':message='require a final main item'
    elif variant=='extra-side-expression':
        tokens=['equal','sequence','type_individual',book,'types_end',*empty]
        side=[book,book];message='exactly one complete expression'
    else:side_at=3;message='Type header cannot carry'
    with pytest.raises(ValueError,match=message):
        writing.decode(from_svg(raw_svg(tokens,side_at=side_at,side_tokens=side)))


def test_branch_prefix_and_serial_layout_keep_identical_element_order():
    index=next(i for i,(key,_,_) in enumerate(cases()) if key=='three-items')
    row=checked(index);source=cases()[index][2]
    assert row['maximum_sides']>=2 and not row['branch_limits'] and not row['unbranched_paths']
    serial=writing.compile_statement(source,branch=False)
    assert writing.decode(from_svg(to_svg(serial['shapes'])))==source


def test_repeated_shape_table_lookup_is_unambiguous():
    assert writing.table.__wrapped__()==writing.table()
