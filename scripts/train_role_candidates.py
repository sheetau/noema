"""Expand role candidates beyond frozen PAS edges, then test lexical transfer."""
import argparse
from contextlib import ExitStack
import json
import logging
import os
from pathlib import Path
from unittest.mock import patch

import torch
from safetensors.torch import load_file, save_file

from noema.definition_probe import digest
from noema.japanese_pas import JapanesePAS
from noema.role_transfer import LABELS, UNLINKED, RoleHead, candidates, all_phrase_candidates, targets
from scripts.train_role_transfer import DATA, fit, evaluate, validate_rows

CONFIRMATION = "data/role-candidates-v2.json"


def evaluate_strict(examples, head):
    result = evaluate(examples, head)
    extra, wrong, exact = 0, 0, 0
    for example, case in zip(examples, result["cases"], strict=True):
        labels = example["targets"]
        selected = torch.tensor([LABELS.index(o["role"]) for o in case["outputs"]])
        non_roles = labels == 0
        roles = labels > 0
        case["extra_roles"] = int(((selected != 0) & non_roles).sum())
        case["wrong_roles_on_detected_arguments"] = int(((selected != labels) & roles).sum())
        case["annotated_frame_exact"] = case["all_specified_correct"] and case["extra_roles"] == 0
        extra += case["extra_roles"]
        wrong += case["wrong_roles_on_detected_arguments"]
        exact += case["annotated_frame_exact"]
    result["summary"].update(extra_roles=extra, wrong_roles_on_detected_arguments=wrong, annotated_frames_exact=exact)
    return result


def extract(model, rows, cases):
    examples = []
    for row in rows:
        prediction, vectors = model.analyze(row["text"], return_features=True)
        pairs, features = all_phrase_candidates(prediction, vectors, cases)
        native_pairs, native_features = candidates(prediction, vectors, cases[:-1])
        examples.append({"row": row, "prediction": prediction, "pairs": pairs, "features": features,
                         "targets": targets(row, prediction, pairs), "native_pairs": native_pairs,
                         "native_features": native_features, "native_targets": targets(row, prediction, native_pairs)})
        print("features", row["id"], flush=True)
    return examples


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="reports/role-candidates-v2")
    parser.add_argument("--artifacts", default="artifacts/role-candidates-v2")
    args = parser.parse_args()
    out, artifacts = Path(args.output), Path(args.artifacts)
    if out.exists() or artifacts.exists():
        raise ValueError("Refusing to overwrite an experiment")
    out.mkdir(parents=True)
    artifacts.mkdir(parents=True)
    def save(name, value):
        (out / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    os.environ["KWJA_CLI_MODE"] = "1"
    logging.disable(logging.WARNING)
    from transformers.generation.utils import GenerationMixin
    from kwja.utils.jumandic import JumanDic
    from kwja.callbacks.word_module_writer import WordModuleWriter
    from kwja.modules import Seq2SeqModule, TypoModule
    with ExitStack() as stack:
        guards = [stack.enter_context(patch.object(cls, method, side_effect=AssertionError("Forbidden generation/dictionary path")))
                  for cls, method in ((GenerationMixin, "generate"), (JumanDic, "__init__"), (WordModuleWriter, "__init__"),
                                      (Seq2SeqModule, "__init__"), (TypoModule, "__init__"))]
        rows = json.loads(Path(DATA).read_text(encoding="utf-8"))
        validate_rows(rows)
        confirmation = json.loads(Path(CONFIRMATION).read_text(encoding="utf-8"))
        assert not ({r["family"] for r in rows} & {r["family"] for r in confirmation})
        validate_rows([{**r, "split": "test"} for r in confirmation])
        model = JapanesePAS()
        cases = list(model.configs["word"].pas_cases) + [UNLINKED]
        dimension = model.models["word"].encoder.config.hidden_size
        examples = extract(model, [r for r in rows if r["split"] != "test"], cases)
        heads, choices = {}, {}
        for name, hidden in (("linear", 0), ("mlp", 64)):
            heads[name], choices[name], history = fit(examples, dimension, cases, hidden)
            save_file(heads[name].state_dict(), str(artifacts / f"{name}.safetensors"))
            save(f"{name}-history.json", history)
        selection = {"selected": min(choices, key=lambda n: choices[n]["dev_loss"]), "choices": choices,
                     "dimension": dimension, "cases": cases, "labels": LABELS, "candidate_policy": "all_phrases",
                     "weights_sha256": {n: digest(artifacts / f"{n}.safetensors") for n in heads}}
        save("selection.json", selection)
        examples.extend(extract(model, [r for r in rows if r["split"] == "test"] + confirmation, cases))
        # Frozen previous baseline shares the exact same encoder invocation.
        old = json.loads(Path("reports/role-transfer-v1/selection.json").read_text(encoding="utf-8"))
        old_name = old["selected"]
        old_path = Path("artifacts/role-transfer-v1", old_name + ".safetensors")
        assert digest(old_path) == old["weights_sha256"][old_name]
        baseline = RoleHead(dimension, old["cases"], old["choices"][old_name]["hidden"])
        baseline.load_state_dict(load_file(str(old_path)), strict=True)
        baseline.eval()
        native = [{**e, "pairs": e["native_pairs"], "features": e["native_features"], "targets": e["native_targets"]} for e in examples]
        all_heads = {**heads, "frozen_native_baseline": baseline}
        results = {name: {split: evaluate_strict([e for e in (native if name == "frozen_native_baseline" else examples)
                                               if e["row"]["split"] == split], head)
                          for split in ("train", "dev", "test", "confirmation")} for name, head in all_heads.items()}
        save("evaluation.json", results)
        save("evidence.json", [{k: e[k] for k in ("row", "prediction", "pairs", "native_pairs")} |
                               {k: e[k].tolist() for k in ("targets", "native_targets")} for e in examples])
        save_file({prefix + e["row"]["id"]: e[field] for e in examples
                   for prefix, field in (("all/", "features"), ("native/", "native_features"))}, str(artifacts / "features.safetensors"))
        save("run.json", {"encoder": model.metadata, "fixtures": {p: digest(p) for p in (DATA, CONFIRMATION)},
                          "code_sha256": {p: digest(p) for p in ("noema/role_transfer.py", "scripts/train_role_transfer.py", __file__)},
                          "features_sha256": digest(artifacts / "features.safetensors"),
                          "forbidden_path_calls": [g.call_count for g in guards]})
        print(json.dumps({"selected": selection["selected"], "confirmation": {
            n: r["confirmation"]["summary"] for n, r in results.items()}}, indent=2))


if __name__ == "__main__":
    main()
