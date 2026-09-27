"""Learn argument scopes separately for each predicted predicate."""
import argparse
import json
from pathlib import Path

import torch
from safetensors.torch import load_file, save_file

from noema.definition_probe import digest
from noema.japanese_pas import JapanesePAS
from noema.event_frames import (predicate_candidates, supervised_frames, add_frame_candidates, predict_frames,
                                scoped_candidates, assess_document)
from noema.mention_scope import TAGS, mention_targets, role_outputs
from noema.mention_sequence import SequenceMentionHead, infer_sequence_mentions
from noema.role_context import ContextRoleHead
from noema.role_transfer import LABELS, anchor
from scripts.train_mention_sequence import cached_sources as old_sources, fit_sequence
from scripts.train_role_context import fit as fit_role
from scripts.train_mention_scope import ARCHITECTURES, forbidden_paths

DATA = "data/multi-frame-v5.json"
PREVIOUS = Path("reports/mention-sequence-v4")
PREVIOUS_ARTIFACTS = Path("artifacts/mention-sequence-v4")


def cached_documents():
    examples, _, _, _, _ = old_sources()
    run = json.loads((PREVIOUS / "run.json").read_text(encoding="utf-8"))
    for group in ("code_sha256", "previous_files_sha256"):
        assert all(digest(p) == sha for p, sha in run[group].items())
    assert digest("data/mention-sequence-v4.json") == run["new_fixture_sha256"]
    path = PREVIOUS_ARTIFACTS / "new-vectors.safetensors"
    assert digest(path) == run["new_vectors_sha256"]
    vectors = load_file(str(path))
    for e in json.loads((PREVIOUS / "evidence.json").read_text(encoding="utf-8")):
        if e["row"]["id"] in vectors:
            examples.append({**e, "vectors": vectors[e["row"]["id"]]})
    documents = []
    for e in examples:
        row = e["row"]
        documents.append({"document": {"id": row["id"], "split": row["split"], "text": row["text"], "complete_frames": False,
             "frames": [{key: row[key] for key in ("predicate", "family", "roles")}]}, "prediction": e["prediction"], "vectors": e["vectors"]})
    selection = json.loads((PREVIOUS / "selection.json").read_text(encoding="utf-8"))
    heads = {}
    for stage in ("mention", "role"):
        name = selection[stage]["selected"]
        path = PREVIOUS_ARTIFACTS / f"{stage}-{name}.safetensors"
        assert digest(path) == selection[stage]["weights_sha256"][name]
        hidden = selection[stage]["choices"][name]["hidden"]
        head = SequenceMentionHead(selection["dimension"], hidden) if stage == "mention" else ContextRoleHead(selection["dimension"], selection["cases"], hidden)
        head.load_state_dict(load_file(str(path)), strict=True)
        heads[stage] = head.eval()
    return documents, heads, selection, run


def connected_folds(documents):
    families = sorted({f["family"] for d in documents for f in d["document"]["frames"]})
    parents = {f: f for f in families}
    def root(f):
        while parents[f] != f:
            f = parents[f]
        return f
    for d in documents:
        group = [f["family"] for f in d["document"]["frames"]]
        for family in group[1:]:
            a, b = sorted((root(group[0]), root(family)))
            parents[b] = a
    components = sorted({root(f) for f in families})
    assert len(components) >= 4
    by_family = {f: components.index(root(f)) % 4 for f in families}
    by_document = {}
    for d in documents:
        folds = {by_family[f["family"]] for f in d["document"]["frames"]}
        assert len(folds) == 1
        by_document[d["document"]["id"]] = folds.pop()
    return {"family_folds": by_family, "document_folds": by_document}


def extract(model, rows):
    documents = []
    for row in rows:
        prediction, vectors = model.analyze(row["text"], return_features=True)
        for frame in row["frames"]:
            mention_targets({**frame, "text": row["text"]}, prediction["tokens"])
        documents.append({"document": {**row, "complete_frames": True}, "prediction": prediction, "vectors": vectors})
        print("frame source", row["id"], flush=True)
    return documents


