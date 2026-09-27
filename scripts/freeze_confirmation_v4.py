"""Bind reviewed v4 fixtures to the preregistered v9 candidate."""
from datetime import datetime, timezone
import json
from pathlib import Path
from noema.dataset import digest
from noema.semantics import require
from noema.training import save_json


def main():
    target = Path("reports/confirmation-v4-manifest.json")
    require(not target.exists(), "Frozen manifest already exists")
    fixture = json.loads(Path("reports/confirmation-v4-fixture.json").read_text(encoding="utf-8"))
    require(digest("artifacts/confirmation-v4.jsonl") == fixture["dataset_sha256"], "Reviewed fixture changed")
    require(digest("docs/confirmation-v4-protocol.md") == fixture["protocol_sha256"], "Protocol changed")
    review = Path("docs/confirmation-v4-review.md")
    require(review.is_file(), "Review must precede predictions")
    checkpoint = Path("artifacts/routed-v9")
    route = json.loads((checkpoint / "metadata.json").read_text(encoding="utf-8"))
    selection_path = Path("reports/routed-v9-selection.json")
    selection = json.loads(selection_path.read_text(encoding="utf-8"))
    require(selection["manifest"] == route and selection["final_partition_used"] is False, "Route differs from selection")
    for language, child in route["routes"].items():
        path = (checkpoint / child["checkpoint"]).resolve()
        require(path == Path("artifacts/joint-v9-xlmr").resolve(), "Candidate not preregistered")
        metadata = json.loads((path / "metadata.json").read_text(encoding="utf-8"))
        require(metadata["epochs"] == 30 and metadata["decoder"] == "joint-v1" and metadata["dataset_sha256"] == fixture["source_sha256"], "Conditions changed")
        require(digest(path / "metadata.json") == child["metadata_sha256"], "Metadata changed")
        require(digest(path / "heads.safetensors") == metadata["weights_sha256"] == selection["decisions"][language]["weights_sha256"], "Weights changed")
    save_json(target, {**fixture, "review": str(review).replace("\\", "/"), "review_sha256": digest(review),
                       "route_metadata_sha256": digest(checkpoint / "metadata.json"), "selection_sha256": digest(selection_path),
                       "frozen_at": datetime.now(timezone.utc).isoformat()})
    print(target)


if __name__ == "__main__":
    main()
