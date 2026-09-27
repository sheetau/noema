import json
from pathlib import Path
import pytest
from noema.grammar import parse, format_graph
from noema.language import policy, convert, EXTENSION
from noema.semantics import SemanticError
from noema.script import encode, decode


def test_every_new_word_has_a_typed_parseable_use():
    roots, concepts, markers, roles = policy("0.3")
    assert len(roots) == len(set(roots.values())) == 91
    assert set(EXTENSION["roots"]) == set(EXTENSION["concepts"])
    for ident, concept in EXTENSION["concepts"].items():
        word = roots[ident]
        if concept["kind"] in ("event", "state"):
            pieces = [word]
            for marker, role in markers.items():
                if role in concept["roles"]:
                    pieces.extend((marker, "laa" if role in ("location", "source", "destination") else "maa"))
            text = "noema c c " + " ".join(pieces) + "."
        else:
            text = "noema c c saa i " + word + "."
        graph = parse(text)
        assert parse(format_graph(graph)) == graph
        assert parse(encode(text)) == graph
        assert decode(encode(text)) == format_graph(graph)


def test_source_and_destination_are_distinct_and_not_collapsed_to_location():
    graph = parse('noema c c vae i qo n "Aki" z tp 2 lac.')
    roles = graph["utterances"][0]["content"]["roles"]
    entities = {e["id"]: e for e in graph["entities"]}
    assert entities[roles["source"]]["concept"] == "ai"
    assert entities[roles["destination"]]["concept"] == "dc"
    assert roles["location"] is None
    for version in ("0.1", "0.2"):
        with pytest.raises(SemanticError):
            convert(graph, version)


def test_old_documents_round_trip_through_new_edition_without_new_meaning():
    graph = parse('noema b b u [ ih i mu o dog j si ]. b no i p dog j c.')
    lifted = convert(graph, "0.3")
    assert convert(lifted, "0.2") == graph
    assert lifted["schema_version"] == "0.3"
    old = parse(Path("examples/chase.noema").read_text(encoding="utf-8"))
    assert convert(convert(old, "0.3"), "0.1") == old


@pytest.mark.parametrize("text", [
    "noema b b vaa i fo j mac.",
    "noema c c vae i fo 2 mu.",
    "noema c c vaa i fo z tp.",
    "noema c c ih i tp j mu.",
    "noema c b po i mu.",
])
def test_editions_role_types_and_predicate_frames_are_enforced(text):
    with pytest.raises(SemanticError):
        parse(text)


def test_dictionary_authoring_source_matches_packaged_resource():
    from scripts.build_lexicon_v03 import build
    assert build() == EXTENSION