def crossfit(documents, dimension, cases, choice):
    split = connected_folds(documents)
    by_document = split["document_folds"]
    examples, heads, records = [], {}, {}
    for fold in range(4):
        fitted = [d for d in documents if by_document[d["document"]["id"]] != fold]
        held = [d for d in documents if by_document[d["document"]["id"]] == fold]
        training, predicted = supervised_frames(fitted), supervised_frames(held)
        head, _, history = fit_sequence(training, dimension * 5, choice["hidden"], epochs=choice["epoch"])
        add_frame_candidates(predicted, head, cases)
        examples.extend(predicted)
        heads[str(fold)] = head
        records[str(fold)] = {"training_ids": [d["document"]["id"] for d in fitted],
                             "predicted_ids": [d["document"]["id"] for d in held], "history": history}
    return examples, heads, {**split, "folds": records}


def predict_baseline(document, mention_head, role_head):
    prediction, vectors = document["prediction"], document["vectors"]
    mentions = infer_sequence_mentions(prediction, vectors, mention_head)
    frames = []
    for source in predicate_candidates(prediction):
        pairs, features = scoped_candidates(prediction, vectors, source, mentions, role_head.cases)
        _, roles = role_outputs(pairs, features, role_head)
        frames.append({"source": source["id"], "predicate": source["head"], "mentions": mentions, "roles": roles})
    return frames


def evaluate(documents, mention_head, role_head, baseline=False):
    checks = []
    for document in documents:
        frames = predict_baseline(document, mention_head, role_head) if baseline else predict_frames(
            document["prediction"], document["vectors"], mention_head, role_head)
        check = assess_document(document["document"], document["prediction"], frames)
        checks.append({**check, "frames": frames})
    keys = ("gold_frames", "detected_frames", "predicate_candidates", "unannotated_predicate_candidates",
            "gold_spans", "predicted_spans", "exact_spans", "gold_roles", "predicted_roles", "exact_roles",
            "extra_roles", "missing_roles", "duplicate_roles", "frames_exact", "document_exact")
    summary = {key: sum(c[key] for c in checks) for key in keys}
    summary["documents"] = len(checks)
    for unit in ("spans", "roles"):
        for name, prefix in (("precision", "predicted_"), ("recall", "gold_")):
            count = summary[prefix + unit]
            summary[unit + "_" + name] = summary["exact_" + unit] / count if count else None
    return {"summary": summary, "cases": checks}


def groups(documents):
    result = {}
    for d in documents:
        row = d["document"]
        key = ("multi_" if row["complete_frames"] else "single_") + row["split"]
        result.setdefault(key, []).append(d)
    return result


