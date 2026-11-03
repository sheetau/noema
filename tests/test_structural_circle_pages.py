from copy import deepcopy
import pytest

from scripts.check_structural_circle import cases
from scripts.structural_circle import to_svg,from_svg
from scripts.structural_circle_pages import compile_pages,decode_pages


@pytest.mark.parametrize('payload',[1,3,7,19,96,512])
def test_page_breaks_inside_words_types_quotes_and_binders(payload):
    document=cases()[8][2]
    pages=compile_pages(document,payload=payload)
    assert decode_pages(from_svg(to_svg(p['shapes'])) for p in pages)==document


@pytest.mark.parametrize('case',[0,2,5,6,18,25,39])
def test_multiple_expression_families_with_continued_scope(case):
    d=cases()[case][2]
    assert decode_pages(p['shapes'] for p in compile_pages(d,payload=11))==d


@pytest.mark.parametrize('mutation',['missing','duplicate','reversed','extra','mixed','cut'])
def test_page_sequence_corruption_is_rejected(mutation):
    pages=[p['shapes'] for p in compile_pages(cases()[8][2],payload=19)]
    if mutation=='missing':pages.pop(1)
    elif mutation=='duplicate':pages.insert(1,pages[0])
    elif mutation=='reversed':pages.reverse()
    elif mutation=='extra':pages.append(pages[-1])
    elif mutation=='mixed':pages[1]=compile_pages(cases()[5][2],payload=19)[1]['shapes']
    else:pages=pages[:-1]
    with pytest.raises(ValueError):decode_pages(pages)


def test_incorrect_local_branch_is_rejected_after_global_parsing():
    from scripts.structural_circle import read_geometry,render_tree,Vocabulary
    v=Vocabulary();pages=[p['shapes'] for p in compile_pages(cases()[8][2],payload=19)]
    tokens,tree=read_geometry(pages[0],v)
    chain=[[i+1] if i+1<len(tokens) else [] for i in range(len(tokens))]
    pages[0]=render_tree(tokens,chain,v)['shapes']
    with pytest.raises(ValueError,match='continued grammatical scopes'):decode_pages(pages,v)


def test_missing_final_marker_is_not_inferred_from_file_order():
    from scripts.structural_circle import read_geometry,render_tree,Vocabulary
    from scripts.structural_circle_pages import mark,CONTINUE
    v=Vocabulary();pages=[p['shapes'] for p in compile_pages(cases()[8][2],payload=19)]
    tokens,tree=read_geometry(pages[-1],v);tokens[-2:]=mark(CONTINUE)
    pages[-1]=render_tree(tokens,tree,v)['shapes']
    with pytest.raises(ValueError,match='final/continuation'):decode_pages(pages,v)


def test_shared_expression_can_span_frames_without_scope_change():
    from scripts.check_visible_syntax import doc,assertion,logic,num
    expression=logic('equal',num(7,3),num(11,5))
    d=doc(assertion(logic('and',expression,expression)))
    assert decode_pages(p['shapes'] for p in compile_pages(d,payload=7,sharing=True))==d
