import itertools
import json
from pathlib import Path
import pytest

torch = pytest.importorskip("torch")
pytest.importorskip("transformers")
from noema.srl_spans import decode_bio, spans_from_tags, FrozenSpanSRL
from noema.semantics import SemanticError
from scripts.probe_srl_spans import assess_spans


def legal(tags):
    previous = "O"
    for tag in tags:
        if tag.startswith("I-") and previous not in (tag, "B-" + tag[2:]):
            return False
        previous = tag
    return True


def test_viterbi_matches_exhaustive_valid_sequences():
    labels = ["O", "B-A0", "I-A0", "B-A1", "I-A1"]
    generator = torch.Generator().manual_seed(42)
    for _ in range(5):
        probabilities = torch.rand(4, len(labels), generator=generator).softmax(-1)
        selected = decode_bio(probabilities, labels)
        possibilities = [p for p in itertools.product(range(len(labels)), repeat=4) if legal([labels[i] for i in p])]
        score = lambda path: sum(float(probabilities[j, i]) for j, i in enumerate(path))
        assert legal([labels[i] for i in selected])
        assert score(selected) == pytest.approx(max(map(score, possibilities)), abs=1e-6)
    # The upstream objective sums probabilities, not their logarithms.
    values = torch.tensor([[0.6, 0.3, 0.1, 0., 0.], [0.02, 0.03, 0.45, 0.20, 0.30]])
    assert decode_bio(values, labels) == [0, 3]
    # The other path has a larger product but a smaller sum.
    assert values[0, 1] * values[1, 2] > values[0, 0] * values[1, 3]


def test_spans_preserve_global_offsets_and_never_repair_invalid_roles():
    text = "First. Two cats sleep."
    tokens = [{"text": "Two", "start": 7, "end": 10}, {"text": "cats", "start": 11, "end": 15},
              {"text": "sleep", "start": 16, "end": 21}]
    assert spans_from_tags(["B-A0", "I-A0", "B-V"], tokens, text) == [
        {"label": "A0", "start": 7, "end": 15, "text": "Two cats"},
        {"label": "V", "start": 16, "end": 21, "text": "sleep"}]
    for tags in (["I-A0", "I-A0", "B-V"], ["B-A0", "I-A1", "O"], ["O", "I-A0", "O"]):
        with pytest.raises(SemanticError, match="no automatic repair"):
            spans_from_tags(tags, tokens, text)
    with pytest.raises(SemanticError, match="offsets"):
        spans_from_tags(["O"], [{"text": "wrong", "start": 7, "end": 10}], text)


def test_predicate_indicator_covers_all_its_subwords_and_input_is_not_truncated():
    model = object.__new__(FrozenSpanSRL)
    class Tokenizer:
        cls_token, sep_token = "<s>", "</s>"
        def _tokenize(self, word): return list(word)
        def convert_tokens_to_ids(self, pieces): return list(range(len(pieces)))
    model.tokenizer = Tokenizer()
    model.metadata = {"max_subwords": 8}
    encoded, starts, ends = model.encode(["ab", "cde"], 1)
    assert starts == [1, 3] and ends == [2, 5]
    assert encoded["token_type_ids"].tolist() == [[0, 0, 0, 1, 1, 1, 0]]
    with pytest.raises(SemanticError, match="no silent truncation"):
        model.encode(["abcdefg"], 0)
    with pytest.raises(SemanticError, match="outside"):
        model.encode(["ab"], -1)


def test_span_assessment_requires_exact_boundaries_and_role():
    row = {"id": "test", "en": "dog sees cat", "predicates": [{"en": "sees", "roles": [["A0", "", "dog"]]}]}
    prediction = {"language": "en", "text": row["en"], "sentences": [{
        "tokens": [{"start": 4, "end": 8}], "span_annotations": [{"predicate_token": 0, "status": "valid_bio",
            "spans": [{"label": "A0", "start": 0, "end": 12}]}]}]}
    check = assess_spans(row, prediction)
    assert not check["all_specified_exact"]
    assert check["checks"][0]["roles"][0]["covered"]
    prediction["sentences"][0]["span_annotations"][0]["spans"][0].update(end=3, label="A1")
    assert not assess_spans(row, prediction)["checks"][0]["roles"][0]["covered"]


def test_saved_predictions_reproduce_exact_span_and_content_checks():
    root = Path("reports/srl-span-v1")
    predictions = json.loads((root / "predictions.json").read_text(encoding="utf-8"))
    for fixture, report in (("srl-span-v1", "assessment.json"), ("srl-transfer-v1", "content-checks.json")):
        rows = {r["id"]: r for r in json.loads(Path("data", fixture + ".json").read_text(encoding="utf-8"))}
        assessed = json.loads(json.dumps([assess_spans(rows[p["id"]], p) for p in predictions]))
        assert assessed == json.loads((root / report).read_text(encoding="utf-8"))
    prior = json.loads(Path("reports/srl-transfer-v1/predictions.json").read_text(encoding="utf-8"))
    # A span model must not silently alter the predicate detector's evidence.
    for old, new in zip(prior, predictions):
        assert (old["id"], old["language"], old["text"]) == (new["id"], new["language"], new["text"])
        assert old["sentences"] == [{k: v for k, v in s.items() if k != "span_annotations"} for s in new["sentences"]]
