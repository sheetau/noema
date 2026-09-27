"""Shared role classification with source-position boundary context features."""
import json
from pathlib import Path

import torch
from torch import nn
from torch.nn import functional as F
from safetensors.torch import load_file

from .definition_probe import digest
from .mention_scope import TAGS, MentionHead, infer_mentions, mention_candidates, role_outputs
from .role_transfer import LABELS, overlap
from .semantics import require

FEATURES = ("mean", "boundary")


class ContextRoleHead(nn.Module):
    def __init__(self, dimension, cases, hidden=0, features="boundary"):
        super().__init__()
        require(features in FEATURES and dimension > 0, "Invalid contextual role feature mode")
        self.dimension, self.cases, self.hidden, self.features = dimension, tuple(cases), hidden, features
        self.input_size = (9 if features == "boundary" else 5) * dimension + len(cases)
        self.network = nn.Linear(self.input_size, len(LABELS)) if hidden == 0 else nn.Sequential(
            nn.Linear(self.input_size, hidden), nn.Tanh(), nn.Linear(hidden, len(LABELS)))

    def forward(self, features):
        require(features.ndim == 2 and features.shape[1] == self.input_size, "Invalid contextual role features")
        return self.network(features)


def context_candidates(prediction, vectors, mentions, cases, mode="boundary"):
    require(mode in FEATURES, "Unknown contextual role feature mode")
    pairs, base = mention_candidates(prediction, vectors, mentions, cases)
    if mode == "mean":
        return pairs, base
    dimension = vectors.shape[1]
    boundaries = {}
    for mention in mentions:
        indices = [i for i, token in enumerate(prediction["tokens"]) if overlap(token, mention)]
        require(bool(indices) and prediction["tokens"][indices[0]]["start"] == mention["start"]
                and prediction["tokens"][indices[-1]]["end"] == mention["end"], "Mention boundary is inside a source token")
        last = indices[-1]
        right = F.normalize(vectors[last + 1], dim=0) if last + 1 < len(vectors) else vectors.new_zeros(dimension)
        boundaries[mention["id"]] = F.normalize(vectors[last], dim=0), right
    extra = []
    for pair, row in zip(pairs, base, strict=True):
        last, right = boundaries[pair["target"]]
        predicate = row[:dimension]
        extra.append(torch.cat((last, right, predicate * right, predicate - right)))
    return pairs, torch.cat((base, torch.stack(extra)), dim=-1) if extra else vectors.new_empty((0, 9 * dimension + len(cases)))


class ContextRoleAnalyzer:
    """Saved research inference; boundary features do not change source spans."""
    def __init__(self, report="reports/role-context-v3", artifacts="artifacts/role-context-v3"):
        from .japanese_pas import JapanesePAS
        selection = json.loads((Path(report) / "selection.json").read_text(encoding="utf-8"))
        require(selection["tags"] == list(TAGS) and selection["labels"] == list(LABELS), "Context checkpoint inventory differs")
        name = selection["mention"]["selected"]
        path = Path(artifacts) / f"mention-{name}.safetensors"
        require(digest(path) == selection["mention"]["weights_sha256"][name], "Mention checkpoint hash differs")
        self.mention_head = MentionHead(selection["dimension"], selection["mention"]["choices"][name]["hidden"])
        self.mention_head.load_state_dict(load_file(str(path)), strict=True)
        self.mention_head.eval().requires_grad_(False)
        name = selection["role"]["selected"]
        choice = selection["role"]["choices"][name]
        path = Path(artifacts) / f"role-{name}.safetensors"
        require(digest(path) == selection["role"]["weights_sha256"][name], "Context role checkpoint hash differs")
        self.role_head = ContextRoleHead(selection["dimension"], selection["cases"], choice["hidden"], choice["features"])
        self.role_head.load_state_dict(load_file(str(path)), strict=True)
        self.role_head.eval().requires_grad_(False)
        self.parser = JapanesePAS()

    def analyze(self, text):
        prediction, vectors = self.parser.analyze(text, return_features=True)
        mentions = infer_mentions(prediction, vectors, self.mention_head)
        pairs, features = context_candidates(prediction, vectors, mentions, self.role_head.cases, self.role_head.features)
        _, roles = role_outputs(pairs, features, self.role_head)
        return {"status": "research_context_role_candidates", "analysis": prediction, "mentions": mentions, "roles": roles}
