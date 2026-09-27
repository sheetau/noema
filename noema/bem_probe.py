"""Frozen pretrained word/definition matching; oracle-span research only."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import gc
import json
from pathlib import Path
import platform
import time

from .definition_probe import (DefinitionIndex, definitions, digest, distribution,
                               rows_from_fixture, save, span_vector)
from .encoder import FrozenEncoder, deterministic
from .semantics import require

MODEL = "ucrelnlp/PyMUSAS-Neural-Multilingual-Small-BEM"
REVISION = "2e42e0de8d5b00144a8eb1e61013457021b016c0"


def base_weights(state):
    """Reject architectures with unimplemented learned components."""
    require(state and all(k.startswith("base_model.") for k in state),
            "Unsupported BEM checkpoint components")
    return {k.removeprefix("base_model."): v for k, v in state.items()}


class FrozenBEM(FrozenEncoder):
    """Exact base-only BEM architecture, without its USAS label inventory.

    Reuses offset-preserving inference. No remote Python or pickle is loaded.
    This adapter intentionally accepts only the pinned base-only checkpoint.
    """
    def __init__(self, offline=True):
        import torch
        import transformers
        from huggingface_hub import hf_hub_download
        from safetensors.torch import load_file
        from transformers import AutoConfig, AutoModel, AutoTokenizer
        deterministic()
        kwargs = {"revision": REVISION, "local_files_only": offline}
        config_path = hf_hub_download(MODEL, "config.json", **kwargs)
        config = json.loads(Path(config_path).read_text(encoding="utf-8"))
        require(config["add_scalar_mixer"] is False and config["number_transformer_encoder_layers"] == 0,
                "Unsupported BEM architecture")
        base_path = hf_hub_download(MODEL, "base_model_config/config.json", **kwargs)
        weight_path = hf_hub_download(MODEL, "model.safetensors", **kwargs)
        auto_config = AutoConfig.from_pretrained(base_path, trust_remote_code=False)
        require(auto_config.model_type == "modernbert", "Unexpected BEM backbone")
        auto_config.reference_compile = False
        self.model = AutoModel.from_config(auto_config, attn_implementation="eager", trust_remote_code=False)
        self.model.load_state_dict(base_weights(load_file(weight_path)), strict=True)
        self.model.to(device="cpu", dtype=torch.float32).eval().requires_grad_(False)
        self.tokenizer = AutoTokenizer.from_pretrained(MODEL, use_fast=True, trust_remote_code=False, **kwargs)
        require(self.tokenizer.is_fast, "Character offsets require a fast tokenizer")
        self.device, self.key = "cpu", "bem"
        self.dimension = auto_config.hidden_size
        self.spec = {"id": MODEL, "revision": REVISION, "max_length": 128}
        self.metadata = {**self.spec, "key": self.key, "torch": str(torch.__version__),
                         "transformers": transformers.__version__, "python": platform.python_version(),
                         "platform": platform.platform(), "processor": platform.processor(),
                         "device": "cpu", "dtype": "float32", "threads": torch.get_num_threads(),
                         "seed": 17, "attention": "eager", "reference_compile": False,
                         "pooling": "attention-mask mean including special tokens",
                         "parameters": sum(p.numel() for p in self.model.parameters()),
                         "checkpoint_sha256": digest(weight_path), "config_sha256": digest(config_path),
                         "base_config_sha256": digest(base_path)}


class GlossIndex:
    """English definitions, mean pooling, raw dot product as in upstream BEM."""
    def __init__(self, encoder, bank):
        import torch
        require(bank and len({d["id"] for d in bank}) == len(bank), "Invalid concept inventory")
        ordered = sorted(bank, key=lambda d: d["id"])
        require(all(isinstance(d["en"], str) and d["en"].strip() for d in ordered), "Empty definition")
        self.ids = [d["id"] for d in ordered]
        features = encoder.encode([d["en"] for d in ordered])
        require(all(not f["truncated"] for f in features), "Truncated definition")
        self.vectors = torch.stack([f["pooled"] for f in features])
        require(bool(torch.isfinite(self.vectors).all()), "Non-finite definition")

    def rank(self, vector, limit=3):
        import torch
        require(bool(torch.isfinite(vector).all()), "Non-finite query")
        scores = self.vectors @ vector
        require(bool(torch.isfinite(scores).all()), "Non-finite score")
        ordered = sorted(zip(self.ids, scores.tolist()), key=lambda x: (-x[1], x[0]))
        return [{"concept": key, "score": score} for key, score in ordered[:limit]]


def summarize(predictions):
    result = {}
    for language in ("ja", "en"):
        selected = [p for p in predictions if p["language"] == language]
        groups = {}
        for group in ("base", "extension", "supported"):
            subset = [p for p in selected if p["group"] == group or group == "supported" and p["expected"] is not None]
            count = len(subset)
            correct = sum(p["expected"] == p["top"][0]["concept"] for p in subset)
            groups[group] = {"count": count, "correct": correct, "accuracy": correct / count if count else None,
                             "top3_correct": sum(p["expected"] in [t["concept"] for t in p["top"]] for p in subset)}
        scores = {k: [] for k in ("known_correct", "known_wrong", "unsupported")}
        for p in selected:
            category = "unsupported" if p["expected"] is None else "known_correct" if p["expected"] == p["top"][0]["concept"] else "known_wrong"
            scores[category].append(p["top"][0]["score"])
        result[language] = {**groups, "top1_score": {k: distribution(v) for k, v in scores.items()}}
    pairs = {}
    for p in predictions:
        if p["expected"] is not None:
            pairs.setdefault(p["pair"], {})[p["language"]] = p
    result["bilingual"] = {
        "pairs": len(pairs),
        "same_candidate": sum(p["ja"]["top"][0]["concept"] == p["en"]["top"][0]["concept"] for p in pairs.values()),
        "both_correct": sum(all(p[l]["top"][0]["concept"] == p[l]["expected"] for l in ("ja", "en")) for p in pairs.values())}
    return result


def run(output, offline=True):
    import torch
    output = Path(output)
    require(not output.exists(), "Choose a new output directory")
    bank = definitions()
    fixtures = {key: Path(f"data/definition-probe-{key}.json") for key in ("v1", "v2")}
    rows = {key: rows_from_fixture(json.loads(path.read_text(encoding="utf-8")), {d["id"] for d in bank})
            for key, path in fixtures.items()}
    output.mkdir(parents=True)
    save(output / "definitions.json", bank)
    sources = [Path(__file__), Path("noema/definition_probe.py"), Path("noema/encoder.py"),
               Path("noema/resources/models.json"), Path("docs/bem-probe-protocol.md")]
    provenance = {"started_at": datetime.now(timezone.utc).isoformat(), "status": "running",
                  "interpretation": "oracle-span concept matching, no full parsing or calibrated rejection",
                  "fixtures": {key: {"sha256": digest(path), "counts": dict(Counter(r["language"] + ":" + r["group"] for r in rows[key]))}
                               for key, path in fixtures.items()},
                  "definitions_sha256": digest(output / "definitions.json"),
                  "source_sha256": {str(p): digest(p) for p in sources}}
    save(output / "run.json", provenance)
    for key in ("bem", "minilm"):
        started = time.monotonic()
        encoder = FrozenBEM(offline=offline) if key == "bem" else FrozenEncoder("minilm", offline=offline)
        require(not any(p.requires_grad for p in encoder.model.parameters()), "Unfrozen encoder")
        require(not any(m.training for m in encoder.model.modules()), "Training mode enabled")
        index = GlossIndex(encoder, bank) if key == "bem" else DefinitionIndex(encoder, bank)
        for fixture, entries in rows.items():
            features = encoder.encode([r["text"] for r in entries])
            predictions = []
            for row, feature in zip(entries, features):
                top = index.rank(span_vector(feature, row["start"], row["end"]))
                if key == "minilm":
                    top = [{"concept": t["concept"], "score": t["cosine"]} for t in top]
                predictions.append({**row, "top": top})
            repeated = encoder.encode([r["text"] for r in entries[:16]])
            equal = all(torch.equal(a["tokens"], b["tokens"]) for a, b in zip(features[:16], repeated))
            require(equal, "Repeated token inference differs")
            report = {"model": encoder.metadata, "seconds_since_model_start": time.monotonic() - started,
                      "noema_fitted_parameters": 0, "candidate_count": len(index.ids),
                      "definition_language": "en" if key == "bem" else "bilingual normalized mean",
                      "score": "dot_product" if key == "bem" else "cosine",
                      "repeat_count": 16, "repeat_tokens_exact": equal, "metrics": summarize(predictions)}
            save(output / f"{key}-{fixture}-predictions.json", predictions)
            save(output / f"{key}-{fixture}-report.json", report)
            print(json.dumps({"model": key, "fixture": fixture, "metrics": report["metrics"]}), flush=True)
        del index, encoder, features, repeated
        gc.collect()
    save(output / "run.json", {**provenance, "status": "complete", "finished_at": datetime.now(timezone.utc).isoformat()})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    parser.add_argument("--download", action="store_true", help="Allow pinned public model downloads")
    args = parser.parse_args()
    run(args.output, offline=not args.download)


if __name__ == "__main__":
    main()
