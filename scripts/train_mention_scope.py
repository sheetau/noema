"""Fit mention boundaries and shared roles before reading held-out source text."""
import argparse
from contextlib import contextmanager, ExitStack
import json
import logging
import os
from pathlib import Path
from unittest.mock import patch

import torch
from torch.nn import functional as F
from safetensors.torch import save_file

from noema.definition_probe import digest
from noema.encoder import deterministic
from noema.japanese_pas import JapanesePAS
from noema.mention_scope import (TAGS, MentionHead, mention_targets, infer_mentions,
                                 mention_candidates, scope_targets, assess_scope, role_outputs)
from noema.role_transfer import LABELS, UNLINKED
from scripts.train_role_transfer import fit as fit_role, supervised, validate_rows

DATA = ("data/role-transfer-v1.json", "data/role-candidates-v2.json", "data/mention-scope-v1.json")
SPLITS = ("train", "dev", "test", "confirmation", "mention_confirmation")
ARCHITECTURES = (("linear", 0), ("mlp", 64))


@contextmanager
def forbidden_paths():
    os.environ["KWJA_CLI_MODE"] = "1"
    logging.disable(logging.WARNING)
    from transformers.generation.utils import GenerationMixin
    from kwja.utils.jumandic import JumanDic
    from kwja.callbacks.word_module_writer import WordModuleWriter
    from kwja.modules import Seq2SeqModule, TypoModule
    with ExitStack() as stack:
        guards = [stack.enter_context(patch.object(cls, method, side_effect=AssertionError("Forbidden generation/dictionary path")))
                  for cls, method in ((GenerationMixin, "generate"), (JumanDic, "__init__"),
                                      (WordModuleWriter, "__init__"), (Seq2SeqModule, "__init__"), (TypoModule, "__init__"))]
        yield guards


def extract(model, rows):
    examples = []
    for row in rows:
        prediction, vectors = model.analyze(row["text"], return_features=True)
        try:
            tags = mention_targets(row, prediction["tokens"])
        except ValueError as error:
            # Never round or silently drop annotation boundaries.
            raise ValueError(f"{row['id']}: {error}; tokens={prediction['tokens']}") from error
        examples.append({"row": row, "prediction": prediction, "vectors": vectors, "tags": tags})
        print("word features", row["id"], flush=True)
    return examples


def fit_mentions(examples, dimension, hidden):
    deterministic()
    head = MentionHead(dimension, hidden)
    optimizer = torch.optim.AdamW(head.parameters(), lr=.003, weight_decay=.01)
    def batch(split):
        selected = [e for e in examples if e["row"]["split"] == split]
        return torch.cat([e["vectors"] for e in selected]), torch.cat([e["tags"] for e in selected])
    tx, ty = batch("train")
    dx, dy = batch("dev")
    best, history = None, []
    for epoch in range(1, 201):
        optimizer.zero_grad()
        loss = F.cross_entropy(head(tx), ty)
        loss.backward()
        optimizer.step()
        with torch.no_grad():
            dev_loss = float(F.cross_entropy(head(dx), dy))
        history.append({"epoch": epoch, "train_loss": float(loss.detach()), "dev_loss": dev_loss})
        if best is None or dev_loss < best["dev_loss"]:
            best = {"epoch": epoch, "dev_loss": dev_loss,
                    "state": {key: value.detach().clone() for key, value in head.state_dict().items()}}
    head.load_state_dict(best["state"])
    return head.eval(), {"epoch": best["epoch"], "dev_loss": best["dev_loss"], "hidden": hidden}, history


def add_candidates(examples, head, cases):
    for example in examples:
        mentions = infer_mentions(example["prediction"], example["vectors"], head)
        pairs, features = mention_candidates(example["prediction"], example["vectors"], mentions, cases)
        example.update(mentions=mentions, pairs=pairs, features=features,
                       targets=scope_targets(example["row"], example["prediction"], mentions, pairs))


