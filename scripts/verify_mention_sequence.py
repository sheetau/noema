"""Reproduce sequence training, held-out folds, and saved raw-text inference."""
import json
from pathlib import Path

import torch
from safetensors.torch import load_file

from noema.definition_probe import digest
from noema.mention_sequence import SequenceRoleAnalyzer
from noema.mention_scope import mention_targets
from scripts.train_mention_sequence import (DATA, SPLITS, ARCHITECTURES, PREVIOUS, cached_sources,
    source_only, fit_sequence, add_candidates, crossfit, fit_role, evaluate, forbidden_paths)
from scripts.audit_role_context import audit


def main():
    root, artifacts = Path("reports/mention-sequence-v4"), Path("artifacts/mention-sequence-v4")
    def read(name):
        return json.loads((root / name).read_text(encoding="utf-8"))
    run, selection, expected = read("run.json"), read("selection.json"), read("evaluation.json")
    for group in ("code_sha256", "previous_files_sha256"):
        assert all(digest(p) == sha for p, sha in run[group].items()), group
    assert digest(DATA) == run["new_fixture_sha256"]
    assert digest(artifacts / "new-vectors.safetensors") == run["new_vectors_sha256"]
    examples, old_mention, old_role, old_selection, _ = cached_sources()
    saved = {e["row"]["id"]: e for e in read("evidence.json")}
    tensors = load_file(str(artifacts / "new-vectors.safetensors"))
    for row in json.loads(Path(DATA).read_text(encoding="utf-8")):
        e = saved[row["id"]]
        assert row == e["row"]
        examples.append({"row": row, "prediction": e["prediction"], "vectors": tensors[row["id"]], "tags": torch.tensor(e["tags"], dtype=torch.long)})
    for e in examples:
        assert torch.equal(mention_targets(e["row"], e["prediction"]["tokens"]), e["tags"])
    training = [e for e in examples if e["row"]["split"] == "train"]
    development = [e for e in examples if e["row"]["split"] == "dev"]
    checks = {}
    def check_head(head, path, sha):
        assert digest(path) == sha
        weights = load_file(str(path))
        assert head.state_dict().keys() == weights.keys()
        assert all(torch.equal(value, weights[key]) for key, value in head.state_dict().items())
    mention_head = None
    for name, hidden in ARCHITECTURES:
        head, choice, history = fit_sequence(training, selection["dimension"], hidden, development)
        check_head(head, artifacts / f"mention-{name}.safetensors", selection["mention"]["weights_sha256"][name])
        assert choice == selection["mention"]["choices"][name]
        assert history == read(f"mention-{name}-history.json")
        checks["mention-" + name] = {"weights_equal": True, "history_equal": True}
        if name == selection["mention"]["selected"]:
            mention_head = head
    add_candidates(examples, mention_head, selection["cases"])
    for e in examples:
        original = saved[e["row"]["id"]]
        assert e["mentions"] == original["mentions"] and e["pairs"] == original["pairs"]
        assert e["targets"].tolist() == original["targets"]
    choice = selection["mention"]["choices"][selection["mention"]["selected"]]
    oof, fold_heads, record = crossfit(training, selection["dimension"], selection["cases"], choice)
    expected_folds = read("crossfit.json")
    assert record["family_folds"] == expected_folds["family_folds"]
    by_id = {e["row"]["id"]: e for e in examples}
    for fold, head in fold_heads.items():
        saved_fold = expected_folds["folds"][fold]
        assert record["folds"][fold] == {k: v for k, v in saved_fold.items() if k != "weights_sha256"}
        check_head(head, artifacts / f"fold-{fold}.safetensors", saved_fold["weights_sha256"])
        assert not ({by_id[i]["row"]["family"] for i in saved_fold["training_ids"]}
                    & {by_id[i]["row"]["family"] for i in saved_fold["predicted_ids"]})
        checks["fold-" + fold] = {"weights_equal": True, "history_equal": True, "families_disjoint": True}
    for e, original in zip(oof, read("crossfit-evidence.json"), strict=True):
        assert e["row"] == original["row"] and e["mentions"] == original["mentions"] and e["pairs"] == original["pairs"]
        assert e["targets"].tolist() == original["targets"]
    for name, hidden in ARCHITECTURES:
        head, choice, history = fit_role(oof + development, selection["dimension"], selection["cases"], hidden, "boundary")
        check_head(head, artifacts / f"role-{name}.safetensors", selection["role"]["weights_sha256"][name])
        assert choice == selection["role"]["choices"][name]
        assert history == read(f"role-{name}-history.json")
        for split in SPLITS:
            assert evaluate([e for e in examples if e["row"]["split"] == split], head) == expected[name][split]
        checks["role-" + name] = {"weights_equal": True, "history_equal": True, "all_evaluation_equal": True}
    baseline = [source_only(e) for e in examples]
    add_candidates(baseline, old_mention, selection["cases"], sequence=False)
    old_evaluation = json.loads((PREVIOUS / "evaluation.json").read_text(encoding="utf-8"))[old_selection["role"]["selected"]]
    for split in SPLITS:
        actual = evaluate([e for e in baseline if e["row"]["split"] == split], old_role)
        assert actual == expected["saved_v3"][split]
        if split != "sequence_confirmation":
            assert actual == old_evaluation[split]
    error_audit = audit(examples, {name: r for name, r in expected.items() if name != "saved_v3"})
    error_audit.update(audit(baseline, {"saved_v3": expected["saved_v3"]}))
    assert error_audit == read("error-audit.json")
    checks["all_candidates_baseline_and_error_audit_equal"] = True
    matches = []
    with forbidden_paths() as guards:
        analyzer = SequenceRoleAnalyzer(str(root), str(artifacts))
        for case in expected[selection["role"]["selected"]]["sequence_confirmation"]["cases"]:
            e = by_id[case["id"]]
            actual = analyzer.analyze(e["row"]["text"])
            assert actual["analysis"] == e["prediction"]
            assert actual["mentions"] == case["mentions"] and actual["roles"] == case["outputs"]
            assert actual == analyzer.analyze(e["row"]["text"])
            matches.append(case["id"])
        checks["forbidden_path_calls"] = [g.call_count for g in guards]
    checks["raw_api_equal_and_repeated"] = matches
    with (root / "verification.json").open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(checks, indent=2) + "\n")
    print("Verified eight training runs, all candidates, evaluation, and", len(matches), "fresh repeated text cases")


if __name__ == "__main__":
    main()
