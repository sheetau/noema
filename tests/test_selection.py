import json
import pytest
pytest.importorskip("torch")
from noema.dataset import digest
from noema.training import save_json
from scripts.select_routes import select


def candidate(path):
    path.mkdir()
    (path / "heads.safetensors").write_bytes(b"selection fixture only")
    meta = {"dataset_sha256": "same-data", "weights_sha256": digest(path / "heads.safetensors")}
    metrics = {lang: {"passes_provisional_gate": True, "coverage": .9, "confirmed_exact_match": .99, "unsupported_false_accept_rate": .01} for lang in ("ja", "en")}
    save_json(path / "metadata.json", meta)
    save_json(path / "development-report.json", {"metadata": meta, "metrics": metrics})


def test_route_ties_follow_candidate_name_not_argument_order(tmp_path):
    a, z = tmp_path / "a", tmp_path / "z"
    candidate(a)
    candidate(z)
    manifest = select([z, a], tmp_path / "bundle", tmp_path / "selection.json")
    assert all(r["checkpoint"] == "../a" for r in manifest["routes"].values())


def test_stale_report_cannot_select_a_changed_checkpoint(tmp_path):
    path = tmp_path / "model"
    candidate(path)
    (path / "heads.safetensors").write_bytes(b"changed weights")
    with pytest.raises(ValueError, match="differ"):
        select([path], tmp_path / "bundle", tmp_path / "selection.json")
