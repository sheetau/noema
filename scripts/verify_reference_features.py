"""Verify cached reference tensors and their correspondence to native links."""
import argparse
import json
from pathlib import Path

import torch

from noema.definition_probe import digest
from noema.reference_ranker import scalar_features, reference_targets
from noema.semantics import require
from scripts.cache_reference_features import ROOT, CORPUS, read_cached
from scripts.prepare_reference_corpus import write


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--split", choices=("train", "dev"), required=True)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest_path = args.root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    require(all(digest(p) == sha for p, sha in manifest["code_sha256"].items()), "Reference extraction source changed")
    path = CORPUS / f"{args.split}.jsonl"
    require(digest(path) == manifest["corpus_sha256"][args.split], "Reference corpus changed")
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    chosen = rows if args.limit is None else rows[:args.limit]
    records, links, counts = [], 0, {}
    for row in chosen:
        cached = read_cached(args.root, row)
        require(cached is not None, "Requested reference document has not been extracted")
        record, features = cached
        if features is not None:
            require(bool(torch.isfinite(scalar_features(features)).all()), "Invalid reference scalar features")
            _, statistics = reference_targets(row, record["prediction"])
            for key, value in statistics.items():
                counts[key] = counts.get(key, 0) + value
            for index, phrase in enumerate(record["prediction"]["phrases"]):
                for relation in phrase["relations"]:
                    if relation["label"] == "=" and relation["target_phrase"] is not None:
                        column = relation["target_phrase"] + 1
                        require(column <= index, "Native reference is not to a previous phrase")
                        require(float(features["native"][index, column]) == float(features["native"][index, :index + 1].max()),
                                "Captured native scores differ from predicted reference")
                        links += 1
        records.append({"id": row["id"], "record_sha256": digest(args.root / args.split / f"{row['id']}.json"),
                        "vectors_sha256": record["vectors_sha256"], "failure": record["failure"]})
    write(args.output, {"split": args.split, "documents": len(chosen), "expected_documents": len(rows),
          "complete_split": len(chosen) == len(rows), "native_positive_links_equal": links, "supervision": counts,
          "manifest_sha256": digest(manifest_path), "records": records,
          "verification_code_sha256": {p: digest(p) for p in ("scripts/verify_reference_features.py", "noema/reference_ranker.py")}})
    print("Verified", len(chosen), "documents and", links, "native reference links")


if __name__ == "__main__":
    main()
