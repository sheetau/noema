"""Train BIO chains and cross-fitted boundary role heads on frozen source states."""
import argparse
import json
from pathlib import Path

import torch
from torch.nn.utils.rnn import pad_sequence
from safetensors.torch import load_file, save_file

from noema.definition_probe import digest
from noema.encoder import deterministic
from noema.japanese_pas import JapanesePAS
from noema.mention_scope import TAGS, infer_mentions, scope_targets
from noema.mention_sequence import SequenceMentionHead, infer_sequence_mentions
from noema.role_context import ContextRoleHead, context_candidates
from noema.role_transfer import LABELS
from scripts.train_mention_scope import ARCHITECTURES, extract, evaluate, forbidden_paths
from scripts.train_mention_learning import family_folds, source_only, serializable
from scripts.train_role_context import cached_sources as previous_sources, fit as fit_role, SPLITS as OLD_SPLITS
from scripts.train_role_transfer import validate_rows

DATA = "data/mention-sequence-v4.json"
SPLITS = (*OLD_SPLITS, "sequence_confirmation")
PREVIOUS = Path("reports/role-context-v3")
PREVIOUS_ARTIFACTS = Path("artifacts/role-context-v3")


def cached_sources():
    examples, _, old_mention, _, _ = previous_sources()
    run = json.loads((PREVIOUS / "run.json").read_text(encoding="utf-8"))
    for group in ("code_sha256", "previous_files_sha256"):
        assert all(digest(p) == sha for p, sha in run[group].items())
    assert digest("data/role-context-v3.json") == run["new_fixture_sha256"]
    path = PREVIOUS_ARTIFACTS / "new-vectors.safetensors"
    assert digest(path) == run["new_vectors_sha256"]
    vectors = load_file(str(path))
    for e in json.loads((PREVIOUS / "evidence.json").read_text(encoding="utf-8")):
        examples.append({**e, "vectors": vectors[e["row"]["id"]], "tags": torch.tensor(e["tags"], dtype=torch.long)})
    selection = json.loads((PREVIOUS / "selection.json").read_text(encoding="utf-8"))
    name = selection["role"]["selected"]
    path = PREVIOUS_ARTIFACTS / f"role-{name}.safetensors"
    assert digest(path) == selection["role"]["weights_sha256"][name]
    choice = selection["role"]["choices"][name]
    old_role = ContextRoleHead(selection["dimension"], selection["cases"], choice["hidden"], choice["features"])
    old_role.load_state_dict(load_file(str(path)), strict=True)
    return [source_only(e) for e in examples], old_mention, old_role.eval(), selection, run


def sequence_batch(examples):
    return (pad_sequence([e["vectors"] for e in examples], batch_first=True),
            pad_sequence([e["tags"] for e in examples], batch_first=True),
            torch.tensor([len(e["tags"]) for e in examples], dtype=torch.long))


def fit_sequence(training, dimension, hidden, development=None, epochs=200):
    deterministic()
    head = SequenceMentionHead(dimension, hidden)
    optimizer = torch.optim.AdamW(head.parameters(), lr=.003, weight_decay=.01)
    train_batch = sequence_batch(training)
    dev_batch = sequence_batch(development) if development else None
    best, history = None, []
    for epoch in range(1, epochs + 1):
        optimizer.zero_grad()
        loss = head.loss(*train_batch)
        assert torch.isfinite(loss), "Non-finite training loss"
        loss.backward()
        optimizer.step()
        with torch.no_grad():
            dev_loss = float(head.loss(*dev_batch)) if dev_batch else None
        history.append({"epoch": epoch, "train_loss": float(loss.detach()), "dev_loss": dev_loss})
        if best is None or dev_batch is None or dev_loss < best["dev_loss"]:
            best = {"epoch": epoch, "dev_loss": dev_loss, "state": {k: v.detach().clone() for k, v in head.state_dict().items()}}
        if epoch % 50 == 0:
            print("sequence epoch", epoch, "hidden", hidden, "train", float(loss.detach()), "dev", dev_loss, flush=True)
    head.load_state_dict(best["state"])
    return head.eval(), {"epoch": best["epoch"], "dev_loss": best["dev_loss"], "hidden": hidden}, history


def add_candidates(examples, head, cases, sequence=True):
    for example in examples:
        infer = infer_sequence_mentions if sequence else infer_mentions
        mentions = infer(example["prediction"], example["vectors"], head)
        pairs, features = context_candidates(example["prediction"], example["vectors"], mentions, cases)
        example.update(mentions=mentions, pairs=pairs, features=features,
                       targets=scope_targets(example["row"], example["prediction"], mentions, pairs))


