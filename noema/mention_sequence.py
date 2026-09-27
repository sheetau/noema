"""Non-generative BIO sequence classification over frozen token vectors."""
import json
from pathlib import Path

import torch
from torch import nn
from safetensors.torch import load_file

from .definition_probe import digest
from .mention_scope import TAGS, MentionHead, role_outputs
from .role_context import ContextRoleHead, context_candidates
from .role_transfer import LABELS
from .semantics import require
from .srl_spans import bio_potentials, spans_from_tags


class BIOChain(nn.Module):
    def __init__(self):
        super().__init__()
        transitions, starts = bio_potentials(TAGS)
        self.register_buffer("legal_transitions", transitions)
        self.register_buffer("legal_starts", starts)
        self.transitions = nn.Parameter(torch.zeros(len(TAGS), len(TAGS)))
        self.starts = nn.Parameter(torch.zeros(len(TAGS)))
        self.ends = nn.Parameter(torch.zeros(len(TAGS)))

    def partition(self, emissions, lengths):
        require(emissions.ndim == 3 and emissions.shape[0] > 0 and emissions.shape[1] > 0
                and emissions.shape[2] == len(TAGS), "Invalid sequence emissions")
        require(lengths.dtype == torch.long and lengths.shape == emissions.shape[:1]
                and bool(((lengths > 0) & (lengths <= emissions.shape[1])).all()), "Invalid sequence lengths")
        require(bool(torch.isfinite(emissions).all()), "Non-finite sequence emissions")
        scores = emissions[:, 0] + self.starts + self.legal_starts
        transition = self.transitions + self.legal_transitions
        for position in range(1, emissions.shape[1]):
            updated = torch.logsumexp(scores[:, :, None] + transition, dim=1) + emissions[:, position]
            scores = torch.where((position < lengths)[:, None], updated, scores)
        return torch.logsumexp(scores + self.ends, dim=-1)

    def nll(self, emissions, tags, lengths):
        normalizer = self.partition(emissions, lengths)
        require(tags.dtype == torch.long and tags.shape == emissions.shape[:2]
                and bool(((tags >= 0) & (tags < len(TAGS))).all()), "Invalid sequence targets")
        active = torch.arange(emissions.shape[1], device=emissions.device)[None, :] < lengths[:, None]
        require(bool((tags[:, 0] != 2).all()) and not bool(((tags[:, :-1] == 0) & (tags[:, 1:] == 2) & active[:, 1:]).any()),
                "Invalid gold BIO sequence")
        scores = emissions.gather(-1, tags[..., None]).squeeze(-1)
        transition = self.transitions + self.legal_transitions
        steps = scores[:, 1:] + transition[tags[:, :-1], tags[:, 1:]]
        gold = scores[:, 0] + self.starts[tags[:, 0]] + self.legal_starts[tags[:, 0]]
        gold = gold + torch.where(active[:, 1:], steps, torch.zeros_like(steps)).sum(-1)
        final = tags[torch.arange(len(tags), device=tags.device), lengths - 1]
        gold = gold + self.ends[final]
        return normalizer - gold

    def decode(self, emissions):
        require(emissions.ndim == 2 and emissions.shape[1] == len(TAGS)
                and bool(torch.isfinite(emissions).all()), "Invalid decode emissions")
        if not len(emissions):
            return []
        scores = emissions[0] + self.starts + self.legal_starts
        transition = self.transitions + self.legal_transitions
        back = []
        for emission in emissions[1:]:
            scores, previous = (scores[:, None] + transition).max(dim=0)
            scores = scores + emission
            back.append(previous)
        path = [int((scores + self.ends).argmax())]
        for previous in reversed(back):
            path.append(int(previous[path[-1]]))
        return list(reversed(path))


class SequenceMentionHead(nn.Module):
    def __init__(self, dimension, hidden=0):
        super().__init__()
        self.dimension, self.hidden = dimension, hidden
        self.emitter = MentionHead(dimension, hidden)
        self.chain = BIOChain()

    def forward(self, vectors):
        return self.emitter(vectors)

    def loss(self, vectors, tags, lengths):
        emissions = self(vectors.reshape(-1, self.dimension)).reshape(*tags.shape, len(TAGS))
        return self.chain.nll(emissions, tags, lengths).sum() / lengths.sum()


def infer_sequence_mentions(prediction, vectors, head):
    require(len(prediction["tokens"]) == len(vectors), "Sequence source vectors differ")
    with torch.inference_mode():
        tags = head.chain.decode(head(vectors))
    spans = spans_from_tags([TAGS[t] for t in tags], prediction["tokens"], prediction["text"])
    return [{"id": i, "start": span["start"], "end": span["end"], "text": span["text"]} for i, span in enumerate(spans)]


class SequenceRoleAnalyzer:
    def __init__(self, report="reports/mention-sequence-v4", artifacts="artifacts/mention-sequence-v4"):
        from .japanese_pas import JapanesePAS
        selection = json.loads((Path(report) / "selection.json").read_text(encoding="utf-8"))
        require(selection["tags"] == list(TAGS) and selection["labels"] == list(LABELS), "Sequence checkpoint inventory differs")
        require(selection["candidate_policy"] == "learned_bio_chain", "Unknown sequence candidate policy")
        heads = {}
        for stage in ("mention", "role"):
            name = selection[stage]["selected"]
            path = Path(artifacts) / f"{stage}-{name}.safetensors"
            require(digest(path) == selection[stage]["weights_sha256"][name], "Sequence checkpoint hash differs")
            choice = selection[stage]["choices"][name]
            head = SequenceMentionHead(selection["dimension"], choice["hidden"]) if stage == "mention" else ContextRoleHead(
                selection["dimension"], selection["cases"], choice["hidden"], "boundary")
            head.load_state_dict(load_file(str(path)), strict=True)
            heads[stage] = head.eval().requires_grad_(False)
        self.mention_head, self.role_head = heads["mention"], heads["role"]
        self.parser = JapanesePAS()

    def analyze(self, text):
        prediction, vectors = self.parser.analyze(text, return_features=True)
        mentions = infer_sequence_mentions(prediction, vectors, self.mention_head)
        pairs, features = context_candidates(prediction, vectors, mentions, self.role_head.cases)
        _, roles = role_outputs(pairs, features, self.role_head)
        return {"status": "research_sequence_role_candidates", "analysis": prediction, "mentions": mentions, "roles": roles}
