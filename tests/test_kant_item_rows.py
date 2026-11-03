import json
from pathlib import Path
import pytest
from scripts.check_kant_item_rows import cases,checked,BASELINE
from scripts.kant_item_rows import split_rows,decode_page,pack_rows,shifted,ROW_GAP
from scripts.visible_syntax_geometry import from_svg
from scripts.balanced_circle_script import LARGE,near,line


@pytest.mark.parametrize('index',range(len(cases())))
def test_whole_svg_is_read_without_item_boundaries_or_order_metadata(index):
    row=checked(index)
    assert row['recovered_rows']==row['expected_items']


def saved_items():
    report=json.loads(Path(BASELINE).read_text(encoding='utf-8'))
    row=next(r for r in report['diagnostics'] if r['key']=='dependency-chain')
    return [from_svg(svg) for svg in row['item_svgs']]


def test_rows_without_large_circle_are_read_by_the_same_public_rails():
    items=saved_items()
    assert not any(s['kind']=='circle' and near(s['r'],LARGE) for s in items[-1])
    assert decode_page(list(reversed(pack_rows(items))))==cases()[1][2]


def test_vertical_translation_does_not_change_the_document():
    page=from_svg(checked(1)['svg'])
    assert decode_page(shifted(page,137.25))==cases()[1][2]


def test_reversed_dependency_order_is_not_corrected_using_source_metadata():
    items=saved_items()
    with pytest.raises(ValueError):decode_page(pack_rows([items[1],items[0],items[2]]))


def test_ink_in_the_row_gap_cannot_be_silently_discarded():
    page=from_svg(checked(1)['svg']);rows=split_rows(page)
    centers=[min(s['y'] for s in r if s['kind']=='circle') for r in rows]
    page.append(line((0,centers[0]),(0,centers[1])))
    with pytest.raises(ValueError,match='inconsistent central rails'):decode_page(page)


def test_an_isolated_line_creates_an_invalid_row():
    page=from_svg(checked(0)['svg']);page.append(line((0,1000),(20,1000)))
    with pytest.raises(ValueError,match='Page row has no circles'):decode_page(page)
