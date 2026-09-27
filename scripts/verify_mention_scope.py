"""Reproduce both learned stages, then compare fresh text inference and repeats."""
import json
from pathlib import Path

import torch
from safetensors.torch import load_file

from noema.definition_probe import digest
from noema.mention_scope import MentionRoleAnalyzer, mention_targets
from scripts.train_mention_scope import (ARCHITECTURES, SPLITS, add_candidates, evaluate,
                                         fit_mentions, forbidden_paths)
from scripts.train_role_transfer import fit as fit_role


def main():
    root, artifacts = Path("reports/mention-scope-v1"), Path("artifacts/mention-scope-v1")
    def read(name):
        return json.loads((root / name).read_text(encoding="utf-8"))
    selection, evidence, run = read("selection.json"), read("evidence.json"), read("run.json")
    for group in ("fixtures_sha256", "code_sha256"):
        assert all(digest(path) == expected for path, expected in run[group].items()), group
    assert digest(artifacts / "features.safetensors") == run["features_sha256"]
    tensors = load_file(str(artifacts / "features.safetensors"))
    examples = [{**e, "vectors": tensors["tokens/" + e["row"]["id"]], "features": tensors["roles/" + e["row"]["id"]],
                 "tags": torch.tensor(e["tags"]), "targets": torch.tensor(e["targets"])} for e in evidence]
    for example in examples:
        assert torch.equal(mention_targets(example["row"], example["prediction"]["tokens"]), example["tags"])
    training = [e for e in examples if e["row"]["split"] in ("train", "dev")]
    expected, checks = read("evaluation.json"), {}
    chosen_mention = None
    for stage in ("mention", "role"):
        for name, hidden in ARCHITECTURES:
            if stage == "mention":
                head, choice, history = fit_mentions(training, selection["dimension"], hidden)
                if name == selection[stage]["selected"]:
                    chosen_mention = head
            else:
                head, choice, history = fit_role(training, selection["dimension"], selection["cases"], hidden)
                for split in SPLITS:
                    assert evaluate([e for e in examples if e["row"]["split"] == split], head) == expected[name][split]
            path = artifacts / f"{stage}-{name}.safetensors"
            assert digest(path) == selection[stage]["weights_sha256"][name]
            weights = load_file(str(path))
            assert all(torch.equal(value, weights[key]) for key, value in head.state_dict().items())
            assert choice == selection[stage]["choices"][name]
            assert history == read(f"{stage}-{name}-history.json")
            checks[f"{stage}-{name}"] = {"weights_equal": True, "history_equal": True}
    reproduced = [{key: e[key] for key in ("row", "prediction", "vectors")} for e in examples]
    add_candidates(reproduced, chosen_mention, selection["cases"])
    for actual, original in zip(reproduced, examples, strict=True):
        assert actual["mentions"] == original["mentions"] and actual["pairs"] == original["pairs"]
        assert torch.equal(actual["features"], original["features"]) and torch.equal(actual["targets"], original["targets"])
    checks["cached_mentions_features_targets_and_all_evaluations_equal"] = True
    by_id, matches = {e["row"]["id"]: e for e in evidence}, []
    with forbidden_paths() as guards:
        analyzer = MentionRoleAnalyzer(str(root), str(artifacts))
        for case in expected[selection["role"]["selected"]]["mention_confirmation"]["cases"]:
            example = by_id[case["id"]]
            result = analyzer.analyze(example["row"]["text"])
            assert result["analysis"] == example["prediction"]
            assert result["mentions"] == case["mentions"] and result["roles"] == case["outputs"]
            assert result == analyzer.analyze(example["row"]["text"])
            matches.append(case["id"])
        checks["forbidden_path_calls"] = [g.call_count for g in guards]
    checks["raw_api_equal_and_repeated"] = matches
    with (root / "verification.json").open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(checks, indent=2) + "\n")
    print("Verified four training runs, all cached predictions, and", len(matches), "fresh repeated text cases")


if __name__ == "__main__":
    main()
