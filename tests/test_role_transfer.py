import json
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")
from noema.role_transfer import RoleHead, candidates, targets, assess
from scripts.train_role_transfer import validate_rows


def example():
    return {"text": "A B C", "tokens": [
        {"text": "A", "start": 0, "end": 1}, {"text": "B", "start": 2, "end": 3}, {"text": "C", "start": 4, "end": 5}],
        "phrases": [
            {"id": 0, "start": 0, "end": 1, "head": {"start": 0, "end": 1}, "relations": [
                {"label": "case", "target_phrase": 1}, {"label": "case", "target_phrase": None, "external": "writer"}]},
            {"id": 1, "start": 2, "end": 3, "head": {"start": 2, "end": 3}, "relations": []},
            {"id": 2, "start": 4, "end": 5, "head": {"start": 4, "end": 5}, "relations": [{"label": "case", "target_phrase": 1}]}]}


def test_candidates_have_no_gold_input_and_never_turn_external_guesses_into_entities():
    pairs, features = candidates(example(), torch.eye(3), ("case",))
    assert pairs == [{"source": 0, "target": 1, "native_case": "case"}, {"source": 2, "target": 1, "native_case": "case"}]
    head = RoleHead(3, ("case",), hidden=4)
    assert head(features).shape == (2, 5)
    assert head(features[:1]).shape == (1, 5)
    assert features.shape == (2, 16)
    assert not torch.equal(features[0], features[1])


def test_unannotated_predicates_are_not_false_negative_training_examples():
    prediction = example()
    pairs, _ = candidates(prediction, torch.eye(3), ("case",))
    row = {"text": prediction["text"], "predicate": "A", "roles": [["patient", "B"]]}
    assert targets(row, prediction, pairs).tolist() == [2, -100]
    row["roles"] = [["patient", "C"]]
    assert targets(row, prediction, pairs).tolist() == [0, -100]


def test_assessment_keeps_missing_arguments_in_denominator():
    prediction = example()
    pairs, _ = candidates(prediction, torch.eye(3), ("case",))
    row = {"id": "test-p", "split": "test", "family": "new", "text": prediction["text"],
           "predicate": "A", "roles": [["patient", "B"], ["agent", "C"]]}
    result = assess(row, prediction, pairs, [2, 1])
    assert result["arguments"][0]["correct"]
    assert not result["arguments"][1]["detected"]
    assert not result["all_specified_correct"]


def test_role_corpus_holds_out_predicate_families():
    rows = json.loads(Path("data/role-transfer-v1.json").read_text(encoding="utf-8"))
    validate_rows(rows)
    assert {s: sum(r["split"] == s for r in rows) for s in ("train", "dev", "test")} == {"train": 32, "dev": 8, "test": 16}
    altered = [dict(r) for r in rows]
    altered[-1]["family"] = altered[0]["family"]
    with pytest.raises(AssertionError):
        validate_rows(altered)


def test_saved_role_labels_and_argument_checks_reproduce():
    root = Path("reports/role-transfer-v1")
    evidence = json.loads((root / "evidence.json").read_text(encoding="utf-8"))
    evaluation = json.loads((root / "evaluation.json").read_text(encoding="utf-8"))
    from noema.role_transfer import LABELS
    for e in evidence:
        assert targets(e["row"], e["prediction"], e["pairs"]).tolist() == e["targets"]
    by_id = {e["row"]["id"]: e for e in evidence}
    for method in evaluation.values():
        for split in method.values():
            for case in split["cases"]:
                e = by_id[case["id"]]
                result = assess(e["row"], e["prediction"], e["pairs"], [LABELS.index(p["role"]) for p in case["outputs"]])
                assert result == {k: v for k, v in case.items() if k != "outputs"}
