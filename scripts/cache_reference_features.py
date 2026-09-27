"""Resumable, hash-checked CPU extraction for the official reference splits."""
import argparse
from contextlib import contextmanager
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

import torch
from safetensors.torch import load_file, save_file

from noema.definition_probe import digest
from noema.japanese_pas_aligned import AlignedJapanesePAS
from noema.reference_features import extract_reference_features
from noema.semantics import SemanticError, require
from scripts.prepare_reference_corpus import ARTIFACTS as CORPUS, REPORT as CORPUS_REPORT, write
from scripts.probe_corpus_references import EXPECTED_LIMITS
from scripts.train_mention_scope import forbidden_paths

ROOT = Path("artifacts/reference-ranker-v1")
REPORT = Path("reports/reference-ranker-v1")
CODE = ("noema/reference_features.py", "noema/japanese_pas.py", "noema/japanese_pas_aligned.py",
        "noema/character_alignment.py", "noema/preserving_word_tokenizer.py", "noema/encoder.py",
        "scripts/cache_reference_features.py")


def row_digest(row):
    return hashlib.sha256(json.dumps(row, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()


@contextmanager
def exclusive_cache(path):
    with path.open("a+b") as stream:
        stream.seek(0, 2)
        if stream.tell() == 0:
            stream.write(b" ")
            stream.flush()
        stream.seek(0)
        if sys.platform == "win32":
            import msvcrt
            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            stream.seek(0)
            if sys.platform == "win32":
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream, fcntl.LOCK_UN)


def read_cached(root, row):
    folder = root / row["split"]
    path = folder / f"{row['id']}.json"
    if not path.exists():
        return None
    record = json.loads(path.read_text(encoding="utf-8"))
    require(record["row_sha256"] == row_digest(row) and record["id"] == row["id"], "Cached reference source differs")
    features = None
    if record["failure"] is None:
        vector_path = folder / f"{row['id']}.safetensors"
        require(digest(vector_path) == record["vectors_sha256"], "Cached reference tensors changed")
        features = load_file(str(vector_path))
        require(record["prediction"]["text"] == row["text"], "Cached reference source text changed")
        require(len(features["nodes"]) == len(record["prediction"]["phrases"]), "Cached reference node count differs")
    return record, features


def save_cached(root, row, prediction, features, failure, repeated):
    folder = root / row["split"]
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{row['id']}.json"
    require(not path.exists(), "Reference cache record already committed")
    vector_sha = None
    if features is not None:
        temp = folder / f"{row['id']}.safetensors.tmp"
        final = folder / f"{row['id']}.safetensors"
        save_file({k: v.contiguous() for k, v in features.items()}, str(temp))
        temp.replace(final)  # An orphan from an interrupted write has no committed record.
        vector_sha = digest(final)
    record = {"id": row["id"], "row_sha256": row_digest(row), "prediction": prediction,
              "failure": failure, "vectors_sha256": vector_sha, "repeated_equal": repeated}
    temp = path.with_suffix(".json.tmp")
    temp.write_text(json.dumps(record, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    temp.replace(path)  # The JSON is the final commit marker for the pair.
    return record


def main():
    args_parser = argparse.ArgumentParser()
    args_parser.add_argument("--splits", nargs="+", choices=("train", "dev", "test"), default=["train", "dev"])
    args_parser.add_argument("--limit", type=int, default=None, help="Extraction smoke check only; final reports require the entire split")
    args_parser.add_argument("--resume", action="store_true")
    args_parser.add_argument("--root", type=Path, default=ROOT)
    args_parser.add_argument("--report", type=Path, default=REPORT)
    args = args_parser.parse_args()
    require(len(args.splits) == len(set(args.splits)), "Duplicate cache split")
    require(args.limit is None or args.limit > 0, "Invalid extraction limit")
    if "test" in args.splits:
        require((args.report / "selection.json").exists(), "Select the ranker before reading test predictions")
    preparation = json.loads((CORPUS_REPORT / "preparation.json").read_text(encoding="utf-8"))
    contract = {"protocol_sha256": digest("docs/reference-ranker-v1-protocol.md"),
                "preparation_sha256": digest(CORPUS_REPORT / "preparation.json"),
                "corpus_sha256": preparation["prepared_sha256"], "code_sha256": {p: digest(p) for p in CODE}}
    args.root.mkdir(parents=True, exist_ok=args.resume)
    args.report.mkdir(parents=True, exist_ok=True)
    with exclusive_cache(args.root / "cache.lock"), forbidden_paths() as guards:
        parser = AlignedJapanesePAS()
        contract["model"] = parser.metadata
        manifest = args.root / "manifest.json"
        if manifest.exists():
            require(args.resume and json.loads(manifest.read_text(encoding="utf-8")) == contract, "Reference cache contract changed")
        else:
            write(manifest, contract)
        for split in args.splits:
            corpus_path = CORPUS / f"{split}.jsonl"
            require(digest(corpus_path) == preparation["prepared_sha256"][split], "Prepared reference corpus changed")
            rows = [json.loads(line) for line in corpus_path.read_text(encoding="utf-8").splitlines()]
            selected = rows if args.limit is None else rows[:args.limit]
            previous = None
            if split == "dev":
                path = Path("artifacts/character-alignment-v1/predictions.jsonl")
                run = json.loads(Path("reports/character-alignment-v1/run.json").read_text(encoding="utf-8"))
                require(digest(path) == run["predictions_sha256"], "Previous aligned corpus predictions changed")
                previous = {r["id"]: r["prediction"] for r in (json.loads(line) for line in path.read_text(encoding="utf-8").splitlines())}
            records, reasons = [], Counter()
            for i, row in enumerate(selected):
                cached = read_cached(args.root, row)
                if cached is not None:
                    record, features = cached
                else:
                    repeated = False
                    try:
                        prediction, features = extract_reference_features(parser, row["text"])
                        failure = None
                        if i < 2:
                            again, same_features = extract_reference_features(parser, row["text"])
                            require(prediction == again and all(torch.equal(features[k], same_features[k]) for k in features), "Reference extraction is not repeatable")
                            repeated = True
                    except SemanticError as error:
                        if str(error) not in EXPECTED_LIMITS:
                            raise
                        prediction = features = None
                        failure = str(error)
                    record = save_cached(args.root, row, prediction, features, failure, repeated)
                if previous is not None:
                    require(previous[row["id"]] == record["prediction"], "Feature extraction changed baseline prediction")
                if record["failure"]:
                    reasons[record["failure"]] += 1
                records.append({"id": row["id"], "record_sha256": digest(args.root / split / f"{row['id']}.json"),
                                "vectors_sha256": record["vectors_sha256"], "failure": record["failure"],
                                "repeated_equal": record["repeated_equal"]})
                if i % 32 == 0 or i + 1 == len(selected):
                    print(split, i + 1, "/", len(rows), "cached", cached is not None, "failures", sum(reasons.values()), flush=True)
            summary = {"split": split, "documents": len(records), "expected_documents": len(rows), "complete": len(records) == len(rows),
                       "manifest_sha256": digest(manifest), "failures": dict(reasons), "records": records,
                       "forbidden_path_calls": [guard.call_count for guard in guards]}
            path = args.report / f"features-{split}.json"
            if summary["complete"]:
                if path.exists():
                    require(json.loads(path.read_text(encoding="utf-8")) == summary, "Committed feature report differs")
                else:
                    write(path, summary)
            print("split summary", split, "complete", summary["complete"], "documents", len(records), "failures", dict(reasons), flush=True)


if __name__ == "__main__":
    main()
