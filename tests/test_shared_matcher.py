import json
from pathlib import Path
import pytest

torch = pytest.importorskip("torch")
from noema.definition_probe import definitions, normalized, rows_from_fixture
from noema.semantics import CONCEPTS, SemanticError
from noema.shared_matcher import CompatibilityHead, predict, query_features, select_rows


def test_head_is_candidate_equivariant_and_has_no_class_parameters():
    torch.manual_seed(17)
    head = CompatibilityHead(384)
    assert sum(p.numel() for p in head.parameters()) == 49155
    query = normalized(torch.randn(5, 3, 384))
    bank = normalized(torch.randn(7, 384))
    assert torch.allclose(head(query, bank), query[:, 0] @ bank.T, atol=1e-6)
    with torch.no_grad():
        head.definition_projection.weight.normal_()
    scores = head(query, bank)
    permutation = torch.tensor([3, 0, 6, 1, 4, 5, 2])
    assert torch.allclose(head(query, bank[permutation]), scores[:, permutation], atol=1e-6)
    expanded = torch.cat([bank, normalized(torch.randn(9, 384))])
    assert torch.allclose(head(query, expanded)[:, :7], scores, atol=1e-6)
    assert sum(p.numel() for p in head.parameters()) == 49155
    linear = (torch.einsum("bkd,cd->bkc", query, bank) * head.cosine_weights[None, :, None]).sum(1)
    assert (scores - linear).abs().max() <= .250001
    with pytest.raises(SemanticError, match="query shape"):
        head(query[:, :2], bank)


def test_entire_heldout_sentence_is_excluded_and_sampling_is_stable():
    corpus = []
    for language in ("ja", "en"):
        for split, concepts in (("train", ["aa", "ab"]), ("dev", ["ae"])):
            for concept in concepts:
                text = f"{language} {split} {concept}"
                corpus.append({"id": text, "text": text, "split": split, "supported": True,
                               "language": language, "spans": [{"start": len(text) - 2, "end": len(text),
                               "kind": "entity", "concept": concept}]})
        # A training target may be allowed while its sentence contains a heldout concept.
        corpus.append({"id": language + "excluded", "text": "excluded " + language, "split": "train",
                       "supported": True, "language": language,
                       "spans": [{"start": 0, "end": 8, "kind": "entity", "concept": "aa"}],
                       "graph": {"nodes": [{"concept": "ae"}]}})
    kwargs = {"train_cap": 1, "dev_cap": 1, "train_ids": {"aa", "ab"}, "dev_ids": {"ae"}}
    selected = select_rows(corpus, **kwargs)
    assert selected == select_rows(corpus[::-1] + corpus, **kwargs)
    assert len(selected["train"]) == 4 and len(selected["dev"]) == 2
    assert not any("excluded" in r["id"] for rows in selected.values() for r in rows)
    assert not {r["text"] for r in selected["train"]} & {r["text"] for r in selected["dev"]}
    with pytest.raises(SemanticError, match="disjoint"):
        select_rows([], train_ids={"aa"}, dev_ids={"aa"})


def test_query_features_use_context_span_isolation_and_sentence_separately():
    class Encoder:
        def encode(self, texts):
            return [{"truncated": False, "offsets": [(0, 1), (1, 2)],
                     "tokens": torch.tensor([[1., 0.], [0., 2.]]),
                     "pooled": torch.tensor([0., 1.]) if t == "b" else torch.tensor([1., 1.])} for t in texts]
    row = {"text": "ab", "span": "b", "start": 1, "end": 2}
    query = query_features(Encoder(), [row])
    assert torch.allclose(query, torch.tensor([[[0., 1.], [0., 1.], [2 ** -.5, 2 ** -.5]]]))
    with pytest.raises(SemanticError, match="Span text"):
        query_features(Encoder(), [{**row, "span": "a"}])


def test_confirmation_concepts_are_unseen_and_predictions_do_not_use_gold():
    bank = {d["id"] for d in definitions()}
    fixtures = {key: rows_from_fixture(json.loads(Path(f"data/definition-probe-{key}.json").read_text(encoding="utf-8")), bank)
                for key in ("v1", "v2", "v3")}
    new = fixtures["v3"]
    gold = {r["expected"] for r in new if r["expected"]}
    old = {r["expected"] for key in ("v1", "v2") for r in fixtures[key] if r["expected"]}
    assert len(gold) == 50 and not gold & (old | set(CONCEPTS))
    assert gold | old | set(CONCEPTS) == bank
    assert len(new) == 116 and sum(r["expected"] is None for r in new) == 16
    assert not {r["text"] for r in new} & {r["text"] for key in ("v1", "v2") for r in fixtures[key]}
    rows = [{"expected": "a"}, {"expected": "b"}, {"expected": None}]
    predictions = predict(torch.tensor([[.1, .8], [.1, .8], [.1, .8]]), rows, ["a", "b"])
    assert all(p["top"][0]["concept"] == "b" for p in predictions)
