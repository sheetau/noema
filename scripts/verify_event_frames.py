"""Reproduce event-conditioned scopes, connected folds and raw nested inference."""
import json
from pathlib import Path

import torch
from safetensors.torch import load_file

from noema.definition_probe import digest
from noema.event_frames import EventFrameAnalyzer, supervised_frames, add_frame_candidates
from noema.mention_scope import mention_targets
from scripts.train_event_frames import (DATA, PREVIOUS, ARCHITECTURES, cached_documents, fit_sequence,
    crossfit, serialize_training, fit_role, groups, evaluate, forbidden_paths)


def main():
    root, artifacts = Path("reports/multi-frame-v5"), Path("artifacts/multi-frame-v5")
    def read(name):
        return json.loads((root / name).read_text(encoding="utf-8"))
    selection, run, expected = read("selection.json"), read("run.json"), read("evaluation.json")
    for group in ("code_sha256", "previous_files_sha256"):
        assert all(digest(p) == sha for p, sha in run[group].items()), group
    assert digest(DATA) == run["fixture_sha256"]
    assert digest(artifacts / "new-vectors.safetensors") == run["new_vectors_sha256"]
    documents, old_heads, _, _ = cached_documents()
    tensors = load_file(str(artifacts / "new-vectors.safetensors"))
    rows = {r["id"]: r for r in json.loads(Path(DATA).read_text(encoding="utf-8"))}
    for d in read("evidence.json"):
        row = d["document"]
        assert row == {**rows[row["id"]], "complete_frames": True}
        for frame in row["frames"]:
            mention_targets({**frame, "text": row["text"]}, d["prediction"]["tokens"])
        documents.append({**d, "vectors": tensors[row["id"]]})
    training_docs = [d for d in documents if d["document"]["split"] == "train"]
    development_docs = [d for d in documents if d["document"]["split"] == "dev"]
    training, development = supervised_frames(training_docs), supervised_frames(development_docs)
    assert len(training_docs) == run["training_documents"] and len(training) == run["training_predicates"]
    assert len(development_docs) == run["development_documents"] and len(development) == run["development_predicates"]
    checks = {}
    def check_head(head, path, sha):
        assert digest(path) == sha
        weights = load_file(str(path))
        assert head.state_dict().keys() == weights.keys()
        assert all(torch.equal(value, weights[key]) for key, value in head.state_dict().items())
    mention_head = None
    for name, hidden in ARCHITECTURES:
        head, choice, history = fit_sequence(training, selection["dimension"] * 5, hidden, development)
        check_head(head, artifacts / f"mention-{name}.safetensors", selection["mention"]["weights_sha256"][name])
        assert choice == selection["mention"]["choices"][name]
        assert history == read(f"mention-{name}-history.json")
        checks["mention-" + name] = {"weights_equal": True, "history_equal": True}
        if name == selection["mention"]["selected"]:
            mention_head = head
    choice = selection["mention"]["choices"][selection["mention"]["selected"]]
    oof, fold_heads, record = crossfit(training_docs, selection["dimension"], selection["cases"], choice)
    original_folds = read("crossfit.json")
    for key in ("family_folds", "document_folds"):
        assert record[key] == original_folds[key]
    by_id = {d["document"]["id"]: d for d in documents}
    for fold, head in fold_heads.items():
        original = original_folds["folds"][fold]
        assert record["folds"][fold] == {k: v for k, v in original.items() if k != "weights_sha256"}
        check_head(head, artifacts / f"fold-{fold}.safetensors", original["weights_sha256"])
        trained = {f["family"] for i in original["training_ids"] for f in by_id[i]["document"]["frames"]}
        predicted = {f["family"] for i in original["predicted_ids"] for f in by_id[i]["document"]["frames"]}
        assert not trained & predicted
        checks["fold-" + fold] = {"weights_equal": True, "history_equal": True, "all_families_disjoint": True}
    assert serialize_training(oof) == read("crossfit-predictions.json")
    add_frame_candidates(development, mention_head, selection["cases"])
    for name, hidden in ARCHITECTURES:
        head, choice, history = fit_role(oof + development, selection["dimension"], selection["cases"], hidden, "boundary")
        check_head(head, artifacts / f"role-{name}.safetensors", selection["role"]["weights_sha256"][name])
        assert choice == selection["role"]["choices"][name]
        assert history == read(f"role-{name}-history.json")
        for group, ds in groups(documents).items():
            assert evaluate(ds, mention_head, head) == expected[name][group]
        checks["role-" + name] = {"weights_equal": True, "history_equal": True, "all_evaluation_equal": True}
    for group, ds in groups(documents).items():
        assert evaluate(ds, old_heads["mention"], old_heads["role"], baseline=True) == expected["saved_v4"][group]
    checks["all_crossfit_predictions_and_baseline_equal"] = True
    matches = []
    with forbidden_paths() as guards:
        analyzer = EventFrameAnalyzer(str(root), str(artifacts))
        for case in expected[selection["role"]["selected"]]["multi_frame_confirmation"]["cases"]:
            d = by_id[case["id"]]
            actual = analyzer.analyze(d["document"]["text"])
            assert actual["analysis"] == d["prediction"] and actual["frames"] == case["frames"]
            assert actual == analyzer.analyze(d["document"]["text"])
            matches.append(case["id"])
        checks["forbidden_path_calls"] = [g.call_count for g in guards]
    checks["raw_api_equal_and_repeated"] = matches
    with (root / "verification.json").open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(checks, indent=2) + "\n")
    print("Verified eight training runs, all frame predictions, connected fold isolation, and", len(matches), "fresh repeated text cases")


if __name__ == "__main__":
    main()
