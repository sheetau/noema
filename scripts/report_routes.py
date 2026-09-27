"""Combine predictions using a selection recorded before final evaluation."""
import argparse
import json
from pathlib import Path
from noema.dataset import digest, load_dataset
from noema.evaluation import evaluate
from noema.training import save_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--selection", required=True)
    parser.add_argument("--ja", required=True)
    parser.add_argument("--en", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    selection = json.loads(Path(args.selection).read_text(encoding="utf-8"))
    all_rows = load_dataset(args.dataset)
    mappings, reports = {}, {}
    for lang in ("ja", "en"):
        root = Path(getattr(args, lang))
        report = json.loads((root / "report.json").read_text(encoding="utf-8"))
        if report["metadata"]["weights_sha256"] != selection["decisions"][lang]["weights_sha256"]:
            raise ValueError("Evaluation checkpoint differs from the frozen route")
        if report["metadata"]["dataset_sha256"] != digest(args.dataset):
            raise ValueError("Evaluation data checksum mismatch")
        predictions = json.loads((root / "predictions.json").read_text(encoding="utf-8"))
        mappings[lang] = {p["id"]: p for p in predictions}
        if len(mappings[lang]) != len(predictions):
            raise ValueError("Duplicate prediction ID")
        reports[lang] = report
    if reports["ja"]["split"] != reports["en"]["split"]:
        raise ValueError("Routes used different evaluation splits")
    split = reports["ja"]["split"]
    rows = [r for r in all_rows if r["split"] == split]
    predictions = [mappings[r["language"]][r["id"]] for r in rows]
    save_json(args.output, {"selection": selection, "dataset_sha256": digest(args.dataset), "split": split,
                           "metrics": evaluate(rows, predictions), "repeat_exact": all(r["repeat_exact"] for r in reports.values()),
                           "rejection_reasons_in_scope": {l: reports[l]["rejection_reasons_in_scope"][l] for l in reports},
                           "unsupported_categories": {k: v for l, r in reports.items() for k, v in r["unsupported_categories"].items() if k.startswith(l + ":")}})


if __name__ == "__main__":
    main()
