"""Replay role training and diagnose the prior raw-text regression examples."""
from contextlib import ExitStack
import json
import logging
import os
from pathlib import Path
from unittest.mock import patch

import torch
from safetensors.torch import load_file

from noema.role_transfer import RoleAnalyzer, LABELS, assess
from scripts.train_role_transfer import fit, evaluate


def main():
    root = Path("reports/role-transfer-v1")
    selection = json.loads((root / "selection.json").read_text(encoding="utf-8"))
    evidence = json.loads((root / "evidence.json").read_text(encoding="utf-8"))
    cached = load_file("artifacts/role-transfer-v1/features.safetensors")
    examples = [{**e, "features": cached[e["row"]["id"]], "targets": torch.tensor(e["targets"])} for e in evidence]
    expected = json.loads((root / "evaluation.json").read_text(encoding="utf-8"))
    checks = {}
    for name, hidden in (("linear", 0), ("mlp", 64)):
        head, choice, history = fit([e for e in examples if e["row"]["split"] != "test"], selection["dimension"], selection["cases"], hidden)
        weights = load_file(f"artifacts/role-transfer-v1/{name}.safetensors")
        assert all(torch.equal(value, weights[key]) for key, value in head.state_dict().items())
        assert choice == selection["choices"][name]
        assert history == json.loads((root / f"{name}-history.json").read_text(encoding="utf-8"))
        for split in ("train", "dev", "test"):
            assert evaluate([e for e in examples if e["row"]["split"] == split], head) == expected[name][split]
        checks[name] = {"weights_equal": True, "history_equal": True, "evaluation_equal": True}
    os.environ["KWJA_CLI_MODE"] = "1"
    logging.disable(logging.WARNING)
    from transformers.generation.utils import GenerationMixin
    from kwja.utils.jumandic import JumanDic
    from kwja.callbacks.word_module_writer import WordModuleWriter
    from kwja.modules import Seq2SeqModule, TypoModule
    with ExitStack() as stack:
        guards = [stack.enter_context(patch.object(cls, name, side_effect=AssertionError("Forbidden generation/dictionary path")))
                  for cls, name in ((GenerationMixin, "generate"), (JumanDic, "__init__"),
                                    (WordModuleWriter, "__init__"), (Seq2SeqModule, "__init__"), (TypoModule, "__init__"))]
        analyzer = RoleAnalyzer()
        prior = {(p["fixture"], p["id"]): p for p in json.loads(Path("reports/japanese-pas-v1/predictions.json").read_text(encoding="utf-8"))}
        predictions, assessments = [], []
        for fixture in ("data/srl-span-v1.json", "data/srl-boundary-v1.json"):
            for row in json.loads(Path(fixture).read_text(encoding="utf-8")):
                prediction = analyzer.analyze(row["ja"])
                assert prediction == analyzer.analyze(row["ja"])
                before = {k: v for k, v in prior[fixture, row["id"]].items() if k not in ("fixture", "id")}
                assert prediction["analysis"] == before
                predictions.append({"fixture": fixture, "id": row["id"], **prediction})
                for i, event in enumerate(row["predicates"]):
                    # This maps the existing evaluation annotation, never runtime labels.
                    role_names = {"A0": "agent", "A1": "patient", "A2": "recipient"}
                    annotated = {"id": f"{row['id']}-{i}", "text": row["ja"], "predicate": event["ja"],
                                 "split": "regression", "family": row["id"],
                                 "roles": [[role_names[r], ja] for r, ja, _ in event["roles"] if r in role_names]}
                    check = assess(annotated, prediction["analysis"], prediction["roles"],
                                   [LABELS.index(r["role"]) for r in prediction["roles"]])
                    assessments.append({"fixture": fixture, **check})
        checks.update(repeated_raw_predictions_equal=True, prior_parser_outputs_equal=True,
                      forbidden_path_calls=[g.call_count for g in guards])
    for name, value in (("verification.json", checks), ("regression-predictions.json", predictions), ("regression-assessment.json", assessments)):
        with (root / name).open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(checks))


if __name__ == "__main__":
    main()
