import pytest
pytest.importorskip("torch")
from noema.train_structured import train


def test_training_refuses_an_existing_checkpoint_before_loading_data(tmp_path):
    weights = tmp_path / "heads.safetensors"
    weights.write_bytes(b"preserved checkpoint")
    with pytest.raises(ValueError, match="preserve previous checkpoints"):
        train("missing-data.jsonl", "missing-cache.pt", tmp_path)
    assert weights.read_bytes() == b"preserved checkpoint"
    assert list(tmp_path.iterdir()) == [weights]
