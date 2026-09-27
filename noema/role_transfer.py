"""Vocabulary-independent semantic role heads over frozen Japanese PAS states."""
import torch
from torch import nn
from torch.nn import functional as F

from .semantics import require

LABELS = ("none", "agent", "patient", "recipient", "location")
UNLINKED = "__unlinked__"


class RoleHead(nn.Module):
    def __init__(self, dimension, cases, hidden=0):
        super().__init__()
        require(dimension > 0 and len(cases) == len(set(cases)), "Invalid role feature shape")
        self.dimension, self.cases, self.hidden = dimension, tuple(cases), hidden
        size = 5 * dimension + len(cases)
        self.network = nn.Linear(size, len(LABELS)) if hidden == 0 else nn.Sequential(
            nn.Linear(size, hidden), nn.Tanh(), nn.Linear(hidden, len(LABELS)))

    def forward(self, features):
        require(features.ndim == 2 and features.shape[1] == 5 * self.dimension + len(self.cases), "Invalid role features")
        return self.network(features)


def overlap(a, b):
    return a["start"] < b["end"] and a["end"] > b["start"]


def anchor(text, surface):
    require(text.count(surface) == 1, "Annotation anchor must occur exactly once")
    start = text.index(surface)
    return {"start": start, "end": start + len(surface)}


def candidates(prediction, vectors, cases):
    """No annotation or natural-language lookup table is accepted here."""
    require(len(vectors) == len(prediction["tokens"]), "Token vectors do not align")
    phrases = {p["id"]: p for p in prediction["phrases"]}
    pairs, features = [], []
    def pool(span):
        indices = [i for i, t in enumerate(prediction["tokens"]) if overlap(t, span)]
        require(bool(indices), "Phrase has no contextual vectors")
        return F.normalize(vectors[indices].mean(0), dim=0)
    for source in prediction["phrases"]:
        for relation in source["relations"]:
            if relation["label"] not in cases or relation["target_phrase"] is None:
                continue
            target = phrases[relation["target_phrase"]]
            predicate, argument, phrase = pool(source["head"]), pool(target["head"]), pool(source)
            case = F.one_hot(torch.tensor(cases.index(relation["label"])), len(cases)).float()
            features.append(torch.cat((predicate, argument, phrase, predicate * argument, predicate - argument, case)))
            pairs.append({"source": source["id"], "target": target["id"], "native_case": relation["label"]})
    size = vectors.shape[1] * 5 + len(cases)
    return pairs, torch.stack(features) if features else vectors.new_empty((0, size))


def all_phrase_candidates(prediction, vectors, cases):
    """Compare predicted predicates with every distinct source-text phrase.

    Native cases are features, never a required edge or a semantic-role rule.
    """
    require(len(vectors) == len(prediction["tokens"]) and cases[-1] == UNLINKED,
            "Expanded candidate feature inventory differs")
    require(len(cases) == len(set(cases)), "Repeated native case feature")
    def pool(span):
        indices = [i for i, token in enumerate(prediction["tokens"]) if overlap(token, span)]
        require(bool(indices), "Phrase has no contextual vectors")
        return F.normalize(vectors[indices].mean(0), dim=0)
    states = {p["id"]: (pool(p["head"]), pool(p)) for p in prediction["phrases"]}
    pairs, features = [], []
    for source in prediction["phrases"]:
        if not ("用言" in source["features"] or "非用言格解析" in source["features"]):
            continue
        predicate, phrase = states[source["id"]]
        for target in prediction["phrases"]:
            if source["id"] == target["id"]:
                continue
            labels = [label for label in cases[:-1] if any(
                r["label"] == label and r["target_phrase"] == target["id"] for r in source["relations"])]
            case = vectors.new_zeros(len(cases))
            for label in labels or [UNLINKED]:
                case[cases.index(label)] = 1
            argument = states[target["id"]][0]
            features.append(torch.cat((predicate, argument, phrase, predicate * argument, predicate - argument, case)))
            pairs.append({"source": source["id"], "target": target["id"], "native_cases": labels})
    size = vectors.shape[1] * 5 + len(cases)
    return pairs, torch.stack(features) if features else vectors.new_empty((0, size))


def targets(row, prediction, pairs):
    """Supervise annotated events only; avoid labeling unannotated events none."""
    phrases = {p["id"]: p for p in prediction["phrases"]}
    event = anchor(row["text"], row["predicate"])
    labels = []
    for pair in pairs:
        source, target = phrases[pair["source"]], phrases[pair["target"]]
        if not overlap(source["head"], event):
            labels.append(-100)
            continue
        matching = [role for role, surface in row["roles"] if overlap(target["head"], anchor(row["text"], surface))]
        require(len(matching) <= 1, "Multiple roles match one predicted argument")
        labels.append(LABELS.index(matching[0]) if matching else 0)
    return torch.tensor(labels, dtype=torch.long)


def assess(row, prediction, pairs, indices):
    phrases = {p["id"]: p for p in prediction["phrases"]}
    event = anchor(row["text"], row["predicate"])
    arguments = []
    for role, surface in row["roles"]:
        span = anchor(row["text"], surface)
        matched = [i for i, pair in enumerate(pairs) if overlap(phrases[pair["source"]]["head"], event)
                   and overlap(phrases[pair["target"]]["head"], span)]
        predicted = [LABELS[indices[i]] for i in matched]
        arguments.append({"role": role, "span": span, "detected": bool(matched),
                          "predicted": predicted, "correct": bool(matched) and all(p == role for p in predicted)})
    return {"id": row["id"], "split": row["split"], "family": row["family"],
            "voice": "passive" if row["id"].endswith("-p") else "active",
            "arguments": arguments, "all_specified_correct": all(a["correct"] for a in arguments)}


class RoleAnalyzer:
    """Research inference with a saved common head; no training corpus access."""
    def __init__(self, report="reports/role-transfer-v1", artifacts="artifacts/role-transfer-v1"):
        import json
        from pathlib import Path
        from safetensors.torch import load_file
        from .definition_probe import digest
        from .japanese_pas import JapanesePAS
        selection = json.loads((Path(report) / "selection.json").read_text(encoding="utf-8"))
        require(selection["labels"] == list(LABELS), "Role inventory differs from checkpoint")
        name = selection["selected"]
        path = Path(artifacts) / (name + ".safetensors")
        require(digest(path) == selection["weights_sha256"][name], "Role checkpoint hash differs")
        self.parser = JapanesePAS()
        self.head = RoleHead(selection["dimension"], selection["cases"], selection["choices"][name]["hidden"])
        self.head.load_state_dict(load_file(str(path)), strict=True)
        self.head.eval().requires_grad_(False)
        self.candidate_policy = selection.get("candidate_policy", "native")
        require(self.candidate_policy in ("native", "all_phrases"), "Unknown candidate policy")

    def analyze(self, text):
        prediction, vectors = self.parser.analyze(text, return_features=True)
        extract = all_phrase_candidates if self.candidate_policy == "all_phrases" else candidates
        pairs, features = extract(prediction, vectors, self.head.cases)
        with torch.inference_mode():
            probabilities = self.head(features).softmax(-1)
        indices = probabilities.argmax(-1)
        return {"status": "research_semantic_role_candidates", "analysis": prediction,
                "roles": [{**pair, "role": LABELS[int(index)], "confidence": float(probabilities[i, index])}
                          for i, (pair, index) in enumerate(zip(pairs, indices, strict=True))]}
