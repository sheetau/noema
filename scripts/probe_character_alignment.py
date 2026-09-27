"""Compare source-preserving character alignment with the frozen corpus baseline."""
import json
from pathlib import Path

import torch

from noema.definition_probe import digest
from noema.japanese_pas_aligned import AlignedJapanesePAS
from noema.kwdlc_references import assess_corpus_references, corpus_summary
from noema.semantics import SemanticError
from scripts.prepare_reference_corpus import ARTIFACTS as PREVIOUS_ARTIFACTS, REPORT as PREVIOUS_REPORT, write
from scripts.probe_corpus_references import EXPECTED_LIMITS
from scripts.train_mention_scope import forbidden_paths

REPORT = Path("reports/character-alignment-v1")
ARTIFACTS = Path("artifacts/character-alignment-v1")
SYNTHETIC = Path("data/character-alignment-v1.json")
CODE = ("noema/character_alignment.py", "noema/japanese_pas_aligned.py", "noema/japanese_pas.py",
        "noema/preserving_word_tokenizer.py", "noema/kwdlc_references.py", "scripts/probe_character_alignment.py")


def read_rows(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def check_source(text, prediction):
    assert prediction["text"] == text
    assert "".join(token["text"] for token in prediction["tokens"]) == text
    assert all(text[t["start"]:t["end"]] == t["text"] for t in prediction["tokens"])


def main():
    previous = json.loads((PREVIOUS_REPORT / "run.json").read_text(encoding="utf-8"))
    preparation = json.loads((PREVIOUS_REPORT / "preparation.json").read_text(encoding="utf-8"))
    assert digest(PREVIOUS_ARTIFACTS / "predictions.jsonl") == previous["predictions_sha256"]
    assert digest(PREVIOUS_ARTIFACTS / "dev.jsonl") == preparation["prepared_sha256"]["dev"]
    assert all(digest(p) == sha for p, sha in previous["code_sha256"].items())
    rows = read_rows(PREVIOUS_ARTIFACTS / "dev.jsonl")
    old = read_rows(PREVIOUS_ARTIFACTS / "predictions.jsonl")
    REPORT.mkdir(parents=True, exist_ok=False)
    ARTIFACTS.mkdir(parents=True, exist_ok=False)
    cases, comparisons, synthetic, repeated, logits_equal = [], [], [], [], []
    with forbidden_paths() as guards, (ARTIFACTS / "predictions.jsonl").open("x", encoding="utf-8", newline="\n") as stream:
        parser = AlignedJapanesePAS()
        for index, (row, baseline) in enumerate(zip(rows, old, strict=True)):
            assert row["id"] == baseline["id"]
            new_input, _, groups = parser.character_input(row["text"])
            old_input = parser.tokenizers["char"](row["text"], return_tensors="pt", truncation=False)
            same_ids = old_input.keys() == new_input.keys() and all(torch.equal(value, new_input[key]) for key, value in old_input.items())
            try:
                prediction = parser.analyze(row["text"])
                failure = None
                check_source(row["text"], prediction)
                if index < 8 or baseline["prediction"] is None:
                    assert prediction == parser.analyze(row["text"])
                    repeated.append(row["id"])
                    if same_ids:
                        with torch.inference_mode():
                            original_logits, aligned_logits = parser.models["char"](old_input), parser.models["char"](new_input)
                        assert original_logits.keys() == aligned_logits.keys()
                        assert all(torch.equal(value, aligned_logits[key]) for key, value in original_logits.items())
                        logits_equal.append(row["id"])
            except SemanticError as error:
                if str(error) not in EXPECTED_LIMITS:
                    raise
                prediction, failure = None, str(error)
            stream.write(json.dumps({"id": row["id"], "prediction": prediction, "failure": failure}, ensure_ascii=False) + "\n")
            stream.flush()
            cases.append({**assess_corpus_references(row, prediction), "failure": failure})
            comparisons.append({"id": row["id"], "character_inputs_equal": same_ids,
                                "previously_parsed": baseline["prediction"] is not None,
                                "parsed": prediction is not None, "prediction_equal": prediction == baseline["prediction"],
                                "changed_source_groups": sum(g["source_end"] - g["source_start"] != 1 or g["model_end"] - g["model_start"] != 1 for g in groups)})
            if index % 16 == 0 or index == len(rows) - 1:
                print("processed", index + 1, "/", len(rows), "failures", sum(c["failure"] is not None for c in cases), flush=True)
        corpus_word_fallback_calls = parser.tokenizers["word"].fallback_calls
        for row in json.loads(SYNTHETIC.read_text(encoding="utf-8")):
            prediction, vectors = parser.analyze(row["text"], return_features=True)
            check_source(row["text"], prediction)
            assert len(prediction["tokens"]) == len(vectors)
            assert prediction == parser.analyze(row["text"])
            synthetic.append({**row, "prediction": prediction, "vectors_aligned": True, "repeated_equal": True})
            print("source preserved", row["id"], flush=True)
        guard_counts = [guard.call_count for guard in guards]
    write(REPORT / "evaluation.json", {"summary": corpus_summary(cases), "cases": cases})
    write(REPORT / "comparison.json", {"cases": comparisons,
          "previous_success_unchanged": sum(c["previously_parsed"] and c["prediction_equal"] for c in comparisons),
          "previous_success_changed": sum(c["previously_parsed"] and not c["prediction_equal"] for c in comparisons),
          "recovered": sum(not c["previously_parsed"] and c["parsed"] for c in comparisons),
          "character_inputs_equal": sum(c["character_inputs_equal"] for c in comparisons)})
    write(REPORT / "synthetic.json", synthetic)
    write(REPORT / "run.json", {"code_sha256": {p: digest(p) for p in CODE},
          "protocol_sha256": digest("docs/character-alignment-v1-protocol.md"), "synthetic_sha256": digest(SYNTHETIC),
          "previous_run_sha256": digest(PREVIOUS_REPORT / "run.json"), "metadata": parser.metadata,
          "predictions_sha256": digest(ARTIFACTS / "predictions.jsonl"), "repeated_equal": repeated,
          "corpus_word_fallback_calls": corpus_word_fallback_calls,
          "all_word_fallback_calls": parser.tokenizers["word"].fallback_calls,
          "character_logits_equal": logits_equal, "forbidden_path_calls": guard_counts,
          "outputs_sha256": {p: digest(REPORT / p) for p in ("evaluation.json", "comparison.json", "synthetic.json")}})
    print(json.dumps(corpus_summary(cases)["all"], indent=2), flush=True)


if __name__ == "__main__":
    main()
