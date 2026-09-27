"""Freeze language routes using development reports before final evaluation."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from noema.dataset import digest
from noema.training import save_json


def select(checkpoints, output, record):
    output = Path(output)
    if output.exists() or Path(record).exists():
        raise ValueError("Choose new paths; a frozen selection must not be overwritten")
    candidates = [(Path(p), json.loads((Path(p) / "development-report.json").read_text(encoding="utf-8"))) for p in checkpoints]
    if len({r["metadata"]["dataset_sha256"] for _, r in candidates}) != 1:
        raise ValueError("Candidates used different datasets")
    routes, decisions = {}, {}
    for language in ("ja", "en"):
        eligible = [(p, r) for p, r in candidates if r["metrics"][language]["passes_provisional_gate"] and r["metrics"][language]["unsupported_false_accept_rate"] <= .05]
        if not eligible:
            raise ValueError(f"No development-qualified checkpoint for {language}")
        path, report = max(eligible, key=lambda item: (item[1]["metrics"][language]["coverage"], item[1]["metrics"][language]["confirmed_exact_match"]))
        routes[language] = {"checkpoint": os.path.relpath(path, output).replace("\\", "/"), "metadata_sha256": digest(path / "metadata.json")}
        decisions[language] = {"checkpoint": str(path), "metrics": report["metrics"][language], "weights_sha256": report["metadata"]["weights_sha256"]}
    manifest = {"format": 3, "architecture": "language-routed", "routes": routes,
                "selected_at": datetime.now(timezone.utc).isoformat(),
                "policy": "highest development coverage among candidates with >=80% coverage, >=95% confirmed exact match, <=5% unsupported false acceptance; explicit language routing"}
    save_json(output / "metadata.json", manifest)
    save_json(record, {"manifest": manifest, "decisions": decisions, "final_partition_used": False})
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkpoints", nargs="+")
    parser.add_argument("--output", required=True)
    parser.add_argument("--record", required=True)
    args = parser.parse_args()
    print(json.dumps(select(args.checkpoints, args.output, args.record), indent=2))


if __name__ == "__main__":
    main()
