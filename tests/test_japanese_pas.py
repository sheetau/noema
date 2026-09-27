import json
from pathlib import Path

import pytest

from noema.japanese_pas import source_spans
from noema.semantics import SemanticError
from scripts.probe_japanese_pas import assess


def test_source_spans_preserve_spaces_unicode_and_repeated_words():
    assert source_spans("猫 猫🐈。", ["猫", " ", "猫", "🐈", "。"]) == [
        {"text": "猫", "start": 0, "end": 1}, {"text": " ", "start": 1, "end": 2},
        {"text": "猫", "start": 2, "end": 3}, {"text": "🐈", "start": 3, "end": 4},
        {"text": "。", "start": 4, "end": 5}]
    with pytest.raises(SemanticError, match="changed or omitted"):
        source_spans("猫 猫", ["猫", "猫"])
    with pytest.raises(SemanticError, match="Empty"):
        source_spans("猫", ["", "猫"])


def test_case_diagnostic_does_not_count_external_or_bridging_as_pas():
    row = {"id": "case", "ja": "猫を追う", "predicates": [{"ja": "追う", "roles": [["A1", "猫を", "cat"]]}]}
    prediction = {"text": row["ja"], "pas_labels": ["ガ", "ヲ"], "phrases": [
        {"id": 0, "start": 0, "end": 2, "head": {"start": 0, "end": 1}, "relations": []},
        {"id": 1, "start": 2, "end": 4, "head": {"start": 2, "end": 4}, "relations": [
            {"label": "ノ", "target_phrase": 0, "external": None},
            {"label": "ガ", "target_phrase": None, "external": "著者"}]}]}
    check = assess(row, prediction)["checks"][0]
    assert not check["arguments"][0]["covered_ignoring_role"]
    assert check["external_relations"][0]["external"] == "著者"
    prediction["phrases"][1]["relations"][0]["label"] = "ガ"
    check = assess(row, prediction)["checks"][0]
    assert check["arguments"][0]["covered_ignoring_role"]
    # Role-agnostic coverage deliberately retains the incompatible native label.
    assert check["arguments"][0]["covering_native_cases"] == ["ガ"]


def test_japanese_pas_saved_evidence_and_source_offsets():
    root = Path("reports/japanese-pas-v1")
    predictions = json.loads((root / "predictions.json").read_text(encoding="utf-8"))
    expected = json.loads((root / "assessment.json").read_text(encoding="utf-8"))
    rows = {path: {row["id"]: row for row in json.loads(Path(path).read_text(encoding="utf-8"))}
            for path in {p["fixture"] for p in predictions}}
    actual = []
    for prediction in predictions:
        text = prediction["text"]
        assert prediction["tokens"] == source_spans(text, [t["text"] for t in prediction["tokens"]])
        for phrase in prediction["phrases"]:
            assert text[phrase["start"]:phrase["end"]] == phrase["text"]
            assert text[phrase["head"]["start"]:phrase["head"]["end"]] == phrase["head"]["text"]
        actual.append({"fixture": prediction["fixture"], **assess(rows[prediction["fixture"]][prediction["id"]], prediction)})
    assert actual == expected
    summary = json.loads((root / "summary.json").read_text(encoding="utf-8"))
    arguments = [a for doc in actual for c in doc["checks"] for a in c["arguments"]]
    assert len(arguments) == summary["arguments_expected"]
    assert sum(a["covered_ignoring_role"] for a in arguments) == summary["arguments_covered_ignoring_role"]
