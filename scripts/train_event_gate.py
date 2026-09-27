"""Learn a shared event gate while freezing the scope and role models."""
import argparse
import json
from pathlib import Path

import torch
from torch.nn import functional as F
from safetensors.torch import load_file, save_file

from noema.definition_probe import digest
from noema.encoder import deterministic
from noema.event_gate import GATE_LABELS, EventGateHead, event_features, gate_targets, event_decisions, assess_gate
from noema.event_frames import predict_frames, assess_document
from noema.japanese_pas import JapanesePAS
from noema.mention_sequence import SequenceMentionHead
from noema.role_context import ContextRoleHead
from scripts.train_event_frames import cached_documents as previous_documents, groups, extract
from scripts.train_mention_scope import ARCHITECTURES, forbidden_paths

DATA = "data/event-gate-v6.json"
PREVIOUS = Path("reports/multi-frame-v5")
PREVIOUS_ARTIFACTS = Path("artifacts/multi-frame-v5")


def cached_documents():
    documents, _, _, _ = previous_documents()
    run = json.loads((PREVIOUS / "run.json").read_text(encoding="utf-8"))
    for group in ("code_sha256", "previous_files_sha256"):
        assert all(digest(p) == sha for p, sha in run[group].items())
    assert digest("data/multi-frame-v5.json") == run["fixture_sha256"]
    path = PREVIOUS_ARTIFACTS / "new-vectors.safetensors"
    assert digest(path) == run["new_vectors_sha256"]
    vectors = load_file(str(path))
    documents.extend({**d, "vectors": vectors[d["document"]["id"]]} for d in json.loads((PREVIOUS / "evidence.json").read_text(encoding="utf-8")))
    selection = json.loads((PREVIOUS / "selection.json").read_text(encoding="utf-8"))
    heads = {}
    for stage in ("mention", "role"):
        name = selection[stage]["selected"]
        path = PREVIOUS_ARTIFACTS / f"{stage}-{name}.safetensors"
        assert digest(path) == selection[stage]["weights_sha256"][name]
        hidden = selection[stage]["choices"][name]["hidden"]
        head = SequenceMentionHead(selection["dimension"] * 5, hidden) if stage == "mention" else ContextRoleHead(selection["dimension"], selection["cases"], hidden)
        head.load_state_dict(load_file(str(path)), strict=True)
        heads[stage] = head.eval().requires_grad_(False)
    return documents, heads, selection, run


def training_batch(documents, split):
    features, targets = [], []
    for d in documents:
        if d["document"]["split"] != split:
            continue
        candidates, x = event_features(d["prediction"], d["vectors"])
        y = gate_targets(d["document"], candidates)
        features.append(x[y != -100])
        targets.append(y[y != -100])
    return torch.cat(features), torch.cat(targets)


def fit(documents, dimension, hidden):
    deterministic()
    head = EventGateHead(dimension, hidden)
    optimizer = torch.optim.AdamW(head.parameters(), lr=.003, weight_decay=.01)
    tx, ty = training_batch(documents, "train")
    dx, dy = training_batch(documents, "dev")
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
            best = {"epoch": epoch, "dev_loss": dev_loss, "state": {k: v.detach().clone() for k, v in head.state_dict().items()}}
    head.load_state_dict(best["state"])
    return head.eval(), {"epoch": best["epoch"], "dev_loss": best["dev_loss"], "hidden": hidden}, history


