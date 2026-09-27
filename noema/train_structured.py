"""Development-only model selection; final evaluation is a separate command."""
import argparse
import copy
import json
from pathlib import Path
import time
import torch
from torch.nn import functional as F
from torch.nn.utils.rnn import pad_sequence
from safetensors.torch import save_file
from .dataset import digest
from .encoder import deterministic
from .evaluation import evaluate
from .structured import SequenceHeads, LABELS, TOKEN_HEADS, decode, character_features
from .unknown_supervision import targets
from .training import load_cache, save_json


def batch(indices, features, labels=None):
    tokens = pad_sequence([features[i]["tokens"] for i in indices], batch_first=True)
    lengths = torch.tensor([len(features[i]["tokens"]) for i in indices])
    if labels is None:
        return tokens, lengths
    gold = {key: pad_sequence([labels[i][key] for i in indices], batch_first=True, padding_value=-100) if key in TOKEN_HEADS else torch.stack([labels[i][key] for i in indices]) for key in LABELS}
    gold["attachment"] = pad_sequence([labels[i]["attachment"] for i in indices], batch_first=True, padding_value=-100)
    return tokens, lengths, gold


def infer(model, rows, features, threshold=0., decoder=decode):
    predictions = []
    model.eval()
    with torch.inference_mode():
        for start in range(0, len(rows), 64):
            indices = list(range(start, min(start + 64, len(rows))))
            tokens, lengths = batch(indices, features)
            result = model(tokens, lengths)
            for j, i in enumerate(indices):
                logits = {k: v[j, :lengths[j], :lengths[j]] if k == "attachment" else v[j, :lengths[j]] if k in TOKEN_HEADS else v[j] for k, v in result.items()}
                predictions.append(decoder(rows[i]["text"], features[i], logits, threshold))
    return predictions


def calibrate(rows, predictions):
    """Maximize development coverage subject to precision and rejection constraints."""
    thresholds = {}
    metrics = {}
    for lang in ("ja", "en"):
        pairs = [(r, p) for r, p in zip(rows, predictions) if r["language"] == lang]
        best = None
        # A value above one explicitly means no validated operating point exists.
        for threshold in [i / 100 for i in range(101)]:
            accepted = [(r, p) for r, p in pairs if p["status"] == "confirmed" and p["diagnostics"]["confidence"] >= threshold]
            inside = [(r, p) for r, p in accepted if r["supported"]]
            total_inside = sum(r["supported"] for r, _ in pairs)
            total_outside = sum(not r["supported"] for r, _ in pairs)
            precision = sum(r["graph"] == p["graph"] for r, p in inside) / len(inside) if inside else 0.
            false_accept = sum(not r["supported"] for r, _ in accepted) / max(1, total_outside)
            coverage = len(inside) / max(1, total_inside)
            if precision >= .95 and false_accept <= .05 and (best is None or coverage > best[0]):
                best = (coverage, threshold, precision, false_accept)
        thresholds[lang] = best[1] if best else 1.01
        metrics[lang] = {"coverage": best[0] if best else 0., "precision": best[2] if best else None,
                         "unsupported_false_accept_rate": best[3] if best else 0., "threshold": thresholds[lang], "validated": best is not None}
    return thresholds, metrics


def gate(rows, predictions, thresholds):
    result = copy.deepcopy(predictions)
    for row, prediction in zip(rows, result):
        if prediction["status"] == "confirmed" and prediction["diagnostics"]["confidence"] < thresholds[row["language"]]:
            prediction["status"], prediction["graph"] = "unresolved", None
            prediction["diagnostics"]["reason"] = "low_confidence"
    return result


