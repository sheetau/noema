import copy

import pytest

torch = pytest.importorskip("torch")
from noema.reference_heads import (dependency_evidence, align_head, reference_graph, frame_references,
                                   assess_references, analyze_dependencies)
from noema.semantics import SemanticError
from scripts.probe_reference_heads import gold_mentions


def sample():
    text = "A B C D"
    tokens = [{"start": i, "end": i + 1, "text": text[i]} for i in (0, 2, 4, 6)]
    phrases = [{"id": i, **token, "head": token, "relations": []} for i, token in enumerate(tokens)]
    return {"text": text, "tokens": tokens, "phrases": phrases}


def test_nested_spans_share_only_the_dependency_head():
    p = sample()
    deps = dependency_evidence(p, [1, 2, 3, 10], 10)
    g = reference_graph(p, deps, [{"start": 0, "end": 3}, p["tokens"][1], p["tokens"][0]])
    by_span = {(m["start"], m["end"]): m for m in g["mentions"]}
    assert by_span[0, 3]["referent"] == by_span[2, 3]["referent"] != by_span[0, 1]["referent"]
    assert any(e["kind"] == "same_source_head" for e in g["evidence"])


def test_cycles_self_loops_unknown_parents_and_multiple_heads_stay_unresolved():
    p = sample()
    for parents in ([1, 0, 3, 10], [0, 0, 3, 10], [99, 0, 3, 10]):
        deps = dependency_evidence(p, parents, 10)
        assert align_head({"start": 0, "end": 3}, p, deps)["head_phrase"] is None
    deps = dependency_evidence(p, [3, 2, 3, 10], 10)
    assert align_head({"start": 0, "end": 3}, p, deps)["head_status"] == "ambiguous_head"
    graph = reference_graph(p, deps, [{"start": 0, "end": 3}, {"start": 1, "end": 2}])
    assert len(graph["referents"]) == 2  # Never merge all unresolved heads through None.


def test_only_document_identity_relations_merge_and_transitivity_is_preserved():
    p = sample()
    p["phrases"][1]["relations"] = [{"label": "=", "target_phrase": 0, "external": None}]
    p["phrases"][2]["relations"] = [{"label": "=", "target_phrase": 1, "external": None}]
    p["phrases"][3]["relations"] = [{"label": "other", "target_phrase": 0, "external": None},
                                      {"label": "=", "target_phrase": None, "external": "author"}]
    original = copy.deepcopy(p)
    deps = dependency_evidence(p, [3, 3, 3, 10], 10)
    graph = reference_graph(p, deps, p["tokens"])
    assert [m["referent"] for m in graph["mentions"]] == [0, 0, 0, 1]
    assert len(graph["evidence"]) == 2 and p == original


def test_missing_singletons_and_excess_identity_are_counted():
    p = sample()
    deps = dependency_evidence(p, [3, 3, 3, 10], 10)
    gold = [{**t, "referent": i} for i, t in enumerate(p["tokens"])]
    empty = assess_references(gold, reference_graph(p, deps, []))
    assert empty["missing_mentions"] == 4 and not empty["partition_exact"]
    p["phrases"][1]["relations"] = [{"label": "=", "target_phrase": 0, "external": None}]
    result = assess_references(gold, reference_graph(p, deps, p["tokens"]))
    assert result["extra_pairs"] == 1 and not result["partition_exact"]


def test_roles_share_entities_without_losing_mention_positions_or_mutating_frames():
    p = sample()
    deps = dependency_evidence(p, [1, 2, 3, 10], 10)
    frames = [{"source": 2, "mentions": [{"id": 0, **p["tokens"][1]}, {"id": 1, **p["tokens"][0]}],
               "roles": [{"role": "patient", "target": 0}, {"role": "none", "target": 1}]},
              {"source": 3, "mentions": [{"id": 0, "start": 0, "end": 3}],
               "roles": [{"role": "agent", "target": 0}]}]
    original = copy.deepcopy(frames)
    graph = frame_references(p, deps, frames)
    assert len(graph["mentions"]) == 2 and len(graph["referents"]) == 1
    assert [r["role"] for r in graph["roles"]] == ["patient", "agent"]
    assert frames == original


def test_annotation_occurrences_are_positions_not_runtime_surface_equivalence():
    row = {"text": "name name", "mentions": [["name", 0, "a"], ["name", 1, "b"]]}
    assert [(m["start"], m["referent"]) for m in gold_mentions(row)] == [(0, "a"), (5, "b")]
    row["mentions"][1][1] = 2
    with pytest.raises(SemanticError, match="Missing annotated"):
        gold_mentions(row)


def test_dependency_capture_removes_hook_when_parser_fails():
    class Parser:
        models = {"word": torch.nn.Linear(1, 1)}
        def analyze(self, text, **kwargs):
            raise RuntimeError("failed")
    parser = Parser()
    with pytest.raises(RuntimeError, match="failed"):
        analyze_dependencies(parser, "input")
    assert not parser.models["word"]._forward_hooks


def test_repeated_spans_are_one_observation_and_invalid_spans_fail():
    p = sample()
    deps = dependency_evidence(p, [3, 3, 3, 10], 10)
    assert len(reference_graph(p, deps, p["tokens"] * 2)["mentions"]) == 4
    with pytest.raises(SemanticError, match="Invalid reference span"):
        reference_graph(p, deps, [{"start": -1, "end": 2}])
