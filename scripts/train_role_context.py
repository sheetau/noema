"""Compare unchanged role training with boundary context on frozen mentions."""
import argparse
import json
from pathlib import Path
import shutil

import torch
from torch.nn import functional as F
from safetensors.torch import load_file, save_file

from noema.definition_probe import digest
from noema.encoder import deterministic
from noema.japanese_pas import JapanesePAS
from noema.mention_scope import MentionHead, infer_mentions, scope_targets
from noema.role_context import FEATURES, ContextRoleHead, context_candidates
from scripts.train_mention_scope import ARCHITECTURES, extract, evaluate, forbidden_paths
from scripts.train_mention_learning import SPLITS as OLD_SPLITS
from scripts.train_role_transfer import supervised, validate_rows

DATA = "data/role-context-v3.json"
SPLITS = (*OLD_SPLITS, "context_confirmation")
PREVIOUS = Path("reports/mention-learning-v2")
PREVIOUS_ARTIFACTS = Path("artifacts/mention-learning-v2")


def cached_sources():
    def read(name):
        return json.loads((PREVIOUS / name).read_text(encoding="utf-8"))
    run, selection = read("run.json"), read("selection.json")
    assert all(digest(p) == value for p, value in run["fixtures_sha256"].items())
    assert all(digest(p) == value for p, value in run["code_sha256"].items())
    path = PREVIOUS_ARTIFACTS / "features.safetensors"
    assert digest(path) == run["features_sha256"]
    tensors = load_file(str(path))
    def recover(name):
        return [{**e, "vectors": tensors["tokens/" + e["row"]["id"]],
                 "tags": torch.tensor(e["tags"], dtype=torch.long), "targets": torch.tensor(e["targets"], dtype=torch.long)} for e in read(name)]
    name = selection["mention"]["selected"]
    path = PREVIOUS_ARTIFACTS / f"mention-{name}.safetensors"
    assert digest(path) == selection["mention"]["weights_sha256"][name]
    head = MentionHead(selection["dimension"], selection["mention"]["choices"][name]["hidden"])
    head.load_state_dict(load_file(str(path)), strict=True)
    return recover("evidence.json"), recover("crossfit-evidence.json"), head.eval(), selection, run


def with_features(examples, cases, mode):
    converted = []
    for example in examples:
        pairs, features = context_candidates(example["prediction"], example["vectors"], example["mentions"], cases, mode)
        assert pairs == example["pairs"]
        converted.append({**example, "features": features})
    return converted


def fit(examples, dimension, cases, hidden, mode):
    deterministic()
    head = ContextRoleHead(dimension, cases, hidden, mode)
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
                    "state": {key: value.detach().clone() for key, value in head.state_dict().items()}}
    head.load_state_dict(best["state"])
    return head.eval(), {"epoch": best["epoch"], "dev_loss": best["dev_loss"], "hidden": hidden, "features": mode}, history


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="reports/role-context-v3")
    parser.add_argument("--artifacts", default="artifacts/role-context-v3")
    args = parser.parse_args()
    out, artifacts = Path(args.output), Path(args.artifacts)
    if out.exists() or artifacts.exists():
        raise ValueError("Refusing to overwrite a role context experiment")
    out.mkdir(parents=True)
    artifacts.mkdir(parents=True)
    def save(name, value):
        (out / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    examples, crossfit, mention_head, previous_selection, previous_run = cached_sources()
    dimension, cases = previous_selection["dimension"], previous_selection["cases"]
    for name, sha in previous_selection["mention"]["weights_sha256"].items():
        source = PREVIOUS_ARTIFACTS / f"mention-{name}.safetensors"
        assert digest(source) == sha
        shutil.copyfile(source, artifacts / source.name)
    development = [e for e in examples if e["row"]["split"] == "dev"]
    heads, choices = {}, {}
    for mode in FEATURES:
        training = with_features(crossfit + development, cases, mode)
        for name, hidden in ARCHITECTURES:
            key = f"{mode}-{name}"
            heads[key], choices[key], history = fit(training, dimension, cases, hidden, mode)
            save_file(heads[key].state_dict(), str(artifacts / f"role-{key}.safetensors"))
            save(f"role-{key}-history.json", history)
    chosen = min(choices, key=lambda key: choices[key]["dev_loss"])
    selection = {**{key: previous_selection[key] for key in ("mention", "dimension", "cases", "tags", "labels")},
                 "candidate_policy": "learned_mentions_with_role_context", "role": {"selected": chosen, "choices": choices,
                 "weights_sha256": {key: digest(artifacts / f"role-{key}.safetensors") for key in heads}}}
    save("selection.json", selection)
    rows = json.loads(Path(DATA).read_text(encoding="utf-8"))
    validate_rows([e["row"] for e in examples] + rows)
    assert not ({r["family"] for r in rows} & {e["row"]["family"] for e in examples})
    with forbidden_paths() as guards:
        model = JapanesePAS()
        assert model.metadata == previous_run["encoder"]
        new = extract(model, rows)
        for example in new:
            mentions = infer_mentions(example["prediction"], example["vectors"], mention_head)
            pairs, _ = context_candidates(example["prediction"], example["vectors"], mentions, cases, "mean")
            example.update(mentions=mentions, pairs=pairs, targets=scope_targets(example["row"], example["prediction"], mentions, pairs))
        examples.extend(new)
        results = {}
        for mode in FEATURES:
            converted = with_features(examples, cases, mode)
            for name, _ in ARCHITECTURES:
                key = f"{mode}-{name}"
                results[key] = {split: evaluate([e for e in converted if e["row"]["split"] == split], heads[key]) for split in SPLITS}
        save("evaluation.json", results)
        # Only new evidence is duplicated; old evidence is addressed by hashes.
        save("evidence.json", [{key: e[key] for key in ("row", "prediction", "mentions", "pairs")} |
                               {"targets": e["targets"].tolist(), "tags": e["tags"].tolist()} for e in new])
        save_file({e["row"]["id"]: e["vectors"] for e in new}, str(artifacts / "new-vectors.safetensors"))
        save("run.json", {"encoder": model.metadata, "new_fixture_sha256": digest(DATA),
            "previous_files_sha256": {str(PREVIOUS / name): digest(PREVIOUS / name) for name in (
                "selection.json", "run.json", "evidence.json", "crossfit-evidence.json", "crossfit.json")},
            "code_sha256": {p: digest(p) for p in ("noema/role_context.py", "scripts/train_role_context.py", "noema/mention_scope.py",
                "noema/role_transfer.py", "noema/japanese_pas.py", "scripts/train_mention_scope.py")},
            "new_vectors_sha256": digest(artifacts / "new-vectors.safetensors"), "forbidden_path_calls": [g.call_count for g in guards]})
        print(json.dumps({"selection": selection["role"], "confirmation": {name: result["context_confirmation"]["summary"] for name, result in results.items()}}, indent=2))


if __name__ == "__main__":
    main()
