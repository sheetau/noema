"""Audit pretrained head probabilities on development data without fitting or tuning."""
import argparse
import json
from pathlib import Path

from noema.definition_probe import digest
from noema.head_candidates import extract_head_candidates, assess_head_candidates, summarize_head_candidates
from noema.japanese_pas_aligned import AlignedJapanesePAS
from noema.semantics import SemanticError, require
from scripts.cache_reference_features import CODE as BASE_CODE, exclusive_cache, row_digest
from scripts.prepare_reference_corpus import ARTIFACTS as CORPUS, write
from scripts.probe_corpus_references import EXPECTED_LIMITS
from scripts.train_mention_scope import forbidden_paths

ROOT = Path("artifacts/native-heads-v1")
REPORT = Path("reports/native-heads-v1")
BASELINE = Path("artifacts/reference-ranker-v1/dev")
CODE = (*BASE_CODE, "noema/head_candidates.py", "scripts/probe_native_heads.py")


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument("--resume", action="store_true")
    args = cli.parse_args()
    corpus = CORPUS / "dev.jsonl"
    rows = [json.loads(line) for line in corpus.read_text(encoding="utf-8").splitlines()]
    baseline_report = Path("reports/reference-ranker-v1/features-dev.json")
    previous = json.loads(baseline_report.read_text(encoding="utf-8"))
    require(previous["complete"] and [r["id"] for r in rows] == [r["id"] for r in previous["records"]], "Baseline inventory differs")
    ROOT.mkdir(parents=True, exist_ok=args.resume)
    REPORT.mkdir(parents=True, exist_ok=True)
    with exclusive_cache(ROOT / "cache.lock"), forbidden_paths() as guards:
        parser = AlignedJapanesePAS()
        contract = {"model": parser.metadata, "corpus_sha256": digest(corpus),
                    "baseline_report_sha256": digest(baseline_report),
                    "protocol_sha256": digest("docs/native-heads-v1-protocol.md"),
                    "code_sha256": {p: digest(p) for p in CODE}, "decision": "native_head_probability_ge_0.5"}
        manifest = ROOT / "manifest.json"
        if manifest.exists():
            require(args.resume and json.loads(manifest.read_text(encoding="utf-8")) == contract, "Head probe contract changed")
        else:
            write(manifest, contract)
        cases, inventory = [], []
        for i, (row, baseline_item) in enumerate(zip(rows, previous["records"], strict=True)):
            baseline_path = BASELINE / f"{row['id']}.json"
            require(digest(baseline_path) == baseline_item["record_sha256"], "Baseline prediction changed")
            baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
            path = ROOT / f"{row['id']}.json"
            if path.exists():
                record = json.loads(path.read_text(encoding="utf-8"))
                require(record["row_sha256"] == row_digest(row), "Head probe source changed")
            else:
                repeated = False
                try:
                    result = extract_head_candidates(parser, row["text"])
                    if i < 8:
                        require(result == extract_head_candidates(parser, row["text"]), "Native head probe is not repeatable")
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
            require(record["failure"] == baseline["failure"], "Head probe changed parser failure")
            require((record["result"]["analysis"] if record["result"] is not None else None) == baseline["prediction"],
                    "Head probe changed raw prediction")
            cases.append({**assess_head_candidates(row, record["result"]), "failure": record["failure"]})
            inventory.append({"id": row["id"], "record_sha256": digest(path), "repeated_equal": record["repeated_equal"]})
            if i % 32 == 0 or i + 1 == len(rows):
                print("native heads", i + 1, "/", len(rows), flush=True)
        report = {"split": "dev", "no_training_or_threshold_selection": True,
                  "summary": summarize_head_candidates(cases), "cases": cases,
                  "manifest_sha256": digest(manifest), "records": inventory,
                  "raw_prediction_equal": len(rows), "forbidden_path_calls": [g.call_count for g in guards]}
        final = REPORT / "evaluation.json"
        if final.exists():
            require(json.loads(final.read_text(encoding="utf-8")) == report, "Native head report changed")
        else:
            write(final, report)
        print(json.dumps(report["summary"], indent=2), flush=True)


if __name__ == "__main__":
    main()
