import json
from pathlib import Path
import pytest

torch = pytest.importorskip("torch")
from noema.bem_probe import GlossIndex, base_weights, summarize
from noema.definition_probe import definitions, rows_from_fixture
from noema.semantics import SemanticError


def test_bem_rejects_extra_trained_components():
    weights = {"base_model.embeddings.weight": torch.ones(2)}
    assert list(base_weights(weights)) == ["embeddings.weight"]
    with pytest.raises(SemanticError, match="components"):
        base_weights({**weights, "scalar_mix.gamma": torch.ones(1)})


def test_gloss_scores_are_raw_dot_products_and_inventory_independent():
    class Encoder:
        def encode(self, texts):
            return [{"truncated": False, "pooled": torch.tensor({"east": [2., 0.], "north": [0., 3.]}[t])} for t in texts]
    bank = [{"id": "a", "en": "east"}, {"id": "b", "en": "north"}]
    initial = GlossIndex(Encoder(), bank[:1])
    expanded = GlossIndex(Encoder(), bank[::-1])
    query = torch.tensor([4., 5.])
    assert initial.rank(query) == [{"concept": "a", "score": 8.0}]
    assert expanded.rank(query) == [{"concept": "b", "score": 15.0}, {"concept": "a", "score": 8.0}]
    renamed = GlossIndex(Encoder(), [{"id": "z", "en": "east"}, {"id": "y", "en": "north"}])
    assert [x["score"] for x in renamed.rank(query)] == [15., 8.]
    with pytest.raises(SemanticError, match="Non-finite"):
        expanded.rank(torch.tensor([float("nan"), 0.]))


def test_fresh_fixture_is_disjoint_and_unknowns_are_not_scored_as_correct():
    inventory = {d["id"] for d in definitions()}
    old = rows_from_fixture(json.loads(Path("data/definition-probe-v1.json").read_text(encoding="utf-8")), inventory)
    rows = rows_from_fixture(json.loads(Path("data/definition-probe-v2.json").read_text(encoding="utf-8")), inventory)
    assert len(rows) == 68
    assert not {r["text"] for r in rows} & {r["text"] for r in old}
    assert sum(r["expected"] is None for r in rows) == 16
    report = summarize([{**r, "top": [{"concept": r["expected"] or "aa", "score": 99.}]} for r in rows])
    assert report["ja"]["supported"] == {"count": 26, "correct": 26, "accuracy": 1., "top3_correct": 26}
    assert report["en"]["top1_score"]["unsupported"]["count"] == 8
    assert report["bilingual"]["both_correct"] == 26
