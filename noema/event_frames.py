"""Predicate-conditioned overlapping argument scopes from frozen source states."""
import json
from pathlib import Path

import torch
from torch.nn import functional as F
from safetensors.torch import load_file

from .definition_probe import digest
from .mention_scope import TAGS, mention_targets, scope_targets, role_outputs
from .mention_sequence import SequenceMentionHead, infer_sequence_mentions
from .role_context import ContextRoleHead, context_candidates
from .role_transfer import LABELS, anchor, overlap
from .semantics import require


def predicate_candidates(prediction):
    return [p for p in prediction["phrases"] if "用言" in p["features"] or "非用言格解析" in p["features"]]


def conditioned_vectors(prediction, vectors, source):
    require(len(vectors) == len(prediction["tokens"]), "Frame source vectors differ")
    def pool(span):
        indices = [i for i, token in enumerate(prediction["tokens"]) if overlap(token, span)]
        require(bool(indices), "Predicate has no source vectors")
        return F.normalize(vectors[indices].mean(0), dim=0).expand(len(vectors), -1)
    words = F.normalize(vectors, dim=-1)
    predicate, phrase = pool(source["head"]), pool(source)
    return torch.cat((words, predicate, phrase, words * predicate, words - predicate), dim=-1)


def scoped_candidates(prediction, vectors, source, mentions, cases):
    pairs, features = context_candidates(prediction, vectors, mentions, cases)
    indices = [i for i, pair in enumerate(pairs) if pair["source"] == source["id"]]
    return [pairs[i] for i in indices], features[indices]


def matching_frame(document, source):
    matches = [i for i, frame in enumerate(document["frames"]) if overlap(source["head"], anchor(document["text"], frame["predicate"]))]
    require(len(matches) <= 1, "One predicted predicate overlaps multiple gold frames")
    return matches[0] if matches else None


def supervised_frames(documents):
    examples = []
    for document in documents:
        row, prediction = document["document"], document["prediction"]
        for source in predicate_candidates(prediction):
            index = matching_frame(row, source)
            if index is None:
                continue  # Unannotated events are not negative examples.
            frame = row["frames"][index]
            legacy = {**frame, "id": f"{row['id']}/{index}/{source['id']}", "split": row["split"], "text": row["text"]}
            examples.append({"row": legacy, "document_id": row["id"], "source": source, "prediction": prediction,
                             "raw_vectors": document["vectors"], "vectors": conditioned_vectors(prediction, document["vectors"], source),
                             "tags": mention_targets(legacy, prediction["tokens"])})
    return examples


def add_frame_candidates(examples, head, cases):
    for example in examples:
        mentions = infer_sequence_mentions(example["prediction"], example["vectors"], head)
        pairs, features = scoped_candidates(example["prediction"], example["raw_vectors"], example["source"], mentions, cases)
        example.update(mentions=mentions, pairs=pairs, features=features,
                       targets=scope_targets(example["row"], example["prediction"], mentions, pairs))


def predict_frames(prediction, vectors, mention_head, role_head):
    frames = []
    for source in predicate_candidates(prediction):
        mentions = infer_sequence_mentions(prediction, conditioned_vectors(prediction, vectors, source), mention_head)
        pairs, features = scoped_candidates(prediction, vectors, source, mentions, role_head.cases)
        _, roles = role_outputs(pairs, features, role_head)
        frames.append({"source": source["id"], "predicate": source["head"], "mentions": mentions, "roles": roles})
    return frames


def assess_document(document, prediction, frames):
    gold_spans, gold_roles = set(), set()
    for index, frame in enumerate(document["frames"]):
        for role, text in frame["roles"]:
            span = anchor(document["text"], text)
            gold_spans.add((index, span["start"], span["end"]))
            gold_roles.add((index, role, span["start"], span["end"]))
    phrases = {p["id"]: p for p in prediction["phrases"]}
    spans, roles, detected, unannotated = set(), [], set(), 0
    for frame in frames:
        key = matching_frame(document, phrases[frame["source"]])
        if key is None:
            unannotated += 1
            if not document["complete_frames"]:
                continue
            key = f"unmatched-{frame['source']}"
        else:
            detected.add(key)
        mentions = {m["id"]: m for m in frame["mentions"]}
        spans.update((key, m["start"], m["end"]) for m in mentions.values())
        for output in frame["roles"]:
            if output["role"] != "none":
                mention = mentions[output["target"]]
                roles.append((key, output["role"], mention["start"], mention["end"]))
    role_set = set(roles)
    duplicate = len(roles) - len(role_set)
    exact_frames = sum({r for r in gold_roles if r[0] == i} == {r for r in role_set if r[0] == i}
                       and i in detected and sum(r[0] == i for r in roles) == sum(r[0] == i for r in role_set)
                       for i in range(len(document["frames"])))
    return {"id": document["id"], "gold_frames": len(document["frames"]), "detected_frames": len(detected),
            "predicate_candidates": len(frames), "unannotated_predicate_candidates": unannotated,
            "gold_spans": len(gold_spans), "predicted_spans": len(spans), "exact_spans": len(gold_spans & spans),
            "gold_roles": len(gold_roles), "predicted_roles": len(roles), "exact_roles": len(gold_roles & role_set),
            "extra_roles": len(role_set - gold_roles) + duplicate, "missing_roles": len(gold_roles - role_set),
            "duplicate_roles": duplicate, "frames_exact": exact_frames,
            "document_exact": len(detected) == len(document["frames"]) and role_set == gold_roles and duplicate == 0}


class EventFrameAnalyzer:
    def __init__(self, report="reports/multi-frame-v5", artifacts="artifacts/multi-frame-v5"):
        from .japanese_pas import JapanesePAS
        selection = json.loads((Path(report) / "selection.json").read_text(encoding="utf-8"))
        require(selection["tags"] == list(TAGS) and selection["labels"] == list(LABELS), "Frame checkpoint inventory differs")
        require(selection["candidate_policy"] == "predicate_conditioned_bio", "Unknown frame candidate policy")
        heads = {}
        for stage in ("mention", "role"):
            name = selection[stage]["selected"]
            path = Path(artifacts) / f"{stage}-{name}.safetensors"
            require(digest(path) == selection[stage]["weights_sha256"][name], "Frame checkpoint hash differs")
            hidden = selection[stage]["choices"][name]["hidden"]
            head = SequenceMentionHead(5 * selection["dimension"], hidden) if stage == "mention" else ContextRoleHead(
                selection["dimension"], selection["cases"], hidden, "boundary")
            head.load_state_dict(load_file(str(path)), strict=True)
            heads[stage] = head.eval().requires_grad_(False)
        self.mention_head, self.role_head = heads["mention"], heads["role"]
        self.parser = JapanesePAS()

    def analyze(self, text):
        prediction, vectors = self.parser.analyze(text, return_features=True)
        return {"status": "research_event_frame_candidates", "analysis": prediction,
                "frames": predict_frames(prediction, vectors, self.mention_head, self.role_head)}
