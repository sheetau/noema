"""Reproduce both encoders, linear/MLP heads, and a training-size comparison.

Run from the repository root: python -m scripts.run_experiments
"""
import argparse
import json
from pathlib import Path
from noema.dataset import write_dataset
from noema.training import cache_features, train, save_json


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--models", nargs="+", choices=("minilm", "xlmr"), default=["minilm", "xlmr"])
    p.add_argument("--epochs", type=int, default=30)
    p.add_argument("--device", default="cpu")
    p.add_argument("--rerun", action="store_true", help="Replace derived checkpoints and reports after an implementation change")
    args = p.parse_args()
    dataset = "data/evaluation.jsonl"
    if not Path(dataset).exists():
        write_dataset(dataset)
    summary = {}
    for model in args.models:
        cache = f"artifacts/{model}-features.pt"
        if not Path(cache).exists():
            cache_features(dataset, cache, model, args.device)
        for architecture, fraction in (("linear", .25), ("linear", 1.), ("mlp", 1.)):
            name = f"{model}-{architecture}-{int(fraction * 100)}"
            path = Path("artifacts") / name
            existing = path / "report.json"
            if existing.exists() and not args.rerun:
                report = json.loads(existing.read_text(encoding="utf-8"))
                from noema.dataset import digest
                if report["metadata"]["dataset_sha256"] != digest(dataset) or report["metadata"]["epochs"] != args.epochs or report["metadata"].get("training_implementation") != 2:
                    raise ValueError(f"Stale run {path}; use a fresh artifacts directory")
            else:
                report = train(dataset, cache, path, architecture, args.epochs, fraction)
            summary[name] = {k: report[k] for k in ("metadata", "dev", "test")}
            save_json("reports/experiments.json", summary)
    print("Saved reports/experiments.json")


if __name__ == "__main__":
    main()
