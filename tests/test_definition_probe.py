import json
from pathlib import Path
import pytest

torch = pytest.importorskip("torch")
from noema.definition_probe import DefinitionIndex, definitions, metrics, rows_from_fixture, span_vector
from noema.semantics import SemanticError


def test_definition_index_can_add_a_concept_without_a_class_head():
    class Encoder:
        def encode(self, texts):
            return [{"truncated": False, "pooled": torch.tensor({"east": [2., 0.], "north": [0., 3.]}[t])} for t in texts]
    east = {"id": "a", "ja": "east", "en": "east"}
    north = {"id": "b", "ja": "north", "en": "north"}
    initial = DefinitionIndex(Encoder(), [east])
    extended = DefinitionIndex(Encoder(), [east, north])
    assert initial.rank(torch.tensor([0., 1.]))[0]["concept"] == "a"
    assert extended.rank(torch.tensor([0., 1.]))[0] == {"concept": "b", "cosine": 1.0}
    # Stable ties and order-independent inventory.
    assert [r["concept"] for r in DefinitionIndex(Encoder(), [north, east]).rank(torch.ones(2))] == ["a", "b"]
    with pytest.raises(SemanticError, match="Zero embedding"):
        extended.rank(torch.zeros(2))


def test_contextual_span_excludes_special_and_outside_tokens():
    feature = {"truncated": False, "offsets": [(0, 0), (0, 2), (2, 4), (4, 5), (0, 0)],
               "tokens": torch.tensor([[99., 99.], [1., 2.], [3., 4.], [90., 90.], [99., 99.]])}
    assert torch.equal(span_vector(feature, 1, 3), torch.tensor([2., 3.]))
    with pytest.raises(SemanticError, match="no tokens"):
        span_vector(feature, 5, 6)
    feature["truncated"] = True
    with pytest.raises(SemanticError, match="Truncated"):
        span_vector(feature, 0, 2)


def test_probe_fixture_and_metrics_do_not_count_unknowns_as_correct():
    fixture = json.loads(Path("data/definition-probe-v1.json").read_text(encoding="utf-8"))
    bank = definitions()
    assert len(bank) == 91
    rows = rows_from_fixture(fixture, {d["id"] for d in bank})
    assert len(rows) == 96
    assert sum(r["group"] == "unsupported" for r in rows) == 16
    predictions = []
    for mode in ("isolated", "contextual_span", "sentence"):
        for row in rows:
            predictions.append({**row, "mode": mode, "top": [{"concept": row["expected"] or "aa", "cosine": .8}]})
    report = metrics(predictions)
    assert report["isolated:ja"]["supported"]["count"] == 40
    assert report["isolated:ja"]["extension"]["count"] == 26
    assert report["isolated:ja"]["supported"]["top1_accuracy"] == 1.0
    assert report["isolated:en"]["top1_cosine"]["unsupported"]["count"] == 8
    assert report["isolated:bilingual"]["both_correct"] == 40
    fixture["pairs"][0]["ja"][1] = "missing"
    with pytest.raises(SemanticError, match="exactly once"):
        rows_from_fixture(fixture, {d["id"] for d in bank})
