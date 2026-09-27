"""Bind reviewed v2 cases to the development-selected v7 candidates."""
from datetime import datetime, timezone
import json
from pathlib import Path
from noema.dataset import digest
from noema.semantics import require
from noema.training import save_json


def main():
    target = Path("reports/confirmation-v2-manifest.json")
    require(not target.exists(), "The frozen confirmation manifest already exists")
    fixture = json.loads(Path("reports/confirmation-v2-fixture.json").read_text(encoding="utf-8"))
    require(digest("artifacts/confirmation-v2.jsonl") == fixture["dataset_sha256"], "Reviewed confirmation data changed")
    require(digest("docs/confirmation-v2-protocol.md") == fixture["protocol_sha256"], "Confirmation protocol changed")
    checkpoint = Path("artifacts/routed-v7")
    route = json.loads((checkpoint / "metadata.json").read_text(encoding="utf-8"))
    selection_path = Path("reports/routed-v7-selection.json")
    selection = json.loads(selection_path.read_text(encoding="utf-8"))
    require(selection["manifest"] == route and selection["final_partition_used"] is False, "Route differs from development selection")
    for language, child in route["routes"].items():
        path = (checkpoint / child["checkpoint"]).resolve()
        require(path in {Path("artifacts/joint-v7-xlmr").resolve(), Path("artifacts/joint-v7-minilm").resolve()}, "Candidate was not preregistered")
        metadata = json.loads((path / "metadata.json").read_text(encoding="utf-8"))
        require(metadata["epochs"] == 30 and metadata["decoder"] == "joint-v1" and metadata["dataset_sha256"] == fixture["source_sha256"], "Candidate training conditions changed")
        require(digest(path / "metadata.json") == child["metadata_sha256"], "Candidate metadata changed")
        require(digest(path / "heads.safetensors") == metadata["weights_sha256"] == selection["decisions"][language]["weights_sha256"], "Candidate weights changed")
    save_json(target, {**fixture, "route_metadata_sha256": digest(checkpoint / "metadata.json"),
                       "selection_sha256": digest(selection_path), "frozen_at": datetime.now(timezone.utc).isoformat()})
    print(target)


if __name__ == "__main__":
    main()
