"""Small sequence-aware classifiers over a frozen multilingual encoder.

BIO decoding constrains syntax of annotations, never applies lexical corrections.
Quantities and names are copied from learned spans, not inferred by a word table.
"""
import torch
from torch import nn
from torch.nn.utils.rnn import pack_padded_sequence, pad_packed_sequence
from .model import LABELS as BASE_LABELS, targets as baseline_targets
from .semantics import CONCEPTS, ROLES, SemanticError, make_graph

LABELS = {k: v for k, v in BASE_LABELS.items() if k != "quantity"}
LABELS["frame"] = [str(i) for i in range(16)]
LABELS["explicit_time"] = BASE_LABELS["time"]
TOKEN_HEADS = ("span", "concept", "role", "explicit_time")
GLOBAL_HEADS = tuple(k for k in LABELS if k not in TOKEN_HEADS)


def character_features(text, feature):
    """Project frozen subwords onto original characters, preserving exact spans.

    Structural position/Unicode features support span boundaries; there is no
    mapping from a natural-language word to its meaning in this projection.
    """
    dimension = feature["tokens"].shape[-1]
    rows = []
    for i, char in enumerate(text):
        overlap = [j for j, (a, b) in enumerate(feature["offsets"]) if a <= i < b]
        contextual = feature["tokens"][overlap].mean(0) if overlap else torch.zeros(dimension)
        if overlap:
            a = min(feature["offsets"][j][0] for j in overlap)
            b = max(feature["offsets"][j][1] for j in overlap)
            position = [(i - a) / max(1, b - a), (b - i - 1) / max(1, b - a), float(i == a), float(i == b - 1)]
        else:
            position = [0., 0., 0., 0.]
        rows.append(torch.cat((contextual, torch.tensor(position + [float(char.isspace()), float(char.isdecimal()),
                                                                  float(char.isupper()), float(char.islower()), float(ord(char) % 4096)]))))
    tokens = torch.stack(rows) if rows else torch.zeros(1, dimension + 9)
    return {"tokens": tokens, "offsets": [(i, i + 1) for i in range(len(text))] or [(0, 0)], "truncated": feature["truncated"]}


class SequenceHeads(nn.Module):
    def __init__(self, dimension, hidden=96):
        super().__init__()
        self.dimension, self.hidden = dimension, hidden
        self.normalization = nn.LayerNorm(dimension - 1)
        self.characters = nn.Embedding(4096, 24)
        self.projection = nn.Linear(dimension - 1 + 24, hidden)
        self.sequence = nn.GRU(hidden, hidden, batch_first=True, bidirectional=True)
        self.heads = nn.ModuleDict({k: nn.Linear(dimension - 1 + 24 + hidden * 2, len(labels)) for k, labels in LABELS.items()})
        self.attachment_query = nn.Linear(hidden * 2, 32)
        self.attachment_key = nn.Linear(hidden * 2, 32)
        self.attachment_distance = nn.Sequential(nn.Linear(3, 24), nn.Tanh(), nn.Linear(24, 1))

    def forward(self, tokens, lengths):
        normalized = torch.cat((self.normalization(tokens[:, :, :-1]), self.characters(tokens[:, :, -1].long())), -1)
        projected = self.projection(normalized).tanh()
        packed = pack_padded_sequence(projected, lengths.cpu(), batch_first=True, enforce_sorted=False)
        contextual, _ = self.sequence(packed)
        contextual, _ = pad_packed_sequence(contextual, batch_first=True, total_length=tokens.shape[1])
        combined = torch.cat((normalized, contextual), -1)
        mask = torch.arange(tokens.shape[1], device=tokens.device)[None, :] < lengths[:, None]
        pooled = (combined * mask.unsqueeze(-1)).sum(1) / lengths[:, None]
        result = {k: self.heads[k](combined if k in TOKEN_HEADS else pooled) for k in LABELS}
        positions = torch.arange(tokens.shape[1], device=tokens.device)
        distance = positions[None, :] - positions[:, None]
        relative = torch.stack((distance.clamp(-32, 32) / 32., distance.abs().clamp(max=32) / 32., distance.sign().float()), -1)
        result["attachment"] = (self.attachment_query(contextual) @ self.attachment_key(contextual).transpose(1, 2)) / 32 ** .5
        result["attachment"] = result["attachment"] + self.attachment_distance(relative).squeeze(-1)
        result["attachment"] = result["attachment"].masked_fill(~mask[:, None, :], -torch.inf)
        return result


