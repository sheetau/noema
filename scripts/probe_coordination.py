"""Measure native parallel dependencies on all KWDLC dev documents."""
import argparse
import json
import logging
from pathlib import Path

from noema.coordination import corpus_coordination, extract_coordination, assess_coordination, summarize_coordination
from noema.definition_probe import digest
from noema.japanese_pas_aligned import AlignedJapanesePAS
from noema.semantics import SemanticError, require
from scripts.cache_reference_features import exclusive_cache, row_digest
from scripts.prepare_reference_corpus import SOURCE, REPORT as SOURCE_REPORT, write
from scripts.probe_corpus_references import EXPECTED_LIMITS
from scripts.train_mention_scope import forbidden_paths

ROOT = Path("artifacts/coordination-v1")
REPORT = Path("reports/coordination-v1")
BASELINE = Path("artifacts/reference-ranker-v1/dev")
CODE = ("noema/coordination.py", "noema/reference_heads.py", "scripts/probe_coordination.py")
PROTOCOL = "docs/coordination-v1-protocol.md"


def source_rows():
    from rhoknp import Document
    logging.disable(logging.WARNING)
    source_report = SOURCE_REPORT / "preparation.json"
    preparation = json.loads(source_report.read_text(encoding="utf-8"))
    corrected_report = Path("reports/corpus-reference-v2/preparation.json")
    corrected = json.loads(corrected_report.read_text(encoding="utf-8"))
    require(corrected["previous_preparation_sha256"] == digest(source_report), "Corpus preparation differs")
    corrected_path = Path("artifacts/corpus-reference-v2/dev.jsonl")
    require(digest(corrected_path) == corrected["prepared_sha256"]["dev"], "Corrected phrase corpus differs")
    corrected_rows = [json.loads(line) for line in corrected_path.read_text(encoding="utf-8").splitlines()]
    items = [item for item in preparation["records"] if item["split"] == "dev"]
    require(len(items) == len(corrected_rows) == 512, "Official development inventory differs")
    rows = []
    for item, previous in zip(items, corrected_rows, strict=True):
        path = SOURCE / item["path"]
        require(digest(path) == item["file_sha256"], "Annotated corpus source changed")
        row = corpus_coordination(Document.from_knp(path.read_text(encoding="utf-8")))
        require(row["id"] == item["id"] == previous["id"], "Corpus coordination ID differs")
        require(row["text"] == previous["text"] and row["phrases"] == previous["phrases"], "Annotated phrase spans differ")
        rows.append(row)
    return rows


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument("--resume", action="store_true")
    cli.add_argument("--verify-only", action="store_true")
    args = cli.parse_args()
    rows = source_rows()
    baseline_path = Path("reports/reference-ranker-v1/features-dev.json")
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    require(baseline["complete"] and [r["id"] for r in rows] == [r["id"] for r in baseline["records"]],
            "Raw baseline inventory differs")
    ROOT.mkdir(parents=True, exist_ok=args.resume or args.verify_only)
    REPORT.mkdir(parents=True, exist_ok=True)
    with exclusive_cache(ROOT / "cache.lock"), forbidden_paths() as guards:
        manifest_path = ROOT / "manifest.json"
        parser = None if args.verify_only else AlignedJapanesePAS()
        previous_manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else None
        require(not args.verify_only or previous_manifest is not None, "Missing coordination manifest")
        contract = {"model": parser.metadata if parser is not None else previous_manifest["model"],
                    "source_preparation_sha256": digest(SOURCE_REPORT / "preparation.json"),
                    "corrected_preparation_sha256": digest("reports/corpus-reference-v2/preparation.json"),
                    "baseline_report_sha256": digest(baseline_path), "protocol_sha256": digest(PROTOCOL),
                    "code_sha256": {p: digest(p) for p in CODE},
                    "corpus_sha256": row_digest(rows), "training": False, "threshold_selection": False}
        if previous_manifest is None:
            write(manifest_path, contract)
        else:
            require(contract == previous_manifest, "Coordination probe contract changed")
        cases, inventory = [], []
        old_report = json.loads((REPORT / "development.json").read_text(encoding="utf-8")) if args.verify_only else None
        for i, (row, prior) in enumerate(zip(rows, baseline["records"], strict=True)):
            prior_path = BASELINE / f"{row['id']}.json"
            require(digest(prior_path) == prior["record_sha256"], "Raw baseline record changed")
            prior_record = json.loads(prior_path.read_text(encoding="utf-8"))
            path = ROOT / f"{row['id']}.json"
            if path.exists():
                if args.verify_only:
                    require(digest(path) == old_report["records"][i]["record_sha256"], "Coordination record changed")
                record = json.loads(path.read_text(encoding="utf-8"))
                require(record["row_sha256"] == row_digest(row) and record["id"] == row["id"], "Coordination source changed")
            else:
                require(not args.verify_only, "Missing saved coordination record")
                repeated = False
                try:
                    result = extract_coordination(parser, row["text"])
                    if i < 8:
                        require(result == extract_coordination(parser, row["text"]), "Coordination repeat differs")
                        repeated = True
                    failure = None
                except SemanticError as error:
                    if str(error) not in EXPECTED_LIMITS:
                        raise
                    result, failure = None, str(error)
                record = {"id": row["id"], "row_sha256": row_digest(row), "result": result,
                          "failure": failure, "repeated_equal": repeated}
                temporary = path.with_suffix(".tmp")
                temporary.write_text(json.dumps(record, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
                temporary.replace(path)
            require(record["failure"] == prior_record["failure"], "Coordination changed parser failure")
            result = record["result"]
            require((result["analysis"] if result is not None else None) == prior_record["prediction"], "Coordination changed raw parser output")
            cases.append({**assess_coordination(row, result), "failure": record["failure"]})
            inventory.append({"id": row["id"], "record_sha256": digest(path), "repeated_equal": record["repeated_equal"]})
            if i % 32 == 0 or i + 1 == len(rows):
                print("coordination", i + 1, "/", len(rows), flush=True)
        report = {"split": "dev", "summary": summarize_coordination(cases), "cases": cases, "records": inventory,
                  "manifest_sha256": digest(manifest_path), "raw_prediction_equal": len(rows),
                  "forbidden_path_calls": [g.call_count for g in guards]}
        target = REPORT / "development.json"
        if target.exists():
            require(json.loads(target.read_text(encoding="utf-8")) == report, "Coordination replay differs")
        else:
            write(target, report)
        if args.verify_only:
            write(REPORT / "verification.json", {"source_rebuilt": len(rows), "saved_replayed": len(rows),
                  "report_sha256": digest(target), "manifest_sha256": digest(manifest_path),
                  "forbidden_path_calls": [g.call_count for g in guards]})
        print(json.dumps(report["summary"], indent=2), flush=True)


if __name__ == "__main__":
    main()
