from pathlib import Path
import pytest
from scripts import check_visible_senses_library as check
from scripts.visible_senses_book import compile_book
from scripts.visible_syntax_geometry import from_svg,to_svg


def test_report_inspects_saved_geometry_without_rendering(monkeypatch):
    def no_render(*a,**kw):raise AssertionError('Artifact inspection must read SVG shapes')
    monkeypatch.setattr(check,'compile_book',no_render)
    row=check.saved_case('senses-selection')
    assert row['result']==check.expected('senses-selection')
    assert row['glyphs']==sum(p['glyphs'] for p in row['pages'])
    assert 1<len(row['pages'])<=8


@pytest.mark.parametrize('change',['missing','extra','geometry','valid-other-document'])
def test_saved_page_errors_are_not_hidden_by_previous_test_results(tmp_path,monkeypatch,change):
    original=check.OUT/'dictionary-1.svg';text=original.read_text(encoding='utf-8')
    monkeypatch.setattr(check,'OUT',tmp_path)
    if change!='missing':(tmp_path/'dictionary-1.svg').write_text(text,encoding='utf-8')
    if change=='extra':(tmp_path/'dictionary-3.svg').write_text(text,encoding='utf-8')
    elif change=='geometry':
        shapes=from_svg(text);shapes.pop()
        (tmp_path/'dictionary-1.svg').write_text(to_svg(shapes),encoding='utf-8')
    elif change=='valid-other-document':
        other=check.vocabulary().encode(check.doc(names=['home']))
        page=compile_book(other,check.vocabulary())[0]
        (tmp_path/'dictionary-1.svg').write_text(to_svg(page['shapes']),encoding='utf-8')
    with pytest.raises(ValueError):check.saved_case('dictionary')
