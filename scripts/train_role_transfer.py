"""Train shared role heads; freeze development selection before test inference."""
import argparse
from contextlib import ExitStack
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
from noema.role_transfer import LABELS, RoleHead, anchor, candidates, targets, assess

DATA = "data/role-transfer-v1.json"


def validate_rows(rows):
    assert len({r["id"] for r in rows}) == len(rows)
    groups = {split: {r["family"] for r in rows if r["split"] == split} for split in ("train", "dev", "test")}
    assert not (groups["train"] & groups["dev"] or groups["train"] & groups["test"] or groups["dev"] & groups["test"])
    for row in rows:
        anchor(row["text"], row["predicate"])
        assert len({role for role, _ in row["roles"]}) == len(row["roles"])
        for role, text in row["roles"]:
            assert role in LABELS[1:]
            anchor(row["text"], text)


def extract(model, rows, cases):
    extracted = []
    for row in rows:
        prediction, vectors = model.analyze(row["text"], return_features=True)
        pairs, features = candidates(prediction, vectors, cases)
        extracted.append({"row": row, "prediction": prediction, "pairs": pairs, "features": features,
                          "targets": targets(row, prediction, pairs)})
        print("features", row["id"], flush=True)
    return extracted


def supervised(examples, split):
    selected = [e for e in examples if e["row"]["split"] == split]
    x, y = torch.cat([e["features"] for e in selected]), torch.cat([e["targets"] for e in selected])
    return x[y != -100], y[y != -100]


def fit(examples, dimension, cases, hidden):
    deterministic()
    head = RoleHead(dimension, cases, hidden)
    optimizer = torch.optim.AdamW(head.parameters(), lr=.003, weight_decay=.01)
    tx, ty = supervised(examples, "train")
    dx, dy = supervised(examples, "dev")
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
                    "state": {k: v.detach().clone() for k, v in head.state_dict().items()}}
    head.load_state_dict(best["state"])
    return head.eval(), {"epoch": best["epoch"], "dev_loss": best["dev_loss"], "hidden": hidden}, history


def evaluate(examples, head):
    cases, correct, total = [], 0, 0
    for example in examples:
        with torch.no_grad():
            probabilities = head(example["features"]).softmax(-1)
        selected = probabilities.argmax(-1)
        mask = example["targets"] != -100
        correct += int((selected[mask] == example["targets"][mask]).sum())
        total += int(mask.sum())
        check = assess(example["row"], example["prediction"], example["pairs"], selected.tolist())
        check["outputs"] = [{**pair, "role": LABELS[int(index)], "confidence": float(probabilities[i, index])}
                            for i, (pair, index) in enumerate(zip(example["pairs"], selected, strict=True))]
        cases.append(check)
    arguments = [a for c in cases for a in c["arguments"]]
    families = {c["family"] for c in cases}
    summary = {"documents": len(cases), "classified_pairs": total, "classified_pairs_correct": correct,
               "arguments_expected": len(arguments), "arguments_detected": sum(a["detected"] for a in arguments),
               "arguments_correct": sum(a["correct"] for a in arguments),
               "documents_all_specified_correct": sum(c["all_specified_correct"] for c in cases),
               "families_both_voices_correct": sum(all(c["all_specified_correct"] for c in cases if c["family"] == f) for f in families),
               "by_voice": {}, "by_role": {}}
    for voice in ("active", "passive"):
        args = [a for c in cases if c["voice"] == voice for a in c["arguments"]]
        summary["by_voice"][voice] = {"correct": sum(a["correct"] for a in args), "expected": len(args)}
    for role in LABELS[1:]:
        args = [a for a in arguments if a["role"] == role]
        summary["by_role"][role] = {"correct": sum(a["correct"] for a in args), "expected": len(args)}
    return {"summary": summary, "cases": cases}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="reports/role-transfer-v1")
    parser.add_argument("--artifacts", default="artifacts/role-transfer-v1")
    args = parser.parse_args()
    out, artifacts = Path(args.output), Path(args.artifacts)
    if out.exists() or artifacts.exists():
        raise ValueError("Refusing to overwrite a role experiment")
    out.mkdir(parents=True)
    artifacts.mkdir(parents=True)
    def save(name, value):
        (out / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    os.environ["KWJA_CLI_MODE"] = "1"
    logging.disable(logging.WARNING)
    from transformers.generation.utils import GenerationMixin
    from kwja.utils.jumandic import JumanDic
    from kwja.callbacks.word_module_writer import WordModuleWriter
    from kwja.modules import Seq2SeqModule, TypoModule
    with ExitStack() as stack:
        guards = [stack.enter_context(patch.object(cls, name, side_effect=AssertionError("Forbidden generation/dictionary path")))
                  for cls, name in ((GenerationMixin, "generate"), (JumanDic, "__init__"),
                                    (WordModuleWriter, "__init__"), (Seq2SeqModule, "__init__"), (TypoModule, "__init__"))]
        model = JapanesePAS()
        rows = json.loads(Path(DATA).read_text(encoding="utf-8"))
        validate_rows(rows)
        cases = list(model.configs["word"].pas_cases)
        dimension = model.models["word"].encoder.config.hidden_size
        examples = extract(model, [r for r in rows if r["split"] != "test"], cases)
        heads, choices = {}, {}
        for name, hidden in (("linear", 0), ("mlp", 64)):
            heads[name], choices[name], history = fit(examples, dimension, cases, hidden)
            save_file(heads[name].state_dict(), str(artifacts / (name + ".safetensors")))
            save(name + "-history.json", history)
        chosen = min(choices, key=lambda name: choices[name]["dev_loss"])
        selection = {"selected": chosen, "choices": choices, "dimension": dimension, "cases": cases,
                     "labels": LABELS, "weights_sha256": {name: digest(artifacts / (name + ".safetensors")) for name in heads}}
        save("selection.json", selection)
        # No test sentence is encoded until both epoch and architecture are saved.
        examples.extend(extract(model, [r for r in rows if r["split"] == "test"], cases))
        save_file({e["row"]["id"]: e["features"] for e in examples}, str(artifacts / "features.safetensors"))
        save("evidence.json", [{k: e[k] for k in ("row", "prediction", "pairs")} | {"targets": e["targets"].tolist()} for e in examples])
        results = {name: {split: evaluate([e for e in examples if e["row"]["split"] == split], head)
                          for split in ("train", "dev", "test")} for name, head in heads.items()}
        save("evaluation.json", results)
        save("run.json", {"encoder": model.metadata, "fixture_sha256": digest(DATA), "code_sha256": {
            p: digest(p) for p in ("noema/role_transfer.py", "scripts/train_role_transfer.py")},
            "features_sha256": digest(artifacts / "features.safetensors"), "forbidden_path_calls": [g.call_count for g in guards],
            "supervised_label_counts": {split: torch.bincount(supervised(examples, split)[1], minlength=len(LABELS)).tolist()
                                        for split in ("train", "dev", "test")}})
        print(json.dumps({"selection": selection, "test": {n: r["test"]["summary"] for n, r in results.items()}}, indent=2))


if __name__ == "__main__":
    main()
