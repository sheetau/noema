"""Learn event candidacy from context, without lexical exclusion lists."""
import json
from pathlib import Path

import torch
from torch import nn
from torch.nn import functional as F
from safetensors.torch import load_file

from .definition_probe import digest
from .event_frames import (EventFrameAnalyzer, predicate_candidates, matching_frame,
                           conditioned_vectors, scoped_candidates)
from .mention_scope import role_outputs
from .mention_sequence import infer_sequence_mentions
from .role_transfer import overlap
from .semantics import require

GATE_LABELS = ("not_event", "event")


class EventGateHead(nn.Module):
    def __init__(self, dimension, hidden=0):
        super().__init__()
        self.dimension, self.hidden = dimension, hidden
        self.network = nn.Linear(6 * dimension, 2) if hidden == 0 else nn.Sequential(
            nn.Linear(6 * dimension, hidden), nn.Tanh(), nn.Linear(hidden, 2))

    def forward(self, features):
        require(features.ndim == 2 and features.shape[1] == self.dimension * 6, "Invalid event gate features")
        return self.network(features)


def event_features(prediction, vectors):
    require(len(prediction["tokens"]) == len(vectors), "Event source vectors differ")
    candidates, features = predicate_candidates(prediction), []
    for source in candidates:
        head_indices = [i for i, token in enumerate(prediction["tokens"]) if overlap(token, source["head"])]
        phrase_indices = [i for i, token in enumerate(prediction["tokens"]) if overlap(token, source)]
        require(bool(head_indices) and bool(phrase_indices), "Event candidate has no contextual vectors")
        head = F.normalize(vectors[head_indices].mean(0), dim=0)
        phrase = F.normalize(vectors[phrase_indices].mean(0), dim=0)
        left = F.normalize(vectors[head_indices[0] - 1], dim=0) if head_indices[0] > 0 else vectors.new_zeros(vectors.shape[1])
        right = F.normalize(vectors[head_indices[-1] + 1], dim=0) if head_indices[-1] + 1 < len(vectors) else vectors.new_zeros(vectors.shape[1])
        features.append(torch.cat((head, phrase, left, right, head * phrase, head - phrase)))
    return candidates, torch.stack(features) if features else vectors.new_empty((0, 6 * vectors.shape[1]))


def gate_targets(document, candidates):
    return torch.tensor([1 if matching_frame(document, candidate) is not None else 0 if document["complete_frames"] else -100
                         for candidate in candidates], dtype=torch.long)


def event_decisions(prediction, vectors, head):
    candidates, features = event_features(prediction, vectors)
    with torch.inference_mode():
        probabilities = head(features).softmax(-1)
    choices = probabilities.argmax(-1).tolist()
    return [{"source": source["id"], "predicate": source["head"], "keep": choice == 1,
             "event_score": float(probabilities[i, 1])} for i, (source, choice) in enumerate(zip(candidates, choices, strict=True))]


def assess_gate(document, prediction, decisions):
    candidates = predicate_candidates(prediction)
    require([d["source"] for d in decisions] == [c["id"] for c in candidates], "Event decisions differ from candidates")
    targets = gate_targets(document, candidates).tolist()
    before, after = set(), set()
    for candidate, decision in zip(candidates, decisions, strict=True):
        frame = matching_frame(document, candidate)
        if frame is not None:
            before.add(frame)
            if decision["keep"]:
                after.add(frame)
    counts = {"gold_events": len(document["frames"]), "detected_before": len(before), "retained_events": len(after),
              "newly_lost_events": len(before - after), "upstream_misses": len(document["frames"]) - len(before),
              "positive_kept": 0, "positive_rejected": 0, "negative_kept": 0, "negative_rejected": 0,
              "unlabeled_kept": 0, "unlabeled_rejected": 0}
    for target, decision in zip(targets, decisions, strict=True):
        kind = "positive" if target == 1 else "negative" if target == 0 else "unlabeled"
        counts[kind + ("_kept" if decision["keep"] else "_rejected")] += 1
    return counts


def kept_frames(prediction, vectors, mention_head, role_head, decisions):
    sources = predicate_candidates(prediction)
    require([d["source"] for d in decisions] == [s["id"] for s in sources], "Frame gate decisions differ")
    frames = []
    for source, decision in zip(sources, decisions, strict=True):
        if not decision["keep"]:
            continue
        mentions = infer_sequence_mentions(prediction, conditioned_vectors(prediction, vectors, source), mention_head)
        pairs, features = scoped_candidates(prediction, vectors, source, mentions, role_head.cases)
        _, roles = role_outputs(pairs, features, role_head)
        frames.append({"source": source["id"], "predicate": source["head"], "mentions": mentions, "roles": roles})
    return frames


class GatedEventFrameAnalyzer:
    def __init__(self, report="reports/event-gate-v6", artifacts="artifacts/event-gate-v6"):
        selection = json.loads((Path(report) / "selection.json").read_text(encoding="utf-8"))
        require(selection["labels"] == list(GATE_LABELS) and selection["decision"] == "argmax", "Unknown gate decision policy")
        require(digest(Path(selection["frame_report"]) / "selection.json") == selection["frame_selection_sha256"], "Frame selection changed")
        name = selection["selected"]
        path = Path(artifacts) / f"gate-{name}.safetensors"
        require(digest(path) == selection["weights_sha256"][name], "Event gate checkpoint changed")
        self.gate = EventGateHead(selection["dimension"], selection["choices"][name]["hidden"])
        self.gate.load_state_dict(load_file(str(path)), strict=True)
        self.gate.eval().requires_grad_(False)
        self.frame = EventFrameAnalyzer(selection["frame_report"], selection["frame_artifacts"])

    def analyze(self, text):
        prediction, vectors = self.frame.parser.analyze(text, return_features=True)
        decisions = event_decisions(prediction, vectors, self.gate)
        frames = kept_frames(prediction, vectors, self.frame.mention_head, self.frame.role_head, decisions)
        return {"status": "research_gated_event_frames", "analysis": prediction, "event_decisions": decisions, "frames": frames}
