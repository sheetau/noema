"""Run the frozen raw-text reference baseline on every official dev document."""
import json
from pathlib import Path

from noema.definition_probe import digest
from noema.japanese_pas import JapanesePAS
from noema.kwdlc_references import assess_corpus_references, corpus_summary
from noema.semantics import SemanticError
from scripts.prepare_reference_corpus import REPORT, ARTIFACTS, write
from scripts.train_mention_scope import forbidden_paths

EXPECTED_LIMITS = {"Japanese char context exceeded", "Japanese word context exceeded",
                   "Japanese word input was split or omitted", "Character tokenizer lost source alignment"}


def main():
    preparation = json.loads((REPORT / "preparation.json").read_text(encoding="utf-8"))
    assert all(digest(path) == sha for path, sha in preparation["code_sha256"].items())
    assert digest(ARTIFACTS / "dev.jsonl") == preparation["prepared_sha256"]["dev"]
    rows = [json.loads(line) for line in (ARTIFACTS / "dev.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 512 and all(row["split"] == "dev" for row in rows)
    cases, repeated = [], []
    with forbidden_paths() as guards, (ARTIFACTS / "predictions.jsonl").open("x", encoding="utf-8", newline="\n") as stream:
        parser = JapanesePAS()
        for index, row in enumerate(rows):
            try:
                prediction = parser.analyze(row["text"])
                failure = None
                if index < 8:
                    assert parser.analyze(row["text"]) == prediction
                    repeated.append(row["id"])
            except SemanticError as error:
                if str(error) not in EXPECTED_LIMITS:
                    raise
                prediction, failure = None, str(error)
            stream.write(json.dumps({"id": row["id"], "prediction": prediction, "failure": failure}, ensure_ascii=False) + "\n")
            stream.flush()
            cases.append({**assess_corpus_references(row, prediction), "failure": failure})
            if index % 16 == 0 or index == len(rows) - 1:
                print("processed", index + 1, "/", len(rows), "failed", sum(c["failure"] is not None for c in cases), flush=True)
        forbidden_counts = [guard.call_count for guard in guards]
    write(REPORT / "evaluation.json", {"summary": corpus_summary(cases), "cases": cases})
    write(REPORT / "run.json", {"preparation_sha256": digest(REPORT / "preparation.json"),
          "protocol_sha256": digest("docs/corpus-reference-v1-protocol.md"),
          "code_sha256": {p: digest(p) for p in ("noema/kwdlc_references.py", "noema/japanese_pas.py", "scripts/probe_corpus_references.py")},
          "metadata": parser.metadata, "split": "dev", "training": False, "model_selection": False,
          "repeated_equal": repeated, "forbidden_path_calls": forbidden_counts,
          "predictions_sha256": digest(ARTIFACTS / "predictions.jsonl"), "evaluation_sha256": digest(REPORT / "evaluation.json")})
    print(json.dumps(corpus_summary(cases), indent=2), flush=True)


if __name__ == "__main__":
    main()