def crossfit(examples, dimension, cases, choice):
    training = [e for e in examples if e["row"]["split"] == "train"]
    folds, heads, record, out = family_folds(training), {}, {}, []
    for fold in sorted(set(folds.values())):
        fitted = [e for e in training if folds[e["row"]["family"]] != fold]
        held = [source_only(e) for e in training if folds[e["row"]["family"]] == fold]
        head, _, history = fit_sequence(fitted, dimension, choice["hidden"], epochs=choice["epoch"])
        add_candidates(held, head, cases)
        out.extend(held)
        heads[str(fold)] = head
        record[str(fold)] = {"training_ids": [e["row"]["id"] for e in fitted], "predicted_ids": [e["row"]["id"] for e in held], "history": history}
    by_id = {e["row"]["id"]: e for e in out}
    return [by_id[e["row"]["id"]] for e in training], heads, {"family_folds": folds, "folds": record}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="reports/mention-sequence-v4")
    parser.add_argument("--artifacts", default="artifacts/mention-sequence-v4")
    args = parser.parse_args()
    out, artifacts = Path(args.output), Path(args.artifacts)
    if out.exists() or artifacts.exists():
        raise ValueError("Refusing to overwrite a sequence experiment")
    out.mkdir(parents=True)
    artifacts.mkdir(parents=True)
    def save(name, value):
        (out / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    examples, old_mention, old_role, previous_selection, previous_run = cached_sources()
    dimension, cases = previous_selection["dimension"], previous_selection["cases"]
    training = [e for e in examples if e["row"]["split"] == "train"]
    development = [e for e in examples if e["row"]["split"] == "dev"]
    heads, choices = {}, {}
    for name, hidden in ARCHITECTURES:
        heads[name], choices[name], history = fit_sequence(training, dimension, hidden, development)
        save_file(heads[name].state_dict(), str(artifacts / f"mention-{name}.safetensors"))
        save(f"mention-{name}-history.json", history)
    chosen = min(choices, key=lambda name: choices[name]["dev_loss"])
    mention_selection = {"selected": chosen, "choices": choices, "weights_sha256": {
        name: digest(artifacts / f"mention-{name}.safetensors") for name in heads}}
    save("mention-selection.json", mention_selection)
    mention_head = heads[chosen]
    add_candidates(training + development, mention_head, cases)
    oof, fold_heads, record = crossfit(training, dimension, cases, choices[chosen])
    for fold, head in fold_heads.items():
        save_file(head.state_dict(), str(artifacts / f"fold-{fold}.safetensors"))
        record["folds"][fold]["weights_sha256"] = digest(artifacts / f"fold-{fold}.safetensors")
    save("crossfit.json", record)
    save("crossfit-evidence.json", serializable(oof))
    role_heads, role_choices = {}, {}
    for name, hidden in ARCHITECTURES:
        role_heads[name], role_choices[name], history = fit_role(oof + development, dimension, cases, hidden, "boundary")
        save_file(role_heads[name].state_dict(), str(artifacts / f"role-{name}.safetensors"))
        save(f"role-{name}-history.json", history)
    selected_role = min(role_choices, key=lambda name: role_choices[name]["dev_loss"])
    selection = {"mention": mention_selection, "role": {"selected": selected_role, "choices": role_choices,
                 "weights_sha256": {name: digest(artifacts / f"role-{name}.safetensors") for name in role_heads}},
                 "dimension": dimension, "cases": cases, "tags": TAGS, "labels": LABELS, "candidate_policy": "learned_bio_chain"}
    save("selection.json", selection)
    rows = json.loads(Path(DATA).read_text(encoding="utf-8"))
    validate_rows([e["row"] for e in examples] + rows)
    assert not ({r["family"] for r in rows} & {e["row"]["family"] for e in examples})
    with forbidden_paths() as guards:
        model = JapanesePAS()
        assert model.metadata == previous_run["encoder"]
        new = extract(model, rows)
        examples.extend(new)
        add_candidates([e for e in examples if e["row"]["split"] not in ("train", "dev")], mention_head, cases)
        save("evidence.json", serializable(examples))
        save_file({e["row"]["id"]: e["vectors"] for e in new}, str(artifacts / "new-vectors.safetensors"))
        results = {name: {split: evaluate([e for e in examples if e["row"]["split"] == split], head) for split in SPLITS}
                   for name, head in role_heads.items()}
        baseline = [source_only(e) for e in examples]
        add_candidates(baseline, old_mention, cases, sequence=False)
        results["saved_v3"] = {split: evaluate([e for e in baseline if e["row"]["split"] == split], old_role) for split in SPLITS}
        save("evaluation.json", results)
        from scripts.audit_role_context import audit
        error_audit = audit(examples, {name: result for name, result in results.items() if name != "saved_v3"})
        error_audit.update(audit(baseline, {"saved_v3": results["saved_v3"]}))
        save("error-audit.json", error_audit)
        save("run.json", {"encoder": model.metadata, "new_fixture_sha256": digest(DATA),
            "previous_files_sha256": {str(PREVIOUS / name): digest(PREVIOUS / name) for name in ("run.json", "selection.json", "evidence.json")},
            "code_sha256": {p: digest(p) for p in ("noema/mention_sequence.py", "scripts/train_mention_sequence.py",
                "noema/role_context.py", "noema/mention_scope.py", "scripts/train_role_context.py", "scripts/audit_role_context.py")},
            "new_vectors_sha256": digest(artifacts / "new-vectors.safetensors"), "forbidden_path_calls": [g.call_count for g in guards],
            "role_training_labels": torch.bincount(torch.cat([e["targets"][e["targets"] != -100] for e in oof]), minlength=len(LABELS)).tolist()})
        print(json.dumps({"selection": selection, "confirmation": {name: r["sequence_confirmation"]["summary"] for name, r in results.items()}}, indent=2))


if __name__ == "__main__":
    main()
