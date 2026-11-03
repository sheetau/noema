"""Reuse the saved overlap ink at item junctions and line continuations."""
from scripts.check_kant_root_overlap import OUT, fixture, cases, build_report
from scripts.kant_incremental_dictionary import PublishedStatementReader
from scripts.kant_saved_item_join import join, endpoints
from scripts.kant_folded_flow import fold, decode_page
from scripts.visible_syntax_geometry import from_svg, to_svg


def test_saved_overlaps_survive_join_and_fold_with_a_published_dictionary():
    build_report()  # Content hashes include the actual saved SVGs.
    context,_=fixture()
    reader=PublishedStatementReader(context.published())
    before=reader.result(True)
    rows=cases()[:2]
    shapes=[from_svg((OUT/(key+'.svg')).read_text(encoding='utf-8')) for key,_ in rows]
    assert [endpoints(s)[2] for s in shapes]==['wrbookzq','wrabovezq']
    joined=join(shapes,reader=reader)
    page=fold(joined['shapes'],max_width=400)
    assert len(page['row_shapes'])>1
    recovered=decode_page(list(reversed(from_svg(to_svg(page['shapes'])))),reader=reader,include_spellings=True)
    assert recovered['native']['statements']==[source for _,source in rows]
    assert reader.result(True)==before