def evaluate(documents, raw_frames, head=None):
    checks = []
    for d in documents:
        row, prediction = d["document"], d["prediction"]
        decisions = event_decisions(prediction, d["vectors"], head) if head is not None else [
            {"source": p["id"], "predicate": p["head"], "keep": True, "event_score": None} for p in event_features(prediction, d["vectors"])[0]]
        kept = {decision["source"] for decision in decisions if decision["keep"]}
        frames = [frame for frame in raw_frames[row["id"]] if frame["source"] in kept]
        check = assess_document(row, prediction, frames)
        checks.append({**check, "gate": assess_gate(row, prediction, decisions), "event_decisions": decisions, "frames": frames})
    summary = {key: sum(c[key] for c in checks) for key in (
        "gold_frames", "detected_frames", "predicate_candidates", "unannotated_predicate_candidates", "gold_spans", "predicted_spans", "exact_spans",
        "gold_roles", "predicted_roles", "exact_roles", "extra_roles", "missing_roles", "duplicate_roles", "frames_exact", "document_exact")}
    summary["documents"] = len(checks)
    summary["gate"] = {key: sum(c["gate"][key] for c in checks) for key in checks[0]["gate"]} if checks else {}
    for unit in ("spans", "roles"):
        for name, prefix in (("precision", "predicted_"), ("recall", "gold_")):
            count = summary[prefix + unit]
            summary[unit + "_" + name] = summary["exact_" + unit] / count if count else None
    return {"summary": summary, "cases": checks}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="reports/event-gate-v6")
    parser.add_argument("--artifacts", default="artifacts/event-gate-v6")
    args = parser.parse_args()
    out, artifacts = Path(args.output), Path(args.artifacts)
    if out.exists() or artifacts.exists():
        raise ValueError("Refusing to overwrite an event gate experiment")
    out.mkdir(parents=True)
    artifacts.mkdir(parents=True)
    def save(name, value):
        (out / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    documents, frame_heads, previous, previous_run = cached_documents()
    heads, choices = {}, {}
    for name, hidden in ARCHITECTURES:
        heads[name], choices[name], history = fit(documents, previous["dimension"], hidden)
        save_file(heads[name].state_dict(), str(artifacts / f"gate-{name}.safetensors"))
        save(f"gate-{name}-history.json", history)
    chosen = min(choices, key=lambda name: choices[name]["dev_loss"])
    selection = {"selected": chosen, "choices": choices, "dimension": previous["dimension"], "labels": GATE_LABELS,
                 "decision": "argmax", "weights_sha256": {name: digest(artifacts / f"gate-{name}.safetensors") for name in heads},
                 "frame_report": str(PREVIOUS), "frame_artifacts": str(PREVIOUS_ARTIFACTS), "frame_selection_sha256": digest(PREVIOUS / "selection.json")}
    save("selection.json", selection)
    rows = json.loads(Path(DATA).read_text(encoding="utf-8"))
    train_dev_families = {f["family"] for d in documents if d["document"]["split"] in ("train", "dev") for f in d["document"]["frames"]}
    assert not train_dev_families & {f["family"] for r in rows for f in r["frames"]}
    with forbidden_paths() as guards:
        model = JapanesePAS()
        assert model.metadata == previous_run["encoder"]
        added = extract(model, rows)
        documents.extend(added)
        save("evidence.json", [{"document": d["document"], "prediction": d["prediction"]} for d in added])
        save_file({d["document"]["id"]: d["vectors"] for d in added}, str(artifacts / "new-vectors.safetensors"))
        raw_frames = {d["document"]["id"]: predict_frames(d["prediction"], d["vectors"], frame_heads["mention"], frame_heads["role"]) for d in documents}
        results = {name: {group: evaluate(ds, raw_frames, head) for group, ds in groups(documents).items()} for name, head in heads.items()}
        results["ungated"] = {group: evaluate(ds, raw_frames) for group, ds in groups(documents).items()}
        save("evaluation.json", results)
        save("run.json", {"encoder": model.metadata, "fixture_sha256": digest(DATA),
            "previous_files_sha256": {str(PREVIOUS / name): digest(PREVIOUS / name) for name in ("run.json", "selection.json", "evidence.json")},
            "code_sha256": {p: digest(p) for p in ("noema/event_gate.py", "scripts/train_event_gate.py", "noema/event_frames.py",
                "scripts/train_event_frames.py", "noema/mention_sequence.py", "noema/role_context.py")},
            "new_vectors_sha256": digest(artifacts / "new-vectors.safetensors"), "forbidden_path_calls": [g.call_count for g in guards],
            "training_labels": {split: torch.bincount(training_batch(documents, split)[1], minlength=2).tolist() for split in ("train", "dev")}})
        print(json.dumps({"selection": selection, "confirmation": {name: result["multi_gate_confirmation"]["summary"] for name, result in results.items()}}, indent=2))


if __name__ == "__main__":
    main()
