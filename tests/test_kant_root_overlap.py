from functools import lru_cache
import pytest
from scripts import kant_public_fragment as writing
from scripts.kant_root_overlap import pair_token, _templates
from scripts.check_kant_root_overlap import build_report
from scripts.check_visible_syntax import call
from scripts.visible_syntax_geometry import from_svg, to_svg

report=lru_cache(maxsize=1)(build_report)


def test_legal_inventory_is_recovered_without_changing_root_order():
    rows=report()['root_variants']
    assert len(rows)==20
    assert len({(r['first'],r['second']) for r in rows})==14
    assert all(r['exact'] for r in rows)
    assert len(writing.table())==94
    for first,second in [('wrbookzq','wrabovezq'),('wrgivezq','wrbookzq')]:
        assert _templates.__wrapped__(first,second)==_templates(first,second)


def test_real_overlapping_glyph_cannot_be_two_separate_words():
    glyph=writing.forms(pair_token('wrredzq','wrbookzq'))[0]
    with pytest.raises(ValueError,match='one lexical word'):
        writing.decode(from_svg(to_svg(glyph['shapes'])))
    source=dict(kind='assert',body=call('red',call('book')))
    before=writing.compile_statement(source)
    after=writing.compile_statement(source,overlap=True)
    assert after['shapes']==before['shapes']
    assert writing.decode(after['shapes'])==source


def test_scope_quote_argument_order_and_branch_reading_survive():
    rows={r['key']:r for r in report()['cases']}
    assert set(rows)=={'two-pairs','reverse-pair','swapped','bound','quoted','branch'}
    assert all(r['exact'] and r['overlaps']>0 for r in rows.values())
    assert all(r['before_circles']==r['circles'] for r in rows.values())
    assert rows['two-pairs']['syntax_sha256']!=rows['swapped']['syntax_sha256']
    assert rows['branch']['branches']>0


def test_actual_source_and_existing_page_obey_the_same_strict_rule():
    result=report();body=result['actual_body']
    assert body['exact'] and body['overlaps']>0
    assert body['circles']==body['before_circles']
    assert body['width']<body['before_width']
    assert result['shared_argument_page']==dict(svg_count=24,circles=244,legal=True)
