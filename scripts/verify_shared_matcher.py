"""Reproduce head training from recorded frozen features, without new tuning."""
import argparse
import json
from pathlib import Path

import torch
from safetensors.torch import load_file

from noema.definition_probe import digest, save
from noema.semantics import CONCEPTS, require
from noema.shared_matcher import DEV_IDS, TRAIN_IDS, SETTINGS, fit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkpoint")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    root, output = Path(args.checkpoint), Path(args.output)
    require(not output.exists(), "Choose a new verification output")
    run = json.loads((root / "run.json").read_text(encoding="utf-8"))
    require(run["status"] == "complete" and run["settings"] == SETTINGS, "Incomplete or different training run")
    for path, expected in run["source_sha256"].items():
        require(digest(path) == expected, f"Changed source: {path}")
    for filename, key in (("features.safetensors", "features_sha256"), ("selection.json", "selection_sha256"),
                          ("definitions.json", "definitions_sha256")):
        require(digest(root / filename) == run[key], f"Changed artifact: {filename}")
    rows = json.loads((root / "selection.json").read_text(encoding="utf-8"))
    require(not any(set(r["sentence_concepts"]) & DEV_IDS for r in rows["train"]), "Heldout concept leaked into training")
    require({r["expected"] for r in rows["train"]} == TRAIN_IDS, "Wrong training concepts")
    require({r["expected"] for r in rows["dev"]} == DEV_IDS, "Wrong development concepts")
    require(not {r["text"] for r in rows["train"]} & {r["text"] for r in rows["dev"]}, "Sentence leakage")
    cache = load_file(str(root / "features.safetensors"))
    bank_ids = sorted(d["id"] for d in json.loads((root / "definitions.json").read_text(encoding="utf-8")))
    train_ids, dev_ids = sorted(TRAIN_IDS), sorted(CONCEPTS)
    train_bank = cache["definitions"][[bank_ids.index(k) for k in train_ids]]
    dev_bank = cache["definitions"][[bank_ids.index(k) for k in dev_ids]]
    results = {}
    for key, rank in (("linear", 0), ("bilinear", SETTINGS["rank"])):
        recorded = json.loads((root / f"{key}-training.json").read_text(encoding="utf-8"))
        require(digest(root / f"{key}.safetensors") == recorded["weights_sha256"], "Changed weights")
        head, history = fit(cache["train"], cache["dev"], train_bank, dev_bank, rows["train"], rows["dev"],
                            train_ids, dev_ids, rank)
        weights = load_file(str(root / f"{key}.safetensors"))
        equal = all(torch.equal(v, weights[k]) for k, v in head.state_dict().items())
        same_history = all(recorded[k] == v for k, v in history.items())
        require(equal and same_history, "Repeated training changed weights or history")
        with torch.inference_mode():
            scores = head(cache["dev"], cache["definitions"])
            preds = scores.argmax(1).tolist()
        results[key] = {"weights_exact": equal, "history_exact": same_history,
                        "selected_epoch": history["selected_epoch"],
                        "post_selection_dev_with_91_candidates": {
                            lang: {"count": sum(r["language"] == lang for r in rows["dev"]),
                                   "correct": sum(bank_ids[p] == r["expected"] for p, r in zip(preds, rows["dev"]) if r["language"] == lang)}
                            for lang in ("ja", "en")}}
    output.parent.mkdir(parents=True, exist_ok=True)
    save(output, {"run_sha256": digest(root / "run.json"), "script_sha256": digest(__file__),
                  "scope": "same cached features and environment; no fresh encoder extraction or model reselection",
                  "results": results})
    print(json.dumps(results))


if __name__ == "__main__":
    main()
