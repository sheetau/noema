import copy
import json
import random
import xml.etree.ElementTree as ET
import pytest
from noema import parse, format_graph, normalize, SemanticError
from noema.grammar import number_word, read_number
from noema.render import render, glyph_path, alphabet_svg
from noema.semantics import make_graph, ALPHABET


def chase():
    return make_graph("ba", {"agent": {"concept": "aa"}, "patient": {"concept": "ab"}})


def test_manual_noema_and_role_order():
    text = 'noema a a { patient z y; en y ab ? ?; ev z ba pos unspec; agent z x; en x aa ? ?; }'
    assert parse(text) == chase()
    assert parse(format_graph(parse(text))) == chase()


def test_graph_alpha_equivalence_and_shared_references():
    g = chase()
    g["relations"][1]["target"] = g["relations"][0]["target"]
    g["nodes"].pop()
    g["nodes"].reverse()
    g["relations"].reverse()
    assert parse(format_graph(g)) == normalize(g)
    assert len(normalize(g)["nodes"]) == 2


def test_distinctions_and_omission():
    g = chase()
    swapped = make_graph("ba", {"agent": {"concept": "ab"}, "patient": {"concept": "aa"}})
    negative = make_graph("ba", {"agent": {"concept": "aa"}, "patient": {"concept": "ab"}}, "negated")
    counted = make_graph("ba", {"agent": {"concept": "aa", "quantity": 2}, "patient": {"concept": "ab"}})
    tomorrow = make_graph("ba", {"agent": {"concept": "aa"}, "patient": {"concept": "ab"}}, time="tomorrow")
    missing = make_graph("ba", {"patient": {"concept": "ab"}})
    assert len({format_graph(x) for x in (g, swapped, negative, counted, tomorrow, missing)}) == 6
    assert parse(format_graph(missing))["relations"][0]["target"] is None
    assert parse(format_graph(tomorrow))["nodes"][0]["time"] == {"kind": "relative", "value": "tomorrow"}


def test_roundtrip_varied_graphs():
    rng = random.Random(42)
    for _ in range(100):
        graph = make_graph("bd", {"agent": {"concept": "ag", "name": rng.choice(['明日', 'a"b\\c', '<script>&', '😀\nAki'])},
                                  "patient": {"concept": "af", "quantity": rng.choice([0, 1, 32, 10**18, None])},
                                  "recipient": {"concept": "ac"}, "location": {"concept": "ah"}},
                           rng.choice(["affirmed", "negated", "unspecified"]), rng.choice(["tomorrow", "past", "unspecified"]))
        assert parse(format_graph(graph)) == normalize(graph)


def test_absolute_date_and_state():
    g = make_graph("bf", {"agent": {"concept": "ac"}})
    g["nodes"][0]["time"] = {"kind": "date", "value": "2026-09-27"}
    assert parse(format_graph(g)) == g


@pytest.mark.parametrize("text", [
    '', 'noema a b {}', 'noema a a {}',
    'noema a a { ev e ba pos unspec; agent e x; }',
    'noema a a { ev e ba pos unspec; agent e ?; agent e ?; }',
    'noema a a { ev e ba pos unspec; } trailing',
    'noema a a { ev e aa pos unspec; }',
    'noema a a { en x zz ? ?; ev e ba pos unspec; }',
    'noema a a { ev e be pos unspec; en x aa ? ?; patient e x; }',
    'noema a a { ev e ba pos unspec; en x aa ? ?; location e x; }',
    'noema a a { ev e ba pos unspec; en x aa ab ?; agent e x; }',
    'noema a a { ev e ba pos date "2026-99-99"; }',
    'noema a a { ev e ba pos unspec; ev x bb pos unspec; }',
    'noema a a { ev e ba pos unspec; en x aa ? ?; }',
])
def test_reject_invalid(text):
    with pytest.raises((SemanticError, ValueError)):
        parse(text)


@pytest.mark.parametrize("mutation", [lambda g: g.update(extra=1), lambda g: g["nodes"][1].update(quantity=True), lambda g: g["nodes"][1].update(name=""), lambda g: g["nodes"].append(copy.deepcopy(g["nodes"][1]))])
def test_no_silent_loss(mutation):
    g = chase()
    mutation(g)
    with pytest.raises(SemanticError):
        normalize(g)


def test_glyphs_svg_and_literal_escaping():
    assert len(ALPHABET) == len(set(glyph_path(i) for i in range(32))) == 32
    graph = make_graph("be", {"agent": {"concept": "ag", "name": '<script>犬&"'}})
    svg = render(format_graph(graph), columns=8)
    root = ET.fromstring(svg)
    assert parse(root.find('{http://www.w3.org/2000/svg}metadata').text) == graph
    assert '<script>' not in svg
    ET.fromstring(alphabet_svg())
    for n in (0, 31, 32, 1024, 10**30):
        assert read_number(number_word(n)) == n
