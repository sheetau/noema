"""Feature caching, head-only training, development selection, final held-out evaluation."""
import hashlib
import json
from pathlib import Path
import time
import torch
from torch.nn import functional as F
from .dataset import digest, load_dataset
from .encoder import FrozenEncoder, deterministic
from .evaluation import evaluate
from .model import Heads, LABELS, TOKEN_HEADS, GLOBAL_HEADS, targets, decode


def save_json(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def cache_features(dataset, output, model="xlmr", device="cpu", batch_size=16, offline=False):
    rows = load_dataset(dataset)
    encoder = FrozenEncoder(model, device, offline)
    features = []
    started = time.monotonic()
    for start in range(0, len(rows), batch_size):
        features.extend(encoder.encode([r["text"] for r in rows[start:start + batch_size]], batch_size))
        if start % (batch_size * 20) == 0:
            print(f"features {start + min(batch_size, len(rows) - start)}/{len(rows)}", flush=True)
    # Repetition test uses batch size 1 both times; padding-dependent numerical differences are a separate question.
    probes = [next(r["text"] for r in rows if r["language"] == lang and r["supported"]) for lang in ("ja", "en")]
    first, second = encoder.encode(probes, 1), encoder.encode(probes, 1)
    repeat = all(torch.equal(a["tokens"], b["tokens"]) for a, b in zip(first, second))
    payload = {"format": 1, "dataset_sha256": digest(dataset), "ids": [r["id"] for r in rows],
               "metadata": encoder.metadata, "features": features, "dimension": encoder.dimension,
               "repeat_exact": repeat, "elapsed_seconds": time.monotonic() - started, "batch_size": batch_size}
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    torch.save(payload, output)
    return {k: v for k, v in payload.items() if k not in ("features", "ids")}


def load_cache(dataset, path):
    rows = load_dataset(dataset)
    cache = torch.load(path, map_location="cpu", weights_only=True)
    if cache.get("format") != 1 or cache["dataset_sha256"] != digest(dataset) or cache["ids"] != [r["id"] for r in rows]:
        raise ValueError("Feature cache does not match dataset")
    return rows, cache


def batches(indices, features, labels, batch_size=64):
    for start in range(0, len(indices), batch_size):
        selected = indices[start:start + batch_size]
        token = torch.cat([torch.cat((features[i]["tokens"], features[i]["pooled"].expand(len(features[i]["tokens"]), -1)), -1) for i in selected])
        pooled = torch.stack([features[i]["pooled"] for i in selected])
        target = {k: torch.cat([labels[i][k] for i in selected]) if k in TOKEN_HEADS else torch.stack([labels[i][k] for i in selected]) for k in LABELS}
        yield token, pooled, target


def losses(model, batch, weights):
    token, pooled, target = batch
    result = []
    for key in LABELS:
        if (target[key] != -100).any():
            logits = model.heads[key](token if key in TOKEN_HEADS else pooled)
            result.append(F.cross_entropy(logits, target[key], weight=weights.get(key), ignore_index=-100))
    return torch.stack(result).mean()


def infer_features(model, rows, features, threshold):
    model.eval()
    predictions, sentence_hits = [], 0
    with torch.inference_mode():
        for row, feature in zip(rows, features):
            logits = model(feature["tokens"], feature["pooled"])
            predictions.append(decode(row["text"], feature, logits, threshold))
            if row["supported"]:
                event = row["graph"]["nodes"][0]
                sentence_hits += LABELS["sentence_concept"][int(logits["sentence_concept"].argmax())] == event["concept"]
    return predictions, {"correct": sentence_hits, "total": sum(r["supported"] for r in rows), "task": "sentence-level predicate concept only; not structure extraction"}


def train(dataset, cache_path, output, architecture="linear", epochs=30, fraction=1.0, threshold=.9, seed=17):
    if epochs < 1 or not 0 < fraction <= 1 or not 0 <= threshold <= 1:
        raise ValueError("Invalid epochs, fraction or threshold")
    deterministic(seed)
    rows, cache = load_cache(dataset, cache_path)
    features = cache["features"]
    labels = [targets(r, f) for r, f in zip(rows, features)]
    groups = sorted({r["group"] for r in rows if r["split"] == "train" and r["supported"]})
    generator = torch.Generator().manual_seed(seed)
    shuffled = torch.randperm(len(groups), generator=generator).tolist()
    selected = {groups[i] for i in shuffled[:max(1, int(len(groups) * fraction))]}
    training = [i for i, r in enumerate(rows) if r["split"] == "train" and (r["group"] in selected or not r["supported"])]
    development = [i for i, r in enumerate(rows) if r["split"] == "dev"]
    if not training or not development:
        raise ValueError("Training and development splits must be nonempty")
    model = Heads(cache["dimension"], architecture)
    optimizer = torch.optim.AdamW(model.parameters(), lr=.005 if architecture == "linear" else .001, weight_decay=.01)
    counts = torch.bincount(torch.stack([labels[i]["support"] for i in training]), minlength=2).float()
    weights = {"support": counts.sum() / (2 * counts.clamp_min(1))}
    best, best_state, best_epoch, history = float("inf"), None, None, []
    started = time.monotonic()
    for epoch in range(epochs):
        model.train()
        order = [training[i] for i in torch.randperm(len(training), generator=generator).tolist()]
        total = 0.0
        for batch in batches(order, features, labels):
            optimizer.zero_grad(set_to_none=True)
            loss = losses(model, batch, weights)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 5.)
            optimizer.step()
            total += float(loss.detach())
        model.eval()
        with torch.inference_mode():
            validation = [float(losses(model, batch, weights)) for batch in batches(development, features, labels)]
        value = sum(validation) / len(validation)
        history.append({"epoch": epoch + 1, "dev_loss": value})
        if value < best:
            best, best_epoch = value, epoch + 1
            best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
        if epoch == 0 or (epoch + 1) % 5 == 0:
            print(f"epoch {epoch + 1}/{epochs} dev_loss={value:.4f}", flush=True)
    model.load_state_dict(best_state)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    # All metadata is JSON; weights use safetensors, so inference never unpickles a checkpoint.
    from safetensors.torch import save_file
    save_file(model.state_dict(), str(output / "heads.safetensors"))
    metadata = {"format": 1, "schema_version": "0.1", "lexicon_version": "0.1", "labels": LABELS,
                "dimension": cache["dimension"], "architecture": architecture, "encoder": cache["metadata"],
                "threshold": threshold, "seed": seed, "training_fraction": fraction, "training_rows": len(training),
                "dataset_sha256": cache["dataset_sha256"], "best_epoch": best_epoch, "epochs": epochs,
                "encoder_repeat_exact": cache["repeat_exact"], "encoder_batch_size": cache["batch_size"],
                "elapsed_seconds": time.monotonic() - started,
                "weights_sha256": digest(output / "heads.safetensors")}
    save_json(output / "metadata.json", metadata)
    report = {"metadata": metadata, "history": history, "threshold_policy": "fixed before final evaluation; no test-set calibration"}
    for split in ("dev", "test"):
        indices = [i for i, r in enumerate(rows) if r["split"] == split]
        subset, fs = [rows[i] for i in indices], [features[i] for i in indices]
        predictions, sentence = infer_features(model, subset, fs, threshold)
        # Ungated component failures are reported too; abstentions alone hide what needs improvement.
        raw, _ = infer_features(model, subset, fs, 0.)
        report[split] = {"selective": evaluate(subset, predictions), "without_confidence_gate": evaluate(subset, raw), "sentence_concept": sentence}
        save_json(output / f"{split}-predictions.json", [{"id": r["id"], **p} for r, p in zip(subset, predictions)])
    save_json(output / "report.json", report)
    return report