def evaluate(examples, head):
    checks = []
    for example in examples:
        indices, outputs = role_outputs(example["pairs"], example["features"], head)
        check = assess_scope(example["row"], example["prediction"], example["mentions"], example["pairs"], indices)
        check.update(mentions=example["mentions"], outputs=outputs)
        checks.append(check)
    totals = {key: sum(c[key] for c in checks) for key in (
        "gold_mentions", "predicted_mentions", "exact_mentions", "gold_roles", "predicted_roles", "exact_roles",
        "extra_roles", "missing_roles", "annotated_frame_exact")}
    for unit in ("mentions", "roles"):
        for metric, denominator in (("precision", "predicted_"), ("recall", "gold_")):
            count = totals[denominator + unit]
            totals[unit + "_" + metric] = totals["exact_" + unit] / count if count else None
    totals["documents"] = len(checks)
    return {"summary": totals, "cases": checks}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="reports/mention-scope-v1")
    parser.add_argument("--artifacts", default="artifacts/mention-scope-v1")
    args = parser.parse_args()
    out, artifacts = Path(args.output), Path(args.artifacts)
    if out.exists() or artifacts.exists():
        raise ValueError("Refusing to overwrite a mention experiment")
    out.mkdir(parents=True)
    artifacts.mkdir(parents=True)
    def save(name, value):
        (out / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    rows = [row for path in DATA for row in json.loads(Path(path).read_text(encoding="utf-8"))]
    validate_rows(rows)
    families = {split: {r["family"] for r in rows if r["split"] == split} for split in SPLITS}
    assert all(not (families[a] & families[b]) for i, a in enumerate(SPLITS) for b in SPLITS[i + 1:])
    with forbidden_paths() as guards:
        model = JapanesePAS()
        dimension = model.models["word"].encoder.config.hidden_size
        cases = list(model.configs["word"].pas_cases) + [UNLINKED]
        examples = extract(model, [r for r in rows if r["split"] in ("train", "dev")])
        selections, mention_heads, role_heads = {}, {}, {}
        for stage, heads in (("mention", mention_heads), ("role", role_heads)):
            choices = {}
            for name, hidden in ARCHITECTURES:
                if stage == "mention":
                    head, choice, history = fit_mentions(examples, dimension, hidden)
                else:
                    head, choice, history = fit_role(examples, dimension, cases, hidden)
                heads[name], choices[name] = head, choice
                save_file(head.state_dict(), str(artifacts / f"{stage}-{name}.safetensors"))
                save(f"{stage}-{name}-history.json", history)
            chosen = min(choices, key=lambda name: choices[name]["dev_loss"])
            selections[stage] = {"selected": chosen, "choices": choices, "weights_sha256": {
                name: digest(artifacts / f"{stage}-{name}.safetensors") for name in heads}}
            save(stage + "-selection.json", selections[stage])
            if stage == "mention":
                add_candidates(examples, heads[chosen], cases)
        selection = {**selections, "dimension": dimension, "cases": cases, "tags": TAGS, "labels": LABELS,
                     "candidate_policy": "learned_mentions"}
        save("selection.json", selection)
        # Epochs and both architectures are persisted before held-out inference.
        held_out = extract(model, [r for r in rows if r["split"] not in ("train", "dev")])
        add_candidates(held_out, mention_heads[selections["mention"]["selected"]], cases)
        examples.extend(held_out)
        save_file({"tokens/" + e["row"]["id"]: e["vectors"] for e in examples} |
                  {"roles/" + e["row"]["id"]: e["features"] for e in examples}, str(artifacts / "features.safetensors"))
        save("evidence.json", [{key: e[key] for key in ("row", "prediction", "mentions", "pairs")} |
                               {"targets": e["targets"].tolist(), "tags": e["tags"].tolist()} for e in examples])
        results = {name: {split: evaluate([e for e in examples if e["row"]["split"] == split], head)
                          for split in SPLITS} for name, head in role_heads.items()}
        save("evaluation.json", results)
        save("run.json", {"encoder": model.metadata, "fixtures_sha256": {path: digest(path) for path in DATA},
            "code_sha256": {path: digest(path) for path in ("noema/mention_scope.py", "noema/role_transfer.py",
                "scripts/train_mention_scope.py", "scripts/train_role_transfer.py", "noema/japanese_pas.py")},
            "features_sha256": digest(artifacts / "features.safetensors"), "forbidden_path_calls": [g.call_count for g in guards],
            "role_label_counts": {split: torch.bincount(supervised(examples, split)[1], minlength=len(LABELS)).tolist()
                                  for split in SPLITS}})
        print(json.dumps({"selection": selection, "summaries": {name: {split: value["summary"] for split, value in result.items()}
                                                                 for name, result in results.items()}}, indent=2))


if __name__ == "__main__":
    main()
