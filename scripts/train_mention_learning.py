"""Compare structural mention supervision and out-of-fold role candidates."""
import argparse
import json
from pathlib import Path

import torch
from torch.nn import functional as F
from safetensors.torch import load_file, save_file

from noema.definition_probe import digest
from noema.encoder import deterministic
from noema.japanese_pas import JapanesePAS
from noema.mention_scope import TAGS, MentionHead, gold_mentions, infer_mentions
from noema.role_transfer import LABELS, RoleHead, UNLINKED
from scripts.train_mention_scope import (ARCHITECTURES, DATA as PREVIOUS_DATA, SPLITS as PREVIOUS_SPLITS,
                                         extract, fit_mentions, add_candidates, evaluate, forbidden_paths)
from scripts.train_role_transfer import fit as fit_role, supervised, validate_rows

DATA = (*PREVIOUS_DATA, "data/mention-training-v2.json", "data/mention-confirmation-v2.json")
SPLITS = (*PREVIOUS_SPLITS, "scope_confirmation")


def source_only(example):
    return {key: example[key] for key in ("row", "prediction", "vectors", "tags")}


def cached_sources():
    root = Path("reports/mention-scope-v1")
    run = json.loads((root / "run.json").read_text(encoding="utf-8"))
    path = Path("artifacts/mention-scope-v1/features.safetensors")
    assert digest(path) == run["features_sha256"]
    assert all(digest(p) == value for p, value in run["fixtures_sha256"].items())
    assert all(digest(p) == value for p, value in run["code_sha256"].items())
    evidence = json.loads((root / "evidence.json").read_text(encoding="utf-8"))
    tensors = load_file(str(path))
    return [{"row": e["row"], "prediction": e["prediction"], "vectors": tensors["tokens/" + e["row"]["id"]],
             "tags": torch.tensor(e["tags"], dtype=torch.long)} for e in evidence], run


def family_folds(examples, count=4):
    families = sorted({e["row"]["family"] for e in examples if e["row"]["split"] == "train"})
    assert len(families) >= count > 1
    return {family: index % count for index, family in enumerate(families)}


def fit_fixed_mentions(examples, dimension, hidden, epochs):
    """Train a fold for the already selected epoch count, without its held-out rows."""
    assert epochs > 0 and examples
    deterministic()
    head = MentionHead(dimension, hidden)
    optimizer = torch.optim.AdamW(head.parameters(), lr=.003, weight_decay=.01)
    x, y = torch.cat([e["vectors"] for e in examples]), torch.cat([e["tags"] for e in examples])
    history = []
    for epoch in range(1, epochs + 1):
        optimizer.zero_grad()
        loss = F.cross_entropy(head(x), y)
        loss.backward()
        optimizer.step()
        history.append({"epoch": epoch, "train_loss": float(loss.detach())})
    return head.eval(), history


def crossfit_candidates(examples, dimension, cases, choice):
    training = [e for e in examples if e["row"]["split"] == "train"]
    folds = family_folds(training)
    results, heads, records = [], {}, {}
    for fold in sorted(set(folds.values())):
        fitted = [e for e in training if folds[e["row"]["family"]] != fold]
        predicted = [source_only(e) for e in training if folds[e["row"]["family"]] == fold]
        head, history = fit_fixed_mentions(fitted, dimension, choice["hidden"], choice["epoch"])
        add_candidates(predicted, head, cases)
        results.extend(predicted)
        heads[str(fold)] = head
        records[str(fold)] = {"training_ids": [e["row"]["id"] for e in fitted],
                              "predicted_ids": [e["row"]["id"] for e in predicted], "history": history}
    by_id = {e["row"]["id"]: e for e in results}
    return [by_id[e["row"]["id"]] for e in training], heads, {"family_folds": folds, "folds": records}


