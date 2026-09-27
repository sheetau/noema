"""General surface variation and explicitly annotated training outliers.

All transformations author training examples. Runtime inference uses none of
these word lists or grammatical realization rules.
"""
import argparse
import copy
import json
from pathlib import Path
from .annotation_audit import audit
from .augment import partition_hash
from .corpus_v2 import frame, validate, PAST
from .dataset import load_dataset, digest, VERBS
from .semantics import require

OUTLIERS = [
    ("羊", "sheep", "sheep"), ("豚", "pig", "pigs"), ("牛", "cow", "cows"), ("兎", "rabbit", "rabbits"),
    ("猿", "monkey", "monkeys"), ("虎", "tiger", "tigers"), ("狐", "fox", "foxes"), ("亀", "turtle", "turtles"),
    ("蛇", "snake", "snakes"), ("鼠", "mouse", "mice"), ("椅子", "chair", "chairs"), ("車", "car", "cars"),
    ("机", "table", "tables"), ("靴", "shoe", "shoes"), ("石", "stone", "stones"), ("鍵", "key", "keys"),
    ("箱", "box", "boxes"), ("皿", "plate", "plates"), ("林檎", "apple", "apples"), ("桃", "peach", "peaches"),
    ("鉛筆", "pencil", "pencils"), ("時計", "clock", "clocks"), ("船", "boat", "boats"), ("山羊", "goat", "goats")]


def replace(row, start, end, value):
    result = copy.deepcopy(row)
    result["text"] = row["text"][:start] + value + row["text"][end:]
    delta = len(value) - (end - start)
    for span in result["spans"]:
        if span["end"] <= start:
            continue
        if span["start"] >= end:
            span["start"] += delta
            span["end"] += delta
        elif span["start"] == start and span["end"] == end:
            span["end"] = start + len(value)
        else:
            raise ValueError("Replacement cuts an annotated span")
    return result


def compose(row, chunks):
    result = copy.deepcopy(row)
    text, spans, used = "", [], set()
    for chunk in chunks:
        if isinstance(chunk, str):
            text += chunk
            continue
        start, end = chunk
        for i, span in enumerate(row["spans"]):
            if start <= span["start"] and span["end"] <= end:
                require(i not in used, "An annotation was copied twice")
                used.add(i)
                spans.append({**span, "start": len(text) + span["start"] - start, "end": len(text) + span["end"] - start})
            else:
                require(span["end"] <= start or span["start"] >= end, "Composition cuts an annotation")
        text += row["text"][start:end]
    require(len(used) == len(row["spans"]), "Composition lost an annotation")
    result["text"], result["spans"] = text, sorted(spans, key=lambda s: s["start"])
    return result


def variations(row):
    # Sentence-final punctuation does not change the annotated proposition.
    yield "bare", replace(row, len(row["text"]) - 1, len(row["text"]), "")
    entities = {s["role"]: s for s in row["spans"] if s["kind"] == "entity"}
    if row["language"] == "en":
        capital = copy.deepcopy(row)
        capital["text"] = capital["text"][0].upper() + capital["text"][1:]
        yield "capital", capital
        if row["pattern"].endswith(":active") and "agent" in entities and "location" in entities:
            a, loc = entities["agent"], entities["location"]
            start = loc["start"] - 7
            if a["end"] < start and row["text"][start:loc["start"]] == "in the ":
                moved = compose(row, [(0, a["end"]), ", ", (start, loc["end"]), ",", (a["end"], start - 1), (loc["end"], len(row["text"]))])
                moved["text"] = moved["text"][0].upper() + moved["text"][1:]
                yield "medial_location", moved
    else:
        predicate = row["graph"]["nodes"][0]
        concept = predicate["concept"]
        if concept in ("ba", "bb", "bc") and "agent" in entities:
            end = entities["agent"]["end"]
            if row["text"][end:end + 4] == "によって":
                yield "passive_ni", replace(row, end, end + 4, "に")
        if concept in ("ba", "bb", "bc") and "agent" not in entities:
            target = entities["patient"]
            require(row["text"][target["end"]] == "が", "Expected authored passive subject marker")
            changed = replace(row, target["end"], target["end"] + 1, "を")
            pred_span = next(s for s in changed["spans"] if s["kind"] == "predicate")
            past, neg = predicate["time"]["value"] in ("past", "yesterday"), predicate["polarity"] == "negated"
            word = PAST[concept][1 if neg else 0] if past else VERBS[concept][1] + "ない" if neg else VERBS[concept][0]
            changed = replace(changed, pred_span["start"], pred_span["end"], word)
            yield "omitted_active", changed
            yield "omitted_active_bare", replace(changed, len(changed["text"]) - 1, len(changed["text"]), "")


def build(rows):
    forbidden = {frame(r) for r in rows if r["split"] != "train" and r["supported"]}
    seen = {(r["language"], r["text"]) for r in rows}
    added = []
    counts = {"ja": 0, "en": 0}
    for row in (r for r in rows if r["split"] == "train" and r["supported"]):
        index = counts[row["language"]]
        counts[row["language"]] += 1
        for kind, candidate in variations(row):
            if kind in ("bare", "capital") and index % 3:
                continue
            candidate.update(id="surface" + kind + row["id"], pattern=row["language"] + ":surface:" + kind)
            key = candidate["language"], candidate["text"]
            if key not in seen and frame(candidate) not in forbidden:
                seen.add(key)
                added.append(candidate)
        # Supervise unknown concepts at their actual span, not only at sentence level.
        eligible = [s for s in row["spans"] if s["kind"] == "entity" and s["concept"] in ("aa", "ab", "ac", "ad", "ae") and s["quantity"] == "unspecified"]
        if index % 4 == 0 and eligible:
            span = eligible[(index // 4) % len(eligible)]
            word = OUTLIERS[(index // 4) % len(OUTLIERS)][0 if row["language"] == "ja" else 1]
            candidate = replace(row, span["start"], span["end"], word)
            candidate.update(id="outlier" + row["id"], group="outlier" + row["id"], supported=False, graph=None, spans=[], combination=None,
                             category="unknown_concept", pattern=row["language"] + ":surface:unknown",
                             unknown_spans=[{"start": span["start"], "end": span["start"] + len(word), "kind": "entity"}])
            key = candidate["language"], candidate["text"]
            if key not in seen:
                seen.add(key)
                added.append(candidate)
    combined = rows + added
    validate(combined)
    audit(combined)
    require(all(partition_hash(rows, s) == partition_hash(combined, s) for s in ("dev", "test")), "Evaluation data changed")
    return combined


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", default="artifacts/corpus-v2-augmented.jsonl")
    parser.add_argument("--output", required=True)
    parser.add_argument("--manifest", required=True)
    args = parser.parse_args()
    require(not Path(args.output).exists() and not Path(args.manifest).exists(), "Choose new output paths")
    original = load_dataset(args.source)
    rows = build(original)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows), encoding="utf-8", newline="\n")
    from .training import save_json
    manifest = {"source_sha256": digest(args.source), "sha256": digest(args.output), "counts": validate(rows), "audit": audit(rows),
                "added_rows": len(rows) - len(original), "unknown_span_rows": sum(bool(r.get("unknown_spans")) for r in rows),
                "fixed_partitions": {s: partition_hash(rows, s) for s in ("dev", "test")}, "evaluation_status": "Historical corpus-v2 test remains regression only"}
    save_json(args.manifest, manifest)
    print(json.dumps(manifest, indent=2))
