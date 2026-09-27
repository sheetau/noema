import json
import pytest
from noema.annotation_audit import audit
from noema.dataset import digest


@pytest.fixture
def frozen(tmp_path):
    # Negative fixtures need no model or positive semantic annotation.
    rows = [{"id": language, "group": language, "language": language, "split": "test",
             "text": "outside scope", "supported": False, "graph": None, "spans": [],
             "category": "unknown_concept", "pattern": "unsupported"} for language in ("ja", "en")]
    dataset = tmp_path / "data.jsonl"
    dataset.write_text(''.join(json.dumps(r) + '\n' for r in rows), encoding="utf-8")
    protocol, selection = tmp_path / "protocol.md", tmp_path / "selection.json"
    protocol.write_text("Frozen before prediction", encoding="utf-8")
    selection.write_text("{}", encoding="utf-8")
    checkpoint = tmp_path / "checkpoint"
    checkpoint.mkdir()
    metadata = checkpoint / "metadata.json"
    metadata.write_text("{}", encoding="utf-8")
    manifest = tmp_path / "manifest.json"
    record = {"dataset_sha256": digest(dataset), "protocol_sha256": digest(protocol),
              "selection_sha256": digest(selection), "route_metadata_sha256": digest(metadata), "audit": audit(rows)}
    manifest.write_text(json.dumps(record), encoding="utf-8")
    return dataset, manifest, checkpoint, protocol, selection


@pytest.mark.parametrize("changed", (0, 2, 3, 4))
def test_confirmation_rejects_changed_frozen_inputs(frozen, changed):
    pytest.importorskip("torch")
    from noema.evaluate_confirmation import verify_inputs
    assert len(verify_inputs(*frozen)[0]) == 2
    target = frozen[changed] / "metadata.json" if changed == 2 else frozen[changed]
    target.write_bytes(target.read_bytes() + b' ')
    with pytest.raises(ValueError, match="Frozen confirmation input changed"):
        verify_inputs(*frozen)


def test_regression_rejects_changed_data_and_training_partitions(frozen):
    pytest.importorskip("torch")
    from noema.evaluate_regression import fixture
    dataset = frozen[0]
    expected = digest(dataset)
    assert len(fixture(dataset, expected)[0]) == 2
    text = dataset.read_text(encoding="utf-8").replace('"test"', '"train"')
    dataset.write_text(text, encoding="utf-8")
    with pytest.raises(ValueError, match="fixture changed"):
        fixture(dataset, expected)
    with pytest.raises(ValueError, match="test-only"):
        fixture(dataset, digest(dataset))
