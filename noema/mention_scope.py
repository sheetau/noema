"""Learn source mention boundaries independently of vocabulary and role labels."""
import torch
from torch import nn
from torch.nn import functional as F

from .role_transfer import LABELS, UNLINKED, RoleHead, anchor, overlap
from .semantics import require
from .srl_spans import decode_bio, spans_from_tags

TAGS = ("O", "B-mention", "I-mention")


class MentionHead(nn.Module):
    def __init__(self, dimension, hidden=0):
        super().__init__()
        self.dimension, self.hidden = dimension, hidden
        self.network = nn.Linear(dimension, len(TAGS)) if hidden == 0 else nn.Sequential(
            nn.Linear(dimension, hidden), nn.Tanh(), nn.Linear(hidden, len(TAGS)))

    def forward(self, vectors):
        require(vectors.ndim == 2 and vectors.shape[1] == self.dimension, "Invalid mention vectors")
        return self.network(F.normalize(vectors, dim=-1))


def gold_mentions(row):
    spans = [anchor(row["text"], text) for _, text in row["roles"]]
    spans.sort(key=lambda s: (s["start"], s["end"]))
    require(all(a["end"] <= b["start"] for a, b in zip(spans, spans[1:])), "Overlapping mention annotation")
    return spans


def mention_targets(row, tokens):
    tags = torch.zeros(len(tokens), dtype=torch.long)
    for span in gold_mentions(row):
        indices = [i for i, token in enumerate(tokens) if overlap(token, span)]
        require(bool(indices) and tokens[indices[0]]["start"] == span["start"]
                and tokens[indices[-1]]["end"] == span["end"], "Gold mention is not aligned to model tokens")
        tags[indices] = 2
        tags[indices[0]] = 1
    return tags


def decode_mentions(text, tokens, logits):
    require(len(tokens) == len(logits), "Mention logits do not align with tokens")
    if not tokens:
        return []
    # The BIO dynamic program maximizes a sum; here the scores are log probabilities.
    indices = decode_bio(logits.log_softmax(-1), TAGS)
    spans = spans_from_tags([TAGS[i] for i in indices], tokens, text)
    return [{"id": i, "start": s["start"], "end": s["end"], "text": s["text"]} for i, s in enumerate(spans)]


def mention_candidates(prediction, vectors, mentions, cases):
    require(cases[-1] == UNLINKED and len(vectors) == len(prediction["tokens"]), "Mention feature inventory differs")
    phrases = {p["id"]: p for p in prediction["phrases"]}
    def pool(span):
        indices = [i for i, token in enumerate(prediction["tokens"]) if overlap(token, span)]
        require(bool(indices), "Mention has no source vectors")
        return F.normalize(vectors[indices].mean(0), dim=0)
    pairs, features = [], []
    for source in prediction["phrases"]:
        if not ("用言" in source["features"] or "非用言格解析" in source["features"]):
            continue
        predicate, context = pool(source["head"]), pool(source)
        for mention in mentions:
            argument = pool(mention)
            linked = {r["label"] for r in source["relations"] if r["target_phrase"] is not None and
                      r["label"] in cases[:-1] and mention["start"] <= phrases[r["target_phrase"]]["head"]["start"]
                      and mention["end"] >= phrases[r["target_phrase"]]["head"]["end"]}
            case = vectors.new_zeros(len(cases))
            for label in linked or {UNLINKED}:
                case[cases.index(label)] = 1
            features.append(torch.cat((predicate, argument, context, predicate * argument, predicate - argument, case)))
            pairs.append({"source": source["id"], "target": mention["id"], "native_cases": [c for c in cases if c in linked]})
    return pairs, torch.stack(features) if features else vectors.new_empty((0, vectors.shape[1] * 5 + len(cases)))


