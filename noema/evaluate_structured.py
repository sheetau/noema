"""Evaluate a frozen sequence checkpoint without training or test calibration."""
import argparse
from collections import Counter
import json
from pathlib import Path
import torch
from safetensors.torch import load_file
from .dataset import digest
from .encoder import deterministic
from .evaluation import evaluate
from .structured import SequenceHeads, LABELS, character_features, decode
from .training import load_cache, save_json
from .train_structured import infer, gate


def run(dataset, features_path, checkpoint, split="dev"):
    if split not in ("dev", "test"):
        raise ValueError("Evaluation requires dev or test")
    deterministic()
    path = Path(checkpoint)
    meta = json.loads((path / "metadata.json").read_text(encoding="utf-8"))
    if (meta.get("format") != 2 or meta.get("architecture") != "sequence-gru-attachment"
            or meta.get("representation") != "characters-v2" or meta.get("labels") != LABELS):
        raise ValueError("Incompatible sequence checkpoint")
    if meta.get("decoder_sha256") != digest(Path(__file__).with_name("structured.py")):
        raise ValueError("Decoder differs from calibrated checkpoint")
    decoder = decode
    if meta.get("decoder", "independent-v4") not in ("independent-v4", "joint-v1"):
        raise ValueError("Unsupported decoder")
    if meta.get("decoder") == "joint-v1":
        if meta.get("joint_decoder_sha256") != digest(Path(__file__).with_name("joint.py")):
            raise ValueError("Joint decoder differs from calibrated checkpoint")
        from .joint import decode as decoder
    if meta["weights_sha256"] != digest(path / "heads.safetensors"):
        raise ValueError("Checkpoint checksum mismatch")
    rows, cache = load_cache(dataset, features_path)
    if meta["dataset_sha256"] != cache["dataset_sha256"] or meta["encoder"] != cache["metadata"]:
        raise ValueError("Evaluation data/encoder differs from the frozen experiment")
    selected = [i for i, row in enumerate(rows) if row["split"] == split]
    features = [character_features(rows[i]["text"], cache["features"][i]) for i in selected]
    rows = [rows[i] for i in selected]
    model = SequenceHeads(meta["dimension"], meta["hidden"])
    model.load_state_dict(load_file(str(path / "heads.safetensors")))
    raw = infer(model, rows, features, decoder=decoder)
    gated = gate(rows, raw, meta["thresholds"])
    repeated = infer(model, rows[:16], features[:16], decoder=decoder)
    first = infer(model, rows[:16], features[:16], decoder=decoder)
    reasons = {lang: dict(Counter(p["diagnostics"]["reason"] or "confirmed" for r, p in zip(rows, gated) if r["language"] == lang and r["supported"])) for lang in ("ja", "en")}
    categories = {}
    for row, pred in zip(rows, gated):
        if not row["supported"]:
            key = row["language"] + ":" + row.get("category", "unspecified")
            value = categories.setdefault(key, {"total": 0, "false_accepts": 0})
            value["total"] += 1
            value["false_accepts"] += pred["status"] == "confirmed"
    report = {"metadata": meta, "split": split, "metrics": evaluate(rows, gated), "raw_metrics": evaluate(rows, raw),
              "rejection_reasons_in_scope": reasons, "unsupported_categories": categories,
              "repeat_exact": first == repeated, "repeat_probe_count": len(first),
              "selection": "thresholds and checkpoint fixed on development data; no evaluation-time calibration",
              "evaluation_status": meta.get("evaluation_status", "original frozen experiment")}
    return report, [{"id": r["id"], **p} for r, p in zip(rows, gated)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", default="artifacts/corpus-v2.jsonl")
    parser.add_argument("--features", required=True)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--split", choices=("dev", "test"), default="dev")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = Path(args.output)
    if output.exists():
        parser.error("Use a new output directory to preserve previous evaluation reports")
    report, predictions = run(args.dataset, args.features, args.checkpoint, args.split)
    save_json(output / "report.json", report)
    save_json(output / "predictions.json", predictions)
    print(json.dumps(report["metrics"], indent=2))


if __name__ == "__main__":
    main()
