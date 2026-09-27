from pathlib import Path
import pytest
from noema import parse, format_graph
from noema.script import encode, decode, TO_SCRIPT, SCRIPT_START, ALPHABET_SPEC


def test_script_roundtrip_preserves_literal_unicode():
    original = 'noema b b po i qo n "Aki\\\"犬\ue001".'
    encoded = encode(original)
    assert encoded.startswith(TO_SCRIPT['n'])
    assert 'Aki\\\"犬\ue001' in encoded
    assert parse(encoded) == parse(original)
    assert decode(encoded) == format_graph(parse(original))


def test_script_supports_both_language_editions():
    source = Path(__file__).parent.parent / "examples/chase.noema"
    original = source.read_text(encoding="utf-8")
    assert parse(encode(original)) == parse(original)


def test_font_mapping_bounds_and_reproducibility(tmp_path):
    pytest.importorskip("fontTools")
    from fontTools.ttLib import TTFont
    from scripts.build_font import build
    a, b = tmp_path / "a.ttf", tmp_path / "b.ttf"
    build(a)
    build(b)
    assert a.read_bytes() == b.read_bytes()
    font = TTFont(a)
    cmap = font.getBestCmap()
    assert set(cmap) == {32} | set(range(SCRIPT_START, SCRIPT_START + 32))
    glyphs = [font["glyf"][cmap[SCRIPT_START + i]] for i in range(32)]
    assert all(g.numberOfContours > 0 and 0 <= g.xMin < g.xMax < 816 and 0 <= g.yMin < g.yMax < 860 for g in glyphs)
    assert len(set(ALPHABET_SPEC["paths"])) == 32
