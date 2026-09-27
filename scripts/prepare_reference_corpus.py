"""Pin and audit the official KWDLC splits without redistributing corpus text."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import subprocess

from noema.definition_probe import digest
from noema.kwdlc_references import corpus_document, annotation_counts, gold_partition
from noema.semantics import require

REVISION = "c6ae49d29eca4e1134c6676d682adf5ed6a25f5a"
SOURCE = Path("artifacts/kwdlc-source")
ARTIFACTS = Path("artifacts/corpus-reference-v1")
REPORT = Path("reports/corpus-reference-v1")


def text_digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def official_splits(root):
    splits = {name: (root / "id/split_for_pas" / f"{name}.id").read_text(encoding="utf-8").splitlines()
              for name in ("train", "dev", "test")}
    all_ids = [key for ids in splits.values() for key in ids]
    require(all(all_ids) and len(all_ids) == len(set(all_ids)), "Repeated or empty official document ID")
    files = {p.stem: p for p in (root / "knp").rglob("*.knp")}
    require(set(files) == set(all_ids), "Official split and corpus document inventories differ")
    return splits, files


def write(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def main():
    import logging
    from rhoknp import Document
    logging.disable(logging.WARNING)
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--artifacts", type=Path, default=ARTIFACTS)
    parser.add_argument("--report", type=Path, default=REPORT)
    args = parser.parse_args()
    revision = subprocess.check_output(["git", "-C", str(args.source), "rev-parse", "HEAD"], text=True).strip()
    require(revision == REVISION, "Corpus revision differs")
    require(not subprocess.check_output(["git", "-C", str(args.source), "status", "--porcelain"], text=True).strip(), "Corpus checkout is modified")
    splits, files = official_splits(args.source)
    args.artifacts.mkdir(parents=True, exist_ok=False)
    args.report.mkdir(parents=True, exist_ok=False)
    summaries, records, texts = {}, [], defaultdict(list)
    for split, ids in splits.items():
        counts, types = Counter(), Counter()
        with (args.artifacts / f"{split}.jsonl").open("x", encoding="utf-8", newline="\n") as stream:
            for key in sorted(ids):
                path = files[key]
                row = corpus_document(Document.from_knp(path.read_text(encoding="utf-8")))
                require(row["id"] == key, "Corpus path and document ID differ")
                row["split"] = split
                stream.write(json.dumps(row, ensure_ascii=False) + "\n")
                counts.update(documents=1, sentences=row["sentences"], heads=len(row["heads"]),
                              explicit_plain_identity_pairs=len(gold_partition(row)[1]))
                types.update(annotation_counts(row))
                sha = text_digest(row["text"])
                texts[sha].append({"split": split, "id": key})
                records.append({"id": key, "split": split, "path": path.relative_to(args.source).as_posix(),
                                "file_sha256": digest(path), "text_sha256": sha, "characters": len(row["text"])})
        summaries[split] = {**dict(counts), "reference_annotation_types": dict(sorted(types.items()))}
    write(args.report / "preparation.json", {"source": "https://github.com/ku-nlp/KWDLC", "revision": revision,
          "source_root": args.source.as_posix(), "artifacts": args.artifacts.as_posix(),
          "split": "id/split_for_pas", "readme_sha256": digest(args.source / "README.md"),
          "split_files_sha256": {name: digest(args.source / "id/split_for_pas" / f"{name}.id") for name in splits},
          "summary": summaries, "records": records,
          "cross_split_duplicate_texts": [rows for rows in texts.values() if len({r["split"] for r in rows}) > 1],
          "code_sha256": {p: digest(p) for p in ("noema/kwdlc_references.py", "scripts/prepare_reference_corpus.py")},
          "prepared_sha256": {name: digest(args.artifacts / f"{name}.jsonl") for name in splits}})
    print(json.dumps({s: {k: v for k, v in c.items() if k != "reference_annotation_types"} for s, c in summaries.items()}))


if __name__ == "__main__":
    main()
