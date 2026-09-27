import json
from pathlib import Path
import pytest

torch = pytest.importorskip("torch")
from safetensors.torch import save_file
from noema.analyzer import Analyzer
from noema.dataset import digest
from noema.encoder import MODELS
from noema.structured import SequenceHeads, LABELS
from noema.training import save_json


@pytest.fixture
def checkpoint(tmp_path, monkeypatch):
    import noema.encoder
    class Frozen:
        dimension = 4
        def __init__(self, *args):
            self.metadata = {**MODELS["minilm"], "key": "minilm"}
        def encode(self, texts, batch_size):
            return [{"tokens": torch.zeros(len(t), 4), "offsets": [(i, i+1) for i in range(len(t))], "truncated": False} for t in texts]
    monkeypatch.setattr(noema.encoder, "FrozenEncoder", Frozen)
    path = tmp_path / "model"
    path.mkdir()
    heads = SequenceHeads(13, 8)
    save_file(heads.state_dict(), str(path / "heads.safetensors"))
    import noema.structured
    metadata = {"format": 2, "architecture": "sequence-gru-attachment", "dimension": 13, "hidden": 8,
                "representation": "characters-v2", "schema_version": "0.1", "lexicon_version": "0.1", "labels": LABELS,
                "encoder": Frozen().metadata, "thresholds": {"ja": 1.01, "en": 1.01},
                "weights_sha256": digest(path / "heads.safetensors"), "decoder_sha256": digest(noema.structured.__file__)}
    save_json(path / "metadata.json", metadata)
    return path, metadata


def test_sequence_checkpoint_loads_and_uses_language_thresholds(checkpoint):
    path, _ = checkpoint
    analyzer = Analyzer(path)
    result = analyzer.analyze("test", "en")
    assert result["status"] != "confirmed"
    assert result["diagnostics"]["threshold"] == 1.01
    assert analyzer.analyze("test", "fr")["status"] == "unsupported"


def test_truncated_input_is_rejected_before_character_projection(checkpoint, monkeypatch):
    path, _ = checkpoint
    analyzer = Analyzer(path)
    monkeypatch.setattr(analyzer.encoder, "encode", lambda *args: [{"truncated": True}])
    import noema.structured
    def unexpected(*args):
        raise AssertionError("Truncated text must never be projected")
    monkeypatch.setattr(noema.structured, "character_features", unexpected)
    result = analyzer.analyze("a" * 10000, "en")
    assert result["status"] == "unresolved"
    assert result["diagnostics"]["reason"] == "input_too_long"


@pytest.mark.parametrize("field,value", [("decoder_sha256", "changed"), ("weights_sha256", "changed"), ("thresholds", {"ja": 0.5}), ("representation", "other")])
def test_checkpoint_mismatch_is_rejected(checkpoint, field, value):
    path, metadata = checkpoint
    save_json(path / "metadata.json", {**metadata, field: value})
    with pytest.raises(ValueError):
        Analyzer(path)


def test_language_routes_are_lazy_and_hash_checked(checkpoint, tmp_path):
    path, metadata = checkpoint
    bundle = tmp_path / "bundle"
    route = {"checkpoint": "../model", "metadata_sha256": digest(path / "metadata.json")}
    save_json(bundle / "metadata.json", {"format": 3, "architecture": "language-routed", "routes": {"ja": route, "en": route}})
    analyzer = Analyzer(bundle)
    assert not analyzer.loaded_routes
    assert "routing" in analyzer.analyze("test", "en")["diagnostics"]
    assert set(analyzer.loaded_routes) == {"en"}
    save_json(path / "metadata.json", {**metadata, "thresholds": {"en": .5, "ja": .5}})
    with pytest.raises(ValueError, match="checksum"):
        Analyzer(bundle)
