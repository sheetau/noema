"""Compare Noema's frozen adapter with the published BEM implementation.

Install the optional reference independently with:
python -m pip install --no-deps --target artifacts/wsd-reference wsd-torch-models==0.1.3
"""
import argparse
import inspect
import json
from pathlib import Path
import sys

from noema.bem_probe import FrozenBEM, MODEL, REVISION
from noema.definition_probe import digest, save, span_vector
from noema.semantics import require


def main():
    import torch
    from huggingface_hub import hf_hub_download
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", default="artifacts/wsd-reference")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = Path(args.output)
    require(not output.exists(), "Choose a new output file")
    sys.path.insert(0, str(Path(args.reference).resolve()))
    from wsd_torch_models.bem import BEM
    encoder = FrozenBEM()
    config_path = hf_hub_download(MODEL, "config.json", revision=REVISION, local_files_only=True)
    config = json.loads(Path(config_path).read_text(encoding="utf-8"))
    config["base_model"] = encoder.model
    reference = BEM(**config).eval().requires_grad_(False)
    texts = ["The key opens the door.", "その鍵で扉を開けた。"]
    targets = ["key", "鍵"]
    features = encoder.encode(texts)
    tokenized = encoder.tokenizer(texts, return_tensors="pt", padding=True, return_offsets_mapping=True)
    offsets = tokenized.pop("offset_mapping")
    mask = torch.zeros_like(tokenized["attention_mask"])
    for i, (text, target) in enumerate(zip(texts, targets)):
        start = text.index(target)
        end = start + len(target)
        for j, (a, b) in enumerate(offsets[i].tolist()):
            mask[i, j] = int(a < b and a < end and b > start)
    with torch.inference_mode():
        ref_tokens = reference.text_encoding(tokenized["input_ids"], tokenized["attention_mask"])
        ref_spans = reference.token_encoding_using_text_encoding(ref_tokens, mask)
        ref_pooled = reference.label_definition_encoding(tokenized["input_ids"].unsqueeze(1),
                                                         tokenized["attention_mask"].unsqueeze(1)).squeeze(1)
        actual_spans = torch.stack([span_vector(f, t.index(s), t.index(s) + len(s)) for f, t, s in zip(features, texts, targets)])
        actual_pooled = torch.stack([f["pooled"] for f in features])
        ref_scores = reference.token_label_similarity(ref_pooled.unsqueeze(0).expand(2, -1, -1), ref_spans)
        actual_scores = actual_spans @ actual_pooled.T
    comparisons = {"span": (actual_spans, ref_spans), "definition_mean": (actual_pooled, ref_pooled),
                   "dot_scores": (actual_scores, ref_scores)}
    for i, feature in enumerate(features):
        comparisons[f"tokens_{i}"] = (feature["tokens"], ref_tokens[i, :len(feature["tokens"])])
    errors = {name: {"max_absolute_error": (a - b).abs().max().item(),
                     "within_tolerance": torch.allclose(a, b, atol=1e-5, rtol=1e-6)}
              for name, (a, b) in comparisons.items()}
    require(all(v["within_tolerance"] for v in errors.values()), "Adapter differs from upstream")
    output.parent.mkdir(parents=True, exist_ok=True)
    save(output, {"model": encoder.metadata, "reference_distribution": "wsd-torch-models==0.1.3",
                  "reference_source_sha256": digest(inspect.getfile(BEM)),
                  "script_sha256": digest(__file__), "atol": 1e-5, "rtol": 1e-6,
                  "scope": "same strict-loaded backbone; compare upstream token, pooling and score operations",
                  "comparisons": errors})
    print(json.dumps(errors))


if __name__ == "__main__":
    main()
