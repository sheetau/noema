from copy import deepcopy
import pytest
from scripts import kant_public_fragment as writing,kant_incremental_dictionary as document
from scripts.kant_lexical_context import use_context
from scripts.visible_syntax_geometry import from_svg,to_svg
from scripts.visible_word_forms import Word,symbol
from scripts.kant_interleaved_layout import compile_stream
from scripts.check_kant_spelling_records import fixtures,cases,checked,preserved,preserved_count,spelling,prior


@pytest.mark.parametrize('index',range(len(cases())))
def test_spelling_mapping_and_native_document_from_one_svg(index):checked(index)


@pytest.mark.parametrize('index',range(preserved_count()))
def test_old_ink_keeps_its_exact_reading(index):preserved(index)


def initialized():
    reader=document.Reader();reader.read(from_svg(checked(0)['item_svgs'][0]))
    return reader


def test_spelling_is_learned_after_the_record_and_old_names_stay_available():
    row=fixtures()[2];reader=document.Reader()
    for svg in checked(2)['item_svgs'][:-1]:reader.read(from_svg(svg))
    name=row['native']['declarations'][0]['name']
    for record in row['spellings']:
        parts=tuple(symbol(Word('root',(p,)),writing.vocabulary()) for p in record['parts'])
        assert reader.context.spellings[parts]==name
    assert reader.context.full_spellings
    # The earlier page's statement still uses the first alias, even after the
    # second alias has become preferred for newly written text.
    assert reader.read(from_svg(checked(0)['item_svgs'][-1]))==row['native']['statements'][0]
    with pytest.raises(ValueError,match='Export recovered declarations'):reader.context.published()


@pytest.mark.parametrize('parts,error',[
    (['book'],'two to four'),
    (['round','give'],'collides with another'),
    (['round']*5,'two to four'),
])
def test_bad_mapping_does_not_change_dictionary_state(parts,error):
    reader=initialized();before=reader.result(True);name=fixtures()[0]['native']['declarations'][0]['name']
    with pytest.raises(ValueError,match=error):reader.register(spelling(name,parts))
    assert reader.result(True)==before


def test_future_name_and_root_rename_are_rejected():
    name=fixtures()[0]['native']['declarations'][0]['name'];reader=document.Reader()
    with pytest.raises(ValueError,match='not declared'):reader.register(spelling(name,['round','town']))
    with pytest.raises(ValueError,match='Cannot rename a root'):reader.register(spelling(prior.call('book')['symbol'],['round','town']))


def test_later_full_name_cannot_steal_an_existing_alias():
    reader=initialized();reader.read(from_svg(checked(0)['item_svgs'][1]));before=reader.result(True)
    new=prior.primitive(prior.name('round','town'),[],'individual')
    drawing=writing.compile_declaration(new,lexicon=reader.context,full_names=True)
    with pytest.raises(ValueError,match='collides with another'):reader.read(from_svg(to_svg(drawing['shapes'])))
    assert reader.result(True)==before


def test_duplicate_record_and_post_statement_record_are_rejected():
    reader=initialized();svg=checked(0)['item_svgs'][1];reader.read(from_svg(svg))
    with pytest.raises(ValueError,match='already registered'):reader.read(from_svg(svg))
    reader.read(from_svg(checked(0)['item_svgs'][-1]))
    with pytest.raises(ValueError,match='follows a statement'):
        reader.register(spelling(fixtures()[0]['native']['declarations'][0]['name'],['round','home']))


@pytest.mark.parametrize('change,error',[
    ('target-end','Missing spelling target end'),('final-end','Missing full name end'),
    ('type-part','Full name requires root components'),('one-part','two to four'),('branch','cannot carry branches'),
])
def test_malformed_record_is_rejected_from_geometry(change,error):
    reader=initialized();record=fixtures()[0]['spellings'][0]
    with use_context(reader.context):events=writing.events(record)
    first=next(i for i,e in enumerate(events) if e['token']=='types_end')
    if change=='target-end':events.pop(first)
    elif change=='final-end':events.pop()
    elif change=='type-part':events[first+1]['token']='type_number'
    elif change=='one-part':events.pop(-2)
    else:events[first+1]['side']=[dict(token=prior.call('book')['symbol'],side=None,depth=0,path=[])]
    drawing=compile_stream(events,contacts=False)
    with pytest.raises(ValueError,match=error):reader.read(from_svg(to_svg(drawing['shapes'])))
