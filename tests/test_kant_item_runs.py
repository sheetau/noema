import pytest
from scripts import kant_item_runs as runs,kant_public_fragment as writing
from scripts.kant_incremental_dictionary import Reader
from scripts.kant_interleaved_layout import compile_stream
from scripts.visible_syntax_geometry import from_svg,to_svg
from scripts.check_kant_item_runs import fixtures,cases,checked,preserved,preserved_count,prior


@pytest.mark.parametrize('index',range(len(cases())))
def test_connected_items_recovered_without_item_metadata(index):checked(index)


@pytest.mark.parametrize('index',range(preserved_count()))
def test_preserved_ink_keeps_its_exact_native_reading(index):preserved(index)


def test_cross_item_longest_match_needs_a_real_seam():
    row=next(r for r in fixtures() if r['key']=='lexical-junction')
    stream,_=runs.item_events(row['records'],Reader(),multiple=True)
    seams=[i for i,e in enumerate(stream) if e.get('lexical_seam')]
    assert len(seams)==1
    stream[seams[0]].pop('lexical_seam')
    drawing=compile_stream(stream)
    with pytest.raises(ValueError):writing.decode_run(from_svg(to_svg(drawing['shapes'])),reader=Reader())


def test_successful_run_returns_new_reader_and_does_not_mutate_start():
    reader=Reader();before=reader.result(True)
    index=next(i for i,r in enumerate(fixtures()) if r['key']=='two-spellings')
    pending,items=writing.decode_run(from_svg(checked(index)['row_svgs'][0]),reader=reader)
    assert items==fixtures()[index]['records']
    assert pending.result(True)==fixtures()[index]['source']
    assert reader.result(True)==before


def test_trailing_invalid_item_does_not_publish_earlier_declarations():
    row=next(r for r in fixtures() if r['key']=='later-definition')
    stream,_=runs.item_events(row['records'][:2],Reader(),multiple=True)
    stream.append(dict(token='bound0',side=None,path=[],depth=0))
    drawing=compile_stream(stream)
    reader=Reader();before=reader.result(True)
    with pytest.raises(ValueError,match='Unbound'):
        writing.decode_run(from_svg(to_svg(drawing['shapes'])),reader=reader)
    assert reader.result(True)==before


def test_binder_does_not_leak_to_the_next_statement():
    red=prior.prior.call('red',prior.prior.variable('x'))
    first=prior.prior.canonical([], [dict(kind='assert',body=dict(kind='forall',variable='x',sort='individual',body=red))])['statements'][0]
    stream,_=runs.item_events([first],Reader(),multiple=True)
    stream += [dict(token=prior.prior.call('red',prior.prior.call('book'))['symbol'],side=None,path=[],depth=0),
               dict(token='bound0',side=None,path=[],depth=0)]
    drawing=compile_stream(stream)
    with pytest.raises(ValueError,match='Unbound'):
        writing.decode_run(from_svg(to_svg(drawing['shapes'])),reader=Reader())


def test_no_generic_start_marker_or_unnecessary_seam():
    row=fixtures()[0];stream,_=runs.item_events(row['records'],Reader(),multiple=True)
    for e in stream:
        assert e['token'] not in ('full_name','primitive','definition','spelling')
    assert not any(e.get('lexical_seam') for e in stream)


def test_bounded_runs_reject_empty_and_oversized_input_before_layout():
    with pytest.raises(ValueError,match='at least one'):runs.item_events([],Reader())
    with pytest.raises(ValueError,match='512 events'):runs.item_events([fixtures()[0]['records'][0]]*260,Reader())