def evaluate_mentions(examples, head):
    checks = []
    for example in examples:
        mentions = infer_mentions(example["prediction"], example["vectors"], head)
        gold = {(span["start"], span["end"]) for span in gold_mentions(example["row"])}
        actual = {(span["start"], span["end"]) for span in mentions}
        checks.append({"id": example["row"]["id"], "gold": len(gold), "predicted": len(actual),
                       "exact": len(gold & actual), "document_exact": gold == actual, "mentions": mentions})
    summary = {key: sum(c[key] for c in checks) for key in ("gold", "predicted", "exact", "document_exact")}
    summary.update(documents=len(checks), precision=summary["exact"] / summary["predicted"] if summary["predicted"] else None,
                   recall=summary["exact"] / summary["gold"] if summary["gold"] else None)
    return {"summary": summary, "cases": checks}


def old_heads():
    root = Path("reports/mention-scope-v1")
    selection = json.loads((root / "selection.json").read_text(encoding="utf-8"))
    heads = {}
    for stage in ("mention", "role"):
        name = selection[stage]["selected"]
        path = Path("artifacts/mention-scope-v1") / f"{stage}-{name}.safetensors"
        assert digest(path) == selection[stage]["weights_sha256"][name]
        hidden = selection[stage]["choices"][name]["hidden"]
        head = MentionHead(selection["dimension"], hidden) if stage == "mention" else RoleHead(selection["dimension"], selection["cases"], hidden)
        head.load_state_dict(load_file(str(path)), strict=True)
        heads[stage] = head.eval()
    return heads