def train(dataset, cache_path, output, epochs=35, hidden=96, seed=71, decoder_name="independent-v4", regression_test=False):
    if decoder_name not in ("independent-v4", "joint-v1"):
        raise ValueError("Unsupported decoder")
    decoder = decode
    if decoder_name == "joint-v1":
        from .joint import decode as decoder
    deterministic(seed)
    rows, cache = load_cache(dataset, cache_path)
    # Do not construct labels or invoke prediction on the final partition here.
    selected = [i for i, r in enumerate(rows) if r["split"] != "test"]
    rows, features = [rows[i] for i in selected], [cache["features"][i] for i in selected]
    features = [character_features(r["text"], f) for r, f in zip(rows, features)]
    labels = [targets(r, f) for r, f in zip(rows, features)]
    training = [i for i, r in enumerate(rows) if r["split"] == "train"]
    development = [i for i, r in enumerate(rows) if r["split"] == "dev"]
    dev_rows, dev_features = [rows[i] for i in development], [features[i] for i in development]
    dimension = cache["dimension"] + 9
    model = SequenceHeads(dimension, hidden)
    optimizer = torch.optim.AdamW(model.parameters(), lr=.001, weight_decay=.01)
    rng = torch.Generator().manual_seed(seed)
    counts = torch.bincount(torch.tensor([int(rows[i]["supported"]) for i in training]), minlength=2).float()
    support_weights = counts.sum() / (2 * counts.clamp_min(1))
    history, best, state = [], -1., None
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    start = time.monotonic()
    for epoch in range(epochs):
        model.train()
        order = [training[i] for i in torch.randperm(len(training), generator=rng).tolist()]
        for offset in range(0, len(order), 64):
            tokens, lengths, gold = batch(order[offset:offset + 64], features, labels)
            logits = model(tokens, lengths)
            losses = []
            for key in LABELS:
                valid = gold[key].reshape(-1) != -100
                if valid.any():
                    raw = F.cross_entropy(logits[key].reshape(-1, len(LABELS[key])), gold[key].reshape(-1),
                                          weight=support_weights if key == "support" else None, reduction="none", ignore_index=-100)
                    losses.append(raw[valid].mean())
            if (gold["attachment"] != -100).any():
                losses.append(F.cross_entropy(logits["attachment"].flatten(0, 1), gold["attachment"].flatten(), ignore_index=-100))
            loss = torch.stack(losses).mean()
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 5.)
            optimizer.step()
        if epoch == 0 or (epoch + 1) % 5 == 0 or epoch + 1 == epochs:
            raw = infer(model, dev_rows, dev_features, decoder=decoder)
            thresholds, calibration = calibrate(dev_rows, raw)
            metrics = evaluate(dev_rows, gate(dev_rows, raw, thresholds))
            raw_metrics = evaluate(dev_rows, raw)
            # Prefer coverage passing the accuracy/rejection constraints. The
            # secondary term gives a learning signal before any point qualifies.
            score = sum(calibration[l]["coverage"] for l in ("ja", "en")) + .001 * sum(raw_metrics[l]["exact"] / max(1, raw_metrics[l]["in_scope"]) for l in ("ja", "en"))
            history.append({"epoch": epoch + 1, "calibration": calibration, "raw": raw_metrics})
            print(json.dumps({"epoch": epoch + 1, "calibration": calibration, "raw_exact": {l: raw_metrics[l]["exact"] / raw_metrics[l]["in_scope"] for l in ("ja", "en")}}), flush=True)
            if score > best:
                best = score
                state = {k: v.detach().clone() for k, v in model.state_dict().items()}
                best_epoch, best_thresholds, best_metrics = epoch + 1, thresholds, metrics
                save_file(state, str(output / "heads.safetensors"))
                save_json(output / "dev-predictions.json", [{"id": r["id"], **p} for r, p in zip(dev_rows, raw)])
        save_json(output / "development-history.json", history)
    metadata = {"format": 2, "architecture": "sequence-gru-attachment", "dimension": dimension, "hidden": hidden, "representation": "characters-v2",
                "labels": LABELS, "schema_version": "0.1", "lexicon_version": "0.1", "encoder": cache["metadata"],
                "head_runtime": {"torch": str(torch.__version__), "seed": seed}, "thresholds": best_thresholds,
                "best_epoch": best_epoch, "epochs": epochs, "dataset_sha256": digest(dataset), "weights_sha256": digest(output / "heads.safetensors"),
                "trainable_parameters": sum(p.numel() for p in model.parameters()), "elapsed_seconds": time.monotonic() - start,
                "decoder_sha256": digest(Path(__file__).with_name("structured.py")),
                "selection": "development selective coverage at >=95% exact precision and <=5% unsupported false acceptance; no final partition labels or predictions used"}
    metadata["decoder"] = decoder_name
    metadata["unknown_span_supervision"] = sum(bool(r.get("unknown_spans")) for r in rows if r["split"] == "train")
    if decoder_name == "joint-v1":
        metadata["joint_decoder_sha256"] = digest(Path(__file__).with_name("joint.py"))
    if regression_test:
        metadata["evaluation_status"] = "test partition was inspected in earlier experiments; subsequent test evaluation is regression, not independent final validation"
    save_json(output / "metadata.json", metadata)
    save_json(output / "development-report.json", {"metadata": metadata, "metrics": best_metrics, "history": history})
    return best_metrics


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="artifacts/corpus-v2.jsonl")
    parser.add_argument("--features", default="artifacts/corpus-v2-minilm.pt")
    parser.add_argument("--output", default="artifacts/sequence-v2-minilm")
    parser.add_argument("--epochs", type=int, default=35)
    parser.add_argument("--hidden", type=int, default=96)
    parser.add_argument("--decoder", choices=("independent-v4", "joint-v1"), default="independent-v4")
    parser.add_argument("--regression-test", action="store_true", help="Record that the test partition has already been inspected")
    args = parser.parse_args()
    if args.epochs < 1 or args.hidden < 1:
        parser.error("epochs and hidden must be positive")
    print(json.dumps(train(args.dataset, args.features, args.output, args.epochs, args.hidden, decoder_name=args.decoder, regression_test=args.regression_test), indent=2))


if __name__ == "__main__":
    main()