def serialize_training(examples):
    return [{"id": e["row"]["id"], "document_id": e["document_id"], "source": e["source"]["id"],
             "mentions": e["mentions"], "pairs": e["pairs"], "targets": e["targets"].tolist()} for e in examples]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="reports/multi-frame-v5")
    parser.add_argument("--artifacts", default="artifacts/multi-frame-v5")
    args = parser.parse_args()
    out, artifacts = Path(args.output), Path(args.artifacts)
    if out.exists() or artifacts.exists():
        raise ValueError("Refusing to overwrite a frame experiment")
    out.mkdir(parents=True)
    artifacts.mkdir(parents=True)
    def save(name, value):
        (out / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    documents, old_heads, previous, previous_run = cached_documents()
    rows = json.loads(Path(DATA).read_text(encoding="utf-8"))
    dimension, cases = previous["dimension"], previous["cases"]
    with forbidden_paths() as guards:
        model = JapanesePAS()
        assert model.metadata == previous_run["encoder"]
        added = extract(model, [r for r in rows if r["split"] in ("train", "dev")])
        documents.extend(added)
        training_documents = [d for d in documents if d["document"]["split"] == "train"]
        development_documents = [d for d in documents if d["document"]["split"] == "dev"]
        training, development = supervised_frames(training_documents), supervised_frames(development_documents)
        heads, choices = {}, {}
        for name, hidden in ARCHITECTURES:
            heads[name], choices[name], history = fit_sequence(training, dimension * 5, hidden, development)
            save_file(heads[name].state_dict(), str(artifacts / f"mention-{name}.safetensors"))
            save(f"mention-{name}-history.json", history)
        chosen = min(choices, key=lambda name: choices[name]["dev_loss"])
        mention_selection = {"selected": chosen, "choices": choices, "weights_sha256": {
            name: digest(artifacts / f"mention-{name}.safetensors") for name in heads}}
        save("mention-selection.json", mention_selection)
        oof, fold_heads, record = crossfit(training_documents, dimension, cases, choices[chosen])
        for fold, head in fold_heads.items():
            save_file(head.state_dict(), str(artifacts / f"fold-{fold}.safetensors"))
            record["folds"][fold]["weights_sha256"] = digest(artifacts / f"fold-{fold}.safetensors")
        save("crossfit.json", record)
        save("crossfit-predictions.json", serialize_training(oof))
        mention_head = heads[chosen]
        add_frame_candidates(development, mention_head, cases)
        role_heads, role_choices = {}, {}
        for name, hidden in ARCHITECTURES:
            role_heads[name], role_choices[name], history = fit_role(oof + development, dimension, cases, hidden, "boundary")
            save_file(role_heads[name].state_dict(), str(artifacts / f"role-{name}.safetensors"))
            save(f"role-{name}-history.json", history)
        chosen_role = min(role_choices, key=lambda name: role_choices[name]["dev_loss"])
        selection = {"mention": mention_selection, "role": {"selected": chosen_role, "choices": role_choices,
                     "weights_sha256": {name: digest(artifacts / f"role-{name}.safetensors") for name in role_heads}},
                     "dimension": dimension, "cases": cases, "tags": TAGS, "labels": LABELS, "candidate_policy": "predicate_conditioned_bio"}
        save("selection.json", selection)
        confirmation = extract(model, [r for r in rows if r["split"] == "frame_confirmation"])
        documents.extend(confirmation)
        added.extend(confirmation)
        save("evidence.json", [{"document": d["document"], "prediction": d["prediction"]} for d in added])
        save_file({d["document"]["id"]: d["vectors"] for d in added}, str(artifacts / "new-vectors.safetensors"))
        results = {name: {group: evaluate(ds, mention_head, head) for group, ds in groups(documents).items()} for name, head in role_heads.items()}
        results["saved_v4"] = {group: evaluate(ds, old_heads["mention"], old_heads["role"], baseline=True) for group, ds in groups(documents).items()}
        save("evaluation.json", results)
        save("run.json", {"encoder": model.metadata, "fixture_sha256": digest(DATA),
            "previous_files_sha256": {str(PREVIOUS / name): digest(PREVIOUS / name) for name in ("run.json", "selection.json", "evidence.json")},
            "code_sha256": {p: digest(p) for p in ("noema/event_frames.py", "scripts/train_event_frames.py", "scripts/train_mention_sequence.py",
                "scripts/train_role_context.py", "noema/mention_sequence.py", "noema/role_context.py")},
            "new_vectors_sha256": digest(artifacts / "new-vectors.safetensors"), "forbidden_path_calls": [g.call_count for g in guards],
            "training_documents": len(training_documents), "training_predicates": len(training),
            "development_documents": len(development_documents), "development_predicates": len(development),
            "role_training_labels": torch.bincount(torch.cat([e["targets"] for e in oof]), minlength=len(LABELS)).tolist()})
        print(json.dumps({"selection": selection, "confirmation": {name: result["multi_frame_confirmation"]["summary"] for name, result in results.items()}}, indent=2))


if __name__ == "__main__":
    main()
