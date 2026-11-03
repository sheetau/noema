import pytest
from scripts import kant_paragraph_pages as layout
from scripts.check_kant_paragraph_pages import build_report, fixtures
from scripts.kant_item_rows import split_rows, vertical_bounds, ROW_GAP
from scripts.visible_syntax_geometry import from_svg


def test_real_prefix_preserves_paragraph_order_and_joins_multiple_saved_items():
    row = build_report()['diagnostics'][0]
    assert row['exact'] and row['items'] == 4
    assert [f['items'] for f in row['flows']] == [1, 3]
    assert [f['paragraph'] for f in row['flows']] == [0, 1]
    assert row['breaks'] == []
    assert sum(row['paragraph_rows']) == row['rows']


def test_unavailable_junction_and_budget_close_only_complete_items():
    rows = build_report()['diagnostics']
    assert [f['items'] for f in rows[1]['flows']] == [1, 1]
    assert rows[1]['breaks'][0]['reason'] == 'unchanged-ink-junction-unavailable'
    assert [f['items'] for f in rows[2]['flows']] == [2, 1]
    assert rows[2]['breaks'][0]['reason'] == 'flow-circle-budget'
    assert all(r['exact'] for r in rows)


def test_page_boundaries_and_extra_paragraph_whitespace_are_geometric():
    row = [dict(kind='circle', x=0., y=32., r=10.)]
    drawings, counts = layout.physical_pages([row, row, row], [0, 2], 1000.)
    assert counts == [3]
    recovered = split_rows(drawings[0])
    gaps = [min(vertical_bounds(s)[0] for s in b) - max(vertical_bounds(s)[1] for s in a)
        for a, b in zip(recovered, recovered[1:])]
    assert gaps == [ROW_GAP, ROW_GAP+64.]
    for result in build_report()['diagnostics']:
        for svg, count in zip(result['page_svgs'], result['page_row_counts']):
            shapes = from_svg(svg)
            assert len(split_rows(shapes)) == count
            assert max(vertical_bounds(s)[1] for s in shapes)-min(vertical_bounds(s)[0] for s in shapes) <= 900.+1e-5


def test_invalid_input_does_not_turn_into_a_layout_break():
    fixture = fixtures()[1]
    with pytest.raises(ValueError):
        layout.compose([[[]]], reader=fixture['reader'], row_width=400., page_height=900.)
    with pytest.raises(ValueError, match='complete item exceeds'):
        layout.compose(fixture['paragraphs'], reader=fixture['reader'], row_width=400., page_height=900., circle_budget=1)
    with pytest.raises(ValueError, match='Empty'):
        layout.compose([[]], reader=fixture['reader'], row_width=400., page_height=900.)
