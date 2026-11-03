from collections import Counter
import pytest
from scripts import kant_saved_item_join as joining
from scripts.check_kant_saved_item_join import fixtures, checked
from scripts.kant_folded_flow import translate
from scripts.visible_syntax_geometry import from_svg
from scripts import kant_public_fragment as writing
from scripts.check_kant_statements import call
from scripts.kant_incremental_dictionary import Reader


def shape_key(shape):
    return tuple(sorted((k, round(v, 5) if isinstance(v, (int, float)) else v) for k, v in shape.items()))


@pytest.mark.parametrize('index', range(3))
def test_original_ink_survives_translation_and_page_round_trip(index):
    fixture = fixtures()[index]
    before = fixture['reader'].result(True)
    result = checked(index)
    original = Counter(shape_key(s) for shapes, dx in zip(result['input_shapes'], result['translations']) for s in translate(shapes, dx))
    actual = Counter(shape_key(s) for s in from_svg(result['svg']))
    assert not original - actual
    added = actual - original
    assert sum(added.values()) == sum(j['added_lines'] for j in result['junctions'])
    assert all(dict(key)['kind'] == 'line' for key in added)
    assert fixture['reader'].result(True) == before
    assert result['exact']


def test_unaligned_lexical_boundary_is_rejected_instead_of_changing_the_next_statement():
    records = [dict(kind='assert', body=call(name, call('book'))) for name in ('red', 'round')]
    shapes = [writing.compile_statement(s)['shapes'] for s in records]
    with pytest.raises(ValueError, match='bounded route choices'):
        joining.join(shapes, reader=Reader())


def test_non_item_input_and_single_item_are_rejected():
    fixture = fixtures()[0]
    with pytest.raises(ValueError, match='at least two'):
        joining.join(fixture['shapes'][:1], reader=fixture['reader'])
    with pytest.raises(ValueError, match='one complete item'):
        joining.join([from_svg(checked(0)['svg']), fixture['shapes'][0]], reader=fixture['reader'])
