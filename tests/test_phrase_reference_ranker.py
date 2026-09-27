import copy
import json

import pytest

torch = pytest.importorskip("torch")
from noema.kwdlc_phrase_references import UNIT
from noema.phrase_reference_ranker import phrase_targets, load_phrase_ranker
from noema.semantics import SemanticError
from scripts.train_phrase_reference_ranker import training_record, evaluate
from scripts.train_reference_ranker import fit


def fixture():
    text = '「A」B'
    tokens = [{"text": t, "start": i, "end": i + 1} for i, t in enumerate(text)]
    row = {"id": "example", "split": "train", "text": text, "alignment_unit": UNIT,
           "phrases": [{"id": 0, "start": 0, "end": 3}, {"id": 1, "start": 3, "end": 4}],
           "relations": [{"source": 1, "target": 0, "type": "=", "mode": None, "external": None}]}
    prediction = {"text": text, "tokens": tokens, "phrases": [
        {**row["phrases"][0], "head": tokens[1], "relations": []},
        {**row["phrases"][1], "head": tokens[3], "relations": [{"label": "=", "target_phrase": 0, "external": None}]}]}
    features = {"nodes": torch.zeros(2, 4), "native": torch.zeros(2, 3), "word_indices": torch.tensor([1, 3]),
                "word_count": torch.tensor(4)}
    legacy = {**row, "heads": [{"id": 0, **tokens[0]}, {"id": 1, **tokens[3]}]}
    cached = {"prediction": prediction, "failure": None}
    return row, legacy, cached, features


def test_corrected_targets_ignore_invented_gold_heads_and_native_head_positions():
    row, legacy, cached, features = fixture()
    record, counts = training_record(row, legacy, cached, features)
    assert record["target"].tolist() == [[True, False, False], [False, True, False]]
    assert counts["positive"] == 1 and counts["unmatched_source"] == counts["missing_antecedent"] == 0
    legacy["heads"] = [{"start": 999, "end": 1000}]
    again, _ = training_record(row, legacy, cached, features)
    assert torch.equal(again["target"], record["target"])
    changed = copy.deepcopy(cached["prediction"])
    changed["phrases"][0]["head"] = changed["tokens"][0]
    assert torch.equal(phrase_targets(row, changed)[0], record["target"])


def test_boundary_mismatch_still_excludes_loss_and_remains_in_evaluation():
    row, legacy, cached, features = fixture()
    cached["prediction"]["phrases"][0]["start"] = 1
    record, counts = training_record(row, legacy, cached, features)
    assert not record["target"].any()
    assert counts["unmatched_source"] == counts["missing_antecedent"] == 1
    assessment = evaluate([record])["summary"]["all"]
    assert assessment["gold_pairs"] == assessment["missing_pairs"] == 1
    assert assessment["missing_phrases"] == 1 and assessment["document_exact"] == 0


def test_changed_annotations_and_vector_phrase_mapping_are_rejected():
    row, legacy, cached, features = fixture()
    legacy = copy.deepcopy(legacy)
    legacy["relations"] = []
    with pytest.raises(SemanticError, match="source or relations"):
        training_record(row, legacy, cached, features)
    row, legacy, cached, features = fixture()
    features["word_indices"] = torch.tensor([0, 3])
    with pytest.raises(SemanticError, match="node vectors"):
        training_record(row, legacy, cached, features)


def test_shared_fit_selects_using_phrase_evaluator_and_is_reproducible():
    row, legacy, cached, features = fixture()
    before = copy.deepcopy(cached["prediction"])
    record, _ = training_record(row, legacy, cached, features)
    first, choice, history = fit([record], [record], 2, 0, epochs=2, batch_size=1, evaluate_fn=evaluate)
    second, same_choice, same_history = fit([record], [record], 2, 0, epochs=2, batch_size=1, evaluate_fn=evaluate)
    assert choice == same_choice and history == same_history
    assert all(torch.equal(value, second.state_dict()[name]) for name, value in first.state_dict().items())
    assert "gold_phrases" in history[0]["dev_summary"]["all"] and "gold_heads" not in history[0]["dev_summary"]["all"]
    assert cached["prediction"] == before


def test_loader_refuses_unmarked_legacy_units_and_invalidated_runs(tmp_path):
    report = tmp_path / "report"
    report.mkdir()
    (report / "selection.json").write_text(json.dumps({"alignment_unit": "lexical_head"}), encoding="utf-8")
    (report / "training.json").write_text(json.dumps({"alignment_unit": UNIT}), encoding="utf-8")
    with pytest.raises(SemanticError, match="annotation unit"):
        load_phrase_ranker(tmp_path, report)
    (report / "invalidated.json").write_text('{}', encoding="utf-8")
    with pytest.raises(SemanticError, match="invalidated"):
        load_phrase_ranker(tmp_path, report)


def test_regression_overlap_filter_preserves_failed_document_and_gold_phrase_pairs():
    from noema.reference_ranker import ReferenceRanker
    from scripts.evaluate_phrase_reference_ranker import test_evaluation as evaluate_test
    row, legacy, cached, features = fixture()
    record, _ = training_record(row, legacy, cached, features)
    kept = copy.deepcopy(record)
    kept["row"]["id"] = "kept"
    failed = {**kept, "row": {**kept["row"], "id": "failed"}, "prediction": None,
              "features": None, "target": None, "failure": "context exceeded"}
    head = ReferenceRanker(2)
    for parameter in head.parameters():
        parameter.data.zero_()
    assessment = evaluate_test([record, kept, failed], head, [record["row"]["id"]])
    counts = assessment["without_training_text_overlap"]["selected"]["summary"]["all"]
    assert counts["documents"] == 2 and counts["parsed"] == 1
    assert counts["gold_phrases"] == 4 and counts["missing_phrases"] == 2
    assert counts["gold_pairs"] == counts["missing_pairs"] == 2
