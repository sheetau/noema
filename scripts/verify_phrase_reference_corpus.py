"""Verify corrected annotation units, unchanged relation labels, and native metric replay."""
import json
import logging
from pathlib import Path

from noema.definition_probe import digest
from noema.kwdlc_phrase_references import corpus_phrase_document, assess_phrase_references, phrase_summary
from noema.semantics import require
from scripts.prepare_phrase_reference_corpus import ROOT, REPORT
from scripts.prepare_reference_corpus import SOURCE, ARTIFACTS as OLD_CORPUS, REPORT as OLD_REPORT, write


def main():
    from rhoknp import Document
    logging.disable(logging.WARNING)
    prep_path = REPORT / "preparation.json"
    prep = json.loads(prep_path.read_text(encoding="utf-8"))
    old_path = OLD_REPORT / "preparation.json"
    require(digest(old_path) == prep["previous_preparation_sha256"], "Original corpus provenance changed")
    old = json.loads(old_path.read_text(encoding="utf-8"))
    source_records = {r["id"]: r for r in old["records"]}
    require(all(digest(p) == sha for p, sha in prep["code_sha256"].items()), "Corrected corpus code changed")
    checked, development_rows = {}, []
    for split in ("train", "dev", "test"):
        new_path, legacy_path = ROOT / f"{split}.jsonl", OLD_CORPUS / f"{split}.jsonl"
        require(digest(new_path) == prep["prepared_sha256"][split], "Corrected corpus changed")
        require(digest(legacy_path) == old["prepared_sha256"][split], "Previous corpus changed")
        rows = [json.loads(line) for line in new_path.read_text(encoding="utf-8").splitlines()]
        legacy = [json.loads(line) for line in legacy_path.read_text(encoding="utf-8").splitlines()]
        require([r["id"] for r in rows] == [r["id"] for r in legacy], "Corrected corpus changed document inventory")
        for row, before in zip(rows, legacy, strict=True):
            require(all(row[key] == before[key] for key in ("id", "text", "sentences", "relations", "split")),
                    "Correction changed source, split, or relation annotations")
            source_record = source_records[row["id"]]
            source = SOURCE / source_record["path"]
            require(digest(source) == source_record["file_sha256"], "Original annotated source changed")
            rebuilt = {**corpus_phrase_document(Document.from_knp(source.read_text(encoding="utf-8"))), "split": split}
            require(rebuilt == row, "Corrected phrase spans do not reproduce")
        checked[split] = len(rows)
        if split == "dev":
            development_rows = rows
    evaluation_path = REPORT / "native-development.json"
    evaluation = json.loads(evaluation_path.read_text(encoding="utf-8"))
    require(all(digest(p) == sha for p, sha in evaluation["code_sha256"].items()), "Corrected evaluation code changed")
    baseline_path = Path("reports/reference-ranker-v1/features-dev.json")
    require(digest(baseline_path) == evaluation["baseline_report_sha256"], "Native prediction inventory changed")
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    cases = []
    for row, item in zip(development_rows, baseline["records"], strict=True):
        require(row["id"] == item["id"], "Native evaluation inventory differs")
        path = Path("artifacts/reference-ranker-v1/dev") / f"{row['id']}.json"
        require(digest(path) == item["record_sha256"], "Native prediction changed")
        record = json.loads(path.read_text(encoding="utf-8"))
        cases.append({**assess_phrase_references(row, record["prediction"]), "failure": record["failure"]})
    require(cases == evaluation["cases"] and phrase_summary(cases) == evaluation["summary"], "Corrected native evaluation changed")
    write(REPORT / "verification.json", {"preparation_sha256": digest(prep_path), "evaluation_sha256": digest(evaluation_path),
          "documents_rebuilt": checked, "original_text_and_relation_annotations_unchanged": True,
          "native_predictions_unchanged_and_replayed": len(cases), "verification_code_sha256": digest(__file__)})
    print("Verified", checked, "and", len(cases), "unchanged native predictions")


if __name__ == "__main__":
    main()
