import copy
import itertools
from xml.etree import ElementTree
import pytest
from noema.grammar import parse, format_graph
from noema.language import COMPOUNDS, convert, policy, normalize_document
from noema.render import render
from noema.script import encode, decode
from noema.semantics import SemanticError


def test_compound_properties_count_and_reference_survive_nested_scope():
    text = 'noema d d u [ vac i qo n "葵" j jx-sak-sai m c n "赤-本" o book ]. b vac i c j p book.'
    graph = parse(text)
    book = next(e for e in graph["entities"] if e["concept"] == "af")
    assert book["qualifiers"] == ["fi", "fk"] and book["quantity"] == 2
    assert graph["utterances"][0]["content"]["kind"] == "not"
    assert len(graph["utterances"]) == 2  # No separate adjective assertion is added.
    canonical = format_graph(graph)
    assert 'jx-sai-sak' in canonical and '"赤-本"' in canonical
    assert parse(canonical) == graph == parse(encode(text))
    assert decode(encode(text)) == canonical
    assert ElementTree.fromstring(render(text)).find('{http://www.w3.org/2000/svg}metadata').text == canonical


def test_compounds_commute_without_identifying_distinct_referents():
    a = parse('noema d d vac i fo j jx-sak-sai. ku i fo j jx-sai-sak k zr.')
    b = parse('noema d d vac i fo j jx-sai-sak. ku i fo j jx-sak-sai k zr.')
    assert a == b
    assert len([e for e in a["entities"] if e["concept"] == "af"]) == 2


def test_every_pair_of_entity_properties_has_a_compositional_round_trip():
    roots, _, _, _ = policy("0.4")
    for first, second in itertools.combinations(COMPOUNDS["attributive_states"], 2):
        graph = parse('noema d d no i fo j mu-' + roots[first] + '-' + roots[second] + '.')
        assert parse(format_graph(graph)) == graph
    assert policy("0.3") == policy("0.4")  # No old primitive is redefined.


@pytest.mark.parametrize("text", [
    'noema c c vac i fo j jx-sai.',
    'noema d d vac i fo j jx-vac.',
    'noema d d vac i fo j jx-sab.',
    'noema d d vac i fo j jx-saa.',
    'noema d d vac i fo j jx-unknown.',
    'noema d d vac i fo j jx-sai-sai.',
    'noema d d saa i tp-wm.',
    'noema d d vac i qo-sai j jx.',
])
def test_invalid_or_unrepresentable_compounds_are_rejected(text):
    with pytest.raises(SemanticError):
        parse(text)


def test_old_versions_convert_exactly_and_compound_downgrade_is_explicitly_rejected():
    for version, text in (("0.2", 'noema b b po i mu.'), ("0.3", 'noema c c vae i fo z tp 2 lac.')):
        old = parse(text)
        new = convert(old, "0.4")
        assert all(e["qualifiers"] == [] for e in new["entities"])
        assert convert(new, version) == old
    original = convert(parse('noema b b po i mu.'), "0.1")
    assert convert(convert(original, "0.4"), "0.1") == original
    qualified = parse('noema d d po i mu-wm.')
    before = copy.deepcopy(qualified)
    for version in ("0.1", "0.2", "0.3"):
        with pytest.raises(SemanticError, match="compound properties"):
            convert(qualified, version)
    assert qualified == before


def test_compound_json_is_strict_about_types_and_schema_fields():
    graph = parse('noema d d po i mu-wm.')
    for value in (None, "bf", [True], ["ba"], ["bf", "bf"]):
        changed = copy.deepcopy(graph)
        changed["entities"][0]["qualifiers"] = value
        with pytest.raises(SemanticError):
            normalize_document(changed)
    del graph["entities"][0]["qualifiers"]
    with pytest.raises(SemanticError):
        normalize_document(graph)
