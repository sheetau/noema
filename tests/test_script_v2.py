import json
from pathlib import Path
import pytest
from noema.grammar import parse, format_graph
from noema.script import encode, decode, transcribe, FUNCTIONAL_SPEC, SCRIPT_MAPS
from noema.render import render
from noema.semantics import SemanticError


def test_grammar_families_share_meaningful_components():
    from scripts.build_alphabet_v2 import build
    spec = FUNCTIONAL_SPEC
    assert spec == build()
    assert set(spec["letters"]) == set('abcdefghijklmnopqrstuvwxyz234567')
    for earlier, later, extra in (("e", "r", "past_day"), ("f", "s", "present_day"), ("g", "t", "future_day"), ("5", "6", "cause")):
        assert spec["letters"][earlier]["family"] == spec["letters"][later]["family"]
        assert spec["letters"][later]["features"] == spec["letters"][earlier]["features"] + [extra]
    assert len({path for path in spec["paths"]}) == 32


def test_both_alphabets_and_mixed_input_preserve_quotes_scope_and_quantities():
    text = 'noema e e u [ t 6-sam i qo n "a\\\"\ue001\ue101\\\\5" j maj m bab o door ]. b sam i p door.'
    graph = parse(text)
    legacy, current = encode(text, "v1"), encode(text, "v2")
    assert current.startswith(chr(0xE100 + 13))
    assert 'a\\\"\ue001\ue101\\\\5' in current
    assert current != legacy and parse(current) == graph == parse(legacy)
    assert decode(current) == decode(legacy) == format_graph(graph)
    assert transcribe(legacy, alphabet="v2") == current
    assert transcribe(current, alphabet="v1") == legacy
    mixed = current.replace(SCRIPT_MAPS["v2"]["s"], SCRIPT_MAPS["v1"]["s"])
    assert parse(mixed) == graph
    with pytest.raises(SemanticError, match="alphabet"):
        encode(text, "v3")


def test_all_written_examples_survive_both_scripts_and_svg_is_explicit():
    for path in Path("examples").glob("*.noema"):
        text = path.read_text(encoding="utf-8")
        assert parse(encode(text, "v2")) == parse(text)
        assert parse(encode(encode(text, "v2"), "v1")) == parse(text)
    text = 'noema e e 5-sam i maj.'
    assert render(text, alphabet="v1") != render(text, alphabet="v2")
    assert FUNCTIONAL_SPEC["paths"][0] in render(text, alphabet="v2")


def test_font_keeps_all_letters_visible_at_small_sizes():
    pytest.importorskip("PIL")
    from scripts.proof_alphabet_v2 import measure
    report = measure("noema/resources/NoemaWritten.ttf")
    assert all(v["distinct"] == 32 and v["nonempty"] for v in report["measures"].values())
