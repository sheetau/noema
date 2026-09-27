"""Label-independent compatibility heads over frozen multilingual features.

Research only: oracle spans, no calibrated acceptance or structure extraction.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import time

import torch
from torch import nn
from safetensors.torch import save_file

from .bem_probe import summarize
from .definition_probe import (DefinitionIndex, definitions, digest, normalized,
                               rows_from_fixture, save, span_vector)
from .encoder import FrozenEncoder, deterministic
from .semantics import CONCEPTS, require

DEV_IDS = frozenset(("ae", "bc", "ah"))
TRAIN_IDS = frozenset(CONCEPTS) - DEV_IDS
SETTINGS = {"seed": 17, "epochs": 20, "batch_size": 128, "learning_rate": .002,
            "weight_decay": .001, "temperature_multiplier": 10., "rank": 32,
            "residual_bound": .25, "train_per_language_concept": 128, "dev_per_language_concept": 48}


def row_key(row):
    return row["language"], row["text"], row["start"], row["end"]


def sample_key(row):
    text = json.dumps([17, *row_key(row)], ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest(), row["id"]


def select_rows(corpus, train_cap=128, dev_cap=48, train_ids=TRAIN_IDS, dev_ids=DEV_IDS):
    """Hold out whole sentences containing any development concept."""
    require(train_ids and dev_ids and not set(train_ids) & set(dev_ids), "Concept splits must be disjoint")
    require(type(train_cap) is int and type(dev_cap) is int and min(train_cap, dev_cap) > 0, "Invalid sample cap")
    candidates = {"train": {}, "dev": {}}
    for row in corpus:
        split = row.get("split")
        if split not in candidates or row.get("supported") is not True:
            continue
        concepts = {s.get("concept") for s in row["spans"]} | {n.get("concept") for n in row.get("graph", {}).get("nodes", [])}
        if split == "train" and concepts & set(dev_ids):
            continue
        allowed = train_ids if split == "train" else dev_ids
        require(row["language"] in ("ja", "en"), "Unexpected corpus language")
        for span in row["spans"]:
            if span.get("kind") not in ("entity", "predicate") or span.get("concept") not in allowed:
                continue
            a, b = span["start"], span["end"]
            require(0 <= a < b <= len(row["text"]), "Invalid training span")
            query = {"id": f"{row['id']}:{a}:{b}", "source_id": row["id"], "split": split,
                     "language": row["language"], "text": row["text"], "start": a, "end": b,
                     "span": row["text"][a:b], "expected": span["concept"],
                     "sentence_concepts": sorted(c for c in concepts if c in CONCEPTS)}
            key = row_key(query)
            prior = candidates[split].get(key)
            require(prior is None or prior["expected"] == query["expected"], "Conflicting span annotations")
            if prior is None or query["id"] < prior["id"]:
                candidates[split][key] = query
    selected = {}
    for split, ids, cap in (("train", train_ids, train_cap), ("dev", dev_ids, dev_cap)):
        pool = list(candidates[split].values())
        if split == "dev":
            train_texts = {r["text"] for r in selected["train"]}
            pool = [r for r in pool if r["text"] not in train_texts]
        result = []
        for language in ("ja", "en"):
            for concept in sorted(ids):
                group = sorted((r for r in pool if r["language"] == language and r["expected"] == concept), key=sample_key)
                require(len(group) >= cap, f"Insufficient {split} examples for {language}:{concept}")
                result.extend(group[:cap])
        selected[split] = result
    return selected


class CompatibilityHead(nn.Module):
    """No concept IDs or candidate-count-dependent parameters."""
    def __init__(self, dimension, rank=32):
        super().__init__()
        require(type(dimension) is int and dimension > 0 and type(rank) is int and rank >= 0, "Invalid head shape")
        self.dimension, self.rank = dimension, rank
        self.cosine_weights = nn.Parameter(torch.tensor([1., 0., 0.]))
        if rank:
            self.query_projection = nn.Linear(3 * dimension, rank, bias=False)
            self.definition_projection = nn.Linear(dimension, rank, bias=False)
            nn.init.zeros_(self.definition_projection.weight)

    def forward(self, query, definitions):
        require(query.ndim == 3 and query.shape[1:] == (3, self.dimension), "Invalid query shape")
        require(definitions.ndim == 2 and definitions.shape[1] == self.dimension and len(definitions) > 0,
                "Invalid definition shape")
        score = (torch.einsum("bkd,cd->bkc", query, definitions) * self.cosine_weights[None, :, None]).sum(1)
        if self.rank:
            residual = self.query_projection(query.flatten(1)) @ self.definition_projection(definitions).T
            score = score + SETTINGS["residual_bound"] * torch.tanh(residual / math.sqrt(self.rank))
        return score


def query_features(encoder, rows):
    texts = list(dict.fromkeys([r["text"] for r in rows] + [r["span"] for r in rows]))
    features = dict(zip(texts, encoder.encode(texts)))
    require(all(not f["truncated"] for f in features.values()), "Truncated input")
    vectors = []
    for row in rows:
        require(0 <= row["start"] < row["end"] <= len(row["text"]), "Invalid query span")
        require(row["text"][row["start"]:row["end"]] == row["span"], "Span text mismatch")
        full = features[row["text"]]
        vectors.append(normalized(torch.stack([span_vector(full, row["start"], row["end"]),
                                               features[row["span"]]["pooled"], full["pooled"]])))
    return torch.stack(vectors)


def dev_accuracy(head, queries, bank, rows, ids):
    with torch.inference_mode():
        predictions = head(queries, bank).argmax(1).tolist()
    by_language = {}
    for language in ("ja", "en"):
        pairs = [(p, r) for p, r in zip(predictions, rows) if r["language"] == language]
        require(pairs, "Missing development language")
        by_language[language] = sum(ids[p] == r["expected"] for p, r in pairs) / len(pairs)
    return {**by_language, "macro": sum(by_language.values()) / 2}


def fit(train, dev, train_bank, dev_bank, train_rows, dev_rows, train_ids, dev_ids, rank):
    deterministic(SETTINGS["seed"])
    head = CompatibilityHead(train.shape[-1], rank=rank)
    labels = torch.tensor([train_ids.index(r["expected"]) for r in train_rows])
    optimizer = torch.optim.AdamW(head.parameters(), lr=SETTINGS["learning_rate"], weight_decay=SETTINGS["weight_decay"])
    history = [{"epoch": 0, "training_loss": None, "dev": dev_accuracy(head, dev, dev_bank, dev_rows, dev_ids)}]
    best_accuracy, best_epoch = history[0]["dev"]["macro"], 0
    best_state = {k: v.detach().clone() for k, v in head.state_dict().items()}
    generator = torch.Generator().manual_seed(SETTINGS["seed"])
    for epoch in range(1, SETTINGS["epochs"] + 1):
        head.train()
        total_loss = 0.
        order = torch.randperm(len(train), generator=generator)
        for offset in range(0, len(order), SETTINGS["batch_size"]):
            selected = order[offset:offset + SETTINGS["batch_size"]]
            scores = head(train[selected], train_bank)
            loss = nn.functional.cross_entropy(scores * SETTINGS["temperature_multiplier"], labels[selected])
            require(bool(torch.isfinite(loss)), "Non-finite training loss")
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            total_loss += loss.item() * len(selected)
        head.eval()
        accuracy = dev_accuracy(head, dev, dev_bank, dev_rows, dev_ids)
        history.append({"epoch": epoch, "training_loss": total_loss / len(train), "dev": accuracy})
        if accuracy["macro"] > best_accuracy:
            best_accuracy, best_epoch = accuracy["macro"], epoch
            best_state = {k: v.detach().clone() for k, v in head.state_dict().items()}
    head.load_state_dict(best_state, strict=True)
    head.eval().requires_grad_(False)
    return head, {"selected_epoch": best_epoch, "history": history,
                  "parameters": sum(p.numel() for p in head.parameters()),
                  "cosine_weights": head.cosine_weights.tolist()}


def predict(scores, rows, ids):
    require(scores.shape == (len(rows), len(ids)), "Prediction shape mismatch")
    require(bool(torch.isfinite(scores).all()), "Non-finite scores")
    return [{**row, "top": [{"concept": concept, "score": score} for concept, score in
                            sorted(zip(ids, vector), key=lambda x: (-x[1], x[0]))[:3]]}
            for row, vector in zip(rows, scores.tolist())]


def run(corpus_path, output):
    output = Path(output)
    require(not output.exists(), "Choose a new output directory")
    require(Path(corpus_path).is_file(), "Training corpus not found")
    started = time.monotonic()
    with Path(corpus_path).open(encoding="utf-8") as source:
        selected = select_rows((json.loads(line) for line in source if line.strip()))
    bank = definitions()
    output.mkdir(parents=True)
    save(output / "selection.json", selected)
    save(output / "definitions.json", bank)
    sources = [__file__, "noema/definition_probe.py", "noema/bem_probe.py", "noema/encoder.py",
               "noema/resources/models.json", "docs/shared-matcher-protocol.md"]
    fixtures = {key: Path(f"data/definition-probe-{key}.json") for key in ("v1", "v2", "v3")}
    provenance = {"status": "running", "started_at": datetime.now(timezone.utc).isoformat(),
                  "settings": SETTINGS, "corpus_sha256": digest(corpus_path),
                  "source_sha256": {str(p): digest(p) for p in sources},
                  "fixture_sha256": {key: digest(p) for key, p in fixtures.items()},
                  "selection_sha256": digest(output / "selection.json"),
                  "definitions_sha256": digest(output / "definitions.json"),
                  "train_concepts": sorted(TRAIN_IDS), "dev_concepts": sorted(DEV_IDS),
                  "selection_counts": {key: dict(Counter(r["language"] + ":" + r["expected"] for r in rows)) for key, rows in selected.items()},
                  "interpretation": "oracle-span concept selection, not full semantic structure or calibrated rejection"}
    save(output / "run.json", provenance)
    encoder = FrozenEncoder("minilm", offline=True)
    require(not any(p.requires_grad for p in encoder.model.parameters()), "Unfrozen encoder")
    require(not any(m.training for m in encoder.model.modules()), "Encoder in training mode")
    index = DefinitionIndex(encoder, bank)
    queries = {}
    for split, rows in selected.items():
        queries[split] = query_features(encoder, rows)
        print(json.dumps({"features": split, "rows": len(rows), "seconds": time.monotonic() - started}), flush=True)
    train_ids, dev_ids = sorted(TRAIN_IDS), sorted(CONCEPTS)
    train_bank = index.vectors[[index.ids.index(k) for k in train_ids]]
    dev_bank = index.vectors[[index.ids.index(k) for k in dev_ids]]
    save_file({**queries, "definitions": index.vectors}, str(output / "features.safetensors"))
    heads = {}
    for key, rank in (("linear", 0), ("bilinear", SETTINGS["rank"])):
        head, history = fit(queries["train"], queries["dev"], train_bank, dev_bank,
                            selected["train"], selected["dev"], train_ids, dev_ids, rank)
        heads[key] = head
        save_file(head.state_dict(), str(output / f"{key}.safetensors"))
        save(output / f"{key}-training.json", {**history, "weights_sha256": digest(output / f"{key}.safetensors")})
        print(json.dumps({"head": key, "selected_epoch": history["selected_epoch"], "dev": history["history"][history["selected_epoch"]]["dev"]}), flush=True)
    # Confirmation inputs are read only after both heads have been selected.
    for fixture, path in fixtures.items():
        rows = rows_from_fixture(json.loads(path.read_text(encoding="utf-8")), set(index.ids))
        features = query_features(encoder, rows)
        with torch.inference_mode():
            scores = {key: head(features, index.vectors) for key, head in heads.items()}
            scores.update({key: features[:, n] @ index.vectors.T for n, key in enumerate(("contextual", "isolated", "sentence"))})
        for key, values in scores.items():
            predictions = predict(values, rows, index.ids)
            save(output / f"{key}-{fixture}-predictions.json", predictions)
            report = {"score": "shared compatibility" if key in heads else "cosine", "metrics": summarize(predictions)}
            save(output / f"{key}-{fixture}-report.json", report)
            print(json.dumps({"method": key, "fixture": fixture, "supported": {lang: report["metrics"][lang]["supported"] for lang in ("ja", "en")}}), flush=True)
    # Recompute a fixed batch, without changing model selection or hyperparameters.
    texts = [r["text"] for r in selected["dev"][:16]]
    first, second = encoder.encode(texts), encoder.encode(texts)
    repeated = all(torch.equal(a["tokens"], b["tokens"]) for a, b in zip(first, second))
    require(repeated, "Repeated encoder features differ")
    save(output / "run.json", {**provenance, "status": "complete", "model": encoder.metadata,
                               "features_sha256": digest(output / "features.safetensors"), "repeat_count": 16,
                               "repeat_tokens_exact": repeated, "seconds": time.monotonic() - started,
                               "finished_at": datetime.now(timezone.utc).isoformat()})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", default="artifacts/corpus-v9.jsonl")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    run(args.corpus, args.output)


if __name__ == "__main__":
    main()
