"""Diagnose learned Japanese case links without treating case labels as roles."""
import argparse
from contextlib import ExitStack
import json
import logging
from pathlib import Path
from unittest.mock import patch

from noema.definition_probe import digest
from noema.japanese_pas import JapanesePAS

FIXTURES = ("data/srl-span-v1.json", "data/srl-boundary-v1.json")


def assess(row, prediction):
    if row["ja"] != prediction["text"]:
        raise ValueError("Prediction text differs from annotation")
    phrases = prediction["phrases"]
    lookup = {p["id"]: p for p in phrases}
    checks = []
    for predicate in row["predicates"]:
        begin = row["ja"].index(predicate["ja"])
        end = begin + len(predicate["ja"])
        matching = [p for p in phrases if p["head"]["start"] < end and p["head"]["end"] > begin]
        arguments = []
        for label, argument, _ in predicate["roles"]:
            start = row["ja"].index(argument)
            stop = start + len(argument)
            labels = [r["label"] for p in matching for r in p["relations"]
                      if r["label"] in prediction["pas_labels"] and r["target_phrase"] is not None
                      and lookup[r["target_phrase"]]["start"] <= start and lookup[r["target_phrase"]]["end"] >= stop]
            arguments.append({"semantic_role_in_annotation": label, "expected": [start, stop],
                              "covering_native_cases": labels, "covered_ignoring_role": bool(labels)})
        checks.append({"anchor": [begin, end], "head_detected": bool(matching), "arguments": arguments,
                       "external_relations": [r for p in matching for r in p["relations"] if r["external"] is not None]})
    return {"id": row["id"], "checks": checks}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="reports/japanese-pas-v1")
    args = parser.parse_args()
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=False)
    def save(name, value):
        (output / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    logging.disable(logging.WARNING)
    # The guards cover model initialization and every real inference, not just a mock test.
    import os
    os.environ["KWJA_CLI_MODE"] = "1"
    from transformers.generation.utils import GenerationMixin
    from kwja.utils.jumandic import JumanDic
    from kwja.callbacks.word_module_writer import WordModuleWriter
    from kwja.modules import Seq2SeqModule, TypoModule
    with ExitStack() as stack:
        guards = [stack.enter_context(patch.object(cls, name, side_effect=AssertionError("Forbidden generation/dictionary path")))
                  for cls, name in ((GenerationMixin, "generate"), (JumanDic, "__init__"),
                                    (WordModuleWriter, "__init__"), (Seq2SeqModule, "__init__"), (TypoModule, "__init__"))]
        model = JapanesePAS()
        save("run.json", {"model": model.metadata, "fixture_sha256": {p: digest(p) for p in FIXTURES},
                          "probe_sha256": digest(__file__), "gold_predicates": False})
        predictions, assessments = [], []
        repeat_equal = True
        for path in FIXTURES:
            for row in json.loads(Path(path).read_text(encoding="utf-8")):
                prediction = model.analyze(row["ja"])
                repeat_equal &= prediction == model.analyze(row["ja"])
                predictions.append({"fixture": path, "id": row["id"], **prediction})
                assessments.append({"fixture": path, **assess(row, prediction)})
                print(row["id"], flush=True)
        arguments = [a for doc in assessments for c in doc["checks"] for a in c["arguments"]]
        summary = {"scope": "Role-agnostic coverage of specified spans, not semantic role or graph accuracy",
                   "documents": len(predictions), "arguments_expected": len(arguments),
                   "arguments_covered_ignoring_role": sum(a["covered_ignoring_role"] for a in arguments),
                   "repeat_equal": repeat_equal, "forbidden_path_calls": [g.call_count for g in guards]}
        save("predictions.json", predictions)
        save("assessment.json", assessments)
        save("summary.json", summary)
        print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
