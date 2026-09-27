"""Replay the complete head-candidate audit and compare fresh raw-text predictions."""
import json
from pathlib import Path

from noema.definition_probe import digest
from noema.head_candidates import extract_head_candidates, assess_head_candidates, summarize_head_candidates
from noema.japanese_pas_aligned import AlignedJapanesePAS
from noema.semantics import SemanticError, require
from scripts.prepare_reference_corpus import ARTIFACTS as CORPUS, write
from scripts.probe_native_heads import ROOT, REPORT, BASELINE
from scripts.train_mention_scope import forbidden_paths


def main():
    report_path = REPORT / "evaluation.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    manifest = ROOT / "manifest.json"
    require(digest(manifest) == report["manifest_sha256"], "Head probe manifest changed")
    contract = json.loads(manifest.read_text(encoding="utf-8"))
    require(all(digest(path) == sha for path, sha in contract["code_sha256"].items()), "Head probe source changed")
    require(digest("docs/native-heads-v1-protocol.md") == contract["protocol_sha256"], "Head protocol changed")
    corpus = CORPUS / "dev.jsonl"
    require(digest(corpus) == contract["corpus_sha256"], "Head corpus changed")
    baseline_path = "reports/reference-ranker-v1/features-dev.json"
    require(digest(baseline_path) == contract["baseline_report_sha256"], "Head baseline report changed")
    baseline = json.loads(Path(baseline_path).read_text(encoding="utf-8"))
    rows = [json.loads(line) for line in corpus.read_text(encoding="utf-8").splitlines()]
    require([row["id"] for row in rows] == [r["id"] for r in report["records"]], "Head record inventory differs")
    cases, records = [], []
    for row, item, previous in zip(rows, report["records"], baseline["records"], strict=True):
        path = ROOT / f"{row['id']}.json"
        require(digest(path) == item["record_sha256"], "Head record changed")
        record = json.loads(path.read_text(encoding="utf-8"))
        original_path = BASELINE / f"{row['id']}.json"
        require(digest(original_path) == previous["record_sha256"], "Original prediction changed")
        original = json.loads(original_path.read_text(encoding="utf-8"))
        require((record["result"]["analysis"] if record["result"] is not None else None) == original["prediction"]
                and record["failure"] == original["failure"], "Head probe changed native analysis")
        cases.append({**assess_head_candidates(row, record["result"]), "failure": record["failure"]})
        records.append(record)
    require(cases == report["cases"] and summarize_head_candidates(cases) == report["summary"], "Head audit replay differs")
    raw = []
    with forbidden_paths() as guards:
        parser = AlignedJapanesePAS()
        require(parser.metadata == contract["model"], "Native head model changed")
        for row, record in zip(rows[:8], records[:8], strict=True):
            if record["result"] is None:
                try:
                    extract_head_candidates(parser, row["text"])
                except SemanticError as error:
                    require(str(error) == record["failure"], "Native head failure changed")
                    raw.append({"id": row["id"], "failure_equal": True})
                    continue
                raise AssertionError("Native head failure disappeared")
            actual = extract_head_candidates(parser, row["text"])
            require(actual == record["result"], "Fresh native head output differs from cache")
            require(actual == extract_head_candidates(parser, row["text"]), "Fresh native head output is not repeatable")
            raw.append({"id": row["id"], "output_equal": True, "repeated_equal": True})
        counts = [g.call_count for g in guards]
    write(REPORT / "verification.json", {"evaluation_sha256": digest(report_path), "documents_replayed": len(cases),
          "metric_validity": "invalidated_lexical_head_labels" if (REPORT / "invalidated.json").exists() else "not_a_semantic_validity_check",
          "raw": raw, "forbidden_path_calls": counts, "verification_code_sha256": digest(__file__)})
    print("Verified", len(cases), "head candidate records and", len(raw), "fresh raw inputs")


if __name__ == "__main__":
    main()
