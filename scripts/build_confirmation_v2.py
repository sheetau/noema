"""Author the preregistered v2 cases; never load a model or its predictions."""
import argparse
from collections import Counter
import json
from pathlib import Path
from noema.annotation_audit import audit
from noema.confirmation import build
from noema.corpus_v2 import validate
from noema.dataset import load_dataset, digest
from noema.semantics import require
from noema.training import save_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", default="artifacts/corpus-v7.jsonl")
    parser.add_argument("--previous", default="artifacts/confirmation-v1.jsonl")
    parser.add_argument("--output", default="artifacts/confirmation-v2.jsonl")
    parser.add_argument("--manifest", default="reports/confirmation-v2-fixture.json")
    args = parser.parse_args()
    require(not Path(args.output).exists() and not Path(args.manifest).exists(), "Preserve previous confirmation files")
    record = json.loads(Path("reports/confirmation-v2-protocol-record.json").read_text(encoding="utf-8"))
    require(digest(record["protocol"]) == record["sha256"], "Confirmation v2 protocol changed")
    source = load_dataset(args.source) + load_dataset(args.previous)
    rows = build(source, seed=91028, names=("Lewis", "Eva", "Nina", "Kenji", "Samira", "Leon"),
                 quantity_values=(11, 19, 37, 73, 512, 4096),
                 unknown_words={"ja": ("狼", "栗鼠", "ハムスター"), "en": ("wolf", "squirrel", "hamster")},
                 exclude_existing_meanings=True, id_prefix="confirmv2")
    previous_text = {(r["language"], r["text"]) for r in source}
    require(not any((r["language"], r["text"]) in previous_text for r in rows), "Confirmation text overlaps earlier data")
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows), encoding="utf-8", newline="\n")
    supported = [r for r in rows if r["supported"]]
    strata = {"polarity": dict(Counter(r["graph"]["nodes"][0]["polarity"] for r in supported)),
              "time": dict(Counter(r["graph"]["nodes"][0]["time"]["value"] for r in supported)),
              "omitted_agent": sum(r["combination"][1] is None for r in supported),
              "without_quantity": sum(all(n.get("quantity") is None for n in r["graph"]["nodes"]) for r in supported)}
    manifest = {"dataset_sha256": digest(args.output), "source_sha256": digest(args.source), "previous_sha256": digest(args.previous),
                "protocol_sha256": record["sha256"], "counts": validate(rows), "audit": audit(rows), "seed": 91028,
                "patterns": dict(Counter(r["pattern"] for r in supported)), "strata": strata,
                "text_overlap_with_earlier_data": 0, "exact_graph_overlap_with_earlier_data": 0,
                "provenance": "Prospective synthetic resampling of known pattern families after v1 failure; new complete graphs and sentences, not human-authored free text"}
    save_json(args.manifest, manifest)
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
