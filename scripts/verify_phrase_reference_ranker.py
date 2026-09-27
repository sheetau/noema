"""Check saved corrected metrics, raw API equivalence, and fixed handwritten regressions."""
import json
from pathlib import Path

from safetensors.torch import load_file

from noema.definition_probe import digest
from noema.encoder import deterministic
from noema.phrase_reference_ranker import ROOT, REPORT, load_phrase_ranker, PhraseReferenceRankerAnalyzer
from noema.reference_ranker import ReferenceRanker, rank_references
from noema.reference_heads import frame_references
from noema.semantics import SemanticError, require
from scripts.evaluate_phrase_reference_ranker import test_evaluation
from scripts.prepare_reference_corpus import write
from scripts.probe_reference_heads import evaluate as regression_evaluate, summarize as regression_summary
from scripts.train_phrase_reference_ranker import load_split, evaluate
from scripts.train_mention_scope import forbidden_paths


def main():
    deterministic()
    selected, selection = load_phrase_ranker()
    dev, _, _ = load_split("dev")
    development = json.loads((REPORT / "development.json").read_text(encoding="utf-8"))
    require(evaluate(dev) == development["native"], "Corrected native development replay differs")
    for name, choice in selection["choices"].items():
        path = ROOT / f"ranker-{name}.safetensors"
        require(digest(path) == selection["weights_sha256"][name], "Corrected checkpoint changed")
        head = ReferenceRanker(selection["dimension"], choice["hidden"])
        head.load_state_dict(load_file(str(path)), strict=True)
        require(evaluate(dev, head.eval()) == development[name], "Corrected checkpoint development replay differs")
    test, _, _ = load_split("test")
    regression_path = REPORT / "test-regression.json"
    saved = json.loads(regression_path.read_text(encoding="utf-8"))
    require(saved["selection_sha256"] == digest(REPORT / "selection.json"), "Regression selection differs")
    require(saved["feature_report_sha256"] == digest("reports/reference-ranker-v1/features-test.json"), "Regression features differ")
    require(saved["corrected_test_sha256"] == digest("artifacts/corpus-reference-v2/test.jsonl"), "Regression annotation source differs")
    require(all(digest(p) == sha for p, sha in saved["code_sha256"].items()), "Regression evaluation implementation changed")
    require(test_evaluation(test, selected, saved["training_text_overlap_ids"]) == saved["evaluation"], "Test regression replay differs")
    raw, regression, native_regression = [], [], []
    with forbidden_paths() as guards:
        analyzer = PhraseReferenceRankerAnalyzer()
        for record in test[:8]:
            row = record["row"]
            if record["prediction"] is None:
                try:
                    analyzer.analyze(row["text"])
                except SemanticError as error:
                    require(str(error) == record["failure"], "Raw phrase ranker failure differs")
                    raw.append({"id": row["id"], "failure_equal": True})
                    continue
                raise AssertionError("Raw phrase ranker failure disappeared")
            actual = analyzer.analyze(row["text"])
            ranked, decisions = rank_references(record["prediction"], record["features"], selected)
            require(actual["analysis"] == record["prediction"] and actual["ranked_prediction"] == ranked
                    and actual["reference_decisions"] == decisions, "Raw phrase ranker differs from saved features")
            require(analyzer.analyze(row["text"]) == actual, "Raw phrase ranker is not repeatable")
            raw.append({"id": row["id"], "output_equal": True, "repeated_equal": True})
        previous_path = Path("reports/reference-head-v1/evidence.json")
        for entry in json.loads(previous_path.read_text(encoding="utf-8")):
            row, baseline = entry["row"], entry["output"]
            actual = analyzer.analyze(row["text"])
            require(actual["analysis"] == baseline["analysis"], "Handwritten regression source parser differs")
            ranked = actual["ranked_prediction"]
            output = {**baseline, "analysis": ranked,
                      "references": frame_references(ranked, baseline["dependencies"]["phrases"], baseline["frames"])}
            regression.append(regression_evaluate(row, output))
            native_regression.append(regression_evaluate(row, baseline))
        counts = [g.call_count for g in guards]
    write(REPORT / "handwritten-regression.json", {"native": {"summary": regression_summary(native_regression), "cases": native_regression},
          "selected": {"summary": regression_summary(regression), "cases": regression},
          "source_sha256": digest(previous_path), "selection_sha256": digest(REPORT / "selection.json")})
    write(REPORT / "verification.json", {"development_replay_equal": len(dev), "test_regression_replay_equal": len(test),
          "raw": raw, "handwritten_documents": len(regression), "forbidden_path_calls": counts,
          "selection_sha256": digest(REPORT / "selection.json"), "verification_code_sha256": digest(__file__)})
    print("Verified corrected ranker:", len(dev), "development,", len(test), "test regression,", len(raw), "raw API cases")


if __name__ == "__main__":
    main()
