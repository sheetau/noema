import copy
from pathlib import Path
from xml.etree import ElementTree
import pytest

from noema.derivation import DERIVATION
from noema.editor import inspect_text
from noema.grammar import parse, format_graph
from noema.language import convert, policy, normalize_document
from noema.render import render
from noema.script import encode, decode
from noema.semantics import SemanticError
from noema.translation import Translator


def content(text):
    return parse("noema e e " + text)["utterances"][0]["content"]


def test_state_change_and_causation_are_distinct_without_new_primitive_ids():
    state = content("sam i maj.")
    change = content("5-sam i maj.")
    cause = content("6-sam i fo j maj.")
    assert state["predicate"] == "fm"
    assert change["predicate"] == {"operator": "become", "state": "fm"}
    assert cause["predicate"] == {"operator": "cause_change", "state": "fm"}
    assert len(policy("0.5")[1]) == 91 and policy("0.5") == policy("0.4")
    assert change["roles"]["patient"] is None
    assert cause["roles"]["agent"] != cause["roles"]["patient"]
    assert content("u [ 5-sam i maj ].") != content("u [ sam i maj ].")
    assert content("5-san i maj.")["predicate"]["state"] == "fn"  # Not closing =/= opening.


def test_derived_predicates_preserve_scope_references_properties_and_time():
    text = ('noema e e u [ t 6-sai i qo n "葵" o aki j jx-sak m c o book ]. '
            'b 5-sai i p book. y [ sam i maj o door ] [ 6-san i p aki j p door ].')
    graph = parse(text)
    assert graph["utterances"][0]["content"]["body"]["time"]["value"] == "tomorrow"
    assert graph["utterances"][1]["speech_act"] == "question"
    assert graph["utterances"][0]["content"]["kind"] == "not"
    assert graph["utterances"][2]["content"]["kind"] == "if"
    assert len(graph["entities"]) == 3
    book = next(e for e in graph["entities"] if e["concept"] == "af")
    assert book["quantity"] == 2 and book["qualifiers"] == ["fk"]
    assert parse(format_graph(graph)) == graph == parse(encode(text))
    assert decode(encode(text)) == format_graph(graph)
    assert ElementTree.fromstring(render(text)).find('{http://www.w3.org/2000/svg}metadata').text == format_graph(graph)
    assert inspect_text(encode(text))["graph"] == graph


def test_every_state_supports_both_operators_with_the_same_composition_rule():
    roots, concepts, _, _ = policy("0.5")
    for state in DERIVATION["state_bases"]:
        for operator, rule in DERIVATION["operators"].items():
            word = rule["marker"] + "-" + roots[state]
            text = "noema e e " + word + (" i fo j mu" if operator == "cause_change" else " i mu") + "."
            graph = parse(text)
            assert graph["utterances"][0]["content"]["predicate"] == {"operator": operator, "state": state}
            assert parse(encode(format_graph(graph))) == graph
            # The state bearer's type, including place when supported, propagates.
            place_ok = "place" in concepts[state].get("role_types", {}).get("agent", ["entity"])
            text = "noema e e " + word + (" i fo j lab" if operator == "cause_change" else " i lab") + "."
            if place_ok:
                assert parse(format_graph(parse(text))) == parse(text)
            else:
                with pytest.raises(SemanticError, match="type"):
                    parse(text)


def test_omission_is_not_filled_and_questions_requests_keep_their_meaning():
    graph = parse('noema e e 6-sam j maj o door. b 6-sam i c j p door. d 5-sam i p door.')
    first, second, third = graph["utterances"]
    assert first["content"]["roles"]["agent"] is None
    assert second["content"]["roles"]["agent"] == {"query": True}
    assert third["speech_act"] == "request"
    assert parse(format_graph(graph)) == graph


@pytest.mark.parametrize("text", [
    'noema d d 5-sam i maj.',  # Never reinterpret old editions.
    'noema e e 5-vat i maj.',  # Event as a state.
    'noema e e 5-sab i maj.',  # Relational state loses an argument.
    'noema e e 5-saa i maj.',  # Location-dependent state is not a unary property.
    'noema e e 6-mu i fo j mu.',
    'noema e e 5-6-sam i maj.',
    'noema e e 7-sam i maj.',
    'noema e e 5-sam j maj.',
    'noema e e 6-sam i lab j maj.',
    'noema e e 6-sam i fo j maj k fo.',
    'noema e e 5-sam i maj 3 mat.',
    'noema e e 6-sam i fo j maj 3 lab.',
    'noema e e sam i maj-5-sam.',
])
def test_invalid_derivations_and_role_frames_are_rejected(text):
    with pytest.raises(SemanticError):
        parse(text)


def test_json_operators_are_strict_and_failed_conversion_does_not_mutate_input():
    graph = parse('noema e e 6-sam i fo j maj.')
    for value in ({"operator": "become", "state": "fm", "extra": 1}, {"operator": [], "state": "fm"},
                  {"operator": "become", "state": ["fm"]}, {"operator": "stop", "state": "fm"}, [], None, True):
        changed = copy.deepcopy(graph)
        changed["utterances"][0]["content"]["predicate"] = value
        with pytest.raises(SemanticError):
            normalize_document(changed)
    before = copy.deepcopy(graph)
    for version in ("0.1", "0.2", "0.3", "0.4"):
        with pytest.raises(SemanticError, match="derived predicates"):
            convert(graph, version)
    assert graph == before
    # The UI never silently reduces a causative to a state in reverse translation.
    assert Translator().translate({"text": format_graph(graph), "direction": "from_noema", "language": "ja"})["status"] == "unsupported"


def test_all_preexisting_example_documents_round_trip_through_new_edition():
    for path in Path("examples").glob("*.noema"):
        old = parse(path.read_text(encoding="utf-8"))
        newer = convert(old, "0.5")
        assert parse(format_graph(newer)) == newer
        assert convert(newer, old["schema_version"]) == old
