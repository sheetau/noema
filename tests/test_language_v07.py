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
    assert normalize_document(graph) == graph
    for notation in ("full", "compact"):
        canonical = format_graph(graph, notation)
        assert parse(canonical) == graph
        for alphabet in ("v1", "v2"):
            native = encode(canonical, alphabet)
            assert parse(native) == graph and decode(native) == canonical
            assert ElementTree.fromstring(render(native, alphabet=alphabet)).find('{http://www.w3.org/2000/svg}metadata').text == canonical
    return graph


def test_collective_each_and_unspecified_are_distinct_applications():
    collective = roundtrip('g:w-w i[no w[mu][si] fo].')
    each = roundtrip('g:w-p a[w[mu][si]][no p a fo].')
    unspecified = roundtrip('g:no w[mu][si] fo.')
    assert collective["entities"] == each["entities"] == unspecified["entities"]
    assert len(policy("0.7")[1]) == 91
    assert collective["utterances"][0]["content"]["kind"] == "collective"
    assert each["utterances"][0]["content"]["body"]["roles"]["agent"] == {"bound": "va"}
    assert each != collective != unspecified != each


def test_negation_scope_has_different_truth_conditions():
    every_not = roundtrip('g:w-p a[w[mu][si]][u[po p a]].')
    not_every = roundtrip('g:u[w-p a[w[mu][si]][po p a]].')
    entities = {e["id"]: e for e in every_not["entities"]}
    # A finite interpretation with one asleep and one awake distinguishes scopes.
    asleep = {entities['na']['members'][0]}
    def holds(expr, environment):
        if expr["kind"] == "not":
            return not holds(expr["body"], environment)
        if expr["kind"] == "each":
            return all(holds(expr["body"], {**environment, expr["variable"]: member})
                       for member in entities[expr["group"]]["members"])
        return environment[expr["roles"]["agent"]["bound"]] in asleep
    assert not holds(every_not["utterances"][0]["content"], {})
    assert holds(not_every["utterances"][0]["content"], {})


def test_alpha_renaming_identity_and_scope_do_not_leak():
    first = roundtrip('g:w-p member[w[mu o dog][si]o pets][no p member p dog]. po p pets.')
    renamed = roundtrip('g:w-p item[w[mu o a][si]o b][no p item p a]. po p b.')
    assert first == renamed
    assert first["utterances"][0]["content"]["group"] == first["utterances"][1]["content"]["roles"]["agent"]
    # Independent binders may reuse a spelling; normal form gives them distinct names.
    roundtrip('g:w-p a[w[mu][si]][po p a]. w-p a[w[fo][mu]][po p a].')
    with pytest.raises(SemanticError, match="not been introduced"):
        parse('g:w-p a[w[mu][si]][po p a]. po p a.')


def test_nested_domains_preserve_direct_members_and_outer_references():
    graph = roundtrip('g:w-p team[w[w[mu][si]][w[fo][mu]]][w-p member[p team][no p member p team]].')
    outer = graph["utterances"][0]["content"]
    inner = outer["body"]
    assert inner["group"] == {"bound": outer["variable"]}
    assert inner["body"]["roles"]["patient"] == {"bound": outer["variable"]}
    assert inner["body"]["roles"]["agent"] == {"bound": inner["variable"]}
    assert len([e for e in graph["entities"] if e["kind"] == "group"]) == 3
    roundtrip('g:w-p team[w[w[mu][si]][w[fo][mu]]][w-w i[po p team]].')
    # Two independent domains express all pairs; they do not imply zipped pairing.
    roundtrip('g:w-p a[w[mu][si]][w-p b[w[fo][mu]][no p a p b]].')


def test_all_member_types_and_collective_roles_are_checked():
    roundtrip('g:w-p place[w[yf][tp]][po mu l p place].')
    for text in ('g:w-p a[w[mu][yf]][po p a].', 'g:w-p a[w[mu][si]][po mu l p a].',
                 'g:w-p a[w[w[mu][si]][fo]][w-w i[po p a]].',
                 'g:w-p a[w[w[mu][si]][fo]][w-p b[p a][po p b]].'):
        with pytest.raises(SemanticError):
            parse(text)


def test_scope_connectives_questions_requests_names_counts_and_time_survive():
    roundtrip('g:b w-p a[w[mu m c][si]][no p a c].')
    roundtrip('g:d w-p door[w[maj-sai][maj-saj]][t 6-sam qo n"葵" p door].')
    roundtrip('g:w-p a[w[mu][si]][y[wm p a][u[po p a]]].')
    roundtrip('g:w-w i[w-w j[no w[mu][si] w[fo][mu]]].')
    graph = roundtrip('g:w-p a[w[mu m c][si]][po p a].')
    assert graph["entities"][1]["quantity"] == 2  # No invented individual members.


