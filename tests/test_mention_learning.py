import json
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")
from scripts import train_mention_learning as learning
from scripts.train_role_transfer import validate_rows


def test_crossfit_never_trains_on_predicted_family(monkeypatch):
    examples = [{"row": {"id": f"{family}-{voice}", "family": family, "split": "train"},
                 "prediction": {}, "vectors": torch.empty(0, 2), "tags": torch.empty(0, dtype=torch.long)}
                for family in ("a", "b", "c", "d", "e", "f", "g", "h") for voice in ("a", "p")]
    development = {**examples[0], "row": {"id": "dev", "family": "outside", "split": "dev"}}
    def fit(training, dimension, hidden, epochs):
        assert all(e["row"]["split"] == "train" for e in training)
        return {e["row"]["family"] for e in training}, []
    def predict(held_out, head, cases):
        assert not ({e["row"]["family"] for e in held_out} & head)
        for example in held_out:
            example["mentions"] = []
    monkeypatch.setattr(learning, "fit_fixed_mentions", fit)
    monkeypatch.setattr(learning, "add_candidates", predict)
    actual, _, record = learning.crossfit_candidates(examples + [development], 2, ("case",), {"hidden": 0, "epoch": 5})
    assert [e["row"]["id"] for e in actual] == [e["row"]["id"] for e in examples]
    assert len(record["folds"]) == 4
    assert all("mentions" not in e for e in examples)
    assert all(len(fold["training_ids"]) == 12 and len(fold["predicted_ids"]) == 4 for fold in record["folds"].values())


def test_corpus_expansion_preserves_family_separation_and_new_confirmation():
    rows = [r for path in learning.DATA for r in json.loads(Path(path).read_text(encoding="utf-8"))]
    validate_rows(rows)
    assert len(rows) == len({r["text"] for r in rows}) == 128
    assert sum(r["split"] == "train" for r in rows) == 64
    assert sum(r["split"] == "dev" for r in rows) == 16
    groups = {split: {r["family"] for r in rows if r["split"] == split} for split in learning.SPLITS}
    assert all(not groups[a] & groups[b] for i, a in enumerate(learning.SPLITS) for b in learning.SPLITS[i + 1:])
    new = [r for r in rows if r["split"] == "scope_confirmation"]
    assert len(new) == 8 and sum(len(r["roles"]) for r in new) == 22


def test_learning_curve_counts_partial_span_as_miss(monkeypatch):
    example = {"row": {"id": "example", "text": "AB C", "roles": [["agent", "AB"]]},
               "prediction": {}, "vectors": torch.empty(0, 2)}
    monkeypatch.setattr(learning, "infer_mentions", lambda *args: [{"id": 0, "start": 1, "end": 2, "text": "B"}])
    result = learning.evaluate_mentions([example], None)
    assert result["summary"]["exact"] == 0
    assert result["summary"]["predicted"] == result["summary"]["gold"] == 1
    assert result["summary"]["document_exact"] == 0
