"""Natural-language analysis result envelope; semantic graph stays model-independent."""
import json
from pathlib import Path


class Analyzer:
    def __init__(self, checkpoint=None, device="cpu", offline=False):
        self.encoder = self.heads = self.metadata = None
        self.routes, self.loaded_routes = None, {}
        self.device, self.offline = device, offline
        if checkpoint is None:
            return
        from safetensors.torch import load_file
        from .dataset import digest
        from .encoder import FrozenEncoder, MODELS
        from .model import Heads, LABELS
        path = Path(checkpoint)
        self.metadata = json.loads((path / "metadata.json").read_text(encoding="utf-8"))
        meta = self.metadata
        if meta.get("format") == 3:
            if meta.get("architecture") != "language-routed" or set(meta.get("routes", {})) != {"ja", "en"}:
                raise ValueError("Invalid language routing manifest")
            self.routes = {}
            for language, route in meta["routes"].items():
                child = (path / route["checkpoint"]).resolve()
                if route["metadata_sha256"] != digest(child / "metadata.json"):
                    raise ValueError("Routed checkpoint metadata checksum mismatch")
                child_meta = json.loads((child / "metadata.json").read_text(encoding="utf-8"))
                if child_meta.get("format") != 2:
                    raise ValueError("Routes must point to sequence checkpoints")
                self.routes[language] = child
            return
        if meta.get("format") == 2:
            from .structured import LABELS, SequenceHeads
            if meta.get("architecture") != "sequence-gru-attachment" or meta.get("representation") != "characters-v2":
                raise ValueError("Unsupported sequence architecture or representation")
            if meta.get("decoder_sha256") != digest(Path(__file__).with_name("structured.py")):
                raise ValueError("Decoder implementation differs from the calibrated checkpoint")
            if meta.get("decoder", "independent-v4") not in ("independent-v4", "joint-v1"):
                raise ValueError("Unsupported decoder")
            if meta.get("decoder") == "joint-v1" and meta.get("joint_decoder_sha256") != digest(Path(__file__).with_name("joint.py")):
                raise ValueError("Joint decoder differs from the calibrated checkpoint")
            if set(meta.get("thresholds", {})) != {"ja", "en"} or any(type(v) not in (float, int) or not 0 <= v <= 1.01 for v in meta["thresholds"].values()):
                raise ValueError("Invalid per-language thresholds")
        if meta.get("format") not in (1, 2) or meta.get("labels") != LABELS or meta.get("schema_version") != "0.1" or meta.get("lexicon_version") != "0.1":
            raise ValueError("Incompatible checkpoint format, labels, schema or lexicon")
        spec = MODELS[meta["encoder"]["key"]]
        if any(meta["encoder"][k] != spec[k] for k in ("id", "revision", "max_length")):
            raise ValueError("Encoder does not match pinned model")
        if meta["weights_sha256"] != digest(path / "heads.safetensors"):
            raise ValueError("Checkpoint checksum mismatch")
        self.encoder = FrozenEncoder(meta["encoder"]["key"], device, offline)
        if meta["dimension"] != self.encoder.dimension + (9 if meta["format"] == 2 else 0):
            raise ValueError("Encoder dimension mismatch")
        self.heads = SequenceHeads(meta["dimension"], meta["hidden"]) if meta["format"] == 2 else Heads(meta["dimension"], meta["architecture"])
        self.heads.load_state_dict(load_file(str(path / "heads.safetensors")))
        self.heads.eval()

    def analyze(self, text, language):
        if language not in ("ja", "en"):
            return {"status": "unsupported", "graph": None, "diagnostics": {"reason": "language_not_supported", "language": language, "confidence": None, "spans": []}}
        if not isinstance(text, str):
            raise ValueError("Input must be text")
        if self.routes is not None:
            if language not in self.loaded_routes:
                self.loaded_routes[language] = Analyzer(self.routes[language], self.device, self.offline)
            result = self.loaded_routes[language].analyze(text, language)
            result["diagnostics"]["routing"] = "explicit input language; frozen development-selected checkpoint"
            return result
        if self.encoder is None:
            return {"status": "unresolved", "graph": None, "diagnostics": {"reason": "checkpoint_required", "language": language, "confidence": None, "spans": [], "model": None}}
        import torch
        from .model import decode
        feature = self.encoder.encode([text], 1)[0]
        threshold = self.metadata["thresholds"][language] if self.metadata["format"] == 2 else self.metadata["threshold"]
        with torch.inference_mode():
            if self.metadata["format"] == 2:
                from .structured import decode, character_features
                if self.metadata.get("decoder") == "joint-v1":
                    from .joint import decode
                if feature["truncated"]:
                    logits = {}  # Reject before projecting an arbitrarily long original text.
                else:
                    feature = character_features(text, feature)
                    logits = {k: v[0] for k, v in self.heads(feature["tokens"].unsqueeze(0), torch.tensor([len(feature["tokens"])] )).items()}
            else:
                logits = self.heads(feature["tokens"], feature["pooled"])
            result = decode(text, feature, logits, threshold)
        result["diagnostics"].update(language=language, model=self.encoder.metadata,
                                     checkpoint_sha256=self.metadata["weights_sha256"], threshold=threshold,
                                     decoder_sha256=self.metadata.get("decoder_sha256"))
        result["diagnostics"]["decoder"] = self.metadata.get("decoder", "independent-v4" if self.metadata["format"] == 2 else "baseline")
        return result
