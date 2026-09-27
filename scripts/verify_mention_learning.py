"""Verify structural learning curves, fold isolation, and raw inference replay."""
import json
from pathlib import Path

import torch
from safetensors.torch import load_file

from noema.definition_probe import digest
from noema.mention_scope import MentionRoleAnalyzer, mention_targets
from scripts.train_mention_learning import (ARCHITECTURES, SPLITS, source_only, fit_mentions, crossfit_candidates,
    add_candidates, fit_role, evaluate, evaluate_mentions, old_heads, forbidden_paths)


def main():
    root, artifacts = Path("reports/mention-learning-v2"), Path("artifacts/mention-learning-v2")
    def read(name):
        return json.loads((root / name).read_text(encoding="utf-8"))
    selection, run = read("selection.json"), read("run.json")
    for key in ("fixtures_sha256", "code_sha256"):
        assert all(digest(path) == value for path, value in run[key].items()), key
    assert digest(artifacts / "features.safetensors") == run["features_sha256"]
    assert digest("reports/mention-scope-v1/run.json") == run["previous_run_sha256"]
    tensors = load_file(str(artifacts / "features.safetensors"))
    examples = [{**e, "vectors": tensors["tokens/" + e["row"]["id"]], "features": tensors["roles/" + e["row"]["id"]],
                 "targets": torch.tensor(e["targets"], dtype=torch.long), "tags": torch.tensor(e["tags"], dtype=torch.long)}
                for e in read("evidence.json")]
    for example in examples:
        assert torch.equal(mention_targets(example["row"], example["prediction"]["tokens"]), example["tags"])
    training = [e for e in examples if e["row"]["split"] in ("train", "dev")]
    curve_selections, expected_curve = read("mention-selections.json"), read("learning-curve.json")
    checks, mention_heads = {}, {}
    def compare_head(head, path, sha):
        assert digest(path) == sha
        weights = load_file(str(path))
        assert head.state_dict().keys() == weights.keys()
        assert all(torch.equal(value, weights[key]) for key, value in head.state_dict().items())
    for amount in (32, 64):
        selected_training = [e for e in training if amount == 64 or e["row"]["split"] == "dev"
                             or not e["row"]["id"].startswith("scope-")]
        assert sum(e["row"]["split"] == "train" for e in selected_training) == amount
        choice_group = curve_selections[str(amount)]
        prefix = "mention-32" if amount == 32 else "mention"
        for name, hidden in ARCHITECTURES:
            head, choice, history = fit_mentions(selected_training, selection["dimension"], hidden)
            compare_head(head, artifacts / f"{prefix}-{name}.safetensors", choice_group["weights_sha256"][name])
            assert choice == choice_group["choices"][name]
            assert history == read(f"{prefix}-{name}-history.json")
            checks[f"{prefix}-{name}"] = {"weights_equal": True, "history_equal": True}
            if name == choice_group["selected"]:
                mention_heads[str(amount)] = head
                for split in SPLITS:
                    assert evaluate_mentions([e for e in examples if e["row"]["split"] == split], head) == expected_curve[str(amount)][split]
    reproduced = [source_only(e) for e in examples]
    add_candidates(reproduced, mention_heads["64"], selection["cases"])
    for actual, original in zip(reproduced, examples, strict=True):
        assert actual["mentions"] == original["mentions"] and actual["pairs"] == original["pairs"]
        assert torch.equal(actual["features"], original["features"]) and torch.equal(actual["targets"], original["targets"])
    choice = selection["mention"]["choices"][selection["mention"]["selected"]]
    crossfit, fold_heads, record = crossfit_candidates(training, selection["dimension"], selection["cases"], choice)
    expected_folds = read("crossfit.json")
    assert record["family_folds"] == expected_folds["family_folds"]
    by_id = {e["row"]["id"]: e for e in examples}
    for fold, head in fold_heads.items():
        saved = expected_folds["folds"][fold]
        assert record["folds"][fold] == {key: value for key, value in saved.items() if key != "weights_sha256"}
        compare_head(head, artifacts / f"fold-{fold}.safetensors", saved["weights_sha256"])
        trained = {by_id[i]["row"]["family"] for i in saved["training_ids"]}
        predicted = {by_id[i]["row"]["family"] for i in saved["predicted_ids"]}
        assert not trained & predicted
        checks["fold-" + fold] = {"weights_equal": True, "history_equal": True, "families_disjoint": True}
    for actual, saved in zip(crossfit, read("crossfit-evidence.json"), strict=True):
        assert actual["row"] == saved["row"] and actual["mentions"] == saved["mentions"] and actual["pairs"] == saved["pairs"]
        assert actual["targets"].tolist() == saved["targets"]
        assert torch.equal(actual["features"], tensors["crossfit/" + actual["row"]["id"]])
    expected = read("evaluation.json")
    for policy in ("in_sample", "crossfit"):
        role_training = training if policy == "in_sample" else crossfit + [e for e in training if e["row"]["split"] == "dev"]
        for name, hidden in ARCHITECTURES:
            key = f"{policy}-{name}"
            head, choice, history = fit_role(role_training, selection["dimension"], selection["cases"], hidden)
            compare_head(head, artifacts / f"role-{key}.safetensors", selection["role"]["weights_sha256"][key])
            assert {**choice, "training_candidates": policy} == selection["role"]["choices"][key]
            assert history == read(f"role-{key}-history.json")
            for split in SPLITS:
                assert evaluate([e for e in examples if e["row"]["split"] == split], head) == expected[key][split]
            checks["role-" + key] = {"weights_equal": True, "history_equal": True, "all_evaluation_equal": True}
    baseline = old_heads()
    old_examples = [source_only(e) for e in examples]
    add_candidates(old_examples, baseline["mention"], selection["cases"])
    for split in SPLITS:
        assert evaluate([e for e in old_examples if e["row"]["split"] == split], baseline["role"]) == expected["saved_v1"][split]
    checks["learning_curves_baseline_and_all_candidate_features_equal"] = True
    raw_matches = []
    with forbidden_paths() as guards:
        analyzer = MentionRoleAnalyzer(str(root), str(artifacts))
        for case in expected[selection["role"]["selected"]]["scope_confirmation"]["cases"]:
            example = by_id[case["id"]]
            result = analyzer.analyze(example["row"]["text"])
            assert result["analysis"] == example["prediction"]
            assert result["mentions"] == case["mentions"] and result["roles"] == case["outputs"]
            assert result == analyzer.analyze(example["row"]["text"])
            raw_matches.append(case["id"])
        checks["forbidden_path_calls"] = [g.call_count for g in guards]
    checks["raw_api_equal_and_repeated"] = raw_matches
    with (root / "verification.json").open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(checks, indent=2) + "\n")
    print("Verified 12 training runs, all cached evaluations, fold isolation, and", len(raw_matches), "fresh repeated text cases")


if __name__ == "__main__":
    main()
