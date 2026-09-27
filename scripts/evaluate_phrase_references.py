"""Re-evaluate unchanged native development predictions at actual annotation units."""
import json
from pathlib import Path

from noema.definition_probe import digest
from noema.kwdlc_phrase_references import assess_phrase_references, phrase_summary, UNIT
from noema.semantics import require
from scripts.prepare_phrase_reference_corpus import ROOT, REPORT
from scripts.prepare_reference_corpus import write


def main():
    preparation = json.loads((REPORT / "preparation.json").read_text(encoding="utf-8"))
    path = ROOT / "dev.jsonl"
    require(digest(path) == preparation["prepared_sha256"]["dev"], "Phrase corpus changed")
    baseline_path = Path("reports/reference-ranker-v1/features-dev.json")
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    require([r["id"] for r in rows] == [r["id"] for r in baseline["records"]], "Phrase evaluation inventory differs")
    cases = []
    for row, item in zip(rows, baseline["records"], strict=True):
        path = Path("artifacts/reference-ranker-v1/dev") / f"{row['id']}.json"
        require(digest(path) == item["record_sha256"], "Native prediction changed")
        record = json.loads(path.read_text(encoding="utf-8"))
        cases.append({**assess_phrase_references(row, record["prediction"]), "failure": record["failure"]})
    write(REPORT / "native-development.json", {"alignment_unit": UNIT, "split": "dev",
          "summary": phrase_summary(cases), "cases": cases, "prepared_sha256": preparation["prepared_sha256"]["dev"],
          "baseline_report_sha256": digest(baseline_path), "predictions_reused_without_modification": True,
          "code_sha256": {p: digest(p) for p in ("noema/kwdlc_phrase_references.py", "noema/kwdlc_references.py",
                                                "scripts/evaluate_phrase_references.py")}})
    print(json.dumps(phrase_summary(cases), indent=2))


if __name__ == "__main__":
    main()
