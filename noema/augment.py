"""Training-only surface and literal diversity; fixed evaluation rows stay intact."""
import argparse
import hashlib
import json
from pathlib import Path
import random
from .corpus_v2 import realize, frame, validate
from .dataset import load_dataset, digest
from .semantics import ROLES

NAMES = ("Ada", "Emi", "Jun", "Nao", "Riku", "Noa", "Zoe", "Omar", "Liam", "Amina", "Mei", "Luca")
QUANTITIES = (1, 2, 5, 8, 16, 31, 32, 47, 128, 1024, 12345)


def insert(text, spans, position, value):
    shifted = []
    for span in spans:
        if span["start"] < position < span["end"]:
            raise ValueError("Cannot insert punctuation inside an annotated span")
        shifted.append({**span, "start": span["start"] + (len(value) if span["start"] >= position else 0),
                        "end": span["end"] + (len(value) if span["end"] > position else 0)})
    return text[:position] + value + text[position:], shifted


def parenthesize_location(text, spans, language):
    location = next(s for s in spans if s["role"] == "location" and s["kind"] == "entity")
    start = location["start"] - (7 if language == "en" else 0)
    end = location["end"] + (0 if language == "en" else 1)
    if language == "en" and text[start:location["start"]] != "in the ":
        raise ValueError("Unexpected authored location phrase")
    text, spans = insert(text, spans, end, ")" if language == "en" else "）")
    return insert(text, spans, start, "(" if language == "en" else "（")


def partition_hash(rows, split):
    data = ''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows if r["split"] == split)
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def build(rows, variants=28):
    forbidden = {frame(r) for r in rows if r["split"] != "train" and r["supported"]}
    combinations = sorted({tuple(r["combination"]) for r in rows if r["split"] == "train" and r["supported"]}, key=str)
    texts = {(r["language"], r["text"]) for r in rows}
    added = []
    for i, combo in enumerate(combinations):
        for variant in range(variants):
            rng = random.Random(42001 + i * variants + variant)
            polarity = rng.choice(("affirmed", "negated"))
            temporal = rng.choice(("unspecified", "past", "present", "future", "today", "tomorrow", "yesterday"))
            quantities = {role: rng.choice(QUANTITIES) for role, concept in zip(ROLES, combo[1:]) if role != "location" and concept not in (None, "ag") and rng.random() < .55}
            template = "object_first" if variant % 3 == 0 and combo[-1] else rng.choice(("active", "passive"))
            name = rng.choice(NAMES)
            group = f"aug{i:04d}v{variant:03d}"
            for language in ("ja", "en"):
                text, spans, graph = realize(combo, quantities, name, polarity, temporal, language, template)
                if template == "object_first":
                    text, spans = parenthesize_location(text, spans, language)
                row = {"corpus_version": "0.2", "id": group + language, "group": group, "combination": list(combo),
                       "pattern": language + ":augmented:" + template, "split": "train", "language": language,
                       "supported": True, "text": text, "spans": spans, "graph": graph}
                key = language, text
                if frame(row) not in forbidden and key not in texts:
                    texts.add(key)
                    added.append(row)
    combined = rows + added
    validate(combined)
    for split in ("dev", "test"):
        if partition_hash(rows, split) != partition_hash(combined, split):
            raise AssertionError("Evaluation partition changed")
    return combined


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", default="artifacts/corpus-v2.jsonl")
    parser.add_argument("--output", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--variants", type=int, default=28)
    args = parser.parse_args()
    if args.variants < 1 or Path(args.output).exists() or Path(args.manifest).exists():
        parser.error("Use positive variants and new output paths")
    original = load_dataset(args.source)
    rows = build(original, args.variants)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows), encoding="utf-8", newline="\n")
    manifest = {"source_sha256": digest(args.source), "sha256": digest(args.output), "counts": validate(rows),
                "added_train_rows": len(rows) - len(original), "names": NAMES, "quantities": QUANTITIES, "variants": args.variants,
                "fixed_partitions": {s: partition_hash(rows, s) for s in ("dev", "test")},
                "evaluation_status": "The unchanged corpus-v2 test is historical regression; no new independent final validation is claimed."}
    from .training import save_json
    save_json(args.manifest, manifest)
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
