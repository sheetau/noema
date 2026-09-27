import copy
import xml.etree.ElementTree as ET
import pytest
from noema import parse, format_graph, normalize, SemanticError
from noema.language import from_graph, to_graph, ROOTS, EDITION
from noema.render import render
from noema.semantics import make_graph


def p(text):
    return parse("noema b b\n" + text)


def test_short_sentence_matches_original_graph():
    expected = make_graph("ba", {"agent": {"concept": "aa"}, "patient": {"concept": "ab"}})
    actual = p("ih i mu j si.")
    assert actual == from_graph(expected)
    assert to_graph(actual) == expected
    assert format_graph(actual) == "noema b b\nih i mu j si."


def test_each_graph_value_is_lossless():
    for polarity in ("affirmed", "negated", "unspecified"):
        for time in ("unspecified", "past", "present", "future", "yesterday", "today", "tomorrow"):
            g = make_graph("bd", {"agent": {"concept": "ag", "name": '蒼 "Aki"'}, "patient": {"concept": "af", "quantity": 37},
                                  "recipient": {"concept": "ac"}, "location": {"concept": "ah"}}, polarity, time)
            assert to_graph(parse(format_graph(from_graph(g)))) == g


def test_discourse_identity_and_alpha_renaming():
    a = p("ih i mu o dog j si o cat. no j p cat i p dog.")
    b = p("ih i mu o x j si o y. no i p x j p y.")
    assert a == b
    assert len(a["entities"]) == 2
    assert parse(format_graph(a)) == a
    distinct = p("ih i mu j si. no i mu j si.")
    assert len(distinct["entities"]) == 4 and distinct != a


def test_reference_is_not_inferred_from_same_name():
    a = p('po i qo n "Aki". wm i qo n "Aki".')
    assert len(a["entities"]) == 2
    b = p('po i qo n "Aki" o person. wm i p person.')
    assert len(b["entities"]) == 1


def test_questions_requests_and_omission_are_distinct():
    values = [p(s) for s in ("ih j si.", "b ih j si.", "b ih i c j si.", "d ih j si.")]
    assert len({format_graph(v) for v in values}) == 4
    assert values[0]["utterances"][0]["content"]["roles"]["agent"] is None
    assert values[2]["utterances"][0]["content"]["roles"]["agent"] == {"query": True}
    for v in values[1:]:
        with pytest.raises(SemanticError):
            to_graph(v)


def test_negation_and_connective_scope_are_not_collapsed():
    sentences = ["w [ po i mu ] [ wm i si ].", "u [ w [ po i mu ] [ wm i si ] ].",
                 "w [ u po i mu ] [ wm i si ].", "x [ po i mu ] [ wm i si ].",
                 "y [ po i mu ] [ wm i si ].", "u u po i mu."]
    normalized = [p(s) for s in sentences]
    assert len({format_graph(d) for d in normalized}) == len(sentences)
    for d in normalized:
        assert parse(format_graph(d)) == d
        with pytest.raises(SemanticError):
            to_graph(d)


def test_date_number_and_name_literals():
    d = p('q "2026-09-27" ku i qo n "Aki" k fo j jx m ba.')
    assert d["entities"][1]["quantity"] == 32
    assert to_graph(d)["nodes"][0]["time"] == {"kind": "date", "value": "2026-09-27"}
    assert parse(format_graph(d)) == d


@pytest.mark.parametrize("text", [
    "", "ih i mu", "ih i mu i si.", "ih i p dog.", "ih i mu o a j si o a.",
    "ih i c.", "d ih i c.", "po j si.", "ih l mu.", "ih i qo.",
    "ih i mu m ab.", "ih i mu m b m c.", "t s ih i mu.",
    "q \"2026-99-99\" ih i mu.", "w [ po i mu ] [ wm i si .", "po [i mu].",
    "ih i zz.", "b b po i mu.", "[u] po i mu.",
])
def test_invalid_language_is_rejected(text):
    with pytest.raises(SemanticError):
        p(text)


def test_strict_document_validation():
    d = p("ih i mu j si.")
    invalid = copy.deepcopy(d)
    invalid["utterances"][0]["content"]["extra"] = "must not be dropped"
    with pytest.raises(SemanticError):
        normalize(invalid)
    invalid = copy.deepcopy(d)
    invalid["entities"].append({**invalid["entities"][0], "id": "unused"})
    with pytest.raises(SemanticError):
        normalize(invalid)


def test_vocabulary_markers_and_svg_metadata():
    assert len(set(ROOTS.values())) == len(ROOTS)
    assert not set(ROOTS.values()) & set(EDITION["markers"])
    d = p("y [ ih i mu o dog j si ] [ po i p dog ].")
    root = ET.fromstring(render(format_graph(d)))
    assert parse(root.find("{http://www.w3.org/2000/svg}metadata").text) == d
