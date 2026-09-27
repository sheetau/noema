"""Frozen BIO argument-span probe; no generation or lexical correction.

Compatible with LIAAD's srl-en_xlmr-base and the published linear classifier:
https://github.com/asofiaoliveira/srl_bert_pt
"""
import json
from pathlib import Path

import torch
from torch import nn

from .definition_probe import digest
from .encoder import deterministic
from .semantics import require, SemanticError

MODEL = "liaad/srl-en_xlmr-base"
REVISION = "55387c653aba11f0025a2f7089435c11c4c583f6"
SOURCE_REVISION = "634d145cdca1aa2dfb0cf66143e3a358ac6e56fd"


def bio_potentials(labels):
    """Only BIO structural restrictions; no role/word-specific constraints."""
    require(len(labels) == len(set(labels)) and "O" in labels, "Invalid BIO inventory")
    require(all(label == "O" or label.startswith(("B-", "I-")) and len(label) > 2 for label in labels), "Invalid BIO label")
    transitions = torch.zeros(len(labels), len(labels))
    start = torch.zeros(len(labels))
    for j, current in enumerate(labels):
        if current.startswith("I-"):
            start[j] = float("-inf")
            for i, previous in enumerate(labels):
                if previous not in (current, "B-" + current[2:]):
                    transitions[i, j] = float("-inf")
    return transitions, start


def decode_bio(probabilities, labels):
    """Max-sum probabilities, as in the published model (not log scores)."""
    require(probabilities.ndim == 2 and probabilities.shape[1] == len(labels) and probabilities.shape[0] > 0,
            "Invalid BIO score shape")
    require(bool(torch.isfinite(probabilities).all()), "Non-finite BIO scores")
    transitions, starts = bio_potentials(labels)
    scores = probabilities[0] + starts
    back = []
    for position in range(1, len(probabilities)):
        scores, indices = (scores[:, None] + transitions).max(dim=0)
        scores = scores + probabilities[position]
        back.append(indices)
    path = [int(scores.argmax())]
    for indices in reversed(back):
        path.append(int(indices[path[-1]]))
    return list(reversed(path))


def spans_from_tags(tags, tokens, text):
    require(len(tags) == len(tokens), "Tags and source tokens differ in length")
    spans = []
    active = None
    previous_end = -1
    for tag, token in zip(tags, tokens):
        begin, end = token["start"], token["end"]
        require(type(begin) is int and type(end) is int and previous_end <= begin < end <= len(text)
                and text[begin:end] == token["text"], "Invalid source offsets")
        previous_end = end
        if tag == "O":
            active = None
        elif tag.startswith("B-") and len(tag) > 2:
            active = {"label": tag[2:], "start": begin, "end": end}
            spans.append(active)
        elif tag.startswith("I-") and active is not None and active["label"] == tag[2:]:
            active["end"] = end
        else:
            raise SemanticError("Invalid word-level BIO sequence; no automatic repair")
    return [{**s, "text": text[s["start"]:s["end"]]} for s in spans]


class FrozenSpanSRL:
    def __init__(self, source="artifacts/span-srl-source"):
        import transformers
        from transformers import AutoModel, AutoTokenizer
        from huggingface_hub import hf_hub_download
        deterministic()
        source = Path(source)
        model_path = source / "Models/srl-en_xlmr-base"
        labels_path = model_path / "Vocabulary/labels.txt"
        self.labels = labels_path.read_text(encoding="utf-8").splitlines()
        bio_potentials(self.labels)
        options = {"revision": REVISION, "local_files_only": True, "trust_remote_code": False}
        self.tokenizer = AutoTokenizer.from_pretrained(MODEL, use_fast=False, **options)
        self.model = AutoModel.from_pretrained(MODEL, weights_only=True, attn_implementation="eager", **options).eval().requires_grad_(False)
        require(self.model.config.type_vocab_size == 2, "Model must encode predicate indicators")
        self.classifier = nn.Linear(self.model.config.hidden_size, len(self.labels))
        self.classifier.load_state_dict(torch.load(model_path / "linear_layer.pt", map_location="cpu", weights_only=True), strict=True)
        self.classifier.eval().requires_grad_(False)
        weights = hf_hub_download(MODEL, "pytorch_model.bin", revision=REVISION, local_files_only=True)
        self.metadata = {"model": MODEL, "revision": REVISION, "source_revision": SOURCE_REVISION,
                         "torch": str(torch.__version__), "transformers": transformers.__version__,
                         "device": "cpu", "dtype": "float32", "seed": 17, "decoder": "BIO max-sum probabilities",
                         "max_subwords": self.model.config.max_position_embeddings - self.model.config.pad_token_id - 1,
                         "weights_sha256": digest(weights), "labels_sha256": digest(labels_path),
                         "head_sha256": digest(model_path / "linear_layer.pt"),
                         "source_hashes": {name: digest(source / name) for name in ("my_reader.py", "my_model.py")}}

    def encode(self, words, predicate):
        require(type(predicate) is int and 0 <= predicate < len(words), "Predicate is outside sentence")
        pieces, starts, ends, indicator = [], [], [], [0]
        for i, word in enumerate(words):
            subwords = self.tokenizer._tokenize(word)  # Published reader uses this exact method.
            require(bool(subwords), "Empty subword encoding")
            starts.append(len(pieces) + 1)
            pieces.extend(subwords)
            ends.append(len(pieces))
            indicator.extend([int(i == predicate)] * len(subwords))
        ids = self.tokenizer.convert_tokens_to_ids([self.tokenizer.cls_token] + pieces + [self.tokenizer.sep_token])
        indicator.append(0)
        require(len(ids) <= self.metadata["max_subwords"], "Sentence exceeds span model context; no silent truncation")
        return {"input_ids": torch.tensor([ids]), "token_type_ids": torch.tensor([indicator]),
                "attention_mask": torch.ones(1, len(ids), dtype=torch.long)}, starts, ends

    def predict(self, text, tokens, predicate):
        encoded, starts, _ = self.encode([t["text"] for t in tokens], predicate)
        with torch.inference_mode():
            logits = self.classifier(self.model(**encoded).last_hidden_state)[0]
            indices = decode_bio(logits.softmax(-1), self.labels)
        subword_tags = [self.labels[i] for i in indices]
        tags = [subword_tags[i] for i in starts]
        result = {"predicate_token": predicate, "word_tags": tags, "subword_tags": subword_tags}
        try:
            result.update(status="valid_bio", spans=spans_from_tags(tags, tokens, text))
        except SemanticError as exc:
            result.update(status="invalid_bio", spans=None, diagnostic=str(exc))
        return result

    def annotate(self, dependency_prediction):
        text = dependency_prediction["text"]
        sentences = []
        for sentence in dependency_prediction["sentences"]:
            spans = [self.predict(text, sentence["tokens"], p["token"]) for p in sentence["inventories"]["EN"]]
            sentences.append({**sentence, "span_annotations": spans})
        return {**dependency_prediction, "status": "research_span_annotation", "sentences": sentences}
