"""Natural-language analysis result envelope; semantic graph stays model-independent."""
import json
from pathlib import Path


class Analyzer:
    def __init__(self, checkpoint=None, device="cpu", offline=False):
        self.encoder = self.heads = self.metadata = None
        if checkpoint is None:
            return
        from safetensors.torch import load_file
        from .dataset import digest
        from .encoder import FrozenEncoder, MODELS
        from .model import Heads, LABELS
        path = Path(checkpoint)
        self.metadata = json.loads((path / "metadata.json").read_text(encoding="utf-8"))
        meta = self.metadata
        if meta.get("format") != 1 or meta.get("labels") != LABELS or meta.get("schema_version") != "0.1" or meta.get("lexicon_version") != "0.1":
            raise ValueError("Incompatible checkpoint format, labels, schema or lexicon")
        spec = MODELS[meta["encoder"]["key"]]
        if any(meta["encoder"][k] != spec[k] for k in ("id", "revision", "max_length")):
            raise ValueError("Encoder does not match pinned model")
        if meta["weights_sha256"] != digest(path / "heads.safetensors"):
            raise ValueError("Checkpoint checksum mismatch")
        self.encoder = FrozenEncoder(meta["encoder"]["key"], device, offline)
        if meta["dimension"] != self.encoder.dimension:
            raise ValueError("Encoder dimension mismatch")
        self.heads = Heads(meta["dimension"], meta["architecture"])
        self.heads.load_state_dict(load_file(str(path / "heads.safetensors")))
        self.heads.eval()

    def analyze(self, text, language):
        if language not in ("ja", "en"):
            return {"status": "unsupported", "graph": None, "diagnostics": {"reason": "language_not_supported", "language": language, "confidence": None, "spans": []}}
        if not isinstance(text, str):
            raise ValueError("Input must be text")
        if self.encoder is None:
            return {"status": "unresolved", "graph": None, "diagnostics": {"reason": "checkpoint_required", "language": language, "confidence": None, "spans": [], "model": None}}
        import torch
        from .model import decode
        feature = self.encoder.encode([text], 1)[0]
        with torch.inference_mode():
            logits = self.heads(feature["tokens"], feature["pooled"])
            result = decode(text, feature, logits, self.metadata["threshold"])
        result["diagnostics"].update(language=language, model=self.encoder.metadata,
                                     checkpoint_sha256=self.metadata["weights_sha256"], threshold=self.metadata["threshold"])
        return result
