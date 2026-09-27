import copy
from pathlib import Path
import subprocess
import sys
from xml.etree import ElementTree

import pytest

from noema.editor import inspect_text
from noema.grammar import parse, format_graph, number_word
from noema.language import convert, normalize_document, policy
from noema.render import render
from noema.script import encode, decode
from noema.semantics import SemanticError
from noema.translation import Translator


def roundtrip(text):
    graph = parse(text)
    for notation in ("full", "compact"):
        canonical = format_graph(graph, notation)
        assert parse(canonical) == graph
        for alphabet in ("v1", "v2"):
            native = encode(canonical, alphabet)
            assert parse(native) == graph and decode(native) == canonical
            assert ElementTree.fromstring(render(native, alphabet=alphabet)).find('{http://www.w3.org/2000/svg}metadata').text == canonical
    assert normalize_document(graph) == graph
    return graph


def test_group_is_not_two_assertions_or_an_invented_count():
    graph = roundtrip('f:po w[mu][si].')
    group, dog, cat = graph["entities"]
    assert group == {"id": "na", "kind": "group", "members": ["nb", "nc"]}
    assert dog["quantity"] is cat["quantity"] is None
    assert len(graph["utterances"]) == 1
    assert graph != parse('f:w[po mu][po si].')
    assert len(policy("0.6")[1]) == 91


def test_members_and_group_have_separate_identity_and_reuse():
    graph = roundtrip('f:po w[mu o dog][si]o pets. ih p pets p dog.')
    group = graph["entities"][0]
    first, second = [u["content"] for u in graph["utterances"]]
    assert first["roles"]["agent"] == second["roles"]["agent"] == group["id"]
    assert second["roles"]["patient"] == group["members"][0]
    # Referring to an existing member is not a second declaration of an identical-looking entity.
    another = roundtrip('f:po w[mu][si]o pets. ih p pets mu.')
    assert len(another["entities"]) == 4 and len(graph["entities"]) == 3


def test_nested_groups_preserve_membership_and_shared_members_without_flattening():
    graph = roundtrip('f:po w[w[mu o dog][si]o pets][fo]o all. no p pets p dog. po p all.')
    groups = [e for e in graph["entities"] if e["kind"] == "group"]
    assert len(groups) == 2 and groups[1]["id"] in groups[0]["members"]
    assert len(graph["entities"]) == 5
    direct = roundtrip('f:po w[mu][si][fo].')
    assert graph["entities"] != direct["entities"]


def test_scope_names_quantities_derived_predicates_and_questions_survive():
    graph = roundtrip('f:u[t 6-sam w[qo n"葵"o aki][qo n"Jun"] w[maj-sai m c][maj-saj]]. b no p aki c.')
    content = graph["utterances"][0]["content"]
    assert content["kind"] == "not" and content["body"]["time"]["value"] == "tomorrow"
    assert content["body"]["predicate"] == {"operator": "cause_change", "state": "fm"}
    assert any(e.get("quantity") == 2 for e in graph["entities"])
    assert graph["utterances"][1]["speech_act"] == "question"
    assert inspect_text(format_graph(graph, "compact"))["graph"] == graph
    # A place group remains spatial, rather than being accepted in every role as generic entities.
    roundtrip('f:po mu l w[yf][tp].')
    with pytest.raises(SemanticError, match="type"):
        parse('f:po w[mu][yf].')


@pytest.mark.parametrize("text", [
    'e:po w[mu][si].', 'f:po w[mu].', 'f:po w.', 'f:po w[?][si].',
    'f:b no w[c][mu] si.', 'f:po w[mu o a][p a].',
    'f:po w[mu][si] m c.', 'f:po w[mu][si] n"pets".',
    'f:po w[mu][si]o a o b.', 'f:po w[mu][p missing].',
    'f:po w[po mu][si].', 'f:po w[mu][si]o a. po fo o a.',
])
def test_invalid_or_unsupported_group_meanings_are_rejected(text):
    with pytest.raises(SemanticError):
        parse(text)


def test_invalid_json_cycles_dangling_members_and_extra_fields_are_rejected_without_mutation():
    graph = parse('f:po w[mu][si].')
    for members in (["na", "nb"], ["missing", "nb"], ["nb", "nb"], ["nb"], [None, "nc"], {"nb", "nc"}):
        changed = copy.deepcopy(graph)
        changed["entities"][0]["members"] = members
        original = copy.deepcopy(changed)
        with pytest.raises(SemanticError):
            normalize_document(changed)
        assert changed == original
    graph["entities"][0]["quantity"] = 2
    with pytest.raises(SemanticError, match="Expected fields"):
        normalize_document(graph)


def test_group_depth_is_bounded_even_when_earlier_members_are_cached():
    graph = parse('f:po mu o a. po si o b.')
    first, second = [e["id"] for e in graph["entities"]]
    for n in range(65):
        ident = 'g' + number_word(n)
        graph["entities"].append({"id": ident, "kind": "group", "members": [first, second]})
        first, second = ident, first
    graph["utterances"][0]["content"]["roles"]["agent"] = first
    with pytest.raises(SemanticError, match="nesting"):
        normalize_document(graph)


def test_old_editions_roundtrip_and_group_downgrades_fail_including_reverse_translation():
    for path in Path("examples").glob("*.noema"):
        old = parse(path.read_text(encoding="utf-8"))
        upgraded = convert(old, "0.6")
        assert parse(format_graph(upgraded)) == upgraded
        assert convert(upgraded, old["schema_version"]) == old
    group = parse('f:po w[mu][si].')
    before = copy.deepcopy(group)
    for version in ("0.1", "0.2", "0.3", "0.4", "0.5"):
        with pytest.raises(SemanticError, match="groups"):
            convert(group, version)
    assert group == before
    for language in ("ja", "en"):
        assert Translator().translate({"text": 'f:po w[mu][si].', "language": language, "direction": "from_noema"})["status"] == "unsupported"


def test_group_cli_runs_without_model_dependencies():
    text = 'f:po w[mu][si]o pets. po p pets.'
    result = subprocess.run([sys.executable, '-S', '-m', 'noema', 'parse', '--text', text],
                            capture_output=True, text=True, encoding='utf-8', check=True)
    assert '"schema_version": "0.6"' in result.stdout and '"kind": "group"' in result.stdout
