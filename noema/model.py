"""Small independent heads over fixed token and sentence representations."""
import torch
from torch import nn
from .semantics import CONCEPTS, POLARITIES, ROLES, TIMES, SemanticError, make_graph

KINDS = ("predicate", "entity", "quantity", "time", "negation")
LABELS = {
    "span": ["O"] + [prefix + "-" + kind for kind in KINDS for prefix in ("B", "I")],
    "concept": ["none"] + list(CONCEPTS),
    "role": ["none"] + list(ROLES),
    "quantity": ["unspecified"] + [str(i) for i in range(11)],
    "polarity": list(POLARITIES), "time": list(TIMES), "support": ["unsupported", "supported"],
    "sentence_concept": ["none"] + [c for c, info in CONCEPTS.items() if info["kind"] in ("event", "state")]
}
TOKEN_HEADS = ("span", "concept", "role", "quantity")
GLOBAL_HEADS = ("polarity", "time", "support", "sentence_concept")


class Heads(nn.Module):
    def __init__(self, dimension, architecture="linear"):
        super().__init__()
        if architecture not in ("linear", "mlp"):
            raise ValueError("Unknown head architecture")
        self.dimension, self.architecture = dimension, architecture
        def head(d, n):
            return nn.Linear(d, n) if architecture == "linear" else nn.Sequential(nn.Linear(d, 128), nn.Tanh(), nn.Linear(128, n))
        self.heads = nn.ModuleDict({k: head(dimension * 2 if k in TOKEN_HEADS else dimension, len(labels)) for k, labels in LABELS.items()})

    def forward(self, tokens, pooled):
        token_features = torch.cat((tokens, pooled.expand(tokens.shape[0], -1)), dim=-1)
        return {k: self.heads[k](token_features if k in TOKEN_HEADS else pooled) for k in LABELS}


def targets(row, feature):
    count = len(feature["offsets"])
    result = {k: torch.full((count,), -100, dtype=torch.long) for k in TOKEN_HEADS}
    result["support"] = torch.tensor(int(row["supported"]))
    for k in ("polarity", "time", "sentence_concept"):
        result[k] = torch.tensor(-100)
    if not row["supported"]:
        return result
    graph = row["graph"]
    event = next(n for n in graph["nodes"] if n["kind"] in ("event", "state"))
    for key, value in (("polarity", event["polarity"]), ("time", event["time"]["value"] or "unspecified"), ("sentence_concept", event["concept"])):
        result[key] = torch.tensor(LABELS[key].index(value))
    for i, (start, end) in enumerate(feature["offsets"]):
        if start == end:
            continue
        result["span"][i] = 0
    primary = [s for s in row["spans"] if s["kind"] in ("predicate", "entity")]
    for span in row["spans"]:
        matched = [i for i, (s, e) in enumerate(feature["offsets"]) if s < e and s < span["end"] and e > span["start"]]
        if span["kind"] not in ("predicate", "entity"):
            # A subword may include a predicate and its negative suffix. Assign that
            # token to the predicate; polarity still has its separate sentence target.
            # This is tokenizer alignment, independent of language and surface words.
            matched = [i for i in matched if not any(feature["offsets"][i][0] < s["end"] and feature["offsets"][i][1] > s["start"] for s in primary)]
        for index, i in enumerate(matched):
            # Two distinct entities/predicates in one token cannot be represented.
            if result["span"][i] > 0:
                raise ValueError(f"Token overlaps annotations: {row['id']}")
            result["span"][i] = LABELS["span"].index(("B-" if index == 0 else "I-") + span["kind"])
            if span["kind"] in ("predicate", "entity"):
                result["concept"][i] = LABELS["concept"].index(span["concept"])
            if span["kind"] == "entity":
                result["role"][i] = LABELS["role"].index(span["role"])
                result["quantity"][i] = LABELS["quantity"].index(span["quantity"])
    return result


def decode(text, feature, logits, threshold=0.9):
    """Validate predicted annotations; never repair their meanings with lexical rules."""
    probabilities = {k: value.softmax(-1) for k, value in logits.items()}
    support = float(probabilities["support"][1])
    result = {"status": "unresolved", "graph": None, "diagnostics": {"confidence": support, "spans": [], "reason": None}}
    diag = result["diagnostics"]
    if feature["truncated"]:
        diag["reason"] = "input_too_long"
        return result
    if not text.strip():
        result["status"], diag["reason"] = "unsupported", "empty_input"
        return result
    if support < 0.5:
        result["status"], diag["reason"] = "unsupported", "support_classifier"
        return result
    confidences = [support]
    spans, current = [], None
    try:
        for i, (start, end) in enumerate(feature["offsets"]):
            if start == end:
                continue
            confidence, label_id = probabilities["span"][i].max(-1)
            confidences.append(float(confidence))
            label = LABELS["span"][int(label_id)]
            if label == "O":
                current = None
                continue
            prefix, kind = label.split("-")
            if prefix == "B":
                current = {"start": start, "end": end, "kind": kind, "indices": [i]}
                spans.append(current)
            else:
                if current is None or current["kind"] != kind:
                    raise SemanticError("Invalid BIO sequence")
                current["end"] = end
                current["indices"].append(i)
        def choose(key, indices=None):
            p = probabilities[key] if indices is None else probabilities[key][indices].mean(0)
            confidence, index = p.max(-1)
            confidences.append(float(confidence))
            return LABELS[key][int(index)]
        predicate, entities = None, {}
        for span in spans:
            # Fast tokenizers can include leading whitespace; trim only boundaries for literal names.
            start, end = span["start"], span["end"]
            while start < end and text[start].isspace():
                start += 1
            annotation = {"start": start, "end": end, "kind": span["kind"], "text": text[start:end]}
            if span["kind"] in ("predicate", "entity"):
                concept = choose("concept", span["indices"])
                annotation["concept"] = concept
                if concept not in CONCEPTS:
                    raise SemanticError("Unknown concept prediction")
                if span["kind"] == "predicate":
                    if predicate is not None or CONCEPTS[concept]["kind"] not in ("event", "state"):
                        raise SemanticError("Expected one predicate")
                    predicate = concept
                else:
                    role = choose("role", span["indices"])
                    quantity = choose("quantity", span["indices"])
                    annotation.update(role=role, quantity=quantity)
                    if role == "none" or role in entities or CONCEPTS[concept]["kind"] not in ("entity", "place"):
                        raise SemanticError("Invalid or duplicate entity role")
                    entities[role] = {"concept": concept, "quantity": None if quantity == "unspecified" else int(quantity), "name": text[start:end] if concept == "ag" else None}
            diag["spans"].append(annotation)
        if predicate is None:
            raise SemanticError("Missing predicate")
        polarity, time = choose("polarity"), choose("time")
        graph = make_graph(predicate, entities, polarity, time)
        diag["confidence"] = min(confidences)
        if diag["confidence"] < threshold:
            diag["reason"] = "low_confidence"
        else:
            result["status"], result["graph"] = "confirmed", graph
    except SemanticError as exc:
        diag["confidence"] = min(confidences)
        diag["reason"] = "inconsistent_structure: " + str(exc)
    return result
