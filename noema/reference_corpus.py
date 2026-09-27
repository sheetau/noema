"""Training/development contrasts for reference ambiguity and topic marking.

These authoring rules are never used by runtime inference. Historical tests and
confirmation fixtures remain unchanged and serve only as regression evidence.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
from .annotation_audit import audit
from .augment import partition_hash
from .corpus_v2 import frame, validate
from .dataset import load_dataset, digest
from .semantics import require
from .surface_corpus import replace

PRONOUNS = {"ja": ("彼", "それ", "あれ", "その人", "あの人"), "en": ("he", "it", "this", "that")}
ABSTRACT = {"train": {"ja": ("記憶", "自由", "静寂", "知恵", "正義", "義務", "平和", "時間"),
                      "en": ("Memory", "Freedom", "Silence", "Wisdom", "Justice", "Duty", "Peace", "Time")},
            "dev": {"ja": ("運命", "信念", "喜び", "幸福"), "en": ("Destiny", "Faith", "Joy", "Happiness")}}


def outlier(row, span, word, category, serial):
    changed = replace(row, span["start"], span["end"], word)
    changed.update(id=f"reference{serial}{row['id']}", group=f"reference{serial}{row['id']}",
                   supported=False, graph=None, spans=[], combination=None, category=category,
                   pattern=row["pattern"] + ":reference:" + category,
                   unknown_spans=[{"start": span["start"], "end": span["start"] + len(word), "kind": "entity"}])
    return changed


def build(rows):
    seen = {(r["language"], r["text"]) for r in rows}
    forbidden = {frame(r) for r in rows if r["split"] != "train" and r["supported"]}
    additions, counters = [], Counter()

    def add(row):
        key = row["language"], row["text"]
        if key not in seen:
            additions.append(row)
            seen.add(key)

    for row in rows:
        if not row["supported"] or row["split"] == "test":
            continue
        split, language = row["split"], row["language"]
        counters[split, language, "all"] += 1
        if split == "train" and language == "ja" and counters[split, language, "all"] % 3 == 0:
            subjects = [s for s in row["spans"] if s["kind"] == "entity" and row["text"][s["end"]:s["end"] + 1] == "が"]
            if subjects:
                subject = subjects[0]
                changed = replace(row, subject["end"], subject["end"] + 1, "は")
                changed.update(id="topic" + row["id"], pattern="ja:reference:topic")
                if frame(changed) not in forbidden:
                    add(changed)
        # Only original active training examples; development has independent
        # surface layouts and semantic combinations. No test rows become labels.
        if split == "train" and not row["pattern"].endswith(":active"):
            continue
        spans = [s for s in row["spans"] if s["kind"] == "entity" and s["role"] == "agent" and s["concept"] == "ag"]
        if not spans or split == "dev" and counters[split, language, "names"] >= 48:
            continue
        index = counters[split, language, "names"]
        counters[split, language, "names"] += 1
        span = spans[0]
        pronoun = PRONOUNS[language][index % len(PRONOUNS[language])]
        if language == "en":
            if row["text"][:span["start"]].endswith("by ") and pronoun == "he":
                pronoun = "him"
            if span["start"] == 0:
                pronoun = pronoun.capitalize()
        abstract = ABSTRACT[split][language][index % len(ABSTRACT[split][language])]
        for serial, word, category in (("p", pronoun, "anaphora"), ("a", abstract, "ambiguous_name_or_abstract")):
            changed = outlier(row, span, word, category, serial)
            add(changed)
            if split == "train" and changed["text"][-1] in ".。":
                add({**changed, "id": changed["id"] + "bare", "group": changed["group"] + "bare", "text": changed["text"][:-1]})
    result = rows + additions
    validate(result)
    audit(result)
    require(partition_hash(rows, "test") == partition_hash(result, "test"), "Historical test changed")
    require(result[:len(rows)] == rows, "Original annotations changed")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", default="artifacts/corpus-v7.jsonl")
    parser.add_argument("--output", required=True)
    parser.add_argument("--manifest", required=True)
    args = parser.parse_args()
    require(not Path(args.output).exists() and not Path(args.manifest).exists(), "Use new output paths")
    original = load_dataset(args.source)
    rows = build(original)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows), encoding="utf-8", newline="\n")
    from .training import save_json
    manifest = {"source_sha256": digest(args.source), "sha256": digest(args.output), "counts": validate(rows), "audit": audit(rows),
                "added": dict(Counter(r["split"] + ":" + r["language"] + ":" + r.get("category", "topic") for r in rows[len(original):])),
                "fixed_test_sha256": partition_hash(rows, "test"), "development_extension": "new reference/abstract outliers only; original development rows unchanged",
                "evaluation_status": "All previously inspected tests and confirmations are regression only"}
    save_json(args.manifest, manifest)
    print(json.dumps(manifest, indent=2))
