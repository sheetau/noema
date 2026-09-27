"""Author preregistered v4 fixtures without loading a model."""
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
from noema.annotation_audit import audit
from noema.challenge import examples
from noema.confirmation import build, realize
from noema.corpus_v2 import validate
from noema.dataset import load_dataset, digest
from noema.semantics import require
from noema.training import save_json
from scripts.build_confirmation_v3 import add_reference_cases


def main():
    output = Path("artifacts/confirmation-v4.jsonl")
    manifest = Path("reports/confirmation-v4-fixture.json")
    require(not output.exists() and not manifest.exists(), "Preserve frozen fixtures")
    record = json.loads(Path("reports/confirmation-v4-protocol-record.json").read_text(encoding="utf-8"))
    require(digest(record["protocol"]) == record["sha256"], "Protocol changed")
    paths = ["artifacts/corpus-v9.jsonl"] + [f"artifacts/confirmation-v{i}.jsonl" for i in (1, 2, 3)]
    source = [r for path in paths for r in load_dataset(path)]
    # Held-out positive combinations have no named agent for giving or hunger.
    # Author separate reference replacement seeds; never add them as positives.
    seeds = []
    for combo in (("bd", "ag", "af", "ac", "ah"), ("bf", "ag", None, None, "ai")):
        for language in ("ja", "en"):
            for variant in (0, 1):
                text, spans, graph, pattern = realize(combo, {}, "Hugo", "affirmed", "tomorrow", language, variant)
                seeds.append({"corpus_version": "0.2", "split": "test", "language": language,
                              "supported": True, "combination": list(combo), "pattern": language + ":confirmation:" + pattern,
                              "text": text, "spans": spans, "graph": graph})
    rows = add_reference_cases(build(source, seed=15129, names=("Hugo", "Stella", "Omar", "Yuki", "Nora", "Emil"),
        quantity_values=(23, 31, 47, 89, 1024, 16384),
        unknown_words={"ja": ("アザラシ", "アライグマ", "アナグマ"), "en": ("seal", "raccoon", "badger")},
        exclude_existing_meanings=True, id_prefix="confirmv4"),
        abstracts={"ja": ("驚異", "武勇", "宿命"), "en": ("Wonder", "Valor", "Fate")},
        stratified=True, id_prefix="confirmv4", reference_seeds=seeds)
    previous_text = {(r["language"], r["text"]) for r in source + examples()}
    previous_graphs = {json.dumps(r["graph"], sort_keys=True) for r in source + examples() if r["supported"]}
    require(not any((r["language"], r["text"]) in previous_text for r in rows), "Text overlaps previous data")
    require(not any(json.dumps(r["graph"], sort_keys=True) in previous_graphs for r in rows if r["supported"]), "Meaning overlaps previous data")
    require(len(rows) == 1392 and len({(r["language"], r["text"]) for r in rows}) == len(rows), "Size or uniqueness mismatch")
    counts, annotation = validate(rows), audit(rows)
    output.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows), encoding="utf-8", newline="\n")
    save_json(manifest, {"dataset_sha256": digest(output), "source_sha256": digest(paths[0]),
        "previous_sha256": {p: digest(p) for p in paths[1:]}, "protocol_sha256": record["sha256"],
        "created_at": datetime.now(timezone.utc).isoformat(), "counts": counts, "audit": annotation, "seed": 15129,
        "patterns": dict(Counter(r["pattern"] for r in rows if r["supported"])),
        "unsupported_categories": dict(Counter(r["language"] + ":" + r["category"] for r in rows if not r["supported"])),
        "category_gates": {"anaphora": .05, "ambiguous_name_or_abstract": .05},
        "text_overlap_with_earlier_data": 0, "exact_graph_overlap_with_earlier_data": 0,
        "provenance": "Prospective synthetic resampling of known pattern families with six-predicate reference strata; not human free text"})
    print(manifest)


if __name__ == "__main__":
    main()
