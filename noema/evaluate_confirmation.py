"""Run a preregistered confirmation without training, calibration or selection."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
from .analyzer import Analyzer
from .annotation_audit import audit
from .dataset import load_dataset, digest
from .encoder import deterministic
from .evaluation import evaluate, category_gates
from .grammar import parse, format_graph
from .semantics import require
from .structured import character_features
from .joint import decode
from .train_structured import infer, gate
from .training import save_json


def verify_inputs(dataset, manifest, checkpoint, protocol, selection):
    recorded = json.loads(Path(manifest).read_text(encoding="utf-8"))
    for path, expected in ((dataset, "dataset_sha256"), (protocol, "protocol_sha256"),
                           (Path(checkpoint) / "metadata.json", "route_metadata_sha256"), (selection, "selection_sha256")):
        require(digest(path) == recorded[expected], f"Frozen confirmation input changed: {path}")
    rows = load_dataset(dataset)
    if "review" in recorded:
        require(digest(recorded["review"]) == recorded["review_sha256"], "Frozen annotation review changed")
    require(all(r["split"] == "test" for r in rows), "Confirmation must have no training or development partition")
    require(audit(rows) == recorded["audit"], "Confirmation annotation audit changed")
    return rows, recorded


def run(dataset, manifest, checkpoint, protocol, selection, output):
    output = Path(output)
    require(not output.exists(), "Preserve previous confirmation runs; use a new output directory")
    rows, recorded = verify_inputs(dataset, manifest, checkpoint, protocol, selection)
    deterministic()
    analyzer = Analyzer(checkpoint, offline=True)
    require(analyzer.routes is not None, "Expected a frozen language routing manifest")
    output.mkdir(parents=True)
    started = datetime.now(timezone.utc).isoformat()
    save_json(output / "run.json", {"started_at": started, "manifest": recorded, "status": "running"})
    predictions, models, repetitions = {}, {}, {}
    for language in ("ja", "en"):
        child = Analyzer(analyzer.routes[language], offline=True)
        require(child.metadata.get("decoder") == "joint-v1", "Confirmation protocol requires the frozen joint decoder")
        require(child.encoder.metadata == child.metadata["encoder"], "Runtime differs from the frozen candidate environment")
        require(not any(p.requires_grad for p in child.encoder.model.parameters()), "Encoder must remain frozen")
        require(not any(m.training for m in child.encoder.model.modules()), "Encoder must be in evaluation mode")
        subset = [r for r in rows if r["language"] == language]
        frozen = child.encoder.encode([r["text"] for r in subset], batch_size=32)
        features = [character_features(r["text"], f) for r, f in zip(subset, frozen)]
        # infer reads only input text and features; labels enter only the report.
        raw = infer(child.heads, subset, features, decoder=decode)
        gated = gate(subset, raw, child.metadata["thresholds"])
        for row, prediction in zip(subset, gated):
            if prediction["graph"] is not None:
                require(parse(format_graph(prediction["graph"])) == prediction["graph"], "Confirmed meaning failed the Noema round trip")
            predictions[row["id"]] = prediction
        first = [child.analyze(r["text"], language) for r in subset[:6]]
        second = [child.analyze(r["text"], language) for r in subset[:6]]
        repetitions[language] = {"count": 6, "full_repeat_exact": first == second,
                                 "single_vs_batch_same_meaning": all((a["status"], a["graph"]) == (b["status"], b["graph"]) for a, b in zip(first, gated[:6]))}
        models[language] = child.metadata
        print(json.dumps({"language": language, "evaluated": len(subset), "repetition": repetitions[language]}), flush=True)
    ordered = [predictions[r["id"]] for r in rows]
    metrics = evaluate(rows, ordered)
    category_results = category_gates(rows, ordered, recorded.get("category_gates", {}))
    strata = {}
    for row, prediction in zip(rows, ordered):
        key = row["language"] + ":" + (row["pattern"] if row["supported"] else row["category"])
        entry = strata.setdefault(key, {"total": 0, "confirmed": 0, "exact": 0})
        entry["total"] += 1
        entry["confirmed"] += prediction["status"] == "confirmed"
        entry["exact"] += row["supported"] and prediction["graph"] == row["graph"]
    report = {"started_at": started, "completed_at": datetime.now(timezone.utc).isoformat(), "manifest": recorded,
              "models": models, "metrics": metrics, "strata": strata, "repetition": repetitions,
              "category_gates": category_results,
              "passes_confirmation": (all(metrics[l]["passes_provisional_gate"] and metrics[l]["unsupported_false_accept_rate"] <= .05 for l in ("ja", "en"))
                                      and all(result["passes"] for result in category_results.values())),
              "reasons": {l: dict(Counter(p["diagnostics"]["reason"] or "confirmed" for r, p in zip(rows, ordered) if r["language"] == l and r["supported"])) for l in ("ja", "en")},
              "scope": "Prospective synthetic confirmation; not independent human-authored free-text evaluation. No threshold or checkpoint selection used these predictions."}
    save_json(output / "report.json", report)
    save_json(output / "predictions.json", [{"id": r["id"], **p} for r, p in zip(rows, ordered)])
    save_json(output / "run.json", {"started_at": started, "completed_at": report["completed_at"], "status": "complete", "report_sha256": digest(output / "report.json")})
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", default="artifacts/confirmation-v1.jsonl")
    parser.add_argument("--manifest", default="reports/confirmation-v1-manifest.json")
    parser.add_argument("--checkpoint", default="artifacts/routed-v6")
    parser.add_argument("--protocol", default="docs/confirmation-protocol.md")
    parser.add_argument("--selection", default="reports/routed-v6-selection.json")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    report = run(args.dataset, args.manifest, args.checkpoint, args.protocol, args.selection, args.output)
    print(json.dumps({"metrics": report["metrics"], "passes_confirmation": report["passes_confirmation"]}, indent=2))
