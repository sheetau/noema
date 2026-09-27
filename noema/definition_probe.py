"""Untrained definition retrieval diagnostic, deliberately separate from Analyzer.

Oracle spans make this a concept-matching probe, not a semantic parser. Scores
are cosine similarities, never probabilities or a basis for confirmed output.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import gc
import hashlib
import json
from pathlib import Path
import time

from .encoder import FrozenEncoder
from .glossary import lexicon
from .semantics import CONCEPTS, require


def normalized(vector):
    import torch
    require(bool(torch.isfinite(vector).all()), "Non-finite embedding")
    norm = vector.norm(dim=-1, keepdim=True)
    require(bool((norm > 0).all()), "Zero embedding")
    return vector / norm


def span_vector(feature, start, end):
    require(not feature["truncated"], "Truncated input is not supported")
    require(0 <= start < end, "Invalid span")
    positions = [i for i, (a, b) in enumerate(feature["offsets"]) if a < b and a < end and b > start]
    require(positions, "The span has no tokens")
    return feature["tokens"][positions].mean(0)


class DefinitionIndex:
    """A replaceable vocabulary bank with no fitted parameters or label head."""
    def __init__(self, encoder, definitions):
        import torch
        require(definitions and len({d["id"] for d in definitions}) == len(definitions), "Invalid concept inventory")
        self.ids = sorted(d["id"] for d in definitions)
        by_id = {d["id"]: d for d in definitions}
        texts = [by_id[key][language] for key in self.ids for language in ("ja", "en")]
        require(all(isinstance(t, str) and t.strip() for t in texts), "Definitions must be nonempty")
        features = encoder.encode(texts)
        require(all(not f["truncated"] for f in features), "Truncated definition")
        vectors = normalized(torch.stack([f["pooled"] for f in features]))
        self.vectors = normalized(vectors.reshape(len(self.ids), 2, -1).mean(1))

    def rank(self, vector, limit=3):
        scores = self.vectors @ normalized(vector)
        ordered = sorted(zip(self.ids, scores.tolist()), key=lambda item: (-item[1], item[0]))
        return [{"concept": key, "cosine": score} for key, score in ordered[:limit]]


def definitions():
    return [{"id": w["id"], "kind": w["kind"], "en": w["definition"], "ja": w["definition_ja"]}
            for w in lexicon()["words"]]


def rows_from_fixture(fixture, inventory):
    require(fixture.get("version") == "definition-probe-v1", "Unknown fixture version")
    rows = []
    for pair in fixture["pairs"]:
        require(pair["concept"] is None or pair["concept"] in inventory, "Unknown gold concept")
        for language in ("ja", "en"):
            item = pair[language]
            require(isinstance(item, list) and len(item) in (2, 3), "Expected text, span and optional occurrence")
            text, span = item[:2]
            if len(item) == 2:
                require(span and text.count(span) == 1, "Oracle span must occur exactly once")
                start = text.index(span)
            else:
                occurrence = item[2]
                require(span and type(occurrence) is int and 0 <= occurrence < text.count(span), "Invalid span occurrence")
                start = -len(span)
                for _ in range(occurrence + 1):
                    start = text.index(span, start + len(span))
            rows.append({"id": pair["id"] + ":" + language, "pair": pair["id"], "language": language,
                         "text": text, "span": span, "start": start, "end": start + len(span),
                         "expected": pair["concept"],
                         "group": "unsupported" if pair["concept"] is None else "base" if pair["concept"] in CONCEPTS else "extension"})
    require(len({r["id"] for r in rows}) == len(rows), "Duplicate fixture ID")
    return rows


def distribution(values):
    return {"count": len(values), "min": min(values), "mean": sum(values) / len(values), "max": max(values)} if values else {"count": 0}


def metrics(predictions):
    result = {}
    for mode in ("isolated", "contextual_span", "sentence"):
        entries = [p for p in predictions if p["mode"] == mode]
        for language in ("ja", "en"):
            selected = [p for p in entries if p["language"] == language]
            counts = {}
            for group in ("base", "extension", "supported"):
                subset = [p for p in selected if p["group"] == group or group == "supported" and p["group"] != "unsupported"]
                count = len(subset)
                exact = sum(p["expected"] == p["top"][0]["concept"] for p in subset)
                top3 = sum(p["expected"] in [t["concept"] for t in p["top"]] for p in subset)
                counts[group] = {"count": count, "top1_correct": exact, "top1_accuracy": exact / count if count else None,
                                 "top3_correct": top3, "top3_accuracy": top3 / count if count else None}
            scores = {k: [] for k in ("known_correct", "known_wrong", "unsupported")}
            for p in selected:
                key = "unsupported" if p["expected"] is None else "known_correct" if p["expected"] == p["top"][0]["concept"] else "known_wrong"
                scores[key].append(p["top"][0]["cosine"])
            result[mode + ":" + language] = {**counts, "top1_cosine": {k: distribution(v) for k, v in scores.items()}}
        paired = {}
        for p in entries:
            if p["expected"] is not None:
                paired.setdefault(p["pair"], {})[p["language"]] = p
        result[mode + ":bilingual"] = {
            "pairs": len(paired),
            "same_candidate": sum(p["ja"]["top"][0]["concept"] == p["en"]["top"][0]["concept"] for p in paired.values()),
            "both_correct": sum(all(p[lang]["top"][0]["concept"] == p[lang]["expected"] for lang in ("ja", "en")) for p in paired.values()),
        }
    return result


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")


def run(fixture_path, output):
    import torch
    output = Path(output)
    require(not output.exists(), "Choose a new probe output directory")
    bank = definitions()
    rows = rows_from_fixture(json.loads(Path(fixture_path).read_text(encoding="utf-8")), {d["id"] for d in bank})
    output.mkdir(parents=True)
    save(output / "definitions.json", bank)
    root = Path(__file__).parent
    provenance = {"started_at": datetime.now(timezone.utc).isoformat(), "status": "running",
                  "interpretation": "exploratory oracle-span concept retrieval; no structure accuracy or calibrated rejection",
                  "fixture_sha256": digest(fixture_path), "definitions_sha256": digest(output / "definitions.json"),
                  "source_sha256": {name: digest(root / name) for name in ("definition_probe.py", "encoder.py", "resources/models.json")},
                  "fixture_counts": dict(Counter(r["language"] + ":" + r["group"] for r in rows))}
    save(output / "run.json", provenance)
    for key in ("xlmr", "minilm"):
        started = time.monotonic()
        encoder = FrozenEncoder(key, offline=True)
        require(not any(p.requires_grad for p in encoder.model.parameters()), "Encoder is not frozen")
        require(not any(m.training for m in encoder.model.modules()), "Encoder must be in evaluation mode")
        index = DefinitionIndex(encoder, bank)
        full = encoder.encode([r["text"] for r in rows])
        isolated = encoder.encode([r["span"] for r in rows])
        require(all(not f["truncated"] for f in full + isolated), "Truncated probe input")
        predictions = []
        for row, f, short in zip(rows, full, isolated):
            modes = {"isolated": short["pooled"], "contextual_span": span_vector(f, row["start"], row["end"]), "sentence": f["pooled"]}
            for mode, vector in modes.items():
                predictions.append({**row, "mode": mode, "top": index.rank(vector)})
        # Reproduce the original batch shape as well as row order for bitwise checks.
        repeated = encoder.encode([r["text"] for r in rows[:16]])
        repeat_equal = all(torch.equal(a["tokens"], b["tokens"]) for a, b in zip(full[:16], repeated))
        require(repeat_equal, "Repeated inference changed token vectors")
        report = {"model": encoder.metadata, "seconds": time.monotonic() - started,
                  "fitted_parameters": 0, "candidate_count": len(index.ids), "repeat_count": 16,
                  "repeat_tokens_exact": repeat_equal, "metrics": metrics(predictions)}
        save(output / (key + "-predictions.json"), predictions)
        save(output / (key + "-report.json"), report)
        print(json.dumps({"model": key, "seconds": report["seconds"], "metrics": report["metrics"]}), flush=True)
        del index, encoder, full, isolated, repeated
        gc.collect()
    save(output / "run.json", {**provenance, "status": "complete", "finished_at": datetime.now(timezone.utc).isoformat()})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", default="data/definition-probe-v1.json")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    run(args.fixture, args.output)


if __name__ == "__main__":
    main()
