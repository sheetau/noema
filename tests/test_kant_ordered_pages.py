import pytest
from scripts import kant_ordered_pages as pages,kant_public_fragment as writing
from scripts.kant_incremental_dictionary import PublishedStatementReader,empty_document
from scripts.kant_lexical_context import LexicalContext
from scripts.kant_item_rows import vertical_bounds
from scripts.visible_syntax_geometry import from_svg
from scripts.check_kant_ordered_pages import fixtures,cases,checked,source


@pytest.mark.parametrize('index',range(len(cases())))
def test_document_recovers_across_physical_pages(index):
    result=checked(index);assert result['pages']>=2
    for svg in result['physical_page_svgs']:
        shapes=from_svg(svg)
        assert max(vertical_bounds(s)[1] for s in shapes)-min(vertical_bounds(s)[0] for s in shapes)<=400+1e-5


def test_missing_or_reversed_continuation_page_is_rejected():
    drawings=[from_svg(s) for s in checked(0)['physical_page_svgs']]
    for bad in (drawings[1:],drawings[:-1],list(reversed(drawings))):
        with pytest.raises(ValueError):pages.decode_pages(bad)


def test_empty_or_impossible_page_dimensions_rejected():
    with pytest.raises(ValueError):pages.paginate([],400)
    with pytest.raises(ValueError):pages.decode_pages([])
    with pytest.raises(ValueError):pages.decode_pages([[]])
    with pytest.raises(ValueError):pages.paginate([[dict(kind='circle',x=0,y=0,r=30)]],20)


def test_explicit_published_body_reader_keeps_its_dictionary_closed():
    published=LexicalContext(empty_document()).published();reader=PublishedStatementReader(published)
    value=dict(kind='assert',body=source.prior.prior.call('red',source.prior.prior.call('book')))
    drawing=writing.compile_statement(value,lexicon=reader.context)
    result=pages.decode_pages([drawing['shapes']],reader=reader)
    assert result==dict(empty_document(),statements=[value])
    assert reader.document['statements']==[]
    with pytest.raises(ValueError,match='requires statements'):
        reader.register(dict(kind='spelling',name='unused',parts=['book','town']))
    with pytest.raises(ValueError,match='reader or a seed'):
        pages.decode_pages([drawing['shapes']],reader=reader,seed=empty_document())
