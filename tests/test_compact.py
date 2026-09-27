import json
from pathlib import Path
import re
import subprocess
import sys
import pytest

from noema.grammar import parse, format_graph, notation_of
from noema.language import normalize_document
from noema.render import render
from noema.script import encode, decode
from noema.semantics import SemanticError


@pytest.mark.parametrize("compact,full", [
    ("e:ih mu si.", "noema e e ih i mu j si."),
    ("d:ih si mu.", "noema d d ih i si j mu."),
    ("c:ih j si.", "noema c c ih j si."),
    ("b:po mu.", "noema b b po i mu."),
    ("e:u[t ih mu si].", "noema e e u [ t ih i mu j si ]."),
    ("e:b ih c si.", "noema e e b ih i c j si."),
    ("e:d 6-sam fo maj.", "noema e e d 6-sam i fo j maj."),
    ("e:po mu-sai m c.", "noema e e po i mu-sai m c."),
    ("e:v 5-sai maj.", "noema e e v 5-sai i maj."),
    ('e:q"2031-02-03" po qo n"A \\"B\\"".', 'noema e e q "2031-02-03" po i qo n "A \\"B\\"".'),
    ("e:y[wm mu o a][po p a].", "noema e e y [ wm i mu o longref ] [ po i p longref ]."),
    ("e:ih mu o a si.\nih p a si.", "noema e e ih i mu o a j si. ih i p a j si."),
    ("e:vaf fo jx l laa z tp 2 lac 3 max 4 zr.", "noema e e vaf i fo j jx l laa z tp 2 lac 3 max 4 zr."),
])
def test_compact_is_the_same_versioned_meaning(compact, full):
    expected = parse(full)
    assert parse(compact) == expected
    assert format_graph(expected, "compact") == compact
    assert parse(format_graph(expected, "full")) == expected
    for alphabet in ("v1", "v2"):
        native = encode(compact, alphabet)
        assert notation_of(native) == "compact" and len(native) == len(compact)
        assert parse(native) == expected
        assert decode(native) == compact
        assert decode(native, "full") == format_graph(expected)
    assert parse(encode(full, "v2", "compact")) == expected


def test_omission_explicit_roles_and_placeholders_never_shift_roles():
    expected = parse("noema e e ih j si.")
    assert parse("e:ih ? si.") == expected
    assert format_graph(expected, "compact") == "e:ih j si."
    assert parse("e:ih mu.") != expected
    assert parse("e:ih i mu j si.") == parse("e:ih mu si.")
    assert parse("e:ih j si i mu.") == parse("e:ih mu si.")
    assert parse("e:po ?.") == parse("e:po.")
    for text in ("e:ih j si mu.", "e:ih mu si mu.", "e:ih mu i si.", "e:po mu si.",
                 "e:ih mu si k fo.", "e:ih mu si l mu.", "e:po p a.", "e:po mu o a. po si o a.",
                 "e:ih c si.", "e:5-6-sam maj.", "e:po mu-5-sai.", "d:5-sam maj.",
                 "b:po maa.", "a:po mu.", "g:po mu.", "e:ih mu si. garbage", "e :ih mu si."):
        with pytest.raises(SemanticError):
            parse(text)
    with pytest.raises(SemanticError):
        parse("noema e e ih mu si.")  # The old notation keeps its old grammar.


def test_literals_large_counts_scope_and_identity_survive():
    value = 9007199254740993
    graph = parse('noema e e u [ y [ wm i qo n " e: a [ ] \\\" \\n "] [ po i mu ] ].')
    graph["entities"][0]["quantity"] = value
    text = format_graph(graph, "compact")
    assert parse(text) == normalize_document(graph)
    assert parse(encode(text, "v2")) == normalize_document(graph)
    assert parse(text)["entities"][0]["name"] == graph["entities"][0]["name"]
    shared = parse("e:ih mu o a p a.")
    separate = parse("e:ih mu mu.")
    assert shared != separate
    assert parse(format_graph(shared, "compact")) == shared
    assert parse("e:u[u[po mu]].") != parse("e:po mu.")


def test_document_examples_roundtrip_in_both_notations():
    roots = [Path("examples"), Path("docs")]
    documents = [p.read_text(encoding="utf-8") for p in roots[0].glob("*.noema")]
    for path in roots[1].glob("*.md"):
        documents.extend(re.findall(r"```(?:noema|text)\s*\n(noema\s+[bcdef]\s+[bcdef]\b[\s\S]*?)\n```", path.read_text(encoding="utf-8")))
        documents.extend(re.findall(r"```(?:noema|text)\s*\n([bcdef]:[\s\S]*?)\n```", path.read_text(encoding="utf-8")))
    count = 0
    for text in documents:
        graph = parse(text)
        if graph["schema_version"] == "0.1":
            continue
        compact = format_graph(graph, "compact")
        assert parse(compact) == graph
        assert parse(decode(encode(compact, "v2"))) == graph
        assert len(compact) <= len(format_graph(graph))
        count += 1
    assert count >= 30


def test_length_report_matches_actual_documents():
    from scripts.measure_compact import measure
    assert measure("data/compact-length-v1.json") == json.loads(Path("reports/compact-length-v1.json").read_text(encoding="utf-8"))


def test_svg_cli_and_inspection_preserve_short_notation(tmp_path):
    from noema.editor import inspect_text
    text = "e:u[5-sam maj]."
    inspected = inspect_text(text)
    assert inspected["canonical"] == text and decode(inspected["script"]) == text
    svg = render(text, alphabet="v2")
    assert f"<metadata>{text}</metadata>" in svg
    assert "noema e e" not in svg
    assert "noema e e" in render(text, notation="full")
    source = tmp_path / "graph.json"
    source.write_text(json.dumps(parse(text)), encoding="utf-8")
    result = subprocess.run([sys.executable, "-S", "-m", "noema", "format", "--input", str(source), "--notation", "compact"],
                            check=True, capture_output=True, text=True, encoding="utf-8")
    assert result.stdout.strip() == text
    result = subprocess.run([sys.executable, "-S", "-m", "noema", "script", "--text", text, "--decode", "--notation", "full"],
                            check=True, capture_output=True, text=True, encoding="utf-8")
    assert result.stdout.strip() == format_graph(parse(text))
