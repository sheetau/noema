"""Per-head errors before structure assembly or confidence rejection."""
import torch
from .model import LABELS, targets


def head_metrics(model, rows, features):
    totals = {lang: {key: {"correct": 0, "total": 0, "confusions": {}} for key in LABELS} for lang in ("ja", "en")}
    model.eval()
    with torch.inference_mode():
        for row, feature in zip(rows, features):
            gold = targets(row, feature)
            logits = model(feature["tokens"], feature["pooled"])
            for key in LABELS:
                expected = gold[key].reshape(-1)
                predicted = logits[key].argmax(-1).reshape(-1)
                valid = expected != -100
                metric = totals[row["language"]][key]
                metric["total"] += int(valid.sum())
                metric["correct"] += int(((expected == predicted) & valid).sum())
                for a, b in zip(expected[valid].tolist(), predicted[valid].tolist()):
                    if a != b:
                        pair = LABELS[key][a] + " -> " + LABELS[key][b]
                        metric["confusions"][pair] = metric["confusions"].get(pair, 0) + 1
    for lang in totals.values():
        for metric in lang.values():
            metric["accuracy"] = metric["correct"] / metric["total"] if metric["total"] else None
    return totals
