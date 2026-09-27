"""Replay saved selection and evaluation, then verify the selected raw-text API."""
import json
from pathlib import Path

from safetensors.torch import load_file

from noema.definition_probe import digest
from noema.encoder import deterministic
from noema.reference_ranker import ReferenceRanker, ReferenceRankerAnalyzer, rank_references
from noema.reference_heads import frame_references
from noema.semantics import SemanticError, require
from scripts.cache_reference_features import ROOT, REPORT
from scripts.evaluate_reference_ranker import selected_head, training_overlap_ids, test_evaluation
from scripts.prepare_reference_corpus import REPORT as CORPUS_REPORT, write
from scripts.probe_reference_heads import evaluate as reference_evaluate, summarize as reference_summarize
from scripts.train_reference_ranker import load_split, evaluate
from scripts.train_mention_scope import forbidden_paths


def main():
    deterministic()
    selected, selection = selected_head()
    dev, _, _ = load_split("dev")
    expected = json.loads((REPORT / "development.json").read_text(encoding="utf-8"))
    require(evaluate(dev) == expected["native"], "Native development evaluation changed")
    for name, choice in selection["choices"].items():
        path = ROOT / f"ranker-{name}.safetensors"
        require(digest(path) == selection["weights_sha256"][name], "Reference checkpoint changed")
        head = ReferenceRanker(selection["dimension"], choice["hidden"])
        head.load_state_dict(load_file(str(path)), strict=True)
        require(evaluate(dev, head.eval(), include_decisions=True) == expected[name], "Saved development evaluation changed")
    test, _, _ = load_split("test")
    saved_test = json.loads((REPORT / "test.json").read_text(encoding="utf-8"))
    require(saved_test["selection_sha256"] == digest(REPORT / "selection.json"), "Test used another reference selection")
    require(saved_test["test_features_sha256"] == digest(REPORT / "features-test.json"), "Test features changed")
    require(all(digest(p) == sha for p, sha in saved_test["code_sha256"].items()), "Test evaluation code changed")
    preparation = json.loads((CORPUS_REPORT / "preparation.json").read_text(encoding="utf-8"))
    overlap = training_overlap_ids(preparation)
    require(overlap == saved_test["training_text_overlap_ids"], "Test overlap handling changed")
    require(test_evaluation(test, selected, overlap) == saved_test["evaluation"], "Saved test evaluation changed")
    raw_matches, regression, regression_baseline = [], [], []
    with forbidden_paths() as guards:
        analyzer = ReferenceRankerAnalyzer()
        for record in test[:8]:
            row = record["row"]
            if record["prediction"] is None:
                try:
                    analyzer.analyze(row["text"])
                except SemanticError as error:
                    require(str(error) == record["failure"], "Raw input failure changed")
                    raw_matches.append({"id": row["id"], "failure_equal": True})
                    continue
                raise AssertionError("Previously failed input no longer matches the recorded result")
            actual = analyzer.analyze(row["text"])
            ranked, decisions = rank_references(record["prediction"], record["features"], selected)
            require(actual["analysis"] == record["prediction"] and actual["ranked_prediction"] == ranked
                    and actual["reference_decisions"] == decisions, "Raw API differs from saved feature inference")
            require(analyzer.analyze(row["text"]) == actual, "Raw reference API is not repeatable")
            raw_matches.append({"id": row["id"], "prediction_equal": True, "repeated_equal": True})
        previous = json.loads(Path("reports/reference-head-v1/evidence.json").read_text(encoding="utf-8"))
        for entry in previous:
            row, baseline = entry["row"], entry["output"]
            actual = analyzer.analyze(row["text"])
            require(actual["analysis"] == baseline["analysis"], "Regression source parser changed")
            ranked = actual["ranked_prediction"]
            output = {**baseline, "analysis": ranked,
                      "references": frame_references(ranked, baseline["dependencies"]["phrases"], baseline["frames"])}
            regression.append(reference_evaluate(row, output))
            regression_baseline.append(reference_evaluate(row, baseline))
        forbidden_counts = [guard.call_count for guard in guards]
    write(REPORT / "regression.json", {"native": {"summary": reference_summarize(regression_baseline), "cases": regression_baseline},
          "selected": {"summary": reference_summarize(regression), "cases": regression},
          "selection_sha256": digest(REPORT / "selection.json"),
          "previous_evidence_sha256": digest("reports/reference-head-v1/evidence.json")})
    write(REPORT / "verification.json", {"development_replay_equal": len(dev), "test_replay_equal": len(test),
          "all_checkpoints_checked": list(selection["choices"]), "raw_matches": raw_matches,
          "regression_documents": len(regression), "forbidden_path_calls": forbidden_counts,
          "verification_code_sha256": digest(__file__)})
    print("Verified", len(dev), "development and", len(test), "test records;", len(raw_matches), "raw API cases")


if __name__ == "__main__":
    main()
