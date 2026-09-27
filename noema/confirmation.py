"""Prospective synthetic confirmation fixtures for the frozen v6 candidates.

This is evaluation authoring, never imported by the analyzer or training code.
Its provenance explicitly distinguishes new sentences from new semantic domains.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import random
from .annotation_audit import audit
from .corpus_v2 import phrase, PAST, validate
from .dataset import VERBS, mark, unmark, load_dataset, digest
from .semantics import ROLES, make_graph, require

NAMES = ("Aiko", "Yuna", "Ken", "Mary", "Ahmed", "Iris")
QUANTITIES = (6, 9, 17, 64, 256, 2026)
TIMES = ("unspecified", "past", "present", "future", "today", "tomorrow", "yesterday")
CATEGORIES = ("unknown_concept", "quantification", "nested_scope", "multiple_events", "modality", "question")


def realize(combo, quantities, name, polarity, temporal, language, variant):
    predicate, agent, patient, recipient, location = combo
    entities = {r: {"concept": c, "quantity": quantities.get(r), "name": name if c == "ag" else None}
                for r, c in zip(ROLES, combo[1:]) if c}
    pieces = {r: phrase(e["concept"], r, language, e["quantity"], e["name"]) for r, e in entities.items()}
    a, obj, rec, loc = (pieces.get(r, "") for r in ROLES)
    ja, stem, passive, en, base, participle = VERBS[predicate]
    neg, past, future = polarity == "negated", temporal in ("past", "yesterday"), temporal in ("future", "tomorrow")
    # Alternate voice across paired realizations as well as temporal strata.
    # Both explicit-agent and omitted-agent passives must be represented.
    passive_voice = bool(obj) and (not a or (variant + (0 if temporal in ("today", "past", "future") else 1)) % 2 == 1)
    pred = lambda value: mark("predicate", value, concept=predicate)
    if language == "ja":
        time = {"today": "今日", "tomorrow": "明日", "yesterday": "昨日", "present": "今", "future": "今後"}.get(temporal)
        time = mark("time", time) if time else ""
        if passive_voice:
            verb = passive[:-1] + ("なかった" if neg and past else "ない" if neg else "た" if past else "る")
            body = obj + ("は" if variant == 0 else "が") + (a + "によって" if a else "") + (rec + "に" if rec else "")
        else:
            verb = PAST[predicate][1 if neg else 0] if past else stem + "ない" if neg else ja
            body = a + "は" + (rec + "に" if rec else "") + (obj + "を" if obj else "")
        if variant == 0:
            # Topic marking and a clause-medial location are new realization choices.
            body += (loc + "で" if loc else "") + pred(verb)
            sentence = (time + "、" if time else "") + body
            pattern = "topic_medial_location"
        else:
            if not passive_voice:
                body = (obj + "を" if obj else "") + (a + "が" if a else "") + (rec + "に" if rec else "")
            prefix = (loc + "で" if loc else "") + time
            sentence = (prefix + "、" if prefix else "") + body + pred(verb)
            pattern = "location_time_passive" if passive_voice else "location_time_active"
        sentence += "。"
    else:
        time = mark("time", "now" if temporal == "present" else temporal) if temporal in ("today", "tomorrow", "yesterday", "present") else ""
        pa, pp = quantities.get("agent") not in (None, 1), quantities.get("patient") not in (None, 1)
        location_phrase = "in " + loc if loc else ""
        if passive_voice:
            aux = "will be" if future else ("were" if pp else "was") if past else ("are" if pp else "is")
            if neg:
                aux = "will not be" if future else aux + " not"
            tail = (" to " + rec if rec else "") + (" by " + a if a else "")
            if variant == 0:
                sentence = obj + (" " + time if time else "") + " " + aux + " " + pred(participle) + (" " + location_phrase if loc else "") + tail
                pattern = "passive_location_before_agent"
            else:
                prefix = " ".join(x for x in (location_phrase, time) if x)
                sentence = (prefix + (", " if loc else " ") if prefix else "") + obj + " " + aux + " " + pred(participle) + tail
                pattern = "location_time_passive"
        else:
            if predicate == "bf":
                aux = "will be" if future else ("were" if pa else "was") if past else ("are" if pa else "is")
                if neg:
                    aux = "will not be" if future else aux + " not"
                verb = aux + " " + pred("hungry")
            elif neg:
                aux = "will not" if future else "did not" if past else "do not" if pa else "does not"
                verb = aux + " " + pred(base)
            elif future:
                verb = "will " + pred(base)
            else:
                verb = pred(PAST[predicate][2] if past else base if pa else en)
            tail = (" " + obj if obj else "") + (" to " + rec if rec else "")
            if variant == 0:
                adjunct = ", " + location_phrase + "," if loc else " " + time if time else ""
                sentence = a + adjunct + " " + verb + tail + (" " + time if time and loc else "")
                pattern = "subject_medial_location" if loc else "subject_medial_time"
            else:
                prefix = " ".join(x for x in (location_phrase, time) if x)
                sentence = (prefix + (", " if loc else " ") if prefix else "") + a + " " + verb + tail
                pattern = "location_time_active"
        sentence += "."
    text, spans = unmark(sentence)
    if language == "en":
        text = text[0].upper() + text[1:]
    return text, spans, make_graph(predicate, entities, polarity, temporal), pattern


def build(source):
    rng = random.Random(61027)
    held = {tuple(r["combination"]) for r in source if r["supported"] and r["split"] == "test"}
    trained = {tuple(r["combination"]) for r in source if r["supported"] and r["split"] == "train"}
    require(not held & trained, "Concept combinations leaked into training")
    existing = {(r["language"], r["text"], json.dumps(r["graph"], sort_keys=True)) for r in source}
    rows, meanings, seen_text = [], set(), set()
    for predicate in VERBS:
        candidates = sorted([c for c in held if c[0] == predicate], key=str)
        require(bool(candidates), "Missing held-out predicate")
        accepted = attempts = 0
        while accepted < 50:
            attempts += 1
            require(attempts < 20000, "Unable to fill the preregistered strata")
            combo = rng.choice(candidates)
            temporal = rng.choice(TIMES if combo[-1] else TIMES[4:])
            polarity = rng.choice(("affirmed", "negated"))
            quantities = {r: rng.choice(QUANTITIES) for r, c in zip(ROLES, combo[1:]) if r != "location" and c not in (None, "ag") and rng.random() < .45}
            name = rng.choice(NAMES)
            group = f"confirm{predicate}{accepted:03d}"
            batch = []
            for language in ("ja", "en"):
                for variant in (0, 1):
                    text, spans, graph, pattern = realize(combo, quantities, name, polarity, temporal, language, variant)
                    batch.append({"corpus_version": "0.2", "id": group + language + str(variant), "group": group, "split": "test",
                                  "language": language, "supported": True, "combination": list(combo), "pattern": language + ":confirmation:" + pattern,
                                  "text": text, "spans": spans, "graph": graph})
            signature = json.dumps(batch[0]["graph"], sort_keys=True)
            keys = [(r["language"], r["text"]) for r in batch]
            if (signature in meanings or len(set(keys)) != 4 or any(k in seen_text for k in keys)
                    or any((r["language"], r["text"], signature) in existing for r in batch)):
                continue
            meanings.add(signature)
            seen_text.update(keys)
            rows.extend(batch)
            accepted += 1
    for language in ("ja", "en"):
        examples = [r for r in rows if r["language"] == language and r["supported"] and any(s["kind"] == "entity" and s["concept"] == "aa" and s["quantity"] == "unspecified" for s in r["spans"])]
        require(len(examples) >= 12, "Need enough controlled negative seeds")
        for category in CATEGORIES:
            for i, original in enumerate(examples[:12]):
                text = original["text"]
                dog = next(s for s in original["spans"] if s["kind"] == "entity" and s["concept"] == "aa")
                if category == "unknown_concept":
                    word = ("熊", "象", "鹿")[i % 3] if language == "ja" else ("bear", "elephant", "deer")[i % 3]
                    text = text[:dog["start"]] + word + text[dog["end"]:]
                elif category == "quantification":
                    if language == "ja":
                        text = text[:dog["start"]] + "全ての" + text[dog["start"]:]
                    else:
                        start = dog["start"] - 4
                        require(text[start:dog["start"]].lower() == "the ", "Quantifier requires an article")
                        text = text[:start] + ("Every " if start == 0 else "every ") + text[dog["start"]:]
                elif category == "nested_scope":
                    if language == "en" and text.split()[0] in ("The", "In", "Today", "Tomorrow", "Yesterday", "Now"):
                        text = text[0].lower() + text[1:]
                    text = text.rstrip("。.") + "とは限らない。" if language == "ja" else "It is not necessarily true that " + text
                elif category == "multiple_events":
                    text += "猫も眠る。" if language == "ja" else " The cat also sleeps."
                elif category == "modality":
                    if language == "en" and text.split()[0] in ("The", "In", "Today", "Tomorrow", "Yesterday", "Now"):
                        text = text[0].lower() + text[1:]
                    text = ("もしかすると" if language == "ja" else "Maybe ") + text
                else:
                    text = text.rstrip("。.") + ("のですか？" if language == "ja" else "?")
                rows.append({**original, "id": f"confirmu{category}{language}{i:02d}", "group": f"confirmu{category}{language}{i:02d}",
                             "supported": False, "category": category, "combination": None, "text": text, "spans": [], "graph": None})
    validate(rows)
    audit(rows)
    for language in ("ja", "en"):
        subset = [r for r in rows if r["language"] == language]
        require(sum(r["supported"] for r in subset) == 600 and len(subset) == 672, "Preregistered sample size mismatch")
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", default="artifacts/corpus-v2-augmented.jsonl")
    parser.add_argument("--output", required=True)
    parser.add_argument("--manifest", required=True)
    args = parser.parse_args()
    require(not Path(args.output).exists() and not Path(args.manifest).exists(), "Preserve previous confirmation data")
    record = json.loads(Path("reports/confirmation-protocol-record.json").read_text(encoding="utf-8"))
    require(digest(record["protocol"]) == record["sha256"], "Preregistered protocol changed")
    rows = build(load_dataset(args.source))
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows), encoding="utf-8", newline="\n")
    manifest = {"dataset_sha256": digest(args.output), "source_sha256": digest(args.source), "protocol_sha256": record["sha256"],
                "route_metadata_sha256": digest("artifacts/routed-v6/metadata.json"), "selection_sha256": digest("reports/routed-v6-selection.json"),
                "counts": validate(rows), "audit": audit(rows), "seed": 61027,
                "patterns": dict(Counter(r["pattern"] for r in rows if r["supported"])),
                "provenance": "new synthetic sentences under a preregistered protocol; semantic combinations were previously inspected but never trained"}
    from .training import save_json
    save_json(args.manifest, manifest)
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