def serializable(examples):
    return [{key: e[key] for key in ("row", "prediction", "mentions", "pairs")} |
            {"targets": e["targets"].tolist(), "tags": e["tags"].tolist()} for e in examples]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="reports/mention-learning-v2")
    parser.add_argument("--artifacts", default="artifacts/mention-learning-v2")
    args = parser.parse_args()
    out, artifacts = Path(args.output), Path(args.artifacts)
    if out.exists() or artifacts.exists():
        raise ValueError("Refusing to overwrite a mention learning experiment")
    out.mkdir(parents=True)
    artifacts.mkdir(parents=True)
    def save(name, value):
        (out / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    rows = [r for p in DATA for r in json.loads(Path(p).read_text(encoding="utf-8"))]
    validate_rows(rows)
    groups = {split: {r["family"] for r in rows if r["split"] == split} for split in SPLITS}
    assert all(not groups[a] & groups[b] for i, a in enumerate(SPLITS) for b in SPLITS[i + 1:])
    cached, previous_run = cached_sources()
    expected_rows = {r["id"]: r for r in rows}
    assert all(e["row"] == expected_rows[e["row"]["id"]] for e in cached)
    with forbidden_paths() as guards:
        model = JapanesePAS()
        assert model.metadata == previous_run["encoder"]
        dimension = model.models["word"].encoder.config.hidden_size
        cases = list(model.configs["word"].pas_cases) + [UNLINKED]
        extra_rows = json.loads(Path("data/mention-training-v2.json").read_text(encoding="utf-8"))
        examples = [source_only(e) for e in cached if e["row"]["split"] in ("train", "dev")]
        examples.extend(extract(model, extra_rows))
        curve_heads, curve_selections = {}, {}
        for amount in (32, 64):
            chosen_examples = [e for e in examples if amount == 64 or e["row"]["split"] == "dev"
                               or not e["row"]["id"].startswith("scope-")]
            heads, choices = {}, {}
            prefix = "mention-32" if amount == 32 else "mention"
            for name, hidden in ARCHITECTURES:
                heads[name], choices[name], history = fit_mentions(chosen_examples, dimension, hidden)
                save_file(heads[name].state_dict(), str(artifacts / f"{prefix}-{name}.safetensors"))
                save(f"{prefix}-{name}-history.json", history)
            chosen = min(choices, key=lambda name: choices[name]["dev_loss"])
            curve_heads[str(amount)] = heads[chosen]
            curve_selections[str(amount)] = {"selected": chosen, "choices": choices, "weights_sha256": {
                name: digest(artifacts / f"{prefix}-{name}.safetensors") for name in heads}}
        save("mention-selections.json", curve_selections)
        add_candidates(examples, curve_heads["64"], cases)
        mention_choice = curve_selections["64"]["choices"][curve_selections["64"]["selected"]]
        out_of_fold, fold_heads, fold_record = crossfit_candidates(examples, dimension, cases, mention_choice)
        for fold, head in fold_heads.items():
            save_file(head.state_dict(), str(artifacts / f"fold-{fold}.safetensors"))
            fold_record["folds"][fold]["weights_sha256"] = digest(artifacts / f"fold-{fold}.safetensors")
        save("crossfit.json", fold_record)
        save("crossfit-evidence.json", serializable(out_of_fold))
        role_heads, role_choices = {}, {}
        for policy in ("in_sample", "crossfit"):
            role_examples = examples if policy == "in_sample" else out_of_fold + [e for e in examples if e["row"]["split"] == "dev"]
            for name, hidden in ARCHITECTURES:
                key = f"{policy}-{name}"
                head, choice, history = fit_role(role_examples, dimension, cases, hidden)
                role_heads[key], role_choices[key] = head, {**choice, "training_candidates": policy}
                save_file(head.state_dict(), str(artifacts / f"role-{key}.safetensors"))
                save(f"role-{key}-history.json", history)
        chosen = min(role_choices, key=lambda name: role_choices[name]["dev_loss"])
        selection = {"mention": curve_selections["64"], "role": {"selected": chosen, "choices": role_choices,
                     "weights_sha256": {name: digest(artifacts / f"role-{name}.safetensors") for name in role_heads}},
                     "dimension": dimension, "cases": cases, "tags": TAGS, "labels": LABELS, "candidate_policy": "learned_mentions"}
        save("selection.json", selection)
        # No new confirmation text is encoded before all selections are saved.
        held = [source_only(e) for e in cached if e["row"]["split"] not in ("train", "dev")]
        held.extend(extract(model, [r for r in rows if r["split"] == "scope_confirmation"]))
        add_candidates(held, curve_heads["64"], cases)
        examples.extend(held)
        save("evidence.json", serializable(examples))
        save_file({"tokens/" + e["row"]["id"]: e["vectors"] for e in examples} |
                  {"roles/" + e["row"]["id"]: e["features"] for e in examples} |
                  {"crossfit/" + e["row"]["id"]: e["features"] for e in out_of_fold}, str(artifacts / "features.safetensors"))
        results = {name: {split: evaluate([e for e in examples if e["row"]["split"] == split], head)
                          for split in SPLITS} for name, head in role_heads.items()}
        baseline = old_heads()
        old_examples = [source_only(e) for e in examples]
        add_candidates(old_examples, baseline["mention"], cases)
        results["saved_v1"] = {split: evaluate([e for e in old_examples if e["row"]["split"] == split], baseline["role"])
                               for split in SPLITS}
        save("evaluation.json", results)
        save("learning-curve.json", {amount: {split: evaluate_mentions([e for e in examples if e["row"]["split"] == split], head)
                                             for split in SPLITS} for amount, head in curve_heads.items()})
        save("run.json", {"encoder": model.metadata, "fixtures_sha256": {p: digest(p) for p in DATA},
            "code_sha256": {p: digest(p) for p in ("scripts/train_mention_learning.py", "scripts/train_mention_scope.py",
                "scripts/train_role_transfer.py", "noema/mention_scope.py", "noema/role_transfer.py", "noema/japanese_pas.py")},
            "features_sha256": digest(artifacts / "features.safetensors"), "previous_run_sha256": digest("reports/mention-scope-v1/run.json"),
            "forbidden_path_calls": [g.call_count for g in guards],
            "role_training_labels": {policy: torch.bincount(supervised(es, "train")[1], minlength=len(LABELS)).tolist()
                                     for policy, es in (("in_sample", examples), ("crossfit", out_of_fold))},
            "token_training_labels": {split: torch.bincount(torch.cat([e["tags"] for e in examples if e["row"]["split"] == split]), minlength=3).tolist()
                                      for split in SPLITS}})
        print(json.dumps({"selection": selection, "confirmation": {name: r["scope_confirmation"]["summary"] for name, r in results.items()}}, indent=2))


if __name__ == "__main__":
    main()
