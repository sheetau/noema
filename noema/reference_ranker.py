"""Vocabulary-independent antecedent ranking over frozen contextual features."""
import math

import torch
from torch import nn

from .kwdlc_references import IDENTITY_TYPES, gold_partition
from .semantics import require


from .reference_features import extract_reference_features


def scalar_features(features):
    nodes, native, positions = features["nodes"], features["native"], features["word_indices"]
    n, size = nodes.shape
    require(size % 2 == 0 and native.shape == (n, n + 1) and positions.shape == (n,), "Invalid reference feature shapes")
    require(bool(torch.isfinite(nodes).all()) and bool(torch.isfinite(native).all()), "Non-finite reference features")
    dimension = size // 2
    targets = torch.cat((nodes.new_zeros((1, size)), nodes))
    head_cos = nodes[:, :dimension] @ targets[:, :dimension].T
    phrase_cos = nodes[:, dimension:] @ targets[:, dimension:].T
    margin = native - native[:, :1]
    margin = margin.sign() * torch.log1p(margin.abs())
    distances = (positions[:, None] - positions[None, :]).clamp_min(0).to(nodes.dtype)
    distances = torch.cat((nodes.new_zeros((n, 1)), torch.log1p(distances) / math.log1p(max(int(features["word_count"]), 1))), dim=1)
    null = nodes.new_zeros((n, n + 1))
    null[:, 0] = 1
    return torch.stack((margin, head_cos, phrase_cos, distances, null), dim=-1)


class ReferenceRanker(nn.Module):
    def __init__(self, dimension, hidden=0):
        super().__init__()
        self.dimension, self.hidden = dimension, hidden
        if hidden:
            self.project = nn.Sequential(nn.Linear(dimension * 2, hidden), nn.Tanh())
            self.network = nn.Sequential(nn.Linear(hidden * 4 + 5, hidden), nn.Tanh(), nn.Linear(hidden, 1))
        else:
            self.network = nn.Linear(5, 1)

    def forward(self, features):
        nodes = features["nodes"]
        require(nodes.shape[1] == self.dimension * 2, "Reference vector dimension differs")
        scalars = features.get("scalars")
        if scalars is None:
            scalars = scalar_features(features)
        n = len(nodes)
        require(scalars.shape == (n, n + 1, 5), "Reference scalar feature shape differs")
        if self.hidden:
            projected = self.project(nodes)
            source = projected[:, None, :].expand(n, n + 1, -1)
            target = torch.cat((projected.new_zeros((1, self.hidden)), projected))[None, :, :].expand(n, n + 1, -1)
            inputs = torch.cat((source, target, source * target, source - target, scalars), dim=-1)
        else:
            inputs = scalars
        scores = self.network(inputs).squeeze(-1)
        mask = torch.arange(n + 1, device=scores.device)[None, :] > torch.arange(n, device=scores.device)[:, None]
        return scores.masked_fill(mask, -torch.inf)


def reference_targets(row, prediction):
    heads = [p["head"] for p in prediction["phrases"]]
    spans = [(h["start"], h["end"]) for h in heads]
    gh, gp = gold_partition(row)
    target = torch.zeros((len(heads), len(heads) + 1), dtype=torch.bool)
    counts = {"supervised": 0, "positive": 0, "no_antecedent": 0, "unmatched_source": 0,
              "missing_antecedent": 0, "unsupported_annotation": 0}
    if any(r["type"] in IDENTITY_TYPES and r["mode"] is not None for r in row["relations"]):
        counts["unsupported_annotation"] = len(heads)
        return target, counts
    for i, span in enumerate(spans):
        if span not in gh:
            counts["unmatched_source"] += 1
            continue
        earlier = {b if a == span else a for a, b in gp if span in (a, b) and min(a[0], b[0]) < span[0]}
        candidates = [j + 1 for j, other in enumerate(spans[:i]) if other in earlier]
        if earlier and not candidates:
            counts["missing_antecedent"] += 1
            continue
        target[i, candidates or [0]] = True
        counts["supervised"] += 1
        counts["positive" if candidates else "no_antecedent"] += 1
    return target, counts


def marginal_reference_loss(scores, target):
    require(scores.shape == target.shape and target.dtype == torch.bool, "Reference targets differ")
    active = target.any(-1)
    if not bool(active.any()):
        return scores.new_zeros(()), 0
    selected = scores[active]
    require(bool(torch.isfinite(selected.masked_select(target[active])).all()), "Gold reference candidate is masked")
    losses = torch.logsumexp(selected, -1) - torch.logsumexp(selected.masked_fill(~target[active], -torch.inf), -1)
    return losses.sum(), int(active.sum())


def rank_references(prediction, features, head):
    import copy
    result = copy.deepcopy(prediction)
    with torch.inference_mode():
        scores = head(features)
        choices = scores.argmax(-1).tolist() if len(scores) else []
        probabilities = scores.softmax(-1)
    decisions = []
    for i, (phrase, choice) in enumerate(zip(result["phrases"], choices, strict=True)):
        # Keep external references and non-identity evidence in the raw result.
        phrase["relations"] = [r for r in phrase["relations"] if r["label"] != "=" or r["target_phrase"] is None]
        target = result["phrases"][choice - 1]["id"] if choice else None
        if choice:
            phrase["relations"].append({"label": "=", "target_phrase": target, "external": None})
        decisions.append({"source": phrase["id"], "target": target, "score": float(probabilities[i, choice]),
                          "candidate_probabilities": probabilities[i, :i + 1].tolist()})
    return result, decisions


class ReferenceRankerAnalyzer:
    def __init__(self, report="reports/reference-ranker-v1", artifacts="artifacts/reference-ranker-v1"):
        import json
        from pathlib import Path
        from safetensors.torch import load_file
        from .definition_probe import digest
        from .japanese_pas_aligned import AlignedJapanesePAS
        selection = json.loads((Path(report) / "selection.json").read_text(encoding="utf-8"))
        require(selection["decision"] == "argmax_previous_or_none", "Unknown reference decision policy")
        name = selection["selected"]
        path = Path(artifacts) / f"ranker-{name}.safetensors"
        require(digest(path) == selection["weights_sha256"][name], "Reference ranker weights changed")
        self.head = ReferenceRanker(selection["dimension"], selection["choices"][name]["hidden"])
        self.head.load_state_dict(load_file(str(path)), strict=True)
        self.head.eval().requires_grad_(False)
        self.parser = AlignedJapanesePAS()
        require(self.parser.metadata == selection["model"], "Reference feature model or runtime changed")

    def analyze(self, text):
        prediction, features = extract_reference_features(self.parser, text)
        ranked, decisions = rank_references(prediction, features, self.head)
        return {"status": "research_reference_ranker", "analysis": prediction,
                "ranked_prediction": ranked, "reference_decisions": decisions}
