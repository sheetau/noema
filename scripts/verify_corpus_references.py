"""Recheck the pinned corpus and reproduce all official-dev reference counts."""
import json
from pathlib import Path
import subprocess

from noema.definition_probe import digest
from noema.kwdlc_references import assess_corpus_references, corpus_summary, corpus_document
from scripts.prepare_reference_corpus import REPORT, ARTIFACTS, official_splits, text_digest, write


def main():
    import logging
    from rhoknp import Document
    logging.disable(logging.WARNING)
    preparation = json.loads((REPORT / "preparation.json").read_text(encoding="utf-8"))
    run = json.loads((REPORT / "run.json").read_text(encoding="utf-8"))
    assert digest(REPORT / "preparation.json") == run["preparation_sha256"]
    assert digest("docs/corpus-reference-v1-protocol.md") == run["protocol_sha256"]
    for metadata in (run, preparation):
        assert all(digest(p) == sha for p, sha in metadata["code_sha256"].items())
    source = Path(preparation["source_root"])
    assert digest(source / "README.md") == preparation["readme_sha256"]
    assert subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip() == preparation["revision"]
    splits, files = official_splits(source)
    records = {r["id"]: r for r in preparation["records"]}
    count, by_split = 0, {}
    for name, ids in splits.items():
        assert digest(source / "id/split_for_pas" / f"{name}.id") == preparation["split_files_sha256"][name]
        path = ARTIFACTS / f"{name}.jsonl"
        assert digest(path) == preparation["prepared_sha256"][name]
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        assert [row["id"] for row in rows] == sorted(ids)
        for row in rows:
            file = files[row["id"]]
            assert file.relative_to(source).as_posix() == records[row["id"]]["path"]
            assert digest(file) == records[row["id"]]["file_sha256"]
            expected = {**corpus_document(Document.from_knp(file.read_text(encoding="utf-8"))), "split": name}
            assert expected == row and text_digest(row["text"]) == records[row["id"]]["text_sha256"]
            count += 1
        by_split[name] = rows
    assert digest(ARTIFACTS / "predictions.jsonl") == run["predictions_sha256"]
    outputs = [json.loads(line) for line in (ARTIFACTS / "predictions.jsonl").read_text(encoding="utf-8").splitlines()]
    cases = []
    for row, output in zip(by_split["dev"], outputs, strict=True):
        assert row["id"] == output["id"]
        cases.append({**assess_corpus_references(row, output["prediction"]), "failure": output["failure"]})
    assert digest(REPORT / "evaluation.json") == run["evaluation_sha256"]
    expected = json.loads((REPORT / "evaluation.json").read_text(encoding="utf-8"))
    assert expected == {"summary": corpus_summary(cases), "cases": cases}
    assert run["forbidden_path_calls"] == [0] * 5 and not run["training"] and not run["model_selection"]
    write(REPORT / "verification.json", {"reimported_equal": count, "dev_evaluation_equal": len(cases),
          "all_hashes_equal": True, "forbidden_path_calls": run["forbidden_path_calls"], "raw_repeated_equal": run["repeated_equal"]})
    print("Verified", count, "corpus documents and", len(cases), "dev predictions")


if __name__ == "__main__":
    main()
