import itertools
import json
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")
pytest.importorskip("transformers")
from noema.srl_spans import decode_bio, decode_word_bio
from noema.semantics import SemanticError


def valid(tags):
    previous = "O"
    for tag in tags:
        if tag.startswith("I-") and previous not in (tag, "B-" + tag[2:]):
            return False
        previous = tag
    return True


def test_word_decoder_maximizes_full_subword_score_by_exhaustive_search():
    labels = ["O", "B-A0", "I-A0", "B-A1", "I-A1"]
    generator = torch.Generator().manual_seed(84)
    for lengths in ((1, 1, 1), (3, 1, 2), (2, 3, 1)):
        starts, ends, offset = [], [], 1
        for size in lengths:
            starts.append(offset)
            ends.append(offset + size - 1)
            offset += size
        def expand(sequence):
            pieces = [0]
            for tag, size in zip(sequence, lengths):
                continuation = labels.index("I-" + labels[tag][2:]) if labels[tag].startswith("B-") else tag
                pieces.extend([tag] + [continuation] * (size - 1))
            return pieces + [0]
        paths = [p for p in itertools.product(range(5), repeat=3) if valid([labels[i] for i in p])]
        for _ in range(5):
            probabilities = torch.randn(offset + 1, 5, generator=generator).softmax(-1)
            words, pieces = decode_word_bio(probabilities, labels, starts, ends)
            score = lambda path: sum(float(probabilities[j, i]) for j, i in enumerate(expand(path)))
            assert score(words) == pytest.approx(max(map(score, paths)), abs=1e-6)
            assert pieces == expand(words)
            assert valid([labels[i] for i in words]) and valid([labels[i] for i in pieces])
            if lengths == (1, 1, 1):
                assert words == decode_bio(probabilities[1:-1], labels)


def test_boundary_decoder_rejects_missing_pieces_and_nonfinite_scores():
    probabilities = torch.full((6, 3), 1 / 3)
    labels = ["O", "B-A0", "I-A0"]
    for starts, ends in (([], []), ([1, 3], [1, 4]), ([1], [3]), ([0], [4]), ([1, 3], [3, 4]), ([1], [5])):
        with pytest.raises(SemanticError, match="boundaries"):
            decode_word_bio(probabilities, labels, starts, ends)
    probabilities[2, 0] = float("nan")
    with pytest.raises(SemanticError, match="Non-finite"):
        decode_word_bio(probabilities, labels, [1], [4])


def test_missing_continuation_labels_are_not_invented():
    labels = ["O", "B-X", "I-Y"]
    probabilities = torch.tensor([[1., 0., 0.], [0.1, 0.8, 0.1], [0.1, 0.8, 0.1], [1., 0., 0.]])
    assert decode_word_bio(probabilities, labels, [1], [2]) == ([0], [0, 0, 0, 0])
    assert decode_word_bio(probabilities, labels, [1, 2], [1, 2]) == ([1, 1], [0, 1, 1, 0])


def test_new_fixture_has_unique_exact_source_anchors():
    rows = json.loads(Path("data/srl-boundary-v1.json").read_text(encoding="utf-8"))
    assert len({r["id"] for r in rows}) == len(rows)
    for row in rows:
        for lang, role_index in (("ja", 1), ("en", 2)):
            for predicate in row["predicates"]:
                assert row[lang].count(predicate[lang]) == 1
                for role in predicate["roles"]:
                    assert row[lang].count(role[role_index]) == 1


def test_boundary_report_replays_assessments_and_keeps_detector_evidence():
    from scripts.probe_srl_boundaries import DECODERS, FIXTURES, summarize
    from scripts.probe_srl_spans import assess_spans
    from noema.srl_spans import spans_from_tags
    root = Path("reports/srl-boundary-v1")
    predictions = json.loads((root / "predictions.json").read_text(encoding="utf-8"))
    expected = json.loads((root / "assessment.json").read_text(encoding="utf-8"))
    rows = {dataset: {r["id"]: r for r in json.loads(Path(path).read_text(encoding="utf-8"))}
            for dataset, path in FIXTURES.items()}
    assessments = []
    for doc in predictions:
        variants = doc["decoders"]
        assert variants["published"]["text"] == variants["word_boundary"]["text"]
        strip = lambda p: [{k: v for k, v in s.items() if k != "span_annotations"} for s in p["sentences"]]
        assert strip(variants["published"]) == strip(variants["word_boundary"])
        for sentence in variants["word_boundary"]["sentences"]:
            for annotation in sentence["span_annotations"]:
                assert valid(annotation["word_tags"]) and valid(annotation["subword_tags"])
                assert annotation["subword_tags"][0] == annotation["subword_tags"][-1] == "O"
                assert annotation["spans"] == spans_from_tags(annotation["word_tags"], sentence["tokens"], variants["word_boundary"]["text"])
        assessments.append({k: doc[k] for k in ("dataset", "id", "language")} | {
            "decoders": {name: assess_spans(rows[doc["dataset"]][doc["id"]], variants[name]) for name in DECODERS}})
    assert json.loads(json.dumps(assessments)) == expected
    summary = json.loads((root / "summary.json").read_text(encoding="utf-8"))
    assert summarize(assessments, predictions) == summary["datasets"]
