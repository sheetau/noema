import json

import pytest

torch = pytest.importorskip("torch")
from safetensors.torch import save_file
from noema.definition_probe import digest
from noema.reference_ranker import ReferenceRanker, reference_targets
from noema.semantics import SemanticError
from scripts.evaluate_reference_ranker import selected_head, training_overlap_ids, test_evaluation as evaluate_test


def record(key, failed=False):
    heads = [{"id": 0, "start": 0, "end": 1}, {"id": 1, "start": 2, "end": 3}]
    row = {"id": key, "text": "A B", "heads": heads,
           "relations": [{"source": 1, "target": 0, "type": "=", "mode": None, "external": None}]}
    prediction = {"text": row["text"], "phrases": [{"id": h["id"], "head": h, "relations": []} for h in heads]}
    target, _ = reference_targets(row, prediction)
    features = {"nodes": torch.zeros(2, 4), "native": torch.zeros(2, 3),
                "word_indices": torch.arange(2), "word_count": torch.tensor(2)}
    return {"row": row, "prediction": None if failed else prediction, "features": None if failed else features,
            "failure": "context exceeded" if failed else None, "target": None if failed else target}


def test_overlap_removal_does_not_discard_failures_or_missing_gold_pairs():
    head = ReferenceRanker(2)
    for parameter in head.parameters():
        parameter.data.zero_()
    results = evaluate_test([record("overlap"), record("new"), record("failed", failed=True)], head, ["overlap"])
    for mode in ("native", "selected"):
        all_counts = results["all"][mode]["summary"]["all"]
        filtered = results["without_training_text_overlap"][mode]["summary"]["all"]
        assert all_counts["documents"] == 3 and all_counts["gold_pairs"] == 3
        assert filtered["documents"] == filtered["gold_pairs"] == filtered["missing_pairs"] == 2
        assert filtered["parsed"] == 1 and filtered["pair_recall"] == 0


def test_overlap_inventory_only_uses_documented_train_test_duplicates():
    preparation = {"cross_split_duplicate_texts": [
        [{"split": "train", "id": "a"}, {"split": "test", "id": "b"}],
        [{"split": "dev", "id": "c"}, {"split": "test", "id": "d"}]]}
    assert training_overlap_ids(preparation) == ["b"]


def selection_fixture(tmp_path):
    root, report = tmp_path / "weights", tmp_path / "report"
    root.mkdir()
    report.mkdir()
    (root / "manifest.json").write_text("{}", encoding="utf-8")
    head = ReferenceRanker(2)
    weights = root / "ranker-linear.safetensors"
    save_file(head.state_dict(), str(weights))
    selection = {"selected": "linear", "dimension": 2, "decision": "argmax_previous_or_none",
                 "choices": {"linear": {"hidden": 0, "epoch": 1, "dev_pair_f1": .5, "dev_loss": .2}},
                 "weights_sha256": {"linear": digest(weights)}, "feature_manifest_sha256": digest(root / "manifest.json")}
    (report / "selection.json").write_text(json.dumps(selection), encoding="utf-8")
    training = {"selection_sha256": digest(report / "selection.json"),
                "protocol_sha256": digest("docs/reference-ranker-v1-protocol.md"),
                "code_sha256": {"scripts/evaluate_reference_ranker.py": digest("scripts/evaluate_reference_ranker.py")}}
    (report / "training.json").write_text(json.dumps(training), encoding="utf-8")
    return root, report, head, training


def test_saved_selection_requires_matching_weights_and_is_frozen_for_inference(tmp_path):
    root, report, expected, _ = selection_fixture(tmp_path)
    actual, _ = selected_head(root, report)
    assert all(torch.equal(value, actual.state_dict()[key]) for key, value in expected.state_dict().items())
    assert not actual.training and all(not p.requires_grad for p in actual.parameters())
    with (root / "ranker-linear.safetensors").open("ab") as stream:
        stream.write(b"changed")
    with pytest.raises(SemanticError, match="weights changed"):
        selected_head(root, report)


def test_selection_cannot_bypass_its_training_record_or_decision_policy(tmp_path):
    root, report, _, training = selection_fixture(tmp_path)
    path = report / "selection.json"
    selection = json.loads(path.read_text(encoding="utf-8"))
    selection["decision"] = "test_tuned_threshold"
    path.write_text(json.dumps(selection), encoding="utf-8")
    with pytest.raises(SemanticError, match="selection changed"):
        selected_head(root, report)
    training["selection_sha256"] = digest(path)
    (report / "training.json").write_text(json.dumps(training), encoding="utf-8")
    with pytest.raises(SemanticError, match="decision policy"):
        selected_head(root, report)


def test_invalidated_supervision_blocks_checkpoint_and_raw_api_before_model_loading(tmp_path):
    from noema.reference_ranker import ReferenceRankerAnalyzer
    root, report, _, _ = selection_fixture(tmp_path)
    (report / "invalidated.json").write_text('{}', encoding="utf-8")
    with pytest.raises(SemanticError, match="invalidated"):
        selected_head(root, report)
    with pytest.raises(SemanticError, match="invalidated"):
        ReferenceRankerAnalyzer(report=report, artifacts=root)
