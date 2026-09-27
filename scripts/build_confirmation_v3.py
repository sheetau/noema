"""Author v3 confirmation before obtaining predictions; no model is loaded."""
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
from noema.annotation_audit import audit
from noema.challenge import examples
from noema.confirmation import build
from noema.corpus_v2 import validate
from noema.dataset import load_dataset, digest
from noema.semantics import require
from noema.training import save_json


def add_reference_cases(rows):
    result = list(rows)
    seen = {(r["language"], r["text"]) for r in rows}
    for language in ("ja", "en"):
        candidates = [r for r in rows if r["supported"] and r["language"] == language
                      and r["combination"][1] == "ag"]
        for category in ("anaphora", "ambiguous_name_or_abstract"):
            count = 0
            for original in candidates:
                subject = next(s for s in original["spans"] if s["kind"] == "entity" and s["role"] == "agent")
                if category == "anaphora":
                    word = "彼女" if language == "ja" else "her" if original["text"][:subject["start"]].endswith("by ") else "she"
                else:
                    word = {"ja": ("勇気", "幸運", "真実"), "en": ("Courage", "Luck", "Truth")}[language][count % 3]
                if language == "en" and subject["start"] == 0:
                    word = word[0].upper() + word[1:]
                text = original["text"][:subject["start"]] + word + original["text"][subject["end"]:]
                key = language, text
                if key in seen:
                    continue
                seen.add(key)
                identifier = f"confirmv3u{category}{language}{count:02d}"
                result.append({**original, "id": identifier, "group": identifier, "supported": False,
                               "category": category, "combination": None, "text": text, "spans": [], "graph": None})
                count += 1
                if count == 12:
                    break
            require(count == 12, "Not enough distinct reference cases")
    return result


def main():
    output = Path("artifacts/confirmation-v3.jsonl")
    manifest_path = Path("reports/confirmation-v3-fixture.json")
    require(not output.exists() and not manifest_path.exists(), "Preserve frozen fixtures")
    record = json.loads(Path("reports/confirmation-v3-protocol-record.json").read_text(encoding="utf-8"))
    require(digest(record["protocol"]) == record["sha256"], "Preregistered protocol changed")
    paths = ("artifacts/corpus-v8.jsonl", "artifacts/confirmation-v1.jsonl", "artifacts/confirmation-v2.jsonl")
    source = [r for p in paths for r in load_dataset(p)]
    historical = examples()
    # Hand-authored fixtures have no split/combination fields; their meanings and
    # text are checked separately rather than treated as corpus combinations.
    rows = add_reference_cases(build(source, seed=11128, names=("Maya", "Olivia", "Noel", "Dina", "Arun", "Theo"),
        quantity_values=(13, 29, 41, 97, 2048, 8192),
        unknown_words={"ja": ("カワウソ", "ハリネズミ", "鰐"), "en": ("otter", "hedgehog", "crocodile")},
        exclude_existing_meanings=True, id_prefix="confirmv3"))
    previous_text = {(r["language"], r["text"]) for r in source + historical}
    previous_graphs = {json.dumps(r["graph"], sort_keys=True) for r in source + historical if r["supported"]}
    require(not any((r["language"], r["text"]) in previous_text for r in rows), "Text overlaps previous data")
    require(not any(json.dumps(r["graph"], sort_keys=True) in previous_graphs for r in rows if r["supported"]), "Meaning overlaps previous data")
    require(len(rows) == 1392, "Preregistered total changed")
    require(len({(r["language"], r["text"]) for r in rows}) == len(rows), "Repeated confirmation text")
    counts, annotation = validate(rows), audit(rows)
    output.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows), encoding="utf-8", newline="\n")
    supported = [r for r in rows if r["supported"]]
    save_json(manifest_path, {"dataset_sha256": digest(output), "source_sha256": digest(paths[0]),
        "previous_sha256": {p: digest(p) for p in paths[1:]}, "protocol_sha256": record["sha256"],
        "created_at": datetime.now(timezone.utc).isoformat(), "counts": counts, "audit": annotation, "seed": 11128,
        "patterns": dict(Counter(r["pattern"] for r in supported)),
        "unsupported_categories": dict(Counter(r["language"] + ":" + r["category"] for r in rows if not r["supported"])),
        "category_gates": {"anaphora": .05, "ambiguous_name_or_abstract": .05},
        "text_overlap_with_earlier_data": 0, "exact_graph_overlap_with_earlier_data": 0,
        "provenance": "Prospective synthetic resampling of known pattern families; reference uncertainty strata added before predictions; not human free text"})
    print(manifest_path)


if __name__ == "__main__":
    main()
