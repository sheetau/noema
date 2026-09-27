import copy

import pytest

pytest.importorskip("torch")
from noema.semantics import SemanticError
from scripts.diagnose_reference_ranker import compare_partitions, summarize


def fixture():
    heads = [{"id": i, "start": 2 * i, "end": 2 * i + 1} for i in range(3)]
    row = {"id": "example", "text": "A B C", "heads": heads,
           "relations": [{"source": 1, "target": 0, "type": "=", "mode": None, "external": None},
                         {"source": 2, "target": 1, "type": "=", "mode": None, "external": None}]}
    native = {"text": row["text"], "phrases": [{"id": h["id"], "head": h, "relations": []} for h in heads[:2]]}
    ranked = copy.deepcopy(native)
    ranked["phrases"][1]["relations"] = [{"label": "=", "target_phrase": 0, "external": None}]
    return row, native, ranked


def test_omitted_endpoint_pairs_stay_in_denominator_and_failures_remain():
    row, native, ranked = fixture()
    case = compare_partitions(row, native, ranked)
    assert case["gold_pairs"] == 3
    assert case["gold_pairs_missing_endpoints"] == 2
    assert case["gained_correct_pairs"] == 1
    assert case["native"]["missing_pairs_with_available_endpoints"] == 1
    assert case["selected"]["missing_pairs_with_available_endpoints"] == 0
    result = summarize([case, compare_partitions(row, None, None)])
    assert result["documents"] == 2 and result["parsed"] == 1
    assert result["gold_pairs"] == 6 and result["gold_pairs_missing_endpoints"] == 5
    assert result["endpoint_availability_recall_ceiling"] == 1 / 6


def test_modal_annotations_are_unscored_and_changed_heads_are_rejected():
    row, native, ranked = fixture()
    row["relations"][0]["mode"] = "OR"
    result = summarize([compare_partitions(row, native, ranked)])
    assert result["annotation_supported"] == result["gold_pairs"] == 0
    assert result["endpoint_availability_recall_ceiling"] is None
    ranked["phrases"].pop()
    ranked["phrases"][0]["relations"] = []
    with pytest.raises(SemanticError, match="head availability"):
        compare_partitions(row, native, ranked)


def test_link_regression_and_extraneous_heads_are_accounted_separately():
    row, native, ranked = fixture()
    row["relations"] = row["relations"][:1]
    extra = {"id": 3, "head": {"start": 6, "end": 7}, "relations": []}
    native["phrases"].append(copy.deepcopy(extra))
    ranked["phrases"].append(copy.deepcopy(extra))
    native["phrases"][1]["relations"] = [{"label": "=", "target_phrase": 0, "external": None}]
    ranked["phrases"][1]["relations"] = [{"label": "=", "target_phrase": 3, "external": None}]
    case = compare_partitions(row, native, ranked)
    assert case["lost_correct_pairs"] == case["added_extra_pairs"] == 1
    assert case["selected"]["extra_pairs_with_non_gold_endpoints"] == 1
