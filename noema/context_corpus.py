"""Retain the known local annotations around an unsupported reference.

Only training annotations change. Text, IDs, development and regression remain
byte-for-byte equivalent as records. This authoring module is not used at runtime.
"""
import argparse
import copy
import json
from pathlib import Path
from .dataset import load_dataset, digest
from .surface_corpus import replace
from .augment import partition_hash
from .semantics import require


def build(rows, originals):
    lookup = {r["id"]: r for r in originals}
    result = copy.deepcopy(rows)
    for row in result:
        if row["split"] != "train" or not row["id"].startswith(("referencep", "referencea")):
            continue
        key = row["id"][10:]
        bare = key not in lookup and key.endswith("bare")
        original = lookup[key[:-4] if bare else key]
        span = next(s for s in original["spans"] if s["kind"] == "entity" and s["role"] == "agent")
        unknown, = row["unknown_spans"]
        word = row["text"][unknown["start"]:unknown["end"]]
        changed = replace(original, span["start"], span["end"], word)
        expected = changed["text"][:-1] if bare else changed["text"]
        require(expected == row["text"], "Source reconstruction changed text")
        row["known_spans"] = [s for s in changed["spans"] if not (s["kind"] == "entity" and s["role"] == "agent")]
        for s in row["known_spans"]:
            require(0 <= s["start"] < s["end"] <= len(row["text"]), "Invalid retained span")
            require(s["end"] <= unknown["start"] or s["start"] >= unknown["end"], "Known and unknown overlap")
    for split in ("dev", "test"):
        require(partition_hash(rows, split) == partition_hash(result, split), "Evaluation annotations changed")
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", default="artifacts/corpus-v8.jsonl")
    p.add_argument("--original", default="artifacts/corpus-v7.jsonl")
    p.add_argument("--output", default="artifacts/corpus-v9.jsonl")
    p.add_argument("--manifest", default="reports/corpus-v9-manifest.json")
    p.add_argument("--reuse-features", default="artifacts/corpus-v8-xlmr.pt")
    p.add_argument("--features", default="artifacts/corpus-v9-xlmr.pt")
    args = p.parse_args()
    require(all(not Path(x).exists() for x in (args.output, args.manifest, args.features)), "Preserve existing experiment files")
    rows = load_dataset(args.source)
    result = build(rows, load_dataset(args.original))
    from .training import load_cache, save_json
    import torch
    _, cache = load_cache(args.source, args.reuse_features)
    require([(r["id"], r["text"]) for r in rows] == [(r["id"], r["text"]) for r in result], "Feature inputs changed")
    Path(args.output).write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in result), encoding="utf-8", newline="\n")
    cache["dataset_sha256"] = digest(args.output)
    cache["reused_from"] = {"dataset_sha256": digest(args.source), "feature_cache": args.reuse_features,
                            "condition": "identical ordered IDs and text; training annotations only changed"}
    torch.save(cache, args.features)
    save_json(args.manifest, {"source_sha256": digest(args.source), "sha256": digest(args.output), "rows": len(result),
        "context_annotations": sum("known_spans" in r for r in result),
        "development_sha256": partition_hash(result, "dev"), "test_sha256": partition_hash(result, "test"),
        "feature_reuse": cache["reused_from"], "evaluation_status": "v1-v3 confirmation fixtures are now regression"})
    print(args.manifest)


if __name__ == "__main__":
    main()