def targets(row, feature):
    # Reuse the annotation projection, but not the baseline's bounded quantity head.
    if row["supported"]:
        projected = {**row, "spans": [{**s, "quantity": "unspecified"} for s in row["spans"]]}
    else:
        projected = row
    result = {k: v for k, v in baseline_targets(projected, feature).items() if k != "quantity"}
    result["frame"] = torch.tensor(-100)
    result["explicit_time"] = torch.full((len(feature["offsets"]),), -100, dtype=torch.long)
    result["attachment"] = torch.full((len(feature["offsets"]),), -100, dtype=torch.long)
    if row["supported"]:
        present = {r["role"] for r in row["graph"]["relations"] if r["target"] is not None}
        result["frame"] = torch.tensor(sum(1 << i for i, role in enumerate(ROLES) if role in present))
        for span in row["spans"]:
            if span["kind"] == "time":
                t = row["graph"]["nodes"][0]["time"]["value"] or "unspecified"
                for i, (start, end) in enumerate(feature["offsets"]):
                    if start < end and start < span["end"] and end > span["start"]:
                        result["explicit_time"][i] = LABELS["explicit_time"].index(t)
            if span["kind"] == "quantity":
                entity = next(s for s in row["spans"] if s["kind"] == "entity" and s["role"] == span["role"])
                for i, (start, end) in enumerate(feature["offsets"]):
                    if start < end and start < span["end"] and end > span["start"]:
                        result["role"][i] = LABELS["role"].index(span["role"])
                        result["attachment"][i] = entity["start"]
    return result


def bio_path(logits, text=None):
    """Maximum-scoring legal BIO path; no repair after independent argmax."""
    labels = LABELS["span"]
    if len(logits) == 0:
        return []
    scores = logits.log_softmax(-1)
    if text is not None:
        if len(text) != len(scores):
            raise ValueError("Character BIO decoding requires one character per position")
        scores = scores.clone()
        for i, char in enumerate(text):
            if not char.isdecimal():
                scores[i, labels.index("B-quantity")] = -torch.inf
                scores[i, labels.index("I-quantity")] = -torch.inf
            elif i and text[i - 1].isdecimal():
                # A typed decimal literal has no boundary inside a digit run.
                scores[i, labels.index("B-quantity")] = -torch.inf
    transition = scores.new_zeros((len(labels), len(labels)))
    start = scores.new_zeros(len(labels))
    for j, label in enumerate(labels):
        if label.startswith("I-"):
            start[j] = -torch.inf
            for i, previous in enumerate(labels):
                if previous not in ("B-" + label[2:], label):
                    transition[i, j] = -torch.inf
    state, back = scores[0] + start, []
    for emission in scores[1:]:
        state, previous = (state[:, None] + transition).max(0)
        state = state + emission
        back.append(previous)
    last = int(state.argmax())
    path = [last]
    for previous in reversed(back):
        last = int(previous[last])
        path.append(last)
    return list(reversed(path))