def scope_targets(row, prediction, mentions, pairs):
    event = anchor(row["text"], row["predicate"])
    gold = {(s["start"], s["end"]): LABELS.index(role) for role, text in row["roles"]
            for s in [anchor(row["text"], text)]}
    phrases = {p["id"]: p for p in prediction["phrases"]}
    by_id = {m["id"]: m for m in mentions}
    return torch.tensor([-100 if not overlap(phrases[p["source"]]["head"], event) else
                         gold.get((by_id[p["target"]]["start"], by_id[p["target"]]["end"]), 0)
                         for p in pairs], dtype=torch.long)


def assess_scope(row, prediction, mentions, pairs, indices):
    phrases = {p["id"]: p for p in prediction["phrases"]}
    by_id = {m["id"]: m for m in mentions}
    event = anchor(row["text"], row["predicate"])
    gold_spans = {(s["start"], s["end"]) for s in gold_mentions(row)}
    actual_spans = {(m["start"], m["end"]) for m in mentions}
    gold_roles = {(role, s["start"], s["end"]) for role, text in row["roles"] for s in [anchor(row["text"], text)]}
    actual_roles = {(LABELS[label], by_id[pair["target"]]["start"], by_id[pair["target"]]["end"])
                    for pair, label in zip(pairs, indices, strict=True) if label != 0
                    and overlap(phrases[pair["source"]]["head"], event)}
    return {"id": row["id"], "split": row["split"], "gold_mentions": len(gold_spans), "predicted_mentions": len(actual_spans),
            "exact_mentions": len(gold_spans & actual_spans), "gold_roles": len(gold_roles),
            "predicted_roles": len(actual_roles), "exact_roles": len(gold_roles & actual_roles),
            "extra_roles": len(actual_roles - gold_roles), "missing_roles": len(gold_roles - actual_roles),
            "annotated_frame_exact": gold_roles == actual_roles}


def infer_mentions(prediction, vectors, head):
    with torch.inference_mode():
        return decode_mentions(prediction["text"], prediction["tokens"], head(vectors))


def role_outputs(pairs, features, head):
    with torch.inference_mode():
        probabilities = head(features).softmax(-1)
    indices = probabilities.argmax(-1).tolist()
    outputs = [{**pair, "role": LABELS[index], "confidence": float(probabilities[i, index])}
               for i, (pair, index) in enumerate(zip(pairs, indices, strict=True))]
    return indices, outputs


class MentionRoleAnalyzer:
    """Research-only source spans and roles, without corpus access at inference."""
    def __init__(self, report="reports/mention-scope-v1", artifacts="artifacts/mention-scope-v1"):
        import json
        from pathlib import Path
        from safetensors.torch import load_file
        from .definition_probe import digest
        from .japanese_pas import JapanesePAS
        selection = json.loads((Path(report) / "selection.json").read_text(encoding="utf-8"))
        require(selection["tags"] == list(TAGS) and selection["labels"] == list(LABELS), "Scope checkpoint labels differ")
        require(selection["candidate_policy"] == "learned_mentions", "Scope candidate policy differs")
        self.cases = tuple(selection["cases"])
        heads = {}
        for stage in ("mention", "role"):
            chosen = selection[stage]["selected"]
            path = Path(artifacts) / f"{stage}-{chosen}.safetensors"
            require(digest(path) == selection[stage]["weights_sha256"][chosen], "Scope checkpoint hash differs")
            hidden = selection[stage]["choices"][chosen]["hidden"]
            head = MentionHead(selection["dimension"], hidden) if stage == "mention" else RoleHead(selection["dimension"], self.cases, hidden)
            head.load_state_dict(load_file(str(path)), strict=True)
            heads[stage] = head.eval().requires_grad_(False)
        self.mention_head, self.role_head = heads["mention"], heads["role"]
        self.parser = JapanesePAS()

    def analyze(self, text):
        prediction, vectors = self.parser.analyze(text, return_features=True)
        mentions = infer_mentions(prediction, vectors, self.mention_head)
        pairs, features = mention_candidates(prediction, vectors, mentions, self.cases)
        _, outputs = role_outputs(pairs, features, self.role_head)
        return {"status": "research_mention_role_candidates", "analysis": prediction,
                "mentions": mentions, "roles": outputs}
