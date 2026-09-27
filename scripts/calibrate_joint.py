"""Calibrate joint decoding on development data with fixed existing weights."""
import argparse
import json
from pathlib import Path
import shutil
from safetensors.torch import load_file
from noema.dataset import digest
from noema.encoder import deterministic
from noema.evaluation import evaluate
from noema.structured import SequenceHeads, character_features, LABELS
from noema.joint import decode
from noema.training import load_cache, save_json
from noema.train_structured import infer, calibrate, gate


def run(dataset, features_path, checkpoint, output):
    deterministic()
    output, source = Path(output), Path(checkpoint)
    if output.exists():
        raise ValueError("Choose a new calibration directory")
    metadata = json.loads((source / "metadata.json").read_text(encoding="utf-8"))
    import noema.structured
    if (metadata.get("format") != 2 or metadata.get("architecture") != "sequence-gru-attachment"
            or metadata.get("representation") != "characters-v2" or metadata.get("labels") != LABELS
            or metadata.get("decoder_sha256") != digest(noema.structured.__file__)):
        raise ValueError("Incompatible source checkpoint or classifier implementation")
    rows, cache = load_cache(dataset, features_path)
    if metadata["encoder"] != cache["metadata"] or metadata["dataset_sha256"] != cache["dataset_sha256"]:
        raise ValueError("Calibration data/encoder mismatch")
    if metadata["weights_sha256"] != digest(source / "heads.safetensors"):
        raise ValueError("Checkpoint checksum mismatch")
    selected = [i for i, row in enumerate(rows) if row["split"] == "dev"]
    features = [character_features(rows[i]["text"], cache["features"][i]) for i in selected]
    rows = [rows[i] for i in selected]
    model = SequenceHeads(metadata["dimension"], metadata["hidden"])
    model.load_state_dict(load_file(str(source / "heads.safetensors")))
    raw = infer(model, rows, features, decoder=decode)
    thresholds, calibration = calibrate(rows, raw)
    metrics = evaluate(rows, gate(rows, raw, thresholds))
    import noema.joint
    metadata.update(decoder="joint-v1", joint_decoder_sha256=digest(noema.joint.__file__), thresholds=thresholds,
                    source_checkpoint_metadata_sha256=digest(source / "metadata.json"),
                    evaluation_status="corpus-v2 test was inspected before this change; subsequent evaluation is regression, not independent final validation")
    output.mkdir(parents=True)
    shutil.copyfile(source / "heads.safetensors", output / "heads.safetensors")
    save_json(output / "metadata.json", metadata)
    save_json(output / "development-report.json", {"metadata": metadata, "metrics": metrics, "calibration": calibration, "raw_metrics": evaluate(rows, raw)})
    save_json(output / "dev-predictions.json", [{"id": r["id"], **p} for r, p in zip(rows, raw)])
    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", default="artifacts/corpus-v2.jsonl")
    parser.add_argument("--features", required=True)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.dataset, args.features, args.checkpoint, args.output), indent=2))
