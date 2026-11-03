import pytest
from scripts.check_kant_readable_flow import checked,page,matches_flow
from scripts.check_kant_geometry_reader import source_entries,observed
from scripts.kant_geometry_reader import read_geometry
from scripts.kant_flow_reader import decompose_flow
from scripts import balanced_circle_script as b
from scripts.visible_syntax_geometry import to_svg,from_svg


@pytest.mark.parametrize('index',range(40))
def test_actual_statement_svg_recovers_main_flow_and_terminal_dependencies(index):
    row=checked(index)
    assert matches_flow(row['flow'],row['compiled'])
    original=source_entries()[index]['compiled']
    assert row['compiled']['source']==original['source']
    assert row['compiled']['reference_order']==original['reference_order']
    assert row['compiled']['opening']==original['opening']


def test_old_counterexample_and_local_repair():
    assert not checked(0)['original_flow_matches']
    assert len(checked(0)['flow']['main'])==8
    assert sum(map(len,checked(0)['flow']['side']))==1


def test_same_content_page_keeps_original_scale_and_row_count():
    p=page()
    assert p['rows']==18
    assert p['scale']==p['original_scale']==.53


def test_reader_does_not_call_renderer_or_need_group_metadata(monkeypatch):
    import scripts.kant_readable_flow as writer
    shapes=checked(0)['compiled']['shapes']
    monkeypatch.setattr(writer,'compile_expression',lambda *a,**k:pytest.fail('Reader called writer'))
    result=decompose_flow(read_geometry(from_svg(to_svg(shapes))))
    assert result==checked(0)['flow']


def test_independent_non_symmetric_terminal_dependency():
    shapes=[b.circle(0,32,b.MEDIUM),b.circle(150,32,b.MEDIUM),b.circle(75,0,b.SMALL),
        b.line((b.MEDIUM,32),(150-b.MEDIUM,32)),b.line((75,32),(75,b.SMALL))]
    r=decompose_flow(read_geometry(shapes))
    assert [r['nuclei'][i]['center'] for i in r['main']]==[[0,32],[150,32]]
    assert [r['nuclei'][i]['center'] for i in r['side'][0]]==[[75,0]]


def test_ambiguous_same_column_root_is_rejected():
    shapes=[b.circle(0,0,b.MEDIUM),b.circle(0,64,b.MEDIUM),
        b.line((0,b.MEDIUM),(0,64-b.MEDIUM))]
    with pytest.raises(ValueError,match='initial nucleus'):
        decompose_flow(read_geometry(shapes))