def decode(text, feature, logits, threshold=0.):
    result = {"status": "unresolved", "graph": None, "diagnostics": {"confidence": 0., "spans": [], "reason": None}}
    diag = result["diagnostics"]
    if feature["truncated"]:
        diag["reason"] = "input_too_long"
        return result
    if not text.strip():
        result["status"], diag["reason"] = "unsupported", "empty_input"
        return result
    probs = {k: v.softmax(-1) for k, v in logits.items()}
    support = float(probs["support"][1])
    if support < .5:
        result["status"], diag["reason"], diag["confidence"] = "unsupported", "support_classifier", 1 - support
        return result
    confidences = [support]
    valid = [i for i, (a, b) in enumerate(feature["offsets"]) if a < b]
    path = bio_path(logits["span"][valid], text)
    spans, current = [], None
    for index, label_index in zip(valid, path):
        label = LABELS["span"][label_index]
        start, end = feature["offsets"][index]
        if label == "O":
            current = None
        elif label.startswith("B-"):
            current = {"kind": label[2:], "start": start, "end": end, "indices": [index], "probabilities": [float(probs["span"][index, label_index])]}
            spans.append(current)
        else:
            current["end"] = end
            current["indices"].append(index)
            current["probabilities"].append(float(probs["span"][index, label_index]))

    def choose(key, indices=None):
        values = probs[key] if indices is None else probs[key][indices].mean(0)
        confidence, index = values.max(-1)
        confidences.append(float(confidence))
        return LABELS[key][int(index)]

    predicate, entities, quantities, explicit_time = None, {}, {}, None
    try:
        for span in spans:
            confidences.append(sum(span["probabilities"]) / len(span["probabilities"]))
            start, end = span["start"], span["end"]
            while start < end and text[start].isspace():
                start += 1
            while end > start and text[end - 1].isspace():
                end -= 1
            literal = text[start:end]
            evidence = {"start": start, "end": end, "kind": span["kind"], "text": literal}
            if span["kind"] in ("predicate", "entity"):
                concept = choose("concept", span["indices"])
                evidence["concept"] = concept
                if concept not in CONCEPTS:
                    raise SemanticError("Unknown concept prediction")
                if span["kind"] == "predicate":
                    if predicate is not None or CONCEPTS[concept]["kind"] not in ("event", "state"):
                        raise SemanticError("Expected one predicate")
                    predicate = concept
                else:
                    role = choose("role", span["indices"])
                    evidence["role"] = role
                    if role == "none" or role in entities or CONCEPTS[concept]["kind"] not in ("entity", "place"):
                        raise SemanticError("Invalid or duplicate entity role")
                    entities[role] = {"concept": concept, "quantity": None, "name": literal if concept == "ag" else None}
            elif span["kind"] == "quantity":
                candidates = [s for s in spans if s["kind"] == "entity"]
                if not candidates:
                    raise SemanticError("Quantity has no entity")
                if "attachment" in logits:
                    scores = logits["attachment"][span["indices"]].mean(0)
                    candidate_scores = scores[[s["indices"][0] for s in candidates]].softmax(-1)
                    confidence, index = candidate_scores.max(0)
                    confidences.append(float(confidence))
                    attached = candidates[int(index)]
                    role = choose("role", attached["indices"])
                    evidence["target_start"] = attached["start"]
                else:
                    role = choose("role", span["indices"])
                evidence["role"] = role
                if not literal.isdecimal() or role == "none" or role in quantities:
                    raise SemanticError("Quantity requires one nonnegative decimal literal per role")
                # General typed literal conversion, independent of the input language.
                quantities[role] = int(literal)
            elif span["kind"] == "time":
                if explicit_time is not None:
                    raise SemanticError("Multiple time scopes")
                explicit_time = choose("explicit_time", span["indices"])
            diag["spans"].append(evidence)
        if predicate is None:
            raise SemanticError("Missing predicate")
        if any(role not in entities for role in quantities):
            raise SemanticError("Quantity has no entity")
        for role, quantity in quantities.items():
            entities[role]["quantity"] = quantity
        frame = int(choose("frame"))
        if frame != sum(1 << i for i, r in enumerate(ROLES) if r in entities):
            raise SemanticError("Role presence and extracted entities disagree")
        graph = make_graph(predicate, entities, choose("polarity"), explicit_time if explicit_time is not None else choose("time"))
        diag["confidence"] = min(confidences)
        if diag["confidence"] >= threshold:
            result["status"], result["graph"] = "confirmed", graph
        else:
            diag["reason"] = "low_confidence"
    except SemanticError as exc:
        diag["reason"], diag["confidence"] = "inconsistent_structure: " + str(exc), min(confidences)
    return result
