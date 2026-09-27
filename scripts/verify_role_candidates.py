"""Reproduce expanded-candidate learning and saved-head raw-text inference."""
import json
import logging
from pathlib import Path

import torch
from safetensors.torch import load_file

from noema.role_transfer import RoleAnalyzer
from scripts.train_role_transfer import fit
from scripts.train_role_candidates import evaluate_strict


def main():
    root = Path("reports/role-candidates-v2")
    selection = json.loads((root / "selection.json").read_text(encoding="utf-8"))
    evidence = json.loads((root / "evidence.json").read_text(encoding="utf-8"))
    tensors = load_file("artifacts/role-candidates-v2/features.safetensors")
    examples = [{**e, "features": tensors["all/" + e["row"]["id"]], "targets": torch.tensor(e["targets"])} for e in evidence]
    expected = json.loads((root / "evaluation.json").read_text(encoding="utf-8"))
    checks = {}
    for name, hidden in (("linear", 0), ("mlp", 64)):
        head, choice, history = fit([e for e in examples if e["row"]["split"] in ("train", "dev")],
                                  selection["dimension"], selection["cases"], hidden)
        weights = load_file(f"artifacts/role-candidates-v2/{name}.safetensors")
        assert all(torch.equal(value, weights[key]) for key, value in head.state_dict().items())
        assert choice == selection["choices"][name]
        assert history == json.loads((root / f"{name}-history.json").read_text(encoding="utf-8"))
        for split in ("train", "dev", "test", "confirmation"):
            assert evaluate_strict([e for e in examples if e["row"]["split"] == split], head) == expected[name][split]
        checks[name] = {"weights_equal": True, "history_equal": True, "all_evaluation_equal": True}
    logging.disable(logging.WARNING)
    analyzer = RoleAnalyzer(str(root), "artifacts/role-candidates-v2")
    chosen = selection["selected"]
    by_id = {e["row"]["id"]: e for e in evidence}
    matches = []
    for case in expected[chosen]["confirmation"]["cases"]:
        e = by_id[case["id"]]
        result = analyzer.analyze(e["row"]["text"])
        assert result["analysis"] == e["prediction"]
        assert result["roles"] == case["outputs"]
        assert result == analyzer.analyze(e["row"]["text"])
        matches.append(case["id"])
    checks["raw_api_equal_and_repeated"] = matches
    with (root / "verification.json").open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(checks, indent=2) + "\n")
    print("Verified both training runs and", len(matches), "raw API cases")


if __name__ == "__main__":
    main()
