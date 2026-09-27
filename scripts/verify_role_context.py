"""Reproduce boundary role heads, baseline equivalence, and raw-text inference."""
import json
from pathlib import Path

import torch
from safetensors.torch import load_file

from noema.definition_probe import digest
from noema.mention_scope import infer_mentions, mention_targets, scope_targets
from noema.role_context import ContextRoleAnalyzer, FEATURES
from scripts.train_role_context import (DATA, PREVIOUS, PREVIOUS_ARTIFACTS, SPLITS, ARCHITECTURES,
    cached_sources, with_features, fit, evaluate, forbidden_paths)
from scripts.audit_role_context import audit


def main():
    root, artifacts = Path("reports/role-context-v3"), Path("artifacts/role-context-v3")
    def read(name):
        return json.loads((root / name).read_text(encoding="utf-8"))
    selection, run, expected = read("selection.json"), read("run.json"), read("evaluation.json")
    for group in ("code_sha256", "previous_files_sha256"):
        assert all(digest(p) == sha for p, sha in run[group].items()), group
    assert digest(DATA) == run["new_fixture_sha256"]
    assert digest(artifacts / "new-vectors.safetensors") == run["new_vectors_sha256"]
    examples, crossfit, mention_head, previous_selection, _ = cached_sources()
    old_evaluation = json.loads((PREVIOUS / "evaluation.json").read_text(encoding="utf-8"))
    tensors = load_file(str(artifacts / "new-vectors.safetensors"))
    for example in read("evidence.json"):
        example["vectors"] = tensors[example["row"]["id"]]
        assert mention_targets(example["row"], example["prediction"]["tokens"]).tolist() == example["tags"]
        assert infer_mentions(example["prediction"], example["vectors"], mention_head) == example["mentions"]
        assert scope_targets(example["row"], example["prediction"], example["mentions"], example["pairs"]).tolist() == example["targets"]
        examples.append(example)
    for name, sha in selection["mention"]["weights_sha256"].items():
        assert digest(artifacts / f"mention-{name}.safetensors") == sha
    development = [e for e in examples if e["row"]["split"] == "dev"]
    checks = {}
    for mode in FEATURES:
        training = with_features(crossfit + development, selection["cases"], mode)
        converted = with_features(examples, selection["cases"], mode)
        for name, hidden in ARCHITECTURES:
            key = f"{mode}-{name}"
            head, choice, history = fit(training, selection["dimension"], selection["cases"], hidden, mode)
            path = artifacts / f"role-{key}.safetensors"
            assert digest(path) == selection["role"]["weights_sha256"][key]
            weights = load_file(str(path))
            assert all(torch.equal(value, weights[k]) for k, value in head.state_dict().items())
            assert choice == selection["role"]["choices"][key]
            assert history == read(f"role-{key}-history.json")
            for split in SPLITS:
                actual = evaluate([e for e in converted if e["row"]["split"] == split], head)
                assert actual == expected[key][split]
                if mode == "mean" and split != "context_confirmation":
                    assert actual == old_evaluation[f"crossfit-{name}"][split]
            checks[key] = {"weights_equal": True, "history_equal": True, "all_evaluation_equal": True}
            if mode == "mean":
                assert digest(path) == previous_selection["role"]["weights_sha256"][f"crossfit-{name}"]
                assert history == json.loads((PREVIOUS / f"role-crossfit-{name}-history.json").read_text(encoding="utf-8"))
                checks[key]["previous_baseline_exactly_reproduced"] = True
    assert audit(examples, expected) == read("error-audit.json")
    by_id, matches = {e["row"]["id"]: e for e in examples}, []
    with forbidden_paths() as guards:
        analyzer = ContextRoleAnalyzer(str(root), str(artifacts))
        for case in expected[selection["role"]["selected"]]["context_confirmation"]["cases"]:
            example = by_id[case["id"]]
            result = analyzer.analyze(example["row"]["text"])
            assert result["analysis"] == example["prediction"]
            assert result["mentions"] == case["mentions"] and result["roles"] == case["outputs"]
            assert result == analyzer.analyze(example["row"]["text"])
            matches.append(case["id"])
        checks["forbidden_path_calls"] = [g.call_count for g in guards]
    checks["raw_api_equal_and_repeated"] = matches
    checks["error_audit_equal"] = True
    with (root / "verification.json").open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(checks, indent=2) + "\n")
    print("Verified four training runs, exact baseline reproduction, all evaluations, and", len(matches), "fresh repeated text cases")


if __name__ == "__main__":
    main()
