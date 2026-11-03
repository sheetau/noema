from copy import deepcopy
import pytest
from scripts import kant_folded_flow as folded
from scripts.kant_item_rows import pack_rows
from scripts.visible_syntax_geometry import from_svg
from scripts.check_kant_folded_flow import cases,checked,preserved,saved,ink_key,WIDTHS,prior


@pytest.mark.parametrize('index',range(len(cases())))
def test_folded_geometry_and_syntax_exact(index):
    row=checked(index)
    assert row['rows']>len(saved()[index]['row_svgs'])
    assert all(folded._bounds(from_svg(svg))[1]-folded._bounds(from_svg(svg))[0]<=WIDTHS[index]+1e-5 for svg in row['row_svgs'])


@pytest.mark.parametrize('index',range(len(cases())))
def test_old_complete_item_rows_do_not_need_cut_strokes(index):preserved(index)


def rows(index=6):return [from_svg(svg) for svg in checked(index)['row_svgs']]


def test_missing_first_or_last_row_is_not_a_complete_flow():
    page=rows()
    with pytest.raises(ValueError,match='without a preceding'):folded.unfold(pack_rows(page[1:]))
    with pytest.raises(ValueError,match='Unfinished'):folded.unfold(pack_rows(page[:-1]))


def test_row_indents_and_page_translation_do_not_supply_cut_coordinates():
    page=[folded.translate(row,17*i,43*i) for i,row in enumerate(rows())]
    shapes=folded.translate(pack_rows(page),51,97)
    source=prior.fixtures()[6]
    assert folded.decode_page(list(reversed(shapes)),seed=source['seed'],include_spellings=True)==source['source']


def test_two_crossing_lines_require_both_continuation_ports():
    candidates=[rows(i) for i in (2,6)]
    found=None
    for page in candidates:
        for index,row in enumerate(page):
            entry=folded._ports(row,'left')
            if entry and len(entry[1])>1:found=deepcopy(page),index,entry;break
        if found:break
    assert found is not None
    page,index,(x,ports)=found
    target=next(s for s in page[index] if s['kind']=='line' and
                (abs(s['x1']-x)<1e-5 or abs(s['x2']-x)<1e-5))
    page[index].remove(target)
    with pytest.raises(ValueError,match='count mismatch'):folded.unfold(pack_rows(page))


def test_wrong_slope_at_a_cut_cannot_be_read_as_a_valid_join():
    page=rows();entry=folded._ports(page[1],'left');assert entry
    edge,_=entry
    target=next(s for s in page[1] if s['kind']=='line' and abs(min(s['x1'],s['x2'])-edge)<1e-5)
    target['y1']+=3
    with pytest.raises(ValueError,match='slope|direction'):folded.unfold(pack_rows(page))


def test_folding_does_not_add_circles_or_split_their_pairs():
    for index in (0,6):
        assert sum(s['kind']=='circle' for row in rows(index) for s in row)==saved()[index]['circles']


@pytest.mark.parametrize('width',[0,-1,float('inf'),float('nan'),10])
def test_invalid_or_impossible_width_is_rejected(width):
    with pytest.raises(ValueError):folded.fold(from_svg(saved()[0]['row_svgs'][0]),width)


def test_wide_row_keeps_the_same_ink_without_continuation_marks():
    shapes=from_svg(saved()[0]['row_svgs'][0]);drawing=folded.fold(shapes,10000)
    assert len(drawing['row_shapes'])==1
    assert ink_key(drawing['row_shapes'][0])==ink_key(shapes)


def test_gap_midpoint_at_a_bend_still_has_a_legal_cut():
    from scripts.balanced_circle_script import circle,line,MEDIUM
    from scripts.kant_geometry_reader import read_geometry
    r=MEDIUM
    shapes=[circle(0,0,r),circle(2*r+192,64,r),line((r,0),(r+96,0)),
            line((r+96,0),(r+160,64)),line((r+160,64),(r+192,64))]
    read_geometry(shapes)
    assert folded._crossings([s for s in shapes if s['kind']=='line'],r+96)==[]
    drawing=folded.fold(shapes,250)
    assert len(drawing['row_shapes'])==2
    restored=folded.unfold(drawing['shapes'])
    assert len(restored)==1 and ink_key(restored[0])==ink_key(shapes)
