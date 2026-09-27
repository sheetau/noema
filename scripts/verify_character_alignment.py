"""Replay source ranges, corpus comparison and reference metrics for alignment."""
import json

from noema.character_alignment import character_ids
from noema.definition_probe import digest
from noema.kwdlc_references import assess_corpus_references, corpus_summary
from scripts.prepare_reference_corpus import ARTIFACTS as PREVIOUS_ARTIFACTS, REPORT as PREVIOUS_REPORT, write
from scripts.probe_character_alignment import REPORT, ARTIFACTS, SYNTHETIC, read_rows, check_source


def main():
    from transformers import AutoTokenizer
    def read(name):
        return json.loads((REPORT / name).read_text(encoding="utf-8"))
    run = read("run.json")
    assert all(digest(p) == sha for p, sha in run["code_sha256"].items())
    assert digest("docs/character-alignment-v1-protocol.md") == run["protocol_sha256"]
    assert digest(SYNTHETIC) == run["synthetic_sha256"]
    assert digest(PREVIOUS_REPORT / "run.json") == run["previous_run_sha256"]
    previous = json.loads((PREVIOUS_REPORT / "run.json").read_text(encoding="utf-8"))
    preparation = json.loads((PREVIOUS_REPORT / "preparation.json").read_text(encoding="utf-8"))
    assert digest(PREVIOUS_ARTIFACTS / "dev.jsonl") == preparation["prepared_sha256"]["dev"]
    assert digest(PREVIOUS_ARTIFACTS / "predictions.jsonl") == previous["predictions_sha256"]
    assert digest(ARTIFACTS / "predictions.jsonl") == run["predictions_sha256"]
    assert all(digest(REPORT / p) == sha for p, sha in run["outputs_sha256"].items())
    tokenizer = AutoTokenizer.from_pretrained("artifacts/japanese-pas-model/char/encoder", local_files_only=True,
                                               trust_remote_code=False, do_word_tokenize=False, additional_special_tokens=[" "])
    cases, comparisons = [], []
    rows, previous_outputs = read_rows(PREVIOUS_ARTIFACTS / "dev.jsonl"), read_rows(PREVIOUS_ARTIFACTS / "predictions.jsonl")
    for row, baseline, output in zip(rows, previous_outputs, read_rows(ARTIFACTS / "predictions.jsonl"), strict=True):
        assert row["id"] == baseline["id"] == output["id"]
        ids, groups = character_ids(row["text"], tokenizer)
        same_ids = tokenizer.build_inputs_with_special_tokens(ids) == tokenizer(row["text"])["input_ids"]
        prediction = output["prediction"]
        if prediction is not None:
            check_source(row["text"], prediction)
        cases.append({**assess_corpus_references(row, prediction), "failure": output["failure"]})
        comparisons.append({"id": row["id"], "character_inputs_equal": same_ids,
                            "previously_parsed": baseline["prediction"] is not None, "parsed": prediction is not None,
                            "prediction_equal": prediction == baseline["prediction"],
                            "changed_source_groups": sum(g["source_end"] - g["source_start"] != 1 or g["model_end"] - g["model_start"] != 1 for g in groups)})
    assert {"summary": corpus_summary(cases), "cases": cases} == read("evaluation.json")
    comparison = read("comparison.json")
    assert comparisons == comparison["cases"]
    assert comparison["previous_success_unchanged"] == sum(c["previously_parsed"] and c["prediction_equal"] for c in comparisons)
    assert comparison["previous_success_changed"] == sum(c["previously_parsed"] and not c["prediction_equal"] for c in comparisons)
    assert comparison["recovered"] == sum(not c["previously_parsed"] and c["parsed"] for c in comparisons)
    assert comparison["character_inputs_equal"] == sum(c["character_inputs_equal"] for c in comparisons)
    fixtures = json.loads(SYNTHETIC.read_text(encoding="utf-8"))
    synthetic = read("synthetic.json")
    for row, output in zip(fixtures, synthetic, strict=True):
        assert all(row[k] == output[k] for k in row)
        check_source(row["text"], output["prediction"])
        assert output["repeated_equal"] and output["vectors_aligned"]
    assert run["forbidden_path_calls"] == [0] * 5
    assert run["all_word_fallback_calls"] >= run["corpus_word_fallback_calls"]
    write(REPORT / "verification.json", {"corpus_comparison_equal": len(cases), "evaluation_equal": True,
          "synthetic_source_preserved": len(synthetic), "forbidden_path_calls": run["forbidden_path_calls"],
          "corpus_word_fallback_calls": run["corpus_word_fallback_calls"], "all_word_fallback_calls": run["all_word_fallback_calls"],
          "repeated_equal": run["repeated_equal"], "character_logits_equal": run["character_logits_equal"]})
    print("Verified", len(cases), "corpus comparisons and", len(synthetic), "source-preservation fixtures")


if __name__ == "__main__":
    main()
