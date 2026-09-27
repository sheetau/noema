"""Evaluate a known external fixture without recalibrating the checkpoint.

This command always labels its results as regression. Prospective confirmation
uses evaluate_confirmation and its preregistered manifests instead.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
from .analyzer import Analyzer
from .annotation_audit import audit
from .dataset import digest, load_dataset
from .encoder import deterministic
from .evaluation import evaluate
from .grammar import format_graph, parse
from .joint import decode
from .semantics import require
from .structured import character_features
from .train_structured import infer, gate
from .training import save_json


def fixture(dataset, expected_sha256):
    require(digest(dataset) == expected_sha256, "External regression fixture changed")
    rows = load_dataset(dataset)
    require(rows and all(r["split"] == "test" for r in rows), "Expected a nonempty test-only fixture")
    require(len({r["id"] for r in rows}) == len(rows), "Repeated fixture ID")
    require({r["language"] for r in rows} == {"ja", "en"}, "Expected both Japanese and English")
    return rows, audit(rows)


def run(dataset, expected_sha256, checkpoint, output):
    output = Path(output)
    require(not output.exists(), "Choose a new regression output directory")
    rows, annotation_audit = fixture(dataset, expected_sha256)
    deterministic()
    router = Analyzer(checkpoint, offline=True)
    output.mkdir(parents=True)
    started = datetime.now(timezone.utc).isoformat()
    provenance = {"dataset_sha256": expected_sha256, "checkpoint_metadata_sha256": digest(Path(checkpoint) / "metadata.json"),
                  "evaluation_status": "regression; the fixture has already been inspected; not independent confirmation"}
    save_json(output / "run.json", {**provenance, "started_at": started, "status": "running"})
    predictions, models, repetitions = {}, {}, {}
    for language in ("ja", "en"):
        child = Analyzer(router.routes[language], offline=True) if router.routes else router
        require(child.metadata.get("decoder") == "joint-v1", "This evaluator supports joint-v1 checkpoints")
        require(child.encoder.metadata == child.metadata["encoder"], "Runtime differs from the checkpoint environment")
        require(not any(p.requires_grad for p in child.encoder.model.parameters()), "Encoder is not frozen")
        require(not any(m.training for m in child.encoder.model.modules()), "Encoder is not in evaluation mode")
        subset = [r for r in rows if r["language"] == language]
        encoded = child.encoder.encode([r["text"] for r in subset], batch_size=32)
        features = [character_features(r["text"], f) for r, f in zip(subset, encoded)]
        raw = infer(child.heads, subset, features, decoder=decode)
        gated = gate(subset, raw, child.metadata["thresholds"])
        for row, prediction in zip(subset, gated):
            if prediction["graph"] is not None:
                require(parse(format_graph(prediction["graph"])) == prediction["graph"], "Noema round trip changed meaning")
            predictions[row["id"]] = prediction
        first = [child.analyze(r["text"], language) for r in subset[:6]]
        second = [child.analyze(r["text"], language) for r in subset[:6]]
        repetitions[language] = {"count": len(first), "full_repeat_exact": first == second,
                                 "single_vs_batch_same_meaning": all((a["status"], a["graph"]) == (b["status"], b["graph"]) for a, b in zip(first, gated[:6]))}
        models[language] = child.metadata
        print(json.dumps({"language": language, "evaluated": len(subset), "repetition": repetitions[language]}), flush=True)
    ordered = [predictions[r["id"]] for r in rows]
    strata = {}
    for row, prediction in zip(rows, ordered):
        key = (row["pattern"] if row["supported"] else row["language"] + ":" + row["category"])
        entry = strata.setdefault(key, {"total": 0, "confirmed": 0, "exact": 0})
        entry["total"] += 1
        entry["confirmed"] += prediction["status"] == "confirmed"
        entry["exact"] += row["supported"] and prediction["graph"] == row["graph"]
    metrics = evaluate(rows, ordered)
    report = {**provenance, "started_at": started, "completed_at": datetime.now(timezone.utc).isoformat(),
              "models": models, "metrics": metrics, "strata": strata, "repetition": repetitions, "audit": annotation_audit,
              "passes_regression_gate": all(metrics[l]["passes_provisional_gate"] and metrics[l]["unsupported_false_accept_rate"] <= .05 for l in ("ja", "en")),
              "reasons": {l: dict(Counter(p["diagnostics"]["reason"] or "confirmed" for r, p in zip(rows, ordered) if r["language"] == l and r["supported"])) for l in ("ja", "en")}}
    save_json(output / "report.json", report)
    save_json(output / "predictions.json", [{"id": r["id"], **p} for r, p in zip(rows, ordered)])
    save_json(output / "run.json", {**provenance, "started_at": started, "completed_at": report["completed_at"], "status": "complete", "report_sha256": digest(output / "report.json")})
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--dataset-sha256", required=True)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    report = run(args.dataset, args.dataset_sha256, args.checkpoint, args.output)
    print(json.dumps({"metrics": report["metrics"], "passes_regression_gate": report["passes_regression_gate"]}, indent=2))