@pytest.mark.parametrize("text", [
    'f:w-p a[w[mu][si]][po p a].', 'f:w-w i[po w[mu][si]].',
    'g:w-p a[mu][po p a].', 'g:w-p a[?][po p a].', 'g:b w-p a[c][po p a].',
    'g:w-p a[w[mu][si]o a][po p a].', 'g:w-p a[w[mu][si]][po fo o a].',
    'g:w-p a[w[mu][si]][w-p a[w[fo][mu]][po p a]].',
    'g:w-p a[w[mu][si]][po w[p a][fo]].',
    'g:w-w i[po mu].', 'g:w-w i[po].', 'g:w-w j[po w[mu][si]].',
    'g:b w-w i[no c mu].', 'g:w-w unknown[po w[mu][si]].',
    'g:w-w i[u[po w[mu][si]]].', 'g:w-w i[w-w i[po w[mu][si]]].',
    'g:w-w i[w[po mu][po si]].',
])
def test_ambiguous_binding_and_unsupported_application_are_rejected(text):
    with pytest.raises(SemanticError):
        parse(text)


def test_json_rejects_escaped_variables_unknown_fields_and_self_shadowing_without_mutation():
    graph = parse('g:w-p a[w[mu][si]][po p a].')
    escaped = copy.deepcopy(graph)
    escaped["utterances"].append({"speech_act": "assertion", "content": copy.deepcopy(escaped["utterances"][0]["content"]["body"])})
    malformed = copy.deepcopy(graph)
    malformed["utterances"][0]["content"]["body"]["roles"]["agent"]["query"] = True
    extra = copy.deepcopy(graph)
    extra["utterances"][0]["content"]["quantity"] = 2
    shadowed = copy.deepcopy(graph)
    shadowed["utterances"][0]["content"]["body"] = copy.deepcopy(shadowed["utterances"][0]["content"])
    for invalid in (escaped, malformed, extra, shadowed):
        before = copy.deepcopy(invalid)
        with pytest.raises(SemanticError):
            normalize_document(invalid)
        assert invalid == before


def test_distribution_depth_limit_applies_to_json_and_text():
    graph = parse('g:po w[mu][si].')
    body = graph["utterances"][0]["content"]
    for i in range(65):
        body = {"kind": "each", "group": "na", "variable": 'v' + number_word(i), "body": body}
    graph["utterances"][0]["content"] = body
    with pytest.raises(SemanticError, match="nesting"):
        normalize_document(graph)
    with pytest.raises(SemanticError, match="nesting"):
        parse('g:' + ''.join('w-p v' + number_word(i) + '[w[mu][si]][' for i in range(65)) + 'po mu' + ']' * 65 + '.')


def test_formatter_allocates_variables_away_from_long_document_reference_names():
    graph = parse('g:w-p a[w[mu][si]][po p a].')
    # Compact reference number 672 is "va", otherwise a collision with a binder.
    for i in range(674):
        ident = 'a' + number_word(i)
        graph["entities"].append({"id": ident, "kind": "entity", "concept": "aa", "quantity": None, "name": None, "qualifiers": []})
        clause = {"kind": "clause", "predicate": "be", "polarity": "affirmed", "time": {"kind": "unspecified", "value": None}, "roles": {"agent": ident}}
        graph["utterances"].extend({"speech_act": "assertion", "content": copy.deepcopy(clause)} for _ in range(2))
    normalized = normalize_document(graph)
    assert parse(format_graph(graph, "compact")) == normalized


def test_old_editions_and_strict_downgrade_and_legacy_translator():
    for path in Path("examples").glob("*.noema"):
        old = parse(path.read_text(encoding="utf-8"))
        upgraded = convert(old, "0.7")
        assert parse(format_graph(upgraded)) == upgraded
        assert convert(upgraded, old["schema_version"]) == old
    group = parse('f:po w[mu][si].')
    assert convert(convert(group, "0.7"), "0.6") == group
    for text in ('g:w-p a[w[mu][si]][po p a].', 'g:w-w i[po w[mu][si]].'):
        graph = parse(text)
        before = copy.deepcopy(graph)
        for version in ("0.1", "0.2", "0.3", "0.4", "0.5", "0.6"):
            with pytest.raises(SemanticError):
                convert(graph, version)
        assert graph == before
        for language in ("ja", "en"):
            assert Translator().translate({"text": text, "language": language, "direction": "from_noema"})["status"] == "unsupported"


def test_cli_without_model_dependencies_and_editor_inspection():
    text = 'g:w-p a[w[mu][si]][u[po p a]].'
    result = subprocess.run([sys.executable, '-S', '-m', 'noema', 'parse', '--text', text],
                            capture_output=True, text=True, encoding='utf-8', check=True)
    assert '"schema_version": "0.7"' in result.stdout and '"kind": "each"' in result.stdout
    inspected = inspect_text(text)
    assert parse(inspected["script"]) == inspected["graph"] == parse(text)
