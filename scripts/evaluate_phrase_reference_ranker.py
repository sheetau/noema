"""Evaluate the corrected checkpoint on the previously observed official test split."""
import json
from pathlib import Path

from noema.definition_probe import digest
from noema.encoder import deterministic
from noema.kwdlc_phrase_references import UNIT
from noema.phrase_reference_ranker import REPORT, load_phrase_ranker
from noema.semantics import require
from scripts.evaluate_reference_ranker import training_overlap_ids
from scripts.prepare_reference_corpus import write
from scripts.train_phrase_reference_ranker import load_split, evaluate


def test_evaluation(records, head, overlap):
    remaining = [r for r in records if r["row"]["id"] not in set(overlap)]
    return {"all": {"native": evaluate(records), "selected": evaluate(records, head)},
            "without_training_text_overlap": {"native": evaluate(remaining), "selected": evaluate(remaining, head)}}


def main():
    deterministic()
    head, selection = load_phrase_ranker()
    records, statistics, manifest = load_split("test")
    require(manifest["model"] == selection["model"], "Corrected test feature model differs")
    preparation = json.loads(Path("reports/corpus-reference-v1/preparation.json").read_text(encoding="utf-8"))
    overlap = training_overlap_ids(preparation)
    require(set(overlap) <= {r["row"]["id"] for r in records}, "Test overlap inventory differs")
    results = test_evaluation(records, head, overlap)
    write(REPORT / "test-regression.json", {"alignment_unit": UNIT, "previously_observed_test": True,
          "not_an_independent_confirmation": True, "training_text_overlap_ids": overlap,
          "supervision_diagnostic": statistics, "evaluation": results,
          "selection_sha256": digest(REPORT / "selection.json"),
          "feature_report_sha256": digest("reports/reference-ranker-v1/features-test.json"),
          "corrected_test_sha256": digest("artifacts/corpus-reference-v2/test.jsonl"),
          "code_sha256": {p: digest(p) for p in ("scripts/evaluate_phrase_reference_ranker.py", "scripts/train_phrase_reference_ranker.py")}})
    print(json.dumps({group: {name: {"pair_f1": r["pair_f1"], **r["summary"]["all"]} for name, r in data.items()}
                      for group, data in results.items()}, indent=2))


if __name__ == "__main__":
    main()
