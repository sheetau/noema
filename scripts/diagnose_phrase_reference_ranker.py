"""Diagnose residual errors with corrected phrase endpoints; do not tune the model."""
import json

from noema.definition_probe import digest
from noema.encoder import deterministic
from noema.kwdlc_phrase_references import UNIT, span_metric_inputs
from noema.phrase_reference_ranker import REPORT, load_phrase_ranker
from noema.reference_ranker import rank_references
from scripts.diagnose_reference_ranker import compare_partitions, summarize
from scripts.prepare_reference_corpus import write
from scripts.train_phrase_reference_ranker import load_split


def main():
    deterministic()
    head, _ = load_phrase_ranker()
    records, _, _ = load_split("dev")
    cases = []
    for record in records:
        native = record["prediction"]
        ranked = rank_references(native, record["features"], head)[0] if native is not None else None
        row, native_view = span_metric_inputs(record["row"], native)
        _, ranked_view = span_metric_inputs(record["row"], ranked)
        cases.append(compare_partitions(row, native_view, ranked_view))
    report = {"alignment_unit": UNIT, "split": "dev", "purpose": "post_selection_diagnostic_only",
              "summary": summarize(cases), "cases": cases,
              "selection_sha256": digest(REPORT / "selection.json"),
              "code_sha256": {p: digest(p) for p in ("scripts/diagnose_phrase_reference_ranker.py", "scripts/diagnose_reference_ranker.py")}}
    write(REPORT / "development-diagnostic.json", report)
    print(json.dumps(report["summary"], indent=2))


if __name__ == "__main__":
    main()
